#!/usr/bin/env python3
"""Prepare one bounded observed onset capture with an audited trace pre-roll.

Dry by default.  This is a hash-pinned, fail-closed revision of the frozen
base-QDDimming branch observer.  It adds only a private trace prelude,
read-only per-TID syscall quiescence evidence, a declared pre-roll marker, and
boundary-aware syscall accounting.  Physical/annotation eligibility remains
strictly CAPTURE_START..CAPTURE_END.  No sampled or traced value establishes
physical light, event absence, policy choice, or causation.
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
import subprocess
import sys


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
FROZEN_SOURCE = BASE / "observed-branch-onset-capture.py"
FROZEN_SHA256 = "3aa5c9480c8a643e14be5c6aeac62202f918d16cd9100a5b0c4ff14a5e2785ca"
if hashlib.sha256(FROZEN_SOURCE.read_bytes()).hexdigest() != FROZEN_SHA256:
    raise RuntimeError("frozen branch observer dependency hash changed")
_spec = importlib.util.spec_from_file_location("frozen_branch_observer_3aa5c94", FROZEN_SOURCE)
if _spec is None or _spec.loader is None:
    raise RuntimeError("frozen branch observer dependency unavailable")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

MODEL, BUILD, ACCESS = _base.MODEL, _base.BUILD, _base.ACCESS
AVE_PATH, AVE_SHA = _base.AVE_PATH, _base.AVE_SHA
AVOC_PATH, AVOC_SHA = _base.AVOC_PATH, _base.AVOC_SHA
DEV_PATH, DEV_SHA = _base.DEV_PATH, _base.DEV_SHA
TRACE_DRAIN_SECONDS = _base.TRACE_DRAIN_SECONDS
TRACE_DRAIN_MIN_SECONDS = _base.TRACE_DRAIN_MIN_SECONDS
TRACE_DRAIN_MAX_SECONDS = _base.TRACE_DRAIN_MAX_SECONDS
SIDECAR_LIMITS, SUFFIX = _base.SIDECAR_LIMITS, _base.SUFFIX
TRACE_CONFIG_EXPECTED = _base.TRACE_CONFIG_EXPECTED
ROW_SPAN_MAX_SECONDS = _base.ROW_SPAN_MAX_SECONDS

REMOTE_ROOT = "/tmp/researcher-observed-preroll-onset-20261026"
STAGE_ROOT = "/tmp/researcher-observed-preroll-onset-stage-20261026"
TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-preroll-onset-"
BRANCH_REMOTE_ROOT = _base.REMOTE_ROOT
BRANCH_STAGE_ROOT = _base.STAGE_ROOT
BRANCH_TRACE_PREFIX = _base.TRACE_PREFIX
PRELUDE_MAX_SECONDS = 0.500
ENABLE_BRACKET_MAX_SECONDS = 0.050
PREROLL_MIN_SECONDS = 0.750
PREROLL_MAX_SECONDS = 1.250
QUIESCENCE_MAX_ATTEMPTS = 8
QUIESCENCE_RETRY_SECONDS = 0.002

require = _base.require
sections = _base.sections
syscall_filter_for_tids = _base.syscall_filter_for_tids
validate_metadata = _base.validate_metadata
analyze_samples = _base.analyze_samples
validate_dd_summaries = _base.validate_dd_summaries
vlog_coverage = _base.vlog_coverage
vlog_markers = _base.vlog_markers
parse_manifest = _base.parse_manifest
verify_sidecars = _base.verify_sidecars
parse_annotation = _base.parse_annotation
annotation_summary = _base.annotation_summary
assess_annotations = _base.assess_annotations
private_text = _base.private_text
mark_cleanup_failure = _base.mark_cleanup_failure
mark_acquisition_failure = _base.mark_acquisition_failure

_ORIGINAL_BUILD = _base.build_remote_script
_ORIGINAL_ROOT = _base.root
_ORIGINAL_RUN = _base.run_capture


def _once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, "frozen branch anchor mismatch: " + label)
    return text.replace(old, new, 1)


def _namespace(text: str) -> str:
    return (text.replace(BRANCH_REMOTE_ROOT, REMOTE_ROOT)
            .replace(BRANCH_STAGE_ROOT, STAGE_ROOT)
            .replace(BRANCH_TRACE_PREFIX, TRACE_PREFIX))


def build_remote_script(label: str, seconds: int, allow_short: bool = False) -> str:
    """Build the inherited collector plus bounded pre-roll/quiescence logic."""
    shell = _namespace(_ORIGINAL_BUILD(label, seconds, allow_short=allow_short))
    old_arm = ('''arm=$(awk -v t="$TARGET" 'BEGIN{printf "%.3f",t-1}'); '''
               '''now=$(cut -d" " -f1 /proc/uptime); delay=$(awk -v n="$now" -v t="$arm" 'BEGIN{printf "%.3f",t-n}'); sleep "$delay"''')
    new_arm = ('''arm=$(awk -v t="$TARGET" 'BEGIN{printf "%.3f",t-1.75}'); '''
               '''now=$(cut -d" " -f1 /proc/uptime); delay=$(awk -v n="$now" -v t="$arm" 'BEGIN{printf "%.3f",t-n}'); sleep "$delay"''')
    shell = _once(shell, old_arm, new_arm, "early filter/setup schedule")

    old_enable = '''echo 1 >"$T/tracing_on"; tids_arm=$(tids); test "$tids_arm" = "$tids_pre"; (ulimit -f 2048; { echo @@ TIDS_ARM; echo "$tids_arm"; } >>"$O/fds.txt")
now=$(cut -d" " -f1 /proc/uptime); delay=$(awk -v n="$now" -v t="$TARGET" 'BEGIN{printf "%.3f",t-n}'); sleep "$delay"; ts=$(cut -d" " -f1 /proc/uptime); awk -v n="$ts" -v t="$TARGET" 'BEGIN{exit !(n>=t&&n<=t+.75)}' '''.rstrip()
    new_enable = f'''trace_arm_target=$(awk -v t="$TARGET" 'BEGIN{{printf "%.3f",t-1.25}}'); now=$(cut -d" " -f1 /proc/uptime); delay=$(awk -v n="$now" -v t="$trace_arm_target" 'BEGIN{{printf "%.3f",t-n}}'); sleep "$delay"
eb=$(cut -d" " -f1 /proc/uptime); echo 1 >"$T/tracing_on"; ea=$(cut -d" " -f1 /proc/uptime); awk -v b="$eb" -v a="$ea" 'BEGIN{{exit !(a>=b&&a-b<={ENABLE_BRACKET_MAX_SECONDS})}}'
echo "CAPTURE_TRACE_ARMED utc=$(date -u +%s) uptime=$ea" >"$T/trace_marker"
tids_arm=$(tids); test "$tids_arm" = "$tids_pre"; qs=$(cut -d" " -f1 /proc/uptime)
(ulimit -f 2048; {{ echo @@ TRACE_ARMING_START; echo "ENABLE_BEFORE $eb"; echo "ENABLE_AFTER $ea"; echo "TRACE_ARMED_BODY $ea"; echo @@ TIDS_ARM; echo "$tids_arm"; echo @@ SYSCALL_QUIESCENCE; }} >>"$O/fds.txt")
for qt in $tids_arm; do qualified=0; qi=0; while test "$qi" -lt {QUIESCENCE_MAX_ATTEMPTS}; do qi=$((qi+1)); qu=$(cut -d" " -f1 /proc/uptime); qraw=; qstatus=ok; if ! IFS= read -r qraw <"/proc/$ap/task/$qt/syscall"; then qstatus=read-error; qraw='!read'; fi; printf 'ATTEMPT|%s|%s|%s|%s\n' "$qt" "$qi" "$qu" "$qraw" >>"$O/fds.txt"; qnow=$(cut -d" " -f1 /proc/uptime); awk -v a="$ea" -v n="$qnow" 'BEGIN{{exit !(n>=a&&n-a<={PRELUDE_MAX_SECONDS})}}'; test "$qstatus" = ok || exit 83; if test "$qraw" = running; then test "$qi" -lt {QUIESCENCE_MAX_ATTEMPTS} || exit 84; sleep {QUIESCENCE_RETRY_SECONDS}; continue; fi; set -- $qraw; qnr=${{1:-}}; case "$qnr" in -*) qdigits=${{qnr#-}};; *) qdigits=$qnr;; esac; case "$qdigits" in ''|*[!0-9]*) exit 85;; esac; test "$qnr" -ne 54 || exit 86; qualified=1; break; done; test "$qualified" = 1 || exit 87; done
qe=$(cut -d" " -f1 /proc/uptime); tids_quiet=$(tids); test "$tids_quiet" = "$tids_pre"; awk -v a="$ea" -v e="$qe" 'BEGIN{{exit !(e>=a&&e-a<={PRELUDE_MAX_SECONDS})}}'
(ulimit -f 2048; {{ echo @@ TIDS_QUIESCENT; echo "$tids_quiet"; echo @@ FDS_PREROLL; for q in /proc/$ap/fd/*; do printf "%s " "${{q##*/}}"; readlink "$q" || true; done; }} >>"$O/fds.txt")
pr=$(cut -d" " -f1 /proc/uptime); awk -v a="$ea" -v p="$pr" -v t="$TARGET" 'BEGIN{{exit !(p>a&&p-a<={PRELUDE_MAX_SECONDS}&&t-p>={PREROLL_MIN_SECONDS}&&t-p<={PREROLL_MAX_SECONDS})}}'; echo "CAPTURE_PREROLL_START utc=$(date -u +%s) uptime=$pr" >"$T/trace_marker"
(ulimit -f 2048; {{ echo @@ TRACE_ARMING_END; echo "SWEEP_START $qs"; echo "SWEEP_END $qe"; echo "PREROLL_BODY $pr"; }} >>"$O/fds.txt")
now=$(cut -d" " -f1 /proc/uptime); delay=$(awk -v n="$now" -v t="$TARGET" 'BEGIN{{printf "%.3f",t-n}}'); sleep "$delay"; ts=$(cut -d" " -f1 /proc/uptime); awk -v n="$ts" -v t="$TARGET" 'BEGIN{{exit !(n>=t&&n<=t+.75)}}' '''
    shell = _once(shell, old_enable, new_enable, "trace pre-roll arming and quiescence")
    require("CAPTURE_TRACE_ARMED" in shell and "CAPTURE_PREROLL_START" in shell,
            "pre-roll markers missing")
    require("/proc/$ap/task/$qt/syscall" in shell and "qraw\" = running" in shell,
            "quiescence guard missing")
    require(BRANCH_REMOTE_ROOT not in shell and BRANCH_STAGE_ROOT not in shell and
            BRANCH_TRACE_PREFIX not in shell, "old private namespace remains")
    return shell


class TidEvidence(list):
    """A JSON-compatible TID list carrying the validated sidecar evidence."""

    def __init__(self, values, evidence):
        super().__init__(values)
        self.evidence = evidence


def _tid_rows(value: str, label: str) -> list[int]:
    rows = value.splitlines()
    require(rows and all(row.isdigit() and int(row) > 0 for row in rows),
            "invalid " + label + " TID set")
    result = [int(row) for row in rows]
    require(result == sorted(set(result)), "invalid " + label + " TID set")
    return result


def _fdmap(value: str) -> dict[int, str]:
    result: dict[int, str] = {}
    for line in value.splitlines():
        number, sep, target = line.partition(" ")
        require(sep and number.isdigit() and int(number) not in result and target,
                "malformed FD target row")
        result[int(number)] = target
    return result


def _named_floats(value: str, names: tuple[str, ...]) -> dict[str, float]:
    rows = value.splitlines()
    require(len(rows) == len(names), "malformed trace arming evidence")
    result = {}
    for row, expected in zip(rows, names):
        fields = row.split()
        require(len(fields) == 2 and fields[0] == expected,
                "malformed trace arming evidence")
        number = float(fields[1])
        require(math.isfinite(number), "non-finite trace arming evidence")
        result[expected] = number
    return result


def parse_fds(text: str) -> dict:
    part = sections(text)
    expected = {"TIDS_START", "FDS_START", "TIDS_PRE", "TRACE_ARMING_START",
                "TIDS_ARM", "SYSCALL_QUIESCENCE", "TIDS_QUIESCENT",
                "FDS_PREROLL", "TRACE_ARMING_END", "TIDS_END", "FDS_END"}
    require(set(part) == expected, "unexpected TID/FD/pre-roll sections")
    tids = _tid_rows(part["TIDS_START"], "starting")
    for name in ("TIDS_PRE", "TIDS_ARM", "TIDS_QUIESCENT", "TIDS_END"):
        require(_tid_rows(part[name], name) == tids,
                "AVOC TID set changed before/during pre-roll capture")

    start = _named_floats(part["TRACE_ARMING_START"],
                          ("ENABLE_BEFORE", "ENABLE_AFTER", "TRACE_ARMED_BODY"))
    end = _named_floats(part["TRACE_ARMING_END"],
                        ("SWEEP_START", "SWEEP_END", "PREROLL_BODY"))
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
    seen_order = []
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
            require(number != 54, "active syscall54 during quiescence sweep")
            kind = "numeric"
        attempts[tid].append({"attempt": index, "uptime": when, "raw": raw,
                              "kind": kind, "syscall": number})
    require(seen_order == tids, "syscall quiescence TID order incomplete")
    terminals = []
    for tid in tids:
        rows = attempts[tid]
        require(rows and len(rows) <= QUIESCENCE_MAX_ATTEMPTS and
                rows[-1]["kind"] == "numeric" and
                all(row["kind"] == "indeterminate" for row in rows[:-1]),
                "syscall quiescence lacks terminal numeric non-54 row")
        terminals.append({"tid": tid, **rows[-1]})

    f0, fp, f1 = (_fdmap(part[name]) for name in
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
            "terminal_numeric_rows": terminals, "active_nr54": [],
            "indeterminate_exhausted": [],
            "max_attempts_per_tid": QUIESCENCE_MAX_ATTEMPTS,
            "retry_interval_seconds": QUIESCENCE_RETRY_SECONDS,
            "duration_seconds": qe - qs, "complete": True},
        "fds_start": f0, "fds_preroll": fp, "fds_end": f1}
    return {"tids": TidEvidence(tids, evidence), "pre_tids": tids,
            "armed_tids": tids, "quiescent_tids": tids,
            "fd_changes": changes, "fd_targets_stable": not changes,
            "fd_targets_start": {str(k): v for k, v in f0.items()},
            "fd_targets_preroll": {str(k): v for k, v in fp.items()},
            "fd_targets_end": {str(k): v for k, v in f1.items()},
            "trace_arming": {key: value for key, value in evidence.items()
                              if key not in {"fds_start", "fds_preroll", "fds_end"}},
            "qualification": "Exact START/PRE/ARM/post-sweep/END TIDs, raw bounded syscall-quiescence attempts, and complete start/pre-roll/end FD snapshots; endpoint equality cannot exclude close/reopen-to-same-target."}


def validate_trace_scope(meta: dict, fd_report: dict) -> None:
    require(meta["trace_filter_tids"] == fd_report["pre_tids"] and
            meta["trace_filter"] == syscall_filter_for_tids(fd_report["pre_tids"]),
            "scoped ARM32 ioctl54 completeness filter mismatch")


def _region_for_line(line: int, marker_lines: dict[str, int]) -> str:
    if line < marker_lines["TRACE_ARMED"]:
        return "enable-slop"
    if marker_lines["TRACE_ARMED"] < line < marker_lines["PREROLL_START"]:
        return "trace-prelude"
    if marker_lines["PREROLL_START"] < line < marker_lines["START"]:
        return "pre-roll"
    if marker_lines["START"] < line < marker_lines["END"]:
        return "capture-window"
    if marker_lines["END"] < line < marker_lines["DRAIN_END"]:
        return "drain"
    if line > marker_lines["DRAIN_END"]:
        return "post-drain"
    return "marker"


def trace_accounting(data: bytes, tids: list[int], avoc_pid: int, collector_pid: int,
                     expected_start: float, expected_end: float,
                     expected_drain_end: float | None = None) -> dict:
    """Decode five regions without moving the physical START..END window."""
    require(isinstance(tids, TidEvidence), "pre-roll trace lacks guarded sidecar evidence")
    evidence = tids.evidence
    if expected_drain_end is None:
        expected_drain_end = expected_end + TRACE_DRAIN_SECONDS
    text = data.decode("utf-8", errors="strict")
    accounting = re.search(r"entries-in-buffer/entries-written:\s*(\d+)/(\d+)", text)
    require(accounting is not None, "missing trace accounting")
    retained, written = map(int, accounting.groups())
    require(retained == written, "trace ring overflow")
    event_re = re.compile(
        r"^\s*(?P<task>.+?)-(?P<pid>\d+)\s+\((?P<tgid>[^)]*)\)\s+\[\d+\]\s+\S+\s+"
        r"(?P<time>\d+\.\d+): (?P<event>\w+): (?P<body>.*)$")
    message_re = re.compile(
        r"i2c-(\d+) #(\d+) a=([0-9a-f]+) f=([0-9a-f]+) l=(\d+)"
        r"(?: \[([0-9a-f-]*)\])?$", re.I)
    result_re = re.compile(r"i2c-(\d+) n=(\d+) ret=(-?\d+)$")
    marker_re = re.compile(
        r"CAPTURE_(TRACE_ARMED|PREROLL_START|START|END|DRAIN_END) "
        r"utc=([0-9]+) uptime=([0-9]+\.[0-9]+)$")
    events, malformed, markers = [], [], []
    for number, line in enumerate(text.splitlines(), 1):
        match = event_re.match(line)
        if not match:
            continue
        raw_tgid = match["tgid"].strip()
        item = {"line": number, "time": float(match["time"]),
                "pid": int(match["pid"]),
                "tgid": int(raw_tgid) if raw_tgid.isdigit() else None,
                "event": match["event"], "body": match["body"]}
        events.append(item)
        grammar = result_re if item["event"] == "i2c_result" else (
            message_re if item["event"] in {"i2c_write", "i2c_read", "i2c_reply"}
            else None)
        parsed = grammar.fullmatch(item["body"]) if grammar is not None else None
        if grammar is not None and parsed is None:
            malformed.append(number)
        if parsed is not None and item["event"] in {"i2c_write", "i2c_read", "i2c_reply"}:
            if int(parsed.group(1)) != 5 or int(parsed.group(3), 16) != 0x76:
                malformed.append(number)
            payload, declared = parsed.group(6), int(parsed.group(5))
            tokens = [] if payload == "" else (payload.split("-") if payload is not None else [])
            if ((item["event"] in {"i2c_write", "i2c_reply"} and payload is None) or
                    (payload is not None and
                     (len(tokens) != declared or
                      any(re.fullmatch(r"[0-9a-f]{2}", token, re.I) is None
                          for token in tokens)))):
                malformed.append(number)
        if parsed is not None and item["event"] == "i2c_result" and int(parsed.group(1)) != 5:
            malformed.append(number)
        if item["body"].startswith("CAPTURE_"):
            require(item["event"] == "tracing_mark_write" or
                    re.fullmatch(r"0x[0-9a-f]+", item["event"], re.I) is not None,
                    "capture marker has unexpected trace event source")
            marker = marker_re.fullmatch(item["body"])
            require(marker is not None and item["pid"] == collector_pid and
                    item["tgid"] == collector_pid,
                    "malformed capture trace marker or collector identity")
            markers.append({"kind": marker.group(1), "line": number,
                            "trace_time": item["time"], "utc": int(marker.group(2)),
                            "uptime": float(marker.group(3)),
                            "trace_source": item["event"]})
    require(len(events) == retained, "trace decode count incomplete")
    require(all(right["time"] >= left["time"] for left, right in zip(events, events[1:])),
            "trace event timestamps out of order")
    require(not malformed, "malformed I2C trace events")
    kinds = ["TRACE_ARMED", "PREROLL_START", "START", "END", "DRAIN_END"]
    require(len(markers) == 5 and [row["kind"] for row in markers] == kinds,
            "missing/duplicate/reversed exact five trace markers")
    require(len({row["trace_source"] for row in markers}) == 1,
            "capture marker trace sources differ")
    require(all(abs(row["trace_time"] - row["uptime"]) <= .1 for row in markers),
            "trace marker clock mismatch")
    by_kind = {row["kind"]: row for row in markers}
    require(abs(by_kind["TRACE_ARMED"]["uptime"] - evidence["trace_armed_body"]) <= .001 and
            abs(by_kind["PREROLL_START"]["uptime"] - evidence["preroll_body"]) <= .001 and
            abs(by_kind["START"]["uptime"] - expected_start) <= .1 and
            abs(by_kind["END"]["uptime"] - expected_end) <= .1 and
            abs(by_kind["DRAIN_END"]["uptime"] - expected_drain_end) <= .1,
            "trace marker bodies disagree with sidecar/window evidence")
    require(all(right["line"] > left["line"] and right["trace_time"] > left["trace_time"]
                for left, right in zip(markers, markers[1:])),
            "trace marker order invalid")
    prelude = by_kind["PREROLL_START"]["trace_time"] - by_kind["TRACE_ARMED"]["trace_time"]
    preroll = by_kind["START"]["trace_time"] - by_kind["PREROLL_START"]["trace_time"]
    drain = by_kind["DRAIN_END"]["uptime"] - by_kind["END"]["uptime"]
    require(0 < prelude <= PRELUDE_MAX_SECONDS and
            PREROLL_MIN_SECONDS <= preroll <= PREROLL_MAX_SECONDS and
            TRACE_DRAIN_MIN_SECONDS <= drain <= TRACE_DRAIN_MAX_SECONDS,
            "trace prelude/pre-roll/drain duration outside bounds")
    marker_lines = {key: by_kind[key]["line"] for key in kinds}

    pending: dict[int, dict] = {}
    all_pairs, unmatched, post_drain_rows = [], [], []
    six_args = re.compile(
        r"([0-9a-f]+),\s*([0-9a-f]+),\s*([0-9a-f]+),\s*"
        r"([0-9a-f]+),\s*([0-9a-f]+),\s*([0-9a-f]+)", re.I)
    fd_start, fd_preroll, fd_end = (evidence[name] for name in
                                    ("fds_start", "fds_preroll", "fds_end"))
    request_targets = {0xC010643A: ("/dev/dri/card0", "DRM_IOCTL_WAIT_VBLANK"),
                       0xC004510A: ("/dev/sdp_pqe_dp", "PQE_QUERY_EVENT")}

    for item in events:
        if item["event"] not in {"sys_enter", "sys_exit"}:
            continue
        region = _region_for_line(item["line"], marker_lines)
        if region == "post-drain":
            post_drain_rows.append({"kind": item["event"], "tid": item["pid"],
                                    "saved_tgid": item["tgid"], "line": item["line"]})
            continue
        require(region != "marker" and item["tgid"] == avoc_pid and
                item["pid"] in tids,
                "pre-roll/capture syscall row has unrelated saved-TGID/PID")
        if item["event"] == "sys_enter":
            entered = re.fullmatch(r"NR (\d+) \((.*)\)", item["body"])
            require(entered is not None and int(entered.group(1)) == 54,
                    "unexpected syscall enter")
            args = six_args.fullmatch(entered.group(2))
            require(args is not None, "malformed ARM32 ioctl six-register arguments")
            require(item["pid"] not in pending, "duplicate AVOC ioctl enter")
            values = [int(value, 16) for value in args.groups()]
            item.update({"arguments": entered.group(2), "registers": values,
                         "fd": values[0], "request": values[1]})
            pending[item["pid"]] = item
            continue
        exited = re.fullmatch(r"NR (\d+) = (-?[0-9]+)", item["body"])
        require(exited is not None and int(exited.group(1)) == 54,
                "unexpected syscall exit")
        if item["pid"] not in pending:
            require(region in {"enable-slop", "trace-prelude", "pre-roll"},
                    "orphan AVOC ioctl exit in physical window/drain")
            unmatched.append({"kind": "orphan-exit", "tid": item["pid"],
                              "saved_tgid": item["tgid"], "line": item["line"],
                              "region": region})
            continue
        begin = pending.pop(item["pid"])
        begin_region = _region_for_line(begin["line"], marker_lines)
        require(begin["tgid"] == item["tgid"] and begin["time"] <= item["time"],
                "AVOC ioctl pair TGID/time changed")
        if begin_region in {"enable-slop", "trace-prelude"}:
            require(region not in {"capture-window", "drain"},
                    "unbounded prelude ioctl overlaps physical window")
            classification = "outside_or_unbounded_context"
        elif begin_region == "pre-roll":
            require(region in {"pre-roll", "capture-window", "drain"},
                    "pre-roll ioctl crosses drain cutoff")
            classification = ({"pre-roll": "preroll_complete",
                               "capture-window": "start_boundary_completed_in_window",
                               "drain": "start_boundary_completed_in_drain"}[region])
        elif begin_region == "capture-window":
            require(region in {"capture-window", "drain"},
                    "in-window AVOC ioctl unresolved at drain end")
            classification = ("window_complete" if region == "capture-window"
                              else "window_tail_completed")
        elif begin_region == "drain":
            require(region == "drain", "drain-only ioctl crosses cutoff")
            classification = "drain_only"
        else:
            raise ValueError("invalid syscall enter region")
        fd = begin["fd"]
        targets = {"start": fd_start.get(fd), "preroll": fd_preroll.get(fd),
                   "end": fd_end.get(fd)}
        stable = targets["preroll"] is not None and targets["preroll"] == targets["end"]
        stable_from_start = (targets["start"] is not None and
                             targets["start"] == targets["preroll"] == targets["end"])
        relevant_overlap = classification in {
            "start_boundary_completed_in_window", "start_boundary_completed_in_drain",
            "window_complete", "window_tail_completed"}
        attribution_target = (targets["start"] if
                              begin_region in {"enable-slop", "trace-prelude"} and
                              stable_from_start else
                              (targets["preroll"] if begin_region not in
                               {"enable-slop", "trace-prelude"} and stable else None))
        if relevant_overlap:
            require(stable, "physical-overlap ioctl FD target missing or unstable")
        label = None
        if begin["request"] in request_targets:
            expected_target, label = request_targets[begin["request"]]
            if relevant_overlap:
                require(attribution_target == expected_target,
                        "physical-overlap ioctl request/FD target mismatched")
            elif attribution_target != expected_target:
                label = None
        all_pairs.append({
            "classification": classification, "tid": begin["pid"],
            "saved_tgid": begin["tgid"], "enter_line": begin["line"],
            "exit_line": item["line"], "start": begin["time"], "end": item["time"],
            "duration_seconds": item["time"] - begin["time"],
            "enter_region": begin_region, "exit_region": region,
            "raw_arguments": begin["arguments"], "registers": begin["registers"],
            "fd": fd, "request": begin["request"], "request_label": label,
            "return": int(exited.group(2)), "fd_targets": targets,
            "fd_target_stable_preroll_to_end": stable,
            "fd_target_stable_start_to_end": stable_from_start,
            "attribution_target": attribution_target,
            "overlaps_physical_window": relevant_overlap,
            "crosses_start": begin_region == "pre-roll" and region in {"capture-window", "drain"},
            "crosses_end": begin_region in {"pre-roll", "capture-window"} and region == "drain",
            "return_after_capture_end": region == "drain"})

    for pid, begin in pending.items():
        region = _region_for_line(begin["line"], marker_lines)
        require(region == "drain",
                "physical-overlap AVOC ioctl unresolved at drain end")
        unmatched.append({"kind": "drain-only-pending", "tid": pid,
                          "saved_tgid": begin["tgid"], "line": begin["line"],
                          "region": region, "raw_arguments": begin["arguments"]})

    avoc_forks, avoc_exits = [], []
    for item in events:
        if item["line"] > marker_lines["DRAIN_END"]:
            continue
        if item["event"] == "sched_process_fork":
            fork = re.fullmatch(r"comm=.* pid=(\d+) child_comm=.* child_pid=(\d+)",
                                item["body"])
            require(fork is not None, "malformed sched_process_fork event")
            if int(fork.group(1)) in tids:
                avoc_forks.append({"line": item["line"],
                                   "parent_tid": int(fork.group(1)),
                                   "child_tid": int(fork.group(2)),
                                   "time": item["time"],
                                   "region": _region_for_line(item["line"], marker_lines)})
        elif item["event"] == "sched_process_exit" and item["pid"] in tids:
            exited = re.fullmatch(r"comm=.* pid=(\d+) prio=(-?\d+)", item["body"])
            require(exited is not None and int(exited.group(1)) == item["pid"],
                    "malformed AVOC sched_process_exit event")
            avoc_exits.append({"line": item["line"], "tid": item["pid"],
                               "time": item["time"],
                               "region": _region_for_line(item["line"], marker_lines)})
    require(not avoc_forks and not avoc_exits,
            "AVOC thread lifecycle changed from trace enable through drain")

    region_counts = {name: 0 for name in
                     ("enable-slop", "trace-prelude", "pre-roll",
                      "capture-window", "drain", "post-drain")}
    for item in events:
        region = _region_for_line(item["line"], marker_lines)
        if region != "marker":
            region_counts[region] += 1
    require(sum(region_counts.values()) + len(markers) == len(events),
            "trace region accounting mismatch")
    window_events = [item for item in events
                     if _region_for_line(item["line"], marker_lines) == "capture-window"]
    i2c_names = ("i2c_write", "i2c_read", "i2c_reply", "i2c_result")
    i2c_by_event = {name: sum(item["event"] == name for item in window_events)
                    for name in i2c_names}
    groups = {name: [row for row in all_pairs if row["classification"] == name]
              for name in ("window_complete", "window_tail_completed",
                           "start_boundary_completed_in_window",
                           "start_boundary_completed_in_drain", "preroll_complete",
                           "drain_only", "outside_or_unbounded_context")}
    request_counts: dict[str, int] = {}
    for row in all_pairs:
        key = f"0x{row['request']:08x}@{row['attribution_target'] or 'unknown'}"
        request_counts[key] = request_counts.get(key, 0) + 1
    unmatched_counts: dict[str, int] = {}
    for row in unmatched:
        key = row["kind"] + "@" + row["region"]
        unmatched_counts[key] = unmatched_counts.get(key, 0) + 1
    window_pairs = groups["window_complete"] + groups["window_tail_completed"]
    boundary_pairs = (groups["start_boundary_completed_in_window"] +
                      groups["start_boundary_completed_in_drain"])
    relevant_pairs = boundary_pairs + window_pairs
    relevant_stable = all(row["fd_target_stable_preroll_to_end"]
                          for row in relevant_pairs)
    return {
        "retained": retained, "written": written, "ring_complete": True,
        "decoded_event_lines": len(events), "i2c_parse_errors": malformed,
        "trace_windows": {
            "trace_enable_bracket": evidence["trace_enable_bracket"],
            "trace_armed": by_kind["TRACE_ARMED"]["trace_time"],
            "preroll_start": by_kind["PREROLL_START"]["trace_time"],
            "capture_start": by_kind["START"]["trace_time"],
            "capture_end": by_kind["END"]["trace_time"],
            "drain_end": by_kind["DRAIN_END"]["trace_time"],
            "preroll_duration_seconds": preroll,
            "prelude_duration_seconds": prelude,
            "physical_window_unchanged": True},
        "markers": markers, "event_counts_by_region": region_counts,
        "capture_window_event_lines": region_counts["capture-window"],
        "capture_window_i2c_raw_lines": sum(i2c_by_event.values()),
        "capture_window_i2c_raw_lines_by_event": i2c_by_event,
        "drain_event_lines": region_counts["drain"],
        "ioctl_pairs": window_pairs,
        "window_originated_pairs": groups["window_complete"],
        "window_tail_completed_pairs": groups["window_tail_completed"],
        "start_boundary_pairs": boundary_pairs,
        "preroll_complete_pairs": groups["preroll_complete"],
        "drain_only_pairs": groups["drain_only"],
        "outside_pairs": groups["outside_or_unbounded_context"],
        "all_completed_syscall54_pairs": all_pairs,
        "ioctl_pairs_completed_during_drain": len(groups["window_tail_completed"]),
        "boundary_unmatched_syscall54_rows": unmatched,
        "unmatched_by_kind_and_region": unmatched_counts,
        "pending_at_drain_end": [row for row in unmatched
                                 if row["kind"] == "drain-only-pending"],
        "post_drain_syscall54_rows": post_drain_rows,
        "request_fd_counts": request_counts,
        "avoc_forks": avoc_forks, "avoc_exits": avoc_exits,
        "scope": {"filter_tids": list(tids), "tid_sets_equal": True,
                  "syscall_quiescence": evidence["syscall_quiescence"],
                  "relevant_fd_targets_stable": relevant_stable},
        "ring": {"retained": retained, "written": written,
                 "decoded": len(events), "dropped": written - retained,
                 "complete": True},
        "absence_claim_supported": False,
        "qualification": "Physical/annotation and event-inventory eligibility remains exactly CAPTURE_START..CAPTURE_END. Fully retained pre-roll boundary calls are reported separately; prelude/unresolved overlap, loss, lifecycle ambiguity, or unstable relevant FDs reject. Quiescence is a bounded read-only observation, not proof of generic event absence. I2C rows remain syntax-checked raw inventory, not complete transactions or physical effects."}


def root(command: str, timeout: int, audit_prefix: Path | None = None):
    return _ORIGINAL_ROOT(_namespace(command), timeout, audit_prefix)


@contextlib.contextmanager
def _patched_branch():
    names = {"root": root, "build_remote_script": build_remote_script,
             "parse_fds": parse_fds, "validate_trace_scope": validate_trace_scope,
             "trace_accounting": trace_accounting,
             "REMOTE_ROOT": REMOTE_ROOT, "STAGE_ROOT": STAGE_ROOT,
             "TRACE_PREFIX": TRACE_PREFIX}
    previous = {name: getattr(_base, name) for name in names}
    lower_names = {"parse_fds": parse_fds,
                   "validate_trace_scope": validate_trace_scope,
                   "trace_accounting": trace_accounting}
    lower_previous = {name: getattr(_base._base, name) for name in lower_names}
    for name, value in names.items():
        setattr(_base, name, value)
    for name, value in lower_names.items():
        setattr(_base._base, name, value)
    try:
        yield
    finally:
        for name, value in lower_previous.items():
            setattr(_base._base, name, value)
        for name, value in previous.items():
            setattr(_base, name, value)


def run_capture(label: str, seconds: int, smoke_unobserved: bool = False) -> None:
    with _patched_branch():
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
    largest = len(("set -eu\nprintf %s " + "A" * len(__import__("base64").b64encode(b"x" * 4096)) +
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
                "frozen_branch_observer_sha256": FROZEN_SHA256,
                "staged_script_bytes": len(raw), "staged_script_sha256": digest,
                "largest_staging_command_bytes": largest,
                "remote_root": REMOTE_ROOT, "stage_root": STAGE_ROOT,
                "trace_namespace": TRACE_PREFIX,
                "trace_markers": ["TRACE_ARMED", "PREROLL_START", "START", "END",
                                  "DRAIN_END"],
                "quiescence": {"read_only_proc_syscall": True,
                               "max_attempts_per_tid": QUIESCENCE_MAX_ATTEMPTS,
                               "running_is_qualified": False,
                               "prelude_max_seconds": PRELUDE_MAX_SECONDS},
                "physical_window": "CAPTURE_START..CAPTURE_END unchanged",
                "absence_claim_supported": False, "diagnostic_eligible": False,
                "execution_guard": "--run --reviewed",
            }, indent=2))
        return
    require(args.reviewed,
            "live execution requires both --run and --reviewed after parent review")
    require(not (BASE / (args.label + ".onset")).exists(),
            "existing local capture refused")
    run_capture(args.label, args.seconds, smoke_unobserved=args.smoke_unobserved)


if __name__ == "__main__":
    main()
