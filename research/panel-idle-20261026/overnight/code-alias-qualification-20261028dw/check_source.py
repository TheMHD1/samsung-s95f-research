#!/usr/bin/env python3
"""Bounded host-only code-bank/source fingerprint proposal; no target bindings."""
from pathlib import Path
import hashlib,json,struct,sys
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_LITTLE_ENDIAN,CS_MODE_MCLASS
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent;ASSET=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
raw=ASSET.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();checks=0
def need(ok,why):
 global checks
 if not ok:raise ValueError(why)
 checks+=1
need(len(raw)==5242880 and sha(raw)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package identity')
def bias(image):return [0x200,0x40200][image]
def data(image,va,n):return raw[bias(image)+va:bias(image)+va+n]
def word(image,va):return struct.unpack('<I',data(image,va,4))[0]
decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_LITTLE_ENDIAN|CS_MODE_MCLASS)
def instruction(image,va,mnemonic,operands):
 rows=list(decoder.disasm(data(image,va,4),va,count=1));need(len(rows)==1 and rows[0].mnemonic==mnemonic and rows[0].op_str==operands,'instruction '+str(image)+':'+hex(va));return rows[0]
def mapped(tag,pointer):
 need(type(tag)is int and 0<=tag<=0xffffffff and type(pointer)is int and 0<=pointer<=0xffffffff,'u32 tag/pointer')
 if pointer==0:return 0
 if tag==0:
  if pointer<0x40000:return pointer+0x44000000
  if 0x20000000<=pointer<0x20020000:return pointer+0x25000000
 else:
  if pointer<0x20000:return pointer+0x46000000
  if 0x20000000<=pointer<0x20020000:return pointer+0x27000000
 return 0
need(data(0,0x39d4c,80)==data(1,0x1bb74,80),'byte-identical cross-core resource mapper')
need(word(1,0x1bbc0)==word(0,0x39d98)==0x20020000,'strict SRAM upper bound literal')
for va,mn,op in [(0x1bb74,'mov','r2, r0'),(0x1bb76,'cbnz','r1, #0x1bb7c'),(0x1bb7c,'cbnz','r2, #0x1bb9c'),(0x1bb7e,'cmp.w','r1, #0x40000'),(0x1bb84,'add.w','r0, r1, #0x44000000'),(0x1bb9c,'cmp.w','r1, #0x20000'),(0x1bba2,'add.w','r0, r1, #0x46000000'),(0x1bbb4,'add.w','r0, r1, #0x27000000')]:instruction(1,va,mn,op)
for va,mn,op in [(0x3a134,'adr','r1, #0x24'),(0x3a136,'movs','r0, #1'),(0x3a138,'bl','#0x39dac'),(0x39db4,'ldr','r1, [pc, #0x18]'),(0x39db8,'bl','#0x39dd4'),(0x39de0,'bl','#0x39d9c'),(0x39df2,'bl','#0x39d4c'),(0x39e0c,'bl','#0x39d4c'),(0x39e2a,'bl','#0x39d4c'),(0x39e36,'bl','#0xc04'),(0x39dc6,'ldr','r1, [r5, #4]'),(0x39dc8,'bl','#0x39d4c')]:instruction(0,va,mn,op)
need(data(0,0x3a15c,8)==b'AP_EXCO\0' and word(0,0x39dd0)==0x1000c,'tag1 AP_EXCO directory selector')
def directory(image,va):
 countptr,stride,table=struct.unpack('<3I',data(image,va,12));count=word(image,countptr);need(stride==12 and count%stride==0 and count<=24,'bounded context directory')
 entries=[]
 for at in range(table,table+count,stride):
  name,pointer,length=struct.unpack('<3I',data(image,at,12));label=data(image,name,32).split(b'\0')[0].decode('ascii');entries.append({'entryVa':hex(at),'nameVa':hex(name),'name':label,'pointer':hex(pointer),'length':length})
 return {'directoryVa':hex(va),'countPointer':hex(countptr),'countBytes':count,'stride':stride,'tableVa':hex(table),'entries':entries}
