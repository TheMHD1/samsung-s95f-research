#!/usr/bin/env python3
"""Prepare one finite HDMI onset capture; dry by default.

This host-only derivative pins the reviewed 60-second HDMI collector and the
long-window design.  Its observed mode is fixed at 180 seconds; its only
short mode is a 5-second physically unobserved instrumentation smoke.  It
changes only the duration/private namespaces, the sample-error limit (writer
and validator together), and the narrowly defined one-row AVOC heap-growth
policy.  It never runs without both --run and --reviewed.
"""

from __future__ import annotations

import argparse
import contextlib
from typing import NamedTuple
import hashlib
import importlib.util
import json
import re
from pathlib import Path


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
HDMI_SOURCE = BASE / "observed-hdmi-onset-capture.py"
HDMI_SHA256 = "ab0a8d101bd1058ce4b25becb3ae5294cc29ac38a600ecf23c4dcf3658b886f3"
DESIGN = BASE / "hdmi-long-window-design-20261027.md"
DESIGN_SHA256 = "d39b7c07763b156d6f47f1591d9cfed8c8c4e788f68b2643c9835ab48a9cecf9"
WINDOW_SECONDS = 180
SMOKE_SECONDS = 5
SAMPLE_ERROR_LIMIT = 1024 * 1024
REMOTE_ROOT = "/tmp/researcher-observed-hdmi-long-onset-20261027"
STAGE_ROOT = "/tmp/researcher-observed-hdmi-long-onset-stage-20261027"
TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-hdmi-long-onset-"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


for _path, _digest in ((HDMI_SOURCE, HDMI_SHA256), (DESIGN, DESIGN_SHA256)):
    if hashlib.sha256(_path.read_bytes()).hexdigest() != _digest:
        raise RuntimeError("pinned long-window dependency changed: " + str(_path))
_spec = importlib.util.spec_from_file_location("frozen_hdmi_60_ab0a8d", HDMI_SOURCE)
if _spec is None or _spec.loader is None:
    raise RuntimeError("frozen HDMI collector unavailable")
_hdmi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_hdmi)

MODEL, BUILD, ACCESS = _hdmi.MODEL, _hdmi.BUILD, _hdmi.ACCESS
AVE_PATH, AVE_SHA = _hdmi.AVE_PATH, _hdmi.AVE_SHA
AVOC_PATH, AVOC_SHA = _hdmi.AVOC_PATH, _hdmi.AVOC_SHA
DEV_PATH, DEV_SHA = _hdmi.DEV_PATH, _hdmi.DEV_SHA
PM_EVENTS = _hdmi.PM_EVENTS

_short = _hdmi._short
_quiescent = _short._frozen
_pm = _short._pm
_preroll = _short._preroll
_branch = _short._branch
_terminal = _short._terminal
_ORIGINAL_PM_VALIDATE = _pm.validate_metadata
_ORIGINAL_PARSE_MANIFEST = _terminal.parse_manifest
_ORIGINAL_Q_BYTES = _branch.Q_SAMPLER_BYTES
_ORIGINAL_Q_SHA = _branch.Q_SAMPLER_SHA256
_ACTIVE_CONTRACTS: dict[
    str, tuple[tuple[tuple[str, int, str], ...], int, bool]
] = {}


class MapRow(NamedTuple):
    lo: int
    hi: int
    perms: str
    offset: int
    device: str
    inode: int
    path: str


def parse_full_maps(text: str) -> list[MapRow]:
    rows = []
    for line in text.splitlines():
        fields = line.split(None, 5)
        require(len(fields) >= 5, "malformed full maps line")
        bounds = fields[0].split("-")
        require(len(bounds) == 2 and
                re.fullmatch(r"[0-9a-f]+", bounds[0]) is not None and
                re.fullmatch(r"[0-9a-f]+", bounds[1]) is not None,
                "malformed full maps bounds")
        lo, hi = int(bounds[0], 16), int(bounds[1], 16)
        require(0 <= lo < hi <= 2**32, "invalid full maps range")
        require(re.fullmatch(r"[r-][w-][x-][ps]", fields[1]) is not None,
                "malformed full maps permissions")
        require(re.fullmatch(r"[0-9a-f]+", fields[2]) is not None and
                re.fullmatch(r"[0-9a-f]+:[0-9a-f]+", fields[3]) is not None and
                fields[4].isdigit(), "malformed full maps identity")
        rows.append(MapRow(lo, hi, fields[1], int(fields[2], 16), fields[3],
                           int(fields[4]), fields[5] if len(fields) == 6 else ""))
    require(bool(rows), "empty full maps")
    return rows


