#!/usr/bin/env python3
"""Offline source/landmark check; models are manual transcriptions, not emulation."""
from pathlib import Path
import argparse
import hashlib
import itertools
import struct

from capstone import Cs, CS_ARCH_ARM, CS_ARCH_ARM64, CS_MODE_ARM, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
HASHES = {
    "libave.so.0.1": "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777",
    "qdf_tcon.ko": "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63",
    "tztv_frc_tcon.ko": "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd",
    "tztv_frc_tcon_api.ko": "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6",
}


class Source:
    def __init__(self, name):
        self.name = name
        self.handle = (ROOT / "binaries" / name).open("rb")
        assert hashlib.sha256(self.handle.read()).hexdigest() == HASHES[name], name
        self.handle.seek(0)
        self.elf = ELFFile(self.handle)
        self.symbols = {
            s.name: s for section in self.elf.iter_sections()
            if section["sh_type"] == "SHT_SYMTAB" for s in section.iter_symbols()
            if s.name and not s.name.startswith("$")
        }
        self.plt = {}
        self.relocations = {}
        for section in self.elf.iter_sections():
            if section["sh_type"] not in ("SHT_REL", "SHT_RELA"):
                continue
            linked = self.elf.get_section(section["sh_link"])
            dest = self.elf.get_section(section["sh_info"]).name
            for rel in section.iter_relocations():
                sym = linked.get_symbol(rel["r_info_sym"])
                self.relocations[(dest, rel["r_offset"])] = (
                    sym.name, rel["r_addend"] if section["sh_type"] == "SHT_RELA" else 0)
        rel = self.elf.get_section_by_name(".rel.plt")
        if rel:
            linked = self.elf.get_section(rel["sh_link"])
            base = self.elf.get_section_by_name(".plt")["sh_addr"] + 20
            self.plt = {base + 12 * i: linked.get_symbol(r["r_info_sym"]).name
                        for i, r in enumerate(rel.iter_relocations())}

    def symbol(self, name, address, size):
        s = self.symbols[name]
        assert (s["st_value"], s["st_size"]) == (address, size), name

    def listing(self, section, start, end, thumb=False):
        s = self.elf.get_section_by_name(section)
        raw = s.data()[start - s["sh_addr"]:end - s["sh_addr"]]
        assert len(raw) == end - start
        decoder = Cs(CS_ARCH_ARM if thumb else CS_ARCH_ARM64,
                     CS_MODE_THUMB if thumb else CS_MODE_ARM)
        out = {i.address: (i.mnemonic, i.op_str) for i in decoder.disasm(raw, start)}
        assert out and sum(len(i.bytes) for i in decoder.disasm(raw, start)) == len(raw)
        return out

    def check(self, section, start, end, expected, thumb=False):
        rows = self.listing(section, start, end, thumb)
        for addr, mnemonic, operands in expected:
            assert rows.get(addr) == (mnemonic, operands), (
                self.name, hex(addr), rows.get(addr), (mnemonic, operands))
        return rows


def ave_fault(getter_return, output, mask=0xFFFFFFFF):
    """AVE replaces output with zero if getter return is signed-negative."""
    return -int(bool((0 if getter_return < 0 else output) & mask))


def qdf_fault(kind, power, callback_return, raw, debug=False, mock=0):
    """Nonnull caller; callback-return models provider or absent callback=-1."""
    if not power:
        return 0, 0
    value = (raw if kind == "err" else int(raw == 0)) if callback_return == 0 else 0
    return callback_return, (mock if debug else value)


