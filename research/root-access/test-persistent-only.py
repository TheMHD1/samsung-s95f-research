#!/usr/bin/env python3
"""Offline wrapper-routing tests. All network, controller and SDB calls mocked."""
from pathlib import Path
from contextlib import ExitStack, redirect_stdout
import importlib.util
import io
import json
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("s95f_access", HERE / "s95f-access.py")
access = importlib.util.module_from_spec(spec)
spec.loader.exec_module(access)


class PersistentOnly(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name) / "access"
        (self.base / "persistent").mkdir(parents=True)
        (self.base.parent / "private").mkdir()
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        original_umask = os.umask(0o077)
        self.addCleanup(os.umask, original_umask)
        self.stack.enter_context(patch.object(access, "BASE", self.base))
        self.stack.enter_context(patch.object(access.subprocess, "run", return_value=
            SimpleNamespace(returncode=0, stdout="tcp dport 26099 drop")))
        self.stack.enter_context(patch.object(access, "route_callback_host", return_value=access.CONTROLLER))
        device = {"modelName": access.MODEL, "developerMode": "1", "developerIP": access.CONTROLLER}
        opener = SimpleNamespace(open=lambda *args, **kwargs: io.BytesIO(json.dumps({"device": device}).encode()))
        self.stack.enter_context(patch.object(access, "build_opener", return_value=opener))
        self.sdb = self.stack.enter_context(patch.object(access, "SdbClient", side_effect=AssertionError("SDB fallback forbidden")))
        self.probe = self.stack.enter_context(patch.object(access, "probe", side_effect=AssertionError("Root staging forbidden")))
        self.controller = self.stack.enter_context(patch.object(access, "persistent_request"))
        self.stack.enter_context(patch.object(access.sys, "argv", ["s95f-access.py", "root",
            "--persistent-only", "--command", "echo fixture"]))

    def test_missing_socket_refuses_fallback(self):
        with self.assertRaisesRegex(RuntimeError, "bootstrapping refused"):
            access.main()
        self.controller.assert_not_called()
        self.sdb.assert_not_called()
        self.probe.assert_not_called()

    def test_nonready_controller_refuses_fallback(self):
        (self.base / "persistent/control.sock").touch()
        self.controller.return_value = {"state": "connecting"}
        with self.assertRaisesRegex(RuntimeError, "bootstrapping refused"):
            access.main()
        self.assertEqual(self.controller.call_count, 1)
        self.sdb.assert_not_called()
        self.probe.assert_not_called()

    def test_controller_failure_is_not_retried_or_bootstrapped(self):
        (self.base / "persistent/control.sock").touch()
        self.controller.side_effect = RuntimeError("controller unavailable")
        with self.assertRaisesRegex(RuntimeError, "controller unavailable"):
            access.main()
        self.assertEqual(self.controller.call_count, 1)
        self.sdb.assert_not_called()
        self.probe.assert_not_called()

    def test_ready_controller_checks_build_and_executes_once(self):
        (self.base / "persistent/control.sock").touch()
        result = {"uid": 0, "euid": 0, "exit_code": 0, "timed_out": False,
                  "stdout": "fixture\n", "stderr": ""}
        self.controller.side_effect = [{"state": "ready", "system_files_unchanged": True},
            {**result, "stdout": "BUILD_ID=" + access.BUILD + "\n"}, result]
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(access.main(), 0)
        record = json.loads(output.getvalue())
        self.assertEqual(record["root_persistence"], "host-assisted")
        commands = [call.args[0].get("command") for call in self.controller.call_args_list]
        self.assertEqual(commands.count("echo fixture"), 1)
        self.sdb.assert_not_called()
        self.probe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
