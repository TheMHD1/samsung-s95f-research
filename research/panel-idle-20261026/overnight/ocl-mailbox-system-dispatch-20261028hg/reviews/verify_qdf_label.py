#!/usr/bin/env python3
"""Narrow retained-source check for actual HF printk label interpretation."""
import hashlib,io,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent.parent;ROOT=B.parent
sys.path.insert(0,'/tmp/tcon-capstone')
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
checks=0

def need(v,w):
 global checks
 if not v:raise ValueError(w)
 checks+=1

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=ROOT/'binaries/qdf_tcon.ko';b=p.read_bytes();need(sha(b)=='97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63','QDF source pin')
 e=ELFFile(io.BytesIO(b));code=e.get_section_by_name('.text').data();ro=e.get_section_by_name('.rodata').data();fmt=e.get_section_by_name('.rodata.str1.8').data();md=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 rel=e.get_section_by_name('.rela.text');sy=e.get_section(rel['sh_link']);rs={}
 for r in rel.iter_relocations():
  s=sy.get_symbol(r['r_info_sym']);name=s.name
  if not name and isinstance(s['st_shndx'],int):name=e.get_section(s['st_shndx']).name
  rs[r['r_offset']]=(name,r['r_addend'])
 def ins(a,m,o):
  x=next(md.disasm(code[a:a+4],a));need((x.mnemonic,x.op_str)==(m,o),'instruction '+hex(a))
 def cstr(blob,a):return blob[a:blob.index(0,a)].decode()
 for a in [0x11868,0x11870,0x11a28,0x11a2c]:need(rs[a]==('.rodata',0x1228),'retained x21 label-base relocation')
 need(cstr(ro,0x1228+0xca0)=='m_set_power_control','ordinary embedded power label')
 need(cstr(ro,0x1228+0xcb8)=='m_set_elvdd_onoff','separate embedded reset-print label')
 for a,m,o in [(0x11880,'add','x1, x21, #0xca0'),(0x11a0c,'add','x1, x21, #0xcb8'),(0x11b30,'add','x1, x21, #0xcb8'),
  (0x11890,'ldr','w0, [x20, #0x1a8]'),(0x11894,'cmp','w0, #1'),(0x11898,'b.ne','#0x11954'),
  (0x11954,'ldr','w1, [x20, #0x1ac]'),(0x11958,'cmp','w1, #4'),(0x1195c,'b.eq','#0x119dc'),
  (0x119e8,'cbz','x1, #0x118b4'),(0x119ec,'mov','w0, #0'),(0x119f0,'blr','x1'),
  (0x11ac4,'ldr','w0, [x20, #0x1ac]'),(0x11ac8,'cmp','w0, #4'),(0x11acc,'b.eq','#0x11b04'),
  (0x11b0c,'cbz','x1, #0x11af0'),(0x11b10,'mov','w0, #1'),(0x11b14,'blr','x1')]:ins(a,m,o)
 for a in [0x119dc,0x119e4,0x11b04,0x11b08]:need(rs[a][0]=='tztv_set_sdp_jp_tcon_power_reset','exact imported callback object')
 for a,offset,message in [(0x11a10,0x83a0,'tztv_set_sdp_jp_tcon_power_reset[0]'),(0x11b34,0x8338,'tztv_set_sdp_jp_tcon_power_reset[1]')]:
  need(rs[a]==('.rodata.str1.8',offset)and message in cstr(fmt,offset),'specific callback format')
 api=ROOT/'binaries/tztv_frc_tcon_api.ko';ab=api.read_bytes();need(sha(ab)=='3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6','API source pin')
 ae=ELFFile(io.BytesIO(ab));objects=[s for s in ae.get_section_by_name('.symtab').iter_symbols()if s.name=='tztv_set_sdp_jp_tcon_power_reset']
 need(len(objects)==1 and objects[0]['st_info']['type']=='STT_OBJECT'and objects[0]['st_size']==8 and objects[0]['st_value']==0x88,'API exports pointer object, not directly identified provider')

 frc=ROOT/'binaries/tztv_frc_tcon.ko';fb=frc.read_bytes();need(sha(fb)=='aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd','FRC source pin')
 fe=ELFFile(io.BytesIO(fb));fs=fe.get_section_by_name('.rodata.str1.8').data();ft=fe.get_section_by_name('.text').data();fr=fe.get_section_by_name('.rela.text');fst=fe.get_section(fr['sh_link']);rr={}
 for r in fr.iter_relocations():
  symbol=fst.get_symbol(r['r_info_sym']);name=symbol.name
  if not name and isinstance(symbol['st_shndx'],int):name=fe.get_section(symbol['st_shndx']).name
  rr[r['r_offset']]=(name,r['r_addend'])
 need(rr[0x57d8]==rr[0x57dc]==('.rodata.str1.8',0x51b8),'get_fn_ad loads exact lookup string')
 need(cstr(fs,0x51b8)=='sdp_ocl_reset_tcon_power','named source provider')
 need(rr[0x57e4]==('resolve_symbol',0),'lookup call')
 need(rr[0x57ec]==rr[0x57f8]==('tztv_set_sdp_jp_tcon_power_reset',0),'lookup result stored in exact API pointer')
 for a,m,o in [(0x57e8,'mov','x2, x0'),(0x57f8,'str','x2, [x1]'),(0x2ac4,'ldrsw','x0, [x19]'),(0x2ac8,'add','x19, x19, x0')]:
  x=next(md.disasm(ft[a:a+4],a));need((x.mnemonic,x.op_str)==(m,o),'provider binding instruction '+hex(a))
 need(rr[0x2ab0]==('find_symbol',0),'stock resolver uses actual symbol lookup')
 opath=B/'serdes-ack-copy-20261026/sdp_ocl_jp.ko';ob=opath.read_bytes();need(sha(ob)=='e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c','OCL source pin')
 oe=ELFFile(io.BytesIO(ob));os=list(oe.get_section_by_name('.symtab').iter_symbols())
 need(any(x.name=='sdp_ocl_reset_tcon_power'and x['st_info']['type']=='STT_FUNC'and x['st_value']==0x2b38 and x['st_size']==80 for x in os),'actual named provider function')
 need(any(x.name=='__ksymtab_sdp_ocl_reset_tcon_power'for x in os),'provider is exported to resolver')
 rawpath=B/'menu-recovery-branch-trial-20261028hf/kernel-post-mode2/archive/kernel.raw';raw=rawpath.read_bytes()
 selected=[line for line in raw.splitlines(keepends=True)if b'[6586:'in line and b'tztv_set_sdp_jp_tcon_power_reset['in line]
 need(len(selected)==2,'actual HF PID6586 retains two callback printks')
 need(all(b'm_set_elvdd_onoff[6586:'in line for line in selected),'actual embedded label matches reset-print source')
 need(any(b'power_reset[0]'in line for line in selected)and any(b'power_reset[1]'in line for line in selected),'both call roles printed')
 return dict(schema='hg-qdf-hf-label-context-v1',checks=checks,qdfSha256=sha(b),apiSha256=sha(ab),frcSha256=sha(fb),oclSha256=sha(ob),providerResolutionSourceClosed=True,rawInput={'path':str(rawpath.relative_to(ROOT)),'bytes':len(raw),'sha256':sha(raw)},callbackPrintedLineHashes=[sha(x)for x in selected],interpretation='embedded m_set_elvdd_onoff label is used at reset callback printks inside ELF function m_set_power_control; label alone is not alternative ELVDD branch evidence',actualRuntimePointerRead=False,activeProviderIdentityProven=False,electricalMeaningProven=False,targetCalls=0,networkCalls=0)
if __name__=='__main__':print(json.dumps(main(),indent=2,sort_keys=True))
