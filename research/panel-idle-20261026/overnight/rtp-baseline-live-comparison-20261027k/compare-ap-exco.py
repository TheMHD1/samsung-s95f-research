#!/usr/bin/env python3
"""Compare only the existing AP_EXCO baseline payloads and saved bus bytes."""
import hashlib
import json
from pathlib import Path
import struct

BASE = Path(__file__).resolve().parent.parent


def need(ok, why):
    if not ok:
        raise ValueError(why)


def load(path, digest):
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == digest, str(path))
    return raw


def main():
    package = load(BASE / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin",
        "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    backup = load(BASE / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin",
        "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562")
    observed = load(BASE / "finite-onset-logger-20261027g/selector-context-after-v6/alternate-window.bin",
        "2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a")
    directory = package[0x85e00:0x86000]
    need(directory == backup[0x85e00:0x86000], "AP_EXCO record equality")
    need(directory[:32] == b"AP_EXCO" + bytes(25), "AP_EXCO name")
    expected = {0x20: 4, 0x24: 0x1b0000, 0x28: 1, 0x2c: 0x102200,
                0x6c: 0, 0xac: 0x33a, 0xf0: 1, 0xf4: 0x102600,
                0x134: 0x400, 0x174: 0x1200}
    for offset, value in expected.items():
        need(struct.unpack_from("<I", directory, offset)[0] == value, f"metadata {offset:#x}")
    first = 0x80000 + expected[0x2c]
    second = 0x80000 + expected[0xf4]
    source_alternate = second + 0x3d8 - expected[0xac]
    payloads = []
    for offset, size in ((first, expected[0xac]), (second, expected[0x174])):
        a, b = package[offset:offset+size], backup[offset:offset+size]
        need(len(a) == size and a == b, "baseline payload equality")
        payloads.append({"file_offset": hex(offset), "bytes": size,
                         "sha256": hashlib.sha256(a).hexdigest(), "equal": True})
    static_pair = [package[source_alternate], package[first]]
    bus_pair = [observed[7], observed[8]]
    print(json.dumps({
        "schema": "ap-exco-baseline-vs-candidate-live-v1", "target_operations": 0,
        "selected_and_backup_directory_equal": True,
        "directory_sha256": hashlib.sha256(directory).hexdigest(),
        "selected_and_backup_payloads": payloads,
        "baseline_source_file_offsets": [hex(source_alternate), hex(first)],
        "selected_and_backup_source_pair": static_pair,
        "candidate_bus_addresses": ["0x47000bc7", "0x47000bc8"],
        "candidate_bus_pair": bus_pair,
        "candidate_pair_matches_both_baselines": bus_pair == static_pair,
        "candidate_context_prefix_matches_startup": observed[:6] == bytes.fromhex("70088007400b"),
        "limitations": [
            "These are already copied baseline artifacts and earlier saved bus bytes.",
            "No fresh storage, configuration-bank, persistence or target access occurred.",
            "Candidate bus/CPU interpretation remains conditional.",
            "Mismatch does not identify which runtime writer, callback or configuration state produced it.",
            "The AP_EXCO source object itself was not sampled live.",
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
