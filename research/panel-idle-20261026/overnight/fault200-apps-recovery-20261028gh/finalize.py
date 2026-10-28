#!/usr/bin/env python3
"""GH local-only sealing. No transport/native execution or native rebuild."""
import difflib,hashlib,json,types,sys
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;GE=B/'live-saver-init-adapter-20261028ge'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
base=json.loads((GE/'input-pins.json').read_bytes())['files'];paths=[r['path']for r in base]
paths+=['live-saver-init-adapter-20261028ge/'+n for n in ['run-once.py','helper.py','policy.py','admit-fault.py','prepare-readiness.py','README.md','deployment-manifest.json','source-inventory.json','input-pins.json']]
paths+=['refresh-checkpoint-trial-20261028ei/recover-eb-fault.py','recovery-quickpath-20261027bv/recover.py','ui-navigation-20261027br/navigate.py']
actual=B/'live-saver-wake-trial-20261028gf/fault-capture';paths+=[str(f.relative_to(B))for f in actual.iterdir()if f.is_file()]
paths+=[str(Path(r['path']).relative_to(B))for r in json.loads((actual/'readiness-decision.json').read_bytes())['evidence']]
paths=sorted(set(paths));save(P/'input-pins.json',{'schema':'gh-input-pins-v1','files':[{'path':path,'bytes':len((B/path).read_bytes()),'sha256':sha((B/path).read_bytes())}for path in paths]})
all_hunks=[];patch=[]
for name in ['run-once.py','helper.py','policy.py','admit-fault.py','prepare-readiness.py']:
 old=(GE/name).read_text().splitlines(True);new=(P/name).read_text().splitlines(True);hunks=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
  if tag!='equal':hunks.append({'oldStart':a,'oldEnd':b,'old':''.join(old[a:b]),'new':''.join(new[c:d])})
 all_hunks.append({'base':'live-saver-init-adapter-20261028ge/'+name,'output':name,'hunks':hunks})
 patch.extend(difflib.unified_diff(old,new,fromfile='GE/'+name,tofile='GH/'+name))
save(P/'production-delta.json',{'schema':'gh-production-delta-v1','files':all_hunks,'nativeChanges':0,'uiOperations':0,'sourceLimitBefore':40,'sourceLimitAfter':200,'cachedContextBefore':'Live+saver+CSFS','cachedContextAfter':'Apps+noSaver+CSFS'})
(P/'production-diff.patch').write_text(''.join(patch))
m=types.ModuleType('gh_manifest');m.__file__=str(P/'run-once.py');exec(compile((P/'run-once.py').read_bytes(),m.__file__,'exec'),m.__dict__)
manifest,payload=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
save(P/'host-build-checkpoint.json',{'schema':'gh-external-native-checkpoint-v1','nativeRebuilt':False,'nativeBuildDirectory':'autonomous-fault-harness-20261028dh/deadline-mode2','payloads':manifest['nativePayloads'],'nativeDeadlineSeconds':12,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'targetOperations':0})
if '--sources-only'not in sys.argv and all((P/(name+'.'+mode+'.json')).is_file()for name in ['source-validation','host-validation']for mode in ['normal','optimized']):
 results={}
 for name in ['source-validation','host-validation']:
  raw=(P/(name+'.normal.json')).read_bytes();other=(P/(name+'.optimized.json')).read_bytes()
  if raw!=other:raise ValueError('normal/-O mismatch')
  results[name]={'sha256':sha(raw),'normalOptimizedIdentical':True,'result':json.loads(raw)}
 save(P/'qualification.json',{'schema':'gh-host-qualification-v1','targetOperations':0,'networkOperations':0,'deployed':False,'actualFault200Observed':False,'mode2Under200ProfileEmpiricallyQualified':False,'restoresLimit40Proven':False,'positiveProfileFixture':'explicitly reconstructed from actual GF40; not runtime evidence','newInstanceOrFreshEbQualified':False,'independentReviewClaimed':False,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'validation':results})
files=sorted(f for f in P.iterdir()if f.is_file()and f.name!='source-inventory.json');save(P/'source-inventory.json',{'schema':'gh-source-inventory-v1','files':[{'path':f.name,'bytes':f.stat().st_size,'sha256':sha(f.read_bytes())}for f in files]})
