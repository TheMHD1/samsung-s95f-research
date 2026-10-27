set -eu
umask 077
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
test "$(cat /sys/kernel/debug/tracing/tracing_on)" = 0
test "$(readlink /proc/706/exe)" = /usr/bin/avocd
test "$(cat /proc/706/task/1011/comm)" = AVEMonMain
ps0=$(sed 's/.*) //' /proc/706/stat | awk '{print $20}')
ts0=$(sed 's/.*) //' /proc/706/task/1011/stat | awk '{print $20}')
test "$ps0" -gt 0
test "$ts0" -gt 0
fd21=$(readlink /proc/706/fd/21)
fd33=$(readlink /proc/706/fd/33)
test "$fd21" = /dev/tztv_frc
test "$fd33" = /dev/dri/card0
t=/sys/kernel/debug/tracing/instances/researcher-avemon-syscall-e5283bd06bc04479983072c7b94d97f5-v3
test ! -e "$t"
created=0
cleanup() {
 trap - EXIT HUP INT TERM
 if test "$created" = 1; then
  echo 0 > "$t/tracing_on"
  echo 0 > "$t/events/enable"
  rmdir "$t"
 fi
}
trap cleanup EXIT HUP INT TERM
mkdir "$t"
created=1
echo 0 > "$t/tracing_on"
echo 128 > "$t/buffer_size_kb"
echo mono > "$t/trace_clock"
echo 0 > "$t/events/enable"
for e in raw_syscalls/sys_enter raw_syscalls/sys_exit; do
 test -f "$t/events/$e/enable"
 echo 'common_pid == 1011' > "$t/events/$e/filter"
 echo 1 > "$t/events/$e/enable"
done
echo IDENTITY_BEGIN
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
echo "$ps0 $ts0"
echo "21 $fd21"
echo "33 $fd33"
echo CONFIG_BEGIN
cat "$t/trace_clock"
cat "$t/buffer_size_kb"
for e in raw_syscalls/sys_enter raw_syscalls/sys_exit; do
 echo "$e"
 cat "$t/events/$e/format"
 cat "$t/events/$e/filter"
 cat "$t/events/$e/enable"
done
echo CONFIG_END
echo 1 > "$t/tracing_on"
echo AVEMON_ALL_SYSCALLS_BEGIN > "$t/trace_marker"
sleep 2
echo AVEMON_ALL_SYSCALLS_END > "$t/trace_marker"
echo 0 > "$t/tracing_on"
echo IDENTITY_END
cat /proc/sys/kernel/random/boot_id
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
cat /proc/uptime
ps1=$(sed 's/.*) //' /proc/706/stat | awk '{print $20}')
ts1=$(sed 's/.*) //' /proc/706/task/1011/stat | awk '{print $20}')
echo "$ps1 $ts1"
test "$ps0" = "$ps1"
test "$ts0" = "$ts1"
test "$(readlink /proc/706/exe)" = /usr/bin/avocd
test "$(cat /proc/706/task/1011/comm)" = AVEMonMain
test "$(readlink /proc/706/fd/21)" = "$fd21"
test "$(readlink /proc/706/fd/33)" = "$fd33"
echo "21 $fd21"
echo "33 $fd33"
ns=0
for p in "$t"/per_cpu/cpu*/stats; do
 test -f "$p"
 echo "VALIDATING_STATS $p"
 cat "$p"
 ns=$((ns+1))
 awk -F ': ' '
 NF!=2 {bad=1; next}
 {k=$1; v=$2; sub(/^[[:space:]]+/,"",v); sub(/[[:space:]]+$/,"",v); if(seen[k]++) bad=1}
 k=="entries" || k=="bytes" {if(v !~ /^[0-9]+$/) bad=1; next}
 k=="oldest event ts" || k=="now ts" {if(v !~ /^[0-9]+[.][0-9]+$/) bad=1; next}
 k=="overrun" || k=="commit overrun" || k=="dropped events" || k=="read events" {if(v!="0") bad=1; next}
 {bad=1}
 END {if(NR!=8 || bad) exit 1}
 ' "$p"
done
test "$ns" -gt 0
nb=$(wc -c < "$t/trace")
echo "TRACE_RAW_BYTES $nb"
test "$nb" -lt 1048576
packed=$(gzip -c "$t/trace" | base64)
echo "TRACE_PACKED_BYTES ${#packed}"
test "${#packed}" -gt 0
test "${#packed}" -lt 32768
echo TRACE_GZIP_BASE64_BEGIN
echo "$packed"
echo TRACE_GZIP_BASE64_END
echo STATS_BEGIN
for p in "$t"/per_cpu/cpu*/stats; do echo "$p"; cat "$p"; done
echo STATS_END
cleanup
created=0
test ! -e "$t"
test "$(cat /sys/kernel/debug/tracing/tracing_on)" = 0
echo CLEANUP_VERIFIED
