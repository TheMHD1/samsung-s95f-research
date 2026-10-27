#!/usr/bin/env python3
"""Build a fixed 8192-byte read to qualify the stock backup chunk size."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE/'managed-usb-emmc-sector-read-once'
BUILD = BASE/'managed-usb-emmc-prefix-8192'
DOTNET = BASE.parents[1]/'live-cast/sdk/runtime/dotnet'

def need(ok, why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    need(sha((SOURCE/'Program.cs').read_bytes()) == 'b4e400c973fc5c6c7737a0c6e21fe291c9320d57403e86968d0c6c5180293e49', 'source pin')
    need(sha((SOURCE/'run-once.py').read_bytes()) == '1a6c5870cc4eb33493d6bfe3b79eca03ab108741ae251a02014fe1ea85f1ffc5', 'wrapper pin')
    BUILD.mkdir(exist_ok=False)
    header = '030200000000000000200000'
    source = (SOURCE/'Program.cs').read_text().replace('030200000000000000020000', header).replace('const int Length = 512,', 'const int Length = 8192,')
    (BUILD/'Program.cs').write_text(source)
    project = 'ManagedUsbEmmcSectorReadOnce.csproj'
    (BUILD/project).write_bytes((SOURCE/project).read_bytes())
    wrapper = (SOURCE/'run-once.py').read_text().replace('030200000000000000020000', header).replace('"input_length": 512', '"input_length": 8192').replace('"length": 512', '"length": 8192')
    (BUILD/'run-once.py').write_text(wrapper)
    done = subprocess.run([str(DOTNET),'build','-c','Release','--nologo',str(BUILD/project)],capture_output=True,text=True)
    (BUILD/'build.log').write_text(done.stdout+done.stderr)
    need(done.returncode == 0, 'build')
    checks = []
    for args, rc in (([],0),(['--self-test'],0),(['--execute'],64),(['--unknown'],63)):
        done = subprocess.run([str(DOTNET),str(BUILD/'bin/Release/net6.0/ManagedUsbEmmcSectorReadOnce.dll'),*args],capture_output=True,text=True)
        need(done.returncode == rc, 'check '+str(args))
        checks.append(dict(args=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr))
    names = ['Program.cs',project]+['bin/Release/net6.0/ManagedUsbEmmcSectorReadOnce.'+s for s in ('dll','deps.json','runtimeconfig.json')]
    manifest = dict(schema='usb-fixed-emmc-sector-read-build-v1',fixed_target='0x203',fixed_address='0x0',fixed_length=8192,header_hex=header,
                    files={n:dict(size=len((BUILD/n).read_bytes()),sha256=sha((BUILD/n).read_bytes())) for n in names},checks=checks,
                    acceptance_scope='Exact transport and cleanup; discarded storage-leaf status and executing-code identity remain unproved.')
    raw = (json.dumps(manifest,indent=2)+'\n').encode()
    (BUILD/'build-manifest.json').write_bytes(raw)
    row = dict(build=str(BUILD),manifest_sha256=sha(raw),wrapper_sha256=sha((BUILD/'run-once.py').read_bytes()),header_hex=header,address='0x0',length=8192)
    (HERE/'prefix-build.json').write_text(json.dumps(row,indent=2)+'\n')
    print(json.dumps(row))

if __name__ == '__main__':
    main()
