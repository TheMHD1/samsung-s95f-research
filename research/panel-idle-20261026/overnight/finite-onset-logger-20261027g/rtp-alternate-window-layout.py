#!/usr/bin/env python3
"""Offline verifier for fixed-context +0x6c0..+0x6cf layout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
PACKAGE = BASE / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
D5 = BASE / "overnight/executing-image-identity-20261027e/secondary-root-read-once/returned-block.bin"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def image1(package: bytes, va: int, size: int) -> bytes:
    return package[0x40200 + va : 0x40200 + va + size]


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


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


def main() -> None:
    package = PACKAGE.read_bytes()
    need(len(package) == 0x500000, "selected package extent")
    need(sha256(package) == "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "selected package")
    image = package[0x40200 : 0x60200]

    zero_start, zero_end = 0x200004F8, 0x200004F8 + 0xDCA4
    need(zero_start <= 0x20000BC0 and 0x20000BD0 <= zero_end == 0x2000E19C, "reset zero-fill covers slice")

    # Fixed numeric startup header and its only direct caller.
    need(direct_callers(image, 0x17970) == [0x1BA9E], "startup header direct caller")
    startup = image1(package, 0x17970, 0x22)
    need(sha256(startup) == "7e5d5e317690ae4e85ffc207067df494904a2d504086f004dd615e581142cf14", "startup header body")
    expected_startup = bytes.fromhex("70088007400b00000000000000000000")

    expected_stores = {
        0x1797C: "a4f8c206",
        0x17984: "a4f8c006",
        0x1798C: "a4f8c406",
        0x3952: "85f8c706",
        0x3958: "85f8c806",
        0x17156: "84f8c906",
        0x1717A: "84f8ca06",
        0x185A2: "85f8cb06",
        0x17AC6: "84f8cc06",
        0x17AF4: "84f8cd06",
        0x19A92: "84f8cd06",
        0x17B7A: "84f8ce06",
        0x197FE: "85f8ce06",
        0x19954: "84f8ce06",
    }
    for address, expected_hex in expected_stores.items():
        need(image1(package, address, 4).hex() == expected_hex, f"direct store {address:#x}")

    # Pin the immediate MOVS values feeding each directly claimed flag store.
    for address, value in {
        0x17156: 0,
        0x1717A: 0,
        0x185A2: 0,
        0x17AC6: 0,
        0x17AF4: 0,
        0x17B7A: 1,
        0x19954: 0,
    }.items():
        need(image1(package, address - 2, 2) == bytes((value, 0x20)), f"MOVS source {address:#x}")
    need(image1(package, 0x197F8, 10).hex() == "01203e49087085f8ce06", "mirrored 1 source at 0x197fe")
    need(
        image1(package, 0x19A86, 16).hex() == "bbf1010f01d1022000e0012084f8cd06",
        "conditional 1/2 source at 0x19a92",
    )

    # Same callback refreshes neighboring +6c7/+6c8 from AP_EXCO.
    need(image1(package, 0x394E, 14).hex() == "96f8d80385f8c706307885f8c806", "neighbor refresh sequence")
    first_source, second_source = 0x182200, 0x182600
    need(sha256(package[first_source : first_source + 0x33A]) == "c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf", "AP_EXCO first payload")
    need(sha256(package[second_source : second_source + 0x1200]) == "5000ce2a135b4b463505a32cf5b525916605b32c21a20de4bd91607d4b839761", "AP_EXCO second payload")
    source_3d8 = second_source + (0x3D8 - 0x33A)
    need(source_3d8 == 0x18269E and package[source_3d8] == 0x14, "AP_EXCO +3d8 default")
    need(package[first_source] == 0, "AP_EXCO +0 default")
    selected_callback = bytearray(expected_startup)
    selected_callback[7] = package[source_3d8]
    selected_callback[8] = package[first_source]
    need(selected_callback.hex() == "70088007400b00140000000000000000", "conditional selected callback fingerprint")

    # Frozen older mirror read: useful contradiction to assuming default 20 live.
    d5 = D5.read_bytes()
    need(len(d5) == 64 and sha256(d5) == "2543a59edfbd16832cfddd460c3dae28017309669d35eabc6eedcdfd95b7675d", "frozen D5 root block")
    need(u16(d5, 2) == 0 and u16(d5, 4) == 0, "older +4c2/+4c4 mirrors")
    need(u32(d5, 0x20) == 0x20010000, "older root pointer")

    cpu_start = 0x20000500 + 0x6C0
    candidate_bus = cpu_start + 0x27000000
    need(cpu_start == 0x20000BC0 and candidate_bus == 0x47000BC0, "candidate mapper arithmetic")

    result = {
        "schema": "rtp-alternate-window-layout-verification-v1",
        "cpu_range": "0x20000bc0..0x20000bcf",
        "candidate_bus_range": "0x47000bc0..0x47000bcf",
        "reset_fingerprint": "00" * 16,
        "startup_fingerprint": expected_startup.hex(),
        "conditional_selected_callback_pattern": "70088007400b001400??????????????",
        "constructed_startup_then_callback_fingerprint": selected_callback.hex(),
        "constructed_fingerprint_is_live_anchor": False,
        "ap_exco_plus_3d8": package[source_3d8],
        "ap_exco_plus_0": package[first_source],
        "older_mirror_4c2": u16(d5, 2),
        "older_mirror_4c4": u16(d5, 4),
        "single_byte_match_proves_alias": False,
        "offline_only": True,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
