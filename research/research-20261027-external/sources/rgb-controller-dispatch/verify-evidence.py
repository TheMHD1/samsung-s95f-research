#!/usr/bin/env python3
"""Hash-gated offline landmark check; never loads or executes target code."""
from pathlib import Path
import hashlib,json,struct
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
ROOT=Path('${S95F_EVIDENCE_ROOT}');OUT=Path(__file__).resolve().parent
PINS={'rosem_frc.ko':'c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34','tztv_frc_tcon.ko':'aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd','tztv_frc_tcon_api.ko':'3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6','sdp_frc.ko':'05dea2eaad34a23def837fb86d2f7a4e99ef630066ad6fed18d0cf55ba37063d'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(x,label):
 if not x:raise AssertionError(label)
checks=[]
for n,h in PINS.items():need(sha(ROOT/'panel-idle-20261026/binaries'/n)==h,n+' hash')
p=ROOT/'panel-idle-20261026/binaries/sdp_frc.ko'
with p.open('rb') as f:
 e=ELFFile(f);text=e.get_section_by_name('.text').data();data=e.get_section_by_name('.data').data()
 want={0x2798:('cmp','w20, #0x400'),0x279c:('b.eq','#0x28e8'),0xa138:('cmp','w1, #2'),0xa13c:('b.eq','#0xa270'),0xa148:('cmp','w1, #1'),0xa14c:('b.eq','#0xa17c'),0xa1f8:('cmp','w21, #1'),0xa1fc:('b.hi','#0xa37c'),0xa27c:('cmp','w2, #1'),0xa280:('b.hi','#0xa37c'),0xa2a0:('b.lo','#0xa38c'),0xa2ac:('b.lo','#0xa38c'),0xa250:('and','w1, w1, #0x3ff'),0x1e684:('str','w1, [x0]'),0x1e6d8:('ldr','w0, [x0]'),0xce50:('ldr','x0, [x0, #0x138]'),0x1e30:('str','x0, [x22, #0x138]')}
 for off,w in want.items():
  i=next(Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(text[off:off+4],off));need((i.mnemonic,i.op_str)==w,hex(off));checks.append(f'.text+{off:#x}: {i.mnemonic} {i.op_str}')
 condition=list(struct.unpack_from('<6I',data,0xf88));need(condition==[2,16,16,20,3840,2160],'condition table')
 rel=[]
 for sec in e.iter_sections():
  if isinstance(sec,RelocationSection):
   sy=e.get_section(sec['sh_link']);target=e.get_section(sec['sh_info']).name
   for r in sec.iter_relocations():
    s=sy.get_symbol(r['r_info_sym']); rel.append((target,r['r_offset'],s.name,r['r_addend']))
 for row in [('.text',0x28f0,'sdp_frc_dev_cust_get_pixel_measure',0),('.text',0xa1f0,'wrap_read',0),('.text',0xa210,'wrap_read',0),('.text',0xa2c0,'wrap_write',0),('.text',0x1e2c,'devm_ioremap_resource',0),('.data',0x21650,'allowed_access',0)]:need(row in rel,'relocation '+str(row))
 dtroot=ROOT/'panel-idle-20261026/overnight/devicetree/soc/sdp_frc'
 reg=(dtroot/'reg').read_bytes();need(reg==bytes.fromhex('00b900000005f000'),'retained DT frc reg')
 evidence={'checks':checks,'condition_data_offset':'sdp_frc.ko .data+0xf88','condition_u32':condition,'dt':{'path':str(dtroot),'reg_u32_be':list(struct.unpack('>2I',reg)),'reg_names':(dtroot/'reg-names').read_bytes().decode().replace('\0','')},'register_offsets':{'normalization_selector':'0x22188','slot0':{'control':'0x22190','x':'0x22194','y':'0x22198','R':'0x221b4','G':'0x221ac','B':'0x221b0'},'slot1':{'control':'0x221a0','x':'0x221a4','y':'0x221a8','R':'0x221f0','G':'0x221e8','B':'0x221ec'}},'prepd_literal_census':{},'limits':['Instruction/relocation landmarks only, not emulation or all-path proof.','DT address is retained bus resource; missing parent ranges prevent independent final physical translation.','No current callback/base/gating/selected-controller executable proof.','No freshness acknowledgment, hardware register specification or actual PrePD writer edge recovered.']}
 for n in PINS:
  d=(ROOT/'panel-idle-20261026/binaries'/n).read_bytes()
  evidence['prepd_literal_census'][n]={}
  for address in [0x584109a4,0x58410aa4]:
   for endian in ['little','big']:
    token=address.to_bytes(4,endian);hits=[];off=d.find(token)
    while off>=0:hits.append(hex(off));off=d.find(token,off+1)
    evidence['prepd_literal_census'][n][hex(address)+'_'+endian]=hits
(OUT/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
inv=json.loads((OUT/'source-inventory.json').read_text())
context=[ROOT/'research-20261027-external/reports/video-measurement.md',ROOT/'research-20261027-external/sources/video-measurement/inventory.json',ROOT/'panel-idle-20261026/tcon-research/qd-rt-controller-identity-boundary.md',ROOT/'panel-idle-20261026/tcon-research/frc-extension-and-sdp-register-path.md']
inv['context_inputs']=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in context]
inv['retained_device_tree_inputs']=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dtroot.iterdir())]
(OUT/'source-inventory.json').write_text(json.dumps(inv,indent=2)+'\n')
print('PASS: four full-file pins; dispatch, bounds, normalization, MMIO and mapping landmarks; six-word table; retained DT resource. No target code executed.')
