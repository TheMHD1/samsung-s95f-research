#!/usr/bin/env python3
"""Independent finite GA review. No real transport module is imported or invoked."""
import ast,base64,copy,hashlib,json,subprocess,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;P=R.parent;B=P.parent
FN=B/'combined-event-successor-20261028fn';FW=B/'combined-live-trigger-trial-20261028fw';FO=B/'combined-event-successor-trial-20261028fo/capture-01'
checks=0;cases=0
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def check(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1
def refused(action,label='expected refusal'):
 try:action()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,label);return
 raise ValueError('unexpected acceptance: '+label)
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
pins={
 'deployment-manifest.json':'2890584fce6f59851171de5a47081fcbdf5e58952d44b090e4bfae29b7633709',
 'source-inventory.json':'f0098a4ccd58e1662a9f37e4a7f8d2f38fc1eea72eb4f6950c20c4b6e28f0f2c',
 'run-once.py':'692420eb3981cb2cb6b74787ab67837b73d23c321f858638b77df3b0542148dc',
 'cached-check.py':'e98d16fc1555bdec8de9356a2bd31cccd5fb25cc1e76ba0cf178050592aff1ce',
 'prepare-readiness.py':'0ef3d48b2ec1597a77bf83fbe34cb6b3332e1958f145d4fd46df2c26643cc270',
 'host-build-checkpoint.json':'83c103bba1e0d9a3326165c655842c6f8e8fb672f81ea39cb883e81e04b16a76',
 'qualification.json':'727c50d0971a2f8d6faacdf76883bef92b846b8f89b7a3062a75f95492ca75db'}
before={}
for name,digest in pins.items():
 raw=(P/name).read_bytes();check(sha(raw)==digest,'author freeze '+name);before[name]=sha(raw)
inventory=json.loads((P/'source-inventory.json').read_bytes())['files']
for row in inventory:
 raw=(P/row['path']).read_bytes();check(len(raw)==row['bytes']and sha(raw)==row['sha256'],'all author inventory');before[row['path']]=sha(raw)
inputs=json.loads((P/'input-pins.json').read_bytes())['files']
for row in inputs:
 raw=(B/row['path']).read_bytes();check(len(raw)==row['bytes']and sha(raw)==row['sha256'],'all external source pins')
current_path=FW/'after-recovery-identity/identity.json';current=json.loads(current_path.read_bytes())
current_ready_path=FW/'validation-readiness-corrected/readiness.json';current_ready=json.loads(current_ready_path.read_bytes())
check(current_ready['identity']==current and len(current)==16 and current['devnum']=='66'and current['deviceNode']=='/dev/bus/usb/007/066'and current['nodeStat']=='bd:341:15370520','all actual current USB66 identity fields')
r=load(P/'run-once.py');fn=load(FN/'run-once.py');cached=load(P/'cached-check.py');parser=load(FN/'parse-result.py')
manifest,payload=r.build_manifest();mr=r.manifest_bytes(manifest)
check(mr==(P/'deployment-manifest.json').read_bytes(),'exact frozen manifest reconstruction')
check(payload==fn.build_manifest()[1]and sum(map(len,payload.values()))==103078,'exact all FN payload bytes')
check(r.PARSER_SHA=='d222a8830f222bd0643b2e86bf4b47e2397258cd6cdae62e0b93141b2be7d78d'and sha((FN/'parse-result.py').read_bytes())==r.PARSER_SHA,'exact strict FN parser')
check(r.CHECKPOINT_SHA=='e3d14bc1705a2c91b94fcc4e8dbebe3b96bd8936216870287f55e63a009b05dd'and sha((FN/'host-build-checkpoint.json').read_bytes())==r.CHECKPOINT_SHA,'exact FN native checkpoint')
for name,row in manifest['nativeFiles'].items():
 raw=(FN/name).read_bytes();check(len(raw)==row['bytes']and sha(raw)==row['sha256'],'native/key/pair source or payload pin '+name)
