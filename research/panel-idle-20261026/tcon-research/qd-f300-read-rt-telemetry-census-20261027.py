#!/usr/bin/env python3
"""Offline, hash-gated checks for the selected-profile F3:00 read census.

This program reads only a caller-supplied local copy of the 5 MiB profile.
It does not construct a transport command or access a device.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


PROFILE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
PROFILE_SIZE = 5_242_880
FILE_BIAS = 0x200
TABLE_FILE = 0x219B0
TABLE_PC = 0x217B0
TABLE_COUNT = 0xBD
ZERO_TARGET = 0x21DEA


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def s32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<i", data, offset)[0]


def cstring(data: bytes, offset: int) -> str:
    end = data.index(0, offset)
    return data[offset:end].decode("ascii")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("profile", type=Path)
    ns = ap.parse_args()
    blob = ns.profile.read_bytes()
    need(len(blob) == PROFILE_SIZE, "profile size mismatch")
    need(sha(blob) == PROFILE_SHA256, "profile SHA-256 mismatch")

    slices = {
        "root_accessor": (0xF194, 0xF19C, "ac0f29fcf915e5ca06f49bce9cf9cf8e41fb1b01d5b7905895ac28d9d03cc131"),
        "f300_dispatcher": (0x21824, 0x21876, "5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe"),
        "second_range_helper": (0x21908, 0x2194A, "2c1cbc82be26278fcbc637e1287f9d89514d3d3468bf48e0b0140d39b1d90748"),
        "main_getter": (0x2194C, 0x21FF0, "fc3bbd7a16650a34ce0105c0174f6e5099e8f0fc5722844649149016c1cdea07"),
        "branch_table": (0x219B0, 0x21CA4, "f5e7defc0e7189ddd0f4ce2c5a7b31b0124ea9248e003c895e3e8a54112485dc"),
        "response_bookkeeping": (0x5B24, 0x5B5A, "a8dc7f55717424be6f692640e86c7961f4e226936f9852ac4887d6d7a4286607"),
        "selector_f4_read": (0x21E9C, 0x21EA8, "e25a67adde9bf90b21f37ca1b8b34dda27703902168649ba86a0ea969afe0415"),
        "selector_144_read": (0x21EF8, 0x21F06, "f73ebc0b8f82afc64b7219d76cea55e69d45c36cef163fc45febf74f115c6f05"),
        "selector_1b4_read": (0x21F9C, 0x21FA8, "ac12c5709c143cd602051973947e2a9061371084deac9dcaf82401991f6b3a24"),
        "selector_e0_indirect_writer": (0x25E58, 0x25E70, "f4130608031e6017621231c58042476c0757c2c0fd997c0980304b12e3653a92"),
        "selector_f4_writer": (0x2CF26, 0x2CF36, "ff18e8cd2e1eb779a6a1697fb56147ca9750001b4641d9a3b17d5df23edb9860"),
        "selector_144_writer": (0x2CFBA, 0x2CFD6, "ca3cc33d01499d0e216ac93f99319e70f4fc80f01a863046242acc5fa7f64395"),
        "configuration_map": (0x3CCBC, 0x3CF08, "669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287"),
    }
    for name, (start, end, expected) in slices.items():
        need(sha(blob[start:end]) == expected, f"slice mismatch: {name}")

    # The accessor is linked VA 0xef94 and stored at FILE 0xf194.
    need(blob[0xF194:0xF19C] == bytes.fromhex("0048704700000147"), "root accessor bytes")

    selectors = []
    by_target: dict[int, list[int]] = {}
    for index in range(TABLE_COUNT):
        selector = (index + 9) * 4
        target = (TABLE_PC + s32(blob, TABLE_FILE + index * 4)) & 0xFFFFFFFF
        selectors.append({"selector": selector, "target_va": target})
        by_target.setdefault(target, []).append(selector)
    need(len(selectors) == 189, "first-range selector count")
    need(len(by_target) == 161, "first-range distinct target count")

    expected_direct = {0xF4: 0x21C9C, 0x144: 0x21CF8, 0x1B4: 0x21D9C}
    actual = {row["selector"]: row["target_va"] for row in selectors}
    need(all(actual[k] == v for k, v in expected_direct.items()), "direct-root selector targets")
    zero_selectors = by_target[ZERO_TARGET]
    need(zero_selectors == [
        0x34, 0xE8, 0xEC, 0xF0, 0xF8, 0x14C, 0x154, 0x168,
        0x178, 0x17C, 0x184, 0x188, 0x18C, 0x194, 0x19C, 0x1A0,
        0x1A4, 0x1A8, 0x1AC, 0x1C0, 0x1C4, 0x1C8, 0x1CC, 0x1D8,
        0x1DC, 0x1E0, 0x25C, 0x260, 0x2DC,
    ], "zero-target selector inventory")
    need(not ({0x637C, 0x11058, 0x1148C, 0x2A2F8} & set(by_target)),
         "generic logical reader/callers unexpectedly present in selector targets")

    # The aligned second range is closed by the separately pinned helper.
    second_range = list(range(0x31C, 0x4D8 + 1, 4))
    need(len(second_range) == 112, "second-range selector count")
    need(len(selectors) + len(second_range) == 301, "total F3:00 selector positions")

    # Decode the 21-row physical/logical configuration table.  Name pointers
    # are linked image-0 VAs, hence FILE=VA+0x200.
    rows = {}
    for index in range(21):
        words = struct.unpack_from("<7I", blob, 0x3CCBC + 0x1C * index)
        rows[cstring(blob, words[0] + FILE_BIAS)] = {
            "index": index,
            "first": [words[1], words[2]],
            "second": [words[3], words[4]],
            "logical": [words[5], words[6]],
        }
    expected_rows = {
        "AP_ZA": {"index": 7, "first": [0x47012500, 0x270], "second": [0x2000F560, 0x262], "logical": [0x160000, 0x160300]},
        "AP_SBD": {"index": 8, "first": [0x470129D8, 0x34], "second": [0x47012A0C, 0xD3C], "logical": [0x170000, 0x170400]},
        "AP_RTP": {"index": 14, "first": [0x47012400, 0x100], "second": [0x47010000, 0x2400], "logical": [0x210000, 0x210400]},
        "AP_HUT": {"index": 17, "first": [0x4701377C, 0x3E0], "second": [0x47013B5C, 0xC60], "logical": [0x240000, 0x240800]},
    }
    for name, wanted in expected_rows.items():
        need(rows[name] == wanted, f"configuration row mismatch: {name}")

    fields = {
        "selector_0xf4": {"address": 0x470129DA, "row": "AP_SBD", "row_offset": 2, "width": 1},
        "selector_0x144": {"address": 0x47012748, "row": "AP_ZA", "row_offset": 0x248, "width": 2},
        "selector_0x1b4": {"address": 0x47013826, "row": "AP_HUT", "row_offset": 0xAA, "width": 1},
    }
    for field in fields.values():
        first, length = rows[field["row"]]["first"]
        need(first + field["row_offset"] == field["address"], "field address arithmetic")
        need(field["row_offset"] + field["width"] <= length, "field outside configuration row")
        need(not (0x47012400 <= field["address"] < 0x47012500), "field overlaps AP_RTP first region")
        need(not (0x47010000 <= field["address"] < 0x47012400), "field overlaps AP_RTP second region")

    # Selected package directory records and first-payload defaults.  These
    # are initialization bytes, not live values.
    directory = {}
    for index in range(57):
        record = 0x80200 + 0x200 * index
        name = blob[record:record + 0x20].split(b"\0", 1)[0].decode("ascii")
        directory[name] = {
            "index": index,
            "record": record,
            "type": u32(blob, record + 0x20),
            "logical": u32(blob, record + 0x24),
            "present1": u32(blob, record + 0x28),
            "source1": u32(blob, record + 0x2C),
            "offset1": u32(blob, record + 0x6C),
            "length1": u32(blob, record + 0xAC),
        }
    dir_expect = {
        "AP_ZA": [40, 0x160000, 0xF2E00, 0x26E],
        "AP_SBD": [41, 0x170000, 0xF3600, 0x34],
        "AP_HUT": [52, 0x240000, 0x108A00, 0x112],
    }
    defaults = {}
    cfg_base = 0x80000
    for name, (index, logical, source, length) in dir_expect.items():
        rec = directory[name]
        need([rec["index"], rec["logical"], rec["source1"], rec["length1"]] ==
             [index, logical, source, length], f"directory mismatch: {name}")
        need(rec["type"] == 4 and rec["present1"] == 1 and rec["offset1"] == 0,
             f"directory gates: {name}")
    for label, spec in fields.items():
        rec = directory[spec["row"]]
        at = cfg_base + rec["source1"] + spec["row_offset"]
        raw = blob[at:at + spec["width"]]
        need(len(raw) == spec["width"], "default bytes truncated")
        defaults[label] = int.from_bytes(raw, "little")
    need(defaults == {"selector_0xf4": 0, "selector_0x144": 0, "selector_0x1b4": 0},
         "unexpected selected-package defaults")

    # Pair the two writable fields with the exact F3:00 write dispatch table.
    write_table_file = 0x2C9B4
    write_pc = 0x2C7B4
    write_targets = {
        selector: (write_pc + s32(blob, write_table_file + (selector // 4 - 9) * 4)) & 0xFFFFFFFF
        for selector in (0xE0, 0xF4, 0x144, 0x1B4)
    }
    need(write_targets == {0xE0: 0x2CD14, 0xF4: 0x2CD26, 0x144: 0x2CDBA, 0x1B4: 0x2CF4C},
         "paired write targets")

    result = {
        "profile_sha256": PROFILE_SHA256,
        "mapping": "image0 FILE = linked VA + 0x200",
        "first_range_entries": len(selectors),
        "first_range_distinct_targets": len(by_target),
        "second_range_entries": len(second_range),
        "total_aligned_positions": len(selectors) + len(second_range),
        "direct_0x47010000_fields": fields,
        "selected_package_initial_values": defaults,
        "paired_write_targets": {hex(k): hex(v) for k, v in write_targets.items()},
        "generic_reader_is_direct_selector_target": False,
        "slice_sha256": {name: expected for name, (_, _, expected) in slices.items()},
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
