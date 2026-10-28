#!/usr/bin/env python3
"""Host-only bounded successor manifest and inventory generation."""
from pathlib import Path
import hashlib,json,re,types,difflib
P=Path(__file__).resolve().parent;B=P.parent;FN=B/'combined-event-successor-20261028fn'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(path,v):path.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
inputs=['combined-event-successor-20261028fn/'+n for n in ['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','HostTests.cs','CombinedEventSuccessor.csproj','NuGet.Config','run-once.py','parse-result.py','wake-check.py','prepare-readiness.py','host-build-checkpoint.json','source-inventory.json','deployment-manifest.json','test-key-exposure.py']]+['live-wake-onset-design-20261028fx/'+n for n in ['README.md','source-inventory.json']]+['reader-wake-checkpoints-20261028fc/test-runner.py']
save(P/'input-pins.json',{'schema':'fz-input-pins-v1','files':[{'path':n,'bytes':len((B/n).read_bytes()),'sha256':sha((B/n).read_bytes())}for n in inputs]})
files=['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','HostTests.cs','CombinedEvent81Successor.csproj','NuGet.Config','native-tests.json','fixture.json','time-fixture.json','partial-fixture.json']+['bin/Release/net6.0/CombinedEvent81Successor'+s for s in ['.dll','.deps.json','.runtimeconfig.json']]
save(P/'host-build-checkpoint.json',{'schema':'fz-host-checkpoint-v1','targetOperations':0,'nativeQualification':json.loads((P/'native-tests.json').read_bytes()),'files':{n:{'bytes':len((P/n).read_bytes()),'sha256':sha((P/n).read_bytes())}for n in files}})
p=P/'run-once.py';s=p.read_text();s=re.sub("PARSER_SHA = '[0-9a-f]{64}'","PARSER_SHA = '"+sha((P/'parse-result.py').read_bytes())+"'",s);s=re.sub("CHECKPOINT_SHA = '[0-9a-f]{64}'","CHECKPOINT_SHA = '"+sha((P/'host-build-checkpoint.json').read_bytes())+"'",s);p.write_text(s)
m=types.ModuleType('fz_wrapper');m.__file__=str(p);exec(compile(s,str(p),'exec'),m.__dict__);manifest,_=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
patch=[]
for n in ['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','HostTests.cs','CombinedEventSuccessor.csproj','parse-result.py','run-once.py','prepare-readiness.py','wake-check.py']:
 target=n.replace('CombinedEventSuccessor','CombinedEvent81Successor');patch.extend(difflib.unified_diff((FN/n).read_text().splitlines(True),(P/target).read_text().splitlines(True),fromfile='FN/'+n,tofile='FZ/'+target))
(P/'production-diff.patch').write_text(''.join(patch))
if all((P/(n+'.'+mode+'.json')).exists()for n in ['source-checks','host-validation','key-exposure']for mode in ['normal','optimized']):
 pairs={}
 for n in ['source-checks','host-validation','key-exposure']:
  a=(P/(n+'.normal.json')).read_bytes();b=(P/(n+'.optimized.json')).read_bytes()
  if a!=b:raise ValueError('normal/-O mismatch '+n)
  pairs[n]={'identical':True,'sha256':sha(a),'result':json.loads(a)}
 save(P/'qualification.json',{'schema':'fz-host-qualification-v1','targetOperations':0,'deploymentPerformed':False,'independentReviewPerformed':False,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'native':json.loads((P/'native-tests.json').read_bytes()),'normalOptimized':pairs})
paths=sorted([p for p in P.iterdir()if p.is_file()and p.name!='source-inventory.json']+[P/n for n in files if n.startswith('bin/')]);save(P/'source-inventory.json',{'schema':'fz-source-inventory-v1','targetOperations':0,'files':[{'path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in paths]})