def _extract_sampler_contract(shell: str) -> tuple[tuple[str, int, str], ...]:
    lines = [line for line in shell.splitlines() if line.startswith("sampleok()")]
    require(len(lines) == 1, "generated sampler allowlist missing or ambiguous")
    marker = 'case "$k" in '
    tail = ') return 0;;'
    require(lines[0].count(marker) == lines[0].count(tail) == 1,
            "generated sampler case shape changed")
    alternatives = lines[0].split(marker, 1)[1].split(tail, 1)[0].split("|")
    tokens = []
    pattern = re.compile(r'^"([^"\n]+):(\d+):(\$am|\$dm):(\$ap|\$dp)"$')
    pointer_names = {
        "A", "G", "P", "V", "I", "B", "BV", "BS", "D", "DG",
        "EP", "OP", "EC", "ET", "EA", "ECV", "ETV", "EAV",
    }
    for alternative in alternatives:
        match = pattern.fullmatch(alternative)
        require(match is not None, "unknown generated sampler alternative")
        expression = match.group(1)
        direct = re.fullmatch(r"\$([A-Z]+)", expression)
        added = re.fullmatch(r"\$\(\(([A-Z]+)\+0x[0-9a-f]+\)\)", expression)
        name = direct.group(1) if direct is not None else (
            added.group(1) if added is not None else None)
        require(name in pointer_names, "unknown generated sampler alternative")
        tokens.append(match.groups())
    require(tokens and len(tokens) == len(set(tokens)),
            "empty/duplicate generated sampler allowlist")
    result = []
    for expression, count, maps_name, pid_name in tokens:
        require((maps_name, pid_name) in (("$am", "$ap"), ("$dm", "$dp")),
                "sampler process/map mismatch")
        count_i = int(count)
        require(0 < count_i <= 1024, "sampler word count outside contract")
        result.append((expression, count_i,
                       "avoc" if maps_name == "$am" else "deviced"))
    return tuple(result)


def _pointer_values(text: str) -> tuple[list[int], list[int]]:
    part = _pm.sections(text)
    start = [int(value) for value in part.get("POINTERS_START", "").split()]
    end = [int(value) for value in part.get("POINTERS_END", "").split()]
    require(len(start) == len(end) == 24, "long-window pointer field count")
    require(start == end, "long-window pointer/backend chain changed")
    return start, end


def _variables(values: list[int]) -> dict[str, int]:
    # Exact observed-branch pointer layout; intermediate deviced selectors are
    # retained but only the named final chain values are needed below.
    return {
        "A": values[0], "G": values[1], "P": values[2], "V": values[3],
        "I": values[4], "B": values[5], "BV": values[6], "BS": values[7],
        "D": values[8], "DG": values[9], "EP": values[16], "OP": values[17],
        "EC": values[18], "ET": values[19], "EA": values[20],
        "ECV": values[21], "ETV": values[22], "EAV": values[23],
    }


def _evaluate_expression(expression: str, variables: dict[str, int]) -> int:
    direct = re.fullmatch(r"\$([A-Z]+)", expression)
    if direct is not None:
        require(direct.group(1) in variables, "unknown sampler pointer variable")
        return variables[direct.group(1)]
    added = re.fullmatch(r"\$\(\(([A-Z]+)\+0x([0-9a-f]+)\)\)", expression)
    require(added is not None and added.group(1) in variables,
            "unknown generated sampler expression")
    return variables[added.group(1)] + int(added.group(2), 16)


def _cover(rows: list[MapRow], address: int, size: int, label: str) -> MapRow:
    require(address % 4 == 0 and 0 < address < 2**32 and
            0 < size <= 4096 and address + size <= 2**32,
            "invalid closure span: " + label)
    matches = [row for row in rows if row.perms.startswith("r") and
               row.lo <= address and address + size <= row.hi]
    require(len(matches) == 1, "missing/ambiguous closure map row: " + label)
    return matches[0]


