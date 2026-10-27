#!/usr/bin/env python3
"""Prepare one passive onset capture extended with seven PM-framework events.

Dry by default.  This hash-pinned wrapper preserves the accepted pre-roll
observer's physical START..END window and all of its guards.  It only enables
seven stock tracepoints in the owned private instance, preserves their exact
format/readback/loss evidence, and reports conservative positive PM activity.
It never treats framework silence as proof of absence or software as a
physical-state sensor.
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
FROZEN_SOURCE = BASE / "observed-preroll-onset-capture.py"
FROZEN_SHA256 = "355d98bc04ab26b962fb3e92dc0953dd2aa6ccc837456efd49fbdd5b4329e697"
FORMAT_SOURCE = BASE / "pm-tracepoint-formats-20261026" / "remote-stdout.txt"
FORMAT_SOURCE_SHA256 = "97581bdd24c81dbd69e3c5edd6fef81b071d31284d95bc0cd203b98c3db5ad4e"
IDLE_FORMAT_SOURCE = BASE / "pm-idle-tracepoint-format-20261026" / "remote-stdout.txt"
IDLE_FORMAT_SOURCE_SHA256 = "4b3d1d29cebcca4d119b44075c3839dfc97fb60965d19e70cbcc3985c4159bfa"
DESIGN = BASE / "pm-rpm-onset-extension-design.md"
DESIGN_SHA256 = "1a52bf7c35bd519ccf63ba252ac71de724bfa7365018b5f0e240dc24cd614dc2"
IDLE_ADDENDUM = BASE / "pm-rpm-idle-extension-addendum.md"
IDLE_ADDENDUM_SHA256 = "365b10d403ce3d18e4e5fb5268d81aa73f8dff37f4322a79851d0998c1ee96ff"
STATIC_REPORT = ROOT / "tcon-research" / "serdes-probe-resume-path.md"
STATIC_REPORT_SHA256 = "7601c32b11800cb3d53fb37cd7e01a096386de5b9db475f1402d883e5ea29552"
HDMI_MODULE = ROOT / "binaries" / "sdp_hdmi.ko"
HDMI_MODULE_SHA256 = "f7cffd19934ef459b0263ceddddf003306b399e01d0ddee48df3f64a86667994"
REMOTE_HDMI_MODULE = "/lib/modules/5.4.261/kernel/soc/sdp_hdmi.ko"
KERNEL_RELEASE = "5.4.261"

for _path, _digest in ((FROZEN_SOURCE, FROZEN_SHA256),
                       (FORMAT_SOURCE, FORMAT_SOURCE_SHA256),
                       (IDLE_FORMAT_SOURCE, IDLE_FORMAT_SOURCE_SHA256),
                       (DESIGN, DESIGN_SHA256),
                       (IDLE_ADDENDUM, IDLE_ADDENDUM_SHA256),
                       (STATIC_REPORT, STATIC_REPORT_SHA256),
                       (HDMI_MODULE, HDMI_MODULE_SHA256)):
    if hashlib.sha256(_path.read_bytes()).hexdigest() != _digest:
        raise RuntimeError("pinned PM observer dependency changed: " + str(_path))

_spec = importlib.util.spec_from_file_location("frozen_preroll_observer_355d98", FROZEN_SOURCE)
if _spec is None or _spec.loader is None:
    raise RuntimeError("frozen pre-roll observer dependency unavailable")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

MODEL, BUILD, ACCESS = _base.MODEL, _base.BUILD, _base.ACCESS
AVE_PATH, AVE_SHA = _base.AVE_PATH, _base.AVE_SHA
AVOC_PATH, AVOC_SHA = _base.AVOC_PATH, _base.AVOC_SHA
DEV_PATH, DEV_SHA = _base.DEV_PATH, _base.DEV_SHA
SIDECAR_LIMITS, SUFFIX = _base.SIDECAR_LIMITS, _base.SUFFIX
require, sections = _base.require, _base.sections

REMOTE_ROOT = "/tmp/researcher-observed-pm-onset-20261026"
STAGE_ROOT = "/tmp/researcher-observed-pm-onset-stage-20261026"
TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-pm-onset-"
PARENT_REMOTE_ROOT, PARENT_STAGE_ROOT, PARENT_TRACE_PREFIX = (
    _base.REMOTE_ROOT, _base.STAGE_ROOT, _base.TRACE_PREFIX)

BASE_PM_EVENTS = (
    "power/device_pm_callback_start",
    "power/device_pm_callback_end",
    "power/suspend_resume",
    "rpm/rpm_resume",
    "rpm/rpm_suspend",
    "rpm/rpm_return_int",
)
PM_EVENTS = BASE_PM_EVENTS[:-1] + ("rpm/rpm_idle", BASE_PM_EVENTS[-1])
PM_EVENT_TOKENS = {event.rsplit("/", 1)[1]: event for event in PM_EVENTS}
PM_ACTIONS = {"suspend", "resume", "freeze", "quiesce", "hibernate",
              "thaw", "restore", "recover"}
TOKEN = r"[A-Za-z0-9_.:@/+()=-]+"


def _extract_formats(raw: str, events: tuple[str, ...]) -> dict[str, str]:
    result = {}
    for event in events:
        begin = "@@ FORMAT " + event + "\n"
        end = "@@ END_FORMAT\n"
        require(raw.count(begin) == 1, "missing/duplicate captured PM format: " + event)
        tail = raw.split(begin, 1)[1]
        require(end in tail, "unterminated captured PM format: " + event)
        body = tail.split(end, 1)[0]
        require(event not in result and body, "empty captured PM format: " + event)
        result[event] = body
    return result


FORMAT_TEXTS = _extract_formats(FORMAT_SOURCE.read_text(), BASE_PM_EVENTS)
FORMAT_TEXTS.update(_extract_formats(IDLE_FORMAT_SOURCE.read_text(), ("rpm/rpm_idle",)))
FORMAT_TEXTS = {event: FORMAT_TEXTS[event] for event in PM_EVENTS}
FORMAT_HASHES = {event: hashlib.sha256(body.encode()).hexdigest()
                 for event, body in FORMAT_TEXTS.items()}

_ORIGINAL_BUILD = _base.build_remote_script
_ORIGINAL_ROOT = _base.root
_ORIGINAL_RUN = _base.run_capture
_ORIGINAL_VALIDATE_METADATA = _base.validate_metadata
_ORIGINAL_TRACE_ACCOUNTING = _base.trace_accounting
_ORIGINAL_ASSESS_ANNOTATIONS = _base.assess_annotations
_ACTIVE_PM_REPORT: dict | None = None


def _once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, "frozen pre-roll anchor mismatch: " + label)
    return text.replace(old, new, 1)


def _namespace(text: str) -> str:
    return (text.replace(PARENT_REMOTE_ROOT, REMOTE_ROOT)
            .replace(PARENT_STAGE_ROOT, STAGE_ROOT)
            .replace(PARENT_TRACE_PREFIX, TRACE_PREFIX))


def _remote_format_loop(section: str) -> str:
    lines = [f"echo @@ {section}"]
    for event in PM_EVENTS:
        lines.extend((f"echo 'FORMAT {event}'",
                      f"cat /sys/kernel/debug/tracing/events/{event}/format",
                      "echo END_FORMAT"))
    return "; ".join(lines)


def _remote_enable_loop(section: str) -> str:
    lines = [f"echo @@ {section}"]
    lines += [f"printf '{event}='; cat \"$T/events/{event}/enable\""
              for event in PM_EVENTS]
    return "; ".join(lines)


def build_remote_script(label: str, seconds: int, allow_short: bool = False) -> str:
    """Add PM tracepoints without moving any inherited marker or deadline."""
    shell = _namespace(_ORIGINAL_BUILD(label, seconds, allow_short=allow_short))
    checks = "; ".join(
        f"test \"$(sha256sum /sys/kernel/debug/tracing/events/{event}/format | awk '{{print $1}}')\" = {FORMAT_HASHES[event]}"
        for event in PM_EVENTS)
    anchor = 'mkdir "$T"; echo 0 >"$T/tracing_on";'
    source_start = (f"echo @@ PM_KERNEL; uname -r; echo @@ PM_SOURCE_ID_START; "
                    f"sha256sum {REMOTE_HDMI_MODULE}")
    shell = _once(shell, anchor,
                  f"{checks}; (ulimit -f 4096; {{ {source_start}; {_remote_format_loop('PM_FORMATS_START')}; }} >>\"$M\"); " + anchor,
                  "format preflight")

    anchor = 'echo 1 >"$T/events/raw_syscalls/sys_exit/enable"\n'
    enable = "; ".join(f"echo 1 >\"$T/events/{event}/enable\"" for event in PM_EVENTS)
    evidence = (f'(ulimit -f 4096; {{ {_remote_enable_loop("PM_CONFIG_START")}; '
                f'{_remote_format_loop("PM_FORMATS_CONFIG")}; }} >>"$M")')
    shell = _once(shell, anchor, anchor + enable + "; " + evidence + "\n",
                  "private PM enable/config")

    stop = 'echo 0 >"$T/tracing_on"; tr=0;'
    stats = ('(ulimit -f 4096; { ' + _remote_enable_loop("PM_CONFIG_END") +
             f'; echo @@ PM_SOURCE_ID_END; sha256sum {REMOTE_HDMI_MODULE}' +
             '; echo @@ PM_CPU_STATS; printf "ONLINE "; cat /sys/devices/system/cpu/online; '
             'for ps in "$T"/per_cpu/cpu*/stats; do test -f "$ps"; '
             'pc=${ps%/stats}; pc=${pc##*/cpu}; echo "CPU $pc"; cat "$ps"; done; } >>"$M"); ')
    shell = _once(shell, stop, 'echo 0 >"$T/tracing_on"; ' + stats + 'tr=0;',
                  "PM end readback/stats")
    require(all(f'events/{event}/enable' in shell for event in PM_EVENTS),
            "PM event enable missing")
    require("/sys/kernel/debug/tracing/events/" in shell and
            "/sys/kernel/debug/tracing/instances/researcher-pm-onset-" in shell,
            "PM source/private trace evidence missing")
    require(PARENT_REMOTE_ROOT not in shell and PARENT_STAGE_ROOT not in shell and
            PARENT_TRACE_PREFIX not in shell, "old namespace remains")
    return shell


def _remove_sections(text: str, names: set[str]) -> tuple[str, dict[str, str]]:
    found: dict[str, list[str]] = {}
    kept: list[str] = []
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("@@ "):
            current = line[3:]
            if current in names:
                require(current not in found, "duplicate PM metadata section")
        if current in names:
            found.setdefault(current, []).append(line)
        else:
            kept.append(line)
    require(set(found) == names, "missing/duplicate PM metadata sections")
    extracted = {}
    for name, rows in found.items():
        require(rows[0] == "@@ " + name, "invalid PM metadata section")
        extracted[name] = "\n".join(rows[1:])
    return "\n".join(kept) + "\n", extracted


def _parse_format_section(value: str) -> dict[str, str]:
    lines = value.splitlines(keepends=True)
    result: dict[str, str] = {}
    i = 0
    while i < len(lines):
        match = re.fullmatch(r"FORMAT (\S+)\n", lines[i])
        require(match is not None and match.group(1) in PM_EVENTS and
                match.group(1) not in result, "malformed PM format block")
        event = match.group(1)
        i += 1
        body = []
        while i < len(lines) and lines[i] != "END_FORMAT\n":
            body.append(lines[i]); i += 1
        require(i < len(lines) and body, "unterminated PM format block")
        result[event] = "".join(body)
        i += 1
    require(tuple(result) == PM_EVENTS and result == FORMAT_TEXTS,
            "live PM format differs from pinned contract")
    return result


def _parse_enables(value: str) -> dict[str, int]:
    result = {}
    for line in value.splitlines():
        event, sep, enabled = line.partition("=")
        require(sep and event in PM_EVENTS and event not in result and enabled == "1",
                "PM enable readback differs")
        result[event] = 1
    require(tuple(result) == PM_EVENTS, "PM enable readback incomplete")
    return result


def _cpu_set(value: str) -> set[int]:
    result: set[int] = set()
    for part in value.strip().split(","):
        if "-" in part:
            lo, hi = part.split("-", 1)
            require(lo.isdigit() and hi.isdigit() and int(lo) <= int(hi),
                    "malformed online CPU set")
            result.update(range(int(lo), int(hi) + 1))
        else:
            require(part.isdigit(), "malformed online CPU set")
            result.add(int(part))
    require(result, "empty online CPU set")
    return result


def _parse_cpu_stats(value: str) -> dict:
    lines = value.splitlines()
    require(lines and lines[0].startswith("ONLINE "), "missing online CPU set")
    online = _cpu_set(lines[0][7:])
    result: dict[int, dict[str, float | int]] = {}
    current = None
    for line in lines[1:]:
        if line.startswith("CPU "):
            number = line[4:]
            require(number.isdigit() and int(number) not in result,
                    "malformed/duplicate CPU stats")
            current = int(number); result[current] = {}
            continue
        require(current is not None and ":" in line, "malformed CPU stats row")
        key, raw = (part.strip() for part in line.split(":", 1))
        require(key not in result[current] and key in {
            "entries", "overrun", "commit overrun", "bytes", "oldest event ts",
            "now ts", "dropped events", "read events"}, "unexpected CPU stats field")
        number = float(raw) if key.endswith(" ts") else int(raw)
        require(math.isfinite(number) and number >= 0, "invalid CPU stats value")
        result[current][key] = number
    expected = {"entries", "overrun", "commit overrun", "bytes", "oldest event ts",
                "now ts", "dropped events", "read events"}
    require(set(result) == online and all(set(row) == expected for row in result.values()),
            "CPU stats coverage incomplete")
    require(all(row["overrun"] == row["commit overrun"] == row["dropped events"] == 0
                for row in result.values()), "PM trace CPU loss reported")
    return {"online_cpus": sorted(online), "per_cpu": {str(k): v for k, v in result.items()},
            "loss_free": True}


def validate_metadata(text: str, script_bytes: int, script_sha: str,
                      seconds: int) -> dict:
    names = {"PM_KERNEL", "PM_SOURCE_ID_START", "PM_FORMATS_START",
             "PM_CONFIG_START", "PM_FORMATS_CONFIG", "PM_CONFIG_END",
             "PM_SOURCE_ID_END", "PM_CPU_STATS"}
    stripped, extra = _remove_sections(text, names)
    meta = _ORIGINAL_VALIDATE_METADATA(stripped, script_bytes, script_sha, seconds)
    start_formats = _parse_format_section(extra["PM_FORMATS_START"] + "\n")
    config_formats = _parse_format_section(extra["PM_FORMATS_CONFIG"] + "\n")
    start_enables = _parse_enables(extra["PM_CONFIG_START"])
    end_enables = _parse_enables(extra["PM_CONFIG_END"])
    require(extra["PM_KERNEL"] == KERNEL_RELEASE, "kernel release differs from PM contract")
    expected_source = HDMI_MODULE_SHA256 + "  " + REMOTE_HDMI_MODULE
    require(extra["PM_SOURCE_ID_START"] == expected_source and
            extra["PM_SOURCE_ID_END"] == expected_source,
            "sdp_hdmi module source identity differs or changed")
    meta["pm_extension"] = {
        "format_contract_source_sha256": {
            "six_event_source": FORMAT_SOURCE_SHA256,
            "rpm_idle_source": IDLE_FORMAT_SOURCE_SHA256},
        "format_sha256": {event: hashlib.sha256(start_formats[event].encode()).hexdigest()
                           for event in PM_EVENTS},
        "seven_formats_exact": start_formats == config_formats == FORMAT_TEXTS,
        "kernel_release": KERNEL_RELEASE,
        "sdp_hdmi_module_sha256": HDMI_MODULE_SHA256,
        "private_enable_readback_start": start_enables,
        "private_enable_readback_end": end_enables,
        "cpu_stats": _parse_cpu_stats(extra["PM_CPU_STATS"]),
    }
    return meta


_EVENT_RE = re.compile(
    r"^\s*(?P<task>.+?)-(?P<pid>\d+)\s+\((?P<tgid>[^)]*)\)\s+\[(?P<cpu>\d+)\]\s+"
    r"(?P<context>\S+)\s+"
    r"(?P<time>\d+\.\d+): (?P<event>\w+): (?P<body>.*)$")


def _region(line: int, markers: dict[str, int]) -> str:
    return _base._region_for_line(line, markers)


def _pair_class(start_region: str, end_region: str) -> tuple[str, bool]:
    physical = {"pre-roll", "capture-window"}
    if (start_region in {"enable-slop", "trace-prelude"} and
            end_region in {"capture-window", "drain", "post-drain"}):
        raise ValueError("unbounded PM operation overlaps physical window")
    if start_region == "pre-roll" and end_region in {"capture-window", "drain"}:
        return ("start_boundary", True)
    if start_region == "capture-window" and end_region in {"capture-window", "drain"}:
        return (("window_complete" if end_region == "capture-window" else "window_tail"), True)
    if start_region in physical and end_region not in {"pre-roll", "capture-window", "drain"}:
        raise ValueError("PM operation crosses drain cutoff")
    return ("outside", False)


def _strict_int(raw: str) -> int:
    require(re.fullmatch(r"-?[0-9]+", raw) is not None, "malformed signed PM value")
    value = int(raw)
    require(-(1 << 31) <= value < (1 << 31), "PM signed integer outside captured ABI range")
    return value


def _base_row(item: dict) -> dict:
    return {key: item[key] for key in
            ("line", "time", "pid", "tgid", "raw_tgid", "cpu", "task", "context", "body")}


def _nearest(interval: tuple[float, float], rows: list[dict]) -> dict | None:
    if not rows:
        return None
    def distance(row):
        a, b = interval; c, d = row["start_time"], row["end_time"]
        return 0.0 if max(a, c) <= min(b, d) else min(abs(a - d), abs(c - b))
    row = min(rows, key=distance)
    return {"family": row["family"], "start_line": row["start_line"],
            "end_line": row["end_line"], "distance_seconds": distance(row)}


def _pm_accounting(data: bytes, base_report: dict) -> dict:
    text = data.decode("utf-8", errors="strict")
    markers = {row["kind"]: row["line"] for row in base_report["markers"]}
    rows, lifecycle = [], []
    for number, line in enumerate(text.splitlines(), 1):
        match = _EVENT_RE.match(line)
        if not match:
            continue
        raw_tgid = match["tgid"].strip()
        item = {"line": number, "time": float(match["time"]),
                "pid": int(match["pid"]),
                "tgid": int(raw_tgid) if raw_tgid.isdigit() else None,
                "raw_tgid": raw_tgid,
                "cpu": int(match["cpu"]), "task": match["task"],
                "context": match["context"],
                "event": match["event"], "body": match["body"],
                "raw_line": line, "region": _region(number, markers)}
        if match["event"] in PM_EVENT_TOKENS:
            rows.append(item)
        elif match["event"] == "sched_process_fork":
            parsed = re.fullmatch(r"comm=.* pid=(\d+) child_comm=.* child_pid=(\d+)",
                                  item["body"])
            require(parsed is not None, "malformed sched fork in PM lifecycle evidence")
            lifecycle.append({"kind": "fork", "line": number,
                              "parent_pid": int(parsed[1]),
                              "affected_pid": int(parsed[2]), "raw_body": item["body"]})
        elif match["event"] == "sched_process_exit":
            parsed = re.fullmatch(r"comm=.* pid=(\d+) prio=-?\d+", item["body"])
            require(parsed is not None, "malformed sched exit in PM lifecycle evidence")
            lifecycle.append({"kind": "exit", "line": number,
                              "affected_pid": int(parsed[1]), "raw_body": item["body"]})
        elif match["event"] == "sched_process_exec":
            parsed = re.fullmatch(r"filename=.* pid=(\d+) old_pid=(\d+)", item["body"])
            require(parsed is not None, "malformed sched exec in PM lifecycle evidence")
            lifecycle.append({"kind": "exec", "line": number,
                              "affected_pid": int(parsed[1]),
                              "old_pid": int(parsed[2]), "raw_body": item["body"]})
    require(all(b["time"] >= a["time"] for a, b in zip(rows, rows[1:])),
            "PM event timestamps out of order")

    counts: dict[str, dict[str, dict[str, int]]] = {}
    context_counts: dict[str, dict[str, dict[str, dict[str, int]]]] = {}
    for row in rows:
        event = PM_EVENT_TOKENS[row["event"]]
        counts.setdefault(event, {}).setdefault(row["region"], {}).setdefault(str(row["cpu"]), 0)
        counts[event][row["region"]][str(row["cpu"])] += 1
        contexts = context_counts.setdefault(event, {}).setdefault(row["region"], {}).setdefault(
            str(row["cpu"]), {})
        contexts[row["context"]] = contexts.get(row["context"], 0) + 1

    callback_stack: dict[int, list[dict]] = {}
    system_stack: dict[int, list[dict]] = {}
    runtime_stack: dict[int, list[dict]] = {}
    callbacks, systems, runtimes, unmatched, malformed = [], [], [], [], []
    callback_start = re.compile(
        rf"(?P<driver>{TOKEN}) (?P<device>{TOKEN}), parent: (?P<parent>{TOKEN}), "
        rf"(?P<ops>{TOKEN})\[(?P<action>[A-Za-z]+)\]")
    callback_end = re.compile(rf"(?P<driver>{TOKEN}) (?P<device>{TOKEN}), err=(?P<error>-?[0-9]+)")
    system_re = re.compile(rf"(?P<action>{TOKEN})\[(?P<val>[0-9]+)\] (?P<phase>begin|end)")
    runtime_re = re.compile(
        rf"(?P<name>{TOKEN})\s+flags-(?P<flags>[0-9a-f]+)\s+cnt-(?P<cnt>-?[0-9]+)\s+"
        rf"dep-(?P<dep>-?[0-9]+)\s+auto-(?P<auto>-?[0-9]+)\s+p-(?P<pending>-?[0-9]+)\s+"
        rf"irq-(?P<irq>-?[0-9]+)\s+child-(?P<child>-?[0-9]+)", re.I)
    return_re = re.compile(r"(?P<prefix>.+) ret=(?P<ret>-?[0-9]+)")

    def positive_identity(row: dict) -> tuple:
        require(row["pid"] > 0 and row["tgid"] is not None and row["tgid"] > 0,
                "PM row lacks exact positive task/saved-TGID identity")
        # Keep the mutable printed ftrace state token in the key as a
        # conservative disambiguator.  It is not authoritative context
        # identity, and a state change may reject a legitimate pair closed.
        return ("task", row["pid"], row["tgid"], row["task"], row["context"])

    def runtime_identity(row: dict) -> tuple:
        if row["pid"] != 0:
            return positive_identity(row)
        require(row["task"] == "<idle>" and row["raw_tgid"] == "-------" and
                row["tgid"] is None,
                "runtime-PM PID 0 row is not exact per-CPU idle identity")
        # PID 0 denotes a distinct idle thread on every CPU.  CPU and the
        # opaque printed state token are therefore both pairing disambiguators.
        return ("idle", row["cpu"], 0, "<idle>", "-------", row["context"])

    def finish(begin: dict, end: dict, family: str, fields: dict) -> dict:
        classification, overlaps = _pair_class(begin["region"], end["region"])
        crossed = [row for row in lifecycle
                   if begin["line"] < row["line"] < end["line"] and
                   row["affected_pid"] == begin["pid"]]
        require(begin["time"] <= end["time"] and begin["tgid"] == end["tgid"] and
                begin["raw_tgid"] == end["raw_tgid"] and
                begin["task"] == end["task"] and
                begin["context"] == end["context"] and
                (begin["pid"] != 0 or begin["cpu"] == end["cpu"]) and not crossed,
                "PM pair task identity/lifecycle changed")
        return {"family": family, "classification": classification,
                "overlaps_physical_window": overlaps,
                "start_line": begin["line"], "end_line": end["line"],
                "start_time": begin["time"], "end_time": end["time"],
                "duration_seconds": end["time"] - begin["time"],
                "start_cpu": begin["cpu"], "end_cpu": end["cpu"],
                "pid": begin["pid"], "tgid": begin["tgid"],
                "raw_saved_tgid": begin["raw_tgid"],
                "start_task": begin["task"], "end_task": end["task"],
                "start_context": begin["context"], "end_context": end["context"],
                "crossed_lifecycle_rows": crossed,
                "start_region": begin["region"], "end_region": end["region"],
                "raw_start_body": begin["body"], "raw_end_body": end["body"], **fields}

    for row in rows:
        try:
            if row["event"] == "device_pm_callback_start":
                identity = positive_identity(row)
                parsed = callback_start.fullmatch(row["body"])
                require(parsed is not None and parsed["action"] in PM_ACTIONS,
                        "malformed/unknown PM callback start")
                callback_stack.setdefault(identity, []).append({**row, **parsed.groupdict()})
            elif row["event"] == "device_pm_callback_end":
                identity = positive_identity(row)
                parsed = callback_end.fullmatch(row["body"])
                require(parsed is not None, "malformed PM callback end")
                stack = callback_stack.setdefault(identity, [])
                if not stack:
                    require(row["region"] not in {"capture-window", "drain", "post-drain"},
                            "orphan PM callback end in physical window/drain")
                    unmatched.append({"kind": "callback_orphan_end", **_base_row(row)})
                    continue
                begin = stack[-1]
                require(begin["driver"] == parsed["driver"] and begin["device"] == parsed["device"],
                        "PM callback end does not match stack top")
                stack.pop()
                callbacks.append(finish(begin, row, "device_callback", {
                    "driver": begin["driver"], "device": begin["device"],
                    "parent": begin["parent"], "pm_ops": begin["ops"],
                    "action": begin["action"], "error": _strict_int(parsed["error"])}))
            elif row["event"] == "suspend_resume":
                identity = positive_identity(row)
                parsed = system_re.fullmatch(row["body"])
                require(parsed is not None, "malformed suspend_resume event")
                val = int(parsed["val"])
                require(val < (1 << 32), "suspend_resume value outside unsigned ABI")
                key = (parsed["action"], val)
                stack = system_stack.setdefault(identity, [])
                if parsed["phase"] == "begin":
                    stack.append({**row, "key": key, "action": parsed["action"],
                                  "val": int(parsed["val"])})
                else:
                    if not stack:
                        require(row["region"] not in {"capture-window", "drain", "post-drain"},
                                "orphan system PM phase end in physical window/drain")
                        unmatched.append({"kind": "system_orphan_end", **_base_row(row)})
                        continue
                    require(stack[-1]["key"] == key, "mismatched system PM phase end")
                    begin = stack.pop()
                    systems.append(finish(begin, row, "system_phase", {
                        "action": begin["action"], "val": begin["val"]}))
            elif row["event"] in {"rpm_resume", "rpm_suspend", "rpm_idle"}:
                identity = runtime_identity(row)
                parsed = runtime_re.fullmatch(row["body"])
                require(parsed is not None, "malformed runtime-PM entry")
                values = {key: _strict_int(parsed[key]) for key in
                          ("cnt", "dep", "auto", "pending", "irq", "child")}
                flags = int(parsed["flags"], 16)
                require(flags < (1 << 32), "runtime-PM flags outside captured ABI")
                runtime_stack.setdefault(identity, []).append({
                    **row, "operation": row["event"].removeprefix("rpm_"),
                    "name": parsed["name"], "flags": flags, **values})
            else:
                identity = runtime_identity(row)
                parsed = return_re.fullmatch(row["body"])
                require(parsed is not None, "malformed runtime-PM return")
                stack = runtime_stack.setdefault(identity, [])
                if not stack:
                    unmatched.append({"kind": "unassigned_return_unknown_operation",
                                      "selected_entry_events": ["resume", "suspend", "idle"],
                                      "qualification": "No exact pending selected entry; no operation type is synthesized.",
                                      "return": _strict_int(parsed["ret"]), **_base_row(row)})
                    continue
                begin = stack[-1]
                if not parsed["prefix"].endswith(":" + begin["name"]):
                    unmatched.append({"kind": "unassigned_return_unknown_operation",
                                      "selected_entry_events": ["resume", "suspend", "idle"],
                                      "qualification": "Return name did not match the exact stack top; no operation type is synthesized.",
                                      "return": _strict_int(parsed["ret"]), **_base_row(row)})
                    continue
                stack.pop()
                runtimes.append(finish(begin, row, "runtime_pm", {
                    "operation": begin["operation"], "name": begin["name"],
                    "flags": begin["flags"], "state": {key: begin[key] for key in
                    ("cnt", "dep", "auto", "pending", "irq", "child")},
                    "ip_raw": parsed["prefix"][:-len(begin["name"]) - 1],
                    "return": _strict_int(parsed["ret"])}))
        except (ValueError, OverflowError):
            malformed.append({"line": row["line"], "event": row["event"], "body": row["body"]})
            raise

    for family, stacks in (("callback", callback_stack), ("system", system_stack),
                           ("runtime", runtime_stack)):
        for stack in stacks.values():
            for begin in stack:
                if begin["region"] in {"enable-slop", "trace-prelude", "pre-roll",
                                        "capture-window"}:
                    raise ValueError(f"pending {family} operation overlaps physical window at drain")
                unmatched.append({"kind": family + "_pending_outside", **_base_row(begin)})

    temporal = systems + runtimes
    positives = []
    for pair in callbacks:
        if pair["driver"] == "sdp-hdmi" and pair["action"] == "resume":
            item = dict(pair)
            interval = (pair["start_time"], pair["end_time"])
            item["nearest_runtime_pm"] = _nearest(interval, runtimes)
            item["nearest_system_phase"] = _nearest(interval, systems)
            item["overlapping_temporal_records"] = [
                {"family": row["family"], "start_line": row["start_line"],
                 "end_line": row["end_line"]}
                for row in temporal
                if max(interval[0], row["start_time"]) <= min(interval[1], row["end_time"])]
            item["physical_window_start_position"] = {
                "pre-roll": "before", "capture-window": "within",
                "drain": "after"}.get(pair["start_region"], "outside")
            item["owner_annotation_correlations"] = []
            item["qualification"] = (
                "A framework resume callback for the printed sdp-hdmi identity was retained; "
                "this does not establish SerDes polling, power cycling, panel state, or causation.")
            positives.append(item)
    task_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        event = PM_EVENT_TOKENS[row["event"]]
        key = f"{row['task']}:{row['pid']}/{row['raw_tgid']}"
        event_counts = task_counts.setdefault(event, {})
        event_counts[key] = event_counts.get(key, 0) + 1
    identity_counts: dict[str, int] = {}
    for pair in callbacks:
        key = f"callback:{pair['driver']}:{pair['device']}:{pair['action']}"
        identity_counts[key] = identity_counts.get(key, 0) + 2
    for pair in systems:
        key = f"system:{pair['action']}:{pair['val']}"
        identity_counts[key] = identity_counts.get(key, 0) + 2
    for pair in runtimes:
        key = f"runtime:{pair['operation']}:{pair['name']}"
        identity_counts[key] = identity_counts.get(key, 0) + 2
    byte_counts: dict[str, int] = {}
    for row in rows:
        event = PM_EVENT_TOKENS[row["event"]]
        byte_counts[event] = byte_counts.get(event, 0) + len((row["raw_line"] + "\n").encode())
    return {
        "format_contract": {"source_sha256": {
                                "six_event_source": FORMAT_SOURCE_SHA256,
                                "rpm_idle_source": IDLE_FORMAT_SOURCE_SHA256},
                            "seven_formats_exact": True,
                            "private_enable_readback": True},
        "source_contract": {
            "static_report_sha256": STATIC_REPORT_SHA256,
            "acquired_sdp_hdmi_module_sha256": HDMI_MODULE_SHA256,
            "runtime_loaded_module_binding_established": False,
            "qualification": "Endpoint hashes bind the installed module file, not the live callback object or execution of an internal callsite."},
        "execution_identity_contract": {
            "positive_tasks": "positive PID and numeric positive saved TGID; exact task and printed ftrace state token",
            "idle_runtime_only": "exact <idle>-0, raw saved TGID -------, CPU and printed ftrace state token",
            "context_token_interpretation": "mutable formatted state, not authoritative execution identity; exact equality is a fail-closed disambiguator and flag letters are not decoded"},
        "counts_by_event_region_cpu": counts,
        "counts_by_event_region_cpu_context": context_counts,
        "counts_by_task_pid_tgid": task_counts,
        "counts_by_normalized_paired_identity": identity_counts,
        "formatted_volume": {
            "rows": len(rows),
            "bytes": sum(byte_counts.values()),
            "bytes_by_event": byte_counts,
            "maximum_row_bytes": max((len((row["raw_line"] + "\n").encode())
                                      for row in rows), default=0)},
        "device_callback_pairs": callbacks, "system_phase_pairs": systems,
        "runtime_pm_pairs": runtimes, "unmatched": unmatched,
        "task_lifecycle_rows": lifecycle,
        "malformed_rows": malformed, "sdp_hdmi_positive_correlations": positives,
        "semantic_complete": True, "absence_claim_supported": False,
        "limits": ["framework tracepoints do not cover direct vendor paths",
                   "the proprietary Samsung sdp_runtime_pm callback path may bypass all seven selected tracepoints",
                   "positive timing is not causation",
                   "software does not label physical panel state"]}


def trace_accounting(data: bytes, tids: list[int], avoc_pid: int, collector_pid: int,
                     expected_start: float, expected_end: float,
                     expected_drain_end: float | None = None) -> dict:
    global _ACTIVE_PM_REPORT
    report = _ORIGINAL_TRACE_ACCOUNTING(data, tids, avoc_pid, collector_pid,
                                        expected_start, expected_end, expected_drain_end)
    pm = _pm_accounting(data, report)
    report["pm_extension"] = pm
    _ACTIVE_PM_REPORT = pm
    return report


def assess_annotations(rows: list[dict], sync: dict, meta: dict | None,
                       smoke_unobserved: bool) -> dict:
    report = _ORIGINAL_ASSESS_ANNOTATIONS(rows, sync, meta, smoke_unobserved)
    if _ACTIVE_PM_REPORT is not None:
        for pair in _ACTIVE_PM_REPORT["sdp_hdmi_positive_correlations"]:
            correlations = []
            for row in report["rows"]:
                lo, hi = row["tv_uptime_interval"]
                start, end = pair["start_time"], pair["end_time"]
                distance = 0.0 if max(lo, start) <= min(hi, end) else (
                    lo - end if lo > end else hi - start)
                correlations.append({"dimension": row["dimension"], "value": row["value"],
                                     "annotation_interval": [lo, hi],
                                     "signed_distance_seconds": distance,
                                     "overlaps": distance == 0.0})
            pair["owner_annotation_correlations"] = correlations
    return report


def root(command: str, timeout: int, audit_prefix: Path | None = None):
    return _ORIGINAL_ROOT(_namespace(command), timeout, audit_prefix)


@contextlib.contextmanager
def _patched_preroll():
    """Install wrappers at every nested module layer and restore exactly."""
    branch = _base._base
    lower = branch._base
    top_names = {"root": root, "build_remote_script": build_remote_script,
                 "validate_metadata": validate_metadata,
                 "trace_accounting": trace_accounting,
                 "assess_annotations": assess_annotations,
                 "REMOTE_ROOT": REMOTE_ROOT, "STAGE_ROOT": STAGE_ROOT,
                 "TRACE_PREFIX": TRACE_PREFIX}
    branch_names = {"validate_metadata": validate_metadata}
    lower_names = {"validate_metadata": validate_metadata,
                   "assess_annotations": assess_annotations}
    saved = [(mod, {name: getattr(mod, name) for name in names})
             for mod, names in ((_base, top_names), (branch, branch_names),
                                (lower, lower_names))]
    for mod, names in ((_base, top_names), (branch, branch_names), (lower, lower_names)):
        for name, value in names.items():
            setattr(mod, name, value)
    try:
        yield
    finally:
        for mod, values in reversed(saved):
            for name, value in values.items():
                setattr(mod, name, value)


def run_capture(label: str, seconds: int, smoke_unobserved: bool = False) -> None:
    global _ACTIVE_PM_REPORT
    _ACTIVE_PM_REPORT = None
    try:
        with _patched_preroll():
            _ORIGINAL_RUN(label, seconds, smoke_unobserved=smoke_unobserved)
    finally:
        _ACTIVE_PM_REPORT = None


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
                "capture_kind": "smoke-unobserved" if args.smoke_unobserved else "full-observed",
                "frozen_preroll_observer_sha256": FROZEN_SHA256,
                "pm_format_source_sha256": FORMAT_SOURCE_SHA256,
                "pm_idle_format_source_sha256": IDLE_FORMAT_SOURCE_SHA256,
                "pm_design_sha256": DESIGN_SHA256,
                "pm_idle_addendum_sha256": IDLE_ADDENDUM_SHA256,
                "sdp_hdmi_module_sha256": HDMI_MODULE_SHA256,
                "staged_script_bytes": len(raw), "staged_script_sha256": digest,
                "largest_staging_command_bytes": largest,
                "remote_root": REMOTE_ROOT, "stage_root": STAGE_ROOT,
                "trace_namespace": TRACE_PREFIX, "pm_events": PM_EVENTS,
                "physical_window": "CAPTURE_START..CAPTURE_END unchanged",
                "absence_claim_supported": False, "diagnostic_eligible": False,
                "capacity_status": "requires reviewed passive smoke and separate 90s budget",
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
