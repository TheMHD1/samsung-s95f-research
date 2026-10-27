#!/usr/bin/env python3
"""Offline reproducer for qd-sensing-entry-callers.md; never touches a TV."""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FILES = {
    "libave.so.0.1": (BASE / "binaries/libave.so.0.1", "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"),
    "tztv_frc_tcon_api.ko": (BASE / "binaries/tztv_frc_tcon_api.ko", "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6"),
    "qdf_tcon.ko": (BASE / "binaries/qdf_tcon.ko", "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"),
    "libdisplay-panel.so.0.1": (BASE / "binaries/libdisplay-panel.so.0.1", "6cf2a638ee97772f181847e55dd9d661d9620d2601d5e0ed227562dbfa0106e8"),
    "libdisplay-panel-impl-sec.so.0.1": (BASE / "binaries/libdisplay-panel-impl-sec.so.0.1", "40df6d6e83da608e47d0143c268a964d97fddc7010972b5842f0e21f9b058ca4"),
    "libdisplay-panel-init.so.0.1": (BASE / "binaries/libdisplay-panel-init.so.0.1", "d90147178b8f3081b442d31ebf7808aa2dfd0474f924ba33d72c016ee03d08ea"),
}


def check_hashes() -> None:
    for label, (path, expected) in FILES.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        status = "OK" if actual == expected else "MISMATCH"
        print(f"{status:8} {label} {actual}")
        if status != "OK":
            raise SystemExit(f"refusing to decode unexpected {label}")


def run(*args: str) -> None:
    print("\n$", " ".join(args))
    subprocess.run(args, check=True)


def jump_targets(api_module: Path) -> None:
    # ELF64 little endian: .rodata section starts at file offset 0x? Find it
    # with readelf-less parsing is needlessly brittle, so use pyelftools only
    # for this offline table lookup.
    from elftools.elf.elffile import ELFFile

    with api_module.open("rb") as fh:
        elf = ELFFile(fh)
        rodata = elf.get_section_by_name(".rodata")
        data = rodata.data()
        print("\nTCON_Request jump table (.rodata+0x6a0; base .text+0xe804):")
        for op in (9, 15):
            offset = 0x6A0 + (op - 1) * 2
            displacement = int.from_bytes(data[offset : offset + 2], "little", signed=True)
            target = 0xE804 + displacement * 4
            slot = 0x350 if op == 9 else 0x360
            print(f"op={op:2} jump=0x{target:x} interface+0x{slot:x}")


def thumb_disassembly(libave: Path) -> None:
    """Use Capstone, rather than requiring a cross-architecture objdump."""
    from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile

    with libave.open("rb") as fh:
        elf = ELFFile(fh)
        section = elf.get_section_by_name(".text")
        blob, base = section.data(), section["sh_addr"]
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("\nlibave Thumb disassembly (the two request constructors):")
    for start, stop in ((0x25BE04, 0x25BE30), (0x25BEA0, 0x25BECC)):
        print(f"-- 0x{start:x}..0x{stop:x}")
        for insn in decoder.disasm(blob[start - base : stop - base], start):
            print(f"{insn.address:08x}: {insn.mnemonic:7} {insn.op_str}")


def display_panel_slots(panel: Path) -> None:
    """Print the two facade tail-dispatch ranges from the copied PPI library."""
    from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile

    with panel.open("rb") as fh:
        elf = ELFFile(fh)
        section = elf.get_section_by_name(".text")
        blob, base = section.data(), section["sh_addr"]
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("\nlibdisplay-panel facade wrappers (backend slots +0x2c/+0x30):")
    for name, start in (("set_elsensing", 0x46EF5BB4), ("set_offsensing", 0x46EF5C9C)):
        print(f"-- {name} @ 0x{start:x}")
        for insn in decoder.disasm(blob[start - base : start - base + 0x60], start):
            print(f"{insn.address:08x}: {insn.mnemonic:7} {insn.op_str}")


def display_panel_impl_setters(impl: Path) -> None:
    """Show the two implementation methods that dispatch to libave imports."""
    from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile

    with impl.open("rb") as fh:
        elf = ELFFile(fh)
        section = elf.get_section_by_name(".text")
        blob, base = section.data(), section["sh_addr"]
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("\nimpl-sec methods (PLT/GOT bridge to AVE setters):")
    for name, start in (("setElsensing", 0x64C4), ("setOffsensing", 0x651C)):
        print(f"-- {name} @ 0x{start:x}")
        for insn in decoder.disasm(blob[start - base : start - base + 0x48], start):
            print(f"{insn.address:08x}: {insn.mnemonic:7} {insn.op_str}")