def _same_except_heap_high(start: MapRow, end: MapRow) -> bool:
    return (start.path == end.path == "[heap]" and start.lo == end.lo and
            start.perms == end.perms and start.offset == end.offset and
            start.device == end.device and start.inode == end.inode and
            end.hi >= start.hi)


def validate_map_policy(text: str,
                        contract: tuple[tuple[str, int, str], ...]) -> dict:
    """Validate original raw maps before the frozen equality normalization."""
    part = _pm.sections(text)
    am0, am1 = (parse_full_maps(part[name]) for name in
                ("AVOC_MAPS_START", "AVOC_MAPS_END"))
    dm0, dm1 = (parse_full_maps(part[name]) for name in
                ("DEV_MAPS_START", "DEV_MAPS_END"))
    require(part["DEV_MAPS_START"] == part["DEV_MAPS_END"] and dm0 == dm1,
            "deviced maps changed")
    require(len(am0) == len(am1), "AVOC map row added or removed")
    differences = [index for index, pair in enumerate(zip(am0, am1))
                   if pair[0] != pair[1]]
    heap_pair = None
    if differences:
        require(len(differences) == 1, "AVOC maps have more than one changed row")
        index = differences[0]
        require(_same_except_heap_high(am0[index], am1[index]),
                "AVOC map change is not restricted monotonic heap growth")
        require(am1[index].hi > am0[index].hi,
                "changed AVOC heap row did not grow")
        heap_pair = (am0[index], am1[index])

    start, _end = _pointer_values(text)
    variables = _variables(start)
    spans = []
    for expression, count, process in contract:
        spans.append((process, _evaluate_expression(expression, variables),
                      count * 4, "sample:" + expression))
    # Map-dependent provenance that is not itself a sampled value.
    spans.extend((
        ("avoc", variables["A"], 4, "AVE load base"),
        ("avoc", variables["V"], 0x1c0, "QD vptr source"),
        ("avoc", variables["BV"], 0xdc, "backend vptr source"),
        ("avoc", variables["BS"] & ~1, 4, "backend slot target"),
        ("deviced", variables["D"], 4, "deviced load base"),
        ("deviced", variables["ECV"], 4, "deviced child vptr EC"),
        ("deviced", variables["ETV"], 4, "deviced child vptr ET"),
        ("deviced", variables["EAV"], 4, "deviced child vptr EA"),
    ))
    closure = []
    for process, address, size, label in spans:
        rows0, rows1 = (am0, am1) if process == "avoc" else (dm0, dm1)
        row0, row1 = _cover(rows0, address, size, label), _cover(rows1, address, size, label)
        if row0 != row1:
            require(process == "avoc" and heap_pair is not None and
                    row0 == heap_pair[0] and row1 == heap_pair[1] and
                    address >= row0.lo and address + size <= min(row0.hi, row1.hi),
                    "closure map row changed: " + label)
        closure.append({"process": process, "address": address, "bytes": size,
                        "source": label, "path": row0.path})
    return {
        "policy": "exact maps, or one monotonic AVOC [heap] high-end extension",
        "heap_growth": (None if heap_pair is None else {
            "low": heap_pair[0].lo, "start_high": heap_pair[0].hi,
            "end_high": heap_pair[1].hi}),
        "generated_sampler_spans": len(contract),
        "closure_spans": closure,
        "raw_maps_retained": True,
        "whole_heap_content_stable": False,
    }


def _replace_section(text: str, name: str, old: str, new: str) -> str:
    needle = "@@ " + name + "\n" + old
    require(text.count(needle) == 1, "metadata section replacement ambiguous: " + name)
    return text.replace(needle, "@@ " + name + "\n" + new, 1)


