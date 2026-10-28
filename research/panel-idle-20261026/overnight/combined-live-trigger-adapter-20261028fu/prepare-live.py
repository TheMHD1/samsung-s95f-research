#!/usr/bin/env python3
"""Separate fixed Live Up/Up preparation; dry by default, no controller command."""
import argparse,json,time,types,hashlib,re
from pathlib import Path
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
w=load(P/'wake-check.py')
def up_command():return w.wake_command().replace('XF86AudioRaiseVolume','Up')
def save(path,v):path.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');path.chmod(0o600)
def perform(output,call,manifest_sha,clock=time.monotonic_ns,sleeper=time.sleep):
 need(re.fullmatch('[0-9a-f]{64}',manifest_sha or '')is not None,'manifest digest')
 output.mkdir(mode=0o700)
 ledger={'schema':'fu-live-header-preparation-v1','status':'intent','manifestSha256':manifest_sha,'expectedCachedTab':'Live','intendedNavigation':'Live-header-to-ForYou','navigationSourceSha256':w.NAV_SHA,'keyBinarySha256':w.KEY_SHA,'wakeSourceSha256':sha((P/'wake-check.py').read_bytes()),'preparationSourceSha256':sha(Path(__file__).read_bytes()),'entries':[],'upPairsCompleted':0,'optionalWakePairsCompleted':0,'leftPairsAttempted':0,'uiConsumptionProven':False,'physicalPictureObserved':False}
 path=output/'preparation.json';save(path,ledger)
 def request(command,label,start):
  before=w.stamp(clock);need(0<=before-start<=w.BUDGET_NS,'preparation phase budget before request')
  command_path=output/(label+'-command.txt');command_path.write_text(command);command_path.chmod(0o600)
  ledger.update(status=label+'-submitted',submittedLabel=label);save(path,ledger)
  text=call(command);after=w.stamp(clock);need(after>=before,'preparation clock order')
  need(type(text)is str and 0<len(text.encode())<=w.MAX_RESPONSE,'bounded preparation response')
  response_path=output/(label+'-response.txt');response_path.write_text(text);response_path.chmod(0o600)
  need(after-start<=w.BUDGET_NS,'preparation phase budget after response')
  row={'label':label,'phaseStartedHostMonotonicNs':start,'beforeHostMonotonicNs':before,'returnedHostMonotonicNs':after,'commandSha256':sha(command.encode()),'responseSha256':sha(text.encode())}
  ledger['entries'].append(row);save(path,ledger);return text,row
 def settle(prefix,start):
  for i in range(1,w.MAX_SNAPSHOTS+1):
   text,row=request(w.snapshot_command(),f'{prefix}-settle-{i:02d}',start);summary=w.parse_snapshot(text);row['summary']=summary;save(path,ledger)
   if w.qualified(summary):return summary
   if i<w.MAX_SNAPSHOTS:sleeper(w.SETTLE_SECONDS)
  raise ValueError('Live preparation settle exhausted')
 try:
  start=w.stamp(clock);text,row=request(w.snapshot_command(),'initial',start);summary=w.parse_snapshot(text);row['summary']=summary;save(path,ledger)
  if summary['screensaverWindowsPresent']:
   start=w.stamp(clock);text,_=request(w.wake_command(),'optional-wake',start);need(w.key_status(text)==[0,0],'preparation wake exits');ledger['optionalWakePairsCompleted']=1;save(path,ledger);settle('wake',start)
  else:need(w.qualified(summary),'initial Live/noSaver/CSFS')
  for n in [1,2]:
   start=w.stamp(clock);text,_=request(up_command(),f'up-{n}',start);need(w.key_status(text)==[0,0],'preparation Up exits');ledger['upPairsCompleted']=n;save(path,ledger);settle(f'up-{n}',start)
  ledger.update(status='accepted_live_header_preparation',submittedLabel=None);save(path,ledger);validate(output,ledger,manifest_sha);return ledger
 except Exception as exc:
  ledger.update(status='refused_or_ambiguous',errorType=type(exc).__name__);save(path,ledger);raise

