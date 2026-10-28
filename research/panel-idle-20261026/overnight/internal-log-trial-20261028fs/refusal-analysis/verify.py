#!/usr/bin/env python3
"""FS preflight refusal reconciliation. Pure mock replay, no live adapter import."""
from pathlib import Path
import ast,base64,copy,hashlib,json,tempfile,types,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;F=D.parent;P=F/'log-read-01';B=F.parent;FP=B/'tcon-log-single-read-adapter-20261028fp';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def j(p):return json.loads(p.read_bytes())
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def classify(record,result,command):
 need(record['phase']==record['failurePhase']=='preflight'and result['failurePhase']=='preflight'and result['accepted']is False,'original rejected preflight')
 need(len(record['calls'])==1,'single root submission');c=record['calls'][0];need(c['command']==command and c['command_bytes']==len(command.encode())==1548,'exact original metadata command')
 need(c['host_timeout']is False and c['transport_exit']==1 and c['transport_stderr']=={'data':'','encoding':'base64'},'transport terminal refusal not timeout')
 raw=base64.b64decode(c['transport_stdout']['data'],validate=True);r=json.loads(raw);need(r['authenticated']is True and r['uid']==r['euid']==0 and len(r['commands'])==1,'authenticated root response')
 child=r['commands'][0];need(child==dict(command=command,exit_code=1,timed_out=False,stdout='',stderr=''),'exact remote refusal/empty outputs')
 need(record['nativeInvocations']==result['nativeInvocations']==0 and record['nativeInvocationStatus']==result['nativeInvocationStatus']=='not_started'and record['readMayHaveOccurred']is result['readMayHaveOccurred']is False,'no invocation/read submitted')
 need(result['cleanupRequired']is True and result['retries']==0,'original conservative cleanup flag/retry0')
 return raw
for ref in j(D/'input-pins.json')['files']:
 b=(B/ref['path']).read_bytes();need(len(b)==ref['bytes']and sha(b)==ref['sha256'],'frozen input '+ref['path'])
w=load(FP/'run-once.py');record=j(P/'record.json');result=j(P/'result.json');command=w.prefix()+w.metadata_body();raw=classify(record,result,command)
need(sha(command.encode())=='3961d5a5956359f6facdb8596a454a234e992541076d172944a9ef3951408869','fixed command hash')
need(not any(x in command for x in ['mkdir ','/usr/bin/dotnet',' --execute','cat '+w.TARGET,'base64 '+w.TARGET,'/dev/bus/usb','input_keyevent','ioctl ']),'no stage/native/contentread/USB/UI path')
manifest,payload=w.build_manifest();mb=w.manifest_bytes(manifest);need(mb==(P/'reviewed-manifest.json').read_bytes(),'actual reviewed manifest')
class Replay:
 at=0
 def root(self,cmd,rec,path):
  need(self.at==0 and cmd==command,'no second request');self.at+=1;rec['calls'].append(copy.deepcopy(record['calls'][0]));w.save(path,rec);raise ValueError('Root client failed')
replay=Replay();parser=load(w.FK/'parse-receipt.py');artifacts=0
with tempfile.TemporaryDirectory(dir=D/'private')as tmp:
 out=Path(tmp)/'attempt'
 try:w.execute(out,mb,payload,replay,parser)
 except ValueError as e:need(str(e)=='Root client failed','exact original refusal')
 else:raise ValueError('unexpected acceptance')
 for p in out.iterdir():need(p.read_bytes()==(P/p.name).read_bytes(),'byte-exact original artifact '+p.name);artifacts+=1
need(replay.at==1 and artifacts==3,'one exact command and3 exact artifacts')
mutations=0
for field,value in [('nativeInvocations',1),('nativeInvocationStatus','inflight_or_unknown'),('readMayHaveOccurred',True),('phase','native')]:
 v=copy.deepcopy(record);v[field]=value
 try:classify(v,result,command)
 except ValueError:mutations+=1
 else:raise ValueError('invalid classification '+field)
need(j(F/'preflight-refusal-reconciliation.json')['firstFailingGuardIdentified']is False,'parent retains unidentified guard')
g=F/'guard-metadata-01';dr=j(g/'record.json');need(len(dr['calls'])==1,'separate diagnostic1call');dc=dr['calls'][0];dt=ast.parse((F/'capture-guard-metadata.py').read_text());expected=next(ast.literal_eval(x.value)for x in dt.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='command'for t in x.targets));need(dc['command']==expected==(g/'prospective-command.txt').read_text(),'fixed separately planned metadata command')
dresp=json.loads(base64.b64decode(dc['transport_stdout']['data'],validate=True));need(dc['transport_exit']==0 and dc['host_timeout']is False and dresp['authenticated']is True and dresp['uid']==dresp['euid']==0,'diagnostic authenticated terminal');child=dresp['commands'][0];need(child['command']==expected and child['exit_code']==0 and not child['timed_out']and child['stderr']==''and child['stdout']==(g/'metadata.txt').read_text(),'exact metadata response binding');lines=child['stdout'].splitlines();need(len(lines)==13 and lines[0]=='FS_GUARD_METADATA_BEGIN'and lines[-1]=='FS_GUARD_METADATA_END','diagnostic framing');need(lines[1:6]==['0','0',w.BOOT,w.KERNEL,'debugfs /sys/kernel/debug debugfs'],'diagnostic identity');need(lines[7:11]==['0:100:755:0:directory','0:0:755:0:directory','0:0:644:0:regular empty file','0:0:644:226262:regular file']and lines[11].split()==[w.MODULE_SHA,w.MODULE],'diagnostic exact ownership/type/modulehash')
need(not any(x in expected for x in ['mkdir ','/usr/bin/dotnet',' --execute','cat '+w.TARGET,'base64 '+w.TARGET,'/dev/bus/usb','input_keyevent']),'metadata only no contentread')
summary=dict(schema='fs-independent-preflight-refusal-v1',originalAccepted=False,classification='EXACT_METADATA_COMMAND_REFUSED_BEFORE_STAGING_OR_NATIVE',rootSubmissions=1,transportExit=1,remoteExit=1,timedOut=False,stdoutBytes=0,stderrBytes=0,metadataCommandBytes=len(command.encode()),metadataCommandSha256=sha(command.encode()),rawTransportJsonSha256=sha(raw),nativeInvocations=0,debugfsContentReadsSubmitted=0,targetStageCreationRequests=0,usbOperations=0,uiOperations=0,automaticRetry=False,firstFailingGuardIdentified=False,separateDiagnosticMismatches=[dict(path='/sys/kernel/debug',field='gid',fpExpected=0,observed=100)],diagnosticMatchesRefusalCauseButHistoricalAtomicityUnproved=True,separateDiagnosticRootSubmissions=1,separateDiagnosticContentReads=0,stageExistenceObserved=False,cleanupRequiredOriginal=True,generatedArtifactsByteExact=artifacts,malformedRefusals=mutations,checksPassed=checks,targetCallsDuringAnalysis=0,networkCalls=0)
b=(json.dumps(summary,sort_keys=True,indent=2)+'\n').encode()
if '--write'in sys.argv:(D/'decoded.json').write_bytes(b)
else:need(b==(D/'decoded.json').read_bytes(),'exact derived output')
print(json.dumps(summary,sort_keys=True))
