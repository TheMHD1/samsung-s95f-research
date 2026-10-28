#!/usr/bin/env python3
"""Read-only source/context audit. No root, device, transport or network import."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_MCLASS
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent;checks=0
def need(ok,msg):
 global checks
 checks+=1
 if not ok:raise ValueError(msg)
sha=lambda b:hashlib.sha256(b).hexdigest()
asset=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
raw=asset.read_bytes()
need(len(raw)==5242880 and sha(raw)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected asset')
cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS)
data=lambda va,n:raw[va+0x40200:va+0x40200+n]
word=lambda va:struct.unpack('<I',data(va,4))[0]
anchors=[]
def ins(va,mnemonic,operands):
 rows=list(cs.disasm(data(va,4),va,count=1));need(len(rows)==1 and rows[0].mnemonic==mnemonic and rows[0].op_str==operands,'instruction '+hex(va))
 i=rows[0];anchors.append({'va':hex(va),'mnemonic':mnemonic,'operands':operands,'bytes':i.size,'sha256':sha(data(va,i.size))})
for args in [
 (0xbfae,'ldr','r0, [pc, #0x80]'),(0xbfb2,'cmp','r0, #1'),(0xbfbc,'bl','#0x1e68'),
 (0xbfe0,'ldr','r0, [pc, #0x6c]'),(0xbfe2,'ldrh','r0, [r0]'),(0xbfe4,'cmp','r0, #1'),(0xbfe6,'bne','#0xc024'),
 (0xbfe8,'ldr','r1, [pc, #0x68]'),(0xbfec,'ldr.w','r0, [sp, #0xf14]'),(0xbff0,'udiv','fp, r0, r1'),(0xc01e,'bl','#0xc058'),
 (0xc060,'bl','#0x38fc'),(0xc06a,'movw','r0, #0x246a'),(0xc06e,'ldrh.w','sl, [r0, sb]'),(0xc074,'ldrh.w','r8, [r0, sb]'),
 (0xc078,'mul','r0, r5, sl'),(0xc07c,'add.w','r0, r5, r0, lsr #8'),(0xc080,'uxth','r6, r0'),
 (0xc082,'mul','r0, r5, sl'),(0xc086,'sub.w','r0, r5, r0, lsr #8'),(0xc08a,'uxth','r7, r0'),
 (0xc096,'bgt','#0xc0a0'),(0xc09e,'bge','#0xc0ce'),(0xc0aa,'strh.w','r1, [r2, r0, lsl #1]'),
 (0xc0b6,'ble','#0xc0ce'),(0xc0bc,'cbnz','r1, #0xc0c8'),(0xc0c6,'strh','r1, [r2]'),(0xc0cc,'strb','r1, [r2, r0]'),
 (0xc118,'strb','r2, [r3, r1]'),(0xc164,'strb','r2, [r3, r1]'),(0xc1b0,'strb','r2, [r3, r1]'),(0xc1b4,'uxth','r0, r1'),
 (0xc1bc,'blt.w','#0xc090'),(0xc1c8,'strh.w','r1, [r0, sb]'),
 (0xb8aa,'bl','#0x38fc'),(0xb8ec,'cmp','r0, #1'),(0xb8ee,'bne','#0xb926'),(0xb8f6,'movw','r0, #0x246e'),(0xb8fe,'bne','#0xb920'),
 (0xb906,'ldrb','r1, [r1, r0]'),(0xb90a,'ldrh.w','r2, [r2, r0, lsl #1]'),(0xb90e,'add.w','r1, r1, r2, lsl #1'),(0xb912,'strh.w','r1, [r4, r0, lsl #1]'),(0xb924,'strh','r0, [r1]'),
 (0xc2d0,'movw','r0, #0x2458'),(0xc2d8,'bne','#0xc2de'),(0xc2da,'bl','#0xc470'),
 (0xc4a6,'movw','r0, #0x2460'),(0xc4ae,'bne','#0xc56a'),(0xc4b0,'ldrh.w','r0, [r7, #0x202]'),(0xc4b6,'beq','#0xc56a'),
 (0xc4de,'strh.w','r0, [r1, r4, lsl #1]'),(0xc4e4,'strb','r0, [r1, r4]'),(0xc510,'bl','#0xc314'),
 (0xc530,'ldrb','r0, [r0, r4]'),(0xc534,'ldrh.w','r1, [r1, r4, lsl #1]'),(0xc538,'add.w','r0, r0, r1, lsl #1'),(0xc53c,'strh.w','r0, [r5, r4, lsl #1]'),
 (0xc41a,'strh.w','r0, [r1, r4, lsl #1]'),(0xc428,'ble','#0xc440'),(0xc43e,'strb','r0, [r1, r4]'),
 (0xcb2e,'bl','#0x38fc'),(0xcb50,'bl','#0xca84'),(0xcb6a,'strh.w','r0, [r1, r4, lsl #1]'),(0xcb70,'strb','r0, [r1, r4]'),
 (0xcb7a,'blt','#0xcb66'),(0xb964,'bl','#0xca84')]:ins(*args)
literals={0xc030:0x200004aa,0xc050:0x200004a2,0xc054:0x200004a8,0xc1d0:0x2000ba4c,0xc1d4:0x2000c95c,0xc1d8:0x200004a4,0xc1dc:0x200004a8,
          0xb98c:0x200004a2,0xb9a4:0x2000c95c,0xb9a8:0x2000ba4c,0xb9ac:0x200004a8,
          0xc45c:0x200004a6,0xc460:0x200004a8,0xc464:0x2000ba4c,0xc468:0x2000c95c,0xc46c:0x200004a4,
          0xc59c:0x2000ba4c,0xc5a0:0x2000c95c,0xc5a4:0x200004a8,0xcbc4:0x2000ba4c,0xcbc8:0x2000c95c,
          0xcb10:0x2000d138,0xcb14:0x2020a000,0xcb18:0x2020a788,0xcb1c:0x2020b698,0xcb20:0x2020be20}
for va,v in literals.items():need(word(va)==v,'literal '+hex(va))
need(((0xbfe0+4)&~3)+0x6c==0xc050 and word(0xc050)!=word(0xc030),'trainer vs category gate distinction')
need(0x2000ba4c+2*1920<=0x2000c95c and 0x2000c95c+1920<0x2000e19c,'complete local table bounds')
need(2*1920==0xf00 and 0xf00<0x2400,'primary table does not equal parameter block')
decoder=B.parent/'tcon-research/qd-rt-window-reset-output-reproduce.py'
need(sha(decoder.read_bytes())=='fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02','decoder pin')
spec=importlib.util.spec_from_file_location('ec_pinned_decoder',decoder);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
initial,stop=mod.unpack(raw,0x40200+0x1d860,0x4f8)
need(sha(initial)=='76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8','initialized image1 data')
need(struct.unpack_from('<I',initial,0x4e0)[0]==0x20010000,'root pointer initial')
zero_start,zero_end=0x200004f8,0x2000e19c
need(all(zero_start<=a<a+n<=zero_end for a,n in [(0x2000ba4c,3840),(0x2000c95c,1920)]),'image1 BSS cold zero covers both arrays')
primary,end=mod.unpack(raw,0x200+0x3ea34,0x47bc)
need(sha(primary)=='aee8a64ff7ccfaa95aa4def885fcf7d79c8f4f982d63c5efdb1686eec2cd2b6d' and primary[:3840]==bytes(3840),'image0 scatter alias cold zero primary')
need(sha((D/'training-gate-correction.json').read_bytes())=='fd8cfacff023f4850f358b80d2585b40946e8827cf184381b992553b3f7ff8aa','immutable earlier correction')

# Finite syntactic reference census, not a whole CFG/computed alias writer proof.
refs={hex(v):[]for v in [0x2000ba4c,0x2000c95c]}
for va in range(0,0x1d6a4,2):
 rows=list(cs.disasm(data(va,4),va,count=1))
 if not rows:continue
 i=rows[0];m=re.fullmatch(r'(r\d+), \[pc(?:, #(0x[0-9a-f]+|[0-9]+))?\]',i.op_str)
 if i.mnemonic not in ('ldr','ldr.w')or not m:continue
 literal=((va+4)&~3)+int(m[2]or'0',0);value=word(literal)
 if hex(value)in refs:refs[hex(value)].append({'va':hex(va),'literalVa':hex(literal),'mnemonic':i.mnemonic,'operands':i.op_str})
need([len(refs[k])for k in refs]==[14,18],'bounded direct reference census')

P=B/'rtp-lane-gate-trial-20261028ed/table-read-01';result=json.loads((P/'result.json').read_bytes())
need(result['accepted']is True and result['headersSent']==16 and result['bulkTransfers']==32 and result['cleanup']=='STAGE_ABSENT','completed ED read only')
saved={}
for name in ['M.bin','start-R.bin','end-R.bin','primary-lane-gate.bin','secondary-lane-gate.bin']:
 b=(P/name).read_bytes();row=next(v for v in result['rawFiles']if v['name']==name)
 need(len(b)==row['bytes'] and sha(b)==row['sha256'],'saved raw hash '+name);saved[name]=b
m=saved['M.bin'];r=saved['end-R.bin'];half=lambda b,a:struct.unpack_from('<H',b,a)[0]
need(saved['primary-lane-gate.bin']==bytes(136) and saved['secondary-lane-gate.bin']==bytes(68),'actual sampled zero tables')
need(half(m,2)==0 and half(r,0x60)==0 and half(r,0x6e)==0,'sampled known trainer/publisher controls')
context={'schema':'ec-completed-ed-context-v1','captureRelativePath':'../'+P.parent.name+'/'+P.name,'resultSha256':sha((P/'result.json').read_bytes()),
         'files':{name:{'bytes':len(b),'sha256':sha(b)}for name,b in saved.items()},'u16CPU4a2':half(m,2),'u16CPU4a8':half(m,8),'aa':half(m,10),'ac':half(m,12),'byteCPU4cc':m[44],
         'root':hex(struct.unpack_from('<I',m,64)[0]),'operatingMode':half(r,16),'r2458':half(r,0x58),'r2460':half(r,0x60),'r246e':half(r,0x6e),'r246a':half(r,0x6a),'r246c':half(r,0x6c),
         'rBytesEqual':saved['start-R.bin']==r,'primary68AllZero':True,'secondary68AllZero':True,'historicalTableValuesProven':False,'writerControlsStableDuringFutureTrialProven':False}
ranges=[(0xb8a8,0xd0),(0xbd58,0x80),(0xbe3a,0x7a),(0xbfae,0xb0),(0xc058,0x188),(0xc250,0x9c),(0xc314,0x15c),(0xc470,0x14c),(0xca84,0xac),(0xcb2c,0xa8)]
listing=[];source_rows=[]
for va,n in ranges:
 source_rows.append({'image':1,'va':hex(va),'fileOffset':hex(va+0x40200),'bytes':n,'sha256':sha(data(va,n))})
 listing.append(f'IMAGE1 VA{va:06x} FILE{va+0x40200:06x} bytes{n}')
 listing.extend(f'{i.address:06x} {i.mnemonic:10} {i.op_str}'for i in cs.disasm(data(va,n),va));listing.append('')
report={'schema':'ec-lane-writer-source-v1','assetSha256':sha(raw),'targetOperations':0,'anchors':anchors,'literals':{hex(k):hex(v)for k,v in literals.items()},'sourceRanges':source_rows,
        'knownPrimaryStores':['0xb912','0xc53c'],'knownSecondaryStoreFamilies':['0xc058','0xc314','0xc470-clear','0xcb2c-clear','image1-scatter-BSS'],
        'publisherFormula':'u16(primary[lane]) = (u8(secondary[lane]) + 2*u16(counter[lane])) modulo65536',
        'completeWriterCensus':False,'directLiteralReferenceCandidates':refs,'initialData4a2':half(initial,0x4a2),
        'resetOriginalTablesRestorationGuaranteed':False,'instructionBodyLiveFingerprintProven':False,'physicalUnitsProven':False,
        'scopeBoundary':'Other producer input c470/c314 retained only as low-SRAM writer effect; storage/provider/control operation not followed or invoked.'}
generated={'source-audit.json':(json.dumps(report,indent=2)+'\n').encode(),'completed-ed-context.json':(json.dumps(context,indent=2)+'\n').encode(),'reviewed-disassembly.txt':('\n'.join(listing)+'\n').encode()}
for name,value in generated.items():
 if sys.argv[1:]==['--record']:
  with(D/name).open('xb')as f:f.write(value)
 else:need((D/name).read_bytes()==value,'frozen derived '+name)
print(json.dumps({'accepted':True,'sourceChecks':checks,'targetOperations':0,'completeWriterCensus':False,'sourceAuditSha256':sha(generated['source-audit.json'])},sort_keys=True))
