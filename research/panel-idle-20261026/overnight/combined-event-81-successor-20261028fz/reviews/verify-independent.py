#!/usr/bin/env python3
"""Focused FZ source/cap tests plus an explicit retained-identity66 mock; no transport."""
from pathlib import Path
import contextlib,copy,hashlib,io,json,sys,types
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;P=D.parent;B=P.parent;checks=0
h=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def load(path,src=None):
 m=types.ModuleType(path.stem);m.__file__=str(path)
 exec(compile(path.read_text()if src is None else src,str(path),'exec'),m.__dict__);return m
invraw=(P/'source-inventory.json').read_bytes();ck(h(invraw)=='fd4989f539497d982beeaf6cb23d24161dcb147e8c9eeda007cada2affd7d5df','frozen inventory')
inv=json.loads(invraw)
for row in inv['files']:
 data=(P/row['path']).read_bytes();ck(len(data)==row['bytes']and h(data)==row['sha256'],'frozen '+row['path'])
ck(h((P/'deployment-manifest.json').read_bytes())=='568792dd4c8d730770103cc44fb3574e1b7b81f860b20a77b1eb19bb50b220da','manifest pin')
with contextlib.redirect_stdout(io.StringIO())as output:load(P/'verify-source.py')
source=json.loads(output.getvalue());ck(source['checks']==49,'source delta tests')
# Existing focused101 checks, run in reviewer-owned HOME scratch. Only mock response and
# readiness fixtures are rebound to a retained identity; native data remains explicitly synthetic.
idpath=B/'wake-window-trial-20261028gc/identity-01/identity.json';idraw=idpath.read_bytes();identity=json.loads(idraw);ck(identity['devnum']=='66'and len(identity)==16,'retained current instance16 fields')
s=(P/'test-host.py').read_text().replace("dir=P/'host-environment/tmp'","dir=Path("+repr(str(D/'tmp'))+")")
s=s.replace("rd['identity'].update(devnum='60',deviceNode='/dev/bus/usb/007/060',nodeStat='bd:33b:12345')","rd['identity']="+repr(identity))
s=s.replace("text=m.envelope(raw)","raw=(json.dumps(dict(json.loads(raw),device=66))+'\\n').encode();text=m.envelope(raw)")
with contextlib.redirect_stdout(io.StringIO())as output:m=load(P/'test-host.py',s)
mock=json.loads(output.getvalue());ck(mock['checks']==101 and mock['maxCommandBytes']<=8192 and mock['maximumSemanticEnvelopeBytes']==57747,'identity66 mock checks/caps')
cmds=m.m.commands
ck(any('--execute --device 66' in c for c in cmds),'actual66 native argument')
ck(any('bd:341:15370520' in c and '19:42745' in c and '/dev/bus/usb/007/066' in c for c in cmds),'all retained identity-specific guards in generated command')
ck(all(len(c.encode())<=8192 for c in cmds),'all commands bounded')
# Local readiness is a pure validator, not a queue proof. Exercise actual16-field shape,
# exact family, node minor, descriptors, boot, lineage and explicit evidence references.
r=m.r
with __import__('tempfile').TemporaryDirectory(dir=D/'tmp')as tmp:
 f=Path(tmp)/'readiness.json';rd=copy.deepcopy(m.rd)
 def accept(v):
  raw=json.dumps(v).encode();f.write_bytes(raw);return r.load_readiness(f,h(raw))
 ck(accept(rd)[0]['identity']==identity,'all retained identity fields admitted with synthetic premise')
 mutations=[('schema','fn-combined-event-readiness-decision-v1'),('accepted',False),('interfaceUnbound',False),('noHolders',False),('endpointQueueProof',True)]
 for k,v in mutations:
  bad=copy.deepcopy(rd);bad[k]=v
  try:accept(bad)
  except(ValueError,TypeError,KeyError):ck(True,'readiness refusal')
  else:raise ValueError('readiness admission unexpectedly relaxed '+k)
 for k,v in [('devnum','65'),('deviceNode','/dev/bus/usb/007/065'),('nodeStat','bd:340:15370520'),('boot','different'),('descriptorsSha256','0'*64),('busnum','8'),('authorized','0'),('interfaceNumber','03')]:
  bad=copy.deepcopy(rd);bad['identity'][k]=v
  try:accept(bad)
  except(ValueError,TypeError,KeyError):ck(True,'identity refusal')
  else:raise ValueError('identity admission unexpectedly relaxed '+k)
 ck(rd['endpointQueueProof']is False,'no synthetic queue claim')
for name in ['time-fixture.json','partial-fixture.json']:
 n,rows,i=m.parser.parse_native((P/name).read_text())
 if name.startswith('time-'):ck(n['terminal']=='TimeLimit'and n['accepted']and len(rows)==76,'76complete ordinary deadline')
 else:ck(n['terminal']=='TimeLimitedPartial'and not n['accepted']and len(rows)==19 and n['cyclesStarted']==20 and i['protocolAccepted']is False,'partial refusal never promoted')
print(json.dumps({'schema':'fz-independent-validation-v1','checks':checks,'sourceChecks':source['checks'],'inheritedFocusedChecks':mock['checks'],'identityFieldCount':len(identity),'mockIdentitySourceSha256':h(idraw),'mockOnlyNotActualReadiness':True,'mockCommands':mock['mockCommands'],'maxCommandBytes':mock['maxCommandBytes'],'maximumSemanticEnvelopeBytes':mock['maximumSemanticEnvelopeBytes'],'inventoryFiles':len(inv['files']),'sourceInventorySha256':h(invraw),'targetOperations':0,'rootCalls':0,'networkOperations':0},indent=2,sort_keys=True))