root_source=(B/'managed-ui-tab-launch/root-with-margin.py').read_bytes()
check(sha(root_source)==r.ROOT_SHA=='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a','root source pin without import')
constants={}
for n in ast.parse(root_source).body:
 if isinstance(n,ast.Assign)and isinstance(n.value,ast.Constant):
  for t in n.targets:
   if isinstance(t,ast.Name):constants[t.id]=n.value.value
check([constants[k]for k in ['REMOTE_TIMEOUT_SECONDS','HOST_TIMEOUT_SECONDS','MAX_COMMAND','MAX_RESPONSE']]==[45,75,8192,65536],'serialized root caps source')
fc=B/'reader-wake-checkpoints-20261028fc/test-runner.py';m=types.ModuleType('independent_fixed_fc_mock');m.__file__=str(fc)
exec(compile(fc.read_text().split('manifest,payload=r.build_manifest();')[0],str(fc),'exec'),m.__dict__)
r.uuid=fn.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='c'*32))
positive=json.loads((FO/'native.receipt.json').read_bytes());positive['device']=66
positive_bytes=(json.dumps(positive,separators=(',',':'))+'\n').encode()
check(parser.parse_native(positive_bytes.decode())[0]['accepted'],'synthetic USB66 receipt changes device field only from positive FO')
fault=(FW/'capture-01/native.receipt.json').read_bytes();fault_value=parser.parse_native(fault.decode())[0]
check(not fault_value['accepted']and not fault_value['armAttempted']and fault_value['writes']==0 and not fault_value.get('intervention',{}).get('attempted',False),'actual FW original prearm fault has no arm or Left')
def snapshot(kind='good',control=False):
 tab='d/apps.tab'if control else'd/ug.tab@Live'
 value=r.BOOT+'\n1.00 2.00\nmemory/eden/current_tab, value = '+tab+' (String)\n/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll\n'+(''if control else'ScreenSaverContent.dll\n')+'1.01 2.00\n'
 if kind=='apps':value=value.replace('d/ug.tab@Live','d/apps.tab')
 if kind=='for-you':value=value.replace('d/ug.tab@Live','d/ug.tab@ForYou')
 if kind=='duplicate':value=value.replace('memory/eden/current_tab, value = d/ug.tab@Live (String)\n','memory/eden/current_tab, value = d/ug.tab@Live (String)\n'*2)
 if kind=='missing-tab':value='\n'.join(x for x in value.split('\n')if not x.startswith('memory/eden/current_tab'))
 if kind=='noncanonical':value=value.replace(' (String)','  (String)')
 if kind=='no-saver':value=value.replace('ScreenSaverContent.dll\n','')
 if kind=='no-csfs':value=value.replace('/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll','unrelated')
 if kind=='bad-boot':value=value.replace(r.BOOT,'bad-boot')
 if kind=='backwards-uptime':value=value.replace('1.01 2.00','0.99 2.00')
 if kind=='truncated':value=value[:-1]
 if kind=='oversize':value+='x'*65536
 return value
class Clock:
 def __init__(self,kind='good'):self.now=1000000000;self.calls=0;self.kind=kind;self.sleeps=[]
 def __call__(self):
  self.calls+=1;self.now+=1000000
  if self.calls==4:
   if self.kind=='stale':self.now+=cached.AGE_NS
   if self.kind=='future':self.now-=2000000
   if self.kind=='zero-age':self.now-=1000000
   if self.kind=='max-age':self.now+=cached.AGE_NS-1000000
  if self.kind=='after-clock-failure'and self.calls==3:raise OSError('synthetic clock failure')
  return self.now
 def sleep(self,value):self.sleeps.append(value);self.now+=int(value*1000000000)
