#!/usr/bin/env python3
"""EO exact admission delta + instrumented coordinator no-I/O branch mocks."""
from pathlib import Path
import base64,copy,hashlib,importlib.util,json,os,struct,subprocess,sys,tempfile,types
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;EO=H.parent;B=EO.parent;EM=B/'rtp-quiescent-checkpoints-20261028er';EI=B/'refresh-checkpoint-trial-20261028ei';EB=B/'rtp-lane-gate-capture-20261028eb'
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0

def need(ok,label):
 global checks
 checks+=1
 if not ok:raise ValueError(label)
def load(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
guard=(EO/'verify-observation.py').read_bytes();runner=(EO/'run-instrumented.py').read_bytes()
need(sha(guard)=='536c49f8d7a0a9b482fd6c6b5b66c5cfdadb3857537ac6bdc02d7160ed4e24d0','ES guard frozenpin')
need(sha(runner)=='c6cc7e7bd1be7ddc38d998839d5507cc8031e0bdfc592ebb3d533b5c92e50e2b','ES coordinator frozenpin')
pins=json.loads((EO/'orchestration-input-pins.json').read_text())
for rel,pin in pins.items():need(sha((B/rel).read_bytes())==pin,'coordinator helper pin')
# Existing admission negatives run with ONLY its scratch path redirected into owned reviews.
test=EO/'test-verify-observation.py';test_raw=test.read_bytes();text=test_raw.decode();needle="root=D/'reviews/host-environment/tmp'";need(text.count(needle)==1,'single test scratch path')
bootstrap="import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text().replace(\"root=D/'reviews/host-environment/tmp'\",\"root=Path(sys.argv[2])\"); exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})"
env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(H/'tmp'))
suites=[]
for optimized in (False,True):
 r=subprocess.run([sys.executable]+(['-O']if optimized else[])+['-B','-c',bootstrap,str(test),str(H/'tmp')],cwd=H,env=env,capture_output=True,timeout=20)
 need(r.returncode==0 and not r.stderr,'EO admission mocked suite');v=json.loads(r.stdout);need(v['checksPassed']==229 and v['unexpectedAcceptances']==[]and v['targetOperations']==v['rootCalls']==v['networkOperations']==0,'229 admission checks')
 suites.append({'optimized':optimized,'summary':v,'stdoutSha256':sha(r.stdout)})
# Coordinator filesystem/output is redirected; subprocess.run is replaced completely.
# Only strict EB parser is used; the fixture is generated FakeOps data, never actual raw OEM data.
fixture=json.loads((EB/'fixture.json').read_text())
def eb_native(state):
 n=copy.deepcopy(fixture)
 for w in n['windows']:
  if w['name']in ('start-R','end-R'):
   b=bytearray(base64.b64decode(w['base64']))
   for offset,value in zip((0,10,14),state):struct.pack_into('<H',b,offset,value)
   w['base64']=base64.b64encode(b).decode();w['sha256']=sha(b)
 return n
