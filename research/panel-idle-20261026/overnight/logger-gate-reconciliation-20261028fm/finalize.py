#!/usr/bin/env python3
import hashlib,json,pathlib,re,types
P=pathlib.Path(__file__).resolve().parent
def ent(p):
 b=p.read_bytes();return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
names=['Protocol.cs','NativeBinding.cs','Engine.cs','ReceiptMain.cs','HostTests.cs','LoggerGateReconciliation.csproj','NuGet.Config','native-tests.json','fixture.json']+[f'bin/Release/net6.0/LoggerGateReconciliation{x}'for x in ['.dll','.deps.json','.runtimeconfig.json']]
cp={'schema':'fm-host-checkpoint-v1','targetOperations':0,'files':{n:ent(P/n)for n in names},'nativeQualification':json.loads((P/'native-tests.json').read_text())}
(P/'host-build-checkpoint.json').write_text(json.dumps(cp,indent=2,sort_keys=True)+'\n')
w=P/'run-once.py';s=w.read_text();s=re.sub(r"CHECKPOINT_SHA = '[0-9a-f]{64}'","CHECKPOINT_SHA = '"+ent(P/'host-build-checkpoint.json')['sha256']+"'",s);s=re.sub(r"PARSER_SHA = '[0-9a-f]{64}'","PARSER_SHA = '"+ent(P/'parse-result.py')['sha256']+"'",s);w.write_text(s)
m=types.ModuleType('fm_finalizer');m.__file__=str(w);exec(compile(s,str(w),'exec'),m.__dict__);manifest,_=m.build_manifest();(P/'deployment-manifest.json').write_bytes(m.manifest_bytes(manifest))
files=sorted(p for p in P.iterdir()if p.is_file()and p.name!='source-inventory.json')+sorted((P/'bin/Release/net6.0').glob('LoggerGateReconciliation.*'))
(P/'source-inventory.json').write_text(json.dumps({'schema':'fm-source-inventory-v1','files':[dict(path=str(p.relative_to(P)),**ent(p))for p in files],'targetOperations':0,'excludes':['reviews/','obj/','host-environment/','__pycache__/']},indent=2,sort_keys=True)+'\n')
