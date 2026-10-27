#!/usr/bin/env python3
"""One finite passive all-syscall AVEMonMain check; dry by default.

This records one existing thread only, without an id==54 filter. It does not
run any panel/controller operation or infer physical state. Raw evidence is
not promoted to technical acceptance by transport success.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = HERE.parent
SHELL = HERE / 'avemon-syscall-checkpoint-v2.sh'
SHELL_SHA = '60832356c98aa96250dfde4cbe2f324e947c3c6f66c27db993a8e72ad2f5d4bd'
TRANSPORT = B / 'managed-tcon-status-read/run-status-read.py'
TRANSPORT_SHA = '7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a'
ACCESS = B.parent.parent / 'root-access/s95f-access.py'
ACCESS_SHA = '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5'
DEST = HERE / 'avemon-all-syscalls-20261027b'
INSTANCE = '/sys/kernel/debug/tracing/instances/researcher-avemon-syscall-e5283bd06bc04479983072c7b94d97f5-v2'


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--reviewed', action='store_true')
    args = parser.parse_args()
    for path, expected in ((SHELL, SHELL_SHA), (TRANSPORT, TRANSPORT_SHA),
                           (ACCESS, ACCESS_SHA)):
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                'dependency changed: ' + str(path))
    command = SHELL.read_text()
    require(0 < len(command.encode()) <= 8192, 'command size')
    if not args.run:
        print(json.dumps({'mode': 'dry; no TV or network call',
                          'shell_sha256': SHELL_SHA,
                          'duration_seconds': 5,
                          'thread': 'AVEMonMain/1011',
                          'syscall_id_filter': False,
                          'controller_commands': False,
                          'destination': str(DEST)}, indent=2))
        return
    require(args.reviewed, 'execution requires --run --reviewed')
    DEST.mkdir(mode=0o700, exist_ok=False)
    spec = importlib.util.spec_from_file_location('checkpoint_transport', TRANSPORT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    record = {'schema': 'passive-avemon-all-syscalls-v2',
              'created_utc': module.now(), 'physical_state': 'unobserved',
              'accepted': False, 'technical_capture_complete': False,
              'cleanup_verified': False, 'controller_commands': False,
              'shell_sha256': SHELL_SHA, 'calls': []}
    output = DEST / 'record.json'
    module.save(output, record)
    try:
        raw = module.root(command, record, output)
        (DEST / 'raw.txt').write_text(raw)
        require(raw.endswith('CLEANUP_VERIFIED\n'), 'probe cleanup marker missing')
        record['raw_retained'] = True
    except Exception as exc:
        record['error'] = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        # Verification only. Do not remove an unexplained active instance.
        verify = ('set -eu\n'
                  'test "$(cat /proc/sys/kernel/random/boot_id)" = '
                  '00000000-0000-4000-8000-000000000000\n'
                  f'test ! -e {INSTANCE}\n'
                  'test "$(cat /sys/kernel/debug/tracing/tracing_on)" = 0\n'
                  'echo CHECKPOINT_QUIESCENT\n')
        try:
            record['cleanup_verified'] = module.root(verify, record, output) == 'CHECKPOINT_QUIESCENT\n'
        except Exception as exc:
            record['cleanup_error'] = type(exc).__name__ + ': ' + str(exc)
        module.save(output, record)
    require(record['cleanup_verified'], 'independent cleanup verification failed')
    print(json.dumps({'raw_retained': True, 'cleanup_verified': True,
                      'accepted': False, 'reason': 'offline validation pending',
                      'record': str(output)}, indent=2))


if __name__ == '__main__':
    main()
