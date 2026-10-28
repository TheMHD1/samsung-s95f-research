#!/usr/bin/env python3
"""One fixed ordinary wake and strict cached Live checkpoint; no controller access."""
import hashlib,json,re,time
from pathlib import Path
BOOT='00000000-0000-4000-8000-000000000000'
KEY_SHA='7284ad5b0117a96a166a4fe327c6361bea998e5d2086a0e1a36d2a3477a87db9'
NAV_SHA='74b60a9611f35a76d272b33677f773cc955838c2c6dda2c3565c371cc9d4d530'
MAX_SNAPSHOTS=10;SETTLE_SECONDS=.25;BUDGET_NS=10000000000;AGE_NS=1000000000;MAX_RESPONSE=65536
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def stamp(clock):
 v=clock();need(type(v)is int and v>=0,'host monotonic integer');return v
def wake_command():
 return ('set -eu\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'+'test -x /usr/bin/input_keyevent\n'+f'test "$(sha256sum /usr/bin/input_keyevent | cut -d " " -f1)" = {KEY_SHA}\n'+'down_status=0\n/usr/bin/input_keyevent XF86AudioRaiseVolume down >/dev/null 2>&1 || down_status=$?\nsleep 0.15\nup_status=0\n/usr/bin/input_keyevent XF86AudioRaiseVolume up >/dev/null 2>&1 || up_status=$?\nprintf "LOCAL_KEY_DOWN_EXIT=%s\\n" "$down_status"\nprintf "LOCAL_KEY_UP_EXIT=%s\\n" "$up_status"\n')
def snapshot_command():
 return ('set -eu\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'+'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\nvconftool get memory/eden/current_tab\nenlightenment_info -topvwins\ncat /proc/uptime\n')
def key_status(text):
 need(type(text)is str and len(text.encode())<=MAX_RESPONSE,'bounded wake response')
 m=re.fullmatch(r'LOCAL_KEY_DOWN_EXIT=([0-9]+)\nLOCAL_KEY_UP_EXIT=([0-9]+)\n',text);need(m is not None,'exact wake status receipt')
 return [int(m[1]),int(m[2])]
def parse_snapshot(text):
 need(type(text)is str and 0<len(text.encode())<=MAX_RESPONSE and text.endswith('\n'),'bounded complete cached response')
 lines=text.splitlines();need(len(lines)>=4 and lines[0]==BOOT,'snapshot boot')
 uptime=r'[0-9]+\.[0-9]+ [0-9]+\.[0-9]+'
 need(re.fullmatch(uptime,lines[1])is not None and re.fullmatch(uptime,lines[-1])is not None,'boot uptime brackets')
 from decimal import Decimal
 need(Decimal(lines[-1].split()[0])>=Decimal(lines[1].split()[0]),'uptime ordering')
 tabs=[v for v in lines if v.startswith('memory/eden/current_tab')]
 need(tabs==['memory/eden/current_tab, value = d/ug.tab@Live (String)'],'exactly one canonical Live row')
 return {'cachedTab':'d/ug.tab@Live','screensaverWindowsPresent':any(v in text for v in ['ScreenSaver.dll','ScreenSaverContent.dll']),'csfsWindowPresent':'/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll'in text,'boot':BOOT,'uptimeBefore':lines[1],'uptimeAfter':lines[-1],'physicalPictureObserved':False}
def qualified(v):return not v['screensaverWindowsPresent']and v['csfsWindowPresent']
def perform(output,call,checkpoint,clock=time.monotonic_ns,sleeper=time.sleep):
 path=output/'wake-checkpoint.json';start=stamp(clock)
 checkpoint.update(schema='fu-live-wake-checkpoint-v1',status='intent',startedHostMonotonicNs=start,wrapperUiOperationsAttempted=1,wrapperUiOperationsCompleted=0,keyChildAttempts=None,keyPairReceiptComplete=False,navigationSourceSha256=NAV_SHA,keyBinarySha256=KEY_SHA,executionConfirmed=False,uiConsumptionProven=False,physicalPictureObserved=False,snapshots=[])
 save(path,checkpoint) # Intent precedes the sole key-pair submission.
 def request(command,label):
  before=stamp(clock);need(0<=before-start<=BUDGET_NS,'cooperative wake/settle budget before request')
  (output/(label+'-command.txt')).write_text(command)
  checkpoint['status']=label+'-submitted';save(path,checkpoint)
  text=call(command,ui_wake_submission=(label=='wake'));after=stamp(clock)
  need(after>=before,'host clock ordering')
  (output/(label+'-response.txt')).write_text(text)
  need(after-start<=BUDGET_NS,'cooperative wake/settle budget after response')
  return text,before,after
 try:
  text,before,after=request(wake_command(),'wake');codes=key_status(text)
  checkpoint.update(keyChildAttempts=2,keyPairReceiptComplete=True,keyDownExitCode=codes[0],keyUpExitCode=codes[1],wakeBeforeHostMonotonicNs=before,wakeReturnedHostMonotonicNs=after)
  save(path,checkpoint);need(codes==[0,0],'wake down/up exited zero')
  for i in range(1,MAX_SNAPSHOTS+1):
   label=f'ui-snapshot-{i:02d}';text,before,after=request(snapshot_command(),label);summary=parse_snapshot(text)
   (output/(label+'-summary.json')).write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
   checkpoint['snapshots'].append({'index':i,'label':label,'queryBeforeHostMonotonicNs':before,'queryReturnedHostMonotonicNs':after,'responseSha256':sha(text.encode()),'summary':summary});save(path,checkpoint)
   if qualified(summary):
    checkpoint.update(status='accepted_cached_checkpoint',wrapperUiOperationsCompleted=1,acceptedSnapshotIndex=i,acceptedQueryReturnedHostMonotonicNs=after);save(path,checkpoint);return checkpoint
   if i<MAX_SNAPSHOTS:sleeper(SETTLE_SECONDS)
  raise ValueError('cached Live/noSaver/CSFS settle exhausted')
 except Exception as exc:
  checkpoint.update(status='refused_or_ambiguous',errorType=type(exc).__name__);save(path,checkpoint);raise

