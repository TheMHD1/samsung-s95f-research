#!/usr/bin/env python3
"""Host-only local artifact pins; never imports root transport."""
from pathlib import Path
import hashlib,json,re,subprocess
D=Path(__file__).resolve().parent;runtime='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet';sha=lambda b:hashlib.sha256(b).hexdigest()
r=subprocess.run([runtime,str(D/'bin/Release/net6.0/QuiescentCheckpoints.dll'),'--host-fixture'],check=True,capture_output=True);json.loads(r.stdout);(D/'fixture.json').write_bytes(r.stdout)
names=['Program.cs','OnsetKey.cs','ScoreCheckpoints.cs','NativeBinding.cs','ReceiptMain.cs','SynchronizedOnset.csproj','NuGet.Config','parent-pins.json','source-lineage.json','parse-result.py','parent-synchronized-parser.py','transport-parser.py','fixture.json']+['bin/Release/net6.0/QuiescentCheckpoints'+s for s in ('.dll','.deps.json','.runtimeconfig.json')]
o={'schema':'er-quiescent-checkpoint-host-checkpoint-v1','target_executions':0,'files':{n:{'bytes':len((D/n).read_bytes()),'sha256':sha((D/n).read_bytes())}for n in names}};raw=(json.dumps(o,indent=2,sort_keys=True)+'\n').encode();(D/'host-build-checkpoint.json').write_bytes(raw)
p=D/'run-once.py';s=p.read_text();s=re.sub(r"CHECKPOINT_SHA = '[^']+'","CHECKPOINT_SHA = '"+sha(raw)+"'",s);s=re.sub(r"PARSER_SHA = '[^']+'","PARSER_SHA = '"+sha((D/'parse-result.py').read_bytes())+"'",s);p.write_text(s)
