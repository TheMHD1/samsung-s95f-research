#!/usr/bin/env python3
"""Guarded one-shot AVOC PQE branch-state baseline; dry by default.

Live mode performs one bounded persistent-root command containing only source
identity, maps, and /proc/<pid>/mem reads.  It calls no device, getter, setter,
ioctl, service, key, or TV API.  Values are sequential/non-atomic and always
physical-unobserved; they do not establish a current branch or physical state.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ACCESS = BASE.parent / "root-access/s95f-access.py"
AVOC_LOCAL = BASE / "binaries/avocd"
AVE_LOCAL = BASE / "binaries/libave.so.0.1"
AVOC_PATH = "/usr/bin/avocd"
AVE_PATH = "/prd/usr/lib/libave.so.0.1"
AVOC_SHA256 = "ab450eaf99c793f3c7a9360629b1a1677e9d86dcd74a1f93796b56ba07401de9"
AVE_SHA256 = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"
MODEL = "QN77S95FAFXZC"
MAX_COMMAND_BYTES = 8192
MAP_AWK = ('BEGIN{ok=0} {split($1,a,"-"); '
           'if(length(a[1])==8 && length(a[2])==8 && substr($2,1,1)=="r" '
           '&& q>="x" a[1] && e<="x" a[2]) ok=1} END{exit(ok?0:1)}')

VE_TYPES = {
    "RoseMVideoEnhancer": (0x5B21A0, 0x59CBF8),
    "RoseMVideoEnhancerMNT": (0x5BD6F4, 0x59D51C),
    "RoseMVideoEnhancerEP": (0x5BDEAC, 0x59E030),
}
QD_TYPES = {"QDDimming": 0x59F2E8, "QDDimmingMNT": 0x5A094C}
BACKEND_TYPES = {
    ("QDDimming", 0x5A152C): ("DimmingBackendRoseMQD", 0x1C6275, 0x5AB958),
    ("QDDimmingMNT", 0x5A1784): ("DimmingBackendRoseMQDMNT", 0x1C9E75, 0x5ACB94),
}

COMMON_LAYOUT = {
    "ve_dlsr_class": ("dlsr_state", 0xB0, 1),
    "ve_hdr_brightness": ("ve_state", 0xEC, 1),
    "ve_config_1858_1868": ("ve_state", 0x1858, 5),
    "ve_gsr_enable": ("ve_state", 0x4531C, 1),
    "ve_ai_genre": ("ve_state", 0x45404, 1),
    "ve_gsr": ("ve_state", 0x4D858, 1),
    "ve_color_booster": ("ve_state", 0x4D9D0, 1),
    "qd_outer_header": ("qd_object", 0, 7),
    "qd_working_duty": ("qd_inner", 0xA8, 2),
    "qd_weber_policy": ("qd_inner", 0x458, 12),
    "weber_gain": ("ave_bias", 0x5AD94C, 1),
    "weber_target_count": ("ave_bias", 0x5BF6D0, 2),
}

# These offsets are source-backed only for the exact base QDDimming class.
BASE_QD_LAYOUT = {
    "qd_branch_inner_0000": ("qd_inner", 0x000, 1),
    "qd_branch_condition_0038": ("qd_inner", 0x038, 1),
    "qd_branch_weight_0088": ("qd_inner", 0x088, 1),
    "qd_branch_weight_0098": ("qd_inner", 0x098, 1),
    "qd_branch_floor_00a4": ("qd_inner", 0x0A4, 1),
    "qd_branch_sources_00f8_00fc": ("qd_inner", 0x0F8, 2),
    "qd_branch_model_0188_control_018c": ("qd_inner", 0x188, 2),
    "qd_branch_gain_autodim_02a4_02a8": ("qd_inner", 0x2A4, 2),
    "qd_branch_product_0450": ("qd_inner", 0x450, 1),
    "qd_auto_power_off_count": ("ave_bias", 0x5BE420, 1),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def static_contract() -> dict:
    avoc_hash = hashlib.sha256(AVOC_LOCAL.read_bytes()).hexdigest()
    ave_hash = hashlib.sha256(AVE_LOCAL.read_bytes()).hexdigest()
    require(avoc_hash == AVOC_SHA256, "Offline avocd hash mismatch")
    require(ave_hash == AVE_SHA256, "Offline libave hash mismatch")
    return {
        "avoc_sha256": avoc_hash,
        "ave_sha256": ave_hash,
        "ve_cached_pointer_vma": "0x005adb5c",
        "ve_types": {name: {"singleton_vma": hex(obj), "vptr_vma": hex(vptr)}
                     for name, (obj, vptr) in VE_TYPES.items()},
        "qd_types": {name: hex(vptr) for name, vptr in QD_TYPES.items()},
        "base_qd_branch_class": "QDDimming",
        "base_qd_branch_vptr_vma": hex(QD_TYPES["QDDimming"]),
        "base_qd_branch_layout": {
            name: {"base": base, "offset": hex(offset), "words": words}
            for name, (base, offset, words) in BASE_QD_LAYOUT.items()
        },
        "source_provenance": {
            "final_duty_symbol": "QDDimming::m_SetFinalDuty2D()",
            "final_duty_thumb_symbol_vma": "0x00174261",
            "auto_power_off_symbol": "QDDimming::m_AutoPowerOff()",
            "auto_power_off_thumb_symbol_vma": "0x001740f1",
            "auto_power_off_static_symbol":
                "QDDimming::m_AutoPowerOff()::siAutoDimCount",
            "auto_power_off_static_vma": "0x005be420",
            "eligibility": "exact QDDimming vptr only; never QDDimmingMNT",
        },
        "condition_0038_interpretation": "low byte of aligned u32 read at inner+0x38",
        "physical_state": "unobserved",
        "atomic": False,
    }


def build_command() -> str:
    command = f'''set -euo pipefail
P=$(pidof avocd); case "$P" in ''|*[!0-9]*) exit 31;; esac
test "$(readlink /proc/$P/exe)" = {AVOC_PATH}
test "$(sha256sum {AVOC_PATH}|cut -d' ' -f1)" = {AVOC_SHA256}
test "$(sha256sum {AVE_PATH}|cut -d' ' -f1)" = {AVE_SHA256}
mapok() {{ q=$1; z=$2; test "$q" -gt 0 || return 1; test "$z" -gt 0 || return 1; test $((q%4)) = 0 || return 1; test $((z%4)) = 0 || return 1; test $((q+z)) -lt 4294967296 || return 1; qh=$(printf '%08x' "$q") || return 1; eh=$(printf '%08x' $((q+z))) || return 1; LC_ALL=C awk -v q="x$qh" -v e="x$eh" '{MAP_AWK}' /proc/$P/maps; }}
u32() {{ mapok "$1" 4 || return 1; v=$(dd if=/proc/$P/mem bs=4 skip=$(($1/4)) count=1|od -An -tu4|tr -d ' \n'); case "$v" in ''|*[!0-9]*) return 1;; esac; printf %s "$v"; }}
emit() {{ echo "@@ READ_$1"; mapok "$2" $(($3*4)) || return 1; dd if=/proc/$P/mem bs=4 skip=$(($2/4)) count=$3|base64|tr -d '\n'; echo; }}
starttime() {{ s=$(cat /proc/$P/stat); case "$s" in *') '*) ;; *) return 1;; esac; s=${{s##*) }}; set -- $s; test "$#" -ge 20 || return 1; case "${{20}}" in ''|*[!0-9]*) return 1;; esac; echo "${{20}}"; }}
hx=$(awk '$2 ~ /^r.x/ && $3=="00000000" && $6=="{AVE_PATH}" {{split($1,a,"-"); print a[1]}}' /proc/$P/maps); test "$(printf %s "$hx"|wc -w)" = 1; A=$((0x$hx))
ptrs() {{
 VE=$(u32 $((A+0x5adb5c))) || return 1; VV=$(u32 "$VE") || return 1; VS=$(u32 $((VE+12))) || return 1
 case "$VE:$VV" in $((A+0x5b21a0)):$((A+0x59cbf8))|$((A+0x5bd6f4)):$((A+0x59d51c))|$((A+0x5bdeac)):$((A+0x59e030)));; *) return 1;; esac
 mapok "$VV" 1324 || return 1; mapok "$VS" 317908 || return 1
 DG=$(u32 $((A+0x5a6a28))) || return 1; test "$DG" = $((A+0x5b24e0)) || return 1; DS=$(u32 "$DG") || return 1; mapok "$DS" 180 || return 1
 G=$(u32 $((A+0x5a69ec))) || return 1; test "$G" = $((A+0x5be2a4)) || return 1; Q=$(u32 "$G") || return 1; QV=$(u32 "$Q") || return 1; I=$(u32 $((Q+4))) || return 1
 case "$QV" in $((A+0x59f2e8))|$((A+0x5a094c)));; *) return 1;; esac; mapok "$QV" 448 || return 1; mapok "$Q" 28 || return 1; mapok "$I" 1160 || return 1
 B=$(u32 $((Q+16))) || return 1; BV=0; BS=0; BN=0; BT=0
 if test "$B" -gt 0 2>/dev/null && test $((B%4)) = 0 && mapok "$B" 4; then BV=$(u32 "$B"); BN=1; fi
 if test "$QV:$BV" = "$((A+0x59f2e8)):$((A+0x5a152c))" && mapok $((BV+0xd8)) 4; then BS=$(u32 $((BV+0xd8))); BN=2; test "$BS" = $((A+0x1c6275)) && BT=1 || true; fi
 if test "$QV:$BV" = "$((A+0x5a094c)):$((A+0x5a1784))" && mapok $((BV+0xd8)) 4; then BS=$(u32 $((BV+0xd8))); BN=2; test "$BS" = $((A+0x1c9e75)) && BT=2 || true; fi
 echo "$A $VE $VV $VS $DG $DS $G $Q $QV $I $B $BV $BS $BN $BT"
}}
echo '@@ UTC_START'; date -u +%s
echo '@@ UPTIME_START'; cat /proc/uptime
echo '@@ ID_START'; cat /proc/sys/kernel/random/boot_id; echo "$P"; readlink /proc/$P/exe; starttime; sha256sum {AVOC_PATH} {AVE_PATH}
echo '@@ MAPS_START'; cat /proc/$P/maps
echo '@@ POINTERS_START'; PS=$(ptrs); echo "$PS"; set -- $PS; A=$1; VE=$2; VV=$3; VS=$4; DG=$5; DS=$6; G=$7; Q=$8; QV=$9; I=${{10}}; B=${{11}}; BV=${{12}}; BS=${{13}}; BN=${{14}}; BT=${{15}}
emit ve_dlsr_class $((DS+0xb0)) 1
emit ve_hdr_brightness $((VS+0xec)) 1
emit ve_config_1858_1868 $((VS+0x1858)) 5
emit ve_gsr_enable $((VS+0x4531c)) 1
emit ve_ai_genre $((VS+0x45404)) 1
emit ve_gsr $((VS+0x4d858)) 1
emit ve_color_booster $((VS+0x4d9d0)) 1
emit qd_outer_header "$Q" 7
emit qd_working_duty $((I+0xa8)) 2
emit qd_weber_policy $((I+0x458)) 12
emit weber_gain $((A+0x5ad94c)) 1
emit weber_target_count $((A+0x5bf6d0)) 2
if test "$QV" = $((A+0x59f2e8)); then
 emit qd_branch_inner_0000 "$I" 1
 emit qd_branch_condition_0038 $((I+0x38)) 1
 emit qd_branch_weight_0088 $((I+0x88)) 1
 emit qd_branch_weight_0098 $((I+0x98)) 1
 emit qd_branch_floor_00a4 $((I+0xa4)) 1
 emit qd_branch_sources_00f8_00fc $((I+0xf8)) 2
 emit qd_branch_model_0188_control_018c $((I+0x188)) 2
 emit qd_branch_gain_autodim_02a4_02a8 $((I+0x2a4)) 2
 emit qd_branch_product_0450 $((I+0x450)) 1
 emit qd_auto_power_off_count $((A+0x5be420)) 1
fi
if test "$BT" = 1; then emit backend_cache $((A+0x5ab958)) 1; fi
if test "$BT" = 2; then emit backend_cache $((A+0x5acb94)) 1; fi
echo '@@ POINTERS_END'; PE=$(ptrs); echo "$PE"; test "$PS" = "$PE"
echo '@@ MAPS_END'; cat /proc/$P/maps
echo '@@ ID_END'; cat /proc/sys/kernel/random/boot_id; echo "$P"; readlink /proc/$P/exe; starttime; sha256sum {AVOC_PATH} {AVE_PATH}
echo '@@ UPTIME_END'; cat /proc/uptime
echo '@@ UTC_END'; date -u +%s
'''
    require(len(command.encode()) <= MAX_COMMAND_BYTES, "Remote command exceeds 8192 bytes")
    return command


def blocks(text: str) -> dict[str, str]:
    result: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("@@ "):
            current = line[3:]
            require(current and current not in result, "Duplicate output section")
            result[current] = []
        else:
            require(current is not None, "Unframed remote output")
            result[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in result.items()}


def parse_maps(text: str) -> list[tuple[int, int, str, int, str]]:
    result = []
    for line in text.splitlines():
        fields = line.split(None, 5)
        require(len(fields) >= 5 and "-" in fields[0], "Malformed process map")
        lo, hi = (int(value, 16) for value in fields[0].split("-", 1))
        require(0 <= lo < hi <= 2**32, "Invalid process map range")
        result.append((lo, hi, fields[1], int(fields[2], 16), fields[5] if len(fields) == 6 else ""))
    require(bool(result), "Empty process maps")
    return result


def check_range(mapping, address: int, words: int) -> None:
    require(isinstance(address, int) and 0 < address < 2**32 and address % 4 == 0,
            "Invalid or unaligned read address")
    require(isinstance(words, int) and 1 <= words <= 12, "Invalid read word count")
    require(any(lo <= address and address + words * 4 <= hi and "r" in perms
                for lo, hi, perms, _, _ in mapping), "Unreadable read range")


def check_source_range(mapping, address: int, size: int, *, executable: bool = False) -> None:
    require(address > 0 and address % 4 == 0 and size > 0, "Invalid source range")
    require(any(lo <= address and address + size <= hi and "r" in perms
                and (not executable or "x" in perms) and path == AVE_PATH
                for lo, hi, perms, _, path in mapping), "Expected libave-backed source range")


def decode_words(text: str, count: int) -> list[int]:
    try:
        raw = base64.b64decode("".join(text.split()), validate=True)
    except Exception as exc:
        raise ValueError("Malformed base64 memory read") from exc
    require(len(raw) == count * 4, "Truncated memory read")
    return [int.from_bytes(raw[index:index + 4], "little") for index in range(0, len(raw), 4)]


def parse_identity(text: str) -> dict:
    lines = text.splitlines()
    require(len(lines) == 6, "Malformed identity block")
    boot, pid, exe, start, avoc_hash, ave_hash = lines
    require(re.fullmatch(r"[0-9a-f]{8}-[0-9a-f-]{27}", boot) is not None, "Malformed boot ID")
    require(re.fullmatch(r"[1-9][0-9]*", pid) is not None, "Expected one avocd PID")
    require(exe == AVOC_PATH, "Unexpected avocd executable")
    require(re.fullmatch(r"[1-9][0-9]*", start) is not None, "Malformed process start time")
    require(avoc_hash.split() == [AVOC_SHA256, AVOC_PATH], "Installed avocd hash mismatch")
    require(ave_hash.split() == [AVE_SHA256, AVE_PATH], "Installed libave hash mismatch")
    return {"boot_id": boot, "pid": int(pid), "exe": exe, "start_ticks": int(start)}


def parse_pointers(text: str) -> dict[str, int]:
    names = ("ave_bias", "ve_object", "ve_vptr", "ve_state", "dlsr_global_storage",
             "dlsr_state", "qd_global_storage", "qd_object", "qd_vptr", "qd_inner",
             "backend_object", "backend_vptr", "backend_slot_target",
             "backend_guard_reads", "backend_type")
    tokens = text.split()
    require(len(tokens) == len(names) and all(token.isdigit() for token in tokens),
            "Malformed pointer block")
    return dict(zip(names, (int(token) for token in tokens)))


def check_dd_stderr(text: str, counts: list[int]) -> None:
    lines = text.splitlines()
    require(len(lines) == 3 * len(counts), "Unexpected dd diagnostic inventory")
    for index, count in enumerate(counts):
        group = lines[index * 3:index * 3 + 3]
        require(group[0] == f"{count}+0 records in" and group[1] == f"{count}+0 records out",
                "Incomplete dd record count")
        require(re.fullmatch(rf"{count * 4} bytes \([^()]+\) copied, [0-9.e+-]+ s, [0-9.]+ [kMGT]?B/s",
                             group[2]) is not None, "Unexpected dd byte summary")


def finite_time(value: str, integer: bool = False) -> float:
    require(re.fullmatch(r"[0-9]+" if integer else r"[0-9]+(?:\.[0-9]+)?", value) is not None,
            "Malformed timestamp")
    parsed = float(value)
    require(math.isfinite(parsed), "Non-finite timestamp")
    return parsed


def validate_response(response: dict, contract: dict) -> dict:
    require(response.get("model") == MODEL and response.get("authenticated") is True,
            "Unexpected root controller identity")
    require(response.get("uid") == response.get("euid") == 0, "Root UID mismatch")
    require(response.get("root_persistence") == "host-assisted", "Nonpersistent root path")
    require(response.get("global_system_files_unchanged_at_acquisition") is True,
            "Controller system-file invariant failed")
    commands = response.get("commands")
    require(isinstance(commands, list) and len(commands) == 1, "Unexpected command count")
    item = commands[0]
    require(item.get("exit_code") == 0 and item.get("timed_out") is False, "Remote reader failed")
    sections = blocks(item.get("stdout", ""))
    pointers_start = parse_pointers(sections.get("POINTERS_START", ""))
    pointers_end = parse_pointers(sections.get("POINTERS_END", ""))
    require(pointers_start == pointers_end, "Pointer chain changed during snapshot")
    typed = pointers_start["backend_type"]
    guard_reads = pointers_start["backend_guard_reads"]
    require(typed in (0, 1, 2) and guard_reads in (0, 1, 2), "Invalid backend discriminator")

    identity_start = parse_identity(sections.get("ID_START", ""))
    identity_end = parse_identity(sections.get("ID_END", ""))
    require(identity_start == identity_end, "Process/source identity changed")
    require(sections.get("MAPS_START") == sections.get("MAPS_END"), "Process maps changed")
    mapping = parse_maps(sections["MAPS_START"])
    loads = [lo for lo, _, perms, offset, path in mapping
             if path == AVE_PATH and offset == 0 and "x" in perms]
    require(loads == [pointers_start["ave_bias"]], "Ambiguous or wrong libave load bias")
    bias = pointers_start["ave_bias"]

    ve_class = next((name for name, pair in VE_TYPES.items()
                     if (pointers_start["ve_object"], pointers_start["ve_vptr"]) ==
                     (bias + pair[0], bias + pair[1])), None)
    require(ve_class is not None, "Unexpected VideoEnhancer pointer/vptr pair")
    check_range(mapping, bias + 0x5ADB5C, 1)
    check_range(mapping, pointers_start["ve_object"], 4)
    check_source_range(mapping, pointers_start["ve_vptr"], 0x52C)
    check_range(mapping, pointers_start["ve_state"], 1)
    require(pointers_start["dlsr_global_storage"] == bias + 0x5B24E0,
            "Unexpected DLSR relocated global storage")
    check_range(mapping, bias + 0x5A6A28, 1)
    check_range(mapping, pointers_start["dlsr_global_storage"], 1)
    check_range(mapping, pointers_start["dlsr_state"], 1)

    require(pointers_start["qd_global_storage"] == bias + 0x5BE2A4,
            "Unexpected QD relocated global storage")
    check_range(mapping, bias + 0x5A69EC, 1)
    qd_class = next((name for name, vma in QD_TYPES.items()
                     if pointers_start["qd_vptr"] == bias + vma), None)
    require(qd_class is not None, "Unexpected QD vptr")
    check_source_range(mapping, pointers_start["qd_vptr"], 0x1C0)
    check_range(mapping, pointers_start["qd_global_storage"], 1)
    check_range(mapping, pointers_start["qd_object"], 7)
    check_range(mapping, pointers_start["qd_inner"], 1)

    backend = None
    cache_address = None
    backend_key = (qd_class, pointers_start["backend_vptr"] - bias)
    derived_typed = 0
    if guard_reads == 2 and backend_key in BACKEND_TYPES:
        _, target_vma, _ = BACKEND_TYPES[backend_key]
        if pointers_start["backend_slot_target"] == bias + target_vma:
            derived_typed = 1 if qd_class == "QDDimming" else 2
    require(typed == derived_typed, "Incorrect backend type classification")
    if typed:
        backend, _, cache_vma = BACKEND_TYPES[backend_key]
        cache_address = bias + cache_vma
        check_range(mapping, pointers_start["backend_object"], 1)
        check_source_range(mapping, pointers_start["backend_vptr"] + 0xD8, 4)
        check_source_range(mapping, pointers_start["backend_slot_target"] & ~1, 4,
                           executable=True)
        check_range(mapping, cache_address, 1)
    else:
        if guard_reads == 0:
            require(pointers_start["backend_vptr"] == 0 and
                    pointers_start["backend_slot_target"] == 0,
                    "Unread backend reported guarded values")
        if guard_reads == 1:
            require(pointers_start["backend_slot_target"] == 0,
                    "Unread backend slot reported a target")

    mandatory = {"UTC_START", "UPTIME_START", "ID_START", "MAPS_START",
                 "POINTERS_START", "POINTERS_END", "MAPS_END", "ID_END",
                 "UPTIME_END", "UTC_END"}
    mandatory |= {"READ_" + name for name in COMMON_LAYOUT}
    branch_available = qd_class == "QDDimming"
    if branch_available:
        mandatory |= {"READ_" + name for name in BASE_QD_LAYOUT}
    if typed:
        mandatory.add("READ_backend_cache")
    require(set(sections) == mandatory, "Unexpected or missing output section")

    bases = {"ve_state": pointers_start["ve_state"],
             "dlsr_state": pointers_start["dlsr_state"],
             "qd_object": pointers_start["qd_object"],
             "qd_inner": pointers_start["qd_inner"], "ave_bias": bias}
    decoded = {}
    counts = [1] * (10 + guard_reads)
    layouts = dict(COMMON_LAYOUT)
    if branch_available:
        layouts.update(BASE_QD_LAYOUT)
    for name, (base_name, offset, count) in layouts.items():
        address = bases[base_name] + offset
        check_range(mapping, address, count)
        decoded[name] = {"address": hex(address),
                         "words": decode_words(sections["READ_" + name], count)}
        counts.append(count)
    qd_header = decoded["qd_outer_header"]["words"]
    require(qd_header[0] == pointers_start["qd_vptr"] and
            qd_header[1] == pointers_start["qd_inner"] and
            qd_header[4] == pointers_start["backend_object"],
            "QD outer header disagrees with guarded pointer chain")
    if typed:
        decoded["backend_cache"] = {"address": hex(cache_address),
                                    "words": decode_words(sections["READ_backend_cache"], 1)}
        counts.append(1)
    counts += [1] * (10 + pointers_end["backend_guard_reads"])
    check_dd_stderr(item.get("stderr", ""), counts)

    utc_start = finite_time(sections["UTC_START"], integer=True)
    utc_end = finite_time(sections["UTC_END"], integer=True)
    uptime_start = finite_time(sections["UPTIME_START"].split()[0])
    uptime_end = finite_time(sections["UPTIME_END"].split()[0])
    require(utc_end >= utc_start and uptime_end >= uptime_start, "Nonmonotonic timestamps")

    branch_state = {"available": branch_available, "class_guard": qd_class}
    if branch_available:
        branch_state.update({
            "inner_0000": decoded["qd_branch_inner_0000"]["words"][0],
            "condition_0038_aligned_word": decoded["qd_branch_condition_0038"]["words"][0],
            "condition_0038_low_byte": decoded["qd_branch_condition_0038"]["words"][0] & 0xFF,
            "weight_0088": decoded["qd_branch_weight_0088"]["words"][0],
            "weight_0098": decoded["qd_branch_weight_0098"]["words"][0],
            "floor_00a4": decoded["qd_branch_floor_00a4"]["words"][0],
            "sources_00f8_00fc": decoded["qd_branch_sources_00f8_00fc"]["words"],
            "model_0188_control_018c": decoded["qd_branch_model_0188_control_018c"]["words"],
            "gain_autodim_02a4_02a8": decoded["qd_branch_gain_autodim_02a4_02a8"]["words"],
            "product_0450": decoded["qd_branch_product_0450"]["words"][0],
            "auto_power_off_count": decoded["qd_auto_power_off_count"]["words"][0],
            "current_branch_inferred": False,
        })

    return {
        "physical_state": "unobserved", "physical_state_inferred_from_software": False,
        "accepted": True, "atomic": False, "concurrent_daemon_changes_excluded": False,
        "identity": identity_start,
        "timestamps": {"utc_start": int(utc_start), "utc_end": int(utc_end),
                       "uptime_start": uptime_start, "uptime_end": uptime_end},
        "ave_bias": hex(bias),
        "video_enhancer": {"class": ve_class, "object": hex(pointers_start["ve_object"]),
                           "vptr": hex(pointers_start["ve_vptr"]),
                           "state": hex(pointers_start["ve_state"]),
                           "dlsr_state": hex(pointers_start["dlsr_state"]),
                           "dlsr_state_aliases_object_state":
                               pointers_start["dlsr_state"] == pointers_start["ve_state"]},
        "qd": {"class": qd_class, "object": hex(pointers_start["qd_object"]),
               "vptr": hex(pointers_start["qd_vptr"]),
               "inner": hex(pointers_start["qd_inner"]),
               "initialized_byte": qd_header[6] & 0xFF},
        "backend": {"typed": bool(typed), "class": backend,
                    "object": hex(pointers_start["backend_object"]),
                    "vptr": hex(pointers_start["backend_vptr"]),
                    "slot_target": hex(pointers_start["backend_slot_target"])},
        "branch_state": branch_state, "decoded": decoded,
        "memory_bytes_requested": sum(counts) * 4,
        "limitations": [
            "The reads are sequential and non-atomic; equal endpoint pointers do not exclude changes away and back.",
            "The branch fields are not a simultaneous state and this reader does not infer a current branch.",
            "Integer fields have no inferred physical unit; software values do not prove transport, panel application, or physical light.",
            "Base-QDDimming branch fields and its AutoPowerOff static are omitted unless the exact base class vptr is guarded.",
            "No backend cache is read unless the QD/backend vptr pair is exactly allowlisted.",
        ],
    }


def retained_partial(value) -> dict:
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode()}
    return {"encoding": "text", "data": "" if value is None else str(value)}


def run_capture(destination: Path, contract: dict) -> dict:
    command = build_command()
    record = {
        "schema": "pqe-branch-baseline-v1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "accepted": False, "physical_state": "unobserved", "atomic": False,
        "actions": "one read-only process/source identity, maps, and proc-memory command",
        "contract": contract, "command": command, "command_bytes": len(command.encode()),
        "access_argv": ["python3", str(ACCESS), "root", "--persistent-only", "--timeout", "25",
                        "--command", "<record.command>"],
    }
    try:
        with destination.open("x") as handle:
            handle.write(json.dumps(record, indent=2) + "\n")
    except FileExistsError as exc:
        raise ValueError("Output path already exists") from exc
    try:
        try:
            proc = subprocess.run(
                ["python3", str(ACCESS), "root", "--persistent-only", "--timeout", "25",
                 "--command", command], text=True, capture_output=True, timeout=55)
        except subprocess.TimeoutExpired as timeout:
            record["transport"] = {"timed_out": True, "timeout_seconds": timeout.timeout,
                                   "partial_stdout": retained_partial(timeout.stdout),
                                   "partial_stderr": retained_partial(timeout.stderr)}
            destination.write_text(json.dumps(record, indent=2) + "\n")
            raise
        record["transport"] = {"exit_code": proc.returncode, "stdout": proc.stdout,
                               "stderr": proc.stderr}
        destination.write_text(json.dumps(record, indent=2) + "\n")
        require(proc.returncode == 0, "Root transport failed")
        require(not proc.stderr, "Unexpected root transport stderr")
        try:
            response = json.loads(proc.stdout)
        except ValueError as exc:
            raise ValueError("Root response was not JSON") from exc
        record.update({"accepted": True, "summary": validate_response(response, contract)})
        destination.write_text(json.dumps(record, indent=2) + "\n")
        return record
    except BaseException as exc:
        record["accepted"] = False
        record["error"] = type(exc).__name__ + ": " + str(exc)
        destination.write_text(json.dumps(record, indent=2) + "\n")
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true",
                        help="perform the one reviewed read-only command")
    parser.add_argument("--output", type=Path, help="unique local JSON path (live mode only)")
    args = parser.parse_args()
    contract = static_contract()
    command = build_command()
    if not args.run:
        print(json.dumps({"dry_run": True, "physical_state": "unobserved",
                          "no_tv_or_device_calls": True, "contract": contract,
                          "remote_command_bytes": len(command.encode()),
                          "live_invocation": "--run --output UNIQUE.json"}, indent=2))
        return
    # absolute() preserves a final symlink for the exclusive open; resolve()
    # would follow a dangling output symlink and defeat that refusal.
    destination = (args.output.absolute() if args.output is not None else
                   HERE / ("pqe-branch-baseline-" +
                           dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"))
    result = run_capture(destination, contract)
    print(json.dumps({"path": str(destination), "accepted": result["accepted"],
                      "physical_state": "unobserved"}, indent=2))


if __name__ == "__main__":
    main()
