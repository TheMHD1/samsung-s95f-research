#!/usr/bin/env python3
"""Reproduce the bounded USB/UART-to-AP_RTP read-route audit offline.

This program reads only the already-copied selected profile.  It does not
open a USB device, UART, TV, controller, process, network endpoint, or root
interface, and it deliberately emits no command bytes or invocation recipe.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = (ROOT / "overnight/selected-qd-profile-copy-20261027b/"
           "F_RSM1_BN9659934B_COMMON.bin")
PROFILE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
FILE_BASE = 0x200
IMAGE0_END = 0x40000


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def digest(data: bytes, start: int, end: int) -> str:
    return hashlib.sha256(data[start:end]).hexdigest()


def thumb_bl_target(data: bytes, linked_va: int) -> int | None:
    """Decode a Thumb-2 immediate BL at one linked image-0 address."""
    offset = FILE_BASE + linked_va
    first, second = u16(data, offset), u16(data, offset + 2)
    if (first & 0xF800) != 0xF000 or (second & 0xD000) != 0xD000:
        return None
    s = (first >> 10) & 1
    j1, j2 = (second >> 13) & 1, (second >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ s), 1 ^ (j2 ^ s)
    immediate = ((s << 24) | (i1 << 23) | (i2 << 22) |
                 ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if s:
        immediate -= 1 << 25
    return (linked_va + 4 + immediate) & 0xFFFFFFFF


def direct_bl_callers(data: bytes, target: int,
                      start: int = 0, end: int = IMAGE0_END - FILE_BASE) -> list[int]:
    return [va for va in range(start, end - 3, 2)
            if thumb_bl_target(data, va) == target]


def raw_hits(data: bytes, value: int, start: int = 0,
             end: int = IMAGE0_END) -> list[int]:
    needle = struct.pack("<I", value)
    result: list[int] = []
    cursor = start
    while True:
        cursor = data.find(needle, cursor, end)
        if cursor < 0:
            return result
        result.append(cursor)
        cursor += 1


def cstring(data: bytes, offset: int) -> str:
    end = data.index(b"\0", offset)
    return data[offset:end].decode("ascii")


def main() -> None:
    data = PROFILE.read_bytes()
    need(len(data) == 0x500000, "profile size changed")
    need(hashlib.sha256(data).hexdigest() == PROFILE_SHA256,
         "profile hash changed")
    need(u32(data, 0x200) == 0x20020000 and u32(data, 0x204) == 0x345,
         "canonical image-0 vector changed")

    # AP_RTP table row 14 and the exact one-halfword address resolution.
    row = struct.unpack_from("<7I", data, 0x3CCBC + 14 * 0x1C)
    need(cstring(data, row[0] + FILE_BASE) == "AP_RTP", "AP_RTP name changed")
    need(row[1:] == (0x47012400, 0x100, 0x47010000, 0x2400,
                     0x210000, 0x210400), "AP_RTP table row changed")
    logical = 0x21000A
    low = logical & 0xFFFF
    need((logical >> 16) == (row[5] >> 16) and low < row[2],
         "logical address left AP_RTP first region")
    physical = row[1] + low
    need(physical == 0x4701240A, "logical-to-physical result changed")
    need(data[0x18380A:0x18380C] == b"\0\0", "packaged initial field changed")

    # Exact reader direct-BL closure; there is no literal Thumb pointer to it.
    reader_callers = direct_bl_callers(data, 0x637C)
    need(reader_callers == [0x11058, 0x1148C, 0x2A2F8],
         "generic-reader direct caller census changed")
    need(raw_hits(data, 0x637D) == [], "literal reader Thumb pointer appeared")
    need(data[0x11252:0x1125E].hex() == "69080baa2046f5f790f912e0",
         "variable-count caller changed")
    need(data[0x11682:0x116A8].hex() ==
         "11e0ffe76a4601212046f4f776ff05eb8500154a02eb8001bdf80030224628a0"
         "05f06bfd1ce0",
         "one-halfword caller changed")
    need(data[0x2A4F2:0x2A500].hex() ==
         "0aaa01212846dcf740f8bdf82800", "TCDATA caller changed")

    # The two debug handlers are positively installed in the command table.
    need(u32(data, 0x3D368) == 0x00010F0D and cstring(data, 0x3D36C) == "bin",
         "variable reader command-table row changed")
    need(u32(data, 0x3D3A0) == 0x0001121D and cstring(data, 0x3D3A4) == "param",
         "one-halfword reader command-table row changed")
    need(data[0x17294:0x172C0].hex() ==
         "c4ebc400134a02eb80012846e9f7b0fd68b911a10020e9f799fc0546"
         "c4ebc4000c4a02eb8000816928468847",
         "command-table compare/indirect dispatch changed")

    # The positively recovered ingress is a controller-local UART path.  In
    # polling mode it reads MMIO 0x40152000 directly; otherwise it consumes a
    # 512-byte IRQ ring whose sole direct producer reads the same MMIO block.
    need(u32(data, 0x17150) == 0x40152000, "UART parser MMIO changed")
    need(u32(data, 0x17154) == 0x200153F8, "UART parser mode byte changed")
    need(u32(data, 0x17158) == 0x200155F8, "UART parser ring base changed")
    need([u32(data, x) for x in (0x1715C, 0x17160, 0x17164)] ==
         [0x20000E0E, 0x20000E14, 0x20000E12],
         "UART parser state words changed")
    need(u32(data, 0x161A0) == 0x40152000 and
         u32(data, 0x161A4) == 0x200155F8,
         "UART IRQ source/ring changed")
    need(direct_bl_callers(data, 0x21084) == [0x15F68],
         "UART ring-writer caller census changed")
    need(direct_bl_callers(data, 0x17084) == [0x1701E],
         "command dispatcher caller census changed")

    # The CDC data implementation occupies this bounded mixed-code interval.
    # It contains the separate internal TCDATA reader, but no direct edge to
    # the UART line parser, its dispatcher, or its byte-ring producer.
    for target in (0x16FC0, 0x17084, 0x21084):
        need(direct_bl_callers(data, target, 0x27E00, 0x2C000) == [],
             "CDC-area direct edge appeared for 0x%x" % target)
    for value in (0x40152000, 0x200155F8, 0x20000E0E,
                  0x20000E12, 0x20000E14):
        need(raw_hits(data, value, 0x28000, 0x2C000) == [],
             "CDC-area UART literal appeared for 0x%x" % value)
    need(direct_bl_callers(data, 0x2A2BC) == [0x136F2],
         "TCDATA periodic caller census changed")

    hashes = {
        "generic_reader": digest(data, 0x657C, 0x6610),
        "variable_handler": digest(data, 0x110F0, 0x112D0),
        "one_word_handler": digest(data, 0x1121C, 0x114E4),
        "uart_ring_pop": digest(data, 0xF684, 0xF6E8),
        "uart_irq": digest(data, 0x16150, 0x161B0),
        "uart_parser_dispatch": digest(data, 0x171C0, 0x172E0),
        "cdc_rx_worker": digest(data, 0x29CFC, 0x29DA2),
        "tcdata_sampler": digest(data, 0x2A4BC, 0x2A57C),
        "command_table_excerpt": digest(data, 0x3D334, 0x3D3BC),
    }
    need(hashes == {
        "generic_reader": "7ebc90f811630e1be84808d2dbac850e4c067c0643066714ef5a75b2b0f11b16",
        "variable_handler": "983fa30e28e1fc9d65f3462c83d0197c206a4974bb06cf0bbc25dfe4fb3cf781",
        "one_word_handler": "c96d66e5344391dbb1ca086bc392515f568d10bba8e87fab8f7c1af820383d09",
        "uart_ring_pop": "bcb70af7e0d9a47e8f4cdb24fe75178e3acc7dea2e9ee795ecfc3c7bb35b96f4",
        "uart_irq": "36481610ccd6b4ba52a651eeee74d51136092e35d95dd9fdb53105170629274e",
        "uart_parser_dispatch": "421faef06466558f0101d6d61002d6b00ffde43603f88088526326f9ba65782c",
        "cdc_rx_worker": "95f2b8b66c1a603d4d7b0d7868e5c387f0788086efc88be823b516408c725959",
        "tcdata_sampler": "d7f1d435c2de376b329bec1d282935f0f5d3572906bb1970e541b32f5c9255f6",
        "command_table_excerpt": "2b11956856f2b33086e9969b9fd0fe7a25865a37b9722114a54fa33d7e323b10",
    }, "bounded slice hashes changed")

    print("PASS")
    print("logical=0x%06x words=1 physical=0x%08x" % (logical, physical))
    print("reader_direct_callers=" + ",".join(hex(x) for x in reader_callers))
    print("positive_ingress=local_uart_0x40152000 usb_cdc_bridge=unproved")
    for name, value in hashes.items():
        print(name, value)


if __name__ == "__main__":
    main()
