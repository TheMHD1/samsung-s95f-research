#!/usr/bin/env python3
"""Host-only DM mocks/parser mutations; never imports root transport."""
from pathlib import Path
import base64,copy,json,subprocess,sys,tempfile,types,uuid,os,stat,resource
P=Path(__file__).resolve().parent
r=types.ModuleType('dm');r.__file__=str(P/'run-once.py');exec(compile(Path(r.__file__).read_bytes(),r.__file__,'exec'),r.__dict__)
p=r.load_pinned(P/'parse-result.py',r.PARSER_SHA,'dm_parser');checks=0;commands=[]
def check(x,s):
 global checks
 if not x:raise ValueError(s)
 checks+=1
def reject(f):
 try:f()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'refusal');return
 raise ValueError('unexpected acceptance')
def decision():
 return {'schema':'eb-rtp-lane-gate-readiness-decision-v1','accepted':True,'identity':{'boot':r.BOOT,'sysfsRealpath':'/sys/devices/platform/usb/usb7/7-1','sysfsStat':'42:1234','busnum':'7','devnum':'57','deviceNode':'/dev/bus/usb/007/057','nodeStat':'bd:338:12345','descriptorsSha256':r.sha(bytes.fromhex(r.DESCRIPTORS)),'configuration':'1','authorized':'1','runtimeStatus':'active','interfaceNumber':'02','alternate':'0','interfaceClass':'ff','interfaceSubClass':'00','interfaceProtocol':'00'},'interfaceUnbound':True,'noHolders':True,'closedWorldVendorOutLineage':{'accepted':True,'statement':'SYNTHETIC HOST TEST ONLY: not evidence of any real USB instance or queue readiness.','evidenceSha256':'a'*64},'evidence':[{'path':'/host/fake-only','sha256':'b'*64}],'endpointQueueProof':False}
def envelope(receipt,code=0,stdout=b'[GC_INF{not semantic receipt}\nO] arbitrary diagnostics',stderr=b''):
 vals=(receipt,stdout,stderr);s='EBMETA_BEGIN\n'+r.BOOT+'\n1.0 2.0\n'+str(code)+'\n'
 for b in vals:s+=str(len(b))+'\n'+r.sha(b)+'\n'
 s+='EBMETA_END\n'
 for name,b in zip(('RECEIPT','STDOUT','STDERR'),vals):s+=name+'_B64_BEGIN\n'+base64.b64encode(b).decode()+'\n'+name+'_B64_END\n'
 return s+'EBRUN_COMPLETE\n'
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
   return envelope(b'{"selfTestsPassed":2071,"targetOperations":0}\n')
  if ' --execute --device ' in command:
   self.invocations+=1;check(' --execute --device 57 > ' in command,'fixed device invocation')
   if self.kind=='timeout':raise OSError('ambiguous invoke; no retry')
   if self.kind=='partial':return 'IMMEDIATE_READY\nEBMETA_BEGIN\n'
   raw=(P/'fixture.json').read_bytes()
   if self.kind=='malformed':raw=b'{"schema":'
   if self.kind=='wrong-device':n=json.loads(raw);n['device']=58;raw=json.dumps(n).encode()
   return 'IMMEDIATE_READY\n'+envelope(raw,1 if self.kind=='bad-exit' else 0,stderr=b'x' if self.kind=='stderr' else b'')
  if command.endswith('echo STAGE_ABSENT\n'):
   self.cleanups+=1
   if self.kind=='cleanup':raise OSError('cleanup ambiguity')
   return 'STAGE_ABSENT\n'
  raise ValueError('unclassified fake command')
raw=(P/'fixture.json').read_bytes();n,files,interpret=p.parse_native(raw.decode());check(len(files)==16 and interpret['transportAccepted'] and not interpret['atomicSnapshot'] and not interpret['recordEpochProven'],'postfault transport and conservative interpretation');check(interpret['startR']['stop']==1 and interpret['nBytesEqual'] and interpret['rBytesEqual'],'postfault allowed; matching brackets not atomic')
for field in p.FIELDS:
 x=copy.deepcopy(n);x.pop(field);reject(lambda:p.parse_native(json.dumps(x)))
