#!/usr/bin/env python3
"""Narrow scientific qualifier tests; no transport, runtime build, or target calls."""
import copy,hashlib,json,types
from pathlib import Path
P=Path(__file__).resolve().parent;checks=0
m=types.ModuleType('gg_parser');m.__file__=str(P/'parse-result.py');exec(compile((P/'parse-result.py').read_bytes(),m.__file__,'exec'),m.__dict__)
def check(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
f=json.loads((P/'fixture.json').read_bytes());baseline=f['retained'][0]['transfers'][-1][5]
last=max(c['transfers'][2*i][4]for c in f['retained']if c['cycle']>1 for i,w in enumerate(c['windows'])if w['name']=='R')
cleanupR=next(c for c in f['controls']if c['role']=='prerestore-R')['transfers'][0][4]
restoredEnd=next(c for c in f['controls']if c['role']=='restored-R')['transfers'][-1][5]
check(baseline<last<cleanupR<restoredEnd<f['endUs'],'synthetic timing landmarks')
for name,down,qualified in [('baseline_equal',baseline,True),('inside',baseline+1,True),('just_before_final_optional_R',last-1,True),('equal_final_optional_R',last,False),('after_final_optional_R',last+1,False),('cleanup_R_only',cleanupR-1,False),('after_restored_R',restoredEnd+1,False),('native_end',f['endUs'],False)]:
 v=copy.deepcopy(f);v['intervention']['endUs']=down
 for call in v['intervention']['calls']:call['beforeUs']=call['afterUs']=down
 native,rows,result=m.parse_native(json.dumps(v)+'\n');exposure=result['keyExposure']
 check(native['accepted']is True and result['accepted']is True and result['protocolAccepted']is True,'protocol preserved '+name)
 check(result['keyExposureQualified']is qualified and result['downBeganBeforeLaterOptionalR']is qualified,'scientific overlap '+name)
 check(exposure['baselineEndUs']==baseline and exposure['downBeforeUs']==down and exposure['sameNativeClock']is True,'clock source evidence '+name)
 check(len(exposure['candidateOptionalRHeaders'])==2 and all(c['cycle']>1 and c['windowIndex']in [0,7]for c in exposure['candidateOptionalRHeaders']),'only deduplicated later optional R candidates '+name)
 if qualified:
  check(exposure['witnessOptionalRHeader']['headerBeforeUs']>down>=baseline,'strict later / inclusive baseline '+name)
  check(exposure['reason']=='successful_down_before_later_optional_R_header','qualified reason '+name)
 else:
  check(exposure['witnessOptionalRHeader']is None and exposure['reason']=='no_later_optional_R_header_after_down','late reason '+name)
 check(exposure['uiConsumptionProven']is False and exposure['keyCausalityEstablished']is False and exposure['physicalPictureObserved']is False,'limited scientific claim '+name)
# A refusal stays a refusal, without inspecting partial capture/key structures.
v=copy.deepcopy(f);v['accepted']=False
_,_,result=m.parse_native(json.dumps(v)+'\n');check(not result['keyExposureQualified']and result['keyExposureReason']=='protocol_not_accepted','refusal not qualified')
# The scientific qualifier itself is byte-identical to the frozen FG implementation.
parent=(P.parent/'combined-event-checkpoints-20261028fg/parse-result.py').read_text();local=(P/'parse-result.py').read_text()
def qualifier(s):return s[s.index('def key_exposure('):s.index('def parse_native(')]
check(qualifier(parent)==qualifier(local),'full inherited key exposure qualifier exact')
print(json.dumps({'schema':'gg-key-exposure-tests-v1','checks':checks,'cases':8,'targetOperations':0,'qualifierUnchanged':True},sort_keys=True))
