#!/usr/bin/env python3
"""Strict offline parser for one fixed primary-event-log capture."""
import argparse, base64, binascii, hashlib, importlib.util, json, os, re, sys
from pathlib import Path

BOOT = "00000000-0000-4000-8000-000000000000"
MANIFEST = "ac4133ccb6e2b12576006a981f1d585ad0fe1384a2a6d1a5096f3a81bced5371"
WRAPPER = "245323c709dc098d343a1ee470c505ba909249126d4fe5645b12b20709ff7031"
RUNNER = "7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a"
RUNNER_PATH = Path(__file__).resolve().parent.parent / "managed-tcon-status-read/run-status-read.py"
REQUEST = {"target": "0x101", "address": "0x20205000", "length": 3072}
SELFTEST = {"selfTestsPassed": 26, "targetOperations": 0}
PHASES = ("open", "claim", "out", "in", "release", "close")
VALUES = (None, 0, 12, 3072, 0, 0)
LITERALS = (b"Failmode:", b"F-Set", b"F-Clr", b"RT-P activate!")
UPTIME = re.compile(r"^[0-9]+(?:\.[0-9]+)? [0-9]+(?:\.[0-9]+)?$")
GC_START = re.compile(r"^\[GC_INFO\] GC_Start #(\d+): Gen\((\d+)\), Time\((\d+) ms\), Reason\((\d+)\)$")
GC_END = re.compile(r"^\[GC_INFO\] GC_End #(\d+): Gen\((\d+)\), Time\((\d+) ms\)$")

class Rejected(ValueError): pass
def need(ok, why):
    if not ok: raise Rejected(why)
def digest(raw): return hashlib.sha256(raw).hexdigest()

def no_duplicate_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value: raise Rejected("duplicate JSON key: " + key)
        value[key] = item
    return value

def json_object(text, label):
    try: value = json.loads(text, object_pairs_hook=no_duplicate_object)
    except (json.JSONDecodeError, UnicodeDecodeError) as e: raise Rejected(label + ": invalid JSON") from e
    need(type(value) is dict, label + ": object required")
    return value

def gc_pairs(lines, label):
    need(len(lines) <= 32 and len(lines) % 2 == 0, label + ": GC count")
    need(len(lines) == len(set(lines)), label + ": duplicate GC line")
    for n in range(0, len(lines), 2):
        a, b = GC_START.fullmatch(lines[n]), GC_END.fullmatch(lines[n + 1])
        need(a is not None and b is not None, label + ": unknown GC line")
        need(a.group(1, 2) == b.group(1, 2), label + ": GC pair identity")
        need(int(b.group(3)) >= int(a.group(3)), label + ": GC time reversed")

def validate_outcome(o):
    keys = {"Stage","Steps","Opened","Claimed","Released","Closed","Accepted","OutCount","InCount","DataBase64","DataSha256"}
    need(set(o) == keys and o["Stage"] == "complete", "native shape/stage")
    for key in ("Opened","Claimed","Released","Closed","Accepted"): need(o[key] is True, "native " + key)
    need(type(o["OutCount"]) is int and o["OutCount"] == 12 and
         type(o["InCount"]) is int and o["InCount"] == 3072, "native transfer counts")
    steps = o["Steps"]
    need(type(steps) is list and len(steps) == 6, "native step count")
    for n, (step, phase, expected) in enumerate(zip(steps, PHASES, VALUES)):
        need(type(step) is dict and set(step) == {"Phase","Value","Errno","Error"}, f"step {n}: shape")
        need(step["Phase"] == phase and type(step["Value"]) is int, f"step {n}: phase/value")
        need(step["Value"] >= 0 if expected is None else step["Value"] == expected, f"step {n}: result")
        need(type(step["Errno"]) is int and step["Errno"] == 0 and step["Error"] is None, f"step {n}: error")
    need(type(o["DataBase64"]) is str, "native data type")
    try: data = base64.b64decode(o["DataBase64"], validate=True)
    except (binascii.Error, ValueError) as e: raise Rejected("native data base64") from e
    need(len(data) == 3072 and o["DataSha256"] == digest(data), "native data length/hash")
    return data

