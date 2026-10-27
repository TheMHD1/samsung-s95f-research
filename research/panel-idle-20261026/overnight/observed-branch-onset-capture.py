#!/usr/bin/env python3
"""Prepare one bounded observed onset capture with base-QD branch rows.

Dry by default.  This tool hash-pins and reuses the frozen observed-onset
collector's trace, vlog, annotation, transport, and cleanup implementation,
then applies fail-closed source transformations for a typed base-QDDimming /
DimmingBackendRoseMQD branch sampler.  No software field labels physical light
or selects a current policy branch.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
FROZEN_SOURCE = BASE / "observed-onset-capture.py"
FROZEN_SHA256 = "17a30cbee3d0d6ce5d4b23ffd1333b359b124bb4c1caaac253e1a6bc0f9999d5"
require_frozen = hashlib.sha256(FROZEN_SOURCE.read_bytes()).hexdigest()
if require_frozen != FROZEN_SHA256:
    raise RuntimeError("frozen observed-onset dependency hash changed")
_spec = importlib.util.spec_from_file_location("frozen_observed_onset_17a", FROZEN_SOURCE)
if _spec is None or _spec.loader is None:
    raise RuntimeError("frozen observed-onset dependency unavailable")
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

MODEL = _base.MODEL
BUILD = _base.BUILD
ACCESS = _base.ACCESS
AVE_PATH, AVE_SHA = _base.AVE_PATH, _base.AVE_SHA
AVOC_PATH, AVOC_SHA = _base.AVOC_PATH, _base.AVOC_SHA
DEV_PATH, DEV_SHA = _base.DEV_PATH, _base.DEV_SHA
TRACE_DRAIN_SECONDS = _base.TRACE_DRAIN_SECONDS
TRACE_DRAIN_MIN_SECONDS = _base.TRACE_DRAIN_MIN_SECONDS
TRACE_DRAIN_MAX_SECONDS = _base.TRACE_DRAIN_MAX_SECONDS
SIDECAR_LIMITS, SUFFIX = _base.SIDECAR_LIMITS, _base.SUFFIX
TRACE_CONFIG_EXPECTED = _base.TRACE_CONFIG_EXPECTED

REMOTE_ROOT = "/tmp/researcher-observed-branch-onset-20261026"
STAGE_ROOT = "/tmp/researcher-observed-branch-onset-stage-20261026"
TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-branch-onset-"
OLD_TRACE_PREFIX = "/sys/kernel/debug/tracing/instances/researcher-onset-"
OLD_STAGE_ROOT = "/tmp/researcher-observed-onset-stage-20261026"
BASE_QD_VPTR = 0x59F2E8
BASE_BACKEND_VPTR = 0x5A152C
BASE_BACKEND_SLOT = 0x1C6275
BASE_BACKEND_CACHE = 0x5AB958
AUTO_POWER_OFF_COUNT = 0x5BE420
GLOBAL_GAIN = 0x5AD94C
GLOBAL_TARGET_COUNT = 0x5BF6D0
# A row longer than this is retained but cannot qualify the combined diagnostic.
# This is an a-priori operational ceiling (twice the one-second cadence), not a
# claim about the 0.77 s unloaded baseline or a promise about incident load.
ROW_SPAN_MAX_SECONDS = 2.0
ARCHITECTURE_INVARIANTS = ('"--persistent-only"', "exec /usr/bin/setsid /bin/sh")

_base.REMOTE_ROOT = REMOTE_ROOT
_base.STAGE_ROOT = STAGE_ROOT

# Keep immutable references for wrapper functions that are deliberately
# installed back onto the frozen module during run_capture().  Looking them up
# dynamically through `_base` inside that context would recurse into this file.
_ORIGINAL_BUILD_REMOTE_SCRIPT = _base.build_remote_script
_ORIGINAL_VALIDATE_METADATA = _base.validate_metadata

require = _base.require
syscall_filter_for_tids = _base.syscall_filter_for_tids
sections = _base.sections
parse_maps = _base.parse_maps
mapped = _base.mapped
decode_words = _base.decode_words
identity_block = _base.identity_block
mark_cleanup_failure = _base.mark_cleanup_failure
mark_acquisition_failure = _base.mark_acquisition_failure
parse_fds = _base.parse_fds
validate_trace_scope = _base.validate_trace_scope
trace_accounting = _base.trace_accounting
vlog_coverage = _base.vlog_coverage
vlog_markers = _base.vlog_markers
parse_manifest = _base.parse_manifest
verify_sidecars = _base.verify_sidecars
parse_annotation = _base.parse_annotation
annotation_summary = _base.annotation_summary
assess_annotations = _base.assess_annotations
private_text = _base.private_text

MAP_AWK = ('BEGIN{ok=0} {split($1,a,"-"); '
           'if(length(a[1])==8 && length(a[2])==8 && substr($2,1,1)=="r" '
           '&& q>="x" a[1] && e<="x" a[2]) ok=1} END{exit(ok?0:1)}')
PROC_FUNCTIONS = r'''p4() { test "$#" = 1 || return 1; n=$1; row=; { IFS= read -r row <"/proc/$n/stat"; } 2>/dev/null || return 1; rest=${row##*) }; set -- $rest; test "$#" -ge 20 || return 1; printf "%s %s %s %s\n" "$1" "$3" "$4" "${20}"; }
p2() { test "$#" = 1 || return 1; fields=$(p4 "$1") || return 1; set -- $fields; test "$#" = 4 || return 1; printf "%s %s\n" "$1" "$4"; }
pstart() { test "$#" = 1 || return 1; fields=$(p4 "$1") || return 1; set -- $fields; test "$#" = 4 || return 1; printf "%s\n" "$4"; }'''


def _once(text: str, old: str, new: str, label: str) -> str:
    require(text.count(old) == 1, "frozen collector anchor mismatch: " + label)
    return text.replace(old, new, 1)


def _sub_once(text: str, pattern: str, replacement: str, label: str) -> str:
    result, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)
    require(count == 1, "frozen collector regex anchor mismatch: " + label)
    return result


def _harden_procstat(text: str) -> str:
    """Replace comm-sensitive /proc/stat awk fields with final-`) ` parsing."""
    if "/stat" not in text:
        return text.replace(OLD_TRACE_PREFIX, TRACE_PREFIX).replace(OLD_STAGE_ROOT, STAGE_ROOT)
    if text.startswith("set -eu\n") and "p4() {" not in text[:1000]:
        text = text.replace("set -eu\n", "set -eu\n" + PROC_FUNCTIONS + "\n", 1)
    elif text.startswith("set +e\n") and "p4() {" not in text[:1000]:
        text = text.replace("set +e\n", "set +e\n" + PROC_FUNCTIONS + "\n", 1)
    if "sleep 900; p4() {" not in text:
        text = text.replace("-c 'sleep 900; ", "-c 'sleep 900; " + PROC_FUNCTIONS + " ")
    patterns = (
        (r'''awk '\{print \$22\}' /proc/\$(\w+)/stat(?: 2>/dev/null)?''', r'''pstart "$\1"'''),
        (r'''awk '\{print \$3,\$22\}' /proc/\$(\w+)/stat(?: 2>/dev/null)?''', r'''p2 "$\1"'''),
        (r'''awk '\{print \$3,\$5,\$6,\$22\}' /proc/\$(\w+)/stat(?: 2>/dev/null)?''', r'''p4 "$\1"'''),
        (r'''awk "\{print \\\$3,\\\$22\}" /proc/\$(\w+)/stat(?: 2>/dev/null)?''', r'''p2 "$\1"'''),
        (r'''awk "\{print \\\$3,\\\$5,\\\$6,\\\$22\}" /proc/\$(\w+)/stat(?: 2>/dev/null)?''', r'''p4 "$\1"'''),
    )
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    text = text.replace(OLD_TRACE_PREFIX, TRACE_PREFIX).replace(OLD_STAGE_ROOT, STAGE_ROOT)
    # Cleanup commands from the frozen tool must also remove private sampler
    # temporaries if acquisition was interrupted before concatenation.
    if '"$O/q-samples.tmp"' not in text:
        text = text.replace('"$O/sample-errors.txt"',
                            '"$O/sample-errors.txt" "$O/q-samples.tmp" "$O/q-errors.tmp" "$O/q-sampler.stderr" "$O/q-ready.tmp" "$O/q-sampler.pid" "$O/q-sampler.sh"')
    text = text.replace('stopone "$SD/collector.pid" 1 || exit 50',
                        'stopone "$O/q-sampler.pid" 1 || exit 49\nstopone "$SD/collector.pid" 1 || exit 50')
    require(not any("awk" in line and "/stat" in line for line in text.splitlines()),
            "comm-sensitive procstat parser remains")
    return text


def q_sampler_script() -> str:
    """Return the separately-owned Q sampler DATA executed through `sh -c`."""
    return fr'''set -eu
umask 077
{PROC_FUNCTIONS}
set -- $(p4 "$$"); test "${{2:-}}" = "$$"; test "${{3:-}}" = "$$"; printf '%s %s\n' "$$" "${{4:-}}" >"$QREADY"
mapok() {{ q=$1; z=$2; f=$3; test "$q" -gt 0 || return 1; test "$z" -gt 0 || return 1; test $((q%4)) = 0 || return 1; test $((z%4)) = 0 || return 1; test $((q+z)) -lt 4294967296 || return 1; qh=$(printf '%08x' "$q") || return 1; eh=$(printf '%08x' $((q+z))) || return 1; LC_ALL=C awk -v q="x$qh" -v e="x$eh" '{MAP_AWK}' "$f"; }}
sampleok() {{ k="$1:$2:$3:$4"; case "$k" in "$((A+0x5a69ec)):1:$am:$ap"|"$G:1:$am:$ap"|"$P:7:$am:$ap"|"$B:1:$am:$ap"|"$((BV+0xd8)):1:$am:$ap"|"$((A+0x5ab958)):1:$am:$ap"|"$((I+0xa4)):3:$am:$ap"|"$((I+0x458)):12:$am:$ap"|"$((A+0x5ad94c)):1:$am:$ap"|"$((A+0x5bf6d0)):2:$am:$ap"|"$I:1:$am:$ap"|"$((I+0x38)):1:$am:$ap"|"$((I+0x88)):1:$am:$ap"|"$((I+0x98)):1:$am:$ap"|"$((I+0xf8)):2:$am:$ap"|"$((I+0x188)):2:$am:$ap"|"$((I+0x2a4)):2:$am:$ap"|"$((I+0x450)):1:$am:$ap"|"$((A+0x5be420)):1:$am:$ap"|"$DG:6:$dm:$dp"|"$((D+0x12aeb8)):1:$dm:$dp"|"$((EP+0x30)):4:$dm:$dp"|"$((OP+0x24)):1:$dm:$dp"|"$EC:1:$dm:$dp"|"$ET:1:$dm:$dp"|"$EA:1:$dm:$dp") return 0;; *) return 1;; esac; }}
b64() {{ sampleok "$1" "$2" "$3" "$4" && mapok "$1" $(($2*4)) "$3" || {{ printf '!range'; return; }}; v=$( (ulimit -f 256; dd if=/proc/$4/mem bs=4 skip=$(($1/4)) count=$2 2>>"$QE")|base64|tr -d '\n'); test -n "$v" && printf %s "$v" || printf '!read'; }}
qn=$TS
while awk -v n="$(cut -d' ' -f1 /proc/uptime)" -v e="$EN" 'BEGIN{{exit !(n<e)}}'; do
 qs=$(cut -d' ' -f1 /proc/uptime); test "$(pidof avocd)" = "$ap"; test "$(readlink /proc/$ap/exe)" = "$AVOC_PATH"; aps=$(pstart "$ap"); test "$aps" = "$APSTART"; cab=$(awk '$3=="00000000"&&$6=="/prd/usr/lib/libave.so.0.1"{{split($1,a,"-");print a[1]}}' "$am"); test $((0x$cab)) = "$A"; test "$(pidof deviced)" = "$dp"; test "$(readlink /proc/$dp/exe)" = "$DEV_PATH"; dps=$(pstart "$dp"); test "$dps" = "$DPSTART"; cdb=$(awk '$3=="00000000"&&$6=="/usr/bin/deviced"{{split($1,a,"-");print a[1]}}' "$dm"); test $((0x$cdb)) = "$D"; qline="Q|$qs|$ap,$aps,$A,$dp,$dps,$D"
 for x in "$((A+0x5a69ec)) 1 $am $ap" "$G 1 $am $ap" "$P 7 $am $ap" "$B 1 $am $ap" "$((BV+0xd8)) 1 $am $ap" "$((A+0x5ab958)) 1 $am $ap" "$((I+0xa4)) 3 $am $ap" "$((I+0x458)) 12 $am $ap" "$((A+0x5ad94c)) 1 $am $ap" "$((A+0x5bf6d0)) 2 $am $ap" "$I 1 $am $ap" "$((I+0x38)) 1 $am $ap" "$((I+0x88)) 1 $am $ap" "$((I+0x98)) 1 $am $ap" "$((I+0xf8)) 2 $am $ap" "$((I+0x188)) 2 $am $ap" "$((I+0x2a4)) 2 $am $ap" "$((I+0x450)) 1 $am $ap" "$((A+0x5be420)) 1 $am $ap" "$DG 6 $dm $dp" "$((D+0x12aeb8)) 1 $dm $dp" "$((EP+0x30)) 4 $dm $dp" "$((OP+0x24)) 1 $dm $dp" "$EC 1 $dm $dp" "$ET 1 $dm $dp" "$EA 1 $dm $dp"; do set -- $x; qline="$qline|$(b64 "$1" "$2" "$3" "$4")"; done
 qe=$(cut -d' ' -f1 /proc/uptime); printf '%s|%s\n' "$qline" "$qe" >>"$QF"
 qn=$(awk -v q="$qn" 'BEGIN{{printf "%.3f",q+1}}'); now=$(cut -d' ' -f1 /proc/uptime); delay=$(awk -v q="$qn" -v n="$now" 'BEGIN{{d=q-n;if(d<.001)d=.001;printf "%.3f",d}}'); sleep "$delay"
done
'''


Q_SAMPLER_BYTES = q_sampler_script().encode()
Q_SAMPLER_SHA256 = hashlib.sha256(Q_SAMPLER_BYTES).hexdigest()


def build_remote_script(label: str, seconds: int, allow_short: bool = False) -> str:
    shell = _ORIGINAL_BUILD_REMOTE_SCRIPT(label, seconds, allow_short=allow_short)
    shell = _harden_procstat(shell)

    old_map = next(line for line in shell.splitlines() if line.startswith("mapok()"))
    new_map = ("mapok() { q=$1; z=$2; f=$3; test \"$q\" -gt 0 || return 1; "
               "test \"$z\" -gt 0 || return 1; test $((q%4)) = 0 || return 1; "
               "test $((z%4)) = 0 || return 1; test $((q+z)) -lt 4294967296 || return 1; "
               "qh=$(printf '%08x' \"$q\") || return 1; eh=$(printf '%08x' $((q+z))) || return 1; "
               f"LC_ALL=C awk -v q=\"x$qh\" -v e=\"x$eh\" '{MAP_AWK}' \"$f\"; }}")
    shell = _once(shell, old_map, new_map, "fresh map guard")

    old_children = "vp=; vstart="
    new_children = r'''vp=; vstart=; qp=; qstart=; qowned=0
qgroup_active() { p=$1; for f in /proc/[0-9]*/stat; do row=; { IFS= read -r row <"$f"; } 2>/dev/null || continue; rest=${row##*) }; set -- $rest; test "${1:-Z}" != Z && test "${3:-}" = "$p" && return 0; done; return 1; }
qguard() { test -n "$qp" && set -- $(p4 "$qp") && test "${4:-}" = "$qstart" && test "${1:-}" != Z && test "${2:-}" = "$qp" && test "${3:-}" = "$qp"; }
stopq() { test -z "$qp" && return 0; if qguard; then kill -TERM -"$qp" 2>/dev/null || true; continuous=1; for i in 1 2 3 4 5; do qgroup_active "$qp" || { continuous=0; break; }; sleep .2; done; if test "$continuous" = 1 && qgroup_active "$qp"; then kill -KILL -"$qp" 2>/dev/null || true; for i in 1 2 3 4 5; do qgroup_active "$qp" || break; sleep .2; done; fi; qgroup_active "$qp" && return 1; elif qgroup_active "$qp"; then return 1; elif set -- $(p2 "$qp" 2>/dev/null) && test "${2:-}" = "$qstart" && test "${1:-}" != Z; then kill -KILL "$qp" 2>/dev/null || true; for i in 1 2 3 4 5; do set -- $(p2 "$qp" 2>/dev/null) || break; test "${2:-}" = "$qstart" && test "${1:-}" != Z || break; sleep .2; done; set -- $(p2 "$qp" 2>/dev/null) && test "${2:-}" = "$qstart" && test "${1:-}" != Z && return 1; fi; wait "$qp" 2>/dev/null || true; qowned=0; return 0; }'''
    shell = _once(shell, old_children, new_children, "owned Q sampler helpers")
    shell = _once(shell, "clean() { cs=0; stopv || cs=1;",
                  "clean() { cs=0; stopq || cs=1; stopv || cs=1;",
                  "Q sampler trap cleanup")

    old_preflight = ('G=$((A+0x5be2a4)); test "$(u32 $((A+0x5a69ec)) "$am" $ap)" = "$G"; '
                     'P=$(u32 "$G" "$am" $ap); V=$(u32 "$P" "$am" $ap); I=$(u32 $((P+4)) "$am" $ap)\n'
                     'test "$V" = $((A+0x59f2e8)) || test "$V" = $((A+0x5a094c)); mapok "$I" 688 "$am"')
    new_preflight = ('G=$((A+0x5be2a4)); test "$(u32 $((A+0x5a69ec)) "$am" $ap)" = "$G"; '
                     'P=$(u32 "$G" "$am" $ap); V=$(u32 "$P" "$am" $ap); I=$(u32 $((P+4)) "$am" $ap); B=$(u32 $((P+16)) "$am" $ap)\n'
                     'test "$V" = $((A+0x59f2e8)); BV=$(u32 "$B" "$am" $ap); test "$BV" = $((A+0x5a152c)); '
                     'BS=$(u32 $((BV+0xd8)) "$am" $ap); test "$BS" = $((A+0x1c6275)); '
                     'mapok "$P" 28 "$am"; mapok "$I" 1160 "$am"; mapok $((A+0x5ab958)) 4 "$am"; '
                     'mapok $((A+0x5ad94c)) 4 "$am"; mapok $((A+0x5bf6d0)) 8 "$am"; mapok $((A+0x5be420)) 4 "$am"')
    shell = _once(shell, old_preflight, new_preflight, "base QD/backend preflight")

    old_sampleok = next(line for line in shell.splitlines() if line.startswith("sampleok()"))
    allowed = (
        '"$((A+0x5bfc5c)):38:$am:$ap"|"$((A+0x5a69ec)):1:$am:$ap"|'
        '"$G:1:$am:$ap"|"$P:7:$am:$ap"|"$B:1:$am:$ap"|"$((BV+0xd8)):1:$am:$ap"|'
        '"$((A+0x5ab958)):1:$am:$ap"|"$((I+0xa4)):3:$am:$ap"|'
        '"$((I+0x458)):12:$am:$ap"|"$((A+0x5ad94c)):1:$am:$ap"|'
        '"$((A+0x5bf6d0)):2:$am:$ap"|"$I:1:$am:$ap"|"$((I+0x38)):1:$am:$ap"|'
        '"$((I+0x88)):1:$am:$ap"|"$((I+0x98)):1:$am:$ap"|'
        '"$((I+0xf8)):2:$am:$ap"|"$((I+0x188)):2:$am:$ap"|'
        '"$((I+0x2a4)):2:$am:$ap"|"$((I+0x450)):1:$am:$ap"|'
        '"$((A+0x5be420)):1:$am:$ap"|"$DG:6:$dm:$dp"|'
        '"$((D+0x12aeb8)):1:$dm:$dp"|"$((EP+0x30)):4:$dm:$dp"|'
        '"$((OP+0x24)):1:$dm:$dp"|"$EC:1:$dm:$dp"|"$ET:1:$dm:$dp"|"$EA:1:$dm:$dp"')
    new_sampleok = ('sampleok() { k="$1:$2:$3:$4"; case "$k" in ' + allowed +
                    ') return 0;; *) return 1;; esac; }')
    shell = _once(shell, old_sampleok, new_sampleok, "sample allowlist")
    old_b64 = next(line for line in shell.splitlines() if line.startswith("b64()"))
    new_b64 = ('b64() { sampleok "$1" "$2" "$3" "$4" && mapok "$1" $(($2*4)) "$3" || { printf "!range"; return; }; '
               'er=${5:-$E}; v=$( (ulimit -f 256; dd if=/proc/$4/mem bs=4 skip=$(($1/4)) '
               'count=$2 2>>"$er")|base64|tr -d "\\n"); test -n "$v" && printf %s "$v" || printf "!read"; }')
    shell = _once(shell, old_b64, new_b64, "sampler error routing")

    old_ranges = next(line for line in shell.splitlines() if line.startswith("for x in ") and
                      'A+0x5bfc5c' in line)
    range_items = re.findall(r'"([^\"]+)"', allowed)
    # Convert case tokens address:count:map:pid back to the four-column range rows.
    range_rows = []
    for token in range_items:
        parts = token.split(":")
        require(len(parts) == 4, "internal allowlist token shape")
        range_rows.append(f'"{parts[0]} {parts[1]} {parts[2]} {parts[3]}"')
    q_encoded = base64.b64encode(Q_SAMPLER_BYTES).decode()
    new_ranges = ('for x in ' + " ".join(range_rows) +
                  '; do set -- $x; mapok "$1" $(($2*4)) "$3" || exit 33; done; '
                  'QSC=$O/q-sampler.sh; printf %s ' + q_encoded +
                  ' | base64 -d >"$QSC"; chmod 600 "$QSC"; '
                  f'test "$(wc -c <\"$QSC\")" = {len(Q_SAMPLER_BYTES)}; '
                  f'test "$(sha256sum "$QSC"|cut -d" " -f1)" = {Q_SAMPLER_SHA256}')
    shell = _once(shell, old_ranges, new_ranges, "prevalidated sample ranges")

    old_pointer_start = ('echo "$A $G $P $V $I $D $DG $e0 $e1 $es $o0 $o1 $os '
                         '$EP $OP $EC $ET $EA $ECV $ETV $EAV"')
    new_pointer_start = ('echo "$A $G $P $V $I $B $BV $BS $D $DG $e0 $e1 $es $o0 $o1 $os '
                         '$EP $OP $EC $ET $EA $ECV $ETV $EAV"')
    shell = _once(shell, old_pointer_start, new_pointer_start, "metadata start pointers")
    old_pointer_end = ('echo "$A $(u32 $((A+0x5a69ec)) "$am" $ap) $(u32 "$G" "$am" $ap) '
                       '$(u32 "$P" "$am" $ap) $(u32 $((P+4)) "$am" $ap) $D $DG')
    new_pointer_end = ('echo "$A $(u32 $((A+0x5a69ec)) "$am" $ap) $(u32 "$G" "$am" $ap) '
                       '$(u32 "$P" "$am" $ap) $(u32 $((P+4)) "$am" $ap) '
                       '$(u32 $((P+16)) "$am" $ap) $(u32 "$B" "$am" $ap) '
                       '$(u32 $((BV+0xd8)) "$am" $ap) $D $DG')
    shell = _once(shell, old_pointer_end, new_pointer_end, "metadata end pointers")

    shell = _once(shell, 'echo @@ BOOT_START;',
                  'echo @@ Q_SAMPLER_HASH_START; wc -c "$QSC"; sha256sum "$QSC"; echo @@ BOOT_START;',
                  "Q sampler start hash")
    shell = _once(shell, 'echo @@ BOOT_END;',
                  'echo @@ Q_SAMPLER_HASH_END; wc -c "$QSC"; sha256sum "$QSC"; echo @@ BOOT_END;',
                  "Q sampler end hash")

    sampler = r'''QF=$O/q-samples.tmp; QE=$O/q-errors.tmp; QSE=$O/q-sampler.stderr; QREADY=$O/q-ready.tmp; test ! -e "$QREADY"; : >"$QF"; : >"$QE"; : >"$QSE"; chmod 600 "$QF" "$QE" "$QSE"; qr=0
closefds() { for f in /proc/self/fd/*; do n=${f##*/}; case "$n" in 0|1|2) ;; *) eval "exec $n>&-" 2>/dev/null || true;; esac; done; }
export QF QE QREADY TS="$ts" EN="$en" A G P B BV I am ap APSTART="$(pstart "$ap")" AVOC_PATH="/usr/bin/avocd" DG D dm dp DPSTART="$(pstart "$dp")" DEV_PATH="/usr/bin/deviced" EP OP EC ET EA
(closefds; exec /usr/bin/setsid /bin/sh -c "$(cat "$QSC")") >/dev/null 2>"$QSE" </dev/null & qp=$!
qready=0; for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do if test -f "$QREADY" && test ! -L "$QREADY" && test "$(stat -c '%u:%a' "$QREADY")" = 0:600; then read rp rs <"$QREADY"; if test "$rp" = "$qp"; then qstart=$rs; if qguard; then qready=1; break; fi; fi; fi; set -- $(p2 "$qp" 2>/dev/null) || break; test "${1:-}" != Z || break; sleep .05; done
if test "$qready" != 1; then if test -f "$QREADY" && test ! -L "$QREADY" && test "$(stat -c '%u:%a' "$QREADY")" = 0:600; then read rp rs <"$QREADY"; case "$rs" in ''|*[!0-9]*) kill -KILL "$qp" 2>/dev/null || true;; *) if test "$rp" = "$qp"; then qstart=$rs; qowned=1; stopq || exit 81; else kill -KILL "$qp" 2>/dev/null || true; fi;; esac; else kill -KILL "$qp" 2>/dev/null || true; fi; for i in 1 2 3 4 5; do set -- $(p2 "$qp" 2>/dev/null) || break; test "${1:-}" != Z || break; sleep .2; done; set -- $(p2 "$qp" 2>/dev/null) && test "${1:-}" != Z && exit 81; wait "$qp" 2>/dev/null || true; exit 81; fi; qowned=1; mv "$QREADY" "$O/q-sampler.pid"; set -- $(p4 "$$"); (ulimit -f 4096; { echo @@ SAMPLERS; echo "monitor $$ ${4:-} ${2:-} ${3:-} q $qp $qstart $qp $qp"; } >>"$M")
(ulimit -f 256; while awk -v n="$(cut -d" " -f1 /proc/uptime)" -v e="$en" 'BEGIN{exit !(n<e)}'; do up=$(cut -d" " -f1 /proc/uptime); printf "M|%s|" "$up" >>"$S"; b64 $((A+0x5bfc5c)) 38 "$am" $ap >>"$S"; echo >>"$S"; sleep .2; done) || sr=$?'''
    shell = _sub_once(shell, r'\(ulimit -f 256; i=0; while .*?\) \|\| sr=\$\?',
                      sampler, "parallel monitor/QD sampler")
    q_finalize = r'''te="$te $td"; set +e; sleep 2; qr=0; qdline=$(awk -v e="$en" 'BEGIN{printf "%.3f",e+3}'); while qguard && awk -v n="$(cut -d" " -f1 /proc/uptime)" -v d="$qdline" 'BEGIN{exit !(n<d)}'; do sleep .1; done; if qgroup_active "$qp"; then qr=124; stopq || qr=125; else wait "$qp" || qr=$?; qowned=0; fi; (ulimit -f 2048; cat "$QF" >>"$S") || qr=126; (ulimit -f 256; cat "$QE" >>"$E") || qr=127; test ! -s "$QSE" || { (ulimit -f 256; cat "$QSE" >>"$E") || qr=129; qr=128; }; rm -f "$QF" "$QE" "$QSE" "$O/q-sampler.pid"; test "$sr:$qr" = 0:0 || sr=1'''
    shell = _once(shell, 'te="$te $td"; set +e; sleep 2', q_finalize,
                  "post-trace Q sampler reap")
    shell = _harden_procstat(shell)
    # Independent expiry and host quiesce/cleanup must stop the owned sampler
    # before stopping its collector parent.  Every occurrence is intentional.
    shell = shell.replace('stoppg "$SD/collector.pid"; stoppid "$O/vlog.pid";',
                          'stoppg "$O/q-sampler.pid"; stoppg "$SD/collector.pid"; stoppid "$O/vlog.pid";')
    require(OLD_TRACE_PREFIX not in shell and TRACE_PREFIX in shell,
            "private trace namespace transform failed")
    require("0x5a094c" not in shell, "MNT class remains eligible")
    require(len(re.findall(r'^mapok\(\)', shell, re.MULTILINE)) == 1 and
            "while read r p x" not in shell, "slow map guard remains")
    return shell


def _source_mapped(mapping, address: int, size: int, executable: bool = False) -> bool:
    return address % 4 == 0 and any(
        lo <= address and address + size <= hi and path == AVE_PATH and
        perms.startswith("r") and (not executable or "x" in perms)
        for lo, hi, perms, _offset, path in mapping)


def _old_metadata_text(text: str) -> tuple[str, list[int], list[int]]:
    part = sections(text)
    start = [int(value) for value in part.get("POINTERS_START", "").split()]
    end = [int(value) for value in part.get("POINTERS_END", "").split()]
    require(len(start) == len(end) == 24, "branch pointer field count")
    old_start = start[:5] + start[8:]
    old_end = end[:5] + end[8:]
    require(len(old_start) == len(old_end) == 21, "internal pointer projection")
    converted = text.replace("@@ POINTERS_START\n" + part["POINTERS_START"],
                             "@@ POINTERS_START\n" + " ".join(map(str, old_start)), 1)
    converted = converted.replace("@@ POINTERS_END\n" + part["POINTERS_END"],
                                  "@@ POINTERS_END\n" + " ".join(map(str, old_end)), 1)
    for name in ("Q_SAMPLER_HASH_START", "Q_SAMPLER_HASH_END", "SAMPLERS"):
        converted, count = re.subn(
            rf"(?:^|\n)@@ {name}\n.*?(?=\n@@ |\Z)", "", converted,
            count=1, flags=re.DOTALL)
        require(count == 1, "missing branch sampler metadata: " + name)
    return converted, start, end


def validate_metadata(text: str, script_size: int, script_sha256: str, seconds: int) -> dict:
    raw_part = sections(text)
    expected = {
        "BUILD", "SCRIPT_HASH_START", "Q_SAMPLER_HASH_START", "BOOT_START",
        "SYNC_START", "AVOC_ID_START", "DEV_ID_START", "POINTERS_START",
        "AVOC_MAPS_START", "DEV_MAPS_START", "GLOBAL_TRACE_START", "TRACE_CONFIG",
        "SAMPLERS", "Q_SAMPLER_HASH_END", "BOOT_END", "SYNC_END",
        "CAPTURE_WINDOW", "AVOC_ID_END", "DEV_ID_END", "POINTERS_END",
        "AVOC_MAPS_END", "DEV_MAPS_END", "SCRIPT_HASH_END", "GLOBAL_TRACE_END",
        "VLOG_SEMANTICS"}
    require(set(raw_part) == expected, "unexpected/missing branch metadata sections")
    for name in ("Q_SAMPLER_HASH_START", "Q_SAMPLER_HASH_END"):
        rows = raw_part[name].splitlines()
        require(len(rows) == 2 and int(rows[0].split()[0]) == len(Q_SAMPLER_BYTES) and
                rows[1].split()[0] == Q_SAMPLER_SHA256,
                "Q sampler DATA identity mismatch")
    sampler = raw_part["SAMPLERS"].split()
    require(len(sampler) == 10 and sampler[0] == "monitor" and sampler[5] == "q" and
            all(item.isdigit() and int(item) > 0 for item in sampler[1:5] + sampler[6:]) and
            sampler[1] == sampler[3] == sampler[4] and
            sampler[6] == sampler[8] == sampler[9] and sampler[1] != sampler[6],
            "sampler PID/start/group/session identity malformed")
    converted, start, end = _old_metadata_text(text)
    report = _ORIGINAL_VALIDATE_METADATA(converted, script_size, script_sha256, seconds)
    require(start == end, "branch pointer/backend chain changed")
    a, glob, panel, vptr, inner, backend, backend_vptr, backend_slot = start[:8]
    require(vptr == a + BASE_QD_VPTR, "capture requires exact base QDDimming")
    require(backend_vptr == a + BASE_BACKEND_VPTR and
            backend_slot == a + BASE_BACKEND_SLOT,
            "capture requires typed DimmingBackendRoseMQD slot")
    amap = report["avoc_maps"]
    loads = [lo for lo, _hi, perms, offset, path in amap
             if path == AVE_PATH and offset == 0 and "x" in perms]
    require(loads == [a] and
            _source_mapped(amap, vptr, 0x1C0),
            "QDDimming vptr is not uniquely libave source-backed")
    for address, size in ((panel, 28), (inner, 1160), (backend, 4),
                          (a + BASE_BACKEND_CACHE, 4), (a + GLOBAL_GAIN, 4),
                          (a + GLOBAL_TARGET_COUNT, 8), (a + AUTO_POWER_OFF_COUNT, 4)):
        require(mapped(amap, address, size), "unreadable branch-state target")
    require(_source_mapped(amap, backend_vptr, 0xDC) and
            _source_mapped(amap, backend_slot & ~1, 4, executable=True),
            "backend vptr/slot is not libave source-backed")
    (_a, _glob, _panel, _vptr, _inner, d, dglob,
     ep, op, ec, et, ea, ecv, etv, eav) = report["pointers"]
    report["pointers"] = [a, glob, panel, vptr, inner, backend, backend_vptr,
                          backend_slot, d, dglob, ep, op, ec, et, ea, ecv, etv, eav]
    report["qd_class"] = "QDDimming"
    report["backend_class"] = "DimmingBackendRoseMQD"
    report["sampler_identities"] = {
        "monitor": {"pid": int(sampler[1]), "start_ticks": int(sampler[2]),
                    "process_group": int(sampler[3]), "session": int(sampler[4])},
        "qd_branch": {"pid": int(sampler[6]), "start_ticks": int(sampler[7]),
                      "process_group": int(sampler[8]), "session": int(sampler[9])}}
    report["q_sampler_data"] = {"bytes": len(Q_SAMPLER_BYTES),
                                "sha256": Q_SAMPLER_SHA256}
    report["branch_source_offsets"] = {
        "inner": ["0x0", "0x38(low-byte)", "0x88", "0x98", "0xa4", "0xa8",
                  "0xac", "0xf8", "0xfc", "0x188", "0x18c", "0x2a4", "0x2a8",
                  "0x450", "0x458..0x484"],
        "globals": ["0x5ab958", "0x5ad94c", "0x5bf6d0..0x5bf6d4", "0x5be420"],
    }
    return report


QD_COUNTS = (1, 1, 7, 1, 1, 1, 3, 12, 1, 2, 1, 1, 1, 1, 2, 2, 2, 1, 1,
             6, 1, 4, 1, 1, 1, 1)


def analyze_samples(text: str, meta: dict, seconds: int) -> dict:
    monitor, qd = [], []
    (a, glob, panel, vptr, inner, backend, backend_vptr, backend_slot,
     d, dglob, ep, op, ec, et, ea, ecv, etv, eav) = meta["pointers"]
    for line in text.splitlines():
        fields = line.split("|")
        require(len(fields) >= 3, "malformed sample row")
        if fields[0] == "M":
            require(len(fields) == 3, "monitor row shape")
            up = float(fields[1])
            require(math.isfinite(up) and meta["trace_start"] <= up <= meta["trace_end"],
                    "sample timestamp outside capture window")
            monitor.append((up, decode_words(fields[2], 38)))
            continue
        require(fields[0] == "Q" and len(fields) == 3 + len(QD_COUNTS) + 1,
                "QD branch row shape")
        start, end = float(fields[1]), float(fields[-1])
        require(math.isfinite(start) and math.isfinite(end) and
                meta["trace_start"] <= start <= end <= meta["trace_end"],
                "QD row timestamp span outside capture window")
        require(end - start <= ROW_SPAN_MAX_SECONDS,
                "QD row non-atomic span exceeds predeclared operational ceiling")
        identity = fields[2].split(",")
        require(len(identity) == 6 and all(item.isdigit() for item in identity) and
                [int(item) for item in identity] ==
                [meta["avoc_identity"][0], meta["avoc_identity"][1], a,
                 meta["deviced_identity"][0], meta["deviced_identity"][1], d],
                "QD row process/load identity changed")
        values = [decode_words(raw, count)
                  for raw, count in zip(fields[3:-1], QD_COUNTS)]
        require(values[0] == [glob] and values[1] == [panel] and
                values[2][0] == vptr and values[2][1] == inner and
                values[2][4] == backend and (values[2][6] & 255) == 1 and
                values[3] == [backend_vptr] and
                values[4] == [backend_slot], "sampled QD/backend identity changed")
        dev = values[19]
        require((dev[2] & 255) == 0 and (dev[5] & 255) == 0 and
                dev[0] == ep and dev[3] == op, "sampled deviced pointer chain changed")
        require(values[20][0] <= 6, "invalid power index")
        require(values[21][1:] == [ec, et, ea] and
                [values[23][0], values[24][0], values[25][0]] == [ecv, etv, eav],
                "sampled deviced child/vptr chain changed")
        qd.append((start, end, values))
    require(len(monitor) >= int(seconds * 3.5), "insufficient monitor sampling")
    require(len(qd) >= int(seconds * .7), "insufficient one-Hz sampling")
    require(all(right[0] > left[0] and right[0] - left[0] <= 1.0
                for left, right in zip(monitor, monitor[1:])), "monitor sample gap")
    require(all(right[0] > left[0] and right[0] - left[0] <= 2.0 and
                right[0] >= left[1] for left, right in zip(qd, qd[1:])),
            "QD sample gap/overlap")
    require(monitor[0][0] - meta["trace_start"] <= .6 and
            meta["trace_end"] - monitor[-1][0] <= .8 and
            qd[0][0] - meta["trace_start"] <= 1.2 and
            meta["trace_end"] - qd[-1][1] <= 1.6,
            "sample endpoint coverage incomplete")
    monitor_span = monitor[-1][0] - monitor[0][0]
    qd_span = qd[-1][0] - qd[0][0]
    spans = [row[1] - row[0] for row in qd]
    return {"monitor_rows": len(monitor), "qd_rows": len(qd),
            "monitor_window": [monitor[0][0], monitor[-1][0]],
            "qd_window": [qd[0][0], qd[-1][1]],
            "monitor_span_seconds": monitor_span, "qd_span_seconds": qd_span,
            "monitor_rate_hz": (len(monitor) - 1) / monitor_span,
            "qd_rate_hz": (len(qd) - 1) / qd_span,
            "qd_row_span_seconds": {"min": min(spans), "max": max(spans),
                                    "mean": sum(spans) / len(spans),
                                    "accepted_limit": ROW_SPAN_MAX_SECONDS},
            "leading_gaps_seconds": {"monitor": monitor[0][0] - meta["trace_start"],
                                     "qd": qd[0][0] - meta["trace_start"]},
            "trailing_gaps_seconds": {"monitor": meta["trace_end"] - monitor[-1][0],
                                      "qd": meta["trace_end"] - qd[-1][1]},
            "qualification": "sequential raw branch fields only; no active branch, kernel gate, or emitted-light state inferred"}


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
        require(count in {1, 2, 3, 4, 6, 7, 12, 38},
                "unexpected sampler dd record count")
        counts[count] = counts.get(count, 0) + 1
    expected = {1: 39 + 17 * qd_rows, 2: 4 * qd_rows, 3: qd_rows,
                4: qd_rows, 6: qd_rows, 7: qd_rows, 12: qd_rows,
                38: monitor_rows}
    require(counts == expected, "sampler dd operation inventory mismatch")
    return {"dd_operations": sum(counts.values()), "record_counts": counts,
            "only_complete_success_summaries": True}


_ORIGINAL_ROOT = _base.root
_ORIGINAL_STAGE = _base.stage_script
_ORIGINAL_SYNC = _base.acquire_sync
_ORIGINAL_LAUNCH = _base.launch_collector
_ORIGINAL_RUNNING = _base.collector_running
_ORIGINAL_FETCH_TRANSPORT = _base.fetch_collector_transport
_ORIGINAL_FETCH_FILE = _base.fetch_file
_ORIGINAL_SALVAGE = _base.salvage_partial
_ORIGINAL_QUIESCE = _base.quiesce_remote
_ORIGINAL_CLEANUP = _base.cleanup_remote
_ORIGINAL_RUN = _base.run_capture


def root(command: str, timeout: int, audit_prefix: Path | None = None):
    return _ORIGINAL_ROOT(_harden_procstat(command), timeout, audit_prefix)


@contextlib.contextmanager
def _patched_base():
    names = {"root": root, "build_remote_script": build_remote_script,
             "validate_metadata": validate_metadata, "analyze_samples": analyze_samples,
             "validate_dd_summaries": validate_dd_summaries,
             "REMOTE_ROOT": REMOTE_ROOT, "STAGE_ROOT": STAGE_ROOT}
    previous = {name: getattr(_base, name) for name in names}
    for name, value in names.items():
        setattr(_base, name, value)
    try:
        yield
    finally:
        for name, value in previous.items():
            setattr(_base, name, value)


def _call_with_root(function, *args, **kwargs):
    previous = _base.root
    _base.root = root
    try:
        return function(*args, **kwargs)
    finally:
        _base.root = previous


def stage_script(label, script): return _call_with_root(_ORIGINAL_STAGE, label, script)
def acquire_sync(): return _call_with_root(_ORIGINAL_SYNC)
def launch_collector(label, stage, target_uptime, audit_dir=None):
    return _call_with_root(_ORIGINAL_LAUNCH, label, stage, target_uptime, audit_dir)
def collector_running(label, identity): return _call_with_root(_ORIGINAL_RUNNING, label, identity)
def fetch_collector_transport(label, destination):
    return _call_with_root(_ORIGINAL_FETCH_TRANSPORT, label, destination)
def fetch_file(path, size, digest): return _call_with_root(_ORIGINAL_FETCH_FILE, path, size, digest)
def salvage_partial(label, destination): return _call_with_root(_ORIGINAL_SALVAGE, label, destination)
def quiesce_remote(label): return _call_with_root(_ORIGINAL_QUIESCE, label)
def cleanup_remote(label): return _call_with_root(_ORIGINAL_CLEANUP, label)


def run_capture(label: str, seconds: int, smoke_unobserved: bool = False) -> None:
    with _patched_base():
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
    raw = shell.encode()
    digest = hashlib.sha256(raw).hexdigest()
    largest = len(("set -eu\nprintf %s " + "A" * len(base64.b64encode(b"x" * 4096)) +
                   f" | base64 -d >>{STAGE_ROOT}/{args.label}/capture.sh").encode())
    require(largest <= 8192, "staging command exceeds controller limit")
    if not args.run:
        if args.emit_shell:
            print(shell, end="")
        else:
            print(json.dumps({
                "mode": "dry-run; no TV/network/root call", "seconds": args.seconds,
                "capture_kind": "smoke-unobserved" if args.smoke_unobserved else "full-observed",
                "frozen_observer_sha256": FROZEN_SHA256,
                "staged_script_bytes": len(raw), "staged_script_sha256": digest,
                "largest_staging_command_bytes": largest,
                "remote_root": REMOTE_ROOT, "stage_root": STAGE_ROOT,
                "trace_namespace": TRACE_PREFIX,
                "samplers": {"monitor_hz": "about 5 independent loop",
                             "base_qd_branch_hz": "about 1 independent loop",
                             "qd_row_span_limit_seconds": ROW_SPAN_MAX_SECONDS},
                "qd_class_required": "QDDimming",
                "backend_required": "DimmingBackendRoseMQD slot +0xd8",
                "physical_state": "unobserved" if args.smoke_unobserved else
                                  "only local observer annotations during --run",
                "active_branch_inferred": False, "diagnostic_eligible": False,
                "execution_guard": "--run --reviewed",
            }, indent=2))
        return
    require(args.reviewed, "live execution requires both --run and --reviewed after parent review")
    require(not (BASE / (args.label + ".onset")).exists(), "existing local capture refused")
    run_capture(args.label, args.seconds, smoke_unobserved=args.smoke_unobserved)


if __name__ == "__main__":
    main()
