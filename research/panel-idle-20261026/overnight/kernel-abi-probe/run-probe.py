#!/usr/bin/env python3
"""Stage one tiny invalid-syscall probe in a private TV /tmp dir; clean up.

Dry-run by default. No BPF program/map or perf event/attachment is requested.
This does write/remove the temporary helper; it is not a file-read-only probe.
"""
from pathlib import Path
import argparse
import base64
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ACCESS = BASE.parent / "root-access/s95f-access.py"


def command(binary, digest):
    encoded = base64.b64encode(binary).decode("ascii")
    return f'''set -eu
tv_probe_dir=$(mktemp -d /tmp/researcher-kernel-abi-XXXXXX)
cleanup() {{
 if test -d "$tv_probe_dir"; then
  rm -f "$tv_probe_dir/probe" "$tv_probe_dir/result"
  rmdir "$tv_probe_dir"
 fi
}}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
echo PROBE_BEGIN
date -u
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
echo "$tv_probe_dir"
grep -E '^(Uid|Gid|CapEff|NoNewPrivs|Seccomp):' /proc/self/status
printf %s '{encoded}' | base64 -d > "$tv_probe_dir/probe"
test "$(sha256sum "$tv_probe_dir/probe" | awk '{{print $1}}')" = {digest}
chmod 700 "$tv_probe_dir/probe"
probe_status=0
"$tv_probe_dir/probe" > "$tv_probe_dir/result" || probe_status=$?
echo "PROBE_EXIT=$probe_status"
echo RESULT_SIZE
wc -c "$tv_probe_dir/result"
echo RESULT_BASE64
base64 "$tv_probe_dir/result"
echo RESULT_SHA256
sha256sum "$tv_probe_dir/result"
echo RESULT_END
cat /proc/uptime
cleanup
trap - EXIT HUP INT TERM
test ! -e "$tv_probe_dir"
echo PRIVATE_TEMP_DIRECTORY_REMOVED
'''


def decode(text):
    if text.count("PROBE_EXIT=0\n") != 1:
        raise ValueError("Helper execution failed; interface presence unclassified")
    size = int(text.split("RESULT_SIZE\n", 1)[1].split()[0])
    encoded = text.split("RESULT_BASE64\n", 1)[1].split("RESULT_SHA256\n", 1)[0]
    raw = base64.b64decode("".join(encoded.split()), validate=True)
    digest = text.split("RESULT_SHA256\n", 1)[1].split()[0]
    if len(raw) != size or size != 32 or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Incomplete or inconsistent probe transfer")
    if raw[:8] != b"QDKABI1\n":
        raise ValueError("Wrong helper output format")
    pid, bpf, perf = (int.from_bytes(raw[i:i + 8], "little", signed=True) for i in [8, 16, 24])
    if not 0 < pid < 2**31 or not (-4095 <= bpf < 0 and -4095 <= perf < 0):
        raise ValueError("Unexpected syscall return; preserve raw evidence")
    if not text.rstrip().endswith("PRIVATE_TEMP_DIRECTORY_REMOVED"):
        raise ValueError("Private temporary-directory cleanup not confirmed")
    return {"native_getpid": pid, "invalid_bpf_return": bpf,
            "null_perf_event_return": perf,
            "scope": "Availability to this native-AArch64 process only; not configuration, helper/LSM policy or kernel-memory access proof"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((HERE / "build-manifest.json").read_text())
    binary = (HERE / "probe").read_bytes()
    digest = hashlib.sha256(binary).hexdigest()
    if digest != manifest["binary_sha256"]:
        raise ValueError("Unreviewed probe binary")
    body = command(binary, digest)
    if len(body.encode()) > 7500:
        raise ValueError("Root command exceeds bounded size")
    if not args.run:
        print(body)
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = HERE / ("result-" + stamp + ".json")
    record = {"command": body, "binary_sha256": digest, "physical_state": "unobserved",
              "accepted": False, "temporary_helper_staging": True}
    with destination.open("x") as handle:
        handle.write(json.dumps(record, indent=2) + "\n")
    try:
        proc = subprocess.run(["python3", str(ACCESS), "root", "--persistent-only", "--timeout", "25",
                               "--command", body], capture_output=True, text=True, timeout=55)
        record.update({"transport_exit": proc.returncode, "transport_stderr": proc.stderr})
        try:
            response = json.loads(proc.stdout)
        except ValueError:
            record["unparsed_stdout"] = proc.stdout
            raise
        record["response"] = response
        if proc.returncode or response.get("model") != "QN77S95FAFXZC" or not response.get("authenticated"):
            raise ValueError("Unexpected root transport/model")
        if response.get("uid") != 0 or response.get("euid") != 0 or response.get("root_persistence") != "host-assisted":
            raise ValueError("Unexpected access identity/path")
        if response.get("global_system_files_unchanged_at_acquisition") is not True:
            raise ValueError("Controller source-system invariant failed")
        item = response["commands"][0]
        if item["exit_code"] or item["timed_out"] or item["stderr"]:
            raise ValueError("Remote probe failed; raw outcome retained")
        record["decoded"] = decode(item["stdout"])
        record["accepted"] = True
    except Exception as error:
        record["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        destination.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"path": str(destination), "accepted": True, "decoded": record["decoded"]}))


if __name__ == "__main__":
    main()
