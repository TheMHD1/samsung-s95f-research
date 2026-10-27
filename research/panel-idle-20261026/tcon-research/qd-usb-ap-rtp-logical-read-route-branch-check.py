#!/usr/bin/env python3
"""Check the generic reader's unsigned branch and AP_RTP address offline.

This reads only the retained 5 MiB profile and the historical reports.  It
does not emit a controller command or access a TV, USB device, UART, process,
root interface, or network endpoint.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = (ROOT / "overnight/selected-qd-profile-copy-20261027b/"
           "F_RSM1_BN9659934B_COMMON.bin")
ORIGINAL_REPORT = ROOT / "tcon-research/qd-usb-ap-rtp-logical-read-route.md"
ORIGINAL_CHECKER = (ROOT / "tcon-research/"
                    "qd-usb-ap-rtp-logical-read-route-reproduce.py")
REVIEW = (ROOT / "overnight/sleep-investigation-20261027a/"
          "usb-rt-reader-independent-review.md")

PINS = {
    PROFILE: "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0",
    ORIGINAL_REPORT: "a28594a181c6bd5fd37bc4000b62ff16769872d74a51d56c6c05ad90290a7f75",
    ORIGINAL_CHECKER: "e174f6344cdedfe96159381d9778a275917dbdd5ddf595ae8b0a7626dc31284c",
    REVIEW: "91079e99f4eee17a653c73423eb1152d6290d26a26ed40087f75053e6a846139",
}

FILE_BASE = 0x200
TABLE_FILE = 0x3CCBC
TABLE_ROWS = 21
ROW_SIZE = 0x1C
READER_FILE = 0x657C
READER_VA = READER_FILE - FILE_BASE


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def cstring(data: bytes, offset: int) -> str:
    end = data.index(b"\0", offset)
    return data[offset:end].decode("ascii")


def reader_source(row: tuple[int, ...], logical: int) -> tuple[int, str]:
    """Model the exact unsigned CMP/BHI split at linked VA 0x63c2/0x63c4."""
    low = logical & 0xFFFF
    first_destination, first_length = row[1], row[2]
    second_destination = row[3]
    first_logical, second_logical = row[5], row[6]

    # cmp first_length, low; bhi first_region.  ARM HI means C==1 && Z==0,
    # equivalently first_length > low for this unsigned subtraction.
    if first_length > low:
        return (first_destination + low) & 0xFFFFFFFF, "first"
    delta = (second_logical - first_logical) & 0xFFFFFFFF
    return (second_destination + low - delta) & 0xFFFFFFFF, "second"


def main() -> None:
    for path, expected in PINS.items():
        need(path.is_file() and not path.is_symlink(), f"missing/nonregular {path}")
        need(sha256(path) == expected, f"hash changed: {path}")

    data = PROFILE.read_bytes()
    need(len(data) == 0x500000, "profile size changed")
    need(u32(data, 0x200) == 0x20020000 and u32(data, 0x204) == 0x345,
         "canonical image-0 vector changed")

    # Pin the reader itself and the exact compare/conditional branch.  The
    # halfword 0xd80e is conditional branch code 8 (HI), displacement 14.
    reader = data[READER_FILE:0x6610]
    need(hashlib.sha256(reader).hexdigest() ==
         "7ebc90f811630e1be84808d2dbac850e4c067c0643066714ef5a75b2b0f11b16",
         "reader bytes changed")
    need(data[0x65C0:0x65C6].hex() == "8068b8420ed8",
         "length load/CMP/BHI bytes changed")
    branch = u16(data, 0x65C4)
    need((branch >> 8) == 0xD8, "conditional opcode is not BHI")
    branch_target = 0x63C4 + 4 + ((branch & 0xFF) << 1)
    need(branch_target == 0x63E4, "BHI target changed")
    need(data[0x65C6:0x65E4].hex() ==
         "c4ebc4000b4603eb8000c0683844abeb0903c11a72004046faf748fb0ae0",
         "second-region path changed")
    need(data[0x65E4:0x65FA].hex() ==
         "7200c4ebc400084b03eb80004068c1194046faf73cfb",
         "first-region path changed")
    need(u32(data, 0x660C) == TABLE_FILE - FILE_BASE,
         "reader table linked-VA literal changed")

    rows = [struct.unpack_from("<7I", data, TABLE_FILE + i * ROW_SIZE)
            for i in range(TABLE_ROWS)]
    matches = [(i, row) for i, row in enumerate(rows)
               if (row[5] & 0xFFFF0000) == 0x00210000]
    need(len(matches) == 1 and matches[0][0] == 14,
         "0x0021 logical-prefix row is not uniquely AP_RTP row 14")
    row = matches[0][1]
    need(cstring(data, row[0] + FILE_BASE) == "AP_RTP", "row name changed")
    need(row[1:] == (0x47012400, 0x100, 0x47010000, 0x2400,
                     0x210000, 0x210400), "AP_RTP row changed")

    source, region = reader_source(row, 0x21000A)
    need(region == "first", "0x21000a did not take unsigned-HI first branch")
    need(source == 0x4701240A, "0x21000a source address changed")
    need(data[0x11688:0x1168A].hex() == "0121",
         "one-word caller no longer loads count one")
    byte_count = 1 << 1
    need(byte_count == 2, "one reader word must remain two bytes")
    need((0x000A + byte_count) <= row[2],
         "selected two-byte read crosses the first-region length")

    # These boundary cases make the direction of BHI independently visible.
    need(reader_source(row, 0x2100FF) == (0x470124FF, "first"),
         "low=first_length-1 branch changed")
    need(reader_source(row, 0x210100) == (0x4700FD00, "second"),
         "equality must not satisfy unsigned HI")
    need(reader_source(row, 0x210400) == (0x47010000, "second"),
         "second logical base mapping changed")

    print("PASS")
    print("reader_va=0x%04x cmp=first_length,low condition=unsigned_hi" % READER_VA)
    print("logical=0x21000a words=1 branch=first source=0x%08x bytes=2" % source)
    print("no_command_generated=true target_access=false")


if __name__ == "__main__":
    main()
