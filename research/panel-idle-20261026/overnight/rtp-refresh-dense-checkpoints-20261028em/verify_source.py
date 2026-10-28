#!/usr/bin/env python3
"""Offline exact EH derivative proof. No root transport import or target calls."""
from pathlib import Path
import hashlib,json,re
D=Path(__file__).resolve().parent;P=D.parent/'rtp-refresh-checkpoints-20261028eh'
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0
def need(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1
def text(n):return(D/n).read_text()
def base(s):return s.replace('RefreshCheckpoints','DenseRefreshCheckpoints').replace('researcher-eh-','researcher-em-').replace('eh-refresh-checkpoint','em-dense-refresh-checkpoint').replace('key-eh-v1','key-em-v1')
need(sha((P/'source-inventory.json').read_bytes())=='38ae37ba3e64c516d0e9aa5d2e811d7c6d85e0164f6a155e3bb93ff0990991fd','frozen EH inventory')
need(sha((P/'deployment-manifest.json').read_bytes())=='d0059b32e4e3d99a398a3763934e8927cd2967126c6d1ad9e76d8bf069f3059e','frozen EH manifest')
pins=json.loads(text('parent-pins.json'))
for n,row in pins['files'].items():
 b=(P/n).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'EH source '+n)
for n in ('NativeBinding.cs','OnsetKey.cs','NuGet.Config'):need((D/n).read_bytes()==(P/n).read_bytes(),'byte-identical '+n)
s=base((P/'Program.cs').read_text()).replace('DurationUs = 15_000_000','DurationUs = 2_000_000').replace('public long PeriodUs = 250_000','public long PeriodUs = 25_000').replace('durationMs = 15000','durationMs = 2000').replace('nominalPeriodMs = 250','nominalPeriodMs = 25')
need(s==text('Program.cs'),'exact default duration/period/schema Program delta; full Run/ReadPair/ReadSet identical')
need(base((P/'ScoreCheckpoints.cs').read_text())==text('ScoreCheckpoints.cs'),'exact54-byte layout/capacity/size tests; schema only')
need(base((P/'ReceiptMain.cs').read_text())==text('ReceiptMain.cs'),'exact exclusive receipt, stage prefix only')
need(base((P/'SynchronizedOnset.csproj').read_text())==text('SynchronizedOnset.csproj'),'assembly name only')
need((P/'transport-parser.py').read_text().replace('15_000_000','2_000_000')==text('transport-parser.py'),'exact transport parser duration-only delta')
s=(P/'parent-synchronized-parser.py').read_text();s=re.sub(r"PARENT_SHA = '[^']+'", "PARENT_SHA = '"+sha((D/'transport-parser.py').read_bytes())+"'",s)
need(s==text('parent-synchronized-parser.py'),'unchanged key parser except transport pin')
s=base((P/'parse-result.py').read_text()).replace('EH refresh','EM dense refresh').replace("'EH schema/checkpoints'","'EM schema/checkpoints'").replace('15000000','2000000').replace('250000','25000').replace('15s cooperative observation, at most60 checkpoints, distinct from DP20s/80;250ms nominal sequential polling','2s cooperative observation, at most60 checkpoints;25ms requested start-to-start period, no guaranteed sampling rate; higher polling load than EH').replace('250ms polling may miss','25ms requested polling can still miss')
s=re.sub(r"PARENT_SHA='[^']+'", "PARENT_SHA='"+sha((D/'parent-synchronized-parser.py').read_bytes())+"'",s)
need(s==text('parse-result.py'),'strict decoder exact schemas/budget/interpretation/pin deltas only')
s=base((P/'run-once.py').read_text()).replace('15000000','2000000').replace('250000','25000')
def unpin(s):return re.sub(r"(CHECKPOINT_SHA|PARSER_SHA) = '[^']+'",r"\1 = '<PIN>'",s)
need(unpin(s)==unpin(text('run-once.py')),'exact wrapper delta; staging/framing/ambiguity/cleanup untouched')
need('long sleep = cycleStart + config.PeriodUs - after!.Value;'in text('Program.cs') and 'clock.SleepUs(Math.Min(sleep, untilDeadline))'in text('Program.cs'),'requested cycle-start pacing, service time consumed first')
need('public int MaxCycles = 60;'in text('Program.cs') and 'Size=54, Capacity=60'in text('ScoreCheckpoints.cs'),'60cycle/3240raw byte cap')
# EI cached readiness builder is retained source; all command generation unchanged.
q=D.parent/'refresh-checkpoint-trial-20261028ei'/'prepare-readiness.py';s=q.read_text();a=s.index('WRAPPERS = {');z=s.index('\n}\n',a)+3
s=s[:a]+"WRAPPERS = {\n    'em': ('rtp-refresh-dense-checkpoints-20261028em/run-once.py', 'em-dense-refresh-checkpoint-readiness-decision-v1'),\n}\n"+s[z:];s=s.replace('ei_readiness','em_readiness').replace('EI_CURRENT_READY','EM_CURRENT_READY').replace('ei-fresh-cached','em-fresh-cached')
need(s==text('prepare-readiness.py'),'cached-only readiness derivative exact map/schema/name delta')
lineage={'schema':'em-dense-refresh-source-lineage-v1','parentEhInventorySha256':sha((P/'source-inventory.json').read_bytes()),'parentEhManifestSha256':sha((P/'deployment-manifest.json').read_bytes()),'readinessBuilderParentSha256':sha(q.read_bytes()),'targetOperations':0,'networkOperations':0,'readMapChanged':False,'transportAndRunChanged':False,'keyPathChanged':False,'checkpointBytes':54,'maximumCheckpoints':60,'requestedPeriodUs':25000,'cooperativeDurationUs':2000000,'nominalMaximumCycleStartSpanUs':1475000,'actualRateGuaranteed':False,'serviceTimeOrKeySchedulingCanReduceCoverage':True,'nativeProcessAlarmImplemented':False,'perBulkTimeoutMs':2000,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'newReads':0,'writes':0,'historicalRefreshSequenceObserved':False,'physicalPictureObserved':False,'independentReviewPending':True}
need(json.loads(text('source-lineage.json'))==lineage,'source lineage exact')
print(json.dumps({'schema':'em-dense-refresh-source-verification-v1','checksPassed':checks,'targetOperations':0,'lineage':lineage},indent=2,sort_keys=True))
