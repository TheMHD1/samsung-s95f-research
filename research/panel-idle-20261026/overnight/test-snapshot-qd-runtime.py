#!/usr/bin/env python3
"""Offline acquisition-integrity tests; subprocess is mocked for all stage tests."""
from pathlib import Path
import base64
import importlib.util
import json
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("qd_runtime_reader", HERE / "snapshot-qd-runtime.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class Integrity(unittest.TestCase):
    def test_retained_memory_ranges_and_bytes(self):
        for name, expected_bytes in [
            ("runtime-qd-duty-cache-20261026T115305Z.json", 108),
            ("runtime-deviced-state-20261026T114500Z.json", 120),
        ]:
            record = json.loads((HERE / name).read_text())
            reply = record["commands"][0]
            mapped = reply["stdout"].split("MAPS_BEFORE\n", 1)[1].split("END_MAPS_BEFORE", 1)[0]
            mapping = reader.maps(mapped)
            total = 0
            for word in record["decoded"].values():
                address, count = int(word["address"], 16), len(word["words"])
                reader.check_range(mapping, address, count)
                encoded = base64.b64encode(bytes.fromhex(word["bytes"])).decode()
                self.assertEqual(reader.decode(encoded, count), word["words"])
                total += count * 4
            self.assertEqual(total, expected_bytes)
            reader.check_dd_stderr(reply["stderr"])

    def test_incomplete_or_invalid_memory_rejected(self):
        for text, count in [("AQAAAA==", 2), ("", 1), ("!!!!", 1), ("AQAAAA==extra", 1)]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                reader.decode(text, count)

    def test_memory_bounds_and_alignment(self):
        mapping = [(0x1000, 0x1010, "r--p", 0, "")]
        reader.check_range(mapping, 0x100C, 1)
        for address, count in [(0x100C, 2), (0x1001, 1), (0, 1), (0x1000, 7)]:
            with self.subTest(address=address), self.assertRaises(ValueError):
                reader.check_range(mapping, address, count)
        with self.assertRaises(ValueError):
            reader.check_range([(0x1000, 0x1010, "---p", 0, "")], 0x1000, 1)

    def test_extra_output_and_dd_errors_rejected(self):
        for text in ["unexpected\n@@ A\n1", "@@ A\n1\n@@ A\n2"]:
            with self.assertRaises(ValueError):
                reader.blocks(text)
        for text in ["dd: error reading: Input/output error", "dd: invalid number", "4 bytes copied"]:
            with self.assertRaises(ValueError):
                reader.check_dd_stderr(text)

    def fixture(self, *, end_start_ticks=9, end_pid=706, end_bias=0x10000000,
                byte_text="AQAAAA==", stderr=""):
        lines = ["@@ UTC", "fixture UTC"]
        for suffix in ["", "_END"]:
            pid = end_pid if suffix else 706
            ticks = end_start_ticks if suffix else 9
            bias = end_bias if suffix else 0x10000000
            stat = f"{pid} (avocd) " + " ".join(["S"] + ["0"] * 18 + [str(ticks)])
            values = {"BOOT": "00000000-0000-4000-8000-000000000000", "PID": str(pid),
                      "EXE": "/usr/bin/avocd", "STAT": stat,
                      "HASH": reader.SHA + "  " + reader.SOURCE, "UPTIME": "100.1 200.0",
                      "MAPS": f"{bias:08x}-{bias+0x600000:08x} r-xp 00000000 00:00 1 {reader.SOURCE}"}
            for name, value in values.items():
                lines += ["@@ " + name + suffix, value]
            if not suffix:
                lines += ["@@ READ_word", byte_text]
        response = {"model": "QN77S95FAFXZC", "authenticated": True, "uid": 0, "euid": 0,
                    "root_persistence": "host-assisted",
                    "global_system_files_unchanged_at_acquisition": True,
                    "commands": [{"exit_code": 0, "timed_out": False,
                                  "stdout": "\n".join(lines) + "\n", "stderr": stderr}]}
        return SimpleNamespace(returncode=0, stdout=json.dumps(response), stderr="")

    def stage(self, result, capture=None):
        if capture is None:
            capture = reader.Capture(Path(self.directory.name) / "sample.json", "unobserved")
        with patch.object(reader.subprocess, "run", return_value=result) as mocked:
            decoded = capture.stage("fixture", {"word": (0x10000000, 1)})
            self.assertEqual(mocked.call_count, 1)
        return capture, decoded

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def test_valid_bracketed_capture(self):
        capture, decoded = self.stage(self.fixture())
        self.assertEqual(decoded, {"word": [1]})
        self.assertEqual(capture.expected_identity["start_ticks"], 9)
        self.assertFalse(capture.record["accepted"])  # A single stage isn't the full capture.

    def test_pid_reuse_mapping_change_and_partial_read_rejected(self):
        for arguments in [{"end_start_ticks": 10}, {"end_pid": 707},
                          {"end_bias": 0x20000000}, {"byte_text": "AQAA"}]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.stage(self.fixture(**arguments))

    def test_bias_change_between_stages_rejected(self):
        capture = reader.Capture(Path(self.directory.name) / "bias.json", "unobserved")
        capture.expected_bias = 0x20000000
        with self.assertRaisesRegex(ValueError, "bias changed"):
            self.stage(self.fixture(), capture)


if __name__ == "__main__":
    unittest.main()
