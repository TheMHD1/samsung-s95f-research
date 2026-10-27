#!/usr/bin/env python3
"""Offline reconciliation of exact builds, uploads, root envelopes and RT samples."""
import base64
import hashlib
import json
from pathlib import Path
import re
import shlex

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
BOOT = "00000000-0000-4000-8000-000000000000"
GC = re.compile(r"\[GC_INFO\] GC_(Start|End) #(\d+): Gen\((\d+)\), Time\((\d+) ms\)(?:, Reason\((\d+)\))?")
RUNS = [
    ("rt-block-read-once", "managed-usb-rt-block-read-once", "ManagedUsbRtBlockReadOnce",
     "e5129d3412bd653d2569a64f4a04df9286479b3799dfff46a7a0591ac2c61cc6", 26, False, 256),
    ("rt-block-sampler-smoke", "managed-usb-rt-block-sampler", "ManagedUsbRtBlockSampler",
     "3ce93e2785b4c62bd97d3a515c5717f4045a6a4a8cb028e90075cde9e9845bf7", 35, True, 256),
    ("emmc-sector-read-once", "managed-usb-emmc-sector-read-once", "ManagedUsbEmmcSectorReadOnce",
     "7c4c6b0d0423a381ce25f05039c7b8388ee1cd7220cd97e8294f3769fff6c1d4", 26, False, 512),
]


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(text):
    def bad(value):
        raise ValueError("Non-JSON constant " + value)
    return json.loads(text, parse_constant=bad)


def root_calls(record):
    uploads = {}
    for row in record["calls"]:
        need(not row["host_timeout"] and row["transport_exit"] == 0, "Transport completion")
        need(base64.b64decode(row["transport_stderr"]["data"], validate=True) == b"", "Transport stderr")
        response = strict_json(base64.b64decode(row["transport_stdout"]["data"], validate=True))
        need(response == row["response"], "Transport response identity")
        need(response["model"] == "QN77S95FAFXZC" and response["authenticated"] is True, "Model/authentication")
        need(response["uid"] == response["euid"] == 0 and response["root_persistence"] == "host-assisted", "Root identity")
        need(response["global_system_files_unchanged_at_acquisition"] is True, "Acquisition invariant")
        need(len(response["commands"]) == 1, "Command count")
        command = response["commands"][0]
        need(command["command"] == row["command"] and command["exit_code"] == 0 and command["timed_out"] is False and command["stderr"] == "", "Remote completion")
        for line in row["command"].splitlines():
            if line.startswith("printf %s "):
                words = shlex.split(line)
                need(len(words) == 5 and words[:2] == ["printf", "%s"] and words[3] == ">>", "Upload framing")
                need(words[4].startswith(record["remote_stage"] + "/") and words[4].endswith(".b64"), "Private upload target")
                uploads.setdefault(Path(words[4]).name[:-4], "")
                uploads[Path(words[4]).name[:-4]] += words[2]
    return uploads


def parse_stdout(stdout, tests):
    lines = stdout.splitlines()
    need(lines[0] == BOOT, "Boot")
    before, after = float(lines[1].split()[0]), float(lines[-1].split()[0])
    need(after >= before, "Outer monotonic uptime")
    records, diagnostics = [], []
    active, exit_code = False, None
    for line in lines[2:-1]:
        if line == "ACTIVE_READ_BEGIN":
            need(not active, "One active marker")
            active = True
        elif line.startswith("HELPER_EXIT="):
            need(active and exit_code is None, "Exit framing")
            exit_code = int(line.split("=", 1)[1])
        elif line.startswith("{"):
            value = strict_json(line)
            need(isinstance(value, dict), "Structured helper record")
            if not active:
                need(value.get("selfTestsPassed") == tests and value.get("targetOperations") == 0, "Fake test record")
            else:
                need(exit_code is None, "Structured record after exit")
            records.append((active, value))
        else:
            need(GC.fullmatch(line) is not None, "Unclassified helper output: " + line)
            diagnostics.append(line)
    need(active and exit_code == 0, "Helper completion")
    need(len([r for active, r in records if not active]) == 1, "One fake test result")
    need(sum("GC_Start" in x for x in diagnostics) == sum("GC_End" in x for x in diagnostics), "GC record pairs")
    return before, after, [r for active, r in records if active], diagnostics


