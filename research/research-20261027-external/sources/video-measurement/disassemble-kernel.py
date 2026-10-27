#!/usr/bin/env python3
# Offline only, pre-existing analysis dependencies.
import sys,pathlib,json,hashlib
sys.path.insert(0,'/tmp/tcon-capstone')
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
ROOT=pathlib.Path('${S95F_EVIDENCE_ROOT}'); OUT=ROOT/'research-20261027-external/sources/video-measurement'
SELECT={'rosem_frc.ko':['m_rosem_get_rgb_measure_conditon','RosemFrc_GetRgbMeasureConditonInfo','RosemFrc_SetRgbMeasurePostion','RosemFrc_GetRgbMeasureInfo'],'sdp_frc.ko':['sdp_frc_do_ioctl']}
pins=[]
for name,names in SELECT.items():
 p=ROOT/'panel-idle-20261026/binaries'/name
 with p.open('rb') as f:
  e=ELFFile(f); st=e.get_section_by_name('.symtab'); rels={}
  for sec in e.iter_sections():
   if sec['sh_type']!='SHT_RELA': continue
   for rel in sec.iter_relocations():
    sym=st.get_symbol(rel['r_info_sym']); key=(sec['sh_info'],rel['r_offset'])
    rels[key]=f"{sym.name} + {rel['r_addend']:#x} (type {rel['r_info_type']})"
  lines=[]
  for s in st.iter_symbols():
   if s.name not in names: continue
   sec=e.get_section(s['st_shndx']); addr=s['st_value']; code=sec.data()[addr:addr+s['st_size']]
   lines.append(f'\n{s.name} .text+{addr:#x}, bytes={s["st_size"]}')
   for i in Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN).disasm(code,addr):
    note=rels.get((s['st_shndx'],i.address),'')
    lines.append(f'{i.address:08x}  {i.bytes.hex():12s} {i.mnemonic:8s} {i.op_str}'+ (' ; '+note if note else ''))
  (OUT/(name+'.rgb.disasm.txt')).write_text('\n'.join(lines)+'\n')
 pins.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'kernel-binary-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
