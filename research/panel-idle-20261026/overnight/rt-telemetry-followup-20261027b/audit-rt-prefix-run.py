#!/usr/bin/env python3
"""Offline audit of one fixed RT-prefix read and subsequent status corroboration."""
import base64
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOT = "00000000-0000-4000-8000-000000000000"


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_calls(record):
    for row in record["calls"]:
        need(row["host_timeout"] is False and row["transport_exit"] == 0, "Transport completion")
        need(base64.b64decode(row["transport_stderr"]["data"], validate=True) == b"", "Transport stderr")
        response = json.loads(base64.b64decode(row["transport_stdout"]["data"], validate=True))
        need(response == row["response"], "Decoded transport differs")
        need(response["model"] == "QN77S95FAFXZC" and response["authenticated"] is True, "Model/auth")
        need(response["uid"] == response["euid"] == 0 and response["root_persistence"] == "host-assisted", "Root access")
        need(response["global_system_files_unchanged_at_acquisition"] is True, "Acquisition invariant")
        need(len(response["commands"]) == 1, "Command count")
        command = response["commands"][0]
        need(command["command"] == row["command"] and command["exit_code"] == 0 and command["timed_out"] is False and command["stderr"] == "", "Remote result")


def main():
    directory = HERE / "usb-rt-prefix-read-once"
    build = HERE.parent / "managed-usb-rt-prefix-read-once"
    record_raw = (directory / "record.json").read_bytes()
    record = json.loads(record_raw)
    validate_calls(record)
    manifest_raw = (build / "build-manifest.json").read_bytes()
    need(record["manifest_sha256"] == sha(manifest_raw) == "6e261b3e79d214a5d2aef7eb5fc56be742b77b05df2daf7ad466353df8a8deeb", "Manifest identity")
    manifest = json.loads(manifest_raw)
    for name, row in manifest["files"].items():
        data = (build / name).read_bytes()
        need(len(data) == row["size"] and sha(data) == row["sha256"], "Build file " + name)
    need(record["deployment_script_sha256"] == sha((build / "run-once.py").read_bytes()), "Wrapper identity")
    need(record["root_runner_sha256"] == "7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a", "Root runner")
    need(record["request"] == {"target": "0x101", "address": "0x47012400", "length": 32}, "Fixed RT request")
    active = [row for row in record["calls"] if "ACTIVE_READ_BEGIN" in row["command"]]
    need(len(active) == 1 and active[0]["command"].count(" --execute") == 1, "Exactly one invocation")
    stdout = (directory / "stdout.txt").read_text()
    need(stdout == active[0]["response"]["commands"][0]["stdout"] and sha(stdout.encode()) == record["helper_stdout_sha256"], "Exact stdout")
    lines = stdout.splitlines()
    need(lines[0] == BOOT and json.loads(lines[2]) == {"selfTestsPassed": 26, "targetOperations": 0}, "Boot/tests")
    result = json.loads(lines[4])
    need(result["Stage"] == "complete" and all(result[key] is True for key in ("Opened", "Claimed", "Released", "Closed", "Accepted")), "Complete lifecycle")
    need(result["OutCount"] == 12 and result["InCount"] == 32, "Exact counts")
    need([row["Phase"] for row in result["Steps"]] == ["open", "claim", "out", "in", "release", "close"], "Phase order")
    need([row["Value"] for row in result["Steps"]] == [25, 0, 12, 32, 0, 0], "Phase values")
    need(all(row["Errno"] == 0 and row["Error"] is None for row in result["Steps"]), "No phase errors")
    need("HELPER_EXIT=0" in lines and record["cleanup_stdout"] == "STAGE_ABSENT\n", "Exit/cleanup")
    need(record["calls"][-1]["response"]["commands"][0]["stdout"] == "STAGE_ABSENT\n", "Raw cleanup")
    returned = base64.b64decode(result["DataBase64"], validate=True)
    need(returned == (directory / "returned-prefix.bin").read_bytes() and len(returned) == 32 and sha(returned) == result["DataSha256"], "Returned data")
    profile = HERE.parent / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
    data = profile.read_bytes()
    need(sha(data) == "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "Profile")
    packaged = data[0x183800:0x183820]
    deltas = [(i, a, b) for i, (a, b) in enumerate(zip(packaged, returned)) if a != b]
    need(deltas == [(8, 0, 1), (14, 0, 1)], "Exact default differences")
    need(int.from_bytes(returned[10:12], "little") == 0 and int.from_bytes(returned[16:18], "little") == 4, "RT flag/mode")
    status_raw = (HERE / "rt-prefix-stock-status.json").read_bytes()
    status = json.loads(status_raw)
    validate_calls(status)
    need(status["accepted"] is True and status["read_usable"] is True and status["cleanup_confirmed"] is True, "Status helper accepted/clean")
    need(status["execution"]["boot_id"] == BOOT and status["execution"]["result"]["status_hex"] == "0x00000000", "Status sample")
    log_record = json.loads((HERE / "rt-prefix-status-kernel-log.json").read_text())
    validate_calls(log_record)
    log = (HERE / "rt-prefix-status-kernel-log.txt").read_text()
    need(log == log_record["calls"][0]["response"]["commands"][0]["stdout"], "Log stdout")
    pid = status["execution"]["helper_pid"]
    matches = re.findall(r"\[([0-9.]+)\] \[TCON:QDF\] QDFTcon_GetErrDetStatus\[" + str(pid) + r":TconStatusRead\.\]: ERR DET Status:0x0", log)
    need(len(matches) == 1, "Correlated QDF raw row")
    need(float(lines[-1].split()[0]) < float(matches[0]) <= status["execution"]["execute_uptime"], "Sequential sample times")
    report = {"schema": "rt-prefix-runtime-audit-v1", "record_sha256": sha(record_raw),
              "boot_id": BOOT, "root_calls": len(record["calls"]), "fake_tests": 26,
              "out_count": 12, "in_count": 32, "prefix_hex": returned.hex(),
              "prefix_sha256": sha(returned), "packaged_prefix_sha256": sha(packaged),
              "default_byte_deltas": deltas, "rt_flag_halfword": 0, "mode_halfword": 4,
              "uptime_before": float(lines[1].split()[0]), "uptime_after": float(lines[-1].split()[0]),
              "subsequent_raw_qdf_status": "0x0", "raw_qdf_uptime": float(matches[0]),
              "status_record_sha256": sha(status_raw), "stage_removed": True,
              "physical_state": "unobserved", "causality_or_repair_established": False,
              "image1_alias_or_whole_image_identity_established": False}
    (HERE / "rt-prefix-runtime-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
