#!/usr/bin/env python3
import os,sys,subprocess,json,hashlib,types
from pathlib import Path
P=Path(__file__).resolve().parent.parent
R=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def check_inventory():
 raw=(P/'source-inventory.json').read_bytes()
 if sha(raw)!='b62b8e97a498b2500d4afc1ad897dce33dfcc8ff68d640a903340c78e54f331c':raise ValueError('inventory pin')
 rows=json.loads(raw)['files']
 for row in rows:
  data=(P/row['path']).read_bytes()
  if len(data)!=row['bytes']or sha(data)!=row['sha256']:raise ValueError(row['path'])
 return len(rows)
n=check_inventory()
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(R/'tmp'))
results=[]
for opt in [[],['-O']]:
 for name in ['verify_source.py','test-runner.py','test-readiness.py']:
  q=subprocess.run([sys.executable,*opt,'-B',str(P/name)],capture_output=True,env=env,timeout=120)
  label=name.replace('.py','')+('-optimized'if opt else '-normal')
  (R/(label+'.stdout.txt')).write_bytes(q.stdout)
  (R/(label+'.stderr.txt')).write_bytes(q.stderr)
  if q.returncode or q.stderr:raise ValueError((label,q.returncode,q.stderr.decode()[:1000]))
  results.append({'name':label,'result':json.loads(q.stdout)})
runtime='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet'
for arg in ['--self-test','--receipt-bound-self-test']:
 q=subprocess.run([runtime,str(P/'bin/Release/net6.0/LaneCodeFingerprint.dll'),arg],capture_output=True,env=env,timeout=60)
 if q.returncode or q.stderr:raise ValueError((arg,q.returncode))
 results.append({'name':arg,'result':json.loads(q.stdout)})
w=types.ModuleType('w');w.__file__=str(P/'run-once.py');exec(compile(Path(w.__file__).read_bytes(),w.__file__,'exec'),w.__dict__)
raw=w.manifest_bytes(w.build_manifest()[0])
if raw!=(P/'deployment-manifest.json').read_bytes():raise ValueError('manifest regeneration')
check_inventory()
out={'schema':'ep-independent-validation-v1','sourceInventorySha256':sha((P/'source-inventory.json').read_bytes()),'manifestSha256':sha(raw),'frozenFilesVerifiedBeforeAndAfter':n,'manifestRegeneratedByteExactly':True,'results':results,'targetOperations':0,'rootOperations':0,'networkOperations':0}
(R/'independent-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
