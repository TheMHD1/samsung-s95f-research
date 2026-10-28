#!/usr/bin/env python3
"""Cached-only Live+saver checkpoint; no keys, preparation or controller access."""
import hashlib,json,re,time
from pathlib import Path
BOOT='00000000-0000-4000-8000-000000000000'
MAX_SNAPSHOTS=10;SETTLE_SECONDS=.25;BUDGET_NS=10000000000;AGE_NS=1000000000;MAX_RESPONSE=65536
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def stamp(clock):
 v=clock();need(type(v)is int and v>=0,'host monotonic integer');return v
def snapshot_command():
 return ('set -eu\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'+'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\nvconftool get memory/eden/current_tab\nenlightenment_info -topvwins\ncat /proc/uptime\n')
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
def qualified(value):
 return value['screensaverWindowsPresent'] and value['csfsWindowPresent']

def perform(output,call,checkpoint,clock=time.monotonic_ns,sleeper=time.sleep):
 path=output/'cached-checkpoint.json';start=stamp(clock);previous=start
 checkpoint.update(schema='ga-cached-live-saver-checkpoint-v1',status='intent',startedHostMonotonicNs=start,wrapperUiOperationsAttempted=0,wrapperUiOperationsCompleted=0,wrapperKeyChildrenAttempted=0,executionConfirmed=False,uiConsumptionProven=False,physicalPictureObserved=False,intendedNativeAction='saver-wake-from-cached-Live',snapshots=[])
 save(path,checkpoint)
 try:
  for index in range(1,MAX_SNAPSHOTS+1):
   label=f'ui-snapshot-{index:02d}';before=stamp(clock)
   need(previous<=before and 0<=before-start<=BUDGET_NS,'cooperative cached budget/clock before request')
   command=snapshot_command();(output/(label+'-command.txt')).write_text(command)
   checkpoint['status']=label+'-submitted';save(path,checkpoint)
   text=call(command)
   need(type(text)is str and len(text.encode())<=MAX_RESPONSE,'bounded cached response')
   # Preserve the returned data even if the following host clock fails.
   (output/(label+'-response.txt')).write_text(text)
   after=stamp(clock);need(before<=after<=start+BUDGET_NS,'cooperative cached budget/clock after response')
   previous=after;summary=parse_snapshot(text)
   save(output/(label+'-summary.json'),summary)
   checkpoint['snapshots'].append({'index':index,'label':label,'queryBeforeHostMonotonicNs':before,'queryReturnedHostMonotonicNs':after,'responseSha256':sha(text.encode()),'summary':summary})
   save(path,checkpoint)
   if qualified(summary):
    checkpoint.update(status='accepted_cached_checkpoint',acceptedSnapshotIndex=index,acceptedQueryReturnedHostMonotonicNs=after)
    save(path,checkpoint);return checkpoint
   if index<MAX_SNAPSHOTS:sleeper(SETTLE_SECONDS)
  raise ValueError('cached Live/saver/CSFS settle exhausted')
 except Exception as exc:
  checkpoint.update(status='refused_or_ambiguous',errorType=type(exc).__name__);save(path,checkpoint);raise

def dispatch(checkpoint,clock=time.monotonic_ns):
 need(checkpoint.get('status')=='accepted_cached_checkpoint','accepted pre-native cached checkpoint')
 need(type(checkpoint.get('acceptedQueryReturnedHostMonotonicNs'))is int,'accepted query clock integer')
 now=stamp(clock);age=now-checkpoint['acceptedQueryReturnedHostMonotonicNs']
 need(0<=age<=AGE_NS,'cached-query return to native submission age')
 checkpoint.update(nativeCommandSubmitHostMonotonicNs=now,hostSubmissionAgeNs=age,hostSubmissionAgeBoundNs=AGE_NS)
 return now

def validate(output,checkpoint):
 need(type(checkpoint)is dict and checkpoint.get('schema')=='ga-cached-live-saver-checkpoint-v1'and checkpoint.get('status')=='accepted_cached_checkpoint','completed cached schema')
 for key in ['wrapperUiOperationsAttempted','wrapperUiOperationsCompleted','wrapperKeyChildrenAttempted']:
  need(type(checkpoint.get(key))is int and checkpoint[key]==0,'zero wrapper UI/key counters')
 need(checkpoint.get('executionConfirmed')is False and checkpoint.get('uiConsumptionProven')is False and checkpoint.get('physicalPictureObserved')is False and checkpoint.get('intendedNativeAction')=='saver-wake-from-cached-Live','cached-only scope')
 entries=checkpoint.get('snapshots');need(type(entries)is list and 1<=len(entries)<=MAX_SNAPSHOTS,'snapshot count')
 start=checkpoint.get('startedHostMonotonicNs');need(type(start)is int and start>=0,'start host clock')
 previous=start
 for index,entry in enumerate(entries,1):
  label=f'ui-snapshot-{index:02d}'
  need(type(entry)is dict and set(entry)=={'index','label','queryBeforeHostMonotonicNs','queryReturnedHostMonotonicNs','responseSha256','summary'},'snapshot exact fields')
  need(type(entry['index'])is int and entry['index']==index and entry['label']==label,'snapshot order')
  need((output/(label+'-command.txt')).read_text()==snapshot_command(),'exact cached command')
  text=(output/(label+'-response.txt')).read_text();summary=parse_snapshot(text)
  need(sha(text.encode())==entry['responseSha256']and summary==entry['summary']==json.loads((output/(label+'-summary.json')).read_text()),'snapshot raw/summary binding')
  before,after=entry['queryBeforeHostMonotonicNs'],entry['queryReturnedHostMonotonicNs']
  need(type(before)is type(after)is int and previous<=before<=after<=start+BUDGET_NS,'snapshot time bounds');previous=after
  need(qualified(summary)==(index==len(entries)),'first accepted snapshot ends settle')
 need(type(checkpoint.get('acceptedSnapshotIndex'))is int and checkpoint['acceptedSnapshotIndex']==len(entries)and type(checkpoint.get('acceptedQueryReturnedHostMonotonicNs'))is int and checkpoint['acceptedQueryReturnedHostMonotonicNs']==previous,'accepted final query')
 age=checkpoint.get('hostSubmissionAgeNs');submit=checkpoint.get('nativeCommandSubmitHostMonotonicNs')
 need(type(age)is int and type(submit)is int and 0<=age<=AGE_NS and submit-previous==age and type(checkpoint.get('hostSubmissionAgeBoundNs'))is int and checkpoint['hostSubmissionAgeBoundNs']==AGE_NS,'actual host submission age')
 if 'firstCachedCallIndex'in checkpoint or 'lastCachedCallIndex'in checkpoint:
  first,last=checkpoint.get('firstCachedCallIndex'),checkpoint.get('lastCachedCallIndex')
  need(type(first)is type(last)is int and first>=0 and last-first+1==len(entries),'cached-only call index extent')
 need(not(output/'wake-command.txt').exists()and not(output/'wake-response.txt').exists(),'no wrapper wake artifacts')
 return {'accepted':True,'wrapperUiOperations':0,'wrapperKeyChildrenAttempted':0,'snapshotCount':len(entries),'hostSubmissionAgeNs':age,'physicalPictureObserved':False,'uiConsumptionProven':False,'intendedNativeAction':'saver-wake-from-cached-Live'}
