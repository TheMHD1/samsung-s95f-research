#!/usr/bin/env python3
"""Coordinator control-flow mocks. No target module, subprocess or network calls."""
from pathlib import Path
import contextlib,copy,hashlib,importlib.util,io,json,sys,tempfile,types
H=Path(__file__).resolve().parent;D=H.parent.parent;B=D.parent
checks=0;cases=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)
def dump(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o)+'\n')
def load():
 sp=importlib.util.spec_from_file_location('ex_under_review',D/'run-raised.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
need(sha((D/'run-raised.py').read_bytes())=='23116a99f988947216ab77d95979dadf148aeed97a06d043fdd91b36fdb9dba4','final coordinator source pin')
need(sha((D/'raised-input-pins.json').read_bytes())=='951cc194cc30fa1c29dfcd2d67a84e1d0f66a634e34b9e4acaa96d4c677e6400','final25-input pinfile')
actual_pins=json.loads((D/'raised-input-pins.json').read_text())
for rel,digest in actual_pins.items():need(not(B/rel).is_symlink()and sha((B/rel).read_bytes())==digest,'original25 pins exact')
need(len(actual_pins)==25,'25 reviewed inputs')
(H/'private').mkdir(mode=0o700,exist_ok=True)
class Case:
 def __init__(self,root,kind):
  self.kind=kind;self.root=root;self.events=[];self.m=load();self.m.HERE=root/'limit-rechallenge-trial-20261028ex';self.m.B=root
  for key,family in [('FA','selective-endpoint-limit-writer-20261028fa'),('EY','rtp-limit200-checkpoints-20261028ey'),('EB','rtp-lane-gate-capture-20261028eb'),('EI','refresh-checkpoint-trial-20261028ei')]:setattr(self.m,key,root/family)
  self.m.IDENTITY=root/'quiescent-onset-trial-20261028es/trial-01/after-recovery-identity/identity.json'
  pins={}
  for rel in actual_pins:
   p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('SYNTHETIC OFFLINE HELPER/INPUT '+rel+'\n');pins[rel]=sha(p.read_bytes())
  if kind=='missing-pin':pins.pop('rtp-limit200-checkpoints-20261028ey/verify-observation.py')
  if kind=='changed-pin':pins['rtp-limit200-checkpoints-20261028ey/verify-observation.py']='0'*64
  dump(self.m.HERE/'raised-input-pins.json',pins)
  self.fa_n={'action':'set40to200','device':63,'headersSent':7,'bulkTransfers':14,'protocolPhase':'ReadyForHeader','released':True,'closed':True}
  self.fa_raw=[(n+'.bin',(n+'-SYNTHETIC').encode(),sha((n+'-SYNTHETIC').encode()))for n in('callbacks','baseline-R','pre-M','pre-C','fresh-R','readback-R')]
  self.eb_n={'device':63,'headersSent':16,'bulkTransfers':32,'protocolPhase':'ReadyForHeader','released':True,'closed':True}
  self.eb_raw=[(f'synthetic-window-{i}.bin',bytes([i])*4,sha(bytes([i])*4))for i in range(16)]
  self.eb_q={'startR':{'alternateLimit':200},'endR':{'alternateLimit':200},'sourceContext':{'synthetic':True}}
  self.proof={'schema':'ey-completed-fixed200-admission-v1','accepted':True,'phase':'ReadyForHeader','released':True,'closed':True,'cleanup':'STAGE_ABSENT','actualSampledLimit':200,'terminal':'CycleLimit','checkpoints':56,'maximumSampledA0':44,'fixed200Evidence':{'actualFpSelectionProven':False},'lastRtTuple':[0,0,1],'inputs':[]}
  self.real_run=self.m.subprocess.run;self.m.subprocess.run=self.run;self.m.module=self.module
 def module(self,path,name):
  if path==self.m.FA/'parse-result.py':
   def parse(raw):
    if self.kind=='set-parser-refusal':raise ValueError('synthetic strict parser refusal')
    return self.fa_n,self.fa_raw,[]
   return types.SimpleNamespace(parse_native=parse)
  if path==self.m.EY/'verify-observation.py':
   def verify(path):
    self.events.append('offline-recompute')
    if self.kind=='EY-recompute-refusal':raise ValueError('synthetic stale native input')
    return copy.deepcopy(self.proof)
   return types.SimpleNamespace(verify=verify)
  if path==self.m.EB/'parse-result.py':return types.SimpleNamespace(parse_native=lambda raw:(self.eb_n,self.eb_raw,self.eb_q))
  raise ValueError('unexpected module import '+str(path))
 def run(self,argv,**kwargs):
  helper=Path(argv[1]);args=argv[2:];out=Path(args[args.index('--output')+1])
  if helper.name=='prepare-score-header-v2.py':stage='prepare'
  elif helper.name=='prepare-readiness.py':stage={'fa':'set-readiness','ey':'onset-readiness','eb':'post-readiness'}[args[args.index('--wrapper')+1]]
  elif helper==self.m.FA/'run-once.py':stage='set'
  elif helper==self.m.EY/'run-once.py':stage='onset'
  elif helper==self.m.EY/'verify-observation.py':stage='admission'
  elif helper==self.m.EB/'run-once.py':stage='post-tables'
  else:raise ValueError('unexpected operational helper')
  self.events.append(stage)
  need(not any(x in str(argv)for x in('MODE2','recover-eb','--action\', \'restore','--execute-restore')),'no recovery/restore')
  if self.kind==stage+'-launch-exception':raise OSError('synthetic subprocess launch/transport exception')
  if self.kind==stage+'-exit':return types.SimpleNamespace(returncode=1,stdout=b'synthetic refusal',stderr=b'')
  if stage=='prepare':dump(out/'result.json',{'accepted':self.kind!='prepare-semantic'})
  elif stage.endswith('readiness'):dump(out/'readiness.json',{'syntheticOnly':True,'stage':stage})
  elif stage=='set':
   out.mkdir(parents=True);(out/'native.receipt.json').write_text('SYNTHETIC SET RECEIPT')
   for name,raw,digest in self.fa_raw:(out/name).write_bytes(raw)
   result={'schema':'fa-fixed-limit-wrapper-result-v1','action':'set40to200','accepted':True,'cleanup':'STAGE_ABSENT','manifestSha256':sha((self.m.FA/'deployment-manifest.json').read_bytes()),'readinessSha256':sha(Path(args[args.index('--readiness')+1]).read_bytes()),'headersSent':7,'bulkTransfers':14,'nativeInvocations':1,'retries':0,'rawFiles':[{'name':n,'bytes':len(r),'sha256':h}for n,r,h in self.fa_raw]}
   if self.kind=='set-result-refusal':result['accepted']=False
   if self.kind=='set-manifest':result['manifestSha256']='0'*64
   if self.kind=='set-count':result['headersSent']=8
   if self.kind=='set-bool-count':result['nativeInvocations']=True
   if self.kind=='set-inventory':result['rawFiles']=[]
   if self.kind=='set-raw':(out/self.fa_raw[0][0]).write_bytes(b'bad')
   dump(out/'result.json',result)
  elif stage=='onset':dump(out/'result.json',{'syntheticOnly':True});(out/'native.receipt.json').write_text('SYNTHETIC EY RECEIPT')
  elif stage=='admission':
   proof=copy.deepcopy(self.proof)
   if self.kind=='proof-schema':proof['schema']='wrong'
   if self.kind=='proof-phase':proof['phase']='Unknown'
   if self.kind=='proof-limit':proof['actualSampledLimit']=40
   if self.kind=='proof-input':proof['inputs']=[{'sha256':'0'*64}]
   if self.kind=='proof-missing':del proof['terminal']
   if self.kind=='proof-refusal':proof['accepted']=False
   dump(out,proof)
  elif stage=='post-tables':
   out.mkdir(parents=True);(out/'native.receipt.json').write_text('SYNTHETIC EB RECEIPT')
   for name,raw,digest in self.eb_raw:(out/name).write_bytes(raw)
   result={'schema':'eb-rtp-lane-gate-wrapper-result-v1','accepted':True,'cleanup':'STAGE_ABSENT','manifestSha256':sha((self.m.EB/'deployment-manifest.json').read_bytes()),'readinessSha256':sha(Path(args[args.index('--readiness')+1]).read_bytes()),'headersSent':16,'bulkTransfers':32,'nativeInvocations':1,'retries':0,'rawFiles':[{'name':n,'bytes':len(r),'sha256':h}for n,r,h in self.eb_raw]}
   if self.kind=='post-manifest':result['manifestSha256']='0'*64
   if self.kind=='post-count':result['bulkTransfers']=33
   if self.kind=='post-bool-count':result['nativeInvocations']=True
   if self.kind=='post-inventory':result['rawFiles']=[]
   if self.kind=='post-raw':(out/self.eb_raw[0][0]).write_bytes(b'bad')
   if self.kind=='post-limit':self.eb_q['endR']['alternateLimit']=40
   dump(out/'result.json',result)
  return types.SimpleNamespace(returncode=0,stdout=b'SYNTHETIC HOST MOCK ONLY',stderr=b'')
 def execute(self):
  old=sys.argv;sys.argv=['run-raised.py','--execute'];error=None
  try:
   with contextlib.redirect_stdout(io.StringIO()):self.m.main()
  except Exception as e:error=type(e).__name__
  finally:sys.argv=old;self.m.subprocess.run=self.real_run
  result_path=self.m.HERE/'raised-01/result.json';state=json.loads(result_path.read_text())if result_path.is_file()else None
  return error,state

kinds=['success','missing-pin','changed-pin','prepare-exit','prepare-semantic','set-readiness-exit','set-exit','set-launch-exception','set-parser-refusal','set-result-refusal','set-manifest','set-count','set-bool-count','set-inventory','set-raw','onset-readiness-exit','onset-exit','admission-exit','proof-refusal','proof-schema','proof-phase','proof-limit','proof-input','proof-missing','EY-recompute-refusal','post-readiness-exit','post-tables-exit','post-manifest','post-count','post-bool-count','post-inventory','post-raw','post-limit']
with tempfile.TemporaryDirectory(prefix='flow-',dir=H/'private')as tmp:
 for index,kind in enumerate(kinds):
  case=Case(Path(tmp)/str(index),kind);err,state=case.execute()
  if kind=='success':
   need(err is None and state['accepted']is True,'success complete')
   need(case.events==['prepare','set-readiness','set','onset-readiness','onset','admission','offline-recompute','post-readiness','post-tables'],'exact sequential ordering')
  else:
   need(err is not None and (state is None or state['accepted']is False),'malformed/stage refusal stops '+kind)
  if kind in('missing-pin','changed-pin'):need(case.events==[]and state is None,'pin refusal before any target-stage mock')
  if kind.startswith('set-')and kind!='set-readiness-exit':need('onset'not in case.events and'post-tables'not in case.events,'no observer/post after unqualified set')
  if kind.startswith('proof-')or kind in('onset-exit','admission-exit','EY-recompute-refusal','onset-readiness-exit'):
   need('post-readiness'not in case.events and'post-tables'not in case.events,'no post-read before exact qualified EY proof')
  if state is not None:
   need(state['automatic_restore']is False and state['automatic_retries']==state['target_recovery_invocations']==0,'zero automatic restore/recovery/retry')
   need(state['restoration_required']is('set'in case.events),'conservative change obligation from set attempt')
  cases.append({'case':kind,'refused':err is not None,'stages':case.events,'restorationRequired':None if state is None else state['restoration_required']})
need(sha((D/'run-raised.py').read_bytes())=='23116a99f988947216ab77d95979dadf148aeed97a06d043fdd91b36fdb9dba4','source unchanged after mocks')
need(sha((D/'raised-input-pins.json').read_bytes())=='951cc194cc30fa1c29dfcd2d67a84e1d0f66a634e34b9e4acaa96d4c677e6400','input pins unchanged after mocks')
print(json.dumps({'schema':'ex-independent-coordinator-mock-validation-v1','accepted':True,'checksPassed':checks,'cases':cases,'actualPinsVerified':len(actual_pins),'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
