#!/usr/bin/env python3
"""Dry-default preparation for one fixed TCON selector-0x128 read.

There are no selector/command/setter arguments and no live target action is
implemented by default. A future lifecycle binding must remain one-shot.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "build-manifest.json"
RUNNER_MANIFEST = HERE / "runner-manifest.json"
NAMES = ("ManagedTconDutyRead.deps.json", "ManagedTconDutyRead.dll", "ManagedTconDutyRead.runtimeconfig.json")

class ContractError(ValueError): pass
def require(v, m):
    if not v: raise ContractError(m)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def contract():
    rm=json.loads(RUNNER_MANIFEST.read_text())
    require(rm.get("schema")=="managed-tcon-duty-runner-v1", "runner manifest schema")
    require(rm.get("build_manifest_sha256")==digest(MANIFEST), "build manifest changed")
    m=json.loads(MANIFEST.read_text()); require(m.get("schema")=="managed-tcon-duty-read-build-v1", "build manifest schema")
    f=m.get("fixed_request",{}); require(f.get("device")=="/dev/tztv_tcon" and f.get("ioctl")=="0xc010749f" and f.get("operation_decimal")==19 and f.get("command_low_word")=="0x00000128", "fixed read ABI")
    files=m.get("files",{}); staged={}
    for n in NAMES:
        k="bin/Release/net6.0/"+n; require(re.fullmatch("[0-9a-f]{64}",files.get(k,"")) is not None,"payload hash")
        b=(HERE/k).read_bytes(); require(hashlib.sha256(b).hexdigest()==files[k],"payload mismatch"); staged[n]=b
    return m, staged

def parse_managed(text, pid):
    lines=text.splitlines(); require(lines[:1]==["QD_TCON_DUTY_READ_V1"] and lines[-1:]==["READ_COMPLETE"],"boundary")
    pairs=[x for x in lines if "=" in x]; require(all(x.count("=")==1 for x in pairs),"line shape")
    d=dict(x.split("=",1) for x in pairs)
    required={"ARCH","PTR_BYTES","STRUCT_BYTES","ENDIAN_LITTLE","OPERATION_OFFSET","OUTPUT_OFFSET","COMMAND_HIGH_OFFSET","COMMAND_LOW_OFFSET","ARGUMENT_COUNT","UID","EUID","PID_LIBC","PID_SYSCALL","DEVICE","OPEN_FLAGS","IOCTL_REQUEST","COMMAND_U64","WIRE_REQUEST_HEX","EXPECTED_RESPONSE_BYTES","PAYLOAD_BEFORE","OPEN_RETURN","OPEN_ERRNO","IOCTL_RETURN","IOCTL_ERRNO","PAYLOAD_AFTER","CLOSE_RETURN","CLOSE_ERRNO","CLASSIFICATION","RESULT_HEX","RESULT_U32","PHYSICAL_BRIGHTNESS_INFERRED","PACKAGED_RANGE_0_1023","PROFILE_RANGE_CLASSIFICATION"}
    require(set(d)==required and len(pairs)==len(required),"exact schema")
    fixed={"ARCH":"Arm","PTR_BYTES":"4","STRUCT_BYTES":"16","ENDIAN_LITTLE":"1","OPERATION_OFFSET":"0","OUTPUT_OFFSET":"4","COMMAND_HIGH_OFFSET":"8","COMMAND_LOW_OFFSET":"12","ARGUMENT_COUNT":"0","UID":"0","EUID":"0","PID_LIBC":str(pid),"PID_SYSCALL":str(pid),"DEVICE":"/dev/tztv_tcon","OPEN_FLAGS":"0x80002","IOCTL_REQUEST":"0xc010749f","COMMAND_U64":"0x0000f30000000128","WIRE_REQUEST_HEX":"f30000000128","EXPECTED_RESPONSE_BYTES":"4","PAYLOAD_BEFORE":"00000013,a55a5aa5,0000f300,00000128","OPEN_ERRNO":"0","IOCTL_RETURN":"0","IOCTL_ERRNO":"0","CLOSE_RETURN":"0","CLOSE_ERRNO":"0","CLASSIFICATION":"kernel_output_written","PHYSICAL_BRIGHTNESS_INFERRED":"0","PACKAGED_RANGE_0_1023":"1","PROFILE_RANGE_CLASSIFICATION":"within_packaged_low10_range"}
    require(all(d[k]==v for k,v in fixed.items()),"fixed output")
    q=re.fullmatch(r"00000013,([0-9a-f]{8}),0000f300,00000128",d["PAYLOAD_AFTER"]); require(q is not None and q.group(1)!="a55a5aa5","fresh output")
    v=int(q.group(1),16); require(v<=1023 and d["RESULT_HEX"]=="0x"+q.group(1) and d["RESULT_U32"]==str(v),"result")
    return {"classification":"kernel_output_written","duty_u32":v,"physical_brightness_inferred":False,"raw_fields":d}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--run",action="store_true"); p.add_argument("--reviewed",action="store_true"); p.add_argument("--output"); a=p.parse_args(); m,files=contract()
    if not a.run:
        require(not a.reviewed and a.output is None,"dry flags")
        print(json.dumps({"dry_run":True,"no_tv_or_device_calls":True,"one_shot":True,"retry_permitted":False,"fixed_selector":"0x128","fixed_request":"0xc010749f","build_manifest_sha256":digest(MANIFEST),"runner_manifest_sha256":digest(RUNNER_MANIFEST),"staged_files":{n:{"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()} for n,b in files.items()},"flash_guard":"No target-supported kernel firmware-update flag is currently established; live is fail-closed/deferred, and a quiet process list is not a substitute.","lifecycle":"status runner staging/cleanup/deadline pattern is a review reference only; no target stage/open/ioctl is enabled.","output_schema":"exact QD_TCON_DUTY_READ_V1 parser present","physical_state":"unobserved"},sort_keys=True)); return
    require(a.reviewed and a.output,"live flags")
    raise ContractError("Live deferred: no target-supported firmware flash guard and no reviewed lifecycle binding")
if __name__=="__main__": main()
