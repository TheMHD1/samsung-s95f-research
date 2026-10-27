#!/usr/bin/env python3
"""Offline tests for observed-preroll-onset-capture.py; never contact the TV."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "observed-preroll-onset-capture.py"
FROZEN_TESTS = HERE / "observed-branch-onset-capture-tests.py"
FROZEN_TESTS_SHA256 = "ec4186840e22206efceab6a3fbea994e41ad586ab3068c6b51b83ad1d9411089"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("module unavailable: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if hashlib.sha256(FROZEN_TESTS.read_bytes()).hexdigest() != FROZEN_TESTS_SHA256:
    raise RuntimeError("frozen branch observer tests changed")
capture = load("observed_preroll_capture", SOURCE)
old = load("frozen_branch_tests_ec418", FROZEN_TESTS)


def event(pid, when, kind, body, tgid=None, source_task="worker"):
    tgid = pid if tgid is None else tgid
    return (f" {source_task}-{pid} (  {tgid}) [000] .... {when:.6f}: "
            f"{kind}: {body}\n")


def trace(rows, retained=None, written=None):
    retained = len(rows) if retained is None else retained
    written = retained if written is None else written
    return (f"# entries-in-buffer/entries-written: {retained}/{written}\n" +
            "".join(rows)).encode()


def fds_fixture(attempts=None, mutate=None, shift=0.0):
    attempts = attempts or {7: ["-1 0 0 0 0 0 0 0 0"],
                            11: ["running", "0 0 0 0 0 0 0 0 0"]}
    rows = []
    when = 8.78 + shift
    for tid in (7, 11):
        for index, raw in enumerate(attempts.get(tid, []), 1):
            rows.append(f"ATTEMPT|{tid}|{index}|{when:.3f}|{raw}")
            when += .002
    parts = {
        "TIDS_START": "7\n11", "FDS_START": "27 /dev/sdp_pqe_dp\n33 /dev/dri/card0",
        "TIDS_PRE": "7\n11",
        "TRACE_ARMING_START": (f"ENABLE_BEFORE {8.740 + shift:.3f}\n"
                               f"ENABLE_AFTER {8.750 + shift:.3f}\n"
                               f"TRACE_ARMED_BODY {8.750 + shift:.3f}"),
        "TIDS_ARM": "7\n11", "SYSCALL_QUIESCENCE": "\n".join(rows),
        "TIDS_QUIESCENT": "7\n11",
        "FDS_PREROLL": "27 /dev/sdp_pqe_dp\n33 /dev/dri/card0",
        "TRACE_ARMING_END": (f"SWEEP_START {8.770 + shift:.3f}\n"
                             f"SWEEP_END {8.800 + shift:.3f}\n"
                             f"PREROLL_BODY {9.000 + shift:.3f}"),
        "TIDS_END": "7\n11", "FDS_END": "27 /dev/sdp_pqe_dp\n33 /dev/dri/card0"}
    if mutate:
        mutate(parts)
    order = ("TIDS_START", "FDS_START", "TIDS_PRE", "TRACE_ARMING_START",
             "TIDS_ARM", "SYSCALL_QUIESCENCE", "TIDS_QUIESCENT",
             "FDS_PREROLL", "TRACE_ARMING_END", "TIDS_END", "FDS_END")
    return "".join(f"@@ {name}\n{parts[name]}\n" for name in order)


def evidence(attempts=None, mutate=None):
    return capture.parse_fds(fds_fixture(attempts, mutate))


def good_trace(extra_slop=(), extra_prelude=(), extra_preroll=(),
               extra_window=(), extra_drain=(), extra_post=(), source="tracing_mark_write",
               times=(8.75, 9.0, 10.0, 11.0, 11.1)):
    armed, preroll, start, end, drain = times
    rows = list(extra_slop)
    rows.append(event(99, armed, source,
                      f"CAPTURE_TRACE_ARMED utc=1000 uptime={armed:.3f}",
                      tgid=99, source_task="sh"))
    rows += list(extra_prelude)
    rows.append(event(99, preroll, source,
                      f"CAPTURE_PREROLL_START utc=1000 uptime={preroll:.3f}", tgid=99,
                      source_task="sh"))
    rows += list(extra_preroll)
    rows.append(event(99, start, source,
                      f"CAPTURE_START utc=1001 uptime={start:.3f}", tgid=99,
                      source_task="sh"))
    rows += list(extra_window)
    rows.append(event(99, end, source,
                      f"CAPTURE_END utc=1002 uptime={end:.3f}", tgid=99,
                      source_task="sh"))
    rows += list(extra_drain)
    rows.append(event(99, drain, source,
                      f"CAPTURE_DRAIN_END utc=1002 uptime={drain:.3f}", tgid=99,
                      source_task="sh"))
    rows += list(extra_post)
    return trace(rows)


ARGS_DRM = "21, c010643a, f4efe4ac, f50e, 0, f4efe4ac"
ARGS_PQE = "1b, c004510a, f44f94b8, 0, 0, 0"


def account(data, fd_report=None):
    fd_report = fd_report or evidence()
    return capture.trace_accounting(data, fd_report["tids"], 7, 99, 10.0, 11.0, 11.1)


class PreRollShellTests(unittest.TestCase):
    PATCHED = ("root", "build_remote_script", "parse_fds", "validate_trace_scope",
               "trace_accounting", "REMOTE_ROOT", "STAGE_ROOT", "TRACE_PREFIX")

    def test_generated_modes_are_syntactic_unique_and_private(self):
        hashes = []
        for seconds, smoke in ((5, True), (10, True), (85, False), (90, False)):
            shell = capture.build_remote_script("fixture", seconds, allow_short=smoke)
            subprocess.run(["/bin/sh", "-n"], input=shell, text=True, check=True)
            hashes.append(hashlib.sha256(shell.encode()).hexdigest())
            self.assertIn(capture.REMOTE_ROOT, shell)
            self.assertIn(capture.STAGE_ROOT, shell)
            self.assertIn(capture.TRACE_PREFIX, shell)
            self.assertNotIn(capture.BRANCH_REMOTE_ROOT, shell)
            self.assertNotIn(capture.BRANCH_STAGE_ROOT, shell)
            self.assertNotIn(capture.BRANCH_TRACE_PREFIX, shell)
        self.assertEqual(len(set(hashes)), 4)

    def test_shell_contains_bounded_read_only_quiescence_and_five_markers(self):
        shell = capture.build_remote_script("fixture", 85)
        ordered = ["CAPTURE_TRACE_ARMED utc=", "@@ SYSCALL_QUIESCENCE",
                   "@@ TIDS_QUIESCENT", "@@ FDS_PREROLL",
                   "CAPTURE_PREROLL_START utc=", "CAPTURE_START utc=",
                   "CAPTURE_END utc=", "CAPTURE_DRAIN_END utc="]
        positions = [shell.index(item) for item in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('/proc/$ap/task/$qt/syscall', shell)
        self.assertIn('test "$qraw" = running', shell)
        self.assertIn(f'test "$qi" -lt {capture.QUIESCENCE_MAX_ATTEMPTS}', shell)
        self.assertIn(f'sleep {capture.QUIESCENCE_RETRY_SECONDS}', shell)
        self.assertIn('test "$qnr" -ne 54', shell)
        self.assertNotIn("/dev/sdp_pqe_dp", shell)
        self.assertNotRegex(shell, r"(?:ioctl|setprop|input keyevent)\s")

    def test_exact_emitted_quiescence_loop_accepts_numeric_non54_and_rejects_others(self):
        shell = capture.build_remote_script("fixture", 5, allow_short=True)
        start = shell.index("for qt in $tids_arm; do qualified=0")
        loop = shell[start:shell.index("\nqe=", start)]
        loop = loop.replace('"/proc/$ap/task/$qt/syscall"', '"$FAKE/$qt"')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake, out = root / "fake", root / "out"
            fake.mkdir()
            out.mkdir()
            script = ("set -eu\ntids_arm=7\nap=1\n"
                      f"FAKE={fake}\nO={out}\n"
                      "ea=$(cut -d\" \" -f1 /proc/uptime)\n" + loop + "\n")
            for payload, expected in (("0 0 0 0 0 0 0 0 0\n", 0),
                                      ("running\n", 84),
                                      ("54 0 0 0 0 0 0 0 0\n", 86),
                                      ("54x bad\n", 85)):
                (fake / "7").write_text(payload)
                result = subprocess.run(["/bin/sh", "-c", script],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True)
                self.assertEqual(result.returncode, expected,
                                 (payload, result.stderr))

    def test_actual_public_run_builds_then_stops_before_transport_and_restores(self):
        staged = {}

        def stop(label, script):
            self.assertIs(capture._base._base.parse_fds, capture.parse_fds)
            self.assertIs(capture._base._base.validate_trace_scope,
                          capture.validate_trace_scope)
            self.assertIs(capture._base._base.trace_accounting,
                          capture.trace_accounting)
            staged.update(label=label, script=script)
            raise RuntimeError("offline-stage-sentinel")

        before = {name: getattr(capture._base, name) for name in self.PATCHED}
        clean_proc = SimpleNamespace(returncode=0, stdout="{}", stderr="")
        clean_item = {"exit_code": 0, "timed_out": False, "stdout": "CLEAN\n"}
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(capture._base._base, "BASE", Path(directory)), \
                mock.patch.object(capture._base._base, "stage_script", side_effect=stop), \
                mock.patch.object(capture._base._base, "cleanup_remote",
                                  return_value=(clean_proc, clean_item)), \
                mock.patch.object(capture, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            with self.assertRaisesRegex(RuntimeError, "offline-stage-sentinel"):
                capture.run_capture("fixture", 85)
            remote = Path(directory) / "fixture.onset" / "remote.sh"
            self.assertEqual(remote.read_bytes(), staged["script"])
            subprocess.run(["/bin/sh", "-n"], input=remote.read_text(), text=True,
                           check=True)
        for name, value in before.items():
            self.assertIs(getattr(capture._base, name), value)

    def test_public_nested_run_dispatches_new_sidecar_validators_and_restores(self):
        observed = {}
        branch_before = {name: getattr(capture._base, name) for name in self.PATCHED}
        lower_names = ("parse_fds", "validate_trace_scope", "trace_accounting")
        lower_before = {name: getattr(capture._base._base, name) for name in lower_names}

        def mocked_lower_run(label, seconds, smoke_unobserved=False):
            self.assertEqual((label, seconds, smoke_unobserved), ("fixture", 5, True))
            lower = capture._base._base
            self.assertIs(lower.parse_fds, capture.parse_fds)
            self.assertIs(lower.validate_trace_scope, capture.validate_trace_scope)
            self.assertIs(lower.trace_accounting, capture.trace_accounting)
            fd_report = lower.parse_fds(fds_fixture())
            lower.validate_trace_scope(
                {"trace_filter_tids": [7, 11],
                 "trace_filter": capture.syscall_filter_for_tids([7, 11])}, fd_report)
            report = lower.trace_accounting(good_trace(), fd_report["tids"],
                                            7, 99, 10.0, 11.0, 11.1)
            observed.update(markers=len(report["markers"]),
                            physical=report["trace_windows"]["physical_window_unchanged"])

        with mock.patch.object(capture._base, "_ORIGINAL_RUN",
                               side_effect=mocked_lower_run), \
                mock.patch.object(capture, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            capture.run_capture("fixture", 5, smoke_unobserved=True)
        self.assertEqual(observed, {"markers": 5, "physical": True})
        for name, value in branch_before.items():
            self.assertIs(getattr(capture._base, name), value)
        for name, value in lower_before.items():
            self.assertIs(getattr(capture._base._base, name), value)
        with mock.patch.object(capture._base, "_ORIGINAL_RUN",
                               side_effect=RuntimeError("nested-validation-abort")):
            with self.assertRaisesRegex(RuntimeError, "nested-validation-abort"):
                capture.run_capture("fixture", 5, smoke_unobserved=True)
        for name, value in branch_before.items():
            self.assertIs(getattr(capture._base, name), value)
        for name, value in lower_before.items():
            self.assertIs(getattr(capture._base._base, name), value)

    def test_true_lower_run_completes_with_mocked_new_sidecars_no_network(self):
        state = {}
        lower = capture._base._base

        def stage(label, script):
            state["stage"] = {"bytes": len(script),
                              "sha256": hashlib.sha256(script).hexdigest(),
                              "path": f"{capture.STAGE_ROOT}/{label}/capture.sh"}
            return state["stage"]

        def make_sidecars():
            stage_item = state["stage"]
            metadata = old.branch_metadata(stage_item["bytes"], stage_item["sha256"])
            meta = old.capture.validate_metadata(
                metadata, stage_item["bytes"], stage_item["sha256"], 85)
            sample_text = old.sample_text(meta)
            sample_report = old.capture.analyze_samples(sample_text, meta, 85)
            vlog = "".join(
                f" thread: {stamp:.3f} D/TEST (P1,T1): fixture\n"
                for stamp in [104.0 + index for index in range(89)])
            bodies = {
                "trace": good_trace(times=(104.0, 104.25, 105.2, 190.2, 190.3)),
                "meta": metadata.encode(), "samples": sample_text.encode(),
                "sample-errors": old.dd_stderr(sample_report["monitor_rows"],
                                                sample_report["qd_rows"]).encode(),
                "vlog-after": vlog.encode(), "artifacts": b"offline fixture\n",
                "fds": fds_fixture(shift=95.25).encode()}
            state["bodies"] = bodies
            return bodies

        def transport(_label, _destination):
            bodies = state.get("bodies") or make_sidecars()
            rows = [f"SIDECAR {name} {len(body)} {hashlib.sha256(body).hexdigest()}"
                    for name, body in bodies.items()]
            return "\n".join(rows + ["CAPTURE_COMPLETE"]) + "\n"

        suffix_to_name = {value: key for key, value in capture.SUFFIX.items()}

        def fetch(path, size, digest):
            name = suffix_to_name[Path(path).name]
            body = state["bodies"][name]
            self.assertEqual((len(body), hashlib.sha256(body).hexdigest()),
                             (size, digest))
            return body

        sync = {"host_midpoint_monotonic": 0.0, "target_uptime": 105.0,
                "tv_uptime": 100.0, "tv_utc": 1000,
                "estimated_target_host_monotonic": 5.0,
                "estimated_target_host_utc": 1005.0,
                "mapping_uncertainty_seconds": .1}
        collector = {"pid": 99, "start_ticks": 999,
                     "process_group": 99, "session": 99}
        clean_proc = SimpleNamespace(returncode=0, stdout="0\nCLEAN\n", stderr="")
        clean_item = {"exit_code": 0, "timed_out": False, "stdout": "0\nCLEAN\n"}
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(lower, "BASE", Path(directory)), \
                mock.patch.object(lower, "stage_script", side_effect=stage), \
                mock.patch.object(lower, "acquire_sync", return_value=sync), \
                mock.patch.object(lower, "launch_collector", return_value=collector), \
                mock.patch.object(lower, "collector_running", return_value=False), \
                mock.patch.object(lower, "fetch_collector_transport", side_effect=transport), \
                mock.patch.object(lower, "fetch_file", side_effect=fetch), \
                mock.patch.object(lower, "cleanup_remote",
                                  return_value=(clean_proc, clean_item)), \
                mock.patch.object(lower.time, "monotonic", side_effect=[0.0, 95.0, 95.0]), \
                mock.patch.object(capture, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            capture.run_capture("fixture", 85, smoke_unobserved=False)
            record = json.loads((Path(directory) / "fixture.onset" / "record.json").read_text())
        self.assertTrue(record["accepted"])
        self.assertTrue(record["technical_capture_complete"])
        self.assertFalse(record["diagnostic_eligible"])
        self.assertEqual(len(record["trace"]["markers"]), 5)
        self.assertTrue(record["process_files"]["trace_arming"]
                        ["syscall_quiescence"]["complete"])

    def test_main_run_reviewed_dispatch_is_mocked_before_any_transport(self):
        with mock.patch.object(sys, "argv", [str(SOURCE), "preroll-cli-fixture",
                                             "--seconds", "5", "--smoke-unobserved",
                                             "--run", "--reviewed"]), \
                mock.patch.object(capture, "run_capture") as run, \
                mock.patch.object(capture, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            capture.main()
        run.assert_called_once_with("preroll-cli-fixture", 5, smoke_unobserved=True)


class QuiescenceAndFdTests(unittest.TestCase):
    def test_running_retries_then_numeric_non54_qualifies_with_raw_rows(self):
        report = evidence()
        sweep = report["trace_arming"]["syscall_quiescence"]
        self.assertTrue(sweep["complete"])
        self.assertEqual([row["raw"] for row in sweep["attempts_by_tid"]["11"]],
                         ["running", "0 0 0 0 0 0 0 0 0"])
        self.assertEqual(len(sweep["terminal_numeric_rows"]), 2)
        self.assertEqual(report["tids"], [7, 11])

    def test_running_only_active54_malformed_missing_and_set_change_reject(self):
        cases = [
            ({7: ["running"] * 8, 11: ["0 0"]}, None, "terminal numeric"),
            ({7: ["54 0 0 0 0 0 0 0 0"], 11: ["0 0"]}, None, "active syscall54"),
            ({7: ["wat"], 11: ["0 0"]}, None, "malformed syscall"),
            ({7: ["0 0"]}, None, "TID order incomplete"),
            (None, lambda p: p.__setitem__("TIDS_QUIESCENT", "7\n12"), "TID set changed"),
            (None, lambda p: p.__setitem__(
                "TRACE_ARMING_START", "ENABLE_BEFORE 8.0\nENABLE_AFTER 8.1\nTRACE_ARMED_BODY 8.1"),
             "outside bounds"),
        ]
        for attempts, mutate, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                capture.parse_fds(fds_fixture(attempts, mutate))

    def test_fd_snapshots_and_filter_scope_are_exact(self):
        report = evidence()
        self.assertTrue(report["fd_targets_stable"])
        self.assertEqual(report["fd_targets_preroll"]["33"], "/dev/dri/card0")
        capture.validate_trace_scope(
            {"trace_filter_tids": [7, 11],
             "trace_filter": capture.syscall_filter_for_tids([7, 11])}, report)
        with self.assertRaisesRegex(ValueError, "completeness filter"):
            capture.validate_trace_scope(
                {"trace_filter_tids": [7],
                 "trace_filter": capture.syscall_filter_for_tids([7])}, report)


class PreRollTraceTests(unittest.TestCase):
    def test_start_boundary_pair_is_separate_raw_and_window_unchanged(self):
        begin = event(7, 9.9, "sys_enter", f"NR 54 ({ARGS_DRM})")
        finish = event(7, 10.1, "sys_exit", "NR 54 = 0")
        report = account(good_trace(extra_preroll=[begin], extra_window=[finish]))
        self.assertEqual(report["window_originated_pairs"], [])
        self.assertEqual(len(report["start_boundary_pairs"]), 1)
        pair = report["start_boundary_pairs"][0]
        self.assertEqual(pair["classification"], "start_boundary_completed_in_window")
        self.assertEqual(pair["raw_arguments"], ARGS_DRM)
        self.assertEqual(pair["registers"], [0x21, 0xC010643A, 0xF4EFE4AC,
                                              0xF50E, 0, 0xF4EFE4AC])
        self.assertEqual(pair["request_label"], "DRM_IOCTL_WAIT_VBLANK")
        self.assertTrue(pair["crosses_start"])
        self.assertFalse(pair["crosses_end"])
        self.assertEqual(report["capture_window_event_lines"], 1)
        self.assertFalse(report["absence_claim_supported"])

    def test_both_boundaries_and_window_tail_are_distinct(self):
        pre = event(7, 9.9, "sys_enter", f"NR 54 ({ARGS_DRM})")
        pre_done = event(7, 11.03, "sys_exit", "NR 54 = 0")
        win = event(11, 10.8, "sys_enter", f"NR 54 ({ARGS_PQE})", tgid=7)
        win_done = event(11, 11.04, "sys_exit", "NR 54 = -11", tgid=7)
        report = account(good_trace(extra_preroll=[pre], extra_window=[win],
                                    extra_drain=[pre_done, win_done]))
        self.assertEqual(len(report["start_boundary_pairs"]), 1)
        self.assertTrue(report["start_boundary_pairs"][0]["crosses_end"])
        self.assertEqual(len(report["window_tail_completed_pairs"]), 1)
        self.assertEqual(report["window_tail_completed_pairs"][0]["return"], -11)
        self.assertEqual(report["ioctl_pairs_completed_during_drain"], 1)

    def test_pending_overlap_rejects_but_drain_only_pending_is_reported(self):
        pre = event(7, 9.9, "sys_enter", f"NR 54 ({ARGS_DRM})")
        with self.assertRaisesRegex(ValueError, "physical-overlap.*unresolved"):
            account(good_trace(extra_preroll=[pre]))
        drain = event(7, 11.03, "sys_enter", f"NR 54 ({ARGS_DRM})")
        report = account(good_trace(extra_drain=[drain]))
        self.assertEqual(report["pending_at_drain_end"][0]["kind"],
                         "drain-only-pending")
        post = event(7, 11.2, "sys_exit", "NR 54 = 0")
        with self.assertRaisesRegex(ValueError, "physical-overlap.*unresolved"):
            account(good_trace(extra_preroll=[pre], extra_post=[post]))

    def test_prelude_overlap_orphan_duplicate_scope_and_args_reject(self):
        prelude_begin = event(7, 8.9, "sys_enter", f"NR 54 ({ARGS_DRM})")
        window_exit = event(7, 10.1, "sys_exit", "NR 54 = 0")
        cases = [
            (good_trace(extra_prelude=[prelude_begin], extra_window=[window_exit]),
             "unbounded prelude"),
            (good_trace(extra_window=[window_exit]), "orphan"),
            (good_trace(extra_preroll=[
                event(7, 9.8, "sys_enter", f"NR 54 ({ARGS_DRM})"),
                event(7, 9.9, "sys_enter", f"NR 54 ({ARGS_DRM})")]), "duplicate"),
            (good_trace(extra_window=[event(7, 10.1, "sys_enter",
                                           "NR 54 (21, c010643a, 1)")]), "six-register"),
            (good_trace(extra_window=[event(7, 10.1, "sys_exit", "NR 54 = 0", tgid=8)]),
             "unrelated saved-TGID"),
        ]
        for data, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                account(data)

    def test_prestart_orphan_and_complete_preroll_are_excluded(self):
        orphan = event(7, 9.1, "sys_exit", "NR 54 = 0")
        begin = event(11, 9.2, "sys_enter", f"NR 54 ({ARGS_PQE})", tgid=7)
        finish = event(11, 9.3, "sys_exit", "NR 54 = -11", tgid=7)
        report = account(good_trace(extra_preroll=[orphan, begin, finish]))
        self.assertEqual(len(report["preroll_complete_pairs"]), 1)
        self.assertEqual(report["boundary_unmatched_syscall54_rows"][0]["kind"],
                         "orphan-exit")
        self.assertEqual(report["capture_window_event_lines"], 0)

    def test_prelude_label_requires_start_preroll_end_fd_stability(self):
        begin = event(7, 8.8, "sys_enter", f"NR 54 ({ARGS_DRM})")
        finish = event(7, 8.9, "sys_exit", "NR 54 = 0")

        def changed_start(parts):
            parts["FDS_START"] = "27 /dev/sdp_pqe_dp\n33 /dev/null"

        report = account(good_trace(extra_prelude=[begin, finish]),
                         evidence(mutate=changed_start))
        pair = report["outside_pairs"][0]
        self.assertEqual(pair["fd_targets"],
                         {"start": "/dev/null", "preroll": "/dev/dri/card0",
                          "end": "/dev/dri/card0"})
        self.assertFalse(pair["fd_target_stable_start_to_end"])
        self.assertIsNone(pair["attribution_target"])
        self.assertIsNone(pair["request_label"])
        self.assertEqual(report["request_fd_counts"], {"0xc010643a@unknown": 1})

    def test_fd_missing_changed_and_known_request_mismatch_reject(self):
        rows = good_trace(
            extra_preroll=[event(7, 9.9, "sys_enter", f"NR 54 ({ARGS_DRM})")],
            extra_window=[event(7, 10.1, "sys_exit", "NR 54 = 0")])
        mutations = [
            lambda p: p.__setitem__("FDS_PREROLL", "27 /dev/sdp_pqe_dp"),
            lambda p: p.__setitem__("FDS_END",
                                    "27 /dev/sdp_pqe_dp\n33 /dev/dri/card1"),
            lambda p: p.__setitem__("FDS_PREROLL",
                                    "27 /dev/sdp_pqe_dp\n33 /dev/null"),
        ]
        for mutation in mutations:
            with self.subTest(), self.assertRaisesRegex(ValueError, "FD target"):
                account(rows, evidence(mutate=mutation))

        in_window = good_trace(
            extra_window=[event(7, 10.2, "sys_enter", f"NR 54 ({ARGS_DRM})"),
                          event(7, 10.3, "sys_exit", "NR 54 = 0")])
        with self.assertRaisesRegex(ValueError, "physical-overlap ioctl FD target"):
            account(in_window, evidence(mutate=lambda p: p.__setitem__(
                "FDS_END", "27 /dev/sdp_pqe_dp\n33 /dev/dri/card1")))

        preroll_only = good_trace(
            extra_preroll=[event(7, 9.2, "sys_enter", f"NR 54 ({ARGS_DRM})"),
                           event(7, 9.3, "sys_exit", "NR 54 = 0")])
        report = account(preroll_only, evidence(mutate=lambda p: p.__setitem__(
            "FDS_END", "27 /dev/sdp_pqe_dp\n33 /dev/dri/card1")))
        self.assertIsNone(report["preroll_complete_pairs"][0]["request_label"])
        self.assertIsNone(report["preroll_complete_pairs"][0]["attribution_target"])
        self.assertEqual(report["request_fd_counts"], {"0xc010643a@unknown": 1})

    def test_marker_ownership_source_order_and_durations_reject(self):
        good = good_trace(source="0xffffffc01017095c")
        cases = [
            (good.replace(b"sh-99", b"sh-98", 1), "collector identity"),
            (good.replace(b"0xffffffc01017095c", b"0xffffffc01017095d", 1),
             "sources differ"),
            (good.replace(b"CAPTURE_PREROLL_START", b"CAPTURE_PREROLL_STARTX"),
             "malformed capture"),
            (good.replace(b"9.000000: 0xffffffc01017095c: CAPTURE_PREROLL_START",
                          b"9.900000: 0xffffffc01017095c: CAPTURE_PREROLL_START")
                 .replace(b"uptime=9.000", b"uptime=9.900"), "bodies disagree"),
        ]
        for data, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                account(data)
        fd_report = evidence()
        fd_report["tids"].evidence["preroll_body"] = 9.900
        long_prelude = good.replace(
            b"9.000000: 0xffffffc01017095c: CAPTURE_PREROLL_START",
            b"9.900000: 0xffffffc01017095c: CAPTURE_PREROLL_START").replace(
                b"uptime=9.000", b"uptime=9.900")
        with self.assertRaisesRegex(ValueError, "duration outside bounds"):
            account(long_prelude, fd_report)

    def test_lifecycle_loss_decode_and_i2c_malformed_reject(self):
        fork = event(7, 9.4, "sched_process_fork",
                     "comm=avocd pid=7 child_comm=worker child_pid=12")
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            account(good_trace(extra_preroll=[fork]))
        exited = event(7, 11.02, "sched_process_exit", "comm=avocd pid=7 prio=120")
        with self.assertRaisesRegex(ValueError, "lifecycle"):
            account(good_trace(extra_drain=[exited]))
        good = good_trace()
        with self.assertRaisesRegex(ValueError, "overflow"):
            account(re.sub(rb"(entries-in-buffer/entries-written:\s*)(\d+)/(\d+)",
                           lambda m: m.group(1) + m.group(2) + b"/999", good))
        with self.assertRaisesRegex(ValueError, "decode count"):
            account(good.replace(b"5/5", b"6/6"))
        malformed = event(20, 10.4, "i2c_write",
                          "i2c-5 #0 a=076 f=0000 l=2 [f3--01]", tgid=20)
        with self.assertRaisesRegex(ValueError, "I2C"):
            account(good_trace(extra_window=[malformed]))


class Retained1901Tests(unittest.TestCase):
    def setUp(self):
        self.artifact = HERE / "branch-smoke-20261026t1901.onset"
        record_bytes = (self.artifact / "record.json").read_bytes()
        self.assertEqual(hashlib.sha256(record_bytes).hexdigest(),
                         "61351a4e8d4bc46a3bc5b1346277051fc874af299924d7991b4384ff9cbabbc5")
        self.record = json.loads(record_bytes)
        for name, item in self.record["partial_salvage"]["sidecars"].items():
            body = (self.artifact / item["path"]).read_bytes()
            self.assertEqual((len(body), hashlib.sha256(body).hexdigest()),
                             (item["bytes"], item["sha256"]), name)

    def _raw_window(self):
        part = capture.sections((self.artifact / "partial-meta.txt").read_text())
        values = part["CAPTURE_WINDOW"].split()
        return float(values[1]), float(values[2]), float(values[2].split()[0]) + .1

    def test_original_raw_remains_rejected_by_old_and_new_contracts(self):
        raw = (self.artifact / "partial-trace").read_bytes()
        old_fd = capture._base.parse_fds((self.artifact / "partial-fds.txt").read_text())
        part = capture.sections((self.artifact / "partial-meta.txt").read_text())
        values = part["CAPTURE_WINDOW"].split()
        with self.assertRaisesRegex(ValueError, "crosses capture start"):
            capture._base.trace_accounting(
                raw, old_fd["tids"], 706, self.record["collector"]["pid"],
                float(values[1]), float(values[2]), float(values[2]) + .1)
        with self.assertRaisesRegex(ValueError, "five trace markers"):
            capture.trace_accounting(raw, evidence()["tids"], 706,
                                     self.record["collector"]["pid"],
                                     float(values[1]), float(values[2]),
                                     float(values[2]) + .1)

    def test_byte_pinned_trace_with_only_owned_preroll_markers_classifies_boundary(self):
        raw = (self.artifact / "partial-trace").read_bytes()
        text = raw.decode()
        header = re.search(r"entries-in-buffer/entries-written:\s*(\d+)/(\d+)", text)
        self.assertIsNotNone(header)
        retained = int(header.group(1))
        self.assertEqual(retained, int(header.group(2)))
        start_line = next(line for line in text.splitlines() if "CAPTURE_START utc=" in line)
        source = re.search(r": (0x[0-9a-f]+|tracing_mark_write): CAPTURE_START", start_line).group(1)
        collector = self.record["collector"]["pid"]
        added = (event(collector, 62732.400, source,
                       "CAPTURE_TRACE_ARMED utc=1000 uptime=62732.400",
                       tgid=collector, source_task="sh") +
                 event(collector, 62732.650, source,
                       "CAPTURE_PREROLL_START utc=1000 uptime=62732.650",
                       tgid=collector, source_task="sh"))
        text = re.sub(r"(entries-in-buffer/entries-written:\s*)\d+/\d+",
                      rf"\g<1>{retained + 2}/{retained + 2}", text, count=1)
        first_newline = text.index("\n") + 1
        synthetic = (text[:first_newline] + added + text[first_newline:]).encode()
        old_parts = capture.sections((self.artifact / "partial-fds.txt").read_text())
        tids = [int(row) for row in old_parts["TIDS_PRE"].splitlines()]

        def fdmap(value):
            return {int(line.partition(" ")[0]): line.partition(" ")[2]
                    for line in value.splitlines()}
        f0, f1 = fdmap(old_parts["FDS_START"]), fdmap(old_parts["FDS_END"])
        attempts = {str(tid): [{"attempt": 1, "uptime": 62732.500,
                                "raw": "-1 0 0 0 0 0 0 0 0",
                                "kind": "numeric", "syscall": -1}]
                    for tid in tids}
        ev = {"trace_enable_bracket": [62732.390, 62732.400],
              "trace_armed_body": 62732.400, "sweep_start": 62732.410,
              "sweep_end": 62732.550, "preroll_body": 62732.650,
              "syscall_quiescence": {"tids": tids, "attempts_by_tid": attempts,
                                      "terminal_numeric_rows": [], "active_nr54": [],
                                      "indeterminate_exhausted": [],
                                      "max_attempts_per_tid": 8,
                                      "retry_interval_seconds": .002,
                                      "duration_seconds": .14, "complete": True},
              "fds_start": f0, "fds_preroll": f0, "fds_end": f1}
        guarded = capture.TidEvidence(tids, ev)
        meta_part = capture.sections((self.artifact / "partial-meta.txt").read_text())
        window = [float(value) for value in meta_part["CAPTURE_WINDOW"].split()[:3]]
        event_re = re.compile(
            rb"^\s*.+?-\d+\s+\([^)]*\)\s+\[\d+\]\s+\S+\s+"
            rb"(?P<time>\d+\.\d+): \w+: .*$")
        raw_lines = raw.splitlines()
        start_index = next(index for index, line in enumerate(raw_lines)
                           if b"CAPTURE_START utc=" in line)
        end_index = next(index for index, line in enumerate(raw_lines)
                         if b"CAPTURE_END utc=" in line)
        original_window_events = sum(event_re.match(line) is not None
                                     for line in raw_lines[start_index + 1:end_index])
        report = capture.trace_accounting(synthetic, guarded, 706, collector,
                                          window[1], window[2], window[2] + .1)
        matches = [row for row in report["start_boundary_pairs"]
                   if row["tid"] == 1011 and row["request"] == 0xC010643A]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["classification"],
                         "start_boundary_completed_in_window")
        self.assertEqual(report["capture_window_event_lines"], original_window_events)
        self.assertFalse(report["absence_claim_supported"])


def load_tests(_loader, _tests, _pattern):
    """Run the frozen branch suite first, then the pre-roll delta."""
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(old))
    for case in (PreRollShellTests, QuiescenceAndFdTests, PreRollTraceTests,
                 Retained1901Tests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
