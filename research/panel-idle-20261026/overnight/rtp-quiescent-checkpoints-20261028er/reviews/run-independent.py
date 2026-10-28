#!/usr/bin/env python3
"""Independent host-only tests for the frozen ER candidate."""
import os,sys,json,hashlib,subprocess,types
from pathlib import Path
P=Path(__file__).resolve().parent.parent;R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
expected_inventory='24d3705adf0537690c55c3383548c18e12a884079fcccbf22b64808202b3be43'
def frozen():
 raw=(P/'source-inventory.json').read_bytes()
 if sha(raw)!=expected_inventory:raise ValueError('inventory pin')
 rows=json.loads(raw)['files']
 for row in rows:
  data=(P/row['path']).read_bytes()
  if len(data)!=row['bytes']or sha(data)!=row['sha256']:raise ValueError('changed '+row['path'])
 return len(rows)
n=frozen();results=[]
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(R/'tmp'))
for opt in [[],['-O']]:
 for name in ['verify_source.py','test-parse-result.py','test-quiescent.py','test-timing.py','test-readiness.py','test-runner.py','reviews/test-extra.py']:
  label=Path(name).name.removesuffix('.py')+('-optimized'if opt else '-normal')
  command=[sys.executable,*opt,'-B',str(P/name)]
  if name=='test-readiness.py':
   bootstrap="import tempfile,runpy,sys; old=tempfile.TemporaryDirectory; tempfile.TemporaryDirectory=lambda *a,**k:old(*a,**dict(k,dir=sys.argv[1])); runpy.run_path(sys.argv[2],run_name='__main__')"
   command=[sys.executable,*opt,'-B','-c',bootstrap,str(R/'tmp'),str(P/name)]
  q=subprocess.run(command,capture_output=True,env=env,timeout=120)
  (R/(label+'.stdout.txt')).write_bytes(q.stdout);(R/(label+'.stderr.txt')).write_bytes(q.stderr)
  if q.returncode or q.stderr:raise ValueError((label,q.returncode,q.stderr.decode()[:1000]))
  results.append({'name':label,'result':json.loads(q.stdout.splitlines()[-1])})
runtime='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet';dll=P/'bin/Release/net6.0/QuiescentCheckpoints.dll'
for arg in ['--self-test','--key-self-test','--checkpoint-self-test']:
 q=subprocess.run([runtime,str(dll),arg],capture_output=True,env=env,timeout=60)
 if q.returncode or q.stderr:raise ValueError((arg,q.returncode))
 results.append({'name':arg,'result':json.loads(q.stdout.splitlines()[-1])})
w=types.ModuleType('w');w.__file__=str(P/'run-once.py');exec(compile(Path(w.__file__).read_bytes(),w.__file__,'exec'),w.__dict__)
raw=w.manifest_bytes(w.build_manifest()[0])
if raw!=(P/'deployment-manifest.json').read_bytes():raise ValueError('manifest drift')
frozen()
result={'schema':'er-independent-validation-v1','sourceInventorySha256':expected_inventory,'frozenFilesVerifiedBeforeAndAfter':n,'manifestSha256':sha(raw),'manifestRegeneratedByteExactly':True,'results':results,'targetOperations':0,'rootOperations':0,'networkOperations':0}
(R/'independent-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
