#!/usr/bin/env python3
"""Host-only bounded symbol/call evidence; no OEM execution. Linear decoding marks candidates."""
import argparse,hashlib,json,os,struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB
from capstone.arm import ARM_OP_IMM,ARM_OP_MEM,ARM_REG_IP,ARM_REG_PC

def inspect(path, names):
 raw=path.read_bytes(); f=path.open('rb'); elf=ELFFile(f); symbols={}; byva={}; sections=list(elf.iter_sections())
 for table in (elf.get_section_by_name('.dynsym'),elf.get_section_by_name('.symtab')):
  if table:
   for s in table.iter_symbols():
    if s['st_shndx']!='SHN_UNDEF' and s['st_info']['type']=='STT_FUNC' and s['st_size']:
     v=int(s['st_value']); rec={'name':s.name,'va':v&~1,'thumb':bool(v&1),'size':int(s['st_size']),'section':int(s['st_shndx'])};symbols[s.name]=rec;byva.setdefault(v&~1,[]).append(s.name)
 plt=elf.get_section_by_name('.plt');rel=elf.get_section_by_name('.rel.plt');pltmap={}
 if plt and rel:
  dyn=elf.get_section(rel['sh_link'])
  dyn=elf.get_section(rel['sh_link']); gotnames={int(r['r_offset']):dyn.get_symbol(r['r_info_sym']).name+'@plt' for r in rel.iter_relocations()}
  # Decode each ARM add/add/ldr PLT entry against its actual relocation target.
  arm=Cs(CS_ARCH_ARM,CS_MODE_ARM);arm.detail=True; po=int(plt['sh_offset']);pv=int(plt['sh_addr'])
  for step in range(0,int(plt['sh_size'])-11,4):
   ins=list(arm.disasm(raw[po+step:po+step+12],pv+step))
   if len(ins)!=3:continue
   x,y,z=ins
   if x.mnemonic=='add' and y.mnemonic=='add' and z.mnemonic=='ldr':
    xo,yo,zo=x.operands,y.operands,z.operands
    if len(xo) in (3,4) and len(yo) in (3,4) and len(zo)==2 and xo[0].reg==ARM_REG_IP and xo[1].reg==ARM_REG_PC and xo[2].type==ARM_OP_IMM and yo[0].reg==ARM_REG_IP and yo[1].reg==ARM_REG_IP and yo[2].type==ARM_OP_IMM and zo[0].reg==ARM_REG_PC and zo[1].type==ARM_OP_MEM and zo[1].mem.base==ARM_REG_IP:
     def arm_imm(i):
      w=struct.unpack('<I',i.bytes)[0];v=w&255;r=((w>>8)&15)*2;return ((v>>r)|(v<<(32-r)))&0xffffffff if r else v
     got=(x.address+8+arm_imm(x)+arm_imm(y)+zo[1].mem.disp)&0xffffffff
     if got in gotnames:pltmap[x.address]=gotnames[got]

 out=[]; text=[]
 for name in names:
  if name not in symbols:continue
  s=symbols[name].copy();sec=sections[s.pop('section')];off=s['va']-int(sec['sh_addr'])+int(sec['sh_offset']);code=raw[off:off+s['size']];s.update(file_offset=off,sha256=hashlib.sha256(code).hexdigest(),calls=[],indirect=[])
  md=Cs(CS_ARCH_ARM,CS_MODE_THUMB if s['thumb'] else CS_MODE_ARM);md.detail=True
  text.append('\n'+name+' '+json.dumps(s))
  for ins in md.disasm(code,s['va']):
   target=None
   if ins.mnemonic in ('bl','blx','b','b.w') and ins.operands and ins.operands[0].type==ARM_OP_IMM:
    target=ins.operands[0].imm&~1
    if target in byva or target in pltmap:
     edge={'site':ins.address,'file_offset':off+ins.address-s['va'],'target':target,'names':byva.get(target,[pltmap.get(target)]),'kind':ins.mnemonic,'qualification':'linear_decode_candidate'};s['calls'].append(edge)
   if ins.mnemonic in ('blx','bx') and ins.op_str not in ('lr',) and target is None:s['indirect'].append({'site':ins.address,'operand':ins.op_str})
   text.append(f'{ins.address:08x} [{off+ins.address-s["va"]:08x}] {ins.bytes.hex():10} {ins.mnemonic:8} {ins.op_str}'+(' ; '+','.join(byva.get(target,[pltmap.get(target,'')])) if target else ''))
  out.append(s)
 f.close();return {'path':str(path),'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'elf_link_addresses_not_runtime':True,'linear_decoding_requires_manual_control_flow_review':True,'functions':out},'\n'.join(text)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);p.add_argument('names',nargs='+');a=p.parse_args()
 result,dis=inspect(a.input,a.names);a.output.mkdir(mode=0o700,exist_ok=True)
 for n,v in [('functions.json',json.dumps(result,indent=2)+'\n'),('functions.disasm',dis+'\n')]:
  dest=a.output/n;dest.write_text(v);dest.chmod(0o600)
