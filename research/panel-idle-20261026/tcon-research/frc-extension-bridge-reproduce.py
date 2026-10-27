#!/usr/bin/env python3
"""Offline bounded ELF evidence; manual branch models are not emulation."""
from pathlib import Path
import argparse
import hashlib
import importlib.util

HERE = Path(__file__).resolve().parent
READER_HASH = "e4f195711e774ae432f43343c04e99e506dec89c0d2cf52cd228bc82a447d1c9"


def endpoint(chip):
    # Manual simplification of the unsigned CMP/CCMP chain at 2e38..2e4c.
    chip &= 0xFFFFFFFF
    if chip in (3, 8, 9, 11, 12):
        return "NVT_TCON_ex_proc"
    return "MTK_ex_proc" if chip == 10 else "sdp_display_ex_proc"


def compare(a, b):
    # Only NZCV bits Z/C are consumed by this bounded conditional-compare chain.
    a &= 0xFFFFFFFF
    b &= 0xFFFFFFFF
    return a == b, a >= b


def conditional_chain_endpoint(chip):
    # Independent, manual transcription of CMP/CCMP/CSEL, not execution of ELF.
    chip &= 0xFFFFFFFF
    z, c = compare(chip - 8, 1)
    z, c = compare(chip - 11, 1) if c and not z else (False, False)  # NZCV=0
    z, c = compare(chip, 3) if c and not z else (True, False)  # NZCV=4
    if z:
        return "NVT_TCON_ex_proc"
    return "MTK_ex_proc" if chip == 10 else "sdp_display_ex_proc"


