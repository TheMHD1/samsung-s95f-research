#!/usr/bin/env python3
"""EO exact admission delta + instrumented coordinator no-I/O branch mocks."""
from pathlib import Path
import base64,copy,hashlib,importlib.util,json,os,struct,subprocess,sys,tempfile,types
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;EM=H.parent;B=EM.parent;EI=B/'refresh-checkpoint-trial-20261028ei';EO=B/'dense-onset-trial-20261028eo';EB=B/'rtp-lane-gate-capture-20261028eb'
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0

def need(ok,label):
 global checks
 checks+=1
 if not ok:raise ValueError(label)
def load(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
old=(EI/'verify-observation.py').read_text();guard=(EO/'verify-observation.py').read_bytes();runner=(EO/'run-instrumented.py').read_bytes()
need(sha(guard)=='893a0a024a215d99d916e7f6d31edca7df6209767acf544c80c1632f08b76db9','EO guard frozenpin')
need(sha(runner)=='4e852620c30e0bcb25feb107e0401e3f9184c72f5366e43c280eb14f87dfe8c6','EO coordinator frozenpin')
need(sha(old.encode()).startswith('9b7420'),'retained EI guard priorpin')
expected=old.replace('completed EH40','completed EM40').replace('rtp-refresh-checkpoints-20261028eh','rtp-refresh-dense-checkpoints-20261028em').replace('1de2a8f769f4a801b85f2dff74bb840221e0394db8ec7acb9cffdd7a763d5229','cfa98869b725ce86d9bab876e7a59c554f690b75f77e17e22de035b214cdc49c').replace('d0059b32e4e3d99a398a3763934e8927cd2967126c6d1ad9e76d8bf069f3059e','83382d9a55271194480cb17d777a0d45737128f3dd849228b9517c3d2284c522').replace('frozen EH parser','frozen EM parser').replace('ei_eh_admission','eo_em_admission').replace('one-shot EH result','one-shot EM result').replace('ei-completed-eh40-admission-v1','eo-completed-em40-admission-v1')
need(expected.encode()==guard,'admission identity/schema/pin/display-only exactdelta;allbranchesunchanged')
pins=json.loads((EO/'orchestration-input-pins.json').read_text())
for rel,pin in pins.items():need(sha((B/rel).read_bytes())==pin,'coordinator helper pin')
# Existing admission negatives run with ONLY its scratch path redirected into owned reviews.
test=EO/'test-verify-observation.py';test_raw=test.read_bytes();text=test_raw.decode();needle="root=D/'reviews/host-environment/tmp'";need(text.count(needle)==1,'single test scratch path')
bootstrap="import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text().replace(\"root=D/'reviews/host-environment/tmp'\",\"root=Path(sys.argv[2])\"); exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})"
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(H/'tmp'))
suites=[]
for optimized in (False,True):
 r=subprocess.run([sys.executable]+(['-O']if optimized else[])+['-B','-c',bootstrap,str(test),str(H/'tmp')],cwd=H,env=env,capture_output=True,timeout=20)
 need(r.returncode==0 and not r.stderr,'EO admission mocked suite');v=json.loads(r.stdout);need(v['checksPassed']==124 and v['unexpectedAcceptances']==[]and v['targetOperations']==v['rootCalls']==v['networkOperations']==0,'124 admission checks')
 suites.append({'optimized':optimized,'summary':v,'stdoutSha256':sha(r.stdout)})
# Coordinator filesystem/output is redirected; subprocess.run is replaced completely.
# Only strict EB parser is used; the fixture is generated FakeOps data, never actual raw OEM data.
fixture=json.loads((EB/'fixture.json').read_text())
def eb_native(faulted):
 n=copy.deepcopy(fixture)
 for w in n['windows']:
  if w['name']in ('start-R','end-R'):
   b=bytearray(base64.b64decode(w['base64']))
   for offset,value in zip((0,10,14),(1,0x1001,0)if faulted else(0,0,1)):struct.pack_into('<H',b,offset,value)
   w['base64']=base64.b64encode(b).decode();w['sha256']=sha(b)
 return n
