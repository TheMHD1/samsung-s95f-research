#!/usr/bin/env python3
"""Reconcile retained transport, build, live outcome, known bytes and cleanup."""
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOT = "00000000-0000-4000-8000-000000000000"
KNOWN = bytes.fromhex("12010002ef020140e8040120500201020301")


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(revision, expected_manifest, test_count):
    suffix = "" if revision == 1 else "-v2"
    root = HERE / ("usb-known-descriptor-read-once" + suffix)
    build = HERE.parent / ("managed-usb-descriptor-read-once" + suffix)
    raw = (root / "record.json").read_bytes()
    record = json.loads(raw)
    manifest_raw = (build / "build-manifest.json").read_bytes()
    need(sha(manifest_raw) == expected_manifest == record["manifest_sha256"], "Manifest identity")
    manifest = json.loads(manifest_raw)
    for name, row in manifest["files"].items():
        content = (build / name).read_bytes()
        need(len(content) == row["size"] and sha(content) == row["sha256"], "Build file " + name)
    need(record["deployment_script_sha256"] == sha((build / "run-once.py").read_bytes()), "Wrapper identity")
    need(record["root_runner_sha256"] == "7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a", "Root runner")
    need(record["request"] == {"target": "0x101", "address": "0x20261200", "length": 18}, "Fixed request")
    active = []
    for call in record["calls"]:
        need(not call["host_timeout"] and call["transport_exit"] == 0, "Transport completion")
        transport = base64.b64decode(call["transport_stdout"]["data"], validate=True)
        need(base64.b64decode(call["transport_stderr"]["data"], validate=True) == b"", "Transport stderr")
        response = json.loads(transport)
        need(response == call["response"], "Stored response differs from transport")
        need(response["authenticated"] is True and response["uid"] == response["euid"] == 0, "Authenticated root")
        need(response["model"] == "QN77S95FAFXZC" and response["root_persistence"] == "host-assisted", "Model/access")
        need(len(response["commands"]) == 1, "Command count")
        command = response["commands"][0]
        need(command["command"] == call["command"], "Command echo")
        need(command["exit_code"] == 0 and command["timed_out"] is False and command["stderr"] == "", "Remote completion")
        if "ACTIVE_READ_BEGIN" in call["command"]:
            active.append(command)
    need(len(active) == 1 and active[0]["command"].count(" --execute") == 1, "One execute invocation")
    stdout = (root / "stdout.txt").read_text()
    need(stdout == active[0]["stdout"] and sha(stdout.encode()) == record["helper_stdout_sha256"], "Helper stdout identity")
    lines = stdout.splitlines()
    need(lines[0] == BOOT and lines[3] == "ACTIVE_READ_BEGIN", "Boot/framing")
    tests = json.loads(lines[2])
    need(tests == {"selfTestsPassed": test_count, "targetOperations": 0}, "Fake tests")
    outcome = json.loads(lines[4])
    need(record["cleanup_stdout"] == "STAGE_ABSENT\n", "Cleanup result")
    need(record["calls"][-1]["response"]["commands"][0]["stdout"] == "STAGE_ABSENT\n", "Cleanup raw response")
    uptime_before = float(lines[1].split()[0])
    uptime_after = float(lines[-1].split()[0])
    need(0 <= uptime_after - uptime_before < 5, "Finite runtime window")
    if revision == 1:
        need(outcome["Stage"] == "preflight" and not outcome["Opened"] and not outcome["Claimed"] and not outcome["Accepted"], "First preflight refusal")
        need(outcome["OutCount"] is None and outcome["InCount"] is None and outcome["DataBase64"] is None, "No first transport")
        need(len(outcome["Steps"]) == 1 and outcome["Steps"][0]["Error"].startswith("EndOfStreamException:"), "First error")
        need("HELPER_EXIT=1" in lines, "First helper exit")
        data = None
    else:
        need(outcome["Stage"] == "complete" and all(outcome[k] is True for k in ("Opened", "Claimed", "Released", "Closed", "Accepted")), "Successful lifecycle")
        need(outcome["OutCount"] == 12 and outcome["InCount"] == 18, "Exact counts")
        need([s["Phase"] for s in outcome["Steps"]] == ["open", "claim", "out", "in", "release", "close"], "Exact phase order")
        need([s["Value"] for s in outcome["Steps"]] == [25, 0, 12, 18, 0, 0], "Successful phase values")
        need(all(s["Errno"] == 0 and s["Error"] is None for s in outcome["Steps"]), "No phase errors")
        data = base64.b64decode(outcome["DataBase64"], validate=True)
        need(data == KNOWN and sha(data) == outcome["DataSha256"], "Exact known descriptor bytes")
        need("HELPER_EXIT=0" in lines, "Second helper exit")
    return {"revision": revision, "record_sha256": sha(raw), "manifest_sha256": expected_manifest,
            "root_calls": len(record["calls"]), "same_boot": BOOT, "fake_tests": test_count,
            "uptime_before": uptime_before, "uptime_after": uptime_after,
            "helper_accepted": outcome["Accepted"], "usb_header_sent": revision == 2,
            "returned_bytes": 0 if data is None else len(data),
            "returned_sha256": None if data is None else sha(data), "stage_removed": True}


def main():
    rows = [run(1, "efde9349a12dfceb0fdee366f8e239684703dec931c8543e16319bc24b59bbf5", 23),
            run(2, "9a9b6d13afe9daf12c42b7f7197f859b37a67b921bb7b11abbe8476ff21e4655", 27)]
    report = {"schema": "known-descriptor-runtime-audit-v1", "runs": rows,
              "claim": "One successful fixed known-descriptor memory read; first attempt stopped before USB open.",
              "not_established": ["whole installed image identity", "RT shared-window USB accessibility", "physical picture state", "recovery or prevention"]}
    (HERE / "known-descriptor-runtime-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
