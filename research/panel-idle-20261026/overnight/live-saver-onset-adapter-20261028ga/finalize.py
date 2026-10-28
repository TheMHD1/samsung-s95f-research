#!/usr/bin/env python3
"""Derive local source delta, exact manifest and inventory; no root import."""
import difflib,hashlib,json,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;FN=B/'combined-event-successor-20261028fn'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
inputs=['live-wake-onset-design-20261028fx/'+n for n in ['README.md','verify.py','input-pins.json','source-inventory.json','validation.normal.json','validation.optimized.json']]
inputs+=['combined-event-successor-20261028fn/'+n for n in ['run-once.py','wake-check.py','prepare-readiness.py','parse-result.py','host-build-checkpoint.json','source-inventory.json','deployment-manifest.json','Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','qualification.json']]
inputs+=['combined-event-successor-20261028fn/bin/Release/net6.0/CombinedEventSuccessor'+s for s in ['.dll','.deps.json','.runtimeconfig.json']]
inputs+=['combined-live-trigger-adapter-20261028fu/'+n for n in ['README.md','run-once.py','prepare-readiness.py','wake-check.py','deployment-manifest.json']]
inputs+=['reader-wake-checkpoints-20261028fc/test-runner.py','managed-ui-tab-launch/root-with-margin.py']
inputs+=['combined-event-successor-trial-20261028fo/capture-01/'+n for n in ['native.receipt.json','baseline-ring.bin','post-ring.bin','readiness-decision.json']]
inputs+=['combined-live-trigger-trial-20261028fw/capture-01/'+n for n in ['native.receipt.json','readiness-decision.json']]
save(P/'input-pins.json',{'schema':'ga-input-pins-v1','files':[{'path':n,'bytes':len((B/n).read_bytes()),'sha256':sha((B/n).read_bytes())}for n in inputs]})
files={};patch=[]
for old_name,new_name in [('run-once.py','run-once.py'),('wake-check.py','cached-check.py'),('prepare-readiness.py','prepare-readiness.py')]:
 old=(FN/old_name).read_text().splitlines(True);new=(P/new_name).read_text().splitlines(True);hunks=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
  if tag!='equal':hunks.append({'oldStart':a,'oldEnd':b,'old':''.join(old[a:b]),'new':''.join(new[c:d])})
 files[new_name]={'base':old_name,'hunks':hunks};patch.extend(difflib.unified_diff(old,new,fromfile='FN/'+old_name,tofile='GA/'+new_name))
save(P/'production-delta.json',{'schema':'ga-production-delta-v1','base':'combined-event-successor-20261028fn','files':files,'nativeSourceParserAndPayloadChanges':0,'wrapperKeys':0,'liveSaverMode2Implemented':False})
(P/'production-diff.patch').write_text(''.join(patch))
m=types.ModuleType('ga_wrapper');m.__file__=str(P/'run-once.py');exec(compile((P/'run-once.py').read_bytes(),m.__file__,'exec'),m.__dict__);manifest,payload=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
save(P/'host-build-checkpoint.json',{'schema':'ga-external-native-checkpoint-v1','nativeFamily':'fn','nativeDirectory':str(FN),'nativeCheckpointSha256':m.CHECKPOINT_SHA,'nativeParserSha256':m.PARSER_SHA,'files':{n:{'bytes':len(raw),'sha256':sha(raw)}for n,raw in payload.items()},'nativeRebuilt':False,'targetOperations':0})
if all((P/(name+'.'+mode+'.json')).is_file()for name in ['source-validation','host-validation']for mode in ['normal','optimized']):
 results={}
 for name in ['source-validation','host-validation']:
  a=(P/(name+'.normal.json')).read_bytes();b=(P/(name+'.optimized.json')).read_bytes()
  if a!=b:raise ValueError('normal/-O mismatch '+name)
  results[name]={'normalSha256':sha(a),'optimizedSha256':sha(b),'identical':True,'result':json.loads(a)}
 save(P/'qualification.json',{'schema':'ga-host-qualification-v1','targetOperations':0,'targetDeploymentPerformed':False,'liveSaverCleanPremiseQualified':False,'liveSaverMode2Implemented':False,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'normalOptimized':results})
paths=sorted(p for p in P.iterdir()if p.is_file()and p.name!='source-inventory.json')
save(P/'source-inventory.json',{'schema':'ga-source-inventory-v1','targetOperations':0,'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in paths]})
