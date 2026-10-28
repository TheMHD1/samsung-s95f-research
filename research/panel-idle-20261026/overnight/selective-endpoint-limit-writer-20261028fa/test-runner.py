#!/usr/bin/env python3
"""Host-only mocks, receipt mutation and shell syntax checks. No transport import."""
from pathlib import Path
import base64,copy,hashlib,json,subprocess,sys,tempfile,types,shlex,uuid,os,stat,resource
P=Path(__file__).resolve().parent
r=types.ModuleType('dj_wrapper');r.__file__=str(P/'run-once.py');exec(compile(Path(r.__file__).read_bytes(),r.__file__,'exec'),r.__dict__)
p=r.load_pinned(P/'parse-result.py',r.PARSER_SHA,'dj_parser');checks=0;commands=[]
def check(b,s):
 global checks
 if not b:raise ValueError(s)
 checks+=1
def reject(f):
 try:f()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'rejected');return
 raise ValueError('unexpected acceptance')
def decision():
 return {'schema':'fa-fixed-limit-readiness-decision-v1','accepted':True,'identity':{'boot':r.BOOT,'sysfsRealpath':'/sys/devices/platform/usb/usb7/7-1','sysfsStat':'42:1234','busnum':'7','devnum':'57','deviceNode':'/dev/bus/usb/007/057','nodeStat':'bd:338:12345','descriptorsSha256':r.sha(bytes.fromhex(r.DESCRIPTORS)),'configuration':'1','authorized':'1','runtimeStatus':'active','interfaceNumber':'02','alternate':'0','interfaceClass':'ff','interfaceSubClass':'00','interfaceProtocol':'00'},'interfaceUnbound':True,'noHolders':True,'closedWorldVendorOutLineage':{'accepted':True,'statement':'SYNTHETIC HOST TEST ONLY: no assertion about any real device queue or lineage.','evidenceSha256':'a'*64},'evidence':[{'path':'/host/fake-only.json','sha256':'b'*64}],'endpointQueueProof':False}
def envelope(receipt,rc=0,stdout=b'[GC_INFO] GC_Start #1\n[GC_INFO] GC_End #1\n',stderr=b''):
 values=[receipt,stdout,stderr]
 h='DLMETA_BEGIN\n'+r.BOOT+'\n1.0 2.0\n'+str(rc)+'\n'
 for raw in values:h+=str(len(raw))+'\n'+r.sha(raw)+'\n'
 h+='DLMETA_END\n'
 for raw,label in zip(values,['RECEIPT','STDOUT','STDERR']):h+=label+'_B64_BEGIN\n'+base64.b64encode(raw).decode()+'\n'+label+'_B64_END\n'
 return h+'DLRUN_COMPLETE\n'
