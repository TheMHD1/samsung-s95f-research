#!/usr/bin/env python3
"""Decode the already-faulted X capture without any target operation."""

from pathlib import Path
import base64
import hashlib
import json
import struct

HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
CAPTURE = HERE / "capture-once"


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, digest):
    raw = path.read_bytes()
    need(sha(raw) == digest, "SHA-256 " + str(path))
    return raw


def u16(raw, offset):
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw, offset):
    return struct.unpack_from("<I", raw, offset)[0]


def main():
    # Retained bus bytes do not independently establish the live CPU/core
    # meaning of every alias. Keep the reviewed mapping boundary pinned.
    load(OVERNIGHT / "rtp-observer-feasibility-20261027u/rtp-observer-feasibility.md",
         "04edd954e64ca01f817faa3dfa14469155e2b30253885b60a80c4ff870f64e3a")
    pins = {
        "result.json": "10453603e86c148fb745d69aafa03200d17f903e92824fa4468cedb41cc69392",
        "record.json": "1d6323c136373cc8a55d364014ceaa44cc1e473773977184c28f7fc5551604ca",
        "native.stdout.bin": "2aa93e27503ea1b77d15d630cf7241159a12427bca0726d080991e77bba8fd05",
        "native.stderr.bin": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "retained-00-initial_faulted-cycle001-00-R.bin":
            "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9",
        "retained-01-post_fault-cycle001-00-M.bin":
            "c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9",
        "retained-01-post_fault-cycle001-01-C.bin":
            "2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a",
        "retained-01-post_fault-cycle001-02-H.bin":
            "d94f16ac03ed209ece31c6e35b49d89a81755681fabf296b3bc5a37013c3fe42",
        "retained-01-post_fault-cycle001-03-L.bin":
            "0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439",
        "retained-01-post_fault-cycle001-04-R.bin":
            "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9",
    }
    raw = {name: load(CAPTURE / name, digest) for name, digest in pins.items()}
    result = json.loads(raw["result.json"])
    record = json.loads(raw["record.json"])
    need(result["schema"] == "managed-usb-rt-passive-observer-wrapper-result-v1" and
         result["terminal_reason"] == "AlreadyFaulted" and result["onset_missed"] is True and
         result["onset_observed"] is False and result["transport_accepted"] is True and
         result["native_accepted"] is True and result["samples_sequential_not_atomic"] is True and
         result["target_read_requests"] == 6 and result["bulk_transfers"] == 12 and
         result["cleanup"] == "STAGE_ABSENT" and result["bus_contents_altered"] is False,
         "wrapper result contract")
    need(record["terminal"] == {
        "boot_id": "00000000-0000-4000-8000-000000000000", "exit_code": 0,
        "stderr_sha256": sha(b""), "stdout_sha256": pins["native.stdout.bin"],
        "uptime": "126642.16 472352.66"}, "record terminal")
    need(record["target_operations"] == 6 and
         record["target_operations_status"] == "accepted_exact_read_requests" and
         record["native_invocations"] == 1 and record["cleanup_required"] is False,
         "record accounting")

    lines = raw["native.stdout.bin"].decode().splitlines()
    need(len(lines) == 3 and lines[1].startswith("[GC_INFO] ") and
         lines[2].startswith("[GC_INFO] "), "native output classification")
    native = json.loads(lines[0])
    need(native["schema"] == "managed-usb-rt-passive-observer-v1" and
         native["stage"] == "terminal" and native["terminalReason"] == "AlreadyFaulted" and
         native["protocolPhase"] == "ReadyForHeader" and native["accepted"] is True and
         native["opened"] is True and native["claimed"] is True and
         native["released"] is True and native["closed"] is True and
         native["writes"] == 0 and native["retries"] == 0 and
         native["bulkTransfers"] == 12 and native["headersSent"] == 6 and
         native["inputsCompleted"] == 6 and native["cyclesStarted"] == 1,
         "native terminal contract")
    need(native["startUs"] == 126641969582 and native["endUs"] == 126641984282,
         "native monotonic extent")

    groups = native["retained"]
    need([group["role"] for group in groups] == ["initial-faulted", "post-fault"],
         "retention roles")
    expected_names = [["R"], ["M", "C", "H", "L", "R"]]
    file_names = [["retained-00-initial_faulted-cycle001-00-R.bin"],
                  ["retained-01-post_fault-cycle001-00-M.bin",
                   "retained-01-post_fault-cycle001-01-C.bin",
                   "retained-01-post_fault-cycle001-02-H.bin",
                   "retained-01-post_fault-cycle001-03-L.bin",
                   "retained-01-post_fault-cycle001-04-R.bin"]]
    for group, names, files in zip(groups, expected_names, file_names):
        need([window["name"] for window in group["windows"]] == names, "window order")
        for window, filename in zip(group["windows"], files):
            payload = base64.b64decode(window["rawBase64"], validate=True)
            need(payload == raw[filename] and window["sha256"] == sha(payload) and
                 window["count"] == window["expected"] == len(payload) and
                 window["complete"] is True, "retained window " + filename)
    transfer_names = ["R-header", "R-data", "M-header", "M-data", "C-header", "C-data",
                      "H-header", "H-data", "L-header", "L-data", "R-header", "R-data"]
    transfers = groups[0]["transfers"] + groups[1]["transfers"]
    need([row["name"] for row in transfers] == transfer_names, "transfer order")
    previous = 0
    expected_counts = [12, 256, 12, 68, 12, 16, 12, 96, 12, 64, 12, 256]
    for row, count in zip(transfers, expected_counts):
        need(row["expected"] == row["count"] == count and row["errno"] == 0 and
             row["beforeUs"] >= previous and row["afterUs"] >= row["beforeUs"],
             "exact transfer " + row["name"])
        previous = row["afterUs"]

    r_initial = raw[file_names[0][0]]
    m, c, h, l, r = [raw[name] for name in file_names[1]]
    need((len(m), len(c), len(h), len(l), len(r)) == (68, 16, 96, 64, 256),
         "window extents")
    need(r_initial == r, "initial and final R equality")

    mode = {"aa": u16(m, 0x0A), "ac": u16(m, 0x0C),
            "alternate_mirror": u16(m, 0x22), "mirror_companion": u16(m, 0x24),
            "scan_argument": m[0x38], "root_anchor": u32(m, 0x40),
            "alternate_byte_7": c[7]}
    need(mode == {"aa": 0, "ac": 2, "alternate_mirror": 1,
                  "mirror_companion": 0, "scan_argument": 0,
                  "root_anchor": 0x20010000, "alternate_byte_7": 1}, "M/C fields")
    need(c == bytes.fromhex("70088007400b5c010300000000000000"), "C raw candidate")

    aggregates = [u32(h, 4 + 4 * index) for index in range(6)]
    q = [u16(h, 0x1C + 2 * index) for index in range(6)]
    histories = [[u16(h, 0x28 + 8 * index + 2 * slot) for slot in range(4)]
                 for index in range(6)]
    need(aggregates == [44, 0, 0, 0, 0, 0] and q == [0] * 6 and
         histories == [[6, 0, 0, 6]] + [[0, 0, 0, 0]] * 5, "H mode arrays")

    latches = {"latest_subtractor": u16(l, 4), "mode6": u16(l, 6),
               "shared_non_mode6": u16(l, 8)}
    need(latches == {"latest_subtractor": 0, "mode6": 54, "shared_non_mode6": 44},
         "L latches")
    rt = {"stop": u16(r, 0), "logger_gate": u16(r, 6), "fault": u16(r, 0x0A),
          "ordinary_gate": u16(r, 0x0E),
          "limits": [u16(r, offset) for offset in (0x30, 0x32, 0x40, 0xC0, 0xC4)],
          "actions": {"mode1": u16(r, 0x86), "mode2": u16(r, 0x88),
                      "mode4_or_6_shared": u16(r, 0x8C)}}
    need(rt == {"stop": 1, "logger_gate": 0, "fault": 0x1001, "ordinary_gate": 0,
                "limits": [200, 0, 0, 200, 40],
                "actions": {"mode1": 7, "mode2": 0, "mode4_or_6_shared": 0}},
         "R fields")

    # Under the qualified CPU aliases and selected-code interpretation, the
    # sequential late fields would choose mode 1 and its alternate limit.
    mode_candidate = 1
    selected_limit_offset, selected_limit = "R+0x24c4", rt["limits"][4]
    a32 = aggregates[mode_candidate - 1]
    low_a = a32 & 0xFFFF
    need(mode["aa"] != 1 and mode["ac"] != 1 and mode["alternate_byte_7"] != 0 and
         selected_limit == 40 and a32 == low_a == 44 and low_a > selected_limit and
         latches["shared_non_mode6"] == low_a, "late mode-1 candidate")
    need(aggregates[5] == 0 and latches["mode6"] == 54,
         "sequential H mode-6 zero then L latch 54")

    # Bind the exact repetitions at prior late epochs. Equality is evidence of
    # returned state at discrete times only, not continuous immutability.
    prior = {
        "mode_result": load(OVERNIGHT / "finite-onset-logger-20261027g/selector-context-after-v6/result.json",
                            "d2c3a49f2bd721eb6a33eed70776689386cf32bacab036459fcff2f16795c703"),
        "mode_record": load(OVERNIGHT / "finite-onset-logger-20261027g/selector-context-after-v6/record.json",
                            "374d2e56348cfbe02d1b78a0904b1fe245fef4605048cc522c2f8883c27e4e31"),
        "mode_M": load(OVERNIGHT / "finite-onset-logger-20261027g/selector-context-after-v6/mode-window.bin",
                       pins["retained-01-post_fault-cycle001-00-M.bin"]),
        "mode_C": load(OVERNIGHT / "finite-onset-logger-20261027g/selector-context-after-v6/alternate-window.bin",
                       pins["retained-01-post_fault-cycle001-01-C.bin"]),
        "fault_result": load(OVERNIGHT / "finite-onset-logger-20261027g/fault-context-after-v6/result.json",
                             "8c03aa8af4155f77adca558dcbbb8f37ee6fe0f03e1efa9c4450634c28dacdec"),
        "fault_record": load(OVERNIGHT / "finite-onset-logger-20261027g/fault-context-after-v6/record.json",
                             "017e4b0a749b95a7df3dcc35a7a60fb4a2bed060ddebcb9d97718a7e952acac5"),
        "fault_L": load(OVERNIGHT / "finite-onset-logger-20261027g/fault-context-after-v6/context.bin",
                        pins["retained-01-post_fault-cycle001-03-L.bin"]),
        "fault_R": load(OVERNIGHT / "finite-onset-logger-20261027g/fault-context-after-v6/rt.bin",
                        pins["retained-01-post_fault-cycle001-04-R.bin"]),
        "repeat_result": load(OVERNIGHT / "current-host-health-20261027v/rt-context-once/result.json",
                              "c7a0a3931895a4e529f94492dc1abe1377a40dadfb6bb911f008120361e37cfe"),
        "repeat_record": load(OVERNIGHT / "current-host-health-20261027v/rt-context-once/record.json",
                              "88c3abd7b00f153946f04b4562652da5598f1a6cc05f84e026e5ca2f98ee1193"),
        "repeat_L": load(OVERNIGHT / "current-host-health-20261027v/rt-context-once/context.bin",
                         pins["retained-01-post_fault-cycle001-03-L.bin"]),
        "repeat_R": load(OVERNIGHT / "current-host-health-20261027v/rt-context-once/rt.bin",
                         pins["retained-01-post_fault-cycle001-04-R.bin"]),
    }
    need(prior["mode_M"] == m and prior["mode_C"] == c and
         prior["fault_L"] == prior["repeat_L"] == l and
         prior["fault_R"] == prior["repeat_R"] == r, "prior exact repetitions")
    prior_records = [json.loads(prior[key]) for key in ("mode_record", "fault_record", "repeat_record")]
    need([item["terminal"]["uptime"].split()[0] for item in prior_records] ==
         ["119358.55", "117834.25", "124639.19"], "prior terminal uptimes")

    v6 = json.loads(load(OVERNIGHT / "finite-onset-logger-20261027g/onset-v6/native-outcome.json",
                         "1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9"))
    v6_start = float(v6["ObserveStartUptime"].split()[0])
    v6_end = float(v6["ObserveEndUptime"].split()[0])
    candidate_first_us = groups[1]["transfers"][0]["beforeUs"]
    candidate_last_us = groups[1]["transfers"][-1]["afterUs"]
    # Compare Linux uptime with Linux uptime. The native monotonic timestamps
    # are a separate clock domain and do not prove a microsecond event-age bound.
    terminal_uptime = float(record["terminal"]["uptime"].split()[0])
    terminal_gap_min = terminal_uptime - v6_end
    terminal_gap_max = terminal_uptime - v6_start
    need((v6_start, v6_end) == (115887.39, 115907.45) and
         round(terminal_gap_min, 2) == 10734.71 and round(terminal_gap_max, 2) == 10754.77 and
         candidate_last_us - candidate_first_us == 427, "terminal uptime gap and request span")

    output = {
        "schema": "rt-passive-observer-retained-state-decoder-v1", "target_operations": 0,
        "terminal_reason": "AlreadyFaulted", "onset_missed": True,
        "capture_terminal_uptime": 126642.16,
        "v6_observation_uptime": [v6_start, v6_end],
        "v6_to_X_terminal_uptime_seconds": [round(terminal_gap_min, 2), round(terminal_gap_max, 2)],
        "cross_clock_event_age_bound_proved": False,
        "cpu_aliases_conditional": True,
        "live_core_tag_sampled": False,
        "alias_qualification": {
            "M": "same-response root anchor supports consistency, not every alias",
            "C": "raw candidate; CPU meaning conditional",
            "H": "allocated extent; no live core tag or same-response anchor",
            "L_R": "CPU meanings conditional on non-A mapper interpretation",
        },
        "candidate_host_request_span_us": candidate_last_us - candidate_first_us,
        "mode_fields": mode, "aggregates_A32": aggregates, "q": q, "histories": histories,
        "latches": latches, "rt": rt,
        "late_candidate": {"mode": mode_candidate, "selected_limit_offset": selected_limit_offset,
                           "selected_limit": selected_limit, "A32": a32, "low16_A32": low_a,
                           "comparison_low16_A32_gt_limit": low_a > selected_limit,
                           "shared_latch_matches_low16_A32": True,
                           "under_qualified_alias_and_selected_code_assumptions": True,
                           "event_time_tuple": False},
        "mode6_sequential_A32_read_zero_then_latch_read_54": True,
        "simultaneous_mode6_divergence_proved": False,
        "mode6_latch_stale_at_L_read_proved": False,
        "M_C_repeat_since_uptime": 119358.55,
        "L_R_repeat_uptimes": [117834.25, 124639.19, 126642.16],
        "samples_sequential_not_atomic": True, "physical_cause_inferred": False,
        "reset_or_overwrite_reason_inferred": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
