#!/usr/bin/env python3
"""Reproduce the bounded AV pre/post RT-window delta entirely offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
BASE = OVERNIGHT.parent
AV = OVERNIGHT / "stock-rt-lifecycle-trial-20261027av"
SELECTED = OVERNIGHT / "selected-qd-profile-copy-20261027b" / "F_RSM1_BN9659934B_COMMON.bin"
RECOVERED = OVERNIGHT / "firmware-fingerprint-20261027d" / "full-backup-recovered" / "fixeddata.bin"

PRE0 = AV / "pre-x" / "retained-00-initial_faulted-cycle001-00-R.bin"
PRE1 = AV / "pre-x" / "retained-01-post_fault-cycle001-04-R.bin"
POST0 = AV / "post-x" / "retained-00-last_clean-cycle080-00-R.bin"
POST1 = AV / "post-x" / "retained-00-last_clean-cycle080-05-R.bin"

PRE_SHA = "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9"
POST_SHA = "a15bcc5f51c78ccdea8283d0839533c2e5f12c243a8e351032747b729b66b477"
SELECTED_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
RECOVERED_SHA = "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"
SLOT_SHA = "56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf"

EXPECTED_BYTE_CHANGES = {
    0x00: (0x01, 0x00),
    0x0A: (0x01, 0x00),
    0x0B: (0x10, 0x00),
    0x0E: (0x00, 0x01),
    0x20: (0x59, 0x42),
    0x86: (0x07, 0x00),
    0x90: (0x29, 0x00),
    0x92: (0x36, 0x30),
    0x98: (0x18, 0x17),
    0xAC: (0xF3, 0xF4),
    0xBC: (0x42, 0x14),
    0xCA: (0x01, 0x00),
}

EXPECTED_U16_CHANGES = {
    0x00: (1, 0),
    0x0A: (0x1001, 0),
    0x0E: (0, 1),
    0x20: (3161, 3138),
    0x86: (7, 0),
    0x90: (41, 0),
    0x92: (54, 48),
    0x98: (24, 23),
    0xAC: (243, 244),
    0xBC: (3138, 3092),
    0xCA: (1, 0),
}

THRESHOLDS = {0x30: 200, 0x32: 0, 0x40: 0, 0xC0: 200, 0xC4: 40}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pinned(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    need(sha(data) == expected, f"SHA-256 mismatch: {path}")
    return data


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def validate_raw(pre: bytes, post: bytes) -> None:
    need(len(pre) == len(post) == 0x100, "R window extent")
    got_bytes = {i: (a, b) for i, (a, b) in enumerate(zip(pre, post)) if a != b}
    need(got_bytes == EXPECTED_BYTE_CHANGES, "exact byte-delta set")
    got_u16 = {
        i: (u16(pre, i), u16(post, i))
        for i in range(0, 0x100, 2)
        if u16(pre, i) != u16(post, i)
    }
    need(got_u16 == EXPECTED_U16_CHANGES, "exact aligned-halfword delta set")
    need((u16(pre, 0), u16(pre, 0x0A), u16(pre, 0x0E)) == (1, 0x1001, 0), "faulted tuple")
    need((u16(post, 0), u16(post, 0x0A), u16(post, 0x0E)) == (0, 0, 1), "clean tuple")
    need(u16(pre, 0x10) == u16(post, 0x10) == 4, "mode field unchanged")
    for offset, value in THRESHOLDS.items():
        need(u16(pre, offset) == u16(post, offset) == value, f"threshold +0x{offset:x}")


def validate_source(selected: bytes, recovered: bytes) -> bytes:
    need(len(selected) == len(recovered) == 0x500000, "package extents")
    slot_a = selected[0x40000:0x80000]
    slot_b = recovered[0x40000:0x80000]
    need(slot_a == slot_b and sha(slot_a) == SLOT_SHA, "image-1 slot equality")

    def image1(va: int, length: int) -> bytes:
        return selected[0x40200 + va:0x40200 + va + length]

    setter = image1(0xC1E0, 0x32)
    need(sha(setter) == "f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102", "setter body")
    need(bytes.fromhex("01214ff410500153002142f20e40015341f20101001f0153") in setter,
         "setter stores +0/+e/+a")

    clear = image1(0xBAD8, 0x18)
    need(sha(clear) == "0b7d679a149edde136ceada67b6f35cbd74e92146d55c4224fd8d8359e6c30de", "action clear")
    need(clear.startswith(bytes.fromhex("42f286400153801c0153001d0153")), "clear +2486/+2488/+248c")

    publishers = image1(0xC6CA, 0x38)
    need(sha(publishers) == "9d20a20eefecba4ae31a443f09b2693f8b2aae12a41d60427f3de298f25416d4",
         "record-ID latch publishers")
    need(bytes.fromhex("42f29040") in publishers and publishers.count(bytes.fromhex("42f29240")) == 2,
         "record-ID +2490/+2492 destinations")

    scan_sources = image1(0xBDA2, 0x6C)
    need(sha(scan_sources) == "c4be8ae8cca71183c6489bf3d149fa9ad7a5f4effb0bfa5c80ec73c38d919354",
         "mode-selected source fields")
    for encoded in ("42f2bc40", "42f22040", "42f2c440", "4ff41350", "42f23040"):
        need(bytes.fromhex(encoded) in scan_sources, f"scan source/threshold encoding {encoded}")

    init = selected[0x183800:0x183900]
    need(sha(init) == "3a16ea440b59a8e778c01ddfc429b110fbdd03e55c953954ce99337ebf5b3937",
         "AP_RTP first packaged payload")
    return init


def expect_reject(fn, name: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise RuntimeError(f"negative fixture accepted: {name}")


def main() -> None:
    pre0 = pinned(PRE0, PRE_SHA)
    pre1 = pinned(PRE1, PRE_SHA)
    post0 = pinned(POST0, POST_SHA)
    post1 = pinned(POST1, POST_SHA)
    need(pre0 == pre1, "pre R brackets differ")
    need(post0 == post1, "post R brackets differ")
    validate_raw(pre1, post1)

    selected = pinned(SELECTED, SELECTED_SHA)
    recovered = pinned(RECOVERED, RECOVERED_SHA)
    init = validate_source(selected, recovered)

    need(sum(a != b for a, b in zip(pre1, init)) == 20, "pre versus AP_RTP payload count")
    need(sum(a != b for a, b in zip(post1, init)) == 15, "post versus AP_RTP payload count")
    need(post1 != init, "post window must not equal packaged payload")
    for offset, value in THRESHOLDS.items():
        need(u16(init, offset) == value, f"payload threshold +0x{offset:x}")

    # Meaningful negative fixtures exercise delta, semantic-field, source,
    # generation-equality, and reset-template boundaries without external I/O.
    changed = bytearray(post1)
    changed[0x30] ^= 1
    expect_reject(lambda: validate_raw(pre1, bytes(changed)), "threshold mutation")
    changed = bytearray(post1)
    changed[0x86] = pre1[0x86]
    expect_reject(lambda: validate_raw(pre1, bytes(changed)), "missing action-bucket delta")
    changed_selected = bytearray(selected)
    changed_selected[0x40200 + 0xC1EA] ^= 1
    expect_reject(lambda: validate_source(bytes(changed_selected), recovered), "setter mutation")
    changed_recovered = bytearray(recovered)
    changed_recovered[0x40000] ^= 1
    expect_reject(lambda: validate_source(selected, bytes(changed_recovered)), "slot mutation")
    changed_init = bytearray(init)
    changed_init[0x20] ^= 1
    expect_reject(lambda: need(sha(bytes(changed_init)) == sha(init), "payload mutation"), "payload mutation")

    output = {
        "schema": "stock-rt-state-delta-v1",
        "target_operations": 0,
        "pre_sha256": sha(pre1),
        "post_sha256": sha(post1),
        "changed_byte_count": len(EXPECTED_BYTE_CHANGES),
        "changed_byte_offsets": [f"0x{x:02x}" for x in EXPECTED_BYTE_CHANGES],
        "changed_halfwords": {
            f"0x{x:02x}": {"pre": a, "post": b}
            for x, (a, b) in EXPECTED_U16_CHANGES.items()
        },
        "source_bound": {
            "tuple": ["0x00", "0x0a", "0x0e"],
            "mode1_action_bucket": "0x86",
            "record_id_latches": ["0x90", "0x92"],
            "mode_selected_source_halfwords": ["0x20", "0xbc"],
        },
        "unchanged": {
            "mode_0x10": 4,
            "thresholds": {f"0x{x:02x}": v for x, v in THRESHOLDS.items()},
        },
        "unresolved_changed_halfwords": ["0x98", "0xac", "0xca"],
        "post_equals_packaged_ap_rtp_payload": False,
        "post_vs_packaged_payload_differing_bytes": 15,
        "image1_slots_equal": True,
        "image1_slot_sha256": SLOT_SHA,
        "self_tests": 5,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
