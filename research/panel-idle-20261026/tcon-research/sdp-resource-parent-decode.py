#!/usr/bin/env python3
"""Offline verifier for one fixed-path, passive DT-parent metadata capture."""
from pathlib import Path
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import struct

HERE = Path(__file__).resolve().parent
CAPTURE = HERE.parent / "overnight/sdp-resource-parent-metadata-20261026"
INPUTS = {
    "client-result.json": "1fb50d5ca430ce39c1ca8c559823b3790e73b51c0af354e2fc47ecd61e17097a",
    "client-stderr.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "client-stdout.json": "765defd008f130faf522ebeb657226e85f309c11ae1aaab4f89827b816ff241a",
    "intent.json": "26e68d8ff8311d3fff344aa0c4fe7cc6e63176990703a374df540937ee85ef17",
    "remote-stderr.txt": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "remote-stdout.txt": "ae210a90aa935e9f44619e319daae5db430241471d5ff2db4075890cf8370a70",
}
SELECTOR_SOURCE = HERE / "frc-extension-and-sdp-register-path.md"
SELECTOR_SOURCE_SHA256 = "eb20c468e9b313b1b7c5b308f984eca2c6f259c1fff57263f9d86f74f0c37a4a"
SELECTOR = 0x42B48
NAMES = (
    "#address-cells", "#size-cells", "ranges", "soc/#address-cells",
    "soc/#size-cells", "soc/ranges", "soc/compatible", "soc/name",
    "soc/sdp_frc/reg", "soc/sdp_frc/reg-names", "soc/sdp_frc/compatible",
    "soc/sdp_frc/status",
)
BOOT_ID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
MAX_SECONDS = 25.0


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_utc(value, label):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not ISO-8601") from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed),
            f"{label} is not UTC")
    return parsed.timestamp()


def finite_ordered(start, end, label):
    require(math.isfinite(start) and math.isfinite(end), f"{label} is non-finite")
    require(start <= end, f"{label} is reversed")
    require(end - start <= MAX_SECONDS, f"{label} exceeds {MAX_SECONDS:g}s")


def normalize_raw(raw):
    # The remote formatter emitted exactly 40 literal slash-n separators.
    require(raw.count("\\n") == 40, "unexpected literal slash-n framing count")
    require("\\r" not in raw, "unexpected escaped carriage return")
    return raw.replace("\\n", "\n")


def take(lines, cursor, expected):
    require(cursor < len(lines) and lines[cursor] == expected,
            f"expected {expected!r} at normalized line {cursor + 1}")
    return cursor + 1


