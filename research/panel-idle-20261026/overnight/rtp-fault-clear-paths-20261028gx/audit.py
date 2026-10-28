#!/usr/bin/env python3
"""Bounded host-only stock fault-state writers and initialization split."""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent;ROOT=B.parent
checks=0;pins=[]
def need(v,why):
 global checks
 if not v:raise ValueError(why)
 checks+=1
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();pins.append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':sha(b)});return b
def main():
 sys.path[:0]=['/tmp/tcon-capstone',str(B/'predicate-binary-oracle-20261028gd/tools')]
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
 from unicorn.arm_const import UC_CPU_ARM_CORTEX_M4,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R9
 package=read(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin')
 need(sha(package)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','package pin')
 images=[package[0x200:0x40200],package[0x40200:0x60200]];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 def word(i,a):return struct.unpack_from('<I',images[i],a)[0]
 def ins(i,a):
  x=next(md.disasm(images[i][a:a+4],a));return x.mnemonic,x.op_str
 need(word(0,0xef98)==0x47010000 and ins(0,0xef94)==('ldr','r0, [pc, #0]'),'image0 fixed remote root getter')
 need(word(1,0x3904)==0x200004e0 and ins(1,0x38fe)==('ldr','r0, [r0]'),'image1 indirect root getter')
 dp=ROOT/'tcon-research/qd-rt-window-reset-output-reproduce.py';decoder=read(dp)
 need(sha(decoder)=='fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02','pure decoder pin')
 spec=importlib.util.spec_from_file_location('gx_pinned_decoder',dp);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 seed,end=mod.unpack(package,0x40200+0x1d860,0x4f8)
 need(sha(seed)=='76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8'and struct.unpack_from('<I',seed,0x4e0)[0]==0x20010000,'image1 known-answer seed/root pointer')
 tables=[]
 for i,count in [(0,12),(1,9)]:
  start=word(i,0x174)+0x174;finish=word(i,0x178)+0x174;need(finish-start==count*16,'exact scatter row count')
  rows=[]
  for n in range(count):
   src,dst,length,handler=struct.unpack_from('<4I',images[i],start+16*n)
   rows.append({'row':n,'sourceVa':hex(src),'destination':hex(dst),'bytes':length,'handler':hex(handler)})
  tables.append(rows)
 row=tables[0][9];need(row=={'row':9,'sourceVa':'0x3ea34','destination':'0x47010000','bytes':0x47bc,'handler':'0x17c'},'image0 positive RTP initializer row')
 initial,end=mod.unpack(package,0x200+0x3ea34,0x47bc)
 need(sha(initial)=='aee8a64ff7ccfaa95aa4def885fcf7d79c8f4f982d63c5efdb1686eec2cd2b6d','full row9 output pin')
 fields={hex(a):struct.unpack_from('<H',initial,a)[0]for a in [0x2400,0x2408,0x240a,0x240e]}
 need(set(fields.values())=={0},'row9 initial stop/control/fault/ordinary all zero, not clean triplet')
 need(tables[1][8]['destination']=='0x200004f8'and tables[1][8]['bytes']==0xdca4 and tables[1][8]['handler']=='0x1d8','image1 local BSS clearing range')
 need(not any(int(x['destination'],16)<=0x20012400<int(x['destination'],16)+x['bytes']for x in tables[1]),'root not in image1 startup scatter destination coverage')
 need(0x200004f8<=0x2000ba28<0x2000ba4c<=0x2000e19c,'N in image1 zero BSS')
 candidate_index=[]
 for domain,image in enumerate(images):
  for at in range(0,len(image)-3,2):
   xs=list(md.disasm(image[at:at+4],at,count=1))
   if xs and xs[0].mnemonic.startswith(('mov','add','sub')) and any('#'+hex(v) in xs[0].op_str for v in [0x2400,0x240a,0x240e]):
    candidate_index.append({'image':domain,'va':hex(at),'mnemonic':xs[0].mnemonic,'operands':xs[0].op_str})
 need(len(candidate_index)==20,'bounded fixed-immediate syntactic candidate index')
 anchors=[(1,0xc1ec,'mov.w','r0, #0x2400'),(1,0xc1f0,'strh','r1, [r0, r4]'),(1,0xc1f4,'movw','r0, #0x240e'),(1,0xc1f8,'strh','r1, [r0, r4]'),(1,0xc200,'strh','r1, [r0, r4]'),(0,0x1f642,'strh.w','r1, [r0, sb]'),(0,0x116d8,'movs','r1, #0'),(0,0x116da,'mov.w','r0, #0x2400'),(0,0x116de,'strh','r1, [r0, r4]'),(0,0x21560,'cbnz','r0, #0x21576'),(0,0x21568,'strh','r1, [r0, r4]'),(0,0x215f2,'cmp','r0, #1'),(0,0x215f4,'bne','#0x21614'),(0,0x215fc,'strh','r1, [r0, r5]')]
 for i,a,m,o in anchors:need(ins(i,a)==(m,o),'exact writer/branch '+str(i)+':'+hex(a))
 spans=[]
 for i,lo,hi,label in [(0,0xef94,0xef9c,'fixed cross-core root'),(1,0x38fc,0x3908,'mutable local root getter'),(1,0xc1e0,0xc214,'fault setter'),(1,0xc220,0xc244,'local initialization wrapper'),(1,0xca84,0xcafc,'counter clear'),(1,0xcb2c,0xcbd4,'width/arrays initialization'),(0,0x1163c,0x116e4,'finite argument-conditioned stop/gate stores; no command interface packaged'),(0,0x21544,0x215b4,'ordinary gate on'),(0,0x215bc,0x21618,'ordinary gate off'),(0,0x1f45c,0x1f574,'backup including stop field'),(0,0x1f5d0,0x1f718,'restore including stop field')]:
  spans.append({'image':i,'va':hex(lo),'endExclusive':hex(hi),'fileOffset':hex(lo+[0x200,0x40200][i]),'sha256':sha(images[i][lo:hi]),'label':label})
 def make(i):
  u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4);u.mem_map(0,0x40000);u.mem_write(0,images[i]);u.mem_map(0x20000000,0x40000);u.mem_map(0x20200000,0x10000);u.mem_map(0x47010000,0x5000)
  u.reg_write(UC_ARM_REG_SP,0x2003f000);u.reg_write(UC_ARM_REG_LR,0x30001);return u
 def put(u,a,n,z=2):u.mem_write(a,n.to_bytes(z,'little'))
 def tuple_at(u,base):return [int.from_bytes(u.mem_read(base+a,2),'little')for a in [0x2400,0x240a,0x240e]]
 local=[]
 for entry in [0xca84,0xcb2c,0xc220]:
  u=make(1);base=0x20010000;put(u,0x200004e0,base,4);u.mem_write(base,bytes([0xa5])*0x4800)
  put(u,base+0x2400,1);put(u,base+0x240a,0x1001);put(u,base+0x240e,0);put(u,base+0x2402,2880);put(u,base+0x2408,0);put(u,0x200004a8,1920)
  u.mem_write(0x2000ba28,bytes([0x55])*36);u.mem_write(0x2000d0e0,bytes([0x55])*96)
  writes=[];returned=[]
  def hook(uc,a,size,data):
   if a==0x30000:returned.append(True);uc.emu_stop();return
   need((entry==0xc220 and 0xc220<=a and a+size<=0xc244)or(0xca84<=a and a+size<=0xcafc)or(0xcb2c<=a and a+size<=0xcbb0)or(0x38fc<=a and a+size<=0x3902),'local initializer real closure')
  u.hook_add(UC_HOOK_CODE,hook);u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,s,v,data:writes.append((a,s)))
  before=bytes(u.mem_read(base+0x2400,256));u.emu_start(entry|1,0x30004,count=100000)
  need(bool(returned)and u.reg_read(UC_ARM_REG_SP)==0x2003f000,'local initializer returns')
  need(tuple_at(u,base)==[1,0x1001,0],'local initializer preserves fault tuple')
  need(bytes(u.mem_read(0x2000ba28,36))==bytes(36),'actual local counter clear N')
  expected=bytearray(before)
  if entry==0xc220:expected[8:10]=b'\x01\0'
  need(bytes(u.mem_read(base+0x2400,256))==bytes(expected),'all root R bytes preserved except c220 control2408')
  if entry!=0xca84:
   need(all(bytes(u.mem_read(base+a,1024))==bytes(1024)for a in [0x1000,0x1400,0x1800]),'three diagnostic arrays cleared')
   need(all(bytes(u.mem_read(base+a,1024))==bytes([0xa5])*1024 for a in [0x1c00,0x2000]),'B/Diff arrays preserved')
  local.append({'image1Entry':hex(entry),'beforeFaultTuple':[1,4097,0],'afterFaultTuple':tuple_at(u,base),'NZero':True,'rootControl2408':int.from_bytes(u.mem_read(base+0x2408,2),'little'),'writeOperations':len(writes),'realSourceOnlySyntheticMemory':True})
 gate=[]
 for on in [True,False]:
  for ordinary in [0,1,2]:
   u=make(0);base=0x47010000;put(u,base+0x2400,1);put(u,base+0x240a,0x1001);put(u,base+0x240e,ordinary)
   u.reg_write(UC_ARM_REG_R4,base);u.reg_write(UC_ARM_REG_R5,base);u.reg_write(UC_ARM_REG_R6,0x20016000);u.reg_write(UC_ARM_REG_R7,0x20017000);u.reg_write(UC_ARM_REG_R9,0x20018000)
   start,stop=(0x2155a,0x21576)if on else(0x215ec,0x21614)
   finished=[]
   def gate_hook(uc,a,size,data):
    if a==stop:finished.append(True);uc.emu_stop()
   u.hook_add(UC_HOOK_CODE,gate_hook);u.emu_start(start|1,0x30004,count=60)
   expected=(1 if ordinary==0 else ordinary)if on else(0 if ordinary==1 else ordinary)
   need(bool(finished)and tuple_at(u,base)==[1,4097,expected],'ordinary gate change alone does not clear fault/stop')
   gate.append({'image0EntrySlice':hex(start),'ordinaryBefore':ordinary,'ordinaryAfter':expected,'stopFaultPreserved':True,'partialBody':True})
 for p in [B/'controller-scratch-rollback-20261028dz/source-audit.json',B/'publication-score-dependency-20261028gn/README.md',B/'operating-mode-label-audit-20261028gr/README.md']:read(p)
 print(json.dumps({'schema':'gx-fault-clear-source-audit-v1','status':'PASS_BOUNDED_SOURCE_ONLY','checks':checks,'inputPins':pins,'sourceSpans':spans,'fixedImmediateCandidateIndex':candidate_index,'scatterRows':tables,'image0RootInitialFields':fields,'localInitializationCases':local,'ordinaryGatePartialCases':gate,'rootFaultClearPositive':'image0 scatter row9 full context initialization; no runtime root240a zero-store recovered by bounded fixed-offset search','resetExecutedThisPathProven':False,'image1InitializationCompatibleWithNZeroAndRetainedFault':True,'wholeWriterCensusProven':False,'targetOperations':0,'networkOperations':0},sort_keys=True,indent=2))
if __name__=='__main__':main()
