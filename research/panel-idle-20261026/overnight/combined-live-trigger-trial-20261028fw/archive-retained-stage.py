#!/usr/bin/env python3
"""One explicit fixed ordinary-file archive; no TV mutation, deletion or retry."""
import hashlib,json,os,types
from pathlib import Path
os.umask(0o077)
P=Path(__file__).resolve().parent;B=P.parent
FY=B/'retained-stage-archive-plan-20261028fy'
def need(v,s):
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path,h,name):
 raw=path.read_bytes();need(sha(raw)==h,'source pin '+name);m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw,str(path),'exec'),m.__dict__);return m
def private_new(path,raw):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:
  need(f.write(raw)==len(raw),'exact private write');f.flush();os.fsync(f.fileno())
def json_new(path,value):private_new(path,(json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
need(sha((FY/'source-inventory.json').read_bytes())=='fb51ba12c72597d6af2f73764c0210e0a9e983782ad7f538c9b8ec02abc4d306','FY inventory')
for r in json.loads((FY/'source-inventory.json').read_bytes())['files']:
 raw=(FY/r['path']).read_bytes();need(len(raw)==r['bytes']and sha(raw)==r['sha256'],'FY frozen file')
m=load(FY/'build-plan.py','cc313ab5361aeb28dcc09c98ec2ee38dd59dfc5c1365a60c80409cb357f7e4e0','fw_archive_plan')
raw=(FY/'archive-plan.json').read_bytes();need(sha(raw)=='51c4578e6b194d042ff4d4661b9cadcfad63dd3c1f9f05e7a2219a9e5cdeb9f2','fixed plan')
plan=m.build();need((json.dumps(plan,sort_keys=True,indent=2)+'\n').encode()==raw,'exact plan reconstruction')
for i,row in enumerate(plan['commands'],1):need((FY/f'command-{i:02d}.sh').read_text()==row['command']and sha(row['command'].encode())==row['commandSha256'],'exact fixed command')
ROOT=B/'managed-ui-tab-launch/root-with-margin.py'
root=load(ROOT,'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a','fw_archive_root')
need((root.REMOTE_TIMEOUT_SECONDS,root.HOST_TIMEOUT_SECONDS,root.MAX_COMMAND,root.MAX_RESPONSE)==(45,75,8192,65536),'root bounds')
out=P/'retained-stage-archive-01';need(out.is_absolute()and not out.exists()and not out.is_symlink(),'fresh archive')
out.mkdir(mode=0o700)
json_new(out/'intent.json',{'schema':'fw-fixed-stage-archive-intent-v1','planSha256':sha(raw),'commands':[{k:v for k,v in x.items()if k!='command'}for x in plan['commands']],'automaticRetry':False,'usbOperations':0,'uiOperations':0,'remoteCleanup':False})
record={'schema':'fw-fixed-stage-archive-root-v1','calls':[]};files=[]
try:
 for i,row in enumerate(plan['commands'],1):
  private_new(out/f'command-{i:02d}.txt',row['command'].encode())
  text=root.root(row['command'],record,out/'root-record.json')
  private_new(out/f'response-{i:02d}.txt',text.encode())
  with(out/'root-record.json').open('rb')as fd:os.fsync(fd.fileno())
  data=m.parse_ring(text,row['file'],plan)
  private_new(out/row['file'],data)
  need((out/row['file']).read_bytes()==data,'retained bytes')
  files.append({'path':row['file'],'bytes':len(data),'sha256':sha(data),'responseSha256':sha(text.encode()),'commandSha256':row['commandSha256']})
 for name,meta in plan['knownHostFiles'].items():
  data=(B/meta['hostSource']).read_bytes();need(len(data)==meta['bytes']and sha(data)==meta['sha256'],'existing host file reference')
 index={'schema':'fw-fixed-stage-archive-complete-v1','archiveComplete':True,'archiveOnly':True,'planSha256':sha(raw),'phaseProofSha256':plan['phaseProofSha256'],'remoteStage':plan['remoteStage'],'remoteStageRetained':True,'rootCalls':len(record['calls']),'files':files,'knownHostFiles':plan['knownHostFiles'],'originalNativeAccepted':False,'originalWrapperAccepted':False,'loggerArmed':False,'leftAttempted':False,'usbOperations':0,'uiOperations':0,'remoteWrites':0,'remoteCleanup':False,'retries':0,'baselineIsPrefaultProven':False,'postRingIsCompletedObservation':False,'ringWrapExcluded':False,'physicalPictureObserved':False,'rootRecordSha256':sha((out/'root-record.json').read_bytes())}
 json_new(out/'archive-complete.json',index)
 fd=os.open(out,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:os.fsync(fd)
 finally:os.close(fd)
 print(json.dumps({'archiveComplete':True,'rootCalls':len(record['calls']),'newArchivedBytes':sum(x['bytes']for x in files),'existingHostFilesReferenced':9,'remoteStageRetained':True,'usbOperations':0,'remoteWrites':0},sort_keys=True))
except Exception as error:
 json_new(out/'archive-refused.json',{'archiveComplete':False,'rootCalls':len(record['calls']),'errorType':type(error).__name__,'message':str(error)[:500],'automaticRetry':False,'remoteStageRetained':True})
 raise
