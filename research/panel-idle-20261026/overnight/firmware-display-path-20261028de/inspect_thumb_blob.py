#!/usr/bin/env python3
"""Bounded host-only selected Thumb-image disassembly; literal pools stay candidates."""
import argparse,hashlib,json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('sha256');p.add_argument('file_bias',type=lambda x:int(x,0));p.add_argument('va',type=lambda x:int(x,0));p.add_argument('bytes',type=lambda x:int(x,0));p.add_argument('output',type=Path);a=p.parse_args()
b=a.input.read_bytes()
if hashlib.sha256(b).hexdigest()!=a.sha256:raise ValueError('source pin')
if a.bytes<1 or a.bytes>65536 or a.va<0 or a.file_bias<0 or a.file_bias+a.va+a.bytes>len(b):raise ValueError('bound')
raw=b[a.file_bias+a.va:a.file_bias+a.va+a.bytes];meta={'source_sha256':a.sha256,'image_link_va':a.va,'file_offset':a.va+a.file_bias,'bytes':a.bytes,'range_sha256':hashlib.sha256(raw).hexdigest(),'qualification':'linear Thumb candidates; manually separate literal pools/data/branch tables'}
lines=[json.dumps(meta)]
decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB);decoder.skipdata=True
for i in decoder.disasm(raw,a.va):lines.append(f'{i.address:08x} [{i.address+a.file_bias:08x}] {i.bytes.hex():10} {i.mnemonic:8} {i.op_str}')
a.output.parent.mkdir(mode=0o700,exist_ok=True);a.output.write_text('\n'.join(lines)+'\n');a.output.chmod(0o600)
