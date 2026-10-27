#!/usr/bin/env python3
"""Offline proof of HDMI-input handle FD fallbacks and the switch boundary."""

from pathlib import Path
import argparse
import hashlib
import re
import struct

from capstone import Cs, CS_ARCH_ARM, CS_ARCH_ARM64, CS_MODE_ARM, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WRAPPER = ROOT / "overnight/serdes-hdmi-control-copy-20261026/libhdmi-control.so.0.1"
INPUT = ROOT / "overnight/serdes-hdmi-input-impl-copy-20261026/libhdmi-input-control-impl-sec.so.0.1"
SWITCH = ROOT / "binaries/tztv_hdmi_switch.ko"
WRAPPER_SHA = "067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410"
INPUT_SHA = "5f822a6f297e1d24a65ad8dd4363a1dcf43b7d15f405fa7799ddf20f01410126"
SWITCH_SHA = "11d9c53a0e08300bb12b1cafd513e3fc6ee84ba1bcd434007e459dce70fa82b6"
OUT = HERE / "hdmi-input-kernel-control-boundary.disasm"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(elf, section_name, lo, hi, cs, label):
    section = elf.get_section_by_name(section_name)
    require(section is not None, label + " section")
    start = section["sh_addr"]
    require(start <= lo <= hi <= start + section["sh_size"], label + " bounds")
    raw = section.data()[lo - start : hi - start]
    ins = list(cs.disasm(raw, lo))
    require(sum(x.size for x in ins) == len(raw), label + " full decode")
    return ins


def rows(ins):
    return {x.address: (x.mnemonic, x.op_str) for x in ins}


def exact(row_map, address, mnemonic, operands):
    require(row_map.get(address) == (mnemonic, operands), f"landmark {address:#x}")


def symbol(elf, table_name, name, value, size):
    table = elf.get_section_by_name(table_name)
    require(table is not None, table_name)
    found = [x for x in table.iter_symbols() if x.name == name]
    require(len(found) == 1, name + " unique")
    require((found[0]["st_value"], found[0]["st_size"]) == (value, size), name + " identity")


def plt_identity(elf, address, expected):
    """Bind one decoded ARM PLT veneer to its exact .rel.plt symbol."""
    ins = decode(elf, ".plt", address, address + 12, Cs(CS_ARCH_ARM, CS_MODE_ARM), "PLT")
    got_rows = [(x.mnemonic, x.op_str) for x in ins]
    require(got_rows[0] == ("add", "ip, pc, #0, #12"), "PLT first add")
    m_high = re.fullmatch(r"ip, ip, #(0x[0-9a-f]+)", got_rows[1][1])
    m_low = re.fullmatch(r"pc, \[ip, #(0x[0-9a-f]+)\]!", got_rows[2][1])
    require(got_rows[1][0] == "add" and m_high is not None, "PLT second add")
    require(got_rows[2][0] == "ldr" and m_low is not None, "PLT load")
    got = address + 8 + int(m_high.group(1), 16) + int(m_low.group(1), 16)
    rel = elf.get_section_by_name(".rel.plt")
    require(rel is not None, "rel.plt")
    dyn = elf.get_section(rel["sh_link"])
    matches = [r for r in rel.iter_relocations() if r["r_offset"] == got]
    require(len(matches) == 1, "PLT GOT relocation")
    name = dyn.get_symbol(matches[0]["r_info_sym"]).name
    require(name == expected, f"PLT identity {expected}")
    return ins


def relocation(elf, section_name, offset, expected_name, expected_addend=None):
    rel = elf.get_section_by_name(".rela" + section_name)
    require(rel is not None, "relocation section " + section_name)
    symtab = elf.get_section(rel["sh_link"])
    found = [r for r in rel.iter_relocations() if r["r_offset"] == offset]
    require(len(found) == 1, f"relocation {section_name}+{offset:#x}")
    target = symtab.get_symbol(found[0]["r_info_sym"])
    name = target.name
    if not name and isinstance(target["st_shndx"], int):
        name = elf.get_section(target["st_shndx"]).name
    require(name == expected_name, f"relocation name {section_name}+{offset:#x}")
    if expected_addend is not None:
        require(found[0]["r_addend"] == expected_addend, f"relocation addend {section_name}+{offset:#x}")
    return found[0]


