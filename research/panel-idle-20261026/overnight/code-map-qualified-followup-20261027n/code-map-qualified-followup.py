#!/usr/bin/env python3
"""Offline verifier for the image-1 low-linked-address mapper follow-up."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
SELECTED = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CURRENT = OVERNIGHT / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"

SELECTED_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
CURRENT_SHA256 = "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"
SLOT_SHA256 = "56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def image1(package: bytes, va: int, size: int) -> bytes:
    return package[0x40200 + va : 0x40200 + va + size]


def thumb_bl_target(data: bytes, address: int) -> int:
    need(len(data) == 4, "BL width")
    first, second = struct.unpack("<HH", data)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"BL encoding at {address:#x}")
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


def mapped(selector: int, address: int) -> int:
    """Exact ordinary VA 0x1bb74 behavior for the two covered domains."""
    if address == 0:
        return 0
    if selector == 0:
        if address < 0x40000:
            return address + 0x44000000
        if 0x20000000 <= address < 0x20020000:
            return address + 0x25000000
        return 0
    if address < 0x20000:
        return address + 0x46000000
    if 0x20000000 <= address < 0x20020000:
        return address + 0x27000000
    return 0


def main() -> None:
    selected = SELECTED.read_bytes()
    current = CURRENT.read_bytes()
    need(len(selected) == len(current) == 0x500000, "whole-file extent")
    need(sha256(selected) == SELECTED_SHA256, "selected package SHA-256")
    need(sha256(current) == CURRENT_SHA256, "current backup SHA-256")
    selected_slot = selected[0x40000:0x80000]
    current_slot = current[0x40000:0x80000]
    need(sha256(selected_slot) == SLOT_SHA256 and selected_slot == current_slot,
         "stored image-1 slot equality")
    image = selected[0x40200:0x60200]

    mapper = image1(selected, 0x1BB74, 0x50)
    need(sha256(mapper) ==
         "94da5bec3c7fd05448a66d3828ec420e5cb08e03cb4474a54d07570732d1fe5c",
         "low/RAM mapper body")
    need(mapper.hex() ==
         "024609b90020704772b9b1f5802f02d201f18840f7e7b1f1005f14d30b48814211d201f11450eee7b1f5003f02d201f18c40e8e7b1f1005f05d30448814202d201f11c50dfe70020dde7000000000220",
         "exact mapper instructions and upper-bound literal")
    need(u32(image, 0x1BBC0) == 0x20020000, "RAM upper-bound literal")

    # Positive boundary fixtures for both low linked-address branches and the
    # RAM branches prevent a coincidental predicate-only arithmetic check.
    need(mapped(0, 0) == 0 and mapped(1, 0) == 0, "null mapping")
    need(mapped(0, 1) == 0x44000001 and mapped(0, 0x3FFFF) == 0x4403FFFF and
         mapped(0, 0x40000) == 0, "selector-zero linked domain")
    need(mapped(1, 1) == 0x46000001 and mapped(1, 0x1FFFF) == 0x4601FFFF and
         mapped(1, 0x20000) == 0, "selector-nonzero linked domain")
    need(mapped(0, 0x20000000) == 0x45000000 and
         mapped(1, 0x20000000) == 0x47000000 and
         mapped(0, 0x2001FFFF) == 0x4501FFFF and
         mapped(1, 0x2001FFFF) == 0x4701FFFF and
         mapped(0, 0x20020000) == mapped(1, 0x20020000) == 0,
         "RAM-domain boundary fixtures")

    lookup = image1(selected, 0x1BBC4, 0x1BD4A - 0x1BBC4)
    need(sha256(lookup) ==
         "a81cf57bebffbd2b68f2cfcbc4d75ba9e70834614672b570971b47ea5767d9ba",
         "lookup wrappers/startup body")
    need((u32(image, 0x1BBF8), u32(image, 0x1BC20), u32(image, 0x1BC48)) ==
         (0x10000, 0x10000, 0x1000C), "lookup table roots")
    need(mapped(0, 0x10000) == 0x44010000 and
         mapped(0, 0x1000C) == 0x4401000C and
         mapped(1, 0x10000) == 0x46010000 and
         mapped(1, 0x1000C) == 0x4601000C, "mapped lookup roots")

    # Finite direct-call census. The application-entry path calls the complete
    # context initializer, whose seven direct lookup calls all load selector 0.
    need(direct_callers(image, 0x1BB74) ==
         [0x1BBCE, 0x1BBF0, 0x1BC18, 0x1BC40, 0x1BC6A, 0x1BC84, 0x1BCA2],
         "mapper direct callers")
    need(direct_callers(image, 0x1BBC4) == [0x1BC58], "mapper wrapper direct caller")
    need(direct_callers(image, 0x1BBD4) == [0x1BCD6, 0x1BCFA], "lookup-c direct callers")
    need(direct_callers(image, 0x1BBFC) == [0x1BCCA, 0x1BCEE, 0x1BD06],
         "lookup-first direct callers")
    need(direct_callers(image, 0x1BC24) == [0x1BCE2, 0x1BD12],
         "lookup-second direct callers")
    need(direct_callers(image, 0x1BCC4) == [0x1BA12], "context initializer caller")
    need(direct_callers(image, 0x1BA0C) == [0x2B4], "application entry caller")
    need(sha256(image1(selected, 0x2AC, 0x10)) ==
         "b08d19cb6f498725935e2cf4acbf9b0ab11c2339d7448430cee09fdab9077cd0",
         "runtime application launch sequence")
    need(sha256(image1(selected, 0x1BA0C, 0x20)) ==
         "c282e390f7fd971029b3b62ef4cc00c5c0d6e6fa4b4dddcaac8cddace4d57827",
         "application entry/context call sequence")
    for address in (0x1BCC8, 0x1BCD4, 0x1BCE0, 0x1BCEC, 0x1BCF8, 0x1BD04, 0x1BD10):
        need(image[address : address + 2] == bytes.fromhex("0020"),
             f"selector-zero setup at {address:#x}")

    vector = image1(selected, 0, 8)
    initial_sp, reset_thumb = struct.unpack("<II", vector)
    need((initial_sp, reset_thumb) == (0x20020000, 0x369), "image-1 vector")
    need(sha256(image1(selected, 0x368, 0x24)) ==
         "77428a5791705e4b966092c95715a84b617dfd7f414902ff35ae2089d92c93d6",
         "reset launch body")

    predicate = image1(selected, 0x1E68, 0x2040 - 0x1E68)
    need(len(predicate) == 0x1D8 and sha256(predicate) ==
         "c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a",
         "predicate body")
    need(predicate == current[0x40200 + 0x1E68 : 0x40200 + 0x2040],
         "predicate selected/current equality")
    need(mapped(1, 0x1E68) == 0x46001E68 and
         mapped(1, 0x203F) == 0x4600203F, "predicate selector-one mapped extent")

    specs = [
        (0x46001E60, 0x200,
         "01010000601e004600020000",
         "8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49"),
        (0x460038C0, 0x40,
         "01010000c038004640000000",
         "0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb"),
        (0x4601BB60, 0x240,
         "0101000060bb014640020000",
         "035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8"),
    ]
    rows = []
    for bus, length, header_hex, digest in specs:
        va = bus - 0x46000000
        need(0 < va and va + length <= 0x20000, f"selector-one domain {bus:#x}")
        need(mapped(1, va) == bus and mapped(1, va + length - 1) == bus + length - 1,
             f"full mapped extent {bus:#x}")
        file_offset = 0x40200 + va
        raw = selected[file_offset : file_offset + length]
        need(len(raw) == length and sha256(raw) == digest, f"window hash {bus:#x}")
        need(raw == current[file_offset : file_offset + length],
             f"window selected/current equality {bus:#x}")
        need(struct.pack("<III", 0x101, bus, length).hex() == header_hex,
             f"target-0x101 header {bus:#x}")
        rows.append({
            "bus_address": hex(bus),
            "linked_va": hex(va),
            "length": length,
            "inclusive_end": hex(bus + length - 1),
            "file_offset": hex(file_offset),
            "header_hex": header_hex,
            "selected_expected_sha256": digest,
            "selected_equals_current_stored": True,
        })

    result = {
        "schema": "code-map-qualified-followup-verification-v1",
        "status": "selector1-linked-code-domain-qualified",
        "offline_only": True,
        "target_operations": 0,
        "selected_sha256": SELECTED_SHA256,
        "current_sha256": CURRENT_SHA256,
        "stored_image1_slot_sha256": SLOT_SHA256,
        "stored_image1_slot_equal": True,
        "mapper_linked_domains": {
            "selector_zero": {"input": "0x1..0x3ffff", "add": "0x44000000"},
            "selector_nonzero": {"input": "0x1..0x1ffff", "add": "0x46000000"},
        },
        "ordinary_startup_direct_selector": 0,
        "selector1_direct_ordinary_invocation_proved": False,
        "selector1_is_proven_image1_core": False,
        "executing_image1_identity_proved": False,
        "qualified_selector1_predicate_bus_range": ["0x46001e68", "0x4600203f"],
        "proposed_fixed_read_windows": rows,
        "physical_picture_observed": False,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
