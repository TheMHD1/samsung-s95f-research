#!/usr/bin/env python3
"""Decode retained fixed-window bytes offline; never contacts the TV."""
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
RUN = HERE / "fault-context-after-v6"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def pinned(name, size, digest):
    data = (RUN / name).read_bytes()
    need(len(data) == size, name + " size")
    need(hashlib.sha256(data).hexdigest() == digest, name + " SHA256")
    return data


def main():
    context = pinned("context.bin", 64,
        "0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439")
    rt = pinned("rt.bin", 256,
        "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9")
    record = json.loads((RUN / "record.json").read_text())
    need(record["expected_boot_id"] == "00000000-0000-4000-8000-000000000000", "boot")
    need(record["native_terminal_validated"] is True, "native accepted")
    need(record["cleanup_required"] is False, "stage cleaned")
    need(record["target_operations"] == 2, "request count")
    h = lambda data, offset: struct.unpack_from("<H", data, offset)[0]
    values = {
        "context_f04": h(context, 4), "context_f06": h(context, 6),
        "context_f08": h(context, 8),
    }
    for offset in (0x2400, 0x2406, 0x240A, 0x2410, 0x2430, 0x2432,
                   0x2440, 0x249E, 0x24A0, 0x24A2, 0x24C0, 0x24C4,
                   0x24D2, 0x24D6):
        values[f"rt_{offset:04x}"] = h(rt, offset - 0x2400)
    package = (HERE.parent / "selected-qd-profile-copy-20261027b" /
               "F_RSM1_BN9659934B_COMMON.bin").read_bytes()
    backup = (HERE.parent / "firmware-fingerprint-20261027d" /
              "full-backup-recovered/fixeddata.bin").read_bytes()
    need(hashlib.sha256(package).hexdigest() ==
         "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "package pin")
    need(hashlib.sha256(backup).hexdigest() ==
         "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562", "backup pin")
    # Source arithmetic follows the separately verified AP_RTP loader, not
    # the similarly named logical configuration prefix 0x210000.
    directory = package[0x86000:0x86200]
    need(directory[:32] == b"AP_RTP" + bytes(26), "AP_RTP name")
    need(directory == backup[0x86000:0x86200], "stored AP_RTP directory equality")
    need(struct.unpack_from("<I", directory, 0x20)[0] == 4, "MCU-copy type")
    need(struct.unpack_from("<I", directory, 0x2c)[0] == 0x103800, "first source")
    need(struct.unpack_from("<I", directory, 0xac)[0] == 0x100, "first length")
    defaults = package[0x183800:0x183900]
    need(defaults == backup[0x183800:0x183900], "stored parameter equality")
    comparisons = []
    for offset in (0x2430, 0x2432, 0x2440, 0x249e, 0x24a0, 0x24a2,
                   0x24c0, 0x24c4, 0x24d2, 0x24d6):
        default = h(defaults, offset - 0x2400)
        late = values[f"rt_{offset:04x}"]
        comparisons.append({"root_relative_offset": f"0x{offset:04x}",
                            "package_and_backup_value": default,
                            "late_bus_window_value": late, "equal": default == late})
    cases = []
    for mode, alternate, score, limit, direct in (
        (1, False, "context_f08", "rt_2430", True),
        (1, True,  "context_f08", "rt_24c4", True),
        (2, None,  "context_f08", "rt_2432", False),
        (4, None,  "context_f08", "rt_2440", True),
        (6, False, "context_f06", "rt_24c0", True),
        (6, True,  "context_f06", "rt_24c4", True),
    ):
        cases.append({"hypothetical_mode": mode, "alternate_selector": alternate,
                      "direct_call_in_package": direct,
                      "score_field": score, "score": values[score],
                      "limit_field": limit, "limit": values[limit],
                      "late_numeric_greater": values[score] > values[limit]})
    prior = (HERE / "onset-v6/restored-rt.bin").read_bytes()
    need(len(prior) == 64, "V6 RT prefix size")
    result = {
        "schema": "offline-v6-late-context-decode-v1",
        "target_operations": 0,
        "bus_windows": [{"address": "0x47010f00", "bytes": 64},
                        {"address": "0x47012400", "bytes": 256}],
        "terminal_uptime": record["terminal"]["uptime"],
        "seconds_after_v6_window_end_approx": round(
            float(record["terminal"]["uptime"].split()[0]) - 115907.45, 2),
        "values_u16_le": values,
        "selected_ap_rtp_directory_equal_to_backup": True,
        "selected_ap_rtp_field_payload_equal_to_backup": True,
        "ap_rtp_field_payload_sha256": hashlib.sha256(defaults).hexdigest(),
        "selected_and_stored_initial_value_comparisons": comparisons,
        "hypothetical_late_comparisons": cases,
        "rt_prefix_equal_to_v6_post_block": rt[:64] == prior,
        "all_halfwords": {
            f"0x{base + i:08x}": h(data, i)
            for base, data in ((0x47010F00, context), (0x47012400, rt))
            for i in range(0, len(data), 2)
        },
        "limitations": [
            "Bus-window values; image-1 CPU alias remains conditional.",
            "Sequential late reads are neither atomic nor event-time values.",
            "Non-mode-6 latch is shared; it does not establish the actual mode.",
            "Alternate selector and event-time mode globals were not sampled.",
            "Numeric compatibility is not proof of the V6 triggering comparison.",
            "No physical picture observation, recovery, or prevention is established.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
