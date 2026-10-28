#!/usr/bin/env python3
"""Independent bounded HG source review. No target transport or image output."""
import hashlib,json,struct,sys,zlib
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;HG=HERE.parent;B=HG.parent
checks=0

def need(v,why):
 global checks
 if not v:raise ValueError(why)
 checks+=1

def sha(b):return hashlib.sha256(b).hexdigest()
def reject(fn,why):
 try:fn()
 except(ValueError,struct.error):need(True,why);return
 raise ValueError('unexpected acceptance '+why)

def signed(n,bits):return n-(1<<bits)if n&(1<<(bits-1))else n

def validate_header(c):
 if len(c)<64:raise ValueError('short')
 f=struct.unpack('>7I',c[:28]);magic,hcrc,stamp,size,load,entry,dcrc=f
 if magic!=0x27051956 or size>len(c)-64:raise ValueError('magic or size')
 h=c[:4]+bytes(4)+c[8:64]
 if zlib.crc32(h)!=hcrc or zlib.crc32(c[64:64+size])!=dcrc:raise ValueError('CRC')
 return f

def handler(view,byte):
 # Independent SPARC raw-format decoder with architectural PC/nPC delay model.
 pc=0x2f7e0;npc=pc+4;regs=[0]*32;z=False;trace=[];target=None
 for count in range(10):
  if pc==0x177a4:return(regs[8],regs[9],trace)
  if not 0x2f7e0<=pc<=0x2f7f8:raise ValueError('unexpected callee/PC')
  trace.append(pc);w=struct.unpack_from('>I',view,pc)[0];op=w>>30;rd=(w>>25)&31;op3=(w>>19)&63;rs1=(w>>14)&31;imm=(w>>13)&1;simm=signed(w&8191,13)
  nextpc=npc;nextnpc=npc+4
  if op==3 and op3==1 and rd==1 and rs1==26 and imm and simm==3:regs[1]=byte
  elif op==2 and op3==0x14 and rd==0 and rs1==1 and imm and simm==0:z=regs[1]==0
  elif op==0 and ((w>>22)&7)==2:
   annul=(w>>29)&1;cond=(w>>25)&15
   if annul or cond!=9:raise ValueError('oracle supports actual nonannul bne only')
   if not z:nextnpc=pc+signed(w&0x3fffff,22)*4
  elif op==2 and op3==2 and rs1==0 and imm and rd in [8,9]:regs[rd]=simm&0xffffffff
  elif op==1:
   regs[15]=pc;nextnpc=pc+signed(w&0x3fffffff,30)*4;target=nextnpc
  else:raise ValueError('unexpected actual instruction format')
  regs[0]=0;pc,npc=nextpc,nextnpc
 raise ValueError('instruction bound')

