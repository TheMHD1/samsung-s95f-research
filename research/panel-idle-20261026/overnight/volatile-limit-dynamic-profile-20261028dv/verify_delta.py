#!/usr/bin/env python3
"""Host-only immutable source delta/model lineage audit. No root/target transport."""
from pathlib import Path
import hashlib,json,struct,types,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent;Q=B/'volatile-limit-native-binding-20261028dq';U=B/'volatile-limit-dynamic-profile-design-20261028du'
checks=0
def check(ok,why):
 global checks
 if not ok:raise ValueError(why)
 checks+=1
def sha(b):return hashlib.sha256(b).hexdigest()
lineage=json.loads((D/'source-lineage.json').read_bytes())
for name,digest in lineage['parent_files'].items():check(sha((Q/name).read_bytes())==digest,'parent pin '+name)
proof=json.loads((D/'model-source-proof.json').read_bytes())
for name,digest in proof['pins'].items():check(sha((U/name).read_bytes())==digest,'DU pin '+name)
old=(Q/'Program.cs').read_text();new=(D/'Program.cs').read_text()
for a,z in [('    const int TimeoutMs','    sealed class Outcome'),('    sealed class Controller','    static Outcome Run'),('    sealed class RealClock','    sealed class FakeClock'),('    [DllImport("libc.so.6",EntryPoint="open",SetLastError=true)] static extern int ReceiptOpen','    static int Main')]:
 check(old[old.index(a):old.index(z)]==new[new.index(a):new.index(z)].replace('dv-','dq-'),'fixed source '+a)
check(old[old.index('    static int Main'):]==new[new.index('    static int Main'):].replace('dv-','dq-'),'fixed Main action surface')
for text in ['02010000c424014702000000','0x47012400,256','0x470004a0,68','0x47000bc0,16','0x45000580,64']:
 check(text in old and text in new,'same fixed address/header '+text)
model=(U/'profile_model.py').read_text();model=model[model.index('STATIC='):]
parser=(D/'parse-result.py').read_text();check(model in parser,'exact DU pure model embedded')
parent_parser=(Q/'parse-result.py').read_text()
a='def binding_checks(';z='def parse_native('
check(parent_parser[parent_parser.index(a):parent_parser.index(z)]==parser[parser.index(a):parser.index(z)],'exact independent binding validation')
module=types.ModuleType('pure');exec(compile(model,'pure','exec'),module.__dict__)
vectors=b''.join(struct.pack('<H',module.endpoint(2075,24,t,15,195,3000,3800)['endpoint'])for t in range(4096))
check('Sha(vectors)=="'+sha(vectors)+'"' in new,'all4096 native vectors cross-language bound')
print(json.dumps({'sourceChecksPassed':checks,'targetOperations':0,'nativeVectorSha256':sha(vectors)}))
