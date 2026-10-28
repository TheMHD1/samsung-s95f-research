#!/usr/bin/env python3
"""Bounded selected-source writer audit. Pure host reads, no target adapters."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_MCLASS
D=Path(__file__).resolve().parent;B=D.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1
asset=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';raw=asset.read_bytes()
need(len(raw)==5242880 and sha(raw)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package')
cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS)
def data(image,va,n):return raw[(0x200 if image==0 else 0x40200)+va: (0x200 if image==0 else 0x40200)+va+n]
def word(image,va):return struct.unpack('<I',data(image,va,4))[0]
anchors=[]
def ins(image,va,mn,ops):
 z=list(cs.disasm(data(image,va,4),va,count=1));need(len(z)==1 and z[0].mnemonic==mn and z[0].op_str==ops,'instruction '+str(image)+':'+hex(va));i=z[0]
 anchors.append({'image':image,'va':hex(va),'fileOffset':hex(va+(0x200 if image==0 else 0x40200)),'bytes':i.size,'sha256':sha(data(image,va,i.size)),'mnemonic':mn,'operands':ops})
for a in [
(1,0xb9fc,'ldr','r0, [pc, #0xf4]'),(1,0xba02,'bne','#0xba5a'),(1,0xba04,'movw','r0, #0x2468'),(1,0xba0c,'bne','#0xba20'),(1,0xba12,'cbnz','r0, #0xba20'),(1,0xba1a,'movs','r0, #1'),(1,0xba1e,'strh','r0, [r1]'),(1,0xba64,'cmp','r0, #3'),(1,0xba68,'movs','r0, #1'),(1,0xba6c,'strh','r0, [r1]'),
(1,0xb74a,'cbnz','r4, #0xb794'),(1,0xb76e,'cmp','r0, #1'),(1,0xb772,'movs','r0, #3'),(1,0xb776,'strh','r0, [r1]'),(1,0xb8ec,'cmp','r0, #1'),(1,0xb8f6,'movw','r0, #0x246e'),(1,0xb8fe,'bne','#0xb920'),(1,0xb912,'strh.w','r1, [r4, r0, lsl #1]'),(1,0xb920,'movs','r0, #2'),(1,0xb924,'strh','r0, [r1]'),(1,0xc228,'bl','#0xcb2c'),(1,0xc234,'movs','r0, #0'),(1,0xc238,'strh','r0, [r1]'),(1,0x1ba7e,'bl','#0xc220'),
(1,0xc2e6,'bl','#0xb644'),(1,0xb6ce,'bl','#0xb9f4'),(1,0xb72e,'bl','#0xb8a8'),(1,0xb658,'movw','r0, #0x2460'),(1,0xb660,'beq','#0xb74a'),(1,0xc2c0,'movw','r0, #0x2460'),(1,0xc2c8,'beq','#0xc2d0'),(1,0xc2da,'bl','#0xc470'),(1,0xc4ae,'bne','#0xc56a'),(1,0xc4b6,'beq','#0xc56a'),
(0,0xa6c0,'bl','#0xef94'),(0,0xa6da,'cmp','r6, #0x30'),(0,0xa71a,'movw','r0, #0x2460'),(0,0xa71e,'strh','r4, [r0, r7]'),(0,0xa724,'bne','#0xa728'),(0,0xa726,'strh','r0, [r5, #8]'),(0,0x11a56,'bl','#0xa6ac'),
(0,0x21554,'bl','#0xef94'),(0,0x21560,'cbnz','r0, #0x21576'),(0,0x21562,'movs','r1, #1'),(0,0x21568,'strh','r1, [r0, r4]'),(0,0x215c6,'bl','#0xef94'),(0,0x215da,'bic','r0, r0, #0x10000000'),(0,0x215e2,'bic','r0, r0, #0x2000'),(0,0x215e6,'add.w','r0, r0, #0x2000'),(0,0x215f4,'bne','#0x21614'),(0,0x215f6,'movs','r1, #0'),(0,0x215fc,'strh','r1, [r0, r5]'),(0,0x21604,'strh.w','r0, [r6, #0x204]'),
(0,0x37bee,'cmp','r4, #0xa'),(0,0x37bf2,'cmp','r4, #8'),(0,0x37bf6,'bl','#0x21544'),(0,0x37bfc,'bl','#0x215bc'),(0,0xbc02,'bl','#0x215bc'),(0,0xbc3e,'bl','#0x215bc'),(0,0xc7d2,'bl','#0x215bc'),(0,0x2fee2,'bl','#0x215bc'),(0,0x32828,'bl','#0x215bc'),(0,0x357ec,'bl','#0x215bc'),
(1,0xc1f8,'strh','r1, [r0, r4]'),(0,0x116b6,'strh','r1, [r0, r4]'),(1,0x35b2,'cbnz','r0, #0x35b8'),(1,0xc26e,'bne','#0xc276')]:ins(*a)
lits=[(0,0xef98,0x47010000),(0,0xe67c,0x2000ff14),(0,0xe770,0x200158a8),(1,0x3904,0x200004e0),(1,0xbaf4,0x200004a0),(1,0xbaf8,0x200004a2),(1,0xb98c,0x200004a2),(1,0xb7e8,0x200004a2),(1,0xc244,0x200004a2),(1,0xc2ec,0x200004d8),(1,0xc2f8,0x200004d7)]
for image,va,v in lits:need(word(image,va)==v,'literal '+str(image)+':'+hex(va))
# Direct syntactic PC-literal candidates for4a2: these coherent sites are manually classified.
refs=[]
for va in range(0,0x1d6a4,2):
 z=list(cs.disasm(data(1,va,4),va,count=1))
 if not z:continue
 i=z[0];m=re.fullmatch(r'(r\d+), \[pc(?:, #(0x[0-9a-f]+|[0-9]+))?\]',i.op_str)
 if i.mnemonic in('ldr','ldr.w')and m:
  at=((va+4)&~3)+int(m[2]or'0',0)
  if word(1,at)==0x200004a2:refs.append(hex(va))
need(refs==['0xb76a','0xb774','0xb8e8','0xb922','0xba0e','0xba1c','0xba60','0xba6a','0xbfe0','0xc236'],'bounded4a2 direct-reference candidates')
# Resource descriptor names/data provide an AP_RTP/AP_EXCO data relationship, not an API invocation.
need(word(0,0x3cc44)==0x3de8c and data(0,0x3de8c,7)==b'AP_RTP\0','AP_RTP resource name')
need([word(0,x)for x in range(0x3cc48,0x3cc58,4)]==[0x47012400,0x100,0x47010000,0x2400],'AP_RTP data/context descriptor')
need(word(0,0x3cbd4)==0x3dd8c and data(0,0x3dd8c,8)==b'AP_EXCO\0' and word(0,0x3cbd8)==0x2000ff14,'AP_EXCO data name/address')
dec=B.parent/'tcon-research/qd-rt-window-reset-output-reproduce.py';need(sha(dec.read_bytes())=='fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02','pure scatter decoder pin')
s=importlib.util.spec_from_file_location('eq_scatter_decoder',dec);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
initial,_=m.unpack(raw,0x40200+0x1d860,0x4f8);root,_=m.unpack(raw,0x200+0x3ea34,0x47bc)
need(sha(initial)=='76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8' and sha(root)=='aee8a64ff7ccfaa95aa4def885fcf7d79c8f4f982d63c5efdb1686eec2cd2b6d','cold initial data pins')
half=lambda x,a:struct.unpack_from('<H',x,a)[0]
initial_fields={'image1CPU4a2':half(initial,0x4a2),**{'root'+hex(a):half(root,a)for a in(0x2400,0x240a,0x240e,0x2458,0x2460,0x2468,0x246e)}}
# Independent fixed upstream scopes, not a whole-program writer-exclusion proof.
ranges=[(1,0xb644,0x154),(1,0xb8a8,0xe4),(1,0xb9f4,0xfe),(1,0xc220,0x30),(1,0xc250,0x9c),(1,0xc470,0x4a),(1,0x1ba54,0x30),(1,0xc1e0,0x34),(0,0xa6ac,0x84),(0,0x11a04,0x5c),(0,0x21544,0x6c),(0,0x215bc,0x5c),(0,0x37be8,0x26),(0,0xbbd8,0x78),(0,0xc7a0,0x4e),(0,0x2fed4,0x20),(0,0x32820,0x26),(0,0x357dc,0x2c),(0,0x1163c,0xa8)]
rows=[];listing=[]
for image,a,n in ranges:
 rows.append({'image':image,'va':hex(a),'fileOffset':hex(a+(0x200 if image==0 else 0x40200)),'bytes':n,'sha256':sha(data(image,a,n))})
 listing.append('IMAGE'+str(image)+' VA'+hex(a));listing.extend(f'{i.address:08x} {i.mnemonic:10} {i.op_str}'for i in cs.disasm(data(image,a,n),a))
report={'schema':'eq-writer-control-source-v1','assetSha256':sha(raw),'sourceRanges':rows,'anchors':anchors,'initialFields':initial_fields,'trainerDirectReferenceCandidates':refs,'trainerDirectStores':['0xb776','0xb924','0xba1e','0xba6c','0xc238'],'root2460DirectStore':{'image':0,'va':'0xa71e','selector':'0x30','value':'low16(caller value)','aliasBase':'0x47010000'},'root246eDirectRuntimeStoreResolved':False,'ordinaryGateSourceCompatibleNonfaultDisable':{'image':0,'function':'0x215bc','store':'0x215fc','requiresOldGateEquals1':True,'stopOrFaultStoreInThisFunction':False,'directCallerSites':['0xbc02','0xbc3e','0xc7d2','0x2fee2','0x32828','0x357ec','0x37bfc']},'ordinaryGateEnable':{'image':0,'function':'0x21544','store':'0x21568','requiresOldGateEquals0':True},'completeWriterCensus':False,'continuousPublisherQuiescenceProven':False,'actualEOCallPathProven':False,'targetOperations':0}
generated={'source-audit.json':(json.dumps(report,indent=2,sort_keys=True)+'\n').encode(),'private/reviewed-disassembly.txt':('\n'.join(listing)+'\n').encode()}
for name,b in generated.items():
 if sys.argv[1:]==['--record']:
  p=D/name;p.parent.mkdir(mode=0o700,exist_ok=True)
  with p.open('xb')as f:f.write(b)
  p.chmod(0o600)
 else:need((D/name).read_bytes()==b,'frozen output '+name)
print(json.dumps({'schema':'eq-source-validation-v1','checksPassed':checks,'sourceRangeCount':len(rows),'targetOperations':0,'networkOperations':0,'sourceAuditSha256':sha(generated['source-audit.json']),'completeWriterCensus':False},sort_keys=True))
