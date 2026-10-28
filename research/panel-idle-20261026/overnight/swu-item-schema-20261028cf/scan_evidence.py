#!/usr/bin/env python3
import inspect_core as c
import struct,re,json,bisect
text=c.elf.get_section_by_name('.text');insns=list(c.thumb.disasm(text.data(),text['sh_addr']))
# Static direct calls and PC-relative/GOT literal references; candidates only.
refs=[];calls=[]
tags=json.loads((c.ROOT.parent/'swu-header-validation-20261027bx/descriptor-factory.json').read_text())
vt=[int(x['vtable'],16) for t in tags for x in t['candidates']]
rtti={c.word(x+4):x for x in vt}
gotvals={c.word(0x4ca000+i):i for i in range(0,0x5800,4)}
selected={a for a,v in rtti.items()}|set(vt)
for ins in insns:
 if ins.mnemonic in ('bl','blx') and ins.op_str.startswith('#'):
  dest=int(ins.op_str[1:],0)
  if dest in (0x29fc70,0x29fe14,0x2aa634,0x2a3768,0x2a2874) or dest in c.plt and c.plt[dest]=='__dynamic_cast':calls.append({'at':hex(ins.address),'target':hex(dest),'name':c.plt.get(dest),'function_exidx':hex(c.functions[bisect.bisect_right(c.functions,ins.address)-1])})
 m=re.fullmatch(r'[^,]+, \[pc, #(0x[0-9a-f]+|[0-9]+)\]',ins.op_str)
 if ins.mnemonic in ('ldr','ldr.w') and m:
  try:
   value=c.word(((ins.address+4)&~3)+int(m[1],0));dest=c.word(0x4ca000+value) if value<0x5800 else value
   if dest in selected:refs.append({'at':hex(ins.address),'literal':hex(value),'destination':hex(dest),'vtable':hex(rtti.get(dest,dest)),'function_exidx':hex(c.functions[bisect.bisect_right(c.functions,ins.address)-1])})
  except ValueError:pass
out={'core_sha256':c.EXPECTED,'descriptor_rtti':{hex(k):hex(v) for k,v in rtti.items()},'references_candidates':refs,'calls':calls}
(c.ROOT/'descriptor-consumer-candidates.json').write_text(json.dumps(out,indent=2)+'\n')
for r in refs:
 if r['vtable']=='0x4c19c4':print(r)
