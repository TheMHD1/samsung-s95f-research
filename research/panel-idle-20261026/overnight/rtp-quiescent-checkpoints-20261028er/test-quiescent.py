#!/usr/bin/env python3
"""Truthful Quiescent retention/counters, new taps and malformed cases. Host fake only."""
from pathlib import Path
import base64,copy,hashlib,json,struct,subprocess,types
D=Path(__file__).resolve().parent;checks=0
p=types.ModuleType('er_q_decoder');p.__file__=str(D/'parse-result.py');exec(compile((D/'parse-result.py').read_bytes(),p.__file__,'exec'),p.__dict__)
def check(ok,why):
 global checks
 if not ok:raise ValueError(why)
 checks+=1
def reject(n):
 try:p.parse_native(json.dumps(n))
 except(ValueError,KeyError,TypeError,StopIteration):check(True,'rejected');return
 raise ValueError('malformed accepted')
def pack(n,b):n['scoreCheckpoints']['rawBase64']=base64.b64encode(b).decode();n['scoreCheckpoints']['sha256']=hashlib.sha256(b).hexdigest()
fixtures={}
for kind,expected in [('quiescent',(1,55)),('resume',(28,28)),('quiescent-fault',(1,54))]:
 r=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(D/'bin/Release/net6.0/QuiescentCheckpoints.dll'),'--checkpoint-fixture-'+kind],capture_output=True,check=True);n,_,_,_,q=p.parse_native(r.stdout.decode());fixtures[kind]=n
 check((n['cleanCyclesCompleted'],n['quiescentCyclesCompleted'])==expected,'truthful counters')
 check(q['workflowQualified'] and q['quiescentObserved'] and not q['quiescentIsFaultOrPreventionProof'],'workflow distinct from RT/physical')
 check(q['rtObservationOutcome']==('Faulted'if kind=='quiescent-fault'else'QuiescentObserved'),'outcome distinct')
 check(n['intervention']['completed'] and n['scoreCheckpoints']['count']==56,'one key and boundedcomplete rows')
 check(sum(x['cleanRBrackets']for x in q['scoreCheckpoints']['rows'])==expected[0],'noQuiescent labeledclean')
 check(n['headersSent']==(455 if kind=='quiescent-fault'else 448)and n['bulkTransfers']==2*n['headersSent'],'noextraUSB')
 raw=base64.b64decode(n['scoreCheckpoints']['rawBase64'])
 for i,row in enumerate(q['scoreCheckpoints']['rows']):
  check(struct.unpack_from('<2H',raw,i*58+54)==(0x6000+2*(i+1),0x7000+2*(i+1)),'independent endRsource markers')
  check((row['endRRoot24caU16'],row['endRRoot2468U16'])==(0x6000+2*(i+1),0x7000+2*(i+1)),'decodedtap source')
 for field in ('quiescentCyclesCompleted','cleanCyclesCompleted','cleanCyclesDiscarded'):
  z=copy.deepcopy(n);z[field]+=1;reject(z)
 for rowidx in sorted({cap["cycleIndex"]-1 for cap in n["retained"]if len(cap["windows"])==8}):
  for field in (0,54,56):
   z=copy.deepcopy(n);b=bytearray(raw);b[rowidx*58+field]^=1;pack(z,b);reject(z)
 z=copy.deepcopy(n);z['quiescentCyclesCompleted']=True;reject(z)
 z=copy.deepcopy(n);z['retained'][1]['role']='last-clean';reject(z)
 # Raw R and classifier must agree, including the40 qualification.
 z=copy.deepcopy(n);cap=next(c for c in z['retained']if any(w.get('observedRtState',{}).get('classification')=='Quiescent'for w in c['windows']));w=next(w for w in cap['windows']if w.get('observedRtState',{}).get('classification')=='Quiescent');b=bytearray(base64.b64decode(w['rawBase64']));struct.pack_into('<H',b,0xc4,200);w['rawBase64']=base64.b64encode(b).decode();w['sha256']=hashlib.sha256(b).hexdigest();reject(z)
for kind,headers in [('initial-quiescent',1),('end-initial-quiescent',8)]:
 n=json.loads(subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(D/'bin/Release/net6.0/QuiescentCheckpoints.dll'),'--checkpoint-fixture-'+kind],capture_output=True,check=True).stdout)
 check(n['accepted']is False and n['observationAccepted']is False and n['terminalReason']=='InitialQuiescent','originalrefusal not forged')
 check(not n['intervention']['attempted'] and n['headersSent']==headers and n['protocolPhase']=='ReadyForHeader'and n['released']and n['closed'],'initialQuiescent nokey/completepaircleanup')
 reject(n)
print(json.dumps({'schema':'er-quiescent-validation-v1','checksPassed':checks,'targetOperations':0,'maxFixtureBytes':max(len(json.dumps(x,separators=(',',':')).encode())for x in fixtures.values())},sort_keys=True))
