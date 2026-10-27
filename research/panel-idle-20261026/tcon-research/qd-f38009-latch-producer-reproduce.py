#!/usr/bin/env python3
"""Reproduce bounded provenance facts for the image-0 0x2000f808 latch.

Offline only.  This checker reads one already-copied factory profile and does
not access a device, network, process memory, controller, or firmware service.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = (ROOT / "overnight/selected-qd-profile-copy-20261027b/"
           "F_RSM1_BN9659934B_COMMON.bin")
PROFILE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
IMAGE0_FILE_BASE = 0x200
IMAGE0_FILE_END = 0x40000
OBJECT_BASE = 0x2000F7C2
LATCH = 0x2000F808


def need(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def u16(data: bytes, file_offset: int) -> int:
    return struct.unpack_from("<H", data, file_offset)[0]


def u32(data: bytes, file_offset: int) -> int:
    return struct.unpack_from("<I", data, file_offset)[0]


def sha(data: bytes, start: int, end: int) -> str:
    return hashlib.sha256(data[start:end]).hexdigest()


def thumb_bl_target(data: bytes, linked_va: int) -> int | None:
    """Decode a Thumb-2 immediate BL at an image-0 linked VA."""
    off = IMAGE0_FILE_BASE + linked_va
    a, b = u16(data, off), u16(data, off + 2)
    if (a & 0xF800) != 0xF000 or (b & 0xD000) != 0xD000:
        return None
    s = (a >> 10) & 1
    imm10 = a & 0x03FF
    j1, j2 = (b >> 13) & 1, (b >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ s), 1 ^ (j2 ^ s)
    imm11 = b & 0x07FF
    value = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if s:
        value -= 1 << 25
    return (linked_va + 4 + value) & 0xFFFFFFFF


def main() -> None:
    data = PROFILE.read_bytes()
    need(len(data) == 0x500000, "profile size changed")
    need(hashlib.sha256(data).hexdigest() == PROFILE_SHA256, "profile hash changed")

    # Canonical image-0 mapping and the constant-return accessor.
    need(u32(data, 0x200) == 0x20020000, "image-0 vector SP changed")
    need(u32(data, 0x204) == 0x00000345, "image-0 reset vector changed")
    need(data[0xF6F0:0xF6F4] == bytes.fromhex("00487047"), "accessor code changed")
    need(u32(data, 0xF6F4) == OBJECT_BASE, "latch-object base changed")
    need(OBJECT_BASE + 0x46 == LATCH, "latch arithmetic changed")

    # Getter reads, reports, and clears exactly the halfword at object+0x46.
    need(data[0x10166:0x10176] == bytes.fromhex(
        "b8f8460020b144f020040020a8f84600"), "read-to-clear sequence changed")

    # Image-0 final scatter record is a zero-fill that contains the latch.
    record = struct.unpack_from("<4I", data, 0x3E3F0)
    need(record == (0x3E764, 0x20000F4C, 0x16438, 0x1D8),
         "image-0 final scatter record changed")
    _, destination, length, handler = record
    need(destination <= LATCH < destination + length, "latch left reset zero-fill range")
    need(handler == 0x1D8, "final scatter handler is no longer zero-fill")

    # Direct code references are bounded and separated from coincidental
    # instruction encodings containing the same four bytes.
    object_hits = [i for i in range(len(data) - 3)
                   if data[i:i + 4] == struct.pack("<I", OBJECT_BASE)]
    latch_hits = [i for i in range(len(data) - 3)
                  if data[i:i + 4] == struct.pack("<I", LATCH)]
    need(object_hits == [0xF6F4, 0x3CD4C], "object-base raw-word census changed")
    need(latch_hits == [0x1DEC0], "latch raw-word census changed")
    # The second object hit and sole latch hit are instructions, not literals.
    need(data[0x3CD4C:0x3CD50] == bytes.fromhex("c2f70020"),
         "object coincidence changed")
    need(data[0x1DEC0:0x1DEC4] == bytes.fromhex("08f80020"),
         "latch coincidence changed")
    need(not any(IMAGE0_FILE_END <= x < 0x60000 for x in object_hits + latch_hits),
         "image-1 acquired a direct target/object word")

    direct_callers = []
    for va in range(0, IMAGE0_FILE_END - IMAGE0_FILE_BASE - 3, 2):
        if thumb_bl_target(data, va) == 0xF4F0:
            direct_callers.append(va)
    expected = [
        0x466E, 0x46AA, 0x46F0, 0x763A, 0xC5F6, 0xFE7C, 0x1033A,
        0x12312, 0x15A86, 0x22496, 0x224E6, 0x225BE, 0x22C62,
        0x22EA6, 0x22F5C, 0x22F84, 0x23122, 0x231E2, 0x2320A,
        0x2322E, 0x23256, 0x23396, 0x2349C, 0x23542, 0x236DC,
        0x237BC, 0x23828, 0x23882, 0x238B4, 0x23946, 0x23988,
        0x23A74, 0x23B3C, 0x23BEE, 0x27B92, 0x2B9FE, 0x2BAEC,
        0x2BD9E, 0x2BFEC, 0x333D0,
    ]
    need(direct_callers == expected, "direct object-accessor caller census changed")

    # Every decoded fixed STRH +0x46 site in image 0.  The table records its
    # instruction bytes; the immediately associated constant accessors/array
    # roots keep all but 0xff72 numerically separate from OBJECT_BASE.
    strh46 = {
        0x93AE: "a4f84600", 0x944E: "a4f84600", 0xF568: "a4f84600",
        0xFF72: "a8f84600", 0x1CD5E: "a1f84600", 0x1CE32: "a1f84600",
        0x1DAE8: "a1f84600", 0x22246: "a3f84600", 0x24B5A: "a4f84650",
        0x2B8E4: "a4f84610",
    }
    for va, encoded in strh46.items():
        need(data[IMAGE0_FILE_BASE + va:IMAGE0_FILE_BASE + va + 4].hex() == encoded,
             "fixed STRH +0x46 census changed at 0x%x" % va)
    need(u32(data, IMAGE0_FILE_BASE + 0xE674) == 0x2000F0E0,
         "common-object accessor changed")
    need(u32(data, IMAGE0_FILE_BASE + 0xF1F0) == 0x2000FC6C,
         "alternate-object accessor changed")
    need(u32(data, IMAGE0_FILE_BASE + 0xF504) == 0x2000D340,
         "0xf500 object accessor changed")
    need(u32(data, IMAGE0_FILE_BASE + 0xF50C) == 0x20014440,
         "0xf508 object accessor changed")
    need([u32(data, IMAGE0_FILE_BASE + va) for va in
          (0x1CDA0, 0x1CE70, 0x1DB6C, 0x22268)] ==
         [0x2021F800, 0x2021F400, 0x2021F000, 0x2021F000],
         "indexed +0x46 array roots changed")

    hashes = {
        "image0_stored": sha(data, 0x200, 0x40000),
        "accessor": sha(data, 0xF6F0, 0xF6F8),
        "selector09_getter": sha(data, 0x1006C, 0x101A8),
        "scatter_table": sha(data, 0x3E340, 0x3E400),
        "zero_fill_handler": sha(data, 0x3D8, 0x3F4),
    }
    need(hashes == {
        "image0_stored": "57ef8b1abd39e8d14dc5c9c299ef4b80631262638a065368027680a233a32b5e",
        "accessor": "fc60655e318a4b18ca66752d54d97fce55021d10ca6c5ccfcacebd3641a42bda",
        "selector09_getter": "24f30bf63c8dbfd8fbeb0a8410d07057215b126b5125b91bf0c375615e971b0c",
        "scatter_table": "3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d",
        "zero_fill_handler": "35c9c9990fd6fca376959800dc4a120df626f42d01eb18e8fdfebc5487f091ec",
    }, "bounded slice hashes changed")

    print("PASS")
    print("object_base=0x%08x latch=0x%08x reset_value=0" % (OBJECT_BASE, LATCH))
    print("direct_accessor_callers=%d fixed_strh46=%d image1_direct_words=0" %
          (len(direct_callers), len(strh46)))
    for name, digest in hashes.items():
        print(name, digest)


if __name__ == "__main__":
    main()
