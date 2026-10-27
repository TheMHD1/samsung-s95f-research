#!/usr/bin/env python3
"""Offline proof of the copied deviced power-state/EL standby-lock contract."""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile

BASE = Path(__file__).resolve().parents[1]
TARGET = BASE / "binaries/deviced"
EXPECTED = "2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2"
FUNCTIONS = (
    "gdbus_get_power_state", "pm_get_power_state", "pm_get_power_state_name",
    "pm_get_power_state_name_of", "pm_find_power_state", "state_tv_lock_init",
    "register_notifier", "device_notify", "_ZN12PowerAdapter13lockBGStandbyEii",
    "_ZN12PowerAdapter13getPowerStateEv", "lock_background_standby",
    "pm_lock_state", "pm_lock_timer_cb", "pm_unlock_timeout",
)


def main() -> None:
    digest = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    assert digest == EXPECTED, ("unexpected input", digest)
    print(f"input {TARGET.name} sha256 {digest}")
    with TARGET.open("rb") as handle:
        elf = ELFFile(handle)
        assert elf.elfclass == 32 and elf["e_machine"] == "EM_ARM"
        sections = list(elf.iter_sections())
        symtab = elf.get_section_by_name(".symtab")
        symbols = list(symtab.iter_symbols())
        by_name = {s.name: s for s in symbols}
        text_index = elf.get_section_index(".text")
        mappings = sorted((s["st_value"], s.name[:2]) for s in symbols
                          if s["st_shndx"] == text_index
                          and s.name.startswith(("$a", "$d", "$t")))

        def raw(address: int, count: int) -> bytes:
            for section in sections:
                base, length = section["sh_addr"], section["sh_size"]
                if section["sh_type"] != "SHT_NOBITS" and base <= address and address + count <= base + length:
                    return section.data()[address-base:address-base+count]
            raise ValueError(f"unbacked ELF address {address:#x}")

        def word(address: int) -> int:
            return struct.unpack("<I", raw(address, 4))[0]

        def cstr(address: int) -> str:
            data = bytearray()
            while True:
                char = raw(address, 1)
                if char == b"\0":
                    return data.decode("utf-8")
                data += char
                address += 1

        def pc_target(add_instruction: int, literal: int, expected: int) -> int:
            value = (add_instruction + 8 + word(literal)) & 0xffffffff
            assert value == expected, (hex(add_instruction), hex(value), hex(expected))
            print(f"PC add {add_instruction:#x} literal {literal:#x} -> {value:#x}")
            return value

        # Original PIE addends, not runtime absolute pointers. All nonzero name
        # and callback words below have R_ARM_RELATIVE relocation records.
        relative = {r["r_offset"] for r in elf.get_section_by_name(".rel.dyn").iter_relocations()
                    if r["r_info_type"] == 23}
        expected_rows = (
            (0, "start", (0, 0, 0, 0)),
            (1, "lcdon", (0x61b74, 0x60ef0, 0x60ce8, 0x600d4)),
            (2, "lcdoff", (0x61a80, 0x60c7c, 0x600ec, 0x60cc4)),
            (3, "standby", (0x61830, 0x616a0, 0x61580, 0x62230)),
            (4, "suspend", (0x63f24, 0x60b08, 0x62334, 0x6234c)),
            (5, "lowpower", (0x6201c, 0x64258, 0x6231c, 0x60138)),
            (6, "poweroff", (0x60104, 0x60118, 0x622ec, 0x62304)),
        )
        assert by_name["states"]["st_value"] == 0x1288e4
        assert by_name["states"]["st_size"] == 7 * 24
        print("\n## states table: 24-byte rows; callback roles not inferred")
        for index, (code, name, callbacks) in enumerate(expected_rows):
            address = 0x1288e4 + index * 24
            values = struct.unpack("<6I", raw(address, 24))
            assert values[0] == code and cstr(values[1]) == name
            assert values[2:] == callbacks
            for offset in (4, 8, 12, 16, 20):
                if values[offset // 4]:
                    assert address + offset in relative
            print(f"{address:#x} code={code} name={name} callbacks=" + ",".join(hex(v) for v in callbacks))

        print("\n## exact PC-relative references")
        pc_target(0x624dc, 0x62504, 0x12aeb8)  # current index
        pc_target(0x624e0, 0x62508, 0x1288e4)  # table
        pc_target(0x62574, 0x6259c, 0x12aeb8)
        pc_target(0x62578, 0x625a0, 0x1288e4)
        assert word(0x128220) == 0x3f5e8 and 0x128220 in relative
        pc_target(0x3f608, 0x3f65c, 0x66c4c)  # notifier type10 handler
        assert cstr(pc_target(0x66c68, 0x66d44, 0xee9e4)) == "standby"
        pc_target(0x66970, 0x66ae8, 0x65f08)  # timeout callback
        pc_target(0x65fd4, 0x66104, 0x677f4)  # deferred unlock callback

        # Exact method record bridges the public name to this callback; a
        # similarly named function alone would not establish registration.
        assert by_name["dbus_methods_display"]["st_value"] == 0x128644
        method = struct.unpack("<4I", raw(0x128674, 16))
        assert method == (0xf3278, 0, 0xf6d5c, 0x5dba4)
        assert cstr(method[0]) == "GetPowerState"
        assert all(0x128674 + offset in relative for offset in (0, 8, 12))
        print(f"public GetPowerState record 0x128674 -> callback {method[3]:#x}")

        print("\n## GLib PLT/GOT import identities")
        dynsym = elf.get_section_by_name(".dynsym")
        imports = {r["r_offset"]: dynsym.get_symbol(r["r_info_sym"]).name
                   for r in elf.get_section_by_name(".rel.plt").iter_relocations()}
        for plt, displacement, got, name in (
            (0x3e5fc, 0x48, 0x12a64c, "g_timeout_add"),
            (0x3e2a8, 0x280, 0x12a530, "g_idle_add_full"),
        ):
            assert plt + 8 + 0xec000 + displacement == got
            assert imports[got] == name
            print(f"PLT {plt:#x} -> GOT {got:#x} -> {name}")
            for insn in Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(raw(plt, 12), plt):
                print(f"{insn.address:08x}: {insn.mnemonic:8} {insn.op_str}")

        print("\n## bounded functions, honoring ARM/Thumb/data mapping symbols")
        for name in FUNCTIONS:
            symbol = by_name[name]
            start, size = symbol["st_value"] & ~1, symbol["st_size"]
            end = start + size
            assert size > 0
            print(f"\n{name} {start:#x}..{end:#x}")
            cuts = sorted({start, end} | {a for a, _ in mappings if start < a < end})
            for lo, hi in zip(cuts, cuts[1:]):
                state = [kind for address, kind in mappings if address <= lo][-1]
                if state == "$d":
                    print(f"{lo:08x}..{hi:08x}: <literal/data> {raw(lo, hi-lo).hex()}")
                    continue
                mode = {"$a": CS_MODE_ARM, "$t": CS_MODE_THUMB}[state]
                insns = list(Cs(CS_ARCH_ARM, mode).disasm(raw(lo, hi-lo), lo))
                assert sum(i.size for i in insns) == hi-lo, (name, hex(lo), hex(hi))
                for insn in insns:
                    print(f"{insn.address:08x}: {insn.mnemonic:8} {insn.op_str}")
    print("\nChecks passed. No network access or TV mutation performed.")


if __name__ == "__main__":
    main()
