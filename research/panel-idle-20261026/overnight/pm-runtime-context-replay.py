#!/usr/bin/env python3
"""Offline-only replay of a retained PM trace with runtime context de-keyed.

This does not alter a capture, execute anything on the TV, or turn the
original failed capture record into an accepted physical observation.  It
reuses the hash-pinned PM decoder and relaxes exactly one pairing rule:
runtime-PM pairs use PID/TGID/task (or CPU for PID 0 idle), rather than the
mutable printed ftrace context token.  Device-callback and system-PM pairing
continue to require an exact context token.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import types


BASE = Path(__file__).resolve().parent
PM_SOURCE = BASE / "observed-pm-onset-capture.py"
PM_SOURCE_SHA256 = "c7b07bbcb508005c028824763c84109d18aee1d9df8813a5f59c476093616d06"
QUIESCENT_SOURCE = BASE / "observed-quiescent-pm-onset-capture.py"
QUIESCENT_SOURCE_SHA256 = "8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f"
REQUIRED = ("trace", "meta.txt", "samples.txt", "sample-errors.txt", "vlog-after.txt",
            "artifacts.txt", "fds.txt", "collector.stdout", "collector.stderr",
            "remote.sh", "record.json", "cleanup.json", "quiesce.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "unable to load pinned source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_relaxed_pm():
    require(sha256(PM_SOURCE) == PM_SOURCE_SHA256, "PM replay source hash changed")
    module = load_module("pm_runtime_context_replay_source", PM_SOURCE)
    source = inspect.getsource(module._pm_accounting)
    old_runtime = '''        if row["pid"] != 0:\n            return positive_identity(row)\n'''
    new_runtime = '''        if row["pid"] != 0:\n            require(row["pid"] > 0 and row["tgid"] is not None and row["tgid"] > 0,\n                    "runtime-PM row lacks exact positive PID/saved-TGID identity")\n            return ("runtime-task", row["pid"], row["tgid"], row["task"])\n'''
    old_idle = '''        return ("idle", row["cpu"], 0, "<idle>", "-------", row["context"])\n'''
    new_idle = '''        return ("runtime-idle", row["cpu"], 0, "<idle>", "-------")\n'''
    old_finish = '''                begin["context"] == end["context"] and\n'''
    new_finish = '''                (family == "runtime_pm" or begin["context"] == end["context"]) and\n'''
    require(source.count(old_runtime) == source.count(old_idle) == source.count(old_finish) == 1,
            "pinned PM accounting anchors changed")
    patched = source.replace(old_runtime, new_runtime, 1).replace(old_idle, new_idle, 1)
    patched = patched.replace(old_finish, new_finish, 1)
    exec(compile(patched, str(PM_SOURCE) + ":runtime-context-replay", "exec"), module.__dict__)
    return module


def _sidecars(capture: Path, record: dict) -> dict:
    salvage = record.get("partial_salvage", {})
    declared = salvage.get("sidecars", {})
    require(set(declared) == {"trace", "meta", "samples", "sample-errors", "vlog-after", "artifacts", "fds"},
            "record lacks exact seven retained sidecar declarations")
    result = {}
    for name, item in declared.items():
        suffix = {"meta": "meta.txt", "samples": "samples.txt", "sample-errors": "sample-errors.txt",
                  "vlog-after": "vlog-after.txt", "artifacts": "artifacts.txt", "fds": "fds.txt"}.get(name, name)
        path = capture / suffix
        require(path.is_file() and path.stat().st_size == item["bytes"] and sha256(path) == item["sha256"],
                "retained sidecar hash/size mismatch: " + name)
        result[name] = {"path": suffix, "bytes": item["bytes"], "sha256": item["sha256"]}
    transport = salvage.get("transport", {})
    for name, suffix in (("stdout", "collector.stdout"), ("stderr", "collector.stderr")):
        item, path = transport.get(name), capture / suffix
        require(isinstance(item, dict) and path.is_file() and path.stat().st_size == item["bytes"] and
                sha256(path) == item["sha256"], "retained collector transport mismatch: " + name)
        result[name] = {"path": suffix, "bytes": item["bytes"], "sha256": item["sha256"]}
    return result


def analyze(capture: Path) -> dict:
    require(capture.is_dir(), "capture directory missing")
    require(all((capture / name).is_file() for name in REQUIRED), "capture files incomplete")
    record = json.loads((capture / "record.json").read_text())
    require(record.get("accepted") is False and record.get("physical_state") == "unobserved-or-incomplete",
            "this is only the preserved rejected/unobserved capture class")
    sidecars = _sidecars(capture, record)
    require((capture / "collector.stdout").read_text().splitlines()[-1:] == ["CAPTURE_COMPLETE"],
            "collector completion marker absent")
    require((capture / "collector.stderr").read_bytes() == b"", "collector stderr not empty")
    cleanup = json.loads((capture / "cleanup.json").read_text())
    quiesce = json.loads((capture / "quiesce.json").read_text())
    for item, token in ((cleanup, "CLEAN"), (quiesce, "QUIESCED")):
        command = item.get("commands", [{}])
        require(len(command) == 1 and command[0].get("exit_code") == 0 and
                command[0].get("stdout", "").endswith(token + "\n") and not command[0].get("stderr"),
                "retained lifecycle guard failed: " + token)
    require(sha256(QUIESCENT_SOURCE) == QUIESCENT_SOURCE_SHA256,
            "quiescent sidecar parser hash changed")
    quiescent = load_module("pm_runtime_context_replay_quiescent", QUIESCENT_SOURCE)
    fds = quiescent.parse_fds((capture / "fds.txt").read_text())
    pm = load_relaxed_pm()
    remote = (capture / "remote.sh").read_bytes()
    meta = pm.validate_metadata((capture / "meta.txt").read_text(), len(remote), hashlib.sha256(remote).hexdigest(),
                                int(record["seconds"]))
    collector = record["collector"]
    require(meta["avoc_identity"][0] == 706 and collector["pid"] > 0 and
            meta["target"] == collector["target_uptime"], "start identity/target mismatch")
    tids = pm._base.TidEvidence(list(fds["tids"]), fds["tids"].evidence)
    trace = pm.trace_accounting((capture / "trace").read_bytes(), tids, meta["avoc_identity"][0],
                                collector["pid"], meta["trace_start"], meta["trace_end"], meta["trace_drain_end"])
    extension = trace["pm_extension"]
    changed = [row for row in extension["runtime_pm_pairs"]
               if row["start_context"] != row["end_context"]]
    require(changed, "replay did not exercise the narrowly relaxed runtime context rule")
    return {
        "schema": "pm-runtime-context-replay-v1",
        "offline_only": True,
        "capture_directory": capture.name,
        "source_pins": {"pm": PM_SOURCE_SHA256, "quiescent": QUIESCENT_SOURCE_SHA256},
        "retained_sidecars": sidecars,
        "replay_technical_subset_accepted": True,
        "original_record_accepted": False,
        "physical_state": record["physical_state"],
        "physical_inference": "none; a trace decoder does not observe panel light or establish causation",
        "relaxation": {
            "runtime_pm": "PID/TGID/task; PID 0 remains CPU-specific idle; start/end context retained as evidence",
            "device_callback_and_system_pm": "still require exact start/end context equality",
        },
        "runtime_pm": {"pairs": len(extension["runtime_pm_pairs"]),
                       "context_changed_pairs": len(changed),
                       "context_changed_pair_lines": [[x["start_line"], x["end_line"]] for x in changed]},
        "trace_guard_summary": {"loss_free": trace["ring_complete"], "marker_count": len(trace["markers"]),
                                "end_identity_checked_by_pinned_metadata": True,
                                "lifecycle_rows": len(extension["task_lifecycle_rows"]),
                                "unmatched_rows": len(extension["unmatched"])},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args()
    result = analyze(args.capture)
    raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.write_report is not None:
        require(not args.write_report.exists(), "report destination already exists")
        args.write_report.write_text(raw)
    print(raw, end="")


if __name__ == "__main__":
    main()
