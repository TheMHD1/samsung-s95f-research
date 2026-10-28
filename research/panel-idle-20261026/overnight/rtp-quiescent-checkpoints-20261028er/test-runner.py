#!/usr/bin/env python3
"""Host-only DP mocks/parser mutations; never imports root transport."""
from pathlib import Path
import base64,copy,json,subprocess,sys,tempfile,types,uuid,os,stat,resource
P=Path(__file__).resolve().parent
r=types.ModuleType('dm');r.__file__=str(P/'run-once.py');exec(compile(Path(r.__file__).read_bytes(),r.__file__,'exec'),r.__dict__)
p=r.load_pinned(P/'parse-result.py',r.PARSER_SHA,'dp_parser');checks=0;commands=[]
def check(x,s):
 global checks
 if not x:raise ValueError(s)
 checks+=1
def reject(f):
 try:f()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'refusal');return
 raise ValueError('unexpected acceptance')
def decision():
 return {'schema':'er-quiescent-checkpoint-readiness-decision-v1','accepted':True,'identity':{'boot':r.BOOT,'sysfsRealpath':'/sys/devices/platform/usb/usb7/7-1','sysfsStat':'42:1234','busnum':'7','devnum':'45','deviceNode':'/dev/bus/usb/007/045','nodeStat':'bd:32c:12345','descriptorsSha256':r.sha(bytes.fromhex(r.DESCRIPTORS)),'configuration':'1','authorized':'1','runtimeStatus':'active','interfaceNumber':'02','alternate':'0','interfaceClass':'ff','interfaceSubClass':'00','interfaceProtocol':'00'},'interfaceUnbound':True,'noHolders':True,'closedWorldVendorOutLineage':{'accepted':True,'statement':'SYNTHETIC HOST TEST ONLY: not evidence of any real USB instance or queue readiness.','evidenceSha256':'a'*64},'evidence':[{'path':'/host/fake-only','sha256':'b'*64}],'endpointQueueProof':False}
def envelope(receipt,code=0,stdout=b'[GC_INF{not semantic receipt}\nO] arbitrary diagnostics',stderr=b''):
 vals=(receipt,stdout,stderr);s='DPMETA_BEGIN\n'+r.BOOT+'\n1.0 2.0\n'+str(code)+'\n'
 for b in vals:s+=str(len(b))+'\n'+r.sha(b)+'\n'
 s+='DPMETA_END\n'
 for name,b in zip(('RECEIPT','STDOUT','STDERR'),vals):s+=name+'_B64_BEGIN\n'+base64.b64encode(b).decode()+'\n'+name+'_B64_END\n'
 return s+'DPRUN_COMPLETE\n'
class FakeRoot:
 def __init__(self,kind='success'):self.kind=kind;self.invocations=0;self.cleanups=0
 def root(self,command,record,path):
  commands.append(command);check(len(command.encode())<=8192,'root command bound');check(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'shell syntax');check(not any(x in command for x in ['input_keyevent','vconftool','killall','MODE2','--execute-set','--execute-restore']),'no UI/write/recovery');r.save(path,record)
  for name in ['PRE_READY','BEFORE_INVOKE_READY','POST_READY']:
   if command.endswith('echo '+name+'\n'):
    if self.kind==name:raise ValueError('identity/census refusal')
    return 'FDCENSUS expected=120 missing=1 holders=0 errors=0\n'+name+'\n'
  for marker in ['PRIVATE_STAGE_CREATED','STAGED_CHUNK','STAGED_FILE','FINAL_INTEGRITY_OK']:
   if command.endswith('echo '+marker+'\n'):return marker+'\n'
  if ' --receipt-self-test > ' in command:
   if self.kind=='selftest':return envelope(b'{"selfTestsPassed":false,"targetOperations":0}\n')
   return envelope(b'{"selfTestsPassed":93,"keyTestsPassed":22,"checkpointTestsPassed":79,"targetOperations":0}\n')
  if ' --execute --device ' in command:
   self.invocations+=1;check(' --execute --device 45 > ' in command,'fixed device invocation')
   if self.kind=='timeout':raise OSError('ambiguous invoke; no retry')
   if self.kind=='partial':return 'IMMEDIATE_READY\nDPMETA_BEGIN\n'
   raw=(P/'fixture.json').read_bytes()
   if self.kind in ('quiescent','quiescent-fault'):raw=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/QuiescentCheckpoints.dll'),'--checkpoint-fixture-'+self.kind],capture_output=True,check=True).stdout
   if self.kind=='malformed':raw=b'{"schema":'
   if self.kind=='wrong-device':n=json.loads(raw);n['device']=58;raw=json.dumps(n).encode()
   return 'IMMEDIATE_READY\n'+envelope(raw,1 if self.kind=='bad-exit' else 0,stderr=b'x' if self.kind=='stderr' else b'')
  if command.endswith('echo STAGE_ABSENT\n'):
   self.cleanups+=1
   if self.kind=='cleanup':raise OSError('cleanup ambiguity')
   return 'STAGE_ABSENT\n'
  raise ValueError('unclassified fake command')