dirs=[directory(i,0x1000c)for i in [0,1]]
need(dirs[1]['entries']==[{'entryVa':'0x1c44c','nameVa':'0x1d64c','name':'AP_EXCO','pointer':'0x20000500','length':0x96c0}],'image1 unique AP_EXCO context')
need(mapped(1,0x1000c)==0x4601000c and mapped(1,0x1c458)==0x4601c458 and mapped(1,0x1c44c)==0x4601c44c and mapped(1,0x1d64c)==0x4601d64c and mapped(1,0x20000500)==0x47000500,'tag1 code/name/SRAM chain')
instruction(0,0xc08,'ldr','r2, [r0], #4');instruction(0,0xc20,'ldr','r2, [r0], #4')
for tag in [0,1,2,255,0xffffffff]:
 for pointer in [0,1,0x1ffff,0x20000,0x3ffff,0x40000,0x1fffffff,0x20000000,0x2001ffff,0x20020000,0xffffffff]:
  out=mapped(tag,pointer);need(out==0 or (0x44000001<=out<0x44040000 if tag==0 and pointer<0x20000000 else 0x45000000<=out<0x45020000 if tag==0 else 0x46000001<=out<0x46020000 if pointer<0x20000000 else 0x47000000<=out<0x47020000),'mapper branch boundaries')
for va,mn,op in [(0x28f5a,'str','r0, [r4, #0xc]'),(0x28f60,'str','r0, [r4, #4]'),(0x29266,'ubfx','r8, r0, #8, #0x10'),(0x2927e,'movs','r0, #0'),(0x29282,'strb','r0, [r1]'),(0x292de,'movw','r1, #0x101'),(0x292e6,'beq','#0x29382'),(0x29382,'cmp.w','r8, #2'),(0x29386,'bne','#0x293b0'),(0x28fbe,'ldrb','r0, [r4, #0xc]'),(0x28fc0,'and','r0, r0, #0xef'),(0x2905a,'movs','r0, #0'),(0x2905e,'strb','r0, [r1]'),(0x290cc,'cbz','r0, #0x290d6'),(0x290fe,'ldr','r2, [r4, #4]'),(0x29102,'ldr','r3, [r0]'),(0x29106,'bl','#0x8054'),(0x805c,'mov','r6, r2'),(0x807a,'str','r6, [r4, #0x10]'),(0x2ac46,'ldr','r1, [r4, #0x10]'),(0x2ac48,'bl','#0x280c'),(0x296e,'adds','r0, r6, r4'),(0x2970,'str','r0, [r1, #4]')]:instruction(0,va,mn,op)
need(word(0,0x293b4)==word(0,0x29224)==0x20000570,'remap byte shared literal')
need(word(0,0x291f0)==0x20000571,'direct-address mode literal')
need(word(0,0x29208)==0x20000554,'optional checksum flag literal')
instruction(0,0x29110,'beq','#0x291ec')
for va,mn,op in [(0x29116,'lsrs','r1, r2, #2'),(0x2911a,'bl','#0x4650'),(0x465e,'ldr.w','r4, [r2, r1, lsl #2]'),(0x2914,'cmp','r0, #1'),(0x2918,'sub.w','ip, r2, r4'),(0x291e,'bfi','r0, ip, #0, #0x10')]:instruction(0,va,mn,op)

# Exact fixed proposal, host data only. Never load a target/root adapter.
windows=[]
for name,va,site in [('predicate',0x2020,0x2024),('selection',0xbd58,0xbd58),('tuple',0xc5d0,0xc5d0),('setter',0xc1e0,0xc1e0)]:
 n=16;bus=mapped(1,va);expected=data(1,va,n);need(0<va and va+n<=0x20000 and va%4==0 and bus%4==0,'fixed code window bounds/alignment')
 need(va<=site and site+4<=va+n,'entire DS displaced span covered')
 need(expected!=data(0,va,n),'distinguishes same-VA image0 bytes')
 windows.append({'name':name,'linkedVa':hex(va),'siteVa':hex(site),'image':1,'fileOffset':hex(va+0x40200),'busAddress':hex(bus),'bytes':n,'alignmentBytes':4,'sixteenByteAligned':va%16==0,'expectedSha256':sha(expected),'sameVaImage0Sha256':sha(data(0,va,n)),'target':'0x101','headerLittleEndianHex':struct.pack('<III',0x101,bus,n).hex()})
