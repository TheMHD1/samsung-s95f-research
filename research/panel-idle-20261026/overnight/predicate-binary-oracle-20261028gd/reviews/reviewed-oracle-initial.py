#!/usr/bin/env python3
"""Host-only selected Thumb predicate oracle. No target transport or patch bytes."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
B=HERE.parent
sys.path.insert(0,str(HERE/'tools'))
import unicorn
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE
from unicorn.arm_const import *
PACKAGE=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
PACKAGE_SHA='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
ROOT=0x20010000;CTX=0x20000500;SRAM=0x20000000;RETURN=0x30000
H=0x2000d0e4;Q=0x2000d0fc;HISTORY=0x2000d108;COUNTS=0x2000ba40
REGS=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
SKIP={8,9,10,12,24,25}

def require(v,m):
 if not v:raise ValueError(m)

def selected_image():
 raw=PACKAGE.read_bytes()
 require(len(raw)==0x500000 and hashlib.sha256(raw).hexdigest()==PACKAGE_SHA,'selected package pin')
 return raw[0x40200:0x60200]

def emulate(*,mode=1,selector=1,limit=40,fallback=600,mode2_limit=700,mode4_limit=800,mode6_limit=900,gate=1,aggregate=0,q=0,history=(0,0,0,0),source_count=0,event_bound=160,t=0,alternate_t=False,image=None):
 require(mode in range(1,7),'bounded mode 1..6')
 for x in [limit,fallback,mode2_limit,mode4_limit,mode6_limit,gate,q,source_count,event_bound,*history]:require(type(x)is int and 0<=x<=65535,'u16 input')
 require(type(selector)is int and 0<=selector<=255,'u8 selector')
 for x in [aggregate,t]:require(type(x)is int and 0<=x<=0xffffffff,'u32 input')
 require(len(history)==4,'four history samples')
 image=selected_image() if image is None else image
 uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
 uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M4)
 uc.mem_map(0,0x40000);uc.mem_write(0,image)
 uc.mem_map(SRAM,0x20000)
 def w16(a,v):uc.mem_write(a,struct.pack('<H',v))
 def w32(a,v):uc.mem_write(a,struct.pack('<I',v))
 def r16(a):return struct.unpack('<H',uc.mem_read(a,2))[0]
 def r32(a):return struct.unpack('<I',uc.mem_read(a,4))[0]
 w32(SRAM+0x4e0,ROOT)
 uc.mem_write(CTX+0x6c7,bytes([selector]))
 for off,v in [(0x24c4,limit),(0x2430,fallback),(0x2432,mode2_limit),(0x2440,mode4_limit),(0x24c0,mode6_limit),(0x249e,gate),(0x24a0,event_bound),(0x24d2,int(alternate_t)),(0x240e,1)]:w16(ROOT+off,v)
 n=mode-1;w32(H+n*4,aggregate);w16(Q+n*2,q);w16(COUNTS+n*2,source_count)
 uc.mem_write(HISTORY+n*8,struct.pack('<4H',*history))
 initial=[0x11220000+i for i in range(8)]
 for reg,value in zip(REGS,initial):uc.reg_write(reg,value)
 uc.reg_write(UC_ARM_REG_SP,0x2001f000);uc.reg_write(UC_ARM_REG_LR,RETURN|1)
 uc.reg_write(UC_ARM_REG_R0,mode);uc.reg_write(UC_ARM_REG_R1,2159);uc.reg_write(UC_ARM_REG_R2,0)
 observed={'calls':[],'comparison':None,'returned':False,'instructionCount':0}
 allowed=[(0x1e46,0x2042),(0x38f4,0x38f8),(0x38fc,0x3902),(0xc1e0,0xc214)]
 def stub_return(value=0):
  uc.reg_write(UC_ARM_REG_R0,value);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 def hook(u,a,size,data):
  observed['instructionCount']+=1
  if a==RETURN:
   observed['returned']=True;u.emu_stop();return
  if a in [0x35a4,0xc8a0,0xca10,0x1c0c8,0x1b8c8]:
   observed['calls'].append({'pc':a,'lr':u.reg_read(UC_ARM_REG_LR),'r0':u.reg_read(UC_ARM_REG_R0),'r1':u.reg_read(UC_ARM_REG_R1)})
   stub_return(t if a in [0xc8a0,0xca10] else 0);return
  require(any(lo<=a<hi and a+size<=hi for lo,hi in allowed),'execution outside fixed audited ranges '+hex(a))
  if a==0x202a:observed['comparison']={'score':u.reg_read(UC_ARM_REG_R7),'threshold':u.reg_read(UC_ARM_REG_R11),'mode':u.reg_read(UC_ARM_REG_R4),'t':u.reg_read(UC_ARM_REG_R10)}
  if a==0xc1e0:observed['setter']={'event':u.reg_read(UC_ARM_REG_R0),'lr':u.reg_read(UC_ARM_REG_LR)}
 uc.hook_add(UC_HOOK_CODE,hook)
 uc.emu_start(0x1e69,RETURN+4,timeout=1000000,count=1000)
 require(observed['returned'],'bounded oracle did not return')
 require(uc.reg_read(UC_ARM_REG_SP)==0x2001f000,'original SP restored')
 require([uc.reg_read(r) for r in REGS]==initial,'callee-saved registers restored')
 observed.update({'aggregate':r32(H+n*4),'q':r16(Q+n*2),'history':list(struct.unpack('<4H',uc.mem_read(HISTORY+n*8,8))),'mirror':r16(ROOT+(0xf06 if mode==6 else 0xf08)),'faultTuple':[r16(ROOT+x)for x in [0x2400,0x240a,0x240e]],'actualTargetInvocationProven':False})
 return observed

def model(**kw):
 mode=kw.get('mode',1);selector=kw.get('selector',1);a=kw.get('aggregate',0);q=kw.get('q',0);h=list(kw.get('history',(0,0,0,0)));s=kw.get('source_count',0);t=kw.get('t',0)
 if kw.get('gate',1)!=1:return {'aggregate':a,'q':q,'history':h,'comparison':None,'mirror':0,'faultTuple':[0,0,1]}
 fp=kw.get('mode2_limit',700)if mode==2 else kw.get('mode4_limit',800)if mode==4 else kw.get('limit',40)if selector else kw.get('mode6_limit',900)if mode==6 else kw.get('fallback',600)
 q=((q<<1)&31)+int(s>kw.get('event_bound',160));h=[h[1],h[2],h[3],s]
 skipped=q in SKIP
 if not skipped:
  a=(a+h[0])&0xffffffff
  if a>=t:a-=t
 score=a&65535
 return {'aggregate':a,'q':q,'history':h,'comparison':{'score':score,'threshold':fp,'mode':mode,'t':0 if skipped else t},'mirror':score,'faultTuple':[1,4097,0]if score>fp else[0,0,1]}

def run():
 image=selected_image();cases=[]
 for mode in range(1,7):
  for selector in [0,1,2,255]:
   for score in [0,39,40,41,599,600,601,699,700,701,799,800,801,899,900,901,65535,65536,65577,0xffffffff]:cases.append({'mode':mode,'selector':selector,'aggregate':score})
 for q in range(32):
  for source_count in [0,160,161,65535]:
   for t in [0,1,25,0xffffffff]:cases.append({'q':q,'aggregate':20,'history':[1,4,3,2],'source_count':source_count,'t':t,'alternate_t':bool(q&1)})
 for gate in [0,2,65535]:cases.append({'gate':gate,'aggregate':65577,'q':65535,'history':[1,2,3,4],'source_count':65535})
 for a,h,t in [(0xffffffff,[0,1,0,0],0),(0xfffffffe,[0,4,0,0],1),(20,[0,4,0,0],24),(20,[0,4,0,0],25),(65530,[0,10,0,0],0)]:cases.append({'aggregate':a,'history':h,'t':t})
 checks=0;setters=0;maxins=0
 for n,case in enumerate(cases):
  actual=emulate(image=image,**case);expected=model(**case)
  for k,v in expected.items():require(actual[k]==v,'case '+str(n)+' field '+k);checks+=1
  fault=actual['faultTuple']==[1,4097,0]
  logs=[r for r in actual['calls']if r['pc']==0x1b8c8 and r['lr']in [0xc20b,0xc213]]
  if fault:
   require(actual.get('setter')=={'event':736,'lr':0x203f},'setter event/caller');require(len(logs)==2 and all(r['r1']==736 for r in logs),'one setter has two formatter calls');setters+=1
  else:require('setter'not in actual and not logs,'no setter on no-fault branch')
  checks+=1;maxins=max(maxins,actual['instructionCount'])
 return {'schema':'gd-predicate-binary-oracle-v1','unicornVersion':unicorn.__version__,'selectedPackageSha256':PACKAGE_SHA,'cases':len(cases),'checks':checks,'setterCases':setters,'maximumInstructions':maxins,'fixedStubs':{'0x35a4':'ordinary gate busywait reports available0','0xc8a0':'caller-supplied model T','0xca10':'caller-supplied model T','0x1c0c8':'records mode/action4; no hardware action','0x1b8c8':'records formatter call; no ring side effects'},'realInstructionRanges':[[hex(a),hex(z)]for a,z in [(0x1e46,0x2042),(0x38f4,0x38f8),(0x38fc,0x3902),(0xc1e0,0xc214)]],'targetOperations':0,'instructionHookInstalled':False,'actualTargetInvocationProven':False,'actualComparisonOperandsProven':False,'physicalOrRootCauseFixProven':False}

if __name__=='__main__':print(json.dumps(run(),sort_keys=True,indent=2))