def validate_metadata(text: str, script_size: int, script_sha256: str,
                      seconds: int) -> dict:
    require(script_sha256 in _ACTIVE_CONTRACTS,
            "generated sampler contract unavailable for staged script")
    contract, registered_seconds, smoke_unobserved = _ACTIVE_CONTRACTS[script_sha256]
    require(seconds == registered_seconds and
            ((seconds == WINDOW_SECONDS and not smoke_unobserved) or
             (seconds == SMOKE_SECONDS and smoke_unobserved)),
            "long HDMI metadata duration/mode mismatch")
    policy = validate_map_policy(text, contract)
    part = _pm.sections(text)
    converted = text
    if part["AVOC_MAPS_START"] != part["AVOC_MAPS_END"]:
        converted = _replace_section(converted, "AVOC_MAPS_END",
                                     part["AVOC_MAPS_END"], part["AVOC_MAPS_START"])
    report = _ORIGINAL_PM_VALIDATE(converted, script_size, script_sha256, seconds)
    _validate_ring_capacity(report)
    report["long_window_map_policy"] = policy
    report["original_avoc_maps_start_sha256"] = hashlib.sha256(
        part["AVOC_MAPS_START"].encode()).hexdigest()
    report["original_avoc_maps_end_sha256"] = hashlib.sha256(
        part["AVOC_MAPS_END"].encode()).hexdigest()
    report["long_window_mode"] = {
        "seconds": seconds,
        "smoke_unobserved": smoke_unobserved,
        "physical_window_eligible": not smoke_unobserved,
    }
    return report


def _validate_ring_capacity(report: dict) -> None:
    stats = report.get("pm_extension", {}).get("cpu_stats", {})
    per_cpu = stats.get("per_cpu", {})
    require(bool(per_cpu) and stats.get("loss_free") is True,
            "private ring loss/capacity report absent")
    limit = 4096 * 1024
    require(all(isinstance(row.get("bytes"), int) and 0 <= row["bytes"] < limit
                for row in per_cpu.values()),
            "private per-CPU ring reached capacity")
    report["long_window_ring_capacity"] = {
        "per_cpu_limit_bytes": limit,
        "strictly_below_limit": True,
        "loss_free": True,
    }


def parse_manifest(stdout: str):
    report = _ORIGINAL_PARSE_MANIFEST(stdout)
    limits = dict(_terminal.SIDECAR_LIMITS)
    require(limits.get("sample-errors") == SAMPLE_ERROR_LIMIT,
            "long sample-error host limit not installed")
    for name, (size, _digest) in report.items():
        require(size < limits[name], "sidecar reached capacity limit: " + name)
    return report


def _long_q_sampler() -> bytes:
    old = b'ulimit -f 256; dd if=/proc/$4/mem bs=4 skip=$(($1/4)) count=$2 2>>"$QE"'
    new = b'ulimit -f 1024; dd if=/proc/$4/mem bs=4 skip=$(($1/4)) count=$2 2>>"$QE"'
    require(_ORIGINAL_Q_BYTES.count(old) == 1,
            "Q sampler error-writer anchor missing or ambiguous")
    return _ORIGINAL_Q_BYTES.replace(old, new, 1)


LONG_Q_SAMPLER_BYTES = _long_q_sampler()
LONG_Q_SAMPLER_SHA256 = hashlib.sha256(LONG_Q_SAMPLER_BYTES).hexdigest()


def _transform_shell(shell: str) -> str:
    replacements = (
        ('ulimit -f 256; dd if=/proc/$3/mem bs=4 skip=$(($1/4)) count=1 2>>"$E"',
         'ulimit -f 1024; dd if=/proc/$3/mem bs=4 skip=$(($1/4)) count=1 2>>"$E"'),
        ('ulimit -f 256; dd if=/proc/$4/mem bs=4 skip=$(($1/4)) count=$2 2>>"$er"',
         'ulimit -f 1024; dd if=/proc/$4/mem bs=4 skip=$(($1/4)) count=$2 2>>"$er"'),
        ('(ulimit -f 256; cat "$QE" >>"$E")',
         '(ulimit -f 1024; cat "$QE" >>"$E")'),
        ('(ulimit -f 256; cat "$QSE" >>"$E")',
         '(ulimit -f 1024; cat "$QSE" >>"$E")'),
        ('sample-errors)L=262144', 'sample-errors)L=1048576'),
        ('test "$1" -le "$L"; echo "SIDECAR',
         'test "$1" -lt "$L"; echo "SIDECAR'),
    )
    for old, new in replacements:
        require(shell.count(old) == 1, "long-window shell anchor missing: " + old)
        shell = shell.replace(old, new, 1)
    require('sample-errors)L=262144' not in shell, "old sample-error final cap remains")
    return shell


def _render_smoke_from_quiescent(label: str, seconds: int) -> str:
    """Bypass only the fixed 30/60-second wrappers, not their collectors."""
    require(seconds == SMOKE_SECONDS, "HDMI smoke is fixed at 5 seconds")
    with _short._permit_only_short_window():
        shell = _short._parent_build(label, seconds, allow_short=True)
    shell = _short._namespace(shell)
    return _hdmi._kernel_snapshot_shell(shell)


