#!/usr/bin/env python3
"""GE bounded source/host review; only saved EB replay and explicit mocks."""
from pathlib import Path
import contextlib,copy,hashlib,io,json,sys,tempfile,types
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;P=D.parent;B=P.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def load(p,text=None):
 m=types.ModuleType('review_'+p.stem);m.__file__=str(p);exec(compile(p.read_text()if text is None else text,str(p),'exec'),m.__dict__);return m
def reject(f,s):
 try:f()
 except(ValueError,KeyError,TypeError,OSError):ck(True,s);return
 raise ValueError('unexpected acceptance '+s)
input_rows=json.loads((D/'input-pins.json').read_bytes())['files']
for row in input_rows:
 data=(B/row['path']).read_bytes();ck(len(data)==row['bytes']and sha(data)==row['sha256'],'review input '+row['path'])
invraw=(P/'source-inventory.json').read_bytes();ck(sha(invraw)=='7bf923a4585c75b84c0a33208cf39782a2a3f5ea8270d0f167a182e4b756a1c1','inventory pin')
inv=json.loads(invraw)
for row in inv['files']:
 data=(P/row['path']).read_bytes();ck(len(data)==row['bytes']and sha(data)==row['sha256'],'frozen '+row['path'])
ck(sha((P/'deployment-manifest.json').read_bytes())=='dabb34a5c3c3b9f3e53d3e975d7b1fac798dea55805a5aabb1d3c733d0e9ec23','manifest pin')
with contextlib.redirect_stdout(io.StringIO())as out:load(P/'verify-source.py')
source=json.loads(out.getvalue());ck(source['checks']==108,'source equivalence')
# All replay/negative-fixture scratch is reviewer-owned; no parent author output rewritten.
orig=tempfile.TemporaryDirectory
def private_temp(*args,**kw):kw['dir']=D/'tmp';return orig(*args,**kw)
tempfile.TemporaryDirectory=private_temp
try:
 text=(P/'test-host.py').read_text().replace("scratch=P/'host-environment/tmp'","scratch=Path("+repr(str(D/'tmp'))+")")
 with contextlib.redirect_stdout(io.StringIO())as out:m=load(P/'test-host.py',text)
 host=json.loads(out.getvalue());ck(host['checks']==1044 and host['cases']==73 and host['actualEbSourceCommandsReplayed']==28,'complete inherited qualification')
 # Native/wrapper outputs keep successful helper distinct from context/reinitialization.
 ck(host['identityFields']==16 and host['maxCommandBytes']==4741 and host['shellCommands']==373,'actual source identity and command accounting')
 # Inspect existing saved source through pure API. Each field must match current readiness.
 a=load(P/'admit-fault.py');cap=B/'combined-live-trigger-trial-20261028fw/fault-capture-01';identity=json.loads((cap/'readiness-decision.json').read_bytes())['identity'];digest=sha((cap/'result.json').read_bytes())
 for field in identity:
  bad=copy.deepcopy(identity);bad[field]+='!';reject(lambda:a.admit(cap,digest,bad),'source instance '+field)
 # A clean newer EB snapshot is not a replacement for fault admission.
 clean=B/'wake-window-trial-20261028gc/baseline-capture';current=json.loads((clean/'readiness-decision.json').read_bytes())['identity']
 reject(lambda:a.admit(clean,sha((clean/'result.json').read_bytes()),current),'clean current source must not admit MODE2')
 # Admission's native phase and file proofs are not transferable to another current instance.
 reject(lambda:a.admit(cap,digest,current),'historical fault/newer instance mismatch')
 policy=load(P/'policy.py');valid=policy.BOOT+'\n1.00 0.00\nmemory/eden/current_tab, value = d/ug.tab@Live (String)\nScreenSaverContent.dll\n/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll\n1.01 0.00\n'
 ck(policy.parse_snapshot(valid)['screensaverWindowsPresent'],'second saver spelling admitted')
 for value in [valid.replace('Live','ForYou'),valid.replace('ScreenSaverContent.dll',''),valid.replace('/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll','')]:reject(lambda:policy.parse_snapshot(value),'strict final context')
finally:tempfile.TemporaryDirectory=orig
# No source/payload author file was modified by test replay.
for row in inv['files']:
 data=(P/row['path']).read_bytes();ck(len(data)==row['bytes']and sha(data)==row['sha256'],'unchanged after checks '+row['path'])
print(json.dumps({'schema':'ge-independent-review-validation-v1','checks':checks,'reviewInputFiles':len(input_rows),'sourceChecks':source['checks'],'hostChecks':host['checks'],'cases':host['cases'],'sourceCommandsReplayed':host['actualEbSourceCommandsReplayed'],'shellCommands':host['shellCommands'],'maxCommandBytes':host['maxCommandBytes'],'inventoryFiles':len(inv['files']),'currentCleanSourceRefused':True,'historicalInstanceMismatchRefused':True,'newInstanceQualified':False,'freshEbBaselineQualified':False,'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True,indent=2))
