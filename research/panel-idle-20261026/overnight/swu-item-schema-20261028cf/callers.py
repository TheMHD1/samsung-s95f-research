import inspect_core as c
import bisect,json,sys
wanted={int(x,0) for x in sys.argv[1:]};found=[]
text=c.elf.get_section_by_name('.text')
for i in c.thumb.disasm(text.data(),text['sh_addr']):
 if i.mnemonic in ('bl','blx','b.w') and i.op_str.startswith('#') and int(i.op_str[1:],0) in wanted:
  found.append({'call':hex(i.address),'target':i.op_str,'exidx':hex(c.functions[bisect.bisect_right(c.functions,i.address)-1])})
print(json.dumps(found,indent=2))
