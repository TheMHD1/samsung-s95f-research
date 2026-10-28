#!/usr/bin/env python3
"""Host-only DP engine fixtures/strict decoder mutations."""
from pathlib import Path
import base64,copy,hashlib,json,struct,subprocess,types
D=Path(__file__).resolve().parent
p=types.ModuleType('dp_parser');p.__file__=str(D/'parse-result.py');exec(compile(Path(p.__file__).read_bytes(),p.__file__,'exec'),p.__dict__)
checks=0
def check(x,s):
 global checks
 if not x:raise ValueError(s)
 checks+=1
def reject(n):
 try:p.parse_native(json.dumps(n))
 except (ValueError,KeyError,TypeError):check(True,'malformed refused');return
 raise ValueError('unexpected acceptance')
def repack(n,b):
 n['scoreCheckpoints']['rawBase64']=base64.b64encode(b).decode();n['scoreCheckpoints']['sha256']=hashlib.sha256(b).hexdigest()
fixtures={}
for kind in ('clean','full','partial'):
 r=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(D/'bin/Release/net6.0/ScoreCheckpoints.dll'),'--checkpoint-fixture-'+kind],check=True,capture_output=True);n=json.loads(r.stdout);fixtures[kind]=n
 _,_,files,g,q=p.parse_native(r.stdout.decode());s=q['scoreCheckpoints'];check(s['count']==(79 if kind=='partial' else 80),'complete cycles only');check(s['cleanBracketA0Low16Above40Cycles']==[20],'intermediate discarded clean witness retained');check(s['rows'][-1]['a0Low16']==0,'lastclean alone loses witness');check(len(next(raw for name,raw,digest in files if name=='score-checkpoints.bin'))==34*s['count'],'raw compact retention');check(q['trialQualified'] and not q['keyCausalityEstablished'] and not s['everyComparatorCallObserved'],'unchanged qualification limits');check(len(r.stdout)<=24576,'actual native receipt bound');check(n['headersSent']==n['inputsCompleted']==n['bulkTransfers']//2,'global counters untouched')
 if kind=='partial':check(len(next(c for c in n['retained']if c['role']=='transition')['windows'])==1 and any(w['name']=='H'for c in n['retained']if c['role']=='post-fault'for w in c['windows']),'partial transition keeps original postfaultH')
n=fixtures['full']
for key in n['scoreCheckpoints']:
 z=copy.deepcopy(n);z['scoreCheckpoints'].pop(key);reject(z)
for key,v in [('count',81),('count',True),('recordBytes',40),('sha256','0'*64),('rawBase64','!'),('schema','wrong')]:
 z=copy.deepcopy(n);z['scoreCheckpoints'][key]=v;reject(z)
raw=base64.b64decode(n['scoreCheckpoints']['rawBase64'])
for i in range(80):
 for pos in (0,24,28):
  z=copy.deepcopy(n);b=bytearray(raw)
  if pos==0:b[i*34]=0x22
  else:struct.pack_into('<I',b,i*34+pos,0xffffffff)
  repack(z,b);reject(z)
# Retained baseline, last-clean and full transition must exactly match their raw sources.
for ci in (0,78,79):
 for pos in (1,2,4,6,10,12,20,32):
  z=copy.deepcopy(n);b=bytearray(raw);b[ci*34+pos]^=1;repack(z,b);reject(z)
z=copy.deepcopy(n);z['scoreCheckpoints']['count']=79;repack(z,raw[:-34]);reject(z)
z=copy.deepcopy(n);z['scoreCheckpoints']['extra']=False;reject(z)
check(p.load_parent().PARENT_SHA=='acc9f37f3586dc1066a31ec853d739da127fc2afb704fe7202f14a1cc170f0af','exact original transport parser pin')
print(json.dumps({'checksPassed':checks,'targetOperations':0,'fixtureKinds':list(fixtures),'maximumFixtureBytes':max(len(json.dumps(n,separators=(',',':')).encode())for n in fixtures.values())}))
