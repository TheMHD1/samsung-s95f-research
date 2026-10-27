#!/usr/bin/env python3
"""Offline integrity checker for the selected-profile I2C read-family census.

This script reads only the retained package.  It sends no controller command
and does not attempt to decode or invoke a live protocol.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


PROFILE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
PROFILE_SIZE = 5_242_880
PROFILE = (
    Path(__file__).resolve().parent.parent
    / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
)

# Stored-file coordinates.  For image 0, linked VA = file - 0x200.
SLICES = {
    "parser": (0x12AC4, 0x12DBE,
               "5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85"),
    "f7_receive_action": (0x1EEE4, 0x1EFC6,
                          "bdf186399bea803b7ec43d700238ad147607d89e43f56233ba1bc3a9edb2917e"),
    "f7_response_clear": (0x1EED4, 0x1EEE4,
                          "7276da33f6172e31b583e5e11610dcb89473997ab0cb5bc3722b1abfdde188dc"),
    "f7_transmit": (0x1F608, 0x1F65C,
                    "2ae7a0bb909b54b67268f938d7456961ceb7a60a908794ffe15bc767241f1d51"),
    "f7_packet_sum": (0x1EFD4, 0x1EFF2,
                      "0f9c85389f2b5e0bed86756031ba6286b232bfac3e5c756d8971985557ca3e0d"),
    "open_f3": (0x21824, 0x21876,
                "5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe"),
    "d0": (0x21878, 0x218F2,
           "09a4c7e01bb146e2f7d33d78c59f99da83595b9d73fac3c6bc0388f786923349"),
    "f3_getter": (0x2194C, 0x21FF0,
                  "fc3bbd7a16650a34ce0105c0174f6e5099e8f0fc5722844649149016c1cdea07"),
    "f380_getter": (0x21FF8, 0x220EA,
                    "7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0"),
    "fe": (0x2212E, 0x221C6,
           "fc1635b96eeda65f2976cf9ba4fea0ed7b40391cc18827040685b5a5ff712f53"),
}


def need(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit(message)


def main() -> None:
    data = PROFILE.read_bytes()
    need(len(data) == PROFILE_SIZE, "selected profile size mismatch")
    need(hashlib.sha256(data).hexdigest() == PROFILE_SHA256,
         "selected profile SHA-256 mismatch")
    verified = {}
    for name, (start, end, expected) in SLICES.items():
        actual = hashlib.sha256(data[start:end]).hexdigest()
        need(actual == expected, f"slice mismatch: {name}")
        verified[name] = {
            "file_start": f"0x{start:x}",
            "file_end_exclusive": f"0x{end:x}",
            "linked_va_start": f"0x{start - 0x200:x}",
            "sha256": actual,
        }
    report = {
        "input_sha256": PROFILE_SHA256,
        "address_rule": "image0 linked VA = stored file offset - 0x200",
        "verified_slices": verified,
        "finite_transmit_families": {
            "F3:00": "bounded logical selector table; no raw address operand",
            "F3:80": "35-entry selector table; no saved-RT-history selector",
            "D0:00..04": "five bounded arrays",
            "FE": "ten exact commands; four profile reads plus six other cases",
            "F7:00/F7:20": "two byte indices from protocol/status state",
            "F7:40": "31-byte transient action-response buffer",
        },
        "f7_receive_is_control_capable": True,
        "proven_i2c_memory_or_firmware_read_route": False,
        "proven_saved_rt_or_mcu_ram_read_route": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
