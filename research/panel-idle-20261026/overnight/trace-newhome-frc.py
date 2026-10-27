#!/usr/bin/env python3
"""Offline FRC NewHome evidence. No TV calls; needs capstone/pyelftools."""
from pathlib import Path
import hashlib,json,struct,subprocess
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
P=Path(__file__).resolve().parent
B=P.parent/'binaries'
manifest={n:hashlib.sha256((B/n).read_bytes()).hexdigest() for n in ('libave.so.0.1','tztv_frc_tcon_api.ko','rosem_frc.ko','qdf_tcon.ko')}
with (B/'libave.so.0.1').open('rb') as f:
 e=ELFFile(f);md=Cs(CS_ARCH_ARM,CS_MODE_THUMB);s=e.get_section_by_name('.text');a,b=0x246848,0x246928
 (P/'newhome-frc-libave.disasm').write_text('\n'.join(f'{i.address:08x}: {i.mnemonic:9} {i.op_str}' for i in md.disasm(s.data()[a-s['sh_addr']:b-s['sh_addr']],a))+'\n')
with (B/'tztv_frc_tcon_api.ko').open('rb') as f:
 e=ELFFile(f);d=e.get_section_by_name('.rodata').data()
 rows=[{'selector':n,'branch':hex(0xa6f0+struct.unpack_from('<h',d,0x634+2*(n-1))[0]*4)} for n in range(1,55)]
 assert rows[2]['branch']=='0xa778'
(P/'newhome-frc-jumptable.json').write_text(json.dumps({'binary_sha256':manifest['tztv_frc_tcon_api.ko'],'table_rodata_offset':'0x634','base_text_offset':'0xa6f0','entry_format':'signed LE16 instruction words','rows':rows},indent=2)+'\n')
parts=[]
for name,windows in [('tztv_frc_tcon_api.ko',[(0x17ec,0x1810),(0x27bc,0x282c),(0xa6b8,0xa790),(0x7c48,0x7d64)]),('rosem_frc.ko',[(0x7bd8,0x7d20),(0x37b8,0x3a28),(0x290,0x488),(0xe50,0xf1c)])]:
 for a,b in windows:
  r=subprocess.run(['aarch64-linux-gnu-objdump','-dr','-j','.text',f'--start-address={a}',f'--stop-address={b}',str(B/name)],capture_output=True,text=True,check=True)
  parts.append(r.stdout)
for name in ('rosem_frc.ko','qdf_tcon.ko'):
 r=subprocess.run(['aarch64-linux-gnu-objdump','-dr','-j','.init.text',str(B/name)],capture_output=True,text=True,check=True)
 parts.append(r.stdout)
for a,b in [(0x10508,0x107e8),(0x11058,0x11338)]:
 r=subprocess.run(['aarch64-linux-gnu-objdump','-dr','-j','.text',f'--start-address={a}',f'--stop-address={b}',str(B/'qdf_tcon.ko')],capture_output=True,text=True,check=True)
 parts.append(r.stdout)
(P/'newhome-frc-kernel.disasm').write_text('\n'.join(parts))
(P/'newhome-frc-input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Extracted exact ioctl, selector jump table, Rosem state/rate paths; no live operation.')
