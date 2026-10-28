#!/usr/bin/env python3
"""Read-only frozen FN host review. Writes only this reviews subtree."""
import base64,copy,hashlib,json,os,pathlib,runpy,subprocess,sys,tempfile,types
R=pathlib.Path(__file__).resolve().parent;P=R.parent;B=P.parent;A=R/'artifacts';checks=0
def check(v,m):
 global checks
 checks+=1
 if not v:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def refuse(f):
 try:f()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'rejected');return
 raise ValueError('unexpected acceptance')
if len(sys.argv)==3 and sys.argv[1]=='--suite':
 # The unmodified author suite explicitly supplies its own temporary directory;
 # reroute only temporary storage into this owned review subtree.
 original=tempfile.TemporaryDirectory
 def redirected(*args,**kwargs):kwargs['dir']=str(A/'tmp');return original(*args,**kwargs)
 tempfile.TemporaryDirectory=redirected
 sys.argv=[str(P/sys.argv[2])];runpy.run_path(sys.argv[0],run_name='__main__');raise SystemExit(0)
expected={'deployment-manifest.json':'44ddd0699a59329ced1290a0570e791672004b4aa7875e4d203ad0621bc0f7ce','source-inventory.json':'cda3b1936cab9127ab221e08c588c9e11ecb3628938b0dfd8da84daeec39afc3','qualification.json':'4c7d9e054547c7d8c0936e6259b2f57aa3797ac8f26b0a2c183c6d2039784df6','parse-result.py':'d222a8830f222bd0643b2e86bf4b47e2397258cd6cdae62e0b93141b2be7d78d','run-once.py':'85fbe055b5b9b2331b68c0710d7814d5ceee599b2649b70104dfb37bcd5e8cf0','bin/Release/net6.0/CombinedEventSuccessor.dll':'1628ccfc09d761707a0241e9e3b66a03b85a85470dbef4c93d6758bd634ad9b2'}
for n,h in expected.items():check(sha((P/n).read_bytes())==h,'frozen pin '+n)
inventory=json.loads((P/'source-inventory.json').read_text())['files']
for e in inventory:
 b=(P/e['path']).read_bytes();check(len(b)==e['bytes']and sha(b)==e['sha256'],'inventory '+e['path'])
inputs=json.loads((P/'input-pins.json').read_text())['files']
for e in inputs:
 b=(B/e['path']).read_bytes();check(len(b)==e['bytes']and sha(b)==e['sha256'],'input '+e['path'])
w=load(P/'run-once.py');parser=load(P/'parse-result.py');manifest,payload=w.build_manifest();check(w.manifest_bytes(manifest)==(P/'deployment-manifest.json').read_bytes(),'rebuilt manifest exact')
G=B/'combined-event-checkpoints-20261028fg'
for n in ['NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','wake-check.py']:check((P/n).read_bytes()==(G/n).read_bytes(),'byte-identical '+n)
old=(G/'Protocol.cs').read_text();new=(P/'Protocol.cs').read_text();start='    static PairResult ReadPair(';end='    static PairResult ReadSet(';check(old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)],'full ReadPair exact')
old=(G/'Engine.cs').read_text();new=(P/'Engine.cs').read_text();start=' static PairResult WriteLogger(';end=' static bool RingRead(';check(old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)],'full write/clock/budget exact')
for token in ['const long PairBudgetUs=4_000_000, MarginUs=2_000_000, CleanupReserveUs=6*PairBudgetUs+MarginUs, KeyJoinReserveUs=7_000_000, WholeBudgetUs=40_000_000','phase==ProtocolPhase.ReadyForHeader&&!clockLost&&o.Error==null','x.Current.Windows[2].Buffer[8]==3','c[8]<=4&&(!initial||c[8]==3)']:check(token in new,'source invariant')
check(new.index('x.Current.Windows[2].Buffer[8]==3')<new.index('key?.Start(clock)'),'first-C8 check precedes sole key start')
check(new.index('LoggerR(after,0);x.Restore=gate==1?')>new.index('else x.Restore="observed-zero-unverified"'),'zero finalization after checked readback')
old=(G/'parse-result.py').read_text();new=(P/'parse-result.py').read_text();start='def key_exposure(';end='def parse_native(';check(old[old.index(start):old.index(end)]==new[new.index(start):new.index(end)],'full key qualifier exact')
source=(P/'run-once.py').read_text();check(source.index("if native['accepted']is not True")<source.index("for name,label in [('baseline-ring.bin'"),'primary refusal before sidecar root calls')
fh=json.loads((B/'combined-event-trial-20261028fh/capture-01/native.receipt.json').read_text());cur=next(c for c in fh['retained']if c['role']=='current');actual={v['name']:base64.b64decode(v['raw'])for v in cur['windows']};check(actual['C'].hex()=='70088007400b5c010000000000000000','FH exact current context')
for initial in [False,True]:
 for c8 in range(256):
  c=bytearray(actual['C']);c[8]=c8
  if c8==(3 if initial else c8)and(initial and c8==3 or not initial and c8<=4):parser.context(actual['M'],c,initial);check(True,'positive finite C8')
  else:refuse(lambda:parser.context(actual['M'],c,initial))
