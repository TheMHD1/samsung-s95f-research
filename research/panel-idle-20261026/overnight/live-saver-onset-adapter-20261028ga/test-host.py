#!/usr/bin/env python3
"""Finite mocked GA qualification; no real root import, target or network I/O."""
import base64,copy,contextlib,io,json,shlex,subprocess,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent;checks=0;cases=0

def load(path):
 module=types.ModuleType(path.stem);module.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__);return module

def check(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1

def rejects(action):
 try:action()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'expected refusal');return
 raise ValueError('unexpected acceptance')

r=load(P/'run-once.py');cached=load(P/'cached-check.py');fn=load(r.FN/'run-once.py');parser=load(r.FN/'parse-result.py')
fc=B/'reader-wake-checkpoints-20261028fc/test-runner.py';m=types.ModuleType('fixed_fc_mock_definitions');m.__file__=str(fc)
exec(compile(fc.read_text().split('manifest,payload=r.build_manifest();')[0],str(fc),'exec'),m.__dict__)
FO=B/'combined-event-successor-trial-20261028fo/capture-01';FW=B/'combined-live-trigger-trial-20261028fw/capture-01'
positive=(FO/'native.receipt.json').read_bytes();fault=(FW/'native.receipt.json').read_bytes();native=json.loads(positive);fault_native=json.loads(fault)
check(parser.parse_native(positive.decode())[0]['accepted'],'strict retained positive fixture')
check(parser.parse_native(fault.decode())[0]['accepted']is False and fault_native['armAttempted']is False and fault_native['writes']==0 and not fault_native.get('intervention',{}).get('attempted',False),'strict actual known pre-arm fault/no arm/no key')
manifest,payload=r.build_manifest();raw_manifest=r.manifest_bytes(manifest)
check(raw_manifest==(P/'deployment-manifest.json').read_bytes(),'sealed manifest exact')
check(payload==fn.build_manifest()[1],'exact inherited payload bytes')
r.uuid=fn.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32))

class Clock(m.Clock):
 def __call__(self):
  value=super().__call__()
  if self.kind=='stale'and self.calls==4:self.now+=cached.AGE_NS+1;return self.now
  if self.kind=='future'and self.calls==4:self.now-=10000000;return self.now
  if self.kind=='clock-after'and self.calls==3:raise OSError('synthetic host clock failure')
  if self.kind=='clock-before'and self.calls==2:raise OSError('synthetic host clock failure')
  if self.kind=='budget-after'and self.calls==3:self.now+=cached.BUDGET_NS+1;return self.now
  return value

def snapshot(kind='success'):
 text=m.snapshot().replace('d/apps.tab','d/ug.tab@Live')
 if kind not in ['no-saver']:text=text.replace('volume-app ordinary OSD','ScreenSaver.dll\nvolume-app ordinary OSD')
 if kind=='apps':text=text.replace('d/ug.tab@Live','d/apps.tab')
 if kind=='for-you':text=text.replace('d/ug.tab@Live','d/ug.tab@ForYou')
 if kind=='duplicate-tab':text=text.replace('memory/eden/current_tab, value = d/ug.tab@Live (String)\n','memory/eden/current_tab, value = d/ug.tab@Live (String)\n'*2)
 if kind=='missing-tab':text='\n'.join(line for line in text.split('\n')if not line.startswith('memory/eden/current_tab'))
 if kind=='bad-canonical':text=text.replace(' (String)','  (String)')
 if kind=='no-csfs':text=text.replace('/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll','unrelated-window')
 if kind=='wrong-boot':text=text.replace(r.BOOT,'wrong-boot')
 if kind=='backwards-uptime':text=text.replace('1.01 2.00','0.50 2.00')
 if kind=='truncated':text=text.rsplit('1.01',1)[0]
 if kind=='oversize':text+='x'*65536
 return text

