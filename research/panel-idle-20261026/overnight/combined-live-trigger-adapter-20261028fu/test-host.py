#!/usr/bin/env python3
"""Finite zero-I/O Live preparation/wake and actual-identity wrapper qualification."""
import base64,copy,json,subprocess,tempfile,types,sys,shlex,contextlib,io
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent;checks=0;case_count=0

def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def check(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def rejects(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'expected refusal');return
 raise ValueError('unexpected acceptance')
r=load(P/'run-once.py');w=load(P/'wake-check.py');prep=load(P/'prepare-live.py');fn=load(r.FN/'run-once.py');parser=load(r.FN/'parse-result.py')
fc=B/'reader-wake-checkpoints-20261028fc/test-runner.py';source=fc.read_text().split('manifest,payload=r.build_manifest();')[0];m=types.ModuleType('fc_mock_definitions');m.__file__=str(fc);exec(compile(source,str(fc),'exec'),m.__dict__)
def snapshot(kind='success'):
 text=m.snapshot(kind).replace('d/apps.tab','d/ug.tab@Live')
 if kind=='apps':text=text.replace('d/ug.tab@Live','d/apps.tab')
 if kind=='bad-canonical':text=text.replace(' (String)','  (String)')
 return text
FO=B/'combined-event-successor-trial-20261028fo/capture-01';native=(FO/'native.receipt.json').read_bytes();fixture=json.loads(native);historical=json.loads((B/'combined-event-trial-20261028fh/capture-01/native.receipt.json').read_bytes())
check(parser.parse_native(native.decode())[0]['accepted']and fixture['device']==65,'actual USB65 native fixture')
manifest,payload=r.build_manifest();raw_manifest=r.manifest_bytes(manifest);check(raw_manifest==(P/'deployment-manifest.json').read_bytes(),'sealed manifest exact')
check(payload==fn.build_manifest()[1],'exact FN payload bytes in place')
r.uuid=fn.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32))
class Mock(m.FakeRoot):
 def __init__(self,kind='success',live=True):super().__init__(kind);self.live=live;self.fetch=0
 def response(self,c):
  if ' --receipt-self-test > 'in c:return m.envelope(b'{"smokeTestsPassed":8,"targetOperations":0}\n')
  if 'enlightenment_info -topvwins'in c:
   self.snapshots+=1;return snapshot('apps'if self.kind=='apps'else'success')if self.live else m.snapshot()
  if ' --execute --device 'in c:
   self.native+=1;v=copy.deepcopy(fixture)
   if self.kind=='refused':v=copy.deepcopy(historical);v['schema']='combined-event-checkpoints-fn-v1'
   text=m.envelope((json.dumps(v)+'\n').encode())
   if self.kind=='refused':text=text.replace('\n1.0 2.0\n0\n','\n1.0 2.0\n1\n')
   return 'IMMEDIATE_READY\n'+text
  if 'echo FN_SIDECAR_BEGIN'in c:
   self.fetch+=1;name='baseline-ring.bin'if 'baseline-ring.bin'in c else'post-ring.bin';return 'FN_SIDECAR_BEGIN\n'+base64.b64encode((FO/name).read_bytes()).decode()+'\nFN_SIDECAR_END\n'
  return super().response(c)