class Mock(m.FakeRoot):
 def __init__(self,kind='good',control=False):super().__init__(kind);self.control=control;self.fetch=0
 def response(self,command):
  if' --receipt-self-test > 'in command:return m.envelope(b'{"smokeTestsPassed":8,"targetOperations":0}\n')
  if'enlightenment_info -topvwins'in command:
   self.snapshots+=1;kind=self.kind
   if kind=='settle-ten':kind='good'if self.snapshots==10 else'no-saver'
   if kind in ['stale','future','zero-age','max-age','after-clock-failure','fault','ambiguous','bad-envelope','wrong-receipt-device']:kind='good'
   return snapshot(kind,self.control)
  if' --execute --device 'in command:
   self.native+=1
   if self.kind=='ambiguous':raise OSError('synthetic native ambiguity')
   if self.kind=='bad-envelope':return'IMMEDIATE_READY\npartial'
   raw=fault if self.kind=='fault'else positive_bytes
   if self.kind=='wrong-receipt-device':raw=(FO/'native.receipt.json').read_bytes()
   value=m.envelope(raw)
   if self.kind=='fault':value=value.replace('\n1.0 2.0\n0\n','\n1.0 2.0\n1\n')
   return'IMMEDIATE_READY\n'+value
  if'echo FN_SIDECAR_BEGIN'in command:
   self.fetch+=1;name='baseline-ring.bin'if'baseline-ring.bin'in command else'post-ring.bin'
   return'FN_SIDECAR_BEGIN\n'+base64.b64encode((FO/name).read_bytes()).decode()+'\nFN_SIDECAR_END\n'
  return super().response(command)
