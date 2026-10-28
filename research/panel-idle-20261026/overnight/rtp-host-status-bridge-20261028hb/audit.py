#!/usr/bin/env python3
"""Bounded static source checks plus pure packet/response integer equivalence. No I/O adapter."""
import hashlib,io,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent;ROOT=B.parent
CHECKS=0;PINS=[]
def need(v,why):
 global CHECKS
 if not v:raise ValueError(why)
 CHECKS+=1
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,expected=None):
 b=p.read_bytes()
 if expected:need(sha(b)==expected,'pin '+p.name)
 PINS.append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':sha(b)})
 return b

def packet(command,register):
 if type(command)is not int or type(register)is not int or not 0<=command<=65535 or not 0<=register<=0xffffffff:raise ValueError('packet widths')
 return command.to_bytes(2,'big')+register.to_bytes(4,'big')
def assembled(payload):
 if type(payload)is not bytes or len(payload)!=6:raise ValueError('six bytes')
 command=0;register=0
 for n,b in enumerate(payload):
  if n<2:command=((command<<8)&65535)|b
  else:register=((register<<8)&0xffffffff)|b
 return command,register

def reply(ap_halfword):
 if type(ap_halfword)is not int or not 0<=ap_halfword<=65535:raise ValueError('AP u16')
 # Firmware caches zero-extended return in a word, extracts (24-8*(index&3)).
 return bytes((ap_halfword>>(24-8*i))&255 for i in range(4))

