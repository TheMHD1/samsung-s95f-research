#!/usr/bin/env python3
"""FP independent host-only review runner; all test scratch redirected to reviews."""
import ast,base64,copy,hashlib,json,pathlib,subprocess,sys,types
sys.dont_write_bytecode=True
D=pathlib.Path(__file__).resolve().parent;P=D.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def load(path):
 m=types.ModuleType('review_'+path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
r=load(P/'run-once.py');parser=load(r.FK/'parse-receipt.py')
refs=json.loads((P/'source-inventory.json').read_bytes())['files']
for row in refs:
 b=(P/row['path']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'FP frozen file '+row['path'])
manifest,payload=r.build_manifest();need(r.manifest_bytes(manifest)==(P/'deployment-manifest.json').read_bytes(),'exact regenerated manifest')
need(sum(map(len,payload.values()))==33431 and set(payload)==set(r.NAMES),'three immutable FK payloads')
# Exact author suite, with only its scratch-directory expression redirected.
raw=(P/'test-host.py').read_text();old="P/'host-environment/tmp'";need(raw.count(old)==2,'two scratch references only');code=raw.replace(old,"P/'reviews/private'")
module=types.ModuleType('independent_author_tests');module.__file__=str(P/'test-host.py');exec(compile(code,module.__file__,'exec'),module.__dict__)
fixture=json.loads((r.FK/'fixture.json').read_bytes());refusals=0
def reject(fn,label):
 global refusals
 try:fn()
 except (ValueError,KeyError,TypeError,UnicodeError):refusals+=1;return
 raise ValueError('unexpected accepted '+label)
for k in ['copyCompletionAttested','completeLogProven','loadedModuleBytesAttested','externalRtpProducerProven','timeoutOrRollbackGuaranteed']:
 v=copy.deepcopy(fixture);v[k]=True;reject(lambda v=v:parser.parse((json.dumps(v)+'\n').encode()),k)
for k,v in [('readResult',4097),('requestedCount',1),('allocatedBytes',4095),('readCallsMaximum',2),('retries',1),('writesToDriver',1),('path','/sys/kernel/debug/tcon/other'),('accepted',False),('closeResult',-1)]:
 n=copy.deepcopy(fixture);n[k]=v;reject(lambda n=n:parser.parse((json.dumps(n)+'\n').encode()),k)
for field in ['FP_RUN_BEGIN','RECEIPT_B64_BEGIN','FP_RUN_COMPLETE']:
 reject(lambda field=field:r.parse_envelope(module.envelope().replace(field,field+'X')),field)
for cap,idx in [(r.RECEIPT_CAP,0),(r.STDOUT_CAP,1),(r.STDERR_CAP,2)]:
 vals=[b'{}',b'',b''];vals[idx]=b'x'*(cap+1);reject(lambda vals=vals:r.parse_envelope(module.envelope(*vals)),'cap'+str(idx))
run=r.run_command(payload);need(subprocess.run(['sh','-n'],input=run.encode(),capture_output=True).returncode==0,'exact native command sh-n')
need(sum(line.startswith('/usr/bin/dotnet ')for line in run.splitlines())==1 and run.count(' --execute > ')==1,'one native invocation')
need(all(s not in run for s in ['cat '+r.TARGET,'base64 '+r.TARGET,'dd ','input_keyevent','ioctl','/dev/bus/usb','/dev/mem']),'no shell data read/other domains')
need(r.metadata_body()in run and run.index(r.metadata_body())<run.index(' --execute > '),'guard precedes read')
tree=ast.parse((P/'run-once.py').read_text());ex=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='execute');handler=next(x for x in ast.walk(ex)if isinstance(x,ast.ExceptHandler));need(not any(isinstance(x,ast.Call)and isinstance(x.func,ast.Name)and x.func.id=='call'for x in ast.walk(handler)),'exception path sends no followup root command')
summary=dict(schema='fp-independent-validation-v1',fpFilesVerified=len(refs),checks=checks,extraMalformedRefusals=refusals,authorChecks=module.checks,authorCases=len(module.kinds),mockRootCommands=len(module.commands),maxCommandBytes=max(len(x.encode())for x in module.commands),nativeCommandBytes=len(run.encode()),rootResponseBound=len(module.max_response),manifestSha256=sha((P/'deployment-manifest.json').read_bytes()),wrapperSha256=sha((P/'run-once.py').read_bytes()),fkDllSha256=sha(payload['TconLogSingleRead.dll']),targetReads=0,rootCalls=0,networkCalls=0,scratchOnly='reviews/private')
print(json.dumps(summary,sort_keys=True))
