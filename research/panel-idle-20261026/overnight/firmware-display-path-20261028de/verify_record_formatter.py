#!/usr/bin/env python3
"""Offline exact-source checks for record interpretation; no target operations."""
import hashlib,json,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
D=Path(__file__).resolve().parent;B=D.parent;checks=0
P=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
b=P.read_bytes();pin='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
def need(ok,label):
 global checks
 checks+=1
 if not ok:raise ValueError(label)
need(hashlib.sha256(b).hexdigest()==pin,'package pin');im=b[0x40200:0x60200]
d=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
def op(a):
 i=next(d.disasm(im[a:a+4],a));return i.mnemonic,i.op_str
landmarks=[
(0xc5d4,'mov','r7, r0'),(0xc5d6,'mov','r6, r1'),(0xc5d8,'mov','r8, r2'),(0xc5da,'mov','sb, r3'),(0xc5dc,'ldrd','sl, r4, [sp, #0x38]'),
(0xc652,'ldr','r0, [pc, #0x234]'),(0xc654,'ldrh','r0, [r0]'),(0xc656,'add','r0, r6'),(0xc658,'uxth','r1, r0'),
(0xc666,'strh.w','r1, [r0, r2, lsl #1]'),(0xc676,'strh.w','r8, [r0, r1, lsl #1]'),(0xc686,'strh.w','sb, [r0, r1, lsl #1]'),(0xc696,'strh.w','r7, [r0, r1, lsl #1]'),(0xc6a6,'strh.w','sl, [r0, r1, lsl #1]'),
(0xc604,'bhi','#0xc6de'),(0xc64c,'cmp.w','r0, #0x200'),(0xc650,'bhs','#0xc6aa'),(0xc6b8,'str.w','r0, [r2, r1, lsl #2]'),(0xc718,'strh.w','r1, [r2, r0, lsl #1]'),(0xc77e,'ldr','r2, [pc, #0xcc]'),(0xc780,'str.w','r0, [r2, r1, lsl #2]'),
(0xbbc0,'mov','r8, r0'),(0xbbc2,'mov','r7, r1'),(0xbbc4,'mov','r4, r2'),(0xbbc6,'mov','sb, r3'),(0xbc20,'cmp','r8, r7'),(0xbc24,'sub.w','r0, r7, r8'),(0xbc38,'sub.w','r0, r8, r7'),
(0xbc70,'mov','r0, r7'),(0xbc6e,'mov','r1, r4'),(0xbc6c,'mov','r2, sb'),(0xbc72,'ldr','r3, [sp, #0x30]'),(0xbc74,'bl','#0xc5d0'),(0xbca8,'bl','#0xc5d0'),(0xbcde,'bl','#0xc5d0'),(0xbd1e,'bl','#0xc5d0'),(0xbc9a,'movs','r1, #0'),(0xbc9c,'strd','r1, r0, [sp]'),
(0xbd60,'mov','sl, r2'),(0xbd62,'mov','r6, r3'),(0xbe3a,'ldr.w','r0, [sp, #0xf1c]'),(0xbe3e,'add.w','r7, r0, fp'),(0xbe42,'ldr.w','r0, [sp, #0xf20]'),(0xbe46,'add.w','r8, r0, fp'),(0xbe4a,'ldr.w','r0, [r8]'),(0xbed0,'ldrh.w','r1, [r3, r4, lsl #1]'),(0xbed4,'ldr','r3, [r7]'),(0xbeda,'mov','r3, sl'),(0xbece,'str','r6, [sp]'),(0xbedc,'bl','#0xbbbc'),
(0xb7ee,'mov','r5, r0'),(0xb7f0,'mov','r6, r1'),(0xb840,'mov','r3, r6'),(0xb842,'mov','r2, r5'),(0xb84c,'bl','#0xbd58'),(0xb874,'bl','#0xbd58'),(0xb88a,'bl','#0xbd58'),(0xb800,'strh.w','r1, [r2, r0, lsl #1]'),(0xb808,'cmp','r0, #6'),
(0xca8c,'str.w','r1, [r2, r0, lsl #2]'),(0xca92,'strh.w','r1, [r2, r0, lsl #1]'),(0xcabe,'cmp','r0, #6'),(0xb964,'bl','#0xca84'),(0xcb50,'bl','#0xca84'),
(0xb8cc,'strh.w','r2, [r1, r0, lsl #1]'),(0xb8d4,'strh.w','r2, [r1, r0, lsl #1]'),(0xb8dc,'strh.w','r2, [r1, r0, lsl #1]'),(0xb8e2,'cmp.w','r0, #0x200'),
(0xcb8c,'strh.w','r1, [r0, r4, lsl #1]'),(0xcb94,'strh.w','r1, [r0, r4, lsl #1]'),(0xcb9c,'strh.w','r1, [r0, r4, lsl #1]'),(0xcba2,'cmp.w','r4, #0x200'),(0xcbac,'strh','r0, [r1]')]
for a,m,o in landmarks:need(op(a)==(m,o),'instruction '+hex(a))
for a,v in [(0xc888,0x200004c0),(0xc854,0x200004be),(0xc84c,0x2000ba28),(0xc88c,0x2000ba40),(0xb890,0x2000ba40),(0xb894,0x20000494),(0xb898,0x20000498),(0xb8a0,0x20015000),(0xb8a4,0x20015f10),(0xcafc,0x2000ba28),(0xcb00,0x2000ba40),(0xcbd0,0x200004c0)]:need(struct.unpack_from('<I',im,a)[0]==v,'literal '+hex(a))
need(im[0xc858:0xc888].split(b'\0')[0]==b'[RTP %3d]RGB:%d x:%4d y:%4d/c:%4d/diff:%d/m:%s\n','exact formatter labels')
# Signed difference is lost: two distinct selected A inputs produce identical B/diff.
need(abs(100-600)==abs(1100-600)==500,'difference sign ambiguity')
need(((65530+10)&0xffff)==4,'x narrowing ambiguity')
need([0x47010000+x for x in (0x1000,0x1400,0x1800,0x1c00,0x2000)]==[0x47011000,0x47011400,0x47011800,0x47011c00,0x47012000],'five alias addresses')
ranges=[('formatter',0xc5d0,0x2d4),('comparator',0xbbbc,0x172),('unpacker',0xbd58,0x2d8),('dispatch',0xb7ec,0xbc),('frame_end',0xb8a8,0x130),('ordinal_reset',0xca84,0x78),('record_clear',0xcb2c,0x84)]
print(json.dumps({'accepted':True,'checks':checks,'source_sha256':pin,'ranges':[{'label':n,'image1_va':hex(a),'file_offset':hex(a+0x40200),'length':z,'sha256':hashlib.sha256(im[a:a+z]).hexdigest()} for n,a,z in ranges],'qualification':'manual dataflow with exact landmarks; not live execution attestation, completeness proof or atomic record sampling','tv_actions':0,'network_actions':0,'oem_executions':0},sort_keys=True))
