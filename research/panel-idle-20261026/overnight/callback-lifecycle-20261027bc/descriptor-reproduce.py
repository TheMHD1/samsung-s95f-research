#!/usr/bin/env python3
"""Offline reset-initializer and vector checks; no target operations."""
import hashlib, importlib.util, json, struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent.parent
PACKAGE=HERE.parent/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
DECODER=BASE/'tcon-research/qd-rt-window-reset-output-reproduce.py'
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(x):return hashlib.sha256(x).hexdigest()
def word(x,a):return struct.unpack_from('<I',x,a)[0]
p=PACKAGE.read_bytes()
need(len(p)==0x500000 and sha(p)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','package')
need(sha(DECODER.read_bytes())=='fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02','decoder')
s=importlib.util.spec_from_file_location('pinned_decoder',DECODER);d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
known,end=d.unpack(p,0x5da60,0x4f8)
need(end==0x5db5b and sha(known)=='76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8','decoder known answer')
row=struct.unpack_from('<4I',p,0x3e340)
need(row==(0x3e32c,0x20000000,0xf4c,0x17c),'scatter row0')
ram,end=d.unpack(p,row[0]+0x200,row[2])
need(end==0x3e961 and len(ram)==0xf4c and sha(ram)=='685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3','decoded initializer')
base=0x20000948;index=8;descriptor=base+20*index;offset=descriptor-row[1]
raw=ram[offset:offset+20]
need(raw.hex()=='2400225827000000000000000000000000000000','descriptor8 initializer')
mmio,irq,callback,claimed,tail=struct.unpack('<5I',raw)
need(mmio==0x58220024 and irq==39 and callback==claimed==tail==0,'descriptor fields')
image=p[0x200:0x40200]
vector_offset=4*(16+irq)
need(vector_offset==0xdc and word(image,vector_offset)==0x26a91,'stored standard vector slot')
need(sha(image[0x26a90:0x26aa6])=='28c670cec55d0aa7d8446777241eac6eb2e096d9fa3874671089820deefe8003','vector wrapper')
need(word(image,0x26aa8)==base,'wrapper table literal')
need(image[0x26a94:0x26a98].hex()=='d0f8a800' and image[0x26a9c:0x26aa0].hex()=='d0f8a810','callback field offset0xa8')
need(image[0x26aa0:0x26aa4].hex()=='a0308847','descriptor argument and BLX')
need(sha(image[0x132c0:0x13346])=='2e472ef163d2a285a67628abaef6195cdc824f781654e471f4e9659eb51e7a25','callback body')
need(image[0x132ca:0x132d2].hex()=='20680068c0f3c000','two dereferences then bit3 extraction')
print(json.dumps({'accepted':True,'schema':'descriptor8-source-identity-v1','source_sha256':sha(p),'descriptor_cpu':hex(descriptor),'descriptor_initializer_sha256':sha(raw),'pointed_word_address':hex(mmio),'stored_irq':irq,'stored_vector_slot':hex(vector_offset),'stored_vector_thumb_pointer':'0x26a91','callback_argument':'descriptor8 itself if selected wrapper/vector/registration active','callback_gate':'bit3 of current word reached through descriptor+0; packaged pointer58220024','live_identity_proved':False,'physical_causality_proved':False,'target_operations':0},sort_keys=True))