P.joinpath('host-environment/tmp').mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='fu-',dir=P/'host-environment/tmp')as td:
 base=Path(td);ready=json.loads((FO/'readiness-decision.json').read_bytes());ready['schema']='fu-combined-live-event-readiness-decision-v1';rb=json.dumps(ready).encode();rp=base/'ready.json';rp.write_bytes(rb);check(r.load_readiness(rp,r.sha(rb))[0]['identity']==json.loads((FO/'readiness-decision.json').read_bytes())['identity'],'all17 actual USB65 identity values')
 command_sequences={}
 for kind in ['success','apps','refused']:
  case_count+=1;mock=Mock(kind);clock=m.Clock();out=base/kind
  if kind=='success':
   result=r.execute(out,ready,rb,raw_manifest,payload,mock,parser,clock,clock.sleep);check(result['accepted']and result['keyExposureQualified']and result['expectedCachedTab']=='Live','actual retained capture successful replay')
   check(mock.ui==mock.native==mock.cleanup==1 and mock.fetch==2,'one wake/native/cleanup two sidecars')
   wakeindex=next(i for i,c in enumerate(mock.commands)if 'input_keyevent XF86AudioRaiseVolume down'in c);check(mock.commands[wakeindex-1].endswith('echo BEFORE_INVOKE_READY\n')and ' --execute --device 'in mock.commands[wakeindex+2],'staging/selftest then wake then immediate native')
   check('test -d /tmp/researcher-fn-'in mock.commands[1]or any('/tmp/researcher-fn-'in c for c in mock.commands),'FN native stage prefix')
   names=shlex.split(next(l for l in mock.commands[-1].splitlines()if l.startswith('rm -- ')))[2:];check(len(names)==len(set(names))==11,'exact11file cleanup')
   command_sequences['fu']=mock.commands
  else:
   rejects(lambda:r.execute(out,ready,rb,raw_manifest,payload,mock,parser,clock,clock.sleep))
   check(mock.fetch==mock.cleanup==0,'no cleanup/fetch after refusal')
   if kind=='apps':check(mock.native==0 and mock.ui==1 and mock.snapshots==1,'wrong tab stops before native without second wake')
   else:
    p=json.loads((out/'primary-native-outcome.json').read_bytes());result=json.loads((out/'result.json').read_bytes());check(p['error']==historical['error']and result['error']==historical['error']and not result['accepted'],'original refusal preserved before partial ring binding');check(mock.native==1 and ' --execute --device 'in mock.commands[-1],'no root call after refused native')
 fnready=copy.deepcopy(ready);fnready['schema']='fn-combined-event-readiness-decision-v1';f=Mock(live=False);c=m.Clock();fn.execute(base/'fn-control',fnready,json.dumps(fnready).encode(),fn.manifest_bytes(fn.build_manifest()[0]),payload,f,parser,c,c.sleep);check(command_sequences['fu']==f.commands,'every generated command byte-identical to FN actual65 control')
 # Wake finite guard/clock cases; all calls use a local list callback.
 for kind in ['success','apps','wrong-tab','duplicate-tab','missing-tab','bad-canonical','saver','no-csfs','truncated','oversize','wake-fail','settle','budget','slow-wake']:
  case_count+=1;out=base/('wake-'+kind);out.mkdir();calls=[];cp={};clock=m.Clock(kind)
  def call(command,**kw):
   calls.append(command)
   if command==w.wake_command():return 'LOCAL_KEY_DOWN_EXIT='+('1'if kind=='wake-fail'else'0')+'\nLOCAL_KEY_UP_EXIT=0\n'
   need_kind='saver'if kind=='settle'and len(calls)==2 else'success'if kind in ['settle','budget','slow-wake']else kind
   return snapshot(need_kind)
  if kind in ['success','settle']:
   w.perform(out,call,cp,clock,clock.sleep);w.dispatch(cp,clock);check(w.validate(out,cp)['accepted'],'Live wake acceptance');check(len(calls)==(3 if kind=='settle'else 2),'first accepted snapshot ends settle')
   for age in [-1,w.AGE_NS+1]:rejects(lambda:w.dispatch(cp,lambda:cp['acceptedQueryReturnedHostMonotonicNs']+age))
   bad=copy.deepcopy(cp);bad['keyChildAttempts']=True;rejects(lambda:w.validate(out,bad))
   original=(out/'wake-command.txt').read_bytes();(out/'wake-command.txt').write_bytes(original+b':\n');rejects(lambda:w.validate(out,cp));(out/'wake-command.txt').write_bytes(original)
  else:
   rejects(lambda:w.perform(out,call,cp,clock,clock.sleep));check(cp['status']=='refused_or_ambiguous','truthful wake refusal')
   check(len(calls)<=11 and calls.count(w.wake_command())<=1,'wake finite call count')
   if kind in ['apps','wrong-tab','duplicate-tab','missing-tab','bad-canonical','truncated','oversize']:check(len(calls)==2,'malformed/unknown tab no extra snapshot')
 # Preparation exact Up/Up, optional saver wake and refusal sequencing.
 for kind in ['success','initial-saver','apps','up-fail','up2-fail','after-up-wrong','saver-exhaust','malformed','clock']:
  case_count+=1;out=base/('prep-'+kind);calls=[];clock=m.Clock();up=0;snap=0
  def call(command):
   calls.append(command)
   if command in [prep.up_command(),w.wake_command()]:
    count=calls.count(prep.up_command());bad=command==prep.up_command()and((kind=='up-fail'and count==1)or(kind=='up2-fail'and count==2));return 'LOCAL_KEY_DOWN_EXIT='+('1'if bad else'0')+'\nLOCAL_KEY_UP_EXIT=0\n'
   k='success'
   if kind=='apps':k='apps'
   if kind=='malformed':k='truncated'
   if kind=='after-up-wrong'and prep.up_command()in calls:k='wrong-tab'
   if kind=='initial-saver'and len(calls)==1:k='saver'
   if kind=='saver-exhaust':k='saver'
   if kind=='clock':clock.now+=w.BUDGET_NS+1
   return snapshot(k)
  if kind in ['success','initial-saver']:
   v=prep.perform(out,call,r.sha(raw_manifest),clock,clock.sleep);check(prep.load_certificate(out/'preparation.json',r.sha((out/'preparation.json').read_bytes()),r.sha(raw_manifest))['accepted'],'complete certificate locally bound');check(calls.count(prep.up_command())==2 and len(calls)==(7 if kind=='initial-saver'else 5),'exact bounded prep sequence');check(calls.count(w.wake_command())==(kind=='initial-saver'),'optional volume wake only for saver')
   altered=copy.deepcopy(v);altered['upPairsCompleted']=True;rejects(lambda:prep.validate(out,altered,r.sha(raw_manifest)))
   altered=copy.deepcopy(v);altered['entries'].append(copy.deepcopy(v['entries'][-1]));rejects(lambda:prep.validate(out,altered,r.sha(raw_manifest)))
   altered=copy.deepcopy(v);altered['entries'][1]['beforeHostMonotonicNs']=-1;rejects(lambda:prep.validate(out,altered,r.sha(raw_manifest)))
   path=out/'up-1-command.txt';original=path.read_bytes();path.write_bytes(original.replace(b'Up down',b'Left down'));rejects(lambda:prep.validate(out,v,r.sha(raw_manifest)));path.write_bytes(original)
   rejects(lambda:prep.load_certificate(out/'preparation.json','0'*64,r.sha(raw_manifest)))
  else:
   rejects(lambda:prep.perform(out,call,r.sha(raw_manifest),clock,clock.sleep));check(json.loads((out/'preparation.json').read_bytes())['status']=='refused_or_ambiguous','preparation refusal retained')
   expected={'apps':1,'malformed':1,'up-fail':2,'up2-fail':4,'after-up-wrong':3,'saver-exhaust':12,'clock':1}[kind];check(len(calls)==expected,'no further request after prep refusal')
  check(all('input_keyevent Left'not in c for c in calls),'preparation noLeft')
  for command in calls:check(len(command.encode())<=8192 and subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'prep exact commands shell/cap')
 # Main CLI must bind locally accepted preparation and exact readiness evidence before root import.
 cli_prep=base/'cli-preparation';clock=m.Clock()
 prep.perform(cli_prep,lambda command:('LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n'if command==prep.up_command()else snapshot()),r.sha(raw_manifest),clock,clock.sleep)
 certificate=cli_prep/'preparation.json';certificate_sha=r.sha(certificate.read_bytes())
 real_load=r.load_pinned;root_loads=[];cli_mock=Mock()
 cli_mock.REMOTE_TIMEOUT_SECONDS=45;cli_mock.HOST_TIMEOUT_SECONDS=75;cli_mock.MAX_COMMAND=8192;cli_mock.MAX_RESPONSE=65536
 def load_for_cli(path,digest,name):
  if path==r.ROOT:root_loads.append(path);return cli_mock
  return real_load(path,digest,name)
 r.load_pinned=load_for_cli
 original_argv=sys.argv
 try:
  for kind in ['missing-certificate','wrong-certificate-hash','unbound-certificate','accepted']:
   case_count+=1;rd=copy.deepcopy(ready)
   if kind!='unbound-certificate':rd['evidence'].append({'path':str(certificate),'sha256':certificate_sha})
   rp=base/('cli-'+kind+'.json');rp.write_text(json.dumps(rd));out=base/('cli-output-'+kind)
   sys.argv=['run-once.py','--execute','--manifest-sha256',r.sha(raw_manifest),'--readiness',str(rp),'--readiness-sha256',r.sha(rp.read_bytes()),'--output',str(out)]
   if kind!='missing-certificate':sys.argv+=['--preparation',str(certificate),'--preparation-sha256',('0'*64 if kind=='wrong-certificate-hash'else certificate_sha)]
   with contextlib.redirect_stdout(io.StringIO()):
    if kind=='accepted':r.main()
    else:rejects(r.main)
   check(len(root_loads)==(1 if kind=='accepted'else 0),'local certificate gating before root import')
  check(cli_mock.native==cli_mock.ui==cli_mock.cleanup==1,'one qualified CLI owner')
 finally:r.load_pinned=real_load;sys.argv=original_argv
 # Fresh readiness adds the exact preparation reference; dry/invalid certificates never import root.
 pr=load(P/'prepare-readiness.py');pr_real_load=pr.load;readiness_calls=[]
 class CachedRoot:
  def root(self,command,record,path):
   readiness_calls.append(command);check(len(command.encode())<=8192 and subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'cached readiness command bound/syntax');return 'FDCENSUS expected=100 missing=1 holders=0 errors=0\nFU_CURRENT_READY\n'
 def pr_load(path,digest,name):return CachedRoot()if path==pr.ROOT else pr_real_load(path,digest,name)
 pr.load=pr_load;identity_path=base/'identity.json';identity_path.write_text(json.dumps(ready['identity']));phase=base/'phase.txt';phase.write_text('SYNTHETIC HOST ONLY explicit parent phase premise with no actual device or queue qualification.')
 try:
  for kind in ['dry','invalid-certificate','execute']:
   case_count+=1;out=base/('readiness-'+kind);sys.argv=['prepare-readiness.py','--wrapper','fu','--wrapper-sha256',r.sha((P/'run-once.py').read_bytes()),'--manifest-sha256',r.sha(raw_manifest),'--preparation',str(certificate),'--preparation-sha256',('0'*64 if kind=='invalid-certificate'else certificate_sha),'--identity',str(identity_path),'--phase-note',str(phase),'--output',str(out)]
   if kind=='execute':sys.argv+=['--execute']
   with contextlib.redirect_stdout(io.StringIO()):
    if kind=='invalid-certificate':rejects(pr.main)
    else:pr.main()
   check(len(readiness_calls)==(1 if kind=='execute'else 0),'readiness dry/invalid no root and execute one cached query')
   if kind=='execute':
    result=json.loads((out/'readiness.json').read_bytes());check({'path':str(certificate),'sha256':certificate_sha}in result['evidence'],'fresh readiness pins exact separate preparation');check(result['identity']==ready['identity']and result['endpointQueueProof']is False,'readiness identity/premise distinction')
   else:check(not out.exists(),'dry/local refusal no target output stage')
 finally:pr.load=pr_real_load;sys.argv=original_argv
 check(len(m.commands)>0 and max(len(c.encode())for c in m.commands)<=8192,'root command cap')
print(json.dumps({'schema':'fu-host-validation-v1','checks':checks,'cases':case_count,'fullWrapperRuns':5,'shellCommands':len(m.commands),'maxCommandBytes':max(len(c.encode())for c in m.commands),'actualUsbAddress':65,'all17IdentityFieldsReused':True,'allWrapperCommandsEqualFnControl':True,'targetOperations':0},sort_keys=True))
