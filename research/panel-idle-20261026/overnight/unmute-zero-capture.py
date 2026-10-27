#!/usr/bin/env python3
"""Prepare one AVOC unmute-zero with a finite private QD trace. Dry-run default.

Execution requires a current physical-black observation supplied by the parent,
not merely a software flag. This script does not validate that observation.
There is no mute-one, power, factory, retry, or persistence operation.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import re
import shlex
import subprocess
import sys

def classify_probe(data):
    """Classify only the public reply; accepted never proves downstream I/O."""
    text = data.decode('utf-8', errors='replace')
    match = re.search(r'^UNMUTE_REPLY_BEGIN\n(.*?)^UNMUTE_REPLY_END$',
                      text, re.MULTILINE | re.DOTALL)
    if not match:
        return {'public_outcome': 'unclassified-missing-reply-boundary'}
    block = match[1]
    status = re.findall(r'^PROBE_DBUS_EXIT=(\d+)$', block, re.MULTILINE)
    returns = re.findall(r'^\s+int32\s+(-?\d+)\s*$', block, re.MULTILINE)
    outcome = 'unclassified-reply'
    if len(status) == 1:
        if int(status[0]) != 0:
            outcome = 'delivery-or-effect-uncertain'
        elif len(returns) == 1:
            outcome = 'public-accepted' if int(returns[0]) == 0 else 'public-rejected'
    return {'public_outcome': outcome,
            'dbus_exit': int(status[0]) if len(status) == 1 else None,
            'public_return': int(returns[0]) if len(returns) == 1 else None,
            'lower_io_and_physical_recovery': 'not-established-by-public-reply'}

B = Path(__file__).resolve().parent
ACCESS = B.parents[1] / 'root-access/s95f-access.py'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('label')
parser.add_argument('--seconds', type=int, choices=range(8, 26), default=12)
parser.add_argument('--run', action='store_true')
parser.add_argument('--physical-black-confirmed', action='store_true',
                    help='Parent has a current physical observer; never infer from getters')
args = parser.parse_args()
if not re.fullmatch(r'[a-z][a-z0-9-]{0,30}', args.label):
    parser.error('Use a unique lowercase capture label')
if args.run and not args.physical_black_confirmed:
    parser.error('Execution requires a current physical-black observation')
if any((B / (args.label + suffix)).exists() for suffix in ['.json', '.trace', '.sh']):
    parser.error('Existing capture label refused')

# Reuse the reviewed native capture body in its dry-run mode. That subprocess
# makes no TV call. The baseline helper itself remains setter-free.
body = subprocess.run(['python3', str(B / 'diagnostic-trace.py'), args.label,
                       '--seconds', str(args.seconds)], check=True,
                      capture_output=True, text=True).stdout
expiry = f'sleep {args.seconds + 10}; if test'
assert body.count(expiry) == 1
# The probe adds bounded D-Bus work; leave room for those replies before expiry.
body = body.replace(expiry, f'sleep {args.seconds + 25}; if test')
tr = '/sys/kernel/debug/tracing/instances/researcher-' + args.label
remote_trace = '/tmp/researcher-panel-trace-20261026/' + args.label + '.trace'
remote_probe = remote_trace + '.probe'
dbus = ('dbus-send --system --print-reply --reply-timeout=1500 '
        '--dest=org.tizen.tv.avoc /org/tizen/tv/avoc '
        'org.tizen.tv.avoc.AvOutputControl.')
baseline = f'''cat /proc/uptime > {remote_probe}
{dbus}GetPanelMute > {remote_probe}.mute
{dbus}GetPanelMuteCaseStatus > {remote_probe}.case
cat {remote_probe}.mute {remote_probe}.case >> {remote_probe}
awk '$1 == "int32" {{if ($2 != 0) bad=1; count++}} END {{exit (count != 2 || bad)}}' {remote_probe}.mute
awk '$1 == "int32" {{if ($2 != 0) bad=1; count++}} END {{exit (count != 2 || bad)}}' {remote_probe}.case
'''
needle = 'echo 1 > "$TRACE_DIR/tracing_on"\n'
assert body.count(needle) == 1
body = body.replace(needle, baseline + needle)
needle = f'sleep {args.seconds}\n'
assert body.count(needle) == 1
probe = f'''sleep 2
echo BEFORE_SINGLE_UNMUTE_ZERO > "$TRACE_DIR/trace_marker"
cat /proc/uptime >> {remote_probe}
echo UNMUTE_REPLY_BEGIN >> {remote_probe}
probe_status=0
{dbus}SetPanelMute int32:0 >> {remote_probe} 2>&1 || probe_status=$?
echo "PROBE_DBUS_EXIT=$probe_status" >> {remote_probe}
echo UNMUTE_REPLY_END >> {remote_probe}
cat /proc/uptime >> {remote_probe}
echo AFTER_SINGLE_UNMUTE_ZERO > "$TRACE_DIR/trace_marker"
{dbus}GetPanelMute >> {remote_probe} 2>&1 || true
{dbus}GetPanelMuteCaseStatus >> {remote_probe} 2>&1 || true
sleep {args.seconds - 2}
'''
body = body.replace(needle, probe)
assert body.count('SetPanelMute int32:0') == 1 and 'int32:1' not in body
assert len(('/bin/sh -c ' + shlex.quote(body)).encode()) <= 8192
if not args.run:
    print(body)
    raise SystemExit(0)

def root(command, timeout=25):
    result = subprocess.run(['python3', str(ACCESS), 'root', '--timeout', str(timeout),
                             '--command', command], capture_output=True, text=True,
                            timeout=timeout + 20)
    try:
        command_result = json.loads(result.stdout)['commands'][0]
    except (ValueError, KeyError, IndexError) as exc:
        raise RuntimeError('Root result unavailable; never retry probe') from exc
    return result, command_result

def fetch(command):
    result, reply = root(command)
    if result.returncode or reply['exit_code'] or reply['timed_out']:
        raise RuntimeError('Readback failed; never retry probe')
    return reply['stdout']

try:
    (B / (args.label + '.sh')).write_text(body)
    result, reply = root('/bin/sh -c ' + shlex.quote(body), args.seconds + 40)
    (B / (args.label + '.json')).write_text(result.stdout)
    (B / (args.label + '.stderr')).write_text(result.stderr)
    if result.returncode or reply['exit_code'] or reply['timed_out']:
        raise RuntimeError('Capture/probe failed; no automatic retry')
    lines = reply['stdout'].splitlines()
    size, digest = int(lines[-2].split()[0]), lines[-1].split()[0]
    if not 0 < size < 8 * 1024 * 1024:
        raise RuntimeError('Unexpected trace size')
    # Preserve verified API evidence before handling trace accounting failures.
    probe_info = fetch(f'wc -c {remote_probe}\nsha256sum {remote_probe}').splitlines()
    probe_size = int(probe_info[-2].split()[0])
    probe_digest = probe_info[-1].split()[0]
    if not 0 < probe_size < 65536:
        raise RuntimeError('Unexpected probe-log size; no truncation accepted')
    probe_log = base64.b64decode(fetch(
        f'dd if={remote_probe} bs=65536 count=1 2>/dev/null | base64'))
    if len(probe_log) != probe_size or hashlib.sha256(probe_log).hexdigest() != probe_digest:
        raise RuntimeError('Probe-log transfer mismatch')
    (B / (args.label + '.probe.txt')).write_bytes(probe_log)
    outcome = classify_probe(probe_log)
    outcome.update({'probe_size': probe_size, 'probe_sha256': probe_digest})
    (B / (args.label + '.probe.json')).write_text(json.dumps(outcome, indent=2) + '\n')
    chunks = []
    for index in range((size + 131071) // 131072):
        chunks.append(base64.b64decode(fetch(
            f'dd if={remote_trace} bs=131072 skip={index} count=1 2>/dev/null | base64')))
    trace = b''.join(chunks)
    if len(trace) != size or hashlib.sha256(trace).hexdigest() != digest:
        raise RuntimeError('Trace transfer mismatch')
    (B / (args.label + '.trace')).write_bytes(trace)
    accounting = re.search(rb'entries-in-buffer/entries-written: (\d+)/(\d+)', trace)
    if not accounting or int(accounting[1]) != int(accounting[2]):
        raise RuntimeError('Incomplete/overflowed trace retained')
    print('Probe:', outcome['public_outcome'],
          '; trace/probe SHA verified; physical outcome requires observation.')
finally:
    original_exception = sys.exc_info()[1]
    cleanup = (f'set -eu\nif test -d {tr}; then echo 0 > {tr}/tracing_on; '
               f'echo 0 > {tr}/events/enable; rmdir {tr}; fi\n'
               'cat /sys/kernel/debug/tracing/tracing_on\n'
               f'if test -e {tr}; then exit 1; fi\n'
               'echo PRIVATE_INSTANCE_ABSENT')
    try:
        result, reply = root(cleanup)
        (B / (args.label + '.cleanup.json')).write_text(result.stdout)
        if (result.returncode or reply['exit_code'] or reply['timed_out'] or
                reply['stdout'].splitlines() != ['0', 'PRIVATE_INSTANCE_ABSENT']):
            raise RuntimeError('Immediate cleanup/baseline verification failed')
    except Exception as exc:
        (B / (args.label + '.cleanup-error.txt')).write_text(
            type(exc).__name__ + '; independently verify finite TV expiry')
        if original_exception is None:
            raise RuntimeError('Immediate cleanup not verified; inspect expiry before further tracing') from exc
