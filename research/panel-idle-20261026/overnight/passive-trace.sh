set -eu
grep -qx 'BUILD_ID=T-RSMFAKUC-0090-REL-202607141953' /etc/tizen-release
TRACE_DIR=/sys/kernel/debug/tracing/instances/researcher-black-20261026
TRACE_OUT=/tmp/researcher-panel-trace-20261026/passive-black-i2c.trace
test ! -e "$TRACE_DIR"
test ! -e "$TRACE_OUT"
mkdir "$TRACE_DIR"
cleanup() {
  echo 0 > "$TRACE_DIR/tracing_on" || true
  echo 0 > "$TRACE_DIR/events/enable" || true
  rmdir "$TRACE_DIR" || true
}
trap cleanup EXIT HUP INT TERM
echo 0 > "$TRACE_DIR/tracing_on"
echo 64 > "$TRACE_DIR/buffer_size_kb"
echo mono > "$TRACE_DIR/trace_clock"
for event_name in i2c_write i2c_read i2c_reply i2c_result; do
  echo 'adapter_nr == 5' > "$TRACE_DIR/events/i2c/$event_name/filter"
  echo 1 > "$TRACE_DIR/events/i2c/$event_name/enable"
done
for event_name in sys_enter sys_exit; do
  echo 'common_pid == 1013 && (id == 54 || id == 29)' > "$TRACE_DIR/events/raw_syscalls/$event_name/filter"
  echo 1 > "$TRACE_DIR/events/raw_syscalls/$event_name/enable"
done
echo 1 > "$TRACE_DIR/tracing_on"
sleep 2
echo 0 > "$TRACE_DIR/tracing_on"
cat "$TRACE_DIR/trace" > "$TRACE_OUT"
date -u
cat /proc/uptime
wc -c "$TRACE_OUT"
sha256sum "$TRACE_OUT"
