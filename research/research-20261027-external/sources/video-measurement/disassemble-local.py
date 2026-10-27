#!/usr/bin/env python3
# Offline analysis only. Uses pre-existing analysis dependencies; invokes no target.
import sys, pathlib, hashlib, json
sys.path.insert(0, '/tmp/tcon-capstone')
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
ROOT=pathlib.Path('${S95F_EVIDENCE_ROOT}')
OUT=ROOT/'research-20261027-external/sources/video-measurement'
SELECT={
 'libvideoenhance.so.0':['ppi_ve_get_rgb_measure_condition','ppi_ve_set_rgb_measure_position','ppi_ve_get_rgb_measure_pixel'],
 'libave.so.0.1':['_Z28videoenhancer_impl_set_funcsP23ppi_videoenhancer_funcs','impl_get_rgb_measure_condition','impl_set_rgb_measure_position','impl_get_rgb_measure_pixel','ave_api_get_rgb_measure_condition','ave_api_set_rgb_measure_position','ave_api_get_rgb_measure_pixel','_Z37ave_frc_api_get_rgb_measure_conditionP18AVERgbMeasureInfo_t','_Z36ave_frc_api_set_rgb_measure_positioniii','_Z33ave_frc_api_get_rgb_measure_pixeliP15AVERgbMeasure_t']}
manifest=[]
for name, chosen in SELECT.items():
 p=ROOT/'panel-idle-20261026/binaries'/name
 with p.open('rb') as f:
  e=ELFFile(f); syms=list(e.get_section_by_name('.dynsym').iter_symbols()); lines=[]
  for s in syms:
   nm=s.name
   if nm not in chosen and not ('rgb_measure' in nm and ('ave_frc_api' in nm or 'VideoEnhancerImpl' in nm)):
    continue
   addr=s['st_value']&~1; size=s['st_size']; sec=e.get_section(s['st_shndx']); code=sec.data()[addr-sec['sh_addr']:addr-sec['sh_addr']+size]
   md=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_LITTLE_ENDIAN)
   rel=e.get_section_by_name('.rel.plt'); plt=e.get_section_by_name('.plt'); ds=e.get_section_by_name('.dynsym')
   plt_names={plt['sh_addr']+20+idx*12: ds.get_symbol(x['r_info_sym']).name for idx,x in enumerate(rel.iter_relocations())}

   lines.append(f'\n{nm} VA={addr:#x}, exported={s["st_value"]:#x}, bytes={size}\n')
   for i in md.disasm(code,addr):
    note=''
    if i.mnemonic in ['bl','blx','b','b.w'] and i.op_str.startswith('#0x'):
     dest=int(i.op_str[1:],16)
     if dest in plt_names: note=' ; PLT '+plt_names[dest]
    lines.append(f'{i.address:08x}  {i.bytes.hex():12s} {i.mnemonic:8s} {i.op_str}'+note)
  (OUT/(name+'.rgb.disasm.txt')).write_text('\n'.join(lines)+'\n')
 manifest.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'target-binary-pins.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Resolve the exact registration literals/GOT relocations for the three RGB slots.
import struct
p=ROOT/'panel-idle-20261026/binaries/libave.so.0.1'
with p.open('rb') as f:
 e=ELFFile(f)
 def word(addr):
  for sec in e.iter_sections():
   if sec['sh_type']!='SHT_NOBITS' and sec['sh_addr']<=addr<sec['sh_addr']+sec['sh_size']:
    return struct.unpack_from('<I',sec.data(),addr-sec['sh_addr'])[0]
  raise ValueError(hex(addr))
 base=word(0x2a14a0)+0x2a079a
 relmap={}
 for sec in e.iter_sections():
  if sec['sh_type']=='SHT_REL':
   ds=e.get_section(sec['sh_link'])
   for r in sec.iter_relocations(): relmap[r['r_offset']]=ds.get_symbol(r['r_info_sym']).name
 rows=[]
 for off,pool in [(0xb0,0x2a1554),(0xb4,0x2a1558),(0xb8,0x2a155c)]:
  got=base+word(pool)
  rows.append({'backend_table_offset':hex(off),'pool_va':hex(pool),'got_base':hex(base),'got_slot':hex(got),'got_relocation_symbol':relmap.get(got),'file_value':hex(word(got))})
 (OUT/'backend-slot-resolution.json').write_text(json.dumps(rows,indent=2)+'\n')
