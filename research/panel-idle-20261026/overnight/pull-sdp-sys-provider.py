#!/usr/bin/env python3
"""Finite passive copy of one discovered module; never load or call it."""
from pathlib import Path
import base64
import datetime
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ACCESS = HERE.parents[1] / 'root-access/s95f-access.py'
DEST = HERE / 'sdp-sys-provider-copy-20261026'
REMOTE = '/lib/modules/5.4.261/kernel/soc/sdp_sys.ko'
SIZE = 97550
SHA = '25c9c2eef67137465b228c1297392fa22bf8a080695f8a9c020445a48f834de6'
BOOT = '00000000-0000-4000-8000-000000000000'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    DEST.mkdir(mode=0o700)  # A previous namespace is never reused or retried.
    parts = []
    provenance = []
    for index in range((SIZE + 32767) // 32768):
        command = r'''set -euo pipefail
printf '@@ BOOT_START\n'
cat /proc/sys/kernel/random/boot_id
printf '@@ TIME_START\n'
date -u +%s
cat /proc/uptime
printf '@@ HASH_START\n'
sha256sum /lib/modules/5.4.261/kernel/soc/sdp_sys.ko
printf '@@ DATA\n'
dd if=/lib/modules/5.4.261/kernel/soc/sdp_sys.ko bs=32768 skip=INDEX count=1 2>/dev/null | base64
printf '@@ HASH_END\n'
sha256sum /lib/modules/5.4.261/kernel/soc/sdp_sys.ko
printf '@@ BOOT_END\n'
cat /proc/sys/kernel/random/boot_id
printf '@@ TIME_END\n'
date -u +%s
cat /proc/uptime
'''.replace('skip=INDEX', f'skip={index}')
        stem = DEST / f'chunk-{index}'
        intent = dict(command=command, command_sha256=hashlib.sha256(command.encode()).hexdigest(),
                      started_utc=now(), purpose='Passive fixed-file copy only; no module load, getter, MMIO, trace or display control; physically unobserved.')
        stem.with_suffix('.intent.json').write_text(json.dumps(intent, indent=2)+'\n')
        result = subprocess.run(['python3',str(ACCESS),'root','--persistent-only','--timeout','25','--command',command],
                                capture_output=True, text=True, timeout=50)
        stem.with_suffix('.client-stdout.json').write_text(result.stdout)
        stem.with_suffix('.client-stderr.txt').write_text(result.stderr)
        stem.with_suffix('.client-result.json').write_text(json.dumps(dict(returncode=result.returncode, finished_utc=now()), indent=2)+'\n')
        if result.returncode or result.stderr:
            raise RuntimeError('Client failed; no retry')
        response = json.loads(result.stdout)
        assert response['authenticated'] and response['uid'] == response['euid'] == 0
        assert response['host'] == '198.51.100.20' and response['model'] == 'QN77S95FAFXZC'
        remote, = response['commands']
        assert remote['command'] == command and remote['exit_code'] == 0
        assert not remote['timed_out'] and remote['stderr'] == ''
        text = remote['stdout']
        assert text.count('@@ BOOT_START\n'+BOOT+'\n') == 1
        assert text.count('@@ BOOT_END\n'+BOOT+'\n') == 1
        assert text.count(SHA+'  '+REMOTE+'\n') == 2
        data, = text.split('@@ DATA\n')[1:]
        data = data.split('@@ HASH_END\n', 1)[0]
        chunk = base64.b64decode(''.join(data.splitlines()), validate=True)
        assert len(chunk) == min(32768, SIZE-index*32768)
        parts.append(chunk)
        provenance.append(dict(index=index, bytes=len(chunk), sha256=hashlib.sha256(chunk).hexdigest(),
                               client_sha256=hashlib.sha256(result.stdout.encode()).hexdigest()))
        print(f'chunk {index}: {len(chunk)} bytes verified', flush=True)
    module = b''.join(parts)
    assert len(module) == SIZE and hashlib.sha256(module).hexdigest() == SHA
    with (DEST/'sdp_sys.ko').open('xb') as out:
        out.write(module)
    (DEST/'manifest.json').write_text(json.dumps(dict(remote=REMOTE, bytes=SIZE, sha256=SHA,
        boot_id=BOOT, physically_observed=False, sequential_nonatomic=True,
        loaded_or_called=False, chunks=provenance), indent=2)+'\n')
    print(f'PASS: {SIZE} bytes, SHA256 {SHA}; copied only, not loaded or called.')


if __name__ == '__main__':
    main()
