#!/usr/bin/env python3
"""Offline tests for the 30-second observed derivative; never contact the TV."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "observed-short-onset-capture.py"

def load():
    spec = importlib.util.spec_from_file_location("observed_short", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

capture = load()

class ShortCaptureTests(unittest.TestCase):
    def test_pin_namespace_duration_and_shell_syntax(self):
        self.assertEqual(hashlib.sha256(capture.FROZEN_SOURCE.read_bytes()).hexdigest(),
                         capture.FROZEN_SHA256)
        shell = capture.build_remote_script("fixture")
        subprocess.run(["/bin/sh", "-n"], input=shell, text=True, check=True)
        self.assertIn("-v n=30", shell)
        self.assertIn(capture.REMOTE_ROOT, shell)
        self.assertIn(capture.STAGE_ROOT, shell)
        self.assertIn(capture.TRACE_PREFIX, shell)
        self.assertNotIn(capture._frozen.REMOTE_ROOT, shell)
        self.assertNotIn(capture._frozen.STAGE_ROOT, shell)
        self.assertNotIn(capture._frozen.TRACE_PREFIX, shell)
        self.assertIn("CAPTURE_START", shell)
        self.assertIn("CAPTURE_END", shell)

    def test_only_fixed_30_allowed(self):
        for value in (5, 10, 29, 31, 85):
            with self.assertRaisesRegex(ValueError, "fixed at 30"):
                capture.build_remote_script("fixture", value)
        with self.assertRaisesRegex(ValueError, "full physical-window"):
            capture.build_remote_script("fixture", 30, allow_short=True)

    def test_dry_default_and_live_guard_without_transport(self):
        result = subprocess.run([sys.executable, str(SOURCE), "fixture"],
                                check=True, capture_output=True, text=True)
        body = json.loads(result.stdout)
        self.assertEqual(body["mode"], "dry-run; no TV/network/root call")
        self.assertEqual(body["seconds"], 30)
        self.assertTrue(body["physical_annotation_required"])
        with mock.patch.object(capture, "run_capture", side_effect=AssertionError) as called, \
             mock.patch.object(sys, "argv", [str(SOURCE), "fixture", "--run"]):
            with self.assertRaisesRegex(ValueError, "--run and --reviewed"):
                capture.main()
        called.assert_not_called()

    def test_full_inherited_context_gets_only_short_boundary_hooks(self):
        seen = {}
        def fake_run(label, seconds, smoke_unobserved=False):
            seen["shell"] = capture._frozen.build_remote_script(label, seconds)
            seen["stage"] = capture._frozen.stage_script(label, b"x")
            seen["root"] = capture._frozen.root
        old_stage = capture._frozen._ORIGINAL_STAGE
        capture._frozen._ORIGINAL_STAGE = lambda label, script: {
            "path": capture._frozen.STAGE_ROOT + "/" + label + "/capture.sh",
            "bytes": len(script), "sha256": "x", "chunks": 1,
            "persistent_only": True, "expiry_seconds": 1}
        try:
            with mock.patch.object(capture._frozen, "run_capture", side_effect=fake_run):
                capture.run_capture("fixture")
        finally:
            capture._frozen._ORIGINAL_STAGE = old_stage
        self.assertIn(capture.REMOTE_ROOT, seen["shell"])
        self.assertEqual(seen["stage"]["path"], capture.STAGE_ROOT + "/fixture/capture.sh")
        self.assertIs(seen["root"], capture.root)

    def test_frozen_runner_context_reaches_keyword_terminal_builder(self):
        seen = {}
        def fake_terminal_run(label, seconds, smoke_unobserved=False):
            seen["shell"] = capture._pm.build_remote_script(
                label, seconds, allow_short=smoke_unobserved)
            seen["root"] = capture._pm.root
            seen["stage"] = capture._terminal.stage_script
        old = capture._frozen._ORIGINAL_RUN
        capture._frozen._ORIGINAL_RUN = fake_terminal_run
        try:
            capture.run_capture("fixture")
        finally:
            capture._frozen._ORIGINAL_RUN = old
        self.assertIn("-v n=30", seen["shell"])
        self.assertIn(capture.REMOTE_ROOT, seen["shell"])
        self.assertIs(seen["root"], capture.root)
        self.assertIs(seen["stage"], capture.stage_script)

if __name__ == "__main__":
    unittest.main()
