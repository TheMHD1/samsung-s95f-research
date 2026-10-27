#!/usr/bin/env python3
"""Prepare one finite 60-second observed HDMI onset capture; dry by default.

This host-only derivative reuses the accepted corrected short collector's
complete quiescence, identity, observer, physical-annotation and cleanup
contexts.  It changes only the fixed duration and every private namespace.
It never runs without both --run and --reviewed.
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
SHORT_SOURCE = BASE / "observed-short-onset-capture.py"
SHORT_SHA256 = "5c0e4ff02d1b54f4493dede7c7cda5eb78d2163d936b207c26f572a5ab00f7c4"
WINDOW_SECONDS = 60
REMOTE_ROOT = "/tmp/researcher-observed-hdmi-onset-20261027"
STAGE_ROOT = "/tmp/researcher-observed-hdmi-onset-stage-20261027"
TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-hdmi-onset-"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


if hashlib.sha256(SHORT_SOURCE.read_bytes()).hexdigest() != SHORT_SHA256:
    raise RuntimeError("pinned corrected short ancestor changed")
_spec = importlib.util.spec_from_file_location("observed_hdmi_short_ancestor", SHORT_SOURCE)
if _spec is None or _spec.loader is None:
    raise RuntimeError("corrected short ancestor unavailable")
_short = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_short)
_SHORT_BUILD = _short.build_remote_script

# The short derivative independently pins this accepted quiescent ancestor.
FROZEN_SOURCE = _short.FROZEN_SOURCE
FROZEN_SHA256 = _short.FROZEN_SHA256
MODEL, BUILD, ACCESS = _short.MODEL, _short.BUILD, _short.ACCESS
AVE_PATH, AVE_SHA = _short.AVE_PATH, _short.AVE_SHA
AVOC_PATH, AVOC_SHA = _short.AVOC_PATH, _short.AVOC_SHA
DEV_PATH, DEV_SHA = _short.DEV_PATH, _short.DEV_SHA
PM_EVENTS = _short.PM_EVENTS


def _kernel_snapshot_shell(shell: str) -> str:
    """Add two synchronous, all-or-fail bounded ring snapshots to artifacts."""
    # The established 2 MiB artifacts limit applies to the combined artifact
    # and both snapshots. A capped base64 writer is checked before its end
    # marker, so the capture fails instead of presenting it as complete.
    start_anchor = '} >"$O/artifacts.txt" 2>&1)\n'
    start = (
        'ksnap() { kt=$1; '
        '(ulimit -f 2048; { echo "@@ KERNEL_$kt"; cat /proc/sys/kernel/random/boot_id; '
        'cat /proc/uptime; dmesg | gzip -c | base64; ks=$?; '
        'echo "@@ KERNEL_${kt}_END"; test "$ks" -eq 0; }) >>"$O/artifacts.txt" || return 1; '
        '}\nksnap START || exit 88\n'
    )
    begin = shell.find(start_anchor, shell.find('@@ BASELINE'))
    require(begin >= 0, "baseline artifacts anchor missing")
    begin += len(start_anchor)
    require(shell.find(start_anchor, begin) < 0, "ambiguous baseline artifacts anchor")
    shell = shell[:begin] + start + shell[begin:]
    end_anchor = 'rmdir "$T"; te="$te $td"; set +e; sleep 2;'
    require(shell.count(end_anchor) == 1, "trace export anchor missing or ambiguous")
    end = shell.find(end_anchor) + len('rmdir "$T";')
    shell = shell[:end] + ' ksnap END || exit 89;' + shell[end:]
    for marker in ("@@ KERNEL_$kt", "@@ KERNEL_${kt}_END",
                   "dmesg | gzip -c | base64", "ksnap START || exit 88",
                   "ksnap END || exit 89"):
        require(marker in shell, "kernel snapshot marker missing: " + marker)
    return shell


def _render_from_short(label: str, seconds: int, allow_short: bool) -> str:
    shell = _SHORT_BUILD(label, seconds, allow_short=allow_short)
    return _kernel_snapshot_shell(shell)


def _nested_hdmi_builder(label: str, seconds: int = WINDOW_SECONDS,
                         allow_short: bool = False) -> str:
    require(seconds == WINDOW_SECONDS, "HDMI observed window is fixed at 60 seconds")
    require(not allow_short, "HDMI observed capture remains a full physical-window mode")
    return _render_from_short(label, seconds, allow_short=False)


@contextlib.contextmanager
def _adapt_short_boundary(install_nested_builder: bool = False):
    """Use the full accepted context while altering only its fixed boundary."""
    names = ("WINDOW_SECONDS", "REMOTE_ROOT", "STAGE_ROOT", "TRACE_PREFIX")
    saved = {name: getattr(_short, name) for name in names}
    old_build = _short.build_remote_script
    old_require = _short.require
    def permit_sixty(condition: bool, message: str) -> None:
        # The ancestor's post-render assertion names its fixed 30-second text.
        # Its terminal guard and all other require calls remain unchanged.
        if not condition and message == "fixed 30-second capture duration absent":
            return
        old_require(condition, message)
    _short.WINDOW_SECONDS = WINDOW_SECONDS
    _short.REMOTE_ROOT = REMOTE_ROOT
    _short.STAGE_ROOT = STAGE_ROOT
    _short.TRACE_PREFIX = TRACE_PREFIX
    _short.require = permit_sixty
    if install_nested_builder:
        _short.build_remote_script = _nested_hdmi_builder
    try:
        yield
    finally:
        _short.require = old_require
        _short.build_remote_script = old_build
        for name, value in saved.items():
            setattr(_short, name, value)


def build_remote_script(label: str, seconds: int = WINDOW_SECONDS,
                        allow_short: bool = False) -> str:
    require(seconds == WINDOW_SECONDS, "HDMI observed window is fixed at 60 seconds")
    require(not allow_short, "HDMI observed capture remains a full physical-window mode")
    with _adapt_short_boundary():
        shell = _render_from_short(label, seconds, allow_short=False)
    require(REMOTE_ROOT in shell and STAGE_ROOT in shell and TRACE_PREFIX in shell,
            "HDMI namespace absent from rendered collector")
    require("-v n=60" in shell, "fixed 60-second capture duration absent")
    require("CAPTURE_START" in shell and "CAPTURE_END" in shell,
            "physical annotation markers absent")
    return shell


def run_capture(label: str) -> None:
    with _adapt_short_boundary(install_nested_builder=True):
        _short.run_capture(label)


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
    require(args.seconds == WINDOW_SECONDS, "HDMI observed window is fixed at 60 seconds")
    require(hashlib.sha256(FROZEN_SOURCE.read_bytes()).hexdigest() == FROZEN_SHA256,
            "pinned quiescent PM ancestor changed")
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
                "capture_kind": "full-observed-hdmi",
                "seconds": WINDOW_SECONDS,
                "corrected_short_ancestor_sha256": SHORT_SHA256,
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
