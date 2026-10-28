#!/usr/bin/env python3
"""GH independent frozen-source/semantic review: pure host replays only."""
import base64,contextlib,copy,hashlib,io,json,subprocess,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;P=OUT.parent;B=P.parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
checks=0;pins={}
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def pin(path):
 raw=path.read_bytes();pins[str(path.relative_to(B))]={'bytes':len(raw),'sha256':sha(raw)};return raw
def frozen():
 raw=pin(P/'source-inventory.json');ck(sha(raw)=='4851689c1497e2efbf89cf4d18fcf1fe7586d444b2b5c3611aeb0c0c2f744356','author inventory pin')
 for item in json.loads(raw)['files']:
  data=pin(P/item['path']);ck(len(data)==item['bytes']and sha(data)==item['sha256'],'frozen file '+item['path'])
 ck(sha(pin(P/'deployment-manifest.json'))=='2dbaadd1a9bedd99827b0b7d51cbeb161285085d2bf9de1bb8c54704b1ba537e','manifest pin')
def suite(name):
 ns={'__file__':str(P/name),'__name__':'reviewed_host_suite'};capture=io.StringIO()
 with contextlib.redirect_stdout(capture):exec(compile(pin(P/name),str(P/name),'exec'),ns)
 return json.loads(capture.getvalue()),ns
# Every nested admission/readiness temporary directory stays under this review.
TD=tempfile.TemporaryDirectory
def private_tmp(*args,**kwargs):
 kwargs['dir']=OUT/'tmp';return TD(*args,**kwargs)
