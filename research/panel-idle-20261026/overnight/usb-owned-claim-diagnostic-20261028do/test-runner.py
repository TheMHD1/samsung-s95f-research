#!/usr/bin/env python3
"""Host-only zero-vendor wrapper/parser tests; never import root transport."""
from pathlib import Path
import base64,copy,hashlib,json,subprocess,sys,tempfile,types,uuid,stat,resource
P=Path(__file__).resolve().parent;r=types.ModuleType('do_wrapper');r.__file__=str(P/'run-once.py');exec(compile(Path(r.__file__).read_bytes(),r.__file__,'exec'),r.__dict__);p=r.load_pinned(P/'parse-result.py',r.PARSER_SHA,'do_parser');checks=0;commands=[]
def check(b,s):
 global checks
 if not b:raise ValueError(s)
 checks+=1
def reject(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'reject');return
 raise ValueError('unexpected acceptance')
def decision():
 return {'schema':'do-usb-owned-claim-diagnostic-readiness-decision-v1','accepted':True,'identity':{'boot':r.BOOT,'sysfsRealpath':'/sys/devices/platform/usb/usb7/7-1','sysfsStat':'42:1234','busnum':'7','devnum':'58','deviceNode':'/dev/bus/usb/007/058','nodeStat':'bd:339:12345','descriptorsSha256':r.sha(bytes.fromhex(r.DESCRIPTORS)),'configuration':'1','authorized':'1','runtimeStatus':'active','interfaceNumber':'02','alternate':'0','interfaceClass':'ff','interfaceSubClass':'00','interfaceProtocol':'00'},'interfaceUnbound':True,'noHolders':True,'closedWorldVendorOutLineage':{'accepted':True,'statement':'SYNTHETIC HOST TEST ONLY: no assertion about any real device queue or lineage.','evidenceSha256':'a'*64},'evidence':[{'path':'/host/fake-only.json','sha256':'b'*64}],'endpointQueueProof':False}
def envelope(receipt,rc=0,stdout=b'[GC_INFO] telemetry\n',stderr=b''):
 h='DLMETA_BEGIN\n'+r.BOOT+'\n1.0 2.0\n'+str(rc)+'\n'
 for v in [receipt,stdout,stderr]:h+=str(len(v))+'\n'+r.sha(v)+'\n'
 h+='DLMETA_END\n'
 for v,k in zip([receipt,stdout,stderr],['RECEIPT','STDOUT','STDERR']):h+=k+'_B64_BEGIN\n'+base64.b64encode(v).decode()+'\n'+k+'_B64_END\n'
 return h+'DLRUN_COMPLETE\n'
class FakeRoot:
 def __init__(self,kind='success'):self.kind=kind;self.invocations=0;self.cleanups=0
 def root(self,cmd,record,path):
  commands.append(cmd);check(len(cmd.encode())<=8192,'command extent');q=subprocess.run(['sh','-n'],input=cmd.encode(),capture_output=True);check(q.returncode==0,'shell syntax');r.save(path,record)
  check(not any(x in cmd for x in ['input_keyevent','MODE2','reboot','killall','setsid','vconftool']),'no UI/reset/background')
  for mark in ['PRE_READY','BEFORE_INVOKE_READY','POST_READY']:
   if cmd.endswith('echo '+mark+'\n'):
    if self.kind==mark:raise ValueError('identity refusal')
    return 'FDCENSUS expected=100 missing=1 holders=0 errors=0\n'+mark+'\n'
  if 'echo PRIVATE_STAGE_CREATED\n'in cmd:return 'PRIVATE_STAGE_CREATED\n'
  if cmd.endswith('echo STAGED_CHUNK\n'):return 'STAGED_CHUNK\n'
  if cmd.endswith('echo STAGED_FILE\n'):return 'STAGED_FILE\n'
  if ' --receipt-self-test > 'in cmd:return envelope(b'{"selfTestsPassed":10,"targetOperations":0}\n',stderr=b'bad'if self.kind=='selftest-stderr'else b'')
  if ' --execute > 'in cmd:
   self.invocations+=1
   if self.kind=='timeout':raise OSError('ambiguous submission')
   if self.kind=='partial':return 'IMMEDIATE_READY\nDLMETA_BEGIN\n'
   raw=(P/'fixture.json').read_bytes()
   if self.kind=='bad-native':raw=b'{"schema":'
   if self.kind=='native-error':
    n=json.loads(raw);n['accepted']=False;n['errors']=['synthetic lifecycle failure'];raw=json.dumps(n).encode()
   return 'IMMEDIATE_READY\n'+envelope(raw,1 if self.kind=='exit'else 0,stderr=b'bad'if self.kind=='stderr'else b'')
  if cmd.endswith('echo FINAL_INTEGRITY_OK\n'):return 'FINAL_INTEGRITY_OK\n'
  if cmd.endswith('echo STAGE_ABSENT\n'):
   self.cleanups+=1
   if self.kind=='cleanup':raise OSError('cleanup failure')
   return 'STAGE_ABSENT\n'
  raise ValueError('unclassified command')
