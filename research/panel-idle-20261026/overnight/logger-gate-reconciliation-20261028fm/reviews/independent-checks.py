#!/usr/bin/env python3
"""Host-only frozen FM review; no root adapter, target, network or source mutation."""
import base64,copy,hashlib,json,pathlib,subprocess,sys,tempfile,types
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent.parent;T=P/'reviews/independent-private';T.mkdir(exist_ok=True,mode=0o700)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
checks=0
def check(v,m):
 global checks
 checks+=1
 if not v:raise ValueError(m)
def reject(f):
 try:f()
 except (ValueError,KeyError,TypeError):check(True,'rejected');return
 raise ValueError('unexpected admission')
r=load(P/'run-once.py');p=load(P/'parse-result.py');inv=json.loads((P/'source-inventory.json').read_bytes())
check(sha((P/'source-inventory.json').read_bytes())=='21680e7b8b3750f1fa9e86f63478e420b42781b4d16a7f921994def8ec9f7f1b','inventory pin')
for row in inv['files']:
 b=(P/row['path']).read_bytes();check(len(b)==row['bytes']and sha(b)==row['sha256'],'frozen '+row['path'])
manifest,payload=r.build_manifest();mb=r.manifest_bytes(manifest);check(mb==(P/'deployment-manifest.json').read_bytes(),'regenerated manifest')
check(sha(mb)=='c2315adb3f6643dd45fcceab70b4013fd0670bd96f7226a08dad3dec0094327d','manifest pin')
# Strict original proof and current actual FH refusal raw context, with no accepted projection.
fh=P.parent/'combined-event-trial-20261028fh';premise=json.loads((fh/'restore-only-premise.json').read_bytes());proof=r.validate_restore_premise(premise)
check(len(proof['inputs'])==5,'five original inputs')
n=json.loads((fh/'capture-01/native.receipt.json').read_bytes());check(n['accepted']is False and n['phase']=='ReadyForHeader'and n['released']and n['closed'],'FH preserved refusal')
c=next(c for c in n['retained']if c['role']=='current')
w={w['name']:base64.b64decode(w['raw'],validate=True)for w in c['windows']}
p.context(w['M'],w['C']);p.logger(w['R'],1);check(w['C'][8]==0 and p.rt(w['R'])=='Quiescent','actual FH fresh finite context source candidate')
fixture=json.loads((P/'fixture.json').read_bytes());check(p.parse_native(json.dumps(fixture))[0]['writes']==1,'positive fixture')
# Rehash malformed full-word gate/known-profile/finite-context changes to avoid mere SHA rejection.
for capture,offset,value in [(2,6,0),(2,7,1),(4,6,1),(4,7,1),(2,0xc4,200),(4,0xc4,200),(2,0x9a,1),(4,0x9a,1),(0,56,2),(1,8,1),(1,8,2),(1,8,4),(1,7,2)]:
 z=copy.deepcopy(fixture);q=z['retained'][capture]['windows'][0];b=bytearray(base64.b64decode(q['rawBase64']));b[offset]=value;q.update(rawBase64=base64.b64encode(b).decode(),sha256=sha(b));reject(lambda:p.parse_native(json.dumps(z)))
for index in range(5):
 for field,value in [('beforeUs',True),('afterUs',fixture['endUs']+1),('count',0),('errno',1)]:
  z=copy.deepcopy(fixture);z['retained'][index]['transfers'][1][field]=value;reject(lambda:p.parse_native(json.dumps(z)))
for field,value in [('headers',True),('inputs',5),('writes',0),('restoreAttempted',False),('loggerMayRemain',True),('arms',1),('uiOperations',1),('phase','Unknown'),('accepted',False)]:
 z=copy.deepcopy(fixture);z[field]=value;reject(lambda:p.parse_native(json.dumps(z)))
# Reuse only author host-mock definitions (not live adapter), actual saved USB65 identity/readiness.
s=(P/'verify-host.py').read_text().split('manifest,payload=r.build_manifest();rm=')[0]
s=s.replace("dir=P/'host-environment/tmp'","dir=P/'reviews/independent-private'")
a=types.ModuleType('fm_review_mocks');a.__file__=str(P/'verify-host.py');exec(compile(s,str(P/'verify-host.py'),'exec'),a.__dict__)
rdpath=fh/'restore-readiness-01/readiness.json';rd=r.load_readiness(rdpath,sha(rdpath.read_bytes()))[0];check(rd['identity']['devnum']=='65','actual USB65 readiness')
r.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32))
with tempfile.TemporaryDirectory(dir=T,prefix='actual-identity-')as td:
 root=a.Mock('success');result=r.execute(pathlib.Path(td)/'out',rd,rdpath.read_bytes(),mb,payload,root,p)
 check(result['accepted']and root.native==1 and root.cleanup==1 and root.ui==0,'actual identity mocked lifecycle')
 check(len(root.commands[-1].encode())<=8192,'cleanup bounded')
 maximum=max(len(c.encode())for c in root.commands);check(maximum<=8192,'all actual identity commands bounded')
 for c in root.commands:check(subprocess.run(['sh','-n'],input=c.encode(),capture_output=True).returncode==0,'actual identity shell syntax')
 check(len(root.commands)==len(set(root.commands)),'no repeated commands')
 check('baseline-ring'not in ''.join(root.commands)and'input_keyevent'not in ''.join(root.commands),'no ring/UI')
# No frozen source changed by reads or mocks.
for row in inv['files']:check(sha((P/row['path']).read_bytes())==row['sha256'],'unchanged '+row['path'])
print(json.dumps({'schema':'fm-independent-checks-v1','checks':checks,'sourceFiles':len(inv['files']),'manifestSha256':sha(mb),'actualUsb65MockMaxCommandBytes':maximum,'actualIdentityMockRootCalls':len(root.commands),'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