class FakeRoot:
 def __init__(self,kind='success',action='set'):self.kind=kind;self.action=action;self.invocations=0;self.cleanups=0;self.selftests=0;self.stdout=(P/('fixture-'+action+'.json')).read_bytes()
 def root(self,command,record,path):
  commands.append(command);check(len(command.encode())<=8192,'command bound');v=subprocess.run(['sh','-n'],input=command.encode(),capture_output=True);check(v.returncode==0,'shell syntax')
  check(not any(s in command for s in ['input_keyevent','vconftool','reboot','killall','setsid',' --key-','MODE2','SetPower']),'no unrelated actions');r.save(path,record)
  for label in ['PRE_READY','BEFORE_INVOKE_READY','POST_READY']:
   if command.endswith('echo '+label+'\n'):
    if self.kind==label:raise ValueError('identity/census refusal')
    return 'FDCENSUS expected=120 missing=1 holders=0 errors=0\n'+label+'\n'
  if 'echo PRIVATE_STAGE_CREATED\n' in command:return 'PRIVATE_STAGE_CREATED\n'
  if command.endswith('echo STAGED_CHUNK\n'):return 'STAGED_CHUNK\n'
  if command.endswith('echo STAGED_FILE\n'):return 'STAGED_FILE\n'
  if ' --receipt-self-test > ' in command:
   self.selftests+=1
   receipt=b'{"selfTestsPassed":205631,"targetOperations":0}\n'
   if self.kind=='selftest-receipt':receipt=b'{"selfTestsPassed":0,"targetOperations":0}\n'
   if self.kind=='selftest-timeout':raise OSError('selftest ambiguity')
   if self.kind=='selftest-partial':return 'DLMETA_BEGIN\n'
   return envelope(receipt,1 if self.kind=='selftest-exit' else 0,stderr=b'error' if self.kind=='selftest-stderr' else b'')
  if ' --execute-' in command:
   self.invocations+=1;check(' --execute-'+self.action+' --device 57 > ' in command,'fixed action')
   if self.kind=='timeout':raise OSError('submission ambiguity; no retry')
   if self.kind=='partial':return 'IMMEDIATE_READY\nDLMETA_BEGIN\n'
   if self.kind=='bad-native':return 'IMMEDIATE_READY\n'+envelope(b'{"schema":')
   if self.kind=='bad-exit':return 'IMMEDIATE_READY\n'+envelope(self.stdout,1)
   if self.kind=='stderr':return 'IMMEDIATE_READY\n'+envelope(self.stdout,stderr=b'bad')
   if self.kind=='wrong-action':return 'IMMEDIATE_READY\n'+envelope((P/'fixture-restore.json').read_bytes())
   if self.kind=='diagnostic-json':return 'IMMEDIATE_READY\n'+envelope(self.stdout,stdout=b'[GC_INF{nonsense}\nO] nativeGCfragment\n')
   return 'IMMEDIATE_READY\n'+envelope(self.stdout)
  if command.endswith('echo FINAL_INTEGRITY_OK\n'):return 'FINAL_INTEGRITY_OK\n'
  if command.endswith('echo STAGE_ABSENT\n'):
   self.cleanups+=1
   if self.kind=='cleanup':raise OSError('cleanup failure')
   return 'STAGE_ABSENT\n'
  raise ValueError('unclassified command')
for action in ['set','restore']:
 raw=(P/('fixture-'+action+'.json')).read_bytes();n,files,gc=p.parse_native(raw.decode());check(len(files)==6 and not gc,'host fixture accepted')
 for field in p.NATIVE_FIELDS:
  x=copy.deepcopy(n);x.pop(field);reject(lambda:p.parse_native(json.dumps(x)))
 for field in ['accepted','released','closed','writeTransportComplete','readbackVerified','opened','claimed']:
  x=copy.deepcopy(n);x[field]=False;reject(lambda:p.parse_native(json.dumps(x)))
 for i in range(14):
  for key,val in [('count',-1),('direction','OUT' if n['steps'][i]['direction']=='IN' else 'IN'),('after','Unknown'),('beforeUs',-1),('errno',5)]:
   x=copy.deepcopy(n);x['steps'][i][key]=val;reject(lambda:p.parse_native(json.dumps(x)))
 for i in range(6):
  x=copy.deepcopy(n);x['windows'][i]['sha256']='0'*64;reject(lambda:p.parse_native(json.dumps(x)))
  x=copy.deepcopy(n);w=x['windows'][i];b=bytearray(base64.b64decode(w['base64']));b[0]^=128;w['base64']=base64.b64encode(b).decode();w['sha256']=r.sha(b)
  if i in [1,4,5]:reject(lambda:p.parse_native(json.dumps(x)))
 reject(lambda:p.parse_native(raw.decode()+raw.decode()))
 reject(lambda:p.parse_native(raw.decode().replace('"schema":','"schema":"duplicate","schema":',1)))
