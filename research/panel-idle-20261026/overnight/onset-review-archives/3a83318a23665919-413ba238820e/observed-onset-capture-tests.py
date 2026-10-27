#!/usr/bin/env python3
"""Offline fail-closed tests for observed-onset-capture.py; never contact the TV."""

import base64
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "observed-onset-capture.py"
SPEC = importlib.util.spec_from_file_location("capture", SOURCE)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


def b64(words):
    return base64.b64encode(b"".join(x.to_bytes(4, "little") for x in words)).decode()


def event(pid, when, kind, body, tgid=None):
    tgid = pid if tgid is None else tgid
    return f" worker-{pid} (  {tgid}) [000] .... {when:.6f}: {kind}: {body}\n"


def trace(rows, retained=None, written=None):
    retained = len(rows) if retained is None else retained
    written = retained if written is None else written
    return (f"# entries-in-buffer/entries-written: {retained}/{written}\n" + "".join(rows)).encode()


def good_trace(extra_before=(), extra_inside=(), extra_after=()):
    rows = list(extra_before)
    rows += [event(7, 10, "tracing_mark_write", "CAPTURE_START utc=1000 uptime=10.000")]
    rows += list(extra_inside)
    rows += [event(7, 11, "tracing_mark_write", "CAPTURE_END utc=1001 uptime=11.000")]
    rows += list(extra_after)
    return trace(rows)


POINTERS = [
    0x10000000, 0x105BE2A4, 0x10600000, 0x1059F2E8, 0x10600100,
    0x20000000, 0x2012AF7C, 0x20100000, 0x20101000, 0x20102000,
    0x20103000, 0x20104000, 0x20128A28, 0x20128A90, 0x20128AB0,
]


def qrow(when, pointers=POINTERS):
    (_a, glob, panel, vptr, inner, _d, _dglob, ep, op,
     ec, et, ea, ecv, etv, eav) = pointers
    values = ([glob], [panel], [vptr, inner], [17], [2, 3],
              [ep, ep + 4, 0, op, op + 4, 0], [2], [0, ec, et, ea], [9],
              [ecv], [etv], [eav])
    return "|".join(["Q", f"{when:.3f}"] + [b64(value) for value in values])


def sample_text(start, end, monitor_step=.2, q_step=1.0, pointers=POINTERS):
    rows = []
    value = start + .1
    while value <= end - .1 + 1e-8:
        rows.append(f"M|{value:.3f}|{b64([0] * 38)}")
        value += monitor_step
    value = start + .1
    while value <= end - .1 + 1e-8:
        rows.append(qrow(value, pointers))
        value += q_step
    return "\n".join(rows) + "\n"


def dd_stderr(monitor_rows, qd_rows):
    counts = {1: 33 + 8 * qd_rows, 2: 2 * qd_rows, 4: qd_rows,
              6: qd_rows, 38: monitor_rows}
    rows = []
    for count, operations in counts.items():
        for _ in range(operations):
            size = count * 4
            rows += [f"{count}+0 records in", f"{count}+0 records out",
                     f"{size} bytes ({size} B) copied, 3.1e-05 s, 128 kB/s"]
    return "\n".join(rows) + "\n"


def identity(pid, exe, ticks, hashes):
    return "\n".join([str(pid), exe, str(ticks)] +
                     [f"{digest}  {path}" for path, digest in hashes.items()])


