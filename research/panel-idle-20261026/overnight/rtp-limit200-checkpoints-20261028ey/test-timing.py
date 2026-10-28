#!/usr/bin/env python3
"""Offline cadence checks using only the managed fake fixture and pure arithmetic."""
from pathlib import Path
import base64,copy,hashlib,json,struct,subprocess,types
D=Path(__file__).resolve().parent;checks=0

def check(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1
p=types.ModuleType('em_timing_decoder');p.__file__=str(D/'parse-result.py');exec(compile(Path(p.__file__).read_bytes(),p.__file__,'exec'),p.__dict__)
r=subprocess.run(['${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet',str(D/'bin/Release/net6.0/Limit200Checkpoints.dll'),'--checkpoint-fixture-clean'],capture_output=True,check=True)
n,_,_,_,q=p.parse_native(r.stdout.decode());rows=q['scoreCheckpoints']['rows']
check(n['terminalReason']=='CycleLimit'and len(rows)==56,'56-cycle fake path under2s')
check(n['deadlineUs']-n['startUs']==2_000_000,'exact duration')
check(rows[-1]['hReadBracket']['headerBeforeUs']-rows[0]['hReadBracket']['headerBeforeUs']==55*25_000,'requested25ms start cadence actually reflected in fake H timestamps')
for a,b in zip(rows,rows[1:]):
 check(b['hReadBracket']['headerBeforeUs']-a['hReadBracket']['headerBeforeUs']==25_000,'fake H spacing')
 check(b['hReadBracket']['dataAfterUs']-a['hReadBracket']['dataAfterUs']==25_000,'fake H end spacing')
check(n['headersSent']==448 and n['bulkTransfers']==896,'unchanged eight-pair cycles')
# This is the exact Run sleep arithmetic. Overrun adds no catch-up sleep,
# and a pending matched IN still obeys ReadPair rather than a sampling deadline.
def sleep_for(service,remaining):return min(max(0,25_000-service),max(0,remaining))
for service in (0,1,100,1600,24999,25000,25001,50000,2000000):
 for remain in (0,1,100,24999,25000,2000000):
  x=sleep_for(service,remain);check(0<=x<=remain and x<=max(0,25000-service),'bounded sleep')
  if service>=25000:check(x==0,'no sleep on service overrun')
check(sleep_for(1600,2000000)==23400,'service latency consumes requested interval')
check(n['endUs']>=rows[-1]['hReadBracket']['dataAfterUs'] and n['endUs']-n['startUs']<2_000_000,'actual fake exposure shorter than ceiling')
old=copy.deepcopy(n);old['deadlineUs']=old['startUs']+15_000_000
try:p.parse_native(json.dumps(old))
except ValueError:check(True,'old EH deadline rejected')
else:raise ValueError('old EH accepted')
old=copy.deepcopy(n);old['schema']='managed-usb-rt-synchronized-key-eh-v1'
try:p.parse_native(json.dumps(old))
except ValueError:check(True,'old EH schema rejected')
else:raise ValueError('old EH schema accepted')
print(json.dumps({'schema':'ey-cadence-validation-v1','checksPassed':checks,'fakeHStartSpanUs':rows[-1]['hReadBracket']['headerBeforeUs']-rows[0]['hReadBracket']['headerBeforeUs'],'fakeNativeSpanUs':n['endUs']-n['startUs'],'actualTargetSamplingRateGuaranteed':False,'targetOperations':0},sort_keys=True))
