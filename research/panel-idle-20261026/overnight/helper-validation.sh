set -eu
grep -qx 'BUILD_ID=T-RSMFAKUC-0090-REL-202607141953' /etc/tizen-release
TRACE_DIR=/sys/kernel/debug/tracing/instances/researcher-helper-validation
TRACE_OUT=/tmp/researcher-panel-trace-20261026/helper-validation.trace
test ! -e "$TRACE_DIR"
test ! -e "$TRACE_OUT"
mkdir "$TRACE_DIR"
cleanup() {
 echo 0 > "$TRACE_DIR/tracing_on" || true
 echo 0 > "$TRACE_DIR/events/enable" || true
 rmdir "$TRACE_DIR" || true
}
trap cleanup EXIT HUP INT TERM
# Independent finite cleanup if caller/shell is lost; never touch global instance.
/usr/bin/setsid /bin/sh -c 'sleep 25; if test -d /sys/kernel/debug/tracing/instances/researcher-helper-validation; then echo 0 > /sys/kernel/debug/tracing/instances/researcher-helper-validation/tracing_on; echo 0 > /sys/kernel/debug/tracing/instances/researcher-helper-validation/events/enable; rmdir /sys/kernel/debug/tracing/instances/researcher-helper-validation; fi' > /tmp/researcher-panel-trace-20261026/helper-validation.trace.expiry.log 2>&1 < /dev/null &
expiry_pid=$!
kill -0 "$expiry_pid"
echo 0 > "$TRACE_DIR/tracing_on"
echo 512 > "$TRACE_DIR/buffer_size_kb"
echo mono > "$TRACE_DIR/trace_clock"
for ev in i2c_write i2c_read i2c_reply; do
 echo 'adapter_nr == 5 && addr == 118' > "$TRACE_DIR/events/i2c/$ev/filter"
 echo 1 > "$TRACE_DIR/events/i2c/$ev/enable"
done
echo 'adapter_nr == 5' > "$TRACE_DIR/events/i2c/i2c_result/filter"
echo 1 > "$TRACE_DIR/events/i2c/i2c_result/enable"
for ev in early_trace/early_event drm/drm_vblank_event gpio/gpio_value gpio/gpio_direction clk/clk_set_rate clk/clk_disable clk/clk_enable regulator/regulator_disable regulator/regulator_enable sched/sched_process_exec sched/sched_process_exit; do
 echo 1 > "$TRACE_DIR/events/$ev/enable"
done
date -u
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
echo 1 > "$TRACE_DIR/tracing_on"
sleep 5
echo 0 > "$TRACE_DIR/tracing_on"
cat "$TRACE_DIR/trace" > "$TRACE_OUT"
cat /proc/uptime
wc -c "$TRACE_OUT"
sha256sum "$TRACE_OUT"