for kind in ['root','AA','AC','scan','height','width','packed','category','C7']:
 m=bytearray(actual['M']);c=bytearray(actual['C'])
 if kind=='root':m[64]^=1
 elif kind=='AA':m[10]=1
 elif kind=='AC':m[12]=1
 elif kind=='scan':m[56]=2
 elif kind in ['height','width','packed']:c[{'height':0,'width':2,'packed':4}[kind]]^=1
 elif kind=='category':c[6]^=1
 else:c[7]=2
 refuse(lambda:parser.context(m,c))
v=json.loads((P/'fixture.json').read_text());parser.parse_native(json.dumps(v)+'\n');check(True,'accepted fixed40 fixture')
for role in ['prearm-C','trigger-baseline','last-complete','current','prerestore-C']:
 for c8 in [0,1,2,3,4,5,255]:
  z=copy.deepcopy(v);c=next(c for c in z['controls']+z['retained']if c['role']==role);win=next(x for x in c['windows']if x['name']=='C');b=bytearray(base64.b64decode(win['raw']));b[8]=c8;win['raw']=base64.b64encode(b).decode()
  allowed=c8==3 if role in ['prearm-C','trigger-baseline']else c8<=4
  if allowed:check(parser.parse_native(json.dumps(z)+'\n')[0]['accepted'],'staged context admitted')
  else:refuse(lambda:parser.parse_native(json.dumps(z)+'\n'))
historical=copy.deepcopy(fh);historical['schema']='combined-event-checkpoints-fn-v1';n,_,i=parser.parse_native(json.dumps(historical)+'\n');check(n['accepted']is False and i['protocolAccepted']is False and i['terminalKnownPhase']is True and n['loggerMayRemain']is True,'actual FH refusal never promoted')
dry=subprocess.run([sys.executable,'-B',str(P/'run-once.py')],check=True,capture_output=True,text=True);check(json.loads(dry.stdout)['targetOperations']==0,'dry no target')
env=dict(os.environ,DOTNET_CLI_HOME=str(A/'sdk-home'),TMPDIR=str(A/'tmp'),NUGET_PACKAGES=str(A/'nuget'),DOTNET_NOLOGO='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',PYTHONDONTWRITEBYTECODE='1')
sdk='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet';native=subprocess.run([sdk,str(P/'bin/Release/net6.0/CombinedEventSuccessor.dll'),'--self-test'],check=True,capture_output=True,env=env,timeout=60)
(A/'native-tests.json').write_bytes(native.stdout);check(not native.stderr and json.loads(native.stdout)==json.loads((P/'native-tests.json').read_bytes()),'native suite byte-semantics match frozen')
suites={}
for script in ['verify-source.py','qualify-context.py','qualify-scan.py','test-key-exposure.py','test-host.py']:
 outputs=[]
 for optimized in [False,True]:
  command=[sys.executable,'-B']+(['-O']if optimized else[])+[str(__file__),'--suite',script]
  result=subprocess.run(command,check=True,capture_output=True,env=env,timeout=90);check(not result.stderr,'suite stderr');obj=json.loads(result.stdout);outputs.append(result.stdout);(A/(script+('.optimized.json'if optimized else'.normal.json'))).write_bytes(result.stdout)
 check(outputs[0]==outputs[1],'normal optimized parity '+script);suites[script]=json.loads(outputs[0])
