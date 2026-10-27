#!/usr/bin/env python3
"""Offline tests for observed-branch-onset-capture.py; never contact the TV."""

import base64
import hashlib
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "observed-branch-onset-capture.py"
FROZEN_TESTS = HERE / "observed-onset-capture-tests.py"
FROZEN_TESTS_SHA256 = "ab6c4307d611d00e886d042ec855a7dbae21e76db65673d039811cc8f5872970"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("module unavailable: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if hashlib.sha256(FROZEN_TESTS.read_bytes()).hexdigest() != FROZEN_TESTS_SHA256:
    raise RuntimeError("frozen observer tests changed")
capture = load("observed_branch_capture", SOURCE)
old = load("frozen_observer_tests_ab6c", FROZEN_TESTS)


def b64(words):
    return base64.b64encode(
        b"".join(int(value).to_bytes(4, "little") for value in words)).decode()


def branch_metadata(script_size=123, script_sha="a" * 64, mutate=None):
    part = old.capture.sections(old.metadata_fixture(script_size, script_sha))
    oldptr = [int(value) for value in part["POINTERS_START"].split()]
    a = oldptr[0]
    backend = 0x10601000
    branchptr = oldptr[:5] + [backend, a + capture.BASE_BACKEND_VPTR,
                              a + capture.BASE_BACKEND_SLOT] + oldptr[5:]
    part["POINTERS_START"] = " ".join(map(str, branchptr))
    part["POINTERS_END"] = part["POINTERS_START"]
    # Distinct offset-zero code, Thumb slot code, vtable/static, and data maps.
    part["AVOC_MAPS_START"] = "\n".join((
        "10000000-10010000 r-xp 00000000 00:00 0 " + capture.AVE_PATH,
        "10100000-10200000 r-xp 00100000 00:00 0 " + capture.AVE_PATH,
        "10500000-10600000 r--p 00500000 00:00 0 " + capture.AVE_PATH,
        "10600000-11000000 rw-p 00600000 00:00 0 " + capture.AVE_PATH))
    part["AVOC_MAPS_END"] = part["AVOC_MAPS_START"]
    part["Q_SAMPLER_HASH_START"] = (
        f"{len(capture.Q_SAMPLER_BYTES)} q-sampler.sh\n"
        f"{capture.Q_SAMPLER_SHA256}  q-sampler.sh")
    part["Q_SAMPLER_HASH_END"] = part["Q_SAMPLER_HASH_START"]
    part["SAMPLERS"] = "monitor 70 700 70 70 q 80 800 80 80"
    if mutate is not None:
        mutate(part, branchptr)
    order = [
        "BUILD", "SCRIPT_HASH_START", "Q_SAMPLER_HASH_START", "BOOT_START",
        "SYNC_START", "AVOC_ID_START", "DEV_ID_START", "POINTERS_START",
        "AVOC_MAPS_START", "DEV_MAPS_START", "GLOBAL_TRACE_START", "TRACE_CONFIG",
        "SAMPLERS", "Q_SAMPLER_HASH_END", "BOOT_END", "SYNC_END",
        "CAPTURE_WINDOW", "AVOC_ID_END", "DEV_ID_END", "POINTERS_END",
        "AVOC_MAPS_END", "DEV_MAPS_END", "SCRIPT_HASH_END", "GLOBAL_TRACE_END",
        "VLOG_SEMANTICS"]
    return "\n".join(f"@@ {name}\n{part[name]}" for name in order) + "\n"


def valid_meta():
    return capture.validate_metadata(branch_metadata(), 123, "a" * 64, 85)


def qrow(start, meta=None, end=None, identity=None, initialized=1, replace=None):
    meta = meta or valid_meta()
    (a, glob, panel, vptr, inner, backend, backend_vptr, backend_slot,
     _d, _dglob, ep, op, ec, et, ea, ecv, etv, eav) = meta["pointers"]
    values = [
        [glob], [panel], [vptr, inner, 0, 0, backend, 0, initialized],
        [backend_vptr], [backend_slot], [236], [1, 236, 236],
        list(range(12)), [1023], [1023, 0], [0], [1], [88], [98],
        [248, 252], [392, 396], [676, 680], [1104], [2],
        [ep, ep + 4, 0, op, op + 4, 0], [2], [0, ec, et, ea], [9],
        [ecv], [etv], [eav]]
    if replace is not None:
        replace(values)
    ident = identity or (f"{meta['avoc_identity'][0]},{meta['avoc_identity'][1]},{a},"
                         f"{meta['deviced_identity'][0]},{meta['deviced_identity'][1]},{_d}")
    finish = start + .4 if end is None else end
    return "|".join(["Q", f"{start:.3f}", ident] +
                    [b64(value) for value in values] + [f"{finish:.3f}"])


def sample_text(meta=None, row_transform=None):
    meta = meta or valid_meta()
    rows = []
    value = meta["trace_start"] + .1
    while value <= meta["trace_end"] - .1 + 1e-8:
        rows.append(f"M|{value:.3f}|{b64([0] * 38)}")
        value += .2
    value = meta["trace_start"] + .1
    index = 0
    while value <= meta["trace_end"] - .1 + 1e-8:
        row = qrow(value, meta)
        rows.append(row_transform(index, value, row) if row_transform else row)
        value += 1.0
        index += 1
    return "\n".join(rows) + "\n"


def dd_stderr(monitor_rows, qd_rows, extra=False):
    counts = {1: 45 + 17 * qd_rows, 2: 4 * qd_rows, 3: qd_rows,
              4: qd_rows, 6: qd_rows, 7: qd_rows, 12: qd_rows,
              38: monitor_rows}
    if extra:
        counts[1] += 1
    rows = []
    for count, operations in counts.items():
        for _ in range(operations):
            size = count * 4
            rows += [f"{count}+0 records in", f"{count}+0 records out",
                     f"{size} bytes ({size} B) copied, 3.1e-05 s, 128 kB/s"]
    return "\n".join(rows) + "\n"


class BranchScopeTests(unittest.TestCase):
    def test_all_generated_shells_are_syntactic_and_namespaced(self):
        hashes = {}
        for seconds, smoke in ((5, True), (10, True), (85, False), (90, False)):
            shell = capture.build_remote_script("fixture", seconds, allow_short=smoke)
            subprocess.run(["sh", "-n"], input=shell, text=True, check=True)
            hashes[seconds] = hashlib.sha256(shell.encode()).hexdigest()
            self.assertIn(capture.REMOTE_ROOT, shell)
            self.assertIn(capture.STAGE_ROOT, shell)
            self.assertIn(capture.TRACE_PREFIX, shell)
            self.assertNotIn(capture.OLD_STAGE_ROOT + "/", shell)
            self.assertNotIn(capture.OLD_TRACE_PREFIX, shell)
        self.assertEqual(len(set(hashes.values())), 4)

    def test_generated_shell_has_hash_bound_owned_sampler_and_fresh_guards(self):
        shell = capture.build_remote_script("fixture", 85)
        subprocess.run(["sh", "-n"], input=capture.q_sampler_script(),
                       text=True, check=True)
        self.assertIn(capture.Q_SAMPLER_SHA256, shell)
        self.assertIn("exec /usr/bin/setsid /bin/sh", shell)
        self.assertIn("QREADY=$O/q-ready.tmp", shell)
        self.assertIn('qgroup_active "$qp"', shell)
        self.assertIn('kill -KILL -"$qp"', shell)
        self.assertIn('mapok "$1" $(($2*4)) "$3"', capture.q_sampler_script())
        self.assertIn('test "$(readlink /proc/$ap/exe)" = "$AVOC_PATH"',
                      capture.q_sampler_script())
        self.assertIn('(ulimit -f 2048; cat "$QF" >>"$S")', shell)
        self.assertIn('(ulimit -f 256; cat "$QE" >>"$E")', shell)
        self.assertNotIn("0x5a094c", shell)
        for forbidden in (r"dbus-send", r"SetPanel", r"GetQD", r"\bioctl\s+",
                          r"reboot", r"poweroff", r"systemctl", r"\bservice\s",
                          r"killall", r"pkill", r"input key", r"of=/proc/.+/mem"):
            self.assertNotRegex(shell, forbidden)
        self.assertNotRegex(shell,
                            r">\s*['\"]?/sys/kernel/debug/tracing/(?!instances/)")

    def test_transformed_root_commands_stay_under_controller_ceiling(self):
        script = capture.build_remote_script("fixture", 5, allow_short=True).encode()
        calls, staged = [], bytearray()

        def fake_root(command, _timeout, audit_prefix=None):
            calls.append(command)
            if "printf %s " in command:
                encoded = command.split("printf %s ", 1)[1].split(" | base64", 1)[0]
                staged.extend(base64.b64decode(encoded, validate=True))
                stdout = ""
            elif "wc -c " in command and "capture.sh" in command:
                stdout = (f"{len(staged)} capture.sh\n"
                          f"{hashlib.sha256(staged).hexdigest()}  capture.sh\n")
            else:
                stdout = ""
            return SimpleNamespace(returncode=0), {
                "exit_code": 0, "timed_out": False, "stdout": stdout, "stderr": ""}

        with mock.patch.object(capture, "_ORIGINAL_ROOT", side_effect=fake_root):
            capture.stage_script("fixture", script)
        self.assertEqual(bytes(staged), script)
        self.assertTrue(calls)
        self.assertLessEqual(max(len(command.encode()) for command in calls), 8192)
        self.assertTrue(all(capture.OLD_STAGE_ROOT not in command for command in calls))

    def test_default_is_dry_and_contains_no_control_operation(self):
        proc = subprocess.run(
            ["python3", str(SOURCE), "fixture", "--seconds", "5", "--smoke-unobserved"],
            text=True, capture_output=True, check=True)
        self.assertIn("dry-run; no TV/network/root call", proc.stdout)
        source = SOURCE.read_text()
        for forbidden in ("send_key", "sdb", "reboot", "systemctl", "factory-set"):
            self.assertNotIn(forbidden, source)

    def test_quiesce_and_cleanup_stop_q_sampler_before_collector(self):
        calls = []

        def fake_root(command, timeout, audit_prefix=None):
            calls.append(command)
            return SimpleNamespace(returncode=0), {
                "exit_code": 0, "timed_out": False, "stdout": "QUIESCED\n"
                if "QUIESCED" in command else "CLEAN\n", "stderr": ""}

        with mock.patch.object(capture, "_ORIGINAL_ROOT", side_effect=fake_root):
            capture.quiesce_remote("fixture")
            capture.cleanup_remote("fixture")
        self.assertEqual(len(calls), 2)
        for command in calls:
            self.assertLess(command.index('stopone "$O/q-sampler.pid"'),
                            command.index('stopone "$SD/collector.pid"'))
        self.assertIn("q-sampler.sh", calls[1])

    def test_parent_cat_can_append_more_than_inherited_64k(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            target = Path(directory) / "target"
            source.write_bytes(b"x" * 100_000)
            subprocess.run(
                ["/bin/bash", "-c",
                 'ulimit -Sf 64; (ulimit -f 2048; cat "$1" >>"$2")',
                 "--", str(source), str(target)], check=True)
            self.assertEqual(target.stat().st_size, 100_000)

    def test_q_ready_group_escalates_only_from_valid_leader(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / "q-ready"
            leader = subprocess.Popen(
                ["/usr/bin/setsid", "/bin/bash", "-c",
                 "row=$(cat /proc/$$/stat); rest=${row##*) }; set -- $rest; "
                 "test \"$3\" = \"$$\"; test \"$4\" = \"$$\"; "
                 "printf '%s %s\\n' \"$$\" \"${20}\" >\"$READY\"; "
                 "trap 'exit 0' TERM; /bin/bash -c 'trap \"\" TERM; exec sleep 20' & wait"],
                env={**os.environ, "READY": str(ready)}, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 2
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(ready.exists())
                pid, start = ready.read_text().split()
                self.assertEqual(int(pid), leader.pid)
                model = r'''set -eu
p=$P; s=$S
p4() { row=; IFS= read -r row <"/proc/$1/stat"; rest=${row##*) }; set -- $rest; test "$#" -ge 20; printf '%s %s %s %s\n' "$1" "$3" "$4" "${20}"; }
guardpg() { set -- $(p4 "$p"); test "$4" = "$s"; test "$1" != Z; test "$2" = "$p"; test "$3" = "$p"; }
group_active() { for f in /proc/[0-9]*/stat; do row=; { IFS= read -r row <"$f"; } 2>/dev/null || continue; rest=${row##*) }; set -- $rest; test "${1:-Z}" != Z && test "${3:-}" = "$p" && return 0; done; return 1; }
guardpg
! ( s=999999; guardpg )
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
                               env={**os.environ, "P": pid, "S": start})
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


class BranchMetadataTests(unittest.TestCase):
    def test_valid_metadata_binds_base_qd_backend_and_sampler(self):
        report = valid_meta()
        self.assertEqual(report["qd_class"], "QDDimming")
        self.assertEqual(report["backend_class"], "DimmingBackendRoseMQD")
        self.assertEqual(report["q_sampler_data"]["sha256"], capture.Q_SAMPLER_SHA256)
        self.assertNotEqual(report["sampler_identities"]["monitor"]["pid"],
                            report["sampler_identities"]["qd_branch"]["pid"])

    def test_mnt_and_untyped_backend_rejected(self):
        def mnt(part, pointers):
            pointers[3] = pointers[0] + 0x5A094C
            part["POINTERS_START"] = part["POINTERS_END"] = " ".join(map(str, pointers))
        with self.assertRaisesRegex(ValueError, "exact base QDDimming"):
            capture.validate_metadata(branch_metadata(mutate=mnt), 123, "a" * 64, 85)

        def backend(part, pointers):
            pointers[6] += 4
            part["POINTERS_START"] = part["POINTERS_END"] = " ".join(map(str, pointers))
        with self.assertRaisesRegex(ValueError, "typed DimmingBackend"):
            capture.validate_metadata(branch_metadata(mutate=backend), 123, "a" * 64, 85)

    def test_sampler_hash_and_group_identity_rejected(self):
        def badhash(part, _p):
            part["Q_SAMPLER_HASH_END"] = part["Q_SAMPLER_HASH_END"].replace(
                capture.Q_SAMPLER_SHA256, "0" * 64)
        with self.assertRaisesRegex(ValueError, "DATA identity"):
            capture.validate_metadata(branch_metadata(mutate=badhash), 123, "a" * 64, 85)

        def badgroup(part, _p):
            part["SAMPLERS"] = "monitor 70 700 71 70 q 80 800 80 80"
        with self.assertRaisesRegex(ValueError, "sampler PID"):
            capture.validate_metadata(branch_metadata(mutate=badgroup), 123, "a" * 64, 85)

    def test_backend_slot_requires_executable_source_map(self):
        def noexec(part, _p):
            part["AVOC_MAPS_START"] = part["AVOC_MAPS_START"].replace(
                "10100000-10200000 r-xp", "10100000-10200000 r--p")
            part["AVOC_MAPS_END"] = part["AVOC_MAPS_START"]
        with self.assertRaisesRegex(ValueError, "source-backed"):
            capture.validate_metadata(branch_metadata(mutate=noexec), 123, "a" * 64, 85)

    def test_qd_vptr_requires_exact_unique_libave_mapping(self):
        def wrongpath(part, _p):
            part["AVOC_MAPS_START"] = part["AVOC_MAPS_START"].replace(
                "0 /prd/usr/lib/libave.so.0.1", "0 /tmp/not-libave", 1)
            part["AVOC_MAPS_END"] = part["AVOC_MAPS_START"]
        with self.assertRaisesRegex(ValueError, "QDDimming vptr"):
            capture.validate_metadata(branch_metadata(mutate=wrongpath),
                                      123, "a" * 64, 85)

        def duplicate(part, _p):
            part["AVOC_MAPS_START"] += (
                "\n12000000-12001000 r-xp 00000000 00:00 1 " + capture.AVE_PATH)
            part["AVOC_MAPS_END"] = part["AVOC_MAPS_START"]
        with self.assertRaisesRegex(ValueError, "uniquely libave"):
            capture.validate_metadata(branch_metadata(mutate=duplicate),
                                      123, "a" * 64, 85)

        def nonexecbase(part, _p):
            part["AVOC_MAPS_START"] = part["AVOC_MAPS_START"].replace(
                "10000000-10010000 r-xp", "10000000-10010000 r--p")
            part["AVOC_MAPS_END"] = part["AVOC_MAPS_START"]
        with self.assertRaisesRegex(ValueError, "uniquely libave"):
            capture.validate_metadata(branch_metadata(mutate=nonexecbase),
                                      123, "a" * 64, 85)


class BranchSampleTests(unittest.TestCase):
    def setUp(self):
        self.meta = valid_meta()
        self.text = sample_text(self.meta)

    def test_valid_rows_report_rate_spans_and_no_branch_inference(self):
        report = capture.analyze_samples(self.text, self.meta, 85)
        self.assertGreaterEqual(report["monitor_rate_hz"], 3.5)
        self.assertGreaterEqual(report["qd_rate_hz"], .7)
        self.assertLess(report["qd_row_span_seconds"]["max"],
                        capture.ROW_SPAN_MAX_SECONDS)
        self.assertIn("no active branch", report["qualification"])

    def test_row_process_or_load_identity_change_rejected(self):
        bad = sample_text(self.meta, lambda i, value, row:
                          qrow(value, self.meta, identity="7,11,268435456") if i == 2 else row)
        with self.assertRaisesRegex(ValueError, "process/load identity"):
            capture.analyze_samples(bad, self.meta, 85)

    def test_uninitialized_or_rebound_header_rejected(self):
        bad = sample_text(self.meta, lambda i, value, row:
                          qrow(value, self.meta, initialized=0) if i == 1 else row)
        with self.assertRaisesRegex(ValueError, "sampled QD/backend identity"):
            capture.analyze_samples(bad, self.meta, 85)
        bad2 = sample_text(self.meta, lambda i, value, row:
                           qrow(value, self.meta, replace=lambda v: v[2].__setitem__(4, 1))
                           if i == 1 else row)
        with self.assertRaisesRegex(ValueError, "sampled QD/backend identity"):
            capture.analyze_samples(bad2, self.meta, 85)

    def test_overduration_and_boundary_crossing_rows_rejected(self):
        slow = sample_text(self.meta, lambda i, value, row:
                           qrow(value, self.meta, end=value + 2.001) if i == 1 else row)
        with self.assertRaisesRegex(ValueError, "predeclared operational ceiling"):
            capture.analyze_samples(slow, self.meta, 85)
        crossing = sample_text(self.meta, lambda i, value, row:
                               qrow(value, self.meta, end=self.meta["trace_end"] + .001)
                               if i == 84 else row)
        with self.assertRaisesRegex(ValueError, "outside capture window"):
            capture.analyze_samples(crossing, self.meta, 85)

    def test_truncated_malformed_and_extra_rows_rejected(self):
        rows = self.text.splitlines()
        qindex = next(i for i, row in enumerate(rows) if row.startswith("Q|"))
        fields = rows[qindex].split("|")
        fields[4] = base64.b64encode(b"\x00" * 3).decode()
        rows[qindex] = "|".join(fields)
        with self.assertRaisesRegex(ValueError, "short sample"):
            capture.analyze_samples("\n".join(rows) + "\n", self.meta, 85)
        rows = self.text.splitlines()
        rows.append("X|1|bad")
        with self.assertRaisesRegex(ValueError, "QD branch row shape"):
            capture.analyze_samples("\n".join(rows) + "\n", self.meta, 85)

    def test_exact_dd_inventory_and_injected_diagnostic(self):
        report = capture.analyze_samples(self.text, self.meta, 85)
        good = dd_stderr(report["monitor_rows"], report["qd_rows"])
        parsed = capture.validate_dd_summaries(
            good, report["monitor_rows"], report["qd_rows"])
        self.assertTrue(parsed["only_complete_success_summaries"])
        with self.assertRaisesRegex(ValueError, "inventory"):
            capture.validate_dd_summaries(
                dd_stderr(report["monitor_rows"], report["qd_rows"], extra=True),
                report["monitor_rows"], report["qd_rows"])
        with self.assertRaisesRegex(ValueError, "unexpected sampler stderr"):
            capture.validate_dd_summaries(good + "dd: injected failure\n",
                                          report["monitor_rows"], report["qd_rows"])


def load_tests(_loader, _tests, _pattern):
    """Run the exact frozen 35-test suite, then this integration delta."""
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(old))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(BranchScopeTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(BranchMetadataTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(BranchSampleTests))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
