#!/usr/bin/env python3
"""Focused FN parser, per-pair budget and wrapper tests. All transports are mocks."""
import base64,copy,hashlib,json,subprocess,tempfile,types,shlex
from pathlib import Path
P=Path(__file__).resolve().parent;checks=0

def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
r=load(P/'run-once.py');parser=load(P/'parse-result.py')
def check(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1
def rejects(f):
 try:f()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'rejection');return
 raise ValueError('unexpected acceptance')
fixture=json.loads((P/'fixture.json').read_bytes());raw=(P/'fixture.json').read_bytes();check(len(parser.parse_native(raw.decode())[1])==56,'full56')
ring=bytearray(15372);ring[0:2]=(4).to_bytes(2,'little');ring[12]=7;ring=bytes(ring)
check(parser.bind_rings(fixture,ring,ring)['postRing']['write']==4,'full sidecar')
for k in ['accepted','loggerMayRemain','threshold','headers','bulks','inputs','writes','phase','bindingQualified','restore','arm','observationComplete','retries','physicalPictureObserved','cyclesStarted','cleanCycles']:
 v=copy.deepcopy(fixture)
 if type(v[k])is bool:v[k]=not v[k]
 elif type(v[k])is int:v[k]+=1
 else:v[k]='unknown'
 # accepted=false is preserved as refusal, not a malformed object.
 if k=='accepted':check(parser.parse_native(json.dumps(v)+'\n')[2]['accepted']is False,'refusal never promoted');continue
 rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
for i,c in enumerate(fixture['controls']):
 for j,t in enumerate(c['transfers']):
  v=copy.deepcopy(fixture);v['controls'][i]['transfers'][j][2]-=1;rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
for label in ['baselineRing','postRing']:
 for mutation in [b'',ring[:-1],ring[:-1]+b'1']:
  rejects(lambda:parser.bind_rings(fixture,mutation if label=='baselineRing'else ring,mutation if label=='postRing'else ring))
for i in range(56):
 v=copy.deepcopy(fixture);b=bytearray(base64.b64decode(v['rows']['rawBase64']));b[58*i+2:58*i+4]=(200).to_bytes(2,'little');v['rows']['rawBase64']=base64.b64encode(b).decode();v['rows']['sha256']=r.sha(b);rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
for key in ['headers','bulks','inputs','writes','threshold','retries','cyclesStarted']:
 v=copy.deepcopy(fixture);v[key]=False;rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
for key in ['exitCode','stdoutBytes','stderrBytes']:
 v=copy.deepcopy(fixture);v['intervention']['calls'][0][key]=False;rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
# Bind EVERY field of the first retained58B row, not a selected subset.
for pos in range(58):
 v=copy.deepcopy(fixture);b=bytearray(base64.b64decode(v['rows']['rawBase64']));b[pos]^=1;v['rows']['rawBase64']=base64.b64encode(b).decode();v['rows']['sha256']=r.sha(b);rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
# Cleanup scan is a source-bounded boolean, independent of asynchronous R freshness.
for scan in [0,1,2]:
 v=copy.deepcopy(fixture);cap=next(c for c in v['controls']if c['role']=='prerestore-M');b=bytearray(base64.b64decode(cap['windows'][0]['raw']));b[56]=scan;cap['windows'][0]['raw']=base64.b64encode(b).decode()
 if scan<2:check(parser.parse_native(json.dumps(v)+'\n')[0]['accepted'],'finite lagged cleanup scan admitted')
 else:rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
