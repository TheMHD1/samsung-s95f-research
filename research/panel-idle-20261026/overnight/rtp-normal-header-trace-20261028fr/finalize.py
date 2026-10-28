#!/usr/bin/env python3
"""Freeze FR's retained input pins and derived artifacts; no target access."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;B=P.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def pin(p):
 b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b)}
inputs=['selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin']
for directory,names in [('fault-event-logging-options-20261028et',['README.md','source-audit.json','input-pins.json']),('rtp-checkpoint-hook-design-20261028ds',['README.md','source-audit.json','input-pins.json']),('rtp-record-capture-20261028dm',['instrumentation-map.md','source-lineage.json']),('rtp-fixed-reference-qualification-20261028dr',['README.md','normal-qualification.json']),('onset-trial-20261028cb/operand-analysis',['operand-findings.md','analyze_operands.py']),('combined-event-successor-20261028fn',['ScoreCheckpoints.cs','parse-result.py']),('combined-event-successor-trial-20261028fo/capture-01',['native.receipt.json','baseline-ring.bin','post-ring.bin']),('combined-event-successor-trial-20261028fo/live-analysis',['README.md','verify.py','decoded.json','input-pins.json','source-inventory.json'])]:inputs += [directory+'/'+n for n in names]
inputs += ['/tmp/tcon-capstone/capstone/'+n for n in ['__init__.py','arm.py','lib/libcapstone.so']]
write(P/'input-pins.json',{'schema':'fr-source-input-pins-v1','targetOperations':0,'files':[dict(path=n,**pin(Path(n)if Path(n).is_absolute()else B/n))for n in inputs]})
if (P/'source-audit.json').exists()and(P/'source-audit.optimized.json').exists():
 a=(P/'source-audit.json').read_bytes();b=(P/'source-audit.optimized.json').read_bytes()
 if a!=b:raise ValueError('normal/optimized mismatch')
 report=json.loads(a)
 write(P/'validation.json',{'schema':'fr-validation-v1','targetOperations':0,'sourceChecks':report['checks'],'normalOptimizedIdentical':True,'reportSha256':sha(a),'executableModified':False,'actualFpProven':False,'epochProven':False,'physicalCorrectnessProven':False})
write(P/'source-inventory.json',{'schema':'fr-source-inventory-v1','targetOperations':0,'files':[dict(path=p.name,**pin(p))for p in sorted(P.iterdir())if p.is_file()and p.name!='source-inventory.json']})
