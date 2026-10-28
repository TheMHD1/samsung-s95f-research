#!/usr/bin/env python3
"""Independent bounded interpretation of actual Thumb gate branches; host only."""
from pathlib import Path
import hashlib,json,struct,sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_MCLASS,CS_MODE_LITTLE_ENDIAN
from capstone.arm import ARM_OP_IMM,ARM_OP_REG
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent.parent;B=D.parent;checks=0
PINS={'source-inventory.json':'44fe321b0445c5ca41c7ac4a1b34590c75faa8713e49fd45d751d062ff957371','README.md':'3e94166cd84fac336bb4e523b33165a9862bb2b5764a9af81bd24e72f6e145d3','audit.py':'21fad251296aaa250bf0c9243ddbb2fef66ad3dbc605a1de7d439a6e066b34b2','fixed-read-plan.json':'35cf50b7794d859629c7dd526c455af2756585d0b7269f5d071fa5f0f5d76878'}
def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)
for name,pin in PINS.items():need(sha((D/name).read_bytes())==pin,'frozen '+name)
for f in json.loads((D/'source-inventory.json').read_text())['files']:
 b=(D/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'frozen inventory '+f['path'])
for f in json.loads((D/'input-pins.json').read_text())['files']:
 b=Path(f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'source input')
asset=(B/'firmware-rtp-producer-20261028df/private/official-selected-package.bin').read_bytes();cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS|CS_MODE_LITTLE_ENDIAN);cs.detail=True
insns={i.address:i for i in cs.disasm(asset[0x40200+0xbd58:0x40200+0xc02e],0xbd58)}
def one(a):return next(cs.disasm(asset[0x40200+a:0x40200+a+4],a,count=1))
def word(a):return struct.unpack_from('<I',asset,0x40200+a)[0]
def walk(start,stops,regs,memory):
 pc=start;zero=False
 for _ in range(30):
  if pc in stops:return pc,regs
  i=insns[pc];ops=i.operands;nextpc=pc+i.size;m=i.mnemonic.split('.')[0]
  def val(o):
   if o.type==ARM_OP_IMM:return o.imm
   if o.type==ARM_OP_REG:return regs.get(i.reg_name(o.reg),0)
   raise ValueError('unexpected operand')
  if m in ('ldr','ldrb','ldrh'):
   op=ops[1];mem=op.mem;name=i.reg_name(mem.base)
   if name=='pc':v=word(((pc+4)&~3)+mem.disp)
   else:
    address=regs.get(name,0)+((regs.get(i.reg_name(mem.index),0)<<op.shift.value)if mem.index else 0)+mem.disp
    if address not in memory:raise ValueError('unexpected memory source '+hex(address))
    v=memory[address]
   regs[i.reg_name(ops[0].reg)]=v
  elif m in ('mov','movs'):regs[i.reg_name(ops[0].reg)]=val(ops[1])
  elif m=='adds':regs[i.reg_name(ops[0].reg)]=(val(ops[1])+val(ops[2]))&0xffffffff
  elif m=='and':regs[i.reg_name(ops[0].reg)]=val(ops[1])&val(ops[2])
  elif m=='cmp':zero=val(ops[0])==val(ops[1])
  elif m in ('cbz','cbnz'):
   if (val(ops[0])==0)==(m=='cbz'):nextpc=ops[1].imm
  elif m in ('beq','bne'):
   if zero==(m=='beq'):nextpc=ops[0].imm
  elif m=='b':nextpc=ops[0].imm
  else:raise ValueError('unexpected instruction '+i.mnemonic)
  pc=nextpc
 raise ValueError('local bounded CFG did not exit')
# Execute actual gate-branch instructions rather than replacing them with a hand-written truth table.
local=[(0xbeb4,0xbeca,0xbee4),(0xbee4,0xbefe,0xbf20),(0xbf20,0xbf3a,0xbf62),(0xbf62,0xbf7c,0xbf98)]
for laneoffset,(start,allow,skip)in enumerate(local):
 for primary in range(256):
  for secondary in (0,1,255):
   for sb in (0,1):
    lane=568+laneoffset;end,_=walk(start,{allow,skip},{'r4':568,'r5':0x20010000,'sb':sb},{0x20010000+2*lane:primary,0x2000c95c+lane:secondary})
    need((end==allow)==((primary&1)==0 and (secondary==0 or sb!=0)),'actual branch gate truth table')
for aa in (0,1,2,65535):
 for ac in (0,1,2,65535):
  for cc in (0,1,255):
   end,r=walk(0xbe16,{0xbe32},{},{0x200004aa:aa,0x200004ac:ac,0x200004cc:cc})
   need(end==0xbe32 and r['r0']==int((aa==1 or ac==1)and cc!=0),'actual SB branch truth table')
need(one(0xbf14).mnemonic=='b'and one(0xbf14).op_str=='#0xc026','operating-mode rejection trampoline reaches epilogue')
need('sb' in one(0xbbbc).op_str and 'r4' in one(0xbbbc).op_str and 'r5' in one(0xbbbc).op_str and one(0xbc7c).mnemonic=='pop.w'and 'sb' in one(0xbc7c).op_str,'comparator saves/restores gate-live registers')
for call,branch,target,early in [(0xbedc,0xbee0,0xbee4,0xbee2),(0xbf18,0xbf1c,0xbf20,0xbf1e),(0xbf5a,0xbf5e,0xbf62,0xbf60),(0xbf90,0xbf94,0xbf98,0xbf96)]:
 need(insns[call].mnemonic=='bl'and insns[call].op_str=='#0xbbbc'and insns[branch].mnemonic=='cbnz'and insns[branch].operands[1].imm==target and insns[early].op_str=='#0xbfac','earlier comparator0 can end ordinary loop')
plan=json.loads((D/'fixed-read-plan.json').read_text());need(plan['firstLane']==568 and plan['lastLaneInclusive']==635 and plan['newInputBytes']==204,'exact proposed lane interval')
for w,cpu,length in zip(plan['windows'],(0x20010000+2*568,0x2000c95c+568),(136,68)):
 need(int(w['cpuAddress'],16)==cpu and int(w['busAddress'],16)==cpu+0x27000000 and w['bytes']==length and cpu%4==0 and cpu+length<=0x20020000,'complete fixed CPU/bus interval')
 need(struct.pack('<III',0x101,cpu+0x27000000,length).hex()==w['headerLittleEndianHex'],'independent wire bytes')
need(word(0x1bbc0)==0x20020000 and one(0x1bbb4).op_str=='r0, r1, #0x27000000','nonzero-tag source SRAM translator bound/base')
m=(B/'volatile-limit-trial-20261028dk/dv-final-clean-01/M.bin').read_bytes();r=(B/'volatile-limit-trial-20261028dk/dv-final-clean-01/end-R.bin').read_bytes()
need(struct.unpack_from('<I',m,64)[0]==0x20010000 and struct.unpack_from('<H',m,32)[0]==0 and struct.unpack_from('<H',r,16)[0]==4,'prior source root/xbase/operating-mode distinction')
need(struct.unpack_from('<2H',m,10)==(0,2)and struct.unpack_from('<2H',m,6)==(2880,1920),'prior category and packed geometry')
print(json.dumps({'accepted':True,'checks':checks,'actualInstructionBranchCases':6192,'proposedHeaders':2,'proposedInputBytes':204,'targetRootNetworkOperations':0,'actualMasksObserved':False,'liveGateBodyAttested':False,'writeQualified':False}))