with tempfile.TemporaryDirectory(prefix='independent-',dir=R/'tmp')as td:
 base=Path(td);ready=copy.deepcopy(current_ready);ready['schema']='ga-live-saver-event-readiness-decision-v1';rb=json.dumps(ready).encode();rp=base/'readiness.json';rp.write_bytes(rb)
 check(r.load_readiness(rp,sha(rb))[0]['identity']==current,'full current USB66 GA readiness')
 invalid={'boot':'wrong','sysfsRealpath':'/sys/../7-1','sysfsStat':'bad','busnum':'8','devnum':'65','deviceNode':'/dev/bus/usb/007/065','nodeStat':'bd:340:15370520','descriptorsSha256':'0'*64,'configuration':'0','authorized':'0','runtimeStatus':'suspended','interfaceNumber':'01','alternate':'1','interfaceClass':'02','interfaceSubClass':'01','interfaceProtocol':'01'}
 for key,value in invalid.items():
  bad=copy.deepcopy(ready);bad['identity'][key]=value;raw=json.dumps(bad).encode();rp.write_bytes(raw);refused(lambda:r.load_readiness(rp,sha(raw)),'identity field '+key)
 for update in [dict(schema='fn-combined-event-readiness-decision-v1'),dict(noHolders=False),dict(endpointQueueProof=True),dict(interfaceUnbound=False),dict(accepted=1)]:
  bad=copy.deepcopy(ready);bad.update(update);raw=json.dumps(bad).encode();rp.write_bytes(raw);refused(lambda:r.load_readiness(rp,sha(raw)),'readiness scope mutation')
 rp.write_bytes(rb)
 success=None
 for kind in ['good','zero-age','max-age','settle-ten','apps','for-you','duplicate','missing-tab','noncanonical','no-saver','no-csfs','bad-boot','backwards-uptime','truncated','oversize','stale','future','after-clock-failure','fault','ambiguous','bad-envelope','wrong-receipt-device']:
  cases+=1;out=base/kind;mock=Mock(kind);clock=Clock(kind)
  if kind in ['good','zero-age','max-age','settle-ten']:
   result=r.execute(out,ready,rb,mr,payload,mock,parser,clock,clock.sleep)
   check(result['accepted']and result['wrapperUiOperations']==0 and mock.native==mock.cleanup==1 and mock.ui==0 and mock.fetch==2,'accepted one native, no wrapper keys, exact cleanup')
   cp=json.loads((out/'cached-checkpoint.json').read_bytes());check(cached.validate(out,cp)['accepted'],'independent checkpoint raw binding')
   index=next(i for i,c in enumerate(mock.commands)if' --execute --device 'in c)
   check(index==cp['lastCachedCallIndex']+1 and mock.commands[index-1]==cached.snapshot_command(),'native is next root request after final qualifying snapshot')
   check('--execute --device 66'in mock.commands[index]and'/dev/bus/usb/007/066'in mock.commands[index]and'bd:341:15370520'in mock.commands[index]and'19:42745'in mock.commands[index],'complete USB66 immediate instance guard')
   check(not any('input_keyevent'in c or'prepare-live'in c or'XF86'in c for c in mock.commands),'no GA wrapper control commands')
   rm=next(line for line in mock.commands[-1].splitlines()if line.startswith('rm -- '));check(len(rm.split()[2:])==11,'exact eleven-file accepted cleanup')
   if kind=='good':success=mock.commands
   if kind=='zero-age':check(cp['hostSubmissionAgeNs']==0,'inclusive zero age')
   if kind=='max-age':check(cp['hostSubmissionAgeNs']==1000000000,'inclusive one-second age')
   if kind=='settle-ten':check(mock.snapshots==10 and clock.sleeps==[.25]*9,'last allowed snapshot accepts with nine sleeps')
  else:
   refused(lambda:r.execute(out,ready,rb,mr,payload,mock,parser,clock,clock.sleep),'full wrapper '+kind)
   check(mock.cleanup==mock.fetch==mock.ui==0,'refusal sends no cleanup, fetch or key')
   check(mock.native==(1 if kind in ['fault','ambiguous','bad-envelope','wrong-receipt-device']else 0),'native admission cutoff '+kind)
   if kind in ['no-saver','no-csfs']:check(mock.snapshots==10 and clock.sleeps==[.25]*9,'missing window exhaustion')
   if kind in ['apps','for-you','duplicate','missing-tab','noncanonical','bad-boot','backwards-uptime','truncated','oversize']:check(mock.snapshots==1,'first malformed/wrong-tab snapshot refuses')
   if kind=='after-clock-failure':check((out/'ui-snapshot-01-response.txt').read_text()==snapshot(),'returned response preserved before failed host stamp')
   if kind=='fault':
    primary=json.loads((out/'primary-native-outcome.json').read_bytes());result=json.loads((out/'result.json').read_bytes());record=json.loads((out/'record.json').read_bytes())
    check(primary['error']==fault_value['error']and primary['terminal']==fault_value['terminal']and result['accepted']is False,'original actual FW prearm refusal retained')
    check(primary['terminalKnownPhase']and primary['released']and primary['closed']and not primary['loggerMayRemain']and record['loggerPayloads']==0,'known phase/lifecycle not accepted observation')
    check(' --execute --device 'in mock.commands[-1]and record['native_invocations']==1,'fault is last root request, no retry')
 # Compare every complete USB66 command with frozen FN, removing its sole VOLUP command.
 control=Mock(control=True);clock=m.Clock();fnready=copy.deepcopy(ready);fnready['schema']='fn-combined-event-readiness-decision-v1'
 fn.execute(base/'fn-control',fnready,json.dumps(fnready).encode(),fn.manifest_bytes(fn.build_manifest()[0]),payload,control,parser,clock,clock.sleep)
 check(control.ui==1 and success==[c for c in control.commands if'input_keyevent XF86AudioRaiseVolume down'not in c],'all full USB66 root request bytes equal FN except removed wrapper wake')
 # Independent exact cooperative budget boundaries with explicit pure clocks.
 for values,accepted in [([0,0,10000000000],True),([0,0,10000000001],False),([0,10000000001],False)]:
  cases+=1;out=base/('budget-'+str(cases));out.mkdir();cp={};it=iter(values);calls=[]
  def call(command):calls.append(command);return snapshot()
  if accepted:
   cached.perform(out,call,cp,lambda:next(it),lambda v:None);cached.dispatch(cp,lambda:10000000000);check(cached.validate(out,cp)['accepted'],'inclusive ten-second cooperative budget')
  else:refused(lambda:cached.perform(out,call,cp,lambda:next(it),lambda v:None),'ten-second budget exhaustion')
  check(len(calls)==(0 if len(values)==2 else 1),'budget checked before/after exact request')
 for value in [True,-1,1.5]:
  cases+=1;refused(lambda:cached.perform(base,lambda c:snapshot(),{},lambda:value),'malformed monotonic clock')
 # Reuse fresh USB66 local readiness builder with a substitute cached-only transport.
 pr=load(P/'prepare-readiness.py');original_load=pr.load;ready_requests=[];imports=[]
 class CachedRoot:
  def root(self,command,record,path):
   ready_requests.append(command);check('/dev/bus/usb/007/066'in command and'bd:341:15370520'in command,'readiness exact USB66 instance')
   check('input_keyevent'not in command and' --execute 'not in command and len(command.encode())<=8192,'readiness only bounded cached request')
   check(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'readiness shell syntax')
   return'FDCENSUS expected=100 missing=0 holders=0 errors=0\nGA_CURRENT_READY\n'
 def substituted_load(path,digest,name):
  if path==pr.ROOT:imports.append(path);return CachedRoot()
  return original_load(path,digest,name)
 pr.load=substituted_load;oldargv=sys.argv;original_temporary_directory=tempfile.TemporaryDirectory
 def review_temporary_directory(*args,**kwargs):
  kwargs['dir']=R/'tmp';return original_temporary_directory(*args,**kwargs)
 tempfile.TemporaryDirectory=review_temporary_directory
 identity=base/'identity.json';identity.write_text(json.dumps(current));phase=base/'phase.txt';phase.write_text('SYNTHETIC INDEPENDENT HOST REVIEW ONLY. No actual current readiness or queue qualification.')
 try:
  for kind in ['dry','invalid-node','invalid-manifest','execute']:
   cases+=1;bad=copy.deepcopy(current)
   if kind=='invalid-node':bad['nodeStat']='bd:340:15370520'
   identity.write_text(json.dumps(bad));out=base/('readiness-'+kind)
   sys.argv=['prepare-readiness.py','--wrapper','ga','--wrapper-sha256',pins['run-once.py'],'--manifest-sha256',pins['deployment-manifest.json']if kind!='invalid-manifest'else'0'*64,'--identity',str(identity),'--phase-note',str(phase),'--output',str(out)]
   if kind=='execute':sys.argv.append('--execute')
   import contextlib,io
   with contextlib.redirect_stdout(io.StringIO()):
    if kind.startswith('invalid'):refused(pr.main,'readiness local '+kind)
    else:pr.main()
   check(len(imports)==len(ready_requests)==(1 if kind=='execute'else 0),'no real root import; only explicit cached mock after valid local admission')
   if kind=='execute':check(r.load_readiness(out/'readiness.json',sha((out/'readiness.json').read_bytes()))[0]['identity']==current,'produced current USB66 readiness exact')
   else:check(not out.exists(),'dry/local refusal creates no output stage')
 finally:sys.argv=oldargv;pr.load=original_load;tempfile.TemporaryDirectory=original_temporary_directory
for name,digest in before.items():check(sha((P/name).read_bytes())==digest,'author freeze remains unchanged')
for row in inputs:check(sha((B/row['path']).read_bytes())==row['sha256'],'external source cutoff remains unchanged')
result={'schema':'ga-independent-review-validation-v1','status':'PASS_HOST_ONLY','checks':checks,'independentCases':cases,'mockShellCommands':len(m.commands),'maxCommandBytes':max(len(c.encode())for c in m.commands),'authorInventoryFiles':len(inventory),'authorInputPins':len(inputs),'fullCurrentIdentityFields':len(current),'realTargetOperations':0,'realRootImports':0,'networkOperations':0,'authorFilesChanged':False,'manifestSha256':pins['deployment-manifest.json'],'inventorySha256':pins['source-inventory.json'],'additionalInputs':{str(p.relative_to(B)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}for p in [current_path,current_ready_path]},'positiveUSB66ReceiptIsSyntheticDeviceOnlyDerivative':True,'liveSaverCleanPremiseEstablished':False}
print(json.dumps(result,sort_keys=True))