# One bounded fresh mock uses every actual saved USB65 identity string, rather
# than just substituting devnum into the shorter synthetic identity.
mock_source=(P/'test-host.py').read_text().split('\nmanifest,payload=r.build_manifest();',1)[0]
host=types.ModuleType('fn_actual_identity_mock');host.__file__=str(P/'test-host.py');exec(compile(mock_source,host.__file__,'exec'),host.__dict__)
saved=json.loads((B/'combined-event-trial-20261028fh/capture-01/readiness-decision.json').read_text())
identity=saved['identity'];check(identity['devnum']=='65','retained actual identity65')
w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='b'*32));actual_commands=[]
with tempfile.TemporaryDirectory(prefix='actual-identity65-',dir=A/'tmp')as tmp:
 base=pathlib.Path(tmp);rd=host.m.ready();rd['schema']='fn-combined-event-readiness-decision-v1';rd['identity']=identity
 phase=base/'host-phase.txt';phase.write_text('SYNTHETIC HOST-ONLY TEST using retained identity strings; no current queue or device assertion.')
 rd['evidence']=[{'path':str(phase),'sha256':sha(phase.read_bytes())}];rb=json.dumps(rd).encode();rp=base/'readiness.json';rp.write_bytes(rb);w.load_readiness(rp,sha(rb));check(True,'actual identity readiness parses')
 for kind in ['success65','refused-partial']:
  root=host.Mock(kind);clock=host.m.Clock();out=base/kind
  if kind=='success65':
   result=w.execute(out,rd,rb,w.manifest_bytes(manifest),payload,root,parser,clock,clock.sleep);check(result['accepted']and root.native==root.ui==root.cleanup==1 and root.fetch==2,'accepted actual identity65 mock')
   remove=next(line for line in root.commands[-1].splitlines()if line.startswith('rm -- '));check(len(remove.split())-2==11,'exact eleven cleanup files')
  else:
   refuse(lambda:w.execute(out,rd,rb,w.manifest_bytes(manifest),payload,root,parser,clock,clock.sleep));primary=json.loads((out/'primary-native-outcome.json').read_text());check(root.fetch==root.cleanup==0 and ' --execute --device 65 'in root.commands[-1],'actual refusal stops root requests at invocation');check(primary['error']==fh['error']and primary['accepted']is False and primary['loggerMayRemain']is True,'original semantic error remains primary')
  actual_commands.extend(root.commands)
  for c in root.commands:check(len(c.encode())<=8192 and subprocess.run(['sh','-n'],input=c.encode(),capture_output=True).returncode==0,'actual identity command syntax/cap')
actual={'identitySourceSha256':sha((B/'combined-event-trial-20261028fh/capture-01/readiness-decision.json').read_bytes()),'commands':len(actual_commands),'maxCommandBytes':max(len(c.encode())for c in actual_commands),'acceptedAndRefusedCases':2,'targetOperations':0}
for e in inventory:
 b=(P/e['path']).read_bytes();check(len(b)==e['bytes']and sha(b)==e['sha256'],'unchanged after review '+e['path'])
report={'schema':'fn-independent-review-validation-v1','accepted':True,'checks':checks,'frozenPins':expected,'inventoryFiles':len(inventory),'inputFiles':len(inputs),'native':json.loads(native.stdout),'suites':suites,'actualIdentity65Mock':actual,'targetOperations':0,'rootCalls':0,'networkOperations':0,'wroteOnlyReviews':True,'limitation':'Host qualification and source-equivalence only; sampled producer/key/UI/physical activity is not established.'}
(R/'independent-validation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'accepted':True,'checks':checks,'inventoryFiles':len(inventory),'inputFiles':len(inputs),'nativeChecks':report['native']['selfTestsPassed'],'wrapperChecks':suites['test-host.py']['checks'],'commands':suites['test-host.py']['shellCommands'],'maxCommandBytes':suites['test-host.py']['maxCommandBytes'],'targetOperations':0},sort_keys=True))
