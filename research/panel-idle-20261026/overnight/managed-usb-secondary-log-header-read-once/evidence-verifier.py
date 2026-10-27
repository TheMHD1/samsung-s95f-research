#!/usr/bin/env python3
"""Check exact log-ring dataflow in retained controller bytes; offline only."""
from pathlib import Path
import hashlib, struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
BASE=Path(__file__).resolve().parent.parent
b=(BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
def need(v,why):
 if not v:raise ValueError(why)
need(hashlib.sha256(b).hexdigest()=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','whole package identity')
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS)
def ins(va,size,mnem,ops,bias=0x40200):
 item=next(md.disasm(b[va+bias:va+bias+size],va))
 need(item.size==size and item.mnemonic==mnem and item.op_str==ops,'instruction '+hex(va))
def word(va,bias=0x40200):return struct.unpack_from('<I',b,va+bias)[0]
for label,a,z,h in [('setter',0xc1e0,0xc212,'f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102'),('sink',0x1b8c8,0x1b940,'47abdf7963385a87473920daae5212943303054ceb9ba3df92c3c31928fb545e')]:
 raw=b[a+0x40200:z+0x40200];need(hashlib.sha256(raw).hexdigest()==h,label+' slice')
 print(label,'VA',hex(a),hex(z),'FILE',hex(a+0x40200),hex(z+0x40200),h)
for args in [(0xc204,2,'adr','r0, #0xc'),(0xc20c,2,'adr','r0, #4'),(0xc206,4,'bl','#0x1b8c8'),(0xc20e,4,'bl','#0x1b8c8'),
 (0x1b8d6,4,'movw','r0, #0x2406'),(0x1b8da,2,'ldrb','r0, [r0, r5]'),(0x1b8dc,4,'and','r0, r0, #1'),(0x1b8e0,2,'cbz','r0, #0x1b938'),
 (0x1b8fc,2,'ldr','r0, [pc, #0x44]'),(0x1b900,4,'mov.w','r1, #0x3c00'),(0x1b904,4,'udiv','r2, r0, r1'),(0x1b908,4,'mls','r0, r1, r2, r0'),
 (0x1b90e,2,'str','r0, [r1]'),(0x1b91e,2,'str','r0, [r3]'),(0x1b920,4,'add.w','r0, r3, #0xc'),(0x1b924,2,'strb','r1, [r0, r2]'),
 (0x1b92a,2,'blt','#0x1b8fc'),(0x1b930,2,'str','r0, [r1, #8]')]:ins(*args)
need(((0xc204+4)&~3)+0xc==((0xc20c+4)&~3)+4==0xc214,'ADRs share literal')
need(b[0xc214+0x40200:0xc214+0x40200+12]==b'rtp_act_%d\n\0','exact log literal')
need(word(0x1b944)==0x20200000,'secondary ring index base')
for args in [(0x393b4,4,'mov.w','r1, #0xc00'),(0x393b8,4,'udiv','r2, r0, r1'),(0x393d6,2,'strb','r1, [r0, r2]'),(0x393dc,2,'blt','#0x393b0')]:ins(*args,bias=0x200)
need(word(0x393ec,0x200)==0x20000e5c and word(0x393f0,0x200)==0x20205000,'main ring index and buffer')
need(word(0x30b0)==0x20200000,'mapper exclusive upper bound')
ins(0x308a,4,'cmp.w','r1, #0x20000000')
ins(0x3094,2,'bhs','#0x30a6')
ins(0x3096,2,'cmp','r2, #0xa')
ins(0x3098,2,'bne','#0x30a0')
ins(0x309a,4,'add.w','r0, r1, #0x25000000')
ins(0x30a0,4,'add.w','r0, r1, #0x27000000')
ins(0x30a6,2,'mov','r0, r1')
def translated(addr,tag):return addr+(0x25000000 if tag==0xa else 0x27000000) if 0x20000000<=addr<0x20200000 else addr
for tag in (0xa,0x9):
 need(translated(0x20200000,tag)==0x20200000 and translated(0x2020000c,tag)==0x2020000c,'ring outside mapper range')
 need(translated(0x201fffff,tag)==(0x451fffff if tag==0xa else 0x471fffff),'last mapped byte')
print('PASS: exact calls, gate, literal, per-byte wrap, stores, main-ring anchors and mapper boundary; runtime visibility unproved')