def main():
 inv=HG/'source-inventory.json';need(sha(inv.read_bytes())=='45a47327c30d5ad17a1ef7395e7163fab86579a8c1621e1d790489dcb5961ce3','author inventory')
 j=json.loads(inv.read_text())
 for row in j['files']:
  p=HG/row['path'];data=p.read_bytes();need(not p.is_symlink()and len(data)==row['bytes']and sha(data)==row['sha256'],'frozen author file '+row['path'])
 original=(HG/'validation.normal.json').read_bytes()
 need(original==(HG/'validation.optimized.json').read_bytes()==(HERE/'reproduced.normal.json').read_bytes()==(HERE/'reproduced.optimized.json').read_bytes(),'865 author checks exactly reproduced normal/O')
 p=B/'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root/etc/micom-binary/PMDMICOM_OCJP.bin';raw=p.read_bytes()
 need(len(raw)==901120 and sha(raw)=='61754d8e0445ed1a73685af83cdcf3fea66971b1a622b04c3f614b8b63286aff','candidate identity')
 # Different implementation from HE: four vectorized byte-lane assignments.
 v=bytearray(len(raw))
 for lane in range(4):v[lane::4]=raw[3-lane::4]
 need(zlib.adler32(v[:0xdbff8])==struct.unpack_from('<I',raw,0xdbff8)[0]==0xce93f188,'independent whole-format checksum')
 component=bytes(v[0xf000:0x3f000]);f=validate_header(component)
 need(f==(0x27051956,0x7afe4346,0x65c33ddb,0x2cbe0,0xa0020000,0xa0020000,0x05f82b60),'independent legacy header+CRCs')
 need(component[28:32]==bytes([5,10,1,0])and component[32:64].split(b'\0')[0]==b'fw_sys.uimg','header CPU/type/name metadata')
 base=f[4];low=0xf040;end=low+f[3]
 def mapping(addr):
  if type(addr)is not int or not base<=addr<base+f[3]or addr%4:raise ValueError('unqualified aligned code pointer')
  return low+addr-base
 tables=[]
 for offset,count in [(0x2caec,11),(0x2cfd0,11),(0x2f6a8,60)]:
  vals=[]
  for i in range(count):
   ptr=struct.unpack_from('>I',v,offset+i*4)[0];at=mapping(ptr)
   need(low<=at and at+4<=end and at%4==0,'82 independent bounded mappings');vals.append(at)
  tables.append(vals)
 need(sum(map(len,tables))==82 and tables[0][1]==0x2cd6c and tables[2][59]==0x2f7e0,'positive operation1/command3f entries')
 sys.path.insert(0,'/tmp/tcon-capstone')
 from capstone import Cs,CS_ARCH_SPARC,CS_MODE_BIG_ENDIAN
 md=Cs(CS_ARCH_SPARC,CS_MODE_BIG_ENDIAN)
 def ins(at,m,o):
  xs=list(md.disasm(bytes(v[at:at+4]),at));need(len(xs)==1 and(xs[0].mnemonic,xs[0].op_str)==(m,o),'independent bridge instruction '+hex(at))
 for at,m,o in [(0x2ccd4,'sll','%g1, 2, %g1'),(0x2f7b4,'sll','%g1, 2, %g1'),
  (0x2d0dc,'sethi','0x2800f7, %o5'),(0x2d0e4,'or','%o5, 0x390, %o5'),(0x2d0e8,'ld','[%o5+%g1], %o4'),(0x2d0ec,'jmp','%o4'),
  (0x2f7fc,'ba,a','0x30278'),(0x30278,'ret',''),(0x3027c,'restore',''),
  (0x177b0,'st','%o5, [%sp+0x60]'),(0x177b8,'st','%g1, [%sp+0x5c]'),(0x177d8,'restore','%g0, %o0, %o0'),
  (0x170a4,'ld','[%fp+0x5c], %i3'),(0x170ac,'ld','[%fp+0x60], %i4'),(0x17080,'retl',''),
  (0x16e50,'sethi','0x3f0100, %g1'),(0x16e54,'st','%o0, [%g1]'),(0x16e58,'retl','')]:ins(at,m,o)
 for i in range(256):
  pin,mode,trace=handler(v,i);need((pin,mode)==(20,2 if i else 3),'256 raw-word PC/nPC handler cases')
  need((0x2f7ec in trace)and(0x2f7f8 in trace)and((0x2f7f0 in trace)==(i==0)),'architectural branch+call delay semantics')
 mutations=[]
 for at,mask,name in [(0x2f7e8,1<<29,'annul'),(0x2f7e8,1<<25,'condition'),(0x2f7f4,1,'callee')]:
  bad=bytearray(v);w=struct.unpack_from('>I',bad,at)[0]^mask;struct.pack_into('>I',bad,at,w);reject(lambda:handler(bad,1),'changed '+name);mutations.append(name)
 for at,byte,name in [(0x2f7ec,1,'mode-delay'),(0x2f7f8,1,'pin-delay')]:
  bad=bytearray(v);bad[at+3]^=byte;got=handler(bad,1);need(got[:2]!=(20,2),'delay instruction mutation affects arguments');mutations.append(name)
 for at in [0,4,12,16,20,24,32,64,512]:
  bad=bytearray(component);bad[at]^=1;reject(lambda:validate_header(bytes(bad)),'independent CRC/header mutation');mutations.append('header/payload-'+str(at))
 for bad in [b'',component[:63],component[:64+f[3]-1],raw[0xf000:0x3f000]]:
  reject(lambda:validate_header(bad),'short/wrong transform');mutations.append('short/transform')
 for address in [True,-1,base-4,base+1,base+f[3],0xa8000000]:reject(lambda:mapping(address),'pointer range/alignment');mutations.append('address')
 # All arithmetic facts are source values, not live addresses or electrical labels.
 need(((0x3f0100<<10), (0x3f0c44<<10)|0x20)==(0xfc040000,0xfc311020),'source MMIO constants independently constructed')
 need(bytes([0x40,20,2,0])==struct.pack('>I',0x40140200)and bytes([0x40,20,3,0])==struct.pack('>I',0x40140300),'secondary command pack')
 result=json.loads(original)
 for group,key in [('identity','flashedMcuIdentityProven'),('identity','loaderRmfPmdEquivalenceProven'),('outgoing','downstreamReceiverIdentified'),('outgoing','pinBoardNetIdentified'),('outgoing','mode2And3ElectricalMeaningQualified'),('limits','liveRamAliasesQualified'),('limits','image0SharedRootResetProven'),('limits','physicalResetProven')]:need(result[group][key]is False,'claim boundary '+group+'.'+key)
 return dict(schema='hg-independent-source-review-v1',decision='PASS_HOST_ONLY_SCOPED',checks=checks,authorReproducedChecks=result['checks'],authorFiles=len(j['files']),rawOpcodeHandlerCases=256,focusedMutations=len(mutations),candidateSha256=sha(raw),authorInventorySha256=sha(inv.read_bytes()),authorAuditSha256=sha((HG/'audit.py').read_bytes()),authorReadmeSha256=sha((HG/'README.md').read_bytes()),sourceOnly=True,targetCalls=0,networkCalls=0,oemBytesWritten=0,limits={'runtimeIdentityProven':False,'electricalResetDomainProven':False,'secondaryReceiverProven':False})
if __name__=='__main__':print(json.dumps(main(),indent=2,sort_keys=True))
