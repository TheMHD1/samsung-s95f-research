#!/usr/bin/env python3
"""Prepare one bounded, passive onset capture; dry-run by default.

The remote acquisition is one persistent-root shell.  It only reads process
state and established diagnostic interfaces, and writes a private tracefs
instance plus temporary evidence files.  Human observations are local input;
software artifacts never supply a physical-picture label.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import shlex
import subprocess
import sys
import time


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
ACCESS = ROOT.parent / "root-access/s95f-access.py"
MODEL = "QN77S95FAFXZC"
BUILD = "BUILD_ID=T-RSMFAKUC-0090-REL-202607141953"
AVE_PATH = "/prd/usr/lib/libave.so.0.1"
AVE_SHA = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"
AVOC_PATH = "/usr/bin/avocd"
AVOC_SHA = "ab450eaf99c793f3c7a9360629b1a1677e9d86dcd74a1f93796b56ba07401de9"
DEV_PATH = "/usr/bin/deviced"
DEV_SHA = "2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2"
REMOTE_ROOT = "/tmp/researcher-observed-onset-20261026"
STAGE_ROOT = "/tmp/researcher-observed-onset-stage-20261026"
CHUNK = 131072
SIDECAR_LIMITS = {
    "trace": 128 * 1024 * 1024,
    "meta": 4 * 1024 * 1024,
    "samples": 2 * 1024 * 1024,
    "sample-errors": 256 * 1024,
    "vlog-after": 64 * 1024 * 1024,
    "artifacts": 2 * 1024 * 1024,
    "fds": 2 * 1024 * 1024,
}
SUFFIX = {
    "trace": "trace",
    "meta": "meta.txt",
    "samples": "samples.txt",
    "sample-errors": "sample-errors.txt",
    "vlog-after": "vlog-after.txt",
    "artifacts": "artifacts.txt",
    "fds": "fds.txt",
}
TRACE_CONFIG_EXPECTED = {
    "events/i2c/i2c_write/filter": "adapter_nr == 5 && addr == 118",
    "events/i2c/i2c_read/filter": "adapter_nr == 5 && addr == 118",
    "events/i2c/i2c_reply/filter": "adapter_nr == 5 && addr == 118",
    "events/i2c/i2c_result/filter": "adapter_nr == 5",
    "events/drm/drm_vblank_event/filter": "crtc == 1",
}
for _event in (
    "i2c/i2c_write", "i2c/i2c_read", "i2c/i2c_reply", "i2c/i2c_result",
    "early_trace/early_event", "drm/drm_vblank_event", "gpio/gpio_value",
    "gpio/gpio_direction", "clk/clk_set_rate", "clk/clk_disable", "clk/clk_enable",
    "regulator/regulator_disable", "regulator/regulator_enable",
    "regulator/regulator_set_voltage", "sched/sched_process_exec",
    "sched/sched_process_fork", "sched/sched_process_exit",
    "raw_syscalls/sys_enter", "raw_syscalls/sys_exit",
):
    TRACE_CONFIG_EXPECTED[f"events/{_event}/enable"] = "1"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def syscall_filter_for_tids(tids: list[int]) -> str:
    require(bool(tids) and tids == sorted(set(tids)) and all(value > 0 for value in tids),
            "invalid syscall-filter TID set")
    return "id == 54 && (" + " || ".join(f"common_pid == {value}" for value in tids) + ")"


def mark_cleanup_failure(record: dict, exc: BaseException) -> None:
    record["accepted"] = False
    record["technical_capture_complete"] = False
    record["diagnostic_eligible"] = False
    record["cleanup_verified"] = False
    record["cleanup_error"] = type(exc).__name__ + ": " + str(exc)


def mark_acquisition_failure(record: dict, exc: BaseException) -> None:
    """Preserve interruption provenance without consuming the active exception."""
    record.setdefault("error", type(exc).__name__ + ": " + str(exc))


def build_remote_script(label: str, seconds: int, allow_short: bool = False) -> str:
    """Return the hash-staged acquisition shell. Inputs are constrained here."""
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,30}", label) is not None, "invalid label")
    require((85 <= seconds <= 90) or (allow_short and seconds in {5, 10}),
            "full captures require 85..90 seconds; smoke fixtures allow 5 or 10")
    out = f"{REMOTE_ROOT}/{label}"
    tr = f"/sys/kernel/debug/tracing/instances/researcher-onset-{label}"
    stage = f"/tmp/researcher-observed-onset-stage-20261026/{label}"
    expiry_log = f"{out}/expiry.log"
    script = f'''set -eu
umask 077
O={out}; T={tr}; SD={stage}; SELF=$SD/capture.sh; S=$O/samples.txt; E=$O/sample-errors.txt; M=$O/meta.txt; TARGET=$1
case "$TARGET" in *[!0-9.]*) exit 29;; esac; test ! -L "$SD"; test -d "$SD"; test "$(stat -c '%u:%a' "$SD")" = 0:700; test ! -L "$SELF"; test -f "$SELF"; test "$(stat -c '%u:%a' "$SELF")" = 0:600
R={REMOTE_ROOT}; if test -e "$R"; then test ! -L "$R"; test -d "$R"; test "$(stat -c '%u:%a' "$R")" = 0:700; else mkdir -m 700 "$R"; fi; test ! -e "$O"; test ! -e "$T"; mkdir -m 700 "$O"; : >"$E"
vp=; vstart=
vg() {{ test -n "$vp" && set -- $(awk '{{print $3,$22}}' /proc/$vp/stat 2>/dev/null) && test "${{2:-}}" = "$vstart" && test "${{1:-}}" != Z; }}
stopv() {{ test -z "$vp" && return 0; if vg; then kill -TERM "$vp" 2>/dev/null || true; for i in 1 2 3 4 5; do vg || break; sleep .2; done; fi; if vg; then kill -KILL "$vp" 2>/dev/null || true; for i in 1 2 3 4 5; do vg || break; sleep .2; done; fi; vg && return 1; wait "$vp" 2>/dev/null || true; return 0; }}
clean() {{ cs=0; stopv || cs=1; if test -d "$T"; then echo 0 2>/dev/null >"$T/tracing_on" || cs=1; echo 0 2>/dev/null >"$T/events/enable" || cs=1; rmdir "$T" 2>/dev/null || cs=1; fi; return "$cs"; }}
trap clean EXIT; trap 'trap - EXIT; clean || true; exit 143' HUP INT TERM
/usr/bin/setsid /bin/sh -c 'sleep 900; O={out}; T={tr}; SD={stage}; survivor=0; trusted() {{ test -f "$1" && test ! -L "$1" && test "$(stat -c "%u:%a" "$1")" = 0:600; }}; guard() {{ p=$1; s=$2; set -- $(awk "{{print \\$3,\\$22}}" /proc/$p/stat 2>/dev/null); test "${{2:-}}" = "$s" && test "${{1:-}}" != Z; }}; guardpg() {{ p=$1; s=$2; set -- $(awk "{{print \\$3,\\$5,\\$6,\\$22}}" /proc/$p/stat 2>/dev/null); test "${{4:-}}" = "$s" && test "${{1:-}}" != Z && test "${{2:-}}" = "$p" && test "${{3:-}}" = "$p"; }}; group_active() {{ p=$1; for f in /proc/[0-9]*/stat; do row=; {{ IFS= read -r row <"$f"; }} 2>/dev/null || continue; rest=${{row##*) }}; set -- $rest; test "${{1:-Z}}" != Z && test "${{3:-}}" = "$p" && return 0; done; return 1; }}; stoppg() {{ f=$1; test -e "$f" || return; trusted "$f" || {{ survivor=1; return; }}; read p s <"$f"; if guardpg "$p" "$s"; then kill -TERM -"$p" 2>/dev/null || true; continuous=1; for i in 1 2 3 4 5; do group_active "$p" || {{ continuous=0; break; }}; sleep 1; done; if test "$continuous" = 1 && group_active "$p"; then kill -KILL -"$p" 2>/dev/null || true; for i in 1 2 3 4 5; do group_active "$p" || break; sleep 1; done; fi; group_active "$p" && survivor=1; elif group_active "$p"; then survivor=1; fi; }}; stoppid() {{ f=$1; test -e "$f" || return; trusted "$f" || {{ survivor=1; return; }}; read p s <"$f"; if guard "$p" "$s"; then kill -TERM "$p" 2>/dev/null || true; for i in 1 2 3 4 5; do guard "$p" "$s" || break; sleep 1; done; if guard "$p" "$s"; then kill -KILL "$p" 2>/dev/null || true; for i in 1 2 3 4 5; do guard "$p" "$s" || break; sleep 1; done; fi; guard "$p" "$s" && survivor=1; fi; }}; stoppg "$SD/collector.pid"; stoppid "$O/vlog.pid"; if test -d "$T"; then echo 0 >"$T/tracing_on"; echo 0 >"$T/events/enable"; rmdir "$T"; fi; if test "$survivor" = 0; then rm -f "$O/trace" "$O/meta.txt" "$O/samples.txt" "$O/sample-errors.txt" "$O/vlog-after.txt" "$O/artifacts.txt" "$O/fds.txt" "$O/vlog.pid" "$O/watchdog.pid" "$SD/capture.sh" "$SD/collector.pid" "$SD/collector.stdout" "$SD/collector.stderr" "$SD/expiry.pid" "$SD/expiry.log" {expiry_log}; rmdir "$O" "$SD" 2>/dev/null || true; fi' >{expiry_log} 2>&1 </dev/null &
X=$!; xs=$(awk '{{print $22}}' /proc/$X/stat); case "$xs" in ''|*[!0-9]*) exit 40;; esac; xr=0; for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$X/stat 2>/dev/null); test "${{4:-}}" = "$xs" || break; test "${{1:-}}" != Z || break; if test "${{2:-}}" = "$X" && test "${{3:-}}" = "$X"; then xr=1; break; fi; sleep .05; done; if test "$xr" != 1; then xg=0; set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$X/stat 2>/dev/null); if test "${{4:-}}" = "$xs" && test "${{1:-}}" != Z; then if test "${{2:-}}" = "$X" && test "${{3:-}}" = "$X"; then xg=1; kill -KILL -"$X" 2>/dev/null || true; else kill -KILL "$X" 2>/dev/null || true; fi; fi; for i in 1 2 3 4 5 6 7 8 9 10; do set -- $(awk '{{print $3,$22}}' /proc/$X/stat 2>/dev/null); test "${{2:-}}" = "$xs" && test "${{1:-}}" != Z || break; sleep .05; done; set -- $(awk '{{print $3,$22}}' /proc/$X/stat 2>/dev/null); test "${{2:-}}" != "$xs" || test "${{1:-}}" = Z || exit 42; test "$xg" != 1 || ! kill -0 -"$X" 2>/dev/null || exit 42; exit 41; fi; echo "$X $xs" >"$O/watchdog.pid"; chmod 600 "$O/watchdog.pid"; kill -0 -"$X"
if test -e "$SD/expiry.pid"; then test -f "$SD/expiry.pid"; test ! -L "$SD/expiry.pid"; test "$(stat -c '%u:%a' "$SD/expiry.pid")" = 0:600; read sx ss <"$SD/expiry.pid"; spg() {{ set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$sx/stat 2>/dev/null); test "${{4:-}}" = "$ss" && test "${{1:-}}" != Z && test "${{2:-}}" = "$sx" && test "${{3:-}}" = "$sx"; }}; spga() {{ for f in /proc/[0-9]*/stat; do row=; {{ IFS= read -r row <"$f"; }} 2>/dev/null || continue; rest=${{row##*) }}; set -- $rest; test "${{1:-Z}}" != Z && test "${{3:-}}" = "$sx" && return 0; done; return 1; }}; spg; kill -TERM -"$sx" 2>/dev/null || true; continuous=1; for i in 1 2 3 4 5; do spga || {{ continuous=0; break; }}; sleep .2; done; if test "$continuous" = 1 && spga; then kill -KILL -"$sx" 2>/dev/null || true; for i in 1 2 3 4 5; do spga || break; sleep .2; done; fi; ! spga; rm -f "$SD/expiry.pid"; fi
grep -qx '{BUILD}' /etc/tizen-release
test "$(sha256sum {AVOC_PATH}|cut -d' ' -f1)" = {AVOC_SHA}; test "$(sha256sum {AVE_PATH}|cut -d' ' -f1)" = {AVE_SHA}; test "$(sha256sum {DEV_PATH}|cut -d' ' -f1)" = {DEV_SHA}
fu=$( (ulimit -f 1; awk '/Max file size/{{print $4}}' /proc/self/limits) ); test "$fu" = 1024
dk=$(df -Pk "$O"|awk 'END{{print $4}}'); mk=$(awk '/MemAvailable/{{print $2}}' /proc/meminfo); test "$dk" -ge 262144; test "$mk" -ge 262144
ap=$(pidof avocd); dp=$(pidof deviced); case "$ap:$dp" in *[!0-9:]*) exit 31;; esac
am=/proc/$ap/maps; dm=/proc/$dp/maps
ab=$(awk '$3=="00000000"&&$6=="{AVE_PATH}"{{split($1,a,"-");print a[1]}}' "$am"); db=$(awk '$3=="00000000"&&$6=="{DEV_PATH}"{{split($1,a,"-");print a[1]}}' "$dm")
case "$ab:$db" in ????????:????????) ;; *) exit 32;; esac; A=$((0x$ab)); D=$((0x$db))
mapok() {{ q=$1; z=$2; f=$3; test "$q" -gt 0 || return 1; test "$z" -gt 0 || return 1; test $((q%4)) = 0 || return 1; test $((z%4)) = 0 || return 1; while read r p x; do case "$p" in r*) l=${{r%-*}}; h=${{r#*-}}; l=$((0x$l)); h=$((0x$h)); test "$q" -ge "$l" && test $((q+z)) -le "$h" && return 0;; esac; done <"$f"; return 1; }}
u32() {{ mapok "$1" 4 "$2" || return 1; (ulimit -f 256; dd if=/proc/$3/mem bs=4 skip=$(($1/4)) count=1 2>>"$E")|od -An -tu4|tr -d " "; }}
sampleok() {{ k="$1:$2:$3:$4"; case "$k" in "$((A+0x5bfc5c)):38:$am:$ap"|"$((A+0x5a69ec)):1:$am:$ap"|"$G:1:$am:$ap"|"$P:2:$am:$ap"|"$((A+0x5ab958)):1:$am:$ap"|"$((I+0xa8)):2:$am:$ap"|"$DG:6:$dm:$dp"|"$((D+0x12aeb8)):1:$dm:$dp"|"$((EP+0x30)):4:$dm:$dp"|"$((OP+0x24)):1:$dm:$dp"|"$EC:1:$dm:$dp"|"$ET:1:$dm:$dp"|"$EA:1:$dm:$dp") return 0;; *) return 1;; esac; }}
b64() {{ sampleok "$1" "$2" "$3" "$4" || {{ printf "!range"; return; }}; v=$( (ulimit -f 256; dd if=/proc/$4/mem bs=4 skip=$(($1/4)) count=$2 2>>"$E")|base64|tr -d "\\n"); test -n "$v" && printf %s "$v" || printf "!read"; }}
G=$((A+0x5be2a4)); test "$(u32 $((A+0x5a69ec)) "$am" $ap)" = "$G"; P=$(u32 "$G" "$am" $ap); V=$(u32 "$P" "$am" $ap); I=$(u32 $((P+4)) "$am" $ap)
test "$V" = $((A+0x59f2e8)) || test "$V" = $((A+0x5a094c)); mapok "$I" 688 "$am"
DG=$((D+0x12af7c)); e0=$(u32 "$DG" "$dm" $dp); e1=$(u32 $((DG+4)) "$dm" $dp); es=$(u32 $((DG+8)) "$dm" $dp); o0=$(u32 $((DG+12)) "$dm" $dp); o1=$(u32 $((DG+16)) "$dm" $dp); os=$(u32 $((DG+20)) "$dm" $dp); es=$((es&255)); os=$((os&255)); test "$es" -le 1; test "$os" -le 1
test "$es:$os" = 0:0; EP=$e0; OP=$o0; mapok $((EP+0x30)) 16 "$dm"; mapok $((OP+0x24)) 4 "$dm"
EC=$(u32 $((EP+0x34)) "$dm" $dp); ET=$(u32 $((EP+0x38)) "$dm" $dp); EA=$(u32 $((EP+0x3c)) "$dm" $dp); ECV=$(u32 "$EC" "$dm" $dp); ETV=$(u32 "$ET" "$dm" $dp); EAV=$(u32 "$EA" "$dm" $dp)
test "$ECV" = $((D+0x128a28)); test "$ETV" = $((D+0x128a90)); test "$EAV" = $((D+0x128ab0)); pw=$(u32 $((D+0x12aeb8)) "$dm" $dp); test "$pw" -le 6
for x in "$((A+0x5bfc5c)) 38 $am $ap" "$((A+0x5a69ec)) 1 $am $ap" "$G 1 $am $ap" "$P 2 $am $ap" "$((A+0x5ab958)) 1 $am $ap" "$((I+0xa8)) 2 $am $ap" "$DG 6 $dm $dp" "$((D+0x12aeb8)) 1 $dm $dp" "$((EP+0x30)) 4 $dm $dp" "$((OP+0x24)) 1 $dm $dp" "$EC 1 $dm $dp" "$ET 1 $dm $dp" "$EA 1 $dm $dp"; do set -- $x; mapok "$1" $(($2*4)) "$3" || exit 33; done
(ulimit -f 4096; {{ echo @@ BUILD; cat /etc/tizen-release; echo @@ SCRIPT_HASH_START; wc -c "$SELF"; sha256sum "$SELF"; echo @@ BOOT_START; cat /proc/sys/kernel/random/boot_id; echo @@ SYNC_START; date -u +%s; cat /proc/uptime; echo @@ AVOC_ID_START; echo "$ap"; readlink /proc/$ap/exe; awk '{{print $22}}' /proc/$ap/stat; sha256sum {AVOC_PATH} {AVE_PATH}; echo @@ DEV_ID_START; echo "$dp"; readlink /proc/$dp/exe; awk '{{print $22}}' /proc/$dp/stat; sha256sum {DEV_PATH}; echo @@ POINTERS_START; echo "$A $G $P $V $I $D $DG $e0 $e1 $es $o0 $o1 $os $EP $OP $EC $ET $EA $ECV $ETV $EAV"; echo @@ AVOC_MAPS_START; cat "$am"; echo @@ DEV_MAPS_START; cat "$dm"; echo @@ GLOBAL_TRACE_START; cat /sys/kernel/debug/tracing/tracing_on /sys/kernel/debug/tracing/current_tracer /sys/kernel/debug/tracing/buffer_size_kb /sys/kernel/debug/tracing/trace_clock /sys/kernel/debug/tracing/events/enable; }} >"$M")
tids() {{ for x in /proc/$ap/task/*; do echo "${{x##*/}}"; done | sort -n; }}; tids0=$(tids); test -n "$tids0"
(ulimit -f 2048; {{ echo @@ TIDS_START; echo "$tids0"; echo @@ FDS_START; for q in /proc/$ap/fd/*; do printf "%s " "${{q##*/}}"; readlink "$q" || true; done; }} >"$O/{SUFFIX['fds']}")
(ulimit -f 2048; {{ echo @@ BASELINE; date -u +%s; cat /proc/uptime; df -k "$O"; grep MemAvailable /proc/meminfo; enlightenment_info -frender all; enlightenment_info -hwc_wins; enlightenment_info -screen_info; cat /sys/kernel/debug/frc/frctest/irq_status; }} >"$O/{SUFFIX['artifacts']}" 2>&1)
mkdir "$T"; echo 0 >"$T/tracing_on"; echo 4096 >"$T/buffer_size_kb"; echo mono >"$T/trace_clock"; bt=$(cat "$T/buffer_total_size_kb"); test "$bt" -gt 0; test "$bt" -le 16384; grep -qx record-tgid "$T/trace_options"
for e in i2c_write i2c_read i2c_reply; do echo "adapter_nr == 5 && addr == 118" >"$T/events/i2c/$e/filter"; echo 1 >"$T/events/i2c/$e/enable"; done
echo "adapter_nr == 5" >"$T/events/i2c/i2c_result/filter"; echo 1 >"$T/events/i2c/i2c_result/enable"; echo "crtc == 1" >"$T/events/drm/drm_vblank_event/filter"
for e in early_trace/early_event drm/drm_vblank_event gpio/gpio_value gpio/gpio_direction clk/clk_set_rate clk/clk_disable clk/clk_enable regulator/regulator_disable regulator/regulator_enable regulator/regulator_set_voltage sched/sched_process_exec sched/sched_process_fork sched/sched_process_exit; do echo 1 >"$T/events/$e/enable"; done
cf="events/i2c/i2c_write/filter events/i2c/i2c_read/filter events/i2c/i2c_reply/filter events/i2c/i2c_result/filter events/drm/drm_vblank_event/filter events/i2c/i2c_write/enable events/i2c/i2c_read/enable events/i2c/i2c_reply/enable events/i2c/i2c_result/enable events/early_trace/early_event/enable events/drm/drm_vblank_event/enable events/gpio/gpio_value/enable events/gpio/gpio_direction/enable events/clk/clk_set_rate/enable events/clk/clk_disable/enable events/clk/clk_enable/enable events/regulator/regulator_disable/enable events/regulator/regulator_enable/enable events/regulator/regulator_set_voltage/enable events/sched/sched_process_exec/enable events/sched/sched_process_fork/enable events/sched/sched_process_exit/enable events/raw_syscalls/sys_enter/enable events/raw_syscalls/sys_exit/enable"
vs=$(awk -v t="$TARGET" 'BEGIN{{printf "%.3f",t-2}}'); ve=$(awk -v t="$TARGET" -v n={seconds + 3} 'BEGIN{{printf "%.3f",t+n}}'); now=$(cut -d" " -f1 /proc/uptime); awk -v n="$now" -v t="$TARGET" 'BEGIN{{exit !(n<t-1)}}'
(ulimit -f 65536; exec /usr/bin/vlogutil -v kerneltime -s --start-from="$vs" --end-to="$ve") >"$O/{SUFFIX['vlog-after']}" 2>&1 & vp=$!; vstart=$(awk '{{print $22}}' /proc/$vp/stat); echo "$vp $vstart" >"$O/vlog.pid"; chmod 600 "$O/vlog.pid"
arm=$(awk -v t="$TARGET" 'BEGIN{{printf "%.3f",t-1}}'); now=$(cut -d" " -f1 /proc/uptime); delay=$(awk -v n="$now" -v t="$arm" 'BEGIN{{printf "%.3f",t-n}}'); sleep "$delay"
tids_pre=$(tids); test "$tids_pre" = "$tids0"; (ulimit -f 2048; {{ echo @@ TIDS_PRE; echo "$tids_pre"; }} >>"$O/{SUFFIX['fds']}")
sf='id == 54 && ('; sep=; for q in $tids_pre; do sf="${{sf}}${{sep}}common_pid == $q"; sep=' || '; done; sf="${{sf}})"; echo "$sf" >"$T/events/raw_syscalls/sys_enter/filter"; echo "$sf" >"$T/events/raw_syscalls/sys_exit/filter"; echo 1 >"$T/events/raw_syscalls/sys_enter/enable"; echo 1 >"$T/events/raw_syscalls/sys_exit/enable"
(ulimit -f 4096; {{ echo @@ TRACE_CONFIG; echo "PER_CPU_KB=$(cat "$T/buffer_size_kb")"; echo "TOTAL_KB=$bt"; echo "RECORD_TGID=record-tgid"; printf "TRACE_CLOCK="; cat "$T/trace_clock"; printf "SYSCALL_ENTER_FILTER="; cat "$T/events/raw_syscalls/sys_enter/filter"; printf "SYSCALL_EXIT_FILTER="; cat "$T/events/raw_syscalls/sys_exit/filter"; for f in $cf; do printf "%s=" "$f"; cat "$T/$f"; done; }} >>"$M")
echo 1 >"$T/tracing_on"; tids_arm=$(tids); test "$tids_arm" = "$tids_pre"; (ulimit -f 2048; {{ echo @@ TIDS_ARM; echo "$tids_arm"; }} >>"$O/{SUFFIX['fds']}")
now=$(cut -d" " -f1 /proc/uptime); delay=$(awk -v n="$now" -v t="$TARGET" 'BEGIN{{printf "%.3f",t-n}}'); sleep "$delay"; ts=$(cut -d" " -f1 /proc/uptime); awk -v n="$ts" -v t="$TARGET" 'BEGIN{{exit !(n>=t&&n<=t+.75)}}'
st=$(date -u +%s); en=$(awk -v t="$ts" -v n={seconds} 'BEGIN{{printf "%.3f",t+n}}'); echo "CAPTURE_START utc=$st uptime=$ts" >"$T/trace_marker"; sr=0
(ulimit -f 256; i=0; while awk -v n="$(cut -d" " -f1 /proc/uptime)" -v e="$en" 'BEGIN{{exit !(n<e)}}'; do up=$(cut -d" " -f1 /proc/uptime); printf "M|%s|" "$up" >>"$S"; b64 $((A+0x5bfc5c)) 38 "$am" $ap >>"$S"; echo >>"$S"; if test $((i%5)) = 0; then printf "Q|%s" "$up" >>"$S"; for x in "$((A+0x5a69ec)) 1 $am $ap" "$G 1 $am $ap" "$P 2 $am $ap" "$((A+0x5ab958)) 1 $am $ap" "$((I+0xa8)) 2 $am $ap" "$DG 6 $dm $dp" "$((D+0x12aeb8)) 1 $dm $dp" "$((EP+0x30)) 4 $dm $dp" "$((OP+0x24)) 1 $dm $dp" "$EC 1 $dm $dp" "$ET 1 $dm $dp" "$EA 1 $dm $dp"; do set -- $x; printf "|" >>"$S"; b64 "$1" "$2" "$3" "$4" >>"$S"; done; echo >>"$S"; fi; i=$((i+1)); sleep .2; done) || sr=$?
te=$(cut -d" " -f1 /proc/uptime); echo "CAPTURE_END utc=$(date +%s) uptime=$te" >"$T/trace_marker"; echo 0 >"$T/tracing_on"; tr=0; (ulimit -f 131072; cat "$T/trace") >"$O/{SUFFIX['trace']}" || tr=$?; echo 0 >"$T/events/enable"; rmdir "$T"; set +e; sleep 2
ar=0; (ulimit -f 2048; echo @@ END || exit 71; date -u +%s || exit 72; cat /proc/uptime || exit 73; df -k "$O" || exit 74; grep MemAvailable /proc/meminfo || exit 75; enlightenment_info -frender all || exit 76; enlightenment_info -hwc_wins || exit 77; enlightenment_info -screen_info || exit 78; cat /sys/kernel/debug/frc/frctest/irq_status || exit 79) >>"$O/{SUFFIX['artifacts']}" 2>&1 || ar=$?
vd=$(awk -v e="$ve" 'BEGIN{{printf "%.3f",e+4}}'); while vg && awk -v n="$(cut -d" " -f1 /proc/uptime)" -v d="$vd" 'BEGIN{{exit !(n<d)}}'; do sleep 1; done; vk=0; vr=0; if vg; then vk=1; stopv || vk=2; vr=143; else wait "$vp" || vr=$?; fi; test "$vk" != 2 || exit 62; rm -f "$O/vlog.pid"
hv=0; test "$(sha256sum {AVOC_PATH}|cut -d' ' -f1)" = {AVOC_SHA} || hv=1; test "$(sha256sum {AVE_PATH}|cut -d' ' -f1)" = {AVE_SHA} || hv=1; test "$(sha256sum {DEV_PATH}|cut -d' ' -f1)" = {DEV_SHA} || hv=1
(ulimit -f 4096; {{ echo @@ BOOT_END; cat /proc/sys/kernel/random/boot_id; echo @@ SYNC_END; date -u +%s; cat /proc/uptime; echo @@ CAPTURE_WINDOW; echo "$TARGET $ts $te $vs $ve $vr $vk $tr $hv $sr $ar"; echo @@ AVOC_ID_END; pidof avocd; readlink /proc/$ap/exe; awk '{{print $22}}' /proc/$ap/stat; sha256sum {AVOC_PATH} {AVE_PATH}; echo @@ DEV_ID_END; pidof deviced; readlink /proc/$dp/exe; awk '{{print $22}}' /proc/$dp/stat; sha256sum {DEV_PATH}; echo @@ POINTERS_END; echo "$A $(u32 $((A+0x5a69ec)) "$am" $ap) $(u32 "$G" "$am" $ap) $(u32 "$P" "$am" $ap) $(u32 $((P+4)) "$am" $ap) $D $DG $(u32 "$DG" "$dm" $dp) $(u32 $((DG+4)) "$dm" $dp) $(u32 $((DG+8)) "$dm" $dp) $(u32 $((DG+12)) "$dm" $dp) $(u32 $((DG+16)) "$dm" $dp) $(u32 $((DG+20)) "$dm" $dp) $EP $OP $(u32 $((EP+0x34)) "$dm" $dp) $(u32 $((EP+0x38)) "$dm" $dp) $(u32 $((EP+0x3c)) "$dm" $dp) $(u32 "$EC" "$dm" $dp) $(u32 "$ET" "$dm" $dp) $(u32 "$EA" "$dm" $dp)"; echo @@ AVOC_MAPS_END; cat "$am"; echo @@ DEV_MAPS_END; cat "$dm"; echo @@ SCRIPT_HASH_END; wc -c "$SELF"; sha256sum "$SELF"; echo @@ GLOBAL_TRACE_END; cat /sys/kernel/debug/tracing/tracing_on /sys/kernel/debug/tracing/current_tracer /sys/kernel/debug/tracing/buffer_size_kb /sys/kernel/debug/tracing/trace_clock /sys/kernel/debug/tracing/events/enable; echo @@ VLOG_SEMANTICS; echo "/usr/bin/vlogutil -s absolute uptime bounds; coverage measured"; }} >>"$M")
(ulimit -f 2048; {{ echo @@ TIDS_END; for q in $(for x in /proc/$ap/task/*; do echo "${{x##*/}}"; done | sort -n); do echo "$q"; done; echo @@ FDS_END; for q in /proc/$ap/fd/*; do printf "%s " "${{q##*/}}"; readlink "$q" || true; done; }} >>"$O/{SUFFIX['fds']}")
for n in trace meta samples sample-errors vlog-after artifacts fds; do test "$n" = trace && f="$O/trace" || f="$O/$n.txt"; case "$n" in trace)L=134217728;;meta)L=4194304;;samples)L=2097152;;sample-errors)L=262144;;vlog-after)L=67108864;;*)L=2097152;;esac; set -- $(wc -c "$f") $(sha256sum "$f"); test "$1" -le "$L"; echo "SIDECAR $n $1 $3"; done
echo CAPTURE_COMPLETE
'''
    return script


def sections(text: str) -> dict[str, str]:
    result: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("@@ "):
            current = line[3:]
            require(current not in result, "duplicate section: " + current)
            result[current] = []
        else:
            require(current is not None, "unframed metadata")
            result[current].append(line)
    return {key: "\n".join(value).strip() for key, value in result.items()}


def parse_maps(text: str) -> list[tuple[int, int, str, int, str]]:
    result = []
    for line in text.splitlines():
        fields = line.split(None, 5)
        require(len(fields) >= 5, "malformed maps line")
        bounds = fields[0].split("-")
        require(len(bounds) == 2, "malformed maps bounds")
        result.append((int(bounds[0], 16), int(bounds[1], 16), fields[1],
                       int(fields[2], 16), fields[5] if len(fields) == 6 else ""))
    require(bool(result), "empty maps")
    return result


def mapped(mapping: list[tuple[int, int, str, int, str]], address: int, size: int) -> bool:
    return address % 4 == 0 and 0 < address < 2**32 and 0 < size <= 4096 and any(
        lo <= address and address + size <= hi and perms.startswith("r")
        for lo, hi, perms, _offset, _path in mapping)


def decode_words(value: str, count: int) -> list[int]:
    require(value not in {"!read", "!range"}, "remote memory read failure")
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError("invalid sample base64") from exc
    require(len(raw) == count * 4, "short sample")
    return [int.from_bytes(raw[i:i + 4], "little") for i in range(0, len(raw), 4)]


def identity_block(text: str, exe: str, hashes: dict[str, str]) -> tuple[int, int]:
    lines = text.splitlines()
    require(len(lines) == 3 + len(hashes), "identity field count")
    require(re.fullmatch(r"[1-9][0-9]*", lines[0]) is not None, "bad pid")
    require(lines[1] == exe, "executable changed")
    require(re.fullmatch(r"[1-9][0-9]*", lines[2]) is not None, "bad start ticks")
    observed = {}
    for line in lines[3:]:
        parts = line.split()
        require(len(parts) == 2 and re.fullmatch(r"[0-9a-f]{64}", parts[0]) is not None,
                "bad source hash row")
        observed[parts[1]] = parts[0]
    require(observed == hashes, "source hash mismatch")
    return int(lines[0]), int(lines[2])


def validate_metadata(text: str, script_size: int, script_sha256: str, seconds: int) -> dict:
    part = sections(text)
    needed = {"BUILD", "SCRIPT_HASH_START", "BOOT_START", "SYNC_START", "AVOC_ID_START", "DEV_ID_START",
              "POINTERS_START", "AVOC_MAPS_START", "DEV_MAPS_START", "GLOBAL_TRACE_START",
              "TRACE_CONFIG", "BOOT_END", "SYNC_END", "CAPTURE_WINDOW", "AVOC_ID_END",
              "DEV_ID_END", "POINTERS_END", "AVOC_MAPS_END", "DEV_MAPS_END",
              "SCRIPT_HASH_END", "GLOBAL_TRACE_END", "VLOG_SEMANTICS"}
    require(set(part) == needed, "unexpected/missing metadata sections")
    require(BUILD in part["BUILD"].splitlines(), "build mismatch")
    require(re.fullmatch(r"[0-9a-f-]{36}", part["BOOT_START"]) is not None, "bad boot id")
    require(part["BOOT_START"] == part["BOOT_END"], "boot identity changed")
    av0 = identity_block(part["AVOC_ID_START"], AVOC_PATH,
                         {AVOC_PATH: AVOC_SHA, AVE_PATH: AVE_SHA})
    av1 = identity_block(part["AVOC_ID_END"], AVOC_PATH,
                         {AVOC_PATH: AVOC_SHA, AVE_PATH: AVE_SHA})
    de0 = identity_block(part["DEV_ID_START"], DEV_PATH, {DEV_PATH: DEV_SHA})
    de1 = identity_block(part["DEV_ID_END"], DEV_PATH, {DEV_PATH: DEV_SHA})
    require(av0 == av1 and de0 == de1, "process identity changed")
    require(part["AVOC_MAPS_START"] == part["AVOC_MAPS_END"], "AVOC maps changed")
    require(part["DEV_MAPS_START"] == part["DEV_MAPS_END"], "deviced maps changed")
    require(part["GLOBAL_TRACE_START"] == part["GLOBAL_TRACE_END"],
            "global tracing settings changed")
    for name in ("SCRIPT_HASH_START", "SCRIPT_HASH_END"):
        rows = part[name].splitlines()
        require(len(rows) == 2 and int(rows[0].split()[0]) == script_size and
                rows[1].split()[0] == script_sha256, "staged script identity mismatch")
    require("absolute uptime bounds" in part["VLOG_SEMANTICS"],
            "vlog time-window contract missing")
    config_rows = part["TRACE_CONFIG"].splitlines()
    config = {}
    for row in config_rows:
        key, sep, value = row.partition("=")
        require(sep and key and key not in config, "malformed/duplicate trace configuration")
        config[key] = value
    require(config.pop("PER_CPU_KB", None) == "4096", "private per-CPU trace budget mismatch")
    total = config.pop("TOTAL_KB", "")
    require(total.isdigit() and 0 < int(total) <= 16384, "private total trace budget mismatch")
    require(config.pop("RECORD_TGID", None) == "record-tgid",
            "private saved-TGID trace option unavailable")
    require("[mono]" in config.pop("TRACE_CLOCK", ""), "private trace clock mismatch")
    enter_filter = config.pop("SYSCALL_ENTER_FILTER", "")
    exit_filter = config.pop("SYSCALL_EXIT_FILTER", "")
    filter_match = re.fullmatch(
        r"id == 54 && \(common_pid == ([1-9][0-9]*(?: \|\| common_pid == [1-9][0-9]*)*)\)",
        enter_filter)
    filter_tids = ([int(value) for value in
                    re.findall(r"common_pid == ([1-9][0-9]*)", enter_filter)]
                   if filter_match is not None else [])
    require(enter_filter == exit_filter and filter_match is not None and
            enter_filter == syscall_filter_for_tids(filter_tids),
            "private syscall filters mismatch")
    require(config == TRACE_CONFIG_EXPECTED, "private trace event/filter readback mismatch")
    amap, dmap = parse_maps(part["AVOC_MAPS_START"]), parse_maps(part["DEV_MAPS_START"])
    require(part["AVOC_MAPS_END"] == part["AVOC_MAPS_START"] and
            part["DEV_MAPS_END"] == part["DEV_MAPS_START"],
            "process maps changed during capture")
    start = [int(x) for x in part["POINTERS_START"].split()]
    end = [int(x) for x in part["POINTERS_END"].split()]
    require(len(start) == len(end) == 21, "pointer field count")
    a, glob, panel, vptr, inner, d, dglob = start[:7]
    e0, e1, es, o0, o1, osel, ep, op, ec, et, ea, ecv, etv, eav = start[7:]
    require(es == osel == 0 and e0 == ep and o0 == op, "unsupported starting deviced chain")
    require(glob == a + 0x5BE2A4, "bad AVE global")
    require(vptr in (a + 0x59F2E8, a + 0x5A094C), "unsupported QD object")
    for address, size in ((glob, 4), (panel, 8), (inner + 0xA8, 8),
                          (a + 0x5AB958, 4), (a + 0x5BFC5C, 152)):
        require(mapped(amap, address, size), "unreadable AVOC target")
    for address in (dglob, ep + 0x30, op + 0x24, d + 0x12AEB8, ec, et, ea):
        require(mapped(dmap, address, 4), "unreadable deviced target")
    require([ecv, etv, eav] == [d + 0x128A28, d + 0x128A90, d + 0x128AB0],
            "deviced child vptr mismatch")
    require(end == start, "pointer/vptr chain changed")
    sync0, sync1 = (part[name].splitlines() for name in ("SYNC_START", "SYNC_END"))
    require(len(sync0) == len(sync1) == 2, "sync field count")
    utc0, utc1 = int(sync0[0]), int(sync1[0])
    up0, up1 = float(sync0[1].split()[0]), float(sync1[1].split()[0])
    require(math.isfinite(up0) and math.isfinite(up1) and utc0 <= utc1 and up0 < up1,
            "invalid synchronization anchors")
    require(abs((utc1 - utc0) - (up1 - up0)) <= 3.0,
            "UTC/uptime anchors disagree or wall clock stepped")
    window = part["CAPTURE_WINDOW"].split()
    require(len(window) == 11 and window[5:] == ["0", "0", "0", "0", "0", "0"],
            "vlog/trace/hash export failed or window malformed")
    target, trace_start, trace_end, vlog_start, vlog_end = map(float, window[:5])
    trace_duration = round(trace_end - trace_start, 3)
    require(all(math.isfinite(x) for x in (target, trace_start, trace_end, vlog_start, vlog_end)) and
            target <= trace_start <= target + .75 and seconds <= trace_duration <= seconds + 1.0 and
            up0 <= trace_start < trace_end <= up1 and vlog_start <= trace_start - 1.0 and
            vlog_end >= trace_end + 1.0, "capture/vlog window does not include margins")
    return {"sections": part, "avoc_identity": av0, "deviced_identity": de0,
            "avoc_maps": amap, "deviced_maps": dmap,
            "sync_start": {"utc": utc0, "uptime": up0},
            "sync_end": {"utc": utc1, "uptime": up1}, "target": target, "trace_start": trace_start,
            "trace_end": trace_end, "trace_duration_seconds": trace_duration,
            "vlog_window": [vlog_start, vlog_end],
            "trace_filter": enter_filter, "trace_filter_tids": filter_tids,
            "trace_config": TRACE_CONFIG_EXPECTED,
            "vlog_exit_code": int(window[5]), "vlog_forced_termination": bool(int(window[6])),
            "pointers": [a, glob, panel, vptr, inner, d, dglob, ep, op, ec, et, ea, ecv, etv, eav]}


def analyze_samples(text: str, meta: dict, seconds: int) -> dict:
    monitor, qd = [], []
    (a, glob, panel, vptr, inner, d, dglob, ep, op,
     ec, et, ea, ecv, etv, eav) = meta["pointers"]
    for line in text.splitlines():
        fields = line.split("|")
        require(len(fields) >= 3, "malformed sample row")
        up = float(fields[1])
        require(math.isfinite(up) and meta["trace_start"] <= up <= meta["trace_end"],
                "sample timestamp outside capture window")
        if fields[0] == "M":
            require(len(fields) == 3, "monitor row shape")
            words = decode_words(fields[2], 38)
            monitor.append((up, words))
        elif fields[0] == "Q":
            require(len(fields) == 14, "QD row shape")
            values = [decode_words(value, count) for value, count in zip(
                fields[2:], (1, 1, 2, 1, 2, 6, 1, 4, 1, 1, 1, 1))]
            require(values[0] == [glob] and values[1] == [panel] and
                    values[2] == [vptr, inner], "sampled QD pointer chain changed")
            g = values[5]
            es, osel = g[2] & 255, g[5] & 255
            require(es == 0 and osel == 0, "unsupported sampled deviced selector")
            require(g[0] == ep and g[3] == op, "sampled deviced pointer chain changed")
            require(values[6][0] <= 6, "invalid power index")
            require(values[7][1:] == [ec, et, ea] and
                    [values[9][0], values[10][0], values[11][0]] == [ecv, etv, eav],
                    "sampled deviced child/vptr chain changed")
            qd.append((up, values))
        else:
            raise ValueError("unknown sample row")
    require(len(monitor) >= int(seconds * 3.5), "insufficient monitor sampling")
    require(len(qd) >= int(seconds * .7), "insufficient one-Hz sampling")
    require(all(b[0] > a_[0] and b[0] - a_[0] <= 1.0 for a_, b in zip(monitor, monitor[1:])),
            "monitor sample gap")
    require(all(b[0] > a_[0] and b[0] - a_[0] <= 2.0 for a_, b in zip(qd, qd[1:])),
            "QD sample gap")
    require(monitor[0][0] - meta["trace_start"] <= .6 and
            meta["trace_end"] - monitor[-1][0] <= .8 and
            qd[0][0] - meta["trace_start"] <= 1.2 and
            meta["trace_end"] - qd[-1][0] <= 1.6,
            "sample endpoint coverage incomplete")
    monitor_span = monitor[-1][0] - monitor[0][0]
    qd_span = qd[-1][0] - qd[0][0]
    return {"monitor_rows": len(monitor), "qd_rows": len(qd),
            "monitor_window": [monitor[0][0], monitor[-1][0]],
            "qd_window": [qd[0][0], qd[-1][0]],
            "monitor_span_seconds": monitor_span, "qd_span_seconds": qd_span,
            "monitor_rate_hz": (len(monitor) - 1) / monitor_span,
            "qd_rate_hz": (len(qd) - 1) / qd_span,
            "leading_gaps_seconds": {"monitor": monitor[0][0] - meta["trace_start"],
                                     "qd": qd[0][0] - meta["trace_start"]},
            "trailing_gaps_seconds": {"monitor": meta["trace_end"] - monitor[-1][0],
                                      "qd": meta["trace_end"] - qd[-1][0]},
            "qualification": "userspace raw fields only; no kernel gate or emitted-light state inferred"}


def validate_dd_summaries(text: str, monitor_rows: int, qd_rows: int) -> dict:
    lines = [line for line in text.splitlines() if line]
    require(lines and len(lines) % 3 == 0, "unexpected sampler stderr shape")
    counts: dict[int, int] = {}
    for index in range(0, len(lines), 3):
        incoming = re.fullmatch(r"([0-9]+)\+([0-9]+) records in", lines[index])
        outgoing = re.fullmatch(r"([0-9]+)\+([0-9]+) records out", lines[index + 1])
        copied = re.fullmatch(
            r"([0-9]+) bytes \([^()]+\) copied, [0-9.e+-]+ s, [0-9.]+ [kMGT]?B/s",
            lines[index + 2])
        require(incoming is not None and outgoing is not None and copied is not None,
                "unexpected sampler stderr diagnostic")
        require(incoming.groups() == outgoing.groups() and incoming.group(2) == "0" and
                int(copied.group(1)) == int(incoming.group(1)) * 4,
                "incomplete sampler dd summary")
        count = int(incoming.group(1))
        require(count in {1, 2, 4, 6, 38}, "unexpected sampler dd record count")
        counts[count] = counts.get(count, 0) + 1
    expected = {1: 33 + 8 * qd_rows, 2: 2 * qd_rows, 4: qd_rows,
                6: qd_rows, 38: monitor_rows}
    require(counts == expected, "sampler dd operation inventory mismatch")
    return {"dd_operations": sum(counts.values()), "record_counts": counts,
            "only_complete_success_summaries": True}


def parse_fds(text: str) -> dict:
    part = sections(text)
    require(set(part) == {"TIDS_START", "FDS_START", "TIDS_PRE", "TIDS_ARM",
                          "TIDS_END", "FDS_END"},
            "unexpected TID/FD sections")
    tids0 = [int(x) for x in part["TIDS_START"].splitlines()]
    tids_pre = [int(x) for x in part["TIDS_PRE"].splitlines()]
    tids_arm = [int(x) for x in part["TIDS_ARM"].splitlines()]
    tids1 = [int(x) for x in part["TIDS_END"].splitlines()]
    require(tids0 and len(tids0) == len(set(tids0)) and tids0 == sorted(tids0),
            "invalid starting TID set")
    require(tids_pre == tids0 and tids_arm == tids0 and tids1 == tids0,
            "AVOC TID set changed before/during capture")
    def fdmap(value: str) -> dict[int, str]:
        result = {}
        for line in value.splitlines():
            number, sep, target = line.partition(" ")
            require(sep and number.isdigit() and int(number) not in result and target,
                    "malformed FD target row")
            result[int(number)] = target
        return result
    f0, f1 = fdmap(part["FDS_START"]), fdmap(part["FDS_END"])
    changes = {str(fd): {"start": f0.get(fd), "end": f1.get(fd)}
               for fd in sorted(set(f0) | set(f1)) if f0.get(fd) != f1.get(fd)}
    return {"tids": tids0, "pre_tids": tids_pre, "armed_tids": tids_arm,
            "fd_changes": changes,
            "fd_targets_stable": not changes,
            "qualification": "TIDs are equal before setup, immediately after tracing starts, and at end; FD changes/reuse are reported and targets are not assumed stable."}


def validate_trace_scope(meta: dict, fd_report: dict) -> None:
    require(meta["trace_filter_tids"] == fd_report["pre_tids"] and
            meta["trace_filter"] == syscall_filter_for_tids(fd_report["pre_tids"]),
            "scoped ARM32 ioctl54 completeness filter mismatch")


def trace_accounting(data: bytes, tids: list[int], avoc_pid: int, collector_pid: int,
                     expected_start: float, expected_end: float) -> dict:
    text = data.decode("utf-8", errors="strict")
    match = re.search(r"entries-in-buffer/entries-written:\s*(\d+)/(\d+)", text)
    require(match is not None, "missing trace accounting")
    retained, written = map(int, match.groups())
    require(retained == written, "trace ring overflow")
    event_re = re.compile(
        r"^\s*(?P<task>.+?)-(?P<pid>\d+)\s+\((?P<tgid>[^)]*)\)\s+\[\d+\]\s+\S+\s+"
        r"(?P<time>\d+\.\d+): (?P<event>\w+): (?P<body>.*)$")
    message_re = re.compile(
        r"i2c-(\d+) #(\d+) a=([0-9a-f]+) f=([0-9a-f]+) l=(\d+)"
        r"(?: \[([0-9a-f-]*)\])?$", re.I)
    result_re = re.compile(r"i2c-(\d+) n=(\d+) ret=(-?\d+)$")
    events = []
    malformed = []
    markers = []
    for number, line in enumerate(text.splitlines(), 1):
        event = event_re.match(line)
        if not event:
            continue
        raw_tgid = event["tgid"].strip()
        item = {"line": number, "time": float(event["time"]), "pid": int(event["pid"]),
                "tgid": int(raw_tgid) if raw_tgid.isdigit() else None,
                "event": event["event"], "body": event["body"]}
        events.append(item)
        grammar = result_re if event["event"] == "i2c_result" else (
            message_re if event["event"] in {"i2c_write", "i2c_read", "i2c_reply"} else None)
        if grammar is not None and grammar.fullmatch(event["body"]) is None:
            malformed.append(number)
        if event["event"] in {"i2c_write", "i2c_read", "i2c_reply"} and grammar is not None:
            item = grammar.fullmatch(event["body"])
            if item and (int(item.group(1)) != 5 or int(item.group(3), 16) != 0x76):
                malformed.append(number)
            if item:
                payload = item.group(6)
                declared = int(item.group(5))
                tokens = [] if payload == "" else (payload.split("-") if payload is not None else [])
                if ((event["event"] in {"i2c_write", "i2c_reply"} and payload is None) or
                        (payload is not None and
                         (len(tokens) != declared or
                          any(re.fullmatch(r"[0-9a-f]{2}", token, re.I) is None
                              for token in tokens)))):
                    malformed.append(number)
        if event["event"] == "i2c_result" and grammar is not None:
            item = grammar.fullmatch(event["body"])
            if item and int(item.group(1)) != 5:
                malformed.append(number)
        if event["body"].startswith("CAPTURE_"):
            require(event["event"] == "tracing_mark_write" or
                    re.fullmatch(r"0x[0-9a-f]+", event["event"], re.I) is not None,
                    "capture marker has unexpected trace event source")
            marker = re.fullmatch(r"CAPTURE_(START|END) utc=([0-9]+) uptime=([0-9]+\.[0-9]+)",
                                  event["body"])
            require(marker is not None and item["pid"] == collector_pid and
                    item["tgid"] == collector_pid,
                    "malformed capture trace marker or collector identity")
            markers.append((marker.group(1), item["line"], item["time"],
                            int(marker.group(2)), float(marker.group(3)), event["event"]))
    observed = len(events)
    require(observed == retained, "trace decode count incomplete")
    require(all(b["time"] >= a["time"] for a, b in zip(events, events[1:])),
            "trace event timestamps out of order")
    require(not malformed, "malformed I2C trace events")
    require(len(markers) == 2 and [x[0] for x in markers] == ["START", "END"],
            "missing/duplicate/reversed exact trace markers")
    require(markers[0][5] == markers[1][5], "capture marker trace sources differ")
    for _kind, _line, event_time, _utc, body_uptime, _source in markers:
        require(abs(event_time - body_uptime) <= .1, "trace marker clock mismatch")
    require(abs(markers[0][4] - expected_start) <= .1 and
            abs(markers[1][4] - expected_end) <= .1 and markers[0][1] < markers[1][1] and
            markers[0][2] < markers[1][2],
            "trace marker window mismatch")
    first_line, last_line = markers[0][1], markers[1][1]
    pending: dict[int, dict] = {}
    all_pairs = []
    unmatched = []
    inside = lambda item: first_line < item["line"] < last_line
    for event in events:
        if event["event"] not in {"sys_enter", "sys_exit"}:
            continue
        pid = event["pid"]
        require(event["tgid"] is not None, "ioctl event lacks numeric saved TGID")
        if inside(event):
            require(event["tgid"] == avoc_pid and pid in tids,
                    "in-window syscall row has unrelated saved-TGID/PID")
        if event["event"] == "sys_enter":
            syscall = re.fullmatch(r"NR (\d+) \((.*)\)", event["body"])
            require(syscall is not None and int(syscall.group(1)) == 54,
                    "unexpected syscall enter")
            if pid in pending:
                prior = pending.pop(pid)
                require(not ((inside(prior) or inside(event)) and
                             (prior["tgid"] == avoc_pid or event["tgid"] == avoc_pid)),
                        "duplicate AVOC ioctl enter overlapping capture window")
                unmatched.append({"kind": "duplicate-enter", "tid": pid,
                                  "saved_tgid": prior["tgid"], "line": prior["line"],
                                  "inside_capture_window": inside(prior)})
            pending[pid] = event
        else:
            syscall = re.fullmatch(r"NR (\d+) = (-?[0-9]+)", event["body"])
            require(syscall is not None and int(syscall.group(1)) == 54,
                    "unexpected syscall exit")
            if pid not in pending:
                require(not (inside(event) and event["tgid"] == avoc_pid),
                        "orphan AVOC ioctl exit inside capture window")
                unmatched.append({"kind": "orphan-exit", "tid": pid,
                                  "saved_tgid": event["tgid"], "line": event["line"],
                                  "inside_capture_window": inside(event)})
                continue
            begin = pending.pop(pid)
            if begin["tgid"] != event["tgid"]:
                require(not ((inside(begin) or inside(event)) and
                             (begin["tgid"] == avoc_pid or event["tgid"] == avoc_pid)),
                        "AVOC ioctl pair TGID changed across capture window")
                unmatched.append({"kind": "tgid-change", "tid": pid,
                                  "saved_tgid": begin["tgid"], "line": begin["line"],
                                  "inside_capture_window": inside(begin) or inside(event)})
                continue
            require(begin["time"] <= event["time"], "reversed ioctl pair")
            begin_inside = inside(begin)
            end_inside = inside(event)
            require(not (begin["tgid"] == avoc_pid and begin_inside != end_inside),
                    "AVOC ioctl pair crosses capture marker")
            all_pairs.append({"tid": pid, "saved_tgid": begin["tgid"],
                              "avoc_tgid": begin["tgid"] == avoc_pid,
                              "enter_line": begin["line"],
                              "exit_line": event["line"], "start": begin["time"],
                              "end": event["time"], "return": int(syscall.group(2)),
                              "inside_capture_window": begin_inside and end_inside,
                              "crosses_capture_marker": begin_inside != end_inside})
    for pid, begin in pending.items():
        require(not (inside(begin) and begin["tgid"] == avoc_pid),
                "unclosed AVOC ioctl enter inside capture window")
        unmatched.append({"kind": "unclosed-enter", "tid": pid,
                          "saved_tgid": begin["tgid"], "line": begin["line"],
                          "inside_capture_window": inside(begin)})
    pairs = [item for item in all_pairs
             if item["inside_capture_window"] and item["avoc_tgid"]]
    unrelated = [item for item in all_pairs
                 if item["inside_capture_window"] and not item["avoc_tgid"]]
    window_events = [event for event in events if first_line < event["line"] < last_line]
    avoc_forks = []
    avoc_exits = []
    for event in events:
        if event["event"] == "sched_process_fork":
            fork = re.fullmatch(r"comm=.* pid=(\d+) child_comm=.* child_pid=(\d+)", event["body"])
            require(fork is not None, "malformed sched_process_fork event")
            if int(fork.group(1)) in tids:
                avoc_forks.append({"line": event["line"], "parent_tid": int(fork.group(1)),
                                   "child_tid": int(fork.group(2)), "time": event["time"],
                                   "inside_capture_window": first_line < event["line"] < last_line})
        elif event["event"] == "sched_process_exit" and event["pid"] in tids:
            exited = re.fullmatch(r"comm=.* pid=(\d+) prio=(-?\d+)", event["body"])
            require(exited is not None and int(exited.group(1)) == event["pid"],
                    "malformed AVOC sched_process_exit event")
            avoc_exits.append({"line": event["line"], "tid": event["pid"],
                               "time": event["time"],
                               "inside_capture_window": first_line < event["line"] < last_line})
    require(not avoc_forks and not avoc_exits,
            "AVOC thread lifecycle changed after tracing armed")
    require(all(not (item["avoc_tgid"] and item["inside_capture_window"]) or
                item["tid"] in tids for item in all_pairs),
            "unresolved AVOC saved-TGID lifecycle")
    require(not unrelated, "scoped syscall filter contains unrelated saved-TGID rows")
    unrelated_by_tgid: dict[str, int] = {}
    for item in unrelated:
        key = str(item["saved_tgid"])
        unrelated_by_tgid[key] = unrelated_by_tgid.get(key, 0) + 1
    window_i2c_by_event = {name: sum(event["event"] == name for event in window_events)
                           for name in ("i2c_write", "i2c_read", "i2c_reply", "i2c_result")}
    window_i2c = sum(window_i2c_by_event.values())
    return {"retained": retained, "written": written, "ring_complete": True,
            "decoded_event_lines": observed, "i2c_parse_errors": malformed,
            "capture_window_event_lines": len(window_events),
            "capture_window_i2c_raw_lines": window_i2c,
            "capture_window_i2c_raw_lines_by_event": window_i2c_by_event,
            "excluded_event_lines": observed - len(window_events) - 2,
            "markers": [{"kind": x[0], "line": x[1], "trace_time": x[2],
                        "utc": x[3], "uptime": x[4], "trace_source": x[5]}
                        for x in markers], "ioctl_pairs": pairs,
            "unrelated_syscall54_pairs": len(unrelated),
            "unrelated_syscall54_pairs_by_saved_tgid": unrelated_by_tgid,
            "boundary_unmatched_syscall54_rows": unmatched,
            "excluded_ioctl_pairs": sum(not item["inside_capture_window"] for item in all_pairs),
            "total_ioctl_pairs": len(all_pairs), "avoc_forks": avoc_forks,
            "avoc_exits": avoc_exits,
            "qualification": "Syscall54 tracing is limited to the identical validated AVOC START/PRE/ARM/END TID set; every traced fork/exit involving that set rejects the run, closing pre-marker lifecycle races. Any unrelated saved-TGID row is retained as PID-reuse ambiguity. I2C values are syntax-checked raw line inventory only: adapter-5 i2c_result rows are not address-attributed or grouped with messages, so no complete transfer, MCU acknowledgement, acceptance, or physical effect is claimed. Only complete AVOC pairs strictly between exact collector markers are classified; tracepoint absence covers enabled Linux APIs only."}


def vlog_coverage(data: bytes, start: float, end: float, margin: float = 1.0,
                  source_exit_code: int = 0, forced_termination: bool = False) -> dict:
    text = data.decode("utf-8", errors="replace")
    stamps = [float(x) for x in re.findall(r":\s+([0-9]+\.[0-9]{3,})\s+[A-Z]/", text)]
    if not stamps:
        return {"complete": False, "reason": "no recognized kerneltime timestamps",
                "source_exit_code": source_exit_code,
                "terminated_naturally": not forced_termination and source_exit_code == 0,
                "absence_claim_supported": False}
    require(all(math.isfinite(x) for x in stamps), "non-finite vlog timestamp")
    ordered = all(b >= a for a, b in zip(stamps, stamps[1:]))
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    max_gap = max(gaps, default=0.0)
    endpoint = stamps[0] <= start - margin and stamps[-1] >= end + margin
    natural = not forced_termination and source_exit_code == 0
    complete = endpoint and ordered and max_gap <= 2.0 and natural
    return {"complete": complete, "records": len(stamps), "first": min(stamps), "last": max(stamps),
            "required": [start - margin, end + margin],
            "ordered": ordered, "max_gap_seconds": max_gap, "endpoint_coverage": endpoint,
            "source_exit_code": source_exit_code, "terminated_naturally": natural,
            "absence_claim_supported": False,
            "qualification": "Endpoint/order/gap assessment only; generic log absence is never established."}


def vlog_markers(data: bytes) -> dict:
    """Index decision-relevant raw lines without interpreting their meaning."""
    patterns = {
        "off_sensing": re.compile(r"off[._ -]?sensing", re.I),
        "notification": re.compile(r"show_qd_display|NOTIFICATION_QD|1 min timeout|cancel_reinforce", re.I),
        "request": re.compile(r"RequestQdDisplayOffSensing", re.I),
        "qdf_gate": re.compile(r"qd command skip|command.skip|Set Suspend Flag|tcon state", re.I),
        "monitor": re.compile(r"ERR_DET|recovery|terminal.action", re.I),
        "mute_or_maintenance": re.compile(r"panel.?mute|EL[._ -]?sensing|F3[: ]0?(?:180|1a0)", re.I),
    }
    text = data.decode("utf-8", errors="replace")
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        tags = [name for name, pattern in patterns.items() if pattern.search(line)]
        if tags:
            stamp = re.search(r":\s*([0-9]+\.[0-9]+)\s+[VDIWEF]/", line)
            rows.append({"line": number, "kerneltime": float(stamp.group(1)) if stamp else None,
                         "tags": tags, "text": line})
    return {"matches": rows, "count": len(rows),
            "qualification": "raw source-line index only; ordering is preserved and no physical cause is inferred"}


def parse_manifest(stdout: str) -> dict[str, tuple[int, str]]:
    rows = {}
    lines = stdout.splitlines()
    require(lines and lines[-1] == "CAPTURE_COMPLETE", "capture completion missing")
    for line in lines[:-1]:
        match = re.fullmatch(r"SIDECAR ([a-z-]+) ([0-9]+) ([0-9a-f]{64})", line)
        require(match is not None, "unexpected capture output")
        name, size, digest = match.groups()
        require(name in SIDECAR_LIMITS and name not in rows, "unexpected/duplicate sidecar")
        size_i = int(size)
        require(0 <= size_i <= SIDECAR_LIMITS[name], "sidecar size limit")
        rows[name] = (size_i, digest)
    require(set(rows) == set(SIDECAR_LIMITS), "missing sidecar")
    require(rows["trace"][0] > 0 and rows["meta"][0] > 0 and rows["samples"][0] > 0,
            "empty required sidecar")
    return rows


def verify_sidecars(data: dict[str, bytes], manifest: dict[str, tuple[int, str]]) -> None:
    require(set(data) == set(manifest), "sidecar set mismatch")
    for name, body in data.items():
        size, digest = manifest[name]
        require(len(body) == size, name + " length mismatch")
        require(hashlib.sha256(body).hexdigest() == digest, name + " hash mismatch")


def parse_annotation(line: str, when: dt.datetime | None = None,
                     monotonic_ns: int | None = None) -> dict:
    fields = shlex.split(line)
    require(bool(fields), "empty annotation")
    dimensions = {
        "apps": {"visible", "not-visible", "unknown"},
        "warning": {"visible", "not-visible", "unknown"},
        "picture": {"visible", "black", "unknown"},
        "audio": {"present", "absent", "unknown"},
    }
    if fields[0] == "note":
        require(len(fields) >= 2, "empty observer note")
        dimension, value, rest = "note", " ".join(fields[1:]), []
    else:
        require(len(fields) >= 2 and fields[0] in dimensions and fields[1] in dimensions[fields[0]],
                "invalid observer annotation")
        dimension, value, rest = fields[0], fields[1], fields[2:]
    reaction = clock = None
    for item in rest:
        key, sep, raw = item.partition("=")
        require(sep == "=" and key in {"reaction_ms", "clock_ms"} and raw.isdigit(),
                "invalid uncertainty field")
        require(int(raw) <= 60000, "uncertainty out of bounds")
        if key == "reaction_ms": reaction = int(raw)
        else: clock = int(raw)
    now = when or dt.datetime.now(dt.timezone.utc)
    return {"host_utc": now.isoformat(), "host_monotonic_ns": monotonic_ns or time.monotonic_ns(),
            "dimension": dimension, "value": value,
            "reaction_uncertainty_ms": reaction, "host_clock_uncertainty_ms": clock,
            "source": "local human observer annotation",
            "not_inferred_from": ["PNG", "getter", "userspace memory", "trace"]}


def annotation_summary(rows: list[dict]) -> dict:
    values: dict[str, set[str]] = {}
    for row in rows:
        if row["dimension"] != "note" and row["value"] != "unknown":
            values.setdefault(row["dimension"], set()).add(row["value"])
    ambiguous = {key: sorted(value) for key, value in values.items() if len(value) > 1}
    return {"count": len(rows), "ambiguous_dimensions": ambiguous,
            "physical_state": "unobserved" if not rows else "observer-timeline-only",
            "qualification": "No single physical label is inferred; ordering and uncertainty are retained."}


def assess_annotations(rows: list[dict], sync: dict, meta: dict | None,
                       smoke_unobserved: bool) -> dict:
    mapped_rows = []
    for row in rows:
        item = dict(row)
        host_epoch = dt.datetime.fromisoformat(row["host_utc"]).timestamp()
        utc_estimate = sync["tv_uptime"] + host_epoch - sync["host_midpoint_utc"]
        monotonic_estimate = (sync["tv_uptime"] + row["host_monotonic_ns"] / 1e9 -
                              sync["host_midpoint_monotonic"])
        mapping_disagreement = abs(utc_estimate - monotonic_estimate)
        estimate = monotonic_estimate
        reaction = row.get("reaction_uncertainty_ms")
        clock = row.get("host_clock_uncertainty_ms")
        uncertainty = sync["mapping_uncertainty_seconds"] + mapping_disagreement
        if reaction is not None:
            uncertainty += reaction / 1000
        if clock is not None:
            uncertainty += clock / 1000
        item.update({"estimated_tv_uptime": estimate,
                     "utc_based_tv_uptime": utc_estimate,
                     "monotonic_based_tv_uptime": monotonic_estimate,
                     "clock_mapping_disagreement_seconds": mapping_disagreement,
                     "total_uncertainty_seconds": uncertainty,
                     "tv_uptime_interval": [estimate - uncertainty, estimate + uncertainty],
                     "uncertainty_complete": reaction is not None and clock is not None})
        if meta is not None:
            item["entirely_in_trace_window"] = (
                item["tv_uptime_interval"][0] >= meta["trace_start"] and
                item["tv_uptime_interval"][1] <= meta["trace_end"])
        else:
            item["entirely_in_trace_window"] = False
        mapped_rows.append(item)
    transition = None
    if not smoke_unobserved and meta is not None:
        visible = [x for x in mapped_rows if x["dimension"] == "picture" and
                   x["value"] == "visible" and x["uncertainty_complete"] and
                   x["entirely_in_trace_window"]]
        black = [x for x in mapped_rows if x["dimension"] == "picture" and
                 x["value"] == "black" and x["uncertainty_complete"] and
                 x["entirely_in_trace_window"]]
        for before in visible:
            for after in black:
                if before["tv_uptime_interval"][1] < after["tv_uptime_interval"][0]:
                    transition = {"visible": before, "black": after}
                    break
            if transition:
                break
    eligible = transition is not None
    return {"rows": mapped_rows, "count": len(rows),
            "ordered_visible_to_black": transition,
            "diagnostic_onset_eligible": eligible,
            "physical_state": "observer-reported-visible-to-black" if eligible else "unobserved-or-incomplete",
            "qualification": "Eligibility requires ordered, wholly in-window human picture annotations with both reaction and clock uncertainty; software is never a physical label source."}


def private_text(path: Path, value: str) -> None:
    path.write_text(value)
    path.chmod(0o600)


def root(command: str, timeout: int, audit_prefix: Path | None = None
         ) -> tuple[subprocess.CompletedProcess, dict]:
    require(len(command.encode()) <= 8192, "root command exceeds controller limit")
    proc = subprocess.run(["python3", str(ACCESS), "root", "--persistent-only",
                           "--timeout", str(timeout), "--command", command],
                          text=True, capture_output=True, timeout=timeout + 30)
    if audit_prefix is not None:
        private_text(audit_prefix.with_name(audit_prefix.name + "-root-response.json"), proc.stdout)
        private_text(audit_prefix.with_name(audit_prefix.name + "-client-stderr.txt"), proc.stderr)
    try:
        response = json.loads(proc.stdout)
        require(response.get("authenticated") is True and response.get("uid") == 0 and
                response.get("euid") == 0 and response.get("model") == MODEL,
                "unexpected root/model identity")
        require(response.get("root_persistence") == "host-assisted" and
                response.get("global_system_files_unchanged_at_acquisition") is True,
                "unexpected root access path")
        require(len(response.get("commands", [])) == 1, "unexpected command count")
        item = response["commands"][0]
    except (ValueError, KeyError, IndexError) as exc:
        raise RuntimeError("root response unavailable; no automatic retry") from exc
    if audit_prefix is not None:
        private_text(audit_prefix.with_name(audit_prefix.name + "-remote-stdout.txt"),
                     str(item.get("stdout", "")))
        private_text(audit_prefix.with_name(audit_prefix.name + "-remote-stderr.txt"),
                     str(item.get("stderr", "")))
    return proc, item


def stage_script(label: str, script: bytes) -> dict:
    stage = f"{STAGE_ROOT}/{label}"
    path = stage + "/capture.sh"
    prep = (f"set -eu\numask 077\nSD={stage}\nP={STAGE_ROOT}\n"
            f"if test -e \"$P\"; then test ! -L \"$P\"; test -d \"$P\"; test \"$(stat -c '%u:%a' \"$P\")\" = 0:700; else mkdir -m 700 \"$P\"; fi\n"
            f"test ! -e \"$SD\"\nmkdir -m 700 \"$SD\"\n"
            f": >\"$SD/capture.sh\"\nchmod 600 \"$SD/capture.sh\"\n"
            f"closefds() {{ for f in /proc/self/fd/*; do n=${{f##*/}}; case \"$n\" in 0|1|2) ;; *) eval \"exec $n>&-\" 2>/dev/null || true;; esac; done; }}\n"
            f"(closefds; exec /usr/bin/setsid /bin/sh -c 'sleep 900; "
            f"rm -f {path} {stage}/expiry.pid {stage}/expiry.log; rmdir {stage}' "
            f") >{stage}/expiry.log 2>&1 </dev/null &\np=$!\ns=$(awk '{{print $22}}' /proc/$p/stat)\ncase \"$s\" in ''|*[!0-9]*) exit 40;; esac\n"
            f"ready=0\nfor i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$p/stat 2>/dev/null); test \"${{4:-}}\" = \"$s\" || break; test \"${{1:-}}\" != Z || break; if test \"${{2:-}}\" = \"$p\" && test \"${{3:-}}\" = \"$p\"; then ready=1; break; fi; sleep .05; done\n"
            f"if test \"$ready\" != 1; then grouped=0; set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$p/stat 2>/dev/null); if test \"${{4:-}}\" = \"$s\" && test \"${{1:-}}\" != Z; then if test \"${{2:-}}\" = \"$p\" && test \"${{3:-}}\" = \"$p\"; then grouped=1; kill -KILL -\"$p\" 2>/dev/null || true; else kill -KILL \"$p\" 2>/dev/null || true; fi; fi; for i in 1 2 3 4 5 6 7 8 9 10; do set -- $(awk '{{print $3,$22}}' /proc/$p/stat 2>/dev/null); test \"${{2:-}}\" = \"$s\" && test \"${{1:-}}\" != Z || break; sleep .05; done; set -- $(awk '{{print $3,$22}}' /proc/$p/stat 2>/dev/null); test \"${{2:-}}\" != \"$s\" || test \"${{1:-}}\" = Z || exit 42; test \"$grouped\" != 1 || ! kill -0 -\"$p\" 2>/dev/null || exit 42; exit 41; fi\n"
            f"echo \"$p $s\" >{stage}/expiry.pid\nchmod 600 {stage}/expiry.pid\nkill -0 -\"$p\"")
    proc, item = root(prep, 25)
    require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
            "stage preparation failed")
    chunks = 0
    for offset in range(0, len(script), 4096):
        encoded = base64.b64encode(script[offset:offset + 4096]).decode()
        command = f"set -eu\nprintf %s {encoded} | base64 -d >>{path}"
        require(len(command.encode()) <= 8192, "staging chunk command exceeds controller limit")
        proc, item = root(command, 25)
        require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
                "staging chunk failed; no retry")
        chunks += 1
    digest = hashlib.sha256(script).hexdigest()
    verify = f"set -eu\nwc -c {path}\nsha256sum {path}"
    proc, item = root(verify, 25)
    require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
            "staged script verification failed")
    rows = item["stdout"].splitlines()
    require(len(rows) == 2 and int(rows[0].split()[0]) == len(script) and
            rows[1].split()[0] == digest, "staged script size/hash mismatch")
    return {"path": path, "bytes": len(script), "sha256": digest, "chunks": chunks,
            "persistent_only": True, "expiry_seconds": 900}


def acquire_sync() -> dict:
    before_utc, before_mono = time.time(), time.monotonic()
    proc, item = root("set -eu\ndate -u +%s\ncat /proc/uptime", 25)
    after_mono, after_utc = time.monotonic(), time.time()
    require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
            "pre-capture synchronization failed")
    rows = item["stdout"].splitlines()
    require(len(rows) == 2 and rows[0].isdigit(), "malformed synchronization response")
    tv_utc, tv_uptime = int(rows[0]), float(rows[1].split()[0])
    require(math.isfinite(tv_uptime), "non-finite TV uptime")
    rtt = after_mono - before_mono
    require(0 <= rtt <= 2.0, "pre-capture synchronization RTT exceeds bounded schedule")
    lead = 12
    midpoint_utc = (before_utc + after_utc) / 2
    midpoint_mono = (before_mono + after_mono) / 2
    return {"tv_utc": tv_utc, "tv_uptime": tv_uptime, "target_uptime": tv_uptime + lead,
            "host_midpoint_utc": midpoint_utc, "host_before_utc": before_utc,
            "host_after_utc": after_utc, "host_midpoint_monotonic": midpoint_mono,
            "round_trip_seconds": rtt,
            "mapping_uncertainty_seconds": rtt + 1.0,
            "estimated_target_host_utc": midpoint_utc + lead,
            "estimated_target_host_monotonic": midpoint_mono + lead,
            "qualification": "TV date has integer-second granularity; uncertainty includes full RTT plus 1s."}


def launch_collector(label: str, stage: dict, target_uptime: float,
                     audit_directory: Path | None = None) -> dict:
    sd = f"{STAGE_ROOT}/{label}"
    command = (f'''set -eu
umask 077
SD={sd}; P=$SD/collector.pid; OUT=$SD/collector.stdout; ERR=$SD/collector.stderr
test ! -L "$SD"; test -d "$SD"; test "$(stat -c '%u:%a' "$SD")" = 0:700
test ! -L {stage["path"]}; test -f {stage["path"]}; test "$(stat -c '%u:%a' {stage["path"]})" = 0:600
test ! -e "$P"; test ! -e "$OUT"; test ! -e "$ERR"
test "$(wc -c <{stage["path"]})" = {stage["bytes"]}
test "$(sha256sum {stage["path"]}|cut -d' ' -f1)" = {stage["sha256"]}
closefds() {{ for f in /proc/self/fd/*; do n=${{f##*/}}; case "$n" in 0|1|2) ;; *) eval "exec $n>&-" 2>/dev/null || true;; esac; done; }}
(ulimit -Sf 64; closefds; exec /usr/bin/setsid /bin/sh -c "$(cat {stage["path"]})" -- {target_uptime:.3f}) >"$OUT" 2>"$ERR" </dev/null &
p=$!; s=$(awk '{{print $22}}' /proc/$p/stat); case "$s" in ''|*[!0-9]*) exit 40;; esac; ready=0
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$p/stat 2>/dev/null); test "${{4:-}}" = "$s" || break; test "${{1:-}}" != Z || break; if test "${{2:-}}" = "$p" && test "${{3:-}}" = "$p"; then ready=1; break; fi; sleep .05; done
if test "$ready" != 1; then grouped=0; set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$p/stat 2>/dev/null); if test "${{4:-}}" = "$s" && test "${{1:-}}" != Z; then if test "${{2:-}}" = "$p" && test "${{3:-}}" = "$p"; then grouped=1; kill -KILL -"$p" 2>/dev/null || true; else kill -KILL "$p" 2>/dev/null || true; fi; fi; for i in 1 2 3 4 5 6 7 8 9 10; do set -- $(awk '{{print $3,$22}}' /proc/$p/stat 2>/dev/null); test "${{2:-}}" = "$s" && test "${{1:-}}" != Z || break; sleep .05; done; set -- $(awk '{{print $3,$22}}' /proc/$p/stat 2>/dev/null); test "${{2:-}}" != "$s" || test "${{1:-}}" = Z || exit 42; test "$grouped" != 1 || ! kill -0 -"$p" 2>/dev/null || exit 42; exit 41; fi
echo "$p $s" >"$P"; chmod 600 "$P"; sleep .2
set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$p/stat); test "${{4:-}}" = "$s"; test "${{1:-}}" != Z; test "${{2:-}}" = "$p"; test "${{3:-}}" = "$p"
echo "$p $s $2 $3"''')
    if audit_directory is None:
        proc, item = root(command, 25)
    else:
        proc, item = root(command, 25, audit_directory / "launch")
    require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
            "detached collector launch failed; no retry")
    rows = item["stdout"].splitlines()
    require(len(rows) == 1 and re.fullmatch(r"[1-9][0-9]*(?: [1-9][0-9]*){3}", rows[0]) is not None,
            "collector PID/start identity unavailable")
    pid, start, pgrp, session = map(int, rows[0].split())
    require(pid == pgrp == session, "collector process-group/session identity mismatch")
    return {"pid": pid, "start_ticks": start, "process_group": pid,
            "launch_timeout_seconds": 25, "controller_gate_released": True,
            "target_uptime": target_uptime}


def collector_running(label: str, identity: dict) -> bool:
    sd = f"{STAGE_ROOT}/{label}"
    command = (f'''set -eu
test ! -L {sd}; test -d {sd}; test "$(stat -c '%u:%a' {sd})" = 0:700
test ! -L {sd}/collector.pid; test -f {sd}/collector.pid; test "$(stat -c '%u:%a' {sd}/collector.pid)" = 0:600
read p s <{sd}/collector.pid
test "$p" = {identity["pid"]}; test "$s" = {identity["start_ticks"]}
set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$p/stat 2>/dev/null)
if test "${{4:-}}" = "$s" && test "${{1:-}}" != Z && test "${{2:-}}" = "$p" && test "${{3:-}}" = "$p"; then echo RUNNING; else echo EXITED; fi''')
    proc, item = root(command, 10)
    require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
            "collector status unavailable; no retry")
    require(item["stdout"].splitlines() in (["RUNNING"], ["EXITED"]),
            "unexpected collector status")
    return item["stdout"].splitlines() == ["RUNNING"]


def fetch_collector_transport(label: str, destination: Path) -> str:
    sd = f"{STAGE_ROOT}/{label}"
    command = (f'''set -eu
for n in stdout stderr; do f={sd}/collector.$n; set -- $(wc -c "$f") $(sha256sum "$f"); test "$1" -le 65536; echo "$n $1 $3"; done''')
    proc, item = root(command, 15)
    require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
            "collector transport inventory failed")
    bodies = {}
    for row in item["stdout"].splitlines():
        match = re.fullmatch(r"(stdout|stderr) ([0-9]+) ([0-9a-f]{64})", row)
        require(match is not None and match.group(1) not in bodies,
                "malformed collector transport inventory")
        name, raw_size, digest = match.groups()
        bodies[name] = fetch_file(f"{sd}/collector.{name}", int(raw_size), digest)
        (destination / f"collector.{name}").write_bytes(bodies[name])
    require(set(bodies) == {"stdout", "stderr"}, "collector transport files missing")
    require(not bodies["stderr"], "collector emitted unexpected stderr")
    return bodies["stdout"].decode("utf-8", errors="strict")


def fetch_file(path: str, size: int, digest: str) -> bytes:
    chunks = []
    for index in range((size + CHUNK - 1) // CHUNK):
        command = f"dd if={path} bs={CHUNK} skip={index} count=1 2>/dev/null | base64"
        proc, item = root(command, 25)
        require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
                "sidecar transfer failed; no retry")
        chunks.append(base64.b64decode("".join(item["stdout"].split()), validate=True))
    body = b"".join(chunks)
    require(len(body) == size and hashlib.sha256(body).hexdigest() == digest,
            "sidecar transfer integrity failure")
    return body


def salvage_partial(label: str, destination: Path) -> dict:
    """Make one bounded read-only attempt to retain existing incomplete sidecars."""
    remote = f"{REMOTE_ROOT}/{label}"
    command = f'''set +e
O={remote}
for n in trace meta samples sample-errors vlog-after artifacts fds; do
 test "$n" = trace && f="$O/trace" || f="$O/$n.txt"
 if test -f "$f"; then set -- $(wc -c "$f") $(sha256sum "$f"); echo "PARTIAL $n $1 $3"; fi
done
for n in stdout stderr; do f={STAGE_ROOT}/{label}/collector.$n; if test -f "$f"; then set -- $(wc -c "$f") $(sha256sum "$f"); echo "TRANSPORT $n $1 $3"; fi; done'''
    proc, item = root(command, 30)
    require(proc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"],
            "partial inventory unavailable")
    report, transport = {}, {}
    for line in item["stdout"].splitlines():
        match = re.fullmatch(r"PARTIAL ([a-z-]+) ([0-9]+) ([0-9a-f]{64})", line)
        if match is None:
            wire = re.fullmatch(r"TRANSPORT (stdout|stderr) ([0-9]+) ([0-9a-f]{64})", line)
            require(wire is not None, "malformed partial inventory")
            name, raw_size, digest = wire.groups()
            size = int(raw_size)
            require(size <= 65536 and name not in transport, "partial transport exceeds limit")
            body = fetch_file(f"{STAGE_ROOT}/{label}/collector.{name}", size, digest)
            local = destination / ("partial-collector." + name)
            local.write_bytes(body)
            transport[name] = {"bytes": size, "sha256": digest, "path": local.name}
            continue
        name, raw_size, digest = match.groups()
        require(name in SIDECAR_LIMITS and name not in report, "unexpected partial sidecar")
        size = int(raw_size)
        require(size <= SIDECAR_LIMITS[name], "partial sidecar exceeds limit")
        body = fetch_file(f"{remote}/{SUFFIX[name]}", size, digest)
        local = destination / ("partial-" + SUFFIX[name])
        local.write_bytes(body)
        report[name] = {"bytes": size, "sha256": digest, "path": local.name}
    return {"sidecars": report, "transport": transport,
            "classification": "incomplete-unclassified",
            "qualification": "One read-only salvage attempt; no retry and no absence/physical inference."}


def quiesce_remote(label: str) -> tuple[subprocess.CompletedProcess, dict]:
    """Stop the owned collector/writer before partial evidence is read."""
    out = f"{REMOTE_ROOT}/{label}"
    stage = f"{STAGE_ROOT}/{label}"
    tr = f"/sys/kernel/debug/tracing/instances/researcher-onset-{label}"
    command = f"""set +e
