#!/usr/bin/env python3
"""Host-only FV sealing. Does not import a live root transport."""
import hashlib,json,os,types
from pathlib import Path
os.umask(0o077)
P=Path(__file__).resolve().parent;B=P.parent
def row(p):
 b=p.read_bytes();return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(name,v):(P/name).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
names=['internal-log-trial-20261028fs/'+n for n in ['guard-metadata-01/metadata.txt','guard-metadata-01/comparison.json','guard-metadata-01/record.json','capture-guard-metadata.py','preflight-refusal-reconciliation.json','refusal-analysis/README.md','refusal-analysis/source-inventory.json']]
save('input-pins.json',{'schema':'fv-runtime-input-pins-v1','privateRawMetadataNotForPublication':True,'files':[dict(path=n,**row(B/n))for n in names]})
m=types.ModuleType('fv_sealing');m.__file__=str(P/'run-once.py');exec(compile((P/'run-once.py').read_bytes(),m.__file__,'exec'),m.__dict__)
manifest,_,_=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.raw_manifest(manifest))
if all((P/('qualification.'+mode+'.json')).exists()for mode in ['normal','optimized']):
 a=(P/'qualification.normal.json').read_bytes();b=(P/'qualification.optimized.json').read_bytes()
 if a!=b:raise ValueError('normal optimized mismatch')
 save('host-qualification.json',{'schema':'fv-sealed-qualification-v1','manifestSha256':row(P/'deployment-manifest.json')['sha256'],'normalOptimizedByteIdentical':True,'result':json.loads(a),'rootCalls':0,'targetReads':0})
save('source-inventory.json',{'schema':'fv-source-inventory-v1','targetReads':0,'files':[dict(path=p.name,**row(p))for p in sorted(P.iterdir())if p.is_file()and p.name!='source-inventory.json']})
for p in P.iterdir():
 if p.is_file():p.chmod(0o600)
