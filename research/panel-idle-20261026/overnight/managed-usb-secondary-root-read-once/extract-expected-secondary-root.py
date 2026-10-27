#!/usr/bin/env python3
"""Decode image-1 reset row 0 and retain the fixed 64-byte read prediction."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
D5=BASE/'executing-image-identity-20261027e/verify-callback-initializers.py'
D5_SHA='19d52a1069e89f5e1c06ae78bfc5984b22fa8c3c89c56560cd8ea186b450c6f7'
DECODER=BASE.parent/'tcon-research/qd-rt-window-reset-output-reproduce.py'
DECODER_SHA='fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02'
CURRENT=BASE/'firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin'
CURRENT_SHA='f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562'
PACKAGE=BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
PACKAGE_SHA='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
BIAS=0x40200
CPU_ADDRESS=0x200004c0
DMA_ADDRESS=0x470004c0
LENGTH=64

def need(ok,why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def u32(raw,offset):
    return struct.unpack_from('<I',raw,offset)[0]

def inspect(raw,label,expected,decoder):
    need(len(raw)==0x500000 and sha(raw)==expected,label+' image pin')
    need(struct.unpack_from('<2I',raw,BIAS)==(0x20020000,0x369),label+' image1 vector')
    need(raw[BIAS+0x368:BIAS+0x36c]==bytes.fromhex('06488047'),label+' reset entry')
    anchor=0x174
    table=anchor+u32(raw,BIAS+anchor)
    end=anchor+u32(raw,BIAS+anchor+4)
    need(table==0x1d6a4 and end==0x1d734 and (end-table)%16==0,label+' scatter bounds')
    rows=[struct.unpack_from('<4I',raw,BIAS+table+16*i) for i in range((end-table)//16)]
    need(len(rows)==9 and rows[0]==(0x1d860,0x20000000,0x4f8,0x17c),label+' row0')
    need(rows[-1]==(0x1d95c,0x200004f8,0xdca4,0x1d8),label+' zero-fill row')
    ram,consumed=decoder.unpack(raw,BIAS+rows[0][0],rows[0][2])
    need(consumed==0x5db5b and len(ram)==0x4f8,label+' decoded extent')
    need(sha(ram)=='76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8',label+' row0 hash')
    start=CPU_ADDRESS-0x20000000
    initialized_tail=ram[start:]
    need(len(initialized_tail)==0x38,'row0 tail to 0x200004f8')
    block=initialized_tail+b'\0'*(LENGTH-len(initialized_tail))
    need(len(block)==LENGTH and sha(block)=='a43ca5561d3e7d98c1b8475c68857c35263532edd9b93f822582b466824d8df4',label+' block')
    gates={hex(offset):struct.unpack_from('<H',ram,offset)[0] for offset in (0x4c6,0x4c8,0x4ca)}
    need(gates=={'0x4c6':0,'0x4c8':0,'0x4ca':0},label+' gate initializers')
    root=u32(ram,0x4e0)
    need(root==0x20010000,label+' secondary root')
    return dict(label=label,image_sha256=sha(raw),image1_bias=hex(BIAS),scatter_table_va=hex(table),scatter_end_va=hex(end),
                row0=[hex(value) for value in rows[0]],row0_source_end_file=hex(consumed),row0_sha256=sha(ram),
                cpu_read_address=hex(CPU_ADDRESS),dma_read_candidate=hex(DMA_ADDRESS),read_length=LENGTH,
                block_sha256=sha(block),block_hex=block.hex(),block_sources=['row0 0x200004c0..0x200004f7','zero-fill row 0x200004f8..0x200004ff'],gate_halfwords=gates,
                root_pointer_slot_cpu='0x200004e0',root_value=hex(root),live_core_tag_branch_proved=False),block

def main():
    need(sha(D5.read_bytes())==D5_SHA,'D5 verifier pin')
    need(sha(DECODER.read_bytes())==DECODER_SHA,'decoder pin')
    spec=importlib.util.spec_from_file_location('decoder',DECODER)
    decoder=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    current,current_block=inspect(CURRENT.read_bytes(),'current',CURRENT_SHA,decoder)
    package,package_block=inspect(PACKAGE.read_bytes(),'packaged',PACKAGE_SHA,decoder)
    need(current_block==package_block,'current/package image1 prediction')
    output=dict(schema='secondary-root-image1-row0-prediction-v1',request=dict(target='0x101',dma_address=hex(DMA_ADDRESS),length=LENGTH,
                header_hex=struct.pack('<III',0x101,DMA_ADDRESS,LENGTH).hex()),reports=[current,package],
                expected_bytes_equal=True,secondary_namespace_established=False,active_core_tag_branch_proved=False,no_live_io=True)
    (HERE/'expected-secondary-root.bin').write_bytes(current_block)
    (HERE/'secondary-root-initializer.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(expected_sha256=sha(current_block),root_value=current['root_value'],gates=current['gate_halfwords'],
                          current_row0_sha256=current['row0_sha256'],package_equal=True),indent=2))

if __name__=='__main__':
    main()
