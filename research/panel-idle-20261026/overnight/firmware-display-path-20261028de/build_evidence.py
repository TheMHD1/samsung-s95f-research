#!/usr/bin/env python3
"""Build sanitized display-path evidence from local, already extracted source metadata."""
import hashlib,json,struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
D=Path(__file__).resolve().parent;B=D.parent;R=B.parent
DB=B/'firmware-platform-analysis-20261028db/private';PRD=DB/'prd-extracted/tree/root';PLTF=DB/'pltf-extracted/tree/root'
AVE=PRD/'usr/lib/libave.so.0.1';DLOG=PLTF/'usr/lib/libdlog.so.0.0.0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,j): (D/n).write_text(json.dumps(j,indent=2)+'\n')
inputs=[('prd-ave',AVE,'PRD:/usr/lib/libave.so.0.1'),('live-ave',R/'binaries/libave.so.0.1','retained-live:/usr/lib/libave.so.0.1'),('prd-tconfw',PRD/'usr/fwupdate/controls/libtconfw.so','PRD:/usr/fwupdate/controls/libtconfw.so'),('pltf-dlog',DLOG,'PLTF:/usr/lib/libdlog.so.0.0.0'),('pltf-vlogutil',PLTF/'usr/bin/vlogutil','PLTF:/usr/bin/vlogutil'),('npc-json',PRD/'usr/bin/ave/pq/LUT_NPC_Point.json','PRD:/usr/bin/ave/pq/LUT_NPC_Point.json')]
for n in ['qdf_tcon.ko','tztv_frc_tcon.ko','tztv_frc_tcon_api.ko','soc/sdp_frc.ko','soc/sdp_tcon.ko','soc/sdp_pqe_frc.ko']:inputs.append(('module-'+Path(n).stem,PLTF/'usr/lib/modules/5.4.261/kernel'/n,'PLTF:/usr/lib/modules/5.4.261/kernel/'+n))
sources=[{'id':i,'path':label,'bytes':p.stat().st_size,'sha256':sha(p)} for i,p,label in inputs]
if sources[0]['sha256']!=sources[1]['sha256']:raise ValueError('AVE identity mismatch')
functions=[]
for group in ['ave-first','ave-second','ave-content','ave-upstream','ave-debug','dlog']:
 j=json.loads((D/'private'/group/'functions.json').read_text())
 for f in j['functions']:
  functions.append(dict(f,source_id='pltf-dlog' if group=='dlog' else 'prd-ave',private_evidence=group+'/functions.disasm'))
# Deduplicate symbols without conflating aliases.
functions=list({(f['source_id'],f['name']):f for f in functions}.values())
vtable=[]
with AVE.open('rb') as fd:
 e=ELFFile(fd)
 for sec in e.iter_sections():
  if sec['sh_type']!='SHT_REL':continue
  syms=e.get_section(sec['sh_link'])
  for r in sec.iter_relocations():
   v=r['r_offset']
   if 0x5a1524<=v<0x5a1524+588:
    name=syms.get_symbol(r['r_info_sym']).name
    if name in {f['name'] for f in functions}:vtable.append({'slot_va':v,'vptr_relative_offset':v-0x5a152c,'target':name,'relocation_type':r['r_info_type']})
provider=[];p=PLTF/'usr/lib/modules/5.4.261/kernel/tztv_frc_tcon.ko'
with p.open('rb') as fd:
 e=ELFFile(fd);sy=e.get_section_by_name('.symtab');rel=e.get_section_by_name('.rela.text')
 for s in sy.iter_symbols():
  if s.name not in ['_tztv_gpio_get_value','_tztv_gpio_get_value2','_tztv_frc_tcon_read_pmic_status','_tztv_frc_tcon_read_err_det_status','_tztv_frc_tcon_read_vdd_det_status']:continue
  sec=e.get_section(s['st_shndx']);calls=[]
  for r in rel.iter_relocations():
   if s['st_value']<=r['r_offset']<s['st_value']+s['st_size'] and r['r_info_type'] in (282,283):calls.append({'section_offset':r['r_offset'],'target':sy.get_symbol(r['r_info_sym']).name})
  provider.append({'name':s.name,'section':sec.name,'section_offset':s['st_value'],'file_offset':sec['sh_offset']+s['st_value'],'bytes':s['st_size'],'calls':calls})
