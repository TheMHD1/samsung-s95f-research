#!/usr/bin/env python3
"""Offline hash-gated write/table/replay landmarks, with a pinned ELF reader."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import struct

BASE = Path(__file__).resolve().parent
READER = BASE / "monitor-input-status-provenance.py"
assert hashlib.sha256(READER.read_bytes()).hexdigest() == "e4f195711e774ae432f43343c04e99e506dec89c0d2cf52cd228bc82a447d1c9"
spec = importlib.util.spec_from_file_location("monitor_provenance_reader", READER)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.HASHES["rosem_frc.ko"] = "c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-disassembly", action="store_true")
    args = parser.parse_args()
    ave, api, rose = (reader.Source(n) for n in
                     ("libave.so.0.1", "tztv_frc_tcon_api.ko", "rosem_frc.ko"))
    spans = []
    def check(src, section, lo, hi, expected, thumb=False):
        rows = src.check(section,lo,hi,expected,thumb)
        spans.append((src,section,lo,hi,rows))
    ave.symbol("_Z17ave_frc_write_i2cjj",0x243DB5,308)
    assert ave.plt[0x90680] == "_Z9frc_ioctlmPv"
    check(ave,".text",0x243DB4,0x243EA8,[
        (0x243DE4,"ldr","r3, [r3, #0x20]"),(0x243DE6,"cmp","r3, #1"),
        (0x243DEA,"moveq","r4, #0"),(0x243DEC,"beq","#0x243e04"),
        (0x243DF0,"movw","r0, #0x6623"),(0x243DF4,"movt","r0, #0xc008"),
        (0x243DF8,"strd","r5, r4, [r7, #4]"),(0x243DFC,"blx","#0x90680")],True)
    check(api,".text",0x195C,0x1974,[(0x1968,"b.eq","#0x2a54")])
    check(api,".text",0x2A54,0x2A7C,[(0x2A70,"bl","#0x2a70")])
    assert api.relocations[(".text",0x2A70)] == ("FRC_WriteI2CData",0)
    api.symbol("FRC_WriteI2CData",0x9438,128)
    check(api,".text",0x9438,0x94B8,[
        (0x9464,"ldr","x4, [x0, #0xf0]"),(0x9468,"cbz","x4, #0x9484"),
        (0x9474,"blr","x4"),(0x9484,"mov","w0, #0")])
    # pyelftools exposes an unnamed STT_SECTION symbol as an empty name.
    assert api.relocations[(".text",0x9458)] == ("",0x618)
    check(api,".text",0x7C48,0x7C54,[(0x7C4C,"str","x0, [x1]")])
    check(rose,".init.text",0x1FC,0x208,[(0x204,"str","x2, [x19, #0xf0]")])
    assert rose.relocations[(".init.text",0x1FC)] == ("RosemFrc_WriteI2CData",0)
    check(rose,".init.text",0x3BC,0x3D0,[(0x3C8,"bl","#0x3c8")])
    assert rose.relocations[(".init.text",0x3C8)] == ("map_frc_functions",0)
    check(rose,".text",0x618,0x77C,[
        (0x638,"ldr","w0, [x19, #0x14]"),(0x63C,"cbnz","w0, #0x6c8"),
        (0x648,"ldr","x1, [x19, #0x2a0]"),(0x650,"ldr","w2, [x19, #0x298]"),
        (0x684,"str","w21, [x3, x23]"),(0x694,"b.eq","#0x6fc"),
        (0x6A0,"b.eq","#0x6fc"),(0x6B0,"bl","#0x488")])
    check(rose,".text",0x488,0x55C,[
        (0x49C,"ldr","w19, [x2, #0x14]"),(0x4A0,"ldr","w2, [x2, #0x19c]"),
        (0x4A8,"cbz","w19, #0x4f0"),(0x4B4,"stp","wzr, w1, [sp, #0x20]"),
        (0x4BC,"stp","w0, w2, [sp, #0x28]"),(0x4C8,"mov","w2, #0x10"),
        (0x4CC,"mov","w0, #2"),(0x4D0,"blr","x3"),(0x4D4,"mov","w19, w0"),
        (0x4DC,"mov","w19, #0"),(0x51C,"mov","w19, #-1")])
    assert rose.relocations[(".text",0x4AC)] == ("tztv_frc_tcon_ext_cmd",0)
    check(rose,".text",0x7138,0x71A8,[
        (0x7150,"ldr","w1, [x19, #0xf4]"),(0x7158,"b.ne","#0x7780")])
    check(rose,".text",0x7780,0x7798,[
        (0x7780,"ldr","w0, [x19, #0x1ac]"),(0x7794,"b.eq","#0x79f8")])
    check(rose,".text",0x79F8,0x7A88,[
        (0x79F8,"mov","w0, #9"),(0x79FC,"str","w0, [x19, #0x298]"),
        (0x7A40,"str","x0, [x19, #0x2a0]"),(0x7A4C,"add","x6, x20, #0xf00"),
        (0x7A74,"ldr","w2, [x6, x24, lsl #2]"),(0x7A78,"str","w2, [x1, x5]")])
    check(rose,".text",0x7904,0x791C,[(0x7914,"str","x0, [x19, #0x100]")])
    rose.symbol("uiRosemQDRegisterAddress",0xF00,36)
    raw = rose.elf.get_section_by_name(".rodata").data()[0xF00:0xF24]
    selectors = struct.unpack("<9I",raw)
    assert [i for i,x in enumerate(selectors) if x == 0x42B48] == [3]
    check(rose,".text",0xD550,0xD6A4,[
        (0xD5E0,"str","w2, [x19, #0x14]"),(0xD5F8,"cmp","w21, #0x14"),
        (0xD5FC,"b.ne","#0xdc34"),(0xD63C,"ldr","x0, [x19, #0x100]"),
        (0xD644,"ldr","x1, [x19, #0x2a0]"),(0xD66C,"ldr","w0, [x19, #0x298]"),
        (0xD688,"ldr","w0, [x0, x23]"),(0xD68C,"ldr","w1, [x1, x23]"),
        (0xD690,"bl","#0x488")])
    check(rose,".text",0x5DD8,0x5F80,[
        (0x5E78,"ldr","x0, [x20, #0x100]"),(0x5E80,"ldr","x1, [x20, #0x2a0]"),
        (0x5EC0,"add","x1, x1, x22"),(0x5EC4,"bl","#0x780")])
    text=[]
    for src,sec,lo,hi,rows in spans:
        text.append(f"\n# {src.name} {reader.HASHES[src.name]} {sec} [{lo:#x},{hi:#x})")
        for addr,(mn,ops) in rows.items():
            extra=src.relocations.get((sec,addr))
            if mn in ("bl","blx") and ops.startswith("#"):
                extra=extra or src.plt.get(int(ops[1:],16))
            text.append(f"{addr:08x} {mn:10} {ops:40} {extra or ''}")
    rendered="\n".join(text)+"\n"
    out=BASE/"frc-duty-write-recovery.disasm"
    if args.write_disassembly:
        with out.open("x") as stream: stream.write(rendered)
    else:
        assert out.read_text()==rendered
    print("PASS: three exact ELFs; write ABI/static callback; PVCC cache gate; QD index3; Suspend read/Resume20 write landmarks")
    print("QD selectors:",",".join(hex(x) for x in selectors))
    print("Manual review still required; no live binding, call, transfer, acceptance or physical result established.")


if __name__ == "__main__":
    main()
