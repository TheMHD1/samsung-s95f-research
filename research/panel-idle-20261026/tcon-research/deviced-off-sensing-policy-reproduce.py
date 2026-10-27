#!/usr/bin/env python3
"""Offline ARM disassembly for the copied deviced off-sensing policy. Never contacts a TV."""
from __future__ import annotations

import hashlib
import contextlib
import io
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DEVICE = BASE / "binaries" / "deviced"
SHA256 = "2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2"


def emit(out) -> None:
    if hashlib.sha256(DEVICE.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError("unexpected deviced SHA-256; refusing to decode")
    try:
        from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
        from elftools.elf.elffile import ELFFile
    except ImportError as exc:
        raise RuntimeError("requires PYTHONPATH=/tmp/tcon-capstone (capstone and pyelftools)") from exc

    # $a mapping symbols and the even function addresses identify ARM state,
    # not Thumb. Mapping symbols below explicitly exclude literal pools.
    ranges = (
        ("C wrapper: start by user", 0x76700, 0x76740),
        ("factory selector: off_sensing_init", 0x76558, 0x76700),
        ("GDBus off-sensing request handler", 0x5DEE0, 0x5E040),
        ("legacy start", 0x774E0, 0x776A8),
        ("legacy power suspend decision", 0x78AB8, 0x78FE4),
        ("legacy power-normal cleanup", 0x791AC, 0x7931C),
        ("legacy start by user", 0x79368, 0x79518),
        ("Y23 start", 0x7EEE0, 0x7F044),
        ("Y23 power suspend decision", 0x7FBA4, 0x7FFF8),
        ("Y23 power-normal cleanup", 0x80208, 0x80328),
        ("Y23 start by user", 0x80374, 0x8055C),
        ("TCON power on", 0x7B234, 0x7B2C0),
        ("TCON power off", 0x7B2D4, 0x7B360),
        ("OledDevice off-sensing wrappers", 0x7A834, 0x7A904),
        ("OledDeviceY23 off-sensing wrappers", 0x81078, 0x81148),
    )
    with DEVICE.open("rb") as fh:
        elf = ELFFile(fh)
        text = elf.get_section_by_name(".text")
        blob, base = text.data(), text["sh_addr"]
        mappings = sorted({(symbol["st_value"], symbol.name[:2])
                           for symbol in elf.get_section_by_name(".symtab").iter_symbols()
                           if symbol.name.startswith(("$a", "$d", "$t"))
                           and symbol["st_shndx"] == elf.get_section_index(".text")})
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    print(f"SHA256 OK {SHA256}", file=out)
    print("ELF32 ARM; selected $a mapping symbols; decoded CS_MODE_ARM", file=out)
    for name, start, end in ranges:
        print(f"\n## {name}: 0x{start:x}..0x{end:x}", file=out)
        cuts = sorted({start, end, *(address for address, _ in mappings if start < address < end)})
        for lo, hi in zip(cuts, cuts[1:]):
            state = next((mode for address, mode in reversed(mappings) if address <= lo), None)
            if state != "$a":
                print(f"{lo:08x}..{hi:08x}: <literal/data pool; mapping {state}>", file=out)
                continue
            for insn in cs.disasm(blob[lo - base : hi - base], lo):
                print(f"{insn.address:08x}: {insn.mnemonic:7} {insn.op_str}", file=out)

    # The ARM PLT has three instructions per import stub.  These two direct
    # targets land at the first ADD instruction of their stubs.  The ensuing
    # ADD/ADD/LDR sequences resolve to these GOT relocation offsets.
    # `ELFFile` is stream-backed; reopen after the earlier `.text` read.
    meta_handle = DEVICE.open("rb")
    meta = ELFFile(meta_handle)
    def vma_bytes(address: int, size: int) -> bytes:
        for segment in meta.iter_segments():
            if segment["p_type"] == "PT_LOAD" and segment["p_vaddr"] <= address < segment["p_vaddr"] + segment["p_filesz"]:
                offset = segment["p_offset"] + address - segment["p_vaddr"]
                with DEVICE.open("rb") as data:
                    data.seek(offset)
                    return data.read(size)
        raise RuntimeError(f"unmapped VMA 0x{address:x}")
    dynsym = meta.get_section_by_name(".dynsym")
    relplt = meta.get_section_by_name(".rel.plt")
    relocs = {dynsym.get_symbol(r.entry.r_info_sym).name: r.entry.r_offset
              for r in relplt.iter_relocations()}
    wanted = {
        "ppi_displaypanel_set_tcon_power": (0x3D558, 0x12A0C0),
        "ppi_displaypanel_set_offsensing": (0x3D5B8, 0x12A0E0),
    }
    print("\n## PLT/GOT resolution", file=out)
    for name, (plt, got) in wanted.items():
        assert relocs[name] == got
        code = vma_bytes(plt, 12)
        print(f"{name}: call target 0x{plt:x}; R_ARM_JUMP_SLOT GOT 0x{got:x}; bytes {code.hex()}", file=out)

    # In Itanium C++ ABI the vptr addresses the third vtable word: symbol+8.
    all_symbols = {s.entry.st_value: s.name for s in meta.get_section_by_name(".symtab").iter_symbols()}
    print("\n## relocated OledDevice virtual tables", file=out)
    for cls, table, count in (("OledDevice", 0x128A20, 26), ("OledDeviceY23", 0x128AE0, 21)):
        print(f"{cls}: table=0x{table:x}; vptr/address-point=0x{table + 8:x}", file=out)
        raw = vma_bytes(table, count * 4)
        for slot in range(2, count):
            addr = int.from_bytes(raw[slot * 4 : slot * 4 + 4], "little")
            print(f"  virtual +0x{(slot - 2) * 4:x}: 0x{addr:x} {all_symbols.get(addr, '?')}", file=out)

    print("\n## factory selector", file=out)
    print("off_sensing_init 0x76558: config_get_off_sensing_support 0xca5ec must be nonzero; config_get_product_year 0xcb69c == 0x17 selects Y23", file=out)
    print("legacy globals: off_sensing_=0x12af88, is_y23_model=0x12af90; Y23 globals: off_sensing_y23_=0x12af8c", file=out)
    meta_handle.close()


def main() -> int:
    try:
        if len(sys.argv) == 1:
            emit(sys.stdout)
        elif len(sys.argv) == 3 and sys.argv[1] == "--write-raw":
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                emit(buf)
            raw = buf.getvalue()
            Path(sys.argv[2]).write_text(raw)
            print(f"wrote {sys.argv[2]} SHA256 {hashlib.sha256(raw.encode()).hexdigest()}")
        else:
            raise RuntimeError("usage: deviced-off-sensing-policy-reproduce.py [--write-raw PATH]")
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
