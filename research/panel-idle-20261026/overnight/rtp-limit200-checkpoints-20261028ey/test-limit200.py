#!/usr/bin/env python3
"""Focused fixed200 semantic/context mutations; host fixtures only."""
from pathlib import Path
import base64,copy,hashlib,json,struct,subprocess,types,tempfile
D=Path(__file__).resolve().parent;checks=0;runtime='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet'
def load(path,name):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def check(b,s):
 global checks
 if not b:raise ValueError(s)
 checks+=1
def reject(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError):check(True,'rejected');return
 raise ValueError('unexpected fixed200 acceptance')
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda n:json.dumps(n,separators=(',',':'))+'\n'
def fixture(kind):return json.loads(subprocess.run([runtime,str(D/'bin/Release/net6.0/Limit200Checkpoints.dll'),'--checkpoint-fixture-'+kind],check=True,capture_output=True).stdout)
def rawset(w,b):w.update(rawBase64=base64.b64encode(b).decode(),sha256=sha(b))
def pack(n,b):n['scoreCheckpoints'].update(rawBase64=base64.b64encode(b).decode(),sha256=sha(b))
p=load(D/'parse-result.py','ey200p');v=load(D/'verify-observation.py','ey200v');fixtures={}
for kind in ('clean','full','partial','quiescent','resume','quiescent-fault','witness'):
 n=fixture(kind);_,_,files,_,q=p.parse_native(enc(n));fixtures[kind]=(n,files,q)
 check(q['trialQualified'] and all(x['startAlternateThreshold']==x['endAlternateThreshold']==200 for x in q['scoreCheckpoints']['rows']),'all states fixed200 '+kind)
 for i,cap in enumerate(n['retained']):
  for j,w in enumerate(cap['windows']):
   if w['name']!='R' or not w['complete']:continue
   check(struct.unpack_from('<H',base64.b64decode(w['rawBase64']),0xc4)[0]==200,'every raw200')
   z=copy.deepcopy(n);rw=z['retained'][i]['windows'][j];b=bytearray(base64.b64decode(rw['rawBase64']));struct.pack_into('<H',b,0xc4,40);rawset(rw,b);reject(lambda:p.parse_native(enc(z)))
 for idx in (10,20,30):
  for off in (2,4):
   z=copy.deepcopy(n);b=bytearray(base64.b64decode(z['scoreCheckpoints']['rawBase64']));struct.pack_into('<H',b,idx*58+off,40);pack(z,b);reject(lambda:p.parse_native(enc(z)))
 n,files,q=fixtures[kind]
 result={'schema':'ey-limit200-checkpoint-wrapper-result-v1','accepted':True,'trialQualified':True,'nativeInvocations':1,'retries':0,'headersSent':n['headersSent'],'bulkTransfers':n['bulkTransfers'],'scoreCheckpointCount':n['scoreCheckpoints']['count'],'manifestSha256':v.MANIFEST_SHA,'cleanup':'STAGE_ABSENT','rawFiles':[{'name':name,'bytes':len(b),'sha256':h}for name,b,h in files]}
 with tempfile.TemporaryDirectory(dir=D/'host-environment/tmp')as td:
  td=Path(td);(td/'native.receipt.json').write_text(enc(n));(td/'result.json').write_text(enc(result))
  for name,b,_ in files:(td/name).write_bytes(b)
  proof=v.verify(td);check(proof['actualSampledLimit']==200 and proof['quiescentCyclesCompleted']==n['quiescentCyclesCompleted'],'admission truthful200/Q '+kind)
  for field,val in [('schema','er-quiescent-checkpoint-wrapper-result-v1'),('manifestSha256','0'*64),('cleanup','PRESENT'),('accepted',False),('trialQualified',False),('nativeInvocations',2),('retries',1),('headersSent',True)]:
   z=copy.deepcopy(result);z[field]=val;(td/'result.json').write_text(enc(z));reject(lambda:v.verify(td))
# Compact contextual witness vs separately retained mode1 evidence.
n,_,q=fixtures['witness'];e=q['fixed200Evidence'];check(e['cleanBracketAbove40SelectorOneCycles']==[20,56] and e['sameCycleRetainedMode1SupportedWitnessCycles']==[56] and e['retainedMode1AlternateContextObserved'],'positive contextual source witness')
check(not e['actualFpSelectionProven'] and not e['unretainedRowModeFlagsProven'],'no actualFP or unretained mode claim')
for off,value in [(1,0),(54,0),(6,40)]:
 z=copy.deepcopy(n);b=bytearray(base64.b64decode(z['scoreCheckpoints']['rawBase64']));at=19*58+off
 if off==1:b[at]=value
 elif off==54:struct.pack_into('<H',b,at,value)
 else:struct.pack_into('<I',b,at,value)
 pack(z,b);_,_,_,_,q0=p.parse_native(enc(z));check(q0['fixed200Evidence']['cleanBracketAbove40SelectorOneCycles']==[56],'wrong selector/mirror/not above40 no witness')
z=copy.deepcopy(n)
for cap in z['retained']:
 for w in cap['windows']:
  if w['name']=='M':b=bytearray(base64.b64decode(w['rawBase64']));struct.pack_into('<H',b,12,1);rawset(w,b)
_,_,_,_,q0=p.parse_native(enc(z));check(q0['fixed200Evidence']['cleanBracketAbove40SelectorOneCycles']==[20,56] and q0['fixed200Evidence']['sameCycleRetainedMode1SupportedWitnessCycles']==[] and not q0['fixed200Evidence']['retainedMode1AlternateContextObserved'],'compact candidates do not invent mode flags')
# Frozen ER native/parser allow Clean200; frozen ES40 admission must refuse it.
ER=D.parent/'rtp-quiescent-checkpoints-20261028er';ES=D.parent/'quiescent-onset-trial-20261028es';oldp=load(ER/'parse-result.py','er_immutable');oldv=load(ES/'verify-observation.py','es_immutable')
n=copy.deepcopy(fixtures['clean'][0]);n['schema']='managed-usb-rt-synchronized-key-er-v1';n['scoreCheckpoints']['schema']='er-quiescent-checkpoints-v1';_,_,ff,_,qq=oldp.parse_native(enc(n));check(qq['trialQualified'],'honest frozen ER Clean200 behavior')
r={'schema':'er-quiescent-checkpoint-wrapper-result-v1','accepted':True,'trialQualified':True,'nativeInvocations':1,'retries':0,'headersSent':n['headersSent'],'bulkTransfers':n['bulkTransfers'],'scoreCheckpointCount':n['scoreCheckpoints']['count'],'manifestSha256':oldv.MANIFEST_SHA,'cleanup':'STAGE_ABSENT','rawFiles':[{'name':name,'bytes':len(b),'sha256':h}for name,b,h in ff]}
with tempfile.TemporaryDirectory(dir=D/'host-environment/tmp')as td:
 td=Path(td);(td/'native.receipt.json').write_text(enc(n));(td/'result.json').write_text(enc(r))
 for name,b,_ in ff:(td/name).write_bytes(b)
 reject(lambda:oldv.verify(td))
n=copy.deepcopy(fixtures['quiescent'][0]);n['schema']='managed-usb-rt-synchronized-key-er-v1';n['scoreCheckpoints']['schema']='er-quiescent-checkpoints-v1';reject(lambda:oldp.parse_native(enc(n)))
print(json.dumps({'schema':'ey-limit200-focused-tests-v1','checksPassed':checks,'targetOperations':0,'rootCalls':0,'networkOperations':0,'frozenErNativeClean200Accepted':True,'frozenEs40AdmissionRejects200':True},sort_keys=True))
