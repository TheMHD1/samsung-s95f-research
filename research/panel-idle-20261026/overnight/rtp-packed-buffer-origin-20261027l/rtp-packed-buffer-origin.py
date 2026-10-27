#!/usr/bin/env python3
"""Offline verifier for the selected image-1 RTP packed-buffer origin."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
PACKAGE = (HERE.parent / "selected-qd-profile-copy-20261027b" /
           "F_RSM1_BN9659934B_COMMON.bin")
PACKAGE_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def image1(package: bytes, va: int, size: int) -> bytes:
    answer = package[0x40200 + va:0x40200 + va + size]
    need(len(answer) == size, f"short image-1 slice {va:#x}")
    return answer


def exact(package: bytes, va: int, expected_hex: str, label: str) -> None:
    expected = bytes.fromhex(expected_hex)
    need(image1(package, va, len(expected)) == expected, label)


def thumb_bl_target(data: bytes, address: int) -> int:
    need(len(data) == 4, "BL width")
    first, second = struct.unpack("<HH", data)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"not BL at {address:#x}")
    sign = (first >> 10) & 1
    j1, j2 = (second >> 13) & 1, (second >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ sign), 1 ^ (j2 ^ sign)
    value = ((sign << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def direct_callers(image: bytes, target: int) -> list[int]:
    answer: list[int] = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
            continue
        if thumb_bl_target(image[address:address + 4], address) == target:
            answer.append(address)
    return answer


def unpack_scatter(data: bytes, source_file: int, size: int) -> tuple[bytes, int]:
    """Exact byte behavior of the selected image-1 scatter handler VA 0x17c."""
    source = source_file
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
        need(literals >= 1, "invalid literal count")
        for _ in range(literals - 1):
            need(len(out) < size, "literal exceeds output")
            out.append(data[source])
            source += 1
        if tag & 8:
            distance = data[source]
            source += 1
            need(0 < distance <= len(out), "invalid back-reference")
            for _ in range(run + 2):
                need(len(out) < size, "back-reference exceeds output")
                out.append(out[-distance])
        else:
            need(len(out) + run <= size, "zero run exceeds output")
            out.extend(b"\0" * run)
    return bytes(out), source


def producer_sequence(initial: int) -> tuple[list[int], int, int, int]:
    need(initial in (0, 1, 2), "selector range")
    selector = initial
    written: list[int] = []
    for _ in range(2):
        written.append(selector)
        selector = (selector + 1) % 3
    return written, selector, selector, (selector + 1) % 3


def producer_source(byte: int, signed_half: int) -> int:
    need(0 <= byte <= 0xFF and -0x8000 <= signed_half <= 0x7FFF,
         "descriptor fixture range")
    return (0x60000000 + byte * 0x195 * 0x10000 +
            signed_half * 3 * 0x400) & 0xFFFFFFFF


def main() -> None:
    package = PACKAGE.read_bytes()
    need(len(package) == 0x500000 and sha(package) == PACKAGE_SHA,
         "selected package identity")
    image = package[0x40200:0x60200]
    need(len(image) == 0x20000, "image-1 extent")

    slices = {
        (0x334, 0x366): "b2aefc02a6d456028382364dd89e64689f24343922d19d16a96dabda2698368c",
        (0x3934, 0x3A68): "ec26ab809b7855bfe374459826c7b00ddacf440b4bfb2d0cfa141a5a504803f2",
        (0xB7EC, 0xB890): "933064bf5a35c03a6d48db614f1cc4aec4cbadf9da35a30bdb4777168fb3372a",
        (0x18AE8, 0x18C10): "6b428beae0cda70ec9f2b07e6f68560148c2b06b5ee72eb8c8e5e08b9aec6c41",
        (0x18C94, 0x18CDA): "2d4c18c7f439b3e2b2000ca704dc00da89c9ac06b06f35cba1048048ed5e7dae",
        (0x18CE0, 0x18D18): "619c8ebc99810e3d9ff88c57d18f5b36fcb76185851938d9b35f9c8fa7bd52ca",
        (0x195F8, 0x19616): "3df948ab1f327e3ea2297d0b04f4ab547a76c30fefcdb0fd88e4193532ad9b48",
        (0x1C12C, 0x1C1A0): "3db9bd26b251decf450baa9f21d1d589253cfceaeb921ee4df371ebc0885e756",
    }
    for (start, end), expected in slices.items():
        need(sha(image[start:end]) == expected, f"code slice {start:#x}..{end:#x}")

    # Positive byte checks for the aperture base, CPU-copy body, selector
    # update, corrected pointer fallback, and fixed snapshots.
    exact(package, 0x18AE8, "2de9f0414ff0c045002482e0",
          "producer setup and 0x60000000 base")
    exact(package, 0x334,
          "2de9f05fb1e8f00f40f8044b40f8045b40f8046b40f8047b40f8048b40f8049b40f804ab40f804bba2f10102002ae9d1bde8",
          "eight-word CPU copy")
    exact(package, 0x18BE4,
          "0c480078401c032190fbf1f201fb120008490870641c022cfff47aaf",
          "selector advance and two-iteration loop")
    exact(package, 0xB80C,
          "01200df067fa2049086000200df062fa1e490860",
          "selector writes A/B pointer slots")
    exact(package, 0xB87A,
          "33462a4606480168083103480068083000f065fa",
          "corrected A/B dynamic fallback")
    exact(package, 0x1C152, "4ff436621348016808311248e4f7d5fa",
          "fixed-buffer copy zero")
    exact(package, 0x1C17E, "4ff436620848016808310848e4f7bffa",
          "fixed-buffer copy one")

    literals = {
        0x18C14: 0x2000A60C, 0x18C18: 0x20253000,
        0x3A68: 0x2000A60A, 0x3A6C: 0x58601408,
        0xB890: 0x2000BA40, 0xB894: 0x20000494,
        0xB898: 0x20000498, 0xB8A0: 0x20015000,
        0xB8A4: 0x20015F10, 0x19618: 0x20000460,
        0x1961C: 0x00018C95, 0x19620: 0x20000468,
        0x1C1A0: 0x200004C4, 0x1C1A4: 0x20000498,
        0x1C1A8: 0x20015000, 0x1C1AC: 0x20015F10,
    }
    need({address: u32(image, address) for address in literals} == literals,
         "bounded literal set")
    need(direct_callers(image, 0x18AE8) == [0x18CC4], "producer caller")
    need(direct_callers(image, 0x3934) == [0x18C96], "refresh caller")
    need(direct_callers(image, 0x195F8) == [0xAEF6], "registration caller")
    need(direct_callers(image, 0x1C12C) == [0xB682, 0xB828], "snapshot callers")
    for call, target, label in (
        (0x18B3C, 0x334, "producer CPU copy"),
        (0x18C96, 0x3934, "callback refresh"),
        (0x18CC4, 0x18AE8, "callback producer"),
        (0xB80E, 0x18CE0, "A selector"),
        (0xB818, 0x18CE0, "B selector"),
        (0x1C15E, 0x70C, "fixed copy zero"),
        (0x1C18A, 0x70C, "fixed copy one"),
    ):
        need(thumb_bl_target(image[call:call + 4], call) == target, label)

    rows_expected = [
        (0x1D860, 0x20000000, 0x4F8, 0x17C),
        (0x1D95C, 0x20015000, 0xB50, 0x17C),
        (0x1D974, 0x20015F10, 0xB50, 0x17C),
        (0x1D98C, 0x2020A000, 0x2D30, 0x17C),
        (0x1D9E8, 0x20253000, 0x223C, 0x17C),
        (0x1DA30, 0x20209000, 0x6C0, 0x17C),
        (0x1DA40, 0x20209800, 0x6C0, 0x17C),
        (0x1DA50, 0x20269000, 0x4890, 0x17C),
        (0x1D95C, 0x200004F8, 0xDCA4, 0x1D8),
    ]
    rows = [struct.unpack_from("<4I", package, 0x5D8A4 + index * 16)
            for index in range(9)]
    need(rows == rows_expected, "image-1 scatter table")
    decoded = {
        1: (0x5DB74, "808d2153198f84442b311077821f6e655e9097896c29c71da39d359f76db7dac"),
        2: (0x5DB8C, "808d2153198f84442b311077821f6e655e9097896c29c71da39d359f76db7dac"),
        4: (0x5DC2E, "4290d3193916dd060be99b27952016e9dff2d1c6e5feb65259f40fc6f0c57808"),
    }
    for index, (expected_end, expected_sha) in decoded.items():
        source, _, size, _ = rows[index]
        output, end = unpack_scatter(package, 0x40200 + source, size)
        need(end == expected_end and sha(output) == expected_sha,
             f"scatter decode row {index}")
        need(output == bytes(size), f"scatter row {index} not zero")

    need(0xB68 == 8 + 0xB60 and 0x5B * 8 * 4 == 0xB60,
         "slot/copy geometry")
    need(0x20253002 + 3 * 0xB68 <= 0x20253000 + 0x223C,
         "three slots fit ring allocation")
    need([producer_sequence(value) for value in range(3)] == [
        ([0, 1], 2, 2, 0), ([1, 2], 0, 0, 1), ([2, 0], 1, 1, 2)
    ], "producer writes consecutive slots")

    exco = package[0x83C00:0x83E00]
    need(sha(exco) == "2dfc6d013c0907962adfed3750534b32f70bbcbfe278020f3aef5a6368789d6a",
         "EXCO_PAR2_S0 record hash")
    need(exco[:32] == b"EXCO_PAR2_S0" + bytes(20), "EXCO record name")
    need(tuple(u32(exco, offset) for offset in (0x20, 0x24, 0x28, 0x2C, 0xAC)) ==
         (7, 0x58601400, 1, 0xC8C00, 0x2600), "EXCO metadata")
    need(u32(exco, 0x24) + 8 == u32(image, 0x3A6C), "EXCO +8 refresh root")

    need(producer_source(0, 0) == 0x60000000, "zero source fixture")
    need(producer_source(1, 1) == 0x61950C00, "positive source fixture")
    need(producer_source(0, -1) == 0x5FFFF400, "signed source fixture")

    print(json.dumps({
        "schema": "rtp-packed-buffer-origin-verification-v1",
        "selected_package_sha256": PACKAGE_SHA,
        "copy_kind": "CPU eight-word loop",
        "source_aperture": "0x60000000 plus EXCO-derived descriptor arithmetic",
        "payload_bytes_per_slot": 0xB60,
        "slot_stride": 0xB68,
        "slots_written_per_call": 2,
        "same_slot_overwrite": False,
        "dynamic_pointer_slots": {"A": "0x20000494", "B": "0x20000498"},
        "fixed_A_payloads": ["0x20015000", "0x20015f10"],
        "physical_stream_identity_proved": False,
        "display_pixel_identity_proved": False,
        "loopback_identity_proved": False,
        "sensor_identity_proved": False,
        "selected_image_live_execution_proved": False,
        "offline_only": True,
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()

