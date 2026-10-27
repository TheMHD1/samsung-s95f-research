set -eu
umask 077
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
test "$(cat /sys/kernel/debug/tracing/tracing_on)" = 0
t=/sys/kernel/debug/tracing/instances/researcher-sdp-checkpoints-ecca06115fee435f92575069b2cd120c
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
echo 64 > "$t/buffer_size_kb"
echo 0 > "$t/events/enable"
for e in sdpsoc/sdp_mem_ioctl sdpsoc/sdp_mem_dbg sdpsoc/sdp_hwmem_ioctl sdpsoc/sdp_hwmem_dbg printk/console; do
 test -f "$t/events/$e/enable"
 echo 1 > "$t/events/$e/enable"
done
echo CHECKPOINT_START
cat /proc/uptime
echo 1 > "$t/tracing_on"
echo researcher_SDP_CHECKPOINT_BEGIN > "$t/trace_marker"
sleep 5
echo researcher_SDP_CHECKPOINT_END > "$t/trace_marker"
echo 0 > "$t/tracing_on"
echo CHECKPOINT_END
cat /proc/uptime
echo TRACE_BYTES
wc -c < "$t/trace"
echo TRACE_BEGIN
dd if="$t/trace" bs=65536 count=2 2>/dev/null
echo TRACE_END
echo STATS_BEGIN
for p in "$t"/per_cpu/cpu*/stats; do echo "$p"; cat "$p"; done
echo STATS_END
cleanup
created=0
test ! -e "$t"
test "$(cat /sys/kernel/debug/tracing/tracing_on)" = 0
echo CLEANUP_VERIFIED
