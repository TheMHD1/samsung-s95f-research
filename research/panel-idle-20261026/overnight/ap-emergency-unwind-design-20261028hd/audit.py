#!/usr/bin/env python3
"""HD bounded source replay and retained HA verification; no device interfaces."""
import base64, copy, hashlib, importlib.util, json, struct, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; B=HERE.parent; checks=0

def need(v, why):
 global checks
 if not v: raise ValueError(why)
 checks+=1

def sha(b): return hashlib.sha256(b).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 pins=json.loads((HERE/'input-pins.json').read_text())['pins']
 for p in pins:
  data=Path(p['path']).read_bytes();need(len(data)==p['bytes'] and sha(data)==p['sha256'],'input pin '+p['path'])
 package=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
 need(len(package)==5242880 and sha(package)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package')
 image=package[0x200:0x40200]
 sys.path[:0]=['/tmp/tcon-capstone',str(B/'predicate-binary-oracle-20261028gd/tools')]
 from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
 from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
 from unicorn.arm_const import UC_CPU_ARM_CORTEX_M4,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_R0,UC_ARM_REG_R1
 md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 def ins(a):
  x=next(md.disasm(image[a:a+4],a));return x.mnemonic,x.op_str
 def word(a):return struct.unpack_from('<I',image,a)[0]
 for a,m,o in [
 (0x1d8,'movs','r3, #0'),(0x1da,'movs','r4, #0'),(0x1dc,'movs','r5, #0'),(0x1de,'movs','r6, #0'),(0x1e4,'stm','r1!, {r3, r4, r5, r6}'),(0x1ec,'stm','r1!, {r4, r5}'),(0x1f0,'str','r3, [r1]'),(0x2c4,'bl','#0x39998'),(0x39a3e,'bl','#0x1e02c'),(0x39b3a,'bl','#0x1e02c'),
 (0x39b60,'bl','#0x1de64'),(0x39b8e,'bl','#0x1e47c'),(0x39b96,'bl','#0x1dd54'),
 (0xb66e,'bl','#0x2fed4'),(0xb678,'bl','#0x96d8'),(0xb6a0,'bl','#0x14910'),(0xb6a6,'bl','#0x2b764'),
 (0xb6f8,'b','#0xb6dc'),(0x14976,'bl','#0x25b24'),(0x149b0,'bl','#0x25b24'),
 (0x25b2e,'bl','#0x3dfc'),(0x25b3c,'bl','#0x3e14'),(0x25b44,'bl','#0x10de0'),
 (0x25b48,'cbz','r5, #0x25b56'),(0x25b4e,'str','r0, [r1, #0x10]'),(0x25b54,'str','r0, [r1, #0x10]'),
 (0x228c0,'strb','r0, [r1]'),(0x228c6,'str','r0, [r1, #0xc]'),
 (0x22900,'strb','r0, [r1]'),(0x22906,'str','r0, [r1, #0xc]'),
 (0x1de70,'bl','#0x1de0c'),(0x1de78,'str','r0, [r1, #0xc]'),
 (0x1dde0,'str','r0, [r1, #0xc]'),(0x1ddca,'bl','#0xb660'),
 (0x1e258,'bl','#0x3e14'),(0x1e272,'bl','#0x3dfc'),
 (0x1e290,'str','r0, [r1, #0x10]'),(0x1e29e,'str','r0, [r1, #0x10]'),(0x1e302,'str','r0, [r1, #0x10]'),
 (0x4462,'cmp','r3, #1'),(0x446e,'str','r2, [r1, #0xc]'),(0x447a,'str','r2, [r1, #0x10]'),
 (0xd81a,'bl','#0x40f4'),(0xd82a,'bl','#0x41d0'),
 (0x96f0,'bl','#0x1b0e8'),(0x9730,'bl','#0x1b0e8'),
 (0x13542,'bl','#0x1b024'),(0x1354e,'bl','#0x1b16e')]:need(ins(a)==(m,o),'instruction '+hex(a))
 for a,v in [(0x360,0x26759),(0x364,0x141),(0x228cc,0x20000cb0),(0x2290c,0x20000cb1),(0x228d0,0x40130000),(0x22910,0x40132000),(0x1de7c,0x40131000),(0x1de00,0x40132000),(0x149c0,0x40134000),(0x1e33c,0x40134000),(0x1b0fc,0xe000e180)]:need(word(a)==v,'literal '+hex(a))
 need([word(a)for a in range(0x4480,0x4498,4)]==[0x40130000+0x1000*i for i in range(6)],'same six output banks')
 # Decode source initialization in memory only; never retain OEM initialized data.
 decoder=load('hd_decoder',B.parent/'tcon-research/qd-rt-window-reset-output-reproduce.py')
 seed,_=decoder.unpack(package,0x40200+0x1d860,0x4f8)
 need(sha(seed)=='76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8','decoder known answer')
 start=word(0x174)+0x174;finish=word(0x178)+0x174
 need(finish-start==12*16,'image0 scatter table extent')
 rows=[struct.unpack_from('<4I',image,start+16*i)for i in range(12)]
 need(rows[11]==(0x3e764,0x20000f4c,0x16438,0x1d8),'image0 BSS row11')
 for a,n in [(0x2000f0e0,20),(0x2000ff14,12),(0x20015924,4)]:need(rows[11][1]<=a and a+n<=rows[11][1]+rows[11][2],'complete witness interval in zero init')
 need(rows[9]==(0x3ea34,0x47010000,0x47bc,0x17c),'shared root initializer row9')
 initial,_=decoder.unpack(package,0x200+rows[9][0],rows[9][2])
 need(sha(initial)=='aee8a64ff7ccfaa95aa4def885fcf7d79c8f4f982d63c5efdb1686eec2cd2b6d','root initializer known answer')
 need([struct.unpack_from('<H',initial,a)[0]for a in [0x2400,0x2408,0x240a,0x240e,0x24c0,0x24c2,0x24c4,0x24c6]]==[0]*8,'startup root initial 0/0/0 and c0/c2/c4/c6 zero, not operational clean40')
 # Fixed-immediate navigation only: actual qualified c4 users are loads.
 image1=package[0x40200:0x60200];c4sites=[]
 for a in range(0,len(image1)-3,2):
  x=next(md.disasm(image1[a:a+4],a,count=1),None)
  if x and x.mnemonic=='movw' and x.op_str=='r0, #0x24c4':
   y=next(md.disasm(image1[a+4:a+8],a+4,count=1));need(y.mnemonic=='ldrh' and y.op_str=='r0, [r0, r5]','positive immediate-c4 consumer is load');c4sites.append(hex(a))
 need(c4sites==['0x1e9e','0x1eca','0x1ee2','0xbdc8','0xbdfa'],'bounded immediate-c4 source candidates')
 spans=json.loads((HERE/'source-spans.json').read_text())['spans']
 for s in spans:need(sha(image[s['start']:s['endExclusive']])==s['sha256'],'bounded span '+s['label'])
 # Run only fixed real bodies with unrelated callees replaced by explicit hooks.
 # MMIO-numbered pages below are synthetic Unicorn memory, not host/device IO.
 def run(entry,arg=0,ap36=0,pin=0,value=0,input1=0,ap170=0):
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
  for a,n in [(0,0x40000),(0x20000000,0x20000),(0x40130000,0x6000)]:u.mem_map(a,n)
  u.mem_write(0,image);u.reg_write(UC_ARM_REG_SP,0x2001f000);u.reg_write(UC_ARM_REG_LR,0x30001)
  u.reg_write(UC_ARM_REG_R0,pin if entry==0x441c else arg);u.reg_write(UC_ARM_REG_R1,value)
  u.mem_write(0x2000f0e0+0x36,struct.pack('<H',ap36));u.mem_write(0x2000f0e0+0x170,struct.pack('<H',ap170))
  u.mem_write(0x2000f0e0+0x8e,struct.pack('<H',17));u.mem_write(0x2000f0e0+0x92,struct.pack('<H',19))
  for base in range(0x40130000,0x40136000,0x1000):
   u.mem_write(base+12,struct.pack('<I',0x40000000));u.mem_write(base+16,struct.pack('<I',0x20000000))
  writes=[];calls=[];done=[]
  allowed={0x25b24:[(0x25b24,0x25b58),(0x3dfc,0x3e0a),(0x3e14,0x3e24),(0xe670,0xe674)],0x441c:[(0x441c,0x4480)],0x228bc:[(0x228bc,0x228ca)],0x228fc:[(0x228fc,0x2290a)],0x1de64:[(0x1de64,0x1de7c),(0xe670,0xe674)],0x1ddac:[(0x1ddac,0x1ddf0),(0xe670,0xe674)]}[entry]
  def code(uc,a,n,d):
   if a==0x30000:done.append('return');uc.emu_stop();return
   if a in [0x10de0,0x1de0c,0xd822,0x3ab74,0x39394,0xb660]:
    calls.append({'address':hex(a),'r0':uc.reg_read(UC_ARM_REG_R0)})
    if a==0xb660:done.append('emergency-entry-stopped');uc.emu_stop();return
    if a==0xd822:uc.mem_write(uc.reg_read(UC_ARM_REG_R1),bytes([input1]))
    uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
   need(any(lo<=a and a+n<=hi for lo,hi in allowed),'fixed synthetic instruction closure')
  u.hook_add(UC_HOOK_CODE,code)
  u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,t,a,n,v,d:writes.append((a,n,v)) if a>=0x40130000 or a in [0x20000cb0,0x20000cb1] else None)
  u.emu_start(entry|1,0x30004,count=2000);need(bool(done),'bounded synthetic completion')
  if done==['return']:need(u.reg_read(UC_ARM_REG_SP)==0x2001f000,'balanced synthetic return')
  return writes,calls,done
 cases=[]
 for arg in [0,1]:
  for ap36 in [0,1,2]:
   w,c,d=run(0x25b24,arg,ap36)
   expected=[(0x20000cb0,1,0),(0x40130010,4,8)]
   if ap36 in [0,1]:expected +=[(0x20000cb1,1,0),(0x40132010,4,0x200)]
   if arg:expected +=[(0x40132010,4,0x80),(0x40131010,4,4)]
   need(w==expected and c==[{'address':'0x10de0','r0':19}],'selector real body store/call order')
   cases.append({'entry':'0x25b24','argument':arg,'AP36':ap36,'writes':w,'stubCalls':c})
 for pin in [3,18,39,68]:
  for value in [0,1]:
   w,c,d=run(0x441c,pin=pin,value=value);address=0x40130000+(pin//16)*0x1000+(12 if value else 16);mask=1<<(pin%16)
   need(w==[(address,4,(0x40000000 if value else 0x20000000)|mask)],'generic code value1 versus value0 mask/register')
   cases.append({'entry':'0x441c','pinIndex':pin,'value':value,'writes':w})
 for entry,expected in [(0x228bc,[(0x20000cb0,1,1),(0x4013000c,4,8)]),(0x228fc,[(0x20000cb1,1,1),(0x4013200c,4,0x200)]),(0x1de64,[(0x4013100c,4,4)])]:
  w,c,d=run(entry);need(w==expected,'complementary source stores');cases.append({'entry':hex(entry),'writes':w,'stubCalls':c})
 for ap170 in [0,1]:
  for value in [0,1]:
   w,c,d=run(0x1ddac,ap170=ap170,input1=value)
   bad=ap170==0 and value==0
   need(d==(['emergency-entry-stopped']if bad else['return']),'monitor condition gate')
   need(w==([]if bad else[(0x4013200c,4,0x80)]),'conditional bank2 bit7 complementary store')
   cases.append({'entry':'0x1ddac','AP170':ap170,'resource1':value,'terminal':d[0],'writes':w})
 # Strict original HA parser replay; all actual raw files independently bound.
 cap=B/'hdmi-endpoint-trial-20261028gp/ha-capture-01';parser=load('hd_ha_parser',B/'ap-fault-witness-reader-20261028ha/parse-result.py')
 native,raws,interpretation=parser.parse_native((cap/'native.receipt.json').read_text())
 need(native['device']==70 and len(raws)==5,'actual device and five intervals')
 for name,raw,digest in raws:need((cap/name).read_bytes()==raw,'actual retained raw '+name)
 need(interpretation==json.loads((cap/'interpretation.json').read_text()),'unchanged strict interpretation')
 need(interpretation['startR']==interpretation['endR']=={'stop':1,'fault':4097,'ordinaryGate':0,'limit':40,'logger':0},'actual fault R brackets')
 need([interpretation[k]for k in ['apMagic','apReasonHalfword10','apExcoDataMagic','apExcoDataHalfword8','apExcoContextWord7c']]==[0,16,0,0,0x3000],'actual AP markers')
 result=json.loads((cap/'result.json').read_text());need(result['accepted']is True and result['cleanup']=='STAGE_ABSENT' and result['nativeInvocations']==1,'actual wrapper terminal')
 need(result['manifestSha256']==sha((cap/'reviewed-manifest.json').read_bytes())==sha((B/'ap-fault-witness-reader-20261028ha/deployment-manifest.json').read_bytes()),'actual reviewed manifest equals frozen source manifest')
 need(result['readinessSha256']==sha((cap/'readiness-decision.json').read_bytes()),'actual result binds readiness')
 decision=json.loads((cap/'readiness-decision.json').read_text());need(decision['accepted']is True and decision['identity']['devnum']=='70','actual readiness')
 negatives=0
 for field,value in [('headersSent',4),('writes',1),('protocolPhase','Unknown'),('released',False)]:
  broken=copy.deepcopy(native);broken[field]=value
  try:parser.parse_native(json.dumps(broken))
  except (ValueError,TypeError,KeyError):negatives+=1
  else:raise ValueError('malformed HA receipt admitted '+field)
 need(negatives==4,'four meaningful retained-receipt refusal cases')
 print(json.dumps({'schema':'hd-emergency-unwind-source-audit-v1','status':'PASS_BOUNDED_SOURCE_AND_RETAINED_ACTUAL','checks':checks,'inputPins':len(pins),'sourceSpans':len(spans),'syntheticCases':cases,'startupDefaults':{'root24c4':0,'APreason10':0,'APdata8':0,'APcontext7c':0},'fixedImmediateC4LoadSites':c4sites,'c4WriterCensusComplete':False,'actualHA':{'device':70,'headers':5,'bulks':10,'INBytes':548,'released':True,'closed':True,'stageAbsent':True,'R':interpretation['startR'],'APmagic':0,'APreason':16,'APdataMagic':0,'APdata8':0,'APcontext7c':12288,'atomicSnapshot':False,'currentPcProven':False,'exactIntervalsCompletedOnce':True},'malformedReceiptCases':negatives,'fullStartupExecutedByMODE2Proven':False,'completeRuntimeUnwindProven':False,'boardSignalIdentitiesProven':False,'targetOperations':0,'networkOperations':0},sort_keys=True,indent=2))
if __name__=='__main__':main()
