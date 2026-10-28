#!/usr/bin/env python3
"""Small offline source-equivalence audit; no native execution or target access."""
import ast,hashlib,json,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent;B=P.parent;ER=B/'rtp-quiescent-checkpoints-20261028er';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def tree(p):return ast.parse(p.read_bytes())
def fn(t,name):return next(n for n in ast.walk(t)if isinstance(n,ast.FunctionDef)and n.name==name)
def code(n):return ast.dump(n,include_attributes=False)
def run():
 for row in json.loads((P/'input-pins.json').read_bytes())['files']:
  raw=Path(row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'frozen input '+row['path'])
 original=tree(ER/'run-once.py');current=tree(P/'run-once.py')
 for name in ['old','strict_json','load_pinned','metadata_body','parse_metadata','receipt_envelope','manifest_bytes','payload_guard']:
  need(code(fn(original,name))==code(fn(current,name)),'unchanged '+name)
 old=ast.unparse(fn(original,'run'));new=ast.unparse(fn(current,'run'))
 old=old.replace("    if mode == 'native':\n        record.update(native_invocations=1, target_operations=None, target_operations_status='inflight_or_unknown')\n",'')
 new=new.replace("call(command, native_submission=mode == 'native')",'call(command)')
 need(old==new,'native/selftest command construction identical; only submission boundary accounting moved')
 need(sha((ER/'run-once.py').read_bytes())=='775348193491a927e82731a8e7cbc2d201b903f39d7e9359cc4a17fb921f433f','ER wrapper')
 need(sha((ER/'parse-result.py').read_bytes())=='3bc61ac0176fcb4ad228fe5357ff80ec856a32068705c5aa8a557d81c005a069','ER parser')
 checkpoint=(ER/'host-build-checkpoint.json').read_bytes();need(sha(checkpoint)=='542015d966781606b135ba304916b6913badcd3b912a808af5fa198aced8b535','unchanged ER checkpoint')
 for name,row in json.loads(checkpoint)['files'].items():
  data=(ER/name).read_bytes();need(len(data)==row['bytes']and sha(data)==row['sha256'],'unchanged ER source/payload '+name)
 # Readiness builder differs only in its fixed family map, diagnostic schema and marker.
 a=(ER/'prepare-readiness.py').read_text();b=(P/'prepare-readiness.py').read_text()
 b=b.replace("'fc': ('reader-wake-checkpoints-20261028fc/run-once.py', 'fc-reader-wake-readiness-decision-v1')","'er': ('rtp-quiescent-checkpoints-20261028er/run-once.py', 'er-quiescent-checkpoint-readiness-decision-v1')").replace('fc-fresh-cached-readiness-v1','er-fresh-cached-readiness-v1').replace('FC_CURRENT_READY','ER_CURRENT_READY')
 need(a==b,'readiness derivative exact')
 need(not list(P.glob('*.cs'))and not (P/'bin').exists(),'no new native source/payload')
 return {'accepted':True,'checksPassed':checks,'hostOnly':True,'targetOperations':0}
if __name__=='__main__':print(json.dumps(run()))
