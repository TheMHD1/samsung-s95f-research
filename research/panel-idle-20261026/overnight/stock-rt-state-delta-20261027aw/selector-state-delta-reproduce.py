#!/usr/bin/env python3
"""Reproduce the bounded pre/post selector and score-state comparison offline."""

from pathlib import Path
import base64
import hashlib
import json
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
AV = OVERNIGHT / "stock-rt-lifecycle-trial-20261027av"
G = OVERNIGHT / "finite-onset-logger-20261027g"
X = OVERNIGHT / "rt-passive-observer-20261027x"


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(path, expected):
    raw = path.read_bytes()
    need(digest(raw) == expected, "SHA-256 mismatch: " + str(path))
    return raw


def u16(raw, offset):
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw, offset):
    return struct.unpack_from("<I", raw, offset)[0]


def changed(before, after):
    need(len(before) == len(after), "delta length")
    return [[index, left, right] for index, (left, right)
            in enumerate(zip(before, after)) if left != right]


def terminal(path, expected_sha, expected_reason):
    lines = pinned(path, expected_sha).decode().splitlines()
    need(lines and all(line.startswith("[GC_INFO] ") for line in lines[1:]),
         "native output framing")
    value = json.loads(lines[0])
    need(value["schema"] == "managed-usb-rt-passive-observer-v1" and
         value["stage"] == "terminal" and value["accepted"] is True and
         value["terminalReason"] == expected_reason and
         value["protocolPhase"] == "ReadyForHeader" and
         value["opened"] is True and value["claimed"] is True and
         value["released"] is True and value["closed"] is True and
         value["writes"] == 0 and value["retries"] == 0 and
         value["busContentsAltered"] is False,
         "native terminal contract")
    return value


def exact_window(group, name, raw, occurrence=0):
    matches = [window for window in group["windows"] if window["name"] == name]
    need(len(matches) > occurrence, "missing retained window " + name)
    window = matches[occurrence]
    decoded = base64.b64decode(window["rawBase64"], validate=True)
    need(decoded == raw and window["complete"] is True and
         window["count"] == window["expected"] == len(raw) and
         window["sha256"] == digest(raw), "retained bytes " + name)


def input_times(group):
    all_inputs = [row for row in group["transfers"] if row["direction"] == "IN"]
    names = [row["name"] for row in all_inputs]
    need(names in (["M-data", "C-data", "H-data", "L-data", "R-data"],
                   ["R-data", "M-data", "C-data", "H-data", "L-data", "R-data"]),
         "bracketed auxiliary transfer order")
    rows = [row for row in all_inputs if row["name"] in
            ("M-data", "C-data", "H-data", "L-data")]
    previous = 0
    output = {}
    for row in rows:
        need(row["count"] == row["expected"] and row["errno"] == 0 and
             row["beforeUs"] >= previous and row["afterUs"] >= row["beforeUs"],
             "exact monotonic transfer " + row["name"])
        output[row["name"][0]] = [row["beforeUs"], row["afterUs"]]
        previous = row["afterUs"]
    return output


def decode_m(raw):
    return {
        "status_counter": u16(raw, 0x00),
        "aa": u16(raw, 0x0A),
        "ac": u16(raw, 0x0C),
        "alternate_mirror": u16(raw, 0x22),
        "mirror_companion": u16(raw, 0x24),
        "y_scalar": u16(raw, 0x30),
        "rgb_scalar": u16(raw, 0x34),
        "ordinary_scan_argument": raw[0x38],
        "root_anchor": u32(raw, 0x40),
    }


def decode_c(raw):
    return {
        "startup_halfwords": [u16(raw, offset) for offset in (0, 2, 4)],
        "byte_6": raw[6],
        "alternate_selector": raw[7],
        "source_byte_0": raw[8],
        "raw_hex": raw.hex(),
    }


def decode_h(raw):
    return {
        "aggregates_a32": [u32(raw, 0x04 + 4 * index) for index in range(6)],
        "q_states": [u16(raw, 0x1C + 2 * index) for index in range(6)],
        "history": [[u16(raw, 0x28 + 8 * mode + 2 * item)
                     for item in range(4)] for mode in range(6)],
    }


