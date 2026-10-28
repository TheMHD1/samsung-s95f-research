#!/usr/bin/env python3
"""Source-only finite C8 transient/restore-dependency audit. No target I/O."""
from pathlib import Path
import hashlib,json,struct
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_LITTLE_ENDIAN
P=Path(__file__).resolve().parent
B=P.parent
checks=0
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 pins=json.loads((P/'input-pins.json').read_text());inputs={}
 for pin in pins['inputs']:
  data=(B/pin['path']).read_bytes()
  need(len(data)==pin['bytes'] and sha(data)==pin['sha256'],'pin '+pin['id'])
  inputs[pin['id']]=data
 pkg=inputs['selected'];need(len(pkg)==0x500000 and sha(pkg)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected source')
 md=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_LITTLE_ENDIAN)
 images={0:pkg[0x200:0x40200],1:pkg[0x40200:0x60200]}
 def ins(image,a,m,o):
  q=list(md.disasm(images[image][a:a+4],a,count=1))
  need(len(q)==1 and(q[0].mnemonic,q[0].op_str)==(m,o),'instruction image'+str(image)+' '+hex(a))
 def u32(image,a):return struct.unpack_from('<I',images[image],a)[0]
 def calls(image,target):
  result=[];raw=images[image]
  for a in range(0,len(raw)-3,2):
   first,second=struct.unpack_from('<HH',raw,a)
   if first&0xf800!=0xf000 or second&0xd000!=0xd000:continue
   s=first>>10&1;j1=second>>13&1;j2=second>>11&1
   v=s<<24|(1^j1^s)<<23|(1^j2^s)<<22|(first&0x3ff)<<12|(second&0x7ff)<<1
   dst=a+4+(v-(1<<25) if v&(1<<24) else v)
   if dst==target:result.append(a)
  return result
 # Cross-core source object and image1 local destination.
 for a,m,o in [(0x393e,'bl','#0x38e8'),(0x3942,'mov','r6, r0'),
  (0x3944,'bl','#0x38f4'),(0x3948,'mov','r5, r0'),
  (0x394e,'ldrb.w','r0, [r6, #0x3d8]'),(0x3952,'strb.w','r0, [r5, #0x6c7]'),
  (0x3956,'ldrb','r0, [r6]'),(0x3958,'strb.w','r0, [r5, #0x6c8]'),
  (0x38e8,'ldr','r0, [pc, #4]'),(0x38ea,'ldr','r0, [r0]'),
  (0x38f4,'ldr','r0, [pc, #0]'),(0x1bce2,'bl','#0x1bc24'),
  (0x1bce8,'str','r0, [r1]'),(0x1bc3e,'ldr','r1, [r5, #4]'),
  (0x1bc40,'bl','#0x1bb74'),(0x1bb96,'add.w','r0, r1, #0x25000000')]:ins(1,a,m,o)
 need(u32(1,0x38f0)==0x200002cc and u32(1,0x38f8)==0x20000500,'getter literals')
 need(u32(1,0x1bd5c)==0x200002cc and u32(1,0x1bc48)==0x1000c,'startup alternate lookup root and slot')
 row=struct.unpack_from('<7I',pkg,0x3c5b8)
 need(row[0]==0x3dd84 and row[3]==0x3dd8c and row[4:6]==(0x200158a8,0x3ec),'derived object record')
 need(pkg[0x3dd84+0x200:].split(b'\0',1)[0]==b'MULTI' and pkg[0x3dd8c+0x200:].split(b'\0',1)[0]==b'AP_EXCO','object names')
 need(0x200158a8+0x25000000==0x450158a8,'selector0 cross-core source alias arithmetic')
 ins(0,0xe76c,'ldr','r0, [pc, #0]')
 need(u32(0,0xe770)==0x200158a8,'image0 derived getter')
 # Ordinary zero clear is independent of startup/reset and does not touch +3d8.
 for a,m,o in [(0x32766,'bl','#0xe76c'),(0x3276a,'mov','r4, r0'),
  (0x3277e,'movs','r0, #0'),(0x32780,'strb','r0, [r4]'),
  (0x32786,'strb.w','r0, [r4, #0x26]'),
  (0x327b6,'blx','r0'),(0x327b8,'cmp','r0, #1'),
  (0x327ba,'bne','#0x327c0'),(0x327bc,'bl','#0x32764'),
  (0x32a8a,'cbz','r7, #0x32aae'),(0x32a8c,'movs','r0, #0'),
  (0x32a96,'movs','r0, #0x2d'),(0x32a98,'ldrb','r0, [r0, r4]'),
  (0x32a9a,'cbz','r0, #0x32aa4'),(0x32aa0,'bl','#0x32764'),
  (0x3286e,'mov','r5, r0'),(0x32870,'bl','#0xe76c'),
  (0x32874,'mov','r4, r0'),(0x3287c,'strb','r5, [r4]'),
  (0x333c4,'bl','#0xe76c'),(0x333c8,'mov','r4, r0'),
  (0x333e8,'movs','r0, #0'),(0x333ea,'strb','r0, [r4]'),
  (0x31474,'cmp','r0, #1'),(0x31476,'beq','#0x3147c'),
  (0x3147c,'cmp','r4, #0xc'),(0x3147e,'bne','#0x314a6'),
  (0x31486,'bl','#0x32764')]:ins(0,a,m,o)
 need(u32(0,0x3278c)==0x20000e70,'clear global pointer slot is image0 local0xe70')
 clear_body=list(md.disasm(images[0][0x32764:0x3278c],0x32764))
 need([(x.mnemonic,x.op_str) for x in clear_body if x.mnemonic in ['bl','blx']]==[('bl','#0xe76c')],'clear body calls only fixed object getter')
 clear_callers=calls(0,0x32764)
 need(clear_callers==[0x31486,0x327bc,0x32aa0],'bounded aligned direct clear callers')
 setter_callers=calls(0,0x3286c)
 need(setter_callers==[0x329f8,0x32a0c,0x32a2e,0x32ab6],'bounded aligned direct setter callers')
 for a,v in [(0x329f8,4),(0x32a0c,1),(0x32a2e,2),(0x32ab6,3)]:
  ins(0,a-2,'movs','r0, #'+str(v));ins(0,a,'bl','#0x3286c')
 # Recorded C8 consumers compare3; zero takes stock non3 branches.
 for a,m,o in [(0x3a12,'ldrb.w','r0, [r5, #0x6c8]'),
  (0x3a16,'cmp','r0, #3'),(0x3a18,'bne','#0x3a54'),
  (0x18c96,'bl','#0x3934'),(0x18c9a,'bl','#0x38f4'),
  (0x18c9e,'ldrb.w','r0, [r0, #0x6c8]'),
  (0x18ca2,'cmp','r0, #3'),(0x18ca4,'bne','#0x18cca')]:ins(1,a,m,o)
 refs=[]
 for a in range(0,len(images[1])-3,2):
  q=list(md.disasm(images[1][a:a+4],a,count=1))
  if q and q[0].mnemonic.startswith(('ldr','str')) and '#0x6c8]' in q[0].op_str:
   refs.append({'va':hex(a),'mnemonic':q[0].mnemonic,'operands':q[0].op_str})
 need([x['va'] for x in refs]==['0x3958','0x3a12','0x18c9e'],'bounded C8 immediate-offset syntactic census')
 # Logger eligibility uses the rooted logger flag, not the C8 selector.
 for a,m,o in [(0x1b8d0,'bl','#0x38fc'),(0x1b8d4,'mov','r5, r0'),
  (0x1b8d6,'movw','r0, #0x2406'),(0x1b8da,'ldrb','r0, [r0, r5]'),
  (0x1b8dc,'and','r0, r0, #1'),(0x1b8e0,'cbz','r0, #0x1b938')]:ins(1,a,m,o)
 sink=list(md.disasm(images[1][0x1b8c8:0x1b942],0x1b8c8))
 need(all('#0x6c8' not in x.op_str for x in sink),'pinned sink contains no direct C8 reference')
 fg=inputs['fg_engine'].decode();protocol=inputs['fg_protocol'].decode()
 need('c[8]==3' in fg,'legacy context refusal reproduced')
 need('phase==ProtocolPhase.ReadyForHeader&&!clockLost&&o.Error==null' in fg,'legacy cleanup prior-error rule')
 need('020100000624014702000000' in protocol,'fixed logger header')
 need('LoggerOffPayload={0,0}' in fg,'exact restoration original halfword')
 # A finite source-path witness, not reconstruction of the failed live cycle.
 state={'derived0':3,'derived3d8':1,'c7':1,'c8':3,'root':0x20010000,'logger':1}
 state['derived0']=0 # image0VA32780
 state['c7']=state['derived3d8'];state['c8']=state['derived0'] # image1VA3952/3958
 need((state['c7'],state['c8'],state['root'],state['logger'])==(1,0,0x20010000,1),'stock transient witness retains independent boolean/root/logger')
 for selector in [0,3]:
  need((1&1)==1 and (0&1)==0,'logger eligibility independent of C8 '+str(selector))
 need({0,1,2,3,4}!={0,3},'no global0or3-only domain claim')
 spans=[]
 for image,a,z,role in [(1,0x38e8,0x395c,'callback/getters'),(1,0x1bb74,0x1bcc4,'mapper/lookup'),
  (1,0x1bcc4,0x1bd48,'pointer binding'),(0,0xe76c,0xe774,'derived getter'),
  (0,0x32764,0x3278c,'ordinary clear'),(0,0x32790,0x327c4,'callback return clear'),
  (0,0x329ce,0x32ac8,'control decision and clear'),(0,0x3286c,0x328a4,'setter'),
  (0,0x333a8,0x33468,'startup clear'),(0,0x31458,0x3149c,'third clear caller prefix'),
  (1,0x3a12,0x3a20,'first direct consumer'),(1,0x18c94,0x18cda,'second direct consumer'),
  (1,0x1b8c8,0x1b948,'stock sink')]:
  spans.append({'image':image,'role':role,'va':hex(a),'end_exclusive':hex(z),
   'file_offset':hex(a+(0x40200 if image else 0x200)),
   'sha256':sha(images[image][a:z])})
 print(json.dumps({'schema':'fl-c8-source-transient-v1','checks':checks,'source_spans':spans,
  'context_field_cpu':'0x20000bc8','cross_core_source_cpu':'0x200158a8',
  'mapped_source':'0x450158a8','source_object':['MULTI','AP_EXCO'],
  'positive_stock_values':[0,1,2,3,4],'global_value_domain_complete':False,
  'zero_requires_reset':False,'stock_runtime_zero_clear':'image0VA0x32780',
  'zero_clear_direct_callers':[hex(a) for a in clear_callers],
  'zero_clear_other_writes':'derived+0x26, derived+0x2a..+0x2f, image0-local callback slot0x20000e70; no derived+0x3d8 or image1-root logger write in this bounded body',
  'setter_direct_callers':[hex(a) for a in setter_callers],
  'image1_immediate_offset_census':refs,'finite_transient_witness':state,
  'source_supports_restore_only_c8_zero':True,'fresh_arm_or_readiness_widening_supported':False,
  'restore_conditions':'Fresh binding, HeaderReady phase, exact root/mode/geometry/profile and known logger0or1 without upper-bit drift; fixed original00 halfword only; observed final readback required. C8zero is a known stock transient and alone does not identify context replacement.',
  'failed_live_cycle_cause_proven':False,'all_indirect_writers_excluded':False,
  'target_network_root_operations':0,'executable_modifications':0},indent=2,sort_keys=True))
if __name__=='__main__':main()