def hsm(power, state, pmic, lpddr, elvdd, i2c):
    return (int(bool(power) and state != 1) | (int(pmic == 0) << 1)
            | (int(lpddr == 0) << 2) | (int(elvdd == 0) << 3) | (int(i2c == 0) << 4))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-disassembly", action="store_true")
    args = parser.parse_args()
    sources = {n: Source(n) for n in HASHES}
    ave, qdf, lower, api = (sources[n] for n in HASHES)
    spans = []
    def check(src, sec, lo, hi, expected=(), thumb=False):
        rows = src.check(sec, lo, hi, expected, thumb)
        spans.append((src, sec, lo, hi, rows))
    ave_specs = [
        ("_Z28ave_tcon_qd_err_detect_checkv", 0x268FFD, 140, 0x26906A, [
            (0x269018,"blx","#0x8ff90"), (0x26901E,"blt","#0x269040"),
            (0x269026,"ldr","r0, [r7]"), (0x269030,"rsbs","r0, r0, #0"),
            (0x26905E,"str","r4, [r7]"), (0x269064,"b","#0x269020")]),
        ("_Z28ave_tcon_qd_vdd_detect_checkv", 0x268F71, 140, 0x268FDE, [
            (0x268F8C,"blx","#0x8e19c"), (0x268F92,"blt","#0x268fb4"),
            (0x268F9A,"ldr","r0, [r7]"), (0x268FA4,"rsbs","r0, r0, #0"),
            (0x268FD2,"str","r4, [r7]"), (0x268FD8,"b","#0x268f94")]),
        ("_Z33ave_tcon_qd_tcon_hsm_status_checkv", 0x269151, 148, 0x2691C6, [
            (0x26916C,"blx","#0x8bfd0"), (0x269172,"blt","#0x26919a"),
            (0x26917C,"and","r0, r0, #0x18"), (0x2691BA,"str","r4, [r7]"),
            (0x2691C0,"b","#0x269174")]),
        ("_Z26ave_tcon_get_err_det_faultPi", 0x25D01D, 164, 0x25D0A4, [
            (0x25D040,"movs","r3, #0x1d"), (0x25D046,"blx","#0x8df5c"),
            (0x25D04C,"str","r3, [r4]")]),
        ("_Z26ave_tcon_get_vdd_det_faultPi", 0x25D0C1, 164, 0x25D148, [
            (0x25D0E4,"movs","r3, #0x1e"), (0x25D0EA,"blx","#0x8df5c"),
            (0x25D0F0,"str","r3, [r4]")]),
        ("_Z26ave_tcon_qd_get_hsm_statusPi", 0x25D9FD, 332, 0x25DB10, [
            (0x25DA36,"movs","r3, #0x23"), (0x25DA46,"blx","#0x8df5c"),
            (0x25DA58,"str","r3, [r6]")]),
    ]
    for name, start, size, end, expected in ave_specs:
        ave.symbol(name, start, size)
        check(ave,".text",start & ~1,end,expected,True)
    for address, name in [(0x8FF90,"_Z26ave_tcon_get_err_det_faultPi"),
                          (0x8E19C,"_Z26ave_tcon_get_vdd_det_faultPi"),
                          (0x8BFD0,"_Z26ave_tcon_qd_get_hsm_statusPi"),
                          (0x8DF5C,"_Z10tcon_ioctlmPv")]:
        assert ave.plt[address] == name
    qdf.symbol("QDFTcon_GetErrDetFault",0x5608,284)
    qdf.symbol("QDFTcon_GetVddDetFault",0x7B0,344)
    qdf.symbol("QDFTcon_GetHsmStatus",0x978,284)
    check(qdf,".text",0x5608,0x5724,[
        (0x5624,"ldr","w19, [x20, #4]"),(0x562C,"cbz","w19, #0x56ec"),
        (0x5640,"blr","x1"),(0x5644,"mov","w19, w0"),
        (0x5648,"cbnz","w0, #0x5684"),(0x5650,"cbnz","w1, #0x56b8"),
        (0x5664,"ldr","w1, [x20, #0x11c]"),(0x5668,"str","w1, [x21]"),
        (0x56B0,"mov","w1, #0"),(0x571C,"mov","w1, #0"),
        (0x5720,"b","#0x5668")])
    check(qdf,".text",0x7B0,0x908,[
        (0x7D8,"cbz","w19, #0x880"),(0x7EC,"blr","x1"),
        (0x7F4,"cbnz","w0, #0x8bc"),(0x7FC,"cbz","w19, #0x84c"),
        (0x800,"mov","w19, #0"),(0x808,"str","w22, [x20]"),
        (0x828,"ldr","w0, [x21, #0x2c]"),(0x870,"mov","w22, #1"),
        (0x8B0,"str","wzr, [x20]"),(0x8CC,"mov","w19, w22"),
        (0x8E8,"mov","w22, #0")])
    check(qdf,".text",0x978,0xA94,[
        (0x9A0,"ldr","w20, [x1, #4]"),(0x9A8,"ldr","w0, [x1, #0x10]"),
        (0x9B4,"ldp","w2, w0, [x1, #0x30]"),
        (0x9C4,"ldp","w2, w0, [x1, #0x38]"),
        (0x9E4,"lsl","w0, w24, #4"),(0x9E8,"orr","w0, w0, w25, lsl #3"),
        (0x9F8,"str","w1, [x19]"),(0xA40,"mov","w0, #0")])
    for lo, hi, name in [(0x1AF0,0x1C30,"_tztv_frc_tcon_read_err_det_status"),
                         (0x1C30,0x1D70,"_tztv_frc_tcon_read_vdd_det_status")]:
        lower.symbol(name,lo,hi-lo-4)
        check(lower,".text",lo,hi,[(lo+0xB4,"bl",f"#{hex(lo+0xB4)}"),
            (lo+0xC0,"bl",f"#{hex(lo+0xC0)}"),(lo+0xCC,"str","w1, [x21]"),
            (lo+0xD4,"mov","w0, w20")])
        for delta, name in [(0xB4,"gpiod_direction_input"),
                            (0xC0,"gpiod_get_raw_value_cansleep"),
                            (0xA0,"gpio_request")]:
            assert lower.relocations[(".text",lo+delta)][0] == name
    ro = api.elf.get_section_by_name(".rodata").data()
    for op, entry, slot in [(0x1D,0xF198,0x3D0),(0x1E,0xF1D8,0x3E0),
                            (0x23,0xEBA0,0x408)]:
        assert 0xE804 + 4*struct.unpack_from("<h",ro,0x6A0+(op-1)*2)[0] == entry
        check(api,".text",entry,entry+0x24,[
            (entry+0xC,"ldr",f"x1, [x0, #{hex(slot)}]"),
            (entry+0x14,"add","x0, x19, #4"),(entry+0x18,"blr","x1")])
    check(qdf,".init.text",0x180,0x340,[
        (0x1B0,"add","x20, x19, #0x3e0"),
        (0x328,"str","x5, [x19, #0x3d0]"),
        (0x2E8,"stp","x3, x1, [x20]"),(0x33C,"str","x0, [x19, #0x408]")])
    for addr,name in [(0x2C8,"QDFTcon_GetErrDetFault"),
                       (0x2D4,"QDFTcon_GetVddDetFault"),(0x31C,"QDFTcon_GetHsmStatus")]:
        assert qdf.relocations[(".init.text",addr)] == (name,0)
    # Counterexamples verify the consequences of the documented manual model.
    for kind in ("err","vdd"):
        for power, ret, raw in itertools.product((0,1),(-16,-1,0),(-22,-1,0,1)):
            status, value = qdf_fault(kind,power,ret,raw)
            actual = ave_fault(status,value)
            expected = 0 if not power or ret < 0 else -int(raw != 0 if kind == "err" else raw == 0)
            assert actual == expected
    assert qdf_fault("err",1,0,-22) == (0,-22)
    assert ave_fault(*qdf_fault("err",1,0,-22)) == -1
    assert ave_fault(*qdf_fault("vdd",1,0,-22)) == 0
    for fields in itertools.product((0,1,2),repeat=6):
        bits = hsm(*fields)
        assert ave_fault(0,bits,0x18) == -int(fields[4] == 0 or fields[5] == 0)
    text = []
    for src, sec, lo, hi, rows in spans:
        text.append(f"\n# {src.name} {HASHES[src.name]} {sec} [{lo:#x},{hi:#x})")
        for addr,(mn,ops) in rows.items():
            extra = src.relocations.get((sec,addr))
            if mn in ("bl","blx") and ops.startswith("#"):
                extra = extra or src.plt.get(int(ops[1:],16))
            text.append(f"{addr:08x} {mn:10} {ops:40} {extra or ''}")
    rendered = "\n".join(text) + "\n"
    output = Path(__file__).with_suffix(".disasm")
    if args.write_disassembly:
        with output.open("x") as stream:
            stream.write(rendered)
    else:
        assert output.read_text() == rendered, "disassembly differs"
    print("PASS: four exact ELFs; six AVE routines; QDF getters/provider/dispatch landmarks; manual-model counterexamples")
    print("Model checks do not execute or emulate the driver, establish live binding, or diagnose physical output.")


if __name__ == "__main__":
    main()
