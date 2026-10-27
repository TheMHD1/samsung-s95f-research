#!/usr/bin/env python3
"""Offline tests for observed-pm-onset-capture.py; never contact the TV."""

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
SOURCE = HERE / "observed-pm-onset-capture.py"
FROZEN_TESTS = HERE / "observed-preroll-onset-capture-tests.py"
FROZEN_TESTS_SHA256 = "144f0a4dc188542180c4a66f4853ba31d61e5909073a9480756527caf6c22de1"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("module unavailable: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if hashlib.sha256(FROZEN_TESTS.read_bytes()).hexdigest() != FROZEN_TESTS_SHA256:
    raise RuntimeError("frozen pre-roll observer tests changed")
capture = load("observed_pm_capture", SOURCE)
old = load("frozen_preroll_tests_144f", FROZEN_TESTS)


def event(pid, when, kind, body, tgid=None, cpu=0, task="worker"):
    tgid = pid if tgid is None else tgid
    return (f" {task}-{pid} (  {tgid}) [{cpu:03d}] .... {when:.6f}: "
            f"{kind}: {body}\n")


def pm_format_section():
    return "".join(f"FORMAT {name}\n{capture.FORMAT_TEXTS[name]}END_FORMAT\n"
                   for name in capture.PM_EVENTS)


def cpu_stats(drop=0, omit_cpu=None):
    rows = ["ONLINE 0-3"]
    for cpu in range(4):
        if cpu == omit_cpu:
            continue
        rows += [f"CPU {cpu}", "entries: 10", "overrun: 0", "commit overrun: 0",
                 "bytes: 100", "oldest event ts: 8.500", "now ts: 11.100",
                 f"dropped events: {drop if cpu == 0 else 0}", "read events: 0"]
    return "\n".join(rows)


def metadata(mutate=None):
    base = old.old.branch_metadata()
    extra = {
        "PM_KERNEL": capture.KERNEL_RELEASE,
        "PM_SOURCE_ID_START": (capture.HDMI_MODULE_SHA256 + "  " +
                               capture.REMOTE_HDMI_MODULE),
        "PM_FORMATS_START": pm_format_section().rstrip("\n"),
        "PM_CONFIG_START": "\n".join(f"{name}=1" for name in capture.PM_EVENTS),
        "PM_FORMATS_CONFIG": pm_format_section().rstrip("\n"),
        "PM_CONFIG_END": "\n".join(f"{name}=1" for name in capture.PM_EVENTS),
        "PM_SOURCE_ID_END": (capture.HDMI_MODULE_SHA256 + "  " +
                             capture.REMOTE_HDMI_MODULE),
        "PM_CPU_STATS": cpu_stats(),
    }
    if mutate:
        mutate(extra)
    return "".join(f"@@ {name}\n{extra[name]}\n" for name in extra) + base


def fds():
    return capture._base.parse_fds(old.fds_fixture())


def account(data):
    evidence = fds()
    return capture.trace_accounting(data, evidence["tids"], 7, 99, 10.0, 11.0, 11.1)


class PMShellAndMetadataTests(unittest.TestCase):
    def test_all_four_shells_are_syntactic_private_and_exact(self):
        hashes = []
        for seconds, short in ((5, True), (10, True), (85, False), (90, False)):
            shell = capture.build_remote_script("fixture", seconds, allow_short=short)
            subprocess.run(["/bin/sh", "-n"], input=shell, text=True, check=True)
            hashes.append(hashlib.sha256(shell.encode()).hexdigest())
            self.assertIn(capture.REMOTE_ROOT, shell)
            self.assertIn(capture.STAGE_ROOT, shell)
            self.assertIn(capture.TRACE_PREFIX, shell)
            self.assertNotIn(capture.PARENT_REMOTE_ROOT, shell)
            for name in capture.PM_EVENTS:
                self.assertIn(f'events/{name}/enable', shell)
                self.assertIn(f'events/{name}/format', shell)
            self.assertNotIn("kprobe", shell.lower())
            self.assertNotIn("function_graph", shell)
        self.assertEqual(len(set(hashes)), 4)

    def test_default_is_dry_and_live_requires_both_guards(self):
        run = subprocess.run([sys.executable, str(SOURCE), "fixture", "--seconds", "5",
                              "--smoke-unobserved"], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, check=True)
        body = json.loads(run.stdout)
        self.assertEqual(body["mode"], "dry-run; no TV/network/root call")
        self.assertFalse(body["absence_claim_supported"])
        self.assertLessEqual(body["largest_staging_command_bytes"], 8192)
        with mock.patch.object(capture, "run_capture",
                               side_effect=AssertionError("transport attempted")) as called:
            with mock.patch.object(sys, "argv", [str(SOURCE), "fixture", "--seconds", "5",
                                                  "--smoke-unobserved", "--run"]):
                with self.assertRaisesRegex(ValueError, "--run and --reviewed"):
                    capture.main()
            called.assert_not_called()
        with mock.patch.object(capture, "run_capture") as dispatched, \
                mock.patch.object(sys, "argv", [str(SOURCE), "unique-pm", "--seconds", "5",
                                                "--smoke-unobserved", "--run", "--reviewed"]):
            capture.main()
        dispatched.assert_called_once_with("unique-pm", 5, smoke_unobserved=True)

    def test_metadata_accepts_exact_formats_enables_and_loss_free_cpu_stats(self):
        result = capture.validate_metadata(metadata(), 123, "a" * 64, 85)
        pm = result["pm_extension"]
        self.assertTrue(pm["seven_formats_exact"])
        self.assertTrue(pm["cpu_stats"]["loss_free"])
        self.assertEqual(pm["cpu_stats"]["online_cpus"], [0, 1, 2, 3])

    def test_metadata_rejects_format_enable_loss_and_missing_cpu(self):
        mutations = (
            lambda x: x.__setitem__("PM_FORMATS_CONFIG",
                                    x["PM_FORMATS_CONFIG"].replace("ID: 121", "ID: 999", 1)),
            lambda x: x.__setitem__("PM_CONFIG_END",
                                    x["PM_CONFIG_END"].replace("=1", "=0", 1)),
            lambda x: x.__setitem__("PM_CPU_STATS", cpu_stats(drop=1)),
            lambda x: x.__setitem__("PM_CPU_STATS", cpu_stats(omit_cpu=3)),
            lambda x: x.__setitem__("PM_SOURCE_ID_END", "0" * 64 + "  " +
                                    capture.REMOTE_HDMI_MODULE),
            lambda x: x.__setitem__("PM_KERNEL", "5.4.999"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                with self.assertRaises(ValueError):
                    capture.validate_metadata(metadata(mutate), 123, "a" * 64, 85)

    def test_pinned_formats_are_complete_and_source_hash_exact(self):
        self.assertEqual(hashlib.sha256(capture.FORMAT_SOURCE.read_bytes()).hexdigest(),
                         capture.FORMAT_SOURCE_SHA256)
        self.assertEqual(hashlib.sha256(capture.IDLE_FORMAT_SOURCE.read_bytes()).hexdigest(),
                         capture.IDLE_FORMAT_SOURCE_SHA256)
        self.assertEqual(hashlib.sha256(capture.IDLE_ADDENDUM.read_bytes()).hexdigest(),
                         capture.IDLE_ADDENDUM_SHA256)
        self.assertEqual(hashlib.sha256(capture.HDMI_MODULE.read_bytes()).hexdigest(),
                         capture.HDMI_MODULE_SHA256)
        self.assertEqual(tuple(capture.FORMAT_TEXTS), capture.PM_EVENTS)
        for event, body in capture.FORMAT_TEXTS.items():
            self.assertIn("name: " + event.rsplit("/", 1)[1], body)
            self.assertIn("print fmt:", body)


class PMTraceTests(unittest.TestCase):
    def test_zero_pm_rows_preserves_window_and_never_supports_absence(self):
        report = account(old.good_trace())
        self.assertEqual(report["capture_window_event_lines"], 0)
        self.assertEqual(report["pm_extension"]["counts_by_event_region_cpu"], {})
        self.assertFalse(report["pm_extension"]["absence_claim_supported"])
        self.assertTrue(report["pm_extension"]["semantic_complete"])
        self.assertTrue(any("proprietary Samsung sdp_runtime_pm" in item
                            for item in report["pm_extension"]["limits"]))

    def test_callback_window_pair_and_positive_sdp_hdmi_are_narrow(self):
        rows = [event(22, 10.2, "device_pm_callback_start",
                      "sdp-hdmi 10c00000.hdmi, parent: platform, dev_pm_ops[resume]", cpu=2),
                event(22, 10.4, "device_pm_callback_end",
                      "sdp-hdmi 10c00000.hdmi, err=0", cpu=3)]
        pm = account(old.good_trace(extra_window=rows))["pm_extension"]
        pair = pm["device_callback_pairs"][0]
        self.assertEqual((pair["classification"], pair["error"]), ("window_complete", 0))
        positive = pm["sdp_hdmi_positive_correlations"][0]
        self.assertIn("does not establish SerDes polling", positive["qualification"])
        self.assertNotIn("caused", positive["qualification"])
        self.assertEqual(positive["physical_window_start_position"], "within")
        self.assertFalse(pm["source_contract"]["runtime_loaded_module_binding_established"])

    def test_positive_driver_identity_is_exact_hyphen_not_underscore_or_near_match(self):
        for driver, expected in (("sdp-hdmi", 1), ("sdp_hdmi", 0), ("sdp-hdmi2", 0)):
            rows = [event(22, 10.2, "device_pm_callback_start",
                          f"{driver} dev, parent: p, ops[resume]"),
                    event(22, 10.3, "device_pm_callback_end", f"{driver} dev, err=0")]
            pm = account(old.good_trace(extra_window=rows))["pm_extension"]
            self.assertEqual(len(pm["sdp_hdmi_positive_correlations"]), expected)

    def test_callback_boundary_tail_nesting_nonzero_and_task_scope(self):
        rows_pre = [event(22, 9.8, "device_pm_callback_start",
                          "drv dev, parent: p, ops[resume]", tgid=22)]
        rows_window = [event(22, 10.2, "device_pm_callback_start",
                             "drv child, parent: dev, ops[suspend]", tgid=22),
                       event(22, 10.3, "device_pm_callback_end", "drv child, err=-11", tgid=22),
                       event(22, 10.4, "device_pm_callback_end", "drv dev, err=0", tgid=22)]
        pm = account(old.good_trace(extra_preroll=rows_pre,
                                    extra_window=rows_window))["pm_extension"]
        self.assertEqual([row["classification"] for row in pm["device_callback_pairs"]],
                         ["window_complete", "start_boundary"])
        self.assertEqual(pm["device_callback_pairs"][0]["error"], -11)

    def test_callback_unbounded_orphan_pending_mismatch_and_bad_action_reject(self):
        cases = (
            old.good_trace(extra_prelude=[event(22, 8.9, "device_pm_callback_start",
                                                "drv dev, parent: p, ops[resume]")],
                           extra_window=[event(22, 10.2, "device_pm_callback_end",
                                               "drv dev, err=0")]),
            old.good_trace(extra_window=[event(22, 10.2, "device_pm_callback_end",
                                               "drv dev, err=0")]),
            old.good_trace(extra_window=[event(22, 10.2, "device_pm_callback_start",
                                               "drv dev, parent: p, ops[resume]")]),
            old.good_trace(extra_window=[event(22, 10.2, "device_pm_callback_start",
                                               "drv dev, parent: p, ops[resume]"),
                                         event(22, 10.3, "device_pm_callback_end",
                                               "drv other, err=0")]),
            old.good_trace(extra_window=[event(22, 10.2, "device_pm_callback_start",
                                               "drv dev, parent: p, ops[unknown]")]),
        )
        for data in cases:
            with self.subTest(data=data[-100:]):
                with self.assertRaises(ValueError):
                    account(data)

    def test_all_three_families_reject_pretrace_pending_through_drain(self):
        pending = (
            event(22, 8.9, "device_pm_callback_start",
                  "drv dev, parent: p, ops[resume]"),
            event(30, 8.9, "suspend_resume", "dpm_resume[1] begin"),
            event(40, 8.9, "rpm_resume",
                  "dev flags-0 cnt-0 dep-0 auto-1 p-0 irq-0 child-0"),
        )
        for row in pending:
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, "pending .* overlaps"):
                    account(old.good_trace(extra_prelude=[row]))
        # Enable-slop is equally unbounded when the row remains pending.
        with self.assertRaisesRegex(ValueError, "pending callback .* overlaps"):
            account(old.good_trace(extra_slop=[event(
                22, 8.7, "device_pm_callback_start",
                "drv dev, parent: p, ops[resume]")]))

    def test_prelude_to_postdrain_pairs_reject_for_all_three_families(self):
        cases = (
            (event(22, 8.9, "device_pm_callback_start",
                   "drv dev, parent: p, ops[resume]"),
             event(22, 11.2, "device_pm_callback_end", "drv dev, err=0")),
            (event(30, 8.9, "suspend_resume", "dpm_resume[1] begin"),
             event(30, 11.2, "suspend_resume", "dpm_resume[1] end")),
            (event(40, 8.9, "rpm_resume",
                   "dev flags-0 cnt-0 dep-0 auto-1 p-0 irq-0 child-0"),
             event(40, 11.2, "rpm_return_int", "fn:dev ret=0")),
        )
        for begin, end in cases:
            with self.subTest(begin=begin):
                with self.assertRaisesRegex(ValueError, "unbounded PM operation"):
                    account(old.good_trace(extra_prelude=[begin], extra_post=[end]))

    def test_postdrain_callback_and_system_orphans_reject_but_generic_return_is_unknown(self):
        for row in (event(22, 11.2, "device_pm_callback_end", "drv dev, err=0"),
                    event(30, 11.2, "suspend_resume", "dpm_resume[1] end")):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, "orphan"):
                    account(old.good_trace(extra_post=[row]))
        report = account(old.good_trace(extra_post=[
            event(40, 11.2, "rpm_return_int", "rpm_idle:dev ret=0")]))
        self.assertEqual(report["pm_extension"]["unmatched"][0]["kind"],
                         "unassigned_return_unknown_operation")

    def test_system_phase_pairs_exactly_without_cycle_claim(self):
        rows = [event(30, 10.1, "suspend_resume", "dpm_suspend[3] begin"),
                event(30, 10.5, "suspend_resume", "dpm_suspend[3] end")]
        pm = account(old.good_trace(extra_window=rows))["pm_extension"]
        pair = pm["system_phase_pairs"][0]
        self.assertEqual((pair["action"], pair["val"]), ("dpm_suspend", 3))
        self.assertNotIn("full_system_cycle", json.dumps(pair).lower())
        with self.assertRaises(ValueError):
            account(old.good_trace(extra_window=[rows[0],
                event(30, 10.5, "suspend_resume", "dpm_suspend[4] end")]))

    def test_runtime_pair_padding_colon_negative_return_and_state(self):
        rows = [event(40, 10.1, "rpm_resume",
                      "dev.0 flags-1a cnt-2  dep--1 auto-1 p-0 irq-1 child-3"),
                event(40, 10.3, "rpm_return_int", "foo:bar:dev.0 ret=-11")]
        pm = account(old.good_trace(extra_window=rows))["pm_extension"]
        pair = pm["runtime_pm_pairs"][0]
        self.assertEqual((pair["operation"], pair["return"], pair["ip_raw"]),
                         ("resume", -11, "foo:bar"))
        self.assertEqual(pair["state"]["dep"], -1)

    def test_unmatched_runtime_return_is_unknown_operation_not_loss(self):
        row = event(40, 10.2, "rpm_return_int", "rpm_idle:dev.0 ret=0")
        pm = account(old.good_trace(extra_window=[row]))["pm_extension"]
        self.assertEqual(pm["unmatched"][0]["kind"],
                         "unassigned_return_unknown_operation")
        self.assertEqual(pm["unmatched"][0]["selected_entry_events"],
                         ["resume", "suspend", "idle"])
        self.assertTrue(pm["semantic_complete"])

    def test_nested_resume_idle_returns_pair_to_exact_stack_top(self):
        rows = [
            event(40, 10.10, "rpm_resume",
                  "dev.0 flags-0 cnt-0 dep-0 auto-1 p-0 irq-0 child-0"),
            event(40, 10.20, "rpm_idle",
                  "dev.0 flags-1 cnt-0 dep-0 auto-1 p-0 irq-0 child-0"),
            event(40, 10.25, "rpm_return_int", "rpm_idle+0x44/0x88:dev.0 ret=-11"),
            event(40, 10.40, "rpm_return_int", "rpm_resume+0x80/0x100:dev.0 ret=0"),
        ]
        pairs = account(old.good_trace(extra_window=rows))["pm_extension"]["runtime_pm_pairs"]
        self.assertEqual([(row["operation"], row["return"]) for row in pairs],
                         [("idle", -11), ("resume", 0)])
        self.assertAlmostEqual(pairs[0]["duration_seconds"], .05)
        self.assertAlmostEqual(pairs[1]["duration_seconds"], .30)

    def test_task_exit_reuse_and_comm_change_reject_all_pair_families(self):
        lifecycle = [
            event(40, 10.20, "sched_process_exit", "comm=worker pid=40 prio=120"),
            event(50, 10.25, "sched_process_fork",
                  "comm=parent pid=50 child_comm=worker child_pid=40"),
        ]
        families = (
            (event(40, 10.10, "device_pm_callback_start",
                   "drv dev, parent: p, ops[resume]"),
             event(40, 10.30, "device_pm_callback_end", "drv dev, err=0")),
            (event(40, 10.10, "suspend_resume", "phase[1] begin"),
             event(40, 10.30, "suspend_resume", "phase[1] end")),
            (event(40, 10.10, "rpm_resume",
                   "dev flags-0 cnt-0 dep-0 auto-1 p-0 irq-0 child-0"),
             event(40, 10.30, "rpm_return_int", "rpm_resume+0x4/0x8:dev ret=0")),
        )
        for begin, end in families:
            with self.subTest(begin=begin):
                with self.assertRaisesRegex(ValueError, "identity/lifecycle"):
                    account(old.good_trace(extra_window=[begin, *lifecycle, end]))
        comm_change = [event(40, 10.1, "rpm_idle",
                             "dev flags-0 cnt-0 dep-0 auto-1 p-0 irq-0 child-0",
                             task="old"),
                       event(40, 10.2, "rpm_return_int", "rpm_idle+0x4/0x8:dev ret=0",
                             task="new")]
        with self.assertRaisesRegex(ValueError, "identity/lifecycle"):
            account(old.good_trace(extra_window=comm_change))

    def test_runtime_mismatch_does_not_synthesize_pair_and_pending_rejects(self):
        rows = [event(40, 10.1, "rpm_suspend",
                      "dev.0 flags-0 cnt-1 dep-0 auto-1 p-0 irq-0 child-0"),
                event(40, 10.3, "rpm_return_int", "fn:other ret=0")]
        with self.assertRaises(ValueError):
            account(old.good_trace(extra_window=rows))

    def test_malformed_grammar_overflow_timestamp_and_wrong_base_trace_reject(self):
        cases = (
            [event(40, 10.2, "rpm_resume",
                   "bad name flags-0 cnt-1 dep-0 auto-1 p-0 irq-0 child-0")],
            [event(40, 10.2, "rpm_resume",
                   "dev flags-100000000 cnt-1 dep-0 auto-1 p-0 irq-0 child-0"),
             event(40, 10.3, "rpm_return_int", "fn:dev ret=0")],
            [event(30, 10.2, "suspend_resume", "a[99999999999] begin"),
             event(30, 10.3, "suspend_resume", "a[99999999999] end")],
            [event(30, 10.2, "suspend_resume", "a[1] begin", tgid=0)],
        )
        for rows in cases:
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    account(old.good_trace(extra_window=rows))
        # Inherited accounting still rejects loss before PM semantics run.
        raw = old.good_trace().replace(b"entries-written: 5/5", b"entries-written: 5/6")
        with self.assertRaises(ValueError):
            account(raw)

    def test_counts_split_event_region_cpu_and_drain_only_excluded(self):
        data = old.good_trace(
            extra_preroll=[event(44, 9.5, "rpm_return_int", "idle:x ret=0", cpu=1)],
            extra_drain=[event(44, 11.05, "rpm_return_int", "idle:x ret=0", cpu=3)])
        pm = account(data)["pm_extension"]
        counts = pm["counts_by_event_region_cpu"]["rpm/rpm_return_int"]
        self.assertEqual(counts["pre-roll"]["1"], 1)
        self.assertEqual(counts["drain"]["3"], 1)
        self.assertFalse(pm["absence_claim_supported"])

    def test_pair_saved_tgid_change_rejects_and_task_counts_are_retained(self):
        rows = [event(22, 10.2, "device_pm_callback_start",
                      "drv dev, parent: p, ops[resume]", tgid=22),
                event(22, 10.3, "device_pm_callback_end", "drv dev, err=0", tgid=23)]
        with self.assertRaises(ValueError):
            account(old.good_trace(extra_window=rows))
        rows[1] = event(22, 10.3, "device_pm_callback_end", "drv dev, err=0", tgid=22)
        pm = account(old.good_trace(extra_window=rows))["pm_extension"]
        self.assertEqual(pm["counts_by_task_pid_tgid"]["power/device_pm_callback_start"]
                         ["worker:22/22"], 1)
        self.assertEqual(pm["counts_by_normalized_paired_identity"]
                         ["callback:drv:dev:resume"], 2)

    def test_annotation_correlation_uses_uncertainty_interval_only(self):
        data = old.good_trace(extra_window=[
            event(22, 10.2, "device_pm_callback_start",
                  "sdp-hdmi dev, parent: p, ops[resume]"),
            event(22, 10.4, "device_pm_callback_end", "sdp-hdmi dev, err=0")])
        account(data)
        capture._ACTIVE_PM_REPORT = capture._ACTIVE_PM_REPORT
        mapped = {"rows": [{"dimension": "picture", "value": "black",
                            "tv_uptime_interval": [10.3, 10.6]}]}
        with mock.patch.object(capture, "_ORIGINAL_ASSESS_ANNOTATIONS",
                               return_value=mapped):
            capture.assess_annotations([], {}, None, True)
        correlation = capture._ACTIVE_PM_REPORT["sdp_hdmi_positive_correlations"][0]
        self.assertTrue(correlation["owner_annotation_correlations"][0]["overlaps"])


class PMDispatchTests(unittest.TestCase):
    def test_nested_patch_installs_and_restores_all_live_validators(self):
        branch, lower = capture._base._base, capture._base._base._base
        tracked = ((capture._base, ("build_remote_script", "validate_metadata",
                                    "trace_accounting", "assess_annotations")),
                   (branch, ("validate_metadata",)),
                   (lower, ("validate_metadata", "assess_annotations")))
        before = {(id(mod), name): getattr(mod, name) for mod, names in tracked for name in names}
        observed = {}

        def fake_branch_run(label, seconds, smoke_unobserved=False):
            self.assertIs(capture._base.build_remote_script, capture.build_remote_script)
            self.assertIs(branch.validate_metadata, capture.validate_metadata)
            self.assertIs(lower.validate_metadata, capture.validate_metadata)
            self.assertIs(lower.assess_annotations, capture.assess_annotations)
            result = branch.validate_metadata(metadata(), 123, "a" * 64, 85)
            report = capture.trace_accounting(old.good_trace(), fds()["tids"],
                                              7, 99, 10.0, 11.0, 11.1)
            observed.update(formats=result["pm_extension"]["seven_formats_exact"],
                            semantic=report["pm_extension"]["semantic_complete"])

        with mock.patch.object(capture._base, "_ORIGINAL_RUN", side_effect=fake_branch_run), \
                mock.patch.object(capture, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            capture.run_capture("fixture", 85)
        self.assertEqual(observed, {"formats": True, "semantic": True})
        for mod, names in tracked:
            for name in names:
                self.assertIs(getattr(mod, name), before[(id(mod), name)])
        with mock.patch.object(capture._base, "_ORIGINAL_RUN",
                               side_effect=RuntimeError("offline abort")):
            with self.assertRaisesRegex(RuntimeError, "offline abort"):
                capture.run_capture("fixture", 85)
        for mod, names in tracked:
            for name in names:
                self.assertIs(getattr(mod, name), before[(id(mod), name)])


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(old))
    for cls in (PMShellAndMetadataTests, PMTraceTests, PMDispatchTests):
        suite.addTests(loader.loadTestsFromTestCase(cls))
    return suite


if __name__ == "__main__":
    unittest.main(verbosity=2)
