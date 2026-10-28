#!/usr/bin/env python3
"""Host-only ELF64/AArch64 bounded symbol disassembly with relocations, no execution."""
import argparse,hashlib,json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from elftools.elf.elffile import ELFFile
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('sha256');p.add_argument('output',type=Path);p.add_argument('symbols',nargs='+');a=p.parse_args()
raw=a.input.read_bytes()
if hashlib.sha256(raw).hexdigest()!=a.sha256:raise ValueError('source pin')
a.output.mkdir(mode=0o700,exist_ok=True)
with a.input.open('rb') as h:
 e=ELFFile(h)
 if e['e_machine']!='EM_AARCH64':raise ValueError('not AArch64')
 sy=e.get_section_by_name('.symtab');symbols={s.name:s for s in sy.iter_symbols()};rels={}
 for sec in e.iter_sections():
  if sec['sh_type']!='SHT_RELA':continue
  target=e.get_section(sec['sh_info']).name;ss=e.get_section(sec['sh_link'])
  for r in sec.iter_relocations():
   s=ss.get_symbol(r['r_info_sym']);name=s.name
   if s['st_info']['type']=='STT_SECTION':name=e.get_section(s['st_shndx']).name
   rels.setdefault((target,r['r_offset']),[]).append({'target':name,'addend':r['r_addend'],'type':r['r_info_type']})
 functions=[];lines=[]
 for name in a.symbols:
  s=symbols[name]
  if not isinstance(s['st_shndx'],int) or not s['st_size'] or s['st_size']>65536:raise ValueError('symbol bound')
  sec=e.get_section(s['st_shndx']);lo=s['st_value'];off=sec['sh_offset']+lo;code=raw[off:off+s['st_size']]
  meta={'name':name,'section':sec.name,'section_offset':lo,'file_offset':off,'bytes':s['st_size'],'sha256':hashlib.sha256(code).hexdigest(),'relocations':[]}
  lines.append('\n'+json.dumps(meta))
  for i in Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(code,lo):
   r=rels.get((sec.name,i.address),[])
   if r:meta['relocations'].append({'section_offset':i.address,'entries':r})
   lines.append(f'{i.address:08x} [{off+i.address-lo:08x}] {i.bytes.hex()} {i.mnemonic:8} {i.op_str}'+(' ; '+json.dumps(r) if r else ''))
  functions.append(meta)
 (a.output/'functions.json').write_text(json.dumps({'source_sha256':a.sha256,'functions':functions},indent=2)+'\n')
 (a.output/'functions.disasm').write_text('\n'.join(lines)+'\n')
 for n in ['functions.json','functions.disasm']:(a.output/n).chmod(0o600)
