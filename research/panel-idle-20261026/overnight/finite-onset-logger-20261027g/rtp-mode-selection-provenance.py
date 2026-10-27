#!/usr/bin/env python3
"""Offline verifier for ordinary RTP mode-selector provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
PACKAGE = BASE / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"


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


def occurrences(data: bytes, value: int) -> list[int]:
    pattern = struct.pack("<I", value)
    result: list[int] = []
    start = 0
    while True:
        offset = data.find(pattern, start)
        if offset < 0:
            return result
        result.append(offset)
        start = offset + 1


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


def unpack(data: bytes, source_file: int, size: int) -> tuple[bytes, int]:
    source = source_file
    out = bytearray()
    while len(out) < size:
        tag = data[source]
        source += 1
        literal_count = tag & 7
        if literal_count == 0:
            literal_count = data[source]
            source += 1
        run_count = tag >> 4
        if run_count == 0:
            run_count = data[source]
            source += 1
        need(literal_count >= 1, "invalid literal count")
        for _ in range(literal_count - 1):
            need(len(out) < size, "literal exceeds output")
            out.append(data[source])
            source += 1
        if tag & 8:
            distance = data[source]
            source += 1
            need(0 < distance <= len(out), "invalid back-reference")
            for _ in range(run_count + 2):
                need(len(out) < size, "back-reference exceeds output")
                out.append(out[-distance])
        else:
            need(len(out) + run_count <= size, "zero run exceeds output")
            out.extend(b"\0" * run_count)
    return bytes(out), source


def main() -> None:
    package = pinned(
        PACKAGE,
        "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0",
    )
    need(len(package) == 0x500000, "selected package extent")
    image = package[0x40200 : 0x60200]

    # Exact reset output: aa/ac are zero; +6c7 lies in the subsequent zero fill.
    reset, end = unpack(package, 0x40200 + 0x1D860, 0x4F8)
    need(end == 0x5DB5B, "reset stream consumed extent")
    need(sha256(reset) == "76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8", "reset output")
    need(u16(reset, 0x4AA) == 0 and u16(reset, 0x4AC) == 0, "aa/ac reset defaults")
    zero_start, zero_end = 0x200004F8, 0x200004F8 + 0xDCA4
    need(zero_start <= 0x20000BC7 < zero_end == 0x2000E19C, "+6c7 reset zero-fill inclusion")

    # All aligned literal values in image 1 are pinned, bounding direct refs.
    aa_literals = [x for x in occurrences(image, 0x200004AA) if x % 4 == 0]
    ac_literals = [x for x in occurrences(image, 0x200004AC) if x % 4 == 0]
    need(aa_literals == [0xB7CC, 0xB9B0, 0xBB10, 0xBD50, 0xC030, 0xC248], "aa literal census")
    need(ac_literals == [0xB7D0, 0xB9D0, 0xBB2C, 0xBD54, 0xC040, 0xC24C], "ac literal census")

    expected_slices = {
        (0x3934, 0x3A78): "7133805d06d87607b588f02602bd1bbbf4f818dd3dd2fc0d72ced0f8cf69ef49",
        (0xC220, 0xC244): "c300e75306e19f005a0d9c7774c757a0124bb916d5319237cc5a735360033748",
        (0xB644, 0xB798): "77eaad94857db91496e71c80e7dd23f9509519fa5b0da7b2eac7a0119fba4ffa",
        (0xB8A8, 0xB976): "a40c6da321991212c63a8de7b9aca3e7c65edbdf0ac9c75ba1ed62ac5d290395",
        (0xB9F4, 0xBAF2): "e93aa53bdc7874bf76c29f7b641cbc5c5d06950063cde8de05bf155bba4ba311",
        (0xBBBC, 0xBD2E): "9161e90f083f9e3f230c6e8d6f2b2f2503c7cbcd6c2ca1525e025f116a30dd71",
        (0xBD58, 0xC040): "dc9c513b47436ecce6297c99bb3083be667a254aa5fa210f170d53bd15c6a291",
    }
    for (lo, hi), expected in expected_slices.items():
        need(sha256(image1(package, lo, hi - lo)) == expected, f"body {lo:#x}..{hi:#x}")

    # Startup direct zero stores, ordinary transition blocks, and callback copy.
    need(image1(package, 0xC234, 14).hex() == "0020034908800349088003490880", "startup zero stores")
    need(image1(package, 0xBA60, 42).hex() == "25480088032802d101202349088028480088032802d10120254908802b480088032802d1012029490880", "3-to-1 transitions")
    need(image1(package, 0xB926, 56).hex() == "22480088012809d121480088012805d120a00ff0c6ff02201c49088023480088012809d11a480088012805d120a00ff0b8ff02201d490880", "1-to-2 transitions")
    need(image1(package, 0x394E, 8).hex() == "96f8d80385f8c706", "source+3d8 to fixed+6c7 copy")
    need(package[0x40200:].count(bytes.fromhex("85f8c706")) == 1, "unique exact +6c7 STRB encoding")

    # Positive direct-call reachability for init and alternate-threshold refresh.
    need(thumb_bl_target(image1(package, 0x1BA7E, 4), 0x1BA7E) == 0xC220, "application init call")
    need(direct_callers(image, 0xC220) == [0x1BA7E], "direct init caller census")
    need(direct_callers(image, 0x3934) == [0x18C96], "direct +6c7 refresh caller census")
    need(direct_callers(image, 0x195F8) == [0xAEF6], "ordinary callback-registration caller")
    need(u32(image1(package, 0x1961C, 4), 0) == 0x00018C95, "registered callback pointer")

    # Status selects ac then aa. Tail selects aa then ac. Root +2410 is separate.
    need(image1(package, 0xBA8C, 26).hex() == "27480088012801d1062506e01d480088012801d1042500e00125", "status mode priority")
    need(image1(package, 0xBFAE, 50).hex() == "20480088012805d1324651460420f5f754ff0ee01f480088012805d1324651460620f5f74aff04e0324651460120f5f744ff", "predicate-tail mode priority")
    need(image1(package, 0xBE0C, 10).hex() == "42f21040405b06287eda", "root +2410 scan bound")
    wrapper = image1(package, 0xBBBC, 0xBD2E - 0xBBBC)
    need(wrapper.count(bytes.fromhex("42f21040")) == 3, "three root +2410 wrapper loads")

    # The frozen V6 text has only NORMAL detailed rows before event 736.
    ring = pinned(
        HERE / "onset-v6-event-log.bin",
        "deccf31188b565c7c4c9aadcb838e042c55f81f94ffae7c88093902dc21678ba",
    )
    lines = ring.decode("ascii").splitlines()
    detail = [line for line in lines if line.startswith("[RTP ")]
    need(len(detail) == 31 and all(line.endswith("/m:NORMAL") for line in detail), "V6 NORMAL detailed rows")
    need(lines[-2:] == ["rtp_act_736", "rtp_act_736"], "V6 event tail")

    # Late +2410=4 is a separately addressed bus-window observation.
    rt = pinned(
        HERE / "fault-context-after-v6/rt.bin",
        "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9",
    )
    need(len(rt) == 0x100 and u16(rt, 0x10) == 4, "late bus-window +2410")

    result = {
        "schema": "rtp-mode-selection-provenance-verification-v1",
        "package_sha256": sha256(package),
        "reset_aa": u16(reset, 0x4AA),
        "reset_ac": u16(reset, 0x4AC),
        "reset_20000bc7": 0,
        "mode4_selector_cpu": "uint16[0x200004aa] == 1",
        "mode6_selector_cpu": "aa != 1 && uint16[0x200004ac] == 1",
        "alternate_fp_selector_cpu": "byte[0x20000bc7]",
        "root_2410_is_final_mode_selector": False,
        "late_window_47012410": u16(rt, 0x10),
        "v6_normal_rows": len(detail),
        "internal_unpacker_selector_store": False,
        "asynchronous_change_excluded": False,
        "offline_only": True,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
