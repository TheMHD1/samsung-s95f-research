#!/usr/bin/env python3
"""One bounded read-only sample of AVOC's HDMI control backend slot; default dry."""
from pathlib import Path
import hashlib
import importlib.util

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'read-pm-idle-format.py'
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != '47262917994451714b3dbfb8f53d761c61232587f2e83b3303cd5ce94a1b28e9':
    raise ValueError('frozen acquisition helper changed')
INPUTS = {
    HERE/'serdes-hdmi-control-copy-20261026/libhdmi-control.so.0.1':
        '067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410',
    HERE/'serdes-hdmi-control-impl-copy-20261026/libhdmi-control-impl-sec.so.0.1':
        '5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1',
}
for path, expected in INPUTS.items():
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('static derivation input changed: '+str(path))
spec = importlib.util.spec_from_file_location('fixed_hdmi_control_binding', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.__doc__ = __doc__
module.DEST = HERE/'hdmi-control-binding-20261026'
module.COMMAND = '''set -euo pipefail
P=706
MAIN=/usr/lib/libhdmi-control.so.0.1
IMPL=/prd/usr/lib/libhdmi-control-impl-sec.so.0.1
starttime() { s=$(cat /proc/$P/stat); case "$s" in *') '*) ;; *) return 1;; esac; s=${s##*) }; set -- $s; test "$#" -ge 20; echo "${20}"; }
sourceok() {
  sourcepath=$1
  sourceidentity=$(stat -c '%d %i' "$sourcepath") || return 1
  set -- $sourceidentity; test "$#" = 2 || return 1
  for number in "$@"; do case "$number" in ''|*[!0-9]*) return 1;; esac; done
  sourcedev=$(printf '%02x:%02x' $((($1>>8)&4095)) $((($1&255)|(($1>>12)&1048320)))) || return 1
  sourceinode=$2
  LC_ALL=C awk -v p="$sourcepath" -v d="$sourcedev" -v i="$sourceinode" 'BEGIN{n=0;bad=0} $NF==p{n++;if($4!=d || $5!=i)bad=1} END{exit(n>0 && bad==0?0:1)}' /proc/$P/maps || return 1
  echo "$sourceidentity $sourcedev $sourcepath"
}
identity() {
  b=$(cat /proc/sys/kernel/random/boot_id); echo "$b"; test "$b" = 00000000-0000-4000-8000-000000000000
  readlink -f /proc/$P/exe; test "$(readlink -f /proc/$P/exe)" = /usr/bin/avocd
  st=$(starttime); echo "$P $st"; test "$st" = 603
  sha256sum "$MAIN" "$IMPL"
  test "$(sha256sum "$MAIN" | cut -d' ' -f1)" = 067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410
  test "$(sha256sum "$IMPL" | cut -d' ' -f1)" = 5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1
  sourceok "$MAIN"
  sourceok "$IMPL"
}
mapok() {
  q=$1; z=$2; test "$q" -gt 0 || return 1; test "$z" -gt 0 || return 1
  test $((q%4)) = 0 || return 1; test $((z%4)) = 0 || return 1; test $((q+z)) -lt 4294967296 || return 1
  qh=$(printf '%08x' "$q") || return 1; eh=$(printf '%08x' $((q+z))) || return 1
  LC_ALL=C awk -v q="x$qh" -v e="x$eh" 'BEGIN{ok=0} {split($1,a,"-"); if(length(a[1])==8 && length(a[2])==8 && substr($2,1,1)=="r" && q>="x" a[1] && e<="x" a[2])ok=1} END{exit(ok?0:1)}' /proc/$P/maps
}
u32() {
  mapok "$1" 4 || return 1
  octets=$(dd if=/proc/$P/mem bs=4 skip=$(($1/4)) count=1 | od -An -tu1) || return 1
  set -- $octets; test "$#" = 4 || return 1
  for octet in "$@"; do case "$octet" in ''|*[!0-9]*) return 1;; esac; test "$octet" -le 255 || return 1; done
  printf '%s' $(($1+($2<<8)+($3<<16)+($4<<24)))
}
loadbases() {
  mh=$(awk -v p="$MAIN" '$2=="r-xp" && $3=="00000000" && $NF==p{split($1,a,"-");print a[1]}' /proc/$P/maps)
  ih=$(awk -v p="$IMPL" '$2=="r-xp" && $3=="00000000" && $NF==p{split($1,a,"-");print a[1]}' /proc/$P/maps)
  case "$mh:$ih" in *[!0-9a-f:]*|:|:*|*:) return 1;; esac
  test "${#mh}" = 8 || return 1; test "${#ih}" = 8 || return 1
  mb=$((0x$mh-0x47e10000)); ib=$((0x$ih)); test "$mb" -ge 0 || return 1
  echo "$mb $ib"
}
snapshot() {
  mainword=$(u32 "$MAIN_GETTER") || return 1
  implword=$(u32 $((EXPECTED_CALLBACK-1))) || return 1
  test "$mainword" = 1148733441 || return 1
  test "$implword" = 4022383920 || return 1
  flag=$(u32 "$STORAGE") || return 1
  table=$(u32 $((STORAGE+4))) || return 1
  test "$flag" -ne 0 || return 1
  mapok "$table" 60 || return 1
  callback=$(u32 $((table+0x38))) || return 1
  test $((callback%2)) = 1 || return 1
  test "$callback" = "$EXPECTED_CALLBACK" || return 1
  echo "$flag $table $callback $mainword $implword"
}
selectedmaps() {
  th=$(printf '%08x' "$TABLE"); te=$(printf '%08x' $((TABLE+60)))
  LC_ALL=C awk -v m="$MAIN" -v i="$IMPL" -v q="x$th" -v e="x$te" '$NF==m || $NF==i{print;next} {split($1,a,"-");if(length(a[1])==8 && length(a[2])==8 && q>="x" a[1] && e<="x" a[2])print}' /proc/$P/maps
}
echo '@@ TIME_START'; date -u +%s; cat /proc/uptime
echo '@@ ID_START'; identity
BASES_START=$(loadbases); set -- $BASES_START; MAIN_BIAS=$1; IMPL_BIAS=$2
STORAGE=$((MAIN_BIAS+0x47e834fc)); EXPECTED_CALLBACK=$((IMPL_BIAS+0x8575))
MAIN_GETTER=$((MAIN_BIAS+0x47e613a4))
sh=$(printf '%08x' "$STORAGE"); se=$(printf '%08x' $((STORAGE+8)))
LC_ALL=C awk -v p="$MAIN" -v q="x$sh" -v e="x$se" 'BEGIN{ok=0} $NF==p && substr($2,1,1)=="r"{split($1,a,"-");if(length(a[1])==8 && length(a[2])==8 && q>="x" a[1] && e<="x" a[2])ok=1} END{exit(ok?0:1)}' /proc/$P/maps
gh=$(printf '%08x' "$MAIN_GETTER"); ge=$(printf '%08x' $((MAIN_GETTER+4)))
LC_ALL=C awk -v p="$MAIN" -v q="x$gh" -v e="x$ge" 'BEGIN{ok=0} $NF==p && $2=="r-xp"{split($1,a,"-");if(length(a[1])==8 && length(a[2])==8 && q>="x" a[1] && e<="x" a[2])ok=1} END{exit(ok?0:1)}' /proc/$P/maps
ch=$(printf '%08x' $((EXPECTED_CALLBACK-1))); ce=$(printf '%08x' $((EXPECTED_CALLBACK+3)))
LC_ALL=C awk -v p="$IMPL" -v q="x$ch" -v e="x$ce" 'BEGIN{ok=0} $NF==p && $2=="r-xp"{split($1,a,"-");if(length(a[1])==8 && length(a[2])==8 && q>="x" a[1] && e<="x" a[2])ok=1} END{exit(ok?0:1)}' /proc/$P/maps
echo '@@ BASES'; echo "$MAIN_BIAS $IMPL_BIAS $STORAGE $EXPECTED_CALLBACK"
SNAP_START=$(snapshot); set -- $SNAP_START; TABLE=$2
MAPS_START=$(selectedmaps)
echo '@@ MAPS_START'; echo "$MAPS_START"
echo '@@ VALUES_START'; echo "$SNAP_START"
SNAP_END=$(snapshot)
echo '@@ VALUES_END'; echo "$SNAP_END"
MAPS_END=$(selectedmaps)
echo '@@ MAPS_END'; echo "$MAPS_END"
test "$SNAP_START" = "$SNAP_END"; test "$MAPS_START" = "$MAPS_END"
BASES_END=$(loadbases); test "$BASES_START" = "$BASES_END"
echo '@@ ID_END'; identity
echo '@@ TIME_END'; date -u +%s; cat /proc/uptime
echo '@@ COMPLETE'; echo PASS_SAMPLED_BINDING_ONLY
'''
if len(module.COMMAND.encode()) > 8192:
    raise ValueError('root command exceeds fixed bound')

if __name__ == '__main__':
    module.main()