def _render_long(label: str, seconds: int, smoke_unobserved: bool) -> str:
    with _dependency_context():
        with _hdmi._adapt_short_boundary():
            if smoke_unobserved:
                shell = _render_smoke_from_quiescent(label, seconds)
            else:
                shell = _hdmi._render_from_short(label, seconds, allow_short=False)
    shell = _transform_shell(shell)
    require(REMOTE_ROOT in shell and STAGE_ROOT in shell and TRACE_PREFIX in shell,
            "long HDMI namespace absent from rendered collector")
    require(f"-v n={seconds}" in shell and "sleep 900" in shell,
            "long duration/expiry contract absent")
    contract = _extract_sampler_contract(shell)
    digest = hashlib.sha256(shell.encode()).hexdigest()
    _ACTIVE_CONTRACTS[digest] = (contract, seconds, smoke_unobserved)
    return shell


def build_remote_script(label: str, seconds: int = WINDOW_SECONDS,
                        allow_short: bool = False) -> str:
    valid = ((seconds == WINDOW_SECONDS and not allow_short) or
             (seconds == SMOKE_SECONDS and allow_short))
    require(valid, "observed mode is 180 seconds; smoke-unobserved is 5 seconds")
    return _render_long(label, seconds, allow_short)


def _nested_long_builder(label: str, seconds: int = WINDOW_SECONDS,
                         allow_short: bool = False) -> str:
    valid = ((seconds == WINDOW_SECONDS and not allow_short) or
             (seconds == SMOKE_SECONDS and allow_short))
    require(valid, "observed mode is 180 seconds; smoke-unobserved is 5 seconds")
    if allow_short:
        shell = _render_smoke_from_quiescent(label, seconds)
    else:
        shell = _hdmi._render_from_short(label, seconds, allow_short=False)
    shell = _transform_shell(shell)
    _ACTIVE_CONTRACTS[hashlib.sha256(shell.encode()).hexdigest()] = (
        _extract_sampler_contract(shell), seconds, allow_short)
    return shell


_LIMIT_MODULES = tuple(dict.fromkeys(
    module for module in (_quiescent, _pm, _preroll, _branch, _terminal)
    if hasattr(module, "SIDECAR_LIMITS")))


@contextlib.contextmanager
def _dependency_context(runtime: bool = False):
    """Install all deltas only for rendering/one run and restore exactly."""
    hdmi_names = ("WINDOW_SECONDS", "REMOTE_ROOT", "STAGE_ROOT", "TRACE_PREFIX")
    hdmi_saved = {name: getattr(_hdmi, name) for name in hdmi_names}
    nested_saved = _hdmi._nested_hdmi_builder
    pm_validate_saved = _pm.validate_metadata
    terminal_manifest_saved = _terminal.parse_manifest
    q_saved = (_branch.Q_SAMPLER_BYTES, _branch.Q_SAMPLER_SHA256)
    limit_saved = [(module, module.SIDECAR_LIMITS) for module in _LIMIT_MODULES]
    for name, value in (("WINDOW_SECONDS", WINDOW_SECONDS),
                        ("REMOTE_ROOT", REMOTE_ROOT), ("STAGE_ROOT", STAGE_ROOT),
                        ("TRACE_PREFIX", TRACE_PREFIX)):
        setattr(_hdmi, name, value)
    _branch.Q_SAMPLER_BYTES = LONG_Q_SAMPLER_BYTES
    _branch.Q_SAMPLER_SHA256 = LONG_Q_SAMPLER_SHA256
    for module in _LIMIT_MODULES:
        limits = dict(module.SIDECAR_LIMITS)
        limits["sample-errors"] = SAMPLE_ERROR_LIMIT
        module.SIDECAR_LIMITS = limits
    if runtime:
        _hdmi._nested_hdmi_builder = _nested_long_builder
        _pm.validate_metadata = validate_metadata
        _terminal.parse_manifest = parse_manifest
    try:
        yield
    finally:
        _terminal.parse_manifest = terminal_manifest_saved
        _pm.validate_metadata = pm_validate_saved
        _hdmi._nested_hdmi_builder = nested_saved
        _branch.Q_SAMPLER_BYTES, _branch.Q_SAMPLER_SHA256 = q_saved
        for module, limits in limit_saved:
            module.SIDECAR_LIMITS = limits
        for name, value in hdmi_saved.items():
            setattr(_hdmi, name, value)


