#!/usr/bin/env python3
"""Bounded AVE reader capture, without producer-setting changes."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import uuid

HERE = Path(__file__).resolve().parent
ADAPTER = HERE.parent / 'swu-stream-root-20261028cp/root-with-margin.py'
PIN = 'be9c5362fa40b52be2b824e6cc3e11013bdaafd44b1710f010bbccebac2bdc55'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('label')
    parser.add_argument('--seconds', type=int, choices=[2, 30], default=2)
    args = parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,48}', args.label):
        raise ValueError('invalid label')
    out = HERE / args.label
    out.mkdir(mode=0o700)
    if hashlib.sha256(ADAPTER.read_bytes()).hexdigest() != PIN:
        raise ValueError('adapter identity')
    spec = importlib.util.spec_from_file_location('log_root', ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    remote = '/tmp/s95f-ave-log-' + uuid.uuid4().hex
    command = f'''set -eu
test "$(cat /proc/sys/kernel/random/boot_id)" = 00000000-0000-4000-8000-000000000000
umask 077
mkdir {remote}
echo META_BEGIN
cat /proc/sys/kernel/random/boot_id
cat /proc/uptime
date -u
ulimit -f 128
tv_log_rc=0
/usr/bin/vlogutil -v kerneltime -t {args.seconds} '*:S' 'AVE:I' >{remote}/raw.log 2>{remote}/stderr.log || tv_log_rc=$?
echo CAPTURE_EXIT
echo "$tv_log_rc"
echo CAPTURE_BYTES
wc -c <{remote}/raw.log
echo CAPTURE_SHA256
sha256sum {remote}/raw.log
echo RAW_BASE64
head -c 24576 {remote}/raw.log | base64
echo STDERR_BASE64
head -c 2048 {remote}/stderr.log | base64
echo META_END
cat /proc/uptime
date -u
'''
    text = module.root(command, {'schema': 'passive-ave-log-v1', 'calls': []}, out / 'root.json')
    (out / 'framed.txt').write_text(text)
    raw = text.split('RAW_BASE64\n', 1)[1].split('STDERR_BASE64\n', 1)[0]
    data = base64.b64decode(''.join(raw.split()), validate=True)
    (out / 'raw.log').write_bytes(data)
    err = text.split('STDERR_BASE64\n', 1)[1].split('META_END\n', 1)[0]
    (out / 'stderr.log').write_bytes(base64.b64decode(''.join(err.split()), validate=True))
    count = int(text.split('CAPTURE_BYTES\n', 1)[1].splitlines()[0])
    rc = int(text.split('CAPTURE_EXIT\n', 1)[1].splitlines()[0])
    sha = text.split('CAPTURE_SHA256\n', 1)[1].split()[0]
    accepted = rc == 0 and count == len(data) and hashlib.sha256(data).hexdigest() == sha
    result = {'accepted': accepted, 'capture_exit': rc, 'target_bytes': count,
              'retained_bytes': len(data), 'truncated': count > len(data),
              'remote_private_directory': remote, 'physical_state': 'unobserved',
              'producer_settings_changed': False, 'requested_history_seconds': args.seconds,
              'driver_losslessness_claimed': False}
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if not accepted:
        raise ValueError('capture failed or incomplete; target files retained')

if __name__ == '__main__':
    main()
