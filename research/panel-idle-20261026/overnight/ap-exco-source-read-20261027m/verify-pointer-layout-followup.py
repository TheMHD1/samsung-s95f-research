#!/usr/bin/env python3
"""Offline verifier for the corrected image-1 configuration-pointer layout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


ROOT = Path("${S95F_EVIDENCE_ROOT}/panel-idle-20261026")
PACKAGE = ROOT / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CAPTURE = ROOT / "overnight/ap-exco-source-read-20261027m/capture-once"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def image1(data: bytes, va: int, size: int) -> bytes:
    return data[0x40200 + va:0x40200 + va + size]


def cstring(data: bytes, file_offset: int) -> str:
    end = data.index(b"\0", file_offset, file_offset + 64)
    return data[file_offset:end].decode("ascii")


def thumb_bl_target(data: bytes, va: int) -> int:
    first, second = struct.unpack_from("<HH", data, 0x40200 + va)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"BL encoding {va:#x}")
    s = (first >> 10) & 1
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    i1 = 1 ^ (j1 ^ s)
    i2 = 1 ^ (j2 ^ s)
    value = ((s << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return va + 4 + value


def thumb_adr_target(data: bytes, va: int) -> int:
    instruction = u16(data, 0x40200 + va)
    need(instruction & 0xF800 == 0xA000, f"ADR encoding {va:#x}")
    return ((va + 4) & ~3) + (instruction & 0xFF) * 4


def thumb_ldr_literal(data: bytes, va: int) -> int:
    instruction = u16(data, 0x40200 + va)
    need(instruction & 0xF800 == 0x4800, f"LDR literal encoding {va:#x}")
    literal_va = ((va + 4) & ~3) + (instruction & 0xFF) * 4
    return u32(data, 0x40200 + literal_va)


def unpack_scatter(data: bytes, source: int, size: int) -> bytes:
    out = bytearray()
    while len(out) < size:
        tag = data[source]
        source += 1
        literals = tag & 7
        if literals == 0:
            literals = data[source]
            source += 1
        run = tag >> 4
        if run == 0:
            run = data[source]
            source += 1
        need(literals >= 1, "scatter literal count")
        for _ in range(literals - 1):
            need(len(out) < size, "scatter literal overrun")
            out.append(data[source])
            source += 1
        if tag & 8:
            distance = data[source]
            source += 1
            need(distance != 0 and distance <= len(out), "scatter distance")
            for _ in range(run + 2):
                need(len(out) < size, "scatter back-reference overrun")
                out.append(out[-distance])
        else:
            need(len(out) + run <= size, "scatter zero overrun")
            out.extend(b"\0" * run)
    return bytes(out)


def main() -> None:
    package = PACKAGE.read_bytes()
    need(len(package) == 0x500000, "package extent")
    need(sha256(package) ==
         "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0",
         "package pin")

    pointer = (CAPTURE / "pointer-window.bin").read_bytes()
    need(len(pointer) == 32 and sha256(pointer) ==
         "7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3",
         "captured pointer window")
    result_raw = (CAPTURE / "result.json").read_bytes()
    need(sha256(result_raw) ==
         "ffba3a63943e30fe689a1251237dfe18dcadff0c6eb5aec1022c3ac1eb20e901",
         "capture result pin")
    result = json.loads(result_raw)
    need(result["transport_accepted"] is True and result["cleanup"] == "STAGE_ABSENT",
         "capture acceptance")
    need(result["pointer_raw_sha256"] == sha256(pointer), "capture/result raw binding")
    source_base = (CAPTURE / "source-base-window.bin").read_bytes()
    source_tail = (CAPTURE / "source-tail-window.bin").read_bytes()
    need(len(source_base) == 16 and sha256(source_base) ==
         "374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb",
         "captured standard AP_EXCO base window")
    need(len(source_tail) == 32 and sha256(source_tail) ==
         "f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b",
         "captured standard AP_EXCO tail window")
    need(source_base == bytes(16), "captured base is not all zero")
    need(source_tail == package[0x182692:0x1826B2], "captured tail/package comparison")
    need(source_base != package[0x182200:0x182210], "full base unexpectedly matches package")
    words = list(struct.unpack("<8I", pointer))
    expected_words = [0x00000001, 0x4500FF14, 0x4501024E, 0x450158A8,
                      0x450130B6, 0x450130F0, 0x4500F0E0, 0x0001B691]
    need(words == expected_words, "captured pointer words")

    # The exact seven startup stores are: three AP_EXCO lookups, two AP_TED
    # lookups, AP, and MULTI. Decode their names, call targets and destination
    # literals instead of assuming one call in isolation describes the layout.
    calls = [0x1BCCA, 0x1BCD6, 0x1BCE2, 0x1BCEE, 0x1BCFA, 0x1BD06, 0x1BD12]
    expected = [
        ("AP_EXCO", 0x1BBFC, 0x200002C4),
        ("AP_EXCO", 0x1BBD4, 0x200002C8),
        ("AP_EXCO", 0x1BC24, 0x200002CC),
        ("AP_TED",  0x1BBFC, 0x200002D0),
        ("AP_TED",  0x1BBD4, 0x200002D4),
        ("AP",      0x1BBFC, 0x200002D8),
        ("MULTI",   0x1BC24, 0x200002BC),
    ]
    decoded = []
    for call, wanted in zip(calls, expected):
        name_va = thumb_adr_target(package, call - 4)
        name = cstring(package, 0x40200 + name_va)
        target = thumb_bl_target(package, call)
        slot = thumb_ldr_literal(package, call + 4)
        need(u16(package, 0x40200 + call + 6) == 0x6008, "startup STR")
        got = (name, target, slot)
        need(got == wanted, f"startup triplet at {call:#x}")
        decoded.append(got)

    startup = image1(package, 0x1BCC4, 0x84)
    need(sha256(startup) ==
         "344accecffd7cff7fb1e7e56ec85778bfa99a9b12646223f34a84e43fb49288b",
         "startup body")

    # The standard first/second lookup wrappers use discriminator 0x10000 and
    # select row words +4 and +12 respectively. The third wrapper uses a
    # distinct 0x1000c namespace and selects its row word +4.
    wrappers = {
        0x1BBD4: (0x1BBFC, "c1da8944bfcffd4f8cfcfe01737c040e21f4dd8c1c1c76ab960e5de8bac25922", 0x10000, "second"),
        0x1BBFC: (0x1BC24, "0c718c8af720ca992a613b0a9cc6091f76ce58ec7160d229af12af03d40c5b53", 0x10000, "first"),
        0x1BC24: (0x1BC4C, "5a79a33e09ba696ab0ff9eb60bdcec8c1a1aabd20b7f4a3cd02f93f5942c0960", 0x1000C, "alternate"),
    }
    for start, (end, digest, discriminator, _) in wrappers.items():
        body = image1(package, start, end - start)
        need(sha256(body) == digest, f"lookup wrapper {start:#x}")
        need(u32(body, len(body) - 4) == discriminator, f"lookup discriminator {start:#x}")
    need(bytes.fromhex("e968") in image1(package, 0x1BBD4, 0x28), "second-row +12 load")
    need(bytes.fromhex("6968") in image1(package, 0x1BBFC, 0x28), "first-row +4 load")
    need(bytes.fromhex("6968") in image1(package, 0x1BC24, 0x28), "alternate-row +4 load")

    # The common lookup maps the wrapper-provided root (0x10000 or 0x1000c),
    # follows its descriptor and entry-array words, walks fixed-stride entries,
    # and compares each entry name through the ordinary string comparator.
    # This proves the literals select distinct registry roots rather than being
    # interchangeable constants.
    map_thin = image1(package, 0x1BBC4, 0x10)
    common = image1(package, 0x1BC4C, 0x78)
    need(sha256(map_thin) ==
         "a41b0741bbbca8b34615f29930d5585edcbeebdb2bb00223a629f95eee232c74",
         "mapping thunk")
    need(sha256(common) ==
         "de75682718d9e334652ad449ae8ccc62445ee631d5b670c10dbb145be1eda83e",
         "common registry lookup")
    need(thumb_bl_target(package, 0x1BC58) == 0x1BBC4,
         "common root mapping call")
    need(thumb_bl_target(package, 0x1BC6A) == 0x1BB74 and
         thumb_bl_target(package, 0x1BC84) == 0x1BB74 and
         thumb_bl_target(package, 0x1BCA2) == 0x1BB74,
         "common descriptor/entry mapping calls")
    need(thumb_bl_target(package, 0x1BCAE) == 0x89C,
         "common entry-name comparison")

    # Standard configuration table rows explain five neighboring live words.
    standard = package[0x3CCBC:0x3CF08]
    need(sha256(standard) ==
         "669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287",
         "standard configuration table")
    rows = [struct.unpack_from("<7I", standard, i * 0x1C) for i in range(21)]
    named = {cstring(package, row[0] + 0x200): row for row in rows}
    need(named["AP_EXCO"] ==
         (0x3DD8C, 0x2000FF14, 0x33A, 0x2001024E, 0x1200, 0x1B0000, 0x1B0400),
         "standard AP_EXCO row")
    need(named["AP_TED"] ==
         (0x3DE4C, 0x200130B6, 0x3A, 0x200130F0, 0xF42, 0x190000, 0x190200),
         "standard AP_TED row")
    need(named["AP"] ==
         (0x3DE88, 0x2000F0E0, 0x40C, 0, 0, 0x130000, 0),
         "standard AP row")

    # The distinct MULTI namespace contains an AP_EXCO entry whose first
    # destination is 0x200158a8. It is the exact origin of slot 0x200002cc.
    alternate = package[0x3C5B8:0x3C5D4]
    need(sha256(alternate) ==
         "41dfa8809a435830065f05cbcf22bc20ee9b0f4b4f773e3d49f02f3b04403f66",
         "alternate table record")
    alt_words = struct.unpack("<7I", alternate)
    need(alt_words == (0x3DD84, 0x3D44B, 2, 0x3DD8C, 0x200158A8, 0x3EC, 0x18),
         "MULTI/AP_EXCO alternate record")
    need(cstring(package, 0x200 + alt_words[0]) == "MULTI", "alternate table name")
    need(cstring(package, 0x200 + alt_words[3]) == "AP_EXCO", "alternate entry name")

    expected_by_slot = {
        0x200002C4: named["AP_EXCO"][1] + 0x25000000,
        0x200002C8: named["AP_EXCO"][3] + 0x25000000,
        0x200002CC: alt_words[4] + 0x25000000,
        0x200002D0: named["AP_TED"][1] + 0x25000000,
        0x200002D4: named["AP_TED"][3] + 0x25000000,
        0x200002D8: named["AP"][1] + 0x25000000,
    }
    for slot, expected_value in expected_by_slot.items():
        captured_value = words[(slot - 0x200002C0) // 4]
        need(captured_value == expected_value, f"captured slot {slot:#x}")

    # Reset scatter initializes +0xdc to an odd linked-code address and zeros
    # the dynamic slots. This independently explains the last capture word.
    reset = unpack_scatter(package, 0x5DA60, 0x4F8)
    need(sha256(reset) ==
         "76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8",
         "reset row")
    for address in range(0x200002C0, 0x200002DC, 4):
        need(u32(reset, address - 0x20000000) == 0, f"reset dynamic slot {address:#x}")
    need(u32(reset, 0x2DC) == 0x1B691 and words[7] == 0x1B691,
         "reset-initialized linked-code word")

    # Getter 0x38e8 reads 0x200002cc. The ordinary callback calls it and then
    # reads byte +1 into r8, copies byte +0x3d8 to context +0x6c7, and copies
    # byte +0 to context +0x6c8. Therefore the callback source is the alternate
    # 0x450158a8 object, not either standard AP_EXCO allocation sampled by the
    # other two capture windows. The role of the extra +1 value remains unnamed.
    getters = image1(package, 0x38E8, 0x20)
    need(sha256(getters) ==
         "6cecc2e176e4eebe73302ec1a1644613b705fe843044ee0aa279f547b5c82c4c",
         "getter block")
    need(getters[:12].hex() == "0148006870470000cc020020", "0x38e8 getter")
    callback = image1(package, 0x3934, 0x2C)
    need(sha256(callback) ==
         "3eb32bd2a2930a045ee01a9c605e81d7ef9e2f8ca07615ebae8837efad9f8a72",
         "callback prefix")
    need(thumb_bl_target(package, 0x393E) == 0x38E8, "callback source getter")
    need(bytes.fromhex("96f80180") in callback, "callback source +1 to r8")
    need(bytes.fromhex("96f8d80385f8c706") in callback,
         "callback source +3d8 to context +6c7")
    need(bytes.fromhex("307885f8c806") in callback,
         "callback source +0 to context +6c8")

    print(json.dumps({
        "schema": "ap-exco-pointer-layout-followup-v1",
        "offline_only": True,
        "target_operations": 0,
        "capture_pointer_sha256": sha256(pointer),
        "bus_window_maps_without_shift": True,
        "global_minus_8_relocation_supported": False,
        "slots": {hex(slot): hex(value) for slot, value in expected_by_slot.items()},
        "source_getter_slot": "0x200002cc",
        "source_pointer": "0x450158a8",
        "source_copy_offsets": {"r8_unnamed": "0x1", "context_6c7": "0x3d8",
                                "context_6c8": "0x0"},
        "standard_ap_exco_pointers": ["0x4500ff14", "0x4501024e"],
        "previous_pointer_interpretation_mistaken": True,
        "previous_source_windows_are_valid_raw_standard_ap_exco_samples": True,
        "previous_source_windows_sample_callback_source": False,
        "standard_base_window_all_zero": True,
        "standard_base_window_matches_full_packaged_window": False,
        "standard_tail_window_matches_full_packaged_window": True,
        "semantic_or_physical_meaning_proved": False,
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