def parse_stdout(raw):
    need(0 < len(raw) <= 65536, "stdout size")
    try: text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as e: raise Rejected("stdout UTF-8") from e
    need(text.endswith("\n"), "stdout final newline")
    lines = text.splitlines()
    need(len(lines) >= 7 and lines[0] == BOOT and UPTIME.fullmatch(lines[1]), "stdout prefix")
    need(json_object(lines[2], "selftest") == SELFTEST, "selftest values")
    active = [n for n,x in enumerate(lines) if x == "ACTIVE_READ_BEGIN"]
    exits = [n for n,x in enumerate(lines) if x.startswith("HELPER_EXIT=")]
    need(len(active) == len(exits) == 1, "marker counts")
    ai, ei = active[0], exits[0]
    need(ai >= 3 and ei >= ai + 2 and ei == len(lines)-2, "marker ordering")
    need(lines[ei] == "HELPER_EXIT=0" and UPTIME.fullmatch(lines[-1]), "exit/end uptime")
    gc_pairs(lines[3:ai], "pre-read")
    inner = lines[ai+1:ei]
    js = [n for n,x in enumerate(inner) if x.startswith("{")]
    need(len(js) == 1, "native JSON count")
    oi = js[0]
    gc_pairs(inner[:oi], "pre-outcome"); gc_pairs(inner[oi+1:], "post-outcome")
    outcome = json_object(inner[oi], "native outcome")
    return outcome, validate_outcome(outcome), {"start_uptime_raw":lines[1],"end_uptime_raw":lines[-1],"gc_line_count":len(lines[3:ai])+len(inner)-1}

def blob(value, label):
    need(type(value) is dict and set(value) == {"data","encoding"} and value["encoding"] == "base64" and type(value["data"]) is str, label+": envelope")
    try: return base64.b64decode(value["data"], validate=True)
    except (binascii.Error, ValueError) as e: raise Rejected(label+": base64") from e

def validate_record(r, stdout):
    keys={"manifest_sha256","remote_stage","deployment_script_sha256","root_runner_sha256","request","calls","helper_stdout_sha256","cleanup_stdout"}
    need(type(r) is dict and set(r)==keys, "record keys")
    need(r["manifest_sha256"]==MANIFEST and r["deployment_script_sha256"]==WRAPPER and r["root_runner_sha256"]==RUNNER, "record pins")
    need(r["request"]==REQUEST and r["helper_stdout_sha256"]==digest(stdout), "record request/stdout hash")
    need(r["cleanup_stdout"]=="STAGE_ABSENT\n", "record cleanup")
    need(type(r["remote_stage"]) is str and re.fullmatch(r"/tmp/researcher-usb-rtblock-[0-9a-f]{32}",r["remote_stage"]), "stage name")
    need(type(r["request"]["length"]) is int, "record request length type")
    need(digest(RUNNER_PATH.read_bytes()) == RUNNER, "local root-runner pin")
    spec=importlib.util.spec_from_file_location("pinned_primary_log_root_runner",RUNNER_PATH)
    need(spec is not None and spec.loader is not None,"root-runner import spec")
    common=importlib.util.module_from_spec(spec); spec.loader.exec_module(common)
    calls=r["calls"]; need(type(calls) is list and len(calls)==16, "call count")
    for n,c in enumerate(calls):
        need(type(c) is dict and type(c.get("transport_exit")) is int and c.get("transport_exit")==0 and c.get("host_timeout") is False, f"call {n}: transport")
        need(blob(c.get("transport_stderr"),f"call {n} stderr")==b"", f"call {n}: transport stderr")
        wire=blob(c.get("transport_stdout"),f"call {n} stdout")
        response=c.get("response")
        need(json_object(wire,f"call {n} wire")==response and type(response) is dict, f"call {n}: envelope binding")
        need(response.get("authenticated") is True and type(response.get("uid")) is int and
             type(response.get("euid")) is int and response.get("uid")==response.get("euid")==0,
             f"call {n}: root identity")
        commands=response.get("commands"); need(type(commands) is list and len(commands)==1, f"call {n}: command count")
        cmd=commands[0]; need(type(cmd) is dict and cmd.get("exit_code")==0 and cmd.get("timed_out") is False and cmd.get("stderr")=="" and type(cmd.get("stdout")) is str, f"call {n}: command result")
        need(type(cmd.get("exit_code")) is int and type(c.get("command")) is str,
             f"call {n}: numeric/command types")
        try: common.validate_response(response,c["command"])
        except Exception as e: raise Rejected(f"call {n}: common response contract: {e}") from e
    need(calls[-2]["response"]["commands"][0]["stdout"].encode()==stdout, "execution stdout binding")
    need(calls[-1]["response"]["commands"][0]["stdout"]=="STAGE_ABSENT\n", "cleanup stdout binding")

