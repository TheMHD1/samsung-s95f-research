#!/usr/bin/env python3
import hashlib
from pathlib import Path
from capstone import CS_ARCH_ARM,CS_MODE_THUMB,Cs
from elftools.elf.elffile import ELFFile
p=Path(__file__).resolve().parents[1]/'binaries/libave.so.0.1'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777'
with p.open('rb') as f:
 e=ELFFile(f)
 def b(a,n):
  for s in e.iter_segments():
   if s['p_type']=='PT_LOAD' and s['p_vaddr']<=a and a+n<=s['p_vaddr']+s['p_filesz']:
    f.seek(s['p_offset']+a-s['p_vaddr']);return f.read(n)
  raise AssertionError(hex(a))
 rel={}
 for s in e.iter_sections():
  if s['sh_type']=='SHT_REL':
   st=e.get_section(s['sh_link'])
   for r in s.iter_relocations(): rel[r['r_offset']]=st.get_symbol(r['r_info_sym']).name
 assert rel[0x59f3ac]=='_ZN9QDDimming15t_vSyncCallBackEv'
 assert rel[0x5a0a10]=='_ZN12QDDimmingMNT15t_vSyncCallBackEv'
 assert rel[0x59fac4]=='_ZN22DimmingVendorInterface23t_SetFinalDuty2D_NonFRCEP19VendorFinalDuty2D_t'
 assert rel[0x5a1604]=='_ZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_t'
 def I(a,n): return {(x.address,x.mnemonic,x.op_str) for x in Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b(a,n),a)}
 v=I(0x17b55e,12); assert (0x17b564,'mov','r0, r4') in v and (0x17b566,'blx','#0x8e304') in v
 a=I(0x1742fa,8); assert (0x1742fa,'str.w','r2, [r3, #0xa8]') in a and (0x1742fe,'blx','#0x8f75c') in a
 q=I(0x174100,0x60); assert (0x174110,'ldr.w','r6, [r0, #0x2a8]') in q and (0x174118,'cmp','r6, #1') in q and (0x17415c,'str.w','r3, [r0, #0xa8]') in q
 g=I(0x17433c,0x78); assert (0x17433c,'ldr','r0, [r4, #0x10]') in g and (0x174340,'cbz','r0, #0x17438e') in g and (0x174382,'ldr','r3, [r0]') in g and (0x174384,'ldr.w','r3, [r3, #0xd8]') in g and (0x174388,'blx','r3') in g and (0x17438e,'ldr','r2, [r3]') in g and (0x174390,'cmp','r2, #1') in g and (0x174392,'bne','#0x1743b6') in g and (0x1743a0,'ldr','r0, [r4, #0xc]') in g and (0x1743b0,'ldr','r3, [r3, #0x48]') in g and (0x1743b2,'blx','r3') in g
 t=I(0x1c6288,0x42); assert (0x1c6288,'ldr.w','r8, [r6, #8]') in t and (0x1c629e,'cmp','r2, r8') in t and (0x1c62a0,'beq','#0x1c62ca') in t and (0x1c62a4,'mov.w','r1, #0xf300') in t and (0x1c62a8,'mov.w','r0, #0x128') in t and (0x1c62ac,'str.w','r8, [r3, #0x10]') in t and (0x1c62b4,'blx','#0x8db9c') in t and (0x1c62b8,'ldr','r1, [r7]') in t and (0x1c62c4,'blx','#0x9023c') in t
 assert int.from_bytes(b(0x1c6354,4),'little')==0x3e56be and 0x1c628a+0x3e56be==0x5ab948
 c=I(0x17b564,10); assert (0x17b566,'blx','#0x8e304') in c and (0x17b56a,'b','#0x17b3e4') in c
print('PASS: active QDDimming base path, resolved backend/cache/transport invariants; runtime emission/state unknown.')
