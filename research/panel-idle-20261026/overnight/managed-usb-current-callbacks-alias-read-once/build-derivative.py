#!/usr/bin/env python3
"""Mechanically derive one fixed DMA-alias callback reader from the 64-byte reader."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
SOURCE=BASE/'managed-usb-current-callbacks-read-once'
DOTNET=BASE.parents[1]/'live-cast/sdk/runtime/dotnet'
PROGRAM_PARENT='1a333a85ab001e5f64e27a1e416840a61b1f2b7f24921212388257a2b91705f3'
WRAPPER_PARENT='430871ea0cabfc46c42dcb8bc5a8651679019591b5aa67b916e3a58b2e7329db'
ADDRESS=0x45000580
LENGTH=64
HEADER=struct.pack('<III',0x101,ADDRESS,LENGTH).hex()

def need(ok,why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def replace_exact(text,old,new,count):
    need(text.count(old)==count,'occurrence count '+old)
    return text.replace(old,new)

def main():
    need(HEADER=='010100008005004540000000','derived header')
    need(sha((SOURCE/'Program.cs').read_bytes())==PROGRAM_PARENT,'program parent pin')
    need(sha((SOURCE/'run-once.py').read_bytes())==WRAPPER_PARENT,'wrapper parent pin')
    program=(SOURCE/'Program.cs').read_text()
    program=replace_exact(program,'010100008005002040000000',HEADER.upper(),2)
    program=replace_exact(program,'address = "0x20000580"','address = "0x45000580"',1)
    program=replace_exact(program,'opaque-current-callback-table-memory-IN','opaque-current-callback-table-DMA-alias-IN',1)
    (HERE/'Program.cs').write_text(program)
    project='ManagedUsbRtBlockReadOnce.csproj'
    (HERE/project).write_bytes((SOURCE/project).read_bytes())
    wrapper=(SOURCE/'run-once.py').read_text()
    wrapper=replace_exact(wrapper,'010100008005002040000000',HEADER,1)
    wrapper=replace_exact(wrapper,'usb-fixed-current-callbacks-read-build-v1','usb-fixed-current-callbacks-alias-read-build-v1',1)
    wrapper=replace_exact(wrapper,'"address": "0x20000580", "length": 64','"address": "0x45000580", "length": 64',1)
    (HERE/'run-once.py').write_text(wrapper)
    built=subprocess.run([str(DOTNET),'build','-c','Release','--nologo',str(HERE/project)],capture_output=True,text=True)
    (HERE/'build.log').write_text(built.stdout+built.stderr)
    need(built.returncode==0,'build failed')
    dll=HERE/'bin/Release/net6.0/ManagedUsbRtBlockReadOnce.dll'
    checks=[]
    for args,expected in (([],0),(['--self-test'],0),(['--execute'],64),(['--unknown'],63)):
        done=subprocess.run([str(DOTNET),str(dll),*args],capture_output=True,text=True)
        need(done.returncode==expected,'host check '+str(args))
        checks.append(dict(args=args,exit_code=done.returncode,stdout=done.stdout,stderr=done.stderr))
    names=['Program.cs',project]+['bin/Release/net6.0/ManagedUsbRtBlockReadOnce.'+suffix for suffix in ('dll','deps.json','runtimeconfig.json')]
    manifest=dict(schema='usb-fixed-current-callbacks-alias-read-build-v1',source_parent_sha256=PROGRAM_PARENT,
                  wrapper_parent_sha256=WRAPPER_PARENT,fixed_target='0x101',fixed_address=hex(ADDRESS),
                  fixed_length=LENGTH,header_hex=HEADER,
                  files={name:dict(size=len((HERE/name).read_bytes()),sha256=sha((HERE/name).read_bytes())) for name in names},
                  checks=checks,
                  acceptance_scope='Exact counts and cleanup only; opaque 64-byte controller DMA-alias snapshot. Alias/core mapping and callback-table identity require separate static proof.')
    raw=(json.dumps(manifest,indent=2)+'\n').encode()
    (HERE/'build-manifest.json').write_bytes(raw)
    print(json.dumps(dict(program_sha256=sha((HERE/'Program.cs').read_bytes()),wrapper_sha256=sha((HERE/'run-once.py').read_bytes()),
                          manifest_sha256=sha(raw),dll_sha256=sha(dll.read_bytes()),checks=len(checks)),indent=2))

if __name__=='__main__':
    main()