outcomes=[]
for failure in ('success','trace-start','prepare','baseline-readiness','baseline','baseline-fault','onset-readiness','onset','admission','post-readiness','post-tables','post-disagrees','quiescent-post-clean','quiescent-post-quiescent','baseline-quiescent','post-limit','admission-false','trace-stop'):
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
     p=Path(args[args.index('--output')+1]);p.mkdir();state=(1,0x1001,0)if failure=='baseline-fault'and name=='baseline'or failure=='post-disagrees'and name=='post-tables'else(0,0,0)if failure=='baseline-quiescent'and name=='baseline'or failure=='quiescent-post-quiescent'and name=='post-tables'else(0,0,1);n=eb_native(state);
     if failure=='post-limit'and name=='post-tables':
      for w in n['windows']:
       if w['name']in('start-R','end-R'):
        b=bytearray(base64.b64decode(w['base64']));struct.pack_into('<H',b,0xc4,200);w['base64']=base64.b64encode(b).decode();w['sha256']=sha(b)
     (p/'native.receipt.json').write_text(json.dumps(n));(p/'result.json').write_text('{"accepted":true,"cleanup":"STAGE_ABSENT"}')
    if code==0 and name=='onset':
     p=Path(args[args.index('--output')+1]);p.mkdir();(p/'result.json').write_text('{"accepted":true}');(p/'native.receipt.json').write_text('{}')
    if code==0 and name=='admission':Path(args[args.index('--output')+1]).write_text(json.dumps({'accepted':failure!='admission-false','lastRtTuple':[0,0,0]if failure.startswith('quiescent-')else[0,0,1],'terminal':'CycleLimit','checkpoints':56,'maximumSampledA0':0,'quiescentCyclesCompleted':55 if failure.startswith('quiescent-')else 0,'allSampledClean':not failure.startswith('quiescent-'),'actualSampledLimit':40}))
    return types.SimpleNamespace(returncode=code,stdout=b'{}\n',stderr=b'')
  m.subprocess=FakeProcess();sys.argv=['run-instrumented.py','--execute'];raised=False
  try:m.main()
  except ValueError:raised=True
  result=json.loads((here/'trial-01/result.json').read_text())
  need(result['target_recovery_invocations']==0,'no automatic recovery')
  need(calls.count('onset')<=1 and calls.count('baseline')<=1 and calls.count('post-tables')<=1,'no helper retry')
  need(calls[-1]=='trace-stop'if failure!='trace-start'else calls==['trace-start'],'trace cleanup after confirmed start only')
  if failure in ('success','trace-stop','post-disagrees','quiescent-post-clean','quiescent-post-quiescent'):need(not raised and result['accepted_pair']is True,'pair success independent trace')
  else:need(raised and result['accepted_pair']is False,'failure stops pair')
  if failure in ('baseline-fault','baseline-quiescent'):need('onset'not in calls and 'admission'not in calls and 'post-tables'not in calls,'no key/test after faulted baseline')
  if failure in ('onset','admission','admission-false'):need('post-tables'not in calls,'no postheaders after ambiguous/refused EM/admission')
  if failure=='trace-stop':need(result['trace_collected']is False,'trace failure explicit separate')
  if failure in ('post-disagrees','quiescent-post-clean'):need(result['post_relation']=='state_changed_between_separate_observations' and result['ER_last_R']!=result['EB_post_R'][0],'changed poststate explicit, not false equality')
  if failure=='quiescent-post-quiescent':need(result['post_relation']=='same_as_ER_last_R'and result['ER_last_R']==[0,0,0],'Q preserved, not projectedClean')
  outcomes.append({'case':failure,'calls':calls,'acceptedPair':result['accepted_pair'],'traceCollected':result.get('trace_collected'),'raised':raised})
need(sha((EO/'verify-observation.py').read_bytes())==sha(guard)and sha((EO/'run-instrumented.py').read_bytes())==sha(runner)and sha(test.read_bytes())==sha(test_raw),'EO functional files unchanged')
value={'schema':'es-independent-admission-coordinator-review-v1','accepted':True,'checks':checks,'esGuardSha256':sha(guard),'esCoordinatorSha256':sha(runner),'esInputPinsSha256':sha((EO/'orchestration-input-pins.json').read_bytes()),'esTestSha256':sha(test_raw),'suites':suites,'coordinatorMockCases':outcomes,'targetCalls':0,'networkCalls':0,'limitations':['Trace-start ambiguity before confirmed return does not enter trace-stop; existing watchdog disables a started private instance after90s, possible leftover instance requires reconciliation.','Coordinator does not create one continuous global access lock across helpers; parent serialization and phase premises remain required.','Helper process bounds are inherited; coordinator itself has no outer process deadline.','accepted_pair concerns EB/EM/EB contract; trace-stop failure is reported separately as trace_collectedfalse.']}
(H/'es-independent-validation.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');print(json.dumps({'accepted':True,'checks':checks,'coordinatorMockCases':len(outcomes),'validationSha256':sha((H/'es-independent-validation.json').read_bytes()),'targetCalls':0}))