for i in range(32):
 for key,value in [('count',-1),('beforeUs',-1),('after','Unknown'),('direction','BAD'),('errno',5),('expected',True)]:
  x=copy.deepcopy(n);x['steps'][i][key]=value;reject(lambda:p.parse_native(json.dumps(x)))
for i in range(16):
 for key,value in [('sha256','0'*64),('address',0x60000000),('bytes',95),('name','arbitrary')]:
  x=copy.deepcopy(n);x['windows'][i][key]=value;reject(lambda:p.parse_native(json.dumps(x)))
reject(lambda:p.parse_native(raw.decode()+raw.decode()));reject(lambda:p.parse_native('[GC_INFO] x\n'+raw.decode()));reject(lambda:p.parse_native(raw.decode().replace('"schema":','"schema":"dup","schema":',1)))
x=copy.deepcopy(n);w=x['windows'][1];b=bytearray(base64.b64decode(w['base64']));b[64]^=1;w['base64']=base64.b64encode(b).decode();w['sha256']=r.sha(b);reject(lambda:p.parse_native(json.dumps(x)))

# Fixed candidates are synthetic lane values in the native host fixture, not fault-time A.
check(interpret['sourceContext']['xBase']==0 and interpret['sourceContext']['packedBytes']==2880 and interpret['sourceContext']['lanes']==1920,'exact packing context')
for kind in ('top','bottom'):
 check(interpret['fixedReferenceCandidates'][kind]=={str(x):x for x in (570,571,622,623,624,625,632,633)},'synthetic fixed index decoding')
for name,offset in [('M',6),('M',8),('M',32),('M',64),('C',0),('C',2),('C',4)]:
 x=copy.deepcopy(n);w=next(w for w in x['windows']if w['name']==name);bad=bytearray(base64.b64decode(w['base64']));bad[offset]^=1;w['base64']=base64.b64encode(bad).decode();w['sha256']=r.sha(bad);reject(lambda:p.parse_native(json.dumps(x)))
for length in (0,96,102,103,105,120):reject(lambda:p.decode_fixed(bytes(length)))
# Cross-check independent DR bit model for mixed lane bits and ignored tail.
dr=types.ModuleType('dr_model');exec(compile((P/'../rtp-fixed-reference-qualification-20261028dr/reference_model.py').read_bytes(),'reference_model.py','exec'),dr.__dict__)
for seed in range(32):
 data=bytes((i*73+seed*29)&255 for i in range(104));check(p.decode_fixed(data)=={str(k):v for k,v in dr.decode_window(data,kind='top').items()},'independent DR decoder')

# EA source predicate is conditional on sampled, sequential table/context values.
check(interpret['sourceContext']['operatingMode']==4 and interpret['sourceContext']['categoryIsOperatingMode']is False,'operating mode4 is not category1')
check(len(interpret['laneGateSamples'])==68 and not interpret['historicalGateExecutionProven'] and interpret['localEligibilityOnly'] and not interpret['actualComparatorCallProven'] and not interpret['gateBodyLiveFingerprinted'] and not interpret['lanePhysicalMappingProven'],'gate observation scope')
for i,row in enumerate(interpret['laneGateSamples']):
 check(row=={'lane':568+i,'primaryHalfword':0x100|(i&1),'primaryLowBit':i&1,'secondaryByte':i%3,'secondaryOverrideSB':False,'locallyAdmittedByCapturedTables':i%2==0 and i%3==0},'synthetic gate decode')
def rewindow(native,name,raw):
 w=next(w for w in native['windows']if w['name']==name);w['base64']=base64.b64encode(raw).decode();w['sha256']=r.sha(raw)
for mode in (6,7,65535):
 x=copy.deepcopy(n);rawr=bytearray(base64.b64decode(x['windows'][0]['base64']));rawr[16:18]=mode.to_bytes(2,'little');rewindow(x,'start-R',rawr);reject(lambda:p.parse_native(json.dumps(x)))