# Exact native binding evidence is semantic receipt input, independent of the controller data.
for action in ['set','restore']:
 good=json.loads((P/('fixture-'+action+'.json')).read_bytes())
 for i in range(3):
  for key,value in [('stage','unknown'),('ownClaim',None),('localFdMatches',None)]:
   x=copy.deepcopy(good);x['bindingChecks'][i][key]=value;reject(lambda:p.parse_native(json.dumps(x)))
  for name in ['link','follow','canonical']:
   for field in ['return','errno','mask','mode','inode','devMajor','devMinor']:
    x=copy.deepcopy(good);x['bindingChecks'][i][name][field]=True;reject(lambda:p.parse_native(json.dumps(x)))
 for i in [1,2]:
  for key,value in [('return',7),('errno',13),('name','other'),('interface',1),('rawBase64','AAAA'),('sha256','0'*64)]:
   x=copy.deepcopy(good);x['bindingChecks'][i]['kernel'][key]=value;reject(lambda:p.parse_native(json.dumps(x)))
 for field in ['inode','devMajor','devMinor']:
  x=copy.deepcopy(good);x['bindingChecks'][2]['follow'][field]+=1;reject(lambda:p.parse_native(json.dumps(x)))
 x=copy.deepcopy(good);x['bindingChecks'].reverse();reject(lambda:p.parse_native(json.dumps(x)))
 x=copy.deepcopy(good);x['bindingChecks'][0]['link']['errno']=13;reject(lambda:p.parse_native(json.dumps(x)))
 x=copy.deepcopy(good);x['bindingChecks'][2]['canonical']['mask']=3;reject(lambda:p.parse_native(json.dumps(x)))
 x=copy.deepcopy(good);x['bindingChecks'][2]['follow']['mode']=0xa1ff;reject(lambda:p.parse_native(json.dumps(x)))
# Fixed transport, ownership, receipts and action paths remain frozen; pure guard delta audited separately.
parent=(P.parent/'volatile-limit-native-binding-20261028dq/Program.cs').read_text();current=(P/'Program.cs').read_text()
for start,end in [('    sealed class Controller','    static Outcome Run'),('    sealed class RealClock','    sealed class FakeClock'),('    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen','    static int Main')]:
 check(parent[parent.index(start):parent.index(end)]==current[current.index(start):current.index(end)].replace('fa-','dq-'),'unchanged native fixed source '+start)
manifest,payload=r.build_manifest();reviewed=r.manifest_bytes(manifest)
check(reviewed==r.manifest_bytes(r.build_manifest()[0]),'deterministic manifest')
with tempfile.TemporaryDirectory(prefix='dn-host-only-') as t:
 base=Path(t);ready=decision();raw=json.dumps(ready).encode();rp=base/'ready.json';rp.write_bytes(raw);v,b=r.load_readiness(rp,r.sha(raw));check(v==ready and b==raw,'readiness accepted')
 for k in ['accepted','interfaceUnbound','noHolders']:
  x=copy.deepcopy(ready);x[k]=False;bad=json.dumps(x).encode();rp.write_bytes(bad);reject(lambda:r.load_readiness(rp,r.sha(bad)))
 for action in ['set','restore']:
  f=FakeRoot(action=action);out=base/('success-'+action);res=r.execute(out,ready,raw,reviewed,payload,f,p,action);check(res['accepted'] and f.invocations==f.cleanups==1,'one fixed action and cleanup')
 for kind in ['PRE_READY','BEFORE_INVOKE_READY','POST_READY','timeout','partial','bad-native','bad-exit','stderr','wrong-action','cleanup','selftest-receipt','selftest-exit','selftest-stderr','selftest-partial','selftest-timeout']:
  f=FakeRoot(kind);out=base/kind;reject(lambda:r.execute(out,ready,raw,reviewed,payload,f,p,'set'));check(f.invocations<=1,'never retry')
  if kind not in ['cleanup']:check(f.cleanups==0,'failure retains stage')
  if kind in ['partial','bad-native','bad-exit','stderr','wrong-action']:check((out/'native-envelope.txt').exists(),'preserve envelope before parse')
 f=FakeRoot('diagnostic-json');res=r.execute(base/'diagnostic-json',ready,raw,reviewed,payload,f,p,'set');check(res['accepted'] and f.invocations==1,'GC stdout has no receipt semantics')
 for action in ['set','restore']:
  f=FakeRoot(action=action);out=base/('collide-'+action);out.mkdir();reject(lambda:r.execute(out,ready,raw,reviewed,payload,f,p,action));check(f.invocations==0,'fresh output refusal')
dry=subprocess.run([sys.executable,'-B',str(P/'run-once.py')],capture_output=True);check(dry.returncode==0 and not dry.stderr and json.loads(dry.stdout)['targetOperations']==0,'default dry')

