#!/usr/bin/env python3
"""Read retained exact Core ELF only; no target loads or calls."""
from pathlib import Path
import bisect
import hashlib
import re
import struct
import sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_ARM
from elftools.elf.elffile import ELFFile

ROOT=Path(__file__).resolve().parent
CORE=Path('${S95F_EVIDENCE_ROOT}/research-20261027-external/target-file-acquisition-03/SWUCoreTV')
EXPECTED='b8de9e31bf6e74cf9a1f3cfd2598658d978a4edd88b36d1c2f10129ccc8a2697'
raw=CORE.read_bytes()
if hashlib.sha256(raw).hexdigest()!=EXPECTED: raise ValueError('Core SHA256')
stream=CORE.open('rb'); elf=ELFFile(stream)
segments=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
def read(address,size):
    for s in segments:
        if s['p_vaddr']<=address and address+size<=s['p_vaddr']+s['p_filesz']:
            offset=s['p_offset']+address-s['p_vaddr']; return raw[offset:offset+size]
    raise ValueError('unmapped '+hex(address))
def word(address): return struct.unpack('<I',read(address,4))[0]
def string(address):
    try:
        b=read(address,240).split(b'\0')[0]
        return b.decode('ascii') if b and all(32<=c<127 or c in (9,10,13) for c in b) else None
    except (ValueError,UnicodeDecodeError): return None
ex=elf.get_section_by_name('.ARM.exidx'); data=ex.data(); functions=[]
for i in range(0,len(data),8):
    w=struct.unpack_from('<I',data,i)[0]&0x7fffffff
    functions.append((ex['sh_addr']+i+w-(1<<31 if w&(1<<30) else 0))&~1)
sym=elf.get_section_by_name('.dynsym'); rel=elf.get_section_by_name('.rel.plt')
got={r['r_offset']:sym.get_symbol(r['r_info_sym']).name for r in rel.iter_relocations()}
plt={}; arm=Cs(CS_ARCH_ARM,CS_MODE_ARM); arm.skipdata=True; start=None; ip=None
p=elf.get_section_by_name('.plt')
for ins in arm.disasm(p.data(),p['sh_addr']):
    m=re.fullmatch(r'ip, pc, #(0x[0-9a-f]+|[0-9]+)(?:, #(0x[0-9a-f]+|[0-9]+))?',ins.op_str)
    if ins.mnemonic=='add' and m:
        value=int(m[1],0); rotate=int(m[2],0) if m[2] else 0
        if rotate:value=((value>>rotate)|(value<<(32-rotate)))&0xffffffff
        start=ins.address; ip=ins.address+8+value
    m=re.fullmatch(r'ip, ip, #(0x[0-9a-f]+|[0-9]+)',ins.op_str)
    if ins.mnemonic=='add' and m and ip is not None: ip+=int(m[1],0)
    m=re.fullmatch(r'pc, \[ip, #(0x[0-9a-f]+|[0-9]+)\]!?',ins.op_str)
    if ins.mnemonic=='ldr' and m and ip is not None:
        at=ip+int(m[1],0)
        if at in got: plt[start]=got[at]
for address,name in list(plt.items()):
    try:
        if read(address-4,4)==b'\x78\x47\xfd\xe7':plt[address-4]=name
    except ValueError:pass
thumb=Cs(CS_ARCH_ARM,CS_MODE_THUMB); thumb.skipdata=True
def disassemble(address):
    index=bisect.bisect_right(functions,address)-1
    start,end=functions[index:index+2]
    lines=[f'EXIDX RANGE {start:08x}..{end:08x}; input {address:08x}; may contain multiple functions and literal pools']
    for ins in thumb.disasm(read(start,end-start),start):
        note=''
        if ins.mnemonic in ('bl','blx','b.w') and ins.op_str.startswith('#'):
            target=int(ins.op_str[1:],0)
            if target in plt: note=' ; '+plt[target]
        m=re.fullmatch(r'[^,]+, \[pc, #(0x[0-9a-f]+|[0-9]+)\]',ins.op_str)
        if ins.mnemonic in ('ldr','ldr.w') and m:
            at=((ins.address+4)&~3)+int(m[1],0)
            try:
                value=word(at); note+=f' ; literal[{at:08x}]={value:08x}'
                text=string(value)
                if text:note+=' '+repr(text)
                if value<0x10000:
                    try:
                        g=word(0x4ca000+value);note+=f' ; GOT?={g:08x}'
                        text=string(g)
                        if text:note+=' '+repr(text)
                    except ValueError:pass
            except ValueError: pass
        lines.append(f'{ins.address:08x} {ins.bytes.hex():10s} {ins.mnemonic:10s} {ins.op_str}{note}')
    (ROOT/f'fn-{start:08x}.txt').write_text('\n'.join(lines)+'\n')
    return start,end
if len(sys.argv)>1:
    for arg in sys.argv[1:]:
        start,end=disassemble(int(arg,0)); print(f'{start:08x}..{end:08x}')
else:
    lines=[]
    ro=elf.get_section_by_name('.rodata')
    for m in re.finditer(rb'[\x20-\x7e]{5,}\x00',ro.data()):
        text=m.group()[:-1].decode('ascii')
        if re.search(r'OUIT|OUHeader|CRC|[Cc]rc|[Ss]ignature|[Pp]adding|RSA',text):
            lines.append(f'{ro["sh_addr"]+m.start():08x} {text}')
    (ROOT/'strings.txt').write_text('\n'.join(lines)+'\n')
    (ROOT/'plt.txt').write_text('\n'.join(f'{k:08x} {v}' for k,v in sorted(plt.items()))+'\n')
    print(f'ELF pinned; {len(functions)} exidx bounds; {len(plt)} PLT symbols; {len(lines)} relevant strings')