def main():
 sys.path.insert(0,'/tmp/tcon-capstone')
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
 from elftools.elf.elffile import ELFFile
 package=read(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin','bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0')
 fw=package[0x200:0x40200];image1=package[0x40200:0x60200];thumb=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 qdf=read(ROOT/'binaries/qdf_tcon.ko','97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63')
 elf=ELFFile(io.BytesIO(qdf));sec=elf.get_section_by_name('.text');text=sec.data();arm64=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
 ave=read(ROOT/'binaries/libave.so.0.1','a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777')
 aveelf=ELFFile(io.BytesIO(ave));avesection=aveelf.get_section_by_name('.text');avecode=avesection.data();aveva=avesection['sh_addr']
 def ins(md,b,a,base=0):
  q=next(md.disasm(b[a-base:a-base+4],a,count=1));return q.mnemonic,q.op_str
 fwanchors=[(0x214dc,'movw','r0, #0x240a'),(0x214e0,'ldrb','r0, [r0, r4]'),(0x214e2,'and','r0, r0, #1'),(0x214e6,'cbz','r0, #0x214f6'),(0x214f0,'movs','r0, #0x10'),(0x214f2,'bl','#0xb660'),(0xb664,'mov','r5, r0'),(0xb6a4,'mov','r0, r5'),(0xb6a6,'bl','#0x2b764'),(0x2b766,'mov','r4, r0'),(0x2b768,'bl','#0xe670'),(0x2b76c,'add.w','r5, r0, #0x10'),(0x2b772,'bfi','r0, r4, #0, #0x10'),(0x2b776,'strh','r0, [r5]'),(0x21646,'movw','r0, #0xf380'),(0x2164a,'cmp','r4, r0'),(0x2164c,'bne','#0x21662'),(0x2164e,'mov','r0, r5'),(0x21650,'bl','#0x21df8'),(0x21654,'mov','r6, r0'),(0x21672,'mov','r0, r6'),(0x21e0a,'cmp','r4, #0x23'),(0x21e0c,'bhs','#0x21ee6'),(0x21e0e,'tbb','[pc, r4]'),(0x21e66,'bl','#0xe670'),(0x21e6a,'ldrh','r0, [r0, #0x10]'),(0x21e6c,'b','#0x21e3a'),(0x21e3a,'pop.w','{r4, r5, r6, r7, r8, pc}'),(0x12976,'and.w','r0, r1, r0, lsl #8'),(0x12988,'strh','r0, [r1]'),(0x129b6,'lsls','r0, r0, #8'),(0x129c6,'str','r0, [r1]'),(0x128a2,'cmp','r0, #0xf3'),(0x128a4,'beq','#0x128be'),(0x128be,'movs','r0, #0'),(0x12a9c,'and','r5, r0, #3'),(0x12aa0,'cbnz','r5, #0x12ab2'),(0x12aaa,'bl','#0x21624'),(0x12ab0,'str','r0, [r1]'),(0x12ab2,'movs','r0, #0x18'),(0x12ab4,'sub.w','r7, r0, r5, lsl #3'),(0x12aba,'ldr','r0, [r0]'),(0x12abc,'lsrs','r0, r7'),(0x12abe,'uxtb','r0, r0'),(0x12ac0,'str','r0, [r4, #0x28]')]
 for a,m,o in fwanchors:need(ins(thumb,fw,a)==(m,o),'FW '+hex(a))
 need(struct.unpack_from('<I',fw,0xe674)[0]==0x2000f0e0,'same AP getter object')
 need(ins(thumb,image1,0xc1fa)==('movw','r1, #0x1001') and ins(thumb,image1,0xc200)==('strh','r1, [r0, r4]'),'image1 common setter fault1001')
 need(fw[0x21e12+8]==0x2a and 0x21e12+2*fw[0x21e12+8]==0x21e66,'reg08 table target')
 need(fw[0x21e12+7]!=0x2a and fw[0x21e12+9]!=0x2a,'neighbor registers distinct')
 def literal(at,offset):return struct.unpack_from('<I',fw,((at+4)&~3)+offset)[0]
 globals_={'command':literal(0x12aa6,0x130),'register':literal(0x12aa2,0x13c),'replyIndex':literal(0x12a98,0x12c),'replyWord':literal(0x12aae,0x144)}
 need(globals_=={'command':0x200008c8,'register':0x200008cc,'replyIndex':0x2000090c,'replyWord':0x20000900},'receiver globals')
 need(literal(0x12ab8,0x138)==globals_['replyWord'],'same cached word extraction')
 need(literal(0x12986,0x250)==globals_['command'],'incoming command assembly target')
 need(literal(0x129c4,0x218)==globals_['register'],'incoming register assembly target')
 qanchors=[(0xa030,'mov','x0, #8'),(0xa038,'movk','x0, #0xf380, lsl #32'),(0xa040,'bl','#0x9b88'),(0x9c08,'lsr','x2, x19, #0x28'),(0x9c0c,'lsr','x1, x19, #0x20'),(0x9c10,'rev','w19, w19'),(0x9c18,'strb','w2, [sp, #0x5a]'),(0x9c1c,'strb','w1, [sp, #0x5b]'),(0x9c20,'str','w19, [sp, #0x5c]'),(0x9c4c,'mov','w3, #6'),(0x9c70,'mov','w3, #4'),(0x9c88,'ldur','w0, [sp, #0x56]'),(0x9c8c,'rev','w0, w0'),(0x9c90,'str','w0, [x21]'),(0x9cf8,'mov','w5, #4'),(0x9cfc,'mov','w3, #6'),(0xa078,'ldr','w0, [x21, #0x28]'),(0xa07c,'cmp','w0, #1')]
 for a,m,o in qanchors:need(ins(arm64,text,a)==(m,o),'QDF '+hex(a))
 need(ins(thumb,avecode,0x268d86,aveva)==('ubfx','r3, r3, #4, #1'),'AVE decoder bit4')
 for p in [ROOT/'tcon-research/rt-protect-controller-path.md',ROOT/'tcon-research/rt-protect-controller-path.disasm',B/'menu-fault-rearm-design-20261028gy/source-inventory.json',B/'menu-fault-rearm-design-20261028gy/validation.normal.json']:read(p)
 spans=[]
 for domain,blob,filebase,ranges in [('firmware-image0',fw,0x200,[(0x214d4,0x21512),(0xb660,0xb6fa),(0x2b764,0x2b77a),(0xe670,0xe678),(0x1289a,0x128c2),(0x12966,0x129ca),(0x12a92,0x12acc),(0x21624,0x21676),(0x21df8,0x21eea)]),('qdf-text',text,sec['sh_offset'],[(0xa000,0xa0fc),(0x9b88,0x9d14)])]:
  for lo,hi in ranges:spans.append({'domain':domain,'address':hex(lo),'endExclusive':hex(hi),'fileOffset':hex(filebase+lo),'bytes':hi-lo,'sha256':sha(blob[lo:hi])})
 packet_=packet(0xf380,8);need(packet_==bytes.fromhex('f38000000008') and assembled(packet_)==(0xf380,8),'wire six-byte identity')
 cases=[]
 for value in [0,1,2,15,16,17,31,32,128,255,256,4097,0x1234,0xabcd,65535]:
  raw=reply(value)
  # Driver loads little-endian RAM bytes and REV32, yielding their big-endian numeric value.
  numeric=int.from_bytes(raw,'big')
  need(len(raw)==4 and raw[:2]==bytes(2) and numeric==value,'u16 zero-extension/four response bytes')
  need(((numeric>>4)&1)==((value>>4)&1),'AVE bit4 width')
  cases.append({'apHalfword':value,'fourByteHex':raw.hex(),'hostWord':numeric,'hostBit4':(numeric>>4)&1})
 for command in [0,0xf300,0xf380,65535]:
  for register in [0,7,8,9,0x22,0x23,0xffffffff]:need(assembled(packet(command,register))==(command,register),'input width and byte order')
 for bad in [b'',bytes(5),bytes(7),'f38000000008',bytearray(6)]:
  try:assembled(bad)
  except ValueError:need(True,'malformed bytes rejected')
  else:need(False,'malformed accepted')
 for bad in [-1,65536,True,1.0]:
  try:reply(bad)
  except ValueError:need(True,'invalid AP width rejected')
  else:need(False,'AP value accepted')
 print(json.dumps({'schema':'hb-rtp-host-status-static-bridge-v1','status':'PASS_CONDITIONAL_SOURCE_BRIDGE','checks':CHECKS,'inputPins':PINS,'sourceSpans':spans,'receiverGlobals':{k:hex(v)for k,v in globals_.items()},'apCpuObject':'0x2000f0e0','reasonHalfwordOffset':'0x10','commandHex':packet_.hex(),'register08DispatchTarget':'0x21e66','sourceChain':['image1c1e0→rootfault1001','image0214d4testsrootfaultlowbit→b660reason10','b660→2b764→AP+10=10','F380/08→21df8TBBentry8→e670AP+10u16','12a92caches32bitreturn→fourMSB-firstresponsebytes','QDFsix-bytecommand/four-byteread→REV32→status','AVEbit4decoderRTProtect'], 'responseCases':cases,'wireSourceSemanticsMatch':True,'actualWireExchangeObservedHere':False,'actualImage0EmergencyEntryProven':False,'runtimeHandlerOrOverrideModeAttested':False,'sameInstantAsPriorEL10Proven':False,'causeOrPhysicalSuppressionReversalProven':False,'writerImplemented':False,'targetOperations':0,'networkOperations':0},indent=2,sort_keys=True))
if __name__=='__main__':main()
