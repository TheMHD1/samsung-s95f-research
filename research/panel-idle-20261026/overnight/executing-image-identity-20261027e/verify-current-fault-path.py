#!/usr/bin/env python3
"""Reproduce stored-code coordinates and exact fault-state RAM anchors; offline."""
from pathlib import Path
import hashlib, json, struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
SOURCES={
 'current': ('firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin','f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562'),
 'packaged': ('selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin','bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0')}
SLICES={
 'current':{'eeprom':(0x97d0,0x9852),'feedback':(0x9950,0x99e8),'live':(0x21254,0x21292)},
 'packaged':{'eeprom':(0x97e8,0x986a),'feedback':(0x9968,0x9a00),'live':(0x214d4,0x21512),
 'common_error':(0xb660,0xb6fa),'selector_setter':(0x2b764,0x2b77a),'root_getters':(0xe670,0xe680)}}
def need(v,why):
 if not v:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()
m=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS)
report={'schema':'fault-code-coordinate-anchors-v2','runtime_code_identity_proved':False,'images':{}}
loaded={}
for name,(rel,pin) in SOURCES.items():
 raw=(BASE/rel).read_bytes();need(len(raw)==0x500000 and sha(raw)==pin,'whole image identity '+name);loaded[name]=raw
 rows={}
 for label,(start,end) in SLICES[name].items():
  body=raw[start+0x200:end+0x200]
  rows[label]={'va_start':hex(start),'va_end_exclusive':hex(end),'file_start':hex(start+0x200),'file_end_exclusive':hex(end+0x200),'sha256':sha(body),'instructions':[{'va':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str} for i in m.disasm(body,start)]}
 report['images'][name]={'sha256':pin,'slices':rows}
p=loaded['packaged']
def word(va):return struct.unpack_from('<I',p,va+0x200)[0]
def ins(va,size,mnem,oper):
 i=next(m.disasm(p[va+0x200:va+0x200+size],va));need(i.address==va and i.size==size and i.mnemonic==mnem and i.op_str==oper,'instruction '+hex(va))
need(word(0xe674)==0x2000f0e0,'common root literal');need(word(0xe67c)==0x2000ff14,'second root literal');need(word(0xef98)==0x47010000,'shared RT root literal')
ins(0xe670,2,'ldr','r0, [pc, #0]');ins(0xe678,2,'ldr','r0, [pc, #0]')
ins(0xb668,4,'bl','#0xe678');ins(0xb6a6,4,'bl','#0x2b764');ins(0xb6be,4,'bl','#0xe670')
ins(0xb6c2,2,'ldrh','r0, [r0]');ins(0xb6c4,4,'movw','r1, #0x1234');ins(0xb6cc,2,'ldrh','r0, [r6]');ins(0xb6ce,4,'movw','r1, #0xabcd')
ins(0x2b768,4,'bl','#0xe670');ins(0x2b76c,4,'add.w','r5, r0, #0x10');ins(0x2b776,2,'strh','r0, [r5]')
ins(0x214dc,4,'movw','r0, #0x240a');ins(0x214e0,2,'ldrb','r0, [r0, r4]');ins(0x214f0,2,'movs','r0, #0x10');ins(0x214f2,4,'bl','#0xb660')
report['verified_packaged_ram_anchors']={'common_root_cpu':'0x2000f0e0','second_root_cpu':'0x2000ff14','common_selector_offset':'0x10','common_guard':'0x1234','second_guard':'0xabcd','rt_root_fixed_view':'0x47010000'}
(HERE/'fault-path-static-anchors.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'verified':True,'images':{k:v['sha256'] for k,v in report['images'].items()},'ram_anchors':report['verified_packaged_ram_anchors'],'runtime_code_identity_proved':False},indent=2))
