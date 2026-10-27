#!/usr/bin/env python3
"""Bounded static-event capture, no panel/config setters. Must be coordinated with owner."""
from pathlib import Path
import argparse,base64,hashlib,json,re,shlex,subprocess
BASE=Path(__file__).resolve().parent
ACCESS=BASE.parents[1]/'root-access/s95f-access.py'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('label');p.add_argument('--seconds',type=int,choices=range(5,46),default=25)
p.add_argument('--run',action='store_true',help='Execute; default prints reviewed script only')
a=p.parse_args()
if not re.fullmatch(r'[a-z][a-z0-9-]{0,30}',a.label):p.error('Use a unique lowercase label')
tr='/sys/kernel/debug/tracing/instances/researcher-'+a.label
out='/tmp/researcher-panel-trace-20261026/'+a.label+'.trace'
script='''set -eu
grep -qx 'BUILD_ID=T-RSMFAKUC-0090-REL-202607141953' /etc/tizen-release
TRACE_DIR=TRDIR
TRACE_OUT=OUTFILE
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
/usr/bin/setsid /bin/sh -c 'sleep EXPIRY; if test -d TRDIR; then echo 0 > TRDIR/tracing_on; echo 0 > TRDIR/events/enable; rmdir TRDIR; fi' > OUTFILE.expiry.log 2>&1 < /dev/null &
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
sleep DURATION
echo 0 > "$TRACE_DIR/tracing_on"
cat "$TRACE_DIR/trace" > "$TRACE_OUT"
cat /proc/uptime
wc -c "$TRACE_OUT"
sha256sum "$TRACE_OUT"
'''.replace('TRDIR',tr).replace('OUTFILE',out).replace('EXPIRY',str(a.seconds+10)).replace('DURATION',str(a.seconds))
if not a.run:print(script);raise SystemExit
if (BASE/(a.label+'.json')).exists():raise SystemExit('Existing capture refused')

def root(cmd,timeout=25):
 r=subprocess.run(['python3',str(ACCESS),'root','--persistent-only','--timeout',str(timeout),'--command',cmd],capture_output=True,text=True,timeout=timeout+20)
 try:c=json.loads(r.stdout)['commands'][0]
 except Exception:raise RuntimeError('Access result unavailable')
 return r,c
try:
 (BASE/(a.label+'.sh')).write_text(script)
 r,c=root('/bin/sh -c '+shlex.quote(script),a.seconds+25)
 (BASE/(a.label+'.json')).write_text(r.stdout)
 (BASE/(a.label+'.stderr')).write_text(r.stderr)
 if r.returncode or c['exit_code'] or c['timed_out']:raise RuntimeError('Trace failed; no retry')
 lines=c['stdout'].splitlines();size=int(lines[-2].split()[0]);digest=lines[-1].split()[0]
 if not 0<size<8*1024*1024:raise RuntimeError('Unexpected trace size')
 data=[]
 for i in range((size+131071)//131072):
  r,c=root(f'dd if={shlex.quote(out)} bs=131072 skip={i} count=1 2>/dev/null | base64')
  if r.returncode or c['exit_code']:raise RuntimeError('Trace fetch failed')
  data.append(base64.b64decode(c['stdout']))
 data=b''.join(data)
 if len(data)!=size or hashlib.sha256(data).hexdigest()!=digest:raise RuntimeError('Transfer verification failed')
 (BASE/(a.label+'.trace')).write_bytes(data)
 header=re.search(rb'entries-in-buffer/entries-written: (\d+)/(\d+)',data)
 if not header or int(header[1])!=int(header[2]):raise RuntimeError('Trace ring overflow or missing accounting; saved as incomplete')
 print('SHA verified',size,digest)
finally:
 # Only this unique private instance; global tracing settings are never written.
 cleanup=f'if test -d {tr}; then echo 0 > {tr}/tracing_on; echo 0 > {tr}/events/enable; rmdir {tr}; fi\ncat /sys/kernel/debug/tracing/tracing_on\nls -ld {tr} 2>/dev/null || true'
 try:
  r,c=root(cleanup)
  (BASE/(a.label+'.cleanup.json')).write_text(r.stdout)
 except Exception as exc:
  (BASE/(a.label+'.cleanup-error.txt')).write_text(type(exc).__name__+'; TV expiry must be verified independently')
