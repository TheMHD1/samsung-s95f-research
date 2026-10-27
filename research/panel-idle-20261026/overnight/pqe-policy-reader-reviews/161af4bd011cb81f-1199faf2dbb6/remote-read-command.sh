set -euo pipefail
P=$(pidof avocd); case "$P" in ''|*[!0-9]*) exit 31;; esac
test "$(readlink /proc/$P/exe)" = /usr/bin/avocd
test "$(sha256sum /usr/bin/avocd|cut -d' ' -f1)" = ab450eaf99c793f3c7a9360629b1a1677e9d86dcd74a1f93796b56ba07401de9
test "$(sha256sum /prd/usr/lib/libave.so.0.1|cut -d' ' -f1)" = a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777
mapok() { q=$1; z=$2; test "$q" -gt 0 || return 1; test "$z" -gt 0 || return 1; test $((q%4)) = 0 || return 1; test $((z%4)) = 0 || return 1; test $((q+z)) -lt 4294967296 || return 1; qh=$(printf '%08x' "$q") || return 1; eh=$(printf '%08x' $((q+z))) || return 1; LC_ALL=C awk -v q="x$qh" -v e="x$eh" 'BEGIN{ok=0} {split($1,a,"-"); if(length(a[1])==8 && length(a[2])==8 && substr($2,1,1)=="r" && q>="x" a[1] && e<="x" a[2]) ok=1} END{exit(ok?0:1)}' /proc/$P/maps; }
u32() { mapok "$1" 4 || return 1; v=$(dd if=/proc/$P/mem bs=4 skip=$(($1/4)) count=1|od -An -tu4|tr -d ' 
'); case "$v" in ''|*[!0-9]*) return 1;; esac; printf %s "$v"; }
emit() { echo "@@ READ_$1"; mapok "$2" $(($3*4)) || return 1; dd if=/proc/$P/mem bs=4 skip=$(($2/4)) count=$3|base64|tr -d '
'; echo; }
starttime() { s=$(cat /proc/$P/stat); case "$s" in *') '*) ;; *) return 1;; esac; s=${s##*) }; set -- $s; test "$#" -ge 20 || return 1; case "${20}" in ''|*[!0-9]*) return 1;; esac; echo "${20}"; }
hx=$(awk '$2 ~ /^r.x/ && $3=="00000000" && $6=="/prd/usr/lib/libave.so.0.1" {split($1,a,"-"); print a[1]}' /proc/$P/maps); test "$(printf %s "$hx"|wc -w)" = 1; A=$((0x$hx))
ptrs() {
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
}
echo '@@ UTC_START'; date -u +%s
echo '@@ UPTIME_START'; cat /proc/uptime
echo '@@ ID_START'; cat /proc/sys/kernel/random/boot_id; echo "$P"; readlink /proc/$P/exe; starttime; sha256sum /usr/bin/avocd /prd/usr/lib/libave.so.0.1
echo '@@ MAPS_START'; cat /proc/$P/maps
echo '@@ POINTERS_START'; PS=$(ptrs); echo "$PS"; set -- $PS; A=$1; VE=$2; VV=$3; VS=$4; DG=$5; DS=$6; G=$7; Q=$8; QV=$9; I=${10}; B=${11}; BV=${12}; BS=${13}; BN=${14}; BT=${15}
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
if test "$BT" = 1; then emit backend_cache $((A+0x5ab958)) 1; fi
if test "$BT" = 2; then emit backend_cache $((A+0x5acb94)) 1; fi
echo '@@ POINTERS_END'; PE=$(ptrs); echo "$PE"; test "$PS" = "$PE"
echo '@@ MAPS_END'; cat /proc/$P/maps
echo '@@ ID_END'; cat /proc/sys/kernel/random/boot_id; echo "$P"; readlink /proc/$P/exe; starttime; sha256sum /usr/bin/avocd /prd/usr/lib/libave.so.0.1
echo '@@ UPTIME_END'; cat /proc/uptime
echo '@@ UTC_END'; date -u +%s
