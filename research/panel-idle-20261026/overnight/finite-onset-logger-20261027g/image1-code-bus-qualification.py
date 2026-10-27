#!/usr/bin/env python3
"""Bounded offline verifier for the image-1 executable-bus qualification.

This checker reads two retained local files.  It does not access the TV,
network, a device node, USB, or any process other than itself.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


SELECTED = Path(
    "${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/"
    "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
)
CURRENT = Path(
    "${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/"
    "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
)

WHOLE_SIZE = 0x500000
SELECTED_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
CURRENT_SHA256 = "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"

IMAGE1_SLOT = (0x40000, 0x80000)
IMAGE1_SLOT_SHA256 = "56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def exact_slice(blob: bytes, start: int, end: int, digest: str, label: str) -> bytes:
    value = blob[start:end]
    need(len(value) == end - start, f"{label}: truncated")
    need(sha256(value) == digest, f"{label}: SHA-256 mismatch")
    return value


def main() -> None:
    selected = SELECTED.read_bytes()
    current = CURRENT.read_bytes()
    need(len(selected) == WHOLE_SIZE, "selected size")
    need(len(current) == WHOLE_SIZE, "current size")
    need(sha256(selected) == SELECTED_SHA256, "selected whole-file SHA-256")
    need(sha256(current) == CURRENT_SHA256, "current whole-file SHA-256")

    slot_start, slot_end = IMAGE1_SLOT
    selected_slot = exact_slice(
        selected, slot_start, slot_end, IMAGE1_SLOT_SHA256, "selected image-1 slot"
    )
    current_slot = exact_slice(
        current, slot_start, slot_end, IMAGE1_SLOT_SHA256, "current image-1 slot"
    )
    need(selected_slot == current_slot, "selected/current image-1 slot differs")

    vector = exact_slice(
        selected,
        0x40200,
        0x40208,
        "bef0c9b5c39935347fe872bf9501a20bdbe3c11781d26f7bc521e0e106191b6d",
        "image-1 vector",
    )
    initial_sp, reset_thumb = struct.unpack("<II", vector)
    need(initial_sp == 0x20020000, "image-1 initial SP")
    need(reset_thumb == 0x369, "image-1 Thumb reset vector")
    reset_va = reset_thumb & ~1
    need(0x40200 + reset_va == 0x40568, "image-1 reset file coordinate")

    exact_slice(
        selected,
        0x40568,
        0x4058C,
        "77428a5791705e4b966092c95715a84b617dfd7f414902ff35ae2089d92c93d6",
        "image-1 reset trampoline",
    )
    exact_slice(
        selected,
        0x40340,
        0x403F4,
        "cf4020e3cdb1b314345608c30d00c1efa1e0ad4cf87bf8e54aa92f568fcb6330",
        "image-1 scatter dispatcher",
    )
    table = exact_slice(
        selected,
        0x5D8A4,
        0x5D934,
        "73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef",
        "image-1 scatter table",
    )
    rows = [struct.unpack_from("<IIII", table, offset) for offset in range(0, len(table), 16)]
    expected_rows = [
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
    need(rows == expected_rows, "image-1 scatter rows")
    need(all(not (0 <= destination < 0x40000) for _, destination, _, _ in rows),
         "scatter table unexpectedly contains a linked-code-range destination")

    # This exact mapper body has separately decoded bounds
    # [0x20000000, 0x20200000).  Pinning the bytes makes the report's scope
    # reproducible; it does not extend that mapper to linked code VA 0..0x3ffff.
    mapper = exact_slice(
        selected,
        0x43284,
        0x432A8,
        "64ef2153ee7053a16b6741c455535147ddb1d247aaf216482b5e46fba7c0f471",
        "image-1 RAM mapper body",
    )
    need(mapper == bytes.fromhex(
        "014609480268b1f1005f0ad30748814207d20a2a02d101f11450704701f11c50fbe70846"
    ), "image-1 RAM mapper exact bytes")

    # The one positive 0x4701.... reset-copy record belongs to image 0 and its
    # source VA maps back into image 0, not the image-1 stored slot.
    exact_slice(
        selected,
        0x3E340,
        0x3E400,
        "3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d",
        "image-0 scatter table",
    )
    image0_row = struct.unpack_from("<IIII", selected, 0x3E3D0)
    need(image0_row == (0x3EA34, 0x47010000, 0x47BC, 0x17C),
         "image-0 fixed-window scatter row")
    image0_source_file = 0x200 + image0_row[0]
    need(image0_source_file == 0x3EC34 and image0_source_file < 0x40000,
         "image-0 fixed-window source coordinate")
    exact_slice(
        selected,
        0x3EC34,
        0x3EC74,
        "aefd6168b636ab121e9fdd8e449d248ccbc36a7f2d75d4bcc8a42ca74a8d4ca7",
        "image-0 fixed-window source prefix",
    )

    # Config-copy labels are bounded naming evidence only.  Their exact single
    # locations are recorded so the report cannot silently promote a different
    # occurrence into a loader proof.
    labels = {
        b"Config_CopyData_To_MCU_v5\0": 0x3CF3B,
        b"Config_CopyData_To_MCU\0": 0x3CF55,
        b"Config_CopyData_To_IP_v5\0": 0x3CF6C,
        b"Config_CopyData_To_IP_LUT\0": 0x3CF85,
        b"Config_CopyData_DDR_To_RTL\0": 0x3CF9F,
        b"Config_CopyData_DDR_To_MCU\0": 0x3CFBA,
    }
    for label, offset in labels.items():
        need(selected.find(label) == offset, f"label offset: {label!r}")
        need(selected.find(label, offset + 1) == -1, f"duplicate label: {label!r}")

    # Absence of this raw literal is only a bounded negative observation, not
    # proof that boot ROM or computed remap logic does not exist.
    vtor_literal = struct.pack("<I", 0xE000ED08)
    need(selected[0x200:0x40000].find(vtor_literal) == -1, "image-0 raw VTOR literal")
    need(selected[0x40200:0x80000].find(vtor_literal) == -1, "image-1 raw VTOR literal")

    predicate = exact_slice(
        selected,
        0x42068,
        0x42240,
        "c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a",
        "known image-1 predicate body",
    )
    need(predicate == current[0x42068:0x42240], "current predicate bytes differ")

    result = {
        "status": "qualification_gap",
        "offline_only": True,
        "target_operations": 0,
        "selected_sha256": SELECTED_SHA256,
        "current_sha256": CURRENT_SHA256,
        "image1_slot": {
            "file_range": ["0x40000", "0x80000"],
            "size": len(selected_slot),
            "sha256": IMAGE1_SLOT_SHA256,
            "selected_equals_current": True,
        },
        "linked_layout": {
            "vector_file": "0x40200",
            "initial_sp": hex(initial_sp),
            "reset_thumb": hex(reset_thumb),
            "reset_linked_va": hex(reset_va),
            "reset_file": "0x40568",
            "file_from_linked_va": "0x40200 + VA",
        },
        "scatter": {
            "record_count": len(rows),
            "destinations": [hex(row[1]) for row in rows],
            "contains_linked_code_destination": False,
        },
        "positive_0x4701_scatter_row": {
            "component": "image0",
            "source_linked_va": hex(image0_row[0]),
            "source_file": hex(image0_source_file),
            "destination": hex(image0_row[1]),
            "image1_source": False,
        },
        "known_predicate": {
            "linked_va_range": ["0x1e68", "0x2040"],
            "file_range": ["0x42068", "0x42240"],
            "size": len(predicate),
            "sha256": sha256(predicate),
            "hardware_bus_address": None,
        },
        "qualified_code_bus_address": None,
        "future_read_geometry_qualified": False,
        "reason": (
            "retained loader evidence establishes stored/linked coordinates and RAM/data "
            "scatter destinations, but no code copy destination, launch/remap register, "
            "or other source-proven hardware-visible mapping for image-1 VA 0..0x3ffff"
        ),
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
