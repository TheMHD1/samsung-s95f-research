#!/usr/bin/env python3
"""Independent host-only DM semantic/source checks; writes only sibling review artifacts."""
from pathlib import Path
import base64,copy,hashlib,json,subprocess,sys,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;P=R.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
p=types.ModuleType('independent_dm_parser');p.__file__=str(P/'parse-result.py');exec(compile(Path(p.__file__).read_bytes(),p.__file__,'exec'),p.__dict__)
checks=0

def check(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1

def reject(n,label):
 try:p.parse_native(json.dumps(n))
 except (ValueError,TypeError,KeyError):check(True,label);return
 raise ValueError('unexpected acceptance '+label)

raw=(P/'fixture.json').read_bytes();n,windows,i=p.parse_native(raw.decode())
check(len(windows)==12 and len(i['candidateTuples'])==48,'fixed windows/tuples')
for flag in ['atomicSnapshot','recordEpochProven','actualFixedABranchProven','physicalPictureObserved']:check(i[flag]is False,'bounded interpretation '+flag)
for k in ['schema','bindingChecks','steps','windows']:x=copy.deepcopy(n);x.pop(k);reject(x,'missing '+k)
for j in range(24):
 for key,value in [('count',0),('errno',5),('after','Unknown')]:
  x=copy.deepcopy(n);x['steps'][j][key]=value;reject(x,'step mutation')
for j in range(12):
 x=copy.deepcopy(n);x['windows'][j]['address']+=2;reject(x,'address binding')
for key in ['inode','devMajor','devMinor']:
 x=copy.deepcopy(n);x['bindingChecks'][2]['follow'][key]+=1;reject(x,'native canonical mismatch')
for j in [1,2]:
 x=copy.deepcopy(n);x['bindingChecks'][j]['kernel']['rawBase64']='AAAA';reject(x,'kernel raw buffer binding')
# Source/context disagreement must remain visible without reclassifying exact transport as an atomic record.
for name,offset in [('M',64),('C',0),('end-N',0),('end-R',0)]:
 x=copy.deepcopy(n);w=next(w for w in x['windows'] if w['name']==name);b=bytearray(base64.b64decode(w['base64']));b[offset]^=1;w['base64']=base64.b64encode(b).decode();w['sha256']=sha(b)
 _,_,v=p.parse_native(json.dumps(x));check(v['transportAccepted']is True and v['recordEpochProven']is False and v['atomicSnapshot']is False,'context/epoch separation')
 if name=='M':check(v['sourceContext']['rootMatches']is False,'root discrepancy exposed')
 if name=='C':check(v['sourceContext']['geometryMatches']is False,'geometry discrepancy exposed')
 if name=='end-N':check(v['nBytesEqual']is False,'counter changes exposed')
 if name=='end-R':check(v['rBytesEqual']is False,'state changes exposed')
# Current native binding is byte-exact DQ except the narrower read-only native allowlist.
dq=(P.parent/'volatile-limit-native-binding-20261028dq/Program.cs').read_text();chunk=dq[dq.index('    sealed class RealClock'):dq.index('    sealed class FakeClock')]
a='if (input) Need(data.Length == length && (length == 64 || length == 256 || length == 68 || length == 16), "fixed input length");\n            else Need((length == 12 && AllowedHeader(data)) || (length == 2 && data.Length == 2 && (Half(data,0) == 40 || Half(data,0) == 200)), "fixed OUT only");'
b='if (input) Need(data.Length == length && InputLength(length), "fixed input length");\n            else Need(length == 12 && data.Length == 12 && AllowedHeader(data), "fixed read headers only");'
check(chunk.count(a)==1,'exact narrowing source anchor')
expected='using System;\nusing System.IO;\nusing System.Collections.Generic;\nusing System.Diagnostics;\nusing System.Runtime.InteropServices;\nusing System.Threading;\ninternal static partial class Program\n{\n'+chunk.replace(a,b)+'}\n'
check((P/'NativeBinding.cs').read_text()==expected,'exact DQ native binding/read narrowing')
check(dq[dq.index('    sealed class Controller'):dq.index('    static Outcome Run')].count('ops.Bulk')==1,'parent transaction basis')
check(len(raw)<=24576,'fixture bound')
result={'schema':'dm-independent-host-checks-v1','checksPassed':checks,'targetOperations':0,'fixtureBytes':len(raw),'sourcePins':{name:sha((P/name).read_bytes()) for name in ['Program.cs','NativeBinding.cs','ReceiptMain.cs','HostTests.cs','parse-result.py','run-once.py','test-runner.py','host-build-checkpoint.json']}}
(R/'independent-checks-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
