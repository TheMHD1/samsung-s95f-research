#!/usr/bin/env python3
"""Independent bounded FG checks. Imports only pure parsers/wrappers and mock transports."""
import base64,copy,contextlib,hashlib,io,json,pathlib,sys,tempfile,types
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent.parent
checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
r=load(P/'run-once.py');parser=load(P/'parse-result.py');fixture=json.loads((P/'fixture.json').read_bytes())
def reject(f):
 try:f()
 except (ValueError,KeyError,TypeError,IndexError,OSError,UnicodeError):need(True,'malformed rejected');return
 raise ValueError('unexpected malformed acceptance')
# Exact fixed logger opcode/address/length; no alternative value/address CLI.
s=(P/'Protocol.cs').read_text();need('020100000624014702000000'in s,'logger header bytes')
need(bytes.fromhex('020100000624014702000000')==(0x102).to_bytes(4,'little')+(0x47012406).to_bytes(4,'little')+(2).to_bytes(4,'little'),'fixed packet decode')
s=(P/'NativeBinding.cs').read_text();need('data[1]==0&&(data[0]==0||data[0]==1)'in s,'fixed exact halfword payloads')
s=(P/'OnsetKey.cs').read_text();start=s[s.index('public void Start(IClock clock)'):s.index('void Send(string phase')];need(start.index('State.Attempted = true')<start.index('State.ArmedUs = clock.NowUs()')<start.index('worker = new Thread'),'Attempted before scheduling / consistent join reserve')
for key,value in [('phase','Unknown'),('released',False),('closed',False),('bindingQualified',False),('headers',True)]:
 v=copy.deepcopy(fixture);v[key]=value;reject(lambda:parser.parse_native(json.dumps(v)+'\n'))
for role in ['arm','restore']:
 v=copy.deepcopy(fixture);c=next(c for c in v['controls']if c['role']==role);c['transfers'][1][0]='IN';reject(lambda:parser.parse_native(json.dumps(v)+'\n'))
v=copy.deepcopy(fixture);v['controls'][5],v['controls'][7]=v['controls'][7],v['controls'][5];reject(lambda:parser.parse_native(json.dumps(v)+'\n'))
# Selected last-row fields must bind the retained last/current raw sets as well as the first row.
for pos in [10,12,20,24,28,34,38,42,46,50,56]:
 v=copy.deepcopy(fixture);b=bytearray(base64.b64decode(v['rows']['rawBase64']));b[55*58+pos]^=1;v['rows']['rawBase64']=base64.b64encode(b).decode();v['rows']['sha256']=sha(b);reject(lambda:parser.parse_native(json.dumps(v)+'\n'))
ring=bytearray(15372);ring[0:2]=(4).to_bytes(2,'little');ring[12]=7;ring=bytes(ring)
for name in ['baselineRing','postRing']:
 for field,value in [('complete',False),('bytes',15371),('sha256','0'*64)]:
  v=copy.deepcopy(fixture);v[name][field]=value
  if field=='sha256':reject(lambda:parser.bind_rings(v,ring,ring))
  else:reject(lambda:parser.parse_native(json.dumps(v)+'\n'))
 # Body/hash agree but a cursor is out of the source-qualified inclusive bound.
 body=bytearray(15372);body[:4]=(15361).to_bytes(4,'little');body=bytes(body);v=copy.deepcopy(fixture);v[name]['sha256']=sha(body)
 reject(lambda:parser.bind_rings(v,body if name=='baselineRing'else ring,body if name=='postRing'else ring))
# Load only the author's pure-parser prelude and mock definitions; do not repeat its wrapper cases.
source=(P/'test-host.py').read_text();needle="dir=P/'host-environment/tmp'";need(source.count(needle)==1,'one temp relocation')
ns={'__name__':'fg_review_mock_import','__file__':str(P/'test-host.py')}
source=source.split('\nmanifest,payload=r.build_manifest();',1)[0]
with contextlib.redirect_stdout(io.StringIO()):exec(compile(source,str(P/'test-host.py'),'exec'),ns)
ring=ns['ring'];Mock=ns['Mock'];m=ns['m'];r=ns['r'];parser=ns['parser']
rd=m.ready();rd['schema']='fg-combined-event-readiness-decision-v1';rd['identity']=json.loads((P.parent/'wake-qualified-onset-trial-20261028fe/after-recovery-identity/identity.json').read_bytes());ns['fixture']=copy.deepcopy(fixture);ns['fixture']['device']=65
manifest,payload=r.build_manifest();need(r.manifest_bytes(manifest)==(P/'deployment-manifest.json').read_bytes(),'manifest exact')
with tempfile.TemporaryDirectory(prefix='real-identity-',dir=P/'reviews/private')as tmp:
 base=pathlib.Path(tmp);e=base/'evidence';e.write_text('SYNTHETIC MOCK ONLY: actual saved USB65 identity with no device interaction.');rd['evidence']=[{'path':str(e),'sha256':sha(e.read_bytes())}];rr=json.dumps(rd).encode();readyPath=base/'readiness.json';readyPath.write_bytes(rr);need(r.load_readiness(readyPath,sha(rr))[0]==rd,'actual saved identity passes family readiness shape');f=Mock();clock=m.Clock()
 result=r.execute(base/'capture',rd,rr,r.manifest_bytes(manifest),payload,f,parser,clock,clock.sleep)
 need(result['accepted']and f.native==1 and f.fetch==2 and f.cleanup==1,'real-identity synthetic one-shot completed')
 realmax=max(len(c.encode())for c in f.commands);need(realmax<=8192,'actual identity command bound')
 record=json.loads((base/'capture/record.json').read_bytes());need(record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','stage removed only after accepted tail')
 for kind in ['unknown','native-ambiguous','sidecar-corrupt','POST_READY','cleanup']:
  f=Mock(kind);clock=m.Clock()
  reject(lambda:r.execute(base/kind,rd,rr,r.manifest_bytes(manifest),payload,f,parser,clock,clock.sleep))
  record=json.loads((base/kind/'record.json').read_bytes());need(record['cleanup_required']is True,'refusal retains stage ownership ledger')
  if kind in ['unknown','native-ambiguous']:need(f.fetch==f.cleanup==0,'unknown no later sidecar/cleanup root request')
print(json.dumps({'independentChecks':checks,'actualSavedIdentitySyntheticMaxCommandBytes':realmax,'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