npc=json.loads((PRD/'usr/bin/ave/pq/LUT_NPC_Point.json').read_text());npcshape={'version':npc['version'],'compensation_group_count':len(npc['infoTBL']),'status_counts':[len(g['status']) for g in npc['infoTBL']],'entries_per_status':sorted({len(s['value']) for g in npc['infoTBL'] for s in g['status']}),'raw_table_exported':False}
logger=[{'id':'npc-change','site':0x1c7444,'format_offset':0x53f5b0,'buffer_id':0,'priority':6,'tag':'AVE','gate':'selected LUT differs from cached siNpcLut; after 16 sends and set_npc_lut','fields':{'CompenRatio':'backend-state+0x2e8c','LUT':'selected index sl; also AVEshm+0x9a1c','HDR':'request byte8 or byte9 (normalized selected branch)','isMovie':'computed picture-mode class boolean','P.Mode':'request uint32+0','PeakBri':'request uint32+4','Fac':'request byte0xa'}}, {'id':'npc-addresses','site':0x1c75a0,'format_offset':0x53f620,'buffer_id':0,'priority':6,'tag':'AVE','gate':'same change branch; mirrors sixteen command addresses'}, {'id':'npc-repeat','site':0x1c764a,'format_offset':0x53f6dc,'buffer_id':0,'priority':4,'tag':'AVE','gate':'backend state word0 bit6 (0x40) enabled; may run each invocation'}, {'id':'npc-usb-repeat','site':0x1c7684,'gate':'same bit6 plus AVEshm+0x68 nonzero','sink':'print_usb_file, not necessarily VLOG'}, {'id':'scene-screenprotect-change','site':0x1c63f2,'format_offset':0x53dc04,'buffer_id':0,'priority':6,'tag':'AVE','gate':'request+0x60 differs from cached siPreScreenProtectedApp; precedes FRC0x42618 write','fields':{'previous':'cached word before write','new':'request uint32+0x60'}}, {'id':'final-duty','site':0x1c6318,'format_offset':0x53f0c4,'buffer_id':0,'priority':4,'tag':'AVE','gate':'backend debugmask conditional; exact site verified by checker only if retained','fields':{'labels':['DimLvl','F_Duty(INPUT)','APL_Gain']}}]
# Remove final-duty site until exact branch/site is separately reviewed; preserve request/send as graph anchors.
logger=[x for x in logger if x['id']!='final-duty']
evidence={'schema':'display-path-evidence-v1','scope':'host-only static analysis; no TV/OEM execution','sources':sources,'functions':functions,'vtable':vtable,'provider_calls':provider,'npc_resource_shape':npcshape,'loggers':logger,'qualifications':['All AVE VAs are ELF link VAs, not current process addresses.','Linear-disassembly call inventories are candidates; graph below uses only selected manually reviewed body sites.','BSS has no corresponding initialized file bytes.','Runtime QD backend object/vptr not remeasured by this task.','Authenticated payload plus extraction success does not prove every VDFS per-file RSA scope.','No AP_EXCO data-field bridge to scene registers is proven.']}
save('evidence.json',evidence)
sourcebyid={s['id']:s for s in sources};nodes=[];edges=[];fnbyname={f['name']:f for f in functions};seen=set()
def node(id,label,kind='function',ref=None,limitations=None):
 if id in seen:return
 seen.add(id);nodes.append({'id':id,'kind':kind,'label':label,'source_refs':[ref] if ref else [],'limitations':limitations or []})
def fn(name):
 id='de:'+name
 if name in fnbyname:
  f=fnbyname[name];s=sourcebyid[f['source_id']];node(id,name,ref={'path':s['path'],'sha256':s['sha256'],'file_offset':f['file_offset'],'address':f['va'],'address_domain':'ELF link VA'})
 else:node(id,name,limitations=['Definition not included in this bounded function extraction.'])
 return id
def edge(a,b,relation,site=None,typ='static',limits=None,source='prd-ave'):
 s=sourcebyid[source];edges.append({'id':f'de:e{len(edges)+1:03d}','from':a,'to':b,'relation':relation,'evidence_type':typ,'confidence':'source' if typ=='static' else typ,'evidence_refs':[{'path':s['path'],'sha256':s['sha256'],'locator':f'ELF link VA {site:#x}' if site else 'exact whole-file SHA-256 comparison'}],'limitations':limits or []})
