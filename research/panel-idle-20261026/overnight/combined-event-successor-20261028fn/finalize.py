#!/usr/bin/env python3
"""Author-only derived metadata generation; no transport import or operation."""
from pathlib import Path
import difflib,hashlib,json,re,types
P=Path(__file__).resolve().parent;B=P.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
inputs=['rtp-quiescent-checkpoints-20261028er/'+n for n in ['Program.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','run-once.py','prepare-readiness.py','deployment-manifest.json']]+['reader-wake-checkpoints-20261028fc/'+n for n in ['run-once.py','wake-check.py','test-runner.py','deployment-manifest.json']]+['fault-event-logging-options-20261028et/'+n for n in ['README.md','audit.py','source-audit.json','input-pins.json']]
inputs+=['selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin','wake-qualified-onset-trial-20261028fe/capture-analysis/decoded.json']+[str(p.relative_to(B))for p in sorted((B/'wake-qualified-onset-trial-20261028fe/capture-01').glob('retained-*-*-cycle*-??-?.bin'))if p.name.startswith(('retained-00-trigger_baseline-cycle001','retained-02-post_fault-cycle046'))and p.name.endswith(('-R.bin','-M.bin','-C.bin'))]
inputs += ['combined-event-checkpoints-20261028fg/'+n for n in ['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','CombinedEventCheckpoints.csproj','NuGet.Config','parse-result.py','run-once.py','prepare-readiness.py','wake-check.py','source-inventory.json','deployment-manifest.json','test-key-exposure.py','HostTests.cs','test-host.py']]
inputs += ['logger-context-transient-20261028fl/'+n for n in ['README.md','audit.py','input-pins.json','source-audit.json','source-audit.optimized.json','validation.json','source-inventory.json']]
inputs += ['combined-event-trial-20261028fh/capture-01/native.receipt.json']
write(P/'input-pins.json',{'schema':'fn-input-pins-v1','files':[{'path':n,'bytes':len((B/n).read_bytes()),'sha256':sha((B/n).read_bytes())}for n in inputs]})
write(P/'budget.json',{'schema':'fn-budget-v1','wholeNativeCooperativeUs':40000000,'bulkTimeoutUs':2000000,'pairBudgetUs':4000000,'cleanupPairs':6,'cleanupMarginUs':2000000,'cleanupReserveUs':26000000,'keyJoinReserveUs':7000000,'optionalPairAdmissionRemainingUs':37000000,'armAdmissionRemainingUs':38000000,'controlPairsMax':12,'observationDurationUs':2000000,'periodUs':25000,'rowsMax':56,'rowBytes':58,'rootSeconds':45,'hostSeconds':75,'commandCap':8192,'rootResponseCap':65536,'structuredReceiptCap':24576,'stdoutCap':16384,'stderrCap':2048,'ringSidecarBytes':15372,'ringSidecarCount':2,'targetOperationsPerformed':0})
files=['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','HostTests.cs','CombinedEventSuccessor.csproj','NuGet.Config','native-tests.json','fixture.json']+['bin/Release/net6.0/CombinedEventSuccessor'+s for s in ['.dll','.deps.json','.runtimeconfig.json']]
write(P/'host-build-checkpoint.json',{'schema':'fn-host-checkpoint-v1','targetOperations':0,'nativeQualification':json.loads((P/'native-tests.json').read_bytes()),'files':{n:{'bytes':len((P/n).read_bytes()),'sha256':sha((P/n).read_bytes())}for n in files}})
p=P/'run-once.py';s=p.read_text();s=re.sub("PARSER_SHA = '[0-9a-f]{64}'","PARSER_SHA = '"+sha((P/'parse-result.py').read_bytes())+"'",s);s=re.sub("CHECKPOINT_SHA = '[0-9a-f]{64}'","CHECKPOINT_SHA = '"+sha((P/'host-build-checkpoint.json').read_bytes())+"'",s);p.write_text(s)
m=types.ModuleType('fn_wrapper');m.__file__=str(p);exec(compile(s,str(p),'exec'),m.__dict__);manifest,_=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
production=['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','CombinedEventCheckpoints.csproj','NuGet.Config','parse-result.py','run-once.py','prepare-readiness.py','wake-check.py']
diff=[]
for name in production:
 target=name.replace('CombinedEventCheckpoints','CombinedEventSuccessor')
 diff.extend(difflib.unified_diff((B/'combined-event-checkpoints-20261028fg'/name).read_text().splitlines(True),(P/target).read_text().splitlines(True),fromfile='FG/'+name,tofile='FN/'+target))
(P/'production-diff.patch').write_text(''.join(diff))
families=['source-checks','context-qualification','scan-qualification','host-validation','key-exposure-tests']
if all((P/(name+'.'+mode+'.json')).exists()for name in families for mode in ['normal','optimized']):
 pairs={}
 for name in families:
  normal=(P/(name+'.normal.json')).read_bytes();optimized=(P/(name+'.optimized.json')).read_bytes()
  if normal!=optimized:raise ValueError('normal/optimized mismatch '+name)
  pairs[name]={'normalSha256':sha(normal),'optimizedSha256':sha(optimized),'identical':True,'result':json.loads(normal)}
 native=json.loads((P/'native-tests.json').read_bytes())
 if native['targetOperations']!=0 or native['maxReceiptBytes']>=24576:raise ValueError('native qualification bounds')
 write(P/'qualification.json',{'schema':'fn-host-qualification-v1','targetOperations':0,'targetDeploymentPerformed':False,'native':native,'normalOptimized':pairs,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'limitsUnchanged':True,'genericSemanticErrorCleanupUnchanged':True})
files=sorted([p for p in P.iterdir()if p.is_file()and p.name!='source-inventory.json']+[P/n for n in files if n.startswith('bin/')])
write(P/'source-inventory.json',{'schema':'fn-source-inventory-v1','targetOperations':0,'files':[{'path':str(p.relative_to(P)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in files]})