q=json.loads(subprocess.check_output(['python3','-B',str(P/'qualify-scan.py')]))
check(q['targetOperations']==0 and [s['scan']for s in q['actualSamples']]==[1,0],'actual source-qualified scan samples')
values={}
for row in q['actualInputs']:path=P.parent/row['path'];b=path.read_bytes();check(r.sha(b)==row['sha256'],'actual FE input hash');values[path.name]=b
pre='retained-00-trigger_baseline-cycle001';post='retained-02-post_fault-cycle046'
parser.logger(values[pre+'-00-R.bin'],0);parser.context(values[pre+'-01-M.bin'],values[pre+'-02-C.bin'],True)
parser.logger(values[post+'-06-R.bin'],0);parser.context(values[post+'-00-M.bin'],values[post+'-01-C.bin']);check(True,'actual FEpostfault0 context admitted')
rejects(lambda:parser.context(values[post+'-00-M.bin'],values[post+'-01-C.bin'],True))
# Source-qualified runtime C8, with the actual FH failing current C as a regression fixture.
fh=P.parent/'combined-event-trial-20261028fh/capture-01/native.receipt.json';historical=json.loads(fh.read_bytes())
current=next(c for c in historical['retained']if c['role']=='current');actual={w['name']:base64.b64decode(w['raw'])for w in current['windows']}
check(actual['C'].hex()=='70088007400b5c010000000000000000','actual FH current C8=0 fixture')
parser.context(actual['M'],actual['C']);rejects(lambda:parser.context(actual['M'],actual['C'],True))
for value in [0,1,2,3,4,5,255]:
 v=copy.deepcopy(fixture)
 # Runtime retained context and fresh cleanup may carry only positively qualified 0..4.
 for cap in v['retained']+v['controls']:
  if cap['cycle']>1 or cap['role']=='prerestore-C':
   for w in cap['windows']:
    if w['name']=='C':
     b=bytearray(base64.b64decode(w['raw']));b[8]=value;w['raw']=base64.b64encode(b).decode()
 if value<=4:check(parser.parse_native(json.dumps(v)+'\n')[0]['accepted'],'runtime positive C8 accepted '+str(value))
 else:rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
 for role in ['prearm-C','trigger-baseline']:
  initial=copy.deepcopy(fixture);cap=next(c for c in initial['controls']+initial['retained']if c['role']==role)
  w=next(w for w in cap['windows']if w['name']=='C');b=bytearray(base64.b64decode(w['raw']));b[8]=value;w['raw']=base64.b64encode(b).decode()
  if value==3:check(parser.parse_native(json.dumps(initial)+'\n')[0]['accepted'],'initial C8 three')
  else:rejects(lambda:parser.parse_native(json.dumps(initial)+'\n'))
# Reuse only mock class/helper definitions from the frozen FC suite, never its test execution.
fc=P.parent/'reader-wake-checkpoints-20261028fc/test-runner.py';source=fc.read_text().split('manifest,payload=r.build_manifest();')[0];m=types.ModuleType('fc_host_mocks');m.__file__=str(fc);exec(compile(source,str(fc),'exec'),m.__dict__)
class Mock(m.FakeRoot):
 def __init__(self,kind='success'):super().__init__(kind);self.fetch=0
 def response(self,c):
  if ' --receipt-self-test > 'in c:return m.envelope(b'{"smokeTestsPassed":8,"targetOperations":0}\n')
  if ' --execute --device 'in c:
   self.native+=1
   if self.kind=='native-ambiguous':raise OSError('mock ambiguity')
   v=copy.deepcopy(fixture)
   if self.kind=='success65':v['device']=65
   if self.kind=='unknown':v.update(accepted=False,phase='Unknown',loggerMayRemain=True)
   if self.kind=='refused-partial':
    v=copy.deepcopy(historical);v['schema']='combined-event-checkpoints-fn-v1'
   if self.kind=='wrong-limit':v['threshold']=200
   if self.kind=='late-key':
    down=v['endUs']-1;v['intervention']['endUs']=down
    for call in v['intervention']['calls']:call['beforeUs']=call['afterUs']=down
   envelope=m.envelope((json.dumps(v)+'\n').encode())
   if self.kind=='refused-partial':envelope=envelope.replace('\n1.0 2.0\n0\n','\n1.0 2.0\n1\n')
   return 'IMMEDIATE_READY\n'+envelope
  if 'echo FN_SIDECAR_BEGIN'in c:
   self.fetch+=1;value=ring if self.kind!='sidecar-corrupt'else ring[:-1]
   return 'FN_SIDECAR_BEGIN\n'+base64.b64encode(value).decode()+'\nFN_SIDECAR_END\n'
  return super().response(c)
