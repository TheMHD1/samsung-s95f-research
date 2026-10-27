#!/usr/bin/env python3
"""Offline verifier for the ordinary RTP event-736 predicate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
PACKAGE = BASE / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
V6 = HERE / "onset-v6"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pinned(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    need(sha256(data) == expected, f"SHA-256 mismatch: {path}")
    return data


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def image1(package: bytes, va: int, size: int) -> bytes:
    return package[0x40200 + va : 0x40200 + va + size]


def thumb_bl_target(data: bytes, address: int) -> int:
    need(len(data) == 4, "BL width")
    first, second = struct.unpack("<HH", data)
    need(first & 0xF800 == 0xF000, f"BL first halfword at {address:#x}")
    need(second & 0xD000 == 0xD000, f"BL second halfword at {address:#x}")
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


def direct_bl_callers(image: bytes, target: int) -> list[int]:
    callers: list[int] = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
            continue
        if thumb_bl_target(image[address : address + 4], address) == target:
            callers.append(address)
    return callers


def main() -> None:
    package = pinned(
        PACKAGE,
        "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0",
    )
    need(len(package) == 5 * 1024 * 1024, "selected package extent")
    image = package[0x40200 : 0x80200]

    caller = image1(package, 0x1E68, 0x2040 - 0x1E68)
    need(sha256(caller) == "c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a", "predicate body")
    helper = image1(package, 0x1E46, 0x22)
    need(sha256(helper) == "350de4bfced804f1b66061fdd911b92b9452a1cac8790150b49200ce42f8ae6a", "q membership helper")
    bpflg_format = b"BPFLG :%d  (y:%d / rgb:%d)\n\0"
    need(image1(package, 0x2050, len(bpflg_format)) == bpflg_format, "exact BPFLG diagnostic format")

    # Literal pool resolves the state machine to four exact CPU RAM bases.
    expected_literals = {
        0x2044: 0x2000D0FC,
        0x2048: 0x2000D108,
        0x204C: 0x2000BA40,
        0x206C: 0x2000D0E4,
    }
    for va, value in expected_literals.items():
        need(u32(image1(package, va, 4), 0) == value, f"literal at {va:#x}")

    # Exact state-update blocks: q/history, BPFLG, accumulation, and tail.
    need(
        sha256(image1(package, 0x1F08, 0x203E - 0x1F08))
        == "3eb489d45dcf6e5127b1f4730aec460da1f4c80152cbc1489d06d486897b594f",
        "state machine through event tail",
    )
    tail = image1(package, 0x200E, 0x30)
    need(sha256(tail) == "a08eedbd1f8b8483af94ab4c38fe0762962d4a7a1a1343c78e4b7579476c132e", "r7 tail")
    need(tail[:10].hex() == "601e164931f8200087b2", "mode-indexed low-half accumulator load")
    need(tail[10:28].hex() == "062c03d140f60670475302e040f608704753", "mode-6/non-mode latch stores")
    need(tail[28:32].hex() == "5f4507dd", "r7/fp compare and non-event branch")
    need(thumb_bl_target(image1(package, 0x2032, 4), 0x2032) == 0x1C0C8, "pre-event helper")
    need(image1(package, 0x2036, 4).hex() == "4ff43870", "literal event 0x2e0")
    need(thumb_bl_target(image1(package, 0x203A, 4), 0x203A) == 0xC1E0, "common event setter")

    # The gate and all five threshold offsets are exact in the body.
    threshold_block = image1(package, 0x1E86, 0x70)
    for encoded, name in (
        (bytes.fromhex("42f2c440"), "+0x24c4"),
        (bytes.fromhex("42f23040"), "+0x2430"),
        (bytes.fromhex("42f23240"), "+0x2432"),
        (bytes.fromhex("4ff41150"), "+0x2440"),
        (bytes.fromhex("4ff41350"), "+0x24c0"),
    ):
        need(encoded in threshold_block, f"threshold encoding {name}")
    need(threshold_block.count(bytes.fromhex("96f8c706")) == 3, "three context-byte decisions")
    need(image1(package, 0x1EF6, 10).hex() == "42f29e40405b012873d1", "root +0x249e gate")

    # Both alternate T calculators latch their uint16 results at root +0x0f04.
    need(image1(package, 0xC9FA, 10).hex() == "40f6047020f80b50a8b2", "c8a0 result latch")
    need(image1(package, 0xCA6C, 8).hex() == "40f604704453a0b2", "ca10 result latch")

    # Exact direct caller census and mode/y/RGB tail.
    need(direct_bl_callers(image, 0x1E68) == [0xBFBC, 0xBFD0, 0xBFDC], "all direct predicate callers")
    direct_tail = image1(package, 0xBFAE, 0x32)
    need(sha256(direct_tail) == "23ccb4cf3f20e4bcafae5cba1fee099157d530a4a40dd5d2f1a19a4dcf1ea359", "mode-selection call tail")
    need(u32(image1(package, 0xC030, 4), 0) == 0x200004AA, "mode-4 flag literal")
    need(u32(image1(package, 0xC040, 4), 0) == 0x200004AC, "mode-6 flag literal")
    need(image1(package, 0xBD60, 4).hex() == "92461e46", "unpacker preserves r2 as y and r3 as RGB")

    # Orchestrator/selector argument continuity into the unpacker.
    need(image1(package, 0xB6F2, 12).hex() == "304801882e48008800f077f8", "y/RGB loads and selector call")
    need(u32(image1(package, 0xB7B4, 4), 0) == 0x200004D4, "RGB scalar literal")
    need(u32(image1(package, 0xB7B0, 4), 0) == 0x200004D0, "y scalar literal")
    need(image1(package, 0xB7EC, 6).hex() == "70b505460e46", "selector preserves y/RGB")
    for call_va in (0xB84C, 0xB874, 0xB88A):
        need(thumb_bl_target(image1(package, call_va, 4), call_va) == 0xBD58, f"unpacker caller {call_va:#x}")

    # Reset/scatter-proven getter shape, kept distinct from bus-window reads.
    need(image1(package, 0x38FC, 12).hex() == "0148006870470000e0040020", "root getter and CPU slot")
    need(image1(package, 0x38F4, 8).hex() == "0048704700050020", "fixed context base")

    outcome_raw = pinned(
        V6 / "native-outcome.json",
        "1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9",
    )
    outcome = json.loads(outcome_raw)
    need(outcome.get("Accepted") is True and outcome.get("RestoreVerified") is True, "accepted restored V6")
    need(outcome.get("PreArmFault") == 0 and outcome.get("RestoredGate") == 0, "V6 precondition/restore")
    restored = pinned(
        V6 / "restored-rt.bin",
        "2175e6ce7455123b8071e9edb3b3ada855107d182650c47a307f31bdd39a6ab8",
    )
    need(len(restored) == 64, "fixed V6 window extent")
    need(u16(restored, 0x0A) == 0x1001, "retained window fault halfword")
    need(u16(restored, 0x30) == 0x00C8 and u16(restored, 0x32) == 0, "retained window threshold offsets")
    ring = pinned(
        HERE / "onset-v6-event-log.bin",
        "deccf31188b565c7c4c9aadcb838e042c55f81f94ffae7c88093902dc21678ba",
    )
    need(ring.endswith(b"rtp_act_736\nrtp_act_736\n"), "retained duplicated numeric event")
    need(ring.count(b"rtp_act_736\n") == 2, "exact retained event count")

    result = {
        "schema": "rtp-736-predicate-verification-v1",
        "package_sha256": sha256(package),
        "predicate_body_sha256": sha256(caller),
        "direct_callers": [f"0x{x:x}" for x in direct_bl_callers(image, 0x1E68)],
        "mode_flags_cpu": ["0x200004aa", "0x200004ac"],
        "accumulators_cpu": "0x2000d0e4..0x2000d0fb",
        "r7_source": "low16(uint32[0x2000d0e4 + 4*(mode-1)])",
        "r7_latches": {"mode6": "R+0x0f06", "other": "R+0x0f08"},
        "predicate": "r7 > selected_fp",
        "event_argument_hex": "0x2e0",
        "event_argument_decimal": 736,
        "v6_window_0x47012430": u16(restored, 0x30),
        "cpu_2001_bus_4701_alias_proved": False,
        "physical_meaning_proved": False,
        "offline_only": True,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
