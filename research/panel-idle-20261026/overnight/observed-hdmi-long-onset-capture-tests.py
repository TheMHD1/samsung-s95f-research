#!/usr/bin/env python3
"""Offline tests for the 180-second HDMI collector; never contact the TV."""

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
SOURCE = HERE / "observed-hdmi-long-onset-capture.py"


def load():
    spec = importlib.util.spec_from_file_location("observed_hdmi_long", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


capture = load()


def row(lo, hi, perms="rw-p", offset=0, device="00:00", inode=0, path=""):
    tail = " " + path if path else ""
    return f"{lo:08x}-{hi:08x} {perms} {offset:08x} {device} {inode}{tail}"


def synthetic_metadata(*, heap_end=0x20300000, heap_end_after=None,
                       start_maps=None, end_maps=None, dev_start=None, dev_end=None,
                       pointers_start=None, pointers_end=None):
    a = 0x10000000
    d = 0x40000000
    values = [
        a, a + 0x5be2a4, 0x20001000, a + 0x59f2e8, 0x20002000,
        0x20003000, a + 0x5a152c, a + 0x1c6275,
        d, d + 0x12af7c,
        0x40010000, 0x40010000, 0, 0x40011000, 0x40011000, 0,
        0x40010000, 0x40011000, 0x40012000, 0x40013000, 0x40014000,
        d + 0x128a28, d + 0x128a90, d + 0x128ab0,
    ]
    heap_end_after = heap_end if heap_end_after is None else heap_end_after
    av0 = start_maps or [
        row(a, a + 0x700000, "r-xp", 0, "08:01", 11, capture.AVE_PATH),
        row(0x20000000, heap_end, "rw-p", 0, "00:00", 0, "[heap]"),
    ]
    av1 = end_maps or [
        row(a, a + 0x700000, "r-xp", 0, "08:01", 11, capture.AVE_PATH),
        row(0x20000000, heap_end_after, "rw-p", 0, "00:00", 0, "[heap]"),
    ]
    dm0 = dev_start or [row(d, d + 0x200000, "r-xp", 0, "08:01", 22,
                            capture.DEV_PATH)]
    dm1 = dev_end or list(dm0)
    ps = pointers_start or values
    pe = pointers_end or list(ps)
    return "\n".join((
        "@@ POINTERS_START", " ".join(map(str, ps)),
        "@@ AVOC_MAPS_START", "\n".join(av0),
        "@@ DEV_MAPS_START", "\n".join(dm0),
        "@@ POINTERS_END", " ".join(map(str, pe)),
        "@@ AVOC_MAPS_END", "\n".join(av1),
        "@@ DEV_MAPS_END", "\n".join(dm1),
    ))


class LongHdmiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shell = capture.build_remote_script("fixture")
        cls.smoke_shell = capture.build_remote_script(
            "fixture-smoke", 5, allow_short=True)
        cls.contract = capture._extract_sampler_contract(cls.shell)

    def test_pins_dependencies_and_generated_shell(self):
        self.assertEqual(hashlib.sha256(capture.HDMI_SOURCE.read_bytes()).hexdigest(),
                         capture.HDMI_SHA256)
        self.assertEqual(hashlib.sha256(capture.DESIGN.read_bytes()).hexdigest(),
                         capture.DESIGN_SHA256)
        subprocess.run(["/bin/sh", "-n"], input=self.shell, text=True, check=True)
        subprocess.run(["/bin/sh", "-n"], input=self.smoke_shell,
                       text=True, check=True)
        self.assertIn("-v n=183", self.shell)
        self.assertIn("-v n=180", self.shell)
        self.assertIn("sleep 900", self.shell)
        self.assertIn('echo mono >"$T/trace_clock"', self.shell)
        self.assertIn('printf "TRACE_CLOCK="; cat "$T/trace_clock"', self.shell)
        self.assertIn(capture.REMOTE_ROOT, self.shell)
        self.assertIn(capture.STAGE_ROOT, self.shell)
        self.assertIn(capture.TRACE_PREFIX, self.shell)
        self.assertNotIn("researcher-observed-hdmi-onset-20261027/fixture", self.shell)
        self.assertIn("sample-errors)L=1048576", self.shell)
        self.assertNotIn("sample-errors)L=262144", self.shell)
        self.assertIn('test "$1" -lt "$L"; echo "SIDECAR', self.shell)
        self.assertIn("-v n=5", self.smoke_shell)
        self.assertIn('echo mono >"$T/trace_clock"', self.smoke_shell)
        self.assertIn(capture.REMOTE_ROOT, self.smoke_shell)
        self.assertEqual(capture._extract_sampler_contract(self.smoke_shell),
                         self.contract)
        identities = capture.source_identities()
        self.assertEqual(set(identities), {
            "frozen_hdmi_60", "frozen_short_30", "frozen_quiescent_pm",
            "frozen_pm", "frozen_preroll", "frozen_branch",
            "frozen_terminal", "long_window_design"})
        for item in identities.values():
            self.assertEqual(hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest(),
                             item["sha256"])

    def test_error_writer_and_validator_caps_move_together(self):
        self.assertEqual(capture.SAMPLE_ERROR_LIMIT, 1024 * 1024)
        self.assertEqual(capture.LONG_Q_SAMPLER_BYTES.count(b"ulimit -f 1024"), 1)
        self.assertNotIn(b'ulimit -f 256; dd if=/proc/$4/mem',
                         capture.LONG_Q_SAMPLER_BYTES)
        subprocess.run(["/bin/sh", "-n"], input=capture.LONG_Q_SAMPLER_BYTES,
                       check=True)
        self.assertEqual(self.shell.count('ulimit -f 1024; dd if=/proc/'), 2)
        self.assertEqual(self.shell.count('ulimit -f 1024; cat "$QE"'), 1)
        self.assertEqual(self.shell.count('ulimit -f 1024; cat "$QSE"'), 1)
        # The monitor samples writer remains the inherited, separately bounded file.
        self.assertEqual(self.shell.count('(ulimit -f 256; while awk'), 1)

    def test_sampler_contract_is_generated_and_complete(self):
        self.assertEqual(len(self.contract), 27)
        self.assertIn(("$((A+0x5bfc5c))", 38, "avoc"), self.contract)
        self.assertIn(("$EA", 1, "deviced"), self.contract)
        with self.assertRaisesRegex(ValueError, "unknown generated sampler"):
            capture._evaluate_expression("$((UNKNOWN+0x4))", {"A": 1})
        changed = self.shell.replace('"$EA:1:$dm:$dp"', '"$NEW:1:$dm:$dp"', 1)
        with self.assertRaisesRegex(ValueError, "unknown generated sampler"):
            capture._extract_sampler_contract(changed)

    def test_private_ring_must_be_loss_free_and_strictly_below_capacity(self):
        def report(value, loss_free=True):
            return {"pm_extension": {"cpu_stats": {
                "loss_free": loss_free, "per_cpu": {"0": {"bytes": value}}}}}
        good = report(4096 * 1024 - 1)
        capture._validate_ring_capacity(good)
        self.assertTrue(good["long_window_ring_capacity"]["strictly_below_limit"])
        with self.assertRaisesRegex(ValueError, "reached capacity"):
            capture._validate_ring_capacity(report(4096 * 1024))
        with self.assertRaisesRegex(ValueError, "report absent"):
            capture._validate_ring_capacity(report(1, loss_free=False))

    def test_only_180_observed_and_5_second_smoke_are_supported(self):
        for value in (10, 30, 60, 85, 90, 179, 181, 240):
            with self.subTest(value=value), self.assertRaisesRegex(
                    ValueError, "observed mode is 180"):
                capture.build_remote_script("fixture", value)
        with self.assertRaisesRegex(ValueError, "observed mode is 180"):
            capture.build_remote_script("fixture", 180, allow_short=True)
        with self.assertRaisesRegex(ValueError, "observed mode is 180"):
            capture.build_remote_script("fixture", 5, allow_short=False)

    def test_dry_default_and_review_guard_make_no_transport(self):
        result = subprocess.run([sys.executable, str(SOURCE), "fixture"], check=True,
                                capture_output=True, text=True)
        body = json.loads(result.stdout)
        self.assertEqual(body["mode"], "dry-run; no TV/network/root call")
        self.assertEqual(body["seconds"], 180)
        self.assertEqual(body["sample_error_limit_bytes"], 1048576)
        self.assertTrue(body["physical_annotation_required"])
        self.assertEqual(body["trace_clock"],
                         "private instance explicitly set/read back as mono")
        smoke = subprocess.run(
            [sys.executable, str(SOURCE), "fixture-smoke", "--seconds", "5",
             "--smoke-unobserved"], check=True, capture_output=True, text=True)
        smoke_body = json.loads(smoke.stdout)
        self.assertEqual(smoke_body["capture_kind"], "smoke-unobserved")
        self.assertEqual(smoke_body["seconds"], 5)
        self.assertEqual(smoke_body["physical_state"], "unobserved")
        self.assertFalse(smoke_body["physical_annotation_required"])
        self.assertEqual(len(smoke_body["source_identities"]), 8)
        with mock.patch.object(capture, "run_capture", side_effect=AssertionError) as called, \
             mock.patch.object(sys, "argv", [str(SOURCE), "fixture", "--run"]):
            with self.assertRaisesRegex(ValueError, "--run and --reviewed"):
                capture.main()
        called.assert_not_called()

    def test_public_run_installs_nested_builder_validators_limits_and_restores(self):
        seen = {}
        old_run = capture._short._frozen._ORIGINAL_RUN
        saved = (capture._pm.validate_metadata, capture._terminal.parse_manifest,
                 capture._branch.Q_SAMPLER_BYTES,
                 capture._terminal.SIDECAR_LIMITS["sample-errors"])
        def fake_run(label, seconds, smoke_unobserved=False):
            seen["seconds"] = seconds
            seen["validator"] = capture._pm.validate_metadata
            seen["manifest"] = capture._terminal.parse_manifest
            seen["limit"] = capture._terminal.SIDECAR_LIMITS["sample-errors"]
            seen["q"] = capture._branch.Q_SAMPLER_BYTES
            seen["shell"] = capture._short._pm.build_remote_script(
                label, seconds, allow_short=smoke_unobserved)
        capture._short._frozen._ORIGINAL_RUN = fake_run
        try:
            capture.run_capture("fixture")
        finally:
            capture._short._frozen._ORIGINAL_RUN = old_run
        self.assertEqual(seen["seconds"], 180)
        self.assertIs(seen["validator"], capture.validate_metadata)
        self.assertIs(seen["manifest"], capture.parse_manifest)
        self.assertEqual(seen["limit"], 1048576)
        self.assertEqual(seen["q"], capture.LONG_Q_SAMPLER_BYTES)
        self.assertIn("sample-errors)L=1048576", seen["shell"])
        self.assertEqual((capture._pm.validate_metadata, capture._terminal.parse_manifest,
                          capture._branch.Q_SAMPLER_BYTES,
                          capture._terminal.SIDECAR_LIMITS["sample-errors"]), saved)

    def test_public_smoke_run_passes_unobserved_mode_through_nested_builder(self):
        seen = {}
        old_run = capture._short._frozen._ORIGINAL_RUN
        def frozen_metadata(_text, script_size, script_sha, seconds):
            seen["metadata_call"] = (script_size, script_sha, seconds)
            return {"pm_extension": {"cpu_stats": {
                "loss_free": True,
                "per_cpu": {"0": {"bytes": 1024}},
            }}}
        def fake_run(label, seconds, smoke_unobserved=False):
            seen["label"] = label
            seen["seconds"] = seconds
            seen["smoke"] = smoke_unobserved
            seen["shell"] = capture._short._pm.build_remote_script(
                label, seconds, allow_short=smoke_unobserved)
            raw = seen["shell"].encode()
            digest = hashlib.sha256(raw).hexdigest()
            seen["metadata"] = capture._pm.validate_metadata(
                synthetic_metadata(), len(raw), digest, seconds)
        capture._short._frozen._ORIGINAL_RUN = fake_run
        try:
            with mock.patch.object(capture, "_ORIGINAL_PM_VALIDATE",
                                   side_effect=frozen_metadata):
                capture.run_capture("fixture-smoke", 5, smoke_unobserved=True)
        finally:
            capture._short._frozen._ORIGINAL_RUN = old_run
        self.assertEqual((seen["label"], seen["seconds"], seen["smoke"]),
                         ("fixture-smoke", 5, True))
        self.assertIn("-v n=5", seen["shell"])
        self.assertIn("sample-errors)L=1048576", seen["shell"])
        self.assertEqual(seen["metadata_call"][2], 5)
        self.assertEqual(seen["metadata"]["long_window_mode"], {
            "seconds": 5, "smoke_unobserved": True,
            "physical_window_eligible": False})

    def test_script_hash_binds_metadata_duration_and_mode(self):
        digest = hashlib.sha256(self.smoke_shell.encode()).hexdigest()
        with mock.patch.object(capture, "_ORIGINAL_PM_VALIDATE",
                               return_value={"pm_extension": {"cpu_stats": {
                                   "loss_free": True,
                                   "per_cpu": {"0": {"bytes": 1}}}}}):
            with self.assertRaisesRegex(ValueError, "duration/mode mismatch"):
                capture.validate_metadata(synthetic_metadata(), len(self.smoke_shell),
                                          digest, 180)

    def test_public_run_restores_after_exception(self):
        old_run = capture._short._frozen._ORIGINAL_RUN
        saved = (capture._pm.validate_metadata, capture._terminal.parse_manifest,
                 capture._branch.Q_SAMPLER_BYTES)
        capture._short._frozen._ORIGINAL_RUN = mock.Mock(side_effect=RuntimeError("fixture"))
        try:
            with self.assertRaisesRegex(RuntimeError, "fixture"):
                capture.run_capture("fixture")
        finally:
            capture._short._frozen._ORIGINAL_RUN = old_run
        self.assertEqual((capture._pm.validate_metadata, capture._terminal.parse_manifest,
                          capture._branch.Q_SAMPLER_BYTES), saved)

    def test_actual_nested_run_stages_180_script_and_cleans_without_transport(self):
        staged = {}
        old_stage = capture._quiescent._ORIGINAL_STAGE
        def stop_at_stage(label, script):
            staged.update(label=label, script=script)
            raise RuntimeError("offline-stage-sentinel")
        clean_proc = SimpleNamespace(returncode=0, stdout="0\nCLEAN\n", stderr="")
        clean_item = {"exit_code": 0, "timed_out": False,
                      "stdout": "0\nCLEAN\n"}
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(capture._terminal, "BASE", Path(directory)), \
                mock.patch.object(capture._terminal, "cleanup_remote",
                                  return_value=(clean_proc, clean_item)) as cleanup, \
                mock.patch.object(capture._quiescent, "_ORIGINAL_ROOT",
                                  side_effect=AssertionError("transport attempted")):
            capture._quiescent._ORIGINAL_STAGE = stop_at_stage
            try:
                with self.assertRaisesRegex(RuntimeError, "offline-stage-sentinel"):
                    capture.run_capture("fixture-stage")
            finally:
                capture._quiescent._ORIGINAL_STAGE = old_stage
        self.assertEqual(staged["label"], "fixture-stage")
        rendered = staged["script"].decode()
        subprocess.run(["/bin/sh", "-n"], input=rendered, text=True, check=True)
        self.assertIn("-v n=180", rendered)
        self.assertIn(capture.REMOTE_ROOT, rendered)
        self.assertNotIn("researcher-observed-hdmi-onset-20261027/", rendered)
        cleanup.assert_called_once_with("fixture-stage")

    def test_main_reviewed_smoke_dispatch_remains_offline_in_fixture(self):
        with mock.patch.object(sys, "argv", [str(SOURCE), "fixture-cli-smoke",
                                             "--seconds", "5", "--smoke-unobserved",
                                             "--run", "--reviewed"]), \
                mock.patch.object(capture, "run_capture") as run:
            capture.main()
        run.assert_called_once_with("fixture-cli-smoke", 5,
                                    smoke_unobserved=True)

    def test_exact_maps_and_monotonic_heap_growth_pass(self):
        exact = capture.validate_map_policy(synthetic_metadata(), self.contract)
        self.assertIsNone(exact["heap_growth"])
        grown = capture.validate_map_policy(
            synthetic_metadata(heap_end_after=0x20303000), self.contract)
        self.assertEqual(grown["heap_growth"]["end_high"], 0x20303000)
        self.assertEqual(grown["generated_sampler_spans"], len(self.contract))
        self.assertFalse(grown["whole_heap_content_stable"])

    def test_actual_program_b_single_heap_growth_fixture_passes_policy_only(self):
        meta = (HERE / "ugoos-program_b-20261027a.onset" / "meta.txt").read_text()
        report = capture.validate_map_policy(meta, self.contract)
        self.assertEqual(report["heap_growth"], {
            "low": 0x020cd000, "start_high": 0x022d4000,
            "end_high": 0x022d7000})

    def test_heap_shrink_and_identity_mutations_reject(self):
        base0 = row(0x10000000, 0x10700000, "r-xp", 0, "08:01", 11,
                    capture.AVE_PATH)
        start_heap = row(0x20000000, 0x20300000, "rw-p", 0, "00:00", 0, "[heap]")
        mutations = {
            "shrink": row(0x20000000, 0x202ff000, "rw-p", 0, "00:00", 0, "[heap]"),
            "low": row(0x20001000, 0x20301000, "rw-p", 0, "00:00", 0, "[heap]"),
            "perms": row(0x20000000, 0x20301000, "r--p", 0, "00:00", 0, "[heap]"),
            "offset": row(0x20000000, 0x20301000, "rw-p", 0x1000, "00:00", 0, "[heap]"),
            "device": row(0x20000000, 0x20301000, "rw-p", 0, "00:01", 0, "[heap]"),
            "inode": row(0x20000000, 0x20301000, "rw-p", 0, "00:00", 1, "[heap]"),
            "path": row(0x20000000, 0x20301000, "rw-p", 0, "00:00", 0, "[anon]"),
        }
        for name, changed in mutations.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                capture.validate_map_policy(synthetic_metadata(
                    start_maps=[base0, start_heap], end_maps=[base0, changed]), self.contract)

    def test_other_map_add_remove_reorder_or_change_rejects(self):
        base0 = row(0x10000000, 0x10700000, "r-xp", 0, "08:01", 11,
                    capture.AVE_PATH)
        heap0 = row(0x20000000, 0x20300000, "rw-p", 0, "00:00", 0, "[heap]")
        extra = row(0x30000000, 0x30001000, "r--p", 0, "00:00", 0, "[anon]")
        cases = ([base0, heap0, extra], [heap0, base0],
                 [row(0x10000000, 0x10701000, "r-xp", 0, "08:01", 11,
                      capture.AVE_PATH), heap0])
        for end in cases:
            with self.subTest(end=end), self.assertRaises(ValueError):
                capture.validate_map_policy(synthetic_metadata(
                    start_maps=[base0, heap0], end_maps=end), self.contract)

    def test_deviced_map_and_pointer_changes_reject(self):
        dm0 = row(0x40000000, 0x40200000, "r-xp", 0, "08:01", 22,
                  capture.DEV_PATH)
        with self.assertRaisesRegex(ValueError, "deviced maps changed"):
            capture.validate_map_policy(synthetic_metadata(
                dev_start=[dm0], dev_end=[dm0.replace("40200000", "40201000")]),
                self.contract)
        text = synthetic_metadata()
        part = capture._pm.sections(text)
        values = [int(x) for x in part["POINTERS_END"].split()]
        values[4] += 4
        with self.assertRaisesRegex(ValueError, "pointer/backend chain changed"):
            capture.validate_map_policy(synthetic_metadata(pointers_end=values), self.contract)

    def test_ambiguous_or_outside_common_heap_span_rejects(self):
        base0 = row(0x10000000, 0x10700000, "r-xp", 0, "08:01", 11,
                    capture.AVE_PATH)
        heap0 = row(0x20000000, 0x20300000, "rw-p", 0, "00:00", 0, "[heap]")
        overlap = row(0x20000000, 0x20300000, "r--p", 0, "00:00", 0, "[anon]")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            capture.validate_map_policy(synthetic_metadata(
                start_maps=[base0, heap0, overlap], end_maps=[base0, heap0, overlap]),
                self.contract)
        text = synthetic_metadata(heap_end=0x20001010, heap_end_after=0x20002000)
        with self.assertRaises(ValueError):
            capture.validate_map_policy(text, self.contract)

    def test_manifest_rejects_exact_limit_and_accepts_below(self):
        names = tuple(capture._terminal.SIDECAR_LIMITS)
        digest = "0" * 64
        def body(error_size):
            rows = []
            for name in names:
                size = error_size if name == "sample-errors" else 1
                rows.append(f"SIDECAR {name} {size} {digest}")
            return "\n".join(rows + ["CAPTURE_COMPLETE"])
        with capture._dependency_context(runtime=True):
            report = capture.parse_manifest(body(capture.SAMPLE_ERROR_LIMIT - 1))
            self.assertEqual(report["sample-errors"][0], capture.SAMPLE_ERROR_LIMIT - 1)
            with self.assertRaisesRegex(ValueError, "reached capacity"):
                capture.parse_manifest(body(capture.SAMPLE_ERROR_LIMIT))

    def test_malformed_full_map_fields_reject(self):
        bad = (
            "1000-1000 rw-p 00000000 00:00 0 [heap]",
            "1000-2000 zzzp 00000000 00:00 0 [heap]",
            "1000-2000 rw-p nope 00:00 0 [heap]",
            "1000-2000 rw-p 00000000 bad 0 [heap]",
            "1000-2000 rw-p 00000000 00:00 inode [heap]",
        )
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                capture.parse_full_maps(value)


if __name__ == "__main__":
    unittest.main()
