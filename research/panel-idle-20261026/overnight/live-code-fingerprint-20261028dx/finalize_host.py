#!/usr/bin/env python3
"""Host-only checkpoint pins, no TV transport load/invocation."""
from pathlib import Path
import hashlib,json,re,subprocess
D=Path(__file__).resolve().parent;runtime='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet';dll=D/'bin/Release/net6.0/CodeFingerprint.dll';sha=lambda b:hashlib.sha256(b).hexdigest()
r=subprocess.run([runtime,str(dll),'--host-fixture'],check=True,capture_output=True);json.loads(r.stdout);(D/'fixture.json').write_bytes(r.stdout)
names=['Program.cs','NativeBinding.cs','ReceiptMain.cs','HostTests.cs','CodeFingerprint.csproj','NuGet.Config','source-lineage.json','dw-source-pins.json','verify_source.py','parse-result.py','fixture.json']+['bin/Release/net6.0/CodeFingerprint'+s for s in ('.dll','.deps.json','.runtimeconfig.json')]
o={'schema':'dx-code-fingerprint-host-checkpoint-v1','target_executions':0,'files':{n:{'bytes':len((D/n).read_bytes()),'sha256':sha((D/n).read_bytes())}for n in names}}
b=(json.dumps(o,indent=2,sort_keys=True)+'\n').encode();(D/'host-build-checkpoint.json').write_bytes(b)
p=D/'run-once.py';s=p.read_text();s=re.sub(r"CHECKPOINT_SHA = '[^']+'","CHECKPOINT_SHA = '"+sha(b)+"'",s);s=re.sub(r"PARSER_SHA = '[^']+'","PARSER_SHA = '"+sha((D/'parse-result.py').read_bytes())+"'",s);p.write_text(s)