tempfile.TemporaryDirectory=private_tmp
frozen()
source,_=suite('verify-source.py');host,ns=suite('test-host.py')
w=ns['w'];policy=ns['policy'];admit=ns['admit'];eb=policy.wrapper();parser=policy.load(policy.EB/'parse-result.py',policy.EB_PARSER_SHA,'gh_independent_eb_parser')
identity_path=B/'live-saver-wake-trial-20261028gf/after-recovery-identity/identity.json'
identity=json.loads(pin(identity_path));ck(len(identity)==16 and identity['devnum']=='67','retained authoritative identity67')
# Construct a full synthetic accepted EB ledger at 200/device67 from the author's
# counterfactual200/device66 fixture. This is NOT actual device67 fault evidence.
with TD(prefix='gh-review-',dir=OUT/'tmp')as td:
 root=Path(td);base=ns['cap'];native=eb.strict_json((base/'native.receipt.json').read_bytes());native['device']=67
 receipt=(json.dumps(native,separators=(',',':'))+'\n').encode();parser.parse_native(receipt.decode())
 ready=eb.strict_json((base/'readiness-decision.json').read_bytes());ready['identity']=identity
 note=root/'synthetic-phase.txt';note.write_text('SYNTHETIC HOST ONLY: counterfactual Fault200/device67 EB replay. Not an actual current fault, queue proof, readiness decision, target admission or recovery outcome. Uses retained identity facts only.')
 ready['closedWorldVendorOutLineage']={'accepted':True,'statement':note.read_text(),'evidenceSha256':sha(note.read_bytes())};ready['evidence']=[{'path':str(note),'sha256':sha(note.read_bytes())}]
 ready_raw=(json.dumps(ready,indent=2,sort_keys=True)+'\n').encode()
 ledger=eb.strict_json((base/'record.json').read_bytes())['calls'];rendered=[]
 class SyntheticEb67:
  position=0
  def root(self,command,record,path):
   c=copy.deepcopy(ledger[self.position]);self.position+=1;stdout=policy.call_stdout(c)
   if stdout.startswith('IMMEDIATE_READY\nEBMETA_BEGIN\n'):
    terminal,old,output,error=eb.receipt_envelope(stdout[len('IMMEDIATE_READY\n'):]);blobs=[receipt,output,error]
    stdout='IMMEDIATE_READY\nEBMETA_BEGIN\n'+terminal['boot']+'\n'+terminal['uptime']+'\n'+str(terminal['exit_code'])+'\n'
    for blob in blobs:stdout+=str(len(blob))+'\n'+sha(blob)+'\n'
    stdout+='EBMETA_END\n'
    for label,blob in zip(['RECEIPT','STDOUT','STDERR'],blobs):stdout+=label+'_B64_BEGIN\n'+base64.b64encode(blob).decode()+'\n'+label+'_B64_END\n'
    stdout+='EBRUN_COMPLETE\n'
   c['command']=command;c['command_bytes']=len(command.encode());c['response']['commands'][0].update(command=command,stdout=stdout)
   c['transport_stdout']={'encoding':'base64','data':base64.b64encode(json.dumps(c['response'],separators=(',',':')).encode()).decode()}
   policy.call_stdout(c);record['calls'].append(c);eb.save(path,record);rendered.append(command);return stdout
 mock=SyntheticEb67();eb.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='c'*32));manifest,payload=eb.build_manifest();cap=root/'COUNTERFACTUAL-FAULT200-USB67'
 result=eb.execute(cap,ready,ready_raw,eb.manifest_bytes(manifest),payload,mock,parser)
 ck(mock.position==28 and result['accepted'],'complete synthetic67 source ledger')
 proof=admit.admit(cap,sha((cap/'result.json').read_bytes()),identity)
 ck(proof['exactRootCommandsReplayed']==28 and len(proof['files'])==32,'all32 synthetic artifacts and28 source requests admitted')
 ck(proof['stableFault200Logger0']and proof['phase']=='ReadyForHeader'and proof['sameInstance'],'strict source interpretation')
 # Full CLI sequencing with the real pure admissions; only the final root loader
 # is substituted, and all helper calls are the unchanged finite Mock implementation.
 ghready=copy.deepcopy(ready);ghready['schema']='gh-fault200-apps-recovery-readiness-decision-v1';rp=root/'readiness.json';w.save(rp,ghready)
 cli_identity=w.load_readiness(rp,sha(rp.read_bytes()))[0]['identity'];ck(cli_identity==identity,'all16 current retained identity fields')
 ghmanifest,ghpayload=w.build_manifest();manifest_raw=w.manifest_bytes(ghmanifest)
 adapter=ns['Mock']();adapter.REMOTE_TIMEOUT_SECONDS=45;adapter.HOST_TIMEOUT_SECONDS=75;adapter.MAX_COMMAND=8192;adapter.MAX_RESPONSE=65536;root_imports=[];oldload=w.load;oldargv=sys.argv
 def mock_load(path,digest,name):
  if path==w.ROOT:
   ck(sha(path.read_bytes())==digest,'real adapter source identity checked but not imported');root_imports.append(path);return adapter
  if path==P/'helper.py':return ns['h']
  return oldload(path,digest,name)
 w.load=mock_load
 try:
  sys.argv=[str(P/'run-once.py'),'--execute','--manifest-sha256',sha(manifest_raw),'--capture',str(cap),'--capture-result-sha256',sha((cap/'result.json').read_bytes()),'--readiness',str(rp),'--readiness-sha256',sha(rp.read_bytes()),'--output',str(root/'mock-recovery')]
  output=io.StringIO()
  with contextlib.redirect_stdout(output):w.main()
  final=json.loads(output.getvalue());ck(final['accepted']and adapter.native==adapter.cleanup==1,'single mocked helper lifecycle')
  ck(root_imports==[w.ROOT],'only one final adapter load after admission')
  ck(final['nativeTerminalAccepted']and final['helperCleanupConfirmed']and final['postCachedContextQualified'],'success fields independent')
  ck(not any(final[k]for k in ['newInstanceQualified','freshEbBaselineQualified','initializationPrerequisiteQualified','mode2Under200ProfileEmpiricallyQualified','restoresLimit40Proven']),'no recovery/parent postconditions invented')
  ck(adapter.snapshots==3 and adapter.publics==2,'initial/poststage Apps and final postcontext separately queried')
  ck(final['wrapperUiOperations']==final['thresholdWrites']==final['vendorReads']==final['automaticRetries']==0,'no added actions')
 finally:w.load=oldload;sys.argv=oldargv
 commands=rendered+adapter.commands
 for c in commands:
  ck(len(c.encode())<=8192 and subprocess.run(['sh','-n'],input=c.encode(),capture_output=True).returncode==0,'actual67 command cap/syntax')
  ck('input_keyevent'not in c and '--set-limit'not in c and '--restore-limit'not in c,'no keys/threshold route')
 identity_commands=[c for c in adapter.commands if 'GH_INITIAL_READY'in c or 'GH_BEFORE_NATIVE'in c]
 ck(len(identity_commands)==2,'same instance at both helper identity checkpoints')
 for c in identity_commands:ck(all(v in c for v in [identity['deviceNode'],identity['sysfsStat'],identity['nodeStat'],identity['sysfsRealpath'],identity['descriptorsSha256']]),'actual67 filesystem and descriptor guards')
 actual67={'sourceRootCommands':len(rendered),'recoveryMockCommands':len(adapter.commands),'maxCommandBytes':max(len(c.encode())for c in commands),'fullSourceArtifacts':len(proof['files']),'identityFields':len(identity),'syntheticFaultSource':True,'actualFault200Observed':False,'freshLiveReadiness':False,'noRealRootModuleImported':True}
frozen()
print(json.dumps({'schema':'gh-independent-review-validation-v1','sourceSuite':source,'hostSuite':host,'independentChecks':checks,'actualRetained67Mock':actual67,'pins':pins,'targetOperations':0,'networkOperations':0,'deploymentAdmitted':False,'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'authorInventorySha256':sha((P/'source-inventory.json').read_bytes())},indent=2,sort_keys=True))
