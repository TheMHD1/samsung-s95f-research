#!/usr/bin/env python3
"""Offline tests; all root/device transport is replaced with local fixtures."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "run-power-cycle-once.py"
SPEC = importlib.util.spec_from_file_location("power_cycle_once", SOURCE)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

GOOD = """QD_TCON_POWER_CYCLE_ONCE_V1
ARCH=Arm
PTR_BYTES=4
STRUCT_BYTES=16
ENDIAN_LITTLE=1
OPERATION_OFFSET=0
MODE_OFFSET=4
RESERVED0_OFFSET=8
RESERVED1_OFFSET=12
ARGUMENT_COUNT=0
UID=0
EUID=0
PID_LIBC=7
PID_SYSCALL=7
DEVICE=/dev/tztv_tcon
OPEN_FLAGS=0x80002
IOCTL_REQUEST=0xc010749f
OPERATION_DECIMAL=41
MODE_DECIMAL=2
PAYLOAD_BEFORE=00000029,00000002,00000000,00000000
OPEN_RETURN=3
OPEN_ERRNO=0
IOCTL_RETURN=0
IOCTL_ERRNO=0
PAYLOAD_AFTER=00000029,00000002,00000000,00000000
CLOSE_RETURN=0
CLOSE_ERRNO=0
CLASSIFICATION=kernel_return_zero_only
POWER_ACTION_ACKNOWLEDGED=0
RECOVERY_INFERRED=0
PHYSICAL_STATE_INFERRED=0
POWER_CYCLE_REQUEST_COMPLETE"""


class PowerCycleTests(unittest.TestCase):
    def test_manifest_payload_and_dry_plan(self):
        manifest, files = runner.contract()
        plan = runner.dry_plan(manifest, files)
        self.assertTrue(plan["dry_run"])
        self.assertTrue(plan["no_tv_root_device_or_network_calls"])
        self.assertEqual(plan["fixed_payload"], [
            "0x00000029", "0x00000002", "0x00000000", "0x00000000"])
        self.assertFalse(plan["retry_permitted"])
        self.assertTrue(plan["all_root_commands_within_8192"])
        self.assertLessEqual(plan["root_command_max_bytes"], 8192)
        self.assertGreaterEqual(plan["helper_deadline_seconds"],
                                plan["lower_explicit_wait_budget_seconds"])
        self.assertEqual(set(files), set(runner.REMOTE_NAMES))
        self.assertEqual(hashlib.sha256(runner.MANIFEST.read_bytes()).hexdigest(),
                         runner.MANIFEST_SHA256)

    def test_fixed_parser_positive_and_no_acknowledgement(self):
        parsed = runner.parse_managed(GOOD, 7)
        self.assertEqual(parsed["classification"], "kernel_return_zero_only")
        self.assertEqual(parsed["mode"], 2)
        self.assertFalse(parsed["power_action_acknowledged"])
        self.assertFalse(parsed["recovery_inferred"])
        self.assertFalse(parsed["physical_state_inferred"])

    def test_parser_rejects_every_control_and_result_mutation(self):
        mutations = (
            ("ARCH=Arm", "ARCH=X64"),
            ("PID_SYSCALL=7", "PID_SYSCALL=8"),
            ("OPERATION_DECIMAL=41", "OPERATION_DECIMAL=19"),
            ("MODE_DECIMAL=2", "MODE_DECIMAL=1"),
            ("00000029,00000002,00000000,00000000",
             "00000029,00000002,00000001,00000000"),
            ("OPEN_RETURN=3", "OPEN_RETURN=-1"),
            ("OPEN_ERRNO=0", "OPEN_ERRNO=5"),
            ("IOCTL_RETURN=0", "IOCTL_RETURN=-1"),
            ("IOCTL_ERRNO=0", "IOCTL_ERRNO=5"),
            ("CLOSE_RETURN=0", "CLOSE_RETURN=-1"),
            ("CLASSIFICATION=kernel_return_zero_only", "CLASSIFICATION=recovered"),
            ("POWER_ACTION_ACKNOWLEDGED=0", "POWER_ACTION_ACKNOWLEDGED=1"),
            ("RECOVERY_INFERRED=0", "RECOVERY_INFERRED=1"),
            ("POWER_CYCLE_REQUEST_COMPLETE", "X=1\nPOWER_CYCLE_REQUEST_COMPLETE"),
            ("POWER_CYCLE_REQUEST_COMPLETE", "UNKNOWN\nPOWER_CYCLE_REQUEST_COMPLETE"),
        )
        for before, after in mutations:
            with self.subTest(after=after), self.assertRaises(runner.ContractError):
                runner.parse_managed(GOOD.replace(before, after, 1), 7)

    def test_source_has_one_fixed_ioctl_and_no_action_arguments(self):
        text = (HERE / "Program.cs").read_text()
        self.assertEqual(text.count("ioctl(fd, Request, ref value)"), 1)
        self.assertIn("private const uint Operation = 41;", text)
        self.assertIn("private const uint Mode = 2;", text)
        self.assertIn("Reserved0 = 0", text)
        self.assertIn("Reserved1 = 0", text)
        self.assertIn("if (args.Length != 0)", text)
        imports = set(re.findall(r"private static extern \w+ (\w+)\(", text))
        self.assertEqual(imports, {"Syscall", "open", "ioctl", "close",
                                   "getpid", "getuid", "geteuid"})
        for forbidden in ("SetProtection", "PowerOff", "PowerOn"):
            self.assertNotIn(forbidden, text)

    def test_rendered_lifecycle_uses_managed_payload_and_bounded_deadline(self):
        _manifest, files = runner.contract()
        private = "/tmp/researcher-tcon-" + "0" * 32
        commands = runner.render_lifecycle(
            private, "00000000-0000-0000-0000-000000000000", files)
        execute = next(command for command in commands if "EXECUTE_COMPLETE" in command)
        self.assertIn("ManagedTconPowerCycleOnce.dll", execute)
        self.assertNotIn("TconStatusRead.dll", execute)
        self.assertIn('while test "$i" -lt 80', execute)
        self.assertEqual(execute.count("/usr/bin/dotnet --clr-path"), 1)
        self.assertTrue(all(len(command.encode()) <= 8192 for command in commands))

    def fixture_run(self, managed=GOOD, cleanup_ok=True):
        module = runner.lifecycle_module()
        calls = []
        boot = "00000000-0000-0000-0000-000000000000"
        def root(command, _record, _output):
            calls.append(command)
            if "echo PREFLIGHT_IDENTITY_MATCH" in command:
                return (f"PREFLIGHT_BOOT={boot}\nPREFLIGHT_UTC=1\n"
                        "PREFLIGHT_UPTIME=1.0\nPREFLIGHT_IDENTITY_MATCH\n")
            if "echo EXECUTE_COMPLETE" in command:
                return ("HELPER_PID=7\nHELPER_START=1\nHELPER_DEADLINE_HIT=0\n"
                        "HELPER_EXIT=0\nMANAGED_STDOUT_BEGIN\n" + managed +
                        "\nMANAGED_STDOUT_END\nMANAGED_STDERR_BEGIN\n"
                        "MANAGED_STDERR_END\nEXECUTE_BOOT=" + boot +
                        "\nEXECUTE_UTC=2\nEXECUTE_UPTIME=2.0\nEXECUTE_COMPLETE\n")
            if "echo POSTFLIGHT_IDENTITY_MATCH" in command:
                return "POSTFLIGHT_IDENTITY_MATCH\n"
            if "echo PRIVATE_REMOVED" in command:
                return "PRIVATE_REMOVED\n" if cleanup_ok else "INCOMPLETE\n"
            if "echo PRIVATE_CREATED" in command:
                return "PRIVATE_CREATED\n"
            if "echo STAGE_CHUNK_COMPLETE" in command:
                return "STAGE_CHUNK_COMPLETE\n"
            raise AssertionError("unhandled lifecycle command")
        module.root = root
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(runner, "lifecycle_module", return_value=module):
            destination = Path(directory) / "result.json"
            try:
                result = runner.run_once(destination, *runner.contract())
            except runner.ContractError:
                result = json.loads(destination.read_text())
        return result, calls

    def test_full_mocked_lifecycle_accepts_return_zero_only_and_cleans(self):
        result, calls = self.fixture_run()
        self.assertTrue(result["accepted"])
        self.assertTrue(result["cleanup_confirmed"])
        self.assertFalse(result["recovery_inferred"])
        self.assertEqual(result["execution"]["result"]["classification"],
                         "kernel_return_zero_only")
        self.assertEqual(sum("echo EXECUTE_COMPLETE" in call for call in calls), 1)
        self.assertTrue(any("echo PRIVATE_REMOVED" in call for call in calls))

    def test_bad_result_still_cleans_and_cleanup_failure_rejects(self):
        bad = GOOD.replace("RECOVERY_INFERRED=0", "RECOVERY_INFERRED=1")
        result, calls = self.fixture_run(bad)
        self.assertFalse(result["accepted"])
        self.assertTrue(result["cleanup_confirmed"])
        self.assertTrue(any("echo PRIVATE_REMOVED" in call for call in calls))
        result, _calls = self.fixture_run(cleanup_ok=False)
        self.assertFalse(result["accepted"])
        self.assertFalse(result["cleanup_confirmed"])

    def test_existing_and_dangling_output_refused_before_transport(self):
        manifest, files = runner.contract()
        module = runner.lifecycle_module()
        module.root = mock.Mock(side_effect=AssertionError("transport attempted"))
        with tempfile.TemporaryDirectory() as directory, \
                mock.patch.object(runner, "lifecycle_module", return_value=module):
            root = Path(directory)
            existing = root / "existing.json"
            existing.write_text("preserve")
            dangling = root / "dangling.json"
            dangling.symlink_to(root / "absent-target")
            for destination in (existing, dangling):
                with self.subTest(destination=destination), \
                        self.assertRaisesRegex(module.ContractError,
                                               "Output path already exists"):
                    runner.run_once(destination, manifest, files)
            self.assertEqual(existing.read_text(), "preserve")
            self.assertTrue(dangling.is_symlink())
            self.assertFalse((root / "absent-target").exists())
            module.root.assert_not_called()

    def test_default_cli_is_dry(self):
        result = subprocess.run([sys.executable, str(SOURCE)], check=True,
                                capture_output=True, text=True)
        body = json.loads(result.stdout)
        self.assertTrue(body["dry_run"])
        self.assertTrue(body["no_tv_root_device_or_network_calls"])
        self.assertFalse(body["retry_permitted"])


if __name__ == "__main__":
    unittest.main()
