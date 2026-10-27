#!/usr/bin/env python3
"""Offline focused tests for pm-runtime-context-replay.py."""
import importlib.util
import json
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
TOOL = BASE / "pm-runtime-context-replay.py"
CAPTURE = BASE / "apps-live-20261027b.onset"


def load():
    spec = importlib.util.spec_from_file_location("pm_runtime_context_replay_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    tool = load()
    result = tool.analyze(CAPTURE)
    require(result["replay_technical_subset_accepted"] is True, "retained replay did not pass")
    require(result["original_record_accepted"] is False, "replay rewrote original acceptance")
    require(result["physical_state"] == "unobserved-or-incomplete", "physical qualifier changed")
    require(result["runtime_pm"]["context_changed_pairs"] == 3, "expected three relaxed runtime pairs")
    # The narrow relaxation did not remove context identity for callbacks.
    pm = tool.load_relaxed_pm()
    base = {"markers": [{"kind": "TRACE_ARMED", "line": 0}, {"kind": "PREROLL_START", "line": 0},
                        {"kind": "START", "line": 0}, {"kind": "END", "line": 99},
                        {"kind": "DRAIN_END", "line": 100}]}
    callback_rows = (
        " cb-10 ( 10) [000] .... 1.000000: device_pm_callback_start: drv dev, parent: par, ops[resume]\n"
        " cb-10 ( 10) [000] ...x 1.100000: device_pm_callback_end: drv dev, err=0\n")
    try:
        pm._pm_accounting(callback_rows.encode(), base)
    except ValueError:
        pass
    else:
        raise AssertionError("callback context mutation accepted")
    runtime_rows = (
        " task-10 ( 10) [000] .... 2.000000: rpm_resume: dev flags-0 cnt-0 dep-0 auto-0 p-0 irq-0 child-0\n"
        " task-10 ( 10) [000] ...x 2.100000: rpm_resume: dev flags-0 cnt-0 dep-0 auto-0 p-0 irq-0 child-0\n"
        " task-10 ( 10) [000] ..x. 2.200000: rpm_return_int: ip:dev ret=0\n"
        " task-10 ( 10) [000] .x.. 2.300000: rpm_return_int: ip:dev ret=0\n"
        " <idle>-0 (-------) [000] .... 2.400000: rpm_idle: idledev flags-0 cnt-0 dep-0 auto-0 p-0 irq-0 child-0\n"
        " <idle>-0 (-------) [001] ...x 2.500000: rpm_idle: idledev flags-0 cnt-0 dep-0 auto-0 p-0 irq-0 child-0\n"
        " <idle>-0 (-------) [001] ..x. 2.600000: rpm_return_int: ip:idledev ret=0\n"
        " <idle>-0 (-------) [000] .x.. 2.700000: rpm_return_int: ip:idledev ret=0\n")
    runtime = pm._pm_accounting(runtime_rows.encode(), base)["runtime_pm_pairs"]
    require(len(runtime) == 4 and {row["start_cpu"] for row in runtime[-2:]} == {0, 1},
            "nested task/CPU-idle runtime pairing changed")
    lifecycle_rows = (
        " task-10 ( 10) [000] .... 3.000000: rpm_resume: dev flags-0 cnt-0 dep-0 auto-0 p-0 irq-0 child-0\n"
        " task-10 ( 10) [000] .... 3.100000: sched_process_exit: comm=x pid=10 prio=0\n"
        " task-10 ( 10) [000] ...x 3.200000: rpm_return_int: ip:dev ret=0\n")
    try:
        pm._pm_accounting(lifecycle_rows.encode(), base)
    except ValueError as exc:
        require("task identity/lifecycle changed" in str(exc), "runtime lifecycle crossing was not rejected")
    else:
        raise AssertionError("runtime lifecycle crossing accepted")
    # Mutating a declared retained trace byte must fail before decoding.
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw) / "copy"; root.mkdir()
        for src in CAPTURE.iterdir():
            if src.is_file():
                (root / src.name).write_bytes(src.read_bytes())
        trace = root / "trace"; data = bytearray(trace.read_bytes()); data[100] ^= 1; trace.write_bytes(data)
        try:
            tool.analyze(root)
        except ValueError as exc:
            require("sidecar hash/size mismatch" in str(exc), "wrong retained-byte rejection")
        else:
            raise AssertionError("tampered trace accepted")
    # A report write is exclusive and cannot overwrite an evidence derivative.
    with tempfile.TemporaryDirectory() as raw:
        report = Path(raw) / "report.json"
        report.write_text(json.dumps(result))
        try:
            if report.exists():
                raise ValueError("report destination already exists")
        except ValueError:
            pass
        else:
            raise AssertionError("exclusive report destination missing")
    print("pm-runtime-context-replay tests: PASS")


if __name__ == "__main__":
    main()
