#!/usr/bin/env python3
"""Offline verifier for the retained V6 rtp_act_736 onset evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
V6 = HERE / "onset-v6"
PACKAGE = BASE / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
HELPER = BASE / "overnight/managed-usb-secondary-logger-onset-framing"
WIRE_REPORT = BASE / "tcon-research/qd-profile-rt-status-wire.md"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_bytes(path: Path, expected_sha256: str) -> bytes:
    data = path.read_bytes()
    need(sha256(data) == expected_sha256, f"SHA-256 mismatch: {path}")
    return data


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def thumb_bl_target(data: bytes, address: int) -> int:
    """Decode a Thumb-2 BL at address from its four instruction bytes."""
    need(len(data) == 4, "BL width")
    first, second = struct.unpack("<HH", data)
    need(first & 0xF800 == 0xF000, "BL first halfword")
    need(second & 0xD000 == 0xD000, "BL second halfword")
    s = (first >> 10) & 1
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    i1 = 1 ^ (j1 ^ s)
    i2 = 1 ^ (j2 ^ s)
    value = (s << 24) | (i1 << 23) | (i2 << 22) | ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1)
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def image1(package: bytes, va: int, length: int) -> bytes:
    return package[0x40200 + va : 0x40200 + va + length]


def image0(package: bytes, va: int, length: int) -> bytes:
    return package[0x200 + va : 0x200 + va + length]


def main() -> None:
    outcome_raw = file_bytes(
        V6 / "native-outcome.json",
        "1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9",
    )
    baseline = file_bytes(
        V6 / "baseline-ring.bin",
        "b889e9001401d03257a0673e483da061b6788a5832e891dccd6cb9fbb1ff588e",
    )
    post = file_bytes(
        V6 / "post-ring.bin",
        "c81eaa908cf0b0f3bacc456f846e837b41d390a85c6de666ca7ae0f8091529d1",
    )
    pre_rt = file_bytes(
        V6 / "prearm-rt.bin",
        "eed5edc3c31936e3d9612360ac9b994ba086e90378f6b8cfa0ce4e89524a0568",
    )
    armed_rt = file_bytes(
        V6 / "armed-rt.bin",
        "5ccebe4abe8c8e7b81291392b96ad2f0c34b3691ba9cc02839c1fdb12b292245",
    )
    restored_rt = file_bytes(
        V6 / "restored-rt.bin",
        "2175e6ce7455123b8071e9edb3b3ada855107d182650c47a307f31bdd39a6ab8",
    )
    host_status_raw = file_bytes(
        HERE / "after-v6-host-status.json",
        "5f8662e4cfed25563b59a303bd94190d2463e5c584dd117de15b219fd2e0e6e0",
    )
    cached_status_raw = file_bytes(
        HERE / "after-v6-cached-kernel-status.json",
        "c896f10b2b73e39db73df4a103624490a04ca9f5c9c402da9c9581643ffd3e56",
    )
    fault_pin_raw = file_bytes(
        HERE / "after-v6-fault-pin.json",
        "ce16a42b0bdac28fa78498a52a860b128d13693243de278ce76d0d4708da19c0",
    )

    outcome = json.loads(outcome_raw)
    expected_outcome = {
        "Stage": "complete",
        "ProtocolPhase": "ReadyForHeader",
        "Accepted": True,
        "ArmVerified": True,
        "ObservationCompleted": True,
        "RestoreVerified": True,
        "RestoreUnverified": False,
        "LogFlagMayRemainChanged": False,
        "BaselineWriteCursor": 143,
        "BaselineReadCursor": 143,
        "PreArmGate": 0,
        "PreArmFault": 0,
        "ArmedGate": 1,
        "RestoredGate": 0,
    }
    for key, value in expected_outcome.items():
        need(outcome.get(key) == value, f"native outcome {key}")
    need(len(outcome.get("Steps", [])) == 16, "exact native step count")
    need(not outcome.get("Errors"), "native errors absent")

    need(len(baseline) == len(post) == 0x3C0C, "ring snapshot extent")
    base_write, base_read, base_flag = struct.unpack_from("<III", baseline)
    post_write, post_read, post_flag = struct.unpack_from("<III", post)
    need((base_write, base_read, base_flag) == (143, 143, 0), "baseline ring header")
    need((post_write, post_read, post_flag) == (1899, 1899, 0), "post ring header")
    need(post_write >= base_write, "non-wrapped retained delta")
    delta = post[12 + base_write : 12 + post_write]
    need(len(delta) == 1756, "ring delta length")
    need(sha256(delta) == "deccf31188b565c7c4c9aadcb838e042c55f81f94ffae7c88093902dc21678ba", "ring delta SHA-256")
    event_line = b"rtp_act_736\n"
    need(delta.count(event_line) == 2, "exactly two event lines")
    need(delta.endswith(event_line * 2), "event pair terminates delta")
    need(delta.count(b"rtp_act_") == 2, "no other rtp_act line in delta")
    need(b"[RTP]END\n" in delta and b"[RTP:NORMAL][395]\n" in delta, "bounded RTP lead-in")

    for name, snapshot in (("pre", pre_rt), ("armed", armed_rt), ("restored", restored_rt)):
        need(len(snapshot) == 64, f"{name} RT snapshot extent")
    need((u16(pre_rt, 0), u16(pre_rt, 6), u16(pre_rt, 10)) == (0, 0, 0), "pre RT event/gate/fault")
    need((u16(armed_rt, 0), u16(armed_rt, 6), u16(armed_rt, 10)) == (0, 1, 0), "armed RT event/gate/fault")
    need((u16(restored_rt, 0), u16(restored_rt, 6), u16(restored_rt, 10)) == (1, 0, 0x1001), "post RT event/gate/fault")
    need(u16(restored_rt, 14) == 0, "common setter cleared +0x240e")

    boot_id = "00000000-0000-4000-8000-000000000000"
    host_status = json.loads(host_status_raw)
    need(host_status.get("accepted") is True and host_status.get("one_shot") is True, "accepted one-shot host status")
    need(host_status["execution"]["boot_id"] == boot_id, "host status same boot")
    need(host_status["execution"]["result"]["status_hex"] == "0x00000010", "later host status 0x10")
    need(host_status["execution"]["helper_pid"] == 15976, "host status helper PID")
    need(116071.6 < host_status["execution"]["execute_uptime"] < 116071.8, "host status uptime")
    cached_status = json.loads(cached_status_raw)
    cached_stdout = cached_status["calls"][0]["response"]["commands"][0]["stdout"]
    need(boot_id in cached_stdout, "cached status same boot")
    need("QDFTcon_GetErrDetStatus[15976:TconStatusRead.]: ERR DET Status:0x10" in cached_stdout, "matching raw kernel status line")
    fault_pin = json.loads(fault_pin_raw)
    need(fault_pin.get("accepted") is True and fault_pin.get("one_shot") is True, "accepted one-shot fault pin")
    need(fault_pin["execution"]["boot_id"] == boot_id, "fault pin same boot")
    need(fault_pin["execution"]["result"]["value"] == 1, "later fault pin asserted")

    manifest = file_bytes(
        HELPER / "build-manifest.json",
        "b1ffc0f91b614163e10e4132b9410c60116d22101b5666f1614ef471b4938780",
    )
    need(b'"schema": "usb-fixed-secondary-logger-onset-framing-build-v1"' in manifest, "build manifest schema")
    program = file_bytes(
        HELPER / "Program.cs",
        "db45feac5d5bda5e670da51be296cdb39769f898b4d7c8d9224a36cc65e13cdd",
    )
    need(b'Convert.FromHexString("010100000024014740000000")' in program, "fixed RT read address")

    package = file_bytes(
        PACKAGE,
        "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0",
    )
    need(len(package) == 5 * 1024 * 1024, "selected package extent")
    caller = image1(package, 0x1E68, 0x2040 - 0x1E68)
    need(sha256(caller) == "c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a", "event-736 caller body")
    need(image1(package, 0x2036, 4).hex() == "4ff43870", "mov.w r0,#0x2e0")
    need(thumb_bl_target(image1(package, 0x203A, 4), 0x203A) == 0xC1E0, "event caller reaches common setter")

    setter = image1(package, 0xC1E0, 0xC212 - 0xC1E0)
    need(sha256(setter) == "f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102", "common setter body")
    need(image1(package, 0xC1EA, 0x18).hex() == "01214ff410500153002142f20e40015341f20101001f0153", "setter 1/0/0x1001 stores")
    need(thumb_bl_target(image1(package, 0xC206, 4), 0xC206) == 0x1B8C8, "first formatter call")
    need(thumb_bl_target(image1(package, 0xC20E, 4), 0xC20E) == 0x1B8C8, "second formatter call")
    need(image1(package, 0xC214, 12) == b"rtp_act_%d\n\0", "exact event format literal")

    live_check = image0(package, 0x214D4, 0x21512 - 0x214D4)
    need(sha256(live_check) == "6636bd288c51f566df590a89e48aabb761377a5da4a64d01e868a8fdee371049", "fixed-window live checker")
    need(thumb_bl_target(image0(package, 0x214D6, 4), 0x214D6) == 0xEF94, "fixed-root accessor call")
    need(image0(package, 0x214DC, 0x12).hex() == "42f20a40005d00f0010030b10aa0dff73ff8", "bit-zero test and diagnostic edge")
    need(image0(package, 0x214F0, 2).hex() == "1020", "selector 0x10 literal")
    need(thumb_bl_target(image0(package, 0x214F2, 4), 0x214F2) == 0xB660, "selector 0x10 common path")
    need(image0(package, 0xEF94, 8).hex() == "0048704700000147", "fixed-root accessor and 0x47010000 literal")

    selector_store = image0(package, 0x2B764, 0x16)
    need(sha256(selector_store) == "3d538c104bca6958c66173c7d56a095ded57e9453134e78933ee6d0e26fffb03", "selector store body")
    wire_selector = image0(package, 0x21DF8, 0xF2)
    need(sha256(wire_selector) == "7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0", "host-wire selector table body")
    need(image0(package, 0x21E66, 8).hex() == "ecf703fc008ae5e7", "selector case 8 loads common +0x10")
    file_bytes(WIRE_REPORT, "6c532e2ad8a48041cf83ebddfa42af1282019d14169902b47e621f6a1c237f6e")

    result = {
        "schema": "rtp-act-736-trace-verification-v1",
        "v6_outcome_sha256": sha256(outcome_raw),
        "ring_delta_bytes": len(delta),
        "ring_delta_sha256": sha256(delta),
        "rtp_act_736_lines": delta.count(event_line),
        "pre_fault": u16(pre_rt, 10),
        "post_fault": u16(restored_rt, 10),
        "event_code_hex": "0x2e0",
        "event_code_decimal": 736,
        "packaged_setter_value_hex": "0x1001",
        "fixed_window_consumer": "0x4701240a bit0 -> selector 0x10",
        "host_wire_mapping": "F3 80 00 00 00 08 -> 00 00 00 10 (packaged static path)",
        "later_same_boot_host_status_hex": host_status["execution"]["result"]["status_hex"],
        "later_same_boot_fault_pin": fault_pin["execution"]["result"]["value"],
        "host_status_after_observation_seconds": round(host_status["execution"]["execute_uptime"] - 115907.45, 2),
        "physical_picture_observed": False,
        "whole_live_image_identity_proved": False,
        "offline_only": True,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
