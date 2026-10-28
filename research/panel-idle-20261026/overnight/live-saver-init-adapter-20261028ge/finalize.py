#!/usr/bin/env python3
"""GE local-only source/manifest sealing; no live transport load."""
import difflib,hashlib,json,types,sys
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
base=json.loads((B/'live-saver-init-design-20261028gb/input-pins.json').read_bytes())['files'];paths=[r['path']for r in base]
paths+=['live-saver-init-design-20261028gb/'+n for n in ['README.md','verify.py','input-pins.json','source-inventory.json']]
paths+=['live-saver-onset-adapter-20261028ga/prepare-readiness.py']
paths+=['combined-live-trigger-trial-20261028fw/recovery-01/mode2/'+n for n in ['framed.txt','receipt.txt']]
paths+=['rtp-lane-gate-capture-20261028eb/'+n for n in ['run-once.py','deployment-manifest.json','source-inventory.json']]
paths=sorted(set(paths));save(P/'input-pins.json',{'schema':'ge-input-pins-v1','files':[{'path':path,'bytes':len((B/path).read_bytes()),'sha256':sha((B/path).read_bytes())}for path in paths]})
old=(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py').read_text().splitlines(True);new=(P/'helper.py').read_text().splitlines(True);hunks=[]
for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
 if tag!='equal':hunks.append({'oldStart':a,'oldEnd':b,'old':''.join(old[a:b]),'new':''.join(new[c:d])})
save(P/'production-delta.json',{'schema':'ge-helper-delta-v1','base':'autonomous-fault-harness-20261028dh/run-deadline-mode2.py','hunks':hunks,'nativeChanges':0,'uiOperations':0})
(P/'production-diff.patch').write_text(''.join(difflib.unified_diff(old,new,fromfile='DH/run-deadline-mode2.py',tofile='GE/helper.py')))
m=types.ModuleType('ge_manifest');m.__file__=str(P/'run-once.py');exec(compile((P/'run-once.py').read_bytes(),m.__file__,'exec'),m.__dict__)
manifest,payload=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
save(P/'host-build-checkpoint.json',{'schema':'ge-external-native-checkpoint-v1','nativeRebuilt':False,'nativeBuildDirectory':'autonomous-fault-harness-20261028dh/deadline-mode2','payloads':manifest['nativePayloads'],'nativeDeadlineSeconds':12,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'targetOperations':0})
if '--sources-only'not in sys.argv and all((P/(name+'.'+mode+'.json')).is_file()for name in ['source-validation','host-validation']for mode in ['normal','optimized']):
 results={}
 for name in ['source-validation','host-validation']:
  raw=(P/(name+'.normal.json')).read_bytes();other=(P/(name+'.optimized.json')).read_bytes()
  if raw!=other:raise ValueError('normal/-O mismatch')
  results[name]={'sha256':sha(raw),'normalOptimizedIdentical':True,'result':json.loads(raw)}
 save(P/'qualification.json',{'schema':'ge-host-qualification-v1','targetOperations':0,'networkOperations':0,'deployed':False,'liveSaverPremiseQualified':False,'newInstanceOrFreshEbQualified':False,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'validation':results})
files=sorted(f for f in P.iterdir()if f.is_file()and f.name!='source-inventory.json');save(P/'source-inventory.json',{'schema':'ge-source-inventory-v1','files':[{'path':f.name,'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in files]})
