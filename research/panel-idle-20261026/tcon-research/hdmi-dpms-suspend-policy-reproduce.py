#!/usr/bin/env python3
"""Offline landmarks for DPMS-cached HDMI suspend policy; no target actions."""
from pathlib import Path
import argparse, hashlib
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
API=ROOT/'binaries/tztv_hdmi_switch_api.ko'
SHA='c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97'
OUT=HERE/'hdmi-dpms-suspend-policy-v2.disasm'
def require(x,m):
    if not x: raise ValueError(m)
def span(sec,cs,name,lo,hi):
    raw=sec.data()[lo:hi]; q=list(cs.disasm(raw,lo))
    require(sum(i.size for i in q)==len(raw),name+' decode')
    return name,q
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--write-disassembly',action='store_true'); a=ap.parse_args()
    require(hashlib.sha256(API.read_bytes()).hexdigest()==SHA,'API SHA-256')
    with API.open('rb') as f:
        e=ELFFile(f); text=e.get_section_by_name('.text'); cold=e.get_section_by_name('.text.unlikely'); data=e.get_section_by_name('.data')
        sy={s.name:s for s in e.get_section_by_name('.symtab').iter_symbols() if s.name}
        require((sy['s_dpmsType']['st_shndx'],sy['s_dpmsType']['st_value'],sy['s_dpmsType']['st_size'])==(data.section_index if hasattr(data,'section_index') else 20,0xa38,1),'s_dpmsType')
        # pyelftools sections lack section_index on some versions; value/size plus .data symbol is the portable identity.
        require(sy['s_dpmsType']['st_value']==0xa38 and sy['s_dpmsType']['st_size']==1,'dpms symbol')
        require((sy['Suspend']['st_value'],sy['Suspend']['st_size'])==(0xe588,452),'Suspend symbol')
        require((sy['suspend_hdmi_suspend']['st_value'],sy['suspend_hdmi_suspend']['st_size'])==(0x1bb8,152),'private suspend symbol')
        require((sy['tztv_hdmi_switch_suspend']['st_shndx'],sy['tztv_hdmi_switch_suspend']['st_value'],sy['tztv_hdmi_switch_suspend']['st_size'])==(cold.section_index if hasattr(cold,'section_index') else 5,0x228,104),'cold suspend symbol')
        cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
        spans=[span(text,cs,'Suspend',0xe588,0xe750),span(text,cs,'private_suspend',0x1bb8,0x1c50),span(cold,cs,'switch_suspend_cold',0x228,0x290),span(text,cs,'se22_mode',0x36da8,0x36e0c),span(text,cs,'external_mode',0x343c8,0x34430)]
        r={i.address:(i.mnemonic,i.op_str) for _,q in spans for i in q}
        for ad,m,o in [(0xe618,'and','w20, w0, #2'),(0xe61c,'tbz','w0, #1, #0xe628'),(0xe620,'bl','#0xe620'),(0xe630,'adrp','x0, #0xe000'),(0xe634,'ldrb','w0, [x0]'),(0xe63c,'b.ne','#0xe714'),(0xe644,'bl','#0xe644'),(0xe65c,'adrp','x0, #0xe000'),(0xe660,'ldrb','w0, [x0]'),(0xe668,'b.ne','#0xe730'),(0xe670,'bl','#0xe670'),(0xe6dc,'mov','w0, w20'),(0x1c04,'bl','#0x1c04'),(0x1c20,'bl','#0x1c20'),(0x24c,'cbz','x0, #0x274'),(0x254,'cbz','x1, #0x274'),(0x25c,'blr','x1'),(0x26c,'mov','w0, #0'),(0x280,'mov','w0, #-0x13'),(0x36dac,'mov','w3, w0'),(0x36db0,'mov','w4, #1'),(0x36db8,'mov','w2, #0x41'),(0x36dbc,'mov','w1, #-0x60'),(0x36dc8,'mov','w0, #1'),(0x36dcc,'bl','#0x36dcc'),(0x36dd4,'tbz','w0, #0x1f, #0x36dec'),(0x36ddc,'mov','w19, #-0x80000000'),(0x36dfc,'mov','w0, w19'),(0x343d8,'strb','w0, [sp, #0x2f]'),(0x343e0,'ldr','w0, [x1]'),(0x343e4,'mov','w2, #0x41'),(0x343e8,'mov','w1, #-0x60'),(0x343f0,'mov','w19, #-0x80000000'),(0x343f4,'bl','#0x343f4'),(0x343f8,'tbz','w0, #0x1f, #0x3440c'),(0x3440c,'mov','w19, w0')]: require(r.get(ad)==(m,o),f'instruction {ad:#x}')
        rela=e.get_section_by_name('.rela.text'); dyn=e.get_section(rela['sh_link'])
        want={0xe620:'ext_switch_suspend',0xe644:'ext_se22s_set_mode',0xe670:'ext_sw_SetMode',0xe718:'ext_se22s_set_mode',0xe734:'ext_sw_SetMode',0x1c04:'sdp_runtime_pm_put',0x1c20:'tztv_hdmi_switch_suspend',0x36dcc:'tztv_i2c_write_8bit',0x343f4:'tztv_ext_i2c_write'}
        got={x['r_offset']:dyn.get_symbol(x['r_info_sym']).name for x in rela.iter_relocations()}
        for off,name in want.items(): require(got.get(off)==name,'relocation '+hex(off))
        # The two cached-byte ADRP/LDUR pairs are R_AARCH64_ADR_PREL_PG_HI21 / LDST8_ABS_LO12_NC to .data+a38.
        for hi,lo in [(0xe630,0xe634),(0xe65c,0xe660)]:
            rs=[x for x in rela.iter_relocations() if x['r_offset'] in (hi,lo)]
            require(len(rs)==2 and all(dyn.get_symbol(x['r_info_sym']).name=='' and x['r_addend']==0xa38 for x in rs),'dpms reloc '+hex(hi))
    out=''.join('\n## '+n+'\n'+''.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}\n' for i in q) for n,q in spans)
    if a.write_disassembly:
        with OUT.open('x') as f:f.write(out)
    else: require(OUT.read_text()==out,'listing equality')
    print('PASS: static DPMS cached-byte suspend gates and lower I2C-call landmarks.')
    print('No live flags, bus/address ABI, I2C completion, external-device semantics, or panel causality established.')
if __name__=='__main__': main()
