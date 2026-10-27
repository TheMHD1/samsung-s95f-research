#!/usr/bin/env python3
"""Budgeted 180s/5s HDMI collector derivative; dry by default.

This host-only wrapper pins the reviewed long collector and changes only its
private namespace and explicit resource budgets: 128 MiB vlog, 8 MiB per-CPU
private trace rings, and 384 MiB preflight memory/tmpfs headroom.  It preserves
the 180-second observed and 5-second physically-unobserved modes.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
ANCESTOR = BASE / "observed-hdmi-long-onset-capture.py"
ANCESTOR_SHA256 = "65aeae50409ad05532163072e118140d09c7eaf3437aabc5b3843a138ab5c2eb"
WINDOW_SECONDS = 180
SMOKE_SECONDS = 5
VLOG_LIMIT = 128 * 1024 * 1024
RING_PER_CPU_KIB = 8192
RING_PER_CPU_BYTES = RING_PER_CPU_KIB * 1024
MEM_AVAILABLE_MIN_KIB = 384 * 1024
TMP_AVAILABLE_MIN_KIB = 384 * 1024
REMOTE_ROOT = "/tmp/researcher-observed-hdmi-budgeted-onset-20261027"
STAGE_ROOT = "/tmp/researcher-observed-hdmi-budgeted-onset-stage-20261027"
TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-hdmi-budgeted-onset-"


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


require(hashlib.sha256(ANCESTOR.read_bytes()).hexdigest() == ANCESTOR_SHA256,
        "pinned long HDMI ancestor changed")
_spec = importlib.util.spec_from_file_location("long_hdmi_65ae", ANCESTOR)
require(_spec is not None and _spec.loader is not None, "long HDMI ancestor unavailable")
_long = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_long)

MODEL, BUILD, ACCESS = _long.MODEL, _long.BUILD, _long.ACCESS
AVE_PATH, AVE_SHA = _long.AVE_PATH, _long.AVE_SHA
AVOC_PATH, AVOC_SHA = _long.AVOC_PATH, _long.AVOC_SHA
DEV_PATH, DEV_SHA = _long.DEV_PATH, _long.DEV_SHA
PM_EVENTS = _long.PM_EVENTS
_ORIGINAL_BUILD = _long.build_remote_script
_ORIGINAL_RUN = _long.run_capture
_ORIGINAL_NESTED = _long._nested_long_builder
_ORIGINAL_VALIDATE = _long.validate_metadata
_ORIGINAL_MANIFEST = _long.parse_manifest
_ORIGINAL_RING_VALIDATE = _long._validate_ring_capacity
_LIMIT_MODULES = _long._LIMIT_MODULES
ANCESTOR_REMOTE_ROOT = _long.REMOTE_ROOT
ANCESTOR_STAGE_ROOT = _long.STAGE_ROOT
ANCESTOR_TRACE_PREFIX = _long.TRACE_PREFIX


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, "budget shell anchor missing or ambiguous: " + label)
    return text.replace(old, new, 1)


def _namespace(shell: str) -> str:
    for old, new in ((ANCESTOR_REMOTE_ROOT, REMOTE_ROOT),
                     (ANCESTOR_STAGE_ROOT, STAGE_ROOT),
                     (ANCESTOR_TRACE_PREFIX, TRACE_PREFIX)):
        shell = shell.replace(old, new)
    return shell


def _transform_shell(shell: str) -> str:
    shell = _namespace(shell)
    replacements = (
        ('test "$dk" -ge 262144; test "$mk" -ge 262144',
         f'test "$dk" -ge {TMP_AVAILABLE_MIN_KIB}; '
         f'test "$mk" -ge {MEM_AVAILABLE_MIN_KIB}', "resource preflight"),
        ('echo 4096 >"$T/buffer_size_kb"',
         f'echo {RING_PER_CPU_KIB} >"$T/buffer_size_kb"', "ring allocation"),
        ('test "$bt" -le 16384', 'test "$bt" -le 32768', "ring total"),
        ('ulimit -f 65536; exec /usr/bin/vlogutil',
         'ulimit -f 131072; exec /usr/bin/vlogutil', "vlog writer"),
        ('vlog-after)L=67108864', 'vlog-after)L=134217728',
         "remote vlog manifest"),
    )
    for old, new, label in replacements:
        shell = _replace_once(shell, old, new, label)
    require(ANCESTOR_REMOTE_ROOT not in shell and ANCESTOR_STAGE_ROOT not in shell and
            ANCESTOR_TRACE_PREFIX not in shell, "ancestor namespace remains")
    return shell


def _register(shell: str, seconds: int, smoke_unobserved: bool) -> str:
    digest = hashlib.sha256(shell.encode()).hexdigest()
    contract = _long._extract_sampler_contract(shell)
    _long._ACTIVE_CONTRACTS[digest] = (contract, seconds, smoke_unobserved)
    return shell


def build_remote_script(label: str, seconds: int = WINDOW_SECONDS,
                        allow_short: bool = False) -> str:
    valid = ((seconds == WINDOW_SECONDS and not allow_short) or
             (seconds == SMOKE_SECONDS and allow_short))
    require(valid, "observed mode is 180 seconds; smoke-unobserved is 5 seconds")
    shell = _transform_shell(_ORIGINAL_BUILD(label, seconds, allow_short=allow_short))
    return _register(shell, seconds, allow_short)


def _nested_builder(label: str, seconds: int = WINDOW_SECONDS,
                    allow_short: bool = False) -> str:
    valid = ((seconds == WINDOW_SECONDS and not allow_short) or
             (seconds == SMOKE_SECONDS and allow_short))
    require(valid, "observed mode is 180 seconds; smoke-unobserved is 5 seconds")
    shell = _transform_shell(_ORIGINAL_NESTED(label, seconds, allow_short=allow_short))
    return _register(shell, seconds, allow_short)


def _trace_budget(text: str) -> tuple[str, dict]:
    sections = _long._pm.sections(text)
    config = sections["TRACE_CONFIG"]
    rows = config.splitlines()
    per_cpu = [row for row in rows if row.startswith("PER_CPU_KB=")]
    total_rows = [row for row in rows if row.startswith("TOTAL_KB=")]
    require(per_cpu == [f"PER_CPU_KB={RING_PER_CPU_KIB}"],
            "budgeted per-CPU trace readback mismatch")
    require(len(total_rows) == 1 and total_rows[0][9:].isdigit(),
            "budgeted total trace readback malformed")
    total = int(total_rows[0][9:])
    require(0 < total <= 32768, "budgeted total trace allocation too large")
    normalized = config.replace(f"PER_CPU_KB={RING_PER_CPU_KIB}",
                                "PER_CPU_KB=4096", 1)
    normalized = normalized.replace(total_rows[0],
                                    "TOTAL_KB=" + str(min(total, 16384)), 1)
    converted = _long._replace_section(text, "TRACE_CONFIG", config, normalized)
    return converted, {"per_cpu_kib": RING_PER_CPU_KIB,
                       "total_kib": total, "raw_readback_retained": True}


def _ring_validate(report: dict) -> None:
    stats = report.get("pm_extension", {}).get("cpu_stats", {})
    per_cpu = stats.get("per_cpu", {})
    require(bool(per_cpu) and stats.get("loss_free") is True,
            "private ring loss/capacity report absent")
    require(all(isinstance(row.get("bytes"), int) and
                0 <= row["bytes"] < RING_PER_CPU_BYTES
                for row in per_cpu.values()),
            "private per-CPU ring reached 8 MiB capacity")
    report["long_window_ring_capacity"] = {
        "per_cpu_limit_bytes": RING_PER_CPU_BYTES,
        "strictly_below_limit": True,
        "loss_free": True,
    }


def validate_metadata(text: str, script_size: int, script_sha256: str,
                      seconds: int) -> dict:
    converted, budget = _trace_budget(text)
    saved = _long._validate_ring_capacity
    _long._validate_ring_capacity = _ring_validate
    try:
        report = _ORIGINAL_VALIDATE(converted, script_size, script_sha256, seconds)
    finally:
        _long._validate_ring_capacity = saved
    stats = report["pm_extension"]["cpu_stats"]
    require(budget["total_kib"] == RING_PER_CPU_KIB * len(stats["per_cpu"]),
            "private total ring does not match online per-CPU allocation")
    budget.update({
        "per_cpu_limit_bytes": RING_PER_CPU_BYTES,
        "memory_preflight_min_kib": MEM_AVAILABLE_MIN_KIB,
        "tmp_available_preflight_min_kib": TMP_AVAILABLE_MIN_KIB,
        "vlog_limit_bytes": VLOG_LIMIT,
        "capacity_qualified_for_180_seconds": False,
    })
    report["budgeted_resources"] = budget
    return report


def parse_manifest(stdout: str):
    report = _ORIGINAL_MANIFEST(stdout)
    require(_long._terminal.SIDECAR_LIMITS.get("vlog-after") == VLOG_LIMIT,
            "128 MiB host vlog limit not installed")
    require(report["vlog-after"][0] < VLOG_LIMIT,
            "vlog sidecar reached 128 MiB capacity")
    return report


@contextlib.contextmanager
def _budget_context(runtime: bool = False):
    constants = ("REMOTE_ROOT", "STAGE_ROOT", "TRACE_PREFIX")
    saved_constants = {name: getattr(_long, name) for name in constants}
    saved_functions = (_long._nested_long_builder, _long.validate_metadata,
                       _long.parse_manifest, _long._validate_ring_capacity)
    saved_limits = [(module, module.SIDECAR_LIMITS) for module in _LIMIT_MODULES]
    for name, value in (("REMOTE_ROOT", REMOTE_ROOT), ("STAGE_ROOT", STAGE_ROOT),
                        ("TRACE_PREFIX", TRACE_PREFIX)):
        setattr(_long, name, value)
    for module in _LIMIT_MODULES:
        limits = dict(module.SIDECAR_LIMITS)
        limits["vlog-after"] = VLOG_LIMIT
        module.SIDECAR_LIMITS = limits
    if runtime:
        _long._nested_long_builder = _nested_builder
        _long.validate_metadata = validate_metadata
        _long.parse_manifest = parse_manifest
        _long._validate_ring_capacity = _ring_validate
    try:
        yield
    finally:
        (_long._nested_long_builder, _long.validate_metadata,
         _long.parse_manifest, _long._validate_ring_capacity) = saved_functions
        for module, limits in saved_limits:
            module.SIDECAR_LIMITS = limits
        for name, value in saved_constants.items():
            setattr(_long, name, value)


def run_capture(label: str, seconds: int = WINDOW_SECONDS,
                smoke_unobserved: bool = False) -> None:
    valid = ((seconds == WINDOW_SECONDS and not smoke_unobserved) or
             (seconds == SMOKE_SECONDS and smoke_unobserved))
    require(valid, "observed mode is 180 seconds; smoke-unobserved is 5 seconds")
    with _budget_context(runtime=True):
        _ORIGINAL_RUN(label, seconds, smoke_unobserved=smoke_unobserved)


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
        require(args.seconds == SMOKE_SECONDS, "smoke-unobserved requires --seconds 5")
    else:
        require(args.seconds == WINDOW_SECONDS,
                "observed HDMI window is fixed at 180 seconds")
    for name, digest in {"binaries/libave.so.0.1": AVE_SHA,
                         "binaries/avocd": AVOC_SHA,
                         "binaries/deviced": DEV_SHA}.items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
                "local matching binary changed: " + name)
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
                                 else "full-observed-hdmi-budgeted"),
                "seconds": args.seconds,
                "ancestor_sha256": ANCESTOR_SHA256,
                "collector_source_sha256": hashlib.sha256(
                    Path(__file__).read_bytes()).hexdigest(),
                "staged_script_bytes": len(raw),
                "staged_script_sha256": hashlib.sha256(raw).hexdigest(),
                "remote_root": REMOTE_ROOT, "stage_root": STAGE_ROOT,
                "trace_namespace": TRACE_PREFIX,
                "vlog_limit_bytes": VLOG_LIMIT,
                "ring_per_cpu_kib": RING_PER_CPU_KIB,
                "ring_total_kib_max": 32768,
                "memory_preflight_min_kib": MEM_AVAILABLE_MIN_KIB,
                "tmp_available_preflight_min_kib": TMP_AVAILABLE_MIN_KIB,
                "physical_state": ("unobserved" if args.smoke_unobserved
                                   else "requires ordered annotations"),
                "capacity_qualified_for_180_seconds": False,
                "global_trace_write": False,
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
