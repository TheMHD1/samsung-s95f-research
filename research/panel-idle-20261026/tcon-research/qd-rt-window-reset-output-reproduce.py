#!/usr/bin/env python3
"""Offline replay of the packaged scatter decoder for the two QD roots.

The decoder is validated first against the already-pinned image-1 context
output.  It then decodes only image-0 scatter row 9.  It does not emulate an
MCU, access a device, or claim that either packaged reset sequence ran live.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
PROFILE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def unpack(data: bytes, source_file: int, size: int) -> tuple[bytes, int]:
    """Exact byte-level behavior of the shared packaged handler VA 0x17c.

    The loop uses the low three tag bits for literal count (minus one), the
    high nibble for a zero/back-reference count, and bit 3 for a one-byte
    back-reference distance.  The image-1 context stream below is the
    independent known-answer guard for this implementation.
    """
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
            need(len(out) < size, "literal exceeds scatter output size")
            out.append(data[source])
            source += 1
        if tag & 8:
            distance = data[source]
            source += 1
            need(distance != 0 and distance <= len(out),
                 "invalid backward reference")
            for _ in range(run_count + 2):
                need(len(out) < size, "back-reference exceeds scatter output size")
                out.append(out[-distance])
        else:
            need(len(out) + run_count <= size, "zero run exceeds scatter output size")
            out.extend(b"\0" * run_count)
    return bytes(out), source


def main() -> None:
    data = PROFILE.read_bytes()
    need(len(data) == 0x500000, "selected profile size changed")
    need(hashlib.sha256(data).hexdigest() == PROFILE_SHA256,
         "selected profile hash changed")

    # Known answer: image-1 record 0, source linked VA 0x1d860, image-1
    # stored bias 0x40200, output size 0x4f8.
    image1, image1_end = unpack(data, 0x40200 + 0x1D860, 0x4F8)
    need(image1_end == 0x5DB5B, "image1 decoder consumed unexpected source length")
    need(hashlib.sha256(image1).hexdigest() ==
         "76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8",
         "image1 known-answer decompression mismatch")
    need(u32(image1, 0x4E0) == 0x20010000,
         "image1 reset context pointer changed")

    # Image-0 scatter row 9: linked source VA 0x3ea34 -> file +0x200.
    row9 = struct.unpack_from("<4I", data, 0x3E340 + 9 * 16)
    need(row9 == (0x3EA34, 0x47010000, 0x47BC, 0x17C),
         "image0 fixed-window row changed")
    image0, image0_end = unpack(data, 0x200 + row9[0], row9[2])
    need(image0_end == 0x3ECC5, "image0 decoder consumed unexpected source length")
    need(hashlib.sha256(image0).hexdigest() ==
         "aee8a64ff7ccfaa95aa4def885fcf7d79c8f4f982d63c5efdb1686eec2cd2b6d",
         "image0 fixed-window output changed")
    need(image0 == b"\0" * row9[2], "image0 reset window is no longer all zero")

    # AP_RTP's later packaged payload is intentionally different from the
    # reset image at selected offsets. This is provenance, not alias evidence.
    ap_first = 0x183800
    checks = {0x2400: 0, 0x240A: 0, 0x240E: 0, 0x2410: 4,
              0x24AA: 100, 0x24AC: 0}
    for offset, expected in checks.items():
        need(image0[offset] == 0, "reset window offset changed")
        need(data[ap_first + offset - 0x2400] == expected,
             "AP_RTP payload field changed")

    # Image-1's scatter/zero-fill does not write the root it later points to.
    zero_start, zero_size = 0x200004F8, 0xDCA4
    zero_end = zero_start + zero_size
    root = 0x20010000
    need(zero_end == 0x2000E19C and zero_end < root,
         "image1 zero-fill/root separation changed")
    rows = [struct.unpack_from("<4I", data, 0x5D8A4 + 16 * i) for i in range(9)]
    need(not any(destination <= root < destination + size
                  for _, destination, size, _ in rows),
         "image1 scatter now initializes context root range")

    print("PASS")
    print("image0_window=0x47010000+0x47bc reset_sha256=" + hashlib.sha256(image0).hexdigest())
    print("image0_window_all_zero=true source_file=0x3ec34..0x3ecc4")
    print("image1_context_pointer=0x%08x root_scatter_initialized=false" % u32(image1, 0x4E0))
    print("image1_zero_fill=0x%08x..0x%08x root=0x%08x" %
          (zero_start, zero_end, root))


if __name__ == "__main__":
    main()