n=p.parse_native((P/'fixture.json').read_text());check(n['postDriver']['managed']['fileExists']['value']=='True','diagnostic records differing .NETvalue without rejecting it')
for k in p.FIELDS:
 x=copy.deepcopy(n);x.pop(k);reject(lambda:p.parse_native(json.dumps(x)))
for key,value in [('vendorHeaders',1),('vendorBulkTransfers',1),('vendorControlTransfers',1),('accepted',False),('driverPolicyEstablished',True),('device',57),('interface',1),('released',False),('closed',False)]:
 x=copy.deepcopy(n);x[key]=value;reject(lambda:p.parse_native(json.dumps(x)))
for field in ['preKernelDriver','postKernelDriver']:
 x=copy.deepcopy(n);x[field]['sha256']='0'*64;reject(lambda:p.parse_native(json.dumps(x)))
 x=copy.deepcopy(n);x[field]['rawBase64']='AAAA';reject(lambda:p.parse_native(json.dumps(x)))
# Post-claim metadata is observation, including individual managed-method errors.
x=copy.deepcopy(n);x['postDriver']['managed']['resolvedFinal']={'ok':False,'value':None,'error':'synthetic resolution failure'};check(p.parse_native(json.dumps(x))['accepted'],'individual diagnostic error preserved')
manifest,payload=r.build_manifest();reviewed=r.manifest_bytes(manifest)
with tempfile.TemporaryDirectory(prefix='do-host-only-')as tmp:
 base=Path(tmp);ready=decision();raw=json.dumps(ready).encode();q=base/'ready.json';q.write_bytes(raw);loaded,b=r.load_readiness(q,r.sha(raw));check(loaded==ready and b==raw,'exact readiness')
 x=copy.deepcopy(ready);x['identity']['devnum']='57';bad=json.dumps(x).encode();q.write_bytes(bad);reject(lambda:r.load_readiness(q,r.sha(bad)))
 f=FakeRoot();out=base/'success';res=r.execute(out,ready,raw,reviewed,payload,f,p);check(res['accepted']and f.invocations==f.cleanups==1 and res['vendorHeaders']==0,'one claim diagnostic success cleanup')
 for kind in ['PRE_READY','BEFORE_INVOKE_READY','POST_READY','selftest-stderr','timeout','partial','bad-native','native-error','exit','stderr','cleanup']:
  f=FakeRoot(kind);out=base/kind;reject(lambda:r.execute(out,ready,raw,reviewed,payload,f,p));check(f.invocations<=1,'no retry');check(not(out/'result.json').exists(),'no accepted result')
  if kind!='cleanup':check(f.cleanups==0,'failure retains stage')
 for key in ['accepted','interfaceUnbound','noHolders']:
  x=copy.deepcopy(ready);x[key]=False;b=json.dumps(x).encode();q.write_bytes(b);reject(lambda:r.load_readiness(q,r.sha(b)))
for bad in [envelope(b'{}')+'extra',envelope(b'{}').replace(r.sha(b'{}'),'0'*64),envelope(b'x'*24577),envelope(b'{}',stdout=b'x'*16385)]:reject(lambda:r.receipt_envelope(bad))
source=(P/'Program.cs').read_text();check(all(s not in source for s in ['0xc0105502','ioctlTransfer','usbdevfs_bulktransfer','ctrltransfer','0x4701','0x4500']),'no vendor or controller-memory operation path')
check(source.count('ioctlInterface(fd,ClaimRequest')==1 and source.count('ioctlInterface(fd,ReleaseRequest')==1 and source.count('ioctlGetDriver(fd,GetDriverRequest')==1,'fixed request sites')
dot='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet';dll=str(P/'bin/Release/net6.0/ClaimDiagnostic.dll')
q=subprocess.run([dot,dll,'--execute'],capture_output=True);check(q.returncode==64 and b'REFUSED_ARM32_ABI'in q.stdout and not q.stderr,'host ABI refusal before device access')
stage=Path('/tmp/researcher-do-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
try:
 q=subprocess.run([dot,dll,'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);receipt=stage/'selftest.receipt.json';check(q.returncode==0 and not q.stderr and json.loads(receipt.read_bytes())=={'selfTestsPassed':10,'targetOperations':0},'actual host fake-only receipt');check(stat.S_IMODE(receipt.stat().st_mode)==0o600,'private receipt mode');b=receipt.read_bytes();q=subprocess.run([dot,dll,'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);check(q.returncode!=0 and receipt.read_bytes()==b,'exclusive no overwrite')
finally:
 for q in stage.iterdir():q.unlink()
 stage.rmdir()
print(json.dumps({'checksPassed':checks,'targetOperations':0,'shells':len(commands),'maxCommandBytes':max(len(c.encode())for c in commands)}))
