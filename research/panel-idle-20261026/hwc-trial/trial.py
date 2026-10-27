#!/usr/bin/env python3
"""DISABLED historical probe: original mapping inference was wrong.

Live mapping is CLI0 -> deactive1 (fallback), CLI1 -> deactive0 (normal).
See actual-restored.json and ../hwc-prevention/trial.py. Historical artifacts
active.json/restored.json retain their original misleading labels.
"""
raise SystemExit('Disabled historical probe: use reviewed hwc-prevention trial; see mapping correction')

from pathlib import Path
import json
import subprocess
import time
import shlex

BASE = Path(__file__).resolve().parent
ACCESS = BASE.parents[1]/'root-access/s95f-access.py'
BUILD = 'T-RSMFAKUC-0090-REL-202607141953'

def root(command, filename):
    r = subprocess.run(['python3',str(ACCESS),'root','--timeout','25','--command',command],
                       capture_output=True,text=True,timeout=50)
    (BASE/filename).write_text(r.stdout)
    (BASE/(filename+'.stderr')).write_text(r.stderr)
    if r.returncode:
        raise RuntimeError('root request failed')
    c = json.loads(r.stdout)['commands'][0]
    if c['exit_code'] or c['timed_out']:
        raise RuntimeError('TV command failed')
    return c['stdout']

if (BASE/'baseline.json').exists():
    raise SystemExit('Existing trial evidence; no automatic rerun')
before = root('date -u\ncat /proc/uptime\nenlightenment_info -hwc_wins','baseline.json')
if 'deactive:0 ' not in before:
    raise SystemExit('HWC baseline is not deactive0; refused')
expiry = ('sleep 105\n'
          f'grep -qx {shlex.quote("BUILD_ID="+BUILD)} /etc/tizen-release || exit 70\n'
          'enlightenment_info -hwc 0\nsleep 1\nenlightenment_info -hwc_wins\n')
subprocess.run(['/bin/sh','-n'],input=expiry,text=True,check=True)
(BASE/'tv-expiry-source.sh').write_text(expiry)
launch = (f'/bin/sh -c {shlex.quote(expiry)} '
          '> /tmp/researcher-panel-trace-20261026/hwc-expiry.log 2>&1 < /dev/null &\n'
          'expiry_pid=$!\nsleep 1\nkill -0 "$expiry_pid"\n'
          'printf "expiry_pid=%s\\n" "$expiry_pid"')
print(root(launch,'expiry-launch.json').strip(),flush=True)
try:
    active = root('date -u\ncat /proc/uptime\nenlightenment_info -hwc 1\nsleep 1\n'
                  'enlightenment_info -hwc_wins\nenlightenment_info -screen_info','active.json')
    if 'deactive:1 ' not in active:
        raise RuntimeError('runtime deactivation did not read back')
    print('HWC_TRIAL_ACTIVE deactive1; parent restores deactive0 after 90 seconds.',flush=True)
    print(active.split('HWC:',1)[-1].splitlines()[0],flush=True)
    time.sleep(90)
finally:
    result = root('date -u\ncat /proc/uptime\nenlightenment_info -hwc 0\nsleep 1\n'
                  'enlightenment_info -hwc_wins\nenlightenment_info -screen_info','restored.json')
    if 'deactive:0 ' not in result:
        raise RuntimeError('restore did not read back deactive0; TV expiry remains armed')
    print('HWC_RESTORED deactive0',flush=True)
