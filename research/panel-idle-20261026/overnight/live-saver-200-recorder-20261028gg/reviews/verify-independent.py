#!/usr/bin/env python3
"""Independent, host-only GG review. Only reviewer-owned outputs/tempfiles are written."""
import base64,contextlib,copy,hashlib,io,json,os,subprocess,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;P=OUT.parent;B=P.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=0
pins={}
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def pin(p):
 raw=p.read_bytes();pins[str(p.relative_to(B))]={'bytes':len(raw),'sha256':sha(raw)};return raw
def inventory():
 raw=pin(P/'source-inventory.json');ck(sha(raw)=='bc7fad762b194d7bc55f7d618689fbd909d44c30ac3ae2f7614000c40d1744a6','frozen source inventory pin')
 for f in json.loads(raw)['files']:
  data=pin(P/f['path']);ck(len(data)==f['bytes'] and sha(data)==f['sha256'],'frozen file '+f['path'])
 ck(sha(pin(P/'deployment-manifest.json'))=='0c6beb9e76f95060f95f89bfa2ba13b7d648bbf84ab992b64d2473e451d2f42a','manifest pin')
def execute(name,text=None):
 path=P/name;ns={'__file__':str(path),'__name__':'reviewed_host_suite'};output=io.StringIO()
 with contextlib.redirect_stdout(output):exec(compile(text if text is not None else pin(path),str(path),'exec'),ns)
 return json.loads(output.getvalue()),ns
inventory()
source,_=execute('verify-source.py')
identity_path=B/'live-saver-wake-trial-20261028gf/after-recovery-identity/identity.json'
identity=json.loads(pin(identity_path));ck(len(identity)==16 and identity['devnum']=='67','authoritative retained GF67 identity sixteen fields')
text=pin(P/'test-host.py').decode()
old="if device==67:case['identity'].update(devnum='67',deviceNode='/dev/bus/usb/007/067',nodeStat='bd:342:12345')"
new="if device==67:case['identity']="+repr(identity)
ck(text.count(old)==1,'single synthetic67 identity substitution')
text=text.replace(old,new).replace("scratch=P/'host-environment/tmp'","scratch=P/'reviews/tmp'")
host,ns=execute('test-host.py',text)
key,_=execute('test-key-exposure.py')
r=ns['r'];parser=ns['parser'];f=ns['f'];branches=ns['branches']
ck(host['targetOperations']==host['networkOperations']==0,'host transport mocks only')
ck(host['maxCommandBytes']<=8192,'actual67 whole command cap')
# Every exact metadata guard must bind all sixteen authoritative fields. No forged
# live readiness: the unchanged suite's known-phase lineage is explicitly synthetic.
cmd=r.metadata_body(identity,'PRE_READY')
ck(identity['nodeStat'] in cmd and identity['sysfsStat'] in cmd and identity['sysfsRealpath'] in cmd,'actual67 filesystem identity guarded')
ck(identity['deviceNode'] in cmd and identity['descriptorsSha256'] in cmd,'actual67 device/descriptor guarded')
ck('0x' not in identity['devnum'],'canonical device number')
ck(r.manifest_bytes(r.build_manifest()[0])==(P/'deployment-manifest.json').read_bytes(),'regenerated manifest byte exact')
# Mutate the actual RT bytes for each recognized class, independently of fixture labels.
rtstates={}
for state,triplet in [('Clean',(0,0,1)),('Fault',(1,4097,0)),('Q',(0,0,0))]:
 raw=bytearray(base64.b64decode(f['controls'][0]['windows'][0]['raw']))
 for off,value in zip((0,10,14),triplet):raw[off:off+2]=value.to_bytes(2,'little')
 raw[196:198]=(200).to_bytes(2,'little');rtstates[state]=parser.rt(raw)
 ck(rtstates[state] in (0,1,3),'recognized fixed200 '+state)
 raw[196:198]=(40).to_bytes(2,'little')
 try:parser.rt(raw)
 except ValueError:ck(True,'all-state40 rejected '+state)
 else:raise ValueError('40 accepted '+state)
# Genuine branch fixtures, not rewritten target40 data.
for name,value in branches.items():
 native,rows,q=parser.parse_native(value+'\n')
 ck(native['schema']=='live-saver-event200-gg-v1' and native['threshold']==200,'family branch '+name)
 for record in native['controls']+native['retained']:
  for window in record['windows']:
   if window['name']=='R':ck(int.from_bytes(base64.b64decode(window['raw'])[196:198],'little')==200,'all retained full RT limits '+name)
ck(len(branches)==11,'all native branches present')
env=dict(os.environ,DOTNET_CLI_HOME=str(OUT/'sdk-home'),TMPDIR=str(OUT/'tmp'),DOTNET_NOLOGO='1',DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1')
dotnet='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet'
dll=P/'bin/Release/net6.0/CombinedEvent200.dll'
def native_run(flag):
 result=subprocess.run([dotnet,str(dll),flag],capture_output=True,env=env,timeout=60)
 ck(result.returncode==0 and result.stderr==b'','host FakeOps CLI '+flag)
 return json.loads(result.stdout)
native=native_run('--self-test');ck(native==json.loads((P/'native-tests.json').read_bytes()),'existing pinned DLL reproduces native selftest report')
regenerated=native_run('--branch-fixtures');ck(regenerated==branches,'existing DLL regenerates all eleven native fixtures byte-exact')
ck(native['selfTestsPassed']==3563 and native['maxReceiptBytes']==18270 and native['targetOperations']==0,'native bounds/zero target')
inventory()
result={'schema':'gg-independent-review-validation-v1','independentChecks':checks,'sourceSuite':source,'hostSuiteWithAuthoritativeGF67Identity':host,'keySuite':key,'nativeSuite':native,'nativeBranchFixturesReproduced':11,'recognizedFixed200States':rtstates,'sourceInventorySha256':sha((P/'source-inventory.json').read_bytes()),'manifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'actualRetainedIdentityFields':16,'authoritativeIdentitySha256':sha(identity_path.read_bytes()),'identityUse':'host mock only; synthetic phase lineage, no current readiness or raised-limit qualification','pins':pins,'targetOperations':0,'networkOperations':0,'faulted200RecoveryPrerequisite':'OPEN; outside this recorder review'}
print(json.dumps(result,indent=2,sort_keys=True))
