#!/usr/bin/env python3
"""Local derived manifest/delta/inventory generation; no transport imports."""
import difflib,hashlib,json,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;FN=B/'combined-event-successor-20261028fn'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
inputs=['reader-live-trigger-design-20261028ft/'+n for n in ['README.md','check.py','input-pins.json','validation.json','source-inventory.json']]
inputs+=['combined-event-successor-20261028fn/'+n for n in ['run-once.py','wake-check.py','prepare-readiness.py','parse-result.py','host-build-checkpoint.json','source-inventory.json','deployment-manifest.json','Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','qualification.json']]
inputs+=['combined-event-successor-20261028fn/bin/Release/net6.0/CombinedEventSuccessor'+s for s in ['.dll','.deps.json','.runtimeconfig.json']]
inputs+=['reader-wake-checkpoints-20261028fc/test-runner.py','ui-navigation-20261027br/navigate.py','managed-ui-tab-launch/root-with-margin.py']
inputs+=['combined-event-successor-trial-20261028fo/capture-01/'+n for n in ['native.receipt.json','baseline-ring.bin','post-ring.bin','readiness-decision.json']]+['combined-event-trial-20261028fh/capture-01/native.receipt.json']
save(P/'input-pins.json',{'schema':'fu-input-pins-v1','files':[{'path':n,'bytes':len((B/n).read_bytes()),'sha256':sha((B/n).read_bytes())}for n in inputs]})
files={};patch=[]
for name in ['run-once.py','wake-check.py','prepare-readiness.py']:
 old=(FN/name).read_text().splitlines(True);new=(P/name).read_text().splitlines(True);hunks=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
  if tag!='equal':hunks.append({'oldStart':a,'oldEnd':b,'old':''.join(old[a:b]),'new':''.join(new[c:d])})
 files[name]=hunks;patch.extend(difflib.unified_diff(old,new,fromfile='FN/'+name,tofile='FU/'+name))
save(P/'production-delta.json',{'schema':'fu-production-delta-v1','base':'combined-event-successor-20261028fn','files':files,'nativeSourceParserAndPayloadChanges':0,'nativeExecutionFlowChanges':0,'prepareKeysSeparate':True})
(P/'production-diff.patch').write_text(''.join(patch))
m=types.ModuleType('fu_wrapper');m.__file__=str(P/'run-once.py');exec(compile((P/'run-once.py').read_bytes(),m.__file__,'exec'),m.__dict__);manifest,payload=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
save(P/'host-build-checkpoint.json',{'schema':'fu-external-native-checkpoint-v1','nativeFamily':'fn','nativeDirectory':str(FN),'nativeCheckpointSha256':m.CHECKPOINT_SHA,'nativeParserSha256':m.PARSER_SHA,'files':{n:{'bytes':len(v),'sha256':sha(v)}for n,v in payload.items()},'nativeRebuilt':False,'targetOperations':0})
if all((P/(n+'.'+mode+'.json')).is_file()for n in ['source-validation','host-validation']for mode in ['normal','optimized']):
 results={}
 for n in ['source-validation','host-validation']:
  a=(P/(n+'.normal.json')).read_bytes();b=(P/(n+'.optimized.json')).read_bytes()
  if a!=b:raise ValueError('normal/-O mismatch '+n)
  results[n]={'normalSha256':sha(a),'optimizedSha256':sha(b),'identical':True,'result':json.loads(a)}
 save(P/'qualification.json',{'schema':'fu-host-qualification-v1','targetOperations':0,'targetDeploymentPerformed':False,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'normalOptimized':results})
paths=sorted(p for p in P.iterdir()if p.is_file()and p.name!='source-inventory.json')
save(P/'source-inventory.json',{'schema':'fu-source-inventory-v1','targetOperations':0,'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in paths]})
