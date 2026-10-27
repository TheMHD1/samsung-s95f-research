from pathlib import Path
import hashlib,json,struct,zlib
R=Path('${S95F_EVIDENCE_ROOT}/research-20261027-external')
O=R/'reviews/swu-audit-artifacts'
p=R.parent/'panel-idle-20261026/overnight/samsung-official-T-RSMFAKUC-0090-msd-prefix.bin'
d=p.read_bytes(); expected='01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d'
if hashlib.sha256(d).hexdigest()!=expected: raise ValueError('prefix hash')
if d[242:250]!=b'Salted__': raise ValueError('marker')
c=d[258:4290]; word=struct.unpack_from('<I',d,238)[0]; crc=zlib.crc32(c)&0xffffffff
if len(c)!=4032 or len(c)%16 or crc!=word: raise ValueError('boundary/CRC')
r={'prefix':{'path':str(p),'sha256':expected,'bytes':len(d)},'envelope':[234,4290],'wrapper_words_le':list(struct.unpack_from('<II',d,234)),'marker':[242,250],'salt_range_only':[250,258],'ciphertext':[258,4290],'ciphertext_bytes':len(c),'ciphertext_sha256':hashlib.sha256(c).hexdigest(),'ciphertext_crc32':f'{crc:08x}','word_at_238_equals_ciphertext_crc32':True,'salt_value_omitted':True}
# Compare every previously inventoried source against its actual bytes; don't assume a report hash is correct.
inv=json.loads((R/'sources/swu-target-applicability/source-inventory.json').read_text())
checks=[]
for a in inv['artifacts']:
 q=Path(a['path']); actual=hashlib.sha256(q.read_bytes()).hexdigest(); checks.append({'path':str(q),'expected':a['sha256'],'actual':actual,'match':actual==a['sha256']})
r['source_inventory_checks']=checks
r['source_inventory_all_match']=all(a['match'] for a in checks)
# Acquisition manifest comparisons for the actual retained ELF files.
inputs=json.loads((O/'independent-input-hashes.json').read_text())
r['acquisition_manifest_matches']=[]
for num in ['02','03','04']:
 m=json.loads((R/f'target-file-acquisition-{num}/acquisition-manifest.json').read_text())
 for a in m['files']:
  ap=a.get('path',a.get('remote_path'))
  matches=[x for x in inputs.values() if Path(x['path']).name==Path(ap).name]
  if matches:
   ok=matches[0]['sha256']==a['sha256'] and matches[0]['bytes']==a['size']
   if not ok: raise ValueError('manifest mismatch')
   r['acquisition_manifest_matches'].append({'path':ap,'match':ok,'boot_id':m['boot_id']})
(O/'independent-boundary-and-source-verification.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({k:v for k,v in r.items() if k not in ['source_inventory_checks','acquisition_manifest_matches']},indent=2))
