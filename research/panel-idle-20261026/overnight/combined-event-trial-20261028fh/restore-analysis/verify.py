#!/usr/bin/env python3
"""Pure offline FM actual replay; no real root adapter or transport imported."""
import base64,copy,hashlib,json,pathlib,sys,tempfile,types
sys.dont_write_bytecode=True
D=pathlib.Path(__file__).resolve().parent;F=D.parent;B=F.parent;M=B/'logger-gate-reconciliation-20261028fm';P=F/'logger-restore-01';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def j(p):return json.loads(p.read_bytes())
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def pincheck():
 rows=j(D/'input-pins.json')['files']
 for row in rows:
  raw=(B/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'input '+row['path'])
 return len(rows)
def ledger(calls):
 need(type(calls)is list and len(calls)==32,'exact32calls')
 for c in calls:
  a=c['response'];t=a['commands'];need(type(c['transport_exit'])is int and c['transport_exit']==0 and c['host_timeout']is False and c['transport_stderr']=={'data':'','encoding':'base64'},'root transport')
  need(a['authenticated']is True and type(a['uid'])is int and type(a['euid'])is int and a['uid']==a['euid']==0 and len(t)==1,'root identity')
  need(t[0]['command']==c['command']and type(t[0]['exit_code'])is int and t[0]['exit_code']==0 and t[0]['timed_out']is False and t[0]['stderr']=='','root child')
  raw=base64.b64decode(c['transport_stdout']['data'],validate=True);need(c['transport_stdout']['encoding']=='base64'and json.loads(raw)==a,'root response matches transport')
  need(type(c['command_bytes'])is int and c['command_bytes']==len(c['command'].encode())<=8192 and len(t[0]['stdout'].encode())<=65536,'command/response caps')
 return calls
class Replay:
 def __init__(self,w,calls):self.w=w;self.calls=ledger(calls);self.at=0
 def root(self,command,record,path):
  need(self.at<len(self.calls),'no extra root call');c=self.calls[self.at];self.at+=1;need(command==c['command'],'exact generated command');record['calls'].append(copy.deepcopy(c));self.w.save(path,record);return c['response']['commands'][0]['stdout']
def replay(w,p,ready,rr,mb,payload,record,calls,compare=True):
 w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].rsplit('-',1)[-1]));root=Replay(w,calls)
 with tempfile.TemporaryDirectory(dir=D/'private',prefix='replay-')as tmp:
  out=pathlib.Path(tmp)/'out';v=w.execute(out,ready,rr,mb,payload,root,p);need(root.at==32,'all32calls consumed')
  if compare:
   need(v==j(P/'result.json'),'exact generated result')
   files=list(out.iterdir());need(len(files)==len(list(P.iterdir())),'all artifacts count')
   for f in files:need(f.read_bytes()==(P/f.name).read_bytes(),'byteexact generated '+f.name)
   return len(files)
