#!/usr/bin/env python3
"""Focused FM changed-contract checks and mocked wrapper lifecycle; no target."""
import base64,copy,hashlib,json,pathlib,shlex,subprocess,tempfile,types
P=pathlib.Path(__file__).resolve().parent;B=P.parent;checks=0
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def check(v,m):
 global checks
 checks+=1
 if not v:raise ValueError(m)
def refuse(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'refusal');return
 raise ValueError('unexpected acceptance')
r=load(P/'run-once.py');parser=load(P/'parse-result.py')
old=(B/'combined-event-checkpoints-20261028fg/NativeBinding.cs').read_text()
expected=old.replace('(data[0]==0||data[0]==1)','data[0]==0').replace('(data.Length==256&&length!=Ring.Length||data.Length==Ring.Length&&length==Ring.Length)','data.Length==256')
check((P/'NativeBinding.cs').read_text()==expected,'native binding exact except narrower fixed whitelist')
old=(B/'combined-event-checkpoints-20261028fg/Protocol.cs').read_text();new=(P/'Protocol.cs').read_text()
for start,end in [('    static PairResult ReadPair(', '    static PairResult ReadSet('),('    static long? Stamp(', '    static PairResult ReadPair('),('    static byte[] ReadCachedDescriptors(Stream','    sealed class FakeClock')]:check(old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)],'inherited source '+start)
check('static readonly WindowSpec[] AllSpecs = { R, M, C };'in new and 'WindowSpec Ring ='not in new,'three fixed reads')
e=(P/'Engine.cs').read_text();check('LoggerOffPayload={0,0}'in e and 'LoggerOnPayload'not in e and 'key'not in e.lower(),'restore only no key')
check('c[8]==0||c[8]==3'in e,'finite restore-only C8')
for row in json.loads((P/'input-pins.json').read_text())['files']:
 b=(B/row['path']).read_bytes();check(len(b)==row['bytes']and r.sha(b)==row['sha256'],'input hash')
fl=json.loads((B/'logger-context-transient-20261028fl/source-audit.json').read_text());check(fl['checks']==103 and fl['global_value_domain_complete']is False and fl['fresh_arm_or_readiness_widening_supported']is False,'FL finite qualification')
for row in json.loads((B/'logger-context-transient-20261028fl/source-inventory.json').read_text())['files']:
 b=(B/'logger-context-transient-20261028fl'/row['path']).read_bytes();check(len(b)==row['bytes']and r.sha(b)==row['sha256'],'FL frozen inventory')
premise={'accepted':True,'phase':'ReadyForHeader','released':True,'closed':True,'priorNativeAccepted':False,'loggerOriginallyZero':True,'loggerMayRemainOne':True,'proofPath':str(r.PHASE_PROOF),'proofSha256':r.PHASE_PROOF_SHA}
check(r.validate_restore_premise(premise)['headers']==158,'actual FH independent proof + all inputs')
for k in premise:
 v=copy.deepcopy(premise);v[k]=not v[k]if type(v[k])is bool else'bad';refuse(lambda:r.validate_restore_premise(v))
v=json.loads((P/'fixture.json').read_text());check(parser.parse_native(json.dumps(v))[2]['restoredOriginalZero'],'restored fixture')
already=copy.deepcopy(v);already.update(restore='already-zero-no-write',restoreAttempted=False,headers=4,bulks=8,writes=0);already['retained']=[c for c in already['retained']if c['role']!='restore']
w=already['retained'][2]['windows'][0];b=bytearray(base64.b64decode(w['rawBase64']));b[6:8]=b'\0\0';w['rawBase64']=base64.b64encode(b).decode();w['sha256']=r.sha(b)
check(parser.parse_native(json.dumps(already))[0]['writes']==0,'already zero distinct')
for k in v:
 if k=='retained':continue
 changed=copy.deepcopy(v)
 if type(changed[k])is bool:changed[k]=not changed[k]
 elif type(changed[k])is int:changed[k]='invalid'
 else:changed[k]='bad'
 refuse(lambda:parser.parse_native(json.dumps(changed)))
for i,cap in enumerate(v['retained']):
 for j,t in enumerate(cap['transfers']):
  for field in ['count','beforeUs','errno']:
   z=copy.deepcopy(v);z['retained'][i]['transfers'][j][field]=-1;refuse(lambda:parser.parse_native(json.dumps(z)))
 for j,w in enumerate(cap['windows']):
  z=copy.deepcopy(v);z['retained'][i]['windows'][j]['sha256']='a'*64;refuse(lambda:parser.parse_native(json.dumps(z)))
for subtype in [0,3,1,2,4,255]:
 z=copy.deepcopy(v);w=z['retained'][1]['windows'][0];b=bytearray(base64.b64decode(w['rawBase64']));b[8]=subtype;w.update(rawBase64=base64.b64encode(b).decode(),sha256=r.sha(b))
 if subtype in [0,3]:check(parser.parse_native(json.dumps(z))[0]['accepted'],'finite subtype admitted')
 else:refuse(lambda:parser.parse_native(json.dumps(z)))