outcomes=[]
for failure in ('success','trace-start','prepare','baseline-readiness','baseline','baseline-fault','onset-readiness','onset','admission','post-readiness','post-tables','post-disagrees','trace-stop'):
 with tempfile.TemporaryDirectory(prefix='eo-coordinator-',dir=H/'tmp')as tmp:
  here=Path(tmp);(here/'orchestration-input-pins.json').write_bytes((EO/'orchestration-input-pins.json').read_bytes());(here/'verify-observation.py').write_bytes(guard)
  m=load(EO/'run-instrumented.py','eo_coordinator_mock');m.HERE=here;calls=[]
  class FakeProcess:
   def run(self,argv,capture_output):
    helper=Path(argv[1]);args=argv[2:]
    if helper.name=='kernel-trace.py':name='trace-'+args[0]
    elif helper.name=='prepare-score-header-v2.py':name='prepare'
    elif helper.name=='prepare-readiness.py':name=Path(args[args.index('--output')+1]).name
    elif helper==EB/'run-once.py':name=Path(args[args.index('--output')+1]).name
    elif helper==EM/'run-once.py':name='onset'
    elif helper.name=='verify-observation.py':name='admission'
    else:raise ValueError('unexpected helper')
    calls.append(name)
    code=1 if name==failure else 0
    if name=='trace-start':Path(args[args.index('--output')+1]).mkdir(mode=0o700)
    if code==0 and name=='prepare':
     p=Path(args[args.index('--output')+1]);p.mkdir();(p/'result.json').write_text('{"accepted":true}')
    if code==0 and name.endswith('readiness'):
     p=Path(args[args.index('--output')+1]);p.mkdir();(p/'readiness.json').write_text('{"syntheticHostMock":true}')
    if code==0 and name in ('baseline','post-tables'):
     p=Path(args[args.index('--output')+1]);p.mkdir();n=eb_native(failure=='baseline-fault'and name=='baseline'or failure=='post-disagrees'and name=='post-tables');(p/'native.receipt.json').write_text(json.dumps(n));(p/'result.json').write_text('{"accepted":true,"cleanup":"STAGE_ABSENT"}')
    if code==0 and name=='onset':
     p=Path(args[args.index('--output')+1]);p.mkdir();(p/'result.json').write_text('{"accepted":true}');(p/'native.receipt.json').write_text('{}')
    if code==0 and name=='admission':Path(args[args.index('--output')+1]).write_text(json.dumps({'accepted':True,'lastRtTuple':[0,0,1],'terminal':'CycleLimit','checkpoints':60,'maximumSampledA0':0}))
    return types.SimpleNamespace(returncode=code,stdout=b'{}\n',stderr=b'')
  m.subprocess=FakeProcess();sys.argv=['run-instrumented.py','--execute'];raised=False
  try:m.main()
  except ValueError:raised=True
  result=json.loads((here/'trial-01/result.json').read_text())
  need(result['target_recovery_invocations']==0,'no automatic recovery')
  need(calls.count('onset')<=1 and calls.count('baseline')<=1 and calls.count('post-tables')<=1,'no helper retry')
  need(calls[-1]=='trace-stop'if failure!='trace-start'else calls==['trace-start'],'trace cleanup after confirmed start only')
  if failure in ('success','trace-stop'):need(not raised and result['accepted_pair']is True,'pair success independent trace')
  else:need(raised and result['accepted_pair']is False,'failure stops pair')
  if failure=='baseline-fault':need('onset'not in calls and 'admission'not in calls and 'post-tables'not in calls,'no key/test after faulted baseline')
  if failure in ('onset','admission'):need('post-tables'not in calls,'no postheaders after ambiguous/refused EM/admission')
  if failure=='trace-stop':need(result['trace_collected']is False,'trace failure explicit separate')
  outcomes.append({'case':failure,'calls':calls,'acceptedPair':result['accepted_pair'],'traceCollected':result.get('trace_collected'),'raised':raised})
need(sha((EO/'verify-observation.py').read_bytes())==sha(guard)and sha((EO/'run-instrumented.py').read_bytes())==sha(runner)and sha(test.read_bytes())==sha(test_raw),'EO functional files unchanged')
value={'schema':'eo-independent-admission-coordinator-review-v1','accepted':True,'checks':checks,'eiGuardSha256':sha(old.encode()),'eoGuardSha256':sha(guard),'eoCoordinatorSha256':sha(runner),'eoInputPinsSha256':sha((EO/'orchestration-input-pins.json').read_bytes()),'eoTestSha256':sha(test_raw),'admissionGuardExactIdentityOnlyDelta':True,'suites':suites,'coordinatorMockCases':outcomes,'targetCalls':0,'networkCalls':0,'limitations':['Trace-start ambiguity before confirmed return does not enter trace-stop; existing watchdog disables a started private instance after90s, possible leftover instance requires reconciliation.','Coordinator does not create one continuous global access lock across helpers; parent serialization and phase premises remain required.','Helper process bounds are inherited; coordinator itself has no outer process deadline.','accepted_pair concerns EB/EM/EB contract; trace-stop failure is reported separately as trace_collectedfalse.']}
(H/'eo-independent-validation.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');print(json.dumps({'accepted':True,'checks':checks,'coordinatorMockCases':len(outcomes),'validationSha256':sha((H/'eo-independent-validation.json').read_bytes()),'targetCalls':0}))
