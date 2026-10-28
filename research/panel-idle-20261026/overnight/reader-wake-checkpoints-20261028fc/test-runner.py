#!/usr/bin/env python3
"""Focused offline FC boundary tests. No real adapter import or target operations."""
import base64,copy,json,subprocess,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent;ER=B/'rtp-quiescent-checkpoints-20261028er';checks=0;commands=[]
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
r=load(P/'run-once.py');wake=load(P/'wake-check.py');parser=load(ER/'parse-result.py')
def check(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def refuse(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'refused');return
 raise ValueError('unexpected acceptance')
def ready():
 return {'schema':'fc-reader-wake-readiness-decision-v1','accepted':True,'identity':{'boot':r.BOOT,'sysfsRealpath':'/sys/devices/platform/usb/usb7/7-1','sysfsStat':'42:1234','busnum':'7','devnum':'45','deviceNode':'/dev/bus/usb/007/045','nodeStat':'bd:32c:12345','descriptorsSha256':r.sha(bytes.fromhex(r.DESCRIPTORS)),'configuration':'1','authorized':'1','runtimeStatus':'active','interfaceNumber':'02','alternate':'0','interfaceClass':'ff','interfaceSubClass':'00','interfaceProtocol':'00'},'interfaceUnbound':True,'noHolders':True,'closedWorldVendorOutLineage':{'accepted':True,'statement':'SYNTHETIC HOST TEST ONLY: no actual device or queue qualification exists.','evidenceSha256':'a'*64},'evidence':[],'endpointQueueProof':False}
def envelope(raw):
 vals=[raw,b'[GC_INF{opaque}\nO] native diagnostics',b''];s='DPMETA_BEGIN\n'+r.BOOT+'\n1.0 2.0\n0\n'
 for v in vals:s+=str(len(v))+'\n'+r.sha(v)+'\n'
 s+='DPMETA_END\n'
 for label,v in zip(['RECEIPT','STDOUT','STDERR'],vals):s+=label+'_B64_BEGIN\n'+base64.b64encode(v).decode()+'\n'+label+'_B64_END\n'
 return s+'DPRUN_COMPLETE\n'
def snapshot(kind='success'):
 tab='memory/eden/current_tab, value = d/apps.tab (String)\n'
 if kind=='wrong-tab':tab=tab.replace('d/apps.tab','d/ug.tab@ForYou')
 if kind=='duplicate-tab':tab+=tab
 if kind=='missing-tab':tab=''
 window='/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll\n'
 if kind=='no-csfs':window='unrelated-window\n'
 if kind=='saver':window+='ScreenSaver.dll\n'
 # The accepted predicate permits ordinary volume OSD; no focus inference.
 text=r.BOOT+'\n1.00 2.00\n'+tab+window+'volume-app ordinary OSD\n1.01 2.00\n'
 if kind=='truncated':text=text.rsplit('1.01',1)[0]
 if kind=='oversize':text+='x'*65536
 return text
def fixture40(limit=40):
 n=json.loads((ER/'fixture.json').read_bytes())
 for cap in n['retained']:
  for window in cap['windows']:
   if window['name']=='R'and window['complete']:
    raw=bytearray(base64.b64decode(window['rawBase64']));raw[196:198]=limit.to_bytes(2,'little');window['rawBase64']=base64.b64encode(raw).decode();window['sha256']=r.sha(raw)
 raw=bytearray(base64.b64decode(n['scoreCheckpoints']['rawBase64']))
 for offset in range(0,len(raw),58):raw[offset+2:offset+6]=limit.to_bytes(2,'little')*2
 n['scoreCheckpoints']['rawBase64']=base64.b64encode(raw).decode();n['scoreCheckpoints']['sha256']=r.sha(raw)
 return json.dumps(n).encode()
class Clock:
 def __init__(self,kind='success'):self.now=1000000000;self.calls=0;self.kind=kind;self.sleeps=[]
 def __call__(self):
  self.calls+=1;self.now+=1000000
  if self.kind=='age'and self.calls==6:self.now+=2000000000
  if self.kind=='budget'and self.calls==2:self.now+=11000000000
  if self.kind=='slow-wake'and self.calls==3:self.now+=11000000000
  return self.now
 def sleep(self,s):self.sleeps.append(s);self.now+=int(s*1000000000)
class FakeRoot:
 def __init__(self,kind='success'):self.kind=kind;self.commands=[];self.native=0;self.ui=0;self.snapshots=0;self.cleanup=0
 def root(self,command,record,path):
  self.commands.append(command);commands.append(command)
  check(0<len(command.encode())<=8192,'command cap');check(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'shell syntax')
  call={'command':command,'command_bytes':len(command.encode()),'host_timeout':False,'transport_exit':0,'transport_stderr':{'data':'','encoding':'base64'}};record['calls'].append(call);r.save(path,record)
  try:
   value=self.response(command)
  except Exception:
   call['host_timeout']=True;r.save(path,record);raise
  call['response']={'authenticated':True,'uid':0,'euid':0,'commands':[{'command':command,'stdout':value,'stderr':'','exit_code':0,'timed_out':False}]};r.save(path,record);return value
 def response(self,c):
  if 'input_keyevent XF86AudioRaiseVolume down'in c:
   self.ui+=1;check('input_keyevent XF86AudioRaiseVolume up'in c,'up attempted in same command')
   if self.kind=='wake-ambiguous':raise OSError('synthetic wake ambiguity')
   return 'LOCAL_KEY_DOWN_EXIT='+('1'if self.kind=='wake-fail'else'0')+'\nLOCAL_KEY_UP_EXIT='+('1'if self.kind=='wake-up-fail'else'0')+'\n'
  if 'enlightenment_info -topvwins'in c:
   self.snapshots+=1;kind=self.kind
   if kind=='settle':kind='saver'if self.snapshots==1 else'success'
   return snapshot(kind)
  for marker in ['PRE_READY','BEFORE_INVOKE_READY','POST_READY']:
   if c.endswith('echo '+marker+'\n'):
    if self.kind==marker:raise ValueError('synthetic identity failure')
    return 'FDCENSUS expected=100 missing=1 holders=0 errors=0\n'+marker+'\n'
  for marker in ['PRIVATE_STAGE_CREATED','STAGED_CHUNK','STAGED_FILE','FINAL_INTEGRITY_OK']:
   if c.endswith('echo '+marker+'\n'):return marker+'\n'
  if ' --receipt-self-test > 'in c:
   return envelope(b'{}'if self.kind=='selftest'else b'{"selfTestsPassed":93,"keyTestsPassed":22,"checkpointTestsPassed":79,"targetOperations":0}\n')
  if ' --execute --device 'in c:
   self.native+=1
   if self.kind=='native-ambiguous':raise OSError('synthetic native ambiguity')
   return 'IMMEDIATE_READY\n'+envelope(b'{}'if self.kind=='native-malformed'else fixture40(200 if self.kind=='wrong-limit'else 40))
  if c.endswith('echo STAGE_ABSENT\n'):
   self.cleanup+=1
   if self.kind=='cleanup':raise OSError('synthetic cleanup ambiguity')
   return 'STAGE_ABSENT\n'
  raise ValueError('unexpected fake command')
manifest,payload=r.build_manifest();rawmanifest=r.manifest_bytes(manifest);check(rawmanifest==(P/'deployment-manifest.json').read_bytes(),'frozen manifest exact')
check(manifest['wrapperUiOperations']==1 and manifest['plannedWrapperKeyChildren']==2 and manifest['nativeMaxCycles']==56 and manifest['nativeDurationUs']==2000000,'truthful plan')
r.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32))
with tempfile.TemporaryDirectory(prefix='fc-test-',dir=P)as tmp:
 base=Path(tmp);evidence=base/'phase.txt';evidence.write_text('SYNTHETIC only. No real queue or device readiness.')
 rd=ready();rd['evidence']=[{'path':str(evidence),'sha256':r.sha(evidence.read_bytes())}];rb=json.dumps(rd).encode();rp=base/'ready.json';rp.write_bytes(rb);check(r.load_readiness(rp,r.sha(rb))[0]==rd,'FC readiness')
 erready=copy.deepcopy(rd);erready['schema']='er-quiescent-checkpoint-readiness-decision-v1';rp.write_text(json.dumps(erready));refuse(lambda:r.load_readiness(rp,r.sha(rp.read_bytes())))
 def execute(kind='success'):
  f=FakeRoot(kind);clock=Clock(kind);out=base/kind
  value=r.execute(out,rd,rb,rawmanifest,payload,f,parser,clock,clock.sleep);return f,clock,out,value
 f,clock,out,res=execute();check(res['accepted']and f.ui==f.native==f.cleanup==1 and res['wrapperUiOperations']==1 and res['wrapperKeyChildAttempts']==2,'one visible workflow one native one cleanup')
 cp=json.loads((out/'wake-checkpoint.json').read_bytes());check(wake.validate(out,cp)['accepted']and cp['hostSubmissionAgeNs']<=1000000000,'qualified UI gap')
 # Insertion order and every non-UI generated command equal frozen ER.
 order=f.commands;wakeindex=next(i for i,c in enumerate(order)if 'input_keyevent XF86AudioRaiseVolume down'in c);check(order[wakeindex-1].endswith('echo BEFORE_INVOKE_READY\n')and ' --execute --device 'in order[wakeindex+2],'exact insertion/native immediately after accepted snapshot')
 er=load(ER/'run-once.py');er.uuid=r.uuid;ef=FakeRoot();er.execute(base/'er',erready,json.dumps(erready).encode(),er.manifest_bytes(er.build_manifest()[0]),payload,ef,parser)
 check([c for c in order if 'input_keyevent XF86AudioRaiseVolume down'not in c and 'enlightenment_info -topvwins'not in c]==ef.commands,'every inherited generated command byte-identical')
 admission=load(P/'verify-observation.py');proof=admission.verify(out,r.sha(rawmanifest));check(proof['accepted']and proof['wakeCheckpoint']['wrapperUiOperations']==1,'new completed admission')
 # Terminal labels must bind the recorded authenticated requests and nine-file builders.
 original_record=json.loads((out/'record.json').read_text())
 def tamper_record(change):
  altered=copy.deepcopy(original_record);change(altered);r.save(out/'record.json',altered)
  refuse(lambda:admission.verify(out,r.sha(rawmanifest)))
  r.save(out/'record.json',original_record)
 def stdout_change(index,value):return lambda z:z['calls'][index]['response']['commands'][0].update(stdout=value)
 def command_change(index):
  def change(z):
   z['calls'][index]['command']+=': # injected terminal command\n';z['calls'][index]['response']['commands'][0]['command']=z['calls'][index]['command']
  return change
 for index in [-1,-2,-3]:
  tamper_record(lambda z,index=index:z['calls'].pop(index))
 for left,right in [(-3,-2),(-2,-1)]:
  def swap(z,left=left,right=right):z['calls'][left],z['calls'][right]=z['calls'][right],z['calls'][left]
  tamper_record(swap)
 tamper_record(lambda z:z['calls'].append(copy.deepcopy(z['calls'][-1])))
 tamper_record(lambda z:z['calls'].insert(z['wakeCheckpoint']['lastUiCallIndex']+1,copy.deepcopy(z['calls'][-1])))
 for index,value in [(-1,'NOT_REMOVED\n'),(-2,'NOT_CHECKED\n'),(-3,'FDCENSUS expected=100 missing=1 holders=1 errors=0\nPOST_READY\n')]:tamper_record(stdout_change(index,value))
 for index in [-1,-2,-3]:tamper_record(command_change(index))
 tamper_record(lambda z:z.update(remote_stage='/tmp/researcher-er-'+'b'*32))
 tamper_record(lambda z:z.update(native_invocations=True))
 tamper_record(lambda z:z['calls'][-1].update(transport_exit=False))
 tamper_record(lambda z:z['calls'][-1]['response']['commands'][0].update(exit_code=False))
 tamper_record(lambda z:z['calls'][-1]['response'].update(uid=False))
 tamper_record(lambda z:z['postCensus'].update(observedHolders=False))
 tamper_record(lambda z:z['selftestTerminal'].update(exit_code=False))
 for field,value in [('hostSubmissionAgeNs',1000000001),('keyChildAttempts',1),('wrapperUiOperationsCompleted',0),('wrapperUiOperationsCompleted',True)]:
  bad=copy.deepcopy(cp);bad[field]=value;refuse(lambda:wake.validate(out,bad))
 after=json.loads((out/'result.json').read_text());after['wrapperUiOperations']=0;r.save(out/'result.json',after);refuse(lambda:admission.verify(out,r.sha(rawmanifest)));r.save(out/'result.json',res)
 f2,c2,_,_=execute('settle');check(f2.snapshots==2 and c2.sleeps==[.25],'bounded settle first success')
 for kind in ['PRE_READY','BEFORE_INVOKE_READY','selftest','wake-fail','wake-up-fail','wake-ambiguous','slow-wake','wrong-tab','duplicate-tab','missing-tab','truncated','oversize','saver','no-csfs','age','budget','native-ambiguous','native-malformed','wrong-limit','POST_READY','cleanup']:
  f=FakeRoot(kind);clock=Clock(kind);directory=base/kind
  refuse(lambda:r.execute(directory,rd,rb,rawmanifest,payload,f,parser,clock,clock.sleep))
  check(f.ui<=1 and f.native<=1,'no key/native retry')
  rec=json.loads((directory/'record.json').read_bytes());check(rec['cleanup_required']is True,'failure retains stage')
  before=kind not in ['native-ambiguous','native-malformed','wrong-limit','POST_READY','cleanup'];check(f.native==(0 if before else 1),'native submission accounting')
  check(rec['native_invocations']==f.native and rec['wrapperUiOperations']==f.ui,'actual/inflight UI/native counts')
  if before:check(f.cleanup==0,'no cleanup after pre-native refusal')
  if kind in ['saver','no-csfs']:check(f.snapshots==10 and clock.sleeps==[.25]*9,'finite settle exhaustion')
  if kind in ['PRE_READY','BEFORE_INVOKE_READY','selftest','budget']:check(f.ui==0,'no wake before admission')
  if kind=='wake-ambiguous':check(rec['wakeCheckpoint']['keyChildAttempts']is None,'ambiguous child attempts unknown')
