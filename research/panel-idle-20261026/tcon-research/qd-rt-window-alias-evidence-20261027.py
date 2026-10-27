#!/usr/bin/env python3
"""Offline bounded check of reset/config sources for the QD RT roots.

This checker deliberately verifies only the two packaged scatter tables and
the already-recovered AP_RTP source ranges.  It neither emulates a controller
nor infers an inter-core alias from equal object offsets.
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


def row(data: bytes, offset: int) -> tuple[int, int, int, int]:
    return struct.unpack_from("<4I", data, offset)


def sha(data: bytes, start: int, end: int) -> str:
    return hashlib.sha256(data[start:end]).hexdigest()


def main() -> None:
    data = PROFILE.read_bytes()
    need(len(data) == 0x500000, "selected package size changed")
    need(hashlib.sha256(data).hexdigest() == PROFILE_SHA256,
         "selected package hash changed")

    # These tables are reached by their own image reset scatter dispatchers.
    # Their values are linked source VAs; file source = VA + image vector base.
    image0 = [row(data, 0x3E340 + 16 * i) for i in range(12)]
    image1 = [row(data, 0x5D8A4 + 16 * i) for i in range(9)]
    need(image0[9] == (0x3EA34, 0x47010000, 0x47BC, 0x17C),
         "image0 fixed-window scatter record changed")
    need(image1[0] == (0x1D860, 0x20000000, 0x4F8, 0x17C),
         "image1 context scatter record changed")
    need(image1[-1] == (0x1D95C, 0x200004F8, 0xDCA4, 0x1D8),
         "image1 zero-fill record changed")
    need(not any(destination == 0x47010000 for _, destination, _, _ in image1),
         "image1 reset scatter acquired image0 fixed-window destination")

    # Bound the source identity without claiming compressed stream decoding.
    # The image0 fixed-window record's source maps into image0, not image1.
    image0_window_source_file = image0[9][0] + 0x200
    need(0x200 <= image0_window_source_file < 0x40000,
         "image0 fixed-window source left image0 stored range")
    need(not (0x40000 <= image0_window_source_file < 0x60000),
         "image0 fixed-window source points into image1")

    # AP_RTP is a separate image0 configuration-loader route.  Its two raw
    # source payloads also lie outside image1's stored interval.
    entry = struct.unpack_from("<7I", data, 0x3CCBC + 14 * 0x1C)
    need(entry[1:7] == (0x47012400, 0x100, 0x47010000, 0x2400,
                        0x210000, 0x210400), "AP_RTP mapping changed")
    first_source, second_source = 0x80000 + 0x103800, 0x80000 + 0x103A00
    need(first_source == 0x183800 and second_source == 0x183A00,
         "AP_RTP source arithmetic changed")
    for source in (first_source, second_source):
        need(not (0x40000 <= source < 0x60000),
             "AP_RTP source moved into image1")

    hashes = {
        "image0_reset_prefix": sha(data, 0x544, 0x56C),
        "image0_scatter_table": sha(data, 0x3E340, 0x3E400),
        "image1_reset_prefix": sha(data, 0x40568, 0x4058C),
        "image1_scatter_table": sha(data, 0x5D8A4, 0x5D934),
        "image0_window_source_prefix": sha(data, image0_window_source_file,
                                                image0_window_source_file + 0x40),
    }
    need(hashes == {
        "image0_reset_prefix": "ab26f68c73c5451c7a615f64d0e2a4241000bba3c50e6f1f21eabaacebec8162",
        "image0_scatter_table": "3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d",
        "image1_reset_prefix": "77428a5791705e4b966092c95715a84b617dfd7f414902ff35ae2089d92c93d6",
        "image1_scatter_table": "73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef",
        "image0_window_source_prefix": "aefd6168b636ab121e9fdd8e449d248ccbc36a7f2d75d4bcc8a42ca74a8d4ca7",
    }, "bounded evidence bytes changed")

    print("PASS")
    print(f"image0_window_reset_source_file=0x{image0_window_source_file:x}")
    print("image0_window_reset_destination=0x47010000 length=0x47bc")
    print("image1_reset_destinations=" + ",".join(f"0x{x[1]:08x}" for x in image1))
    print("ap_rtp_sources=0x183800,0x183a00")
    for name, digest in hashes.items():
        print(name, digest)


if __name__ == "__main__":
    main()