# Check generated metadata uses exactly one batched stat census, no per-FD
# external command, and precise rdev matching (alternate path names covered).
body=r.metadata_body(decision()['identity'],'PRE_READY')
check(body.count('bx_fd_snapshot=$(LC_ALL=C stat ') == 1 and 'for bx_fd' not in body, 'bounded batch census')
check('test "$#" -le 32768' in body and 'stat -L -c "%F|%t:%T" "$@"' in body, 'census bounded/noholders')
check(max(len(command.encode()) for command in commands) <= 8192, 'all command maxima')
# Execute only the standalone awk classifier with synthetic text; no target
# shell or /proc traversal. ENOENT is snapshot churn, never queue clearance.
def classify(text, expected, rc):
    return subprocess.run(['awk','-F','|','-v','expected='+str(expected),'-v','rc='+str(rc),
                           '-v','bx_rdev=bd:338',r.FD_CENSUS_AWK],input=text.encode(),capture_output=True)
# Exact ordinary-target diagnostic fixture acquired by the parent, never
# generated by this host test. Opening quote is ASCII backtick, closing quote
# is ASCII apostrophe; keep the source bytes and hash pinned.
actual_stat=(P.parent/'onset-sync-20261027bx/stat-format-qualified-03.txt').read_bytes()
check(r.sha(actual_stat) == 'df9ca13c2d7fa58897e0292519cbf2034d9f8b8b0a8e49b51e26dd8d14e702fe',
      'actual target stat fixture pin')
actual_lines=actual_stat.decode('ascii').splitlines()
check(actual_lines[3] == "stat: cannot stat `/proc/2147483647/fd/2147483647': No such file or directory",
      'actual backtick/apostrophe diagnostic')
actual_reply=classify('\n'.join(actual_lines[:4])+'\n',4,1)
check(actual_reply.returncode == 0 and actual_reply.stderr == b'' and
      actual_reply.stdout == b'FDCENSUS expected=4 missing=1 holders=0 errors=0\n',
      'actual target stat ENOENT classification')
for text, expected, rc, accepted in [
    ('regular file|0:0\ncharacter special file|1:3\n',2,0,True),
    ("stat: cannot statx '/proc/123/fd/4': No such file or directory\nregular file|0:0\n",2,1,True),
    ("stat: can't stat '/proc/123/fd/4': No such file or directory\nregular file|0:0\n",2,1,True),
    ("stat: cannot stat `/proc/123/fd/4': No such file or directory\nregular file|0:0\n",2,1,True),
    ("stat: cannot stat `/proc/123/fd/4': Permission denied\n",1,1,False),
    ("stat: cannot stat `/proc/non_numeric/fd/4': No such file or directory\n",1,1,False),
    ("stat: cannot stat `/proc/123/fd/4`: No such file or directory\n",1,1,False),
    ("stat: cannot stat `/proc/123/fd/4': No such file or directory extra\n",1,1,False),
    ('character special file|bd:338\n',1,0,False),
    ('character special file|bd:3380\n',1,0,True),
    ("stat: cannot statx '/proc/123/fd/4': Permission denied\n",1,1,False),
    ("stat: cannot statx '/etc/passwd': No such file or directory\n",1,1,False),
    ('regular file|0:0\n',2,0,False),
    ("stat: cannot statx '/proc/123/fd/4': No such file or directory\n",1,0,False),
    ('regular file|0:0\n',1,2,False),
    ('unexpected diagnostic\n',1,1,False),
]:
    response=classify(text,expected,rc)
    check((response.returncode == 0) is accepted and response.stderr == b'', 'synthetic stat classifier')
    if accepted:
        counts=r.parse_metadata(response.stdout.decode()+'PRE_READY\n','PRE_READY')
        check(counts['continuousAbsenceEstablished'] is False, 'snapshot narrow scope')
# Execute the exact shell-quoted census command-substitution and awk pipeline
# emitted by metadata_body. Mock only stat using a local fixture; do not execute
# identity getters, actual /proc traversal, or any target/root transport.
first=body.index('if bx_fd_snapshot=')
last=body.index('\nbx_value=',first)
exact_pipeline=body[first:last]
check(chr(92) not in r.FD_CENSUS_AWK and chr(92) not in exact_pipeline,
      'census classifier/pipeline has no backslash transport sensitivity')
