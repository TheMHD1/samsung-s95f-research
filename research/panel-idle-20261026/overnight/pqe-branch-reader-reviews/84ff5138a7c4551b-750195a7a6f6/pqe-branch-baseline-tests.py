#!/usr/bin/env python3
"""Offline fixtures for pqe-branch-baseline.py; no TV/root/network calls."""

from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("pqe_branch_baseline", HERE / "pqe-branch-baseline.py")
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
QD_INNER = 0x40000000
BACKEND = 0x50000000

BASE_QD_VPTR = A + 0x59F2E8
BASE_BACKEND_VPTR = A + 0x5A152C
BASE_BACKEND_SLOT = A + 0x1C6275
MNT_QD_VPTR = A + 0x5A094C
MNT_BACKEND_VPTR = A + 0x5A1784
MNT_BACKEND_SLOT = A + 0x1C9E75

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
    return base64.b64encode(b"".join(word.to_bytes(4, "little") for word in words)).decode()


def pointer_line(*, qd_vptr=BASE_QD_VPTR, backend_vptr=BASE_BACKEND_VPTR,
                 backend_slot=BASE_BACKEND_SLOT, backend_reads=2, backend_type=1,
                 ve=VE, ve_vptr=VE_VPTR, dlsr_global=DLSR_GLOBAL,
                 dlsr_state=DLSR_STATE):
    return " ".join(str(value) for value in (
        A, ve, ve_vptr, VE_STATE, dlsr_global, dlsr_state,
        QD_GLOBAL, QD, qd_vptr, QD_INNER, BACKEND, backend_vptr,
        backend_slot, backend_reads, backend_type,
    ))


def dd_stderr(counts):
    lines = []
    for count in counts:
        lines += [f"{count}+0 records in", f"{count}+0 records out",
                  f"{count * 4} bytes ({count * 4} B) copied, 0.001 s, 4 kB/s"]
    return "\n".join(lines) + "\n"


def fixture_response(*, pointers=None, pointers_end=None, mapping=MAPPING,
                     mapping_end=None, bad_ave_hash=False, truncate=None,
                     corrupt_base64=None, include_backend=True,
                     include_branch=None, bad_qd_header=False, extra_section=None):
    pointers = pointers or pointer_line()
    pointers_end = pointers if pointers_end is None else pointers_end
    mapping_end = mapping if mapping_end is None else mapping_end
    values = [int(token) for token in pointers.split()]
    values_end = [int(token) for token in pointers_end.split()]
    qd_vptr = values[8]
    if include_branch is None:
        include_branch = qd_vptr == BASE_QD_VPTR
    identity = "\n".join((
        "00000000-0000-4000-8000-000000000000", "706", module.AVOC_PATH, "603",
        module.AVOC_SHA256 + "  " + module.AVOC_PATH,
        ("0" * 64 if bad_ave_hash else module.AVE_SHA256) + "  " + module.AVE_PATH,
    ))
    fields = {"UTC_START": "1793034000", "UPTIME_START": "55000.10 200000.20",
              "ID_START": identity, "MAPS_START": mapping,
              "POINTERS_START": pointers}
    emitted = []
    layouts = dict(module.COMMON_LAYOUT)
    if include_branch:
        layouts.update(module.BASE_QD_LAYOUT)
    for index, (name, (_, _, count)) in enumerate(layouts.items(), 1):
        words = list(range(index * 100, index * 100 + count))
        if name == "qd_outer_header":
            words = [qd_vptr + (4 if bad_qd_header else 0), QD_INNER, 0, 0,
                     BACKEND, 0, 1]
        if name == "qd_branch_condition_0038":
            words = [0xAABBCC05]
        if name == "qd_auto_power_off_count":
            words = [299]
        if truncate == name:
            words = words[:-1]
        data = encode_words(words)
        fields["READ_" + name] = "%%%" if corrupt_base64 == name else data
        emitted.append(count)
    if include_backend:
        fields["READ_backend_cache"] = encode_words([207])
        emitted.append(1)
    if extra_section is not None:
        fields[extra_section] = "injected"
    fields.update({"POINTERS_END": pointers_end, "MAPS_END": mapping_end,
                   "ID_END": identity, "UPTIME_END": "55000.30 200000.40",
                   "UTC_END": "1793034001"})
    stdout = "".join("@@ " + name + "\n" + value + "\n" for name, value in fields.items())
    counts = [1] * (10 + values[13]) + emitted + [1] * (10 + values_end[13])
    return {"model": module.MODEL, "authenticated": True, "uid": 0, "euid": 0,
            "root_persistence": "host-assisted",
            "global_system_files_unchanged_at_acquisition": True,
            "commands": [{"exit_code": 0, "timed_out": False,
                          "stdout": stdout, "stderr": dd_stderr(counts)}]}


class BranchBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = module.static_contract()

    def test_default_is_dry_and_never_invokes_transport(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["pqe-branch-baseline.py"]), \
                patch.object(module.subprocess, "run") as run, \
                contextlib.redirect_stdout(output):
            module.main()
        run.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["physical_state"], "unobserved")

    def test_command_is_bounded_read_only_and_shell_valid(self):
        command = module.build_command()
        self.assertLessEqual(len(command.encode()), 8192)
        self.assertIn('/proc/$P/mem', command)
        self.assertIn('if test "$QV" = $((A+0x59f2e8)); then', command)
        self.assertIn('emit qd_branch_condition_0038 $((I+0x38)) 1', command)
        self.assertIn('emit qd_auto_power_off_count $((A+0x5be420)) 1', command)
        self.assertIn('s=${s##*) }', command)
        self.assertNotIn("strtonum", command)
        self.assertNotIn("while read r p", command)
        self.assertNotIn("/dev/", command.replace("/dev/null", ""))
        for forbidden in ("ioctl", "systemctl", "reboot", "kill ", "setFactory",
                          "SetGSR", "SetObject", "tracefs", "debugfs", "chmod", "mount "):
            self.assertNotIn(forbidden, command)
        syntax = subprocess.run(["bash", "-n"], input=command, text=True,
                                capture_output=True)
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        source = (HERE / "pqe-branch-baseline.py").read_text()
        self.assertIn('"--persistent-only", "--timeout", "25"', source)
        self.assertNotIn("pqe-policy-baseline", source)
        self.assertNotIn("args.output.resolve()", source)

    def test_contract_pins_exact_base_offsets_and_static_provenance(self):
        layout = self.contract["base_qd_branch_layout"]
        self.assertEqual({int(item["offset"], 16) for item in layout.values()},
                         {0, 0x38, 0x88, 0x98, 0xA4, 0xF8, 0x188, 0x2A4, 0x450,
                          0x5BE420})
        self.assertEqual(self.contract["base_qd_branch_class"], "QDDimming")
        self.assertEqual(self.contract["source_provenance"]["auto_power_off_static_vma"],
                         "0x005be420")
        self.assertIn("never QDDimmingMNT",
                      self.contract["source_provenance"]["eligibility"])

    def test_valid_base_snapshot_decodes_raw_branch_fields_without_inference(self):
        summary = module.validate_response(fixture_response(), self.contract)
        self.assertTrue(summary["accepted"])
        self.assertEqual(summary["qd"]["class"], "QDDimming")
        self.assertTrue(summary["branch_state"]["available"])
        self.assertEqual(summary["branch_state"]["condition_0038_aligned_word"],
                         0xAABBCC05)
        self.assertEqual(summary["branch_state"]["condition_0038_low_byte"], 5)
        self.assertEqual(summary["branch_state"]["auto_power_off_count"], 299)
        self.assertFalse(summary["branch_state"]["current_branch_inferred"])
        self.assertEqual(summary["physical_state"], "unobserved")
        self.assertFalse(summary["physical_state_inferred_from_software"])
        self.assertEqual(summary["decoded"]["backend_cache"]["words"], [207])

    def test_mnt_omits_every_base_only_group(self):
        pointers = pointer_line(qd_vptr=MNT_QD_VPTR, backend_vptr=MNT_BACKEND_VPTR,
                                backend_slot=MNT_BACKEND_SLOT, backend_type=2)
        summary = module.validate_response(fixture_response(pointers=pointers), self.contract)
        self.assertTrue(summary["accepted"])
        self.assertEqual(summary["qd"]["class"], "QDDimmingMNT")
        self.assertFalse(summary["branch_state"]["available"])
        self.assertFalse(any(name.startswith("qd_branch_") or
                             name == "qd_auto_power_off_count"
                             for name in summary["decoded"]))

    def test_mnt_with_injected_base_group_is_rejected(self):
        pointers = pointer_line(qd_vptr=MNT_QD_VPTR, backend_vptr=MNT_BACKEND_VPTR,
                                backend_slot=MNT_BACKEND_SLOT, backend_type=2)
        with self.assertRaisesRegex(ValueError, "Unexpected or missing output section"):
            module.validate_response(
                fixture_response(pointers=pointers, include_branch=True), self.contract)

    def test_base_missing_branch_groups_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unexpected or missing output section"):
            module.validate_response(fixture_response(include_branch=False), self.contract)

    def test_truncated_or_malformed_branch_read_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Truncated memory read"):
            module.validate_response(
                fixture_response(truncate="qd_branch_sources_00f8_00fc"), self.contract)
        with self.assertRaisesRegex(ValueError, "Malformed base64 memory read"):
            module.validate_response(
                fixture_response(corrupt_base64="qd_branch_condition_0038"), self.contract)

    def test_qd_header_and_remote_backend_classification_are_rechecked(self):
        with self.assertRaisesRegex(ValueError, "QD outer header disagrees"):
            module.validate_response(fixture_response(bad_qd_header=True), self.contract)
        pointers = pointer_line(backend_type=0)
        with self.assertRaisesRegex(ValueError, "Incorrect backend type classification"):
            module.validate_response(
                fixture_response(pointers=pointers, include_backend=False), self.contract)

    def test_untyped_backend_omits_cache_but_keeps_base_branch(self):
        pointers = pointer_line(backend_vptr=A + 0x1234, backend_slot=0,
                                backend_reads=1, backend_type=0)
        summary = module.validate_response(
            fixture_response(pointers=pointers, include_backend=False), self.contract)
        self.assertTrue(summary["branch_state"]["available"])
        self.assertNotIn("backend_cache", summary["decoded"])

    def test_wrong_hash_pointer_maps_and_source_mapping_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Installed libave hash mismatch"):
            module.validate_response(fixture_response(bad_ave_hash=True), self.contract)
        with self.assertRaisesRegex(ValueError, "Pointer chain changed"):
            module.validate_response(
                fixture_response(pointers_end=pointer_line(ve_vptr=VE_VPTR + 4)),
                self.contract)
        changed = MAPPING + "\n60000000-60001000 rw-p 00000000 00:00 0"
        with self.assertRaisesRegex(ValueError, "Process maps changed"):
            module.validate_response(fixture_response(mapping_end=changed), self.contract)
        mapping = MAPPING.replace(
            "1059c000-105a4000 r--p 0058c000 b3:1b 2 /prd/usr/lib/libave.so.0.1",
            "1059c000-105a4000 r--p 00000000 00:00 0")
        with self.assertRaisesRegex(ValueError, "libave-backed source range"):
            module.validate_response(fixture_response(mapping=mapping), self.contract)

    def test_unaligned_inner_and_dd_injection_are_rejected(self):
        values = pointer_line().split()
        values[9] = str(QD_INNER + 2)
        with self.assertRaisesRegex(ValueError, "unaligned"):
            module.validate_response(fixture_response(pointers=" ".join(values)), self.contract)
        response = fixture_response()
        response["commands"][0]["stderr"] += "dd: injected read error\n"
        with self.assertRaisesRegex(ValueError, "dd diagnostic inventory"):
            module.validate_response(response, self.contract)

    def test_portable_awk_guard_handles_large_arm32_map(self):
        lines = []
        for index in range(1299):
            lo = 0x01000000 + index * 0x2000
            lines.append(f"{lo:08x}-{lo + 0x1000:08x} r--p 00000000 00:00 0")
        lines.append("f0000000-f0010000 rw-p 00000000 00:00 0")
        mapping = "\n".join(lines) + "\n"
        argv = ["awk", "-v", "q=xf0000100", "-v", "e=xf0000104", module.MAP_AWK]
        started = time.monotonic()
        for _ in range(25):
            result = subprocess.run(argv, input=mapping, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(time.monotonic() - started, 5.0)
        outside = subprocess.run(
            ["awk", "-v", "q=xf0010000", "-v", "e=xf0010004", module.MAP_AWK],
            input=mapping, text=True, capture_output=True)
        self.assertNotEqual(outside.returncode, 0)

    def test_failure_record_retains_raw_root_response(self):
        response = fixture_response(truncate="qd_branch_sources_00f8_00fc")
        completed = subprocess.CompletedProcess([], 0, json.dumps(response), "")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "failed.json"
            with patch.object(module.subprocess, "run", return_value=completed) as run:
                with self.assertRaisesRegex(ValueError, "Truncated memory read"):
                    module.run_capture(destination, self.contract)
            saved = json.loads(destination.read_text())
            self.assertFalse(saved["accepted"])
            self.assertEqual(saved["transport"]["stdout"], json.dumps(response))
            argv = run.call_args.args[0]
            self.assertEqual(argv[2:7],
                             ["root", "--persistent-only", "--timeout", "25", "--command"])
            self.assertEqual(run.call_count, 1)

    def test_preexisting_or_dangling_output_is_preserved_without_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            existing = Path(temporary) / "existing.json"
            existing.write_text("owner data\n")
            with patch.object(module.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    module.run_capture(existing, self.contract)
            run.assert_not_called()
            self.assertEqual(existing.read_text(), "owner data\n")
            dangling = Path(temporary) / "dangling.json"
            dangling.symlink_to(Path(temporary) / "missing")
            with patch.object(module.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    module.run_capture(dangling, self.contract)
            run.assert_not_called()
            self.assertTrue(dangling.is_symlink())

    def test_cli_run_refuses_dangling_output_without_following_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "must-not-be-created.json"
            dangling = Path(temporary) / "cli-output.json"
            dangling.symlink_to(target)
            with patch.object(
                    sys, "argv",
                    ["pqe-branch-baseline.py", "--run", "--output", str(dangling)]), \
                    patch.object(module.subprocess, "run") as run:
                with self.assertRaisesRegex(ValueError, "already exists"):
                    module.main()
            run.assert_not_called()
            self.assertTrue(dangling.is_symlink())
            self.assertFalse(target.exists())

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


if __name__ == "__main__":
    unittest.main()