def run():
 count=pincheck();w=load(M/'run-once.py');p=load(M/'parse-result.py');record=j(P/'record.json');native,_,interpretation=p.parse_native((P/'native.receipt.json').read_text());need(interpretation==j(P/'interpretation.json'),'strict interpretation')
 need(native['restore']=='readback-zero'and native['headers']==5 and native['bulks']==10 and native['inputs']==4 and native['writes']==1,'restore five-pair accounting')
 need(native['phase']=='ReadyForHeader'and all(native[k]is True for k in ['bindingQualified','opened','claimed','released','closed']),'known phase/cleanup')
 man,payload=w.build_manifest();mb=w.manifest_bytes(man);need(mb==(M/'deployment-manifest.json').read_bytes()==(P/'reviewed-manifest.json').read_bytes(),'manifest regenerated/captured')
 need(sha(mb)=='c2315adb3f6643dd45fcceab70b4013fd0670bd96f7226a08dad3dec0094327d','manifest pin')
 ready,rr=w.load_readiness(P/'readiness-decision.json',record['readinessSha256']);need(sha(rr)=='9802410a028de39c206a56b565fecdb659daafafd56279f4dfe06703ed4900c9','actual readiness pin')
 for row in ready['evidence']:need(sha(pathlib.Path(row['path']).read_bytes())==row['sha256'],'readiness evidence')
 need(ready['identity']['devnum']=='65'and native['device']==65,'same65device')
 for tag in ['selftest','native']:
  text=(P/(tag+'-envelope.txt')).read_text();found=[c for c in record['calls']if (' --receipt-self-test > 'if tag=='selftest'else' --execute --device ')in c['command']];need(len(found)==1 and text==found[0]['response']['commands'][0]['stdout'],'root bound '+tag)
  if tag=='native':need(text.startswith('IMMEDIATE_READY\n'),'immediate cached identity marker');text=text.removeprefix('IMMEDIATE_READY\n')
  term,receipt,stdout,stderr=w.receipt_envelope(text);need(term==record[tag+'Terminal']and term['exit_code']==0 and stderr==b'','strict successful terminal')
  for suffix,raw in [('receipt.json',receipt),('stdout',stdout),('stderr',stderr)]:need(raw==(P/(tag+'.'+suffix)).read_bytes(),'exclusive blob '+tag+suffix)
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'diagnostic separate')
  if tag=='selftest':need(json.loads(receipt)=={'schema':'fm-host-tests-v1','checks':406,'cases':72,'targetOperations':0,'restoreOnly':True},'zero target selftest')
 artifacts=replay(w,p,ready,rr,mb,payload,record,record['calls'])
 need(record['native_invocations']==1 and record['target_operations']==5 and record['target_operations_status']=='accepted_restore_only'and record['loggerPayloads']==1 and record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','final wrapper ledger')
 need(record['wrapperUiOperations']==0 and record['no_retry']is True,'no UI/retry')
 windows=[]
 for i,c in enumerate(native['retained']):
  for x in c['windows']:
   raw=base64.b64decode(x['rawBase64'],validate=True);windows.append((f'{i:02}-{x["name"]}.bin',raw))
 m,c,r0,r1=[v for _,v in windows];half=lambda b,n:int.from_bytes(b[n:n+2],'little')
 dif=[i for i in range(256)if r0[i]!=r1[i]];need(dif==[6]and half(r0,6)==1 and half(r1,6)==0,'only logger low byte changed across Rs')
 need(p.rt(r0)==p.rt(r1)=='Clean'and half(r0,0xc4)==half(r1,0xc4)==40,'both fresh R clean40')
 need(c[7]==0 and c[8]==3 and m[56]==1,'actual sampled context')
 old=j(F/'capture-01/native.receipt.json');oldrecord=j(F/'capture-01/record.json');need(old['accepted']is False and old['loggerMayRemain']is True and oldrecord['target_operations_status']=='inflight_or_unknown','original FH refusal/generic audit preserved')
 # Meaningful native/envelope/ledger mutations; originals never edited or projected.
 bad=0
 def reject(f):
  nonlocal bad
  try:f()
  except (ValueError,KeyError,TypeError):bad+=1;return
  raise ValueError('malformed unexpectedly accepted')
 for field,value in [('accepted',False),('phase','Unknown'),('released',False),('writes',0),('loggerMayRemain',True)]:
  z=copy.deepcopy(native);z[field]=value;reject(lambda:p.parse_native(json.dumps(z)))
 z=copy.deepcopy(native);q=z['retained'][-1]['windows'][0];b=bytearray(r1);b[6]=1;q.update(rawBase64=base64.b64encode(b).decode(),sha256=sha(b));reject(lambda:p.parse_native(json.dumps(z)))
 reject(lambda:w.receipt_envelope((P/'native-envelope.txt').read_text().removeprefix('IMMEDIATE_READY\n')+'x'))
 for kind in ['delete-cleanup','reorder-tail','cleanup-stdout','integrity-stdout','post-census','command-substitution']:
  calls=copy.deepcopy(record['calls'])
  if kind=='delete-cleanup':calls.pop()
  elif kind=='reorder-tail':calls[-1],calls[-2]=calls[-2],calls[-1]
  elif kind=='command-substitution':calls[-1]['command']+='echo EXTRA\n'
  else:
   at={'cleanup-stdout':-1,'integrity-stdout':-2,'post-census':-3}[kind];calls[at]['response']['commands'][0]['stdout']='NOT_ACCEPTED\n'
   # Keep transport JSON coherent so byte binding cannot be the sole rejection.
   calls[at]['transport_stdout']['data']=base64.b64encode(json.dumps(calls[at]['response']).encode()).decode()
  reject(lambda:replay(w,p,ready,rr,mb,payload,record,calls,False))
 pincheck()
 controls=native['retained'];write=controls[3]['transfers'];pre=controls[2]['transfers'];post=controls[4]['transfers']
 result={'schema':'fh-independent-fm-restoration-analysis-v1','accepted':True,'nativeAccepted':True,'wrapperAccepted':True,'originalFhNativeAccepted':False,'originalFhWrapperRecordModified':False,'originalFgStageTouched':False,'device':65,'sameOriginalIdentity':True,'boot':ready['identity']['boot'],'headers':5,'bulks':10,'inputs':4,'loggerPayloads':1,'thresholdWrites':0,'uiOperations':0,'resets':0,'retries':0,'phase':'ReadyForHeader','released':True,'closed':True,'loggerBefore':1,'loggerAfter':0,'rChangedByteOffsets':dif,'rBeforeTriplet':[half(r0,a)for a in (0,10,14)],'rAfterTriplet':[half(r1,a)for a in (0,10,14)],'thresholdBeforeAfter':[half(r0,0xc4),half(r1,0xc4)],'c7':c[7],'c8':c[8],'scan':m[56],'mRoot':hex(int.from_bytes(m[64:68],'little')),'aaAc':[half(m,10),half(m,12)],'nativeStartUs':native['startUs'],'nativeEndUs':native['endUs'],'nativeDurationUs':native['endUs']-native['startUs'],'preRFullPairUs':[pre[0]['beforeUs'],pre[1]['afterUs']],'restoreFullPairUs':[write[0]['beforeUs'],write[1]['afterUs']],'postRFullPairUs':[post[0]['beforeUs'],post[1]['afterUs']],'originalFhEndToFmStartUs':native['startUs']-old['endUs'],'rootCallsReplayed':32,'generatedArtifactsByteExact':artifacts,'maxCommandBytes':max(c['command_bytes']for c in record['calls']),'cleanup':'STAGE_ABSENT','stageOwnedFiles':9,'preCensus':record['preCensus'],'beforeInvokeCensus':record['beforeInvokeCensus'],'postCensus':record['postCensus'],'nativeDiagnosticStdoutBytes':len((P/'native.stdout').read_bytes()),'selftestDiagnosticStdoutBytes':len((P/'selftest.stdout').read_bytes()),'rawFiles':[{'name':name,'bytes':len(raw),'sha256':sha(raw)}for name,raw in windows],'malformedRefusals':bad,'inputFilesVerified':count,'checksPassed':checks,'physicalPictureObserved':False,'loggerRestorationCausedCleanState':False,'continuousCleanBetweenCapturesProven':False,'thresholdOrResetRecoveryPerformed':False,'targetOperations':0,'rootCalls':0,'networkOperations':0}
 return result,windows
if __name__=='__main__':
 result,raws=run();raw=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
 if sys.argv[1:]==['--write']:
  (D/'decoded.json').write_bytes(raw)
  for name,data in raws:
   p=D/'private'/name;p.write_bytes(data);p.chmod(0o600)
 else:sys.stdout.buffer.write(raw)
