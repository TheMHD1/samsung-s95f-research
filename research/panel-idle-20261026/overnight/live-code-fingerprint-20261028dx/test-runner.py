#!/usr/bin/env python3
"""Host-only DX mocks/parser mutations; never imports root transport."""
from pathlib import Path
import base64,copy,json,subprocess,sys,tempfile,types,uuid,os,stat,resource
P=Path(__file__).resolve().parent
r=types.ModuleType('dx');r.__file__=str(P/'run-once.py');exec(compile(Path(r.__file__).read_bytes(),r.__file__,'exec'),r.__dict__)
p=r.load_pinned(P/'parse-result.py',r.PARSER_SHA,'dx_parser');checks=0;commands=[]
def check(x,s):
 global checks
 if not x:raise ValueError(s)
 checks+=1
def reject(f):
 try:f()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'refusal');return
 raise ValueError('unexpected acceptance')
def decision():
 return {'schema':'dx-code-fingerprint-readiness-decision-v1','accepted':True,'identity':{'boot':r.BOOT,'sysfsRealpath':'/sys/devices/platform/usb/usb7/7-1','sysfsStat':'42:1234','busnum':'7','devnum':'57','deviceNode':'/dev/bus/usb/007/057','nodeStat':'bd:338:12345','descriptorsSha256':r.sha(bytes.fromhex(r.DESCRIPTORS)),'configuration':'1','authorized':'1','runtimeStatus':'active','interfaceNumber':'02','alternate':'0','interfaceClass':'ff','interfaceSubClass':'00','interfaceProtocol':'00'},'interfaceUnbound':True,'noHolders':True,'closedWorldVendorOutLineage':{'accepted':True,'statement':'SYNTHETIC HOST TEST ONLY: not evidence of any real USB instance or queue readiness.','evidenceSha256':'a'*64},'evidence':[{'path':'/host/fake-only','sha256':'b'*64}],'endpointQueueProof':False}
def envelope(receipt,code=0,stdout=b'[GC_INF{not semantic receipt}\nO] arbitrary diagnostics',stderr=b''):
 vals=(receipt,stdout,stderr);s='DXMETA_BEGIN\n'+r.BOOT+'\n1.0 2.0\n'+str(code)+'\n'
 for b in vals:s+=str(len(b))+'\n'+r.sha(b)+'\n'
 s+='DXMETA_END\n'
 for name,b in zip(('RECEIPT','STDOUT','STDERR'),vals):s+=name+'_B64_BEGIN\n'+base64.b64encode(b).decode()+'\n'+name+'_B64_END\n'
 return s+'DXRUN_COMPLETE\n'
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
   return envelope(b'{"selfTestsPassed":724,"targetOperations":0}\n')
  if ' --execute --device ' in command:
   self.invocations+=1;check(' --execute --device 57 > ' in command,'fixed device invocation')
   if self.kind=='timeout':raise OSError('ambiguous invoke; no retry')
   if self.kind=='partial':return 'IMMEDIATE_READY\nDXMETA_BEGIN\n'
   raw=(P/'fixture.json').read_bytes()
   if self.kind=='malformed':raw=b'{"schema":'
   if self.kind=='mismatch':
    row=json.loads(raw);w=row['windows'][0];b=bytearray(base64.b64decode(w['base64']));b[0]^=1;w['base64']=base64.b64encode(b).decode();w['sha256']=r.sha(b);raw=json.dumps(row).encode()
   if self.kind=='wrong-device':n=json.loads(raw);n['device']=58;raw=json.dumps(n).encode()
   return 'IMMEDIATE_READY\n'+envelope(raw,1 if self.kind=='bad-exit' else 0,stderr=b'x' if self.kind=='stderr' else b'')
  if command.endswith('echo STAGE_ABSENT\n'):
   self.cleanups+=1
   if self.kind=='cleanup':raise OSError('cleanup ambiguity')
   return 'STAGE_ABSENT\n'
  raise ValueError('unclassified fake command')