fc=B/'reader-wake-checkpoints-20261028fc/test-runner.py';s=fc.read_text().split('manifest,payload=r.build_manifest();')[0];m=types.ModuleType('frozen_host_mocks');m.__file__=str(fc);exec(compile(s,str(fc),'exec'),m.__dict__)
class Mock(m.FakeRoot):
 def response(self,c):
  check('input_keyevent'not in c and 'enlightenment_info'not in c and 'baseline-ring.bin'not in c and 'post-ring.bin'not in c,'no UI/ring')
  if ' --receipt-self-test > 'in c:return m.envelope((P/'native-tests.json').read_bytes())
  if ' --execute --device 'in c:
   self.native+=1
   if self.kind=='native-ambiguous':raise OSError('ambiguous')
   raw=copy.deepcopy(already if self.kind=='already'else v)
   if self.kind=='wrong-device':raw['device']=64
   if self.kind=='unknown':raw.update(accepted=False,phase='Unknown')
   return 'IMMEDIATE_READY\n'+m.envelope((json.dumps(raw)+'\n').encode())
  return super().response(c)
manifest,payload=r.build_manifest();rm=r.manifest_bytes(manifest);check(rm==(P/'deployment-manifest.json').read_bytes(),'manifest exact')
r.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32))
with tempfile.TemporaryDirectory(prefix='fm-host-',dir=P/'host-environment/tmp')as tmp:
 p=pathlib.Path(tmp);rd=m.ready();rd.update(schema='fm-logger-reconciliation-readiness-decision-v1',restoreOnlyPremise=premise);rd['identity']=json.loads((r.PHASE_PROOF.parent.parent/'capture-01/readiness-decision.json').read_text())['identity'];e=p/'evidence';e.write_text('SYNTHETIC HOST ONLY; no live device or queue premise.');rd['evidence']=[{'path':str(e),'sha256':r.sha(e.read_bytes())}];raw=json.dumps(rd).encode();rp=p/'readiness.json';rp.write_bytes(raw);check(r.load_readiness(rp,r.sha(raw))[0]==rd,'FM readiness exact')
 for k in ['restoreOnlyPremise','identity','endpointQueueProof']:
  z=copy.deepcopy(rd);z.pop(k);rp.write_text(json.dumps(z));refuse(lambda:r.load_readiness(rp,r.sha(rp.read_bytes())))
 for kind in ['success','already','native-ambiguous','unknown','wrong-device','PRE_READY','BEFORE_INVOKE_READY','POST_READY','cleanup']:
  a=Mock(kind);out=p/kind
  if kind in ['success','already']:
   result=r.execute(out,rd,raw,rm,payload,a,parser);check(result['accepted']and a.native==a.cleanup==1 and a.ui==0,'one invocation no UI cleanup');check(result['loggerPayloads']==(0 if kind=='already'else 1),'payload count');check(result['originalFgStageTouched']is False,'old stage separate')
   line=next(x for x in a.commands[-1].splitlines()if x.startswith('rm -- '));names=[pathlib.Path(x).name for x in shlex.split(line)[2:]];check(len(names)==len(set(names))==9,'exact nine files');check(all('/tmp/researcher-fm-'in x for x in shlex.split(line)[2:]),'cleanup newstage only')
  else:
   refuse(lambda:r.execute(out,rd,raw,rm,payload,a,parser));check(a.native<=1 and a.ui==0,'no retries/UI');check(json.loads((out/'record.json').read_text())['cleanup_required']is True,'refusal retains')
   if kind in ['native-ambiguous','unknown','wrong-device']:check(a.cleanup==0,'no cleanup after native ambiguity/refusal')
 for command in m.commands:check(len(command.encode())<=8192 and subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'bounded shell')
for text in [m.envelope(b'{}')+'x',m.envelope(b'x'*24577)]:refuse(lambda:r.receipt_envelope(text))
native=json.loads((P/'native-tests.json').read_text());check(native=={'schema':'fm-host-tests-v1','checks':406,'cases':72,'targetOperations':0,'restoreOnly':True},'native qualification')
check(json.loads(subprocess.check_output(['python3','-B',str(P/'run-once.py')]))['wrapperUiOperations']==0,'dry no target')
print(json.dumps({'schema':'fm-host-validation-v1','checks':checks,'nativeChecks':native['checks'],'nativeCases':native['cases'],'shellCommands':len(m.commands),'maxCommandBytes':max(len(c.encode())for c in m.commands),'targetOperations':0,'rootCalls':0,'networkOperations':0,'receiptBytes':len((P/'fixture.json').read_bytes())},sort_keys=True))
