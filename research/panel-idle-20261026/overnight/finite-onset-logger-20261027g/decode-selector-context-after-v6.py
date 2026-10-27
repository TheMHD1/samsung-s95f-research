#!/usr/bin/env python3
"""Offline decoder of the completed fixed selector capture, with raw pins."""
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
RUN = HERE / "selector-context-after-v6"


def need(ok, why):
    if not ok:
        raise ValueError(why)


def pinned(name, size, digest):
    raw = (RUN / name).read_bytes()
    need(len(raw) == size and hashlib.sha256(raw).hexdigest() == digest, name)
    return raw


def main():
    mode = pinned("mode-window.bin", 68,
        "c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9")
    alt = pinned("alternate-window.bin", 16,
        "2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a")
    record = json.loads((RUN / "record.json").read_text())
    need(record["expected_boot_id"] == "00000000-0000-4000-8000-000000000000", "boot")
    need(record["native_terminal_validated"] is True and
         record["cleanup_required"] is False and record["target_operations"] == 2,
         "accepted terminal and cleanup")
    h = lambda offset: struct.unpack_from("<H", mode, offset)[0]
    root = struct.unpack_from("<I", mode, 0x40)[0]
    aa, ac, mirror, mirror_control = h(0xa), h(0xc), h(0x22), h(0x24)
    root_matches = root == 0x20010000
    proposed_mode = (4 if aa == 1 else 6 if ac == 1 else 1) if root_matches else None
    result = {
        "schema": "offline-v6-late-selector-decode-v1", "target_operations": 0,
        "terminal_uptime": record["terminal"]["uptime"],
        "seconds_after_v6_end_approx": round(
            float(record["terminal"]["uptime"].split()[0]) - 115907.45, 2),
        "mode_window_hex": mode.hex(), "candidate_window_hex": alt.hex(),
        "root_word": f"0x{root:08x}", "root_anchor_matches": root_matches,
        "aa_raw_u16": aa, "ac_raw_u16": ac,
        "tail_mode_if_reached_under_conditional_cpu_model": proposed_mode,
        "scan_counter_a0_raw_u16": h(0),
        "alternate_mirror_c2_raw_u16": mirror,
        "mirror_control_c4_raw_u16": mirror_control,
        "ordinary_scan_argument_d8_raw_byte": mode[0x38],
        "candidate_alternate_byte_7": alt[7],
        "candidate_source_plus_zero_byte_8": alt[8],
        "candidate_startup_constants_match": alt[:6] == bytes.fromhex("70088007400b"),
        "candidate_flag_matches_numeric_mirror": alt[7] == mirror,
        "candidate_pair_matches_selected_package_defaults": alt[7:9] == bytes([20, 0]),
        "mirror_control_matches_simple_nonzero_model": mirror_control == int(mirror != 0),
        "candidate_alternate_alias_promoted": False,
        "all_mode_halfwords": {
            f"0x{0x470004a0+i:08x}": h(i) for i in range(0, len(mode), 2)
        },
        "all_candidate_bytes": {
            f"0x{0x47000bc0+i:08x}": byte for i, byte in enumerate(alt)
        },
        "interpretation": [
            "Same-response root anchors a conditional image-1 mode sample.",
            "Local startup constants and mirror agreement corroborate candidate layout.",
            "Candidate source bytes differ from selected packaged defaults.",
            "Current flags would select mode 1 if the ordinary predicate were reached.",
            "The ordinary scan argument is zero; no active comparison is inferred.",
            "These sequential late bytes do not reconstruct the V6 event-time operands.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
