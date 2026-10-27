#!/usr/bin/env python3
"""Decode only retained owner-power-on sampler bytes, without target access.

This is deliberately weaker than observed-branch-onset-capture.analyze_samples:
the failed collection has start metadata but no authenticated end metadata, maps,
or dd accounting. It nevertheless applies the start-side row-shape, identity,
and documented pointer/field checks before emitting raw deltas.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RETAINED = HERE / "owner-power-on-20261026a-rescue" / "retained"
SAMPLES = RETAINED / "samples.txt"
META = RETAINED / "meta.txt"

# Exact tuple from observed-branch-onset-capture.py, QD_COUNTS.
QD_COUNTS = (1, 1, 7, 1, 1, 1, 3, 12, 1, 2, 1, 1, 1, 1, 2, 2, 2, 1, 1,
             6, 1, 4, 1, 1, 1, 1)
FIELDS = (
    ("ave_global", ("pointer",)), ("panel", ("pointer",)),
    ("qddimming_header", ("vptr", "inner", "header_08", "header_0c", "backend", "header_14", "initialized_word")),
    ("backend_vptr", ("pointer",)), ("backend_slot", ("pointer",)),
    ("ave_global_5ab958", ("word",)),
    ("inner_a4_a8_ac", ("inner_plus_a4", "inner_plus_a8_autodim_raw", "inner_plus_ac")),
    ("inner_458_484", tuple(f"inner_plus_{off:03x}" for off in range(0x458, 0x488, 4))),
    ("ave_global_5ad94c", ("word",)), ("ave_global_5bf6d0", ("word_0", "word_4")),
    ("inner_0", ("inner_plus_000",)), ("inner_38", ("inner_plus_038",)),
    ("inner_88", ("inner_plus_088",)), ("inner_98", ("inner_plus_098",)),
    ("inner_f8", ("inner_plus_0f8", "inner_plus_0fc")),
    ("inner_188", ("inner_plus_188", "inner_plus_18c")),
    ("inner_2a4_2a8", ("inner_plus_2a4", "inner_plus_2a8_autodim_raw")),
    ("inner_450", ("inner_plus_450",)), ("ave_global_5be420", ("word",)),
    ("deviced_chain", tuple(f"chain_word_{n}" for n in range(6))),
    ("power_index", ("power_state_index",)),
    ("ep_plus_30", tuple(f"word_{n}" for n in range(4))),
    ("op_plus_24", ("raw_word",)), ("ec_word", ("raw_word",)),
    ("et_word", ("raw_word",)), ("ea_word", ("raw_word",)),
)
assert tuple(len(names) for _field, names in FIELDS) == QD_COUNTS

# 38 words at AVE bias + 0x5bfc5c. Only labels proved in qd-monitor-runtime-map
# are semantic; the remainder are intentionally raw offsets.
MONITOR_NAMES = (
    "err_det_cnt", "vdd_det_cnt", "elvdd_i2c_error_cnt", "err_det_reboot_try",
    "vdd_det_reboot_try", "elvdd_i2c_reboot_try", "si_ok_count", "qd_tcon_off",
    "onetime_execution", "ip_status_count", "raw_plus_64", "fault_occurred",
    # These are offsets from the sampled 0x5bfc5c address (not state+0).
    *tuple(f"raw_sample_plus_{off:02x}" for off in range(0x30, 0x74, 4)),
    "pre_monitor_on", *tuple(f"raw_sample_plus_{off:02x}" for off in range(0x78, 0x8c, 4)),
    "g_tcon_monitor_restart", "g_tcon_monitor_on", "raw_sample_plus_94",
)
assert len(MONITOR_NAMES) == 38


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u32_words(encoded: str, count: int) -> list[int]:
    raw = base64.b64decode(encoded, validate=True)
    require(len(raw) == count * 4, f"expected {count} words, got {len(raw)} bytes")
    return list(struct.unpack("<" + "I" * count, raw))


def sections(text: str) -> dict[str, str]:
    out: dict[str, list[str]] = {}
    name: str | None = None
    for line in text.splitlines():
        if line.startswith("@@ "):
            name = line[3:]
            out[name] = []
        elif name is not None:
            out[name].append(line)
    return {key: "\n".join(value) for key, value in out.items()}


def parse_start_metadata() -> dict[str, object]:
    part = sections(META.read_text())
    avoc = part["AVOC_ID_START"].splitlines()
    deviced = part["DEV_ID_START"].splitlines()
    pointers = [int(value) for value in part["POINTERS_START"].split()]
    require(len(avoc) >= 3 and len(deviced) >= 3 and len(pointers) == 24,
            "incomplete retained start metadata")
    return {"avoc": (int(avoc[0]), int(avoc[2])),
            "deviced": (int(deviced[0]), int(deviced[2])),
            "pointers": pointers, "boot": part.get("BOOT_START", "")}


def event(field: str, subfield: str, old: int, new: int,
          first: float, second: float) -> dict[str, object]:
    return {"field": field, "subfield": subfield, "from": old, "to": new,
            "between_uptime": [first, second]}


def main() -> None:
    meta = parse_start_metadata()
    avoc_pid, avoc_start = meta["avoc"]  # type: ignore[misc]
    dev_pid, dev_start = meta["deviced"]  # type: ignore[misc]
    p = meta["pointers"]  # type: ignore[assignment]
    a, glob, panel, vptr, inner, backend, backend_vptr, backend_slot = p[:8]
    require(glob == a + 0x5BE2A4 and vptr == a + 0x59F2E8 and
            backend_vptr == a + 0x5A152C and backend_slot == a + 0x1C6275,
            "retained start metadata is not the exact base-QD/backend chain")
    # The expanded branch sampler stores D/DG, then legacy selector triplets,
    # then the EP/OP/EC/ET/EA/ECV/ETV/EAV tuple.  Only the latter tuple maps
    # to Q fields 19 and 21--25; do not reuse the legacy slots as EP/OP.
    d, _dglob = p[8:10]
    ep, op, ec, et, ea, ecv, etv, eav = p[16:24]
    monitor: list[tuple[float, list[int]]] = []
    qd: list[tuple[float, float, list[list[int]]]] = []
    for rawline in SAMPLES.read_text().splitlines():
        fields = rawline.split("|")
        require(fields[0] in {"M", "Q"}, "unknown sampler row kind")
        if fields[0] == "M":
            require(len(fields) == 3, "M row shape")
            uptime = float(fields[1]); require(math.isfinite(uptime), "M uptime")
            monitor.append((uptime, u32_words(fields[2], 38)))
            continue
        require(len(fields) == 3 + len(QD_COUNTS) + 1, "Q row shape")
        start, end = float(fields[1]), float(fields[-1])
        require(math.isfinite(start) and math.isfinite(end) and start <= end,
                "Q uptime span")
        identity = [int(value) for value in fields[2].split(",")]
        require(identity == [avoc_pid, avoc_start, a, dev_pid, dev_start, d],
                "Q process/load identity differs from start metadata")
        values = [u32_words(encoded, count) for encoded, count in zip(fields[3:-1], QD_COUNTS)]
        require(values[0] == [glob] and values[1] == [panel] and values[2][0] == vptr and
                values[2][1] == inner and values[2][4] == backend and
                (values[2][6] & 0xff) == 1 and values[3] == [backend_vptr] and
                values[4] == [backend_slot], "QD/backend identity differs from start metadata")
        dev = values[19]
        require(dev[0] == ep and dev[3] == op and (dev[2] & 0xff) == 0 and
                (dev[5] & 0xff) == 0, "deviced chain differs from start metadata")
        require(values[20][0] <= 6, "invalid power state index")
        require(values[21][1:] == [ec, et, ea] and
                [values[23][0], values[24][0], values[25][0]] == [ecv, etv, eav],
                "EL chain differs from start metadata")
        qd.append((start, end, values))
    require(monitor and qd, "no retained M or Q rows")

    q_events: list[dict[str, object]] = []
    changed: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for left, right in zip(qd, qd[1:]):
        for (field, subs), before, after in zip(FIELDS, left[2], right[2]):
            for sub, old, new in zip(subs, before, after):
                if old != new:
                    item = event(field, sub, old, new, left[0], right[0])
                    q_events.append(item); changed[(field, sub)].append(item)
    q_summary = []
    for (field, sub), events in sorted(changed.items()):
        values = {events[0]["from"], *(item["to"] for item in events)}
        q_summary.append({"field": field, "subfield": sub, "transitions": len(events),
                          "first_change_uptime": events[0]["between_uptime"],
                          "last_change_uptime": events[-1]["between_uptime"],
                          "distinct_values": sorted(values)})
    monitor_events = []
    for left, right in zip(monitor, monitor[1:]):
        for word, old, new in zip(MONITOR_NAMES, left[1], right[1]):
            if old != new:
                monitor_events.append({"word": word, "from": old, "to": new,
                                       "between_uptime": [left[0], right[0]]})
    result = {
        "qualification": ("offline start-metadata-only raw decode; every retained row passes "
                          "start-side shape/identity checks, but missing end metadata/maps/DD "
                          "accounting means this is not an accepted capture and is non-atomic"),
        "input": {"meta_sha256": sha256(META), "samples_sha256": sha256(SAMPLES),
                  "boot_start": meta["boot"], "avoc_identity": [avoc_pid, avoc_start],
                  "deviced_identity": [dev_pid, dev_start], "pointer_count_start": len(p)},
        "validation": {"start_side_invariants_passed": [
            "all Q rows match retained AVOC/deviced PID, start ticks, and AVE/deviced load-bias fields",
            "all Q rows preserve QDDimming/vptr/inner/backend/backend-vptr/backend-slot fields",
            "all Q rows have initialized_word low byte 1, preserve checked deviced/EL chain fields, and power_state_index in 0..6",
            "all 38 monitor words were compared across every retained M row"],
            "end_identity_maps_dd_available": False,
            "all_rows_checked": {"monitor": len(monitor), "qd": len(qd)}},
        "windows": {"monitor": [monitor[0][0], monitor[-1][0]],
                    "qd": [qd[0][0], qd[-1][1]],
                    "qd_row_spans": {"min": min(end-start for start, end, _ in qd),
                                     "max": max(end-start for start, end, _ in qd)}},
        "monitor": {"base": "AVOC libave load bias + 0x5bfc5c", "words": MONITOR_NAMES,
                    "initial_words": dict(zip(MONITOR_NAMES, monitor[0][1])),
                    "delta_count": len(monitor_events), "deltas": monitor_events},
        "q": {"field_counts": dict(zip((name for name, _ in FIELDS), QD_COUNTS)),
              "delta_count": len(q_events), "changed_fields": q_summary, "deltas": q_events},
    }
    destination = HERE / "owner-power-on-20261026a-qstate.json"
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"monitor_rows": len(monitor), "qd_rows": len(qd),
                      "monitor_delta_count": len(monitor_events), "q_delta_count": len(q_events),
                      "q_changed_subfields": len(q_summary), "output": str(destination)}, indent=2))


if __name__ == "__main__":
    main()
