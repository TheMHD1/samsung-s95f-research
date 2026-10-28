#!/usr/bin/env python3
"""Host-only bounded source/retained-data audit and pure rearm-state model. No transport."""
import hashlib,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent
PINS=[];CHECKS=0

def need(v,why):
 global CHECKS
 if not v:raise ValueError(why)
 CHECKS+=1

def sha(b):return hashlib.sha256(b).hexdigest()
def read(rel,expected=None):
 p=B/rel;b=p.read_bytes()
 if expected:need(sha(b)==expected,'pin '+rel)
 PINS.append({'path':rel,'bytes':len(b),'sha256':sha(b)})
 return b

def local_scan(stop,gate):return int(stop==0 and gate==1)
def fault_consumer(fault):return bool(fault&1)
def write_header(address):
 if type(address)is not int or address not in (0x47012400,0x4701240a,0x4701240e):raise ValueError('design address')
 return struct.pack('<III',0x102,address,2)

def planned_controls(state):
 # A pure counterfactual sequence; deliberately no implementation that sends it.
 if type(state)is not tuple or len(state)!=3 or any(type(x)is not int for x in state) or state!=(1,0x1001,0):raise ValueError('exact original fault tuple')
 return [(0x47012400,0),(0x4701240e,1)]

def main():
 sys.path.insert(0,'/tmp/tcon-capstone')
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 package=read('selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin','bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0')
 images=[package[0x200:0x40200],package[0x40200:0x60200]];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 def ins(i,a):
  q=next(md.disasm(images[i][a:a+4],a,count=1));return q.mnemonic,q.op_str
 anchors=[(1,0xc25e,'mov.w','r0, #0x2400'),(1,0xc262,'ldrh','r0, [r0, r4]'),(1,0xc264,'cbnz','r0, #0xc276'),(1,0xc266,'movw','r0, #0x240e'),(1,0xc26c,'cmp','r0, #1'),(1,0xc26e,'bne','#0xc276'),(1,0xc272,'strb','r0, [r1]'),(1,0xc27a,'strb','r0, [r1]'),(1,0xc2e6,'bl','#0xb644'),(1,0xb6a6,'cmp','r4, #0'),(1,0xb6a8,'beq','#0xb732'),(1,0xb6aa,'cmp','r5, #0'),(1,0xb6ac,'beq','#0xb732'),(0,0x214dc,'movw','r0, #0x240a'),(0,0x214e0,'ldrb','r0, [r0, r4]'),(0,0x214e2,'and','r0, r0, #1'),(0,0x214e6,'cbz','r0, #0x214f6'),(0,0x214f0,'movs','r0, #0x10'),(0,0x214f2,'bl','#0xb660'),(0,0xb66e,'bl','#0x2fed4'),(0,0x2fee2,'bl','#0x215bc'),(0,0xb6a0,'bl','#0x14910'),(0,0xb6a6,'bl','#0x2b764'),(0,0x1494a,'cmp','r4, #0x10'),(0,0x1494e,'b','#0x14970'),(0,0x14972,'strh','r0, [r6, #8]'),(0,0x14976,'bl','#0x25b24'),(0,0x1497a,'movs','r0, #0x10'),(0,0x1497e,'str','r0, [r1, #0xc]'),(0,0x14980,'bl','#0x9968'),(0,0x14984,'bl','#0xa030'),(0,0x25b4e,'str','r0, [r1, #0x10]'),(0,0x25b54,'str','r0, [r1, #0x10]'),(0,0x2b76c,'add.w','r5, r0, #0x10'),(0,0x2b772,'bfi','r0, r4, #0, #0x10'),(0,0x2b776,'strh','r0, [r5]'),(0,0xb6c4,'movw','r1, #0x1234'),(0,0xb6ce,'movw','r1, #0xabcd'),(0,0xb6ca,'bne','#0xb6da'),(0,0xb6d4,'bne','#0xb6da'),(0,0xb6d6,'pop.w','{r4, r5, r6, r7, r8, pc}'),(0,0xb6da,'b','#0xb6f8'),(0,0xb6f8,'b','#0xb6dc')]
 for i,a,m,o in anchors:need(ins(i,a)==(m,o),'source instruction '+str(i)+':'+hex(a))
 word=lambda i,a:struct.unpack_from('<I',images[i],a)[0]
 need(word(0,0x149c0)==0x40134000,'reason MMIO base')
 mmio=[{'address':hex(word(0,a)+0x10),'value':v,'literalVa':hex(a)}for a,v in [(0x25b58,0x80),(0x25b5c,4)]]
 getters={'AP':hex(word(0,0xe674)),'AP_EXCO_data':hex(word(0,0xe67c)),'AP_EXCO_context':hex(word(0,0xe770))}
 need(getters=={'AP':'0x2000f0e0','AP_EXCO_data':'0x2000ff14','AP_EXCO_context':'0x200158a8'},'fixed object getter literals')
 spans=[]
 for i,lo,hi,label in [(1,0xc250,0xc27c,'scan predicate'),(1,0xc2de,0xc2ec,'scan dispatch'),(1,0xb644,0xb6b4,'gated ordinary scan prefix'),(0,0x214d4,0x21512,'fault low-bit consumer'),(0,0xb660,0xb6fa,'emergency entry and tail'),(0,0x2fed4,0x2fef8,'ordinary-off/context marking'),(0,0x14910,0x149c4,'reason-specific hardware path'),(0,0x25b24,0x25b60,'additional MMIO'),(0,0x2b764,0x2b77a,'reason halfword'),(0,0x9968,0x99fe,'bounded handshake prefix'),(0,0xa030,0xa050,'diagnostic transfer caller'),(0,0x1163c,0x116e4,'argument-conditioned stop/gate control'),(0,0x21544,0x215b4,'ordinary gate on'),(0,0x215bc,0x21618,'ordinary gate off')]:
  spans.append({'image':i,'va':hex(lo),'endExclusive':hex(hi),'fileOffset':hex(lo+[0x200,0x40200][i]),'bytes':hi-lo,'sha256':sha(images[i][lo:hi]),'label':label})
 read('rtp-fault-clear-paths-20261028gx/README.md','cda38c5f8ac58550712396d73f5e541da988230a0594a2ad208f5f3439d96205')
 read('rtp-fault-clear-paths-20261028gx/source-inventory.json','9c9f3fab5f920c814dab774bc4de4ecf734af770fd64ff7ffaa678b9671a82ad')
 for n in ['Program.cs','README-wrapper.md','deployment-manifest.json','host-build-checkpoint.json']:read('selective-endpoint-limit-writer-20261028fa/'+n)
 read('rtp-lane-gate-capture-20261028eb/parse-result.py')
 read('code-alias-qualification-20261028dw/README.md')
 read('code-alias-qualification-20261028dw/check_source.py')
 read('firmware-rtp-producer-20261028df/cross-core-slg-addendum.md')
 need(images[0][0x39d4c:0x39d9c]==images[1][0x1bb74:0x1bbc4],'identical source mappers')
 need(ins(1,0x1bb96)==('add.w','r0, r1, #0x25000000'),'tag0 SRAM translation')
 observation=[]
 for pointer,length,label in [(0x2000f0e0,20,'AP first magic and reason halfword+10'),(0x2000ff14,12,'AP_EXCO data first magic and halfword+8'),(0x20015924,4,'AP_EXCO context word+7c')]:
  need(0x20000000<=pointer<pointer+length<=0x20020000,'full source SRAM interval')
  alias=pointer+0x25000000
  observation.append({'cpuAddress':hex(pointer),'sourceBusAlias':hex(alias),'bytes':length,'label':label,'readHeader':struct.pack('<III',0x101,alias,length).hex(),'exactUsbIntervalLiveQualified':False})
 gp='hdmi-endpoint-trial-20261028gp/'
 result=json.loads(read(gp+'post-back-validation-capture/result.json','1b5be9f3c19026f3a7d63c47fc6609a07c2905f95e3b9ec2dd3962c071a7f819'))
 read(gp+'post-back-validation-check.json','ac3fb5d5da7eb48f6e8c5010d83779fa05bc3b10cfff08dc1b8e8c50e004deb4')
 read(gp+'parent-progress-checkpoint.json','cf993436dc388dcba3aaa0d434997b6ce58978a6c1aba2e9964ada89bc17a8c0')
 need(result['accepted']is True and result['headersSent']==16 and result['bulkTransfers']==32 and result['cleanup']=='STAGE_ABSENT','retained accepted EB summary, not full original-envelope replay')
 raws={}
 for row in result['rawFiles']:
  b=read(gp+'post-back-validation-capture/'+row['name'],row['sha256']);need(len(b)==row['bytes'],'raw length');raws[row['name']]=b
 need(len(raws)==16,'16 raw windows')
 r=raws['start-R.bin'];m=raws['M.bin'];c=raws['C.bin'];u16=lambda b,a:struct.unpack_from('<H',b,a)[0]
 need(r==raws['end-R.bin'],'R brackets equal')
 triplet=tuple(u16(r,a)for a in (0,10,14));need(triplet==(1,4097,0),'actual original tuple')
 need(u16(r,196)==40 and u16(r,6)==0,'limit40/logger0')
 context={'globalSelector':u16(r,16),'AA':u16(m,10),'AC':u16(m,12),'scan':m[0],'root':hex(struct.unpack_from('<I',m,64)[0]),'xBase':u16(m,32),'packedBytes':u16(m,6),'lanes':u16(m,8),'secondaryOverride':m[44],'C7':c[7],'C8':c[8],'geometry':list(struct.unpack_from('<3H',c)),'publicationMirror':u16(m,42)}
 need(context['AA']==0 and context['AC']==3 and context['globalSelector']==4,'actual context differs from AA0/AC2 writer admission')
 need(raws['start-N.bin']==raws['end-N.bin']==bytes(36),'N0 alone not root reset')
 states=[(1,4097,0),(0,4097,0),(0,4097,1),(0,0,1),(0,0,0)]
 modeled=[{'stop':s,'fault':f,'gate':g,'localScanPredicate':local_scan(s,g),'faultConsumerLowBit':fault_consumer(f),'originalReaderClean':(s,f,g)==(0,0,1)}for s,f,g in states]
 for s in range(3):
  for g in range(3):
   for f in [0,1,2,4096,4097,65535]:
    need(local_scan(s,g)==int(s==0 and g==1),'local boolean exact')
    need(fault_consumer(f)==bool(f%2),'lowbit exact')
 need(planned_controls(triplet)==[(0x47012400,0),(0x4701240e,1)],'stop first, ordinary last, fault untouched')
 for bad in [(0,0,1),(1,4096,0),(1,4097,1),(True,4097,0),[1,4097,0],(1,4097)]:
  try:planned_controls(bad)
  except ValueError:need(True,'invalid state rejected')
  else:need(False,'invalid state accepted')
 headers={}
 for a in (0x47012400,0x4701240a,0x4701240e):
  b=write_header(a);need(len(b)==12 and struct.unpack('<III',b)==(0x102,a,2),'design packet integer layout');headers[hex(a)]=b.hex()
 for a in (0x470124c4,0x47012401,-1,True):
  try:write_header(a)
  except ValueError:need(True,'nonallowlisted address rejected')
  else:need(False,'address accepted')
 print(json.dumps({'schema':'gy-host-source-rearm-design-audit-v1','status':'PASS_DESIGN_ONLY_NOT_DEPLOYABLE','checks':CHECKS,'inputPins':PINS,'sourceSpans':spans,'actualRetainedContext':context,'actualTriplet':list(triplet),'modeledStates':modeled,'sourceGetters':getters,'additionalMmioWrites':mmio,'reasonMmio':{'address':'0x4013400c','value':16},'readOnlyWitnessProposal':observation,'magicPredicateRecheckedInEmergencyLoop':False,'designOnlyWriteHeaders':headers,'faultCodeReportOnly':False,'faultLowBitToReason16SourcePath':True,'liveEmergencyExecutionProven':False,'kernelELReasonIdentityProven':False,'wholeFaultConsumerCensusProven':False,'rootScalarRearmReversesEmergencyEffects':False,'writerImplemented':False,'targetOperations':0,'networkOperations':0},indent=2,sort_keys=True))
if __name__=='__main__':main()
