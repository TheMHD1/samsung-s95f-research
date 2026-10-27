#!/usr/bin/env python3
"""Hash-gated, offline checks for frc-ioctl-6626-analysis.md.

Reads copied binaries and the retained trace only.  It never opens a device,
executes a target binary, or contacts the TV/network.  Static call relocations
are unresolved in copied kernel modules, so the checker validates instruction
and relocation landmarks, not a live callback binding or hardware transfer.
"""
from __future__ import annotations

import collections
import hashlib
import re
import sys
from pathlib import Path

try:
    from capstone import CS_ARCH_ARM, CS_ARCH_ARM64, CS_MODE_ARM, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile
except ModuleNotFoundError:
    # The workspace's offline analysis dependency bundle is intentionally used
    # rather than downloading anything.
    sys.path.insert(0, "/tmp/tcon-capstone")
    from capstone import CS_ARCH_ARM, CS_ARCH_ARM64, CS_MODE_ARM, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "binaries/libave.so.0.1": "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777",
    "binaries/tztv_frc_tcon_api.ko": "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6",
    "binaries/tztv_frc_tcon.ko": "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd",
    "binaries/rosem_frc.ko": "c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34",
    "overnight/capacity-20261026t1648.onset/trace": "403d6951854ae14e312d894534a02b1fe42bb59e576ef58fe9ef8a44994058e7",
    "overnight/capacity-20261026t1648.onset/fds.txt": "5b7e89cb8c52b3031ca03f499c4489f6ac3faa034ac3402723376b4c6c9ff4ac",
}


def require(condition: bool, text: str) -> None:
    if not condition:
        raise ValueError(text)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section_bytes(path: Path, section_name: str, address: int, size: int) -> bytes:
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        section = elf.get_section_by_name(section_name)
        require(section is not None, f"{path}: missing {section_name}")
        start = address - section["sh_addr"]
        data = section.data()
        require(0 <= start and start + size <= len(data), f"{path}: bad {section_name} range")
        return data[start : start + size]


def disasm(path: Path, arch: int, mode: int, address: int, size: int) -> list[str]:
    engine = Cs(arch, mode)
    return [f"{item.address:x}: {item.mnemonic} {item.op_str}" for item in engine.disasm(section_bytes(path, ".text", address, size), address)]


def relocations(path: Path) -> str:
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        values: list[str] = []
        for section in elf.iter_sections():
            if section["sh_type"] in {"SHT_RELA", "SHT_REL"}:
                symbols = elf.get_section(section["sh_link"])
                for rel in section.iter_relocations():
                    symbol = symbols.get_symbol(rel["r_info_sym"])
                    values.append(f"{rel['r_offset']:x}:{symbol.name}")
        return "\n".join(values)


def symbols(path: Path) -> str:
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        values: list[str] = []
        for section in elf.iter_sections():
            if section["sh_type"] == "SHT_SYMTAB":
                values.extend(f"{s['st_value']:x}:{s.name}" for s in section.iter_symbols())
        return "\n".join(values)