for aa in (0,1,2):
 for ac in (0,1,2):
  for enabled in (0,255):
   for primary in (0,1,2,65534):
    for secondary in (0,1,255):
     x=copy.deepcopy(n);m=bytearray(base64.b64decode(x['windows'][1]['base64']));m[10:12]=aa.to_bytes(2,'little');m[12:14]=ac.to_bytes(2,'little');m[44]=enabled;rewindow(x,'M',m)
     rewindow(x,'primary-lane-gate',primary.to_bytes(2,'little')*68);rewindow(x,'secondary-lane-gate',bytes([secondary])*68)
     decoded=p.parse_native(json.dumps(x))[2]['laneGateSamples'];expected=primary%2==0 and (secondary==0 or ((aa==1 or ac==1) and enabled!=0))
     check(all(row['primaryHalfword']==primary and row['secondaryByte']==secondary and row['locallyAdmittedByCapturedTables']==expected for row in decoded),'independent gate truth table')
for key in ('laneGateContextQualified','packingQualified','accepted'):
 for value in (False,0,1,None):
  x=copy.deepcopy(n);x[key]=value;reject(lambda:p.parse_native(json.dumps(x)))

manifest,payload=r.build_manifest();reviewed=r.manifest_bytes(manifest);check(reviewed==r.manifest_bytes(r.build_manifest()[0]),'manifest deterministic')
with tempfile.TemporaryDirectory(prefix='eb-host-only-') as tmp:
 base=Path(tmp);ready=decision();b=json.dumps(ready).encode();rp=base/'ready.json';rp.write_bytes(b);check(r.load_readiness(rp,r.sha(b))[0]==ready,'readiness accepted')
 for k in ('accepted','interfaceUnbound','noHolders'):
  bad=copy.deepcopy(ready);bad[k]=False;br=json.dumps(bad).encode();rp.write_bytes(br);reject(lambda:r.load_readiness(rp,r.sha(br)))
 f=FakeRoot();res=r.execute(base/'success',ready,b,reviewed,payload,f,p);check(res['accepted'] and f.invocations==f.cleanups==1 and res['headersSent']==16 and len(res['rawFiles'])==16,'one pass cleanup')
 for kind in ('PRE_READY','BEFORE_INVOKE_READY','POST_READY','selftest','timeout','partial','malformed','wrong-device','bad-exit','stderr','cleanup'):
  f=FakeRoot(kind);out=base/kind;reject(lambda:r.execute(out,ready,b,reviewed,payload,f,p));check(f.invocations<=1,'no retry');check(f.cleanups==(1 if kind=='cleanup' else 0),'failure cleanup policy')
  if kind in ('partial','malformed','wrong-device','bad-exit','stderr'):check((out/'native-envelope.txt').exists(),'save envelope before parse')
 for ftext in [envelope(b'{}')+'x',envelope(b'x'*24577),envelope(b'{}',stdout=b'x'*16385),envelope(b'{}',stderr=b'x'*2049)]:reject(lambda:r.receipt_envelope(ftext))
body=r.metadata_body(decision()['identity'],'PRE_READY');check(body.count('bx_fd_snapshot=$(LC_ALL=C stat ')==1,'batched census');check('test "$#" -le 32768' in body,'FD census bound')
check(json.loads(subprocess.run([sys.executable,'-B',str(P/'run-once.py')],check=True,capture_output=True).stdout)['targetOperations']==0,'default dry')
# Host receipt creation exercises the actual exclusive file mechanism, never RealOps.
stage=Path('/tmp/researcher-eb-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
try:
 out=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/RecordCapture.dll'),'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);file=stage/'selftest.receipt.json';check(out.returncode==0 and not out.stderr and json.loads(file.read_bytes())=={'selfTestsPassed':2071,'targetOperations':0},'actual host receipt fake selftest');check(stat.S_IMODE(file.stat().st_mode)==0o600,'actual0600');before=file.read_bytes();again=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/RecordCapture.dll'),'--receipt-self-test'],cwd=stage,capture_output=True,preexec_fn=no_core);check(again.returncode!=0 and file.read_bytes()==before,'exclusive no overwrite')
finally:
 for file in stage.iterdir():file.unlink()
 stage.rmdir()
print(json.dumps({'checksPassed':checks,'targetOperations':0,'commandsSyntaxChecked':len(commands),'maximumCommandBytes':max(len(s.encode())for s in commands)}))
