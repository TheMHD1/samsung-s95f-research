#!/usr/bin/env python3
"""Offline exact-module SerDes lookup/probe/resume path checks."""
from pathlib import Path
import argparse
import hashlib
import importlib.util

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def require(ok,message):
    if not ok:raise ValueError(message)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--write-disassembly',action='store_true')
    args=parser.parse_args()
    reader=HERE/'sdp-hdmi-cell-gate-reproduce.py'
    require(hashlib.sha256(reader.read_bytes()).hexdigest()=='8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67','reader hash')
    spec=importlib.util.spec_from_file_location('exact_arm64_reader',reader)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SOURCES.update({
        'hdmi':(ROOT/'binaries/sdp_hdmi.ko','f7cffd19934ef459b0263ceddddf003306b399e01d0ddee48df3f64a86667994'),
        'support':(ROOT/'overnight/serdes-support-copy-20261026/system_drv.ko','fbe4eaad57c66865e2cc50b575a878a690c06303905e666e75b9f08d139dd1f0'),
        'ocif':(ROOT/'overnight/serdes-ocif-copy-20261026/sdp_ocl.ko','80b9e66f4129a31207f1eee8d7636d7565193ecf9ba87e3bded6196c5e1b02e7'),
    })
    sources={n:module.Source(n) for n in ('hdmi','provider','support','ocif')}
    definitions=[
        ('provider','tztv_system_serdes_lock_check','.text',0x8d60,308),
        ('provider','_get_serdes_lock_symbol.constprop.0','.text',0x8c78,232),
        ('provider','_check_serdes_lock','.text',0x8be8,52),
        ('provider','_check_ocif_lock','.text',0x8c20,88),
        ('support','tztv_sys_is_oc_support','.text',0xdc0,40),
        ('ocif','sdp_ocif_lock_get','.text',0x90,28),
        ('ocif','sdp_serdes_lock','.text',0x49c8,160),
        ('ocif','read_u32','.text',0x42e0,92),
        ('hdmi','sdp_hrx_is_ocl_serdes_locked','.text',0x4cad0,132),
        ('hdmi','sdp_hdmi_resume_fxn','.text',0x48f8,1380),
        ('hdmi','sdp_hdmi_pm_resume','.text',0x4e60,700),
        ('hdmi','sdp_hdmi_resume','.text',0x5348,492),
    ]
    spans=[]
    rows={}
    for name,symbol,sec,lo,size in definitions:
        src=sources[name]
        src.symbol(symbol,sec,lo,size)
        listing=src.listing(sec,lo,lo+size)
        rows.update({(name,sec,a):value for a,value in listing.items()})
        spans.append((name,symbol,sec,lo,lo+size,listing))
    sources['hdmi'].symbol('sdp_hdmi_probe','.text.unlikely',0x53c,4948)
    listing=sources['hdmi'].listing('.text.unlikely',0x1370,0x13e0)
    rows.update({('hdmi','.text.unlikely',a):v for a,v in listing.items()})
    spans.append(('hdmi','sdp_hdmi_probe excerpt','.text.unlikely',0x1370,0x13e0,listing))
    for name,sec,offset,mn,op in [
        ('provider','.text',0x8d94,'mov','w19, #0x12c'),
        ('provider','.text',0x8dbc,'mov','w0, #0xa'),
        ('provider','.text',0x8db8,'sub','w19, w19, #1'),
        ('provider','.text',0x8d88,'cbz','w0, #0x8e74'),
        ('provider','.text',0x8c2c,'cmp','w0, #0'),
        ('provider','.text',0x8c30,'b.le','#0x8c40'),
        ('provider','.text',0x8bf4,'cbnz','w0, #0x8c00'),
        ('support','.text',0xdcc,'ldrb','w2, [x1, #3]'),
        ('support','.text',0xdd0,'tst','w2, #0xf0'),
        ('support','.text',0xdd8,'ldrb','w0, [x1, #1]'),
        ('support','.text',0xddc,'cmp','w0, #4'),
        ('ocif','.text',0x9c,'ldrb','w0, [x0, #0xb8]'),
        ('hdmi','.text',0x4caf4,'cset','w0, eq'),
        ('hdmi','.text',0x4cb30,'cset','w0, eq'),
        ('hdmi','.text',0x49d0,'ldrb','w1, [x0, #0x60]'),
        ('hdmi','.text',0x49d4,'cbnz','w1, #0x4c04'),
        ('hdmi','.text',0x4cd8,'tst','w0, #0xff'),
        ('hdmi','.text',0x4cdc,'b.eq','#0x4c3c'),
    ]:
        require(rows.get((name,sec,offset))==(mn,op),f'landmark {name} {sec}+{offset:x}')
    for name,sec,offset,target,addend in [
        ('provider','.text',0x8e00,'__symbol_get',0),
        ('provider','.text',0x8df8,'.rodata.str1.8',0x42c8),
        ('provider','.text',0x8ca8,'.rodata.str1.8',0x4280),
        ('provider','.text',0x8cc4,'.rodata.str1.8',0x42b8),
        ('provider','.text',0x8dc0,'msleep',0),
        ('provider','.text',0x8cb4,'__symbol_get',0),
        ('provider','.text',0x8cd0,'__symbol_get',0),
        ('provider','.text',0x8d70,'.bss',0x218),
        ('support','.text',0xdc0,'.bss',0xa8),
        ('ocif','.text',0x90,'.bss',0),
        ('ocif','.text',0x49f8,'read_u32',0),
        ('hdmi','.text',0x4cb04,'.rodata.str1.8',0x1f740),
        ('hdmi','.text',0x4cb10,'__symbol_get',0),
        ('hdmi','.text',0x4cb14,'.bss',0x1700),
        ('hdmi','.text',0x4cb28,'__symbol_put',0),
        ('hdmi','.text',0x4cd4,'sdp_hrx_is_ocl_serdes_locked',0),
        ('hdmi','.text.unlikely',0x13b8,'sdp_hrx_is_ocl_serdes_locked',0),
        ('hdmi','.text',0x4f84,'sdp_hdmi_resume_fxn',0),
        ('hdmi','.text',0x5444,'sdp_hdmi_resume_fxn',0),
    ]:
        sources[name].relocation(sec,offset,target,addend)
    for name,offset,expected in [('provider',0x42c8,b'tztv_sys_is_oc_support'),
            ('provider',0x4280,b'sdp_ocif_lock_get'),('provider',0x42b8,b'sdp_serdes_lock'),
            ('hdmi',0x1f740,b'tztv_system_serdes_lock_check')]:
        raw=sources[name].elf.get_section_by_name('.rodata.str1.8').data()
        require(raw[offset:].split(b'\0',1)[0]==expected,'lookup literal')
    def exports(src):
        section=src.elf.get_section_by_name('.rela__ksymtab')
        symbols=src.elf.get_section(section['sh_link'])
        return [symbols.get_symbol(r['r_info_sym']).name for r in section.iter_relocations()]
    for name,symbol in [('provider','tztv_system_serdes_lock_check'),
                        ('support','tztv_sys_is_oc_support'),('ocif','sdp_ocif_lock_get')]:
        require(exports(sources[name]).count(symbol)==1,'primary export '+symbol)
    require('sdp_serdes_lock' not in exports(sources['ocif']), 'fallback candidate export changed')
    require('__ksymtab_sdp_serdes_lock' not in sources['ocif'].symbols and
            '__kstrtab_sdp_serdes_lock' not in sources['ocif'].symbols,'unexpected fallback export symbols')
    output=''.join(f'\n## {name} {symbol} {sec} {lo:#x}..{hi:#x}\n'+
        ''.join(f'{a:08x}  {mn:8} {op}\n' for a,(mn,op) in listing.items())
        for name,symbol,sec,lo,hi,listing in spans)
    path=HERE/'serdes-lock-path.disasm'
    if args.write_disassembly:
        with path.open('x') as out:out.write(output)
    else:require(path.read_text()==output,'saved listing equality')
    print('PASS: exact HDMI/probe/resume lookup edges, conditional SerDes poll and distinct support/OCIF providers.')
    print('Primary exports checked; same-named sdp_ocl fallback body is NOT exported and does not resolve the dynamic fallback name.')
    print('Static landmarks require manual flow review; no live binding, hardware query, panel state, incident cause or repair established.')


if __name__=='__main__':main()
