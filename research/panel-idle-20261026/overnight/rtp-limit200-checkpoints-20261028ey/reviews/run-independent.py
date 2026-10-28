"""Independent read-only frozen source/payload verification and host fake tests."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
H=Path(__file__).resolve().parent;D=H.parent;B=D.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
need=lambda ok,msg:None if ok else(_ for _ in()).throw(ValueError(msg))
need(sha((D/'source-inventory.json').read_bytes())=='98855348468cc404e97bfb953dc3a47a8dfb13f5550dbda6beb0831437ce0189','frozen EY inventory')
inv=json.loads((D/'source-inventory.json').read_text());need(len(inv['files'])==50,'50 frozen files')
for row in inv['files']:
 raw=(D/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'frozen file '+row['path'])
for n in ('NativeBinding.cs','OnsetKey.cs'):
 need((D/n).read_bytes()==(B/'rtp-quiescent-checkpoints-20261028er'/n).read_bytes(),'unchanged '+n)
need(sha((D/'deployment-manifest.json').read_bytes())=='d5147751a8ec387cf6d85b06eb197c0f08075a1cb2e2157b7fef152fcd6a878b','manifest')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',DOTNET_CLI_HOME=str(H/'private/cli'),TMPDIR=str(H/'private/tmp'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_NOLOGO='1')
runtime=B.parent.parent/'live-cast/sdk/runtime/dotnet'
# ROOT/live-cast, not an externally retrieved runtime.
need(runtime.is_file(),'retained runtime')
runs=[]
for arg in ('--self-test','--key-self-test','--checkpoint-self-test'):
 p=subprocess.run([str(runtime),str(D/'bin/Release/net6.0/Limit200Checkpoints.dll'),arg],cwd=D,env=env,capture_output=True,timeout=30)
 (H/(arg[2:]+'.stdout')).write_bytes(p.stdout);(H/(arg[2:]+'.stderr')).write_bytes(p.stderr);need(p.returncode==0,'native host fake '+arg)
 runs.append({'suite':arg,'returnCode':0,'result':json.loads(p.stdout)})
for opt in(False,True):
 for n in ('verify_source.py','test-parse-result.py','test-quiescent.py','test-timing.py','test-readiness.py','test-runner.py','test-limit200.py'):
  p=subprocess.run([sys.executable,'-B']+(['-O']if opt else[])+[str(D/n)],cwd=D,env=env,capture_output=True,timeout=60)
  label=n+('-optimized'if opt else'-normal');(H/(label+'.stdout')).write_bytes(p.stdout);(H/(label+'.stderr')).write_bytes(p.stderr);need(p.returncode==0,label+' failed; inspect private review logs')
  lines=[line for line in p.stdout.decode().splitlines()if line.strip().startswith('{')]
  result=json.loads(lines[-1])if lines else{}
  runs.append({'suite':n,'optimized':opt,'returnCode':0,'result':result})
for row in inv['files']:
 raw=(D/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'posttest unchanged '+row['path'])
r={'schema':'ey-independent-host-review-v1','accepted':True,'frozenFilesVerified':50,'manifestSha256':sha((D/'deployment-manifest.json').read_bytes()),'runs':runs,'targetOperations':0,'rootCalls':0,'networkOperations':0,'frozenInputsUnchanged':True}
(H/'independent-validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'accepted':True,'frozenFiles':50,'hostSuites':len(runs),'targetOperations':0}))
