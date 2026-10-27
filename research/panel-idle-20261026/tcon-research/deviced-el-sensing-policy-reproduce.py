#!/usr/bin/env python3
"""Offline bounded evidence for deviced-el-sensing-policy.md; never contacts a TV."""
from __future__ import annotations
import hashlib
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
TARGET = BASE / "binaries" / "deviced"
SHA256 = "2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2"
RANGES = (
    ("ELSensing::start", 0x74A94, 0x294),
    ("ELSensing::init object layout", 0x74574, 0xA4),
    ("ELSensing::stop", 0x74FA0, 0x280),
    ("ELSensing::pixelRefreshRequestByUser", 0x73D50, 0xEC),
    ("ELSensing::onOffSensingByELSensingDone", 0x756F0, 0x1F4),
    ("ELSensing wrappers start/stop", 0x7A690, 0xD0),
    ("ELSensing terminal callbacks", 0x75220, 0x180),
    ("ELSensingY23::start", 0x7D394, 0x294),
    ("ELSensingY23::init object layout", 0x7CE74, 0xA4),
    ("ELSensingY23::stop", 0x7DA34, 0x280),
    ("ELSensingY23::pixelRefreshRequestByUser", 0x7C650, 0xEC),
    ("ELSensingY23::onSensingPrepared", 0x7D628, 0x1A0),
    ("ELSensingY23 wrappers start/stop", 0x80ED4, 0xD0),
    ("ELSensingY23 terminal callbacks", 0x7DCB4, 0x1A0),
    ("OledDevice get-result/cooling", 0x7A760, 0x21C),
    ("OledDeviceY23 get-result/cooling", 0x80FA4, 0x330),
    ("PowerAdapter::lockBGStandby", 0x7C254, 0x78),
)

def main() -> int:
    actual = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    print(f"sha256 {actual}")
    if actual != SHA256:
        print("unexpected binary; refusing to decode", file=sys.stderr)
        return 2
    try:
        from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
        from elftools.elf.elffile import ELFFile
    except ImportError:
        print("requires PYTHONPATH=/tmp/tcon-capstone (Capstone and pyelftools)", file=sys.stderr)
        return 3
    with TARGET.open("rb") as fh:
        elf = ELFFile(fh)
        text = elf.get_section_by_name(".text")
        assert text is not None
        blob, base = text.data(), text["sh_addr"]
        all_mappings = sorted((x["st_value"], x.name[:2]) for x in elf.get_section_by_name(".symtab").iter_symbols()
                              if x.name.startswith(("$a", "$d", "$t"))
                              and x["st_shndx"] == elf.get_section_index(".text"))
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    print("mode ARM (ELF32 ARM; named addresses are even; relevant mapping symbols are $a)")
    for label, start, length in RANGES:
        print(f"\n## {label} 0x{start:x}..0x{start+length:x}")
        # ELF mapping symbols delimit embedded literal pools. Decode only spans
        # marked $a, never present $d pool words as executable ARM instructions.
        mappings = sorted((a, name) for a, name in all_mappings if start <= a < start + length)
        cuts = [start] + [a for a, _ in mappings if a != start] + [start + length]
        for lo, hi in zip(cuts, cuts[1:]):
            state = None
            for a, name in all_mappings:
                if a <= lo:
                    state = name
            if state != "$a":
                print(f"{lo:08x}..{hi:08x}: <literal/data pool>")
                continue
            for insn in md.disasm(blob[lo-base:hi-base], lo):
                print(f"{insn.address:08x}: {insn.mnemonic:8} {insn.op_str}")
    print("\nDynamic-import evidence:")
    relocs = subprocess.check_output(["readelf", "-rW", str(TARGET)], text=True)
    lines = [line for line in relocs.splitlines() if "ppi_displaypanel_set_elsensing" in line]
    assert lines == ["0012a0d0  00003716 R_ARM_JUMP_SLOT        00000000   ppi_displaypanel_set_elsensing@libdisplay-panel.so.0"]
    print(lines[0])
    disasm = subprocess.check_output(["aarch64-linux-gnu-objdump", "-d", "-marm", str(TARGET)], text=True)
    for needle in ("0003d588 <ppi_displaypanel_set_elsensing@plt>:", "7a6e4:", "7a74c:", "80f28:", "80f90:"):
        assert needle in disasm, needle
        print("verified objdump label/instruction anchor:", needle)
    # The unrelocated vtable addends identify the actual ARM methods selected
    # by the virtual slots used in ELSensing::start. In the Itanium layout the
    # object vptr is base+8. Old start uses +0x30/+0x08; Y23 uses +0x2c/+0x08.
    with TARGET.open("rb") as fh:
        elf = ELFFile(fh)
        ro = elf.get_section_by_name(".data.rel.ro")
        assert ro is not None
        def word(address: int) -> int:
            fh.seek(ro["sh_offset"] + address - ro["sh_addr"])
            return int.from_bytes(fh.read(4), "little")
        assert word(0x128A58) == 0x7A9D4 and word(0x128A30) == 0x7A690
        assert word(0x128B14) == 0x81218 and word(0x128AF0) == 0x80ED4
        # PowerAdapter: base 0x128aa8, address point +8; start's +0x10 call
        # selects full-vtable offset +0x18.
        assert word(0x128AC0) == 0x7C254
    print("verified OledDevice/Y23 vtable start slots: turnOn then startELSensing")
    print("verified PowerAdapter call: lockBGStandby(int, int)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
