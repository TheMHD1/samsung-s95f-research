#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,re
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
files=['Program.cs','ClaimDiagnostic.csproj','parse-result.py','fixture.json']+['bin/Release/net6.0/ClaimDiagnostic'+x for x in ['.dll','.deps.json','.runtimeconfig.json']]
obj={'schema':'do-usb-owned-claim-diagnostic-host-checkpoint-v1','target_executions':0,'files':{n:{'bytes':len((P/n).read_bytes()),'sha256':sha((P/n).read_bytes())}for n in files}}
raw=(json.dumps(obj,indent=2,sort_keys=True)+'\n').encode();(P/'host-build-checkpoint.json').write_bytes(raw)
f=P/'run-once.py';s=f.read_text();s=re.sub("CHECKPOINT_SHA = '[^']+'","CHECKPOINT_SHA = '"+sha(raw)+"'",s);s=re.sub("PARSER_SHA = '[^']+'","PARSER_SHA = '"+sha((P/'parse-result.py').read_bytes())+"'",s);f.write_text(s)
