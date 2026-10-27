#!/usr/bin/env python3
"""One finite passive copy of the newly discovered callback candidate module."""
from pathlib import Path
import argparse
import datetime
import hashlib
import importlib.util
import json
import subprocess

HERE = Path(__file__).resolve().parent
REMOTE = '/lib/modules/5.4.261/kernel/tztv-battery.ko'
SIZE = 174902
SHA = 'dd7e9c1c68b3802e8e8fc04a9097c2cc6baaedd5960e7a25bb387499edbc2270'
DEST = HERE / 'hdmi-cell-provider-copy-20261026'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    reader_path = HERE/'complete-sdp-sys-provider-copy.py'
    reader_sha = hashlib.sha256(reader_path.read_bytes()).hexdigest()
    require(reader_sha == 'b587e16d4e85a056c248b1adc3f04dccbabed682fe50a8dfdd9987a1543c4582', 'reader source identity')
    spec = importlib.util.spec_from_file_location('module_copy_reader', reader_path)
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    # The reused parser validates exactly these per-module size/hash/path values;
    # its source digest is recorded, with the original provider discovery retained.
    reader.REMOTE, reader.SIZE, reader.SHA = REMOTE, SIZE, SHA
    if not args.run:
        print(f'DRY: six fixed 32768-byte chunks; {REMOTE}; {SIZE} bytes; SHA256 {SHA}.')
        return
    DEST.mkdir(mode=0o700)
    parts, provenance = [], []
    for index in range((SIZE+32767)//32768):
        lines = [
            'set -euo pipefail', "echo '@@ BOOT_START'", 'cat /proc/sys/kernel/random/boot_id',
            "echo '@@ TIME_START'", 'date -u +%s', 'cat /proc/uptime', "echo '@@ HASH_START'",
            'sha256sum '+REMOTE, "echo '@@ DATA'",
            f'dd if={REMOTE} bs=32768 skip={index} count=1 2>/dev/null | base64',
            "echo '@@ HASH_END'", 'sha256sum '+REMOTE, "echo '@@ BOOT_END'",
            'cat /proc/sys/kernel/random/boot_id', "echo '@@ TIME_END'", 'date -u +%s', 'cat /proc/uptime']
        command = '\n'.join(lines)+'\n'
        source = DEST/f'chunk-{index}'
        source.with_suffix('.intent.json').write_text(json.dumps(dict(command=command,
            command_sha256=hashlib.sha256(command.encode()).hexdigest(),started_utc=reader.now(),
            purpose='Passive read-only fixed-module copy; no load, getter, control or trace; no retry; physical panel unobserved.'),indent=2)+'\n')
        result = subprocess.run(['python3',str(reader.ACCESS),'root','--persistent-only','--timeout','25','--command',command],capture_output=True,text=True,timeout=50)
        source.with_suffix('.client-stdout.json').write_text(result.stdout)
        source.with_suffix('.client-stderr.txt').write_text(result.stderr)
        source.with_suffix('.client-result.json').write_text(json.dumps(dict(returncode=result.returncode,finished_utc=reader.now()),indent=2)+'\n')
        data, meta = reader.parse(source,index)
        parts.append(data)
        provenance.append(meta)
        print(f'chunk {index}: {len(data)} verified bytes',flush=True)
    module = b''.join(parts)
    require(len(module)==SIZE and hashlib.sha256(module).hexdigest()==SHA,'whole-file identity')
    with (DEST/'tztv-battery.ko').open('xb') as out:
        out.write(module)
    (DEST/'manifest.json').write_text(json.dumps(dict(remote=REMOTE,bytes=SIZE,sha256=SHA,
        reader_sha256=reader_sha,boot_id=reader.BOOT,sequential_nonatomic=True,
        physical_picture='unobserved',loaded_or_called=False,chunks=provenance),indent=2)+'\n')
    print('PASS: callback candidate copied only; not loaded or called.')


if __name__=='__main__':
    main()