raw=(P/'fixture.json').read_bytes();n,files,interpret=p.parse_native(raw.decode());check(len(files)==4 and interpret['transportAccepted'] and interpret['sampledCodeMatch'] and interpret['sampledBytes']==64,'four exact matches accepted');check(not any(interpret[k]for k in ['atomicSnapshot','wholeRunningImageAttested','activeInstructionFetchProven','executableWriteQualified','physicalPictureObserved']),'narrow identity claims')
for field in p.FIELDS:
 x=copy.deepcopy(n);x.pop(field);reject(lambda:p.parse_native(json.dumps(x)))
for field in ['opened','claimed','released','closed','accepted','sampledCodeMatch']:
 x=copy.deepcopy(n);x[field]=False;reject(lambda:p.parse_native(json.dumps(x)))
for field in ['atomicSnapshot','physicalPictureObserved','wholeRunningImageAttested','executableWriteQualified']:
 x=copy.deepcopy(n);x[field]=True;reject(lambda:p.parse_native(json.dumps(x)))
for field in ['headersSent','bulkTransfers','writes','uiOperations','device']:
 x=copy.deepcopy(n);x[field]=True;reject(lambda:p.parse_native(json.dumps(x)))
for i in range(8):
 for key,value in [('count',-1),('beforeUs',-1),('after','Unknown'),('direction','BAD'),('errno',5),('expected',True)]:
  x=copy.deepcopy(n);x['steps'][i][key]=value;reject(lambda:p.parse_native(json.dumps(x)))
for i in range(4):
 for key,value in [('sha256','0'*64),('address',0x60000000),('bytes',15),('name','arbitrary')]:
  x=copy.deepcopy(n);x['windows'][i][key]=value;reject(lambda:p.parse_native(json.dumps(x)))
 for at in range(16):
  x=copy.deepcopy(n);w=x['windows'][i];b=bytearray(base64.b64decode(w['base64']));b[at]^=1;w['base64']=base64.b64encode(b).decode();w['sha256']=r.sha(b);reject(lambda:p.parse_native(json.dumps(x)))
 x=copy.deepcopy(n);x['windows'][i]['base64']+='=';reject(lambda:p.parse_native(json.dumps(x)))
reject(lambda:p.parse_native(raw.decode()+raw.decode()));reject(lambda:p.parse_native('[GC_INFO] x\n'+raw.decode()));reject(lambda:p.parse_native(raw.decode().replace('"schema":','"schema":"dup","schema":',1)))
for i in range(3):
 for field,value in [('stage','wrong'),('ownClaim',None),('localFdMatches',None)]:
  x=copy.deepcopy(n);x['bindingChecks'][i][field]=value;reject(lambda:p.parse_native(json.dumps(x)))
 for node in ['link','follow','canonical']:
  for field in ['return','errno','mask','mode','inode','devMajor','devMinor']:
   x=copy.deepcopy(n);x['bindingChecks'][i][node][field]=True;reject(lambda:p.parse_native(json.dumps(x)))
for i in [1,2]:
 for field,value in [('return',7),('errno',13),('name','other'),('interface',1),('rawBase64','AAAA'),('sha256','0'*64)]:
  x=copy.deepcopy(n);x['bindingChecks'][i]['kernel'][field]=value;reject(lambda:p.parse_native(json.dumps(x)))
for field in ['inode','devMajor','devMinor']:
 x=copy.deepcopy(n);x['bindingChecks'][2]['follow'][field]+=1;reject(lambda:p.parse_native(json.dumps(x)))
