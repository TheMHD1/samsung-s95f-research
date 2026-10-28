#!/usr/bin/env python3
"""Derive factory tag -> ctor -> RTTI/vtable/serializer anchors. Static only."""
import inspect_core as c
import re,struct,json
out=[]
for tag in range(1,63):
 target=0x2a088c+2*struct.unpack('<H',c.read(0x2a088c+(tag-1)*2,2))[0]
 if target==0x2a0908:continue
 ctor=None
 for ins in c.thumb.disasm(c.read(target,100),target):
  if ins.mnemonic=='bl' and ins.op_str.startswith('#') and int(ins.op_str[1:],0) not in c.plt:
   ctor=int(ins.op_str[1:],0);break
 if not ctor:continue
 start,end=c.disassemble(ctor)
 choices=[]
 for ins in c.thumb.disasm(c.read(ctor,end-ctor),ctor):
  m=re.fullmatch(r'[^,]+, \[pc, #(0x[0-9a-f]+|[0-9]+)\]',ins.op_str)
  if ins.mnemonic in ('ldr','ldr.w') and m:
   try:
    lit=c.word(((ins.address+4)&~3)+int(m[1],0))
    if lit>=0x10000:continue
    v=c.word(0x4ca000+lit)
    if c.word(v)!=0:continue
    rt=c.word(v+4);name=c.string(c.word(rt+4))
    if name and 'ObjectUpgrade' in name and 'Desc' in name and not name.endswith('IDescriptorE'):
     choices.append({'vtable':hex(v),'rtti_name':name,'serializer':hex(c.word(v+0x28)&~1)})
   except ValueError:pass
 out.append({'tag':tag,'factory_branch':hex(target),'constructor':hex(ctor),'candidates':choices})
(c.ROOT/'descriptor-factory.json').write_text(json.dumps(out,indent=2)+'\n')
for x in out:print(x)
