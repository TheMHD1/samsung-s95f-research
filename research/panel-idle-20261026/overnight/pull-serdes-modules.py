#!/usr/bin/env python3
"""Finite passive copy of two explicitly discovered SerDes/support modules."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import subprocess

HERE = Path(__file__).resolve().parent
ALLOWLIST = {
    'support': ('/lib/modules/5.4.261/kernel/system_drv.ko',46510,
                'fbe4eaad57c66865e2cc50b575a878a690c06303905e666e75b9f08d139dd1f0'),
    'ocif': ('/lib/modules/5.4.261/kernel/soc/sdp_ocl.ko',261166,
             '80b9e66f4129a31207f1eee8d7636d7565193ecf9ba87e3bded6196c5e1b02e7'),
}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('module',choices=ALLOWLIST)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    remote,size,digest=ALLOWLIST[args.module]
    reader_path=HERE/'complete-sdp-sys-provider-copy.py'
    if hashlib.sha256(reader_path.read_bytes()).hexdigest()!='b587e16d4e85a056c248b1adc3f04dccbabed682fe50a8dfdd9987a1543c4582':
        raise ValueError('parser source changed')
    spec=importlib.util.spec_from_file_location('bounded_copy_parser',reader_path)
    reader=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    reader.REMOTE,reader.SIZE,reader.SHA=remote,size,digest
    if not args.run:
        print(f'DRY: {remote}; {size} bytes; {(size+32767)//32768} fixed chunks. No request.')
        return
    dest=HERE/f'serdes-{args.module}-copy-20261026'
    dest.mkdir(mode=0o700)
    parts=[]
    provenance=[]
    for index in range((size+32767)//32768):
        command='\n'.join(('set -euo pipefail',"echo '@@ BOOT_START'",'cat /proc/sys/kernel/random/boot_id',
            "echo '@@ TIME_START'",'date -u +%s','cat /proc/uptime',"echo '@@ HASH_START'",'sha256sum '+remote,
            "echo '@@ DATA'",f'dd if={remote} bs=32768 skip={index} count=1 2>/dev/null | base64',
            "echo '@@ HASH_END'",'sha256sum '+remote,"echo '@@ BOOT_END'",'cat /proc/sys/kernel/random/boot_id',
            "echo '@@ TIME_END'",'date -u +%s','cat /proc/uptime'))+'\n'
        stem=dest/f'chunk-{index}'
        stem.with_suffix('.intent.json').write_text(json.dumps(dict(command=command,
            command_sha256=hashlib.sha256(command.encode()).hexdigest(),started_utc=reader.now(),
            purpose='Finite fixed-module passive copy; no load/callback/getter/control/trace; no retry; physical panel unobserved.'),indent=2)+'\n')
        result=subprocess.run(['python3',str(reader.ACCESS),'root','--persistent-only','--timeout','25','--command',command],capture_output=True,text=True,timeout=50)
        stem.with_suffix('.client-stdout.json').write_text(result.stdout)
        stem.with_suffix('.client-stderr.txt').write_text(result.stderr)
        stem.with_suffix('.client-result.json').write_text(json.dumps(dict(returncode=result.returncode,finished_utc=reader.now()),indent=2)+'\n')
        data,meta=reader.parse(stem,index)
        parts.append(data);provenance.append(meta)
    module=b''.join(parts)
    reader.require(len(module)==size and hashlib.sha256(module).hexdigest()==digest,'whole-module identity')
    with (dest/Path(remote).name).open('xb') as out:out.write(module)
    (dest/'manifest.json').write_text(json.dumps(dict(remote=remote,bytes=size,sha256=digest,
        boot_id=reader.BOOT,physical_picture='unobserved',sequential_nonatomic=True,
        loaded_or_called_by_capture=False,chunks=provenance),indent=2)+'\n')
    print(f'PASS: copied only {Path(remote).name}; {size} bytes SHA256 {digest}.')


if __name__=='__main__':main()
