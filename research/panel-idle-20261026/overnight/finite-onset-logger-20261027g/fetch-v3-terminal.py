#!/usr/bin/env python3
"""Bounded read-only terminal artifact fetch for the single frozen v3 stage.

Dry by default. Live mode performs only authenticated file/process reads. It
does not execute the staged program, touch a device node, signal a process, or
clean the stage. Remote command text contains no backslash because the pinned
transport's argument quoting doubles backslashes.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Callable


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
STAGE = "/tmp/researcher-usb-onset-cf319c141c8141698db46d55634de752"
BOOT = "00000000-0000-4000-8000-000000000000"
ADAPTER = OVERNIGHT / "managed-usb-secondary-logger-onset/root-with-margin.py"
ADAPTER_SHA256 = "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a"
SOURCE_RECORD = HERE / "control-smoke-v3/record.json"
SOURCE_RECORD_SHA256 = "fed51d0624c3c627e3cb49e40fa03a588c0314c9e06cff95fb9189e6b4d518f7"
CHUNK = 8192
MAX_COMMAND = 8192
ELIGIBLE_UPTIME = 114322.76
SUPERVISOR_PID = 9140
SUPERVISOR_START_TICKS = 28569437
SUPERVISOR_PID_SIZE = 5
SUPERVISOR_PID_SHA256 = "ee80a54379f0083a8a0b7d7e095886f57502d8d0db0fea0d612e53ebfe25c533"
SUPERVISOR_STAT_SIZE = 250
SUPERVISOR_STAT_SHA256 = "2f709d4eb77f7988acc7b970069c9a6bdecbf6e7aff22cfe4661de7ace71a6db"
SUPERVISOR_START_SIZE = 69
SUPERVISOR_START_SHA256 = "7806fd9e6947c58f15da931b6a88947df2fd07cbea3e914431e717ff2e62778f"

INPUTS = {
    "ManagedUsbSecondaryLoggerOnset.dll":
        (71680, "4870eed095247b8f5c86a58044e10e8c3682248b4c0465c49e5d4642cb8e54e9"),
    "ManagedUsbSecondaryLoggerOnset.deps.json":
        (460, "d905733139977c0436bfd4ac520a13c29498c406961c0d9e39717dbac7b4b320"),
    "ManagedUsbSecondaryLoggerOnset.runtimeconfig.json":
        (242, "aeb46a15366e38511c192ccf65312442c64e8753b3c16fd2ca0b4cb34a5c59f3"),
    "supervisor.sh":
        (1819, "6535741f16f14286a9e894728b2ae3fd76ccafa7487e8979e0daf95f7367deb6"),
}
OUTPUT_LIMITS = {
    "supervisor.launch.stdout": 2048,
    "supervisor.launch.stderr": 2048,
    "supervisor.pid": 32,
    "supervisor.stat": 2048,
    "supervisor.start": 256,
    "native.pid": 32,
    "native.stdout": 50000,
    "native.stderr": 2048,
    "native.exit": 2048,
    "logger.ready": 2048,
}
INVENTORY = tuple(INPUTS) + tuple(OUTPUT_LIMITS)
HEX64 = re.compile(r"[0-9a-f]{64}")
UPTIME = re.compile(r"[0-9]+(?:[.][0-9]+)? [0-9]+(?:[.][0-9]+)?")


class ContractError(ValueError):
    pass


def need(value: bool, message: str) -> None:
    if not value:
        raise ContractError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict_json(raw: bytes):
    def reject(value: str):
        raise ContractError("non-JSON constant " + value)
    try:
        return json.loads(raw.decode("utf-8"), parse_constant=reject)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("strict JSON") from exc


def write_new(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)


def local_contract() -> dict:
    need(digest(ADAPTER.read_bytes()) == ADAPTER_SHA256, "margin adapter identity")
    raw = SOURCE_RECORD.read_bytes()
    need(digest(raw) == SOURCE_RECORD_SHA256, "frozen v3 source record identity")
    source = strict_json(raw)
    need(source.get("remote_stage") == STAGE, "v3 stage identity")
    need(source.get("root_adapter_sha256") == ADAPTER_SHA256, "v3 adapter identity")
    need(source.get("cleanup_deferred") is True and source.get("no_retry") is True,
         "v3 retained-stage policy")
    need(len(INVENTORY) == len(set(INVENTORY)) == 14, "fixed inventory")
    return source


def shell_guard(path: str) -> str:
    return (f'test ! -L "{path}"\n'
            f'test -f "{path}"\n'
            f'test "$(stat -c \'%u:%g:%a\' "{path}")" = 0:0:600\n')


def inventory_shell() -> str:
    allowed = "|".join(INVENTORY)
    return f'''d={STAGE}
test ! -L "$d"
test -d "$d"
test "$(stat -c '%u:%g:%a' "$d")" = 0:0:700
cd "$d"
test "$(pwd)" = "$d"
count=0
for item in ./* ./.[!.]* ./..?*; do
  test -e "$item" || test -L "$item" || continue
  name=${{item##*/}}
  case "$name" in {allowed}) ;; *) exit 91;; esac
  count=$((count+1))
done
test "$count" = 13 || test "$count" = 14
'''


def checked_command(command: str, label: str) -> str:
    need(0 < len(command.encode()) <= MAX_COMMAND, label + " command bound")
    need("\\" not in command, label + " command contains transport-unstable backslash")
    return command


def require_ready_absence_guard(command: str) -> None:
    marker = 'else\ntest ! -L logger.ready\necho "MISSING logger.ready"\nfi\n'
    need(command.count(marker) == 1, "optional READY dangling-symlink guard")


def terminal_command() -> str:
    command = "set -eu\n" + inventory_shell()
    for name, (size, sha) in INPUTS.items():
        path = name
        command += shell_guard(path)
        command += f'test "$(wc -c < "{path}")" = {size}\n'
        command += f'test "$(sha256sum "{path}" | cut -d \' \' -f1)" = {sha}\n'
    for name, limit in OUTPUT_LIMITS.items():
        if name == "logger.ready":
            continue
        path = name
        command += shell_guard(path)
        command += f'test "$(wc -c < "{path}")" -le {limit}\n'
    command += f'''boot=$(cat /proc/sys/kernel/random/boot_id)
test "$boot" = {BOOT}
sp=$(cat supervisor.pid); case "$sp" in ''|*[!0-9]*) exit 92;; esac; test "$sp" -gt 1
np=$(cat native.pid); case "$np" in ''|*[!0-9]*) exit 93;; esac; test "$np" -gt 1
test "$sp" = {SUPERVISOR_PID}
test "$(wc -c < supervisor.pid)" = {SUPERVISOR_PID_SIZE}
test "$(sha256sum supervisor.pid | cut -d ' ' -f1)" = {SUPERVISOR_PID_SHA256}
test "$(wc -c < supervisor.stat)" = {SUPERVISOR_STAT_SIZE}
test "$(sha256sum supervisor.stat | cut -d ' ' -f1)" = {SUPERVISOR_STAT_SHA256}
test "$(wc -c < supervisor.start)" = {SUPERVISOR_START_SIZE}
test "$(sha256sum supervisor.start | cut -d ' ' -f1)" = {SUPERVISOR_START_SHA256}
saved=$(cat supervisor.stat); rest=${{saved##*) }}; set -- $rest
test "$#" -ge 20; test "${{saved%% *}}" = "$sp"; test "$3" = "$sp"; test "$4" = "$sp"
st=${{20}}; case "$st" in ''|*[!0-9]*) exit 94;; esac
test "$st" = {SUPERVISOR_START_TICKS}
eligible=$(cut -d ' ' -f1 /proc/uptime)
awk -v u="$eligible" 'BEGIN {{ exit !(u >= {ELIGIBLE_UPTIME}) }}'
terminal_process() {{
  label=$1; pid=$2; expected_ticks=$3
  if test -e "/proc/$pid/stat"; then
    live=$(cat "/proc/$pid/stat"); rest=${{live##*) }}; set -- $rest
    test "$#" -ge 20; test "${{live%% *}}" = "$pid"
    state=$1; test "$state" = Z || test "$state" = X
    test "$expected_ticks" = - || test "${{20}}" = "$expected_ticks"
    echo "PROCESS $label ZOMBIE $pid ${{20}}"
  else
    echo "PROCESS $label ABSENT $pid $expected_ticks"
  fi
}}
echo TERMINAL_META_V1_BEGIN
echo "BOOT=$boot"
echo "UPTIME=$(cat /proc/uptime)"
terminal_process supervisor "$sp" "$st"
terminal_process native "$np" -
'''
    for name in OUTPUT_LIMITS:
        path = name
        if name == "logger.ready":
            command += (f'if test -e {path}; then\n' + shell_guard(path) +
                        f'test "$(wc -c < {path})" -le {OUTPUT_LIMITS[name]}\n'
                        f'echo "FILE {name} $(wc -c < {path}) $(sha256sum {path} | cut -d \' \' -f1)"\n'
                        f'else\ntest ! -L {path}\necho "MISSING {name}"\nfi\n')
        else:
            command += f'echo "FILE {name} $(wc -c < "{path}") $(sha256sum "{path}" | cut -d \' \' -f1)"\n'
    command += ("echo EXIT_BASE64_BEGIN\n"
                'base64 native.exit\n'
                "echo EXIT_BASE64_END\n"
                "echo TERMINAL_META_V1_END\n")
    require_ready_absence_guard(command)
    return checked_command(command, "terminal")


def chunk_command(name: str, size: int, sha: str, offset: int, count: int) -> str:
    need(name in OUTPUT_LIMITS, "fixed output name")
    need(0 <= offset <= size and 0 <= count <= CHUNK and offset + count <= size,
         "fixed chunk bounds")
    need(HEX64.fullmatch(sha) is not None, "fixed chunk digest")
    path = name
    command = ("set -eu\n" + inventory_shell() + shell_guard(path) +
               f'test "$(wc -c < "{path}")" = {size}\n'
               f'test "$(sha256sum "{path}" | cut -d \' \' -f1)" = {sha}\n'
               f'b1=$(cat /proc/sys/kernel/random/boot_id); test "$b1" = {BOOT}\n'
               "echo FETCH_CHUNK_V1_BEGIN\n"
               'echo "BOOT_BEFORE=$b1"\n'
               f"echo 'FILE={name} OFFSET={offset} COUNT={count}'\n"
               "echo DATA_BASE64_BEGIN\n"
               f'dd if="{path}" bs=1 skip={offset} count={count} 2>&- | base64\n'
               "echo DATA_BASE64_END\n"
               f'test "$(wc -c < "{path}")" = {size}\n'
               f'test "$(sha256sum "{path}" | cut -d \' \' -f1)" = {sha}\n'
               f'b2=$(cat /proc/sys/kernel/random/boot_id); test "$b2" = {BOOT}; test "$b2" = "$b1"\n'
               'echo "BOOT_AFTER=$b2"\n'
               "echo FETCH_CHUNK_V1_END\n")
    return checked_command(command, "chunk")


def decode_block(lines: list[str], begin: str, end: str, maximum_lines: int) -> bytes:
    need(lines.count(begin) == 1 and lines.count(end) == 1, "unique " + begin)
    first, last = lines.index(begin), lines.index(end)
    need(first < last and last - first - 1 <= maximum_lines, "bounded " + begin)
    text = "".join(lines[first + 1:last])
    try:
        return base64.b64decode(text, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ContractError("strict base64 " + begin) from exc


def process_line(line: str, label: str) -> dict:
    match = re.fullmatch(rf"PROCESS {label} (ABSENT|ZOMBIE) ([1-9][0-9]*) (-|[0-9]+)", line)
    need(match is not None, "terminal process " + label)
    state, pid, ticks = match.groups()
    need((state == "ABSENT" and (ticks == "-" or ticks.isdigit())) or
         (state == "ZOMBIE" and ticks.isdigit()), "process state/ticks " + label)
    if label == "supervisor":
        need(int(pid) == SUPERVISOR_PID and ticks == str(SUPERVISOR_START_TICKS),
             "recovered supervisor identity")
    else:
        need(not (state == "ABSENT" and ticks != "-"), "absent native identity")
    return {"state": state.lower(), "pid": int(pid),
            "start_ticks": None if ticks == "-" else int(ticks)}


def parse_metadata(stdout: str) -> dict:
    lines = stdout.splitlines()
    need(len(lines) >= 18 and lines[0] == "TERMINAL_META_V1_BEGIN" and
         lines[-1] == "TERMINAL_META_V1_END", "terminal metadata envelope")
    need(lines[1] == "BOOT=" + BOOT, "terminal boot")
    need(lines[2].startswith("UPTIME=") and UPTIME.fullmatch(lines[2][7:]) is not None and
         float(lines[2][7:].split()[0]) >= ELIGIBLE_UPTIME,
         "terminal uptime")
    supervisor = process_line(lines[3], "supervisor")
    native = process_line(lines[4], "native")
    rows = lines[5:5 + len(OUTPUT_LIMITS)]
    files = {}
    for expected, line in zip(OUTPUT_LIMITS, rows):
        if expected == "logger.ready" and line == "MISSING logger.ready":
            continue
        match = re.fullmatch(r"FILE ([A-Za-z0-9.]+) ([0-9]+) ([0-9a-f]{64})", line)
        need(match is not None and match.group(1) == expected, "file metadata order")
        size = int(match.group(2)); sha = match.group(3)
        need(0 <= size <= OUTPUT_LIMITS[expected] and HEX64.fullmatch(sha) is not None,
             "file metadata bound " + expected)
        files[expected] = {"size": size, "sha256": sha}
    recovered = {
        "supervisor.pid": (SUPERVISOR_PID_SIZE, SUPERVISOR_PID_SHA256),
        "supervisor.stat": (SUPERVISOR_STAT_SIZE, SUPERVISOR_STAT_SHA256),
        "supervisor.start": (SUPERVISOR_START_SIZE, SUPERVISOR_START_SHA256),
    }
    for name, (size, sha) in recovered.items():
        need(files.get(name) == {"size": size, "sha256": sha},
             "recovered file binding " + name)
    exit_raw = decode_block(lines, "EXIT_BASE64_BEGIN", "EXIT_BASE64_END", 40)
    need(5 + len(OUTPUT_LIMITS) == lines.index("EXIT_BASE64_BEGIN"), "exit block position")
    need(lines.index("EXIT_BASE64_END") == len(lines) - 2, "exit block terminal position")
    need(len(exit_raw) == files["native.exit"]["size"] and
         digest(exit_raw) == files["native.exit"]["sha256"], "exit metadata binding")
    completion = strict_json(exit_raw)
    expected_keys = {"schema", "supervisor_pid", "child_pid", "child_exit",
                     "stdout_bytes", "stderr_bytes", "stdout_sha256", "stderr_sha256",
                     "boot_id", "uptime"}
    need(isinstance(completion, dict) and set(completion) == expected_keys,
         "completion schema keys")
    need(completion["schema"] == "secondary-logger-onset-exit-v1" and
         completion["boot_id"] == BOOT and UPTIME.fullmatch(completion["uptime"]) is not None,
         "completion identity")
    need(type(completion["supervisor_pid"]) is int and
         completion["supervisor_pid"] == supervisor["pid"], "completion supervisor PID")
    need(type(completion["child_pid"]) is int and completion["child_pid"] == native["pid"],
         "completion native PID")
    need(type(completion["child_exit"]) is int and 0 <= completion["child_exit"] <= 255,
         "completion exit")
    for prefix, filename in (("stdout", "native.stdout"), ("stderr", "native.stderr")):
        need(type(completion[prefix + "_bytes"]) is int and
             completion[prefix + "_bytes"] == files[filename]["size"] and
             completion[prefix + "_sha256"] == files[filename]["sha256"],
             "completion " + prefix + " binding")
    return {"boot_id": BOOT, "uptime": lines[2][7:],
            "processes": {"supervisor": supervisor, "native": native},
            "files": files, "completion": completion, "native_exit": exit_raw}


def parse_chunk(stdout: str, name: str, offset: int, count: int) -> bytes:
    lines = stdout.splitlines()
    need(len(lines) >= 8 and lines[0] == "FETCH_CHUNK_V1_BEGIN" and
         lines[1] == "BOOT_BEFORE=" + BOOT and
         lines[2] == f"FILE={name} OFFSET={offset} COUNT={count}" and
         lines[-2] == "BOOT_AFTER=" + BOOT and lines[-1] == "FETCH_CHUNK_V1_END",
         "chunk envelope")
    raw = decode_block(lines, "DATA_BASE64_BEGIN", "DATA_BASE64_END", 150)
    need(lines.index("DATA_BASE64_BEGIN") == 3 and
         lines.index("DATA_BASE64_END") == len(lines) - 3, "chunk block position")
    need(len(raw) == count, "chunk exact count")
    return raw


def fetch(call: Callable[[str], str], output: Path) -> dict:
    first = parse_metadata(call(terminal_command()))
    fetched = {}
    for name, row in first["files"].items():
        data = bytearray()
        size, sha = row["size"], row["sha256"]
        offsets = [0] if size == 0 else range(0, size, CHUNK)
        for offset in offsets:
            count = min(CHUNK, size - offset)
            raw = parse_chunk(call(chunk_command(name, size, sha, offset, count)),
                              name, offset, count)
            data.extend(raw)
        need(len(data) == size and digest(bytes(data)) == sha, "complete artifact " + name)
        write_new(output / name, bytes(data))
        fetched[name] = {"size": size, "sha256": sha,
                         "chunks": 1 if size == 0 else (size + CHUNK - 1) // CHUNK}
    second = parse_metadata(call(terminal_command()))
    need(second["files"] == first["files"] and
         second["completion"] == first["completion"] and
         second["native_exit"] == first["native_exit"], "terminal metadata changed")
    start_raw = (output / "supervisor.start").read_bytes()
    start_lines = start_raw.decode("ascii").splitlines()
    need(len(start_lines) == 2 and start_lines[0] == "BOOT=" + BOOT and
         start_lines[1].startswith("UPTIME=") and
         UPTIME.fullmatch(start_lines[1][7:]) is not None, "supervisor start identity")
    need((output / "native.exit").read_bytes() == first["native_exit"],
         "fetched exit equality")
    return {"schema": "v3-terminal-fetch-result-v1", "stage": STAGE,
            "boot_id": BOOT, "terminal_before": first["processes"],
            "terminal_after": second["processes"], "completion": first["completion"],
            "artifacts": fetched, "read_only": True, "cleanup_performed": False,
            "retry_performed": False, "target_program_executed": False,
            "ready_present": "logger.ready" in first["files"],
            "armed_control_established": False, "protocol_state_validated": False,
            "physical_picture_observed": False}


class FakeRoot:
    def __init__(self, artifacts: dict[str, bytes], fault: str | None = None):
        self.artifacts = artifacts
        self.fault = fault
        self.calls = []
        self.metadata_calls = 0
        if fault == "bad-stat":
            self.artifacts["supervisor.stat"] += b"x"
        if fault == "bad-start":
            self.artifacts["supervisor.start"] += b"x"
        if fault == "bad-saved-pid":
            self.artifacts["supervisor.pid"] = b"9142\n"

    def metadata(self) -> str:
        self.metadata_calls += 1
        rows = ["TERMINAL_META_V1_BEGIN", "BOOT=" + BOOT, "UPTIME=114400.00 426700.00",
                "PROCESS supervisor ABSENT 9140 28569437", "PROCESS native ABSENT 9141 -"]
        for name in OUTPUT_LIMITS:
            if name not in self.artifacts:
                rows.append("MISSING " + name)
                continue
            raw = self.artifacts[name]
            rows.append(f"FILE {name} {len(raw)} {digest(raw)}")
        rows += ["EXIT_BASE64_BEGIN", base64.b64encode(self.artifacts["native.exit"]).decode(),
                 "EXIT_BASE64_END", "TERMINAL_META_V1_END"]
        if self.fault == "live-process":
            rows[3] = "PROCESS supervisor RUNNING 9140 28569437"
        if self.fault == "wrong-supervisor-identity":
            rows[3] = "PROCESS supervisor ABSENT 9142 28569438"
        if self.fault == "stale-uptime":
            rows[2] = "UPTIME=114300.00 426600.00"
        if self.fault == "final-change" and self.metadata_calls == 2:
            rows[5] = rows[5].replace(" 0 ", " 1 ")
        return "\n".join(rows) + "\n"

    def __call__(self, command: str) -> str:
        self.calls.append(command)
        if "TERMINAL_META_V1_BEGIN" in command:
            return self.metadata()
        match = re.search(r"echo 'FILE=([^ ]+) OFFSET=([0-9]+) COUNT=([0-9]+)'", command)
        need(match is not None, "fake chunk command")
        name, offset, count = match.group(1), int(match.group(2)), int(match.group(3))
        raw = self.artifacts[name][offset:offset + count]
        encoded = base64.b64encode(raw).decode()
        if self.fault == "bad-middle" and name == "native.stdout" and offset == CHUNK:
            encoded = "!" + encoded[1:]
        boot_after = "changed" if self.fault == "boot-change" and name == "native.stdout" else BOOT
        return ("FETCH_CHUNK_V1_BEGIN\nBOOT_BEFORE=" + BOOT +
                f"\nFILE={name} OFFSET={offset} COUNT={count}\nDATA_BASE64_BEGIN\n" + encoded +
                "\nDATA_BASE64_END\nBOOT_AFTER=" + boot_after + "\nFETCH_CHUNK_V1_END\n")


def fake_artifacts(include_ready: bool = True) -> dict[str, bytes]:
    values = {name: b"" for name in OUTPUT_LIMITS}
    values.update({
        "supervisor.pid": b"9140\n",
        "supervisor.stat": (b"9140 (sh) S 1 9140 9140 0 -1 4194304 434 600 0 0 0 0 0 0 20 0 1 0 "
                            b"28569437 4845568 299 18446744073709551615 8794112 9354548 4294832000 "
                            b"0 0 0 65536 4103 65536 1 0 0 17 0 0 0 0 0 0 9421056 9445744 31989760 "
                            b"4294833804 4294835634 4294835634 4294836208 0\n"),
        "supervisor.start": ("BOOT=" + BOOT + "\nUPTIME=114277.76 426562.77\n").encode(),
        "native.pid": b"9141\n",
        "native.stdout": bytes(range(256)) * 70,
    })
    if include_ready:
        values["logger.ready"] = b'{"ready":true}\n'
    else:
        del values["logger.ready"]
    completion = {"schema": "secondary-logger-onset-exit-v1", "supervisor_pid": 9140,
                  "child_pid": 9141, "child_exit": 0,
                  "stdout_bytes": len(values["native.stdout"]),
                  "stderr_bytes": len(values["native.stderr"]),
                  "stdout_sha256": digest(values["native.stdout"]),
                  "stderr_sha256": digest(values["native.stderr"]), "boot_id": BOOT,
                  "uptime": "114330.00 426610.00"}
    values["native.exit"] = (json.dumps(completion, separators=(",", ":")) + "\n").encode()
    return values


def self_test() -> dict:
    tests = []

    def run(name, action):
        action(); tests.append(name)

    def success():
        with tempfile.TemporaryDirectory() as temporary:
            root = FakeRoot(fake_artifacts())
            result = fetch(root, Path(temporary))
            need(result["read_only"] is True and len(result["artifacts"]) == 10,
                 "success result")
            need((Path(temporary) / "native.stdout").read_bytes() ==
                 fake_artifacts()["native.stdout"], "success bytes")
            need(len(root.calls) == 14, "success bounded calls")
    run("success-multichunk-exact-hash", success)

    def success_without_ready():
        with tempfile.TemporaryDirectory() as temporary:
            root = FakeRoot(fake_artifacts(include_ready=False))
            result = fetch(root, Path(temporary))
            need(result["ready_present"] is False and
                 result["armed_control_established"] is False and
                 "logger.ready" not in result["artifacts"], "missing READY classification")
            need(len(root.calls) == 13, "missing READY bounded calls")
    run("terminal-exit-without-ready-is-retrieved-not-armed", success_without_ready)

    def rejected(fault, expected_calls):
        with tempfile.TemporaryDirectory() as temporary:
            root = FakeRoot(fake_artifacts(), fault)
            try:
                fetch(root, Path(temporary))
            except ContractError:
                pass
            else:
                raise AssertionError("fault accepted " + fault)
            need(len(root.calls) == expected_calls, "fault bounded calls " + fault)
    run("live-process-preflight-stops", lambda: rejected("live-process", 1))
    run("wrong-supervisor-identity-stops", lambda: rejected("wrong-supervisor-identity", 1))
    run("wrong-saved-pid-hash-stops", lambda: rejected("bad-saved-pid", 1))
    run("wrong-saved-stat-hash-stops", lambda: rejected("bad-stat", 1))
    run("wrong-saved-start-hash-stops", lambda: rejected("bad-start", 1))
    run("before-eligibility-uptime-stops", lambda: rejected("stale-uptime", 1))
    run("middle-malformed-base64-stops", lambda: rejected("bad-middle", 9))
    run("chunk-boot-drift-stops", lambda: rejected("boot-change", 8))
    run("final-metadata-drift-stops", lambda: rejected("final-change", 14))

    def command_policy():
        commands = [terminal_command(), chunk_command("native.stdout", 50000, "a" * 64,
                                                       40960, 8192)]
        forbidden = ("/dev/", " rm ", "kill", "pkill", "reset", "--execute", "dotnet")
        for command in commands:
            need(len(command.encode()) <= MAX_COMMAND, "command size")
            need("\\" not in command, "transport backslash")
            need(not any(token in command for token in forbidden), "read-only command policy")
        terminal = commands[0]
        for value in (str(SUPERVISOR_PID), str(SUPERVISOR_START_TICKS),
                      SUPERVISOR_PID_SHA256, SUPERVISOR_STAT_SHA256,
                      SUPERVISOR_START_SHA256, str(ELIGIBLE_UPTIME)):
            need(value in terminal, "recovered binding missing " + value)
    run("commands-bounded-read-only-no-backslash", command_policy)

    def dangling_ready_guard():
        terminal = terminal_command()
        broken = terminal.replace("test ! -L logger.ready\n", "", 1)
        try:
            require_ready_absence_guard(broken)
        except ContractError:
            pass
        else:
            raise AssertionError("dangling optional READY guard removal accepted")
    run("dangling-ready-guard-removal-refused", dangling_ready_guard)
    return {"status": "PASS", "tests": tests, "count": len(tests),
            "target_operations": 0}


def load_adapter():
    need(digest(ADAPTER.read_bytes()) == ADAPTER_SHA256, "margin adapter identity")
    spec = importlib.util.spec_from_file_location("pinned_v3_terminal_margin_adapter", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    need(module.REMOTE_TIMEOUT_SECONDS == 45 and module.HOST_TIMEOUT_SECONDS == 75 and
         module.MAX_COMMAND == 8192 and module.MAX_RESPONSE == 65536,
         "margin adapter bounds")
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    local_contract()
    need(sum((args.fetch, args.self_test)) <= 1, "choose one action")
    if args.self_test:
        need(args.output is None, "self-test output forbidden")
        print(json.dumps(self_test(), separators=(",", ":")))
        return 0
    if not args.fetch:
        need(args.output is None, "output requires --fetch")
        print(json.dumps({"dry_run": True, "stage": STAGE, "boot_id": BOOT,
                          "inventory_count": [13, 14], "ready_optional": True,
                          "chunk_bytes": CHUNK,
                          "adapter_sha256": ADAPTER_SHA256, "target_operations": 0,
                          "mutations": 0, "retry": False, "cleanup": False},
                         separators=(",", ":")))
        return 0
    need(args.output is not None, "--fetch requires --output")
    output = args.output.resolve()
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    adapter = load_adapter()
    record_path = output / "record.json"
    record = {"schema": "v3-terminal-fetch-record-v1", "source_record_sha256": SOURCE_RECORD_SHA256,
              "adapter_sha256": ADAPTER_SHA256, "stage": STAGE, "boot_id": BOOT,
              "read_only": True, "no_retry": True, "cleanup": False, "calls": []}
    adapter.save(record_path, record)
    record_path.chmod(0o600)
    raw_index = 0

    def call(command: str) -> str:
        nonlocal raw_index
        checked_command(command, "remote")
        stdout = adapter.root(command, record, record_path)
        write_new(output / f"raw-call-{raw_index:03d}.stdout.txt", stdout.encode())
        raw_index += 1
        return stdout

    try:
        result = fetch(call, output)
        result["root_calls"] = raw_index
        write_new(output / "result.json",
                  (json.dumps(result, indent=2, sort_keys=True) + "\n").encode())
        print(json.dumps({"status": "FETCHED", "output": str(output),
                          "root_calls": raw_index, "cleanup": False}, separators=(",", ":")))
        return 0
    except Exception as exc:
        failure = {"status": "STOPPED", "error_type": type(exc).__name__,
                   "error": str(exc), "root_calls_completed": raw_index,
                   "retry": False, "cleanup": False}
        write_new(output / "failure.json",
                  (json.dumps(failure, indent=2, sort_keys=True) + "\n").encode())
        print(json.dumps(failure, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