def occurrences(data):
    answer=[]
    for literal in LITERALS:
        found=[]; start=0
        while True:
            at=data.find(literal,start)
            if at<0: break
            found.append(at); start=at+1
        if found: answer.append({"literal_ascii":literal.decode(),"offsets":found,"count":len(found)})
    return answer

def write_outputs(directory, result, data):
    finals=(directory/"parsed-result.json",directory/"returned-block.bin")
    temps=(directory/"parsed-result.json.tmp",directory/"returned-block.bin.tmp")
    for p in finals+temps: need(not p.exists() and not p.is_symlink(), "output exists: "+p.name)
    payloads=((temps[1],data),(temps[0],(json.dumps(result,indent=2,sort_keys=True)+"\n").encode()))
    made=[]
    try:
        for p,raw in payloads:
            fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600); made.append(p)
            with os.fdopen(fd,"wb") as f: f.write(raw); f.flush(); os.fsync(f.fileno())
        os.replace(temps[1],finals[1]); made.remove(temps[1])
        os.replace(temps[0],finals[0]); made.remove(temps[0])
    finally:
        for p in made:
            try: p.unlink()
            except FileNotFoundError: pass

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("capture_dir",type=Path); args=ap.parse_args()
    try:
        directory=args.capture_dir.resolve(strict=True); need(directory.is_dir(),"capture directory")
        rp,sp=directory/"record.json",directory/"stdout.txt"
        need(rp.is_file() and not rp.is_symlink() and sp.is_file() and not sp.is_symlink(),"record/stdout inputs")
        record_raw=rp.read_bytes(); stdout=sp.read_bytes(); record=json_object(record_raw,"record")
        validate_record(record,stdout); outcome,data,timing=parse_stdout(stdout)
        result={"schema":"primary-log-offline-parse-v1","accepted":True,"capture_dir":str(directory),"record_sha256":digest(record_raw),"stdout_sha256":digest(stdout),"returned_block_sha256":digest(data),"returned_block_length":len(data),"native_stage":outcome["Stage"],"native_out_count":outcome["OutCount"],"native_in_count":outcome["InCount"],**timing,"literal_occurrences":occurrences(data),"literal_search_scope":[x.decode() for x in LITERALS],"rt_p_activate_sink_qualified_as_primary_ring":False,"interpretation":"Only listed occurrences are positive byte-offset evidence in this sequential snapshot. Missing literals do not establish absence, timing, causality, or physical state. RT-P activate! is a raw literal search only; its logger sink is not qualified as this primary ring."}
        write_outputs(directory,result,data)
        print(json.dumps({"accepted":True,"returned_block_sha256":digest(data),"positive_literal_kinds":len(result["literal_occurrences"])})); return 0
    except (OSError,Rejected) as e:
        print(json.dumps({"accepted":False,"error":str(e)},sort_keys=True),file=sys.stderr); return 1
if __name__=="__main__": raise SystemExit(main())
