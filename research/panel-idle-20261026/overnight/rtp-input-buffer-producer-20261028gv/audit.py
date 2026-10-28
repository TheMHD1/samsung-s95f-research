#!/usr/bin/env python3
"""Finite isolated source closure for GV. No device, network or build tooling."""
import hashlib,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent
checks=0;pins=[]
def need(ok,why):
 global checks
 if not ok:raise ValueError(why)
 checks+=1
def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel):
 b=(B/rel).read_bytes();pins.append({'path':rel,'bytes':len(b),'sha256':sha(b)});return b
def main():
 sys.path.insert(0,'/tmp/tcon-capstone');sys.path.insert(0,str(B/'predicate-binary-oracle-20261028gd/tools'))
 import capstone,unicorn
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
 from unicorn.arm_const import UC_CPU_ARM_CORTEX_M4,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
 tooling=[]
 for module,version in [(capstone,'5.0.7'),(unicorn,'2.1.4')]:
  need(module.__version__==version,'retained isolated tool version')
  base=Path(module.__file__).parent
  for f in [Path(module.__file__),*sorted(base.rglob('*.so*'))]:
   data=f.read_bytes();tooling.append({'package':module.__name__,'version':version,'file':str(f.relative_to(base)),'bytes':len(data),'sha256':sha(data)})
 raw=read('selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin')
 need(len(raw)==0x500000 and sha(raw)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','package identity')
 image=raw[0x40200:0x60200];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 def dis(lo,hi):return list(md.disasm(image[lo:hi],lo))
 def decoded(lo,hi):return [(x.address,x.mnemonic,x.op_str)for x in dis(lo,hi)]
 spans=[]
 for lo,hi,name in [(0x18ce0,0x18d1c,'full selector and literal'),(0x18ae8,0x18c1c,'full software ring producer and literals'),(0x334,0x368,'full eight-word copy'),(0x3934,0x3a70,'descriptor refresh and source literals'),(0x18c94,0x18ce0,'refresh/producer wrapper'),(0x18d1c,0x18d84,'ring initialization'),(0x18d84,0x18dac,'descriptor change marker'),(0xb7ec,0xb8a8,'input/fixed-reference selection'),(0x1c12c,0x1c1b4,'fixed-reference copy'),(0x195f8,0x19624,'callback registration'),(0x1bb74,0x1bbc4,'bank mapper')]:
  spans.append({'name':name,'vaStart':hex(lo),'vaEndExclusive':hex(hi),'fileStart':hex(lo+0x40200),'sha256':sha(image[lo:hi])})
 helper=dis(0x18ce0,0x18d18)
 need(not any(x.mnemonic in ['bl','blx','bx']for x in helper),'selector has no callees/indirect branches; returns via pop')
 need([x.address for x in helper if x.mnemonic.startswith('str')]==[],'selector has no explicit nonstack stores')
 need(struct.unpack_from('<I',image,0x18d18)[0]==0x20253000,'selector byte/ring base literal')
 need([x.op_str for x in dis(0x18ae8,0x18c14)if x.mnemonic=='bl']==['#0x334','#0x18ce0','#0x18ce0'],'software producer full direct closure')
 need(decoded(0x334,0x33c)==[(0x334,'push.w','{r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}'),(0x338,'ldm.w','r1!, {r4, r5, r6, r7, r8, sb, sl, fp}')],'real eight-word CPU source copy')
 need(struct.unpack_from('<I',image,0x18c14)[0]==0x2000a60c and struct.unpack_from('<I',image,0x18c18)[0]==0x20253000,'descriptor/ring producer literals')
 need(struct.unpack_from('<I',image,0x3a68)[0]==0x2000a60a and struct.unpack_from('<I',image,0x3a6c)[0]==0x58601408,'refresh D/register roots')
 need(struct.unpack_from('<I',image,0x1961c)[0]==0x18c95 and struct.unpack_from('<I',image,0x19620)[0]==0x20000468,'indirect callback registration positive edge')
 # This halfword syntactic BL candidate index is not reachable-code completeness.
 targets={0x18ce0,0x18ae8,0x18c94,0xb7ec,0x3934};calls=[]
 for a in range(0,len(image)-3,2):
  h1,h2=struct.unpack_from('<HH',image,a)
  if h1&0xf800!=0xf000 or h2&0xd000!=0xd000:continue
  s=(h1>>10)&1;j1=(h2>>13)&1;j2=(h2>>11)&1
  v=(s<<24)|((1^(j1^s))<<23)|((1^(j2^s))<<22)|((h1&0x3ff)<<12)|((h2&0x7ff)<<1)
  if s:v-=1<<25
  t=a+4+v
  if t in targets:
   xs=dis(a,a+4)
   if len(xs)==1 and xs[0].mnemonic=='bl'and xs[0].op_str=='#'+hex(t):calls.append({'va':hex(a),'target':hex(t)})
 need([x['va']for x in calls if x['target']=='0x18ce0']==['0xb67a','0xb80e','0xb818','0xc4fa','0x18c02','0x18c0a','0x19822','0x199a4','0x1bfda'],'selector positive syntactic callers')
 def new():
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
  u.mem_map(0,0x40000);u.mem_write(0,image);u.mem_map(0x20000000,0x40000);u.mem_map(0x20250000,0x10000)
  u.reg_write(UC_ARM_REG_SP,0x2003f000);u.reg_write(UC_ARM_REG_LR,0x30001);return u
 def put(u,a,n,size=2):u.mem_write(a,(n&((1<<(size*8))-1)).to_bytes(size,'little'))
 def get(u,a,size=2):return int.from_bytes(u.mem_read(a,size),'little')
 mapper_cases=[]
 for pointer,expected in [(0x20000490,0x47000490),(0x200004a0,0x470004a0),(0x20000bc0,0x47000bc0),(0x2000a60a,0x4700a60a),(0x20012400,0x47012400),(0x2001ffff,0x4701ffff),(0x20020000,0),(0x20253000,0),(0x20253002,0),(0x60000000,0)]:
  u=new();u.reg_write(UC_ARM_REG_R0,1);u.reg_write(UC_ARM_REG_R1,pointer);returned=[]
  def mapper_hook(uc,a,size,data):
   if a==0x30000:returned.append(True);uc.emu_stop();return
   need(0x1bb74<=a and a+size<=0x1bbbe,'mapper exact source closure')
  u.hook_add(UC_HOOK_CODE,mapper_hook);u.emu_start(0x1bb75,0x30004,count=30)
  need(bool(returned)and u.reg_read(UC_ARM_REG_R0)==expected,'real tag1 mapper qualification/rejection')
  mapper_cases.append({'cpuPointer':hex(pointer),'returnedBusAddress':hex(expected)})
 selector_cases=0
 for index in range(256):
  for tag in [0,1,2,0xffffffff]:
   u=new();put(u,0x20253000,index,1);u.reg_write(UC_ARM_REG_R0,tag);writes=[];pc=[]
   def selector_hook(uc,a,size,data):
    if a==0x30000:uc.emu_stop();return
    need(0x18ce0<=a and a+size<=0x18d18,'selector exact source closure');pc.append(a)
   u.hook_add(UC_HOOK_CODE,selector_hook);u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,s,v,data:writes.append((a,s)))
   u.emu_start(0x18ce1,0x30004,count=40)
   expected=0x20253002+((index+(1 if tag==0 else 0))%3)*0xb68
   need(u.reg_read(UC_ARM_REG_R0)==expected and u.reg_read(UC_ARM_REG_SP)==0x2003f000,'real selector formula and return')
   need(sorted(writes)==[(0x2003eff8,4),(0x2003effc,4)],'selector writes only fixed prologue stack')
   selector_cases+=1
 producer_cases=[]
 for initial in [0,1,2]:
  u=new();put(u,0x20253000,initial,1)
  descriptors=[(1,0,77,0),(0,1,88,2159)]
  payloads=[];addresses=[]
  for i,(flag,channel,value,row)in enumerate(descriptors):
   p=0x2000a60c+10*i;put(u,p,flag,1);put(u,p+2,channel,1);put(u,p+4,value);put(u,p+6,row)
   address=(0x60000000+channel*0x1950000+row*0xc00)&0xffffffff;addresses.append(address)
   page=address&~0xfff;size=((address+0xb60-page+0xfff)//0x1000)*0x1000;u.mem_map(page,size)
   payload=bytes((x+37*i+11*initial)&255 for x in range(0xb60));payloads.append(payload);u.mem_write(address,payload)
  reads=[];writes=[];returned=[];selected=[]
  def prod_hook(uc,a,size,data):
   if a==0x30000:returned.append(True);uc.emu_stop();return
   if a==0x18c10:selected.append((uc.reg_read(UC_ARM_REG_R7),uc.reg_read(UC_ARM_REG_R6)))
   need((0x18ae8<=a and a+size<=0x18c14)or(0x334<=a and a+size<=0x368)or(0x18ce0<=a and a+size<=0x18d18),'producer full real closure')
  def prod_read(uc,access,a,s,v,data):
   if any(lo<=a<lo+0xb60 for lo in addresses):reads.append((a,s))
  u.hook_add(UC_HOOK_CODE,prod_hook);u.hook_add(UC_HOOK_MEM_READ,prod_read);u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,s,v,data:writes.append((a,s,v)))
  u.emu_start(0x18ae9,0x30004,count=10000)
  need(bool(returned)and u.reg_read(UC_ARM_REG_SP)==0x2003f000,'producer bounded return')
  need(get(u,0x20253000,1)==(initial+2)%3,'two modulo-three selector advances')
  for i,(flag,ch,val,row)in enumerate(descriptors):
   slot=(initial+i)%3;base=0x20253002+slot*0xb68
   need(bytes(u.mem_read(base+8,0xb60))==payloads[i],'two exact real-copy payloads')
   need(get(u,base,1)==i and get(u,base+1,1)==int(flag!=0)and get(u,base+2,1)==ch and get(u,base+4)==val and get(u,base+6)==row,'exact produced header fields')
  need(len(reads)==2*0xb60//4 and all(size==4 for a,size in reads),'exact payload source-read footprint')
  need(selected==[(0x20253002+((initial+2)%3)*0xb68,0x20253002+initial*0xb68)],'pre-epilogue selected A/B age ordering; callee-saved registers restored on return')
  nonstack=[(a,s)for a,s,v in writes if not 0x2003e000<=a<0x2003f000]
  allowed={0x20253000}
  need(all(a in allowed or any(0x20253002+((initial+i)%3)*0xb68<=a<0x20253002+((initial+i)%3)*0xb68+0xb68 for i in [0,1])for a,s in nonstack),'producer writes limited to two slots and selector in this case')
  producer_cases.append({'initialSelector':initial,'finalSelector':(initial+2)%3,'writtenSlots':[initial,(initial+1)%3],'dynamicASlot':(initial+2)%3,'dynamicBSlot':initial,'sourceAddresses':[hex(a)for a in addresses],'payloadBytesPerSlot':0xb60,'sourceU32Reads':len(reads),'physicalSourceMemoryWasSynthetic':True})
 address_cases=[]
 for channel in [0,1,2,255]:
  for row in [-32768,-1,0,2159,32767]:
   u=new();put(u,0x20253000,0,1);put(u,0x2000a60e,channel,1);put(u,0x2000a612,row)
   reached=[]
   def address_hook(uc,a,size,data):
    if a==0x334:reached.append((uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R2)));uc.emu_stop()
   u.hook_add(UC_HOOK_CODE,address_hook);u.emu_start(0x18ae9,0x30004,count=60)
   expected=(0x60000000+channel*0x1950000+row*0xc00)&0xffffffff
   need(reached==[(expected,0x2025300a,0x5b)],'signed row/u8 channel address reaches copy without source bounds check')
   address_cases.append({'channel':channel,'signedRow':row,'computedSource':hex(expected),'stoppedBeforeCopy':True})
 refresh_cases=[]
 for c8,provider1,saved,channel,value in [(0,9,1500,2,1500),(3,10,1500,2,1500),(3,9,1439,2,1439),(3,9,1500,1,1500),(3,9,1500,2,1501),(3,9,1500,2,1500)]:
  u=new();u.mem_map(0x58601000,0x1000)
  put(u,0x200004e0,0x20010000,4);put(u,0x200002cc,0x20018000,4);put(u,0x20018000,c8,1);put(u,0x20018001,provider1,1)
  d=0x2000a60a;oldtail=bytes.fromhex('0100110022003300');u.mem_write(d+0x16,oldtail);put(u,d+0x1e,saved)
  for at,n in [(0x58601408,1),(0x5860140c,channel),(0x58601410,value),(0x58601414,2159),(0x5860146c,444)]:put(u,at,n,4)
  returned=[];stubs=[]
  def refresh_hook(uc,a,size,data):
   if a==0x30000:returned.append(True);uc.emu_stop();return
   if a==0xbb58:stubs.append(a);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR));return
   need((0x3934<=a and a+size<=0x3a68)or(0x38e8<=a and a+size<=0x38ee)or(0x38f4<=a and a+size<=0x38fa)or(0x38fc<=a and a+size<=0x3902),'refresh bounded source/getter closure')
  u.hook_add(UC_HOOK_CODE,refresh_hook);u.emu_start(0x3935,0x30004,count=300)
  cleared=c8==3 and provider1!=10 and saved>=1440 and channel==2 and saved==value
  need(bool(returned)and stubs==[0xbb58],'refresh returns with explicit profile-copy stub')
  need(bytes(u.mem_read(d+4,8))==oldtail,'previous descriptor receives OLD scratch tail')
  tail=struct.pack('<4H',0 if cleared else channel,0 if cleared else value,0 if cleared else 2159,444)
  need(bytes(u.mem_read(d+0x16,8))==tail and bytes(u.mem_read(d+0xe,8))==tail,'filtered scratch copied to second descriptor tail')
  need(get(u,d+0x2b,1)==int(cleared),'source conditional marks pending flag')
  refresh_cases.append({'contextC8':c8,'providerPlus1':provider1,'savedD1e':saved,'hardwareChannel':channel,'hardwareValue':value,'hardwareRow':2159,'currentTailZeroedExceptAux':cleared,'nextDescriptorRow':0 if cleared else 2159,'mmioWasSynthetic':True,'stub':'bb58 profile parameter copy only'})
 plan=json.loads(read(HERE.name+'/fixed-read-proposal.json'))
 need([(x['busAddress'],x['bytes'])for x in plan['orderedWindows']]==[('0x47012400',256),('0x470004a0',68),('0x47000bc0',16),('0x4700a60a',48),('0x47000490',16),('0x4700a60a',48),('0x47012400',256)],'fixed low-SRAM metadata proposal only')
 need(sum(x['bytes']for x in plan['orderedWindows'])==plan['rawBytes']==708 and plan['headers']==7 and plan['bulks']==14 and plan['worstBulkBudgetSeconds']==28 and plan['implemented']is False,'read proposal arithmetic/scope')
 for rel in ['firmware-rtp-producer-20261028df/README.md','selector-origin-20261028ej/README.md','publication-score-dependency-20261028gn/README.md','rtp-fixed-reference-qualification-20261028dr/README.md','rtp-record-capture-20261028dm/Program.cs','code-alias-qualification-20261028dw/README.md']:read(rel)
 print(json.dumps({'schema':'gv-input-buffer-source-audit-v1','status':'PASS_FINITE_HOST_ONLY_SOURCE_CLOSURE','checks':checks,'tooling':tooling,'inputPins':pins,'sourceSpans':spans,'positiveSyntacticCallers':calls,'mapperRealCases':mapper_cases,'selectorRealCases':selector_cases,'producerRealCases':producer_cases,'producerAddressCases':address_cases,'refreshPartialCases':refresh_cases,'selectorFormula':'base20253002 + ((u8(index)+(tag==0 ? 1 : 0)) % 3)*0xb68','selectorNonzeroTagsEquivalent':True,'producerIndexPrecondition':'initial byte0..2 in these producer tests; source does not modulo-normalize before first destination store','ringBusAliasQualified':False,'physicalApertureProducerProven':False,'allAliasesClosed':False,'historicalInputEpochProven':False,'targetOperations':0,'networkOperations':0},sort_keys=True,indent=2))
if __name__=='__main__':main()
