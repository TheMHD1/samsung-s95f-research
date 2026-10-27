#!/usr/bin/env python3
"""Offline verifier for the AP_EXCO alternate-threshold source context."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct


HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
PACKAGE = BASE / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def cstring(data: bytes, offset: int) -> str:
    return data[offset : data.index(b"\0", offset)].decode("ascii")


def image1(package: bytes, va: int, size: int) -> bytes:
    return package[0x40200 + va : 0x40200 + va + size]


def thumb_bl_target(data: bytes, address: int) -> int:
    need(len(data) == 4, "BL width")
    first, second = struct.unpack("<HH", data)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000, f"BL encoding at {address:#x}")
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
    need(sha256(package) == "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "selected package SHA-256")
    image = package[0x40200 : 0x60200]

    # AP_EXCO table row: seven words, image-0 linked name VA maps to FILE +0x200.
    row_file = 0x3CCBC + 10 * 0x1C
    row = struct.unpack_from("<7I", package, row_file)
    expected_row = (0x3DD8C, 0x2000FF14, 0x33A, 0x2001024E, 0x1200, 0x1B0000, 0x1B0400)
    need(row == expected_row, "AP_EXCO mapping row")
    need(cstring(package, row[0] + 0x200) == "AP_EXCO", "AP_EXCO row name")
    need(sha256(package[row_file : row_file + 0x1C]) == "e3d967a7b74ce674f6c10d2b5c1f945913b1381baa5ac50ad5aec6e4c370713d", "AP_EXCO row slice")
    need(row[1] + row[2] == row[3], "contiguous AP_EXCO destinations")

    # Selected type-4 metadata and exact packaged sources.
    meta = 0x85E00
    need(cstring(package, meta) == "AP_EXCO", "selected metadata name")
    fields = {offset: u32(package, meta + offset) for offset in (0x20, 0x24, 0x28, 0x2C, 0x6C, 0xAC, 0xF0, 0xF4, 0x134, 0x174)}
    expected_fields = {0x20: 4, 0x24: 0x1B0000, 0x28: 1, 0x2C: 0x102200,
                       0x6C: 0, 0xAC: 0x33A, 0xF0: 1, 0xF4: 0x102600,
                       0x134: 0x400, 0x174: 0x1200}
    need(fields == expected_fields, "AP_EXCO metadata schema")
    need(sha256(package[meta : meta + 0x200]) == "dad4caf149769f0b363a11231267d73752802a3bd7484bd720562bbaa7be1cd8", "AP_EXCO metadata slice")
    printable = [match.group().decode("ascii") for match in re.finditer(rb"[ -~]{4,}", package[meta : meta + 0x200])]
    need(printable == ["AP_EXCO"], "no field-level printable schema in metadata")

    first_source = 0x80000 + fields[0x2C]
    second_source = 0x80000 + fields[0xF4]
    need((first_source, second_source) == (0x182200, 0x182600), "AP_EXCO packaged sources")
    need(sha256(package[first_source : first_source + row[2]]) == "c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf", "first AP_EXCO payload")
    need(sha256(package[second_source : second_source + row[4]]) == "5000ce2a135b4b463505a32cf5b525916605b32c21a20de4bd91607d4b839761", "second AP_EXCO payload")
    object_offset = 0x3D8
    second_offset = object_offset - row[2]
    source_file = second_source + second_offset
    destination = row[3] + second_offset
    need(second_offset == 0x9E and source_file == 0x18269E and destination == 0x200102EC, "+3d8 region arithmetic")
    need(package[source_file] == 0x14, "selected AP_EXCO +3d8 byte")

    # Generic successful type-4 copy path is pinned, without claiming execution.
    need(sha256(package[0x6390:0x657C]) == "77b7c1ba77fa1a27fe5882d047fac7c7ecc3375d42cbe947d6bb6108f04d7ab4", "generic type-4 loader")
    need(package[0x644C:0x645C].hex() == "4968299a114488193a464749faf70bfc", "first destination copy sequence")
    need(package[0x6520:0x652C].hex() == "c96888193a461349faf7a3fb", "second destination copy sequence")

    # Startup AP_EXCO lookup, mapped pointer, slot, and getter.
    need(sha256(image1(package, 0x1BB74, 0x1BD4A - 0x1BB74)) == "9297113c033fee2008a35f991c436e798cb1315114f09272fc37e097b7cebb54", "lookup/mapping body")
    need(image1(package, 0x1BD4C, 8) == b"AP_EXCO\0", "startup AP_EXCO key")
    need(u32(image1(package, 0x1BD5C, 4), 0) == 0x200002CC, "source-context slot literal")
    need(thumb_bl_target(image1(package, 0x1BA12, 4), 0x1BA12) == 0x1BCC4, "startup context initialization call")
    need(thumb_bl_target(image1(package, 0x1BCE2, 4), 0x1BCE2) == 0x1BC24, "AP_EXCO first-destination lookup")
    need(image1(package, 0x1BCE6, 4).hex() == "1d490860", "store mapped AP_EXCO pointer in slot")
    need(image1(package, 0x38E8, 12).hex() == "0148006870470000cc020020", "source-context getter")
    mapped_pointer = row[1] + 0x25000000
    need(mapped_pointer == 0x4500FF14 and mapped_pointer + object_offset == 0x450102EC, "mapped source address")

    # Callback registration and exact ordinary copy into fixed context +6c7.
    need(sha256(image1(package, 0x195F8, 0x20)) == "9aa4a70c4e9b87edc2644439503ddc716afc638f00c55b2b0ca2f4c6e8cd4d82", "callback registration body")
    need(direct_callers(image, 0x195F8) == [0xAEF6], "registration direct caller")
    need(u32(image1(package, 0x1961C, 4), 0) == 0x00018C95, "registered callback pointer")
    need(sha256(image1(package, 0x18C94, 0x46)) == "2d4c18c7f439b3e2b2000ca704dc00da89c9ac06b06f35cba1048048ed5e7dae", "registered callback body")
    need(direct_callers(image, 0x3934) == [0x18C96], "source-copy direct caller")
    need(sha256(image1(package, 0x3934, 0x134)) == "ec26ab809b7855bfe374459826c7b00ddacf440b4bfb2d0cfa141a5a504803f2", "source-copy body")
    need(image1(package, 0x394E, 8).hex() == "96f8d80385f8c706", "AP_EXCO+3d8 to fixed+6c7")
    need(image.count(bytes.fromhex("85f8c706")) == 1, "unique exact fixed+6c7 STRB")

    # The two ordinary event-threshold consumers are exact and remain unnamed.
    predicate = image1(package, 0x1E68, 0x2040 - 0x1E68)
    need(sha256(predicate) == "c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a", "event predicate body")
    need(predicate.count(bytes.fromhex("96f8c706")) == 3, "three predicate selector reads")
    for encoded in (bytes.fromhex("42f2c440"), bytes.fromhex("42f23040"), bytes.fromhex("4ff41350")):
        need(encoded in predicate, "alternate threshold encoding")

    result = {
        "schema": "rtp-alternate-source-context-verification-v1",
        "package_sha256": sha256(package),
        "context_name": "AP_EXCO",
        "field_name": None,
        "object_offset": "0x3d8",
        "selected_package_default": package[source_file],
        "mapped_source_address": "0x450102ec",
        "target_cpu_address": "0x20000bc7",
        "mode1_mode6_nonzero_fp_source": "R+0x24c4",
        "live_v6_value_proved": False,
        "active_bank_proved": False,
        "physical_semantics_proved": False,
        "offline_only": True,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
