#!/usr/bin/env python3
"""Offline, hash-gated landmarks for dlsr-class-pq-route.md."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

try:
    from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile
except ModuleNotFoundError:
    sys.path.insert(0, "/tmp/tcon-capstone")
    from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "binaries/libave.so.0.1"
SHA = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"
DLSR_READ_REG = 0x007C037C


def require(value: bool, text: str) -> None:
    if not value:
        raise ValueError(text)


def main() -> None:
    require(hashlib.sha256(LIB.read_bytes()).hexdigest() == SHA, "libave hash mismatch")
    with LIB.open("rb") as stream:
        elf = ELFFile(stream)
        symtab = elf.get_section_by_name(".symtab")
        symbols = {s.name: (int(s["st_value"]), int(s["st_size"])) for s in symtab.iter_symbols()}
        expected_symbols = {
            "_ZN18RoseMVideoEnhancer14m_SetDlsrClassEv": (0xAD199, 2100),
            "_ZN18RoseMVideoEnhancer11m_SetPQDataEi15AVEScalerPath_k": (0xA6A31, 392),
            "_ZZN18RoseMVideoEnhancer12SetDlsrClassEjE14uiPreDlsrClass": (0x5A8DA8, 4),
        }
        for name, expected in expected_symbols.items():
            require(symbols.get(name) == expected, f"symbol mismatch: {name}")

        relocs = {}
        for section in elf.iter_sections():
            if section["sh_type"] not in {"SHT_REL", "SHT_RELA"}:
                continue
            table = elf.get_section(section["sh_link"])
            for rel in section.iter_relocations():
                relocs[int(rel["r_offset"])] = table.get_symbol(rel["r_info_sym"]).name
        require(relocs.get(0x59D020) == "_ZN18RoseMVideoEnhancer14m_SetDlsrClassEv", "base +0x428 binding")
        require(relocs.get(0x59CE28) == "_ZN18RoseMVideoEnhancer11m_SetPQDataEi15AVEScalerPath_k", "base +0x230 binding")

        plt = elf.get_section_by_name(".plt")
        relplt = elf.get_section_by_name(".rel.plt")
        dynsym = elf.get_section(relplt["sh_link"])
        plt_map = {int(plt["sh_addr"]) + 20 + i * 12: dynsym.get_symbol(r["r_info_sym"]).name for i, r in enumerate(relplt.iter_relocations())}
        require(plt_map.get(0x8FD80) == "_ZN16PictureVendorAPI14ReadPictureRegEjjPj", "ReadPictureReg PLT binding")

        def bytes_at(address: int, size: int) -> bytes:
            for segment in elf.iter_segments():
                if segment["p_type"] == "PT_LOAD" and int(segment["p_vaddr"]) <= address and address + size <= int(segment["p_vaddr"]) + int(segment["p_filesz"]):
                    stream.seek(int(segment["p_offset"]) + address - int(segment["p_vaddr"]))
                    return stream.read(size)
            raise ValueError(f"unmapped VA {address:#x}")

        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        found = {}
        for start, size in ((0xAD234, 0x130), (0xA3244, 0x60)):
            for instruction in md.disasm(bytes_at(start, size), start):
                found[instruction.address] = (instruction.mnemonic, instruction.op_str)
        expected_insns = {
            0xAD238: ("ldr.w", "r0, [r4, #0x114]"),
            0xAD23C: ("mov.w", "r1, #0x37c"),
            0xAD240: ("movt", "r1, #0x7c"),
            0xAD244: ("movs", "r2, #1"),
            0xAD246: ("blx", "#0x8fd80"),
            0xAD24E: ("cmp", "r0, #0"),
            0xAD254: ("cmp", "r5, #1"),
            0xAD25C: ("ldr.w", "r3, [r2, #0xb0]"),
            0xAD32E: ("ldr", "r3, [r4]"),
            0xAD330: ("movs", "r2, #0"),
            0xAD334: ("mov", "r0, r4"),
            0xAD336: ("ldr.w", "r3, [r3, #0x230]"),
            0xAD33A: ("blx", "r3"),
            0xAD346: ("str.w", "r3, [r2, #0xe4]"),
            0xAD354: ("str.w", "r3, [r2, #0xe8]"),
            0xA3292: ("str", "r4, [r6]"),
            0xA3296: ("str.w", "r4, [r3, #0xb0]"),
            0xA329C: ("ldr.w", "r3, [r3, #0x428]"),
        }
        for address, expected in expected_insns.items():
            require(found.get(address) == expected, f"instruction mismatch {address:#x}: {found.get(address)!r}")
        # The two Thumb immediate-building instructions produce one 32-bit
        # register address: mov.w lower 16 bits then movt upper 16 bits.
        require((0x37C | (0x7C << 16)) == DLSR_READ_REG, "combined DLSR read-register constant")

        for address, size, expected in ((0xAD198, 2100, "12fce62378deb2b0ba5a878b885ec1c3aa23c96b14647060db419232b269995e"), (0xA6A30, 392, "9b8f507b259ff069df1e23608092a94dadcb8fb447424e6c7b9469ba2c356867")):
            require(hashlib.sha256(bytes_at(address, size)).hexdigest() == expected, f"function bytes changed {address:#x}")
    print("PASS: base RoseM DLSR cache/read-gate/PQ-slot static landmarks")
    print("LIMIT: static reachability only; no live DLSR class, picture-register result, PQ write, or physical output is proved.")


if __name__ == "__main__":
    main()
