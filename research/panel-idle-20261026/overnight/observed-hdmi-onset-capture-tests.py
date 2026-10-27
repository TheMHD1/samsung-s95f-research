#!/usr/bin/env python3
"""Offline tests for the 60-second HDMI derivative; never contact the TV."""
import hashlib
import base64
import gzip
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "observed-hdmi-onset-capture.py"

def load():
    spec = importlib.util.spec_from_file_location("observed_hdmi", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

capture = load()

class HdmiCaptureTests(unittest.TestCase):
    def test_pins_namespaces_duration_and_shell_syntax(self):
        self.assertEqual(hashlib.sha256(capture.SHORT_SOURCE.read_bytes()).hexdigest(),
                         capture.SHORT_SHA256)
        self.assertEqual(hashlib.sha256(capture.FROZEN_SOURCE.read_bytes()).hexdigest(),
                         capture.FROZEN_SHA256)
        shell = capture.build_remote_script("fixture")
        subprocess.run(["/bin/sh", "-n"], input=shell, text=True, check=True)
        self.assertIn("-v n=60", shell)
        self.assertIn(capture.REMOTE_ROOT, shell)
        self.assertIn(capture.STAGE_ROOT, shell)
        self.assertIn(capture.TRACE_PREFIX, shell)
        self.assertIn("CAPTURE_START", shell)
        self.assertIn("CAPTURE_END", shell)
        for marker in ("@@ KERNEL_$kt", "@@ KERNEL_${kt}_END",
                       "dmesg | gzip -c | base64", "ksnap START || exit 88",
                       "ksnap END || exit 89"):
            self.assertIn(marker, shell)
        self.assertNotIn("researcher-short-onset", shell)

    def test_rejects_other_windows_and_smoke_flag(self):
        for value in (5, 10, 30, 59, 61, 85):
            with self.assertRaisesRegex(ValueError, "fixed at 60"):
                capture.build_remote_script("fixture", value)
        with self.assertRaisesRegex(ValueError, "full physical-window"):
            capture.build_remote_script("fixture", 60, allow_short=True)

    def test_dry_default_and_live_guard_do_not_transport(self):
        result = subprocess.run([sys.executable, str(SOURCE), "fixture"],
                                check=True, capture_output=True, text=True)
        body = json.loads(result.stdout)
        self.assertEqual(body["mode"], "dry-run; no TV/network/root call")
        self.assertEqual(body["seconds"], 60)
        with mock.patch.object(capture, "run_capture", side_effect=AssertionError) as called, \
             mock.patch.object(sys, "argv", [str(SOURCE), "fixture", "--run"]):
            with self.assertRaisesRegex(ValueError, "--run and --reviewed"):
                capture.main()
        called.assert_not_called()

    def test_full_short_context_receives_hdmi_boundary(self):
        seen = {}
        old = capture._short._frozen._ORIGINAL_RUN
        def fake_run(label, seconds, smoke_unobserved=False):
            seen["shell"] = capture._short._pm.build_remote_script(
                label, seconds, allow_short=smoke_unobserved)
            seen["root"] = capture._short._pm.root
            seen["stage"] = capture._short._terminal.stage_script
        capture._short._frozen._ORIGINAL_RUN = fake_run
        try:
            capture.run_capture("fixture")
        finally:
            capture._short._frozen._ORIGINAL_RUN = old
        self.assertIn("-v n=60", seen["shell"])
        self.assertIn(capture.REMOTE_ROOT, seen["shell"])
        self.assertIs(seen["root"], capture._short.root)
        self.assertIs(seen["stage"], capture._short.stage_script)

    def test_kernel_artifact_fixture_is_lossless_when_within_cap(self):
        raw = b"[1.0] retained-kernel-line\\n"
        encoded = base64.b64encode(gzip.compress(raw)).decode()
        fixture = "@@ KERNEL_START\\nboot\\n1.00 0.00\\nBASE64_GZIP_BYTES=" + str(len(encoded)) + "\\n" + encoded + "\\n@@ KERNEL_START_END\\n"
        self.assertIn("@@ KERNEL_START", fixture)
        payload = fixture.split("BASE64_GZIP_BYTES=", 1)[1].split("\\n", 1)[1].split("\\n@@", 1)[0]
        self.assertEqual(gzip.decompress(base64.b64decode(payload)), raw)

    def test_main_validates_fixed_cli_before_execution(self):
        with mock.patch.object(sys, "argv", [str(SOURCE), "fixture", "--seconds", "30"]):
            with self.assertRaisesRegex(ValueError, "fixed at 60"):
                capture.main()

if __name__ == "__main__":
    unittest.main()
