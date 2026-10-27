#!/usr/bin/env python3
"""Five-minute runtime prevention trial. Live verified CLI0=deactive1; restoreCLI1."""
from pathlib import Path
import subprocess
import json
import time
BASE=Path(__file__).resolve().parent
ACCESS=BASE.parents[1]/'root-access/s95f-access.py'
def root(cmd,name):
    r=subprocess.run(['python3',str(ACCESS),'root','--timeout','25','--command',cmd],capture_output=True,text=True,timeout=50)
    (BASE/name).write_text(r.stdout)
    (BASE/(name+'.stderr')).write_text(r.stderr)
    if r.returncode:raise RuntimeError('root request failed')
    c=json.loads(r.stdout)['commands'][0]
    if c['exit_code'] or c['timed_out']:raise RuntimeError('TV request failed')
    return c['stdout']
if (BASE/'before.json').exists():raise SystemExit('Existing trial; no automatic repeat')
before=root('date -u\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\nenlightenment_info -hwc_wins','before.json')
if 'deactive:0 ' not in before:raise SystemExit('Expected normal HWC baseline deactive0')
launch="/bin/sh -c 'sleep 330; enlightenment_info -hwc 1; sleep 2; enlightenment_info -hwc_wins' > /tmp/researcher-panel-trace-20261026/hwc-prevention-expiry.log 2>&1 < /dev/null &\nexpiry_pid=$!\nsleep 1\nkill -0 \"$expiry_pid\"\nprintf 'expiry_pid=%s\\n' \"$expiry_pid\""
print(root(launch,'expiry.json').strip(),flush=True)
try:
    active=root('date -u\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\nenlightenment_info -hwc 0\nsleep 2\nenlightenment_info -hwc_wins','active.json')
    if 'deactive:1 ' not in active:raise RuntimeError('Fallback did not apply')
    print('PREVENTION_ACTIVE: HWC deactive1, baseline restore in five minutes.',flush=True)
    time.sleep(300)
finally:
    for attempt in range(12):
        try:
            restored=root('date -u\ncat /proc/sys/kernel/random/boot_id\nenlightenment_info -hwc 1\nsleep 2\nenlightenment_info -hwc_wins','restored.json')
            if 'deactive:0 ' not in restored:raise RuntimeError('Normal HWC readback missing')
            print('PREVENTION_RESTORED: HWC deactive0',flush=True)
            break
        except Exception:
            if attempt==11:raise
            time.sleep(5)
