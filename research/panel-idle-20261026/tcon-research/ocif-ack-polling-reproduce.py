#!/usr/bin/env python3
"""Offline verifier for the exported OCIF AckPolling write transaction."""
from pathlib import Path
import argparse
import hashlib
import importlib.util


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
READER = HERE / "sdp-hdmi-cell-gate-reproduce.py"
READER_SHA256 = "8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67"
ACK = ROOT / "overnight/serdes-ack-copy-20261026/sdp_ocl_jp.ko"
ACK_SHA256 = "e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_reader():
    require(hashlib.sha256(READER.read_bytes()).hexdigest() == READER_SHA256,
            "pinned exact-ELF Source reader")
    spec = importlib.util.spec_from_file_location("ocif_ack_exact_reader", READER)
    require(spec is not None and spec.loader is not None, "reader loader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCES["ack"] = (ACK, ACK_SHA256)
    return module


def exports(source):
    section = source.elf.get_section_by_name(".rela__ksymtab")
    require(section is not None, "ksymtab relocations")
    symbols = source.elf.get_section(section["sh_link"])
    return [(r["r_offset"], symbols.get_symbol(r["r_info_sym"]).name)
            for r in section.iter_relocations()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-disassembly", action="store_true")
    args = parser.parse_args()
    module = load_reader()
    source = module.Source("ack")
    definitions = [
        ("sdp_ocl_platform_i2c_init", ".text.unlikely", 0x2c, 1116),
        ("SDP_OCL_I2C_AckPolling", ".text", 0x6898, 104),
    ]
    rows, spans = {}, []
    for name, section, offset, size in definitions:
        source.symbol(name, section, offset, size)
        listing = source.listing(section, offset, offset + size)
        rows.update({(section, address): value for address, value in listing.items()})
        spans.append((name, section, offset, offset + size, listing))
    ahb = source.symbols["ahb_adap"]
    require((source.elf.get_section(ahb["st_shndx"]).name, ahb["st_value"], ahb["st_size"]) ==
            (".bss", 0x10, 8), "ahb_adap identity")

    for section, address, mnemonic, operands in [
        (".text", 0x689c, "mov", "w1, w0"),
        (".text", 0x68a0, "mov", "w3, #0x10000"),
        (".text", 0x68b0, "add", "x2, sp, #0x2f"),
        (".text", 0x68b8, "ubfx", "x1, x1, #1, #0xf"),
        (".text", 0x68bc, "strb", "wzr, [sp, #0x2f]"),
        (".text", 0x68c0, "strh", "w1, [sp, #0x30]"),
        (".text", 0x68c4, "stur", "w3, [sp, #0x32]"),
        (".text", 0x68c8, "str", "x2, [sp, #0x38]"),
        (".text", 0x68d4, "add", "x1, sp, #0x30"),
        (".text", 0x68d8, "mov", "w2, #1"),
        (".text", 0x68e0, "bl", "#0x68e0"),
        (".text", 0x68e4, "mov", "w19, w0"),
        (".text", 0x68f0, "mov", "w0, w19"),
        (".text.unlikely", 0xec, "ldr", "x0, [x19, #8]"),
        (".text.unlikely", 0xf0, "ldr", "w0, [x0, #8]"),
        (".text.unlikely", 0xf4, "bl", "#0xf4"),
        (".text.unlikely", 0xf8, "str", "x0, [x19, #0x10]"),
    ]:
        require(rows.get((section, address)) == (mnemonic, operands),
                f"landmark {section}+{address:x}")
    for section, offset, target, addend in [
        (".text", 0x68ac, "ocl_i2c_mutex", 0),
        (".text", 0x68b4, "ocl_i2c_mutex", 0),
        (".text", 0x68d0, "ahb_adap", 0),
        (".text", 0x68dc, "ahb_adap", 0),
        (".text", 0x68cc, "mutex_lock", 0),
        (".text", 0x68e0, "i2c_transfer", 0),
        (".text", 0x68ec, "mutex_unlock", 0),
        (".text.unlikely", 0x40, ".bss", 0),
        (".text.unlikely", 0x44, ".bss", 0),
        (".text.unlikely", 0xf4, "i2c_get_adapter", 0),
    ]:
        source.relocation(section, offset, target, addend)
    require(exports(source).count((0xf0, "SDP_OCL_I2C_AckPolling")) == 1,
            "AckPolling ksymtab export")

    listing = "".join(
        f"\n## {name} {section} {lo:#x}..{hi:#x}\n" +
        "".join(f"{address:08x}  {mnemonic:8} {operands}\n"
                for address, (mnemonic, operands) in instructions.items())
        for name, section, lo, hi, instructions in spans)
    output = HERE / "ocif-ack-polling.disasm"
    if args.write_disassembly:
        with output.open("x") as result:
            result.write(listing)
    else:
        require(output.read_text() == listing, "saved disassembly equality")
    print("PASS: exact exported AckPolling function, one-byte zero-write ABI layout,"
          " raw i2c_transfer return, mutex, and adapter-initialization landmarks.")
    print("This is static vendor-module evidence only: no callback invocation, bus transfer,"
          " adapter value, physical response, cache transition, or causal result was observed.")


if __name__ == "__main__":
    main()
