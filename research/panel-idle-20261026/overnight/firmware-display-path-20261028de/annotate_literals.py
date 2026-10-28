#!/usr/bin/env python3
"""Bounded PC-relative ARM Thumb literal annotations. No control-flow/dataflow proof."""
import argparse,json,struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from capstone.arm import ARM_OP_MEM,ARM_OP_REG,ARM_OP_IMM,ARM_REG_PC
p=argparse.ArgumentParser();p.add_argument('elf',type=Path);p.add_argument('functions',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
raw=a.elf.read_bytes();f=a.elf.open('rb');e=ELFFile(f);secs=list(e.iter_sections())
def offset(va):
 for s in secs:
  if s['sh_type']!='SHT_NOBITS' and (int(s['sh_flags'])&2) and s['sh_addr']<=va<s['sh_addr']+s['sh_size']:return int(s['sh_offset'])+va-int(s['sh_addr'])
 return None
def desc(v):
 o=offset(v)
 if o is None:return ''
 z=raw[o:o+256].split(b'\0')[0]
 return z.decode('ascii') if 3<=len(z)<256 and all(32<=c<=126 or c in(9,10,13) for c in z) else ''
out=[]
for fn in json.loads(a.functions.read_text())['functions']:
 md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);md.detail=True;regs={};out.append('\n'+fn['name']);start=fn['file_offset']
 for i in md.disasm(raw[start:start+fn['size']],fn['va']):
  ops=i.operands;v=None;dst=None
  if i.mnemonic.startswith('ldr') and len(ops)==2 and ops[0].type==ARM_OP_REG and ops[1].type==ARM_OP_MEM and ops[1].mem.base==ARM_REG_PC:
   pos=((i.address+4)&~3)+ops[1].mem.disp;o=offset(pos)
   if o is not None:v=struct.unpack_from('<I',raw,o)[0];dst=ops[0].reg
  elif i.mnemonic in ('add','add.w','adds') and len(ops)>=2 and ops[0].type==ARM_OP_REG:
   dst=ops[0].reg
   if len(ops)==2 and ops[1].type==ARM_OP_REG and ops[1].reg==ARM_REG_PC and dst in regs:v=(regs[dst]+i.address+4)&0xffffffff
   elif len(ops)==2 and ops[1].type==ARM_OP_IMM and dst in regs:v=(regs[dst]+ops[1].imm)&0xffffffff
  elif i.mnemonic in ('mov','movs','movw') and len(ops)==2 and ops[0].type==ARM_OP_REG and ops[1].type==ARM_OP_IMM:dst=ops[0].reg;v=ops[1].imm
  elif i.mnemonic=='movt' and len(ops)==2 and ops[0].reg in regs:dst=ops[0].reg;v=(regs[dst]&65535)|(ops[1].imm<<16)
  if dst is not None and v is not None:
   regs[dst]=v;d=desc(v)
   if d:out.append(f'{i.address:#x} {i.mnemonic} {i.op_str} => {v:#x} file {offset(v):#x}: {d!r}')
  # Straight-line annotation is intentionally approximate; branch/call boundaries reset known values.
  if i.mnemonic.startswith('b') and i.mnemonic not in ('bic','bics','bfi','bfc'):regs.clear()
a.out.write_text('\n'.join(out)+'\n');a.out.chmod(0o600)
