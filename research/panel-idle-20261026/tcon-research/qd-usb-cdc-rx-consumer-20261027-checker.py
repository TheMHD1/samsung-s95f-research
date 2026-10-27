#!/usr/bin/env python3
"""Offline pinning check for the selected profile's CDC RX completion path."""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
BASE = 0x200
IMAGE0_END = 0x40000

def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def h(data: bytes, start: int, end: int) -> str:
    return hashlib.sha256(data[start:end]).hexdigest()

def u16(data: bytes, file: int) -> int:
    return struct.unpack_from("<H", data, file)[0]

def target_bl(data: bytes, va: int) -> int | None:
    a, b = u16(data, va + BASE), u16(data, va + BASE + 2)
    if (a & 0xf800) != 0xf000 or (b & 0xd000) != 0xd000:
        return None
    s, j1, j2 = (a >> 10) & 1, (b >> 13) & 1, (b >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ s), 1 ^ (j2 ^ s)
    imm = ((s << 24) | (i1 << 23) | (i2 << 22) |
           ((a & 0x3ff) << 12) | ((b & 0x7ff) << 1))
    if s:
        imm -= 1 << 25
    return (va + 4 + imm) & 0xffffffff

def callers(data: bytes, target: int, low: int = 0, high: int = IMAGE0_END - BASE) -> list[int]:
    return [va for va in range(low, high - 3, 2) if target_bl(data, va) == target]

def main() -> None:
    data = PROFILE.read_bytes()
    need(len(data) == 0x500000 and hashlib.sha256(data).hexdigest() == SHA,
         "selected profile identity mismatch")
    slices = {
        "usbserial_init": (0x22324, 0x22390, "ac0cbbee3f3088afe88c4541c0136a60778cfcfa4d8461c4720247ecb117a8b6"),
        "rx_completion_body": (0x2980A, 0x2986E, "f623ba9cd7ca4cd9906b0b2f199c65cebff282f83be7c36eb1eff93d8f7fe4a6"),
        "rx_worker": (0x29CFC, 0x29DA2, "95f2b8b66c1a603d4d7b0d7868e5c387f0788086efc88be823b516408c725959"),
        "cdc_region": (0x28000, 0x2C000, "b547be2ba8996708bea037a519a7df368589a74669eb4ffa174b6638a20762f3"),
    }
    result = {}
    for name, (start, end, expected) in slices.items():
        actual = h(data, start, end)
        need(actual == expected, name + " hash mismatch")
        result[name] = {"file_start": hex(start), "file_end": hex(end),
                        "linked_va_start": hex(start - BASE), "sha256": actual}
    # The state object and registration handle have the literal references
    # found in the selected image; the RX path operates through object offsets.
    for val, expected in {
        0x2026142c: [0x22390, 0x2B26C, 0x2B2F4],
        0x20000638: [0x223A4],
    }.items():
        needle = struct.pack("<I", val)
        hits=[]; pos=0
        while True:
            pos=data.find(needle, pos, 0x40200)
            if pos < 0: break
            hits.append(pos); pos += 1
        need(hits == expected, "literal census mismatch for " + hex(val))
    need(callers(data, 0x29afc) == [0x29666, 0x2984e, 0x29a02], "RX worker callers changed")
    need(callers(data, 0x2960a) == [], "unexpected direct BL to completion")
    # In the CDC implementation interval, no direct BL reaches the UART CLI,
    # UART dispatcher, or UART ring producer. The one generic-reader caller
    # here is the separately bounded TCDATA sampler, not an RX-worker caller.
    absent = (0x16fc0, 0x17084, 0x21084)
    for target in absent:
        need(callers(data, target, 0x27e00, 0x2c000) == [],
             "unexpected CDC-area direct edge " + hex(target))
    need(callers(data, 0x637c, 0x27e00, 0x2c000) == [0x2a2f8],
         "CDC-area generic-reader census changed")
    print(json.dumps({
        "profile_sha256": SHA,
        "address_rule": "image0 linked VA = stored file - 0x200",
        "verified_slices": result,
        "rx_worker_direct_callers_va": [hex(x) for x in callers(data, 0x29afc)],
        "cdc_area_direct_edges_to": {hex(x): False for x in absent},
        "cdc_area_generic_reader_callers_va": ["0x2a2f8"],
        "conclusion": "no direct CDC RX worker/completion-to-CLI edge; separate TCDATA reader is not an RX consumer"
    }, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