def main() -> None:
    for relative, expected in EXPECTED.items():
        actual = sha(ROOT / relative)
        require(actual == expected, f"hash mismatch {relative}: {actual}")

    api = ROOT / "binaries/tztv_frc_tcon_api.ko"
    ave = ROOT / "binaries/libave.so.0.1"
    rosem = ROOT / "binaries/rosem_frc.ko"

    handler = "\n".join(disasm(api, CS_ARCH_ARM64, CS_MODE_ARM, 0x195C, 0x50))
    for needle in (
        "195c: mov w1, #0x6623",
        "1960: movk w1, #0xc008, lsl #16",
        "196c: add w1, w1, #3",
        "1988: mov x2, #8",
        "1994: ldr w0, [sp, #0xd0]",
        "1998: add x1, x21, #4",
    ):
        require(needle in handler, f"API ioctl-handler landmark missing: {needle}")
    copyout_branch = "\n".join(disasm(api, CS_ARCH_ARM64, CS_MODE_ARM, 0x19C8, 0x28))
    require(
        "19e0: cbnz x0, #0x2cd4" in copyout_branch,
        "API copyout branch landmark missing",
    )
    copyout = "\n".join(disasm(api, CS_ARCH_ARM64, CS_MODE_ARM, 0x2CD4, 0x40))
    for needle in (
        "2cf4: mov x2, #8",
        "2cf8: mov x1, x21",
        "2d04: cbnz x0, #0x19e4",
        "2d0c: b #0x1478",
    ):
        require(needle in copyout, f"API copyout landmark missing: {needle}")

    reader = "\n".join(disasm(api, CS_ARCH_ARM64, CS_MODE_ARM, 0x94DC, 0x60))
    for needle in (
        "94e4: cbz x0, #0x951c",
        "94e8: ldr x2, [x0, #0xf8]",
        "94ec: cbz x2, #0x951c",
        "94f8: blr x2",
        "951c: mov w21, #0",
    ):
        require(needle in reader, f"API reader landmark missing: {needle}")

    ave_code = "\n".join(disasm(ave, CS_ARCH_ARM, CS_MODE_THUMB, 0x243EE8, 0x80))
    for needle in (
        "243f28: movw r0, #0x6626",
        "243f2c: movt r0, #0xc008",
        "243f34: str r4, [r7, #4]",
        "243f36: str.w r8, [r7, #8]",
        "243f42: ldr r3, [r7, #8]",
        "243f44: str r3, [r5]",
    ):
        require(needle in ave_code, f"libave constructor landmark missing: {needle}")

    ave_symbols = symbols(ave)
    ave_relocs = relocations(ave)
    require("243ee9:_Z16ave_frc_read_i2cjPj" in ave_symbols, "missing ave_frc_read_i2c symbol")
    require("2ad6e5:_Z9frc_ioctlmPv" in ave_symbols, "missing frc_ioctl symbol")
    require("5a60b8:_Z9frc_ioctlmPv" in ave_relocs, "missing libave frc_ioctl jump slot")
    require("5a510c:ioctl" in ave_relocs, "missing libc ioctl jump slot")

    rosem_relocs = relocations(rosem)
    require("38:RosemFrc_ReadI2CData" in rosem_relocs, "missing Rosem read-function materialization")
    require("3c8:map_frc_functions" in rosem_relocs, "missing Rosem map_frc_functions call")
    rosem_code = "\n".join(disasm(rosem, CS_ARCH_ARM64, CS_MODE_ARM, 0x780, 0x90))
    for needle in (
        "7ac: str xzr, [sp, #0x30]",
        "7b0: stp w0, wzr, [sp, #0x38]",
        "7c4: mov w0, #2",
        "7c8: blr x3",
        "7d4: ldr w0, [sp, #0x34]",
        "7d8: str w0, [x20]",
        "7dc: mov w0, w19",
        "7f0: cbz w19, #0x7dc",
    ):
        require(needle in rosem_code, f"Rosem read landmark missing: {needle}")

    trace = ROOT / "overnight/capacity-20261026t1648.onset/trace"
    enter = re.compile(r"^\s*(.*?)\s*-\s*(\d+)\s+\(.*?\) \[[0-9]+\].*?\s([0-9]+\.[0-9]+): sys_enter: NR 54 \(15, c0086626, ([0-9a-f]+),")
    exit_ = re.compile(r"^\s*(.*?)\s*-\s*(\d+)\s+\(.*?\) \[[0-9]+\].*?\s([0-9]+\.[0-9]+): sys_exit: NR 54 = (-?\d+)")
    waiting: dict[tuple[str, str], list[tuple[float, str]]] = collections.defaultdict(list)
    paired: list[tuple[float, str, int]] = []
    for line in trace.read_text(errors="replace").splitlines():
        match = enter.match(line)
        if match:
            name, tid, when, pointer = match.groups()
            waiting[(name.strip(), tid)].append((float(when), pointer))
            continue
        match = exit_.match(line)
        if match:
            name, tid, _when, result = match.groups()
            queue = waiting[(name.strip(), tid)]
            if queue:
                when, pointer = queue.pop(0)
                paired.append((when, pointer, int(result)))
    require(not any(waiting.values()), "unpaired c0086626 enter")
    require(len(paired) == 26387, f"expected 26387 fully paired raw calls, got {len(paired)}")
    require(set(value for _, _, value in paired) == {0}, "raw c0086626 return was not uniformly zero")
    expected_pointers = {"f4afc1dc": 5462, "f4afc3d4": 5462, "f4afc284": 5462, "f4cfd3bc": 5462, "f52fe4e4": 4539}
    require(collections.Counter(pointer for _, pointer, _ in paired) == expected_pointers, "raw pointer inventory changed")

    print("PASS: hash-gated static ABI landmarks and raw trace pairing")
    print("raw-paired=26387 returns={0:26387} pointers=5")
    print("LIMIT: proves neither a live callback binding nor user-buffer contents/hardware transfer.")


if __name__ == "__main__":
    main()
