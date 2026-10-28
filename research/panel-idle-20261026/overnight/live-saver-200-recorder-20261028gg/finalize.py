#!/usr/bin/env python3
"""GG local-only source/native manifest generation; no root transport import."""
import difflib,hashlib,json,re,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;FN=B/'combined-event-successor-20261028fn';GA=B/'live-saver-onset-adapter-20261028ga'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def save(p,value):p.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
inputs=['combined-event-successor-20261028fn/'+name for name in ['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','HostTests.cs','CombinedEventSuccessor.csproj','NuGet.Config','parse-result.py','run-once.py','prepare-readiness.py','host-build-checkpoint.json','source-inventory.json','deployment-manifest.json','test-key-exposure.py']]
inputs+=['live-saver-onset-adapter-20261028ga/'+name for name in ['run-once.py','cached-check.py','prepare-readiness.py','input-pins.json','source-inventory.json','deployment-manifest.json','README.md']]
inputs+=['reader-wake-checkpoints-20261028fc/test-runner.py','managed-ui-tab-launch/root-with-margin.py','wake-window-trial-20261028gc/identity-01/identity.json','combined-event-checkpoints-20261028fg/parse-result.py']
save(P/'input-pins.json',{'schema':'gg-input-pins-v1','files':[{'path':name,'bytes':len((B/name).read_bytes()),'sha256':sha((B/name).read_bytes())}for name in inputs]})
files=['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','HostTests.cs','CombinedEvent200.csproj','NuGet.Config','native-tests.json','fixture.json','branch-fixtures.json']+['bin/Release/net6.0/CombinedEvent200'+s for s in ['.dll','.deps.json','.runtimeconfig.json']]
native=json.loads((P/'native-tests.json').read_bytes());save(P/'host-build-checkpoint.json',{'schema':'gg-host-checkpoint-v1','targetOperations':0,'nativeQualification':native,'files':{name:{'bytes':len((P/name).read_bytes()),'sha256':sha((P/name).read_bytes())}for name in files}})
s=(P/'run-once.py').read_text();s=re.sub("PARSER_SHA = '[^']+'","PARSER_SHA = '"+sha((P/'parse-result.py').read_bytes())+"'",s);s=re.sub("CHECKPOINT_SHA = '[^']+'","CHECKPOINT_SHA = '"+sha((P/'host-build-checkpoint.json').read_bytes())+"'",s);(P/'run-once.py').write_text(s)
production={name:(FN/name)for name in ['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','HostTests.cs','parse-result.py']};production.update({'run-once.py':GA/'run-once.py','cached-check.py':GA/'cached-check.py','prepare-readiness.py':GA/'prepare-readiness.py','CombinedEvent200.csproj':FN/'CombinedEventSuccessor.csproj'})
deltas={};patch=[]
for name,base in production.items():
 old=base.read_text().splitlines(True);new=(P/name).read_text().splitlines(True);hunks=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
  if tag!='equal':hunks.append({'oldStart':a,'oldEnd':b,'old':''.join(old[a:b]),'new':''.join(new[c:d])})
 deltas[name]={'base':str(base.relative_to(B)),'hunks':hunks};patch.extend(difflib.unified_diff(old,new,fromfile=str(base.relative_to(B)),tofile='GG/'+name))
save(P/'production-delta.json',{'schema':'gg-production-delta-v1','files':deltas,'fixedPrimaryThreshold':200,'thresholdWrites':0,'wrapperKeys':0})
(P/'production-diff.patch').write_text(''.join(patch))
m=types.ModuleType('gg_wrapper');m.__file__=str(P/'run-once.py');exec(compile((P/'run-once.py').read_bytes(),m.__file__,'exec'),m.__dict__);manifest,_=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
if '--sources-only'not in sys.argv and all((P/(name+'.'+mode+'.json')).exists()for name in ['source-validation','host-validation','key-validation']for mode in ['normal','optimized']):
 results={}
 for name in ['source-validation','host-validation','key-validation']:
  raw=(P/(name+'.normal.json')).read_bytes();other=(P/(name+'.optimized.json')).read_bytes()
  if raw!=other:raise ValueError('normal/-O mismatch '+name)
  results[name]={'sha256':sha(raw),'normalOptimizedIdentical':True,'result':json.loads(raw)}
 save(P/'qualification.json',{'schema':'gg-host-qualification-v1','native':native,'validation':results,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'targetOperations':0,'networkOperations':0,'deployed':False,'matchedCausalEffectEstablished':False,'thresholdWriterIncluded':False})
paths=sorted([f for f in P.iterdir()if f.is_file()and f.name!='source-inventory.json']+[P/name for name in files if name.startswith('bin/')]);save(P/'source-inventory.json',{'schema':'gg-source-inventory-v1','files':[{'path':str(f.relative_to(P)),'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in paths]})
