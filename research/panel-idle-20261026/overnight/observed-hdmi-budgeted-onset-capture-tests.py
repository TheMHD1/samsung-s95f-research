#!/usr/bin/env python3
"""Offline tests for the budgeted HDMI collector; never contact the TV."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "observed-hdmi-budgeted-onset-capture.py"
SPEC = importlib.util.spec_from_file_location("budgeted_hdmi", SOURCE)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


def metadata_config(total=32768):
    return ("@@ TRACE_CONFIG\nPER_CPU_KB=8192\nTOTAL_KB=" + str(total) +
            "\nRECORD_TGID=record-tgid\n")


class BudgetedCollectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = capture.build_remote_script("fixture-full")
        cls.smoke = capture.build_remote_script("fixture-smoke", 5,
                                                allow_short=True)

    def test_pinned_ancestor_and_both_shells(self):
        self.assertEqual(hashlib.sha256(capture.ANCESTOR.read_bytes()).hexdigest(),
                         capture.ANCESTOR_SHA256)
        for shell, seconds in ((self.full, 180), (self.smoke, 5)):
            with self.subTest(seconds=seconds):
                subprocess.run(["/bin/sh", "-n"], input=shell, text=True,
                               check=True)
                self.assertIn(f"-v n={seconds}", shell)
                self.assertIn('echo mono >"$T/trace_clock"', shell)
                self.assertIn(capture.REMOTE_ROOT, shell)
                self.assertIn(capture.STAGE_ROOT, shell)
                self.assertIn(capture.TRACE_PREFIX, shell)
                self.assertNotIn(capture.ANCESTOR_REMOTE_ROOT, shell)
                self.assertNotIn(capture.ANCESTOR_STAGE_ROOT, shell)
                self.assertNotIn(capture.ANCESTOR_TRACE_PREFIX, shell)

    def test_vlog_writer_remote_manifest_and_host_limit_move_together(self):
        for shell in (self.full, self.smoke):
            self.assertEqual(shell.count(
                'ulimit -f 131072; exec /usr/bin/vlogutil'), 1)
            self.assertEqual(shell.count('vlog-after)L=134217728'), 1)
            self.assertNotIn('ulimit -f 65536; exec /usr/bin/vlogutil', shell)
            self.assertNotIn('vlog-after)L=67108864', shell)
        with capture._budget_context(runtime=True):
            for module in capture._LIMIT_MODULES:
                self.assertEqual(module.SIDECAR_LIMITS["vlog-after"],
                                 capture.VLOG_LIMIT)

    def test_ring_and_resource_preflight_are_exact_and_before_enable(self):
        for shell in (self.full, self.smoke):
            self.assertEqual(shell.count('echo 8192 >"$T/buffer_size_kb"'), 1)
            self.assertEqual(shell.count('test "$bt" -le 32768'), 1)
            guard = 'test "$dk" -ge 393216; test "$mk" -ge 393216'
            self.assertEqual(shell.count(guard), 1)
            self.assertLess(shell.index(guard), shell.index('mkdir "$T"'))
            self.assertLess(shell.index(guard), shell.index(
                'echo 1 >"$T/tracing_on"'))

    def test_metadata_budget_projection_and_ring_capacity(self):
        fake = {"pm_extension": {"cpu_stats": {
            "loss_free": True,
            "per_cpu": {str(cpu): {"bytes": 1000} for cpu in range(4)},
        }}}
        digest = hashlib.sha256(self.smoke.encode()).hexdigest()
        with mock.patch.object(capture, "_ORIGINAL_VALIDATE", return_value=fake):
            report = capture.validate_metadata(metadata_config(), len(self.smoke),
                                               digest, 5)
        self.assertEqual(report["budgeted_resources"]["total_kib"], 32768)
        self.assertEqual(report["budgeted_resources"]["per_cpu_kib"], 8192)
        self.assertFalse(report["budgeted_resources"]
                         ["capacity_qualified_for_180_seconds"])
        with mock.patch.object(capture, "_ORIGINAL_VALIDATE", return_value=fake):
            with self.assertRaisesRegex(ValueError, "does not match"):
                capture.validate_metadata(metadata_config(24576), len(self.smoke),
                                          digest, 5)
        capture._ring_validate(fake)
        bad = {"pm_extension": {"cpu_stats": {"loss_free": True,
               "per_cpu": {"0": {"bytes": 8 * 1024 * 1024}}}}}
        with self.assertRaisesRegex(ValueError, "reached 8 MiB"):
            capture._ring_validate(bad)

    def test_trace_budget_rejects_old_or_oversized_readback(self):
        for value in ("4096", "8193"):
            text = metadata_config().replace("8192", value, 1)
            with self.subTest(value=value), self.assertRaisesRegex(
                    ValueError, "per-CPU trace readback"):
                capture._trace_budget(text)
        with self.assertRaisesRegex(ValueError, "too large"):
            capture._trace_budget(metadata_config(32769))

    def test_manifest_uses_strict_128_mib_cap(self):
        original = capture._ORIGINAL_MANIFEST
        try:
            with capture._budget_context(runtime=True):
                capture._ORIGINAL_MANIFEST = lambda _text: {
                    "vlog-after": (capture.VLOG_LIMIT - 1, "0" * 64)}
                self.assertEqual(capture.parse_manifest("fixture")
                                 ["vlog-after"][0], capture.VLOG_LIMIT - 1)
                capture._ORIGINAL_MANIFEST = lambda _text: {
                    "vlog-after": (capture.VLOG_LIMIT, "0" * 64)}
                with self.assertRaisesRegex(ValueError, "reached 128 MiB"):
                    capture.parse_manifest("fixture")
        finally:
            capture._ORIGINAL_MANIFEST = original

    def test_only_180_observed_and_5_smoke(self):
        for seconds in (10, 60, 90, 179, 181, 240):
            with self.subTest(seconds=seconds), self.assertRaisesRegex(
                    ValueError, "observed mode is 180"):
                capture.build_remote_script("fixture", seconds)
        with self.assertRaises(ValueError):
            capture.build_remote_script("fixture", 180, allow_short=True)
        with self.assertRaises(ValueError):
            capture.build_remote_script("fixture", 5, allow_short=False)

    def test_dry_cli_records_unqualified_capacity(self):
        full = subprocess.run([sys.executable, str(SOURCE), "dry-full"],
                              check=True, capture_output=True, text=True)
        smoke = subprocess.run([sys.executable, str(SOURCE), "dry-smoke",
                                "--seconds", "5", "--smoke-unobserved"],
                               check=True, capture_output=True, text=True)
        a, b = json.loads(full.stdout), json.loads(smoke.stdout)
        self.assertEqual(a["vlog_limit_bytes"], 128 * 1024 * 1024)
        self.assertEqual(a["ring_per_cpu_kib"], 8192)
        self.assertEqual(a["memory_preflight_min_kib"], 393216)
        self.assertFalse(a["capacity_qualified_for_180_seconds"])
        self.assertEqual(b["capture_kind"], "smoke-unobserved")
        self.assertEqual(b["physical_state"], "unobserved")

    def test_nested_smoke_installs_builder_validator_caps_and_restores(self):
        seen = {}
        old_run = capture._long._short._frozen._ORIGINAL_RUN
        saved = (capture._long._nested_long_builder,
                 capture._long.validate_metadata, capture._long.parse_manifest,
                 capture._long._validate_ring_capacity,
                 capture._long._terminal.SIDECAR_LIMITS)
        def fake_run(label, seconds, smoke_unobserved=False):
            seen["args"] = (label, seconds, smoke_unobserved)
            seen["validator"] = capture._long._pm.validate_metadata
            seen["manifest"] = capture._long._terminal.parse_manifest
            seen["ring"] = capture._long._validate_ring_capacity
            seen["limit"] = capture._long._terminal.SIDECAR_LIMITS["vlog-after"]
            seen["shell"] = capture._long._short._pm.build_remote_script(
                label, seconds, allow_short=smoke_unobserved)
        capture._long._short._frozen._ORIGINAL_RUN = fake_run
        try:
            capture.run_capture("fixture-smoke", 5, smoke_unobserved=True)
        finally:
            capture._long._short._frozen._ORIGINAL_RUN = old_run
        self.assertEqual(seen["args"], ("fixture-smoke", 5, True))
        self.assertIs(seen["validator"], capture.validate_metadata)
        self.assertIs(seen["manifest"], capture.parse_manifest)
        self.assertIs(seen["ring"], capture._ring_validate)
        self.assertEqual(seen["limit"], capture.VLOG_LIMIT)
        self.assertIn('echo 8192 >"$T/buffer_size_kb"', seen["shell"])
        self.assertIn('vlog-after)L=134217728', seen["shell"])
        self.assertEqual((capture._long._nested_long_builder,
                          capture._long.validate_metadata,
                          capture._long.parse_manifest,
                          capture._long._validate_ring_capacity,
                          capture._long._terminal.SIDECAR_LIMITS), saved)

    def test_actual_nested_run_stages_budgeted_script_then_cleans_offline(self):
        staged = {}
        old_stage = capture._long._quiescent._ORIGINAL_STAGE
        def stop(label, script):
            staged.update(label=label, script=script)
            raise RuntimeError("offline-stage-sentinel")
        proc = SimpleNamespace(returncode=0, stdout="0\nCLEAN\n", stderr="")
        item = {"exit_code": 0, "timed_out": False, "stdout": "0\nCLEAN\n"}
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(capture._long._terminal, "BASE", Path(directory)), \
                mock.patch.object(capture._long._terminal, "cleanup_remote",
                                  return_value=(proc, item)) as cleanup, \
                mock.patch.object(capture._long._quiescent, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            capture._long._quiescent._ORIGINAL_STAGE = stop
            try:
                with self.assertRaisesRegex(RuntimeError, "offline-stage-sentinel"):
                    capture.run_capture("fixture-stage")
            finally:
                capture._long._quiescent._ORIGINAL_STAGE = old_stage
        shell = staged["script"].decode()
        subprocess.run(["/bin/sh", "-n"], input=shell, text=True, check=True)
        self.assertIn(capture.REMOTE_ROOT, shell)
        self.assertIn('echo 8192 >"$T/buffer_size_kb"', shell)
        self.assertIn('vlog-after)L=134217728', shell)
        cleanup.assert_called_once_with("fixture-stage")

    def test_accepted_smoke_is_rate_evidence_not_180_qualification(self):
        record = json.loads((HERE / "sleep-smoke-20261027a.onset" /
                             "record.json").read_text())
        self.assertTrue(record["accepted"] and record["cleanup_verified"])
        vlog = record["manifest"]["vlog-after"]["bytes"]
        span = record["vlog"]["last"] - record["vlog"]["first"]
        rate = vlog / span
        self.assertGreater(rate * 185, 64 * 1024 * 1024)
        self.assertLess(rate * 185, capture.VLOG_LIMIT)
        artifacts = (HERE / "sleep-smoke-20261027a.onset" /
                     "artifacts.txt").read_text(errors="replace")
        self.assertIn("MemAvailable:     351804 kB", artifacts)
        self.assertIn("970200", artifacts)


if __name__ == "__main__":
    unittest.main()