def listing(title, ins):
    return "\n## " + title + "\n" + "".join(
        f"{x.address:08x} {x.mnemonic:8} {x.op_str}\n" for x in ins
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-disassembly", action="store_true")
    args = ap.parse_args()

    require(sha(WRAPPER) == WRAPPER_SHA and WRAPPER.stat().st_size == 415124, "wrapper identity")
    require(sha(INPUT) == INPUT_SHA and INPUT.stat().st_size == 29650, "input implementation identity")
    require(sha(SWITCH) == SWITCH_SHA and SWITCH.stat().st_size == 87934, "switch identity")

    thumb = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    arm64 = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    spans = []

    with WRAPPER.open("rb") as fh:
        wrapper = ELFFile(fh)
        require(wrapper.elfclass == 32 and wrapper.little_endian, "wrapper ELF32 LE")
        symbol(wrapper, ".dynsym", "ppi_hdmi_input_control_create_handle", 0x47E61205, 328)
        # The symbol includes a literal pool from 0x47e6130c.  The preceding
        # mapping-compatible bounded code is decoded explicitly.
        w_ins = decode(wrapper, ".text", 0x47E61204, 0x47E6130C, thumb, "wrapper create code")
        w = rows(w_ins)
        for item in [
            (0x47E61208, "mov", "r6, r0"),
            (0x47E6120A, "mov", "r7, r1"),
            (0x47E6120E, "mov", "r8, r2"),
            (0x47E61210, "mov", "r5, r3"),
            (0x47E61248, "movs", "r0, #0x10"),
            (0x47E6124E, "mov.w", "r3, #-1"),
            (0x47E61252, "strd", "r3, r3, [r0]"),
            (0x47E61258, "strd", "r3, r3, [r0, #8]"),
            (0x47E6127A, "mov", "r1, r6"),
            (0x47E6127C, "mov", "r3, r8"),
            (0x47E6127E, "mov", "r2, r7"),
            (0x47E61280, "mov", "r0, r4"),
            (0x47E61282, "ldr.w", "r6, [ip, #4]"),
            (0x47E61286, "str", "r5, [sp]"),
            (0x47E61288, "ldr", "r5, [r6]"),
            (0x47E6128A, "blx", "r5"),
            (0x47E612DA, "mov", "r0, r4"),
        ]:
            exact(w, *item)
        w_malloc = plt_identity(wrapper, 0x47E33854, "malloc")
        w_backend = plt_identity(wrapper, 0x47E33890, "ppi_hdmi_input_control_get_backend_data")
        spans += [("wrapper_create", w_ins), ("wrapper_malloc_plt", w_malloc), ("wrapper_backend_plt", w_backend)]

    with INPUT.open("rb") as fh:
        inp = ELFFile(fh)
        require(inp.elfclass == 32 and inp.little_endian, "input ELF32 LE")
        symbol(inp, ".dynsym", "ppi_hdmi_input_control_create_handle_impl", 0x3441, 316)
        # Exact local mapping symbols delimit Thumb code and its literal pool.
        symtab = inp.get_section_by_name(".symtab")
        maps = [(x.name, x["st_value"]) for x in symtab.iter_symbols() if x.name in ("$t", "$d") and 0x3400 <= x["st_value"] < 0x3580]
        require(("$t", 0x3440) in maps and ("$d", 0x354C) in maps and ("$t", 0x357C) in maps, "input mapping boundaries")
        i_ins = decode(inp, ".text", 0x3440, 0x354C, thumb, "input create code")
        i = rows(i_ins)
        for item in [
            (0x3444, "mov", "r6, r3"),
            (0x3454, "ldr.w", "sb, [sp, #0x50]"),
            (0x3468, "ldr.w", "r1, [sb]"),
            (0x3498, "strd", "r8, r7, [r4]"),
            (0x349C, "ldr", "r3, [r6]"),
            (0x34A0, "beq", "#0x350c"),
            (0x34A2, "str", "r3, [r4, #8]"),
            (0x34A4, "ldr.w", "r3, [sb]"),
            (0x34AA, "beq", "#0x34b6"),
            (0x34AE, "str", "r3, [r4, #0xc]"),
            (0x34B8, "movw", "r1, #0x802"),
            (0x34BC, "cmp", "r3, #1"),
            (0x34BE, "beq", "#0x353c"),
            (0x34C4, "blx", "#0x115c"),
            (0x3502, "movs", "r0, #0"),
            (0x3504, "str", "r3, [r4, #0xc"),
            (0x350E, "movw", "r1, #0x802"),
            (0x3514, "blx", "#0x115c"),
            (0x3538, "ldr", "r3, [r6]"),
            (0x353A, "b", "#0x34a2"),
            (0x3540, "blx", "#0x115c"),
            (0x3544, "str.w", "r0, [sb]"),
        ]:
            # Capstone includes the closing bracket for this one operand.
            if item[0] == 0x3504:
                require(i.get(item[0]) == (item[1], "r3, [r4, #0xc]"), "landmark 0x3504")
            else:
                exact(i, *item)
        rodata = inp.get_section_by_name(".rodata")
        require(rodata is not None, "input rodata")
        for value, address in ((b"/dev/video28\0", 0x42D8), (b"/dev/video21\0", 0x4310), (b"/dev/video22\0", 0x4320)):
            at = rodata.data().find(value)
            require(at >= 0 and rodata["sh_addr"] + at == address, value.decode() + " literal")
            require(rodata.data().count(value) == 1, value.decode() + " unique")
        # Resolve the three PC-relative pathname loads, including the Thumb
        # high-register ADD rule whose PC is current-address+4.
        text = inp.get_section_by_name(".text")
        def signed_lit(address):
            off = address - text["sh_addr"]
            return struct.unpack_from("<i", text.data(), off)[0]
        require((0x34C2 + 4 + signed_lit(0x355C)) & 0xFFFFFFFF == 0x4310, "video21 literal target")
        require((0x3512 + 4 + signed_lit(0x3570)) & 0xFFFFFFFF == 0x42D8, "video28 literal target")
        require((0x353E + 4 + signed_lit(0x3578)) & 0xFFFFFFFF == 0x4320, "video22 literal target")
        i_open = plt_identity(inp, 0x115C, "open64")
        spans += [("input_create_impl", i_ins), ("input_open64_plt", i_open)]

    with SWITCH.open("rb") as fh:
        sw = ELFFile(fh)
        require(sw.elfclass == 64 and sw.little_endian and sw["e_type"] == "ET_REL", "switch ELF64 LE REL")
        symbol(sw, ".symtab", "hdmi_switch_set_ctrl", 0x15E8, 3540)
        symbol(sw, ".symtab", "hdmi_switch_vidioc_s_ext_ctrls", 0x23C0, 368)
        symbol(sw, ".symtab", "hdmi_switch_probe", 0x3998, 1064)
        dispatch_ins = decode(sw, ".text", 0x15E8, 0x1668, arm64, "switch dispatcher")
        dispatch = rows(dispatch_ins)
        for item in [
            (0x1600, "sub", "w0, w0, #0xa00, lsl #12"),
            (0x1604, "sub", "w0, w0, #0x998"),
            (0x1608, "cmp", "w0, #0x3d"),
            (0x160C, "b.hi", "#0x1650"),
            (0x1618, "ldrh", "w0, [x1, w0, uxtw #1]"),
            (0x1620, "add", "x0, x1, w0, sxth #2"),
            (0x1624, "br", "x0"),
            (0x1650, "mov", "w20, #-0x16"),
            (0x1654, "mov", "w0, w20"),
            (0x1664, "ret", ""),
        ]:
            exact(dispatch, *item)
        table = sw.get_section_by_name(".rodata").data()
        cid_base = (0xA00 << 12) + 0x998
        require(cid_base == 0x00A00998, "CID base")
        for cid in (0x00A009BC, 0x00A009BD):
            index = cid - cid_base
            require(index in (0x24, 0x25), "CID index")
            rel = int.from_bytes(table[index * 2 : index * 2 + 2], "little", signed=True)
            require(rel == 10 and 0x1628 + rel * 4 == 0x1650, f"CID default dispatch {cid:#x}")

        ioctl_ins = decode(sw, ".text", 0x23C0, 0x2470, arm64, "switch extended controls")
        ioctl_rows = rows(ioctl_ins)
        for item in [
            (0x23D8, "ldr", "w1, [x2]"),
            (0x23DC, "cmp", "w1, #0xa00, lsl #12"),
            (0x23FC, "ldr", "w1, [x2, #4]"),
            (0x2404, "cbz", "w1, #0x23e4"),
            (0x246C, "bl", "#0x15e8"),
        ]:
            exact(ioctl_rows, *item)

        probe_ins = decode(sw, ".text", 0x3A68, 0x3ABC, arm64, "switch video registration")
        probe = rows(probe_ins)
        for item in [
            (0x3A7C, "mov", "w2, #0x1c"),
            (0x3A80, "mov", "w1, #0"),
            (0x3A90, "ldr", "x0, [x27, #0x80]"),
            (0x3AB4, "bl", "#0x3ab4"),
            (0x3AB8, "mov", "w28, w0"),
            (0x3ABC, "cbnz", "w0, #0x3d14"),
        ]:
            # Decode range ends before 0x3abc; check the branch separately below.
            if item[0] != 0x3ABC:
                exact(probe, *item)
        probe_tail = decode(sw, ".text", 0x3ABC, 0x3AC0, arm64, "switch registration result")
        exact(rows(probe_tail), 0x3ABC, "cbnz", "w0, #0x3d14")
        relocation(sw, ".text", 0x3AB4, "__video_register_device", 0)
        relocation(sw, ".data", 0x288, ".text", 0x23C0)
        spans += [
            ("switch_set_ctrl_entry_and_default", dispatch_ins),
            ("switch_extended_controls", ioctl_ins),
            ("switch_video_registration", probe_ins + probe_tail),
        ]

    saved = "".join(listing(name, ins) for name, ins in spans)
    if args.write_disassembly:
        with OUT.open("x", encoding="utf-8") as fh:
            fh.write(saved)
    else:
        require(OUT.read_text(encoding="utf-8") == saved, "saved listing equality")

    print("PASS: exact handle construction, caller-provided/fallback FD paths, requested video minor 28, and conditional switch CID rejection.")
    print("No live handle FD, loaded input DSO, caller use, ioctl execution, or physical behavior is established.")


if __name__ == "__main__":
    main()
