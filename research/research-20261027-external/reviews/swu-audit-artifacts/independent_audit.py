from pathlib import Path
import hashlib,json,struct,zlib
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from elftools.elf.elffile import ELFFile
R=Path('${S95F_EVIDENCE_ROOT}/research-20261027-external')
O=R/'reviews/swu-audit-artifacts'
files={'wrapper':'target-file-acquisition-02/libteec.so','backend':'target-file-acquisition-02/libteec_trustware.so','common':'target-file-acquisition-04/libteec_trustware_common.so','core':'target-file-acquisition-03/SWUCoreTV','config':'target-file-acquisition-03/libSWUProductionConfig.so'}
manifest={}
for name,p in files.items():
 p=R/p; d=p.read_bytes(); manifest[name]={'path':str(p),'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()}
 with p.open('rb') as f:
  e=ELFFile(f); seg=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
  def read(va,n):
   for s in seg:
    if s['p_vaddr']<=va and va+n<=s['p_vaddr']+s['p_filesz']:
     q=s['p_offset']+va-s['p_vaddr']; return d[q:q+n]
   raise ValueError(hex(va))
  evidence_checks={
   'common':[(0x209b6,'07f13803'),(0x209c0,'bb63'),(0x164a8,'9363'),(0x15016,'cb00')],
   'backend':[(0x5954,'a36b')],
   'core':[(0x3fc2e8,'21222222000000000000000000000001'),(0x431fa4,'53616c7465645f5f'),(0x245900,'40f60d56c0f20116'),(0x245f2e,'40f60d66c0f20206'),(0x245dd2,'40f20e2c')]
  }
  for va,h in evidence_checks.get(name,[]):
   if read(va,len(bytes.fromhex(h)))!=bytes.fromhex(h): raise ValueError(name+' byte check '+hex(va))
  manifest[name]['instruction_and_data_checks']=[hex(va) for va,h in evidence_checks.get(name,[])]
  syms=list(e.get_section_by_name('.dynsym').iter_symbols()); md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
  selected=[]
  for s in syms:
   n=s.name
   if s['st_info']['type']=='STT_FUNC' and s['st_shndx']!='SHN_UNDEF' and s['st_size'] and ((name=='common' and any(k in n for k in ['teecOperationWrapper','teecOperationCancellation','insertOperation','insertMemory','insertContext','insertSession','handlePartialMemref','teecSession13invokeCommand'])) or (name=='backend' and n.startswith('TEEC_'))): selected.append((s['st_value']&~1,s['st_size'],n))
  ranges={'backend':[(0x3c64,0x28c,'invoke_internal'),(0x30f4,0xd4,'validate_shared_memory'),(0x5c20,0x70,'cancel')], 'core':[(0x1d503c,0x78,'header_record_factory_caller'),(0x243030,0x1b2,'engine_factory'),(0x244e7c,0x90,'platform_ctor_forwarder'),(0x1d68d0,0x90,'header_first_record_consumption'),(0x245594,0x288,'open'),(0x24581c,0x57c,'init'),(0x245d98,0x140,'final'),(0x245ed8,0x1c0,'update'),(0x246d20,0x1c0,'ctor'),(0x1d614c,0x420,'header_decrypt'),(0x244698,0x90,'get_items_blob')], 'config':[(0x42df03bc,4,'isProduction')]}
  selected+=ranges.get(name,[])
  lines=[]
  for va,size,label in selected:
   lines.append('\n'+label+' '+hex(va)+' size '+str(size))
   for i in md.disasm(read(va,size),va): lines.append(f'{i.address:08x} {i.bytes.hex():10} {i.mnemonic:10} {i.op_str}')
  (O/(name+'-independent-disassembly.txt')).write_text('\n'.join(lines)+'\n')
  (O/(name+'-symbols.txt')).write_text('\n'.join(f"{s['st_value']:08x} {s['st_size']:6} {s.name}" for s in syms if s['st_info']['type']=='STT_FUNC' and any(k in s.name for k in ['TEEC_','Operation','handlePartial','insertMemory','insertContext','insertSession','isProduction','TrustZone']))+'\n')
(O/'independent-input-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
