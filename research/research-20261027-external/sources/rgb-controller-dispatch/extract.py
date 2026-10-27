#!/usr/bin/env python3
from pathlib import Path
import json,hashlib
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
BASE=Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/binaries')
OUT=Path(__file__).resolve().parent
SELECTIONS={
 'tztv_frc_tcon_api.ko':['map_extra_functions','map_frc_functions','FRC_GetRgbMeasureCondition','FRC_SetRgbMeasurePosition','FRC_GetRgbMeasureInfo'],
 'tztv_frc_tcon.ko':['_tztv_frc_tcon_ext_cmd','resolve_symbol','_tztv_get_chip_type','tztv_frc_tcon_probe'],
 'rosem_frc.ko':['init_module','RosemFrc_GetRgbMeasureConditonInfo','m_rosem_get_rgb_measure_conditon','RosemFrc_SetRgbMeasurePostion','RosemFrc_GetRgbMeasureInfo'],
 'sdp_frc.ko':['get_instance_of_display_output_coordinator.part.0','devio_access_disable','devio_access_enable','__dummy_read','__dummy_write','sdp_display_ex_proc','dispay_coordinator_ex_proc','display_coordinator_Init','disp_coord_set','get_instance_of_display_output_coordinator','display_output_coordinator_Init','display_output_do_process','get_display_device_frc','get_instance_of_abstract_display_device_frc','display_device_frc_Init','dd_frc_send_trig_bypass','sdp_frc_ex_proc','sdp_frc_dev_cust_get_pixel_measure','sdp_frc_set_position','sdp_frc_resource_init','wrap_read','wrap_write','ft_read','ft_write','__devio_read','__devio_write']}
manifest=[]
for name,selected in SELECTIONS.items():
 p=BASE/name
 with p.open('rb') as f:
  e=ELFFile(f);sy=e.get_section_by_name('.symtab'); symbols=list(sy.iter_symbols()); rels={}
  for sec in e.iter_sections():
   if isinstance(sec,RelocationSection):
    rs=e.get_section(sec['sh_link'])
    for r in sec.iter_relocations():
     sym=rs.get_symbol(r['r_info_sym']);rels.setdefault((sec['sh_info'],r['r_offset']),[]).append(f"{r['r_info_type']} {sym.name or ('<'+e.get_section(sym['st_shndx']).name+'>' if isinstance(sym['st_shndx'],int) else str(sym['st_shndx']))} + {r['r_addend']:#x}")
  lines=[]; funcs=[]
  for s in symbols:
   if s.name not in selected:continue
   si=s['st_shndx'];sec=e.get_section(si);a=s['st_value'];data=sec.data()[a:a+s['st_size']]
   funcs.append({'name':s.name,'section':sec.name,'offset':hex(a),'size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
   lines.append(f"\n### {s.name} {sec.name}+{a:#x} size {len(data):#x}")
   for i in Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(data,a):
    rr=rels.get((si,i.address),[])
    lines.append(f'{i.address:08x} {i.mnemonic:8} {i.op_str}'+(' ; RELOC '+ ' | '.join(rr) if rr else ''))
  (OUT/(name+'.disasm.txt')).write_text('\n'.join(lines)+'\n')
  # retain complete relocation map to reproduce table/section references
  (OUT/(name+'.relocs.json')).write_text(json.dumps([{'section':e.get_section(si).name,'offset':hex(a),'relocations':r} for (si,a),r in rels.items()],indent=2)+'\n')
  (OUT/(name+'.symbols.json')).write_text(json.dumps([{'name':s.name,'section':e.get_section(s['st_shndx']).name if isinstance(s['st_shndx'],int) else s['st_shndx'],'offset':hex(s['st_value']),'size':s['st_size']} for s in symbols],indent=2)+'\n')
  manifest.append({'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'functions':funcs})
(OUT/'source-inventory.json').write_text(json.dumps({'scope':'Offline retained AArch64 modules; no target execution, acquisition or network device interaction.','modules':manifest},indent=2)+'\n')
