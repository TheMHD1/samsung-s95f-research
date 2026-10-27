#!/usr/bin/env python3
"""Reuse retained chunk zero offline; copy only two missing fixed-file chunks."""
from pathlib import Path
import base64
import datetime
import hashlib
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
OLD = HERE / 'sdp-sys-provider-copy-20261026'
DEST = HERE / 'sdp-sys-provider-copy-20261026-followup'
ACCESS = HERE.parents[1] / 'root-access/s95f-access.py'
REMOTE = '/lib/modules/5.4.261/kernel/soc/sdp_sys.ko'
SIZE = 97550
SHA = '25c9c2eef67137465b228c1297392fa22bf8a080695f8a9c020445a48f834de6'
BOOT = '00000000-0000-4000-8000-000000000000'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def parse(source, index, literal_separators=False):
    out = source.with_suffix('.client-stdout.json').read_bytes()
    intent = json.loads(source.with_suffix('.intent.json').read_text())
    result = json.loads(source.with_suffix('.client-result.json').read_text())
    require(result['returncode'] == 0 and source.with_suffix('.client-stderr.txt').read_bytes() == b'', 'client failure')
    response = json.loads(out)
    require(response['authenticated'] is True and response['uid'] == response['euid'] == 0, 'root identity')
    require(response['host'] == '198.51.100.20' and response['model'] == 'QN77S95FAFXZC', 'target identity')
    require(response['root_persistence'] == 'host-assisted' and response['global_system_files_unchanged_at_acquisition'] is True, 'access provenance')
    require(len(response['commands']) == 1, 'command cardinality')
    command = response['commands'][0]
    require(command['command'] == intent['command'] and hashlib.sha256(intent['command'].encode()).hexdigest() == intent['command_sha256'], 'command binding')
    require(command['exit_code'] == 0 and command['timed_out'] is False and command['stderr'] == '', 'remote status')
    text = command['stdout']
    if literal_separators:
        require(text.count('\\n') == 7, 'original framing count')
        text = text.replace('\\n', '\n')
    pattern = (r'@@ BOOT_START\n(?P<boot1>[0-9a-f-]{36})\n@@ TIME_START\n(?P<wall1>[0-9]+)\n(?P<up1>[0-9]+\.[0-9]+) [0-9]+\.[0-9]+\n'
               r'@@ HASH_START\n(?P<hash1>[0-9a-f]{64})  (?P<path1>[^\n]+)\n@@ DATA\n(?P<data>(?:[A-Za-z0-9+/=]+\n)+)'
               r'@@ HASH_END\n(?P<hash2>[0-9a-f]{64})  (?P<path2>[^\n]+)\n@@ BOOT_END\n(?P<boot2>[0-9a-f-]{36})\n'
               r'@@ TIME_END\n(?P<wall2>[0-9]+)\n(?P<up2>[0-9]+\.[0-9]+) [0-9]+\.[0-9]+\n')
    match = re.fullmatch(pattern, text)
    require(match is not None, 'complete framing')
    m = match.groupdict()
    require(m['boot1'] == m['boot2'] == BOOT, 'stable boot')
    require(m['hash1'] == m['hash2'] == SHA and m['path1'] == m['path2'] == REMOTE, 'file identity')
    require(0 <= int(m['wall2'])-int(m['wall1']) <= 25 and 0 <= float(m['up2'])-float(m['up1']) <= 25, 'clock order/bounds')
    data = base64.b64decode(''.join(m['data'].splitlines()), validate=True)
    require(len(data) == min(32768, SIZE-index*32768), 'chunk size')
    return data, dict(index=index, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
        client_stdout=str(source.with_suffix('.client-stdout.json')), client_sha256=hashlib.sha256(out).hexdigest(),
        command_sha256=intent['command_sha256'], uptime_start=m['up1'], uptime_end=m['up2'],
        literal_separator_normalization=literal_separators)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-missing-two-chunks', action='store_true')
    args = parser.parse_args()
    first, first_meta = parse(OLD/'chunk-0', 0, True)
    if not args.run_missing_two_chunks:
        print('PASS: retained chunk zero verified offline. No TV request made.')
        return
    DEST.mkdir(mode=0o700)
    parts, provenance = [first], [first_meta]
    for index in (1, 2):
        command = '''set -euo pipefail
echo '@@ BOOT_START'
cat /proc/sys/kernel/random/boot_id
echo '@@ TIME_START'
date -u +%s
cat /proc/uptime
echo '@@ HASH_START'
sha256sum /lib/modules/5.4.261/kernel/soc/sdp_sys.ko
echo '@@ DATA'
dd if=/lib/modules/5.4.261/kernel/soc/sdp_sys.ko bs=32768 skip=INDEX count=1 2>/dev/null | base64
echo '@@ HASH_END'
sha256sum /lib/modules/5.4.261/kernel/soc/sdp_sys.ko
echo '@@ BOOT_END'
cat /proc/sys/kernel/random/boot_id
echo '@@ TIME_END'
date -u +%s
cat /proc/uptime
'''.replace('skip=INDEX', f'skip={index}')
        stem = DEST/f'chunk-{index}'
        stem.with_suffix('.intent.json').write_text(json.dumps(dict(command=command,
            command_sha256=hashlib.sha256(command.encode()).hexdigest(), started_utc=now(),
            purpose='Copy only missing fixed-file chunk; no control/load/trace/getter; no retry; physical panel unobserved.'), indent=2)+'\n')
        result = subprocess.run(['python3',str(ACCESS),'root','--persistent-only','--timeout','25','--command',command],
            capture_output=True,text=True,timeout=50)
        stem.with_suffix('.client-stdout.json').write_text(result.stdout)
        stem.with_suffix('.client-stderr.txt').write_text(result.stderr)
        stem.with_suffix('.client-result.json').write_text(json.dumps(dict(returncode=result.returncode,finished_utc=now()),indent=2)+'\n')
        data, meta = parse(stem, index)
        parts.append(data)
        provenance.append(meta)
        print(f'chunk {index}: {len(data)} verified bytes',flush=True)
    module = b''.join(parts)
    require(len(module) == SIZE and hashlib.sha256(module).hexdigest() == SHA, 'whole-file hash')
    with (DEST/'sdp_sys.ko').open('xb') as out:
        out.write(module)
    (DEST/'manifest.json').write_text(json.dumps(dict(remote=REMOTE,bytes=SIZE,sha256=SHA,boot_id=BOOT,
        sequential_nonatomic=True,physical_picture='unobserved',loaded_or_called=False,chunks=provenance),indent=2)+'\n')
    print(f'PASS: module copied only, {SIZE} bytes SHA256 {SHA}.')


if __name__ == '__main__':
    main()
