#!/usr/bin/env python3
"""Additional adversarial compact-state checks, using only frozen managed fakes."""
import base64,copy,hashlib,json,struct,subprocess,types
from pathlib import Path
P=Path(__file__).resolve().parent.parent;checks=0
m=types.ModuleType('er_extra');m.__file__=str(P/'parse-result.py');exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
def check(ok,why):
 global checks
 if not ok:raise ValueError(why)
 checks+=1
def reject(n):
 try:m.parse_native(json.dumps(n))
 except(ValueError,KeyError,TypeError,StopIteration):check(True,'malformed refused');return
 raise ValueError('unexpected acceptance')
def changed(n,raw):
 z=copy.deepcopy(n);z['scoreCheckpoints']['rawBase64']=base64.b64encode(raw).decode();z['scoreCheckpoints']['sha256']=hashlib.sha256(raw).hexdigest();return z
for kind in ['quiescent','resume','quiescent-fault']:
 q=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(P/'bin/Release/net6.0/QuiescentCheckpoints.dll'),'--checkpoint-fixture-'+kind],capture_output=True,check=True)
 n,_,_,_,d=m.parse_native(q.stdout.decode());raw=base64.b64decode(n['scoreCheckpoints']['rawBase64'])
 check(d['workflowQualified']and d['physicalPictureObserved']is False and d['quiescentIsFaultOrPreventionProof']is False,'workflow separated from physical/protection claims')
 for i in [0,27,55]:
  for nibble in [2,4,15]:
   b=bytearray(raw);b[58*i]=(nibble<<4)|(b[58*i]&15);reject(changed(n,b))
   b=bytearray(raw);b[58*i]=(b[58*i]&240)|nibble;reject(changed(n,b))
 # Structurally valid middle Quiescent values are forbidden outside the exact40 qualification,
 # including rows with no retained full raw capture available to the decoder.
 for i in [1,25,54]:
  b=bytearray(raw);b[58*i]=0x33;struct.pack_into('<HH',b,58*i+2,200,200);reject(changed(n,b))
 # A successful workflow does not permit changing raw semantics into a clean rolling role.
 z=copy.deepcopy(n)
 if kind!='resume':
  cap=next(c for c in z['retained']if c['role']=='last-quiescent');cap['role']='last-clean';reject(z)
 z=copy.deepcopy(n);z['quiescentCyclesCompleted']=0;z['cleanCyclesCompleted']=n['cleanCyclesCompleted']+n['quiescentCyclesCompleted'];reject(z)
 for field in ['accepted','observationAccepted','bindingQualified']:
  z=copy.deepcopy(n);z[field]=False;reject(z)
 check(n['scoreCheckpoints']['count']==56 and n['bulkTransfers']==2*n['headersSent']and n['writes']==n['retries']==0,'actual generated shape')
print(json.dumps({'schema':'er-independent-adversarial-checks-v1','checksPassed':checks,'targetOperations':0,'networkOperations':0}))