with tempfile.TemporaryDirectory(prefix='bx-exact-census-host-only-') as tmp:
    fixture=Path(tmp)/'stat.txt'
    for text,expected,rc,accepted in [
        ('\n'.join(actual_lines[:4])+'\n',4,1,True),
        ('regular file|0:0\ncharacter special file|1:3',2,0,True),
        ('character special file|bd:338\n',1,0,False),
        ("stat: cannot stat `/proc/123/fd/4': Permission denied\n",1,1,False),
    ]:
        fixture.write_text(text)
        script=('set -eu\nstat() { cat '+shlex.quote(str(fixture))+'; return '+str(rc)+'; }\n' +
                'set -- '+' '.join('/proc/2147483647/fd/'+str(i) for i in range(expected))+'\n'+exact_pipeline+'\n')
        response=subprocess.run(['sh'],input=script.encode(),capture_output=True)
        check((response.returncode == 0) is accepted and response.stderr == b'',
              'execute exact generated census shell on local fixture')
        if accepted:
            counts=r.parse_metadata(response.stdout.decode()+'PRE_READY\n','PRE_READY')
            check(counts['expected'] == expected and counts['observedHolders'] == 0,
                  'exact generated shell receipt and counts')
for text in ['PRE_READY\n','FDCENSUS expected=0 missing=0 holders=0 errors=0\nPRE_READY\n',
             'FDCENSUS expected=1 missing=2 holders=0 errors=0\nPRE_READY\n',
             'FDCENSUS expected=1 missing=0 holders=1 errors=0\nPRE_READY\n']:
    reject(lambda:r.parse_metadata(text,'PRE_READY'))

with tempfile.TemporaryDirectory(prefix='dn-action-host-only-') as tmp:
 f=FakeRoot();reject(lambda:r.execute(Path(tmp)/'bad',decision(),b'{}',reviewed,payload,f,p,'set; echo BAD'));check(f.invocations==0,'reject arbitrary API action')
for action in ['set','restore']:
 host=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/FixedLimit.dll'),'--execute-'+action,'--device','57'],capture_output=True)
 check(host.returncode==64 and b'ARM32 ABI required' in host.stdout and not host.stderr,'host ABI refusal before native calls')
reject(lambda:p.parse_native('[GC_INFO] console telemetry\n'+(P/'fixture-set.json').read_text()))
# Framed receipts remain independent of arbitrary diagnostic bytes, including
# the actual previous target self-test's byte-interleaved managed JSON row.
oldgc=(P/'fixtures/gc-interleaved-selftest.txt').read_bytes()
check(r.sha(oldgc)=='725e3f4a253ccdcc4148d18d135a372c053e6b2a4a9ed8aa34024c9f1feb7353','actual previous GC fixture pin')
receipt=b'{"selfTestsPassed":205631,"targetOperations":0}\n';framed=envelope(receipt,stdout=oldgc)
terminal,actual,diag,err=r.receipt_envelope(framed);check(actual==receipt and diag==oldgc and not err,'actual mixed GC does not affect receipt')
for bad in [framed+framed,framed+'extra\n',framed.replace('DLRUN_COMPLETE','BAD_COMPLETE'),framed.replace(r.sha(receipt),'0'*64),framed.replace('DLMETA_BEGIN','DLMETA_BEGIN\n'),framed[:-1]]:reject(lambda:r.receipt_envelope(bad))
reject(lambda:r.receipt_envelope(envelope(b'x'*24577)))
reject(lambda:r.receipt_envelope(envelope(receipt,stdout=b'x'*16385)))
reject(lambda:r.receipt_envelope(envelope(receipt,stderr=b'x'*2049)))
# Run only the native fake-operations self-test on this host, in an exclusive
# host-created private directory with the same fixed pathname contract.
stage=Path('/tmp/researcher-limit-fa-'+uuid.uuid4().hex);stage.mkdir(mode=0o700)
def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def selftest_receipt(cwd):
 return subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/FixedLimit.dll'),'--receipt-self-test'],cwd=cwd,capture_output=True,preexec_fn=no_core)
