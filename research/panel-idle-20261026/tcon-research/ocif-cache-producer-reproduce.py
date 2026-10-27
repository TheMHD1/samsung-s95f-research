#!/usr/bin/env python3
"""Offline, hash-pinned landmarks for the sdp_ocl OCIF cache byte."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import struct

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
READER = HERE / "sdp-hdmi-cell-gate-reproduce.py"
READER_SHA256 = "8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67"
OCIF_PATH = ROOT / "overnight/serdes-ocif-copy-20261026/sdp_ocl.ko"
OCIF_SHA256 = "80b9e66f4129a31207f1eee8d7636d7565193ecf9ba87e3bded6196c5e1b02e7"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reader_source():
    require(hashlib.sha256(READER.read_bytes()).hexdigest() == READER_SHA256,
            "pinned Source reader hash")
    spec = importlib.util.spec_from_file_location("ocif_exact_reader", READER)
    require(spec is not None and spec.loader is not None, "Source reader loader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCES["ocif"] = (OCIF_PATH, OCIF_SHA256)
    return module


def exports(source):
    section = source.elf.get_section_by_name(".rela__ksymtab")
    require(section is not None, "ksymtab relocation section")
    symbols = source.elf.get_section(section["sh_link"])
    return [symbols.get_symbol(r["r_info_sym"]).name for r in section.iter_relocations()]


def setter_references(source):
    """Return relocation/direct-BL-B references, bounded to this exact ELF.

    A relocation can name the setter directly or name the .text section plus
    its 0x2030 addend.  The fixed-width scan deliberately does not depend on
    a disassembler stopping at an invalid/data word.  A raw branch target of
    0x2030 is only the setter in the logical .text section; other executable
    sections have independent zero-based address spaces.
    """
    relocations, unwind_relocations = [], []
    for section in source.elf.iter_sections():
        if section["sh_type"] not in ("SHT_REL", "SHT_RELA"):
            continue
        symbols = source.elf.get_section(section["sh_link"])
        for relocation in section.iter_relocations():
            symbol = symbols.get_symbol(relocation["r_info_sym"])
            target_section = (source.elf.get_section(symbol["st_shndx"]).name
                              if symbol["st_info"]["type"] == "STT_SECTION" else None)
            if (symbol.name == "sdp_serdes_is_available_set" or
                    (target_section == ".text" and relocation["r_addend"] == 0x2030)):
                destination = source.elf.get_section(section["sh_info"]).name
                # The sole .eh_frame FDE relocation is unwind metadata, not a
                # callable/data reference. Keep it explicit rather than hide
                # it from the whole-file census.
                if destination == ".eh_frame":
                    unwind_relocations.append((section.name, relocation["r_offset"]))
                else:
                    relocations.append((section.name, relocation["r_offset"]))
    branches = []
    scanned_words = 0
    for section in source.elf.iter_sections():
        if not (section["sh_flags"] & 0x4):
            continue
        raw = section.data()
        require(len(raw) % 4 == 0, "fixed-width executable section")
        for offset in range(0, len(raw), 4):
            word, = struct.unpack_from("<I", raw, offset)
            scanned_words += 1
            # A64 B/BL immediate: opcodes 0x14000000/0x94000000.
            if word & 0x7c000000 != 0x14000000:
                continue
            immediate = (word & 0x03ffffff) << 2
            if immediate & (1 << 27):
                immediate -= 1 << 28
            target = section["sh_addr"] + offset + immediate
            if section.name == ".text" and target == 0x2030:
                branches.append((section.name, section["sh_addr"] + offset,
                                 "bl" if word & 0x80000000 else "b"))
    return relocations, unwind_relocations, branches, scanned_words


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-disassembly", action="store_true")
    args = parser.parse_args()
    module = reader_source()
    source = module.Source("ocif")
    definitions = [
        ("sdp_ocif_lock_get", ".text", 0x90, 28),
        ("sdp_serdes_platform_suspend", ".text", 0xb8, 280),
        ("sdp_serdes_is_available_set", ".text", 0x2030, 36),
        ("sdp_serdes_platform_resume", ".text", 0x2d40, 512),
        ("sdp_serdes_probe", ".text", 0x2f40, 2068),
        ("sdp_serdes_do_ocl_pwr_down", ".text", 0x4ba0, 160),
        ("sdp_serdes_i2c_check", ".text", 0x4ce8, 528),
    ]
    spans, rows = [], {}
    for name, section, address, size in definitions:
        source.symbol(name, section, address, size)
        listing = source.listing(section, address, address + size)
        spans.append((name, section, address, address + size, listing))
        rows.update({(section, offset): value for offset, value in listing.items()})
    for lo, hi, label in [(0x3080, 0x30d0, "probe publication excerpt")]:
        listing = source.listing(".text", lo, hi)
        spans.append((label, ".text", lo, hi, listing))
        rows.update({(".text", offset): value for offset, value in listing.items()})

    for section, address, mnemonic, operands in [
        (".text", 0x94, "ldr", "x0, [x0]"),
        (".text", 0x9c, "ldrb", "w0, [x0, #0xb8]"),
        (".text", 0x2044, "strb", "w2, [x1, #0xb8]"),
        (".text", 0x2d5c, "ldr", "x20, [x0, #0x70]"),
        (".text", 0x2d70, "tbnz", "w0, #0, #0x2d94"),
        (".text", 0x2dec, "bl", "#0x2dec"),
        (".text", 0x2fb8, "strb", "wzr, [x28, #0xb8]"),
        (".text", 0x30c4, "str", "x28, [x22]"),
        (".text", 0x4bbc, "strb", "wzr, [x3, #0xb8]"),
        (".text", 0x4e04, "tbnz", "w19, #0x1f, #0x4d78"),
        (".text", 0x4e0c, "strb", "w0, [x22, #0xb8]"),
    ]:
        require(rows.get((section, address)) == (mnemonic, operands),
                f"landmark {section}+{address:x}")

    for section, offset, target, addend in [
        (".text", 0x90, ".bss", 0), (".text", 0x94, ".bss", 0),
        (".text", 0x2030, ".bss", 0), (".text", 0x2038, ".bss", 0),
        (".text", 0x30b8, ".bss", 0),
        (".text", 0x114, "sdp_serdes_do_ocl_pwr_down", 0),
        (".text", 0x2dec, "sdp_serdes_i2c_check", 0),
        (".text", 0x362c, "sdp_serdes_i2c_check", 0),
        (".text", 0x4de0, "__symbol_get", 0),
        (".text", 0x4e00, "__symbol_put", 0),
        (".text", 0x4d1c, ".rodata.str1.8", 0x1c88),
    ]:
        source.relocation(section, offset, target, addend)
    strings = source.elf.get_section_by_name(".rodata.str1.8").data()
    require(strings[0x1c70:].split(b"\0", 1)[0] == b"SDP_OCL_I2C_AckPolling",
            "AckPolling lookup literal")
    exported = exports(source)
    require(exported.count("sdp_ocif_lock_get") == 1, "getter export")
    require("sdp_serdes_is_available_set" not in exported, "setter must not be ksymtab export")
    require("__ksymtab_sdp_serdes_is_available_set" not in source.symbols,
            "setter ksymtab symbol absence")
    # x24 receives the AckPolling literal via 0x4d0c/0x4d14, then 0x4ddc
    # moves x24 to x0 immediately before the resolver call at 0x4de0.
    source.relocation(".text", 0x4d0c, ".rodata.str1.8", 0x1c70)
    source.relocation(".text", 0x4d14, ".rodata.str1.8", 0x1c70)
    require(rows.get((".text", 0x4ddc)) == ("mov", "x0, x24"),
            "AckPolling literal argument register")
    relocations, unwind_relocations, branches, scanned_words = setter_references(source)
    require(not relocations, "unexpected setter relocation reference")
    require(unwind_relocations == [(".rela.eh_frame", 0x468)],
            "setter unwind metadata identity")
    require(not branches, "unexpected direct setter branch")

    output = "".join(
        f"\n## {name} {section} {lo:#x}..{hi:#x}\n" +
        "".join(f"{address:08x}  {mnemonic:8} {operands}\n"
                for address, (mnemonic, operands) in listing.items())
        for name, section, lo, hi, listing in spans)
    path = HERE / "ocif-cache-producer.disasm"
    if args.write_disassembly:
        with path.open("x") as result:
            result.write(output)
    else:
        require(path.read_text() == output, "saved disassembly equality")
    print("PASS: exact OCIF cache getter, publication, corrected suspend/resume writers,"
          " dynamic AckPolling gate, and bounded setter-reference census.")
    print(f"Setter census scanned {scanned_words} fixed-width words in every executable section;")
    print("Landmarks support manual CFG/dataflow review only; no live value, callback binding,"
          " physical lock, panel behavior, or causation is established.")


if __name__ == "__main__":
    main()