class Mock(m.FakeRoot):
 def __init__(self,kind='success',control=False):super().__init__(kind);self.control=control;self.fetch=0
 def response(self,command):
  if ' --receipt-self-test > 'in command:return m.envelope(b'{}'if self.kind=='selftest'else b'{"smokeTestsPassed":8,"targetOperations":0}\n')
  if 'enlightenment_info -topvwins'in command:
   self.snapshots+=1
   if self.control:return m.snapshot()
   kind='no-saver'if self.kind=='settle'and self.snapshots==1 else'success'if self.kind in ['settle','stale','future','clock-after','clock-before','budget-after','native-ambiguous','known-fault','selftest','PRE_READY']else self.kind
   return snapshot(kind)
  if ' --execute --device 'in command:
   self.native+=1
   if self.kind=='native-ambiguous':raise OSError('synthetic native ambiguity')
   text=m.envelope(fault if self.kind=='known-fault'else positive)
   if self.kind=='known-fault':text=text.replace('\n1.0 2.0\n0\n','\n1.0 2.0\n1\n')
   return 'IMMEDIATE_READY\n'+text
  if 'echo FN_SIDECAR_BEGIN'in command:
   self.fetch+=1;name='baseline-ring.bin'if 'baseline-ring.bin'in command else'post-ring.bin'
   return 'FN_SIDECAR_BEGIN\n'+base64.b64encode((FO/name).read_bytes()).decode()+'\nFN_SIDECAR_END\n'
  return super().response(command)

