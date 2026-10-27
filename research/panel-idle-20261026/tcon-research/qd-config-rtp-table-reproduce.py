#!/usr/bin/env python3
"""Reproduce the selected profile's config-table/RT binding offline only."""
from pathlib import Path
import hashlib, json, struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
EXPECTED='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
b=SOURCE.read_bytes()
def need(ok,msg):
    if not ok: raise ValueError(msg)
need(len(b)==5242880 and hashlib.sha256(b).hexdigest()==EXPECTED,'selected asset mismatch')
def word(k):return struct.unpack_from('<I',b,k)[0]
def text(k):return b[k:b.index(b'\0',k)].decode('ascii')
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_LITTLE_ENDIAN)
def ins(f):
    i=next(md.disasm(b[f:f+4],f-0x200,count=1),None)
    need(i is not None,'no instruction at '+hex(f))
    return i.mnemonic,i.op_str
for f,expect in {
  0x63b2:('bl','#0xc04'), 0x644c:('ldr','r1, [r1, #4]'),
  0x644e:('ldr','r2, [sp, #0xa4]'), 0x6458:('bl','#0xa72'),
  0x6520:('ldr','r1, [r1, #0xc]'),0x6528:('bl','#0xa72'),
  0x657c:('push.w','{r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}'),
  0x65c0:('ldr','r0, [r0, #8]'),0x65d0:('ldr','r0, [r0, #0xc]'),
  0x65f0:('ldr','r0, [r0, #4]'),0x65f6:('bl','#0xa72'),
  0x7780:('bl','#0x6190'),0x77f4:('bl','#0x6190'),
  0x39c5e:('bl','#0x7474'),0x7692:('bl','#0x7544')}.items():
    need(ins(f)==expect,'instruction mismatch '+hex(f)+': '+repr(ins(f)))
need(word(0x6570)==word(0x660c)==0x3cabc,'table pointer mismatch')
rows=[]
for index in range(21):
    f=0x3ccbc+index*0x1c
    w=struct.unpack_from('<7I',b,f)
    rows.append(dict(index=index,file_offset=f,name=text(w[0]+0x200),name_va=w[0],first_destination=w[1],first_limit=w[2],second_destination=w[3],second_limit=w[4],first_logical=w[5],second_logical=w[6]))
r=rows[14]
need(r['name']=='AP_RTP' and r['first_destination']==0x47012400 and r['first_limit']==0x100 and r['second_destination']==0x47010000 and r['second_limit']==0x2400 and r['first_logical']==0x210000 and r['second_logical']==0x210400,'RTP entry mismatch')
base=0x80000
need(word(base)==57,'configuration header count mismatch')
record=0x86000
need(text(record)=='AP_RTP' and word(record+0x20)==4,'RTP metadata name/type mismatch')
fields={hex(o):word(record+o) for o in (0x20,0x24,0x28,0x2c,0x6c,0xac,0xf0,0xf4,0x134,0x174)}
need(fields=={'0x20':4,'0x24':0x210000,'0x28':1,'0x2c':0x103800,'0x6c':0,'0xac':0x100,'0xf0':1,'0xf4':0x103a00,'0x134':0x400,'0x174':0x2400},'RTP metadata schema mismatch')
a=base+fields['0x2c']; z=base+fields['0xf4']
need(a==0x183800 and z==0x183a00,'source arithmetic mismatch')
parameters=[]
for off in (0x2400,0x240a,0x240e,0x2410,0x2436,0x244a,0x244c,0x244e,0x2450,0x2452,0x2454,0x2466,0x2468,0x2484,0x24aa,0x24ac,0x24b4):
    f=a+off-0x2400
    parameters.append(dict(object_offset=off,source_file_offset=f,fixed_destination=0x47010000+off,low_byte=b[f],halfword=struct.unpack_from('<H',b,f)[0]))
ranges=[(0x3ccbc,0x3cf08),(record,record+0x200),(a,a+0x100),(z,z+0x2400),(0x6390,0x657c),(0x657c,0x6610),(0x70e4,0x715c),(0x7744,0x782c),(0x39c58,0x39c66)]
report={'source':str(SOURCE),'source_sha256':EXPECTED,'address_convention':'image0 VA=FILE-0x200; absolute RAM unchanged','table':rows,'rtp_metadata':fields,'conditional_package_base':base,'parameter_first':a,'parameter_second':z,'rtp_parameters':parameters,'slice_hashes':[{'file_start':s,'file_end_exclusive':e,'sha256':hashlib.sha256(b[s:e]).hexdigest()} for s,e in ranges],'limits':['selected-package source/layout and static successful copy path only','current controller flash equality and runtime load not established','logical generic read route is not proven exposed over host I2C','no target action or emulation performed']}
print(json.dumps(report,indent=2))