def bridge_model(initialized, callback_present, operation, resolved, result):
    """Manual ordinary-return model: (status, invokes_callback, initialized)."""
    if not initialized:
        if not resolved:
            return -1, False, False
        initialized, callback_present = True, True
        if operation == -1:
            return 0, False, True
    if not callback_present:
        return 0, False, True
    return result, True, True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-disassembly", action="store_true")
    args = parser.parse_args()
    reader = HERE / "monitor-input-status-provenance.py"
    assert hashlib.sha256(reader.read_bytes()).hexdigest() == READER_HASH
    spec = importlib.util.spec_from_file_location("source_reader", reader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = module.Source("tztv_frc_tcon.ko")
    source.symbol("resolve_symbol", 0x2A78, 136)
    source.symbol("_tztv_frc_tcon_ext_cmd", 0x2D78, 352)
    source.symbol("_tztv_get_chip_type", 0x8C, 52)
    assert source.elf.get_section(source.symbols["_tztv_get_chip_type"]["st_shndx"]).name == ".text.unlikely"
    for name, offset in [("g_chip_type", 0x30), ("func_init.43276", 0x78),
                         ("frc_tcon_ext_cmd.43275", 0x80)]:
        s = source.symbols[name]
        assert s["st_value"] == offset
        assert source.elf.get_section(s["st_shndx"]).name == ".bss"
    spans = []
    def check(sec, lo, hi, expected):
        rows = source.check(sec, lo, hi, expected)
        spans.append((sec, lo, hi, rows))
    check(".text", 0x2A78, 0x2B00, [
        (0x2A98,"bl","#0x2a98"), (0x2AB0,"bl","#0x2ab0"),
        (0x2ABC,"bl","#0x2abc"), (0x2AC4,"ldrsw","x0, [x19]"),
        (0x2AC8,"add","x19, x19, x0")])
    check(".text", 0x2D78, 0x2ED8, [
        (0x2DAC,"ldr","w20, [x19, #0x78]"),
        (0x2DF8,"cbz","w20, #0x2e30"), (0x2DFC,"ldr","x3, [x19, #0x80]"),
        (0x2E00,"cbz","x3, #0x2e98"), (0x2E04,"mov","w2, w23"),
        (0x2E08,"mov","x1, x22"), (0x2E0C,"mov","w0, w21"),
        (0x2E10,"blr","x3"), (0x2E14,"mov","w20, w0"),
        (0x2E30,"ldr","w0, [x19, #0x30]"),
        (0x2E38,"sub","w4, w0, #8"), (0x2E3C,"sub","w3, w0, #0xb"),
        (0x2E40,"cmp","w4, #1"), (0x2E44,"ccmp","w3, #1, #0, hi"),
        (0x2E48,"ccmp","w0, #3, #4, hi"), (0x2E4C,"b.ne","#0x2e84"),
        (0x2E58,"str","x0, [x19, #0x80]"), (0x2E6C,"cbnz","x0, #0x2eb8"),
        (0x2E74,"mov","w20, #-1"), (0x2E8C,"cmp","w0, #0xa"),
        (0x2E90,"csel","x24, x2, x1, eq"), (0x2EA0,"mov","w20, #0"),
        (0x2EC8,"str","w0, [x19, #0x78]"), (0x2ECC,"cmn","w21, #1"),
        (0x2ED0,"b.eq","#0x2e18"), (0x2ED4,"b","#0x2dfc")])
    check(".text.unlikely", 0x8C, 0xC0, [
        (0x94,"cbz","x0, #0xa0"), (0x98,"mov","w1, #0xe"),
        (0x9C,"str","w1, [x0]")])
    check(".text.unlikely", 0x2E78, 0x2EE0, [
        (0x2E90,"add","x19, x21, #0"),
        (0x2EC4,"add","x0, x19, #0x30"), (0x2ED4,"bl","#0x2ed4")])
    for sec, off, target in [
        (".text",0x2A98,"mutex_lock"), (".text",0x2AB0,"find_symbol"),
        (".text",0x2ABC,"mutex_unlock"), (".text",0x2E54,"resolve_symbol"),
        (".text.unlikely",0x2ED4,"_tztv_get_chip_type")]:
        assert source.relocations[(sec,off)] == (target,0)
    # Verify section identity as well as addend for unnamed STT_SECTION targets.
    def relocation(sec, address, target_section, addend):
        rels = source.elf.get_section_by_name(".rela" + sec)
        linked = source.elf.get_section(rels["sh_link"])
        rel, = [r for r in rels.iter_relocations() if r["r_offset"] == address]
        symbol = linked.get_symbol(rel["r_info_sym"])
        assert source.elf.get_section(symbol["st_shndx"]).name == target_section
        assert rel["r_addend"] == addend
    for sec, addr, target, addend in [
        (".text",0x2D80,".rodata",0x60),
        (".text",0x2D94,".bss",0), (".text",0x2DA0,".rodata.str1.8",0x2438),
        (".text.unlikely",0x2E8C,".bss",0)]:
        relocation(sec, addr, target, addend)
    for sec, off, value in [(".rodata",0x518,b"NVT_TCON_ex_proc\0"),
                            (".rodata",0x530,b"MTK_ex_proc\0"),
                            (".rodata.str1.8",0x2438,b"sdp_display_ex_proc\0")]:
        assert source.elf.get_section_by_name(sec).data()[off:off+len(value)] == value
    # Boundary examples include unsigned subtraction wraparound.
    for chip in list(range(256)) + [0x7FFFFFFF,0x80000000,0xFFFFFFFE,0xFFFFFFFF]:
        assert endpoint(chip) == conditional_chain_endpoint(chip)
    assert endpoint(14) == "sdp_display_ex_proc"
    assert bridge_model(False,False,2,False,0) == (-1,False,False)
    assert bridge_model(True,False,2,False,0) == (0,False,True)
    assert bridge_model(False,False,-1,True,77) == (0,False,True)
    assert bridge_model(True,True,-1,False,77) == (77,True,True)
    assert bridge_model(False,False,2,True,-5) == (-5,True,True)
    listing = "".join(
        f"\n## {source.name} {sec} {lo:#x}..{hi:#x}\n" +
        "".join(f"{address:08x}  {mnemonic:8} {operands}\n"
                for address,(mnemonic,operands) in rows.items())
        for sec,lo,hi,rows in spans)
    dest = HERE / "frc-extension-bridge.disasm"
    if args.write_disassembly:
        with dest.open("x") as out:
            out.write(listing)
    else:
        assert dest.read_text() == listing
    print("PASS: exact provider ELF, build chip14 initialization, three endpoint names,")
    print("resolver/cache/return landmarks; manual cold/warm counterexamples")
    print("No live pointer, invocation, bus transfer, panel state or diagnosis established.")


if __name__ == "__main__":
    main()
