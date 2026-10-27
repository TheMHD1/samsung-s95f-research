#!/usr/bin/env python3
"""Hash-gated, bounded static checks for qd-autodim-upstream.md.

Requires pyelftools and capstone.  Offline: reads only the two copied ELF files.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile

BASE = Path(__file__).resolve().parents[1]
AVE = BASE / "binaries/libave.so.0.1"
VE = BASE / "binaries/libvideoenhance.so.0"
EXPECTED = {
    AVE: "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777",
    VE: "3ce4e4741bad4883d7f097b7939e7b1f8853a354329b17398da496bf624228c9",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbols(elf: ELFFile):
    out = {}
    for sec in elf.iter_sections():
        if sec["sh_type"] in ("SHT_DYNSYM", "SHT_SYMTAB"):
            for sym in sec.iter_symbols():
                if sym.name:
                    out[sym.name] = sym
    return out


def relocs(elf: ELFFile):
    out = {}
    for sec in elf.iter_sections():
        if sec["sh_type"] != "SHT_REL":
            continue
        symtab = elf.get_section(sec["sh_link"])
        for rel in sec.iter_relocations():
            out[rel["r_offset"]] = symtab.get_symbol(rel["r_info_sym"]).name
    return out


def bytes_at(elf: ELFFile, fp, addr: int, size: int) -> bytes:
    for seg in elf.iter_segments():
        if seg["p_type"] != "PT_LOAD":
            continue
        lo, hi = seg["p_vaddr"], seg["p_vaddr"] + seg["p_filesz"]
        if lo <= addr and addr + size <= hi:
            fp.seek(seg["p_offset"] + addr - lo)
            return fp.read(size)
    raise AssertionError(f"unmapped file range {addr:#x}+{size:#x}")


def thumb_mnemonics(elf: ELFFile, fp, addr: int, size: int):
    # Function bounds come from ELF symbols.  We intentionally do not decode
    # trailing literal pools after those bounds.
    return [x.mnemonic for x in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(bytes_at(elf, fp, addr, size), addr)]


def main() -> None:
    for path, digest in EXPECTED.items():
        actual = sha256(path)
        assert actual == digest, f"hash mismatch: {path}: {actual}"
        print(f"OK hash {path.name} {actual}")

    with AVE.open("rb") as fp:
        elf = ELFFile(fp)
        sym, rel = symbols(elf), relocs(elf)
        checks = {
            # Itanium vtable address point = symbol + 8.
            sym["_ZTV11ave_dimming"]["st_value"] + 8 + 0x134: "_ZN11ave_dimming10SetAutoDimEi",
            sym["_ZTV9QDDimming"]["st_value"] + 8 + 0x124: "_ZN9QDDimming10SetAutoDimEi",
            0x5A0944 + 8 + 0x124: "_ZN9QDDimming10SetAutoDimEi",
            sym["_ZTV9QDDimming"]["st_value"] + 8 + 0x140: "_ZN16DimmingInterface9SetHomeUIEi",
        }
        for addr, target in checks.items():
            assert rel.get(addr) == target, (hex(addr), rel.get(addr), target)
            print(f"OK relocation {addr:#x} -> {target}")

        # Bounded opcode checks for the forwarding/store facts documented here.
        for addr, size, required in (
            (0x172A34, 0x78, {"str.w", "cbz"}),
            (0x150F78, 0xFE, {"blx", "ldrb"}),
            (0x151710, 0xFE, {"blx", "ldrb"}),
            (0x2A2AF8, 0x50, {"blx", "mov"}),
            (0x29E50C, 0x18, {"blx", "mov"}),
        ):
            decoded = set(thumb_mnemonics(elf, fp, addr, size))
            assert required <= decoded, (hex(addr), required - decoded)
            print(f"OK bounded Thumb decode {addr:#x}+{size:#x}")

        # Provider-table dataflow: literal -> auto-dim GOT -> r1 -> [r0,+0x98].
        assert rel[0x5A6FFC] == "impl_set_auto_dim_OnOff"
        assert rel[0x5A6FE4] == "impl_set_screen_protected_app_launched"
        provider = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(bytes_at(elf, fp, 0x2A08C6, 0x20), 0x2A08C6))
        exact = {(x.address, x.mnemonic, x.op_str) for x in provider}
        assert (0x2A08C6, "ldr.w", "r1, [pc, #0xc74]") in exact
        assert (0x2A08DE, "ldr", "r1, [r3, r1]") in exact
        assert (0x2A08E0, "str.w", "r1, [r0, #0x98]") in exact
        # 0x2a153c is the literal used by 0x2a08c6; r1 is later stored at +0x98.
        literal = int.from_bytes(bytes_at(elf, fp, 0x2A153C, 4), "little")
        assert literal == 0x2FFC
        assert 0x5A4000 + literal == 0x5A6FFC
        print("OK provider dataflow: literal 0x2a153c=0x2ffc -> GOT 0x5a6ffc -> table +0x98")

        inject = {(x.address, x.mnemonic, x.op_str) for x in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(bytes_at(elf, fp, 0x2AB1B2, 0x30), 0x2AB1B2)}
        assert (0x2AB1B2, "ldr", "r3, [r7]") in inject
        assert (0x2AB1B4, "ldr", "r0, [r3, #4]") in inject
        assert (0x2AB1B6, "blx", "#0x918c8") in inject
        assert (0x2AB1DA, "mov.w", "r5, #0x100") in inject
        assert (0x2AB1E0, "str", "r5, [r1]") in inject
        print("OK AVE injection table +4 and provider-version 0x100")

    with VE.open("rb") as fp:
        elf = ELFFile(fp)
        # The exported function's ELF extent includes its diagnostic literal
        # pool.  Executable instructions end at 0x46f44aa8.
        decoded = thumb_mnemonics(elf, fp, 0x46F44A1C, 0x8C)
        assert "bx" in decoded and "blx" in decoded
        print("OK bounded PPI client decode 0x46f44a1c+0x8c")
    print("PASS: static invariants only; runtime object/table/caller remain unknown.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