def linked_bridge_evidence(path: Path, is_ave: bool) -> None:
    """Preserve callback population, relocations and direct public AVE edges."""
    from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile

    with path.open("rb") as fh:
        elf = ELFFile(fh)
        text = elf.get_section_by_name(".text")
        blob, base = text.data(), text["sh_addr"]
        print(f"\n# Linked bridge metadata: {path.name}")
        dynamic = elf.get_section_by_name(".dynamic")
        for tag in dynamic.iter_tags():
            if tag.entry.d_tag == "DT_NEEDED":
                print("DT_NEEDED", tag.needed)
        wanted = {0x5A55F0, 0x5A47C0} if is_ave else {0x1B26C, 0x1B04C, 0x1B348, 0x1B32C}
        for section_name in (".rel.dyn", ".rel.plt"):
            relocs = elf.get_section_by_name(section_name)
            if relocs is None:
                continue
            syms = elf.get_section(relocs["sh_link"])
            for reloc in relocs.iter_relocations():
                if reloc["r_offset"] in wanted:
                    symbol = syms.get_symbol(reloc["r_info_sym"])
                    print(section_name, hex(reloc["r_offset"]), symbol.name, hex(symbol["st_value"]))
        if is_ave:
            plt = elf.get_section_by_name(".plt")
            relocs = elf.get_section_by_name(".rel.plt")
            syms = elf.get_section(relocs["sh_link"])
            arm = Cs(CS_ARCH_ARM, CS_MODE_ARM)
            for index, reloc in enumerate(relocs.iter_relocations()):
                address = plt["sh_addr"] + 20 + 12 * index
                if address not in (0x8E628, 0x8BB98):
                    continue
                print("PLT", hex(address), "GOT", hex(reloc["r_offset"]), syms.get_symbol(reloc["r_info_sym"]).name)
                offset = address - plt["sh_addr"]
                for insn in arm.disasm(plt.data()[offset:offset + 12], address):
                    print(f"{insn.address:08x}: {insn.mnemonic:7} {insn.op_str}")
        ranges = ((0x28A4F4, 0x28A57C), (0x28A61C, 0x28A6A4)) if is_ave else (
            (0x7DF0, 0x7E80), (0x7E84, 0x7F14), (0x8BC0, 0x8C24))
        thumb = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for start, stop in ranges:
            print(f"-- {path.name} 0x{start:x}..0x{stop:x}")
            for insn in thumb.disasm(blob[start - base:stop - base], start):
                print(f"{insn.address:08x}: {insn.mnemonic:7} {insn.op_str}")
        if not is_ave:
            for address in (0x8DEC, 0x8DF0):
                print("literal", hex(address), hex(int.from_bytes(blob[address - base:address - base + 4], "little")))


def main() -> None:
    missing = [name for name in ("elftools", "capstone") if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit("Missing offline prerequisites: " + ", ".join(missing) +
                         ". On this controller run with PYTHONPATH=/tmp/tcon-capstone; "
                         "validated versions: pyelftools 0.33, capstone 5.0.7.")
    check_hashes()
    libave = FILES["libave.so.0.1"][0]
    api = FILES["tztv_frc_tcon_api.ko"][0]
    panel = FILES["libdisplay-panel.so.0.1"][0]
    impl = FILES["libdisplay-panel-impl-sec.so.0.1"][0]
    jump_targets(api)
    # These are inspection-only disassemblies of fixed ranges documented above.
    thumb_disassembly(libave)
    display_panel_slots(panel)
    display_panel_impl_setters(impl)
    linked_bridge_evidence(impl, False)
    linked_bridge_evidence(libave, True)
    run("aarch64-linux-gnu-objdump", "-dr", "-j", ".text", "--start-address=0x3b78", "--stop-address=0x3c04", str(api))
    run("aarch64-linux-gnu-objdump", "-dr", "-j", ".text", "--start-address=0xf028", "--stop-address=0xf278", str(api))
    run("aarch64-linux-gnu-objdump", "-dr", "-j", ".init.text", "--start-address=0", "--stop-address=0x600", str(FILES["qdf_tcon.ko"][0]))


if __name__ == "__main__":
    main()
