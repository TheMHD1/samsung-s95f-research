#!/usr/bin/env python3
"""Offline roots into private HDMI suspend/resume exports."""
from pathlib import Path
import argparse, hashlib, importlib.util

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
READER=HERE/'sdp-hdmi-cell-gate-reproduce.py'
READER_SHA='8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67'
SWITCH=ROOT/'binaries/tztv_hdmi_switch.ko'
API=ROOT/'binaries/tztv_hdmi_switch_api.ko'
SWITCH_SHA='11d9c53a0e08300bb12b1cafd513e3fc6ee84ba1bcd434007e459dce70fa82b6'
API_SHA='c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97'

def require(ok,msg):
    if not ok: raise ValueError(msg)

def load():
    require(hashlib.sha256(READER.read_bytes()).hexdigest()==READER_SHA,'reader hash')
    spec=importlib.util.spec_from_file_location('private_hdmi_reader',READER)
    require(spec and spec.loader,'reader loader')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.SOURCES.update({'switch':(SWITCH,SWITCH_SHA),'api':(API,API_SHA)})
    return mod

def exports(src):
    r=src.elf.get_section_by_name('.rela__ksymtab'); require(r is not None,'ksymtab')
    st=src.elf.get_section(r['sh_link'])
    return [(x['r_offset'],st.get_symbol(x['r_info_sym']).name) for x in r.iter_relocations()]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write-disassembly',action='store_true');args=ap.parse_args()
    m=load(); sw=m.Source('switch'); api=m.Source('api')
    # The private imports are the positive cross-module roots; exact local
    # callers are recovered by relocations, not guessed by name.
    for name in ('suspend_hdmi_suspend','suspend_hdmi_resume'):
        require(name in sw.symbols and sw.symbols[name]['st_shndx']=='SHN_UNDEF','switch private import '+name)
    api.symbol('suspend_hdmi_suspend','.text',0x1bb8,152)
    api.symbol('suspend_hdmi_resume','.text',0x1c50,188)
    require(exports(api).count((0x3fc,'suspend_hdmi_suspend'))==1,'suspend export')
    require(exports(api).count((0x3f0,'suspend_hdmi_resume'))==1,'resume export')
    roots=[]
    for rel in sw.elf.iter_sections():
        if rel['sh_type'] not in ('SHT_RELA','SHT_REL'):
            continue
        target=sw.elf.get_section(rel['sh_info']).name
        st=sw.elf.get_section(rel['sh_link'])
        for r in rel.iter_relocations():
            n=st.get_symbol(r['r_info_sym']).name
            if n in ('suspend_hdmi_suspend','suspend_hdmi_resume'):
                roots.append((target,r['r_offset'],n,r['r_info_type']))
    require(roots,'positive private import relocation roots')
    require(sorted(roots) == [
            ('.text',0x1930,'suspend_hdmi_suspend',283),
            ('.text',0x1948,'suspend_hdmi_resume',283),
            ('.text',0x2034,'suspend_hdmi_suspend',283),
            ('.text',0x20d0,'suspend_hdmi_resume',283)],
            'four exact private CALL26 roots')
    spans=[]
    for src,name,sec,lo,size in [(api,'suspend_hdmi_suspend','.text',0x1bb8,152),(api,'suspend_hdmi_resume','.text',0x1c50,188)]:
        rows=src.listing(sec,lo,lo+size);spans.append((src.name,name,sec,lo,lo+size,rows))
    # Require imported calls themselves decode as BL placeholders and preserve
    # all discovered root offsets in the saved listing.
    swrows={}
    for section,off,name,_typ in roots:
        rows=sw.listing(section,off,off+4); swrows.update({(section,a):v for a,v in rows.items()})
        require(rows[off][0]=='bl','private root call opcode '+name)
    for section in sorted({x[0] for x in roots}):
        rows={a:v for (s,a),v in swrows.items() if s==section}
        spans.append(('switch','private import callsites',section,min(rows),max(rows)+4,rows))
    # The positive user-facing root in this module is the extended-control
    # ioctl callback, not an inferred UI name.  The two relevant CIDs select
    # the two adjacent dispatcher cases.  Include all gate/call blocks needed
    # to reproduce that conclusion, with no claim about the caller of the
    # V4L2 ioctl framework.
    sw.symbol('hdmi_switch_vidioc_s_ext_ctrls','.text',0x23c0,368)
    sw.symbol('hdmi_switch_set_ctrl','.text',0x15e8,3540)
    sw.symbol('hdmi_switch_probe','.text',0x3998,1064)
    for label,lo,hi in [
        ('extended-control callback and direct local dispatch',0x23c0,0x2530),
        ('private CID switch cases and gates',0x1600,0x215c),
        ('V4L2 video-device registration assignments',0x3a48,0x3abc),
    ]:
        rows=sw.listing('.text',lo,hi)
        spans.append(('switch',label,'.text',lo,hi,rows))
    allrows={}
    for n,sy,se,lo,hi,rows in spans:
        allrows.update({(n,se,a):v for a,v in rows.items()})
    checks=[
        ('switch','.text',0x23d8,'ldr','w1, [x2]'),
        ('switch','.text',0x23dc,'cmp','w1, #0xa00, lsl #12'),
        ('switch','.text',0x23fc,'ldr','w1, [x2, #4]'),
        ('switch','.text',0x2404,'cbz','w1, #0x23e4'),
        ('switch','.text',0x2448,'ldrb','w0, [x26]'),
        ('switch','.text',0x2458,'cbz','w0, #0x2468'),
        ('switch','.text',0x2464,'b.ne','#0x24dc'),
        ('switch','.text',0x246c,'bl','#0x15e8'),
        ('switch','.text',0x191c,'adrp','x19, #0x1000'),
        ('switch','.text',0x1924,'ldr','x0, [x19, #0x78]'),
        ('switch','.text',0x1928,'cbnz','x0, #0x2020'),
        ('switch','.text',0x1930,'bl','#0x1930'),
        ('switch','.text',0x1938,'adrp','x0, #0x1000'),
        ('switch','.text',0x1940,'cbnz','x0, #0x20bc'),
        ('switch','.text',0x1948,'bl','#0x1948'),
        ('switch','.text',0x2034,'bl','#0x2034'),
        ('switch','.text',0x20d0,'bl','#0x20d0'),
        ('switch','.text',0x20e4,'mov','w0, #4'),
        ('switch','.text',0x20ec,'bl','#0x20ec'),
        ('switch','.text',0x3a54,'add','x2, x22, #0x898'),
        ('switch','.text',0x3a64,'str','x2, [x1]'),
        ('switch','.text',0x3a68,'add','x7, x23, #0x28'),
        ('switch','.text',0x3a84,'str','x7, [x6, #0x398]'),
    ]
    for src,sec,addr,mn,op in checks:
        require(allrows.get((src,sec,addr))==(mn,op),f'CFG landmark {src} {sec}+{addr:x}')
    # Recover the CID base from the two immediate-subtract fields rather than
    # transcribing the shifted operand as a hexadecimal prefix: 0xa00 << 12
    # is 0x00a00000, not 0xa0000000.
    cid_base=(0xa00 << 12) + 0x998
    require(cid_base==0x00a00998,'CID immediate arithmetic')
    require(allrows.get(('switch','.text',0x1600))==('sub','w0, w0, #0xa00, lsl #12'),'CID high subtract')
    require(allrows.get(('switch','.text',0x1604))==('sub','w0, w0, #0x998'),'CID low subtract')
    # The compact switch table maps CID offsets 0x26/0x27 from that base to
    # these cases.  This is a byte-level table check rather than string naming.
    rt=sw.elf.get_section_by_name('.rodata').data()
    for idx,target in ((0x26,0x191c),(0x27,0x1938)):
        rel=int.from_bytes(rt[idx*2:idx*2+2],'little',signed=True)
        require(0x1628+rel*4==target,f'CID dispatch entry {idx:x}')
    require((cid_base+0x26,cid_base+0x27)==(0x00a009be,0x00a009bf),'CID values')
    # Prove framework publication pointers: fops+0x20 is video_ioctl2;
    # ioctl_ops+0x260 is the exact ext-control callback.
    sw.relocation('.rodata',0xb08,'video_ioctl2',0)
    sw.relocation('.data',0x288,'.text',0x23c0)
    sw.relocation('.data',0x28,'.text',0x18)
    listing=''.join('\n## %s %s %s %#x..%#x\n'%(n,sy,se,lo,hi)+''.join('%08x  %-8s %s\n'%(a,x[0],x[1]) for a,x in rows.items()) for n,sy,se,lo,hi,rows in spans)
    out=HERE/'private-hdmi-invocation-roots-v3.disasm'
    if args.write_disassembly:
        with out.open('x') as f:f.write(listing)
    else: require(out.read_text()==listing,'listing equality')
    print('PASS: exact API exports, four switch CALL26 roots, V4L2 extended-control dispatch, and publication landmarks.')
    print('Manual framework/runtime review remains required; no live invocation, source/UI origin, or causation established.')

if __name__=='__main__': main()
