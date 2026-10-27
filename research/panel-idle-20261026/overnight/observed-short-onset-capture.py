#!/usr/bin/env python3
"""Prepare one finite 30-second observed PM onset capture; dry by default.

This host-only derivative keeps the accepted quiescent-PM collector's identity,
preflight, observer, physical-annotation, end-identity, and cleanup paths. It
changes only the fixed full-window duration and every private namespace. It
does not run without both --run and --reviewed.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
FROZEN_SOURCE = BASE / "observed-quiescent-pm-onset-capture.py"
FROZEN_SHA256 = "8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f"
WINDOW_SECONDS = 30
REMOTE_ROOT = "/tmp/researcher-observed-short-onset-20261027"
STAGE_ROOT = "/tmp/researcher-observed-short-onset-stage-20261027"
TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-short-onset-"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


if hashlib.sha256(FROZEN_SOURCE.read_bytes()).hexdigest() != FROZEN_SHA256:
    raise RuntimeError("pinned quiescent PM ancestor changed")
_spec = importlib.util.spec_from_file_location("frozen_quiescent_pm_short", FROZEN_SOURCE)
if _spec is None or _spec.loader is None:
    raise RuntimeError("frozen quiescent PM ancestor unavailable")
_frozen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frozen)

MODEL, BUILD, ACCESS = _frozen.MODEL, _frozen.BUILD, _frozen.ACCESS
AVE_PATH, AVE_SHA = _frozen.AVE_PATH, _frozen.AVE_SHA
AVOC_PATH, AVOC_SHA = _frozen.AVOC_PATH, _frozen.AVOC_SHA
DEV_PATH, DEV_SHA = _frozen.DEV_PATH, _frozen.DEV_SHA
PM_EVENTS = _frozen.PM_EVENTS
_parent_build = _frozen.build_remote_script
_parent_run = _frozen._ORIGINAL_RUN
_pm = _frozen._base
_preroll = _pm._base
_branch = _preroll._base
_terminal = _branch._base

_ROOTS = tuple(dict.fromkeys((
    _frozen.REMOTE_ROOT, _pm.REMOTE_ROOT, _preroll.REMOTE_ROOT,
    _branch.REMOTE_ROOT, _terminal.REMOTE_ROOT)))
_STAGES = tuple(dict.fromkeys((
    _frozen.STAGE_ROOT, _pm.STAGE_ROOT, _preroll.STAGE_ROOT,
    _branch.STAGE_ROOT, _terminal.STAGE_ROOT)))
_PREFIXES = tuple(dict.fromkeys((
    _frozen.TRACE_PREFIX, _pm.TRACE_PREFIX, _preroll.TRACE_PREFIX,
    _branch.TRACE_PREFIX, "/sys/kernel/debug/tracing/instances/researcher-onset-")))


def _namespace(shell: str) -> str:
    for old in _ROOTS:
        shell = shell.replace(old, REMOTE_ROOT)
    for old in _STAGES:
        shell = shell.replace(old, STAGE_ROOT)
    for old in _PREFIXES:
        shell = shell.replace(old, TRACE_PREFIX)
    return shell


@contextlib.contextmanager
def _permit_only_short_window():
    """Permit 30 only at the frozen terminal duration guard while rendering."""
    old = _terminal.require
    def guarded(condition: bool, message: str) -> None:
        if (not condition and message ==
                "full captures require 85..90 seconds; smoke fixtures allow 5 or 10"):
            return
        old(condition, message)
    _terminal.require = guarded
    try:
        yield
    finally:
        _terminal.require = old


def build_remote_script(label: str, seconds: int = WINDOW_SECONDS,
                        allow_short: bool = False) -> str:
    require(seconds == WINDOW_SECONDS, "short observed window is fixed at 30 seconds")
    require(not allow_short, "short observed capture remains a full physical-window mode")
    with _permit_only_short_window():
        shell = _parent_build(label, seconds, allow_short=False)
    shell = _namespace(shell)
    require(REMOTE_ROOT in shell and STAGE_ROOT in shell and TRACE_PREFIX in shell,
            "short namespace absent from rendered collector")
    require(not any(old in shell for old in (*_ROOTS, *_STAGES, *_PREFIXES)),
            "ancestor namespace remains in rendered collector")
    require("-v n=30" in shell, "fixed 30-second capture duration absent")
    require("CAPTURE_START" in shell and "CAPTURE_END" in shell,
            "physical annotation markers absent")
    return shell


def root(command: str, timeout: int, audit_prefix: Path | None = None):
    return _frozen._ORIGINAL_ROOT(_namespace(command), timeout, audit_prefix)


def stage_script(label: str, script: bytes) -> dict:
    result = dict(_frozen._ORIGINAL_STAGE(label, script))
    require(set(result) == {"path", "bytes", "sha256", "chunks",
                            "persistent_only", "expiry_seconds"},
            "unexpected staged-script metadata")
    result["path"] = _namespace(str(result["path"]))
    require(result["path"] == f"{STAGE_ROOT}/{label}/capture.sh",
            "staged-script metadata namespace mismatch")
    return result


@contextlib.contextmanager
def _patched_frozen_context():
    """Keep the complete accepted quiescent context, replacing only boundary hooks."""
    saved = {name: getattr(_frozen, name) for name in
             ("build_remote_script", "root", "stage_script")}
    _frozen.build_remote_script = build_remote_script
    _frozen.root = root
    _frozen.stage_script = stage_script
    try:
        with _permit_only_short_window():
            yield
    finally:
        for name, value in saved.items():
            setattr(_frozen, name, value)


def run_capture(label: str) -> None:
    with _patched_frozen_context():
        _frozen.run_capture(label, WINDOW_SECONDS, smoke_unobserved=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("--seconds", type=int, default=WINDOW_SECONDS)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--emit-shell", action="store_true")
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,30}", args.label) is not None,
            "use a unique lowercase label")
    require(args.seconds == WINDOW_SECONDS, "short observed window is fixed at 30 seconds")
    for name, digest in {"binaries/libave.so.0.1": AVE_SHA,
                         "binaries/avocd": AVOC_SHA,
                         "binaries/deviced": DEV_SHA}.items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
                "local matching binary hash changed: " + name)
    shell = build_remote_script(args.label)
    raw = shell.encode()
    if not args.run:
        if args.emit_shell:
            print(shell, end="")
        else:
            print(json.dumps({
                "mode": "dry-run; no TV/network/root call",
                "capture_kind": "full-observed-short",
                "seconds": WINDOW_SECONDS,
                "frozen_quiescent_pm_ancestor_sha256": FROZEN_SHA256,
                "staged_script_bytes": len(raw),
                "staged_script_sha256": hashlib.sha256(raw).hexdigest(),
                "remote_root": REMOTE_ROOT, "stage_root": STAGE_ROOT,
                "trace_namespace": TRACE_PREFIX,
                "physical_window": "CAPTURE_START..CAPTURE_END unchanged",
                "physical_annotation_required": True,
                "end_boot_and_daemon_identity_required": True,
                "global_trace_write": False,
                "diagnostic_eligible": False,
                "execution_guard": "--run --reviewed",
            }, indent=2))
        return
    require(args.reviewed, "live execution requires both --run and --reviewed")
    require(not (BASE / (args.label + ".onset")).exists(), "existing local capture refused")
    run_capture(args.label)


if __name__ == "__main__":
    main()