O={out}; SD={stage}; T={tr}
trustdir() {{ test ! -L "$1" && test -d "$1" && test "$(stat -c '%u:%a' "$1")" = 0:700; }}
test ! -e "$SD" || trustdir "$SD" || exit 48; test ! -e "$O" || trustdir "$O" || exit 49
trusted() {{ test -f "$1" && test ! -L "$1" && test "$(stat -c '%u:%a' "$1")" = 0:600; }}
guard() {{ p=$1; s=$2; set -- $(awk '{{print $3,$22}}' /proc/$p/stat 2>/dev/null); test "${{2:-}}" = "$s" && test "${{1:-}}" != Z; }}
guardpg() {{ p=$1; s=$2; set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$p/stat 2>/dev/null); test "${{4:-}}" = "$s" && test "${{1:-}}" != Z && test "${{2:-}}" = "$p" && test "${{3:-}}" = "$p"; }}
group_active() {{ p=$1; for f in /proc/[0-9]*/stat; do row=; {{ IFS= read -r row <"$f"; }} 2>/dev/null || continue; rest=${{row##*) }}; set -- $rest; test "${{1:-Z}}" != Z && test "${{3:-}}" = "$p" && return 0; done; return 1; }}
stopone() {{ f=$1; group=$2; test -e "$f" || return 0; trusted "$f" || return 1; read p s <"$f"; if test "$group" = 1; then if guardpg "$p" "$s"; then kill -TERM -"$p" 2>/dev/null || return 1; continuous=1; for i in 1 2 3 4 5; do group_active "$p" || {{ continuous=0; break; }}; sleep .2; done; if test "$continuous" = 1 && group_active "$p"; then kill -KILL -"$p" 2>/dev/null || return 1; for i in 1 2 3 4 5; do group_active "$p" || break; sleep .2; done; fi; group_active "$p" && return 1; elif group_active "$p"; then return 1; fi; return 0; fi; if guard "$p" "$s"; then kill -TERM "$p" 2>/dev/null || return 1; for i in 1 2 3 4 5; do guard "$p" "$s" || break; sleep .2; done; if guard "$p" "$s"; then kill -KILL "$p" 2>/dev/null || return 1; for i in 1 2 3 4 5; do guard "$p" "$s" || break; sleep .2; done; fi; guard "$p" "$s" && return 1; fi; return 0; }}
stopone "$SD/collector.pid" 1 || exit 50
stopone "$O/vlog.pid" 0 || exit 51
if test -d "$T"; then echo 0 >"$T/tracing_on"; echo 0 >"$T/events/enable"; rmdir "$T"; fi
test ! -e "$T" || exit 52
echo QUIESCED"""
    return root(command, 30)


def cleanup_remote(label: str) -> tuple[subprocess.CompletedProcess, dict]:
    out = f"{REMOTE_ROOT}/{label}"
    stage = f"{STAGE_ROOT}/{label}"
    tr = f"/sys/kernel/debug/tracing/instances/researcher-onset-{label}"
    log = f"{out}/expiry.log"
    command = f"""set +e
O={out}; SD={stage}; T={tr}
trustdir() {{ test ! -L "$1" && test -d "$1" && test "$(stat -c '%u:%a' "$1")" = 0:700; }}
test ! -e "$SD" || trustdir "$SD" || exit 48; test ! -e "$O" || trustdir "$O" || exit 49
trusted() {{ test -f "$1" && test ! -L "$1" && test "$(stat -c '%u:%a' "$1")" = 0:600; }}
guard() {{ p=$1; s=$2; set -- $(awk '{{print $3,$22}}' /proc/$p/stat 2>/dev/null); test "${{2:-}}" = "$s" && test "${{1:-}}" != Z; }}
guardpg() {{ p=$1; s=$2; set -- $(awk '{{print $3,$5,$6,$22}}' /proc/$p/stat 2>/dev/null); test "${{4:-}}" = "$s" && test "${{1:-}}" != Z && test "${{2:-}}" = "$p" && test "${{3:-}}" = "$p"; }}
group_active() {{ p=$1; for f in /proc/[0-9]*/stat; do row=; {{ IFS= read -r row <"$f"; }} 2>/dev/null || continue; rest=${{row##*) }}; set -- $rest; test "${{1:-Z}}" != Z && test "${{3:-}}" = "$p" && return 0; done; return 1; }}
stopone() {{ f=$1; group=$2; test -e "$f" || return 0; trusted "$f" || return 1; read p s <"$f"; if test "$group" = 1; then if guardpg "$p" "$s"; then kill -TERM -"$p" 2>/dev/null || return 1; continuous=1; for i in 1 2 3 4 5; do group_active "$p" || {{ continuous=0; break; }}; sleep .2; done; if test "$continuous" = 1 && group_active "$p"; then kill -KILL -"$p" 2>/dev/null || return 1; for i in 1 2 3 4 5; do group_active "$p" || break; sleep .2; done; fi; group_active "$p" && return 1; elif group_active "$p"; then return 1; fi; return 0; fi; if guard "$p" "$s"; then kill -TERM "$p" 2>/dev/null || return 1; for i in 1 2 3 4 5; do guard "$p" "$s" || break; sleep .2; done; if guard "$p" "$s"; then kill -KILL "$p" 2>/dev/null || return 1; for i in 1 2 3 4 5; do guard "$p" "$s" || break; sleep .2; done; fi; guard "$p" "$s" && return 1; fi; return 0; }}
stopone "$SD/collector.pid" 1 || exit 50
stopone "$O/vlog.pid" 0 || exit 51
stopone "$O/watchdog.pid" 1 || exit 52
stopone "$SD/expiry.pid" 1 || exit 53
if test -d "$T"; then echo 0 >"$T/tracing_on"; echo 0 >"$T/events/enable"; rmdir "$T"; fi
rm -f "$O/trace" "$O/meta.txt" "$O/samples.txt" "$O/sample-errors.txt" "$O/vlog-after.txt" "$O/artifacts.txt" "$O/fds.txt" "$O/vlog.pid" "$O/watchdog.pid"
rm -f "$SD/capture.sh" "$SD/collector.pid" "$SD/collector.stdout" "$SD/collector.stderr" "$SD/expiry.pid" "$SD/expiry.log" {log}
rmdir "$O" "$SD" 2>/dev/null || true
status=0; test ! -e "$T" || status=1; test ! -e "$O" || status=1; test ! -e "$SD" || status=1; test ! -e {log} || status=1
global=$(cat /sys/kernel/debug/tracing/tracing_on) || exit 55; echo "$global"
test "$status" = 0 || {{ echo RESIDUE; exit 54; }}
echo CLEAN"""
    return root(command, 30)


def run_capture(label: str, seconds: int, smoke_unobserved: bool = False) -> None:
    destination = BASE / (label + ".onset")
    destination.mkdir(mode=0o700)
    annotations = destination / "observer.jsonl"
    annotations.touch(mode=0o600)
    script = build_remote_script(label, seconds, allow_short=smoke_unobserved).encode()
    (destination / "remote.sh").write_bytes(script)
    rows: list[dict] = []
    collector = None
    meta = None
    sync = None
    stage = None
    started = dt.datetime.now(dt.timezone.utc)
    record = {"started_utc": started.isoformat(), "seconds": seconds, "accepted": False,
              "mode": "smoke-unobserved" if smoke_unobserved else "full-observed",
              "diagnostic_eligible": False, "physical_state": "unobserved-or-incomplete",
              "absence_claim_supported": False,
              "physical_state_source": "local human annotations only; never software-derived"}
    (destination / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    try:
        stage = stage_script(label, script)
        record["staging"] = stage
        (destination / "staging.json").write_text(json.dumps(stage, indent=2) + "\n")
        sync = acquire_sync()
        record["pre_capture_sync"] = sync
        collector = launch_collector(label, stage, sync["target_uptime"], destination)
        record["collector"] = collector
        require(sync["estimated_target_host_monotonic"] - time.monotonic() >= 2.0,
                "collector launch returned too late for a truthful observer countdown")
        controller_deadline = (sync["host_midpoint_monotonic"] +
                               (sync["target_uptime"] - sync["tv_uptime"]) + seconds + 15)
        if not smoke_unobserved:
            target_utc = dt.datetime.fromtimestamp(sync["estimated_target_host_utc"], dt.timezone.utc)
            print(f"Collector start is scheduled near {target_utc.isoformat()} with at least "
                  f"±{sync['mapping_uncertainty_seconds']:.3f}s clock/transport uncertainty; "
                  "this is a countdown, not verified readiness. Enter annotations as: "
                  "picture visible|black reaction_ms=N clock_ms=N (apps/warning/audio/note also accepted).",
                  file=sys.stderr)
        next_poll = (sync["host_midpoint_monotonic"] +
                     (sync["target_uptime"] - sync["tv_uptime"]) + seconds + 4)
        while True:
            if time.monotonic() >= controller_deadline:
                raise TimeoutError("bounded detached collector deadline expired")
            if time.monotonic() >= next_poll:
                if not collector_running(label, collector):
                    break
                next_poll = time.monotonic() + 2.0
            if smoke_unobserved:
                time.sleep(.25)
                continue
            ready, _, _ = select.select([sys.stdin], [], [], 0.25)
            if not ready:
                continue
            line = sys.stdin.readline()
            if line == "":
                time.sleep(.25)
                continue
            try:
                row = parse_annotation(line.strip())
                rows.append(row)
                with annotations.open("a") as handle:
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
            except ValueError as exc:
                print("Annotation rejected:", exc, file=sys.stderr)
        manifest = parse_manifest(fetch_collector_transport(label, destination))
        remote = f"{REMOTE_ROOT}/{label}"
        data = {name: fetch_file(f"{remote}/{SUFFIX[name]}", *spec)
                for name, spec in manifest.items()}
        verify_sidecars(data, manifest)
        for name, body in data.items():
            (destination / SUFFIX[name]).write_bytes(body)
        meta = validate_metadata(data["meta"].decode(), stage["bytes"], stage["sha256"], seconds)
        require(abs(meta["target"] - sync["target_uptime"]) <= .001,
                "scheduled target differs from pre-capture sync")
        require(sync["tv_uptime"] <= meta["sync_start"]["uptime"] < meta["target"] and
                abs((meta["sync_start"]["utc"] - sync["tv_utc"]) -
                    (meta["sync_start"]["uptime"] - sync["tv_uptime"])) <= 3.0,
                "pre-capture UTC/uptime anchor disagrees with collector anchor")
        fd_report = parse_fds(data["fds"].decode())
        validate_trace_scope(meta, fd_report)
        trace_report = trace_accounting(data["trace"], fd_report["tids"],
                                        meta["avoc_identity"][0], collector["pid"],
                                        meta["trace_start"], meta["trace_end"])
        sample_report = analyze_samples(data["samples"].decode(), meta, seconds)
        stderr_report = validate_dd_summaries(data["sample-errors"].decode(),
                                              sample_report["monitor_rows"],
                                              sample_report["qd_rows"])
        vlog_report = vlog_coverage(data["vlog-after"], meta["trace_start"], meta["trace_end"],
                                    source_exit_code=meta["vlog_exit_code"],
                                    forced_termination=meta["vlog_forced_termination"])
        observer = assess_annotations(rows, sync, meta, smoke_unobserved)
        technical_complete = vlog_report["complete"]
        diagnostic_eligible = technical_complete and observer["diagnostic_onset_eligible"]
        record.update({"manifest": {k: {"bytes": v[0], "sha256": v[1]} for k, v in manifest.items()},
                       "samples": sample_report, "trace": trace_report, "vlog": vlog_report,
                       "sample_stderr": stderr_report, "process_files": fd_report,
                       "vlog_markers": vlog_markers(data["vlog-after"]),
                       "observer": observer, "accepted": False,
                       "technical_capture_complete": False,
                       "diagnostic_eligible": False,
                       "pre_cleanup_technical_complete": technical_complete,
                       "pre_cleanup_diagnostic_eligible": diagnostic_eligible,
                       "physical_state": observer["physical_state"],
                       "absence_claim_supported": False,
                       "decision_limit": "No result proves physical light, MCU acceptance, or causation."})
    except Exception as exc:
        mark_acquisition_failure(record, exc)
        raise
    finally:
        acquisition_error = sys.exc_info()[1]
        if acquisition_error is not None:
            mark_acquisition_failure(record, acquisition_error)
        if acquisition_error is not None and stage is not None:
            try:
                qproc, qitem = quiesce_remote(label)
                (destination / "quiesce.json").write_text(qproc.stdout)
                require(qproc.returncode == 0 and qitem["exit_code"] == 0 and
                        not qitem["timed_out"] and qitem["stdout"].splitlines()[-1:] == ["QUIESCED"],
                        "remote collector quiescence not verified")
                record["quiesce_verified"] = True
            except Exception as exc:
                record["quiesce_verified"] = False
                record["quiesce_error"] = type(exc).__name__ + ": " + str(exc)
        if acquisition_error is not None and not record["accepted"] and record.get("quiesce_verified"):
            try:
                record["partial_salvage"] = salvage_partial(label, destination)
            except Exception as exc:
                record["partial_salvage_error"] = type(exc).__name__ + ": " + str(exc)
        if sync is not None and "observer" not in record:
            record["observer"] = assess_annotations(rows, sync, meta, smoke_unobserved)
        record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        (destination / "record.json").write_text(json.dumps(record, indent=2) + "\n")
        try:
            cproc, item = cleanup_remote(label)
            (destination / "cleanup.json").write_text(cproc.stdout)
            require(cproc.returncode == 0 and item["exit_code"] == 0 and not item["timed_out"] and
                    item["stdout"].splitlines()[-1:] == ["CLEAN"], "cleanup not verified")
            record["cleanup_verified"] = True
            record["technical_capture_complete"] = (
                acquisition_error is None and record.get("pre_cleanup_technical_complete", False))
            record["accepted"] = record["technical_capture_complete"]
            record["diagnostic_eligible"] = (
                record["technical_capture_complete"] and
                record.get("pre_cleanup_diagnostic_eligible", False))
            (destination / "record.json").write_text(json.dumps(record, indent=2) + "\n")
        except Exception as exc:
            mark_cleanup_failure(record, exc)
            (destination / "record.json").write_text(json.dumps(record, indent=2) + "\n")
            (destination / "cleanup-error.txt").write_text(
                type(exc).__name__ + ": immediate cleanup unverified; finite staged/output expiry may remain\n")
            if acquisition_error is None:
                raise RuntimeError("immediate cleanup not verified; inspect finite expiry") from exc
    print(json.dumps({"path": str(destination), "accepted": record["accepted"],
                      "diagnostic_eligible": record["diagnostic_eligible"],
                      "observer": record.get("observer"), "vlog": record.get("vlog")}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("label")
    parser.add_argument("--seconds", type=int, default=86)
    parser.add_argument("--smoke-unobserved", action="store_true",
                        help="5/10s transport-only smoke; no observer input or diagnostic classification")
    parser.add_argument("--run", action="store_true", help="execute after parent review; default is dry")
    parser.add_argument("--reviewed", action="store_true", help="required second execution guard")
    parser.add_argument("--emit-shell", action="store_true", help="print the dry remote shell")
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z][a-z0-9-]{0,30}", args.label) is not None,
            "use a unique lowercase label")
    local = {"binaries/libave.so.0.1": AVE_SHA, "binaries/avocd": AVOC_SHA,
             "binaries/deviced": DEV_SHA}
    for name, digest in local.items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest,
                "local matching binary hash changed: " + name)
    if args.smoke_unobserved:
        require(args.seconds in {5, 10}, "smoke-unobserved requires --seconds 5 or 10")
    else:
        require(85 <= args.seconds <= 90, "full capture requires --seconds 85..90")
    script = build_remote_script(args.label, args.seconds, allow_short=args.smoke_unobserved)
    script_bytes = script.encode()
    script_digest = hashlib.sha256(script_bytes).hexdigest()
    largest_chunk_command = len(("set -eu\nprintf %s " + "A" * len(base64.b64encode(b"x" * 4096)) +
                                 f" | base64 -d >>{STAGE_ROOT}/{args.label}/capture.sh").encode())
    require(largest_chunk_command <= 8192, "staging command exceeds controller limit")
    if not args.run:
        if args.emit_shell:
            print(script, end="")
        else:
            print(json.dumps({"mode": "dry-run; no TV/network/root call", "seconds": args.seconds,
                              "capture_kind": "smoke-unobserved" if args.smoke_unobserved else "full-observed",
                              "staged_script_bytes": len(script_bytes), "staged_script_sha256": script_digest,
                              "largest_staging_command_bytes": largest_chunk_command,
                              "private_trace_per_cpu_kb": 4096, "private_trace_total_kb_max": 16384,
                              "samplers": {"monitor_hz": "about 5", "qd_deviced_hz": "about 1"},
                              "vlog_semantics": "installed help: bounded absolute-uptime streaming; coverage measured",
                              "physical_state": "unobserved" if args.smoke_unobserved else "only local observer annotations during --run",
                              "diagnostic_eligible": False,
                              "eligibility_rule": "ordered wholly in-window visible-to-black human annotations with uncertainties",
                              "execution_guard": "--run --reviewed"}, indent=2))
        return
    require(args.reviewed, "live execution requires both --run and --reviewed after parent review")
    require(not (BASE / (args.label + ".onset")).exists(), "existing local capture refused")
    run_capture(args.label, args.seconds, smoke_unobserved=args.smoke_unobserved)


if __name__ == "__main__":
    main()
