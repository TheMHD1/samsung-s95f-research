#!/usr/bin/env python3
"""Offline, hash-guarded verifier for the copied maintenance IPC binaries."""
from __future__ import annotations
import argparse, hashlib, sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

EXPECTED={"binaries/libdeviced.so.1.0.3":"ea3ddbe08dbad2eb3d969d0df434be23afe69eb00921a7969191646e2d1bcb1a","binaries/deviced":"2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2"}
LIB={"qd_display_request_off_sensing_with_mode":(0x444a450c,436),"qd_display_request_off_sensing":(0x444a46c0,24),"qd_display_request_el_sensing":(0x444a46d8,596),"oled_is_burn_in_protection_in_progress":(0x444a492c,436)}
DAEMON={"gdbus_request_el_sensing":(0x5bf34,392),"el_sensing_request_start":(0x73944,84),"_ZN9ELSensing25pixelRefreshRequestByUserEv":(0x73d50,236),"_ZN9ELSensing24clearPixelRefreshRequestEv":(0x73e3c,148),"_ZN9ELSensing19onPowerOffRequestedEPi":(0x754bc,396)}
STRINGS=(b"org.tizen.system.deviced.display\0",b"/Org/Tizen/System/DeviceD/Display\0",b"org.tizen.system.deviced\0",b"RequestOffSensing\0",b"RequestELSensing\0",b"BurnInProtectionInProgress\0",b"db/sysman/el_sensing_poweroff\0")

def table(path, section):
    with path.open("rb") as f:
        t=ELFFile(f).get_section_by_name(section)
        if not t: raise RuntimeError("missing "+section)
        return {s.name:(s["st_value"],s["st_size"]) for s in t.iter_symbols()}

def vread(path, vaddr, count):
    """Read ELF virtual bytes; this is static evidence, never /proc memory."""
    with path.open("rb") as f:
        elf=ELFFile(f)
        for seg in elf.iter_segments():
            start, size=seg["p_vaddr"],seg["p_filesz"]
            if start <= vaddr and vaddr+count <= start+size:
                f.seek(seg["p_offset"]+vaddr-start); return f.read(count)
    raise RuntimeError("unmapped VMA %#x" % vaddr)

def u32(path, vaddr): return int.from_bytes(vread(path,vaddr,4),"little")

def arm(path, vaddr):
    ins=next(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(vread(path,vaddr,4),vaddr))
    return ins.mnemonic,ins.op_str

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("base",type=Path); a=p.parse_args()
    paths={n:a.base/n for n in EXPECTED}
    for n,path in paths.items():
        got=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "MISSING"
        print("SHA256",n,got)
        if got != EXPECTED[n]: print("STOP: unmatched evidence",file=sys.stderr); return 2
    lib=paths["binaries/libdeviced.so.1.0.3"]; daemon=paths["binaries/deviced"]
    for name,want in LIB.items():
        got=table(paths["binaries/libdeviced.so.1.0.3"],".dynsym").get(name); print("EXPORT",name,got); assert got==want
    for name,want in DAEMON.items():
        got=table(paths["binaries/deviced"],".symtab").get(name); print("SYMBOL",name,got); assert got==want
    blob=b"".join(x.read_bytes() for x in paths.values())
    for value in STRINGS:
        got=value in blob; print("STRING",value[:-1].decode(),got); assert got
    # qd_display_request_el_sensing: literal addresses and the *following*
    # ARM add-PC instruction values. PC is instruction address+8 in ARM mode.
    # These prove the exact mode-1 request tuple, not merely co-present strings.
    tuple_parts=((0x444a48f8,0x444a47ac,b"(i)"),(0x444a48fc,0x444a47c0,b"RequestELSensing"),(0x444a4900,0x444a47d8,b"org.tizen.system.deviced.display"),(0x444a4904,0x444a47dc,b"/Org/Tizen/System/DeviceD/Display"),(0x444a4908,0x444a47ec,b"org.tizen.system.deviced"))
    for literal, add, want in tuple_parts:
        target=(u32(lib,literal)+add+8)&0xffffffff
        got=vread(lib,target,len(want)+1).split(b"\0",1)[0]
        print("ADD-PC",hex(add),hex(target),got.decode()); assert got==want
    # Exact ARM instructions / values for the distinct local mode-0 power-off.
    assert arm(lib,0x444a481c)==("mov","r0, #0x4000002a")
    # Direct named callback edges and its power-off reason store.
    assert arm(daemon,0x754cc)==("bl","#0x73d50")
    assert arm(daemon,0x755d8)==("bl","#0x73e3c")
    assert arm(daemon,0x755e8)==("mov","r3, #0x4000002a")
    assert arm(daemon,0x755ec)==("str","r3, [r7]")
    print("PASS: static evidence matches audited pair; this script makes no IPC call.")
    return 0
if __name__=="__main__": raise SystemExit(main())
