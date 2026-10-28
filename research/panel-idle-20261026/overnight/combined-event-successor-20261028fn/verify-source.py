#!/usr/bin/env python3
"""Explicit finite production equivalence to frozen FG, with all deltas enumerated."""
from pathlib import Path
import difflib,hashlib,json,re
P=Path(__file__).resolve().parent;B=P.parent;G=B/'combined-event-checkpoints-20261028fg';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def check(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def family(name,s):
 if name in ['NativeBinding.cs','OnsetKey.cs','wake-check.py','ScoreCheckpoints.cs']:return s
 return s.replace('fg','fn').replace('FG','FN').replace('CombinedEventCheckpoints','CombinedEventSuccessor').replace('fn-stockevent-checkpoints-v1','fg-stockevent-checkpoints-v1')
def normalize(s):
 for key in ['PARSER_SHA','CHECKPOINT_SHA']:s=re.sub(key+" = '[0-9a-f]{64}'",key+" = '<derived-pin>'",s)
 return s
delta=json.loads((P/'successor-delta.json').read_bytes())['changes'];production=['Protocol.cs','Engine.cs','NativeBinding.cs','OnsetKey.cs','ScoreCheckpoints.cs','ReceiptMain.cs','CombinedEventCheckpoints.csproj','NuGet.Config','parse-result.py','run-once.py','prepare-readiness.py','wake-check.py'];reports=[];diffs=[]
for name in production:
 original=(G/name).read_text();expected=family(name,original)
 for row in delta:
  if row['file']==name:
   check(expected.count(row['old'])==1,'unique original anchor '+name);expected=expected.replace(row['old'],row['new'])
 target=name.replace('CombinedEventCheckpoints','CombinedEventSuccessor');actual=(P/target).read_text()
 check(normalize(expected)==normalize(actual),'complete production equivalence '+name)
 diff=''.join(difflib.unified_diff(original.splitlines(True),actual.splitlines(True),fromfile='FG/'+name,tofile='FN/'+target))
 diffs.append(diff)
 reports.append({'file':target,'parentSha256':sha(original.encode()),'successorSha256':sha(actual.encode()),'diffSha256':sha(diff.encode()),'changedLines':sum(line.startswith(('+','-'))and not line.startswith(('+++','---'))for line in diff.splitlines())})
check((P/'production-diff.patch').read_text()==''.join(diffs),'entire production diff artifact exact')
s=(P/'Engine.cs').read_text()
for token in ['CleanupReserveUs=6*PairBudgetUs+MarginUs','KeyJoinReserveUs=7_000_000','WholeBudgetUs=40_000_000','phase==ProtocolPhase.ReadyForHeader&&!clockLost&&o.Error==null','phase=ProtocolPhase.ExpectingPayload','ops.Bulk(fd,false,payload,2)','LoggerR(after,0)','Context(m,c)','c[8]<=4&&(!initial||c[8]==3)','x.Current.Windows[2].Buffer[8]==3']:
 check(token in s,'engine retained invariant '+token)
check((P/'wake-check.py').read_bytes()==(B/'reader-wake-checkpoints-20261028fc/wake-check.py').read_bytes(),'FC wake exact')
parent=(G/'parse-result.py').read_text();local=(P/'parse-result.py').read_text();a='def key_exposure(';z='def parse_native('
check(parent[parent.index(a):parent.index(z)]==local[local.index(a):local.index(z)],'full key exposure qualifier exact')
print(json.dumps({'schema':'fn-source-equivalence-v1','sourceChecks':checks,'targetOperations':0,'productionFiles':reports,'explicitProductionDeltaCount':len(delta),'pendingPairClockWriteBindingAccountingUnchanged':True,'legacy58ByteRowSchemaUnchanged':True,'fcWakeUnchanged':True},sort_keys=True))
