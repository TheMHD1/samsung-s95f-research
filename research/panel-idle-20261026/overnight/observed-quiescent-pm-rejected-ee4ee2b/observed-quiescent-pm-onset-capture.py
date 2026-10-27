#!/usr/bin/env python3
"""Prepare one passive PM onset capture with bounded numeric-54 quiescence retry.

Dry by default. This derivative preserves the frozen seven-event PM observer
and changes only the pre-start read-only syscall-quiescence loop: an observed
numeric ARM32 syscall 54 may be retried within the existing fixed budget, but
only a later numeric non-54 point sample qualifies the TID. It never infers a
return, physical state, causation, or generic absence.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
FROZEN_SOURCE = BASE / "observed-pm-onset-capture.py"
FROZEN_SHA256 = "c7b07bbcb508005c028824763c84109d18aee1d9df8813a5f59c476093616d06"
DESIGN = BASE / "pm-prestart-quiescence-review.md"
DESIGN_SHA256 = "d7c8e0be5cec4867159c20e4864d5c9b7740765829f2ac3ebc78f9b09d657229"
ADDENDUM = BASE / "pm-prestart-quiescence-addendum.md"
ADDENDUM_SHA256 = "b72e70e640d9b32420d14d0c9bb76c1ec62ed2f254cb5c181e6d8f06a6b98678"

for _path, _digest in ((FROZEN_SOURCE, FROZEN_SHA256),
                       (DESIGN, DESIGN_SHA256),
                       (ADDENDUM, ADDENDUM_SHA256)):
    if hashlib.sha256(_path.read_bytes()).hexdigest() != _digest:
        raise RuntimeError("pinned quiescent PM dependency changed: " + str(_path))

_spec = importlib.util.spec_from_file_location("frozen_pm_observer_c7b07b", FROZEN_SOURCE)
if _spec is None or _spec.loader is None:
    raise RuntimeError("frozen PM observer dependency unavailable")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
_preroll = _base._base

MODEL, BUILD, ACCESS = _base.MODEL, _base.BUILD, _base.ACCESS
AVE_PATH, AVE_SHA = _base.AVE_PATH, _base.AVE_SHA
AVOC_PATH, AVOC_SHA = _base.AVOC_PATH, _base.AVOC_SHA
DEV_PATH, DEV_SHA = _base.DEV_PATH, _base.DEV_SHA
PM_EVENTS = _base.PM_EVENTS
require, sections = _base.require, _base.sections
QUIESCENCE_MAX_ATTEMPTS = _preroll.QUIESCENCE_MAX_ATTEMPTS
QUIESCENCE_RETRY_SECONDS = _preroll.QUIESCENCE_RETRY_SECONDS
PRELUDE_MAX_SECONDS = _preroll.PRELUDE_MAX_SECONDS
ENABLE_BRACKET_MAX_SECONDS = _preroll.ENABLE_BRACKET_MAX_SECONDS
TidEvidence = _preroll.TidEvidence

REMOTE_ROOT = "/tmp/researcher-observed-quiescent-pm-onset-20261026"
STAGE_ROOT = "/tmp/researcher-observed-quiescent-pm-onset-stage-20261026"
TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-quiescent-pm-onset-"
PARENT_REMOTE_ROOT = _base.REMOTE_ROOT
PARENT_STAGE_ROOT = _base.STAGE_ROOT
PARENT_TRACE_PREFIX = _base.TRACE_PREFIX

_ORIGINAL_BUILD = _base.build_remote_script
_ORIGINAL_ROOT = _base.root
_ORIGINAL_RUN = _base.run_capture


def _once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, "frozen PM anchor mismatch: " + label)
    return text.replace(old, new, 1)


def _namespace(text: str) -> str:
    return (text.replace(PARENT_REMOTE_ROOT, REMOTE_ROOT)
            .replace(PARENT_STAGE_ROOT, STAGE_ROOT)
            .replace(PARENT_TRACE_PREFIX, TRACE_PREFIX))


def build_remote_script(label: str, seconds: int, allow_short: bool = False) -> str:
    """Render the frozen collector with only numeric-54 bounded retry changed."""
    shell = _namespace(_ORIGINAL_BUILD(label, seconds, allow_short=allow_short))
    old = 'test "$qnr" -ne 54 || exit 86; qualified=1; break'
    new = (f'if test "$qnr" -eq 54; then test "$qi" -lt '
           f'{QUIESCENCE_MAX_ATTEMPTS} || exit 86; sleep '
           f'{QUIESCENCE_RETRY_SECONDS}; continue; fi; qualified=1; break')
    shell = _once(shell, old, new, "numeric-54 quiescence retry")
    require(shell.count('/proc/$ap/task/$qt/syscall') == 1,
            "quiescence syscall reader count changed")
    require('test "$qraw" = running' in shell and
            'test "$qnr" -eq 54' in shell and
            f'test "$qi" -lt {QUIESCENCE_MAX_ATTEMPTS}' in shell,
            "bounded quiescence retry guard missing")
    require(PARENT_REMOTE_ROOT not in shell and PARENT_STAGE_ROOT not in shell and
            PARENT_TRACE_PREFIX not in shell, "parent PM namespace remains")
    return shell


def parse_fds(text: str) -> dict:
    """Validate exact TID/FD evidence with bounded intermediate numeric 54 rows."""
    part = sections(text)
    expected = {"TIDS_START", "FDS_START", "TIDS_PRE", "TRACE_ARMING_START",
                "TIDS_ARM", "SYSCALL_QUIESCENCE", "TIDS_QUIESCENT",
                "FDS_PREROLL", "TRACE_ARMING_END", "TIDS_END", "FDS_END"}
    require(set(part) == expected, "unexpected TID/FD/pre-roll sections")
    tids = _preroll._tid_rows(part["TIDS_START"], "starting")
    for name in ("TIDS_PRE", "TIDS_ARM", "TIDS_QUIESCENT", "TIDS_END"):
        require(_preroll._tid_rows(part[name], name) == tids,
                "AVOC TID set changed before/during pre-roll capture")

    start = _preroll._named_floats(
        part["TRACE_ARMING_START"], ("ENABLE_BEFORE", "ENABLE_AFTER", "TRACE_ARMED_BODY"))
    end = _preroll._named_floats(
        part["TRACE_ARMING_END"], ("SWEEP_START", "SWEEP_END", "PREROLL_BODY"))
    eb, ea, armed = (start[key] for key in
                     ("ENABLE_BEFORE", "ENABLE_AFTER", "TRACE_ARMED_BODY"))
    qs, qe, preroll = (end[key] for key in
                       ("SWEEP_START", "SWEEP_END", "PREROLL_BODY"))
    require(eb <= ea and ea - eb <= ENABLE_BRACKET_MAX_SECONDS and
            abs(armed - ea) <= .001 and ea <= qs <= qe <= preroll and
            0 < preroll - armed <= PRELUDE_MAX_SECONDS and
            qe - qs <= PRELUDE_MAX_SECONDS,
            "trace enable/prelude evidence outside bounds")

    attempts: dict[int, list[dict]] = {tid: [] for tid in tids}
    seen_order: list[int] = []
    prior_time = -math.inf
    for line in part["SYSCALL_QUIESCENCE"].splitlines():
        fields = line.split("|", 4)
        require(len(fields) == 5 and fields[0] == "ATTEMPT" and
                fields[1].isdigit() and fields[2].isdigit(),
                "malformed syscall quiescence row")
        tid, index = int(fields[1]), int(fields[2])
        when = float(fields[3])
        raw = fields[4]
        require(tid in attempts and math.isfinite(when) and qs <= when <= qe and
                when >= prior_time and index == len(attempts[tid]) + 1 and
                index <= QUIESCENCE_MAX_ATTEMPTS,
                "invalid syscall quiescence ordering/bounds")
        if not seen_order or seen_order[-1] != tid:
            require(tid not in seen_order, "duplicate syscall quiescence TID group")
            seen_order.append(tid)
        prior_time = when
        if raw == "running":
            kind, number = "indeterminate", None
        else:
            match = re.match(r"^(-?[0-9]+)(?:\s|$)", raw)
            require(match is not None, "malformed syscall quiescence payload")
            number = int(match.group(1))
            kind = "transient_active_54" if number == 54 else "numeric"
        attempts[tid].append({"attempt": index, "uptime": when, "raw": raw,
                              "kind": kind, "syscall": number})
    require(seen_order == tids, "syscall quiescence TID order incomplete")

    terminals, active = [], []
    permitted_intermediate = {"indeterminate", "transient_active_54"}
    for tid in tids:
        rows = attempts[tid]
        require(rows and len(rows) <= QUIESCENCE_MAX_ATTEMPTS and
                rows[-1]["kind"] == "numeric" and
                all(row["kind"] in permitted_intermediate for row in rows[:-1]),
                "syscall quiescence lacks terminal numeric non-54 point anchor")
        terminals.append({"tid": tid, **rows[-1]})
        active.extend({"tid": tid, **row} for row in rows
                      if row["kind"] == "transient_active_54")

    f0, fp, f1 = (_preroll._fdmap(part[name]) for name in
                  ("FDS_START", "FDS_PREROLL", "FDS_END"))
    changes = {str(fd): {"start": f0.get(fd), "preroll": fp.get(fd),
                         "end": f1.get(fd)}
               for fd in sorted(set(f0) | set(fp) | set(f1))
               if len({f0.get(fd), fp.get(fd), f1.get(fd)}) != 1}
    evidence = {
        "trace_enable_bracket": [eb, ea], "trace_armed_body": armed,
        "sweep_start": qs, "sweep_end": qe, "preroll_body": preroll,
        "syscall_quiescence": {
            "tids": tids, "attempts_by_tid": {str(k): v for k, v in attempts.items()},
            "terminal_numeric_rows": terminals, "active_nr54": active,
            "indeterminate_exhausted": [], "active_nr54_exhausted": [],
            "max_attempts_per_tid": QUIESCENCE_MAX_ATTEMPTS,
            "retry_interval_seconds": QUIESCENCE_RETRY_SECONDS,
            "duration_seconds": qe - qs, "complete": True,
            "qualification": ("Every TID has a terminal numeric non-54 point sample; "
                              "intermediate 54 rows are retained observations, not returns.")},
        "fds_start": f0, "fds_preroll": fp, "fds_end": f1}
    return {"tids": TidEvidence(tids, evidence), "pre_tids": tids,
            "armed_tids": tids, "quiescent_tids": tids,
            "fd_changes": changes, "fd_targets_stable": not changes,
            "fd_targets_start": {str(k): v for k, v in f0.items()},
            "fd_targets_preroll": {str(k): v for k, v in fp.items()},
            "fd_targets_end": {str(k): v for k, v in f1.items()},
            "trace_arming": {key: value for key, value in evidence.items()
                             if key not in {"fds_start", "fds_preroll", "fds_end"}},
            "qualification": ("Exact START/PRE/ARM/post-sweep/END TIDs, raw bounded "
                              "syscall attempts with terminal non-54 point anchors, and "
                              "complete FD snapshots; no observed 54 return is inferred.")}


def root(command: str, timeout: int, audit_prefix: Path | None = None):
    return _ORIGINAL_ROOT(_namespace(command), timeout, audit_prefix)


@contextlib.contextmanager
def _patched_pm():
    """Install the derivative only for one nested run, then restore exactly."""
    # Leave the parent's constants untouched while it renders: its own
    # self-checks intentionally require its pinned namespace.  The derivative
    # build/root wrappers translate the completed shell and every command.
    pm_names = {"root": root, "build_remote_script": build_remote_script}
    preroll_names = {"parse_fds": parse_fds}
    saved_pm = {name: getattr(_base, name) for name in pm_names}
    saved_preroll = {name: getattr(_preroll, name) for name in preroll_names}
    for name, value in pm_names.items():
        setattr(_base, name, value)
    for name, value in preroll_names.items():
        setattr(_preroll, name, value)
    try:
        yield
    finally:
        for name, value in saved_preroll.items():
            setattr(_preroll, name, value)
        for name, value in saved_pm.items():
            setattr(_base, name, value)


def run_capture(label: str, seconds: int, smoke_unobserved: bool = False) -> None:
    with _patched_pm():
        _ORIGINAL_RUN(label, seconds, smoke_unobserved=smoke_unobserved)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("--seconds", type=int, default=86)
    parser.add_argument("--smoke-unobserved", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--emit-shell", action="store_true")
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,30}", args.label) is not None,
            "use a unique lowercase label")
    for name, digest in {"binaries/libave.so.0.1": AVE_SHA,
                         "binaries/avocd": AVOC_SHA,
                         "binaries/deviced": DEV_SHA}.items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
                "local matching binary hash changed: " + name)
    if args.smoke_unobserved:
        require(args.seconds in {5, 10}, "smoke-unobserved requires --seconds 5 or 10")
    else:
        require(85 <= args.seconds <= 90, "full capture requires --seconds 85..90")
    shell = build_remote_script(args.label, args.seconds,
                                allow_short=args.smoke_unobserved)
    raw, digest = shell.encode(), hashlib.sha256(shell.encode()).hexdigest()
    largest = len(("set -eu\nprintf %s " +
                   "A" * len(__import__("base64").b64encode(b"x" * 4096)) +
                   f" | base64 -d >>{STAGE_ROOT}/{args.label}/capture.sh").encode())
    require(largest <= 8192, "staging command exceeds controller limit")
    if not args.run:
        if args.emit_shell:
            print(shell, end="")
        else:
            print(json.dumps({
                "mode": "dry-run; no TV/network/root call", "seconds": args.seconds,
                "capture_kind": ("smoke-unobserved" if args.smoke_unobserved
                                 else "full-observed"),
                "frozen_pm_observer_sha256": FROZEN_SHA256,
                "quiescence_design_sha256": DESIGN_SHA256,
                "quiescence_addendum_sha256": ADDENDUM_SHA256,
                "staged_script_bytes": len(raw), "staged_script_sha256": digest,
                "largest_staging_command_bytes": largest,
                "remote_root": REMOTE_ROOT, "stage_root": STAGE_ROOT,
                "trace_namespace": TRACE_PREFIX, "pm_events": PM_EVENTS,
                "quiescence": {
                    "read_only_proc_syscall": True,
                    "max_attempts_per_tid": QUIESCENCE_MAX_ATTEMPTS,
                    "retry_interval_seconds": QUIESCENCE_RETRY_SECONDS,
                    "prelude_max_seconds": PRELUDE_MAX_SECONDS,
                    "running_is_qualified": False,
                    "numeric_54_is_intermediate_only": True,
                    "terminal_numeric_non54_required": True,
                    "trace_exit_is_qualification": False},
                "physical_window": "CAPTURE_START..CAPTURE_END unchanged",
                "absence_claim_supported": False, "diagnostic_eligible": False,
                "capacity_status": "requires separately reviewed passive smoke",
                "execution_guard": "--run --reviewed",
            }, indent=2))
        return
    require(args.reviewed,
            "live execution requires both --run and --reviewed after independent review")
    require(not (BASE / (args.label + ".onset")).exists(),
            "existing local capture refused")
    run_capture(args.label, args.seconds, smoke_unobserved=args.smoke_unobserved)


if __name__ == "__main__":
    main()
