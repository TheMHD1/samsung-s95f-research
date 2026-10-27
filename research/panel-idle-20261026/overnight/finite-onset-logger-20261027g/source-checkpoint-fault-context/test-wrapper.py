#!/usr/bin/env python3
"""Zero-target-I/O contract tests for run-once.py."""

import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def load_wrapper():
    spec = importlib.util.spec_from_file_location("fault_context_wrapper", HERE / "run-once.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


W = load_wrapper()


def check(value, why):
    if not value:
        raise AssertionError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rejected(callable_):
    try:
        callable_()
    except (ValueError, UnicodeError, json.JSONDecodeError):
        return True
    return False


def outcome():
    context = bytes((0x40 + i) & 0xff for i in range(64))
    rt = bytes((0x80 + i) & 0xff for i in range(256))
    specs = [("open", "LOCAL", 0, 9), ("claim", "LOCAL", 0, 0),
             ("context-header", "OUT", 12, 12), ("context-data", "IN", 64, 64),
             ("rt-header", "OUT", 12, 12), ("rt-data", "IN", 256, 256),
             ("release", "LOCAL", 0, 0), ("close", "LOCAL", 0, 0)]
    steps = [{"Name": name, "Direction": direction, "Expected": expected,
              "Count": count, "Errno": 0, "Error": None}
             for name, direction, expected, count in specs]
    value = {"Schema": "managed-usb-rt-fault-context-read-v1", "Stage": "complete",
             "ProtocolPhase": "ReadyForHeader", "Steps": steps, "Opened": True,
             "Claimed": True, "Released": True, "Closed": True, "Accepted": True,
             "ContextBase64": base64.b64encode(context).decode(),
             "ContextSha256": sha(context), "RtBase64": base64.b64encode(rt).decode(),
             "RtSha256": sha(rt), "PhysicalPictureObserved": False,
             "BusContentsAltered": False}
    return value, context, rt


def envelope(stdout, stderr=b"", exit_code=0):
    return ("META_BEGIN\n" + W.BOOT + "\n114322.76 0.00\n" + str(exit_code) + "\n" +
            str(len(stdout)) + "\n" + sha(stdout) + "\n" + str(len(stderr)) + "\n" +
            sha(stderr) + "\nINVENTORY_OK\nMETA_END\nSTDOUT_B64_BEGIN\n" +
            base64.b64encode(stdout).decode() + "\nSTDOUT_B64_END\nSTDERR_B64_BEGIN\n" +
            base64.b64encode(stderr).decode() + "\nSTDERR_B64_END\nEXECUTE_COMPLETE\n")


def main():
    tests = 0
    value, context, rt = outcome()
    raw = (json.dumps(value, separators=(",", ":")) + "\n").encode()
    parsed, got_context, got_rt, gc = W.parse_native(raw.decode())
    check(parsed["Accepted"] and got_context == context and got_rt == rt and gc == [], "native success")
    tests += 1

    with_gc = "[GC_INFO] bounded\n" + raw.decode()
    check(W.parse_native(with_gc)[3] == ["[GC_INFO] bounded"], "native GC classification")
    tests += 1

    for mutate in (
        lambda x: x.update(Stage="context-data"),
        lambda x: x.update(ProtocolPhase="Unknown"),
        lambda x: x.update(Accepted=False),
        lambda x: x.update(ContextBase64=base64.b64encode(context[:-1]).decode()),
        lambda x: x.update(RtSha256="0" * 64),
        lambda x: x["Steps"].__setitem__(3, dict(x["Steps"][3], Count=63)),
        lambda x: x["Steps"].__setitem__(1, dict(x["Steps"][1], Count=1)),
        lambda x: x["Steps"].append(dict(x["Steps"][-1])),
    ):
        bad = copy.deepcopy(value)
        mutate(bad)
        check(rejected(lambda bad=bad: W.parse_native(json.dumps(bad) + "\n")), "native rejection")
        tests += 1

    terminal, got_stdout, got_stderr = W.parse_envelope(envelope(raw))
    check(terminal["exit_code"] == 0 and got_stdout == raw and got_stderr == b"", "empty stderr envelope")
    tests += 1
    terminal, _, got_stderr = W.parse_envelope(envelope(raw, b"diagnostic", 1))
    check(terminal["exit_code"] == 1 and got_stderr == b"diagnostic", "failure envelope retention")
    tests += 1
    for bad in (
        envelope(raw).replace("INVENTORY_OK", "BAD", 1),
        envelope(raw).replace(sha(raw), "0" * 64, 1),
        envelope(raw).replace("EXECUTE_COMPLETE", "META_BEGIN", 1),
        envelope(raw) + "EXECUTE_COMPLETE\n",
        "noise\n" + envelope(raw),
        envelope(raw).replace("META_END\n", "META_END\nnoise\n", 1),
        envelope(raw) + "noise\n",
    ):
        check(rejected(lambda bad=bad: W.parse_envelope(bad)), "envelope rejection")
        tests += 1

    W.parse_selftest('{"selfTestsPassed":34,"targetOperations":0}\n')
    W.parse_selftest('[GC_INFO] bounded\n{"selfTestsPassed":34,"targetOperations":0}\n')
    tests += 2
    check(rejected(lambda: W.parse_selftest('{"selfTestsPassed":33,"targetOperations":0}\n')), "selftest count")
    check(rejected(lambda: W.parse_selftest('noise\n{"selfTestsPassed":34,"targetOperations":0}\n')), "selftest noise")
    tests += 2

    command_fragments = (W.dir_guard("/tmp/fixed"), W.file_guard("/tmp/fixed/a", 0),
                         W.exact_inventory("/tmp/fixed", ["a", "b"]))
    check(all("\\" not in fragment for fragment in command_fragments), "root backslash-free commands")
    check("test ! -L" in command_fragments[0] and '0:0:700' in command_fragments[0], "directory guard")
    check('0:0:600' in command_fragments[1] and 'wc -c' in command_fragments[1], "file guard")
    check("exit 91" in command_fragments[2], "inventory guard")
    tests += 3

    dry = subprocess.run([sys.executable, str(HERE / "run-once.py")], check=True,
                         text=True, capture_output=True)
    dry_value = json.loads(dry.stdout)
    check(dry_value["target_operations"] == 0 and dry_value["writes"] == 0, "dry target-free")
    check(dry_value["requests"] == [
        {"target": "0x101", "address": "0x47010f00", "length": 64},
        {"target": "0x101", "address": "0x47012400", "length": 256}], "dry geometry")
    tests += 1

    adapter = (HERE / "root-with-margin.py").read_bytes()
    check(sha(adapter) == W.ROOT_ADAPTER_SHA, "root adapter pin")
    source = (HERE / "Program.cs").read_text()
    check("01010000000F014740000000" in source, "context header source")
    check("010100000024014700010000" in source, "RT header source")
    check("Reset" not in source and "writes = 0" in source, "no reset/write source")
    tests += 2

    wrapper_source = (HERE / "run-once.py").read_text()
    inflight = 'record["target_operations"] = None'
    active = "envelope = call(command)"
    accepted = 'record["target_operations"] = 2'
    check(wrapper_source.index(inflight) < wrapper_source.index(active) <
          wrapper_source.index(accepted), "inflight operation accounting")
    tests += 1

    print(json.dumps({"wrapperTestsPassed": tests, "targetOperations": 0},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