def run_capture(label: str, seconds: int = WINDOW_SECONDS,
                smoke_unobserved: bool = False) -> None:
    valid = ((seconds == WINDOW_SECONDS and not smoke_unobserved) or
             (seconds == SMOKE_SECONDS and smoke_unobserved))
    require(valid, "observed mode is 180 seconds; smoke-unobserved is 5 seconds")
    with _dependency_context(runtime=True):
        with _hdmi._adapt_short_boundary(install_nested_builder=True):
            with _short._patched_frozen_context():
                _short._frozen.run_capture(
                    label, seconds, smoke_unobserved=smoke_unobserved)


def source_identities() -> dict[str, dict[str, str]]:
    modules = {
        "frozen_hdmi_60": _hdmi,
        "frozen_short_30": _short,
        "frozen_quiescent_pm": _quiescent,
        "frozen_pm": _pm,
        "frozen_preroll": _preroll,
        "frozen_branch": _branch,
        "frozen_terminal": _terminal,
    }
    result = {}
    for name, module in modules.items():
        path = Path(module.__file__).resolve()
        result[name] = {"path": str(path),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    result["long_window_design"] = {
        "path": str(DESIGN), "sha256": DESIGN_SHA256}
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("--seconds", type=int, default=WINDOW_SECONDS)
    parser.add_argument("--smoke-unobserved", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--emit-shell", action="store_true")
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,30}", args.label) is not None,
            "use a unique lowercase label")
    if args.smoke_unobserved:
        require(args.seconds == SMOKE_SECONDS,
                "smoke-unobserved requires --seconds 5")
    else:
        require(args.seconds == WINDOW_SECONDS,
                "observed HDMI window is fixed at 180 seconds")
    for name, digest in {"binaries/libave.so.0.1": AVE_SHA,
                         "binaries/avocd": AVOC_SHA,
                         "binaries/deviced": DEV_SHA}.items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
                "local matching binary hash changed: " + name)
    shell = build_remote_script(args.label, args.seconds,
                                allow_short=args.smoke_unobserved)
    raw = shell.encode()
    if not args.run:
        if args.emit_shell:
            print(shell, end="")
        else:
            print(json.dumps({
                "mode": "dry-run; no TV/network/root call",
                "capture_kind": ("smoke-unobserved" if args.smoke_unobserved
                                 else "full-observed-hdmi-long"),
                "seconds": args.seconds,
                "frozen_hdmi_ancestor_sha256": HDMI_SHA256,
                "long_window_design_sha256": DESIGN_SHA256,
                "source_identities": source_identities(),
                "collector_source_sha256": hashlib.sha256(
                    Path(__file__).read_bytes()).hexdigest(),
                "staged_script_bytes": len(raw),
                "staged_script_sha256": hashlib.sha256(raw).hexdigest(),
                "remote_root": REMOTE_ROOT, "stage_root": STAGE_ROOT,
                "trace_namespace": TRACE_PREFIX,
                "sample_error_limit_bytes": SAMPLE_ERROR_LIMIT,
                "map_policy": "exact, except one monotonic AVOC [heap] high endpoint",
                "physical_window": "CAPTURE_START..CAPTURE_END unchanged",
                "physical_annotation_required": not args.smoke_unobserved,
                "physical_state": ("unobserved" if args.smoke_unobserved
                                   else "requires ordered annotations"),
                "capacity_smoke_required_before_observed_use": True,
                "trace_clock": "private instance explicitly set/read back as mono",
                "required_review_markers": [
                    "independent exact-byte review before any execution",
                    "one accepted 5-second passive unobserved smoke before 180 seconds",
                    "strict sidecar/ring headroom and zero-loss evidence",
                ],
                "global_trace_write": False,
                "diagnostic_eligible": False,
                "execution_guard": "--run --reviewed",
            }, indent=2))
        return
    require(args.reviewed, "live execution requires both --run and --reviewed")
    require(not (BASE / (args.label + ".onset")).exists(),
            "existing local capture refused")
    run_capture(args.label, args.seconds,
                smoke_unobserved=args.smoke_unobserved)


if __name__ == "__main__":
    main()
