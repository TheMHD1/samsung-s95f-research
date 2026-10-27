#!/usr/bin/env python3
"""Copy one ordinary, existing factory-data file; no controller operations."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'selected-qd-profile-copy-20261027a'
CLIENT = Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
SOURCE = '/factory_peq/tcon_data/QD/F_RSM1_BN9659934B_COMMON.bin'
EXPECTED = 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
BOOT = '00000000-0000-4000-8000-000000000000'
PACKED_SIZE = 463401
BLOCK = 32768


def need(value, reason):
    if not value:
        raise ValueError(reason)


def main():
    need(hashlib.sha256(CLIENT.read_bytes()).hexdigest() == '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5', 'client changed')
    OUT.mkdir(exist_ok=False)
    chunks = []
    payload = bytearray()
    for index in range((PACKED_SIZE + BLOCK - 1) // BLOCK):
        command = f'''set -eu
p={SOURCE}
test -f "$p"; test ! -L "$p"
echo BEFORE
cat /proc/sys/kernel/random/boot_id
wc -c < "$p"
sha256sum "$p"
echo DATA_START
gzip -n -c "$p" | dd iflag=fullblock bs={BLOCK} skip={index} count=1 2>/dev/null | base64
echo DATA_END
echo AFTER
sha256sum "$p"
cat /proc/sys/kernel/random/boot_id
'''
        stem = OUT / f'chunk-{index:02d}'
        stem.with_suffix('.intent.json').write_text(json.dumps({'physical_state': 'unobserved', 'mode': 'ordinary regular-file copy through compression; no device access', 'command': command}, indent=2) + '\n')
        proc = subprocess.run(['python3', str(CLIENT), 'root', '--persistent-only', '--timeout', '25', '--command', command], capture_output=True, timeout=55)
        stem.with_suffix('.client.stdout').write_bytes(proc.stdout)
        stem.with_suffix('.client.stderr').write_bytes(proc.stderr)
        need(proc.returncode == 0 and not proc.stderr and len(proc.stdout) < 65536, 'client failed or output bound exceeded')
        response = json.loads(proc.stdout)
        need(response['authenticated'] is True and response['uid'] == 0 and response['euid'] == 0 and response['model'] == 'QN77S95FAFXZC', 'root/model mismatch')
        cmds = response['commands']
        need(len(cmds) == 1 and cmds[0]['exit_code'] == 0 and not cmds[0]['timed_out'] and not cmds[0]['stderr'], 'remote command failed')
        text = cmds[0]['stdout']
        before, rest = text.split('DATA_START\n')
        data, after = rest.split('DATA_END\n')
        need(before.splitlines() == ['BEFORE', BOOT, '5242880', EXPECTED + '  ' + SOURCE], 'before mismatch')
        need(after.splitlines() == ['AFTER', EXPECTED + '  ' + SOURCE, BOOT], 'after mismatch')
        decoded = base64.b64decode(''.join(data.splitlines()), validate=True)
        need(len(decoded) == min(BLOCK, PACKED_SIZE - index * BLOCK), 'chunk length mismatch')
        payload.extend(decoded)
        chunks.append({'index': index, 'bytes': len(decoded), 'sha256': hashlib.sha256(decoded).hexdigest(), 'response_sha256': hashlib.sha256(proc.stdout).hexdigest()})
        print(json.dumps(chunks[-1]), flush=True)
    need(len(payload) == PACKED_SIZE, 'packed count mismatch')
    plain = gzip.decompress(payload)
    need(len(plain) == 5242880 and hashlib.sha256(plain).hexdigest() == EXPECTED, 'full source mismatch')
    (OUT / 'profile.bin.gz').write_bytes(payload)
    (OUT / 'F_RSM1_BN9659934B_COMMON.bin').write_bytes(plain)
    manifest = {'accepted': True, 'mode': 'ordinary filesystem copy only', 'source': SOURCE, 'source_bytes': len(plain), 'source_sha256': EXPECTED, 'compressed_bytes': len(payload), 'compressed_sha256': hashlib.sha256(payload).hexdigest(), 'boot_id': BOOT, 'root_calls': len(chunks), 'target_files_created': 0, 'controller_operations': 0, 'physical_state': 'unobserved', 'chunks': chunks}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest), flush=True)


if __name__ == '__main__':
    main()
