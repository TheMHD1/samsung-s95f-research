#!/usr/bin/env python3
"""Private tracefs instance: fixed GPIO/IRQ observations, no device requests."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / 'managed-ui-tab-launch/root-with-margin.py'
ROOT_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT = '00000000-0000-4000-8000-000000000000'
EVENTS = {'gpio/gpio_value': 'gpio == 125 || gpio == 121 || gpio == 126 || gpio == 127 || gpio == 425 || gpio == 429 || gpio == 431 || gpio == 148',
          'gpio/gpio_direction': 'gpio == 125 || gpio == 121 || gpio == 126 || gpio == 127 || gpio == 425 || gpio == 429 || gpio == 431 || gpio == 148',
          'irq/irq_handler_entry': 'irq == 30 || irq == 84',
          'irq/irq_handler_exit': 'irq == 30 || irq == 84',
          'power/suspend_resume': None}

def adapter():
    if hashlib.sha256(ROOT.read_bytes()).hexdigest() != ROOT_SHA: raise ValueError('root adapter')
    spec = importlib.util.spec_from_file_location('trace_root', ROOT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def guard():
    return f'set -eu\ntest "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\numask 077\n'

def start(out):
    out.mkdir(mode=0o700)
    nonce = uuid.uuid4().hex
    inst = '/sys/kernel/debug/tracing/instances/s95f_dh_' + nonce
    state = {'schema': 's95f-private-kernel-trace-v1', 'instance': inst,
             'spool': '/tmp/s95f-trace-' + nonce, 'watchdog_seconds': 90,
             'events': EVENTS, 'physical_state': 'unobserved',
             'scope': 'traces existing kernel operations; does not request/change GPIO pins', 'calls': []}
    (out / 'state.json').write_text(json.dumps(state, indent=2) + '\n')
    command = guard() + f'''echo GLOBAL_BEFORE
cat /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/current_tracer
mkdir {inst}
echo 0 >{inst}/tracing_on
echo 128 >{inst}/buffer_size_kb
echo mono >{inst}/trace_clock
'''
    for event, filt in EVENTS.items():
        if filt: command += f'echo {shlex.quote(filt)} >{inst}/events/{event}/filter\n'
        command += f'echo 1 >{inst}/events/{event}/enable\n'
    watchdog = f'sleep 90; echo 0 >{inst}/tracing_on'
    command += f'/bin/sh -c {shlex.quote(watchdog)} </dev/null >/dev/null 2>&1 &\n'
    command += f'''echo WATCHDOG_PID
echo "$!"
cat /proc/uptime
echo 1 >{inst}/tracing_on
echo STARTED
cat {inst}/tracing_on
cat {inst}/trace_clock
echo GLOBAL_AFTER
cat /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/current_tracer
'''
    text = adapter().root(command, state, out / 'start-root.json')
    (out / 'start.txt').write_text(text)
    if 'STARTED\n1\n' not in text: raise ValueError('trace start receipt')
    print(json.dumps({'started': True, 'instance': inst, 'watchdog_seconds': 90, 'device_requests': 0}))

def stop(out):
    state = json.loads((out / 'state.json').read_text())
    inst, spool = state['instance'], state['spool']
    if not re.fullmatch('/sys/kernel/debug/tracing/instances/s95f_dh_[0-9a-f]{32}', inst): raise ValueError('instance path')
    if not re.fullmatch('/tmp/s95f-trace-[0-9a-f]{32}', spool): raise ValueError('spool path')
    if inst.rsplit('_', 1)[1] != spool.rsplit('-', 1)[1]: raise ValueError('instance/spool binding')
    root = adapter()
    command = guard() + f'''echo 0 >{inst}/tracing_on
mkdir {spool}
cat {inst}/trace >{spool}/trace.txt
echo TRACE_BYTES
wc -c <{spool}/trace.txt
echo TRACE_SHA
sha256sum {spool}/trace.txt
echo STATS
for statfile in {inst}/per_cpu/cpu*/stats; do echo "$statfile"; cat "$statfile"; done
echo GLOBAL_AFTER
cat /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/current_tracer
'''
    text = root.root(command, state, out / 'stop-root.json')
    (out / 'stop.txt').write_text(text)
    size = int(text.split('TRACE_BYTES\n', 1)[1].splitlines()[0])
    pin = text.split('TRACE_SHA\n', 1)[1].split()[0]
    if not 0 <= size <= 1048576: raise ValueError('trace spool bound; retained')
    raw = bytearray()
    for i in range(0, size, 16384):
        count = min(16384, size - i)
        chunk = root.root(guard() + f'dd if={spool}/trace.txt bs=1 skip={i} count={count} 2>/dev/null | base64\n',
                          state, out / f'chunk-{i//16384:03}.json')
        decoded = base64.b64decode(''.join(chunk.split()), validate=True)
        if len(decoded) != count: raise ValueError('short trace chunk')
        raw.extend(decoded)
    if hashlib.sha256(raw).hexdigest() != pin: raise ValueError('trace hash')
    (out / 'trace.txt').write_bytes(raw)
    cleanup = guard()
    for event in EVENTS: cleanup += f'echo 0 >{inst}/events/{event}/enable\n'
    cleanup += f'rmdir {inst}\nrm -- {spool}/trace.txt\nrmdir {spool}\n'
    root.root(cleanup, state, out / 'cleanup-root.json')
    result = {'accepted': True, 'retained_bytes': size, 'sha256': pin,
              'instance_removed': True, 'global_tracer_modified': False,
              'physical_state': 'unobserved'}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'stop'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.output.is_absolute(): raise ValueError('absolute output')
    (start if args.action == 'start' else stop)(args.output)

if __name__ == '__main__': main()
