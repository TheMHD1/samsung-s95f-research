#!/usr/bin/env python3
import hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent
def entry(p):
 b=p.read_bytes();return {'path':str(p.relative_to(P)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
payload=[entry(P/'bin/Release/net6.0'/('TconLogSingleRead'+ext)) for ext in ['.dll','.deps.json','.runtimeconfig.json']]
checkpoint={'schema':'fk-host-build-checkpoint-v1','payload':payload,'nativeTests':entry(P/'native-tests.json'),'hostNormal':entry(P/'host-validation.normal.json'),'hostOptimized':entry(P/'host-validation.optimized.json'),'actualTargetReadPerformed':False,'rootWrapperImplemented':False}
(P/'host-build-checkpoint.json').write_text(json.dumps(checkpoint,indent=2,sort_keys=True)+'\n')
files=sorted(p for p in P.iterdir() if p.is_file() and p.name!='source-inventory.json')
files+=sorted((P/'bin/Release/net6.0').glob('TconLogSingleRead.*'))
inventory={'schema':'fk-source-inventory-v1','files':[entry(p) for p in files],'excludes':['obj/','host-environment/','reviews/','__pycache__/'],'actualTargetReadPerformed':False}
(P/'source-inventory.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