plan={'schema':'dw-fixed-code-fingerprint-proposal-v1','deployableHelperImplemented':False,'targetOperations':0,'sourceAliasQualified':True,'liveUsbCodeDmaReachabilityVerified':False,'wholeRunningImageAttested':False,'executableWriteQualified':False,'tag':1,'windows':windows,'headers':4,'bulks':8,'totalExpectedInputBytes':64,'fallbackBank':None,'retry':False,'hookOrWrite':False,'acceptance':'All four exact16-byte payloads match their individual image1 hashes; strict native/transport/phase/cleanup acceptance required independently. Any mismatch is a retained negative, not a fallback instruction.'}
ranges=[(1,0x1bb74,0x50),(1,0x1bbc4,0x100),(1,0x1bcc4,0x58),(0,0x39d4c,0x100),(0,0x3a120,0x44),(0,0xc04,0x34),(1,0x1000c,12),(1,0x1c44c,16),(1,0x1d64c,8),(0,0x28f24,0xa0),(0,0x28fb4,0x24),(0,0x29046,0x38),(0,0x290c8,0x64),(0,0x291f0,0x40),(0,0x29258,0x164),(0,0x8054,0x3e),(0,0x2ac10,0x66),(0,0x280c,0x180),(0,0x4650,0x1c)]
refs=[{'image':i,'linkedVa':hex(a),'fileOffset':hex(a+bias(i)),'bytes':n,'sha256':sha(data(i,a,n))}for i,a,n in ranges]
out={'schema':'dw-source-qualification-v1','status':'PASS','checksPassed':checks,'targetOperations':0,'networkOperations':0,'assetBytes':len(raw),'assetSha256':sha(raw),'tagRole':'zero=image0 bank; nonzero=image1 bank, with actual selected image0 caller passing1','directories':dirs,'sourceRanges':refs,'limitations':['Source mapping and CPU resource reads do not prove USB DMA reachability at proposed code windows.','Exact64-byte fingerprint would not attest whole running code or instruction-fetch identity.','No executable write/cache/atomic install/scratch/rollback property follows.','Halfword-stride BL census, when used for navigation, is not a complete indirect-call or computed-alias proof.']}
(D/'fixed-read-plan.json').write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n');(D/'source-qualification.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
listing=['# Bounded instruction excerpts, selected package identity pinned in source-qualification.json.',' # File = linkedVA + image bias; literal/data ranges are described separately, not decoded as instructions.']
for image,va,n,label in [(1,0x1bb74,0x4a,'mapper'),(0,0x39d4c,0x4a,'identical mapper'),(0,0x39dac,0x22,'tag-preserving context resolver'),(0,0x39dd4,0x78,'directory walk'),(0,0x3a120,0x2e,'actual tag1 caller'),(0,0xc04,0x34,'CPU reads from translated name'),(0,0x28f44,0x28,'header decoding'),(0,0x28fb4,0x12,'low operation normalization'),(0,0x29046,0x1c,'operation1 mode0 producer'),(0,0x290c8,0x64,'direct-address IN dispatch'),(0,0x29258,0x15c,'validator'),(0,0x8054,0x3e,'IN scheduler pointer retention'),(0,0x2ac42,0xa,'DMA descriptor builder call'),(0,0x296e,0xc,'DMA descriptor source address')]:
 listing.append('\nIMAGE'+str(image)+' '+label+' VA'+hex(va)+' FILE'+hex(va+bias(image)))
 listing.extend(f'{i.address:08x} {i.mnemonic:10s} {i.op_str}'for i in decoder.disasm(data(image,va,n),va))
for row in windows:
 listing.append('\nIMAGE1 fixed fingerprint '+row['name']+' VA'+row['linkedVa'])
 listing.extend(f'{i.address:08x} {i.mnemonic:10s} {i.op_str}'for i in decoder.disasm(data(1,int(row['linkedVa'],16),16),int(row['linkedVa'],16)))
(D/'reviewed-disassembly.txt').write_text('\n'.join(listing)+'\n')
print(json.dumps({'status':'PASS','checksPassed':checks,'planSha256':sha((D/'fixed-read-plan.json').read_bytes()),'sourceQualificationSha256':sha((D/'source-qualification.json').read_bytes()),'targetOperations':0}))
