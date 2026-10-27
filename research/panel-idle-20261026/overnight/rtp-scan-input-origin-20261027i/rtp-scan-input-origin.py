#!/usr/bin/env python3
"""Offline verifier for ordinary RTP x/y/RGB input provenance."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
D7 = OVERNIGHT / "finite-onset-logger-20261027g"
RT = D7 / "fault-context-after-v6/rt.bin"
V6_LOG = D7 / "onset-v6-event-log.bin"


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
    result: list[tuple[int, int]] = []
    for address in range(0, len(image) - 1, 2):
        instruction = u16(image, address)
        if instruction & 0xF800 != 0x4800:
            continue
        destination = ((address + 4) & ~3) + (instruction & 0xFF) * 4
        if destination == literal:
            result.append((address, (instruction >> 8) & 7))
    return result


def exact(package: bytes, va: int, expected_hex: str, label: str) -> None:
    expected = bytes.fromhex(expected_hex)
    need(image1(package, va, len(expected)) == expected, label)


def main() -> None:
    package = PACKAGE.read_bytes()
    need(len(package) == 0x500000, "selected package extent")
    need(sha256(package) == "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "selected package")
    image = package[0x40200 : 0x60200]

    directory = package[0x86000 : 0x86200]
    need(len(directory) == 512 and sha256(directory) == "b4f7b34aedaadfbfc8d67c3f232dd7c37d1d0a1bcea704483071770f39c1f248", "AP_RTP directory")
    need(directory[:32] == b"AP_RTP" + bytes(26), "AP_RTP name")
    need(u32(directory, 0x20) == 4 and u32(directory, 0x2C) == 0x103800 and u32(directory, 0xAC) == 0x100, "AP_RTP payload mapping")
    defaults = package[0x80000 + u32(directory, 0x2C) : 0x80000 + u32(directory, 0x2C) + u32(directory, 0xAC)]
    need(len(defaults) == 256 and sha256(defaults) == "3a16ea440b59a8e778c01ddfc429b110fbdd03e55c953954ce99337ebf5b3937", "AP_RTP defaults")
    expected_root = {0x02: 2880, 0x04: 2160, 0x52: 2157, 0x54: 2160}
    need({offset: u16(defaults, offset) for offset in expected_root} == expected_root, "AP_RTP scan fields")
    rt = RT.read_bytes()
    need(len(rt) == 256 and sha256(rt) == "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9", "retained root window")
    need({offset: u16(rt, offset) for offset in expected_root} == expected_root, "late scan fields equal defaults")

    # Complete aligned literal/load-reference sets for the two scan scalars.
    need(aligned_word_positions(image, 0x200004D0) == [0xB7B0], "y literal census")
    need(literal_load_refs(image, 0xB7B0) == [(0xB692, 1), (0xB6F6, 0), (0xB736, 1)], "y refs")
    need(aligned_word_positions(image, 0x200004D4) == [0xB7B4], "RGB literal census")
    need(literal_load_refs(image, 0xB7B4) == [(0xB69C, 1), (0xB6C2, 0), (0xB6F2, 0), (0xB71E, 0), (0xB746, 1)], "RGB refs")
    exact(package, 0xB68C, "47480068c0884749088045480068807845490880", "dynamic B-header scalar writers")
    exact(package, 0xB6F2, "304801882e48008800f077f8", "scan scalar loads and selector call")
    exact(package, 0xB732, "284800881e490880204800881e4908801f4800881b490880", "latched-header scalar writers")
    need(direct_callers(image, 0xB7EC) == [0xB6FA], "selector direct caller")

    # Callback-latched b0/b2/b4 destinations. Pin the actual helper code and
    # literal pool rather than treating nearby printable data as instructions.
    need((u32(image, 0xBB9C), u32(image, 0xBBA0), u32(image, 0xBBA4)) ==
         (0x200004B0, 0x200004B2, 0x200004B4), "header handoff destinations")
    need(u32(image, 0x3A6C) == 0x58601408, "input-register root literal")
    exco = package[0x83C00 : 0x83E00]
    need(len(exco) == 0x200 and
         sha256(exco) == "2dfc6d013c0907962adfed3750534b32f70bbcbfe278020f3aef5a6368789d6a",
         "EXCO_PAR2_S0 metadata record")
    need(exco[:32] == b"EXCO_PAR2_S0" + bytes(20), "EXCO_PAR2_S0 name")
    need((u32(exco, 0x20), u32(exco, 0x24), u32(exco, 0x28),
          u32(exco, 0x2C), u32(exco, 0xAC)) ==
         (7, 0x58601400, 1, 0xC8C00, 0x2600), "EXCO_PAR2_S0 metadata fields")
    need(u32(exco, 0x24) + 8 == u32(image, 0x3A6C),
         "EXCO_PAR2_S0 base plus eight is refresh root")
    need(sha256(image1(package, 0x398A, 0x30)) == "b22c185ad057700a3e659d6a1732f75d7499e28c0c95312d29af64c5d09d3f21", "memory-mapped input header build")
    need(sha256(image1(package, 0xBB58, 0x1A)) == "cbbb4c7e8f8ccb6a9677ab6ea07ced312131c46f3058a22a8814ea84eebc60a3", "header handoff first stores")
    need(direct_callers(image, 0xBB58) == [0x3A0E], "header handoff direct caller")
    need(direct_callers(image, 0x3934) == [0x18C96], "registered refresh direct caller")

    # Packed-source handoff and exact 12-bit loop index behavior.
    need(u32(image, 0xB894) == 0x20000494 and u32(image, 0xB898) == 0x20000498, "dynamic A/B pointer slots")
    exact(package, 0xB87A, "33462a4606480168083103480068083000f065fa", "dynamic packed A/B call")
    need(direct_callers(image, 0xBD58) == [0xB84C, 0xB874, 0xB88A], "packed unpacker callers")
    need(sha256(image1(package, 0xBD58, 0x2D4)) == "5d9924044096fbef1f5c14db5c289d60d465750ad5ea5be6ce479375542ffcb6", "packed 12-bit unpacker")
    need(direct_callers(image, 0xBBBC) == [0xBEDC, 0xBF18, 0xBF5A, 0xBF90], "four lane-helper calls")
    exact(package, 0xBD72, "00240020cdf8140f", "x and scratch reset")
    exact(package, 0xBE34, "4ff0000bb3e0", "packed-byte offset reset")
    exact(package, 0xBF98, "241d0bf106001ffa80fb", "four-lane/six-byte advance")

    # Root +2402 supplies the packed byte extent; +2404 checks a different
    # neighboring header field rather than the y scalar at d0.
    need(sha256(image1(package, 0xCB2C, 0x28)) == "e7f5729542ae35b9ec058e497ec51e80e30bbaa88ecf5694746dc53f875ff6a5", "root 2402 initialization")
    need(u32(image, 0xCBB0) == 0x200004A6 and u32(image, 0xCBB4) == 0x200004A8, "packed extent globals")
    need(aligned_word_positions(image, 0x200004A6) == [0xC04C, 0xC45C, 0xCBB0], "packed extent literal census")
    exact(package, 0xBF98, "241d0bf106001ffa80fb2a4800888345fff647af", "loop advance and extent compare")
    need(sha256(image1(package, 0xB6FE, 0x20)) == "2b1360343cc1454cad419777bbc18c4f6dde08fd65d4ae45a62c6216aa7a94a4", "root 2404 neighboring-field checks")

    # Formatter receives r2=y in r8 and applies inclusive +2452/+2454 bounds.
    exact(package, 0xC5D0, "2de9ff5f07460e4690469946dde90ea4", "formatter argument preservation")
    need(sha256(image1(package, 0xC7E8, 0x1E)) == "be8cb48822cdb8ed01abe3a5a4fd924cd35bca27608951717a9abdd7e038f82f", "y diagnostic bounds")

    v6 = V6_LOG.read_bytes()
    need(len(v6) == 1756 and sha256(v6) == "deccf31188b565c7c4c9aadcb838e042c55f81f94ffae7c88093902dc21678ba", "V6 log delta")
    text = v6.decode("ascii")
    numeric_rows = [tuple(map(int, match)) for match in re.findall(
        r"\[RTP\s+(\d+)\]RGB:(\d+) x:\s*(\d+) y:\s*(\d+)/c:\s*(\d+)/diff:(\d+)/m:[A-Z]+",
        text,
    )]
    need(len(numeric_rows) == 31, "V6 detail row count")
    need(Counter(row[1] for row in numeric_rows) == {0: 31}, "V6 RGB values")
    need(Counter(row[3] for row in numeric_rows) == {2159: 31}, "V6 y values")
    xs = sorted({row[2] for row in numeric_rows})
    need(xs == [570, 571, 620, 621, 630, 631], "V6 logged x set")

    packed_bytes = expected_root[0x02]
    need(packed_bytes % 6 == 0, "complete packed groups")
    groups = packed_bytes // 6
    lanes = groups * 4
    aa = {
        "schema": "rtp-scan-input-origin-verification-v1",
        "packed_bytes": packed_bytes,
        "packed_groups": groups,
        "logical_12bit_lanes": lanes,
        "logical_x_range": [0, lanes - 1],
        "y_origin": "ordinary input/header scalar copied to CPU 0x200004d0",
        "rgb_origin": "ordinary input/header scalar copied to CPU 0x200004d4",
        "y_incremented_by_packed_loop": False,
        "rgb_incremented_by_packed_loop": False,
        "root_2404_directly_compares_y": False,
        "y_later_formatter_gate_inclusive": [expected_root[0x52], expected_root[0x54]],
        "v6_y": 2159,
        "v6_rgb": 0,
        "physical_coordinate_mapping_proved": False,
        "associated_metadata_name": "EXCO_PAR2_S0",
        "associated_metadata_base": "0x58601400",
        "individual_field_names_proved": False,
        "hardware_input_edge": "EXCO_PAR2_S0-associated address block 0x58601408; physical producer unresolved",
        "offline_only": True,
    }
    print(json.dumps(aa, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