# Fixed ordinary commands equal the pinned NAV generator, without importing its adapter.
nav=load(B/'ui-navigation-20261027br/navigate.py');check(r.sha(Path(nav.__file__).read_bytes())==r.NAV_SHA,'NAV pin')
with tempfile.TemporaryDirectory(prefix='nav-proof-',dir=P)as tmp:
 class Collect:
  commands=[]
  def root(self,c,rec,path):self.commands.append(c);return 'LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n'if'input_keyevent'in c else snapshot()
 c=Collect();nav.local_key_action('wake',Path(tmp),c,'wake');nav.command_snapshot(c,Path(tmp),'before');check(c.commands==[wake.wake_command(),wake.snapshot_command()],'exact NAV command provenance')
for kind in ['wrong-tab','duplicate-tab','missing-tab','truncated','oversize']:refuse(lambda:wake.parse_snapshot(snapshot(kind)))
check(wake.qualified(wake.parse_snapshot(snapshot())),'OSD presence does not change cached predicate')
for text in [snapshot().replace(r.BOOT,'wrong-boot'),snapshot().replace('1.01 2.00','0.50 2.00')]:refuse(lambda:wake.parse_snapshot(text))
for blob in [envelope(b'{}')+'x',envelope(b'x'*24577)]:refuse(lambda:r.receipt_envelope(blob))
check(json.loads(subprocess.run([sys.executable,'-B',str(P/'run-once.py')],check=True,capture_output=True).stdout)['plannedWrapperUiOperations']==1,'dry zeroIO and visible planned UI')
print(json.dumps({'accepted':True,'checksPassed':checks,'commandsSyntaxChecked':len(commands),'maximumCommandBytes':max(len(c.encode())for c in commands),'targetOperations':0,'rootCalls':0,'networkOperations':0}))
