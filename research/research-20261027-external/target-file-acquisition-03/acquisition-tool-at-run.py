#!/usr/bin/env python3
"""Copy two identified ordinary installed files; no SWU/TEE invocation.

Dry by default. One bounded pass, no retries. This does not copy device nodes,
call the updater, decrypt data, create a listener, or change TV files.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path('${S95F_EVIDENCE_ROOT}')
ADAPTER = ROOT / 'panel-idle-20261026/overnight/managed-ui-tab-launch/root-with-margin.py'
ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT = '00000000-0000-4000-8000-000000000000'
FILES = [
    ('/usr/lib/libSWUProductionConfig.so', 6440,
     'c6af8346f4643f2cf50e996682611ece7ad6ff8999274570023561d1a97879f0'),
    ('/usr/bin/SWUCoreTV', 4980824,
     'b8de9e31bf6e74cf9a1f3cfd2598658d978a4edd88b36d1c2f10129ccc8a2697'),
]
BLOCK = 4096
BLOCKS_PER_CHUNK = 6
CHUNK = BLOCK * BLOCKS_PER_CHUNK


def need(ok, message):
    if not ok:
        raise ValueError(message)


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def guard(remote, size):
    return ('set -eu\n'
            f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
            f'test -f {remote}\ntest -r {remote}\n'
            f'test "$(wc -c < {remote})" -eq {size}\n')


def verify_hash_line(text, remote, expected):
    need(re.fullmatch(re.escape(expected) + r'  ' + re.escape(remote) + r'\n', text)
         is not None, 'Remote file identity changed: ' + remote)


def execute(output):
    need(output.is_absolute() and not output.exists(), 'Fresh absolute output required')
    need(hashlib.sha256(ADAPTER.read_bytes()).hexdigest() == ADAPTER_SHA,
         'Adapter identity changed')
    spec = importlib.util.spec_from_file_location('swu_file_copy_adapter', ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    output.mkdir(parents=True, mode=0o700)
    save(output / 'intent.json', {'scope': 'ordinary file copies only', 'files': FILES,
                                 'boot_id': BOOT, 'chunk_bytes': CHUNK, 'retries': 0})
    acquired = []
    for remote, size, expected in FILES:
        name = Path(remote).name
        records = output / (name + '.records')
        records.mkdir(mode=0o700)

        def call(command, label):
            record = {'schema': 'swu-static-file-copy-v1', 'calls': [],
                      'remote_path': remote, 'phase': label,
                      'library_or_device_invocation': False}
            return mod.root(command, record, records / (label + '.json'))

        text = call(guard(remote, size) + f'sha256sum {remote}\n', 'before')
        verify_hash_line(text, remote, expected)
        partial = output / (name + '.partial')
        digest = hashlib.sha256()
        with partial.open('xb') as stream:
            for index, offset in enumerate(range(0, size, CHUNK)):
                length = min(CHUNK, size - offset)
                command = (guard(remote, size) +
                           f'dd if={remote} bs={BLOCK} skip={offset // BLOCK} '
                           f'count={BLOCKS_PER_CHUNK} 2>/dev/null | base64\n')
                text = call(command, f'chunk-{index:04d}')
                need(re.fullmatch(r'[A-Za-z0-9+/=\n]+', text) is not None,
                     'Non-base64 transfer content')
                data = base64.b64decode(''.join(text.splitlines()), validate=True)
                need(len(data) == length, 'Short or oversized file chunk')
                stream.write(data)
                digest.update(data)
                if index % 32 == 0:
                    print(json.dumps({'file': name, 'copied': offset + length,
                                      'size': size}), flush=True)
        text = call(guard(remote, size) + f'sha256sum {remote}\n', 'after')
        verify_hash_line(text, remote, expected)
        need(partial.stat().st_size == size and digest.hexdigest() == expected,
             'Host file hash/size mismatch')
        partial.rename(output / name)
        acquired.append({'remote_path': remote, 'size': size, 'sha256': expected,
                         'target_library_executed': False})
        save(output / 'acquisition-manifest.json', {'boot_id': BOOT, 'files': acquired})
    print(json.dumps({'complete': True, 'files': acquired, 'device_operations': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.execute:
        need(args.output is not None, '--output required')
        execute(args.output)
    else:
        need(args.output is None, '--output requires --execute')
        print(json.dumps({'execute_required': True, 'files': FILES,
                          'device_operations': 0, 'target_library_invocations': 0,
                          'retries': 0, 'remote_file_writes': 0}))
