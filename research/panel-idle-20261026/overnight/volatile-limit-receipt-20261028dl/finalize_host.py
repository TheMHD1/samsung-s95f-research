#!/usr/bin/env python3
"""Refresh an intentionally rebuilt host snapshot. No target access."""
from pathlib import Path
import hashlib,json,re,subprocess
P=Path(__file__).resolve().parent;DOTNET='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet'
def sha(b):return hashlib.sha256(b).hexdigest()
for a in ['set','restore']:(P/('fixture-'+a+'.json')).write_bytes(subprocess.check_output([DOTNET,str(P/'bin/Release/net6.0/FixedLimit.dll'),'--host-fixture-'+a]))
files=['Program.cs','FixedLimit.csproj','parse-result.py','source-lineage.json','fixture-set.json','fixture-restore.json','fixtures/gc-interleaved-selftest.txt']+['bin/Release/net6.0/FixedLimit'+x for x in ['.dll','.deps.json','.runtimeconfig.json']]
obj={'schema':'dl-fixed-limit-host-checkpoint-v1','target_executions':0,'files':{n:{'bytes':len((P/n).read_bytes()),'sha256':sha((P/n).read_bytes())}for n in files}}
raw=(json.dumps(obj,indent=2,sort_keys=True)+'\n').encode();(P/'host-build-checkpoint.json').write_bytes(raw)
f=P/'run-once.py';s=f.read_text();s=re.sub("CHECKPOINT_SHA = '[^']+'","CHECKPOINT_SHA = '"+sha(raw)+"'",s);s=re.sub("PARSER_SHA = '[^']+'","PARSER_SHA = '"+sha((P/'parse-result.py').read_bytes())+"'",s);f.write_text(s)
