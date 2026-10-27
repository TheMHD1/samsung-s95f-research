#!/usr/bin/env python3
"""Offline fixtures for pqe-policy-baseline.py; no TV/root/network calls."""

from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("pqe_policy_baseline", HERE / "pqe-policy-baseline.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

A = 0x10000000
VE = A + 0x5B21A0
VE_VPTR = A + 0x59CBF8
VE_STATE = 0x20000000
DLSR_GLOBAL = A + 0x5B24E0
DLSR_STATE = 0x21000000
QD_GLOBAL = A + 0x5BE2A4
QD = 0x30000000
QD_VPTR = A + 0x59F2E8
QD_INNER = 0x40000000
BACKEND = 0x50000000
BACKEND_VPTR = A + 0x5A152C
BACKEND_SLOT = A + 0x1C6275

MAPPING = """\
00010000-00153000 r-xp 00000000 b3:1a 1 /usr/bin/avocd
00163000-00179000 rw-p 00143000 b3:1a 1 /usr/bin/avocd
10000000-1058c000 r-xp 00000000 b3:1b 2 /prd/usr/lib/libave.so.0.1
1059c000-105a4000 r--p 0058c000 b3:1b 2 /prd/usr/lib/libave.so.0.1
105a4000-10640000 rw-p 00000000 00:00 0
20000000-20100000 rw-p 00000000 00:00 0 /dev/shm/shm_ave
21000000-21100000 rw-p 00000000 00:00 0 /dev/shm/shm_ave_dlsr
30000000-30001000 rw-p 00000000 00:00 0
40000000-40001000 rw-p 00000000 00:00 0
50000000-50001000 rw-p 00000000 00:00 0
""".strip()


def encode_words(words):
    raw = b"".join(word.to_bytes(4, "little") for word in words)
    return base64.b64encode(raw).decode()


def pointer_line(*, ve=VE, ve_vptr=VE_VPTR, qd_vptr=QD_VPTR,
                 dlsr_global=DLSR_GLOBAL, dlsr_state=DLSR_STATE,
                 backend_vptr=BACKEND_VPTR, backend_slot=BACKEND_SLOT,
                 backend_reads=2, backend_type=1):
    return " ".join(str(value) for value in (
        A, ve, ve_vptr, VE_STATE, dlsr_global, dlsr_state,
        QD_GLOBAL, QD, qd_vptr, QD_INNER,
        BACKEND, backend_vptr, backend_slot, backend_reads, backend_type,
    ))


def dd_stderr(counts):
    lines = []
    for count in counts:
        lines += [f"{count}+0 records in", f"{count}+0 records out",
                  f"{count * 4} bytes ({count * 4} B) copied, 0.001 s, 4 kB/s"]
    return "\n".join(lines) + "\n"


def fixture_response(*, pointers=None, pointers_end=None, mapping=MAPPING,
                     mapping_end=None, bad_ave_hash=False, truncate=None,
                     include_backend=True, bad_qd_header=False):
    pointers = pointers or pointer_line()
    pointers_end = pointers if pointers_end is None else pointers_end
    mapping_end = mapping if mapping_end is None else mapping_end
    identity = "\n".join((
        "00000000-0000-4000-8000-000000000000",
        "706",
        module.AVOC_PATH,
        "603",
        module.AVOC_SHA256 + "  " + module.AVOC_PATH,
        ("0" * 64 if bad_ave_hash else module.AVE_SHA256) + "  " + module.AVE_PATH,
    ))
    fields = {
        "UTC_START": "1793034000", "UPTIME_START": "55000.10 200000.20",
        "ID_START": identity, "MAPS_START": mapping, "POINTERS_START": pointers,
    }
    for index, (name, (_, _, count)) in enumerate(module.READ_LAYOUT.items(), 1):
        words = list(range(index * 100, index * 100 + count))
        if name == "qd_outer_header":
            words = [QD_VPTR + (4 if bad_qd_header else 0), QD_INNER, 0, 0,
                     BACKEND, 0, 1]
        if truncate == name:
            words = words[:-1]
        fields["READ_" + name] = encode_words(words)
    if include_backend:
        fields["READ_backend_cache"] = encode_words([207])
    fields.update({
        "POINTERS_END": pointers_end, "MAPS_END": mapping_end,
        "ID_END": identity, "UPTIME_END": "55000.30 200000.40", "UTC_END": "1793034001",
    })
    stdout = "".join("@@ " + name + "\n" + value + "\n" for name, value in fields.items())
    values = [int(token) for token in pointers.split()]
    values_end = [int(token) for token in pointers_end.split()]
    counts = [1] * (10 + values[13])
    counts += [count for _, _, count in module.READ_LAYOUT.values()]
    if include_backend:
        counts.append(1)
    counts += [1] * (10 + values_end[13])
    return {
        "model": module.MODEL, "authenticated": True, "uid": 0, "euid": 0,
        "root_persistence": "host-assisted",
        "global_system_files_unchanged_at_acquisition": True,
        "commands": [{"exit_code": 0, "timed_out": False,
                      "stdout": stdout, "stderr": dd_stderr(counts)}],
    }


class PolicyBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = module.static_contract()

    def test_default_is_dry_and_never_invokes_transport(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["pqe-policy-baseline.py"]), \
                patch.object(module.subprocess, "run") as run, \
                contextlib.redirect_stdout(output):
            module.main()
        run.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["physical_state"], "unobserved")

    def test_command_is_bounded_read_only_and_persistent_argv_is_pinned(self):
        command = module.build_command()
        self.assertLessEqual(len(command.encode()), 8192)
        self.assertIn("/proc/$P/mem", command)
        self.assertIn('mapok "$VV" 1324 || return 1', command)
        self.assertIn('mapok "$QV" 448 || return 1', command)
        self.assertIn('A+0x5a6a28', command)
        self.assertIn('A+0x5b24e0', command)
        self.assertIn('s=${s##*) }', command)
        self.assertNotIn("awk '{print $22}'", command)
        self.assertNotIn("/dev/", command.replace("/dev/null", ""))
        for forbidden in ("ioctl", "systemctl", "reboot", "kill ", "setFactory",
                          "SetGSR", "SetObject", "tracefs", "debugfs", "chmod", "mount "):
            self.assertNotIn(forbidden, command)
        source = (HERE / "pqe-policy-baseline.py").read_text()
        self.assertIn('"--persistent-only", "--timeout", "25"', source)

    def test_valid_typed_snapshot(self):
        summary = module.validate_response(fixture_response(), self.contract)
        self.assertTrue(summary["accepted"])
        self.assertEqual(summary["physical_state"], "unobserved")
        self.assertEqual(summary["video_enhancer"]["class"], "RoseMVideoEnhancer")
        self.assertFalse(summary["video_enhancer"]["dlsr_state_aliases_object_state"])
        self.assertEqual(summary["decoded"]["ve_dlsr_class"]["address"],
                         hex(DLSR_STATE + 0xB0))
        self.assertEqual(summary["qd"]["class"], "QDDimming")
        self.assertEqual(summary["backend"]["class"], "DimmingBackendRoseMQD")
        self.assertEqual(summary["decoded"]["backend_cache"]["words"], [207])

    def test_untyped_backend_omits_cache_without_rejecting_policy_snapshot(self):
        pointers = pointer_line(backend_vptr=A + 0x1234, backend_slot=0,
                                backend_reads=1, backend_type=0)
        summary = module.validate_response(
            fixture_response(pointers=pointers, include_backend=False), self.contract)
        self.assertTrue(summary["accepted"])
        self.assertFalse(summary["backend"]["typed"])
        self.assertNotIn("backend_cache", summary["decoded"])

    def test_remote_cannot_hide_exact_typed_backend(self):
        pointers = pointer_line(backend_type=0)
        with self.assertRaisesRegex(ValueError, "Incorrect backend type classification"):
            module.validate_response(
                fixture_response(pointers=pointers, include_backend=False), self.contract)

    def test_wrong_installed_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "Installed libave hash mismatch"):
            module.validate_response(fixture_response(bad_ave_hash=True), self.contract)

    def test_wrong_video_enhancer_singleton_or_vptr_rejected(self):
        cases = [pointer_line(ve=VE + 4), pointer_line(ve_vptr=VE_VPTR + 4)]
        for pointers in cases:
            with self.subTest(pointers=pointers), \
                    self.assertRaisesRegex(ValueError, "VideoEnhancer pointer/vptr"):
                module.validate_response(fixture_response(pointers=pointers), self.contract)

    def test_expected_numeric_vptr_must_be_in_libave_source_mapping(self):
        mapping = MAPPING.replace(
            "1059c000-105a4000 r--p 0058c000 b3:1b 2 /prd/usr/lib/libave.so.0.1",
            "1059c000-105a4000 r--p 00000000 00:00 0",
        )
        with self.assertRaisesRegex(ValueError, "libave-backed source range"):
            module.validate_response(fixture_response(mapping=mapping), self.contract)

    def test_wrong_qd_vptr_rejected(self):
        pointers = pointer_line(qd_vptr=QD_VPTR + 4, backend_type=0)
        with self.assertRaisesRegex(ValueError, "Unexpected QD vptr"):
            module.validate_response(
                fixture_response(pointers=pointers, include_backend=False), self.contract)

    def test_qd_header_must_match_guarded_pointer_chain(self):
        with self.assertRaisesRegex(ValueError, "QD outer header disagrees"):
            module.validate_response(fixture_response(bad_qd_header=True), self.contract)

    def test_wrong_dlsr_global_chain_rejected(self):
        pointers = pointer_line(dlsr_global=DLSR_GLOBAL + 4)
        with self.assertRaisesRegex(ValueError, "DLSR relocated global storage"):
            module.validate_response(fixture_response(pointers=pointers), self.contract)

    def test_pointer_change_rejected(self):
        end = pointer_line(ve_vptr=VE_VPTR + 4)
        with self.assertRaisesRegex(ValueError, "Pointer chain changed"):
            module.validate_response(fixture_response(pointers_end=end), self.contract)

    def test_changed_maps_rejected(self):
        changed = MAPPING + "\n60000000-60001000 rw-p 00000000 00:00 0"
        with self.assertRaisesRegex(ValueError, "Process maps changed"):
            module.validate_response(fixture_response(mapping_end=changed), self.contract)

    def test_truncated_memory_read_rejected(self):
        with self.assertRaisesRegex(ValueError, "Truncated memory read"):
            module.validate_response(
                fixture_response(truncate="qd_weber_policy"), self.contract)

    def test_unaligned_dynamic_pointer_rejected(self):
        pointers = pointer_line()
        values = pointers.split()
        values[3] = str(VE_STATE + 2)
        pointers = " ".join(values)
        with self.assertRaisesRegex(ValueError, "unaligned"):
            module.validate_response(fixture_response(pointers=pointers), self.contract)

    def test_failure_record_retains_raw_root_response(self):
        response = fixture_response(truncate="qd_weber_policy")
        completed = subprocess.CompletedProcess([], 0, json.dumps(response), "")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "failed.json"
            with patch.object(module.subprocess, "run", return_value=completed) as run:
                with self.assertRaisesRegex(ValueError, "Truncated memory read"):
                    module.run_capture(destination, self.contract)
            saved = json.loads(destination.read_text())
            self.assertFalse(saved["accepted"])
            self.assertIn("Truncated memory read", saved["error"])
            self.assertEqual(saved["transport"]["stdout"], json.dumps(response))
            argv = run.call_args.args[0]
            self.assertEqual(argv[2:7], ["root", "--persistent-only", "--timeout", "25", "--command"])
            self.assertLessEqual(len(argv[-1].encode()), module.MAX_COMMAND_BYTES)

    def test_preexisting_output_is_preserved_without_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "existing.json"
            destination.write_text("owner data\n")
            with patch.object(module.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    module.run_capture(destination, self.contract)
            run.assert_not_called()
            self.assertEqual(destination.read_text(), "owner data\n")

    def test_dangling_output_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "output.json"
            destination.symlink_to(Path(temporary) / "missing-target")
            with patch.object(module.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    module.run_capture(destination, self.contract)
            run.assert_not_called()
            self.assertTrue(destination.is_symlink())

    def test_host_timeout_retains_partial_bytes_without_retry(self):
        timeout = subprocess.TimeoutExpired("root-reader", 55, output=b"partial\x00out",
                                            stderr=b"partial error")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "timeout.json"
            with patch.object(module.subprocess, "run", side_effect=timeout) as run:
                with self.assertRaises(subprocess.TimeoutExpired):
                    module.run_capture(destination, self.contract)
            self.assertEqual(run.call_count, 1)
            saved = json.loads(destination.read_text())
            self.assertFalse(saved["accepted"])
            self.assertEqual(saved["transport"]["partial_stdout"],
                             {"encoding": "base64", "data": "cGFydGlhbABvdXQ="})
            self.assertIn("TimeoutExpired", saved["error"])

    def test_dd_error_or_extra_diagnostic_rejected(self):
        response = fixture_response()
        response["commands"][0]["stderr"] += "dd: injected read error\n"
        with self.assertRaisesRegex(ValueError, "dd diagnostic inventory"):
            module.validate_response(response, self.contract)


if __name__ == "__main__":
    unittest.main()
