#!/usr/bin/env python3
"""Focused FZ81 parser/cap/partial/envelope/mock-wrapper tests; zero target I/O."""
import base64,copy,hashlib,json,subprocess,tempfile,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def check(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def rejects(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'refusal');return
 raise ValueError('unexpected acceptance')
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
r=load(P/'run-once.py');parser=load(P/'parse-result.py');old=load(B/'combined-event-successor-20261028fn/parse-result.py');f=json.loads((P/'fixture.json').read_bytes());native,rows,i=parser.parse_native((P/'fixture.json').read_text())
check(f['accepted']and len(rows)==81 and (f['headers'],f['inputs'],f['bulks'],f['writes'])==(660,658,1320,2),'constructive81 exact accounting')
check(len(base64.b64decode(f['rows']['rawBase64']))==4698 and len(f['rows']['rawBase64'])==6264,'81 allocated row extent')
rejects(lambda:old.parse_native((P/'fixture.json').read_text()))
v=copy.deepcopy(f);v['schema']='combined-event-checkpoints-fn-v1';v['rows']['schema']='fg-stockevent-checkpoints-v1';rejects(lambda:old.parse_native(json.dumps(v)+'\n'))
rejects(lambda:parser.parse_native((B/'combined-event-successor-20261028fn/fixture.json').read_text()))
for key,maximum in {'headers':660,'inputs':658,'bulks':1320,'writes':2,'cyclesStarted':81,'cleanCycles':81,'quiescentCycles':81}.items():
 for value in [maximum+1,True,-1]:
  v=copy.deepcopy(f);v[key]=value;rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
for pos in range(58):
 v=copy.deepcopy(f);raw=bytearray(base64.b64decode(v['rows']['rawBase64']));raw[pos]^=1;v['rows']['rawBase64']=base64.b64encode(raw).decode();v['rows']['sha256']=sha(raw);rejects(lambda:parser.parse_native(json.dumps(v)+'\n'))
for name in ['time-fixture.json','partial-fixture.json']:
 v=parser.parse_native((P/name).read_text())[0]
 if name.startswith('time-'):check(v['accepted']and v['terminal']=='TimeLimit'and 56<v['rows']['count']<81,'normal clock TimeLimit extends cap without duration increase')
 else:check(not v['accepted']and v['terminal']=='TimeLimitedPartial'and v['restore']=='readback-zero','partial remains refused after successful restoration')
qualification=json.loads((P/'native-tests.json').read_bytes());check(qualification['maxRows']==81 and qualification['maxReceiptBytes']<24576,'native constructive maximum')
# Reuse only frozen FC mock definitions. Never load its live transport or execute its test suite.
fc=B/'reader-wake-checkpoints-20261028fc/test-runner.py';source=fc.read_text().split('manifest,payload=r.build_manifest();')[0];m=types.ModuleType('fc_mock_definitions');m.__file__=str(fc);exec(compile(source,str(fc),'exec'),m.__dict__)
ring=bytearray(15372);ring[:2]=(4).to_bytes(2,'little');ring[12]=7;ring=bytes(ring)
class Mock(m.FakeRoot):
 def __init__(self,kind='success'):super().__init__(kind);self.fetch=0
 def response(self,c):
  if ' --receipt-self-test > 'in c:return m.envelope(b'{"smokeTestsPassed":8,"targetOperations":0}\n')
  if ' --execute --device 'in c:
   self.native+=1;raw=(P/('partial-fixture.json'if self.kind=='partial'else'fixture.json')).read_bytes();text=m.envelope(raw)
   if self.kind=='partial':text=text.replace('\n1.0 2.0\n0\n','\n1.0 2.0\n1\n')
   return 'IMMEDIATE_READY\n'+text
  if 'echo FN_SIDECAR_BEGIN'in c:self.fetch+=1;return 'FN_SIDECAR_BEGIN\n'+base64.b64encode(ring).decode()+'\nFN_SIDECAR_END\n'
  return super().response(c)
manifest,payload=r.build_manifest();raw_manifest=r.manifest_bytes(manifest);check(raw_manifest==(P/'deployment-manifest.json').read_bytes(),'frozen manifest')
r.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='b'*32))
with tempfile.TemporaryDirectory(dir=P/'host-environment/tmp',prefix='fz-')as td:
 base=Path(td);rd=m.ready();rd['schema']='fz-combined-event-81-readiness-decision-v1';rd['identity'].update(devnum='60',deviceNode='/dev/bus/usb/007/060',nodeStat='bd:33b:12345');e=base/'premise';e.write_text('SYNTHETIC NO TARGET: explicit known phase premise only.');rd['evidence']=[{'path':str(e),'sha256':sha(e.read_bytes())}];rb=json.dumps(rd).encode();rp=base/'readiness.json';rp.write_bytes(rb);check(r.load_readiness(rp,sha(rb))[0]==rd,'unique readiness family')
 for kind in ['success','partial','wrong-tab']:
  root=Mock(kind);clock=m.Clock();out=base/kind
  if kind=='success':
   result=r.execute(out,rd,rb,raw_manifest,payload,root,parser,clock,clock.sleep);check(result['accepted']and result['rows']==81 and result['headers']==660 and result['bulks']==1320,'full wrapper81 acceptance');check(root.native==root.ui==root.cleanup==1 and root.fetch==2,'one native/wake/no retries/exactcleanup')
  else:
   rejects(lambda:r.execute(out,rd,rb,raw_manifest,payload,root,parser,clock,clock.sleep));check(root.cleanup==root.fetch==0,'refusal no follow-up/cleanup')
   if kind=='partial':check(root.native==1 and ' --execute --device 'in root.commands[-1]and json.loads((out/'result.json').read_bytes())['terminal']=='TimeLimitedPartial','truthful primary partial refusal retained')
   else:check(root.native==0,'wrong tab before native')
 for raw in [(P/'fixture.json').read_bytes(),b'x'*qualification['maxReceiptBytes'],b'x'*24576]:
  envelope=m.envelope(raw);terminal,receipt,stdout,stderr=r.receipt_envelope(envelope);check(receipt==raw and len(envelope.encode())<65536,'actual/stress/full-cap receipt envelope')
 # Construct every allowed semantic file cap simultaneously, independent of actual GC output.
 vals=[b'x'*24576,b'y'*16384,b'z'*2048];envelope='DPMETA_BEGIN\n'+r.BOOT+'\n1.0 2.0\n0\n'
 for value in vals:envelope+=str(len(value))+'\n'+sha(value)+'\n'
 envelope+='DPMETA_END\n'
 for label,value in zip(['RECEIPT','STDOUT','STDERR'],vals):envelope+=label+'_B64_BEGIN\n'+base64.b64encode(value).decode()+'\n'+label+'_B64_END\n'
 envelope+='DPRUN_COMPLETE\n';check(len(envelope.encode())<=65536 and r.receipt_envelope(envelope)[1:]==tuple(vals),'all semantic caps fit root envelope')
print(json.dumps({'schema':'fz-host-tests-v1','checks':checks,'nativeQualification':qualification,'wrapperCases':3,'mockCommands':len(m.commands),'maxCommandBytes':max(len(c.encode())for c in m.commands),'maximumSemanticEnvelopeBytes':len(envelope.encode()),'targetOperations':0},sort_keys=True))