def metadata_fixture(script_size=123, script_sha="a" * 64):
    avh = {capture.AVOC_PATH: capture.AVOC_SHA, capture.AVE_PATH: capture.AVE_SHA}
    deh = {capture.DEV_PATH: capture.DEV_SHA}
    a, glob, panel, vptr, inner, d, dglob, ep, op, ec, et, ea, ecv, etv, eav = POINTERS
    pointer21 = [a, glob, panel, vptr, inner, d, dglob,
                 ep, ep + 4, 0, op, op + 4, 0, ep, op, ec, et, ea, ecv, etv, eav]
    amap = "10000000-11000000 r--p 00000000 00:00 0 /prd/usr/lib/libave.so.0.1"
    dmap = "20000000-21000000 r--p 00000000 00:00 0 /usr/bin/deviced"
    syscall_filter = capture.syscall_filter_for_tids([7, 11])
    config = ["PER_CPU_KB=4096", "TOTAL_KB=16384", "RECORD_TGID=record-tgid",
              "TRACE_CLOCK=global [mono] boot",
              "SYSCALL_ENTER_FILTER=" + syscall_filter,
              "SYSCALL_EXIT_FILTER=" + syscall_filter]
    config += [key + "=" + value for key, value in capture.TRACE_CONFIG_EXPECTED.items()]
    global_trace = "0\nnop\n1024\nglobal [mono] boot\n0"
    values = {
        "BUILD": "NAME=test\n" + capture.BUILD,
        "SCRIPT_HASH_START": f"{script_size} capture.sh\n{script_sha}  capture.sh",
        "BOOT_START": "00000000-0000-4000-8000-000000000000",
        "SYNC_START": "1000\n100.00 200.00",
        "AVOC_ID_START": identity(7, capture.AVOC_PATH, 10, avh),
        "DEV_ID_START": identity(8, capture.DEV_PATH, 20, deh),
        "POINTERS_START": " ".join(map(str, pointer21)),
        "AVOC_MAPS_START": amap, "DEV_MAPS_START": dmap,
        "GLOBAL_TRACE_START": global_trace, "TRACE_CONFIG": "\n".join(config),
        "BOOT_END": "00000000-0000-4000-8000-000000000000",
        "SYNC_END": "1100\n200.00 300.00",
        "CAPTURE_WINDOW": "105.000 105.200 190.200 103.000 194.000 0 0 0 0 0 0",
        "AVOC_ID_END": identity(7, capture.AVOC_PATH, 10, avh),
        "DEV_ID_END": identity(8, capture.DEV_PATH, 20, deh),
        "POINTERS_END": " ".join(map(str, pointer21)),
        "AVOC_MAPS_END": amap, "DEV_MAPS_END": dmap,
        "SCRIPT_HASH_END": f"{script_size} capture.sh\n{script_sha}  capture.sh",
        "GLOBAL_TRACE_END": global_trace,
        "VLOG_SEMANTICS": "/usr/bin/vlogutil -s absolute uptime bounds; coverage measured",
    }
    return "\n".join(f"@@ {key}\n{value}" for key, value in values.items()) + "\n"


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.shell = capture.build_remote_script("fixture", 85)
        self.source = SOURCE.read_text()

    def test_generated_shell_syntax_and_staged_bounds(self):
        subprocess.run(["sh", "-n"], input=self.shell, text=True, check=True)
        longest = capture.build_remote_script("a" + "z" * 30, 90)
        subprocess.run(["sh", "-n"], input=longest, text=True, check=True)
        self.assertGreater(len(longest.encode()), 8192)
        encoded = base64.b64encode(b"x" * 4096).decode()
        chunk = f"set -eu\nprintf %s {encoded} | base64 -d >>{capture.STAGE_ROOT}/{'z'*31}/capture.sh"
        self.assertLessEqual(len(chunk.encode()), 8192)
        self.assertIn("exec /usr/bin/setsid /bin/sh", self.source)

    def test_staging_chunks_are_exact_and_bounded(self):
        script = self.shell.encode()
        captured, staged = [], bytearray()

        def fake_root(command, _timeout):
            captured.append(command)
            if "printf %s " in command:
                encoded = command.split("printf %s ", 1)[1].split(" | base64", 1)[0]
                staged.extend(base64.b64decode(encoded, validate=True))
                stdout = ""
            elif command.startswith("set -eu\nwc -c"):
                stdout = f"{len(staged)} capture.sh\n{hashlib.sha256(staged).hexdigest()}  capture.sh\n"
            else:
                stdout = ""
            return SimpleNamespace(returncode=0), {"exit_code": 0, "timed_out": False,
                                                   "stdout": stdout}

        with mock.patch.object(capture, "root", side_effect=fake_root):
            report = capture.stage_script("fixture", script)
        self.assertEqual(bytes(staged), script)
        self.assertEqual(report["sha256"], hashlib.sha256(script).hexdigest())
        self.assertEqual(report["chunks"], (len(script) + 4095) // 4096)
        self.assertTrue(all(len(command.encode()) <= 8192 for command in captured))
        self.assertIn("closefds()", captured[0])
        self.assertIn("/proc/self/fd/*", captured[0])
        self.assertIn("stat -c '%u:%a'", captured[0])
        self.assertIn("print $3,$5,$6,$22", captured[0])

    def test_detached_launch_fits_actual_controller_contract(self):
        access_source = (capture.ACCESS).read_text()
        controller_max = int(re.search(r"choices=range\(1,\s*(\d+)\)", access_source).group(1)) - 1
        calls = []

        def fake_root(command, timeout):
            calls.append((command, timeout))
            return SimpleNamespace(returncode=0), {
                "exit_code": 0, "timed_out": False, "stdout": "123 456 123 123\n"}

        stage = {"path": capture.STAGE_ROOT + "/fixture/capture.sh", "bytes": 14000,
                 "sha256": "a" * 64}
        with mock.patch.object(capture, "root", side_effect=fake_root):
            report = capture.launch_collector("fixture", stage, 123.456)
        command, timeout = calls[0]
        self.assertLessEqual(timeout, controller_max)
        self.assertLessEqual(len(command.encode()), 8192)
        self.assertIn("exec /usr/bin/setsid /bin/sh", command)
        self.assertIn(f'/bin/sh -c "$(cat {stage["path"]})" -- 123.456', command)
        self.assertNotIn(f"/bin/sh {stage['path']}", command)
        self.assertIn("ulimit -Sf 64", command)
        self.assertIn("/proc/self/fd/*", command)
        self.assertIn("collector.pid", command)
        self.assertEqual(report["process_group"], 123)
        with mock.patch.object(capture, "root", return_value=(SimpleNamespace(returncode=0), {
                "exit_code": 0, "timed_out": False, "stdout": "123 456 99 123\n"})):
            with self.assertRaisesRegex(ValueError, "group/session"):
                capture.launch_collector("fixture", stage, 123.456)

    def test_launch_root_audit_is_persisted_before_result_validation(self):
        response = {"authenticated": True, "uid": 0, "euid": 0,
                    "model": capture.MODEL, "root_persistence": "host-assisted",
                    "global_system_files_unchanged_at_acquisition": True,
                    "commands": [{"exit_code": 41, "timed_out": False,
                                  "stdout": "launch-out\n", "stderr": "launch-error\n"}]}
        proc = SimpleNamespace(returncode=0, stdout=json.dumps(response),
                               stderr="client-error\n")
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(subprocess, "run", return_value=proc):
            prefix = Path(directory) / "launch"
            _proc, item = capture.root("true", 1, prefix)
            self.assertEqual(item["exit_code"], 41)
            self.assertEqual((Path(directory) / "launch-root-response.json").read_text(),
                             json.dumps(response))
            self.assertEqual((Path(directory) / "launch-client-stderr.txt").read_text(),
                             "client-error\n")
            self.assertEqual((Path(directory) / "launch-remote-stdout.txt").read_text(),
                             "launch-out\n")
            self.assertEqual((Path(directory) / "launch-remote-stderr.txt").read_text(),
                             "launch-error\n")
            for path in Path(directory).iterdir():
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_setsid_identity_wait_handles_actual_local_scheduling(self):
        model = r'''set -eu
closefds() { for f in /proc/self/fd/*; do n=${f##*/}; case "$n" in 0|1|2) ;; *) eval "exec $n>&-" 2>/dev/null || true;; esac; done; }
for round in 1 2 3 4 5 6 7 8 9 10; do
 (closefds; exec /usr/bin/setsid /bin/sh -c 'sleep 2') >/dev/null 2>&1 </dev/null &
 p=$!; s=$(awk '{print $22}' /proc/$p/stat); ready=0
 for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  set -- $(awk '{print $3,$5,$6,$22}' /proc/$p/stat 2>/dev/null)
  test "${4:-}" = "$s" || break; test "${1:-}" != Z || break
  if test "${2:-}" = "$p" && test "${3:-}" = "$p"; then ready=1; break; fi
  sleep .05
 done
 test "$ready" = 1
 set -- $(awk '{print $3,$5,$6,$22}' /proc/$p/stat)
 test "$4" = "$s"; test "$2" = "$p"; test "$3" = "$p"
 kill -TERM -"$p"
 wait "$p" 2>/dev/null || true
 for i in 1 2 3 4 5 6 7 8 9 10; do kill -0 -"$p" 2>/dev/null || break; sleep .05; done
 ! kill -0 -"$p" 2>/dev/null
done'''
        subprocess.run(["/bin/bash", "-c", model], check=True, timeout=10)

    def test_owned_group_kills_child_after_leader_exits_on_term(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / "ready"
            leader = subprocess.Popen(
                ["/usr/bin/setsid", "/bin/bash", "-c",
                 "trap 'exit 0' TERM; /bin/bash -c 'trap \"\" TERM; "
                 "printf ready >\"$READY\"; exec sleep 20' & wait"],
                env={**os.environ, "READY": str(ready)},
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 2
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(ready.exists())
                self.assertEqual(os.getpgid(leader.pid), leader.pid)
                self.assertEqual(os.getsid(leader.pid), leader.pid)
                start_ticks = Path(f"/proc/{leader.pid}/stat").read_text().split()[21]
                model = r'''set -eu
p=$P; s=$S
guardpg() { set -- $(awk '{print $3,$5,$6,$22}' /proc/$p/stat 2>/dev/null); test "${4:-}" = "$s" && test "${1:-}" != Z && test "${2:-}" = "$p" && test "${3:-}" = "$p"; }
group_active() { for f in /proc/[0-9]*/stat; do row=; { IFS= read -r row <"$f"; } 2>/dev/null || continue; rest=${row##*) }; set -- $rest; test "${1:-Z}" != Z && test "${3:-}" = "$p" && return 0; done; return 1; }
guardpg
kill -TERM -"$p"
continuous=1
for i in 1 2 3 4 5; do group_active || { continuous=0; break; }; sleep .1; done
test "$continuous" = 1
! guardpg
group_active
kill -KILL -"$p"
for i in 1 2 3 4 5 6 7 8 9 10; do group_active || break; sleep .1; done
! group_active'''
                subprocess.run(["/bin/bash", "-c", model], check=True, timeout=5,
                               env={**os.environ, "P": str(leader.pid), "S": start_ticks})
                leader.wait(timeout=2)
            finally:
                try:
                    os.killpg(leader.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    leader.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    leader.kill()

    def test_no_active_or_global_trace_operations(self):
        forbidden = [r"dbus-send", r"SetPanel", r"GetQD", r"\bioctl\s+", r"reboot",
                     r"poweroff", r"systemctl", r"\bservice\s", r"killall", r"pkill",
                     r"input key", r"rm\s+-r", r"of=/proc/.+/mem"]
        for pattern in forbidden:
            self.assertNotRegex(self.shell, pattern)
        self.assertNotRegex(self.shell, r">\s*['\"]?/sys/kernel/debug/tracing/(?!instances/)")
        self.assertIn('"--persistent-only"', self.source)
        self.assertNotIn("fallback", self.source.lower())
        self.assertIn("exec /usr/bin/setsid /bin/sh", self.source)

    def test_trace_scope_resource_and_lifecycle_contract(self):
        for item in ("adapter_nr == 5 && addr == 118", "crtc == 1", "id == 54",
                     "buffer_total_size_kb", 'test "$bt" -le 16384',
                     "ulimit -f 65536", "ulimit -f 131072", "ulimit -f 256",
                     "MemAvailable", "df -Pk", "watchdog.pid", "vlog.pid"):
            self.assertIn(item, self.shell)
        self.assertNotRegex(self.shell, r"id\s*==\s*29")
        self.assertIn("common_pid == $q", self.shell)
        self.assertIn("@@ TIDS_PRE", self.shell)
        self.assertEqual(self.shell.count('echo "$sf" >"$T/events/raw_syscalls/'), 2)
        self.assertLess(self.shell.index(f"sha256sum {capture.AVOC_PATH}"),
                        self.shell.index("dd if=/proc/$3/mem"))
        for expected in capture.TRACE_CONFIG_EXPECTED:
            self.assertIn(expected, self.shell)
        self.assertIn("sched/sched_process_fork", self.shell)
        self.assertIn('grep -qx record-tgid "$T/trace_options"', self.shell)
        self.assertIn("@@ TIDS_ARM", self.shell)
        self.assertIn("stat -c '%u:%a' \"$SD/expiry.pid\"", self.shell)
        self.assertIn("print $3,$5,$6,$22", self.shell)
        self.assertIn("enlightenment_info -frender all || exit 76", self.shell)
        ordered = ["sched/sched_process_fork sched/sched_process_exit",
                   "tids_pre=$(tids)",
                   'echo "$sf" >"$T/events/raw_syscalls/sys_enter/filter"',
                   'echo 1 >"$T/tracing_on"',
                   "tids_arm=$(tids)",
                   'echo "CAPTURE_START utc=$st uptime=$ts"']
        locations = [self.shell.index(value) for value in ordered]
        self.assertEqual(locations, sorted(locations))

    def test_exact_sampling_allowlist_rejects_substitutions(self):
        function = next(line for line in self.shell.splitlines()
                        if line.startswith("sampleok()"))
        model = f'''set -eu
A=268435456; G=268435500; P=268435600; I=268436000; D=536870912
DG=536871000; EP=536872000; OP=536873000; EC=536874000; ET=536875000; EA=536876000
am=/proc/7/maps; ap=7; dm=/proc/8/maps; dp=8
{function}
sampleok $((A+0x5bfc5c)) 38 "$am" "$ap"
! sampleok $((A+0x5bfc5c+4)) 38 "$am" "$ap"
! sampleok $((A+0x5bfc5c)) 37 "$am" "$ap"
! sampleok $((A+0x5bfc5c)) 38 "$am" 9
sampleok "$DG" 6 "$dm" "$dp"
! sampleok "$DG" 5 "$dm" "$dp"'''
        subprocess.run(["/bin/bash", "-c", model], check=True)

    def test_remote_map_guard_rejects_unaligned_or_zero_ranges(self):
        function = next(line for line in self.shell.splitlines()
                        if line.startswith("mapok()"))
        with tempfile.TemporaryDirectory() as directory:
            maps = Path(directory) / "maps"
            maps.write_text("00001000-00002000 r--p 00000000 00:00 0 fixture\n")
            model = f'''set -u
{function}
set +e
mapok 4096 4 {maps}; r0=$?
mapok 4097 4 {maps}; r1=$?
mapok 0 4 {maps}; r2=$?
mapok 4096 0 {maps}; r3=$?
mapok 4096 2 {maps}; r4=$?
mapok 8192 4 {maps}; r5=$?
set -e
test "$r0:$r1:$r2:$r3:$r4:$r5" = 0:1:1:1:1:1'''
            subprocess.run(["/bin/bash", "-c", model], check=True)

    def test_cleanup_residue_is_not_masked_and_downgrades_classification(self):
        calls = []
        with mock.patch.object(capture, "root", side_effect=lambda command, timeout:
                               (calls.append((command, timeout)) or
                                (SimpleNamespace(returncode=0), {"exit_code": 0,
                                 "timed_out": False, "stdout": "0\nCLEAN\n"}))):
            capture.cleanup_remote("fixture")
        command = calls[0][0]
        self.assertLess(command.index('status=0; test ! -e "$T"'), command.index("echo CLEAN"))
        self.assertIn("echo RESIDUE; exit 54", command)
        record = {"accepted": True, "technical_capture_complete": True,
                  "diagnostic_eligible": True}
        capture.mark_cleanup_failure(record, RuntimeError("residue"))
        self.assertFalse(record["accepted"])
        self.assertFalse(record["technical_capture_complete"])
        self.assertFalse(record["diagnostic_eligible"])
        interrupted = {"accepted": False}
        capture.mark_acquisition_failure(interrupted, KeyboardInterrupt())
        self.assertEqual(interrupted["error"], "KeyboardInterrupt: ")

    def test_monotonic_bounds_and_modes(self):
        self.assertIn('/proc/uptime)', self.shell)
        self.assertNotIn('while test "$(date', self.shell)
        self.assertIn("--start-from=", self.shell)
        self.assertIn("--end-to=", self.shell)
        short = capture.build_remote_script("smoke", 5, allow_short=True)
        self.assertIn("-v n=5", short)
        with self.assertRaises(ValueError):
            capture.build_remote_script("smoke", 5)
        with self.assertRaises(ValueError):
            capture.build_remote_script("smoke", 20, allow_short=True)


class MetadataAndSidecarTests(unittest.TestCase):
    def test_metadata_contract_and_identity_change(self):
        fixture = metadata_fixture()
        report = capture.validate_metadata(fixture, 123, "a" * 64, 85)
        self.assertEqual(report["trace_filter"], capture.syscall_filter_for_tids([7, 11]))
        self.assertEqual(report["trace_filter_tids"], [7, 11])
        changed = fixture.replace("@@ AVOC_ID_END\n7\n", "@@ AVOC_ID_END\n9\n")
        with self.assertRaisesRegex(ValueError, "identity changed"):
            capture.validate_metadata(changed, 123, "a" * 64, 85)
        changed = fixture.replace("events/i2c/i2c_write/enable=1",
                                  "events/i2c/i2c_write/enable=0")
        with self.assertRaisesRegex(ValueError, "readback"):
            capture.validate_metadata(changed, 123, "a" * 64, 85)
        changed = fixture.replace("SYSCALL_EXIT_FILTER=" + capture.syscall_filter_for_tids([7, 11]),
                                  "SYSCALL_EXIT_FILTER=" + capture.syscall_filter_for_tids([7, 12]))
        with self.assertRaisesRegex(ValueError, "syscall filters"):
            capture.validate_metadata(changed, 123, "a" * 64, 85)
        changed = fixture.replace(
            "@@ AVOC_MAPS_END\n10000000-11000000 r--p 00000000 00:00 0 /prd/usr/lib/libave.so.0.1",
            "@@ AVOC_MAPS_END\n10000000-11001000 r--p 00000000 00:00 0 /prd/usr/lib/libave.so.0.1")
        with self.assertRaisesRegex(ValueError, "maps changed"):
            capture.validate_metadata(changed, 123, "a" * 64, 85)

    def test_metadata_rejects_bad_sync_and_missing_tail(self):
        fixture = metadata_fixture()
        stepped = fixture.replace("@@ SYNC_END\n1100\n200.00", "@@ SYNC_END\n1200\n200.00")
        with self.assertRaisesRegex(ValueError, "anchors disagree"):
            capture.validate_metadata(stepped, 123, "a" * 64, 85)
        short = fixture.replace("105.200 190.200", "105.200 164.200")
        with self.assertRaisesRegex(ValueError, "capture/vlog window"):
            capture.validate_metadata(short, 123, "a" * 64, 85)
        under_85 = fixture.replace("105.200 190.200", "105.200 190.190")
        with self.assertRaisesRegex(ValueError, "capture/vlog window"):
            capture.validate_metadata(under_85, 123, "a" * 64, 85)
        artifact_failed = fixture.replace("0 0 0 0 0 0\n@@ AVOC_ID_END",
                                          "0 0 0 0 0 76\n@@ AVOC_ID_END")
        with self.assertRaisesRegex(ValueError, "export failed"):
            capture.validate_metadata(artifact_failed, 123, "a" * 64, 85)

    def test_manifest_integrity_short_and_overflow(self):
        bodies = {name: ((name + "\n").encode() if name != "sample-errors" else b"")
                  for name in capture.SIDECAR_LIMITS}
        rows = [f"SIDECAR {name} {len(body)} {hashlib.sha256(body).hexdigest()}"
                for name, body in bodies.items()]
        manifest = capture.parse_manifest("\n".join(rows + ["CAPTURE_COMPLETE"]) + "\n")
        capture.verify_sidecars(bodies, manifest)
        broken = dict(bodies); broken["meta"] += b"x"
        with self.assertRaisesRegex(ValueError, "length mismatch"):
            capture.verify_sidecars(broken, manifest)
        with self.assertRaisesRegex(ValueError, "missing sidecar"):
            capture.parse_manifest(rows[0] + "\nCAPTURE_COMPLETE\n")
        too_big = rows.copy()
        too_big[0] = f"SIDECAR trace {capture.SIDECAR_LIMITS['trace'] + 1} {'0'*64}"
        with self.assertRaisesRegex(ValueError, "size limit"):
            capture.parse_manifest("\n".join(too_big + ["CAPTURE_COMPLETE"]) + "\n")

    def test_tid_and_fd_stability(self):
        stable = "@@ TIDS_START\n7\n11\n@@ FDS_START\n3 /dev/null\n4 socket:[1]\n@@ TIDS_PRE\n7\n11\n@@ TIDS_ARM\n7\n11\n@@ TIDS_END\n7\n11\n@@ FDS_END\n3 /dev/null\n4 socket:[2]\n"
        report = capture.parse_fds(stable)
        self.assertFalse(report["fd_targets_stable"])
        self.assertEqual(report["fd_changes"]["4"]["end"], "socket:[2]")
        capture.validate_trace_scope(
            {"trace_filter_tids": [7, 11],
             "trace_filter": capture.syscall_filter_for_tids([7, 11])}, report)
        with self.assertRaisesRegex(ValueError, "completeness filter"):
            capture.validate_trace_scope(
                {"trace_filter_tids": [7, 12],
                 "trace_filter": capture.syscall_filter_for_tids([7, 12])}, report)
        with self.assertRaisesRegex(ValueError, "TID set changed"):
            capture.parse_fds(stable.replace("@@ TIDS_END\n7\n11", "@@ TIDS_END\n7\n12"))
        with self.assertRaisesRegex(ValueError, "TID set changed"):
            capture.parse_fds(stable.replace("@@ TIDS_ARM\n7\n11", "@@ TIDS_ARM\n7\n12"))
        with self.assertRaisesRegex(ValueError, "TID set changed"):
            capture.parse_fds(stable.replace("@@ TIDS_PRE\n7\n11", "@@ TIDS_PRE\n7\n12"))


class TraceTests(unittest.TestCase):
    def test_actual_hex_marker_source_and_collector_identity(self):
        rows = [
            "              sh-28455   (  28455) [001] .... 10.000000: "
            "0xffffffc01017095c: CAPTURE_START utc=1000 uptime=10.000\n",
            "              sh-28455   (  28455) [001] .... 11.000000: "
            "0xffffffc01017095c: CAPTURE_END utc=1001 uptime=11.000\n",
        ]
        report = capture.trace_accounting(trace(rows), [7], 7, 28455, 10, 11)
        self.assertEqual([row["trace_source"] for row in report["markers"]],
                         ["0xffffffc01017095c", "0xffffffc01017095c"])
        for changed, message in (
                ([rows[0].replace("sh-28455", "sh-28456"), rows[1]], "collector identity"),
                ([rows[0].replace("(  28455)", "(  28456)"), rows[1]], "collector identity"),
                ([rows[0], rows[1].replace("0xffffffc01017095c",
                                           "0xffffffc01017095d")], "sources differ"),
                ([rows[0], rows[0], rows[1]], "missing/duplicate"),
                ([rows[0].replace("CAPTURE_START", "CAPTURE_STARTX"), rows[1]],
                 "malformed capture")):
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                capture.trace_accounting(trace(changed), [7], 7, 28455, 10, 11)

    def test_exact_markers_ioctl_pair_and_window_exclusion(self):
        outside1 = [event(7, 9.8, "sys_enter", "NR 54 (1, 2, 3)"),
                    event(7, 9.9, "sys_exit", "NR 54 = 0")]
        inside = [event(7, 10.2, "sys_enter", "NR 54 (1, 2, 3)"),
                  event(7, 10.3, "sys_exit", "NR 54 = -1"),
                  event(9, 10.4, "i2c_write", "i2c-5 #0 a=076 f=0000 l=1 [00]")]
        outside2 = [event(7, 11.1, "sys_enter", "NR 54 (4)"),
                    event(7, 11.2, "sys_exit", "NR 54 = 0")]
        report = capture.trace_accounting(good_trace(outside1, inside, outside2), [7], 7, 7, 10, 11)
        self.assertEqual(len(report["ioctl_pairs"]), 1)
        self.assertEqual(report["excluded_ioctl_pairs"], 2)
        self.assertEqual(report["capture_window_i2c_raw_lines"], 1)
        self.assertIn("raw line inventory only", report["qualification"])

    def test_unrelated_syscall54_boundary_rows_reported_and_inside_rejected(self):
        before = [event(40, 9.6, "sys_enter", "NR 54 (0)", tgid=400),
                  event(40, 9.7, "sys_exit", "NR 54 = 0", tgid=400),
                  event(41, 9.8, "sys_exit", "NR 54 = 0", tgid=401)]
        inside = []
        after = [event(60, 11.1, "sys_enter", "NR 54 (2)", tgid=600)]
        report = capture.trace_accounting(good_trace(before, inside, after), [7], 7, 7, 10, 11)
        self.assertEqual(report["unrelated_syscall54_pairs"], 0)
        self.assertEqual(len(report["boundary_unmatched_syscall54_rows"]), 2)
        self.assertEqual(report["ioctl_pairs"], [])
        unrelated = [event(50, 10.2, "sys_enter", "NR 54 (1)", tgid=500),
                     event(50, 10.3, "sys_exit", "NR 54 = 0", tgid=500)]
        with self.assertRaisesRegex(ValueError, "unrelated saved-TGID"):
            capture.trace_accounting(good_trace(extra_inside=unrelated), [7], 7, 7, 10, 11)
        ambiguity_cases = [
            good_trace(extra_inside=[event(50, 10.2, "sys_exit", "NR 54 = 0", tgid=500)]),
            good_trace(extra_inside=[event(50, 10.2, "sys_enter", "NR 54 (1)", tgid=500)]),
            good_trace([event(50, 9.9, "sys_enter", "NR 54 (1)", tgid=500)],
                       [event(50, 10.2, "sys_exit", "NR 54 = 0", tgid=500)]),
        ]
        for data in ambiguity_cases:
            with self.subTest(), self.assertRaisesRegex(ValueError, "unrelated saved-TGID/PID"):
                capture.trace_accounting(data, [7], 7, 7, 10, 11)

    def test_ring_overflow_and_decode_short(self):
        good = good_trace()
        with self.assertRaisesRegex(ValueError, "overflow"):
            capture.trace_accounting(good.replace(b"2/2", b"2/3"), [7], 7, 7, 10, 11)
        with self.assertRaisesRegex(ValueError, "decode count"):
            capture.trace_accounting(good.replace(b"2/2", b"3/3"), [7], 7, 7, 10, 11)

    def test_syscall_pair_failures(self):
        cases = [
            ([event(7, 10.2, "sys_enter", "NR 29 (1)"),
              event(7, 10.3, "sys_exit", "NR 29 = 0")], "unexpected syscall enter"),
            ([event(7, 10.2, "sys_enter", "NR 54 (1)"),
              event(7, 10.3, "sys_exit", "NR 53 = 0")], "unexpected syscall exit"),
            ([event(7, 10.2, "sys_exit", "NR 54 = 0")], "orphan"),
            ([event(7, 10.2, "sys_enter", "NR 54 (1)"),
              event(7, 10.3, "sys_enter", "NR 54 (2)")], "duplicate"),
        ]
        for rows, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                capture.trace_accounting(good_trace(extra_inside=rows), [7], 7, 7, 10, 11)

    def test_transient_avoc_thread_is_rejected(self):
        fork = event(7, 10.4, "sched_process_fork",
                     "comm=avocd pid=7 child_comm=worker child_pid=12")
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            capture.trace_accounting(good_trace(extra_inside=[fork]), [7, 11], 7, 7, 10, 11)
        before = event(7, 9.9, "sched_process_fork",
                       "comm=avocd pid=7 child_comm=worker child_pid=12")
        child_ioctl = [event(12, 10.2, "sys_enter", "NR 54 (1)"),
                       event(12, 10.3, "sys_exit", "NR 54 = 0")]
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            capture.trace_accounting(good_trace([before]), [7, 11], 7, 7, 10, 11)
        with self.assertRaisesRegex(ValueError, "unrelated saved-TGID/PID"):
            capture.trace_accounting(good_trace([before], child_ioctl), [7, 11], 7, 7,
                                     10, 11)
        after_exit = event(7, 11.1, "sched_process_exit", "comm=avocd pid=7 prio=120")
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            capture.trace_accounting(good_trace(extra_after=[after_exit]), [7, 11], 7, 7,
                                     10, 11)

    def test_marker_reversal_crossing_and_i2c_scope_rejected(self):
        reversed_rows = [event(7, 10, "tracing_mark_write", "CAPTURE_END utc=1000 uptime=10.000"),
                         event(7, 11, "tracing_mark_write", "CAPTURE_START utc=1001 uptime=11.000")]
        with self.assertRaisesRegex(ValueError, "markers"):
            capture.trace_accounting(trace(reversed_rows), [7], 7, 7, 10, 11)
        crossing = good_trace([event(7, 9.9, "sys_enter", "NR 54 (1)")],
                              [event(7, 10.2, "sys_exit", "NR 54 = 0")])
        with self.assertRaisesRegex(ValueError, "crosses"):
            capture.trace_accounting(crossing, [7], 7, 7, 10, 11)
        wrong_i2c = good_trace(extra_inside=[
            event(9, 10.4, "i2c_write", "i2c-4 #0 a=075 f=0000 l=1 [00]")])
        with self.assertRaisesRegex(ValueError, "I2C"):
            capture.trace_accounting(wrong_i2c, [7], 7, 7, 10, 11)
        truncated = good_trace(extra_inside=[
            event(9, 10.4, "i2c_write", "i2c-5 #0 a=076 f=0000 l=6 [f3-01]")])
        with self.assertRaisesRegex(ValueError, "I2C"):
            capture.trace_accounting(truncated, [7], 7, 7, 10, 11)
        bad_separator = good_trace(extra_inside=[
            event(9, 10.4, "i2c_write", "i2c-5 #0 a=076 f=0000 l=2 [f3--01]")])
        with self.assertRaisesRegex(ValueError, "I2C"):
            capture.trace_accounting(bad_separator, [7], 7, 7, 10, 11)


class SampleAndVlogTests(unittest.TestCase):
    def test_samples_rates_endpoints_and_pointer_guards(self):
        meta = {"pointers": POINTERS, "trace_start": 10.0, "trace_end": 15.0}
        report = capture.analyze_samples(sample_text(10, 15), meta, 5)
        self.assertGreater(report["monitor_rate_hz"], 4.5)
        self.assertGreater(report["qd_rate_hz"], .9)
        bad = sample_text(10, 15).replace(b64([POINTERS[12]]), b64([0xDEAD]), 1)
        with self.assertRaisesRegex(ValueError, "child/vptr"):
            capture.analyze_samples(bad, meta, 5)
        with self.assertRaisesRegex(ValueError, "outside"):
            capture.analyze_samples(sample_text(10, 15).replace("M|10.100", "M|nan", 1), meta, 5)

    def test_26_second_missing_tail_is_rejected(self):
        meta = {"pointers": POINTERS, "trace_start": 100.0, "trace_end": 185.0}
        monitors = [f"M|{100.1 + i * .2:.3f}|{b64([0] * 38)}" for i in range(297)]
        qds = [qrow(100.1 + i) for i in range(59)]
        with self.assertRaisesRegex(ValueError, "endpoint coverage"):
            capture.analyze_samples("\n".join(monitors + qds) + "\n", meta, 85)

    def test_dd_success_inventory_and_injected_error(self):
        good = dd_stderr(25, 5)
        report = capture.validate_dd_summaries(good, 25, 5)
        self.assertTrue(report["only_complete_success_summaries"])
        with self.assertRaisesRegex(ValueError, "shape|diagnostic"):
            capture.validate_dd_summaries(good + "dd: error reading '/proc/7/mem'\n", 25, 5)
        with self.assertRaisesRegex(ValueError, "inventory"):
            capture.validate_dd_summaries(good, 24, 5)

    def test_actual_vlog_format_and_footer_exclusion(self):
        fixture = json.loads((HERE / "vlogutil-kerneltime-format-20261026T150016Z.json").read_text())
        raw = fixture["response"]["commands"][0]["stdout"].encode()
        report = capture.vlog_coverage(raw, 48421.831, 48423.827, margin=0)
        self.assertEqual(report["records"], 6327)
        self.assertEqual((report["first"], report["last"]), (48421.831, 48423.827))
        self.assertTrue(report["complete"])
        self.assertFalse(report["absence_claim_supported"])

    def test_vlog_gap_order_endpoint_and_termination(self):
        gap = b" a: 98.000 I/TAG (P1,T1): x\n b: 112.000 I/TAG (P1,T1): y\n"
        report = capture.vlog_coverage(gap, 100, 110)
        self.assertFalse(report["complete"])
        self.assertFalse(report["absence_claim_supported"])
        unordered = b" a: 99.000 I/TAG (P1,T1): x\n b: 98.000 I/TAG (P1,T1): y\n c: 111.000 I/TAG (P1,T1): z\n"
        self.assertFalse(capture.vlog_coverage(unordered, 100, 110)["ordered"])
        dense = b" a: 99.000 I/TAG (P1,T1): x\n b: 100.000 I/TAG (P1,T1): y\n c: 111.000 I/TAG (P1,T1): z\n"
        self.assertFalse(capture.vlog_coverage(dense, 100, 110, forced_termination=True)["complete"])
        self.assertFalse(capture.vlog_coverage(b"header [99.0] End", 100, 110)["complete"])


class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.sync = {"tv_uptime": 100.0, "host_midpoint_utc": 1000.0,
                     "host_midpoint_monotonic": 500.0, "mapping_uncertainty_seconds": .1}
        self.meta = {"trace_start": 110.0, "trace_end": 190.0}

    @staticmethod
    def row(text, epoch):
        mono = int((500.0 + epoch - 1000.0) * 1e9)
        return capture.parse_annotation(text, dt.datetime.fromtimestamp(epoch, dt.timezone.utc), mono)

    def test_only_ordered_wholly_in_window_transition_is_eligible(self):
        rows = [self.row("picture visible reaction_ms=100 clock_ms=100", 1020),
                self.row("picture black reaction_ms=100 clock_ms=100", 1030)]
        report = capture.assess_annotations(rows, self.sync, self.meta, False)
        self.assertTrue(report["diagnostic_onset_eligible"])
        self.assertEqual(report["physical_state"], "observer-reported-visible-to-black")
        self.assertFalse(capture.assess_annotations([], self.sync, self.meta, False)["diagnostic_onset_eligible"])
        self.assertFalse(capture.assess_annotations(rows, self.sync, self.meta, True)["diagnostic_onset_eligible"])

    def test_outside_missing_uncertainty_reversed_and_overlap_rejected(self):
        outside = [self.row("picture visible reaction_ms=100 clock_ms=100", 1009),
                   self.row("picture black reaction_ms=100 clock_ms=100", 1030)]
        missing = [self.row("picture visible", 1020), self.row("picture black", 1030)]
        reversed_rows = [self.row("picture black reaction_ms=100 clock_ms=100", 1020),
                         self.row("picture visible reaction_ms=100 clock_ms=100", 1030)]
        overlap = [self.row("picture visible reaction_ms=1000 clock_ms=1000", 1020),
                   self.row("picture black reaction_ms=1000 clock_ms=1000", 1021)]
        for rows in (outside, missing, reversed_rows, overlap):
            with self.subTest(rows=rows):
                self.assertFalse(capture.assess_annotations(
                    rows, self.sync, self.meta, False)["diagnostic_onset_eligible"])

    def test_annotation_ambiguity_and_input_validation(self):
        rows = [capture.parse_annotation("picture visible"),
                capture.parse_annotation("picture black"), capture.parse_annotation("audio present")]
        summary = capture.annotation_summary(rows)
        self.assertEqual(summary["ambiguous_dimensions"]["picture"], ["black", "visible"])
        for line in ("picture off", "warning visible reaction_ms=-1", "apps visible bogus=1", ""):
            with self.assertRaises(ValueError):
                capture.parse_annotation(line)


if __name__ == "__main__":
    unittest.main(verbosity=2)
