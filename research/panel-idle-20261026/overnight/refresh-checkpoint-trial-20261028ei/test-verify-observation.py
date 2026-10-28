#!/usr/bin/env python3
"""Host-only EI admission tests; generated EH FakeOps fixtures, no root calls."""
from pathlib import Path
import base64,copy,hashlib,importlib.util,json,struct,subprocess,sys,tempfile
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent;EH=B/'rtp-refresh-checkpoints-20261028eh';EE=B/'lane-gate-onset-20261028ee';checks=0;unexpected=[]
def check(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def digest(b):return hashlib.sha256(b).hexdigest()
def encode(n):return (json.dumps(n,separators=(',',':'))+'\n').encode()
def setraw(w,b):w['rawBase64']=base64.b64encode(b).decode();w['sha256']=digest(b)
v=load(D/'verify-observation.py','ei_test_guard');p=load(EH/'parse-result.py','ei_test_parser')
# Importing the readiness definition does not run main or load the root adapter.
a=load(D/'prepare-readiness.py','ei_test_readiness')
check(a.WRAPPERS=={'eh':('rtp-refresh-checkpoints-20261028eh/run-once.py','eh-refresh-checkpoint-readiness-decision-v1'),'eb':('rtp-lane-gate-capture-20261028eb/run-once.py','eb-rtp-lane-gate-readiness-decision-v1')},'only EH/EB readiness definitions')
expect=(EE/'prepare-readiness.py').read_text().replace("'dp': ('rtp-score-checkpoints-20261028dp/run-once.py', 'dp-score-checkpoint-readiness-decision-v1')","'eh': ('rtp-refresh-checkpoints-20261028eh/run-once.py', 'eh-refresh-checkpoint-readiness-decision-v1')").replace('ee_readiness_','ei_readiness_').replace('ee-fresh-cached','ei-fresh-cached').replace('EE_CURRENT_READY','EI_CURRENT_READY')
check(expect==(D/'prepare-readiness.py').read_text(),'readiness exact frozen EE derivative; no actual call')
expect=(EE/'check-predecessor.py').read_text().replace("rtp-lane-gate-trial-20261028ed/table-read-01","lane-gate-onset-20261028ee/post-tables-01").replace('ee_predecessor_','ei_predecessor_').replace('ee-offline-predecessor','ei-offline-predecessor')
check(expect==(D/'check-predecessor.py').read_text(),'predecessor exact EE source guard derivative,16/32')
check(v.PARSER_SHA==digest((EH/'parse-result.py').read_bytes())and v.MANIFEST_SHA==digest((EH/'deployment-manifest.json').read_bytes()),'EH source and deployment pins')
proof=json.loads((D/'predecessor-check.json').read_text());check(proof['accepted']is True and proof['headers']==16 and proof['bulks']==32 and proof['phase']=='ReadyForHeader'and proof['released']is True and proof['closed']is True and proof['stageAbsent']is True and proof['actualLimit']==40 and proof['rtState']==[0,0,1],'saved predecessor strict16/32 clean40 boundary')
for row in proof['inputs']:check(digest(Path(row['path']).read_bytes())==row['sha256'],'saved predecessor input pin')
fixtures={}
for kind in ('clean','full','partial'):
 r=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(EH/'bin/Release/net6.0/RefreshCheckpoints.dll'),'--checkpoint-fixture-'+kind],capture_output=True,check=True)
 n=json.loads(r.stdout)
 for cap in n['retained']:
  for w in cap['windows']:
   if w['name']=='R':
    b=bytearray(base64.b64decode(w['rawBase64']));struct.pack_into('<H',b,0xc4,40);setraw(w,b)
 b=bytearray(base64.b64decode(n['scoreCheckpoints']['rawBase64']))
 for at in range(0,len(b),54):struct.pack_into('<2H',b,at+2,40,40)
 n['scoreCheckpoints']['rawBase64']=base64.b64encode(b).decode();n['scoreCheckpoints']['sha256']=digest(b)
 _,_,files,gc,q=p.parse_native(encode(n).decode());check(q['trialQualified']and gc==[],'host fake normalized unchanged40 qualifies '+kind)
 result={'schema':'eh-refresh-checkpoint-wrapper-result-v1','accepted':True,'operation':'read_only_score_checkpoints_with_one_Left','headersSent':n['headersSent'],'bulkTransfers':n['bulkTransfers'],'scoreCheckpointCount':n['scoreCheckpoints']['count'],'trialQualified':True,'keyCausalityEstablished':False,'rawFiles':[{'name':name,'bytes':len(raw),'sha256':d}for name,raw,d in files],'manifestSha256':v.MANIFEST_SHA,'readinessSha256':'a'*64,'endpointQueueProof':False,'identitySnapshotsAtomic':False,'physicalPictureObserved':False,'rootCauseFixEstablished':False,'automaticRestore':False,'wrapperUiOperations':0,'nativeInvocations':1,'retries':0,'cleanup':'STAGE_ABSENT','structuredReceipt':'exclusive_private_file','diagnosticStdoutIsSemanticReceipt':False}
 fixtures[kind]=(n,result,files)