manifest,payload=r.build_manifest();rawmanifest=r.manifest_bytes(manifest);check(rawmanifest==(P/'deployment-manifest.json').read_bytes(),'exact frozen manifest')
r.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32))
with tempfile.TemporaryDirectory(prefix='host-mock-',dir=P/'host-environment/tmp')as tmp:
 base=Path(tmp);rd=m.ready();rd['schema']='fn-combined-event-readiness-decision-v1';rd['identity'].update(devnum='60',deviceNode='/dev/bus/usb/007/060',nodeStat='bd:33b:12345');e=base/'evidence';e.write_text('SYNTHETIC NO DEVICE: explicit known queue-phase premise.');rd['evidence']=[{'path':str(e),'sha256':r.sha(e.read_bytes())}];rr=json.dumps(rd).encode();p=base/'readiness.json';p.write_bytes(rr);check(r.load_readiness(p,r.sha(rr))[0]==rd,'new readiness family')
 reference_commands=None
 for i,kind in enumerate(['success','success65','settle','late-key','native-ambiguous','unknown','wrong-limit','refused-partial','sidecar-corrupt','wake-fail','saver','POST_READY','cleanup']):
  f=Mock(kind);clock=m.Clock();out=base/str(i)
  case_rd=copy.deepcopy(rd)
  if kind in ['success65','refused-partial']:case_rd['identity'].update(devnum='65',deviceNode='/dev/bus/usb/007/065',nodeStat='bd:340:12345')
  case_rr=json.dumps(case_rd).encode()
  if kind=='success65':
   case_path=base/'readiness65.json';case_path.write_bytes(case_rr);check(r.load_readiness(case_path,r.sha(case_rr))[0]['identity']['devnum']=='65','USB65 readiness binds exact node/minor')
  if kind in ['success','success65','settle','late-key']:
   result=r.execute(out,case_rd,case_rr,rawmanifest,payload,f,parser,clock,clock.sleep);check(result['accepted']and f.native==f.ui==f.cleanup==1 and f.fetch==2,'one owner/native/key/wake/exact sidecars cleanup')
   check(result['protocolAccepted']is True and result['keyExposureQualified']is(kind!='late-key'),'wrapper preserves protocol vs exposure');check(result['keyExposure']==json.loads((out/'interpretation.json').read_bytes())['keyExposure'],'wrapper interpretation equality')
   if kind=='success':reference_commands=list(f.commands)
   if kind=='late-key':
    differences=[i for i,(a,b)in enumerate(zip(f.commands,reference_commands))if a!=b];check(len(f.commands)==len(reference_commands)and len(differences)==1 and f.commands[differences[0]].endswith('echo FINAL_INTEGRITY_OK\n'),'same commands; only dynamic native receipt integrity pin differs')
   rec=json.loads((out/'record.json').read_bytes());check(not rec['cleanup_required']and len(rec['rawRingSidecars'])==2,'sidecars enumerated');check('baseline-ring.bin'in f.commands[-1]and 'post-ring.bin'in f.commands[-1],'fixed11-file cleanup')
   line=next(c for c in f.commands[-1].splitlines()if c.startswith('rm -- '));names=[Path(z).name for z in shlex.split(line)[2:]];check(len(names)==len(set(names))==11 and set(names)==set(r.NAMES+['selftest.receipt.json','selftest.stdout','selftest.stderr','native.receipt.json','native.stdout','native.stderr','baseline-ring.bin','post-ring.bin']),'exact removal allowlist')
   nativeindex=next(i for i,c in enumerate(f.commands)if ' --execute --device 'in c);fetchindices=[i for i,c in enumerate(f.commands)if 'echo FN_SIDECAR_BEGIN'in c];check(len(fetchindices)==2 and min(fetchindices)>nativeindex,'ordinary fetch only after terminal receipt')
  else:
   rejects(lambda:r.execute(out,case_rd,case_rr,rawmanifest,payload,f,parser,clock,clock.sleep));check(f.native<=1 and f.ui<=1,'no retries')
   if kind in ['unknown','native-ambiguous','wrong-limit']:check(f.fetch==f.cleanup==0,'no fetch after unknown/malformed semantic terminal')
   if kind=='refused-partial':
    rec=json.loads((out/'record.json').read_bytes());result=json.loads((out/'result.json').read_bytes());primary=json.loads((out/'primary-native-outcome.json').read_bytes())
    check(f.fetch==f.cleanup==0 and f.commands[-1].find(' --execute --device ')>=0,'refusal makes no new root request')
    check(primary['error']==historical['error']and primary['cleanupError']==historical['cleanupError'],'primary refusal retained before empty post-ring')
    check(primary['terminalKnownPhase']and primary['released']and primary['closed']and primary['loggerMayRemain']and not primary['accepted'],'known lifecycle never promotes refusal')
    check(rec['native_invocations_status']=='one_completed'and rec['target_operations_status']=='native_refused'and rec['target_operations']==158 and rec['cleanup_required'],'refused receipt replaces generic inflight status')
    check(result['error']==historical['error']and result['accepted']is False and result['protocolAccepted']is False and result['loggerMayRemain']is True,'failed wrapper result truthfully retains cause/restoration')
   if kind=='wrong-limit':
    rec=json.loads((out/'record.json').read_bytes());check(rec['target_operations_status']=='native_receipt_unparsed'and rec['native_invocations_status']=='terminal_receipt_retained','malformed terminal still retained distinctly from inflight')
   if kind=='sidecar-corrupt':check(f.cleanup==0,'corrupt ordinary fetch retains stage')
  for c in f.commands:
   check(len(c.encode())<=8192,'command bound');check(subprocess.run(['sh','-n'],input=c.encode(),capture_output=True).returncode==0,'shell syntax')
 check(max(len(c.encode())for c in m.commands)<=8192,'all mock command maxima')
summary={'checks':checks,'shellCommands':len(m.commands),'maxCommandBytes':max(map(lambda c:len(c.encode()),m.commands)),'targetOperations':0,'maxRootResponseBytes':57348+1500,'sidecarResponseUpperBound':21000,'receiptBytes':len(raw)}
print(json.dumps(summary,sort_keys=True))
