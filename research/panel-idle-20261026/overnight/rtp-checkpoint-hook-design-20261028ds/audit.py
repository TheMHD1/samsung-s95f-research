#!/usr/bin/env python3
"""Static hook-site/ABI evidence only. Never builds or emits a patch payload."""
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PACKAGE=BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
checks=0

def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)

def sha(b):return hashlib.sha256(b).hexdigest()

def audit():
 pins=json.loads((HERE/'input-pins.json').read_text())
 for x in pins['files']:
  b=Path(x['path']).read_bytes();need(len(b)==x['bytes'] and sha(b)==x['sha256'],'input pin '+x['path'])
 sys.path.insert(0,'/tmp/tcon-capstone')
 import capstone
 need(capstone.__version__=='5.0.7','exact cached disassembler version')
 image=PACKAGE.read_bytes();need(len(image)==5242880 and sha(image)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package')
 md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB);md.detail=True
 def ins(start,end):
  out=list(md.disasm(image[0x40200+start:0x40200+end],start))
  need(sum(i.size for i in out)==end-start,'whole instruction boundaries '+hex(start))
  return out
 specs=[
  ('aggregate-mode1',0x2024,0x1e68, [('movw','r0, #0xf08')],0,
   {'mode':'r4','root':'r5','scoreLow16':'r7','actualThreshold':'fp/r11','helperT':'sl/r10','rowLike':'r8','channelLike':'sb/r9'},
   'Non-mode6 path only. Resume0x2028 executes original mirror store and compare; mode6 bypasses this site.'),
  ('selected-pointers',0xbd58,0xbd58,[('push.w','{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, lr}')],52,
   {'selectedAPayloadPointer':'r0','selectedBPayloadPointer':'r1','rowLike':'r2','channelLike':'r3','branchProvenance':'entry lr'},
   'Capture original entry state before replaying52-byte push; normal function then subtracts0xf1c stack bytes.'),
  ('qualifying-tuple',0xc5d0,0xc5d0,[('push.w','{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}')],56,
   {'bValue':'r0','lane':'r1','rowLike':'r2','channelLike':'r3','actualAValue':'entry r8, only allowlisted comparator caller','difference':'original entry sp+0','type':'original entry sp+4','provenance':'entry lr'},
   'r8=A is a proven property of four specific caller paths, not a generic AAPCS argument or all callers.'),
  ('fault-setter',0xc1e0,0xc1e0,[('push','{r4, r5, r6, lr}'),('mov','r5, r0')],16,
   {'event':'r0','provenance':'entry lr'},
   'Capture event and original lr before getter BL; replay both push and mov exactly once.'),
  ('all-lane-comparator-alternative',0xbbbc,0xbbbc,[('push.w','{r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}')],48,
   {'actualAValue':'r0','bValue':'r1','lane':'r2','rowLike':'r3','channelLike':'original entry sp+0'},
   'High-rate alternative: executes even for nonqualifying lanes; prefer formatter allowlist to reduce perturbation.')]
 sites=[]
 for label,va,fn,expected,stack,args,limit in specs:
  decoded=ins(va,va+4)
  need([(i.mnemonic,i.op_str)for i in decoded]==expected,'exact displaced instructions '+label)
  need(va%4==0,'aligned candidate '+label)
  prefix=ins(fn,va+4)
  need(not any(i.mnemonic.startswith('it')for i in prefix),'no IT instruction in bounded function prefix '+label)
  sites.append({'id':label,'linkedVa':hex(va),'fileOffset':hex(va+0x40200),'displacedBytes':4,
   'originalSpanSha256':sha(image[va+0x40200:va+0x40204]),
   'instructions':[{'address':hex(i.address),'mnemonic':i.mnemonic,'operands':i.op_str,'bytes':i.size}for i in decoded],
   'displacedStackBytes':stack,'registerMeaningAtOriginalEntry':args,'limitation':limit,
   'itScope':'no IT instruction in source-decoded function prefix only; not a complete live CFG/IT-state proof',
   'runtimeExecutableAddressKnown':False,'patchBytesGenerated':False})
 rejected=ins(0x202a,0x202e)
 need([(i.mnemonic,i.op_str)for i in rejected]==[('cmp','r7, fp'),('ble','#0x203e')],'logical compare site')
 need(0x202a%4==2,'unaligned logical compare')
 # Exact operand origins and allowlisted branches; no inference from unrelated function callers.
 anchors=[(0xbbc0,'mov','r8, r0',2),(0xbbc2,'mov','r7, r1',2),
          (0xbbc4,'mov','r4, r2',2),(0xbbc6,'mov','sb, r3',2),
          (0xb84c,'bl','#0xbd58',4),(0xb874,'bl','#0xbd58',4),(0xb88a,'bl','#0xbd58',4),
          (0xbc74,'bl','#0xc5d0',4),(0xbca8,'bl','#0xc5d0',4),
          (0xbcde,'bl','#0xc5d0',4),(0xbd1e,'bl','#0xc5d0',4),
          (0x203a,'bl','#0xc1e0',4),(0xc792,'bl','#0xc1e0',4),
          (0xc7e0,'bl','#0xc1e0',4),(0xc836,'bl','#0xc1e0',4)]
 proofs=[]
 for va,mn,ops,size in anchors:
  i=ins(va,va+size)[0];need((i.mnemonic,i.op_str)==(mn,ops),'argument/callsite '+hex(va))
  proofs.append({'linkedVa':hex(va),'fileOffset':hex(va+0x40200),'mnemonic':mn,'operands':ops,
                 'originalSpanSha256':sha(image[va+0x40200:va+0x40200+size])})
 # Static comparator body has no assignment to r8 after the original A move.
 # Four formatter calls and root getter are the only BL destinations in this body.
 body=ins(0xbbbc,0xbd2e)
 need([i.op_str for i in body if i.mnemonic=='bl']==['#0x38fc','#0xc5d0','#0xc5d0','#0xc5d0','#0xc5d0'],'bounded comparator callees')
 get=ins(0x38fc,0x3902)
 need([i.mnemonic for i in get]==['ldr','ldr','bx'],'root getter does not clobber r8')
 need(not any(capstone.arm.ARM_REG_R8 in i.regs_access()[1] for i in body if i.address!=0xbbc0 and not i.mnemonic.startswith('pop')),'r8 not written after A move except function-return pop')
 need(not any(i.mnemonic.startswith('it')for i in body),'comparator body has no decoded IT')
 record={'schema':'ds-static-hook-audit-v1','checks':checks,'packageSha256':sha(image),'image':1,
  'fileOffsetFormula':'linked VA+0x40200','wholeLiveImageAttested':False,'ramHookQualified':False,
  'sites':sites,'logicalCompareSiteRejectedForNaive4ByteDetour':{'linkedVa':'0x202a','wordAligned':False,'instructions':['cmp r7, fp','ble 0x203e'],'branchNeedsSemanticRelocation':True},
  'argumentAndCallerAnchors':proofs,
  'selectedPointerNormalizedReturns':{'0xb850':'fixed-top path','0xb878':'fixed-bottom path','0xb88e':'dynamic path'},
  'formatterAAllowlistedNormalizedReturns':['0xbc78','0xbcac','0xbce2','0xbd22'],
  'scope':'local source decoding, not execution, timing, ABI certification or a detour implementation'}
 return record

if __name__=='__main__':
 result=audit();s=json.dumps(result,sort_keys=True,indent=2)+'\n'
 if sys.argv[1:]==['--check']:need((HERE/'source-audit.json').read_text()==s,'exact source audit replay')
 elif not sys.argv[1:]:(HERE/'source-audit.json').write_text(s)
 else:raise SystemExit('usage: audit.py [--check]')
 print(json.dumps({'accepted':True,'checks':checks,'sourceAuditSha256':sha(s.encode()),'ramHookQualified':False}))
