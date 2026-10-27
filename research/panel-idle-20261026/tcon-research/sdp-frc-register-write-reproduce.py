#!/usr/bin/env python3
"""Offline exact-ELF landmarks for the conditional SDP register-write route."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import struct

HERE = Path(__file__).resolve().parent
READER_HASH = "e4f195711e774ae432f43343c04e99e506dec89c0d2cf52cd228bc82a447d1c9"
SDP_HASH = "05dea2eaad34a23def837fb86d2f7a4e99ef630066ad6fed18d0cf55ba37063d"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-disassembly", action="store_true")
    args = parser.parse_args()
    reader = HERE / "monitor-input-status-provenance.py"
    assert hashlib.sha256(reader.read_bytes()).hexdigest() == READER_HASH
    spec = importlib.util.spec_from_file_location("source_reader", reader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HASHES["sdp_frc.ko"] = SDP_HASH
    s = module.Source("sdp_frc.ko")
    spans = []
    names = ["sdp_display_ex_proc", "dispay_coordinator_ex_proc",
             "display_coordinator_Init", "disp_coord_set",
             "get_instance_of_display_output_coordinator",
             "get_instance_of_display_output_coordinator.part.0",
             "display_output_coordinator_Init", "display_output_do_process",
             "get_display_device_frc", "get_instance_of_abstract_display_device_frc",
             "display_device_frc_Init", "dd_frc_send_trig_bypass", "sdp_frc_ex_proc",
             "sdp_frc_proc_reg_access", "sdp_frc_proc_s_reg", "wrap_write", "ft_write",
             "__devio_write", "devio_access_disable", "devio_access_enable",
             "__dummy_write", "__dummy_write_mask", "sdp_frc_acl_IS_ACCESSIBLE"]
    decoded = {}
    for name in names:
        sym = s.symbols[name]
        sec = s.elf.get_section(sym["st_shndx"]).name
        lo, hi = sym["st_value"], sym["st_value"] + sym["st_size"]
        rows = s.listing(sec, lo, hi)
        decoded.update({(sec, address): row for address, row in rows.items()})
        spans.append((name, sec, lo, hi, rows))
    for name, addr, size in [("sdp_display_ex_proc",0x1EFC8,20),
                              ("dispay_coordinator_ex_proc",0x22060,32),
                              ("display_output_coordinator_Init",0x22818,176),
                              ("sdp_frc_ex_proc",0x2258,4656),
                              ("__devio_write",0x1E680,12)]:
        s.symbol(name,addr,size)
    def check(sec, addr, mnemonic, operands):
        assert decoded[(sec,addr)] == (mnemonic,operands), (sec,hex(addr),decoded[(sec,addr)])
    for sec,addr,mn,op in [
        (".text",0x22070,"ldr","x3, [x3, #0x48]"),
        (".text",0x22074,"blr","x3"),
        (".text.unlikely",0x143C,"mov","w1, #4"),
        (".text",0x2201C,"str","x0, [x19]"),
        (".text",0x22878,"stp","x7, x6, [x19, #0x40]"),
        (".text",0x22880,"stp","x3, x2, [x19, #0x68]"),
        (".text",0x22894,"str","x0, [x19, #0xa0]"),
        (".text",0x22D48,"cmp","w20, #1"),
        (".text",0x22D50,"ldr","x0, [x21, #0x70]"),
        (".text",0x22D68,"ldr","x3, [x3, #0x30]"),
        (".text.unlikely",0x1C78,"str","x4, [x2, #0x30]"),
        (".text",0x291C,"ldr","w0, [x23]"),
        (".text",0x2920,"cmp","w24, #0x10"),
        (".text",0x2948,"cbnz","w0, #0x2e88"),
        (".text",0x2950,"cmp","w0, #1"),
        (".text",0x2954,"b.eq","#0x2ebc"),
        (".text",0x4DF0,"ldr","w2, [x1, #0xc]"),
        (".text",0x4DF8,"cmp","w2, #1"),
        (".text",0x4A14,"ldr","w1, [x19, #8]"),
        (".text",0x4A18,"mov","w2, w21"),
        (".text",0x4A40,"mov","w0, #0"),
        (".text",0xCDC0,"ldr","x0, [x0, #0x138]"),
        (".text",0xCDC4,"add","x0, x0, w3, uxtw"),
        (".text",0x1E790,"ldr","x2, [x2, #8]"),
        (".text",0x1E794,"blr","x2"),
        (".text",0x1E680,"dmb","oshst"),
        (".text",0x1E684,"str","w1, [x0]"),
        (".text",0x1E718,"add","x0, x0, #8"),
        (".text",0x1E730,"add","x0, x0, #0x28")]:
        check(sec,addr,mn,op)
    def rel(sec, addr, target, addend=0, section_target=False):
        rels = s.elf.get_section_by_name(".rela" + sec)
        linked = s.elf.get_section(rels["sh_link"])
        r, = [r for r in rels.iter_relocations() if r["r_offset"] == addr]
        symbol = linked.get_symbol(r["r_info_sym"])
        actual = s.elf.get_section(symbol["st_shndx"]).name if section_target else symbol.name
        assert (actual,r["r_addend"]) == (target,addend), (sec,hex(addr),actual,r["r_addend"])
    for sec,addr,name in [
        (".text",0x1EFD0,"dispay_coordinator_ex_proc"),
        (".text.unlikely",0x1440,"disp_coord_set"),
        (".text",0x22018,"get_instance_of_display_output_coordinator"),
        (".text.unlikely",0x1578,"display_output_coordinator_Init"),
        (".text",0x22890,"get_instance_of_abstract_display_device_frc"),
        (".text",0x25AFC,"sdp_frc_ex_proc"),
        (".text",0x2EC0,"sdp_frc_acl_IS_ACCESSIBLE"),
        (".text",0x2970,"sdp_frc_proc_reg_access"),
        (".text",0x4E00,"sdp_frc_proc_s_reg"),
        (".text",0x4A20,"wrap_write"), (".text",0xCDC8,"ft_write")]:
        rel(sec,addr,name)
    for sec,addr,target,addend in [
        (".text",0x2206C,".bss",0x8CC10),
        (".text",0x22848,".text",0x22D08),
        (".text",0x22858,".text",0x22608),
        (".text.unlikely",0x1C54,".text",0x25AC0),
        (".text",0x1E78C,".data",0x21650),
        (".data",0x21680,".text",0x1E680),
        (".data",0x21660,".text.unlikely",0x82C)]:
        rel(sec,addr,target,addend,True)
    rel(".data",0x21650,"allowed_access")
    deny = [(struct.unpack_from("<I",s.elf.get_section_by_name(".data").data(),o+8)[0],
             struct.unpack_from("<I",s.elf.get_section_by_name(".data").data(),o+12)[0])
            for o in range(0x1A90,0x1B08,24)]
    assert deny == [(0x18000,0x18F00),(0x19000,0x19F00),(0x20000,0x21000),
                    (0x21000,0x22000),(0x34140,0x34EF8)]
    assert 0x42B48 <= 0x5F000 and not any(lo <= 0x42B48 <= hi for lo,hi in deny)
    listing = "".join(
        f"\n## sdp_frc.ko {name} {sec} {lo:#x}..{hi:#x}\n" +
        "".join(f"{address:08x}  {mnemonic:8} {operands}\n"
                for address,(mnemonic,operands) in rows.items())
        for name,sec,lo,hi,rows in spans)
    path = HERE / "sdp-frc-register-write.disasm"
    if args.write_disassembly:
        with path.open("x") as out:
            out.write(listing)
    else:
        assert path.read_text() == listing
    print("PASS: exact SDP ELF; static coordinator/device callback initializers;")
    print("op2/write-envelope landmarks; wrap/ft/allowed+dummied access targets.")
    print("Manual flow review required. No live call, MMIO store or physical result observed.")


if __name__ == "__main__":
    main()
