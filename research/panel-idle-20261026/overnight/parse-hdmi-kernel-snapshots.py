#!/usr/bin/env python3
"""Offline validator for bounded HDMI kernel-ring snapshots; never contacts TV."""
from __future__ import annotations
import argparse, base64, gzip, hashlib, json, math, os, re
from pathlib import Path

BOOT=re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
UP=re.compile(r"^([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)$")
DT=re.compile(rb"(?m)^\[\s*([0-9]+(?:\.[0-9]+)?)\]")
# Marker records can be supplied either directly from metadata or embedded in
# a trace line after the trace timestamp/prefix.
CAP=re.compile(rb"CAPTURE_(START|END)\s+utc=\S+\s+uptime=([0-9]+(?:\.[0-9]+)?)")

def need(ok,msg):
    if not ok: raise ValueError(msg)

def snap(raw:bytes,name:str):
    a=f"@@ KERNEL_{name}\n".encode(); z=f"@@ KERNEL_{name}_END\n".encode()
    need(raw.count(a)==1,f"expected exactly one {name} start marker")
    need(raw.count(z)==1,f"expected exactly one {name} end marker")
    lo=raw.index(a)+len(a); hi=raw.index(z); need(lo<hi,f"{name} markers out of order")
    body=raw[lo:hi]; need(body.endswith(b"\n"),f"{name} block lacks terminal newline")
    lines=body[:-1].split(b"\n"); need(len(lines)>=3 and lines[0] and lines[1],f"{name} lacks boot/uptime/payload")
    try: boot=lines[0].decode("ascii")
    except UnicodeDecodeError as e: raise ValueError(f"{name} boot is not ASCII") from e
    need(BOOT.fullmatch(boot) is not None,f"{name} boot malformed")
    try: up=lines[1].decode("ascii")
    except UnicodeDecodeError as e: raise ValueError(f"{name} uptime is not ASCII") from e
    m=UP.fullmatch(up); need(m is not None,f"{name} uptime malformed")
    u,i=(float(x) for x in m.groups()); need(math.isfinite(u) and math.isfinite(i) and u>=0 and i>=0,f"{name} uptime invalid")
    payload=b"".join(lines[2:]); need(payload and len(payload)%4==0 and re.fullmatch(rb"[A-Za-z0-9+/]*={0,2}",payload) is not None,f"{name} payload malformed")
    try: comp=base64.b64decode(payload,validate=True); ring=gzip.decompress(comp)
    except Exception as e: raise ValueError(f"{name} base64/gzip integrity failure: {e}") from e
    need(ring,f"{name} decompressed ring is empty")
    ts=[float(x) for x in DT.findall(ring)]; need(all(math.isfinite(x) and x>=0 for x in ts),f"{name} timestamp invalid")
    return {"boot_id":boot,"snapshot_uptime":u,"snapshot_idle":i,"encoded_bytes":len(payload),"gzip_bytes":len(comp),"ring_bytes":len(ring),"ring_sha256":hashlib.sha256(ring).hexdigest(),"timestamped_lines":len(ts),"ring_first_timestamp":min(ts) if ts else None,"ring_last_timestamp":max(ts) if ts else None,"ring_nonempty":True}

def window(meta:bytes|None):
    if meta is None:return {"meta_provided":False,"capture_start":None,"capture_end":None}
    found={}
    for k,v in CAP.findall(meta):
        key=k.decode(); need(key not in found,f"duplicate CAPTURE_{key}"); x=float(v); need(math.isfinite(x) and x>=0,f"CAPTURE_{key} invalid"); found[key]=x
    need(set(found) in (set(),{"START","END"}),"metadata has one-sided capture marker")
    if found: need(found["END"]>=found["START"],"capture end precedes start")
    return {"meta_provided":True,"capture_start":found.get("START"),"capture_end":found.get("END")}

def analyze(artifacts:Path,meta:Path|None=None):
    raw=artifacts.read_bytes(); s=snap(raw,"START"); e=snap(raw,"END")
    need(raw.index(b"@@ KERNEL_START\n")<raw.index(b"@@ KERNEL_START_END\n")<raw.index(b"@@ KERNEL_END\n")<raw.index(b"@@ KERNEL_END_END\n"),"kernel block ordering invalid")
    need(s["boot_id"]==e["boot_id"],"kernel snapshots have different boot IDs")
    w=window(meta.read_bytes() if meta else None); state="nonempty_only"
    if w["capture_start"] is not None:
        need(s["timestamped_lines"] and e["timestamped_lines"],"window supplied but snapshot lacks timestamps")
        state="temporally_bracketed_not_proven_complete" if s["ring_first_timestamp"]<=w["capture_start"] and e["ring_last_timestamp"]>=w["capture_end"] else "nonempty_not_window_bracketed"
    return {"artifacts":{"path":str(artifacts),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()},"meta":{"path":str(meta),"sha256":hashlib.sha256(meta.read_bytes()).hexdigest()} if meta else None,"start":s,"end":e,"capture_window":w,"requested_window_coverage":state,"limits":["valid nonempty gzip/base64 does not prove physical state or root transport acceptance","temporal bracketing does not prove complete kernel-ring event coverage"]}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("artifacts",type=Path);p.add_argument("--meta",type=Path);p.add_argument("--write-result",type=Path,required=True);a=p.parse_args()
    need(a.artifacts.is_file(),"artifacts input must be regular file");need(a.meta is None or a.meta.is_file(),"meta input must be regular file");need(not a.write_result.exists(),"refusing to overwrite result path")
    result=analyze(a.artifacts,a.meta); data=(json.dumps(result,indent=2,sort_keys=True)+"\n").encode();fd=os.open(a.write_result,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try: os.write(fd,data);os.fsync(fd)
    finally: os.close(fd)
    print(json.dumps({"accepted":True,"result":str(a.write_result),"requested_window_coverage":result["requested_window_coverage"]},sort_keys=True))
if __name__=="__main__":main()