def transport(outcome, length):
    need(outcome["Stage"] == "complete" and all(outcome[key] is True for key in ("Opened", "Claimed", "Released", "Closed", "Accepted")), "Accepted lifecycle")
    need(outcome["OutCount"] == 12 and outcome["InCount"] == length, "Exact transfer counts")
    phases = outcome["Steps"]
    need([r["Phase"] for r in phases] == ["open", "claim", "out", "in", "release", "close"], "Phase order")
    need(phases[0]["Value"] >= 0 and [r["Value"] for r in phases[1:]] == [0, 12, length, 0, 0], "Phase values")
    need(all(r["Errno"] == 0 and r["Error"] is None for r in phases), "Phase errors")
    payload = base64.b64decode(outcome["DataBase64"], validate=True)
    need(len(payload) == length and sha(payload) == outcome["DataSha256"], "Payload extent/hash")
    return payload


def audit(item, profile):
    run_name, build_name, assembly, manifest_sha, tests, series, length = item
    storage = run_name == "emmc-sector-read-once"
    packaged = profile[:512] if storage else profile[0x183800:0x183900]
    directory, build = HERE / run_name, BASE / build_name
    raw = (directory / "record.json").read_bytes()
    record = strict_json(raw)
    uploaded = root_calls(record)
    manifest_raw = (build / "build-manifest.json").read_bytes()
    need(sha(manifest_raw) == record["manifest_sha256"] == manifest_sha, "Manifest identity")
    manifest = strict_json(manifest_raw)
    required = {"Program.cs", assembly + ".csproj", *("bin/Release/net6.0/" + assembly + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json"))}
    need(set(manifest["files"]) == required, "Build inventory")
    need(set(uploaded) == {assembly + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json")}, "Upload inventory")
    for name, row in manifest["files"].items():
        data = (build / name).read_bytes()
        need(len(data) == row["size"] and sha(data) == row["sha256"], "Build row " + name)
        if name.startswith("bin/"):
            need(base64.b64decode(uploaded[Path(name).name], validate=True) == data, "Exact uploaded payload")
    need(record["deployment_script_sha256"] == sha((build / "run-once.py").read_bytes()), "Wrapper identity")
    need(record["root_runner_sha256"] == "7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a", "Root runner")
    expected_request = {"target": "0x203" if storage else "0x101",
                        "address": "0x0" if storage else "0x47012400", "length": length}
    if series:
        expected_request.update(max_samples=20, period_ms=250, latest_start_ms=5500)
    need(record["request"] == expected_request, "Fixed request scope")
    active_calls = [c for c in record["calls"] if "ACTIVE_READ_BEGIN" in c["command"]]
    need(len(active_calls) == 1 and active_calls[0]["command"].count(" --execute") == 1, "One helper invocation")
    stdout = (directory / "stdout.txt").read_text()
    need(stdout == active_calls[0]["response"]["commands"][0]["stdout"] and sha(stdout.encode()) == record["helper_stdout_sha256"], "Exact stdout")
    before, after, records, gc = parse_stdout(stdout, tests)
    need(record["cleanup_stdout"] == "STAGE_ABSENT\n" and record["calls"][-1]["response"]["commands"][0]["stdout"] == "STAGE_ABSENT\n", "Raw cleanup")
    result = {"run": run_name, "record_sha256": sha(raw), "manifest_sha256": manifest_sha,
              "root_calls": len(record["calls"]), "stdout_bytes": len(stdout.encode()),
              "uptime_before": before, "uptime_after": after, "gc_rows": len(gc),
              "private_stage_removed": True, "physical_state": "unobserved", "repair_established": False}
    if not series:
        need(len(records) == 1, "One structured read outcome")
        payload = transport(records[0], length)
        need(payload == (directory / ("returned-sector.bin" if storage else "returned-block.bin")).read_bytes(), "Extracted payload")
        result.update(payload_sha256=sha(payload), default_byte_deltas=[(i, a, b) for i, (a, b) in enumerate(zip(packaged, payload)) if a != b])
        if storage:
            result.update(package_sector_equal=payload == packaged,
                          returned_build_tag=payload[0x40:0x60].split(b"\0", 1)[0].decode("ascii"),
                          packaged_build_tag=packaged[0x40:0x60].split(b"\0", 1)[0].decode("ascii"),
                          returned_build_time=payload[0x80:0xa0].split(b"\0", 1)[0].decode("ascii"),
                          packaged_build_time=packaged[0x80:0xa0].split(b"\0", 1)[0].decode("ascii"),
                          storage_success_or_freshness_proved=False, current_running_image_identified=False)
        else:
            result.update(fields={hex(i): int.from_bytes(payload[i:i+2], "little") for i in (0xa, 0x10, 0x36, 0x50, 0x52, 0x54, 0x66, 0x84, 0x9e, 0xaa, 0xac, 0xb4)})
    else:
        need(records[0].get("type") == "rt_block_start" and records[-1].get("Type") == "rt_block_summary", "Series frame")
        need(records[0] == {"type": "rt_block_start", "maxSamples": 20, "periodMs": 250, "latestStartMs": 5500, "inputLength": 256, "address": "0x47012400", "headerHex": "010100000024014700010000"}, "Series start contract")
        samples, summary = records[1:-1], records[-1]
        need(len(samples) == 20 and summary["Reason"] == "sample_limit" and summary["Accepted"] is True and summary["SamplesCompleted"] == summary["SamplesTransportAccepted"] == 20 and summary["Error"] is None, "Smoke complete")
        starts, durations, hashes, origins, offsets = [], [], [], set(), []
        for index, sample in enumerate(samples, 1):
            need(sample["Type"] == "rt_block_sample" and sample["Index"] == index, "Sample indices")
            payload = transport(sample["Transport"], length)
            need(sample["RtFlagHalfword"] == int.from_bytes(payload[10:12], "little") == 0, "Recorded clear RT flag")
            start, end = sample["StartMilliseconds"], sample["EndMilliseconds"]
            need(end >= start and 0 <= sample["StartElapsedMs"] <= 5500, "Finite monotonic sample")
            origins.add(start - sample["StartElapsedMs"])
            up1, up2 = float(sample["UptimeBefore"].split()[0]), float(sample["UptimeAfter"].split()[0])
            need(before <= up1 <= up2 <= after, "Outer/sample uptime enclosure")
            offsets.extend((up1 * 1000 - start, up2 * 1000 - end))
            starts.append(start)
            durations.append(end - start)
            hashes.append(sha(payload))
        need(len(origins) == 1, "Consistent monotonic origin")
        gaps = [b - a for a, b in zip(starts, starts[1:])]
        need(all(g >= 250 for g in gaps), "No catch-up bursts")
        need(summary["ElapsedMs"] >= samples[-1]["EndMilliseconds"] - next(iter(origins)), "Summary encloses final sample")
        need(len(set(hashes)) == 1 and hashes[0] == sha((HERE / "rt-block-read-once/returned-block.bin").read_bytes()), "Observed stable block")
        result.update(samples=20, summary=summary, start_gaps_ms=gaps, sample_durations_ms=durations,
                      payload_sha256=hashes[0], all_rt_flags_zero=True, uptime_minus_stopwatch_ms_range=[round(min(offsets), 3), round(max(offsets), 3)])
    return result


def main():
    profile = BASE / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
    raw = profile.read_bytes()
    need(sha(raw) == "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "Selected package")
    report = {"schema": "rt-block-onset-runtime-audit-v1", "boot_id": BOOT,
              "runs": [audit(item, raw) for item in RUNS],
              "physical_state": "unobserved", "causality_or_permanent_fix_established": False}
    (HERE / "runtime-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
