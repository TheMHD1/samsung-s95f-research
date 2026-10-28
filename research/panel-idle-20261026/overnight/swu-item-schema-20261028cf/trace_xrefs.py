#!/usr/bin/env python3
"""Static PC-relative ASCII references in exact pinned Core; heuristic candidates only."""
import inspect_core as c
import re,json
text=c.elf.get_section_by_name('.text')
loaded={};found=[]
for ins in c.thumb.disasm(text.data(),text['sh_addr']):
 m=re.fullmatch(r'(r\d+|ip|lr|sb|sl|fp), \[pc, #(0x[0-9a-f]+|[0-9]+)\]',ins.op_str)
 if ins.mnemonic in ('ldr','ldr.w') and m:
  try:loaded[m[1]]=(c.word(((ins.address+4)&~3)+int(m[2],0)),ins.address)
  except ValueError:pass
 m=re.fullmatch(r'(r\d+|ip|lr|sb|sl|fp), pc',ins.op_str)
 if ins.mnemonic=='add' and m and m[1] in loaded:
  v,at=loaded[m[1]]
  if ins.address-at<128:
   addr=(ins.address+4+v)&0xffffffff;s=c.string(addr)
   if s and re.search(r'OUIT|OUHeader|[Pp]adding|[Dd]escriptor|[Hh]eader|RSA|AES|[Ss]alt|[Pp]assphrase|[Cc]rypto|CUpgradeGraphBuilder|OUUpgradeItem|OUGroup',s):
    found.append({'instruction':hex(ins.address),'literal_instruction':hex(at),'string_address':hex(addr),'string':s})
  del loaded[m[1]]
(c.ROOT/'string-xrefs.json').write_text(json.dumps(found,indent=2)+'\n')
print(len(found))
