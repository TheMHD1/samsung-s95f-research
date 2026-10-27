#!/usr/bin/env python3
"""Offline exact-site checks for conditional result writes in GetQDDisplayState."""
import hashlib
import io
import json
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from elftools.elf.elffile import ELFFile

BASE = Path(__file__).resolve().parents[1]
HASHES = {
    "deviced": "2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2",
    "libdeviced.so.1.0.3": "ea3ddbe08dbad2eb3d969d0df434be23afe69eb00921a7969191646e2d1bcb1a",
}


class Image:
    def __init__(self, name):
        self.name = name
        self.raw = (BASE / "binaries" / name).read_bytes()
        if hashlib.sha256(self.raw).hexdigest() != HASHES[name]:
            raise SystemExit(f"source hash mismatch: {name}")
        self.elf = ELFFile(io.BytesIO(self.raw))

    def read(self, address, size):
        for segment in self.elf.iter_segments():
            start = segment["p_vaddr"]
            if segment["p_type"] == "PT_LOAD" and start <= address and address + size <= start + segment["p_filesz"]:
                offset = segment["p_offset"] + address - start
                return self.raw[offset:offset + size]
        raise SystemExit(f"unmapped source address: {self.name}: {address:#x}")


def main():
    daemon = Image("deviced")
    client = Image("libdeviced.so.1.0.3")
    disassembler = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    expected = [
        (0x5c0c8, "bl", "#0x71520"),
        (0x715c8, "bl", "#0x73b68"),
        (0x71654, "mov", "r0, #4"),
        (0x71658, "bl", "#0x767c0"),
        (0x73b88, "b", "#0x75a68"),
        (0x73b98, "b", "#0x7e280"),
        (0x75a68, "mov", "r1, #4"),
        (0x75a6c, "b", "#0x74de8"),
        (0x7e280, "mov", "r1, #4"),
        (0x7e284, "b", "#0x7d87c"),
        (0x767e4, "b", "#0x77340"),
        (0x767f4, "b", "#0x7ecd0"),
        (0x77350, "bl", "#0x3d438"),
        (0x7ece4, "bl", "#0x3d438"),
    ]
    for address, mnemonic, operands in expected:
        instructions = list(disassembler.disasm(daemon.read(address, 4), address))
        if len(instructions) != 1 or (instructions[0].mnemonic, instructions[0].op_str) != (mnemonic, operands):
            raise SystemExit(f"instruction mismatch at {address:#x}")

    relocations = daemon.elf.get_section_by_name(".rel.plt")
    symbols = daemon.elf.get_section(relocations["sh_link"])
    names = [symbols.get_symbol(r["r_info_sym"]).name for r in relocations.iter_relocations() if r["r_offset"] == 0x12a060]
    if names != ["vconf_set_int"]:
        raise SystemExit(f"unexpected saved-result setter relocation: {names}")
    if daemon.read(0xfa684, 128).split(b"\0", 1)[0] != b"db/sysman/off_sensing_result":
        raise SystemExit("unexpected result key")

    strings = {
        0x444ddde0: b"org.tizen.system.deviced.display",
        0x444de0c8: b"GetQDDisplayState",
        0x444dde28: b"org.tizen.system.deviced",
        0x444dde04: b"/Org/Tizen/System/DeviceD/Display",
    }
    for address, value in strings.items():
        if client.read(address, len(value) + 1) != value + b"\0":
            raise SystemExit(f"unexpected client binding at {address:#x}")
    print(f"PASS: two source hashes, {len(expected)} exact ARM sites, setter relocation/key and client bindings")
    print("      Conditional reachability and surrounding classifier flow are manually reviewed; no TV query ran.")


if __name__ == "__main__":
    main()