scratch=P/'host-environment/tmp';scratch.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ga-',dir=scratch)as td:
 base=Path(td);ready=json.loads((FO/'readiness-decision.json').read_bytes());ready['schema']='ga-live-saver-event-readiness-decision-v1';rb=json.dumps(ready).encode();rp=base/'ready.json';rp.write_bytes(rb)
 check(r.load_readiness(rp,r.sha(rb))[0]['identity']==json.loads((FO/'readiness-decision.json').read_bytes())['identity'],'all17 actual retained identity fields')
 for kind in ['success','settle','apps','for-you','duplicate-tab','no-saver','no-csfs','stale','future','clock-after','clock-before','budget-after','selftest','PRE_READY','native-ambiguous','known-fault']:
  cases+=1;mock=Mock(kind);clock=Clock(kind);out=base/('wrapper-'+kind);rd=ready;rr=rb
  if kind=='known-fault':
   rd=json.loads((FW/'readiness-decision.json').read_bytes());rd['schema']=ready['schema'];rr=json.dumps(rd).encode()
  if kind in ['success','settle']:
   result=r.execute(out,rd,rr,raw_manifest,payload,mock,parser,clock,clock.sleep)
   check(result['accepted']and result['wrapperUiOperations']==0 and result['intendedNativeAction']=='saver-wake-from-cached-Live','truthful accepted result')
   check(mock.ui==0 and mock.native==mock.cleanup==1 and mock.fetch==2,'no wrapper key/one native/two rings/one cleanup')
   check(mock.snapshots==(2 if kind=='settle'else 1),'first accepted query stops settle')
   cp=json.loads((out/'cached-checkpoint.json').read_bytes());check(cached.validate(out,cp)['accepted']and cp['hostSubmissionAgeNs']<=1000000000,'completed checkpoint binding')
   names=shlex.split(next(line for line in mock.commands[-1].splitlines()if line.startswith('rm -- ')))[2:]
   check(len(names)==len(set(names))==11,'exact11-file accepted cleanup')
   if kind=='success':
    control=Mock(control=True);c=m.Clock();rd2=copy.deepcopy(ready);rd2['schema']='fn-combined-event-readiness-decision-v1'
    fn.execute(base/'fn-control',rd2,json.dumps(rd2).encode(),fn.manifest_bytes(fn.build_manifest()[0]),payload,control,parser,c,c.sleep)
    check(mock.commands==[command for command in control.commands if 'input_keyevent XF86AudioRaiseVolume down'not in command],'all inherited commands identical with only wrapper wake removed')
  else:
   rejects(lambda:r.execute(out,rd,rr,raw_manifest,payload,mock,parser,clock,clock.sleep))
   record=json.loads((out/'record.json').read_bytes());check(record['wrapperUiOperations']==0 and mock.ui==0,'zero wrapper UI on refusal')
   check(record['cleanup_required']is True and mock.cleanup==0 and mock.fetch==0,'no automatic cleanup/fetch after refusal')
   check(mock.native==(1 if kind in ['native-ambiguous','known-fault']else 0),'native invocation cutoff')
   if kind=='known-fault':
    primary=json.loads((out/'primary-native-outcome.json').read_bytes());result=json.loads((out/'result.json').read_bytes())
    check(primary['error']==fault_native['error']and primary['terminal']==fault_native['terminal']and result['accepted']is False,'original known-fault refusal preserved')
    check(primary['terminalKnownPhase']is True and primary['released']and primary['closed']and primary['loggerMayRemain']is False,'lifecycle not observation acceptance')
    check(' --execute --device 'in mock.commands[-1]and result['wrapperUiOperations']==0,'no request after native refusal')
   if kind in ['no-saver','no-csfs']:check(mock.snapshots==10 and clock.sleeps==[.25]*9,'finite ten-query exhaustion')
   if kind=='clock-after':check((out/'ui-snapshot-01-response.txt').is_file(),'raw response retained before clock failure')
  check(not any('input_keyevent'in command for command in mock.commands),'no wrapper key bytes in any command')
 # Pure checkpoint malformed/settle/clock tests do not reach any adapter.
 for kind in ['success','settle','apps','for-you','duplicate-tab','missing-tab','bad-canonical','no-saver','no-csfs','wrong-boot','backwards-uptime','truncated','oversize','budget','budget-after','clock-before','clock-after']:
  cases+=1;out=base/('cached-'+kind);out.mkdir();cp={};calls=[];clock=Clock(kind)
  def call(command):
   calls.append(command);k='no-saver'if kind=='settle'and len(calls)==1 else'success'if kind in ['settle','budget','budget-after','clock-before','clock-after']else kind
   return snapshot(k)
  if kind in ['success','settle']:
   cached.perform(out,call,cp,clock,clock.sleep);cached.dispatch(cp,clock)
   check(cached.validate(out,cp)['accepted'],'strict completed cached checkpoint')
   check(len(calls)==(2 if kind=='settle'else 1),'no extra successful query')
   for age in [-1,cached.AGE_NS+1]:rejects(lambda:cached.dispatch(copy.deepcopy(cp),lambda:cp['acceptedQueryReturnedHostMonotonicNs']+age))
   for age in [0,cached.AGE_NS]:
    copied=copy.deepcopy(cp);cached.dispatch(copied,lambda:cp['acceptedQueryReturnedHostMonotonicNs']+age);check(cached.validate(out,copied)['accepted'],'inclusive exact1s timing bound')
   for field,value in [('wrapperUiOperationsAttempted',True),('wrapperUiOperationsCompleted',1),('wrapperKeyChildrenAttempted',1),('acceptedSnapshotIndex',True),('acceptedQueryReturnedHostMonotonicNs',True),('hostSubmissionAgeNs',True),('uiConsumptionProven',True),('intendedNativeAction','Live-header-to-ForYou')]:
    copied=copy.deepcopy(cp);copied[field]=value;rejects(lambda:cached.validate(out,copied))
   path=out/'ui-snapshot-01-command.txt';raw=path.read_bytes();path.write_bytes(raw+b':\n');rejects(lambda:cached.validate(out,cp));path.write_bytes(raw)
   copied=copy.deepcopy(cp);copied['snapshots'][0]['responseSha256']='0'*64;rejects(lambda:cached.validate(out,copied))
  else:
   rejects(lambda:cached.perform(out,call,cp,clock,clock.sleep));check(cp['status']=='refused_or_ambiguous'and len(calls)<=10,'truthful bounded cached refusal')
   if kind in ['apps','for-you','duplicate-tab','missing-tab','bad-canonical','wrong-boot','backwards-uptime','truncated','oversize']:check(len(calls)==1,'malformed/wrong context stops immediately')
  check(all(command==cached.snapshot_command()and 'input_keyevent'not in command for command in calls),'only exact read-only getter command')
 for invalid in [True,1.5,-1]:rejects(lambda:cached.perform(base,lambda c:snapshot(),{},lambda:invalid))
 # A stale/malformed readiness must fail locally, with no real root import.
 for change in [lambda v:v.update(schema='fn-combined-event-readiness-decision-v1'),lambda v:v['identity'].update(boot='wrong'),lambda v:v['identity'].update(authorized='0'),lambda v:v['identity'].update(deviceNode='/dev/bus/usb/007/999'),lambda v:v.update(noHolders=False)]:
  cases+=1;bad=copy.deepcopy(ready);change(bad);rp.write_text(json.dumps(bad));rejects(lambda:r.load_readiness(rp,r.sha(rp.read_bytes())))
 rp.write_bytes(rb);rejects(lambda:r.load_readiness(rp,'0'*64))
 dry=json.loads(subprocess.run([sys.executable,'-B',str(P/'run-once.py')],capture_output=True,check=True).stdout)
 check(dry['plannedWrapperUiOperations']==dry['plannedWrapperKeyChildren']==dry['targetOperations']==0 and dry['plannedNativeInvocations']==1,'wrapper dry is zero-I/O with honest plan')
 # Readiness builder: dry/local refusal before root import; one cached request only.
 pr=load(P/'prepare-readiness.py');real_load=pr.load;root_loads=[];ready_commands=[]
 class CachedRoot:
  def root(self,command,record,path):
   ready_commands.append(command);check('input_keyevent'not in command and '--execute --device'not in command,'readiness has no UI/native')
   check(len(command.encode())<=8192 and subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'cached readiness command bound/syntax')
   return 'FDCENSUS expected=100 missing=1 holders=0 errors=0\nGA_CURRENT_READY\n'
 def local_load(path,digest,name):
  if path==pr.ROOT:root_loads.append(path);return CachedRoot()
  return real_load(path,digest,name)
 pr.load=local_load;original_argv=sys.argv;identity=base/'identity.json';identity.write_text(json.dumps(ready['identity']));phase=base/'phase.txt';phase.write_text('SYNTHETIC HOST ONLY known-phase/closed-world premise. No actual device or queue qualification.')
 try:
  for kind in ['dry','wrong-manifest','invalid-identity','execute']:
   cases+=1;out=base/('ready-'+kind);value=copy.deepcopy(ready['identity'])
   if kind=='invalid-identity':value['authorized']='0'
   identity.write_text(json.dumps(value));sys.argv=['prepare-readiness.py','--wrapper','ga','--wrapper-sha256',r.sha((P/'run-once.py').read_bytes()),'--manifest-sha256',('0'*64 if kind=='wrong-manifest'else r.sha(raw_manifest)),'--identity',str(identity),'--phase-note',str(phase),'--output',str(out)]
   if kind=='execute':sys.argv.append('--execute')
   with contextlib.redirect_stdout(io.StringIO()):
    if kind in ['wrong-manifest','invalid-identity']:rejects(pr.main)
    else:pr.main()
   check(len(root_loads)==len(ready_commands)==(1 if kind=='execute'else 0),'no root import before local admission/one explicit cached query')
   if kind=='execute':
    value=json.loads((out/'readiness.json').read_bytes());check(r.load_readiness(out/'readiness.json',r.sha((out/'readiness.json').read_bytes()))[0]==value,'fresh GA readiness exact admission')
   else:check(not out.exists(),'dry/refused no output stage')
 finally:pr.load=real_load;sys.argv=original_argv
 check(len(m.commands)>0 and max(len(command.encode())for command in m.commands)<=8192,'all generated command caps')
print(json.dumps({'schema':'ga-host-validation-v1','checks':checks,'cases':cases,'shellCommands':len(m.commands),'maxCommandBytes':max(len(command.encode())for command in m.commands),'nativeAndParserRebuilt':False,'wrapperUiOperations':0,'positiveIdentityFieldsReused':17,'nativeKnownFaultNoArmOrLeftPreserved':True,'noRequestsAfterNativeRefusal':True,'targetOperations':0,'networkOperations':0},sort_keys=True))
