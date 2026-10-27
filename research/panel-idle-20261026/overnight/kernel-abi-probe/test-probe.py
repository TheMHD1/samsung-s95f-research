#!/usr/bin/env python3
"""Offline result-integrity tests. Never launches the native helper or a TV call."""
from pathlib import Path
import base64
import hashlib
import importlib.util
import json
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("kernel_abi_probe", HERE / "run-probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ResultIntegrity(unittest.TestCase):
    def fixture(self, *, data=None, status=0, cleanup=True):
        if data is None:
            data = b"QDKABI1\n" + b"".join(value.to_bytes(8, "little", signed=True)
                                              for value in [123, -38, -14])
        return (f"PROBE_EXIT={status}\nRESULT_SIZE\n{len(data)} /tmp/example/result\n"
                f"RESULT_BASE64\n{base64.b64encode(data).decode()}\nRESULT_SHA256\n"
                f"{hashlib.sha256(data).hexdigest()} /tmp/example/result\nRESULT_END\n"
                + ("PRIVATE_TEMP_DIRECTORY_REMOVED\n" if cleanup else ""))

    def test_valid_format(self):
        result = probe.decode(self.fixture())
        self.assertEqual(result["native_getpid"], 123)
        self.assertEqual(result["invalid_bpf_return"], -38)
        self.assertEqual(result["null_perf_event_return"], -14)

    def test_truncated_and_wrong_magic(self):
        for data in [b"QDKABI1\n", b"WRONG123" + bytes(24)]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                probe.decode(self.fixture(data=data))

    def test_failed_execution_and_missing_cleanup(self):
        for args in [{"status": 126}, {"cleanup": False}]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                probe.decode(self.fixture(**args))

    def test_nonnegative_observer_result_and_bad_pid(self):
        for values in [[123, 3, -14], [123, -38, 3], [0, -38, -14]]:
            data = b"QDKABI1\n" + b"".join(v.to_bytes(8, "little", signed=True) for v in values)
            with self.subTest(values=values), self.assertRaises(ValueError):
                probe.decode(self.fixture(data=data))

    def test_actual_denied_launch_is_not_syscall_evidence(self):
        record = json.loads((HERE / "result-20261026T124321Z.json").read_text())
        self.assertFalse(record["accepted"])
        reply = record["response"]["commands"][0]
        self.assertEqual(reply["exit_code"], 0)  # Shell succeeded; helper didn't.
        self.assertIn("Operation not permitted", reply["stderr"])
        with self.assertRaises(ValueError):
            probe.decode(reply["stdout"])


if __name__ == "__main__":
    unittest.main()
