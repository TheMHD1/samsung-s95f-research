#!/usr/bin/env python3
"""Prepare one reviewed managed TCON status query; dry by default.

Live mode requires both --run and --reviewed. It stages a hash-pinned portable
assembly, runs it once through the installed ARM32 CLR, retains every root
response, and removes only its private files. A changed sentinel proves only
that a kernel callback wrote output, not a controller transaction or fault.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ACCESS = BASE.parent / "root-access/s95f-access.py"
MANIFEST = HERE / "build-manifest.json"
ABI_REPORT = BASE / "tcon-research/qd-error-status-read-abi.md"
ABI_REPRODUCER = BASE / "tcon-research/qd-error-status-read-abi-reproduce.py"
MODEL = "QN77S95FAFXZC"
ACCESS_SHA256 = "3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5"
ABI_REPORT_SHA256 = "3812ca30cd846e0aee4e85da0716577c781939972d1836eeca41624b2ef0e3d1"
ABI_REPRODUCER_SHA256 = "ce08ad96c1e7908274c1b82b8ebbe199783dace74d77fbcc19fb261a3e32270e"
CLR = "/usr/share/dotnet/shared/Microsoft.NETCore.App/6.0.9"
REMOTE_STOCK = {
    "/usr/bin/dotnet": (None, "e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310"),
    CLR + "/libcoreclr.so": (None, "5e5b5f160204058284d7fcced47fc57e65111e8203b53be5104350a63efd46ff"),
    CLR + "/System.Private.CoreLib.dll": (None, "5cfe69fbb72ba75a78b1b993c46a0d7983b2674d0affcee161ecdf4b08fb17f8"),
    "/lib/modules/5.4.261/kernel/tztv_frc_tcon.ko": (254406, "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd"),
    "/lib/modules/5.4.261/kernel/tztv_frc_tcon_api.ko": (317998, "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6"),
    "/lib/modules/5.4.261/kernel/qdf_tcon.ko": (403294, "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"),
}
DEVICE = "/dev/tztv_tcon"
PREFIX = "/tmp/researcher-tcon-"
REMOTE_NAMES = ("TconStatusRead.deps.json", "TconStatusRead.dll",
                "TconStatusRead.runtimeconfig.json")
OUTPUT_NAMES = ("managed.stdout", "managed.stderr", "helper.ready", "helper.go")
MAX_COMMAND = 8192
MAX_RESPONSE = 65536
SENTINEL = "a55a5aa5"


class ContractError(ValueError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise ContractError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def retained(value: object) -> dict[str, object]:
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode()}
    return {"encoding": "text", "data": "" if value is None else str(value)}


def save(path: Path, record: dict[str, object]) -> None:
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def contract() -> tuple[dict[str, object], dict[str, bytes]]:
    require(file_digest(ACCESS) == ACCESS_SHA256, "Root client identity mismatch")
    require(file_digest(ABI_REPORT) == ABI_REPORT_SHA256, "ABI report identity mismatch")
    require(file_digest(ABI_REPRODUCER) == ABI_REPRODUCER_SHA256,
            "ABI reproducer identity mismatch")
    manifest = json.loads(MANIFEST.read_text())
    require(manifest.get("schema") == "managed-tcon-status-read-build-v1",
            "Unexpected manifest schema")
    files = manifest.get("files")
    require(isinstance(files, dict), "Malformed manifest")
    required = {"Program.cs", "TconStatusRead.csproj", "run-status-read.py",
                *("bin/Release/net6.0/" + name for name in REMOTE_NAMES)}
    require(set(files) == required, "Unexpected manifest inventory")
    staged: dict[str, bytes] = {}
    for name, expected in files.items():
        require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
                "Malformed manifest digest")
        data = (HERE / name).read_bytes()
        require(digest(data) == expected, "Build/source mismatch: " + name)
        if name.startswith("bin/"):
            staged[Path(name).name] = data
    require(set(staged) == set(REMOTE_NAMES), "Unexpected staged inventory")
    return manifest, staged


def stock_checks() -> str:
    lines = ["ck() {", "  test -f \"$1\"", "  test ! -L \"$1\"",
             "  test \"$2\" = - || test \"$(wc -c < \"$1\")\" = \"$2\"",
             "  test \"$(sha256sum \"$1\" | cut -d ' ' -f1)\" = \"$3\"", "}"]
    for path, (size, sha) in REMOTE_STOCK.items():
        lines.append(f"ck {path} {'-' if size is None else size} {sha}")
    return "\n".join(lines)


def validate_response(response: object, command: str) -> str:
    require(isinstance(response, dict), "Response is not an object")
    require(response.get("model") == MODEL and response.get("authenticated") is True,
            "Controller/model identity mismatch")
    require(response.get("uid") == response.get("euid") == 0, "Root UID mismatch")
    require(response.get("root_persistence") == "host-assisted", "Nonpersistent root")
    require(response.get("global_system_files_unchanged_at_acquisition") is True,
            "System-file invariant failed")
    items = response.get("commands")
    require(isinstance(items, list) and len(items) == 1, "Unexpected command count")
    item = items[0]
    require(isinstance(item, dict) and item.get("command") == command, "Command echo mismatch")
    require(item.get("exit_code") == 0 and item.get("timed_out") is False,
            "Remote command failed")
    require(item.get("stderr") == "", "Remote command stderr")
    require(isinstance(item.get("stdout"), str), "Remote stdout is not text")
    return item["stdout"]


def root(command: str, record: dict[str, object], output: Path) -> str:
    size = len(command.encode())
    require(0 < size <= MAX_COMMAND, "Root command size")
    argv = ["python3", str(ACCESS), "root", "--persistent-only", "--timeout", "25",
            "--command", command]
    item: dict[str, object] = {"command": command, "command_bytes": size,
                              "started_utc": now()}
    calls = record.setdefault("calls", [])
    require(isinstance(calls, list), "Internal call record")
    calls.append(item)
    save(output, record)
    try:
        process = subprocess.run(argv, capture_output=True, timeout=55)
    except subprocess.TimeoutExpired as exc:
        item.update(host_timeout=True, timeout_seconds=exc.timeout,
                    partial_stdout=retained(exc.stdout), partial_stderr=retained(exc.stderr),
                    finished_utc=now())
        save(output, record)
        raise
    item.update(host_timeout=False, transport_exit=process.returncode,
                transport_stdout=retained(process.stdout), transport_stderr=retained(process.stderr),
                finished_utc=now())
    save(output, record)
    require(len(process.stdout) + len(process.stderr) <= MAX_RESPONSE, "Response over 64 KiB")
    require(process.returncode == 0 and process.stderr == b"", "Root client failed")
    try:
        response = json.loads(process.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("Root response is not strict UTF-8 JSON") from exc
    item["response"] = response
    save(output, record)
    return validate_response(response, command)


def dir_guard(path: str) -> str:
    return (f"test ! -L {path}\n" +
            f'test "$(stat -c "%u:%g:%a:%F" {path})" = "0:0:700:directory"')


def file_guard(path: str, size: int | None = None) -> str:
    out = [f"test -f {path}", f"test ! -L {path}",
           f'test "$(stat -c "%u:%g:%a" {path})" = "0:0:600"']
    if size is not None:
        out.append(f'test "$(wc -c < {path})" = {size}')
    return "\n".join(out)


def preflight() -> str:
    return f'''set -eu
umask 077
{stock_checks()}
test -c {DEVICE}
boot=$(cat /proc/sys/kernel/random/boot_id)
case "$boot" in ????????-????-????-????-????????????) ;; *) exit 80;; esac
echo "PREFLIGHT_BOOT=$boot"
echo "PREFLIGHT_UTC=$(date -u +%s)"
echo "PREFLIGHT_UPTIME=$(cut -d ' ' -f1 /proc/uptime)"
echo PREFLIGHT_IDENTITY_MATCH
'''


def create(private: str, boot: str) -> str:
    return f'''set -eu
umask 077
test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}
test ! -e {private}
test ! -L {private}
mkdir -m 700 {private}
{dir_guard(private)}
echo PRIVATE_CREATED
'''


def stage(private: str, boot: str, files: dict[str, bytes]) -> list[str]:
    out = []
    for name in REMOTE_NAMES:
        data = files[name]
        target = private + "/" + name
        first = True
        for offset in range(0, len(data), 3072):
            raw = data[offset:offset + 3072]
            chunk = base64.b64encode(raw).decode()
            initialize = f": > {target}\nchmod 600 {target}\n" if first else ""
            out.append(f'''set -eu
umask 077
test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}
{dir_guard(private)}
{initialize}printf %s '{chunk}' | base64 -d >> {target}
{file_guard(target, offset + len(raw))}
echo STAGE_CHUNK_COMPLETE
''')
            first = False
    return out


def execute(private: str, boot: str, files: dict[str, bytes]) -> str:
    checks = []
    for name in REMOTE_NAMES:
        target = private + "/" + name
        checks += [file_guard(target, len(files[name])),
                   f'test "$(sha256sum {target} | cut -d " " -f1)" = {digest(files[name])}']
    integrity = "\n".join(checks)
    stdout = private + "/managed.stdout"
    stderr = private + "/managed.stderr"
    ready = private + "/helper.ready"
    gate = private + "/helper.go"
    dll = private + "/TconStatusRead.dll"
    return f'''set -eu
umask 077
test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}
{stock_checks()}
{dir_guard(private)}
{integrity}
: > {stdout}
: > {stderr}
chmod 600 {stdout} {stderr}
pstart() {{
  test -r "/proc/$1/stat" || return 1
  x=$(cat "/proc/$1/stat") || return 1
  x=${{x##*) }}
  set -- $x
  test "$#" -ge 20 || return 1
  echo "${{20}}"
}}
guard() {{
  test "$1" -gt 1 || return 1
  test "$(pstart "$1")" = "$2" || return 1
  x=$(cat "/proc/$1/stat") || return 1
  x=${{x##*) }}
  set -- $x
  test "$1" != Z
}}
hp=
hs=
stop_helper() {{
  trap - EXIT HUP INT TERM
  set +e
  if test -n "$hp"; then
    if test -n "$hs" && guard "$hp" "$hs"; then kill -TERM "$hp"; fi
    i=0
    while test "$i" -lt 10; do
      test -n "$hs" && guard "$hp" "$hs" || break
      sleep .1
      i=$((i+1))
    done
    if test -n "$hs" && guard "$hp" "$hs"; then kill -KILL "$hp"; fi
    # Without a validated handshake the child has a two-second self-expiry.
    # wait never authorizes a signal and only reaps/caches our shell child.
    wait "$hp" 2>/dev/null
    hp=
  fi
}}
trap stop_helper EXIT HUP INT TERM
/bin/sh -c '
set -eu
r=$1
g=$2
priv=$3
clr=$4
dll=$5
p=$$
x=$(cat "/proc/$p/stat")
x=${{x##*) }}
set -- $x
test "$#" -ge 20
s=${{20}}
echo "$p $s" > "$r"
i=0
while test "$i" -lt 100; do
  if test -f "$g"; then
    ulimit -f 16
    exec env TMPDIR="$priv" DOTNET_CLI_HOME="$priv" DOTNET_EnableDiagnostics=0 \
      DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 \
      /usr/bin/dotnet --clr-path "$clr" --globalizationinvariant "$dll"
  fi
  sleep .02
  i=$((i+1))
done
exit 83
' -- {ready} {gate} {private} {CLR} {dll} > {stdout} 2> {stderr} &
hp=$!
i=0
while test "$i" -lt 50; do
  rp=
  rs=
  if test -f {ready} && read rp rs < {ready}; then
    if test "$rp" = "$hp" && test -n "$rs" && test "$(pstart "$hp")" = "$rs"; then
      hs=$rs
      break
    fi
  fi
  sleep .02
  i=$((i+1))
done
test -n "$hs"
test "$hs" -gt 0
{file_guard(ready)}
: > {gate}
chmod 600 {gate}
{file_guard(gate, 0)}
echo "HELPER_PID=$hp"
echo "HELPER_START=$hs"
deadline=0
i=0
while test "$i" -lt 80; do
  guard "$hp" "$hs" || break
  sleep .1
  i=$((i+1))
done
if guard "$hp" "$hs"; then
  deadline=1
  kill -TERM "$hp"
  i=0
  while test "$i" -lt 10; do
    guard "$hp" "$hs" || break
    sleep .1
    i=$((i+1))
  done
  if guard "$hp" "$hs"; then kill -KILL "$hp"; fi
fi
status=0
wait "$hp" || status=$?
hp=
test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}
{dir_guard(private)}
{file_guard(stdout)}
{file_guard(stderr)}
test "$(wc -c < {stdout})" -le 16384
test "$(wc -c < {stderr})" -le 16384
echo "HELPER_DEADLINE_HIT=$deadline"
echo "HELPER_EXIT=$status"
echo MANAGED_STDOUT_BEGIN
cat {stdout}
echo MANAGED_STDOUT_END
echo MANAGED_STDERR_BEGIN
cat {stderr}
echo MANAGED_STDERR_END
echo "EXECUTE_BOOT=$(cat /proc/sys/kernel/random/boot_id)"
echo "EXECUTE_UTC=$(date -u +%s)"
echo "EXECUTE_UPTIME=$(cut -d ' ' -f1 /proc/uptime)"
echo EXECUTE_COMPLETE
trap - EXIT HUP INT TERM
'''


def postflight(private: str, boot: str, files: dict[str, bytes]) -> str:
    checks = []
    for name in REMOTE_NAMES:
        target = private + "/" + name
        checks += [file_guard(target, len(files[name])),
                   f'test "$(sha256sum {target} | cut -d " " -f1)" = {digest(files[name])}']
    return f'''set -eu
umask 077
test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}
{stock_checks()}
{dir_guard(private)}
{chr(10).join(checks)}
echo POSTFLIGHT_IDENTITY_MATCH
'''


def cleanup(private: str, boot: str) -> str:
    allowed = sorted(set(REMOTE_NAMES + OUTPUT_NAMES))
    cases = "|".join(allowed)
    paths = " ".join(private + "/" + name for name in allowed)
    return f'''set -eu
umask 077
test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}
if test -e {private} || test -L {private}; then
  {dir_guard(private)}
  for f in {private}/* {private}/.[!.]* {private}/..?*; do
    test -e "$f" || test -L "$f" || continue
    test ! -L "$f"
    test -f "$f"
    test "$(stat -c '%u:%g:%a' "$f")" = "0:0:600"
    n=${{f##*/}}
    case "$n" in {cases}) ;; *) exit 82;; esac
  done
  rm -f {paths}
  rmdir {private}
fi
test ! -e {private}
test ! -L {private}
echo PRIVATE_REMOVED
'''


def marker(text: str, name: str, pattern: str) -> str:
    found = re.findall(rf"(?m)^{re.escape(name)}=({pattern})$", text)
    require(len(found) == 1, "Missing or duplicate " + name)
    return found[0]


def block(text: str, name: str) -> str:
    begin, end = name + "_BEGIN\n", name + "_END\n"
    require(text.count(begin) == text.count(end) == 1, "Bad " + name + " delimiters")
    before, tail = text.split(begin, 1)
    body, after = tail.split(end, 1)
    require(end not in before and begin not in after, "Reversed " + name + " delimiters")
    return body


def parse_preflight(text: str) -> dict[str, object]:
    require(text.rstrip().endswith("PREFLIGHT_IDENTITY_MATCH"), "Incomplete preflight")
    boot = marker(text, "PREFLIGHT_BOOT",
                  r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
    utc = int(marker(text, "PREFLIGHT_UTC", r"[0-9]+"))
    uptime = float(marker(text, "PREFLIGHT_UPTIME", r"[0-9]+(?:\.[0-9]+)?"))
    require(utc > 0 and uptime >= 0, "Bad preflight anchors")
    return {"boot_id": boot, "utc": utc, "uptime": uptime}


def parse_managed(text: str, helper_pid: int) -> dict[str, object]:
    lines = text.splitlines()
    require(lines[:1] == ["QD_TCON_STATUS_READ_V1"] and lines[-1:] == ["READ_COMPLETE"],
            "Managed output boundary")
    require(all(line.count("=") <= 1 for line in lines), "Malformed managed line")
    require([line for line in lines if "=" not in line] ==
            ["QD_TCON_STATUS_READ_V1", "READ_COMPLETE"], "Unexpected managed status")
    fields = dict(line.split("=", 1) for line in lines if "=" in line)
    expected = {"ARCH", "PTR_BYTES", "STRUCT_BYTES", "ENDIAN_LITTLE", "OUTPUT_OFFSET",
                "UID", "EUID", "PID_LIBC",
                "PID_SYSCALL", "DEVICE", "OPEN_FLAGS", "IOCTL_REQUEST", "PAYLOAD_BEFORE",
                "OPEN_RETURN", "OPEN_ERRNO", "IOCTL_RETURN", "IOCTL_ERRNO", "PAYLOAD_AFTER",
                "CLOSE_RETURN", "CLOSE_ERRNO", "CLASSIFICATION", "TCON_STATUS_HEX"}
    require(len([line for line in lines if "=" in line]) == len(expected) and
            set(fields) == expected, "Unexpected or duplicate managed field inventory")
    require(fields["ARCH"] == "Arm" and fields["PTR_BYTES"] == "4" and
            fields["STRUCT_BYTES"] == "16" and fields["ENDIAN_LITTLE"] == "1" and
            fields["OUTPUT_OFFSET"] == "4", "ARM32 ABI mismatch")
    require(fields["UID"] == fields["EUID"] == "0", "Managed UID mismatch")
    require(fields["PID_LIBC"] == fields["PID_SYSCALL"] == str(helper_pid),
            "Managed PID mismatch")
    require(fields["DEVICE"] == DEVICE and fields["OPEN_FLAGS"] == "0x80002",
            "Open contract mismatch")
    require(fields["IOCTL_REQUEST"] == "0xc010749f", "Request mismatch")
    require(fields["PAYLOAD_BEFORE"] == "0000001f,a55a5aa5,00000000,00000000",
            "Input payload mismatch")
    after = re.fullmatch(r"0000001f,([0-9a-f]{8}),00000000,00000000",
                         fields["PAYLOAD_AFTER"])
    require(after is not None and after.group(1) != SENTINEL,
            "No changed envelope-preserving kernel output")
    require(re.fullmatch(r"[0-9]+", fields["OPEN_RETURN"]) is not None and
            int(fields["OPEN_RETURN"]) >= 0, "Open failed")
    require(fields["OPEN_ERRNO"] == fields["IOCTL_ERRNO"] == fields["CLOSE_ERRNO"] == "0",
            "Unexpected errno on successful calls")
    require(fields["IOCTL_RETURN"] == fields["CLOSE_RETURN"] == "0", "Call failure")
    require(fields["CLASSIFICATION"] == "kernel_output_written", "Classification mismatch")
    require(fields["TCON_STATUS_HEX"] == "0x" + after.group(1), "Status mismatch")
    return {"classification": "kernel_output_written", "status_hex": fields["TCON_STATUS_HEX"],
            "kernel_output_changed_from_sentinel": True,
            "controller_transaction_proved": False, "hardware_status_proved": False,
            "qdf_debug_override_excluded": False, "controller_read_to_clear_excluded": False,
            "raw_fields": fields}


def parse_execution(text: str, boot: str, pre: dict[str, object]) -> dict[str, object]:
    pid = int(marker(text, "HELPER_PID", r"[0-9]+"))
    start = int(marker(text, "HELPER_START", r"[0-9]+"))
    require(pid > 1 and start > 0, "Invalid helper identity")
    require(marker(text, "HELPER_DEADLINE_HIT", r"[01]") == "0", "Helper deadline")
    require(marker(text, "HELPER_EXIT", r"[0-9]+") == "0", "Helper exit")
    stdout, stderr = block(text, "MANAGED_STDOUT"), block(text, "MANAGED_STDERR")
    require(stderr == "", "Managed stderr")
    require(marker(text, "EXECUTE_BOOT", re.escape(boot)) == boot, "Boot changed")
    utc = int(marker(text, "EXECUTE_UTC", r"[0-9]+"))
    uptime = float(marker(text, "EXECUTE_UPTIME", r"[0-9]+(?:\.[0-9]+)?"))
    require(utc >= int(pre["utc"]) and uptime >= float(pre["uptime"]),
            "Nonmonotonic anchors")
    require(text.rstrip().endswith("EXECUTE_COMPLETE"), "Execute incomplete")
    return {"helper_pid": pid, "helper_start_ticks": start, "boot_id": boot,
            "execute_utc": utc, "execute_uptime": uptime,
            "managed_stdout": stdout, "managed_stderr": stderr,
            "result": parse_managed(stdout, pid)}


def run_once(destination: Path, manifest: dict[str, object], files: dict[str, bytes]) -> dict[str, object]:
    private = PREFIX + uuid.uuid4().hex
    require(re.fullmatch(r"/tmp/researcher-tcon-[0-9a-f]{32}", private) is not None,
            "Bad private path")
    record: dict[str, object] = {
        "schema": "managed-tcon-status-read-result-v1", "created_utc": now(),
        "accepted": False, "read_usable": False, "physical_state": "unobserved",
        "physical_state_inferred_from_software": False, "one_shot": True,
        "retry_permitted": False, "private_directory": private,
        "build_manifest_sha256": file_digest(MANIFEST), "abi_report_sha256": ABI_REPORT_SHA256,
        "build": manifest, "calls": [],
        "limitations": [
            "A changed sentinel proves only that a kernel callback wrote output.",
            "The QDF debug override is not excluded by this standalone call.",
            "A controller transaction is not proved without correlated passive I2C/log evidence.",
            "The proprietary status read may be read-to-clear; its controller semantics are unresolved.",
            "No physical panel state or causal conclusion can be inferred from this result.",
        ],
    }
    try:
        with destination.open("x") as stream:
            stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    except FileExistsError as exc:
        raise ContractError("Output path already exists") from exc
    create_attempted = False
    boot: str | None = None
    try:
        pre = parse_preflight(root(preflight(), record, destination))
        record["preflight"] = pre
        boot = str(pre["boot_id"])
        save(destination, record)
        create_attempted = True
        require(root(create(private, boot), record, destination).strip() == "PRIVATE_CREATED",
                "Private creation failed")
        for command in stage(private, boot, files):
            require(root(command, record, destination).strip() == "STAGE_CHUNK_COMPLETE",
                    "Stage chunk failed")
        record["execution"] = parse_execution(
            root(execute(private, boot, files), record, destination), boot, pre)
        require(root(postflight(private, boot, files), record, destination).strip() ==
                "POSTFLIGHT_IDENTITY_MATCH", "Postflight identity failed")
        record["read_usable"] = True
        save(destination, record)
    except BaseException as exc:
        record["error"] = type(exc).__name__ + ": " + str(exc)
        record["accepted"] = record["read_usable"] = False
        save(destination, record)
        raise
    finally:
        if create_attempted and boot is not None:
            try:
                record["cleanup_confirmed"] = (
                    root(cleanup(private, boot), record, destination).strip() == "PRIVATE_REMOVED")
                require(record["cleanup_confirmed"] is True, "Cleanup not confirmed")
            except BaseException as exc:
                record["cleanup_confirmed"] = False
                record["cleanup_error"] = type(exc).__name__ + ": " + str(exc)
                record["read_usable"] = False
        else:
            record["cleanup_confirmed"] = not create_attempted
        record["accepted"] = bool(record.get("read_usable") and record["cleanup_confirmed"])
        record["finished_utc"] = now()
        save(destination, record)
    return record


def dry_plan(manifest: dict[str, object], files: dict[str, bytes]) -> dict[str, object]:
    boot = "00000000-0000-0000-0000-000000000000"
    private = PREFIX + "0" * 32
    commands = [preflight(), create(private, boot), *stage(private, boot, files),
                execute(private, boot, files), postflight(private, boot, files),
                cleanup(private, boot)]
    return {
        "dry_run": True,
        "execution_hold": ("failure-b consumed the prior one-query clearance; fresh exact-byte "
                           "review and a newly planned physical capture are required"),
        "no_tv_or_device_calls": True, "physical_state": "unobserved",
        "live_gate": "--run --reviewed --output /absolute/unique.json",
        "one_shot": True, "retry_permitted": False, "device": DEVICE,
        "request": "0xc010749f",
        "payload_before": ["0x0000001f", "0xa55a5aa5", "0x00000000", "0x00000000"],
        "accepted_classification": "kernel_output_written (not hardware/controller truth)",
        "staged_files": {name: {"bytes": len(data), "sha256": digest(data)}
                         for name, data in files.items()},
        "build_manifest_sha256": file_digest(MANIFEST), "abi_report_sha256": ABI_REPORT_SHA256,
        "root_command_count": len(commands),
        "root_command_max_bytes": max(len(command.encode()) for command in commands),
        "root_commands_within_8192": all(0 < len(command.encode()) <= MAX_COMMAND
                                         for command in commands),
        "manifest": manifest,
        "limitations": ["Static proof does not authorize the query.",
                        "Changed output can be a QDF debug override.",
                        "Controller read-to-clear behavior is unresolved."],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest, files = contract()
    if not args.run:
        require(not args.reviewed and args.output is None,
                "--reviewed/--output are meaningful only with --run")
        print(json.dumps(dry_plan(manifest, files), indent=2, sort_keys=True))
        return
    require(args.reviewed, "Live mode requires --reviewed")
    require(args.output is not None, "Live mode requires --output")
    raw = os.fspath(args.output)
    require(os.path.isabs(raw), "Output path must be absolute")
    destination = Path(os.path.abspath(raw))  # preserves a final symlink; resolve() would not
    result = run_once(destination, manifest, files)
    print(json.dumps({"result": str(destination), "accepted": result["accepted"],
                      "read_usable": result["read_usable"],
                      "cleanup_confirmed": result.get("cleanup_confirmed"),
                      "physical_state": "unobserved",
                      "classification": (result.get("execution", {}).get("result", {})
                                         .get("classification"))}, indent=2, sort_keys=True))
    if not result["accepted"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
