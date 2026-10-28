#!/usr/bin/env python3
"""Host-only source/table/branch checks for additive frame→SLG integration."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_ARCH_ARM64,CS_MODE_THUMB,CS_MODE_ARM
from elftools.elf.elffile import ELFFile
from frame_mode_model import chip14_nonmonitor_mode
D=Path(__file__).resolve().parent;B=D.parent
checks=0
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
p=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';b=p.read_bytes()
need(sha(b)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package')
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
def thumb(va):
 i=next(md.disasm(b[va+0x200:va+0x204],va));return i.mnemonic,i.op_str
for va,m,o in [(0x2c5fc,'cmp.w','r4, #0xf300'),(0x2c606,'bl','#0x2c71c'),(0x2c720,'mov','r6, r0'),(0x2c722,'mov','r4, r1'),(0x2c792,'and','r0, r6, #3'),(0x2c79a,'asrs','r0, r6, #2'),(0x2c79c,'subs','r0, #9'),(0x2c79e,'cmp','r0, #0xbd'),(0x2c7a0,'bhs','#0x2c7a8'),(0x2c7aa,'lsls','r1, r0, #2'),(0x2c7ac,'add','r1, pc'),(0x2c7ae,'ldr','r1, [r1, #4]'),(0x2c7b0,'add','pc, r1'),(0x2ce02,'uxtb','r0, r4'),(0x2ce04,'bl','#0x2555c'),(0x25560,'bl','#0xe670'),(0x2558a,'strh.w','r5, [r4, #0x37a]')]:need(thumb(va)==(m,o),'Thumb landmark '+hex(va))
idx=(0x160>>2)-9;slot=0x2c7b4+4*idx;entry=struct.unpack_from('<I',b,slot+0x200)[0]
need((idx,slot,entry,0x2c7b4+entry)==(0x4f,0x2c8f0,0x648,0x2cdfc),'F300:160 exact switch')
q=B/'firmware-platform-analysis-20261028db/private/pltf-extracted/tree/root/usr/lib/modules/5.4.261/kernel/qdf_tcon.ko';qb=q.read_bytes()
need(sha(qb)=='97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63','QDF module')
with q.open('rb') as fd:
 e=ELFFile(fd);s=e.get_section_by_name('.text');off=s['sh_offset'];md64=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 def arm64(va):
  i=next(md64.disasm(qb[off+va:off+va+4],va));return i.mnemonic,i.op_str
 for va,m,o in [(0x11098,'ldr','w1, [x19, #0x48]'),(0x1109c,'ldr','w2, [x19, #0x138]'),(0x110a0,'and','w0, w1, #0xfffffff7'),(0x110a8,'b.ne','#0x11188'),(0x11188,'cmp','w1, #8'),(0x11190,'cmp','w1, #7'),(0x11198,'ldr','w0, [x19, #0x1a8]'),(0x1119c,'cmp','w2, #1'),(0x111a0,'mov','w21, #2'),(0x111a4,'cbz','w0, #0x112a4'),(0x112a4,'b.eq','#0x110c8'),(0x112a8,'mov','w0, #0x3840'),(0x112b0,'mov','w0, #0x4074'),(0x112b4,'ccmp','w23, w0, #4, ne'),(0x112b8,'cset','w21, eq'),(0x112bc,'b','#0x110c8'),(0x11110,'str','w21, [x19, #0x13c]'),(0x11114,'bl','#0x10508'),(0x112f0,'str','w0, [x19, #0x134]'),(0x1132c,'bl','#0x11058')]:need(arm64(va)==(m,o),'A64 landmark '+hex(va))
for r in [2400,2398,5000,6000,12000,14400,16500]:
 for lag in [0,1,2]:need(chip14_nonmonitor_mode(r,lag)==(2 if lag==1 else int(r in (14400,16500))),'manual-model fixture')
for vals in [(-1,0),(True,0),(6000,False),(0x80000000,0)]:
 try:chip14_nonmonitor_mode(*vals)
 except ValueError:checks+=1
 else:raise ValueError('invalid fixture accepted')
w=(B/'ap-exco-input-snapshot-20261027w/capture-once/ordinary-ap-exco-prefix.bin').read_bytes()
need(sha(w)=='0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271','W ordinary snapshot pin')
initial=b[0x182200:0x182200+826]
need(sha(initial)=='c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf','packaged AP_EXCO initializer pin')
for o,v in [(0x2cc,1),(0x2ce,2),(0x2d0,0),(0x2d2,0),(0x2d4,0),(0x2d6,0),(0x2fc,0)]:
 need(struct.unpack_from('<H',w,o)[0]==v,'W field '+hex(o));need(struct.unpack_from('<H',initial,o)[0]==v,'initializer field '+hex(o))
need((struct.unpack_from('<H',w,0x2ce)[0]&1)==0,'frame branch mask is off in W')
need(struct.unpack_from('<H',w,0xe6)[0]==1 and struct.unpack_from('<H',initial,0xe6)[0]==0,'W is not the same complete initializer state')
for va,m,o in [(0x2cb50,'sub.w','r0, r6, #0x7c'),(0x2cb54,'ubfx','r7, r0, #2, #0x10'),(0x2cb58,'ubfx','r1, r4, #0, #0xa'),(0x2cb5c,'addw','r0, r5, #0x2ae'),(0x2cb60,'strh.w','r1, [r0, r7, lsl #1]')]:need(thumb(va)==(m,o),'NPC store '+hex(va))
for selector in range(0x7c,0xbc,4):
 slot=0x2c7b4+4*((selector>>2)-9);target=0x2c7b4+struct.unpack_from('<I',b,slot+0x200)[0]
 need(0x2cb32<=target<=0x2cb50 and (target&1)==0,'NPC switch entry')
 need(all(thumb(a)==('nop','') for a in range(target,0x2cb50,2)),'NPC fallthrough reaches common store')
print(json.dumps({'accepted':True,'checks':checks,'tv_actions':0,'network_actions':0,'oem_executions':0,'model_qualification':'manual transcription plus exact source landmarks, not ELF execution/full equivalence proof'}))
