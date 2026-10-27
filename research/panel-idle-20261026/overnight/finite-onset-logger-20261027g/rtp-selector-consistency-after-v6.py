#!/usr/bin/env python3
"""Offline verifier for the retained late selector/mirror consistency."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
PACKAGE = BASE / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CAPTURE = HERE / "selector-context-after-v6"
LATE = HERE / "fault-context-after-v6"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def image1(package: bytes, va: int, size: int) -> bytes:
    return package[0x40200 + va : 0x40200 + va + size]


def thumb_bl_target(data: bytes, address: int) -> int:
    need(len(data) == 4, "BL width")
    first, second = struct.unpack("<HH", data)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000, f"BL at {address:#x}")
    s = (first >> 10) & 1
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    i1 = 1 ^ (j1 ^ s)
    i2 = 1 ^ (j2 ^ s)
    value = ((s << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def direct_callers(image: bytes, target: int) -> list[int]:
    result: list[int] = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
            continue
        if thumb_bl_target(image[address : address + 4], address) == target:
            result.append(address)
    return result


def aligned_word_positions(image: bytes, value: int) -> list[int]:
    raw = struct.pack("<I", value)
    return [offset for offset in range(0, len(image) - 3, 2) if image[offset : offset + 4] == raw]


def literal_load_refs(image: bytes, literal: int) -> list[tuple[int, int]]:
    refs: list[tuple[int, int]] = []
    for address in range(0, len(image) - 1, 2):
        instruction = u16(image, address)
        if instruction & 0xF800 != 0x4800:
            continue
        destination = ((address + 4) & ~3) + (instruction & 0xFF) * 4
        if destination == literal:
            refs.append((address, (instruction >> 8) & 7))
    return refs


def direct_stores_covering(image: bytes, byte_offset: int) -> list[tuple[int, str, int]]:
    # Thumb-2 positive imm12 STRB/STRH/STR encodings. This is deliberately a
    # direct-immediate census, not a whole-writer proof.
    result: list[tuple[int, str, int]] = []
    for name, opcode, width in (("STRB", 0xF880, 1), ("STRH", 0xF8A0, 2), ("STR", 0xF8C0, 4)):
        for address in range(0, len(image) - 3, 2):
            first, second = struct.unpack_from("<HH", image, address)
            if first & 0xFFF0 != opcode:
                continue
            immediate = second & 0xFFF
            if immediate <= byte_offset < immediate + width:
                result.append((address, name, immediate))
    return result


def direct_loads_covering(image: bytes, byte_offset: int) -> list[tuple[int, str, int]]:
    result: list[tuple[int, str, int]] = []
    for name, opcode, width in (("LDRB", 0xF890, 1), ("LDRH", 0xF8B0, 2), ("LDR", 0xF8D0, 4)):
        for address in range(0, len(image) - 3, 2):
            first, second = struct.unpack_from("<HH", image, address)
            if first & 0xFFF0 != opcode:
                continue
            immediate = second & 0xFFF
            if immediate <= byte_offset < immediate + width:
                result.append((address, name, immediate))
    return result


def main() -> None:
    package = PACKAGE.read_bytes()
    need(len(package) == 0x500000, "selected package extent")
    need(sha256(package) == "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "selected package")
    image = package[0x40200 : 0x60200]

    mode = (CAPTURE / "mode-window.bin").read_bytes()
    alternate = (CAPTURE / "alternate-window.bin").read_bytes()
    need(len(mode) == 68 and sha256(mode) == "c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9", "late mode window")
    need(len(alternate) == 16 and sha256(alternate) == "2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a", "late alternate window")
    need(u32(mode, 0) == 396, "raw window status")
    need(u16(mode, 0x0A) == 0 and u16(mode, 0x0C) == 2, "late aa/ac")
    need(u16(mode, 0x22) == 1 and u16(mode, 0x24) == 0, "late mirror/companion")
    need(mode[0x38] == 0 and u32(mode, 0x40) == 0x20010000, "late gate/root")
    need(alternate.hex() == "70088007400b5c010300000000000000", "late candidate context")

    context = (LATE / "context.bin").read_bytes()
    rt = (LATE / "rt.bin").read_bytes()
    need(len(context) == 64 and sha256(context) == "0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439", "late score context")
    need(len(rt) == 256 and sha256(rt) == "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9", "late root context")
    need(u16(context, 8) == 44 and u16(rt, 0xC4) == 40, "late compatible score/threshold")

    # Complete aligned literal/reference census for CPU 0x200004c4.
    need(aligned_word_positions(image, 0x200004C4) == [0xB89C, 0xC2F4, 0x1C1A0], "4c4 literal census")
    need(literal_load_refs(image, 0xB89C) == [(0xB82C, 0)], "4c4 read gate ref")
    need(literal_load_refs(image, 0xC2F4) == [(0xC298, 1), (0xC2A0, 1)], "4c4 Boolean store refs")
    need(literal_load_refs(image, 0x1C1A0) == [
        (0x1C134, 0), (0x1C148, 0), (0x1C14E, 1),
        (0x1C174, 0), (0x1C17A, 1), (0x1C18E, 0), (0x1C198, 1),
    ], "4c4 progress refs")
    need(sha256(image1(package, 0xC27C, 0x28)) == "f68bd16875970d70d3a0d77d2c01db9539dfde4c949d1339d64ee8b7fb2559eb", "conditional mirror updater")
    need(sha256(image1(package, 0x1C12C, 0x70)) == "9f05a51defea6d8d255e4fc6364a3fd4beda8a50da738d7880d830b6689dc739", "ordinary progress body")
    need(direct_callers(image, 0x1C12C) == [0xB682, 0xB828], "progress direct callers")
    need(image1(package, 0xB82C, 6).hex() == "1b48008810bb", "4c4 read-only branch gate")

    # Fixed-context +6c6 has one direct read and no direct imm-width writer.
    need(image.count(bytes.fromhex("91f8c606")) == 1, "unique direct +6c6 load encoding")
    need(image1(package, 0x1BD90, 4).hex() == "91f8c606", "fixed +6c6 load")
    need(direct_loads_covering(image, 0x6C6) == [(0x1BD90, "LDRB", 0x6C6)], "direct loads covering +6c6")
    need(
        direct_stores_covering(image, 0x6C0) == [(0x17984, "STRH", 0x6C0)],
        "positive direct-store scanner fixture",
    )
    need(direct_stores_covering(image, 0x6C6) == [], "no direct immediate store covering +6c6")
    need(sha256(image1(package, 0x1BA24, 0x14)) == "6aca1127104e0c2f3e0791009bd5928a65c103c1cfb885a5777c8ffe0ea65412", "startup 5c request/poll")
    need(sha256(image1(package, 0x1BD88, 0x18)) == "dcbd439abb38f781d4004d8a05e411efde97db173e5fabc25185da57dab5818b", "fixed +6c6 equality poll")
    need(thumb_bl_target(image1(package, 0x1BA24, 4), 0x1BA24) == 0x38E8, "AP_EXCO getter")
    need(thumb_bl_target(image1(package, 0x1BA32, 4), 0x1BA32) == 0x1BD88, "poll call")
    need(thumb_bl_target(image1(package, 0x1BD8A, 4), 0x1BD8A) == 0x38F4, "fixed-context getter")
    need(direct_callers(image, 0x1BD88) == [0x1BA32], "poll direct caller")

    aa, ac = u16(mode, 0x0A), u16(mode, 0x0C)
    late_mode = 4 if aa == 1 else (6 if ac == 1 else 1)
    result = {
        "schema": "rtp-selector-consistency-after-v6-verification-v1",
        "late_mode": late_mode,
        "late_selector": alternate[7],
        "late_score": u16(context, 8),
        "late_threshold": u16(rt, 0xC4),
        "numeric_predicate_compatible": u16(context, 8) > u16(rt, 0xC4),
        "event_time_proved": False,
        "mirror": u16(mode, 0x22),
        "companion": u16(mode, 0x24),
        "mirror_one_companion_zero_allowed_by_code": True,
        "candidate_context_hex": alternate.hex(),
        "candidate_bus_alias_proved": False,
        "bc6_direct_immediate_writer_found": False,
        "bc6_producer_identified": False,
        "offline_only": True,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
