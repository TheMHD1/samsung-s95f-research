#!/usr/bin/env python3
"""Offline exact-ELF landmarks for SDP's production-mode request gate."""
from pathlib import Path
import argparse
import hashlib
import struct

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCES = {
    'sdp_frc': (ROOT/'binaries/sdp_frc.ko', '05dea2eaad34a23def837fb86d2f7a4e99ef630066ad6fed18d0cf55ba37063d'),
    'provider': (ROOT/'overnight/hdmi-cell-provider-copy-20261026/tztv-battery.ko',
                 'dd7e9c1c68b3802e8e8fc04a9097c2cc6baaedd5960e7a25bb387499edbc2270'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Source:
    def __init__(self, name):
        path, expected = SOURCES[name]
        self.name = name
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, name+' source hash')
        self.handle = path.open('rb')
        self.elf = ELFFile(self.handle)
        self.symbols = {s.name:s for s in self.elf.get_section_by_name('.symtab').iter_symbols() if s.name}

    def symbol(self, name, section, address, size):
        s = self.symbols[name]
        require((self.elf.get_section(s['st_shndx']).name,s['st_value'],s['st_size']) ==
                (section,address,size), name+' symbol identity')

    def listing(self, sec, lo, hi):
        raw = self.elf.get_section_by_name(sec).data()[lo:hi]
        require(len(raw) == hi-lo, 'section bounds')
        ins = list(Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(raw,lo))
        require(sum(len(i.bytes) for i in ins) == len(raw), 'decode coverage')
        return {i.address:(i.mnemonic,i.op_str) for i in ins}

    def relocation(self, sec, offset, target, addend=0):
        rs = self.elf.get_section_by_name('.rela'+sec)
        syms = self.elf.get_section(rs['sh_link'])
        found = [r for r in rs.iter_relocations() if r['r_offset']==offset]
        require(len(found)==1, f'relocation cardinality {self.name} {sec}+{offset:x}')
        r = found[0]
        s = syms.get_symbol(r['r_info_sym'])
        actual = self.elf.get_section(s['st_shndx']).name if s['st_info']['type']=='STT_SECTION' else s.name
        require((actual,r['r_addend']) == (target,addend), f'{self.name} relocation {sec}+{offset:x}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-disassembly',action='store_true')
    args = parser.parse_args()
    sources = {name:Source(name) for name in SOURCES}
    s, p = sources['sdp_frc'], sources['provider']
    spans = []
    rows = {}
    definitions = [
        (s,'sdp_frc_probe','.text.unlikely',0,904),
        (s,'sdp_frc_set_env_from_boardcfg','.text',0xc88,1524),
        (p,'tztv_gpio_read_num','.text',0x150,400),
        (p,'linker_sysfs_show','.text',0x14c0,40),
        (p,'panel_production_show','.text',0x1528,48),
        (p,'linker_get_panel_production.part.0','.text',0x1898,48),
        (p,'linker_probe','.text',0x18c8,848),
        (p,'linker_get_panel_production','.text',0x1c90,40),
        (p,'tztv_sys_use_hdmi_cell_sw','.text',0x8e98,24),
    ]
    for src,name,sec,lo,size in definitions:
        src.symbol(name,sec,lo,size)
        rs=src.listing(sec,lo,lo+size)
        spans.append((src.name,name,sec,lo,lo+size,rs))
        rows.update({(src.name,sec,a):r for a,r in rs.items()})
    for lo,hi in ((0x2258,0x22c8),(0x2344,0x2360)):
        rs=s.listing('.text',lo,hi)
        spans.append((s.name,'sdp_frc_ex_proc gate excerpt','.text',lo,hi,rs))
        rows.update({(s.name,'.text',a):r for a,r in rs.items()})
    s.symbol('sdp_frc_ex_proc','.text',0x2258,4656)
    checks = [
        ('sdp_frc','.text.unlikely',0x134,'str','xzr, [x19, #0x318]'),
        ('sdp_frc','.text.unlikely',0x1e8,'mov','x0, x19'),
        ('sdp_frc','.text',0xc94,'mov','x19, x0'),
        ('sdp_frc','.text',0xca0,'ldr','x0, [x0, #0x18]'),
        ('sdp_frc','.text',0xca8,'tst','w0, #0xff'),
        ('sdp_frc','.text',0xcac,'b.ne','#0xcc4'),
        ('sdp_frc','.text',0xcb4,'ldr','x0, [x0, #0x40]'),
        ('sdp_frc','.text',0xcbc,'tst','w0, #0xff'),
        ('sdp_frc','.text',0xcc0,'b.eq','#0xfa0'),
        ('sdp_frc','.text',0xcd0,'str','x0, [x19, #0x318]'),
        ('sdp_frc','.text',0xfa4,'ldr','x0, [x0, #0x48]'),
        ('sdp_frc','.text',0xfac,'tst','w0, #0xff'),
        ('sdp_frc','.text',0xfb0,'b.ne','#0xcc4'),
        ('sdp_frc','.text',0x2284,'ldr','x21, [x19, #0x478]'),
        ('sdp_frc','.text',0x2288,'ldr','x0, [x21, #0x318]'),
        ('sdp_frc','.text',0x228c,'cbz','x0, #0x229c'),
        ('sdp_frc','.text',0x2290,'mov','w25, #0'),
        ('sdp_frc','.text',0x2294,'blr','x0'),
        ('sdp_frc','.text',0x2298,'cbnz','w0, #0x2344'),
        ('sdp_frc','.text',0x2344,'mov','w0, w25'),
        ('sdp_frc','.text',0x22ac,'ldr','x0, [x21, #0x318]'),
        ('sdp_frc','.text',0x22b4,'blr','x0'),
        ('sdp_frc','.text',0x22b8,'ldrb','w0, [x21, #0x358]'),
        ('provider','.text',0x8e9c,'mov','x0, #0'),
        ('provider','.text',0x1c98,'cbz','x1, #0x1ca4'),
        ('provider','.text',0x1c9c,'ldr','w0, [x1]'),
        ('provider','.text',0x1898,'cbz','x0, #0x18b4'),
        ('provider','.text',0x18a0,'add','x0, x0, #0x38'),
        ('provider','.text',0x18a4,'str','x0, [x1]'),
        ('provider','.text',0x18ac,'ldr','w0, [x0]'),
        ('provider','.text',0x18c0,'mov','w0, #0'),
        ('provider','.text',0x1984,'str','wzr, [x19, #0x38]'),
        ('provider','.text',0x1978,'str','wzr, [sp, #0x4c]'),
        ('provider','.text',0x19a0,'add','x1, sp, #0x4c'),
        ('provider','.text',0x19a4,'mov','w2, #5'),
        ('provider','.text',0x19ac,'ldr','w1, [sp, #0x4c]'),
        ('provider','.text',0x19bc,'cset','w2, eq'),
        ('provider','.text',0x19c0,'str','w2, [x19, #0x38]'),
        ('provider','.text',0x1d8,'str','w0, [x23]'),
        ('provider','.text',0x1b0,'cbnz','w20, #0x20c'),
        ('provider','.text',0x19dc,'mov','x0, x19'),
        ('provider','.text',0x19e0,'bl','#0x1898'),
        ('provider','.text',0x1538,'ldr','w3, [x3, #0x38]'),
        ('provider','.text',0x14c0,'ldr','x3, [x1, #0x18]'),
        ('provider','.text',0x14d0,'ldr','x0, [x0, #0x40]'),
    ]
    for name,sec,address,mn,op in checks:
        require(rows.get((name,sec,address)) == (mn,op),f'landmark {name} {sec}+{address:x}')
    for sec,offset,target,addend in [
        ('.text.unlikely',0x1ec,'sdp_frc_set_env_from_boardcfg',0),
        ('.text.unlikely',0x210,'sdp_frc_resource_init',0),
        ('.text',0xc9c,'get_ident_info',0),('.text',0xcb0,'get_ident_info',0),
        ('.text',0xfa0,'get_ident_info',0),('.text',0xcc4,'.rodata.str1.8',0x580),
        ('.text',0xcc8,'.rodata.str1.8',0x580),('.text',0xccc,'__symbol_get',0)]:
        s.relocation(sec,offset,target,addend)
    require(s.elf.get_section_by_name('.rodata.str1.8').data()[0x580:].split(b'\0',1)[0] ==
            b'tztv_sys_use_hdmi_cell_sw','lookup symbol literal')
    for sec,offset,target,addend in [
        ('.text',0x8ea4,'linker_get_panel_production',0),
        ('.text',0x1c90,'.bss',0x38),('.text',0x1c94,'.bss',0x38),
        ('.text',0x189c,'.bss',0x38),('.text',0x18a4,'.bss',0x38),
        ('.text',0x1988,'.rodata.str1.8',0x718),
        ('.text',0x19a8,'tztv_gpio_read_num',0),('.text',0x1548,'snprintf',0),
        ('.text',0x1d4,'gpiod_get_raw_value_cansleep',0),
        ('.data',0x168,'.data',0x250),('.data',0x250,'.data',0x2d8),
        ('.data',0x2d8,'.rodata.str1.8',0xa08),('.data',0x2f0,'.text',0x1528),
        ('.rodata',0x720,'.text',0x14c0),
        ('.text',0x1a98,'.rodata.str1.8',0x8d0)]:
        p.relocation(sec,offset,target,addend)
    st=p.elf.get_section_by_name('.rodata.str1.8').data()
    for offset,value in ((0x718,b'samsung,pi_line_con0'),(0xa08,b'panel_production'),(0x8d0,b'production_mode')):
        require(st[offset:].split(b'\0',1)[0]==value,'provider string identity')
    require(struct.unpack_from('<H',p.elf.get_section_by_name('.data').data(),0x2e0)[0] == 0o444,'sysfs permission bits')
    require(p.elf.get_section_by_name('.data').data()[0x2f8:0x300] == bytes(8), 'sysfs store slot zero')
    require(not any(r['r_offset']==0x2f8 for r in p.elf.get_section_by_name('.rela.data').iter_relocations()), 'sysfs store slot has relocation')
    listing=''.join(f'\n## {name} {symbol} {sec} {lo:#x}..{hi:#x}\n'+
        ''.join(f'{a:08x}  {mn:8} {op}\n' for a,(mn,op) in rs.items())
        for name,symbol,sec,lo,hi,rs in spans)
    path=HERE/'sdp-hdmi-cell-gate-with-gpio.disasm'
    if args.write_disassembly:
        with path.open('x') as out:
            out.write(listing)
    else:
        require(path.read_text()==listing,'saved disassembly equality')
    print('PASS: exact SDP/provider ELFs, conditional resolver, zero-return suppression, cached production field and read-only sysfs landmarks.')
    print('Static control-flow interpretation still requires review. No callback invocation, live kernel pointer or incident-aligned cause established.')


if __name__=='__main__':
    main()