try:
 q=selftest_receipt(stage);file=stage/'selftest.receipt.json';check(q.returncode==0 and not q.stderr,'actual host exclusive receipt creation');raw=file.read_bytes();check(json.loads(raw)=={'selfTestsPassed':205631,'targetOperations':0},'actual host selftest receipt');check(stat.S_IMODE(file.stat().st_mode)==0o600,'receipt0600')
 q=selftest_receipt(stage);check(q.returncode!=0 and file.read_bytes()==raw,'exclusive no overwrite');file.unlink()
 with tempfile.TemporaryDirectory(prefix='dn-sentinel-host-only-') as other:
  sentinel=Path(other)/'sentinel';sentinel.write_bytes(b'unchanged');file.symlink_to(sentinel);q=selftest_receipt(stage);check(q.returncode!=0 and sentinel.read_bytes()==b'unchanged' and file.is_symlink(),'receipt symlink refused');file.unlink()
 stage.chmod(0o755);q=selftest_receipt(stage);check(q.returncode!=0 and not file.exists(),'nonprivate stage refused');stage.chmod(0o700)
 with tempfile.TemporaryDirectory(prefix='dn-wrong-stage-host-only-') as other:
  q=selftest_receipt(other);check(q.returncode!=0 and not list(Path(other).iterdir()),'fixed directory shape required')
 check(not list(stage.iterdir()),'host fixture leaves no unexpected files')
finally:
 for x in stage.iterdir():x.unlink()
 stage.rmdir()
# New DV admission policy: direct parser functions are the exact frozen DU model.
def modeled_r(temperature,echo,limit):
 b=bytearray(p.PROFILE);upper=p.endpoint(2075,24,temperature,15,195,3000,3800)['endpoint']
 for offset,value in [(0x20,upper),(0xbc,upper),(0x98,temperature),(0xac,echo),(0xc4,limit)]:b[offset:offset+2]=value.to_bytes(2,'little')
 return bytes(b)
def replace_window(row,name,b):
 w=next(w for w in row['windows'] if w['name']==name);w['base64']=base64.b64encode(b).decode();w['sha256']=r.sha(b)
def modeled_receipt(action,temperature,echoes):
 row=json.loads((P/('fixture-'+action+'.json')).read_bytes());old,new=(40,200)if action=='set'else(200,40)
 for name,limit,echo in zip(['baseline-R','fresh-R','readback-R'],[old,old,new],echoes):replace_window(row,name,modeled_r(temperature,echo,limit))
 b=bytearray(base64.b64decode(next(w['base64']for w in row['windows']if w['name']=='pre-M')));b[38:40]=p.endpoint(2075,24,temperature,15,195,3000,3800)['endpoint'].to_bytes(2,'little');replace_window(row,'pre-M',bytes(b));return row
for t in range(4096):
 b=modeled_r(t,0,40);p.guard_r(b,40);check(True,'every source temperature model guard')
for action in ['set','restore']:
 for t in [0,24,25,4095]:
  row=modeled_receipt(action,t,[254,0,1]);accepted,raws,gc=p.parse_native(json.dumps(row));check(accepted['accepted']and len(raws)==6 and not gc,'full structured receipt with model/echo wrap')
 good=modeled_receipt(action,24,[0,1,2]);old,new=(40,200)if action=='set'else(200,40)
 for name,limit in [('baseline-R',old),('fresh-R',old),('readback-R',new)]:
  for offset,value in [(0x20,3162),(0xbc,3200),(0x98,4096),(0xac,255),(0xac,256),(0x94,2076),(0x96,25),(0xae,16),(0xb0,194),(0xb2,3801),(0x2e,2999),(0xb6,16),(0xb8,194),(0xba,3801),(0x2c,2999)]:
   row=copy.deepcopy(good);b=bytearray(base64.b64decode(next(w['base64']for w in row['windows']if w['name']==name)));b[offset:offset+2]=value.to_bytes(2,'little');replace_window(row,name,bytes(b));reject(lambda:p.parse_native(json.dumps(row)))
 for name,limit in [('fresh-R',old),('readback-R',new)]:
  row=copy.deepcopy(good);replace_window(row,name,modeled_r(25,1,limit));reject(lambda:p.parse_native(json.dumps(row)))
 row=modeled_receipt(action,0,[0,1,2]);replace_window(row,'fresh-R',modeled_r(1,1,old));reject(lambda:p.parse_native(json.dumps(row))) # equal clamped endpoints still differ in temperature
 for value in [3183,3200]:
  row=copy.deepcopy(good);b=bytearray(base64.b64decode(next(w['base64']for w in row['windows']if w['name']=='pre-M')));b[38:40]=value.to_bytes(2,'little');replace_window(row,'pre-M',bytes(b));reject(lambda:p.parse_native(json.dumps(row)))
