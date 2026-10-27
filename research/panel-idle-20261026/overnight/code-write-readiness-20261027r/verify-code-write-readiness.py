#!/usr/bin/env python3
"""Finite offline verifier for selector-1 code-write readiness.

This verifier deliberately stops before any write/probe construction.  It
checks retained package, startup/scatter, and mapped-view evidence only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
SELECTED = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CURRENT = OVERNIGHT / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
N = OVERNIGHT / "code-map-qualified-followup-20261027n"

SELECTED_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
CURRENT_SHA256 = "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"
SLOT_SHA256 = "56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf"
N_MANIFEST_SHA256 = "a365b51fe014af70d50697bdeefd0b5eac2d6abb342fda1c6d21ab6ec2b145d7"
N_RESULT_SHA256 = "3119fb85c08b970794adcdf975313d825c80a301b995e293f2fc5cb458df57c1"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_bytes(path: Path, expected_sha256: str) -> bytes:
    raw = path.read_bytes()
    need(sha256(raw) == expected_sha256, f"SHA-256: {path}")
    return raw


def u16(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def image1(package: bytes, va: int, length: int) -> bytes:
    start = 0x40200 + va
    end = start + length
    need(0 <= va and end <= 0x80000, f"image-1 slice {va:#x}+{length:#x}")
    return package[start:end]


def thumb_literal_address(instruction_va: int, instruction: int) -> int:
    """Decode a 16-bit Thumb LDR Rt,[PC,#imm8*4] literal address."""
    need(instruction & 0xF800 == 0x4800, f"Thumb literal LDR at {instruction_va:#x}")
    return ((instruction_va + 4) & ~3) + ((instruction & 0xFF) << 2)


def overlaps(start: int, length: int, region_start: int, region_end: int) -> bool:
    return start < region_end and region_start < start + length


def main() -> None:
    selected = file_bytes(SELECTED, SELECTED_SHA256)
    current = file_bytes(CURRENT, CURRENT_SHA256)
    need(len(selected) == len(current) == 0x500000, "whole retained file extent")
    selected_slot = selected[0x40000:0x80000]
    current_slot = current[0x40000:0x80000]
    need(selected_slot == current_slot, "stored image-1 slot equality")
    need(sha256(selected_slot) == SLOT_SHA256, "stored image-1 slot SHA-256")

    # The retained mapped-view acquisition is positive read/content evidence,
    # but its own result explicitly declines execution/whole-image claims.
    file_bytes(N / "code-view-evidence-manifest.json", N_MANIFEST_SHA256)
    result_raw = file_bytes(N / "capture-once/result.json", N_RESULT_SHA256)
    result = json.loads(result_raw)
    need(result["transport_accepted"] is True, "N transport accepted")
    need(result["all_windows_match_selected_package"] is True, "N content match")
    need(result["bus_contents_altered"] is False, "N read did not alter contents")
    need(result["executing_code_identity_proved"] is False, "N execution limit")
    need(result["whole_image_identity_inferred"] is False, "N whole-image limit")
    need(result["windows_sequential_not_atomic"] is True, "N acquisition ordering")

    windows = [
        ("a", 0x46001E60, 512,
         "8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49"),
        ("b", 0x460038C0, 64,
         "0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb"),
        ("c", 0x4601BB60, 576,
         "035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8"),
    ]
    need(len(result["windows"]) == len(windows), "N window count")
    for index, (name, bus, length, digest) in enumerate(windows):
        raw = file_bytes(N / f"capture-once/window-{name}.bin", digest)
        need(len(raw) == length, f"N window-{name} length")
        linked_va = bus - 0x46000000
        need(0 < linked_va and linked_va + length <= 0x20000,
             f"N window-{name} selector-1 domain")
        need(raw == image1(selected, linked_va, length), f"N window-{name} package match")
        row = result["windows"][index]
        need(row == {"address": hex(bus), "length": length,
                     "matches_selected_package": True, "sha256": digest},
             f"N window-{name} result row")

    # Exact image-1 reset path.  The two 16-bit literal loads resolve to the
    # packaged first-reset-callee Thumb pointer and scatter-dispatcher pointer.
    vector = image1(selected, 0, 8)
    need(sha256(vector) ==
         "bef0c9b5c39935347fe872bf9501a20bdbe3c11781d26f7bc521e0e106191b6d",
         "image-1 vector SHA-256")
    need(struct.unpack("<II", vector) == (0x20020000, 0x369), "image-1 vector values")
    reset = image1(selected, 0x368, 0x24)
    need(sha256(reset) ==
         "77428a5791705e4b966092c95715a84b617dfd7f414902ff35ae2089d92c93d6",
         "reset body SHA-256")
    need(reset.hex() ==
         "0648804706480047fee7fee7fee7fee7fee7fee7fee7fee7fee7fee701dc000041010000",
         "exact reset body")
    first_literal_va = thumb_literal_address(0x368, u16(reset, 0))
    second_literal_va = thumb_literal_address(0x36C, u16(reset, 4))
    need((first_literal_va, second_literal_va) == (0x384, 0x388), "reset literal locations")
    need((u32(reset, first_literal_va - 0x368),
          u32(reset, second_literal_va - 0x368)) == (0xDC01, 0x141),
         "reset call/branch words")

    # This is intentionally named by position, not guessed as SystemInit.  Its
    # sole raw system-address literal is retained without assigning semantics.
    reset_callee = image1(selected, 0xDC00, 0x14)
    need(reset_callee.hex() == "0348006840f47000014908607047000088ed00e0",
         "exact first reset callee")
    need(sha256(reset_callee) ==
         "720dd0735e0becce7d432e13f0eeb3f5f0d5b9aba240d5b0eaddca5ef557ed89",
         "first reset callee SHA-256")
    need(u32(reset_callee, 0x10) == 0xE000ED88, "first reset callee raw address")

    dispatcher = image1(selected, 0x140, 0xB4)
    need(sha256(dispatcher) ==
         "cf4020e3cdb1b314345608c30d00c1efa1e0ad4cf87bf8e54aa92f568fcb6330",
         "scatter dispatcher SHA-256")
    table = selected[0x5D8A4:0x5D934]
    need(len(table) == 9 * 16, "scatter table extent")
    need(sha256(table) ==
         "73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef",
         "scatter table SHA-256")
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
    rows = [struct.unpack_from("<IIII", table, offset)
            for offset in range(0, len(table), 16)]
    need(rows == expected_rows, "exact image-1 scatter rows")
    for _source, destination, length, _handler in rows:
        need(not overlaps(destination, length, 0x00000000, 0x00040000),
             "no scatter destination in linked code VA domain")
        need(not overlaps(destination, length, 0x44000000, 0x44040000),
             "no scatter destination in selector-0 mapped code view")
        need(not overlaps(destination, length, 0x46000000, 0x46020000),
             "no scatter destination in selector-1 mapped code view")

    # Pin the ordinary launch/context and selector mapper slices.  The mapper
    # establishes address translation for reads; it contains no backing-type
    # or memory-permission declaration.
    need(sha256(image1(selected, 0x2AC, 0x10)) ==
         "b08d19cb6f498725935e2cf4acbf9b0ab11c2339d7448430cee09fdab9077cd0",
         "application launch slice")
    need(sha256(image1(selected, 0x1BA0C, 0x20)) ==
         "c282e390f7fd971029b3b62ef4cc00c5c0d6e6fa4b4dddcaac8cddace4d57827",
         "application/context slice")
    mapper = image1(selected, 0x1BB74, 0x50)
    need(sha256(mapper) ==
         "94da5bec3c7fd05448a66d3828ec420e5cb08e03cb4474a54d07570732d1fe5c",
         "selector mapper slice")

    output = {
        "schema": "code-write-readiness-verification-v1",
        "status": "qualification_gap",
        "offline_only": True,
        "target_operations": 0,
        "selected_sha256": SELECTED_SHA256,
        "current_sha256": CURRENT_SHA256,
        "stored_image1_slot_sha256": SLOT_SHA256,
        "stored_image1_slot_equal": True,
        "mapped_view_read_content_match_proved": True,
        "mapped_view_windows_sequential_not_atomic": True,
        "ordinary_reset_scatter_code_destination_count": 0,
        "first_reset_callee_raw_system_address": "0xe000ed88",
        "first_reset_callee_register_semantics_assigned": False,
        "mutable_backing_classification_proved": False,
        "mapped_view_write_acceptance_proved": False,
        "mapped_view_ram_execution_permission_proved": False,
        "current_core_pc_proved": False,
        "recovery_or_rollback_proved": False,
        "first_missing_proof": "mutable-backing-or-write-permission-for-selector1-mapped-code-view",
        "write_probe_qualified": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