def validate(output,v,manifest_sha):
 need(type(v)is dict and v.get('schema')=='fu-live-header-preparation-v1'and v.get('status')=='accepted_live_header_preparation','accepted preparation schema')
 need(v.get('manifestSha256')==manifest_sha and v.get('navigationSourceSha256')==w.NAV_SHA and v.get('keyBinarySha256')==w.KEY_SHA and v.get('wakeSourceSha256')==sha((P/'wake-check.py').read_bytes()) and v.get('preparationSourceSha256')==sha(Path(__file__).read_bytes()),'preparation pins')
 need(v.get('expectedCachedTab')=='Live'and v.get('intendedNavigation')=='Live-header-to-ForYou'and v.get('submittedLabel')is None,'preparation interpretation')
 need(v.get('uiConsumptionProven')is False and v.get('physicalPictureObserved')is False,'preparation scope')
 need(type(v.get('upPairsCompleted'))is int and v['upPairsCompleted']==2 and type(v.get('optionalWakePairsCompleted'))is int and v['optionalWakePairsCompleted']in [0,1] and type(v.get('leftPairsAttempted'))is int and v['leftPairsAttempted']==0,'exact preparation key counts')
 entries=v.get('entries');need(type(entries)is list and 5<=len(entries)<=34,'bounded preparation entries')
 at=0;previous=-1
 def read(label,command,start=None,snapshot=False):
  nonlocal at,previous
  need(at<len(entries),'missing preparation entry');e=entries[at];at+=1
  need(type(e)is dict and e.get('label')==label,'preparation exact sequence')
  need(set(e)=={'label','phaseStartedHostMonotonicNs','beforeHostMonotonicNs','returnedHostMonotonicNs','commandSha256','responseSha256'}|({'summary'}if snapshot else set()),'preparation entry fields')
  ps,b,a=[e[k]for k in ['phaseStartedHostMonotonicNs','beforeHostMonotonicNs','returnedHostMonotonicNs']]
  need(all(type(t)is int for t in [ps,b,a])and 0<=ps<=b<=a<=ps+w.BUDGET_NS and previous<=b,'preparation phase times')
  need((previous<=ps if start is None else ps==start),'one phase clock origin');previous=a
  for suffix,expected in [('command.txt',command),('response.txt',None)]:
   path=output/(label+'-'+suffix);need(path.is_file()and not path.is_symlink(),'preparation raw regular file');raw=path.read_bytes();need(len(raw)<=w.MAX_RESPONSE,'preparation raw cap');text=raw.decode();need(sha(raw)==e['commandSha256'if suffix=='command.txt'else'responseSha256'],'preparation raw hash');need(expected is None or text==expected,'preparation exact command')
  if snapshot:
   summary=w.parse_snapshot(text);need(summary==e['summary'],'preparation snapshot raw binding');return ps,summary
  need(w.key_status(text)==[0,0],'preparation successful key receipt');return ps,None
 def settled(prefix,start):
  for i in range(1,w.MAX_SNAPSHOTS+1):
   _,s=read(f'{prefix}-settle-{i:02d}',w.snapshot_command(),start,True)
   if w.qualified(s):return
  raise ValueError('preparation settle not accepted')
 _,initial=read('initial',w.snapshot_command(),snapshot=True)
 if initial['screensaverWindowsPresent']:
  need(v['optionalWakePairsCompleted']==1,'initial saver needs one wake');start,_=read('optional-wake',w.wake_command());settled('wake',start)
 else:need(w.qualified(initial)and v['optionalWakePairsCompleted']==0,'initial clean Live no extra wake')
 for n in [1,2]:
  start,_=read(f'up-{n}',up_command());settled(f'up-{n}',start)
 need(at==len(entries),'no extra preparation request')
 return {'accepted':True,'upPairs':2,'optionalWakePairs':v['optionalWakePairsCompleted'],'leftPairs':0,'requests':len(entries),'physicalPictureObserved':False,'uiConsumptionProven':False}

def load_certificate(path,digest,manifest_sha):
 need(type(digest)is str and re.fullmatch('[0-9a-f]{64}',digest)is not None,'preparation digest required')
 need(path.is_absolute()and path.is_file()and not path.is_symlink(),'absolute ordinary preparation certificate')
 with path.open('rb')as source:raw=source.read(49153)
 need(len(raw)<=49152 and sha(raw)==digest,'preparation certificate bytes/digest')
 r=load(P/'run-once.py');v=r.strict_json(raw);return validate(path.parent,v,manifest_sha)

def main():
 cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--execute',action='store_true');cli.add_argument('--manifest-sha256');cli.add_argument('--output',type=Path);args=cli.parse_args()
 r=load(P/'run-once.py');manifest,_=r.build_manifest();raw=r.manifest_bytes(manifest);need(raw==(P/'deployment-manifest.json').read_bytes(),'sealed manifest')
 if not args.execute:print(json.dumps({'mode':'dry','manifestSha256':sha(raw),'preparationUpPairs':2,'optionalWakePairsMaximum':1,'nativeInvocations':0,'controllerCommands':0}));return
 need(args.manifest_sha256==sha(raw)and args.output is not None and args.output.is_absolute(),'explicit execution pins/output')
 root=r.load_pinned(r.ROOT,r.ROOT_SHA,'fu_preparation_root');record={'schema':'fu-preparation-root-v1','calls':[]}
 def call(command):return root.root(command,record,args.output/'root-record.json')
 value=perform(args.output,call,sha(raw));print(json.dumps({'accepted':True,'certificate':str(args.output/'preparation.json'),'sha256':sha((args.output/'preparation.json').read_bytes()),'preparation':validate(args.output,value,sha(raw))}))
if __name__=='__main__':main()
