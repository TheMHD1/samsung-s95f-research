#!/usr/bin/env python3
"""Copy existing failed-capture evidence via gzip; never launch another capture.

Creates one exclusive temporary rescue directory on the TV. Keeps original
files and all failed-run flags intact. No display/device API or trace change.
"""
import argparse
import base64
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
CLIENT = Path('${S95F_EVIDENCE_ROOT}/root-access/s95f-access.py')
CLIENT_SHA = '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5'
DEST = HERE / 'owner-power-on-20261026a-rescue'
ORIGINAL = '/tmp/researcher-observed-quiescent-pm-onset-20261026/owner-power-on-20261026a'
REMOTE = '/tmp/researcher-owner-power-on-rescue-20261026a'
FILES = ('trace', 'meta.txt', 'samples.txt', 'sample-errors.txt', 'artifacts.txt', 'fds.txt', 'vlog-after.txt')
CHUNK = 32768
PREPARE = '''set -euo pipefail
umask 077
boot=$(cat /proc/sys/kernel/random/boot_id)
test "$boot" = 00000000-0000-4000-8000-000000000000
O=ORIGINAL_PATH
R=RESCUE_PATH
test ! -L "$O"; test -d "$O"; test "$(stat -c '%u:%a' "$O")" = 0:700
test ! -e "$R"; test ! -L "$R"; mkdir -m 700 "$R"
echo "BOOT $boot"
for f in FILE_NAMES; do
 test ! -L "$O/$f"; test -f "$O/$f"; test "$(stat -c '%u:%a' "$O/$f")" = 0:600
 n=$(stat -c '%s' "$O/$f"); test "$n" -gt 0; test "$n" -le 134217728
 h=$(sha256sum "$O/$f"); h=${h%% *}
 (ulimit -f 131072; gzip -1 -c "$O/$f" >"$R/$f.gz")
 chmod 600 "$R/$f.gz"
 test "$(stat -c '%s' "$O/$f")" = "$n"
 after=$(sha256sum "$O/$f"); test "${after%% *}" = "$h"
 cn=$(stat -c '%s' "$R/$f.gz"); ch=$(sha256sum "$R/$f.gz"); ch=${ch%% *}
 printf 'FILE %s %s %s %s %s\n' "$f" "$n" "$h" "$cn" "$ch"
done
echo COMPLETE_EXISTING_FAILED_CAPTURE_ONLY
'''.replace('ORIGINAL_PATH', ORIGINAL).replace('RESCUE_PATH', REMOTE).replace('FILE_NAMES', ' '.join(FILES))

def root(command, stem):
    if len(command.encode()) > 8192:
        raise ValueError('command bound')
    argv = ['python3', str(CLIENT), 'root', '--persistent-only', '--timeout', '25', '--command', command]
    intent = dict(argv=argv, command=command, command_sha256=hashlib.sha256(command.encode()).hexdigest(),
                  client_sha256=CLIENT_SHA, retry=False, started_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    (DEST/(stem+'.intent.json')).write_text(json.dumps(intent, indent=2)+'\n')
    with (DEST/(stem+'.stdout.json')).open('xb') as out, (DEST/(stem+'.stderr')).open('xb') as err:
        try:
            p = subprocess.run(argv, stdout=out, stderr=err, timeout=45, check=False)
            result = dict(returncode=p.returncode, host_timeout=False)
        except subprocess.TimeoutExpired:
            result = dict(returncode=None, host_timeout=True)
    result['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    (DEST/(stem+'.result.json')).write_text(json.dumps(result, indent=2)+'\n')
    if result['returncode'] != 0 or result['host_timeout'] or (DEST/(stem+'.stderr')).read_bytes():
        raise ValueError('client failure; no retry')
    reply = json.loads((DEST/(stem+'.stdout.json')).read_text())
    if not (reply.get('model')=='QN77S95FAFXZC' and reply.get('host')=='198.51.100.20'
            and reply.get('authenticated') is True and reply.get('uid')==0 and reply.get('euid')==0
            and reply.get('root_persistence')=='host-assisted'
            and reply.get('global_system_files_unchanged_at_acquisition') is True):
        raise ValueError('root envelope')
    commands = reply.get('commands')
    if not isinstance(commands,list) or len(commands)!=1:
        raise ValueError('command count')
    item = commands[0]
    if item.get('command')!=command or item.get('exit_code')!=0 or item.get('timed_out') is not False or item.get('stderr')!='':
        raise ValueError('remote command failure; no retry')
    return item['stdout']

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--run',action='store_true'); a=p.parse_args()
    if hashlib.sha256(CLIENT.read_bytes()).hexdigest()!=CLIENT_SHA:
        raise ValueError('reviewed client changed')
    if not a.run:
        print(json.dumps(dict(command=PREPARE,command_bytes=len(PREPARE.encode()),files=FILES,
                              existing_failed_capture_only=True,chunk=CHUNK),indent=2)); return
    DEST.mkdir(mode=0o700,exist_ok=False)
    text=root(PREPARE,'prepare'); lines=text.splitlines()
    if len(lines)!=len(FILES)+2 or lines[0]!='BOOT 00000000-0000-4000-8000-000000000000' or lines[-1]!='COMPLETE_EXISTING_FAILED_CAPTURE_ONLY':
        raise ValueError('incomplete preparation; existing files retained')
    manifest={}
    for name,line in zip(FILES,lines[1:-1]):
        parts=line.split()
        if len(parts)!=6 or parts[:2]!=['FILE',name]: raise ValueError('manifest framing')
        n,h,cn,ch=int(parts[2]),parts[3],int(parts[4]),parts[5]
        if not (0<n<=134217728 and 0<cn<=134217728 and len(h)==len(ch)==64): raise ValueError('manifest bounds')
        manifest[name]=dict(size=n,sha256=h,compressed_size=cn,compressed_sha256=ch)
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    retained=DEST/'retained';retained.mkdir(mode=0o700)
    for file_index,(name,spec) in enumerate(manifest.items()):
        chunks=[]
        for index in range((spec['compressed_size']+CHUNK-1)//CHUNK):
            command=f'set -euo pipefail\ndd if={REMOTE}/{name}.gz bs={CHUNK} skip={index} count=1 2>/dev/null | base64\n'
            value=root(command,f'fetch-{file_index:02d}-{index:04d}')
            raw=base64.b64decode(''.join(value.split()),validate=True)
            if len(raw)!=min(CHUNK,spec['compressed_size']-index*CHUNK): raise ValueError('chunk length')
            chunks.append(raw)
        compressed=b''.join(chunks)
        if hashlib.sha256(compressed).hexdigest()!=spec['compressed_sha256']: raise ValueError('compressed hash')
        body=gzip.decompress(compressed)
        if len(body)!=spec['size'] or hashlib.sha256(body).hexdigest()!=spec['sha256']: raise ValueError('original hash')
        (retained/name).write_bytes(body)
        print(json.dumps(dict(file=name,bytes=len(body),sha256=spec['sha256'],copied=True)),flush=True)
    (DEST/'result.json').write_text(json.dumps(dict(copied=True,original_capture_accepted=False,
           physical_timing_unresolved=True,remote_rescue_retained=REMOTE,
           finished_utc=dt.datetime.now(dt.timezone.utc).isoformat()),indent=2)+'\n')

if __name__=='__main__': main()
