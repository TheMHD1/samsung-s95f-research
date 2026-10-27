#!/usr/bin/env python3
"""Offline instruction checks against actual retained sector replies."""
import hashlib
import json
from pathlib import Path
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

HERE = Path(__file__).resolve().parent

def need(ok,why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    expected = {0x28a00:'115e870ba1431deaab2a3920ef022a5ce35672d38fbb6cbd84716f475c2e34d5',
                0x28e00:'28e1db6bad575359da47c6c553a4cca7d2923aabfd804bfcea8abd76f5bdca98',
                0x29000:'8cd7aa864b8f0caa156df3d2498f6fa2b3a7f88d00136872d0501e04cfbac50d'}
    sectors = {}
    for address,digest in expected.items():
        raw = (HERE/f'sector-{address:06x}/returned-sector.bin').read_bytes()
        need(len(raw)==512 and sha(raw)==digest,'sector pin')
        sectors[address]=raw
    def readva(va,size):
        file=va+0x200
        address=file&~511
        need(address in sectors and file-address+size<=512,'captured range')
        return sectors[address][file-address:file-address+size]
    md=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS|CS_MODE_LITTLE_ENDIAN)
    slices=[(0x28d44,0x66),(0x28918,0x40),(0x28eb2,0x3c)]
    rows={}
    for va,size in slices:
        rows.update({i.address:(i.mnemonic,i.op_str,i.bytes.hex()) for i in md.disasm(readva(va,size),va)})
    def exact(va,mnemonic,operands):
        need(rows[va][:2]==(mnemonic,operands),f'instruction {va:x}: {rows[va]}')
    exact(0x28d44,'ldrh','r0, [r5, #0x1e]')
    exact(0x28d46,'cbnz','r0, #0x28d7c')
    exact(0x28d48,'ldr','r0, [r4, #0xc]')
    exact(0x28d4a,'cmp','r0, #4')
    exact(0x28d4c,'bne','#0x28d7c')
    exact(0x28d72,'mov.w','r0, #0x200')
    exact(0x28d76,'ldr','r1, [pc, #0x200]')
    exact(0x28d78,'str','r0, [r1]')
    exact(0x28da2,'mov.w','r0, #0x6000')
    exact(0x28da6,'ldr','r1, [pc, #0x1d0]')
    exact(0x28da8,'str','r0, [r1]')
    need((0x28d76+4)//4*4+0x200==0x28f78 and (0x28da6+4)//4*4+0x1d0==0x28f78,'shared cap literal')
    need(struct.unpack('<I',readva(0x28f78,4))[0]==0x20000548,'current cap location')
    exact(0x28918,'ldr','r0, [r4, #8]')
    exact(0x2891e,'subs','r0, r0, r1')
    exact(0x28920,'str','r0, [r4, #8]')
    exact(0x2892a,'str','r0, [r4, #4]')
    exact(0x2892e,'cbnz','r0, #0x2896e')
    exact(0x2894c,'movs','r0, #6')
    exact(0x2894e,'str','r0, [r4, #0xc]')
    exact(0x28954,'bl','#0x29264')
    exact(0x28eb4,'cmp','r0, #3')
    exact(0x28eda,'bl','#0x9bbc')
    exact(0x28eea,'bl','#0x803c')
    profile=(HERE.parent/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    need(sha(profile)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','package pin')
    need(readva(0x28d44,0x66)==profile[0x28fe0+0x200:0x28fe0+0x200+0x66],'local cap path exact package overlap')
    report=dict(schema='current-returned-protocol-check-v1',sector_hashes={hex(k):v for k,v in expected.items()},
                instructions={hex(va):dict(mnemonic=m,operands=o,bytes=b,file_offset=hex(va+0x200)) for va,(m,o,b) in rows.items()},
                op3_cap=24576,cap_ram='0x20000548',current_read_leaf_call_target='0x9bbc',current_usb_in_scheduler_call_target='0x803c',current_rearm_call_target='0x29264',callee_bodies_verified=False,
                comparison_local_shift='-0x29c',global_relocation_rule=False,current_executing_identity_proved=False,underlying_storage_result_observed=False)
    (HERE/'current-protocol-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='instructions'},indent=2))

if __name__=='__main__':
    main()