for a,b,site in [('_ZN9QDDimming15t_vSyncCallBackEv','_ZN9QDDimming16m_SetSceneDetectEv',0x17b56e),('_ZN9QDDimming15t_vSyncCallBackEv','_ZN9QDDimming16m_SetScreenSaverEv',0x17b580),('_ZN21DimmingBackendRoseMQDC2Ev','_ZN21DimmingBackendRoseMQD12t_GetNPCDataEv',0x1c85d2),('_ZN21DimmingBackendRoseMQD11t_SetNpcLutEP17BackendQdNpcLut_t','_Z28ave_tcon_api_send_onecommandyPj',0x1c73de),('_ZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_t','_Z28ave_tcon_api_send_onecommandyPj',0x1c62b4),('_ZN21DimmingBackendRoseMQD17t_SetQdSeneDetectEP22BackendQdSceneDetect_t','_Z17ave_frc_write_i2cjj',0x1c63fe),('_Z39ave_tcon_monitor_ddr_pmic_check_qd_oledv','_Z29ave_tcon_qd_set_power_controli',0x26977a),('_Z39ave_tcon_monitor_ddr_pmic_check_qd_oledv','_Z29ave_tcon_qd_set_power_controli',0x269b26),('_Z39ave_tcon_monitor_ddr_pmic_check_qd_oledv','_Z26ave_tcon_get_err_det_faultPi',None),('_Z28ave_tcon_qd_err_detect_checkv','_Z26ave_tcon_get_err_det_faultPi',0x269018),('_Z27ave_tcon_get_err_det_statusPi','_Z10tcon_ioctlmPv',0x25d18e),('_Z26ave_tcon_get_err_det_faultPi','_Z10tcon_ioctlmPv',0x25d046),('_Z29ave_tcon_qd_set_power_controli','_Z10tcon_ioctlmPv',0x25c308),('ave_api_do_update','_Z22ave_tcon_api_do_updateiPKcmi',0x284200),('ave_api_do_update_decryption','_Z29ave_tcon_api_do_update_bufferiPKhii',0x28437a),('ave_api_all_update_done','_Z28ave_tcon_api_all_update_donev',0x2853dc)]:
 if site is not None:edge(fn(a),fn(b),'calls via relocation-resolved PLT',site)
edge(fn('_ZN9QDDimming16m_SetSceneDetectEv'),fn('_ZN21DimmingBackendRoseMQD17t_SetQdSeneDetectEP22BackendQdSceneDetect_t'),'virtual dispatch through slot0x70 when RoseMQD vtable active',0x1797a0,limits=['Static table relocation0x5a159c. Live backend vptr not sampled.'])
edge(fn('_ZN9QDDimming16m_SetSceneDetectEv'),fn('_ZN21DimmingBackendRoseMQD11t_SetNpcLutEP17BackendQdNpcLut_t'),'virtual dispatch through slot0x154 when RoseMQD vtable active',0x179836,limits=['Static table relocation0x5a1680. Live backend vptr not sampled.'])
s=sourcebyid['npc-json'];node('de:npc-resource','LUT_NPC_Point.json','resource',{'path':s['path'],'sha256':s['sha256']})
edge(fn('_ZN21DimmingBackendRoseMQD12t_GetNPCDataEv'),'de:npc-resource','opens exact resource pathname',0x1c8018)
for l in logger:
 node('de:log:'+l['id'],l['id'],'logger',{'path':sourcebyid['prd-ave']['path'],'sha256':sourcebyid['prd-ave']['sha256'],'file_offset':l['site'],'address':l['site'],'address_domain':'ELF link VA'})
 if l.get('tag'):edge('de:log:'+l['id'],fn('__dlog_print'),'emits numeric buffer/priority/tag in evidence.loggers',l['site'])
edge(fn('__dlog_print'),fn('vlog_is_allowed'),'checks producer-side priority/tag acceptance',0x432e25a2,source='pltf-dlog')
edge(fn('__dlog_print'),fn('vlog_write'),'writes allowed produced message to VLOG',0x432e25d8,source='pltf-dlog')
node('de:ap-exco','AP_EXCO data -> image0 mode byte -> image1 C+7','cross-core firmware boundary',limitations=['DF owns proven cross-core edge. No proven Linux scene-field link yet.'])
edge(fn('_ZN21DimmingBackendRoseMQD17t_SetQdSeneDetectEP22BackendQdSceneDetect_t'),'de:ap-exco','possible downstream semantic connection; register/field mapping unresolved',typ='unknown',limits=['Do not equate ScreenProtect label with AP_EXCO SLG mode.'])
node('de:home-only','Home-tab-only blackout explanation','hypothesis',limitations=['A complete explanation must also account for failing fullscreen HDMI content and working movie/control content.'])
node('de:content-route','Source/content-sensitive dimming and scene command route','mechanism')
edge('de:content-route','de:home-only','requires broader explanation than Home selection',typ='inferred',limits=['Mechanism existence does not prove fault cause.'])
save('evidence-graph.json',{'schema':'display-path-graph-v1','nodes':nodes,'edges':edges,'no_live_actions':True,'no_root_cause_proven':True})
print(json.dumps({'sources':len(sources),'functions':len(functions),'vtable_bindings':len(vtable),'provider_functions':len(provider),'nodes':len(nodes),'edges':len(edges)}))