raw=(P/'fixture.json').read_bytes();native,caps,files,gc,interpret=p.parse_native(raw.decode());check(interpret['trialQualified'] and interpret['scoreCheckpoints']['count']==2 and len(files)==32,'qualified actual managed fake fixture')
manifest,payload=r.build_manifest();check(manifest['nativeDurationUs']==2000000 and manifest['nativeMaxCycles']==56 and manifest['checkpointRecordBytes']==58 and manifest['nominalPeriodUs']==25000 and manifest['rootTimeoutSeconds']==45 and manifest['hostTimeoutSeconds']==75 and manifest['structuredReceiptCap']==24576,'fixed EM budgets and unchanged receipt/deadline caps');reviewed=r.manifest_bytes(manifest);check(reviewed==r.manifest_bytes(r.build_manifest()[0]),'manifest deterministic')
with tempfile.TemporaryDirectory(prefix='em-host-only-') as tmp:
 base=Path(tmp);ready=decision();b=json.dumps(ready).encode();rp=base/'ready.json';rp.write_bytes(b);check(r.load_readiness(rp,r.sha(b))[0]==ready,'readiness accepted')
 for k in ('accepted','interfaceUnbound','noHolders'):
  bad=copy.deepcopy(ready);bad[k]=False;br=json.dumps(bad).encode();rp.write_bytes(br);reject(lambda:r.load_readiness(rp,r.sha(br)))
 f=FakeRoot();res=r.execute(base/'success',ready,b,reviewed,payload,f,p);check(res['accepted'] and f.invocations==f.cleanups==1 and res['headersSent']==23 and len(res['rawFiles'])==32 and res['scoreCheckpointCount']==2,'one pass cleanup')
 for kind,quiet,outcome in [('quiescent',55,'QuiescentObserved'),('quiescent-fault',54,'Faulted')]:
  f=FakeRoot(kind);res=r.execute(base/kind,ready,b,reviewed,payload,f,p);check(res['accepted'] and res['trialQualified'] and res['quiescentCyclesCompleted']==quiet and res['rtObservationOutcome']==outcome and f.invocations==f.cleanups==1,'truthful Quiescent wrapper result/one-shotcleanup')
 for kind in ('PRE_READY','BEFORE_INVOKE_READY','POST_READY','selftest','timeout','partial','malformed','wrong-device','bad-exit','stderr','cleanup'):
  f=FakeRoot(kind);out=base/kind;reject(lambda:r.execute(out,ready,b,reviewed,payload,f,p));check(f.invocations<=1,'no retry');check(f.cleanups==(1 if kind=='cleanup' else 0),'failure cleanup policy')
  if kind in ('partial','malformed','wrong-device','bad-exit','stderr'):check((out/'native-envelope.txt').exists(),'save envelope before parse')
 for ftext in [envelope(b'{}')+'x',envelope(b'x'*24577),envelope(b'{}',stdout=b'x'*16385),envelope(b'{}',stderr=b'x'*2049)]:reject(lambda:r.receipt_envelope(ftext))
body=r.metadata_body(decision()['identity'],'PRE_READY');check(body.count('bx_fd_snapshot=$(LC_ALL=C stat ')==1,'batched census');check('test "$#" -le 32768' in body,'FD census bound')
check(json.loads(subprocess.run([sys.executable,'-B',str(P/'run-once.py')],check=True,capture_output=True).stdout)['targetOperations']==0,'default dry')
# Host receipt creation exercises the actual exclusive file mechanism, never RealOps.
stage=Path('/tmp/researcher-er-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
try:
 out=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/QuiescentCheckpoints.dll'),'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);file=stage/'selftest.receipt.json';check(out.returncode==0 and not out.stderr and json.loads(file.read_bytes())=={'selfTestsPassed':93,'keyTestsPassed':22,'checkpointTestsPassed':79,'targetOperations':0},'actual host receipt fake selftest');check(stat.S_IMODE(file.stat().st_mode)==0o600,'actual0600');before=file.read_bytes();again=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/QuiescentCheckpoints.dll'),'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);check(again.returncode!=0 and file.read_bytes()==before,'exclusive no overwrite')
finally:
 for file in stage.iterdir():file.unlink()
 stage.rmdir()
print(json.dumps({'checksPassed':checks,'targetOperations':0,'commandsSyntaxChecked':len(commands),'maximumCommandBytes':max(len(s.encode())for s in commands)}))
