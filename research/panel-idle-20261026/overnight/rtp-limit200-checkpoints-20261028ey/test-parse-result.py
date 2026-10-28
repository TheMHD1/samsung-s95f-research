#!/usr/bin/env python3
"""Host-only EM fixtures, independent marker/golden prefix and strict decoder mutations."""
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
 r=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(D/'bin/Release/net6.0/Limit200Checkpoints.dll'),'--checkpoint-fixture-'+kind],check=True,capture_output=True);n=json.loads(r.stdout);fixtures[kind]=n
 _,_,files,g,q=p.parse_native(r.stdout.decode());s=q['scoreCheckpoints'];check(s['count']==(55 if kind=='partial' else 56),'complete cycles only');check(s['cleanBracketA0Low16Above40Cycles']==[20],'intermediate discarded clean witness retained');check(s['rows'][-1]['a0Low16']==0,'lastclean alone loses witness');check(len(next(raw for name,raw,digest in files if name=='score-checkpoints.bin'))==58*s['count'],'raw compact retention');check(q['trialQualified'] and not q['keyCausalityEstablished'] and not s['everyComparatorCallObserved'],'unchanged qualification limits');check(len(r.stdout)<=24576,'actual native receipt bound');check(n['headersSent']==n['inputsCompleted']==n['bulkTransfers']//2,'global counters untouched')
 check(n['deadlineUs']-n['startUs']==2000000 and n['cyclesStarted']==56,'native fixed observation and cycle cap')
 check(n['headersSent']==(455 if kind=='full' else 448) and n['bulkTransfers']==2*n['headersSent'],'exact existing8-read cycle/postfault count')
 if kind=='partial':check(len(next(c for c in n['retained']if c['role']=='transition')['windows'])==1 and any(w['name']=='H'for c in n['retained']if c['role']=='post-fault'for w in c['windows']),'partial transition keeps original postfaultH')
# Markers are independent cycle-coded input sources. Start/end R differ by one;
# pointers are little-endian u32 and include significant upper bytes.
clean=fixtures['clean'];cb=base64.b64decode(clean['scoreCheckpoints']['rawBase64'])
_,_,_,_,cq=p.parse_native(json.dumps(clean));cr=cq['scoreCheckpoints']['rows']
for cycle in range(1,57):
 b=cb[(cycle-1)*58:cycle*58];expect=(cycle,0x1100+cycle,0x2200+cycle,0x3300+cycle,0x4000+2*cycle,0x5000+2*cycle,0xa0000000+cycle,0xb0000000+cycle)
 check(struct.unpack_from('<6H2I',b,34)==expect,'independently cycle-coded appended inputs including endR')
 check(tuple(cr[cycle-1][k]for k in ('mCpu4a2U16','mCpu4a4U16','mCpu4c2U16','mCpu4c4U16','endRRoot2460U16','endRRoot246eU16','capturedDynamicAPointerU32','capturedDynamicBPointerU32'))==expect,'decoded source markers')
# Frozen DP is host fake code only; no native USB path is reachable by fixture CLI.
dp=D.parent/'rtp-score-checkpoints-20261028dp'
r=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(dp/'bin/Release/net6.0/ScoreCheckpoints.dll'),'--checkpoint-fixture-clean'],check=True,capture_output=True)
gold=base64.b64decode(json.loads(r.stdout)['scoreCheckpoints']['rawBase64'])
for i in range(56):check(cb[i*58:i*58+2]+cb[i*58+6:i*58+24]+cb[i*58+32:i*58+34]==gold[i*34:i*34+2]+gold[i*34+6:i*34+24]+gold[i*34+32:(i+1)*34],'original non-time prefix bytes match DP; H timing changes with cadence')
check(cq['scoreCheckpoints']['observationDurationUs']==2000000 and cq['scoreCheckpoints']['maximumCheckpoints']==56 and cq['scoreCheckpoints']['nominalPeriodUs']==25000,'rigid2s/56/25ms distinct observation')
for field,value in [('deadlineUs',clean['startUs']+20000000),('cyclesStarted',80),('headersSent',456),('inputsCompleted',456),('bulkTransfers',912),('schema','managed-usb-rt-synchronized-key-dp-v1')]:
 z=copy.deepcopy(clean);z[field]=value;reject(z)
n=fixtures['full']
for key in n['scoreCheckpoints']:
 z=copy.deepcopy(n);z['scoreCheckpoints'].pop(key);reject(z)
for key,v in [('count',57),('count',True),('recordBytes',34),('sha256','0'*64),('rawBase64','!'),('schema','wrong')]:
 z=copy.deepcopy(n);z['scoreCheckpoints'][key]=v;reject(z)
raw=base64.b64decode(n['scoreCheckpoints']['rawBase64'])
for i in range(56):
 for pos in (0,24,28):
  z=copy.deepcopy(n);b=bytearray(raw)
  if pos==0:b[i*58]=0x22
  else:struct.pack_into('<I',b,i*58+pos,0xffffffff)
  repack(z,b);reject(z)
# Retained baseline, last-clean and full transition must exactly match their raw sources.
for ci in (0,54,55):
 for pos in (1,2,4,6,10,12,20,32,34,36,38,40,42,44,46,50,54,56):
  z=copy.deepcopy(n);b=bytearray(raw);b[ci*58+pos]^=1;repack(z,b);reject(z)
z=copy.deepcopy(n);z['scoreCheckpoints']['count']=55;repack(z,raw[:-58]);reject(z)
z=copy.deepcopy(n);z['scoreCheckpoints']['extra']=False;reject(z)
check(p.load_parent().PARENT_SHA=='642a8fbfbadbd762da4fa07f1ffc0f5be796a4cb0b336d56e68ee394bf28510a','exact fixed200 transport parser pin')
print(json.dumps({'checksPassed':checks,'targetOperations':0,'fixtureKinds':list(fixtures),'maximumFixtureBytes':max(len(json.dumps(n,separators=(',',':')).encode())for n in fixtures.values())}))
