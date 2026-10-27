#!/usr/bin/env python3
"""Offline checks for UID 0x506e's PPI dispatch and conditional storage route."""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, "/tmp/tcon-capstone")
from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile
ROOT=Path(__file__).resolve().parents[1]
TIFS=ROOT/'binaries/TIFSDaemon'; INDEX=ROOT/'binaries/factory-data/FactoryIndexFile_Part1.dat'; DATA=ROOT/'binaries/factory-data/Factory_Part1.dat'; VE=ROOT/'binaries/libvideoenhance.so.0'; AVE=ROOT/'binaries/libave.so.0.1'; FI=ROOT/'binaries/libfactory-interface-ATSC.so'; VM=ROOT/'binaries/libvideo-misc.so.0.1.0'; VFT=ROOT/'binaries/libvideo-ft-control-impl-sec.so.0.1.0'
HASH={'TIFSDaemon':'d2ebc1d11be46b4a189ec87666b68b73ae58d6f5a3c10da901c80e1125620c11','FactoryIndexFile_Part1.dat':'fd6588baf4e57c5b2b8b3c636e55888f9f6e49cf3b2e7dc80302733066993602','Factory_Part1.dat':'687b6b019cb1b1fd5f3ae826949cfbe4dd38027cb8d0e2d8f321fd055e2ce417','libvideoenhance.so.0':'3ce4e4741bad4883d7f097b7939e7b1f8853a354329b17398da496bf624228c9','libave.so.0.1':'a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777','libfactory-interface-ATSC.so':'1fc40fa93b3bf81ee79b610d8c699ba94e3f4ee49e3a737d4dfe1e2e803425dd','libvideo-misc.so.0.1.0':'fcd5faa76492151512544fd29783d33b9f63c91a863909cc0c53ba598ff9e5dd','libvideo-ft-control-impl-sec.so.0.1.0':'2a2d24ed21babd5a7f67e6bd7aa3447cb9a7316fb0234ae4e0e1a93e77650b8d'}
def main():
    for p in (TIFS,INDEX,DATA): assert hashlib.sha256(p.read_bytes()).hexdigest()==HASH[p.name],p
    x=INDEX.read_bytes(); assert x[0x8bc0:0x8be0] == (20590).to_bytes(4,'little')+(0).to_bytes(4,'little')+(6).to_bytes(4,'little')+(0).to_bytes(4,'little')+(5).to_bytes(4,'little')+(2).to_bytes(4,'little')+(1).to_bytes(4,'little')+(6240).to_bytes(4,'little')
    d=DATA.read_bytes(); assert d[0x691dc:0x691e0]==(20590).to_bytes(4,'little'); assert d[0x691e0:0x691e4]==(16).to_bytes(4,'little'); assert b'Offsensing TEST Period' in d[0x691e8:0x69230]
    with TIFS.open('rb') as f:
      e=ELFFile(f); t=e.get_section_by_name('.text');base=t['sh_addr'];b=t.data();cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
      def ins(a,n):return {i.address:(i.mnemonic,i.op_str) for i in cs.disasm(b[a-base:a-base+n],a)}
      tx=ins(0xc5e8c,804); st=ins(0x1077d8,260)
      assert tx[0xc5ef8]==('tbh','[pc, r3, lsl #1]')
      # Table entry sixteen: base PC 0xc5efc plus halfword offset 0x1c*2.
      assert int.from_bytes(b[0xc5efc-base+32:0xc5efc-base+34],'little')==0x1c
      assert 0xc5efc+2*0x1c==0xc5f34
      assert tx[0xc5ee8]==('str','r7, [sp, #0x20]') and tx[0xc5f3e]==('blx','#0x5f880') and tx[0xc5f6a]==('blx','#0x5df38') and tx[0xc5f72]==('cmp','r0, #0')
      assert st[0x107824]==('strb.w','r3, [sp, #0x17]') and st[0x107838]==('bl','#0xc5e8c') and st[0x10789a]==('blx','#0x5fd94')
      rel=e.get_section_by_name('.rel.plt');dyn=e.get_section(rel['sh_link']); got={dyn.get_symbol(r['r_info_sym']).name:r['r_offset'] for r in rel.iter_relocations()}; assert got['_ZN19FCStorageBaseCommon13SetFactoryUIDEjii']==0x165ad0
      assert got['ppi_video_system_diagnosis_set_factory_item']==0x165924 and got['ppi_ve_set_factory_item']==0x1650d4
    assert hashlib.sha256(FI.read_bytes()).hexdigest()==HASH[FI.name]
    with FI.open('rb') as f:
      e=ELFFile(f);t=e.get_section_by_name('.text');base=t['sh_addr'];b=t.data();copy={i.address:(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b[0x43998982-base:0x43998982-base+16],0x43998982)}
      assert copy[0x43998986]==('mov.w','r3, #0x164') and copy[0x4399898c]==('blx','#0x43989ce8')
    assert hashlib.sha256(VE.read_bytes()).hexdigest()==HASH[VE.name]
    with VE.open('rb') as f:
      e=ELFFile(f);t=e.get_section_by_name('.text');base=t['sh_addr'];b=t.data();ve={i.address:(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b[0x46f3cc34-base:0x46f3cc34-base+196],0x46f3cc34)}
      assert ve[0x46f3cc5c]==('ldr.w','r0, [r3, #0x354]') and ve[0x46f3cc78]==('mov','ip, r4') and ve[0x46f3cc80]==('bx','ip')
    assert hashlib.sha256(VM.read_bytes()).hexdigest()==HASH[VM.name]
    with VM.open('rb') as f:
      e=ELFFile(f);t=e.get_section_by_name('.text');base=t['sh_addr'];b=t.data();misc={i.address:(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b[0x47590fd8-base:0x47590fd8-base+64],0x47590fd8)}
      assert misc[0x47590ffa]==('ldr','r0, [r3, #0x3c]') and misc[0x4759100c]==('ldr','r3, [r3, #0x3c]') and misc[0x47591014]==('bx','r3')
    assert hashlib.sha256(VFT.read_bytes()).hexdigest()==HASH[VFT.name]
    with VFT.open('rb') as f:
      e=ELFFile(f);t=e.get_section_by_name('.text');base=t['sh_addr'];b=t.data();diag={i.address:(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(b[0xaa54-base:0xaa54-base+436],0xaa54)}
      assert diag[0xaad0]==('movw','r3, #0x64d') and diag[0xabf4]==('mvn','r0, #0x5e')
    assert hashlib.sha256(AVE.read_bytes()).hexdigest()==HASH[AVE.name]
    with AVE.open('rb') as f:
      e=ELFFile(f);t=e.get_section_by_name('.text');base=t['sh_addr'];b=t.data();cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
      impl={i.address:(i.mnemonic,i.op_str) for i in cs.disasm(b[0x29fa34-base:0x29fa34-base+18],0x29fa34)}
      api={i.address:(i.mnemonic,i.op_str) for i in cs.disasm(b[0x27353c-base:0x27353c-base+452],0x27353c)}
      assert impl[0x29fa40]==('blx','#0x8e1c0')
      assert api[0x273636]==('blx','#0x8ab0c') and api[0x27364e]==('blx','#0x909e0')
      rel=e.get_section_by_name('.rel.plt');dyn=e.get_section(rel['sh_link']);got={dyn.get_symbol(r['r_info_sym']).name:r['r_offset'] for r in rel.iter_relocations()}
      assert got['_ZN17VideoEnhancerImpl16set_factory_itemE22PPI_FACTORY_SPECIAL_IDiiPi']==0x5a629c and got['ave_api_set_factory_item']==0x5a5478
      assert got['_Z28ave_frc_api_set_factory_item22PPI_FACTORY_SPECIAL_IDiiPi']==0x5a423c and got['_Z29ave_tcon_api_set_factory_item22PPI_FACTORY_SPECIAL_IDiiPi']==0x5a61d8
      assert e.get_section_by_name('.rel.dyn') is not None
      dyn=e.get_section_by_name('.dynsym'); rel_dyn=e.get_section_by_name('.rel.dyn')
      glob={dyn.get_symbol(r['r_info_sym']).name:r['r_offset'] for r in rel_dyn.iter_relocations()}
      assert glob['impl_set_factory_item']==0x5a6f44
      table={i.address:(i.mnemonic,i.op_str) for i in cs.disasm(b[0x2a0fb0-base:0x2a0fb0-base+12],0x2a0fb0)}
      assert table[0x2a0fb4]==('ldr','r4, [r3, r4]') and table[0x2a0fb6]==('str.w','r4, [r0, #0x354]')
      frc={i.address:(i.mnemonic,i.op_str) for i in cs.disasm(b[0x242a4e-base:0x242a4e-base+20],0x242a4e)}
      ep={i.address:(i.mnemonic,i.op_str) for i in cs.disasm(b[0x26caac-base:0x26caac-base+110],0x26caac)}
      tcon={i.address:(i.mnemonic,i.op_str) for i in cs.disasm(b[0x263e20-base:0x263e20-base+48],0x263e20)}
      assert frc[0x242a56]==('blx','#0x8f198') and ep[0x26cb16]==('cmp','r3, #0x1e') and ep[0x26cb18]==('bhi','#0x26cad4') and ep[0x26cad6]==('ldr','r2, [pc, #0xe0]')
      assert tcon[0x263e2c]==('movs','r5, #0') and tcon[0x263e46]==('mov','r0, r5')
    print('PASS: hash-gated landmarks; manual paired-path review required')
if __name__=='__main__':main()
