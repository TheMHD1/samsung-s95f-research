#!/usr/bin/env python3
"""Offline tests for the bounded-quiescence PM observer; never contact the TV."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "observed-quiescent-pm-onset-capture.py"
FROZEN_TESTS = HERE / "observed-pm-onset-capture-tests.py"
FROZEN_TESTS_SHA256 = "08dc2d93af4630c308d52ad8f0fe9a8150a95d856f753921f39d0c7186e9dbcd"
FAILED_SMOKE = HERE / "pm-idle-smoke-20261026.onset"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("module unavailable: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if hashlib.sha256(FROZEN_TESTS.read_bytes()).hexdigest() != FROZEN_TESTS_SHA256:
    raise RuntimeError("frozen PM observer tests changed")
capture = load("observed_quiescent_pm", SOURCE)
old = load("frozen_pm_tests_08dc", FROZEN_TESTS)
preroll_tests = old.old


def fds_fixture(attempts=None, mutate=None):
    return preroll_tests.fds_fixture(attempts=attempts, mutate=mutate)


class QuiescentShellTests(unittest.TestCase):
    def test_pinned_parent_design_addendum_and_failed_evidence_are_exact(self):
        pins = ((capture.FROZEN_SOURCE, capture.FROZEN_SHA256),
                (capture.DESIGN, capture.DESIGN_SHA256),
                (capture.ADDENDUM, capture.ADDENDUM_SHA256))
        for path, digest in pins:
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        self.assertEqual(hashlib.sha256(
            (FAILED_SMOKE / "partial-fds.txt").read_bytes()).hexdigest(),
            "75ba03cce48df409ac270420416d40da724a99ad6ff86a6dfd44ec33eeb46bbc")
        record = FAILED_SMOKE / "record.json"
        self.assertEqual(hashlib.sha256(record.read_bytes()).hexdigest(),
                         "247298a3adb37a33ace809438fc6301424c0a3ae5519bca4e59d69b45babfe29")
        body = json.loads(record.read_text())
        self.assertFalse(body["accepted"])
        self.assertFalse(body["technical_capture_complete"])

    def test_all_modes_are_syntactic_private_and_keep_fixed_bounds(self):
        hashes = []
        for seconds, short in ((5, True), (10, True), (85, False), (90, False)):
            shell = capture.build_remote_script("fixture", seconds, allow_short=short)
            subprocess.run(["/bin/sh", "-n"], input=shell, text=True, check=True)
            hashes.append(hashlib.sha256(shell.encode()).hexdigest())
            self.assertIn(capture.REMOTE_ROOT, shell)
            self.assertIn(capture.STAGE_ROOT, shell)
            self.assertIn(capture.TRACE_PREFIX, shell)
            self.assertNotIn(capture.PARENT_REMOTE_ROOT, shell)
            self.assertNotIn(capture.PARENT_STAGE_ROOT, shell)
            self.assertNotIn(capture.PARENT_TRACE_PREFIX, shell)
            self.assertIn('test "$qnr" -eq 54', shell)
            self.assertIn(f'test "$qi" -lt {capture.QUIESCENCE_MAX_ATTEMPTS}', shell)
            self.assertIn(f'sleep {capture.QUIESCENCE_RETRY_SECONDS}', shell)
            self.assertEqual(shell.count('/proc/$ap/task/$qt/syscall'), 1)
            self.assertNotRegex(shell, r"(?:setprop|input keyevent)\s")
        self.assertEqual(len(set(hashes)), 4)

    def test_default_dry_and_both_live_guards_without_transport(self):
        result = subprocess.run(
            [sys.executable, str(SOURCE), "fixture", "--seconds", "5",
             "--smoke-unobserved"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=True)
        body = json.loads(result.stdout)
        self.assertEqual(body["mode"], "dry-run; no TV/network/root call")
        self.assertTrue(body["quiescence"]["numeric_54_is_intermediate_only"])
        self.assertTrue(body["quiescence"]["terminal_numeric_non54_required"])
        self.assertFalse(body["quiescence"]["trace_exit_is_qualification"])
        self.assertFalse(body["absence_claim_supported"])
        with mock.patch.object(capture, "run_capture",
                               side_effect=AssertionError("transport attempted")) as called, \
                mock.patch.object(sys, "argv", [str(SOURCE), "fixture", "--seconds", "5",
                                                 "--smoke-unobserved", "--run"]):
            with self.assertRaisesRegex(ValueError, "--run and --reviewed"):
                capture.main()
        called.assert_not_called()

    def test_emitted_loop_retries_running_and_54_then_requires_non54(self):
        shell = capture.build_remote_script("fixture", 5, allow_short=True)
        start = shell.index("for qt in $tids_arm; do qualified=0")
        loop = shell[start:shell.index("\nqe=", start)]
        original_read = ('if ! IFS= read -r qraw <"/proc/$ap/task/$qt/syscall"; '
                         "then qstatus=read-error; qraw='!read'; fi")
        sequenced_read = ('if ! qraw=$(sed -n "${qi}p" "$FAKE/$qt"); '
                          "then qstatus=read-error; qraw='!read'; fi")
        self.assertEqual(loop.count(original_read), 1)
        loop = loop.replace(original_read, sequenced_read)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake, out = root / "fake", root / "out"
            fake.mkdir(); out.mkdir()
            script = ("set -eu\ntids_arm=7\nap=1\n" + f"FAKE={fake}\nO={out}\n" +
                      "ea=$(cut -d\" \" -f1 /proc/uptime)\n" + loop + "\n")
            cases = (
                ("running\n54 1 2 3 4 5 6 7 8\n54 1 2 3 4 5 6 7 8\n0 0\n", 0),
                (("54 1 2 3 4 5 6 7 8\n" * 8), 86),
                (("running\n" * 8), 84),
                ("54x bad\n", 85),
            )
            for payload, expected in cases:
                with self.subTest(expected=expected):
                    (fake / "7").write_text(payload)
                    result = subprocess.run(["/bin/sh", "-c", script],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, text=True)
                    self.assertEqual(result.returncode, expected, result.stderr)
            attempts = (out / "fds.txt").read_text().splitlines()
            self.assertTrue(any("|54 1 2 3 4 5 6 7 8" in row for row in attempts))

    def test_emitted_loop_absolute_deadline_still_rejects(self):
        shell = capture.build_remote_script("fixture", 5, allow_short=True)
        start = shell.index("for qt in $tids_arm; do qualified=0")
        loop = shell[start:shell.index("\nqe=", start)]
        loop = loop.replace('"/proc/$ap/task/$qt/syscall"', '"$FAKE/$qt"')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); fake = root / "fake"; out = root / "out"
            fake.mkdir(); out.mkdir(); (fake / "7").write_text("0 0\n")
            script = ("set -eu\ntids_arm=7\nap=1\n" +
                      f"FAKE={fake}\nO={out}\nea=0\n" + loop + "\n")
            result = subprocess.run(["/bin/sh", "-c", script],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True)
            self.assertNotEqual(result.returncode, 0)


class QuiescentEvidenceTests(unittest.TestCase):
    def test_running_and_numeric54_are_retained_before_terminal_point_anchor(self):
        raw54 = "54 0x21 0xc010643a 0xf4efe4ac 0x10ac5 0x0 0xf4efe4ac 0xf4efe44c 0x42edcf2c"
        report = capture.parse_fds(fds_fixture({
            7: ["running", raw54, raw54, "0 0 0 0 0 0 0 0 0"],
            11: ["54 1 2 3 4 5 6 7 8", "-1 0 0 0 0 0 0 0 0"]}))
        q = report["trace_arming"]["syscall_quiescence"]
        self.assertTrue(q["complete"])
        self.assertEqual([row["kind"] for row in q["attempts_by_tid"]["7"]],
                         ["indeterminate", "transient_active_54",
                          "transient_active_54", "numeric"])
        self.assertEqual([row["tid"] for row in q["active_nr54"]], [7, 7, 11])
        self.assertEqual(q["active_nr54"][0]["raw"], raw54)
        self.assertEqual([(row["tid"], row["syscall"])
                          for row in q["terminal_numeric_rows"]], [(7, 0), (11, -1)])

    def test_terminal54_exhaustion_and_numeric_before_terminal_are_rejected(self):
        bad = (
            {7: ["54 0"], 11: ["0 0"]},
            {7: ["running", "54 0", "running"], 11: ["0 0"]},
            {7: ["0 0", "54 0", "1 0"], 11: ["0 0"]},
            {7: ["54 0"] * 8, 11: ["0 0"]},
        )
        for attempts in bad:
            with self.subTest(attempts=attempts):
                with self.assertRaisesRegex(ValueError, "terminal numeric non-54"):
                    capture.parse_fds(fds_fixture(attempts))

    def test_malformed_missing_duplicate_clock_and_tid_changes_reject(self):
        valid = {7: ["54 0", "0 0"], 11: ["0 0"]}
        cases = (
            fds_fixture(valid).replace("ATTEMPT|7|2|", "ATTEMPT|7|3|", 1),
            fds_fixture(valid).replace("ATTEMPT|7|2|8.782|0 0\n", "", 1),
            fds_fixture(valid).replace("ATTEMPT|7|1|8.780|54 0",
                                       "ATTEMPT|7|1|nan|54 0", 1),
            fds_fixture(valid).replace("@@ TIDS_QUIESCENT\n7\n11",
                                       "@@ TIDS_QUIESCENT\n7\n12", 1),
            fds_fixture({7: ["wat"], 11: ["0 0"]}),
        )
        for body in cases:
            with self.subTest(body=body[-100:]):
                with self.assertRaises(ValueError):
                    capture.parse_fds(body)

    def test_unanchored_trace_exit_cannot_rescue_missing_terminal_sample(self):
        # FDS validation is intentionally independent of trace contents: a 54
        # observation with no later numeric non-54 point anchor always rejects.
        with self.assertRaisesRegex(ValueError, "terminal numeric non-54"):
            capture.parse_fds(fds_fixture({7: ["54 0"], 11: ["0 0"]}))

    def test_retained_failed_fds_is_immutable_and_still_rejects(self):
        path = FAILED_SMOKE / "partial-fds.txt"
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            capture.parse_fds(before.decode())
        self.assertEqual(path.read_bytes(), before)
        self.assertIn(
            b"ATTEMPT|1011|1|68292.35|54 0x21 0xc010643a 0xf4efe4ac", before)


class QuiescentDispatchTests(unittest.TestCase):
    def test_actual_public_run_reaches_offline_stage_with_new_script_and_no_transport(self):
        lower = capture._preroll._base._base
        staged = {}

        def stop(label, script):
            self.assertIs(capture._preroll.parse_fds, capture.parse_fds)
            self.assertIs(capture._preroll._base.parse_fds, capture.parse_fds)
            self.assertIs(lower.parse_fds, capture.parse_fds)
            staged.update(label=label, script=script)
            raise RuntimeError("offline-stage-sentinel")

        clean_proc = type("Proc", (), {"returncode": 0, "stdout": "{}", "stderr": ""})()
        clean_item = {"exit_code": 0, "timed_out": False, "stdout": "CLEAN\n"}
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(lower, "BASE", Path(directory)), \
                mock.patch.object(lower, "stage_script", side_effect=stop), \
                mock.patch.object(lower, "cleanup_remote",
                                  return_value=(clean_proc, clean_item)), \
                mock.patch.object(capture, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            with self.assertRaisesRegex(RuntimeError, "offline-stage-sentinel"):
                capture.run_capture("fixture", 5, smoke_unobserved=True)
            remote = Path(directory) / "fixture.onset" / "remote.sh"
            self.assertEqual(remote.read_bytes(), staged["script"])
            shell = remote.read_text()
            subprocess.run(["/bin/sh", "-n"], input=shell, text=True, check=True)
            self.assertIn(capture.REMOTE_ROOT, shell)
            self.assertIn('test "$qnr" -eq 54', shell)
            self.assertNotIn(capture.PARENT_REMOTE_ROOT, shell)

    def test_public_nested_run_installs_validator_and_restores_success_and_exception(self):
        branch = capture._preroll._base
        lower = branch._base
        tracked = ((capture._base, ("root", "build_remote_script")),
                   (capture._preroll, ("parse_fds",)),
                   (branch, ("parse_fds",)), (lower, ("parse_fds",)))
        before = {(id(mod), name): getattr(mod, name)
                  for mod, names in tracked for name in names}
        observed = {}

        def fake_lower(label, seconds, smoke_unobserved=False):
            self.assertEqual((label, seconds, smoke_unobserved), ("fixture", 5, True))
            self.assertIs(capture._preroll.parse_fds, capture.parse_fds)
            self.assertIs(branch.parse_fds, capture.parse_fds)
            self.assertIs(lower.parse_fds, capture.parse_fds)
            shell = capture._base.build_remote_script(label, seconds, allow_short=True)
            self.assertIn(capture.REMOTE_ROOT, shell)
            report = lower.parse_fds(fds_fixture({7: ["54 0", "0 0"],
                                                  11: ["0 0"]}))
            observed["active"] = report["trace_arming"]["syscall_quiescence"][
                "active_nr54"][0]["syscall"]

        with mock.patch.object(capture._preroll, "_ORIGINAL_RUN", side_effect=fake_lower), \
                mock.patch.object(capture, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            capture.run_capture("fixture", 5, smoke_unobserved=True)
        self.assertEqual(observed, {"active": 54})
        for mod, names in tracked:
            for name in names:
                self.assertIs(getattr(mod, name), before[(id(mod), name)])

        with mock.patch.object(capture._preroll, "_ORIGINAL_RUN",
                               side_effect=RuntimeError("offline abort")):
            with self.assertRaisesRegex(RuntimeError, "offline abort"):
                capture.run_capture("fixture", 5, smoke_unobserved=True)
        for mod, names in tracked:
            for name in names:
                self.assertIs(getattr(mod, name), before[(id(mod), name)])


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(old))
    for cls in (QuiescentShellTests, QuiescentEvidenceTests, QuiescentDispatchTests):
        suite.addTests(loader.loadTestsFromTestCase(cls))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