def parse_properties(lines, cursor):
    props = {}
    for name in NAMES:
        cursor = take(lines, cursor, f"@@ PROPERTY {name}")
        require(cursor < len(lines), f"missing body for {name}")
        marker = lines[cursor]
        cursor += 1
        if marker == "ABSENT":
            cursor = take(lines, cursor, "@@ END_PROPERTY")
            props[name] = {"absent": True}
            continue
        require(marker.startswith("BYTES "), f"unexpected property marker for {name}")
        count = marker.removeprefix("BYTES ")
        require(re.fullmatch(r"[0-9]+", count) is not None, f"invalid byte count for {name}")
        size = int(count)
        require(size <= 4096, f"oversized property {name}")
        require(cursor < len(lines), f"missing digest/path for {name}")
        pair = lines[cursor].split("  ", 1)
        cursor += 1
        require(len(pair) == 2 and re.fullmatch(r"[0-9a-f]{64}", pair[0]) is not None,
                f"invalid digest/path for {name}")
        digest, path = pair
        require(path == "/sys/firmware/devicetree/base/" + name, f"unexpected source path for {name}")
        encoded = []
        while cursor < len(lines) and lines[cursor] != "@@ END_PROPERTY":
            require(re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", lines[cursor]) is not None,
                    f"invalid base64 line for {name}")
            encoded.append(lines[cursor])
            cursor += 1
        require(encoded, f"missing base64 payload for {name}")
        cursor = take(lines, cursor, "@@ END_PROPERTY")
        try:
            value = base64.b64decode("".join(encoded), validate=True)
        except ValueError as exc:
            raise ValueError(f"invalid base64 payload for {name}") from exc
        require(len(value) == size, f"length mismatch for {name}")
        require(hashlib.sha256(value).hexdigest() == digest, f"digest mismatch for {name}")
        props[name] = {
            "bytes": size, "sha256": digest, "hex": value.hex(),
            "be32": list(struct.unpack(">" + str(size // 4) + "I", value))
            if size and size % 4 == 0 else None,
        }
    return props, cursor


def decode(raw):
    lines = normalize_raw(raw).splitlines()
    cursor = take(lines, 0, "@@ BOOT_START")
    require(cursor < len(lines) and BOOT_ID.fullmatch(lines[cursor]) is not None, "invalid boot start")
    boot = lines[cursor]
    cursor = take(lines, cursor + 1, "@@ TIME_START")
    require(cursor + 1 < len(lines) and re.fullmatch(r"[0-9]+", lines[cursor]) is not None,
            "invalid wall-clock start")
    wall_start = float(lines[cursor])
    start_parts = lines[cursor + 1].split()
    require(len(start_parts) == 2, "invalid uptime start")
    uptime_start, idle_start = map(float, start_parts)
    props, cursor = parse_properties(lines, cursor + 2)
    cursor = take(lines, cursor, "@@ BOOT_END")
    require(cursor < len(lines) and lines[cursor] == boot, "boot changed during capture")
    cursor = take(lines, cursor + 1, "@@ TIME_END")
    require(cursor + 1 < len(lines) and re.fullmatch(r"[0-9]+", lines[cursor]) is not None,
            "invalid wall-clock end")
    wall_end = float(lines[cursor])
    end_parts = lines[cursor + 1].split()
    require(len(end_parts) == 2, "invalid uptime end")
    uptime_end, idle_end = map(float, end_parts)
    require(cursor + 2 == len(lines), "trailing or interstitial normalized framing")
    for label, start, end in (("wall clock", wall_start, wall_end),
                              ("uptime", uptime_start, uptime_end),
                              ("idle uptime", idle_start, idle_end)):
        finite_ordered(start, end, label)
    require(props["#address-cells"]["be32"] == [2], "unexpected root address-cells")
    require(props["#size-cells"]["be32"] == [2], "unexpected root size-cells")
    require(props["ranges"] == {"absent": True}, "root ranges must be absent")
    require(props["soc/#address-cells"]["be32"] == [1], "unexpected soc address-cells")
    require(props["soc/#size-cells"]["be32"] == [1], "unexpected soc size-cells")
    require(props["soc/compatible"]["hex"] == b"simple-bus\0".hex(), "unexpected soc compatible")
    require(props["soc/sdp_frc/reg-names"]["hex"] == b"frc-reg\0".hex(), "unexpected reg-names")
    require(props["soc/sdp_frc/compatible"]["hex"] == b"samsung,sdp-frc\0".hex(), "unexpected frc compatible")
    child, parent_high, parent_low, extent = props["soc/ranges"]["be32"]
    parent = (parent_high << 32) | parent_low
    require((child, parent, extent) == (0, 0, 0xFFFFFFFF), "unexpected soc ranges")
    start, size = props["soc/sdp_frc/reg"]["be32"]
    require((start, size) == (0xB90000, 0x5F000), "unexpected frc-reg tuple")
    require(child <= start and start + size <= child + extent, "reg outside soc ranges")
    translated = parent + start - child
    require(SELECTOR + 4 <= size, "external selector is outside captured reg size")
    return {
        "boot_id": boot,
        "capture_seconds": {"wall": wall_end - wall_start, "uptime": uptime_end - uptime_start,
                            "idle_uptime": idle_end - idle_start, "bound": MAX_SECONDS},
        "uptime_start": uptime_start, "uptime_end": uptime_end,
        "sequential_nonatomic": True, "physical_picture": "unobserved", "properties": props,
        "framing": "Exact ordered BOOT/TIME/property framing after normalizing exactly 40 literal slash-n separators; raw response retained and property bytes length/SHA256 checked.",
        "translated_resource": {"child_address_cells": 1, "parent_address_cells": 2, "size_cells": 1,
            "ranges_words": [child, parent_high, parent_low, extent], "reg_start": start, "reg_size": size,
            "translated_start": translated, "translated_end_inclusive": translated + size - 1,
            "scope": "Captured DT translation arithmetic; no platform-resource struct, ioremap pointer, register access or physical result observed."},
        "selector_external_prior_re": {"selector": SELECTOR, "source": SELECTOR_SOURCE.name,
            "source_sha256": SELECTOR_SOURCE_SHA256, "selector_translated_address": translated + SELECTOR,
            "scope": "Selector is an external prior-static-RE input, not a value read from DT."},
    }


def build_report(capture=CAPTURE):
    for name, expected in INPUTS.items():
        require(sha256_file(capture / name) == expected, f"input hash mismatch: {name}")
    require(sha256_file(SELECTOR_SOURCE) == SELECTOR_SOURCE_SHA256, "selector-source hash mismatch")
    response = json.loads((capture / "client-stdout.json").read_text())
    intent = json.loads((capture / "intent.json").read_text())
    result = json.loads((capture / "client-result.json").read_text())
    remote_stdout = (capture / "remote-stdout.txt").read_text()
    client_stderr = (capture / "client-stderr.txt").read_text()
    remote_stderr = (capture / "remote-stderr.txt").read_text()
    require(response["authenticated"] is True and response["uid"] == response["euid"] == 0,
            "authentication/UID provenance mismatch")
    require(response["root_persistence"] == "host-assisted", "unexpected root persistence")
    require(response["global_system_files_unchanged_at_acquisition"] is True,
            "global-system-files provenance mismatch")
    require(response["model"] == "QN77S95FAFXZC" and response["host"] == "198.51.100.20",
            "target provenance mismatch")
    require(isinstance(response["commands"], list) and len(response["commands"]) == 1,
            "unexpected command count")
    command = response["commands"][0]
    require(command["exit_code"] == result["returncode"] == 0 and command["timed_out"] is False,
            "client/remote return provenance mismatch")
    require(command["stderr"] == client_stderr == remote_stderr == "", "stderr sidecar mismatch")
    require(command["stdout"] == remote_stdout, "remote stdout sidecar mismatch")
    require(command["command"] == intent["command"], "intent command mismatch")
    require(hashlib.sha256(intent["command"].encode()).hexdigest() == intent["command_sha256"],
            "intent command hash mismatch")
    intent_started = parse_utc(intent["recorded_utc"], "intent timestamp")
    client_finished = parse_utc(result["finished_utc"], "client finish timestamp")
    finite_ordered(intent_started, client_finished, "client timing")
    report = decode(remote_stdout)
    report["capture_provenance"] = {"authenticated": True, "uid": 0, "euid": 0,
        "root_persistence": "host-assisted", "global_system_files_unchanged_at_acquisition": True,
        "client_elapsed_seconds": client_finished - intent_started, "input_sha256": INPUTS}
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()
    report = build_report()
    path = CAPTURE / "decoded-reviewed.json"
    if args.write_result:
        with path.open("x") as out:
            json.dump(report, out, indent=2)
            out.write("\n")
    else:
        require(path.is_file(), "reviewed result is absent; use --write-result once")
        require(json.loads(path.read_text()) == report, "reviewed result mismatch")
    print("PASS: hash-pinned client/remote sidecars; exact ordered framing; same boot and bounded clocks.")
    print("DT translation: 0x00b90000..0x00beefff; selector is separately pinned prior-static-RE input.")
    print("No memory/register read or write and no physical panel result established.")


if __name__ == "__main__":
    main()