root=D/'reviews/host-environment/tmp';root.mkdir(parents=True,exist_ok=True,mode=0o700)
with tempfile.TemporaryDirectory(prefix='ei-admission-',dir=root)as tmp:
 tmp=Path(tmp)
 def materialize(n,r,files):
  d=tmp/'capture';d.mkdir(exist_ok=True,mode=0o700)
  for f in d.iterdir():f.unlink()
  (d/'native.receipt.json').write_bytes(encode(n));(d/'result.json').write_bytes(encode(r))
  for name,b,_ in files:(d/name).write_bytes(b)
  return d
 def refuse(label,n,r,files,corrupt=None):
  global checks
  d=materialize(n,r,files)
  if corrupt:corrupt(d)
  try:v.verify(d)
  except (ValueError,TypeError,KeyError,AttributeError,OSError,json.JSONDecodeError):checks+=1;return
  unexpected.append(label)
 for kind,(n,r,files)in fixtures.items():
  d=materialize(n,r,files);proof=v.verify(d)
  expected=[0,0,1]if kind=='clean'else[1,0x1001,0]
  check(proof['accepted']is True and proof['phase']=='ReadyForHeader'and proof['lastRtTuple']==expected,'legitimate shape admitted '+kind)
  check(proof['headers']==n['headersSent']and proof['bulks']==2*n['headersSent']and proof['checkpoints']==n['scoreCheckpoints']['count'],'count derives strict native '+kind)
  ins=[c['transfers'][2*i+1]['afterUs']for c in n['retained']for i,w in enumerate(c['windows'])if w['complete']]
  check(proof['lastCompletedDataAfterUs']==max(ins),'true last completed IN timestamp '+kind)
  for field,value in [('accepted',False),('accepted',1),('trialQualified',False),('trialQualified',1),('manifestSha256','0'*64),('headersSent',n['headersSent']+1),('bulkTransfers',n['bulkTransfers']-1),('cleanup','PRESENT'),('nativeInvocations',2),('retries',1),('scoreCheckpointCount',n['scoreCheckpoints']['count']-1),('rawFiles',r['rawFiles'][:-1])]:
   z=copy.deepcopy(r);z[field]=value;refuse(kind+': result '+field,n,z,files)
  for field,value in [('nativeInvocations',True),('nativeInvocations',1.0),('retries',False),('retries',0.0),('headersSent',float(n['headersSent'])),('bulkTransfers',float(n['bulkTransfers'])),('scoreCheckpointCount',float(n['scoreCheckpoints']['count']))]:
   z=copy.deepcopy(r);z[field]=value;refuse(kind+': noninteger '+field+'='+repr(value),n,z,files)
  z=copy.deepcopy(r);z['rawFiles'][0]['bytes']=float(z['rawFiles'][0]['bytes']);refuse(kind+': noninteger inventory size',n,z,files)
  refuse(kind+': raw file corrupt',n,r,files,lambda d:(d/files[0][0]).write_bytes(b'bad'))
  refuse(kind+': raw file absent',n,r,files,lambda d:(d/files[-1][0]).unlink())
  for field,value in [('accepted',False),('protocolPhase','AwaitingIn'),('closed',False),('released',False),('observationAccepted',False)]:
   z=copy.deepcopy(n);z[field]=value;refuse(kind+': native '+field,z,r,files)
  for offset in (2,4):
   z=copy.deepcopy(n);raw=bytearray(base64.b64decode(z['scoreCheckpoints']['rawBase64']));struct.pack_into('<H',raw,10*54+offset,200);z['scoreCheckpoints']['rawBase64']=base64.b64encode(raw).decode();z['scoreCheckpoints']['sha256']=digest(raw)
   # This discarded intermediate row is NOT independently retained; strict EH
   # parsing admits it, so admission's all-row40 predicate must reject it.
   _,_,ff,_,qq=p.parse_native(encode(z).decode());check(qq['trialQualified'],'non40 intermediate otherwise native-valid')
   rr=copy.deepcopy(r);rr['rawFiles']=[{'name':name,'bytes':len(raw),'sha256':d}for name,raw,d in ff];refuse(kind+': compact-only intermediate non40 '+str(offset),z,rr,ff)
 # Duplicate/nonfinite JSON must not be interpreted as a wrapper success.
 for kind,(n,r,files)in fixtures.items():
  for prefix in (b'"accepted":false,',b'"unused":NaN,',b'"unused":Infinity,',b'"unused":-Infinity,'):
   refuse(kind+': strict result JSON '+prefix.decode(),n,r,files,lambda d,prefix=prefix:(d/'result.json').write_bytes(b'{'+prefix+encode(r)[1:]))
 # Transport-valid/key-successful, but Down after all completed reads leaves no
 # observed R coverage. The strict EH parser returns trialQualified=false.
 n,r,files=fixtures['clean'];z=copy.deepcopy(n);last=max(c['transfers'][-1]['afterUs']for c in z['retained']);z['endUs']=max(z['endUs'],last+20)
 for call in z['intervention']['calls']:call['beforeUs']=call['afterUs']=last+10
 z['intervention']['endUs']=last+10
 _,_,ff,_,qq=p.parse_native(encode(z).decode());check(qq['trialQualified']is False,'native-valid observation without key coverage')
 rr=copy.deepcopy(r);rr['rawFiles']=[{'name':name,'bytes':len(raw),'sha256':d}for name,raw,d in ff];refuse('native-valid UI-unqualified workflow',z,rr,ff)
 # Structurally incomplete/failed key children also refuse.
 n,r,files=fixtures['clean'];z=copy.deepcopy(n);z['intervention']['completed']=False;refuse('incomplete key workflow',z,r,files)
 for field,value in [('started',False),('reaped',False),('exitCode',1)]:
  z=copy.deepcopy(n);z['intervention']['calls'][0][field]=value;refuse('key '+field,z,r,files)
report={'schema':'ei-admission-host-tests-v1','checksPassed':checks,'unexpectedAcceptances':unexpected,'targetOperations':0,'rootCalls':0,'networkOperations':0,'fixtures':['clean','full','partial'],'productionObservations':0,'sourcePins':{name:digest((D/name).read_bytes())for name in ('verify-observation.py','prepare-readiness.py','check-predecessor.py')}}
print(json.dumps(report,sort_keys=True))
if unexpected:sys.exit(1)
