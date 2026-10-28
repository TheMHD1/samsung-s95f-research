#!/usr/bin/env python3
"""Revalidate frozen FL positive source witnesses and FH C8 fixture; no transport."""
from pathlib import Path
import base64,hashlib,json
P=Path(__file__).resolve().parent;B=P.parent;F=B/'logger-context-transient-20261028fl';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
raw=(F/'source-audit.json').read_bytes();need(sha(raw)=='804cf3e296660bc398d14061eadc8ff2db62c2621a67ad74c43fee1e4a44b083','frozen FL report')
need(sha((F/'source-inventory.json').read_bytes())=='30d0327e57116618ee5246078f99089aeb9817f23a09bf98033343f931d1b47d','frozen FL inventory')
for r in json.loads((F/'source-inventory.json').read_bytes())['files']:
 b=(F/r['path']).read_bytes();need(len(b)==r['bytes']and sha(b)==r['sha256'],'FL inventory '+r['path'])
a=json.loads(raw);need(a['positive_stock_values']==[0,1,2,3,4]and a['global_value_domain_complete']is False and a['zero_requires_reset']is False,'positive source domain, not exhaustive')
need(a['context_field_cpu']=='0x20000bc8'and a['cross_core_source_cpu']=='0x200158a8'and a['mapped_source']=='0x450158a8','exact selected object domains')
for r in json.loads((F/'input-pins.json').read_bytes())['inputs']:
 b=(B/r['path']).read_bytes();need(len(b)==r['bytes']and sha(b)==r['sha256'],'FL source input '+r['id'])
asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
for r in a['source_spans']:
 at=int(r['file_offset'],16);va=int(r['va'],16);end=int(r['end_exclusive'],16)
 need(at==va+(0x40200 if r['image']==1 else 0x200),'image mapping '+r['role']);need(sha(asset[at:at+end-va])==r['sha256'],'source span '+r['role'])
fh=B/'combined-event-trial-20261028fh/capture-01/native.receipt.json';b=fh.read_bytes();v=json.loads(b);current=next(c for c in v['retained']if c['role']=='current');c=base64.b64decode(next(w['raw']for w in current['windows']if w['name']=='C'))
need(c.hex()=='70088007400b5c010000000000000000'and current['cycle']==19,'actual FH current C8 zero fixture')
need(v['accepted']is False and v['phase']=='ReadyForHeader'and v['released']and v['closed']and v['loggerMayRemain'],'FH refusal/lifecycle distinct')
print(json.dumps({'schema':'fn-context-qualification-v1','checks':checks,'targetOperations':0,'flReportSha256':sha(raw),'positiveRuntimeValues':[0,1,2,3,4],'globalDomainComplete':False,'prearmAndFirstBaselineC8':3,'contextCpu':'0x20000bc8','loggerCpu':'0x20012406','loggerBus':'0x47012406','fhReceipt':{'path':str(fh.relative_to(B)),'bytes':len(b),'sha256':sha(b)},'fhCurrentC':{'bytes':len(c),'sha256':sha(c),'c7':c[7],'c8':c[8]},'sourceSemantics':'derived MULTI/AP_EXCO byte0 independent from byte3d8; runtime clear and four setter direct callers yield positive0..4; callback copies to C8; no bounded return-to3','admission':'prearm and first full clean baseline remain3; later observation and fresh cleanup positive0..4 only; other context/phase/clock guards retained'},sort_keys=True))
