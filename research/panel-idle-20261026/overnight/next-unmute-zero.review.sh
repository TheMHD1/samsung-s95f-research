set -eu
grep -qx 'BUILD_ID=T-RSMFAKUC-0090-REL-202607141953' /etc/tizen-release
TRACE_DIR=/sys/kernel/debug/tracing/instances/researcher-next-unmute-zero
TRACE_OUT=/tmp/researcher-panel-trace-20261026/next-unmute-zero.trace
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
/usr/bin/setsid /bin/sh -c 'sleep 37; if test -d /sys/kernel/debug/tracing/instances/researcher-next-unmute-zero; then echo 0 > /sys/kernel/debug/tracing/instances/researcher-next-unmute-zero/tracing_on; echo 0 > /sys/kernel/debug/tracing/instances/researcher-next-unmute-zero/events/enable; rmdir /sys/kernel/debug/tracing/instances/researcher-next-unmute-zero; fi' > /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.expiry.log 2>&1 < /dev/null &
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
cat /proc/uptime > /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.GetPanelMute > /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe.mute
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.GetPanelMuteCaseStatus > /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe.case
cat /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe.mute /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe.case >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe
awk '$1 == "int32" {if ($2 != 0) bad=1; count++} END {exit (count != 2 || bad)}' /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe.mute
awk '$1 == "int32" {if ($2 != 0) bad=1; count++} END {exit (count != 2 || bad)}' /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe.case
echo 1 > "$TRACE_DIR/tracing_on"
sleep 2
echo BEFORE_SINGLE_UNMUTE_ZERO > "$TRACE_DIR/trace_marker"
cat /proc/uptime >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe
echo UNMUTE_REPLY_BEGIN >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe
probe_status=0
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.SetPanelMute int32:0 >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe 2>&1 || probe_status=$?
echo "PROBE_DBUS_EXIT=$probe_status" >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe
echo UNMUTE_REPLY_END >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe
cat /proc/uptime >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe
echo AFTER_SINGLE_UNMUTE_ZERO > "$TRACE_DIR/trace_marker"
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.GetPanelMute >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe 2>&1 || true
dbus-send --system --print-reply --reply-timeout=1500 --dest=org.tizen.tv.avoc /org/tizen/tv/avoc org.tizen.tv.avoc.AvOutputControl.GetPanelMuteCaseStatus >> /tmp/researcher-panel-trace-20261026/next-unmute-zero.trace.probe 2>&1 || true
sleep 10
echo 0 > "$TRACE_DIR/tracing_on"
cat "$TRACE_DIR/trace" > "$TRACE_OUT"
cat /proc/uptime
wc -c "$TRACE_OUT"
sha256sum "$TRACE_OUT"


