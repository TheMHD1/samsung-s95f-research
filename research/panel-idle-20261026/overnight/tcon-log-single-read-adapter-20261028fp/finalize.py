#!/usr/bin/env python3
"""FP author-only local metadata generation. Does not import a root transport."""
from pathlib import Path
import hashlib,json,types
P=Path(__file__).resolve().parent;B=P.parent;K=B/'tcon-log-single-read-20261028fk'
sha=lambda b:hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b)}
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
inputs=['tcon-log-single-read-20261028fk/'+n for n in ['Program.cs','README.md','host-build-checkpoint.json','source-inventory.json','input-pins.json','parse-receipt.py','fixture.json','native-tests.json','host-validation.normal.json','reviews/independent-source-review.md','reviews/independent-validation.json','reviews/independent-inventory.json']]
inputs += ['tcon-log-single-read-20261028fk/'+str(p.relative_to(K))for p in sorted((K/'bin/Release/net6.0').iterdir())if p.name in ['TconLogSingleRead.dll','TconLogSingleRead.deps.json','TconLogSingleRead.runtimeconfig.json']]
inputs += ['tcon-log-runtime-metadata-20261028fj/'+n for n in ['metadata.txt','qualification.json','record.json']]
inputs += ['decision-probe-plan-20261028fd/'+n for n in ['README.md','source-audit.json','input-pins.json']]
inputs += ['managed-ui-tab-launch/root-with-margin.py','managed-tcon-status-read/run-status-read.py','managed-usb-rt-passive-observer/run-once.py','../../root-access/s95f-access.py']
write(P/'input-pins.json',{'schema':'fp-input-pins-v1','targetReads':0,'files':[dict(path=n,**pin(B/n))for n in inputs]})
write(P/'host-build-checkpoint.json',{'schema':'fp-host-build-checkpoint-v1','targetReads':0,'nativeRebuilt':False,'payloadOwner':'tcon-log-single-read-20261028fk','fkCheckpoint':pin(K/'host-build-checkpoint.json'),'payload':[dict(path=str(p.relative_to(B)),**pin(p))for p in sorted((K/'bin/Release/net6.0').iterdir())if p.name.startswith('TconLogSingleRead.')],'rootAdapter':pin(B/'managed-ui-tab-launch/root-with-margin.py')})
p=P/'run-once.py';m=types.ModuleType('fp_metadata');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);manifest,_=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
families=['host-validation','source-checks']
if all((P/(n+'.'+mode+'.json')).exists()for n in families for mode in ['normal','optimized']):
 pairs={}
 for n in families:
  a=(P/(n+'.normal.json')).read_bytes();b=(P/(n+'.optimized.json')).read_bytes()
  if a!=b:raise ValueError('normal/optimized mismatch '+n)
  pairs[n]={'identical':True,'sha256':sha(a),'result':json.loads(a)}
 write(P/'qualification.json',{'schema':'fp-qualification-v1','actualTargetReadPerformed':False,'targetRootCalls':0,'targetDeploymentPerformed':False,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'normalOptimized':pairs})
write(P/'source-inventory.json',{'schema':'fp-source-inventory-v1','actualTargetReadPerformed':False,'files':[dict(path=p.name,**pin(p))for p in sorted(P.iterdir())if p.is_file()and p.name!='source-inventory.json']})
