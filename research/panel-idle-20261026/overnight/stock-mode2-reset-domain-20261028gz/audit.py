#!/usr/bin/env python3
"""Source-only ELF/registration/branch evidence. Never imports target helpers."""
import base64,hashlib,io,json,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent;ROOT=B.parent
checks=0;pins=[]
def need(v,why):
 global checks
 if not v:raise ValueError(why)
 checks+=1
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 sys.path.insert(0,'/tmp/tcon-capstone')
 from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
 from elftools.elf.elffile import ELFFile
 md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 def elf(rel,expected=None):
  data=(ROOT/rel).read_bytes();need(not expected or sha(data)==expected,'ELF identity '+rel)
  pins.append({'path':rel,'bytes':len(data),'sha256':sha(data)})
  return ELFFile(io.BytesIO(data))
 qdf=elf('binaries/qdf_tcon.ko','97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63')
 api=elf('binaries/tztv_frc_tcon_api.ko','3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6')
 frc=elf('binaries/tztv_frc_tcon.ko','aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd')
 ocl=elf('overnight/serdes-ack-copy-20261026/sdp_ocl_jp.ko','e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c')
 rosem=elf('overnight/firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root/usr/lib/modules/5.4.261/kernel/rosem_frc.ko')
 def relocs(e,section):
  out={}
  s=e.get_section_by_name('.rela'+section)
  if s:
   sy=e.get_section(s['sh_link'])
   for r in s.iter_relocations():
    sym=sy.get_symbol(r['r_info_sym']);name=sym.name
    if not name and type(sym['st_shndx'])is int:name=e.get_section(sym['st_shndx']).name
    out[r['r_offset']]={'name':name,'addend':r['r_addend'],'type':r['r_info_type'],'value':sym['st_value'],'defined':sym['st_shndx']!='SHN_UNDEF'}
  return out
 def init_table(e,size,baseOffset,mapName):
  code=e.get_section_by_name('.init.text').data();rs=relocs(e,'.init.text');regs={};stores={};zero=None;trace=[]
  for x in md.disasm(code,0):
   a=x.address;m=x.mnemonic;o=x.op_str;parts=o.split(', ')
   if m in ['adrp','add']and a in rs:
    rr=rs[a];regs[parts[0]]=('address',rr['name'],rr['addend']);continue
   if m=='mov':
    v=parts[1];regs[parts[0]]=int(v[1:],0)if v.startswith('#')else regs.get(v);continue
   if m=='add':
    d,s,v=parts
    if d=='x29':continue
    need(v.startswith('#')and isinstance(regs.get(s),tuple),'known init address arithmetic')
    old=regs[s];regs[d]=(old[0],old[1],old[2]+int(v[1:],0));continue
   if m in ['stp','str']:
    v=re.search(r'\[(x\d+|sp)(?:, #(-?0x[0-9a-f]+|-?\d+))?\]',o)
    need(v is not None,'init store shape')
    if v[1]=='sp':continue
    addr=regs.get(v[1]);need(isinstance(addr,tuple)and addr[1]=='.bss','init store is known BSS table')
    at=addr[2]+(int(v[2],0)if v[2]else 0)
    vals=parts[:2]if m=='stp'else parts[:1]
    for i,vn in enumerate(vals):
     val=regs.get(vn);need(val is not None,'known init stored pointer')
     need(baseOffset<=at+8*i<baseOffset+size,'store inside exact cleared interface')
     stores[at+8*i-baseOffset]=val;trace.append({'instruction':hex(a),'slot':hex(at+8*i-baseOffset),'value':val})
    continue
   if m=='bl':
    target=rs[a]['name']if a in rs else ''
    if target=='ft_memset':
     need(regs.get('x0')==('address','.bss',baseOffset)and regs.get('w1')==0 and regs.get('x2')==size,'exact full interface memset')
     zero={'instruction':hex(a),'baseBss':hex(baseOffset),'bytes':size};continue
    need(target==mapName and zero is not None,'only memset then interface registration in examined prefix')
    need(regs.get('x0')==('address','.bss',baseOffset),'registered same interface base')
    return {'zero':zero,'registrationCall':hex(a),'slots':stores,'stores':trace}
   need(m in ['stp','ret'],'known straightline table prefix '+hex(a)+':'+m+' '+o)
  raise ValueError('map call missing')
 qt=init_table(qdf,0x758,0x428,'map_tcon_functions');rt=init_table(rosem,0x3f0,0x380,'map_frc_functions')
 need(0x4c8 not in qt['slots'],'QDF PM slot4c8 remains cleared in exact initializer')
 need(0x2b8 not in rt['slots'],'Rosem PM slot2b8 remains cleared in exact initializer')
 need(qt['slots'][0x458][1]=='QDFTcon_SetQdTconPowerControl','operation41 slot458 independent')
 def read(rel,expected=None):
  b=(ROOT/rel).read_bytes();need(not expected or sha(b)==expected,'pin '+rel)
  pins.append({'path':rel,'bytes':len(b),'sha256':sha(b)});return b
 def ins(e,s,a,m,o):
  x=next(md.disasm(e.get_section_by_name(s).data()[a:a+4],a));need((x.mnemonic,x.op_str)==(m,o),'instruction '+s+':'+hex(a))
 for a,m,o in [(0x7ff0,'ldr','x1, [x0, #0x2b8]'),(0x8010,'ldr','x1, [x0, #0x4c8]'),(0x7fe4,'mov','w20, #0'),(0x8020,'orr','w20, w20, w0')]:ins(api,'.text',a,m,o)
 apiSymbols=api.get_section_by_name('.symtab')
 need(any(s.name=='__ksymtab_set_power_mode' for s in apiSymbols.iter_symbols()),'actual exported PM shim provider exists')
 for a,m,o in [(0x11890,'ldr','w0, [x20, #0x1a8]'),(0x11954,'ldr','w1, [x20, #0x1ac]'),(0x118e0,'str','wzr, [sp, #0x4c]'),(0x118e8,'blr','x1'),(0x118ec,'ldr','w1, [sp, #0x4c]'),(0x118f0,'orr','w19, w19, w0'),(0x118f4,'cbnz','w1, #0x11994'),(0x1192c,'bl','#0xb250'),(0x11930,'bl','#0x107e8'),(0x11934,'bl','#0xf6d8'),(0x11938,'str','w23, [x20, #4]'),(0x11a68,'str','wzr, [x20, #4]'),(0x11a6c,'str','wzr, [x20, #0x10]'),(0x11a70,'str','wzr, [x20, #0x40]'),(0x11ce0,'bl','#0x11848'),(0x11cec,'bl','#0x11848'),(0x11cf0,'orr','w0, w19, w0')]:ins(qdf,'.text',a,m,o)
 fr=relocs(frc,'.text.unlikely')
 for a,name in [(0x174c,'_tztv_frc_tcon_set_pvcc'),(0x17c4,'_tztv_frc_tcon_set_pvcc'),(0x1510,'tztv_frc_tcon_set_power'),(0x2c68,'tztv_frc_tcon_set_power'),(0x176c,'_tztv_frc_tcon_nreset_control'),(0x1954,'_tztv_frc_tcon_nreset_control')]:need(fr[a]['name']==name,'actual PM call target '+hex(a))
 for a,m,o in [(0x60e4,'ldr','w2, [x20, #0x284]'),(0x60ec,'b.eq','#0x6304'),(0x6318,'mov','w19, #0')]:ins(frc,'.text',a,m,o)
 ft=relocs(frc,'.text')
 need(ft[0x62cc]['name']==ft[0x629c]['name']=='_tztv_frc_tcon_set_pvcc','on/off distinct pvcc implementation')
 need(ft[0x5c74]['name']=='gpiod_direction_output_raw','direct PVCC GPIO call, not firmware reload')
 ins(frc,'.text',0x5c78,'ldr','w0, [x20, #0x120]')
 ins(frc,'.text',0x1bbc,'str','w1, [x21]')
 need(ft[0x1bb0]['name']=='gpiod_get_raw_value_cansleep','ERR callback independently samples GPIO when called by stock path')
 need(relocs(ocl,'.text')[0x2b5c]['name']=='SDP_OCL_I2C_MBox_Write','mailbox3f sender call')
 for a,m,o in [(0x2b3c,'mov','w1, #0x3f'),(0x2b40,'mov','w2, #1'),(0x2b54,'strb','w0, [sp, #0x2f]'),(0x2b58,'mov','w0, w2')]:ins(ocl,'.text',a,m,o)
 ins(api,'.text',0xed8c,'ldr','x1, [x0, #0x458]')
 sourceSpans=[]
 for e,label,s,lo,hi,meaning in [(api,'API','.text',0x7fc0,0x8058,'PM provider with two optional function-table callbacks'),(qdf,'QDF','.init.text',0,0x5c4,'full zero/init/registration prefix'),(rosem,'RosemFrc','.init.text',0,0x3cc,'full zero/init/registration prefix'),(qdf,'QDF','.text',0x11848,0x11b88,'power body monitor/platform/ERR branches'),(qdf,'QDF','.text',0x11c48,0x11d78,'operation41 mode2 off/on aggregation'),(frc,'FRC-TCON','.text',0x57d8,0x5804,'two separately resolved callbacks'),(frc,'FRC-TCON','.text',0x5a48,0x5b90,'DT nreset GPIO implementation'),(frc,'FRC-TCON','.text',0x5b90,0x5e1c,'DT PVCC/board-specific GPIO sequence'),(frc,'FRC-TCON','.text',0x60d0,0x6328,'ordinary set_power callback stages'),(frc,'FRC-TCON','.text.unlikely',0x14b8,0x1618,'resume worker set_power1 and stage30'),(frc,'FRC-TCON','.text.unlikely',0x1618,0x19b0,'conditional resume prefix through worker start'),(frc,'FRC-TCON','.text.unlikely',0x2b34,0x2d10,'bounded suspend prefix')]:
  data=e.get_section_by_name(s).data()[lo:hi];need(len(data)==hi-lo,'full declared ELF span')
  sourceSpans.append({'asset':label,'section':s,'start':hex(lo),'endExclusive':hex(hi),'bytes':len(data),'sha256':sha(data),'meaning':meaning})
 for e,label,s,lo,hi,meaning in [(api,'API','.text',0xed80,0xeda0,'operation41 optional callback slot458'),(ocl,'OCL JP','.text',0x2b38,0x2b88,'mailbox3f sender; receiver semantics not included')]:
  data=e.get_section_by_name(s).data()[lo:hi];need(len(data)==hi-lo,'full bridge span')
  sourceSpans.append({'asset':label,'section':s,'start':hex(lo),'endExclusive':hex(hi),'bytes':len(data),'sha256':sha(data),'meaning':meaning})
 err=frc.get_section_by_name('.text').data()[0x1af0:0x1c34]
 sourceSpans.append({'asset':'FRC-TCON','section':'.text','start':'0x1af0','endExclusive':'0x1c34','bytes':len(err),'sha256':sha(err),'meaning':'ERR callback sampled output store and distinct callback return'})
 from capstone import Cs as ThumbCs,CS_ARCH_ARM,CS_MODE_THUMB
 tm=ThumbCs(CS_ARCH_ARM,CS_MODE_THUMB)
 package=read('overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin','bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0');image=package[0x200:0x40200]
 def ti(a,m,o):
  x=next(tm.disasm(image[a:a+4],a));need((x.mnemonic,x.op_str)==(m,o),'image0 instruction '+hex(a))
 for a,m,o in [(0xb6da,'b','#0xb6f8'),(0xb6f8,'b','#0xb6dc'),(0xb6ec,'bl','#0x276ec'),(0x276f6,'bl','#0x24df0'),(0x276fc,'bl','#0x38af0'),(0x27710,'bl','#0x27724'),(0x2772e,'bl','#0x2751c'),(0x2752e,'movs','r1, #2'),(0x2753e,'movs','r2, #1'),(0x27540,'movs','r0, #0'),(0x27542,'bl','#0x123d0'),(0x1240c,'bl','#0x8a44'),(0x8aa0,'movs','r0, #0x10'),(0x8aa4,'str','r0, [r1, #0x24]'),(0x8ae0,'str','r0, [r1, #0xc]')]:ti(a,m,o)
 literals={hex(a):hex(struct.unpack_from('<I',image,a)[0])for a in [0x27720,0x27734,0x2754c,0x27550,0x27554,0x38af8]}
 need(literals=={'0x27720':'0x20000c38','0x27734':'0x20000c1c','0x2754c':'0x20000c14','0x27550':'0x398c5','0x27554':'0x20000c28','0x38af8':'0x20000e30'},'timed service literals')
 for lo,hi,meaning in [(0xb6be,0xb6fa,'one-time magic bypass then service backedge'),(0x276ec,0x27738,'timed service and outgoing fixed read wrapper'),(0x2751c,0x27558,'transaction arguments and fixed literals'),(0x123d0,0x12418,'channel-state and asynchronous transaction wrapper'),(0x8a44,0x8af8,'register-backed transaction initiation'),(0x38af0,0x38afc,'service-enable byte getter')]:
  sourceSpans.append({'asset':'selected package image0','section':'Thumb linked VA','start':hex(lo),'endExclusive':hex(hi),'fileOffset':hex(lo+0x200),'bytes':hi-lo,'sha256':sha(image[lo:hi]),'meaning':meaning})
 # Only bounded source strings/callsite metadata, not module or firmware copies.
 logs=[]
 for e,label,values in [(frc,'FRC-TCON',[(0x5350,'nreset GPIO-success-format, not readback attestation'),(0x5490,'PVCC GPIO-success-format, not readback attestation'),(0x5a90,'set_power already mode'),(0x6030,'resume worker begin'),(0x6050,'resume worker init phase end'),(0x6070,'resume elapsed'),(0x6100,'resume worker return'),(0x6268,'already DPMS on')]),(qdf,'QDF',[(0x83e0,'ERR early return'),(0x8438,'normal status/replay tail')]),(ocl,'OCL JP',[(0xb40,'mailbox3f sender result')])]:
  data=e.get_section_by_name('.rodata.str1.8').data()
  for at,meaning in values:
   end=data.index(0,at);raw=data[at:end];need(bool(raw),'nonempty bounded log marker')
   logs.append({'asset':label,'section':'.rodata.str1.8','offset':hex(at),'meaning':meaning,'text':raw.decode('utf-8'),'sha256':sha(raw)})
 toolRelative='overnight/predicate-binary-oracle-20261028gd/'
 toolProof=json.loads(read(toolRelative+'tool-installed-equivalence.json'))
 need(toolProof['wheelSha256']=='9d6e6dea140560de4ebd8446661f7ef84a357d428c14a3ef09dacd306ec8c239'and toolProof['checkedFiles']==len(toolProof['files'])==39,'retained official wheel reference')
 for row in toolProof['files']:
  data=read(toolRelative+'tools/'+row['name'],row['sha256']);need(len(data)==row['bytes'],'retained installed tool file length')
 import body_oracle
 bodyCases=body_oracle.run(qdf,relocs,need);emergencyCases=body_oracle.emergency_tail(image,need)
 for rel in ['overnight/autonomous-fault-harness-20261028dh/deadline-mode2/Program.cs','tcon-research/qd-full-reset-versus-mode2.md','tcon-research/qd-mode2-reported-fault-clear-semantics.md','overnight/rtp-fault-clear-paths-20261028gx/README.md','overnight/rtp-fault-clear-paths-20261028gx/source-inventory.json','overnight/predicate-binary-oracle-20261028gd/tool-acquisition.json']:
  read(rel)
 dh=(ROOT/'overnight/autonomous-fault-harness-20261028dh/deadline-mode2/Program.cs').read_text()
 need('"/dev/tztv_tcon"'in dh and '0xc010749f'in dh.lower(),'actual frozen helper device node and ioctl')
 trace=read('overnight/hdmi-endpoint-trial-20261028gp/kernel-trace-capabilities/response.txt').decode('utf-8')
 need('AVAILABLE_TRACERS\nnop\n' in trace and 'SELECTED_FILTER_FUNCTIONS\nUNAVAILABLE\n' in trace and 'GLOBAL_TRACING_ON\n0\n' in trace,'retained runtime discovery excludes function graph premise')
 read('overnight/hdmi-endpoint-trial-20261028gp/kernel-trace-capabilities/result.json')
 read('overnight/autonomous-fault-harness-20261028dh/kernel-trace.py')
 partial=json.loads(read('overnight/hdmi-endpoint-trial-20261028gp/kernel-probe-capabilities/root.json'))
 need(len(partial['calls'])==1,'one retained capability request')
 call=partial['calls'][0];envelope=call['transport_stdout'];need(envelope['encoding']=='base64','retained response framing')
 response=json.loads(base64.b64decode(envelope['data'],validate=True));need(response['authenticated']is True and response['uid']==response['euid']==0 and len(response['commands'])==1,'authenticated retained partial response')
 cmd=response['commands'][0];paths=['/sys/kernel/debug/tracing/kprobe_events','/sys/kernel/debug/tracing/dynamic_events','/sys/kernel/debug/tracing/events/kprobes','/sys/kernel/debug/tracing/kprobe_profile']
 lines=cmd['stdout'].splitlines();need(lines[0]=='GP_KPROBE_CAP_BEGIN'and lines[2:]==[x for p in paths for x in ['PATH='+p,'ABSENT']]+['SELECTED_SYMBOLS'],'all four completed absence observations before later failure')
 need(call['transport_exit']==1 and cmd['exit_code']==2 and cmd['timed_out']is False,'partial request remains refused, not accepted success')
 need('/proc/kallsyms'in cmd['stderr']and'No such file or directory'in cmd['stderr']and'GP_KPROBE_CAP_END'not in cmd['stdout'],'symbol lookup failure and terminal marker absent preserved')
 print(json.dumps({'schema':'gz-stock-mode2-source-checkpoint-v2','checks':checks,'inputPins':pins,'QdfTable':qt,'RosemTable':rt,'sourceSpans':sourceSpans,'logMarkers':logs,'timedServiceLiterals':literals,'powerBodySyntheticCases':bodyCases,'emergencyTailSyntheticCases':emergencyCases,'ordinaryPmSlotsInitiallyNull':True,'liveBindingAttested':False,'strongerUserResetCommandQualified':False,'mailbox3fReceiverRecovered':False,'image0RestartEstablished':False,'functionGraphAvailableInRetainedDiscovery':False,'kprobeInterfacesAbsentInRetainedDiscovery':paths,'kprobeDiscoveryRequestAccepted':False,'symbolDiscoveryFailed':True,'kprobePrototypeImplemented':False,'targetOperations':0,'networkOperations':0},sort_keys=True,indent=2))
if __name__=='__main__':main()
