#!/usr/bin/env python3
"""Pure design/source/arithmetic checks; no imported transports or helpers."""
import hashlib,json,base64
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
pins=json.loads((D/'input-pins.json').read_bytes())['files']
for row in pins:
 raw=(B/row['path']).read_bytes();ck(len(raw)==row['bytes']and sha(raw)==row['sha256'],'pinned '+row['path'])
N=B/'combined-event-successor-20261028fn'
protocol=(N/'Protocol.cs').read_text();engine=(N/'Engine.cs').read_text();score=(N/'ScoreCheckpoints.cs').read_text();parser=(N/'parse-result.py').read_text()
for needle,source in [('MaxCycles = 56',protocol),('const int Size=58, Capacity=56',score),('config.MaxCycles<=56',engine),('config.DurationUs==2_000_000&&config.PeriodUs==25_000',engine),("integer(c['cycle'],0,56)",parser),("integer(rows['count'],0,56)",parser),("integer(v[k],0,1000)",parser),('TimeLimitedPartial',engine),('if(!full)break;',engine),('x.ObservationComplete&&',engine)]:ck(needle in source,'actual bound/partial source '+needle)
ck(engine.index('LoggerR(pre,0);Need(ClassifyRt(pre)==RtState.Clean')<engine.index('WriteLogger(ops,clock,x,fd,ref phase,true)')<engine.index('key?.Start(clock)'),'initial clean before arm before key')
ck('WholeBudgetUs=40_000_000'in engine and 'PairBudgetUs=4_000_000, MarginUs=2_000_000, CleanupReserveUs=6*PairBudgetUs+MarginUs'in engine and 'KeyJoinReserveUs=7_000_000'in engine,'budget constants')
cap=81;rawbytes=cap*58;b64bytes=len(base64.b64encode(bytes(rawbytes)));oldb64=len(base64.b64encode(bytes(56*58)))
ck(rawbytes==4698 and b64bytes==6264 and oldb64==4332 and b64bytes-oldb64==1932,'exact row arithmetic')
ck(8*cap+12==660 and 2*(8*cap+12)==1320 and 8*cap+10==658,'fixed transfer arithmetic')
ck(1320>1000,'old parser bound would reject extended cap')
ck((cap-1)*25000==2000000,'81 cycle start lower-bound reasoning')
ck(18273+1932==20205 and 20205<24576,'planning size estimate, not certified upper bound')
fw=json.loads((B/'combined-live-trigger-trial-20261028fw/refusal-analysis/decoded.json').read_bytes());ck(fw['leftAttempted']is False and fw['loggerArmAttempted']is False and fw['prearmR']['rtLimitTuple']==[1,4097,0,40]and fw['baselineToFaultReadGapUs']==288733304,'actual FW missed prearm gap')
helper=(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py').read_text();ei=(B/'refresh-checkpoint-trial-20261028ei/recover-eb-fault.py').read_text();bv=(B/'recovery-quickpath-20261027bv/README.md').read_text()
ck('apps_gate'in ei and 'current_tab'not in helper,'separate higher-level Apps gate')
ck('current_tab'not in helper and 'mode2_invocations'in ei and "manifest['operation'] == 41 and manifest['mode'] == 2"in helper,'fixed helper no tab predicate')
ck('owner-observed success'in bv and 'populated Apps page'in bv,'empirical Apps policy lineage')
plan=(D/'README.md').read_text()
for phrase in ['not necessarily constructible','not a known saver timeout','No code/helper implementation','TimeLimitedPartial','no automatic reset','not assumed to work']:ck(phrase in plan,'design limitation '+phrase)
print(json.dumps({'schema':'fx-design-validation-v1','checks':checks,'inputPins':len(pins),'implementationCreated':False,'targetOperations':0,'rootCalls':0,'networkOperations':0,'optionAConditional':True,'liveSaverMode2NotQualified':True,'optionBProposedCap':81,'optionBMaxHeaders':660,'optionBMaxBulks':1320,'newReceiptWorstProven':False},sort_keys=True))
