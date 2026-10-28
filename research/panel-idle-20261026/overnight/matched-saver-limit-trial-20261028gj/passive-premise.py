#!/usr/bin/env python3
"""One finite cached-only passive Live saver wait. No key, USB, reset or retry."""
from pathlib import Path
import datetime,hashlib,json,subprocess,time,os
P=Path(__file__).resolve().parent;B=P.parent
NAV=B/'ui-navigation-20261027br/navigate.py'
if hashlib.sha256(NAV.read_bytes()).hexdigest()!='74b60a9611f35a76d272b33677f773cc955838c2c6dda2c3565c371cc9d4d530':raise ValueError('NAV source pin')
os.umask(0o077)
out=P/'passive-premise-01';out.mkdir(mode=0o700)
start=time.monotonic();deadline=start+120
record={'schema':'gj-passive-live-saver-premise-v1','queries':[],'keys':0,'vendorOperations':0,'resetRequests':0,'accepted':False,'reason':'not_started','physicalPictureObserved':False}
def save():
 (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
save()
for i in range(5):
 if i:
  remaining=start+30*i-time.monotonic()
  if remaining>0:time.sleep(min(remaining,30))
 now=time.monotonic()
 if now>deadline:record['reason']='cooperative_budget_expired';break
 folder=out/('query-'+str(i+1))
 argv=['python3',str(NAV),'snapshot','--execute','--backend','local','--output',str(folder)]
 q={'ordinal':i+1,'beforeMonotonic':now,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv};record['queries'].append(q);save()
 with (out/('query-'+str(i+1)+'.stdout')).open('xb')as so,(out/('query-'+str(i+1)+'.stderr')).open('xb')as se:
  done=subprocess.run(argv,stdout=so,stderr=se,check=False)
 q.update(exitCode=done.returncode,afterMonotonic=time.monotonic())
 if done.returncode!=0:record['reason']='cached_query_refused';save();break
 summary=json.loads((folder/'before-summary.json').read_text());q['cachedSummary']=summary
 if summary['cached_current_tab']!='d/ug.tab@Live'or summary['csfs_window_present']is not True:record['reason']='required_Live_CSFS_absent';save();break
 if q['afterMonotonic']>deadline:record['reason']='query_return_after_budget';save();break
 if summary['screensaver_windows_present']is True:record.update(accepted=True,reason='cached_Live_saver_CSFS_present');save();break
 record['reason']='saver_not_yet_present';save()
record['endedMonotonic']=time.monotonic();save()
print(json.dumps({'accepted':record['accepted'],'reason':record['reason'],'queries':len(record['queries']),'keys':0,'vendorOperations':0}))
raise SystemExit(0 if record['accepted']else 1)
