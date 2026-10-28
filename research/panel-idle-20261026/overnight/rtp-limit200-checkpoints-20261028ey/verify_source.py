#!/usr/bin/env python3
"""Bounded offline EY/ER semantic delta audit; no live adapters imported."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;P=D.parent/'rtp-quiescent-checkpoints-20261028er';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1
def part(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
need(sha((P/'source-inventory.json').read_bytes())=='24d3705adf0537690c55c3383548c18e12a884079fcccbf22b64808202b3be43','frozen ER inventory')
for row in json.loads((P/'source-inventory.json').read_text())['files']:
 raw=(P/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'parent '+row['path'])
for name in ('NativeBinding.cs','OnsetKey.cs','NuGet.Config'):need((D/name).read_bytes()==(P/name).read_bytes(),'byte-identical '+name)
a=(P/'Program.cs').read_text();b=(D/'Program.cs').read_text()
for left,right in [('    static readonly WindowSpec R','    readonly record struct Identity'),('    static PairResult ReadPair','    static PairResult ReadSet'),('    static PairResult ReadSet','    static CaptureDto ToDto'),('    static Outcome Run','    // sysfs binary attributes'),('    // sysfs binary attributes','    sealed class FakeClock')]:
 need(part(a,left,right)==part(b,left,right),'unchanged '+left.strip())
oldclass=part(a,'    static RtState ClassifyRt','    static long? Stamp')
expected=oldclass.replace('int stop = Half(value, 0),','if (Half(value, 0xc4) != 200) return RtState.Unexpected;\n        int stop = Half(value, 0),').replace('Half(value, 0xc4) == 40','Half(value, 0xc4) == 200')
need(part(b,'    static RtState ClassifyRt','    static long? Stamp')==expected,'only fixed200 prefix and Quiescent delta in classifier')
need(part((D/'ScoreCheckpoints.cs').read_text(),'   Need(Count<Capacity',' sealed class ScoreFakeOps')==part((P/'ScoreCheckpoints.cs').read_text(),'   Need(Count<Capacity',' sealed class ScoreFakeOps'),'packed builder byte-identical')
need('Size=58, Capacity=56'in(D/'ScoreCheckpoints.cs').read_text(),'58x56')
for t in ('DurationUs = 2_000_000','PeriodUs = 25_000','MaxCycles = 56'):need(t in b,'same '+t)
need((D/'ReceiptMain.cs').read_text()==(P/'ReceiptMain.cs').read_text().replace('researcher-er-','researcher-ey-').replace('==79','==100').replace('checkpointTestsPassed=79','checkpointTestsPassed=100'),'same receipt entrypoint apart from stage/testcount')
lo=(D/'transport-parser.py').read_text();old=(P/'transport-parser.py').read_text();need(lo==old.replace('classify = "Clean" if actual','classify = "Unexpected" if int.from_bytes(raw[0xc4:0xc6], "little") != 200 else "Clean" if actual').replace('int.from_bytes(raw[0xc4:0xc6], "little") == 40','int.from_bytes(raw[0xc4:0xc6], "little") == 200'),'lower parser exact classification-only delta')
sy=(D/'parent-synchronized-parser.py').read_text();sp=(P/'parent-synchronized-parser.py').read_text();need(sy.replace(sha((D/'transport-parser.py').read_bytes()),sha((P/'transport-parser.py').read_bytes()))==sp,'parent parser unchanged except child hash')
q=(D/'parse-result.py').read_text();need("'a0Low16Above40':(a0&65535)>40"in q and "'publicationBoundMirrorIsActualFpProven':False"in q,'counterfactual40 and actualFP limitation retained')
need("x['startAlternateThreshold']==x['endAlternateThreshold']==200"in q,'compact all-state limit200')
print(json.dumps({'schema':'ey-source-validation-v1','checksPassed':checks,'targetOperations':0,'networkOperations':0,'unchangedReadMapTransportBindingKey':True},sort_keys=True))
