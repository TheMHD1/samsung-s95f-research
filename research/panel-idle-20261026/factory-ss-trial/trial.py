#!/usr/bin/env python3
"""One exact factory scalar test; no firmware/register writes. Potentially persistent.

No trial may run until ENABLED is set after reviewing the matching setter path.
The TV expiry and separate host watchdog both restore the recorded baseline.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
ACCESS = BASE.parents[1] / 'root-access/s95f-access.py'
STATE = BASE / 'state.json'
BUILD = 'T-RSMFAKUC-0090-REL-202607141953'
KEY = 60802
LABEL = 'Screen Saver Brightness'
DB = ('dbus-send --system --print-reply --reply-timeout=1500 '
      '--dest=org.tizen.tv.factory-service /TIFacSerObj org.tizen.tv.factoryservice.')
GET = DB + 'GetItem int32:60802'
SET7 = DB + 'SetDecimalValue int32:60802 int32:7'
SET0 = DB + 'SetDecimalValue int32:60802 int32:0'
ENABLED = False  # One reviewed trial completed and restored; no unattended rerun.


def root(command, name=None):
    result = subprocess.run([sys.executable, str(ACCESS), 'root', '--timeout', '25',
                             '--command', command], capture_output=True, text=True, timeout=50)
    if name:
        (BASE / name).write_text(result.stdout)
    if result.returncode:
        raise RuntimeError('TV request failed: ' + result.stderr[:300])
    item = json.loads(result.stdout)['commands'][0]
    if item['timed_out'] or item['exit_code']:
        raise RuntimeError('TV command failed')
    return item['stdout']


def parse_item(text):
    ints = [int(x) for x in re.findall(r'^\s+int32 (-?\d+)\s*$', text, re.M)]
    strings = re.findall(r'^\s+string "([^"\n]*)"\s*$', text, re.M)
    byte = re.findall(r'^\s+byte (\d+)\s*$', text, re.M)
    if len(ints) != 6 or ints[-1] != 1 or len(strings) != 2 or len(byte) != 1:
        raise RuntimeError('unexpected factory item response')
    return {'fields': ints[:5], 'enabled': int(byte[0]), 'value': strings[0], 'label': strings[1]}


def target(text):
    item = parse_item(text)
    if item['fields'] != [KEY, 0, 5, 5, 5] or item['label'] != LABEL or item['enabled'] != 1:
        raise RuntimeError('factory item identity mismatch')
    if item['value'] not in ('0', '7'):
        raise RuntimeError('unexpected setting; refusing overwrite')
    return item


def snapshot(name):
    text = root('\n'.join(DB + f'GetChildItem int32:802 int32:{i}' for i in range(36)), name)
    blocks = text.split('method return')[1:]
    if len(blocks) != 36:
        raise RuntimeError('incomplete QD subtree')
    return [parse_item(block) for block in blocks]


def restore():
    state = json.loads(STATE.read_text())
    if state['baseline'] != '7' or state['key'] != KEY or state['build'] != BUILD:
        raise RuntimeError('baseline identity mismatch')
    item = target(root(GET))
    if item['value'] == '0':
        root(SET7, 'restore-response.json')
    if target(root(GET, 'restored-item.json'))['value'] != '7':
        raise RuntimeError('restore readback failed')
    after = snapshot('qd-restored.json')
    deltas = [{'before': old, 'after': new} for old, new in zip(state['qd_before'], after) if old != new]
    (BASE/'qd-deltas.json').write_text(json.dumps(deltas, indent=2))
    if deltas:
        print('Baseline 7 restored; QD deltas recorded for review: ' + str(len(deltas)), flush=True)
    else:
        print('Baseline 7 restored; all 36 QD menu items match.', flush=True)
    (BASE/'restored.json').write_text(json.dumps({'verified_unix': time.time(), 'value': '7'}))


def watch():
    state = json.loads(STATE.read_text())
    time.sleep(max(0, state['expires_unix'] + 30 - time.time()))
    while True:
        try:
            restore()
            return
        except Exception as exc:
            print('restore retry: ' + str(exc), flush=True)
            time.sleep(10)


def trial():
    if not ENABLED:
        raise RuntimeError('disabled pending matching setter/range review')
    if STATE.exists():
        raise RuntimeError('existing baseline; inspect/restore before another test')
    before = snapshot('qd-before.json')
    if target(root(GET, 'target-before.json'))['value'] != '7':
        raise RuntimeError('trial requires baseline 7')
    checks = root('cat /proc/sys/kernel/random/boot_id\n'
                  'dbus-send --system --print-reply --dest=org.tizen.system.deviced '
                  '/Org/Tizen/System/DeviceD/Display '
                  'org.tizen.system.deviced.display.BurnInProtectionInProgress\n'
                  'dbus-send --system --print-reply --dest=org.tizen.system.deviced '
                  '/Org/Tizen/System/DeviceD/Display '
                  'org.tizen.system.deviced.display.GetLockCount string:lcdon\n'
                  'dbus-send --system --print-reply --dest=org.tizen.system.deviced '
                  '/Org/Tizen/System/DeviceD/Display '
                  'org.tizen.system.deviced.display.GetPowerState', 'preflight.json')
    if re.findall(r'int32 (-?\d+)', checks) != ['0', '0'] or 'string "lcdon"' not in checks:
        raise RuntimeError('maintenance/lock/power preflight failed')
    boot = checks.splitlines()[0]
    if not re.fullmatch(r'[0-9a-f-]{36}', boot):
        raise RuntimeError('invalid boot identity')
    state = dict(key=KEY, label=LABEL, build=BUILD, boot=boot, baseline='7',
                 expires_unix=time.time()+180, qd_before=before)
    with STATE.open('x') as stream:
        json.dump(state, stream, indent=2)
    os.chmod(STATE, 0o600)
    with (BASE/'host-watchdog.log').open('x') as log:
        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'watch'],
                                stdout=log, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, start_new_session=True)
    print('Host restore watchdog PID ' + str(proc.pid), flush=True)
    # Stock shell/tool only. No driver writes; same identified factory scalar.
    tv_restore = ('sleep 195\n'
                  f'grep -qx {shlex.quote("BUILD_ID="+BUILD)} /etc/tizen-release || exit 70\n'
                  'attempt=0\nwhile test "$attempt" -lt 120; do\n'
                  'attempt=$((attempt + 1))\n'
                  f'current=$({GET})\n'
                  'if ! printf "%s\\n" "$current" | grep -qx \'      int32 60802\'; then sleep 10; continue; fi\n'
                  f'printf "%s\\n" "$current" | grep -qx \'      string "{LABEL}"\' || exit 71\n'
                  'if printf "%s\\n" "$current" | grep -qx \'      string "7"\'; then printf "%s\\n" "$current"; exit 0; fi\n'
                  'if printf "%s\\n" "$current" | grep -qx \'      string "0"\'; then\n'
                  f'result=$({SET7})\nprintf "%s\\n" "$result"\n'
                  'printf "%s\\n" "$result" | grep -qx \'      int32 1\' || { sleep 10; continue; }\n'
                  'else exit 72\nfi\n'
                  f'verified=$({GET})\n'
                  'if printf "%s\\n" "$verified" | grep -qx \'      int32 60802\' && '
                  f'printf "%s\\n" "$verified" | grep -qx \'      string "{LABEL}"\' && '
                  'printf "%s\\n" "$verified" | grep -qx \'      string "7"\'; then printf "%s\\n" "$verified"; exit 0; fi\n'
                  'sleep 1\ndone\nexit 73\n')
    # Validate the generated stock-shell watchdog without running it on the TV.
    subprocess.run(['/bin/sh', '-n'], input=tv_restore, text=True, check=True)
    (BASE/'tv-expiry-source.sh').write_text(tv_restore)
    logpath = '/home/researcher/share/tmp/sdk_tools/researcher-live-cast/factory-ss-expiry-20261026.log'
    launch = (f'/bin/sh -c {shlex.quote(tv_restore)} > {shlex.quote(logpath)} 2>&1 < /dev/null &\n'
              'expiry_pid=$!\nsleep 1\nkill -0 "$expiry_pid"\n'
              'printf "expiry_pid=%s\\n" "$expiry_pid"')
    print(root(launch, 'tv-watchdog-launch.json').strip(), flush=True)
    try:
        now = root('cat /proc/sys/kernel/random/boot_id\n' + GET)
        if now.splitlines()[0] != boot or target(now)['value'] != '7':
            raise RuntimeError('boot or scalar changed before test')
        response = root(SET0, 'set-zero-response.json')
        print(response, flush=True)
        if re.findall(r'^\s+int32 (-?\d+)\s*$', response, re.M) != ['1']:
            raise RuntimeError('factory setter did not report success')
        if target(root(GET, 'zero-readback.json'))['value'] != '0':
            raise RuntimeError('zero readback failed')
        print('TRIAL_ACTIVE: only Screen Saver Brightness is 0; expiry restores 7.', flush=True)
        while time.time() < state['expires_unix']:
            time.sleep(min(5, max(0, state['expires_unix']-time.time())))
    finally:
        # The independent watchers remain armed even if this process terminates.
        for attempt in range(6):
            try:
                restore()
                break
            except Exception:
                if attempt == 5:
                    raise
                time.sleep(2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['query', 'trial', 'restore', 'watch'])
    action = parser.parse_args().action
    if action == 'query':
        print(json.dumps(target(root(GET)), indent=2))
    else:
        globals()[action]()