x=copy.deepcopy(n);x['windows'].reverse();reject(lambda:p.parse_native(json.dumps(x)))
x=copy.deepcopy(n);x['windows'][1]=x['windows'][0];reject(lambda:p.parse_native(json.dumps(x)))
x=copy.deepcopy(n);x['steps'][-1]['afterUs']=40000001+x['steps'][0]['beforeUs'];reject(lambda:p.parse_native(json.dumps(x)))
manifest,payload=r.build_manifest();reviewed=r.manifest_bytes(manifest);check(reviewed==r.manifest_bytes(r.build_manifest()[0]),'manifest deterministic')
with tempfile.TemporaryDirectory(prefix='dm-host-only-') as tmp:
 base=Path(tmp);ready=decision();b=json.dumps(ready).encode();rp=base/'ready.json';rp.write_bytes(b);check(r.load_readiness(rp,r.sha(b))[0]==ready,'readiness accepted')
 for k in ('accepted','interfaceUnbound','noHolders'):
  bad=copy.deepcopy(ready);bad[k]=False;br=json.dumps(bad).encode();rp.write_bytes(br);reject(lambda:r.load_readiness(rp,r.sha(br)))
 f=FakeRoot();res=r.execute(base/'success',ready,b,reviewed,payload,f,p);check(res['accepted'] and res['sampledCodeMatch'] and not res['wholeRunningImageAttested'] and not res['executableWriteQualified'] and f.invocations==f.cleanups==1 and res['headersSent']==4 and res['bulkTransfers']==8 and len(res['rawFiles'])==4,'one pass cleanup')
 for kind in ('PRE_READY','BEFORE_INVOKE_READY','POST_READY','selftest','timeout','partial','malformed','mismatch','wrong-device','bad-exit','stderr','cleanup'):
  f=FakeRoot(kind);out=base/kind;reject(lambda:r.execute(out,ready,b,reviewed,payload,f,p));check(f.invocations<=1,'no retry');check(f.cleanups==(1 if kind=='cleanup' else 0),'failure cleanup policy')
  if kind in ('partial','malformed','mismatch','wrong-device','bad-exit','stderr'):check((out/'native-envelope.txt').exists(),'save envelope before parse')
 for ftext in [envelope(b'{}')+'x',envelope(b'x'*24577),envelope(b'{}',stdout=b'x'*16385),envelope(b'{}',stderr=b'x'*2049)]:reject(lambda:r.receipt_envelope(ftext))
body=r.metadata_body(decision()['identity'],'PRE_READY');check(body.count('bx_fd_snapshot=$(LC_ALL=C stat ')==1,'batched census');check('test "$#" -le 32768' in body,'FD census bound')
check(json.loads(subprocess.run([sys.executable,'-B',str(P/'run-once.py')],check=True,capture_output=True).stdout)['targetOperations']==0,'default dry')
dll=P/'bin/Release/net6.0/CodeFingerprint.dll';runtime='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet'
q=subprocess.run([runtime,str(dll),'--execute','--device','57'],capture_output=True);check(q.returncode==64 and b'REFUSED_ARM32_ABI' in q.stdout and not q.stderr,'x64 refuses before device/native calls')
for args in [['--execute','--address','0x46002020'],['--execute-set'],['--execute','--device','057'],['--execute','--device','0'],['--execute','--device','128']]:
 q=subprocess.run([runtime,str(dll),*args],capture_output=True);check(q.returncode==64 and not q.stderr,'invalid native CLI cannot select memory/actions')
# Host receipt creation exercises the actual exclusive file mechanism, never RealOps.
stage=Path('/tmp/researcher-dx-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
try:
 out=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/CodeFingerprint.dll'),'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);file=stage/'selftest.receipt.json';check(out.returncode==0 and not out.stderr and json.loads(file.read_bytes())=={'selfTestsPassed':724,'targetOperations':0},'actual host receipt fake selftest');check(stat.S_IMODE(file.stat().st_mode)==0o600,'actual0600');before=file.read_bytes();again=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/CodeFingerprint.dll'),'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);check(again.returncode!=0 and file.read_bytes()==before,'exclusive no overwrite')
 file.unlink()
 with tempfile.TemporaryDirectory(prefix='dx-sentinel-') as other:
  sentinel=Path(other)/'sentinel';sentinel.write_bytes(b'unchanged');file.symlink_to(sentinel);q=subprocess.run([runtime,str(dll),'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);check(q.returncode!=0 and sentinel.read_bytes()==b'unchanged'and file.is_symlink(),'receipt symlink refused');file.unlink()
 stage.chmod(0o755);q=subprocess.run([runtime,str(dll),'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);check(q.returncode!=0 and not file.exists(),'receipt directory mode refused');stage.chmod(0o700)
finally:
 for file in stage.iterdir():file.unlink()
 stage.rmdir()
print(json.dumps({'checksPassed':checks,'targetOperations':0,'commandsSyntaxChecked':len(commands),'maximumCommandBytes':max(len(s.encode())for s in commands)}))
