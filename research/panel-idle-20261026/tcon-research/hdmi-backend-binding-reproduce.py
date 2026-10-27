#!/usr/bin/env python3
"""Offline landmarks for libhdmi-control's input-backend loader."""
from pathlib import Path
import argparse, hashlib, struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
LIB=ROOT/'overnight/serdes-hdmi-control-copy-20261026/libhdmi-control.so.0.1'
SHA='067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410'
def require(x,m):
    if not x:raise ValueError(m)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write-disassembly',action='store_true');a=ap.parse_args()
    require(hashlib.sha256(LIB.read_bytes()).hexdigest()==SHA,'library hash')
    with LIB.open('rb') as h:
        e=ELFFile(h); sy={x.name:x for x in e.get_section_by_name('.dynsym').iter_symbols() if x.name}
        text=e.get_section_by_name('.text'); ro=e.get_section_by_name('.rodata')
        for n,v,size in [('ppi_hdmi_input_control_get_backend_data',0x47e5f815,12),('ppi_hdmi_input_control_get_backend_data_address',0x47e5f821,160),('ppi_hdmi_input_control_get_backend',0x47e5f8c1,288),('ppi_hdmi_input_control_set_source',0x47e60701,184),('ppi_hdmi_input_control_set_foreground',0x47e60595,180),('ppi_hdmi_input_control_set_background',0x47e604e1,180)]:
            s=sy[n];require((s['st_value'],s['st_size'])==(v,size),n)
        input_path=b'/prd/usr/lib/libhdmi-input-control-impl-sec.so\0'
        require(input_path in ro.data(),'input implementation literal')
        require(b'/prd/usr/lib/libhdmi-control-impl-sec.so\0' in ro.data(),'control implementation literal')
        cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB);spans=[]
        for n,lo,hi in [('get_backend_data',0x47e5f814,0x47e5f820),('get_backend_data_address',0x47e5f820,0x47e5f8c0),('get_backend',0x47e5f8c0,0x47e5f9b8),('set_source',0x47e60700,0x47e60798),('set_foreground',0x47e60594,0x47e60628),('set_background',0x47e604e0,0x47e60574)]:
            raw=text.data()[lo-text['sh_addr']:hi-text['sh_addr']];ins=list(cs.disasm(raw,lo));require(sum(i.size for i in ins)==len(raw),n+' decode')
            spans.append((n,ins))
        rows={i.address:(i.mnemonic,i.op_str) for _,z in spans for i in z}
        for ad,mn,op in [(0x47e5f814,'ldr','r0, [pc, #4]'),(0x47e5f816,'add','r0, pc'),(0x47e5f850,'blx','#0x47e33890'),(0x47e5f856,'movs','r0, #0x88'),(0x47e5f858,'blx','#0x47e33854'),(0x47e5f860,'str','r0, [r6, #4]'),(0x47e5f862,'blx','#0x47e32f60'),(0x47e5f868,'str','r6, [r5]'),(0x47e5f8ec,'ldr.w','r8, [pc, #0xd8]'),(0x47e5f8f6,'add','r8, pc'),(0x47e5f90c,'mov','r0, r8'),(0x47e5f910,'blx','#0x47e331b0'),(0x47e60724,'ldr','r3, [r3, #0x3c]'),(0x47e6073c,'bx','r3'),(0x47e605b6,'ldr','r3, [r3, #0x44]'),(0x47e605cc,'bx','r3'),(0x47e60502,'ldr','r3, [r3, #0x48]'),(0x47e60518,'bx','r3')]:require(rows.get(ad)==(mn,op),f'landmark {ad:x}')
        # The path literal is loaded into r8 before r8 is moved into dlopen r0.
        lit=struct.unpack_from('<i',text.data(),0x47e5f9c8-text['sh_addr'])[0]
        require((0x47e5f8f6+4+lit)&0xffffffff==ro['sh_addr']+ro.data().index(input_path),'loader literal target')
        rel=e.get_section_by_name('.rel.plt'); dyn=e.get_section(rel['sh_link'])
        matches=[r for r in rel.iter_relocations() if r['r_offset']==0x47e82aa0]
        require(len(matches)==1 and dyn.get_symbol(matches[0]['r_info_sym']).name=='dlopen','dlopen GOT relocation')
        plt=e.get_section_by_name('.plt'); arm=Cs(CS_ARCH_ARM,CS_MODE_ARM)
        plt_raw=plt.data()[0x47e331b0-plt['sh_addr']:0x47e331bc-plt['sh_addr']]
        ai=list(arm.disasm(plt_raw,0x47e331b0));require(sum(i.size for i in ai)==12,'dlopen veneer decode')
        require([(i.mnemonic,i.op_str) for i in ai]==[('add','ip, pc, #0, #12'),('add','ip, ip, #0x4f000'),('ldr','pc, [ip, #0x8e8]!')],'dlopen veneer')
    out=''.join('\n## '+n+'\n'+''.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}\n' for i in z) for n,z in spans)
    out+='\n## dlopen_veneer_arm\n'+''.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}\n' for i in ai)
    p=HERE/'hdmi-backend-binding-v2.disasm'
    if a.write_disassembly:
        with p.open('x') as f:f.write(out)
    else:require(p.read_text()==out,'listing equality')
    print('PASS: exact HDMI control allocation/publication, loader-to-dlopen, and three callback-table wrapper paths.')
    print('Static loader/table landmarks only; no implementation load, callback binding, CID submission, or live event proved.')
if __name__=='__main__':main()
