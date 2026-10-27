set -eu
grep -qx 'BUILD_ID=T-RSMFAKUC-0090-REL-202607141953' /etc/tizen-release
TRACE_DIR=/sys/kernel/debug/tracing/instances/researcher-output-20261026
TRACE_OUT=/tmp/researcher-panel-trace-20261026/passive-black-output.trace
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
echo 256 > "$TRACE_DIR/buffer_size_kb"
echo mono > "$TRACE_DIR/trace_clock"
for event_name in i2c_write i2c_read i2c_reply i2c_result; do
  echo 'adapter_nr == 5' > "$TRACE_DIR/events/i2c/$event_name/filter"
  if test "$event_name" != i2c_result; then
    echo 'adapter_nr == 5 && addr == 118' > "$TRACE_DIR/events/i2c/$event_name/filter"
  fi
  echo 1 > "$TRACE_DIR/events/i2c/$event_name/enable"
done
for event_path in early_trace/early_event drm/drm_vblank_event drm/drm_vblank_event_queued drm/drm_vblank_event_delivered gpio/gpio_value gpio/gpio_direction clk/clk_set_rate clk/clk_disable clk/clk_enable regulator/regulator_disable regulator/regulator_enable sched/sched_process_exec sched/sched_process_exit; do
  echo 1 > "$TRACE_DIR/events/$event_path/enable"
done
echo 1 > "$TRACE_DIR/tracing_on"
sleep 5
echo 0 > "$TRACE_DIR/tracing_on"
cat "$TRACE_DIR/trace" > "$TRACE_OUT"
date -u
cat /proc/uptime
wc -c "$TRACE_OUT"
sha256sum "$TRACE_OUT"