for i in range(256):
 if not p.legacy_historical_byte(i) and i not in p.ADDITIONAL_MODEL_BYTES|{0xc4,0xc5,0xca}:
  b=bytearray(p.PROFILE);b[i]^=1;reject(lambda:p.guard_r(bytes(b),40))
# Actual fresh admission is read-only evidence; record only identities, never duplicate raw inputs.
base=P.parent/'volatile-limit-trial-20261028dk/admission-clean-01';raw=(base/'start-R.bin').read_bytes();p.guard_r(raw,40);p.validate_candidate_context((base/'M.bin').read_bytes(),(base/'C.bin').read_bytes(),raw);check(raw==(base/'end-R.bin').read_bytes(),'actual admission thermal/context guard and same R')
# FA exact finite-preimage and actual EX complete synthetic receipt integration.
image=set(p.endpoint(2075,24,t,15,195,3000,3800)['endpoint']for t in range(4096))
check(len(image)==72 and image==p.ALTERNATE_ENDPOINT_IMAGE,'exact72sourceimage')
for value in range(3000,3801):
 b=bytearray(modeled_r(24,3,40));b[0xbc:0xbe]=value.to_bytes(2,'little')
 if value in image:p.guard_r(bytes(b),40);check(True,'finiteimageadmitted')
 else:reject(lambda:p.guard_r(bytes(b),40))
ex=P.parent/'limit-rechallenge-trial-20261028ex/preparation-01/baseline'
xr=(ex/'start-R.bin').read_bytes();xm=(ex/'M.bin').read_bytes();xc=(ex/'C.bin').read_bytes()
p.guard_r(xr,40);p.validate_candidate_context(xm,xc,xr);check(xr==(ex/'end-R.bin').read_bytes(),'actual EXnewpolicyadmission')
old=P.parent/'volatile-limit-dynamic-profile-20261028dv/parse-result.py';dv=types.ModuleType('frozenDV');dv.__file__=str(old);exec(compile(old.read_bytes(),str(old),'exec'),dv.__dict__);reject(lambda:dv.guard_r(xr,40))
for action in ['set','restore']:
 row=json.loads((P/('fixture-'+action+'.json')).read_bytes());oldlimit,newlimit=(40,200)if action=='set'else(200,40)
 for name,limit in [('baseline-R',oldlimit),('fresh-R',oldlimit),('readback-R',newlimit)]:
  raw=bytearray(xr);raw[0xc4:0xc6]=limit.to_bytes(2,'little');replace_window(row,name,bytes(raw))
 replace_window(row,'pre-M',xm);replace_window(row,'pre-C',xc);accepted,raws,gc=p.parse_native(json.dumps(row));check(accepted['accepted'],'syntheticEXprofilefullreceipt')
 # Both alternate values valid individually; pairwise drift remains forbidden before/after write.
 for name in ['fresh-R','readback-R']:
  changed=copy.deepcopy(row);raw=bytearray(base64.b64decode(next(w['base64']for w in changed['windows']if w['name']==name)));raw[0xbc:0xbe]=(3161).to_bytes(2,'little');replace_window(changed,name,bytes(raw));reject(lambda:p.parse_native(json.dumps(changed)))
print(json.dumps({'checksPassed':checks,'targetOperations':0,'commandsSyntaxChecked':len(commands),'maximumCommandBytes':max(map(lambda c:len(c.encode()),commands))}))