def dispatch(checkpoint,clock=time.monotonic_ns):
 need(checkpoint.get('status')=='accepted_cached_checkpoint','accepted pre-native UI checkpoint')
 now=stamp(clock);age=now-checkpoint['acceptedQueryReturnedHostMonotonicNs']
 need(0<=age<=AGE_NS,'cached-query return to native submission age')
 checkpoint.update(nativeCommandSubmitHostMonotonicNs=now,hostSubmissionAgeNs=age,hostSubmissionAgeBoundNs=AGE_NS)
 return now

def validate(output,checkpoint):
 need(type(checkpoint)is dict and checkpoint.get('schema')=='fu-live-wake-checkpoint-v1'and checkpoint.get('status')=='accepted_cached_checkpoint','completed wake schema')
 need(all(type(checkpoint.get(k))is int for k in ['wrapperUiOperationsAttempted','wrapperUiOperationsCompleted','keyChildAttempts','startedHostMonotonicNs','wakeBeforeHostMonotonicNs','wakeReturnedHostMonotonicNs','acceptedSnapshotIndex','acceptedQueryReturnedHostMonotonicNs']),'exact integer wake counters/times')
 need(checkpoint.get('wrapperUiOperationsAttempted')==checkpoint.get('wrapperUiOperationsCompleted')==1 and checkpoint.get('keyChildAttempts')==2 and checkpoint.get('keyPairReceiptComplete')is True,'one visible workflow/two acknowledged child attempts')
 need(checkpoint.get('navigationSourceSha256')==NAV_SHA and checkpoint.get('keyBinarySha256')==KEY_SHA and checkpoint.get('executionConfirmed')is False and checkpoint.get('uiConsumptionProven')is False and checkpoint.get('physicalPictureObserved')is False,'source/scope')
 need((output/'wake-command.txt').read_text()==wake_command()and key_status((output/'wake-response.txt').read_text())==[0,0]and checkpoint.get('keyDownExitCode')==checkpoint.get('keyUpExitCode')==0,'exact wake command/status')
 entries=checkpoint.get('snapshots');need(type(entries)is list and 1<=len(entries)<=MAX_SNAPSHOTS,'snapshot count')
 start=checkpoint['startedHostMonotonicNs'];previous=checkpoint['wakeReturnedHostMonotonicNs'];need(type(start)is int and 0<=start<=checkpoint['wakeBeforeHostMonotonicNs']<=previous<=start+BUDGET_NS,'wake timestamps')
 for i,v in enumerate(entries,1):
  label=f'ui-snapshot-{i:02d}';need(type(v['index'])is int and v['index']==i and v['label']==label,'snapshot order')
  need((output/(label+'-command.txt')).read_text()==snapshot_command(),'snapshot exact command')
  text=(output/(label+'-response.txt')).read_text();s=parse_snapshot(text)
  need(sha(text.encode())==v['responseSha256']and s==v['summary']==json.loads((output/(label+'-summary.json')).read_text()),'snapshot raw/summary binding')
  before,after=v['queryBeforeHostMonotonicNs'],v['queryReturnedHostMonotonicNs'];need(type(before)is type(after)is int and previous<=before<=after<=start+BUDGET_NS,'snapshot time bounds');previous=after
  need(qualified(s)==(i==len(entries)),'first accepted snapshot ends settle')
 need(checkpoint['acceptedSnapshotIndex']==len(entries)and checkpoint['acceptedQueryReturnedHostMonotonicNs']==previous,'accepted final query')
 age=checkpoint.get('hostSubmissionAgeNs');submit=checkpoint.get('nativeCommandSubmitHostMonotonicNs')
 need(type(age)is int and type(submit)is int and 0<=age<=AGE_NS and submit-previous==age and checkpoint.get('hostSubmissionAgeBoundNs')==AGE_NS,'actual host submission age')
 return {'accepted':True,'wrapperUiOperations':1,'keyChildAttempts':2,'snapshotCount':len(entries),'hostSubmissionAgeNs':age,'physicalPictureObserved':False,'uiConsumptionProven':False}