def decode_l(raw):
    return {
        "latest_subtractor": u16(raw, 0x04),
        "mode6_latch": u16(raw, 0x06),
        "shared_nonmode6_latch": u16(raw, 0x08),
    }


def decode_r(raw):
    return {
        "tuple": [u16(raw, offset) for offset in (0x00, 0x0A, 0x0E)],
        "limits": {
            "0x2430": u16(raw, 0x30),
            "0x2432": u16(raw, 0x32),
            "0x2440": u16(raw, 0x40),
            "0x24c0": u16(raw, 0xC0),
            "0x24c4": u16(raw, 0xC4),
        },
    }


def selected_mode(mode):
    if mode["aa"] == 1:
        return 4
    if mode["ac"] == 1:
        return 6
    return 1


def selected_limit(mode, alternate, limits):
    if mode == 1:
        key = "0x24c4" if alternate != 0 else "0x2430"
    elif mode == 2:
        key = "0x2432"
    elif mode == 4:
        key = "0x2440"
    elif mode == 6:
        key = "0x24c4" if alternate != 0 else "0x24c0"
    else:
        key = "0x24c4" if alternate != 0 else "0x2430"
    return {"offset": key, "value": limits[key]}


def main():
    # Pin the selected body and the already-reviewed maps used below. This
    # script does not extend their alias or event-time conclusions.
    pinned(OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin",
           "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    source_reports = {
        G / "rtp-mode-selection-provenance.md":
            "1a2783ebf0b93491caffcbb76bc045a30ad0a6879336202ebad13d90d130f607",
        G / "rtp-score-input-provenance.md":
            "ac06e131d4a062d1d7b8179f3f721bb9337b043913c44f3ccce5941c0672a122",
        G / "rtp-selector-consistency-after-v6.md":
            "670c1177931628957d5121f8562f86b4a3624ece3547e2f40e855178b2fd5c11",
        G / "rtp-post-fault-ordinary-gating.md":
            "2511047f9383db061025ffa033b406bf78edc255f4ffadcf4823616b811d2f5a",
        X / "retained-state-findings.md":
            "ec8cc0ab0906ac34cd84de6a4f3f383febccb3d9c8e19c1ea570594edc540658",
    }
    for path, expected in source_reports.items():
        pinned(path, expected)

    pre_dir = AV / "pre-x"
    post_dir = AV / "post-x"
    pre_native = terminal(pre_dir / "native.stdout.bin",
                          "3075f7d927501fa4bfd0667b6c140af3638ba7d026eb36599ddb47d7c222ab43",
                          "AlreadyFaulted")
    post_native = terminal(post_dir / "native.stdout.bin",
                           "dcf694a97796d9afe306669fdc9c4b62717f7f68de98fb51cfae7160f0d03fb7",
                           "TimeLimit")
    pinned(pre_dir / "result.json",
           "00e978140af8ff4dadc223d420cd3018ca57577cf14229e2175d2704f8a13eec")
    pinned(post_dir / "result.json",
           "122ae75f84e69ee94aac3e2878db36d2fef8eca19c805ed7c7e568439c179485")

    pre_names = {
        "M": ("retained-01-post_fault-cycle001-00-M.bin",
              "c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9"),
        "C": ("retained-01-post_fault-cycle001-01-C.bin",
              "2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a"),
        "H": ("retained-01-post_fault-cycle001-02-H.bin",
              "d94f16ac03ed209ece31c6e35b49d89a81755681fabf296b3bc5a37013c3fe42"),
        "L": ("retained-01-post_fault-cycle001-03-L.bin",
              "0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439"),
        "R": ("retained-01-post_fault-cycle001-04-R.bin",
              "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9"),
    }
    post_names = {
        "M": ("retained-00-last_clean-cycle080-01-M.bin",
              "cdc6fc83a62defbb54a37a7004f6c1a4c6b9de01912785c248c1fb256b31c2e3"),
        "C": ("retained-00-last_clean-cycle080-02-C.bin",
              "c9bc21efabc33dc5c687f230ecf321722552c99518957cc37b833c7aaaf9c2b0"),
        "H": ("retained-00-last_clean-cycle080-03-H.bin",
              "2ea9ab9198d1638007400cd2c3bef1cc745b864b76011a0e1bc52180ac6452d4"),
        "L": ("retained-00-last_clean-cycle080-04-L.bin",
              "07a165885767f11c0687509812d30e7a493185f02e03296e70ee1188f3ccb827"),
        "R": ("retained-00-last_clean-cycle080-05-R.bin",
              "a15bcc5f51c78ccdea8283d0839533c2e5f12c243a8e351032747b729b66b477"),
    }
    pre = {key: pinned(pre_dir / name, sha) for key, (name, sha) in pre_names.items()}
    post = {key: pinned(post_dir / name, sha) for key, (name, sha) in post_names.items()}
    need({key: len(value) for key, value in pre.items()} ==
         {"M": 68, "C": 16, "H": 96, "L": 64, "R": 256}, "pre extents")
    need({key: len(value) for key, value in post.items()} ==
         {"M": 68, "C": 16, "H": 96, "L": 64, "R": 256}, "post extents")

    need([group["role"] for group in pre_native["retained"]] ==
         ["initial-faulted", "post-fault"], "pre roles")
    need(len(post_native["retained"]) == 1 and
         post_native["retained"][0]["role"] == "last-clean" and
         post_native["retained"][0]["cycleIndex"] == 80,
         "post rolling role")
    pre_group = pre_native["retained"][1]
    post_group = post_native["retained"][0]
    for key in ("M", "C", "H", "L", "R"):
        exact_window(pre_group, key, pre[key])
        exact_window(post_group, key, post[key], 1 if key == "R" else 0)
    pre_times = input_times(pre_group)
    post_times = input_times(post_group)

    pre_decoded = {"M": decode_m(pre["M"]), "C": decode_c(pre["C"]),
                   "H": decode_h(pre["H"]), "L": decode_l(pre["L"]),
                   "R": decode_r(pre["R"])}
    post_decoded = {"M": decode_m(post["M"]), "C": decode_c(post["C"]),
                    "H": decode_h(post["H"]), "L": decode_l(post["L"]),
                    "R": decode_r(post["R"])}
    need(pre_decoded["M"]["root_anchor"] ==
         post_decoded["M"]["root_anchor"] == 0x20010000, "same-response root anchors")
    need(pre_decoded["C"]["startup_halfwords"] ==
         post_decoded["C"]["startup_halfwords"] == [0x0870, 0x0780, 0x0B40],
         "candidate context fingerprints")
    need(pre_decoded["M"]["alternate_mirror"] ==
         pre_decoded["C"]["alternate_selector"] == 1 and
         post_decoded["M"]["alternate_mirror"] ==
         post_decoded["C"]["alternate_selector"] == 0,
         "sequential alternate values")
    need(pre_decoded["M"]["aa"] == post_decoded["M"]["aa"] == 0 and
         pre_decoded["M"]["ac"] == post_decoded["M"]["ac"] == 2,
         "mode selectors")
    need(pre_decoded["R"]["limits"] == post_decoded["R"]["limits"] ==
         {"0x2430": 200, "0x2432": 0, "0x2440": 0,
          "0x24c0": 200, "0x24c4": 40}, "candidate limits")
    need(pre_decoded["H"] == {
        "aggregates_a32": [44, 0, 0, 0, 0, 0],
        "q_states": [0, 0, 0, 0, 0, 0],
        "history": [[6, 0, 0, 6], [0, 0, 0, 0], [0, 0, 0, 0],
                    [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    }, "pre score state")
    need(post_decoded["H"] == {
        "aggregates_a32": [0, 0, 0, 0, 0, 0],
        "q_states": [0, 0, 0, 0, 0, 0],
        "history": [[0, 0, 0, 0] for _ in range(6)],
    }, "post score state")
    need(pre_decoded["L"] == {"latest_subtractor": 0, "mode6_latch": 54,
                               "shared_nonmode6_latch": 44} and
         post_decoded["L"] == {"latest_subtractor": 0, "mode6_latch": 48,
                                "shared_nonmode6_latch": 0}, "latch state")
    need(pre_decoded["R"]["tuple"] == [1, 0x1001, 0] and
         post_decoded["R"]["tuple"] == [0, 0, 1], "R bracket states")

    pre_mode = selected_mode(pre_decoded["M"])
    post_mode = selected_mode(post_decoded["M"])
    pre_limit = selected_limit(pre_mode, pre_decoded["C"]["alternate_selector"],
                               pre_decoded["R"]["limits"])
    post_limit = selected_limit(post_mode, post_decoded["C"]["alternate_selector"],
                                post_decoded["R"]["limits"])
    need((pre_mode, post_mode) == (1, 1) and
         pre_limit == {"offset": "0x24c4", "value": 40} and
         post_limit == {"offset": "0x2430", "value": 200},
         "conditional route selection")

    deltas = {key: changed(pre[key], post[key]) for key in ("M", "C", "H", "L")}
    need({key: len(value) for key, value in deltas.items()} ==
         {"M": 15, "C": 1, "H": 3, "L": 2}, "raw delta counts")

    result = {
        "schema": "stock-rt-selector-state-delta-v1",
        "target_operations": 0,
        "samples_sequential_not_atomic": True,
        "pre_role": "post-fault auxiliary set after initial-faulted R",
        "post_role": "last-clean cycle 80; first post-X cycle raw not retained",
        "pre_input_times_us": pre_times,
        "post_input_times_us": post_times,
        "raw_changed_byte_counts": {key: len(value) for key, value in deltas.items()},
        "unknown_m_changed_offsets": [
            "0x12", "0x13", "0x14", "0x15", "0x26", "0x2a",
            "0x32", "0x33", "0x36"
        ],
        "mode_selectors": {
            "pre": {"aa": pre_decoded["M"]["aa"], "ac": pre_decoded["M"]["ac"],
                    "conditional_mode": pre_mode},
            "post": {"aa": post_decoded["M"]["aa"], "ac": post_decoded["M"]["ac"],
                     "conditional_mode": post_mode},
        },
        "alternate_route": {
            "pre_mirror_and_candidate": [pre_decoded["M"]["alternate_mirror"],
                                           pre_decoded["C"]["alternate_selector"]],
            "post_mirror_and_candidate": [post_decoded["M"]["alternate_mirror"],
                                            post_decoded["C"]["alternate_selector"]],
            "pre_selected_limit": pre_limit,
            "post_selected_limit": post_limit,
            "stored_candidate_limits_unchanged": True,
        },
        "ordinary_scan_argument": [pre_decoded["M"]["ordinary_scan_argument"],
                                    post_decoded["M"]["ordinary_scan_argument"]],
        "mode1_state": {
            "aggregate_a32": [pre_decoded["H"]["aggregates_a32"][0],
                              post_decoded["H"]["aggregates_a32"][0]],
            "history": [pre_decoded["H"]["history"][0],
                        post_decoded["H"]["history"][0]],
            "q": [pre_decoded["H"]["q_states"][0],
                  post_decoded["H"]["q_states"][0]],
            "shared_latch": [pre_decoded["L"]["shared_nonmode6_latch"],
                             post_decoded["L"]["shared_nonmode6_latch"]],
        },
        "other_latches": {
            "latest_subtractor": [pre_decoded["L"]["latest_subtractor"],
                                  post_decoded["L"]["latest_subtractor"]],
            "mode6": [pre_decoded["L"]["mode6_latch"],
                      post_decoded["L"]["mode6_latch"]],
        },
        "bounded_conclusion": (
            "aa/ac and all five stored candidate limits are unchanged; the conditional "
            "mode remains 1, while the alternate selector changes 1->0 and therefore "
            "the selected mode-1 source changes 0x24c4=40 -> 0x2430=200. The mode-1 "
            "aggregate/history/shared latch also change 44/[6,0,0,6]/44 -> zeros, and "
            "the ordinary scan argument changes 0->1. This is a combined selector/control "
            "and retained-score-state delta, not an event-time tuple or isolated limit rewrite."
        ),
        "pre_is_actual_onset": False,
        "physical_state_inferred": False,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
