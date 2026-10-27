#!/usr/bin/env python3
"""Locate the current scatter table from reset code and decode callback bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_MCLASS,CS_MODE_LITTLE_ENDIAN

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
DECODER=BASE.parent/'tcon-research/qd-rt-window-reset-output-reproduce.py'
DECODER_SHA='fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02'

def need(ok,why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def u32(raw,file):
    return struct.unpack_from('<I',raw,file)[0]

def inspect(raw,label,expected_sha,decoder):
    need(len(raw)==0x500000 and sha(raw)==expected_sha,'image pin')
    need(u32(raw,0x204)==0x345,'reset vector')
    md=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS|CS_MODE_LITTLE_ENDIAN)
    instructions={i.address:(i.mnemonic,i.op_str,i.bytes.hex()) for i in md.disasm(raw[0x344:0x374],0x144)}
    reset={i.address:(i.mnemonic,i.op_str,i.bytes.hex()) for i in md.disasm(raw[0x544:0x54c],0x344)}
    need(reset[0x344][:2]==('ldr','r0, [pc, #0x18]') and reset[0x346][:2]==('blx','r0'),'system-init before main')
    need(reset[0x348][:2]==('ldr','r0, [pc, #0x18]') and reset[0x34a][:2]==('bx','r0') and u32(raw,0x564)==0x141,'main entry')
    need(raw[0x340:0x344]==bytes.fromhex('00f002f8'),'main calls scatter init148')
    for va,mnemonic,operands in ((0x148,'adr','r0, #0x28'),(0x14a,'ldm.w','r0, {sl, fp}'),(0x14e,'add','sl, r0'),(0x150,'add','fp, r0'),(0x162,'ldm.w','sl!, {r0, r1, r2, r3}'),(0x172,'bx','r3')):
        need(instructions[va][:2]==(mnemonic,operands),'scatter instruction '+hex(va))
    anchor=0x174
    table=anchor+u32(raw,anchor+0x200)
    end=anchor+u32(raw,anchor+0x204)
    need(0x200<table<end<0x40000 and (end-table)%16==0,'bounded scatter table')
    rows=[struct.unpack_from('<4I',raw,table+0x200+16*i) for i in range((end-table)//16)]
    need(len(rows)==12 and rows[0][1]==0x20000000 and rows[0][3]==0x17c,'row0 initialized RAM')
    need(rows[0][2]>=0x5c0 and rows[0][2]<=0x2000,'callback range inside initialized row0')
    ram,consumed=decoder.unpack(raw,rows[0][0]+0x200,rows[0][2])
    block=ram[0x580:0x5c0]
    callbacks=struct.unpack_from('<8I',block,12)
    need(all(pointer==0 or (pointer&1 and (pointer&~1)<0x40000) for pointer in callbacks),'bounded Thumb callback pointers')
    (HERE/f'expected-{label}-callbacks.bin').write_bytes(block)
    needle=struct.pack('<I',0x2000058c)
    hits=[hex(i) for i in range(0x200,0x40000-3) if raw[i:i+4]==needle]
    return dict(label=label,image_sha256=sha(raw),scatter_table_va=hex(table),scatter_table_file=hex(table+0x200),scatter_end_va=hex(end),
                rows=[[hex(v) for v in row] for row in rows],row0_source_end_file=hex(consumed),row0_sha256=sha(ram),
                block_sha256=sha(block),block_hex=block.hex(),callback_table_ram='0x2000058c',callbacks=[hex(v) for v in callbacks],
                table_pointer_literal_file_hits=hits,first12_bytes_may_be_runtime_state=True,live_ram_not_observed=True,
                instructions={hex(k):v for k,v in {**instructions,**reset}.items()})

def main():
    need(sha(DECODER.read_bytes())==DECODER_SHA,'known-answer decoder source')
    spec=importlib.util.spec_from_file_location('decoder',DECODER)
    decoder=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    current=(BASE/'firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin').read_bytes()
    package=(BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    need(current[0x37c:0x3d8]==package[0x37c:0x3d8],'identical decompression-handler body')
    reports=[inspect(current,'current','f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562',decoder),
             inspect(package,'packaged','bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0',decoder)]
    need(reports[0]['callbacks']!=reports[1]['callbacks'],'discriminating callback predictions')
    output=dict(schema='current-vs-packaged-callback-initializers-v1',read_address='0x20000580',read_length=64,reports=reports,
                executing_identity_established=False,no_live_io=True)
    (HERE/'callback-initializers.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({r['label']:dict(scatter_table_file=r['scatter_table_file'],row0_sha256=r['row0_sha256'],callbacks=r['callbacks']) for r in reports},indent=2))

if __name__=='__main__':
    main()
