#!/usr/bin/env python3
"""Check the CPU/DMA address distinction in the acquired first image."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_MCLASS,CS_MODE_LITTLE_ENDIAN

HERE=Path(__file__).resolve().parent
BASE=HERE.parent

def need(ok,why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    raw=(BASE/'firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin').read_bytes()
    need(sha(raw)=='f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562','current dump')
    md=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS|CS_MODE_LITTLE_ENDIAN)
    def decode(va,size):
        return {i.address:(i.mnemonic,i.op_str,i.bytes.hex()) for i in md.disasm(raw[va+0x200:va+0x200+size],va)}
    rows={**decode(0x9a48,0x26),**decode(0x28ed0,0x1e)}
    def exact(va,mnemonic,operands):
        need(rows[va][:2]==(mnemonic,operands),'instruction '+hex(va))
    exact(0x9a48,'mov','r1, r0')
    exact(0x9a4a,'ldr','r0, [pc, #0x24]')
    exact(0x9a4c,'ldr','r2, [r0]')
    exact(0x9a4e,'cmp.w','r1, #0x20000000')
    exact(0x9a52,'blo','#0x9a6a')
    exact(0x9a54,'ldr','r0, [pc, #0x1c]')
    exact(0x9a56,'cmp','r1, r0')
    exact(0x9a58,'bhs','#0x9a6a')
    exact(0x9a5a,'cmp','r2, #0xa')
    exact(0x9a5c,'bne','#0x9a64')
    exact(0x9a5e,'add.w','r0, r1, #0x25000000')
    exact(0x9a64,'add.w','r0, r1, #0x27000000')
    exact(0x9a6a,'mov','r0, r1')
    need(struct.unpack_from('<I',raw,0x9a70+0x200)[0]==0xe00fdfdc,'core-tag literal')
    need(struct.unpack_from('<I',raw,0x9a74+0x200)[0]==0x20200000,'upper bound')
    exact(0x28ed4,'ldr','r1, [pc, #0xa4]')
    exact(0x28eda,'bl','#0x9bbc')
    exact(0x28ee2,'ldr','r0, [pc, #0x9c]')
    exact(0x28ee6,'ldr','r2, [r0]')
    exact(0x28eea,'bl','#0x803c')
    need(struct.unpack_from('<I',raw,0x28f7c+0x200)[0]==0x20001bc0,'CPU response buffer')
    need(struct.unpack_from('<I',raw,0x28f80+0x200)[0]==0x20000540,'DMA pointer slot')
    source=BASE.parent/'tcon-research/qd-rt-window-reset-output-reproduce.py'
    need(sha(source.read_bytes())=='fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02','decoder')
    spec=importlib.util.spec_from_file_location('decoder',source)
    decoder=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    ram,end=decoder.unpack(raw,0x3e294,0xf3c)
    need(sha(ram)=='5f2ee00e130c82c366b7eb328f32f150b362112c4207699056ca5aa0a8519600','actual row0')
    dma=struct.unpack_from('<I',ram,0x540)[0]
    need(dma==0x45001bc0==0x20001bc0+0x25000000,'initialized CPU/DMA buffer correspondence')
    result=dict(schema='controller-cpu-dma-alias-proof-v1',image_sha256=sha(raw),mapper_va='0x9a48',core_tag_register='0xe00fdfdc',
                cpu_range=['0x20000000','0x20200000'],core_tag_0xa_addend='0x25000000',other_tag_addend='0x27000000',
                cpu_buffer='0x20001bc0',initialized_usb_dma_buffer=hex(dma),cpu_callback_read='0x20000580',planned_dma_callback_read='0x45000580',
                instructions={hex(va):dict(mnemonic=m,operands=o,bytes=b,file_offset=hex(va+0x200)) for va,(m,o,b) in rows.items()},
                raw_cpu_address_zero_result_identifies_image=False,live_core_tag_register_observed=False,whole_image_identity_proved=False)
    (HERE/'dma-alias-proof.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='instructions'},indent=2))

if __name__=='__main__':
    main()
