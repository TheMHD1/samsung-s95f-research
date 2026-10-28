#!/usr/bin/env python3
"""Strict offline FW refusal classification and exact FU replay. No live transport."""
import base64,copy,hashlib,json,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;F=D.parent;B=F.parent;U=B/'combined-live-trigger-adapter-20261028fu';N=B/'combined-event-successor-20261028fn';E=B/'rtp-lane-gate-capture-20261028eb';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def j(p):return json.loads(p.read_bytes())
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def tuple_r(raw):return [struct.unpack_from('<H',raw,i)[0]for i in [0,10,14,0xc4]]
def classify(n,p):
 ck(n['accepted']is False and n['observationComplete']is False,'original refusal')
 ck(n['terminal']=='Refused'and n['error']=='InvalidOperationException: initial clean R'and not(set(n)&{'cleanupError','keyError'}),'exact source guard failure')
 ck(n['phase']=='ReadyForHeader'and all(n[k]is True for k in ['bindingQualified','opened','claimed','released','closed']),'terminal closed ownership')
 for k,v in [('device',65),('headers',2),('bulks',4),('inputs',2),('writes',0),('retries',0),('threshold',40),('cyclesStarted',0),('cleanCycles',0),('quiescentCycles',0)]:ck(type(n[k])is int and n[k]==v,'counter '+k)
 ck(n['arm']==n['restore']=='not-attempted'and all(n[k]is False for k in ['armAttempted','restoreAttempted','loggerMayRemain']),'never armed/restored')
 ck(n['rows']=={'schema':'fg-stockevent-checkpoints-v1','recordBytes':58,'count':0,'rawBase64':'','sha256':sha(b'')}and n['retained']==[],'no observation rows')
 ck([c['role']for c in n['controls']]==['prearm-R'],'only prearm R')
 c=n['controls'][0];raw=p.capture(c)[0];ck(c['cycle']==0 and [w['name']for w in c['windows']]==['R'],'prearm map')
 p.logger(raw,0);ck(tuple_r(raw)==[1,4097,0,40]and p.rt(raw)==1,'snapshot fault40/loggerzero')
 meta=n['baselineRing'];ck(set(meta)=={'complete','bytes','sha256','transfer'}and meta['complete']is True and meta['bytes']==15372 and len(meta['sha256'])==64,'baseline ring metadata only')
 cap=meta['transfer'];ck(cap['role']=='baseline-ring'and cap['cycle']==0 and cap['windows']==[{'name':'Ring','count':15372}],'ring map')
 ts=cap['transfers'];ck(len(ts)==2 and [t[:3]for t in ts]==[['OUT',12,12],['IN',15372,15372]],'ring full pair')
 ck(n['postRing']=={'complete':False,'bytes':0,'sha256':sha(b''),'transfer':{'role':'unused','cycle':0,'windows':[],'transfers':[]}},'no post ring request')
 allsteps=ts+c['transfers'];previous=n['startUs']
 ck(type(previous)is int and n['startUs']<=n['endUs']<=n['wholeDeadlineUs']==n['startUs']+40000000,'native clock/budget')
 for t in allsteps:
  ck(len(t)==7 and type(t[2])is int and t[2]==t[1]and t[3]==0 and t[6]is None and all(type(z)is int for z in t[4:6])and previous<=t[4]<=t[5]<=n['endUs'],'complete ordered pair transfer');previous=t[5]
 key=n['intervention'];ck(key['key']=='Left'and key['trigger']=='first-full-clean-cycle'and all(key[k]is False for k in ['attempted','completed','uiReceiptObserved','physicalPictureObserved']),'no Left exposure')
 ck([x['phase']for x in key['calls']]==['down','up']and all(x=={'phase':phase,'started':False,'reaped':False,'timedOut':False,'stdoutBytes':0,'stderrBytes':0}for x,phase in zip(key['calls'],['down','up'])),'neither Left child started')
 ck(len(allsteps)==n['bulks']==n['headers']+n['inputs']+n['writes'],'full source pair accounting')
 return raw,allsteps

def run():
 for f in j(D/'input-pins.json')['files']:
  raw=(B/f['path']).read_bytes();ck(len(raw)==f['bytes']and sha(raw)==f['sha256'],'pinned '+f['path'])
 for dirname,expected in [(U,'5015c1acc3d00cdabf5b057f9dc6568fee2bed6c637be462f44f5643abef6a7a')]:
  ck(sha((dirname/'source-inventory.json').read_bytes())==expected,'frozen FU source inventory')
  for row in j(dirname/'source-inventory.json')['files']:
   raw=(dirname/row['path']).read_bytes();ck(len(raw)==row['bytes']and sha(raw)==row['sha256'],'FU source '+row['path'])
 for row in j(U/'input-pins.json')['files']:
  raw=(B/row['path']).read_bytes();ck(len(raw)==row['bytes']and sha(raw)==row['sha256'],'FU input '+row['path'])
 w=load(U/'run-once.py');p=load(N/'parse-result.py');prep=load(U/'prepare-live.py');capture=F/'capture-01';record=j(capture/'record.json');n,rows,q=p.parse_native((capture/'native.receipt.json').read_text());raw,steps=classify(n,p)
 ck(rows==[]and q==j(capture/'interpretation.json')and q['terminalKnownPhase']and not q['accepted']and not q['keyExposureQualified'],'strict FN interpretation')
 man,payload=w.build_manifest();manifest=w.manifest_bytes(man);ck(manifest==(U/'deployment-manifest.json').read_bytes()==(capture/'reviewed-manifest.json').read_bytes(),'manifest exact')
 ready,rr=w.load_readiness(capture/'readiness-decision.json',record['readinessSha256']);ck(sha(manifest)==record['manifestSha256'],'reviewed manifest binding')
 for ref in ready['evidence']:ck(sha(Path(ref['path']).read_bytes())==ref['sha256'],'readiness evidence bytes')
 cert=F/'live-preparation-01/preparation.json';cv=prep.load_certificate(cert,sha(cert.read_bytes()),sha(manifest));ck(cv['accepted']and cv['requests']==7 and cv['upPairs']==2 and cv['optionalWakePairs']==1 and cv['leftPairs']==0,'actual preparation')
 ck({'path':str(cert),'sha256':sha(cert.read_bytes())}in ready['evidence'],'readiness preparation reference')
 for tag,rc in [('selftest',0),('native',1)]:
  env=(capture/(tag+'-envelope.txt')).read_text();matches=[c for c in record['calls']if (' --receipt-self-test > 'if tag=='selftest'else' --execute --device ')in c['command']];ck(len(matches)==1 and matches[0]['response']['commands'][0]['stdout']==env,'root-bound '+tag+' envelope')
  if tag=='native':ck(env.startswith('IMMEDIATE_READY\n'),'immediate cached metadata');env=env.removeprefix('IMMEDIATE_READY\n')
  term,receipt,stdout,stderr=w.receipt_envelope(env);ck(term==record[tag+'Terminal']and term['exit_code']==rc and stderr==b'','native/selftest terminal')
  for suffix,data in [('receipt.json',receipt),('stdout',stdout),('stderr',stderr)]:ck(data==(capture/(tag+'.'+suffix)).read_bytes(),'saved exact blob')
  if tag=='selftest':ck(json.loads(receipt)=={'smokeTestsPassed':8,'targetOperations':0},'zero IO selftest')
 calls=record['calls'];ck(len(calls)==40 and ' --execute --device 'in calls[-1]['command'],'native last of40 root requests')
 for c in calls:
  a=c['response'];t=a['commands'];ck(c['transport_exit']==0 and type(c['transport_exit'])is int and c['host_timeout']is False and c['transport_stderr']=={'data':'','encoding':'base64'}and a['authenticated']is True and a['uid']==a['euid']==0 and len(t)==1 and t[0]['command']==c['command']and t[0]['exit_code']==0 and t[0]['timed_out']is False and t[0]['stderr']=='','root transport/command binding');ck(c['command_bytes']==len(c['command'].encode())<=8192,'command cap')
 ck(record['cleanup_required']is True and record['native_invocations']==1 and record['target_operations']==2 and record['target_operations_status']=='native_refused','original record refusal/stage retained')
 primary=j(capture/'primary-native-outcome.json');result=j(capture/'result.json');ck(primary==record['nativeOutcome']and primary['receiptSha256']==sha((capture/'native.receipt.json').read_bytes()),'primary receipt outcome')
 ck(result['accepted']is False and result['cleanup']=='retained'and result['cleanup_required']is True and result['thresholdWrites']==0 and result['keyExposureQualified']is False,'result no acceptance promotion')
 for name in ['baseline-ring.bin','post-ring.bin','metadata-post.txt','ring-metadata.json']:ck(not(capture/name).exists(),'no later fetch/artifact '+name)
 class Replay:
  at=0
  def root(self,command,rec,path):
   ck(self.at<len(calls),'no extra root request');c=calls[self.at];self.at+=1;ck(c['command']==command,'exact regenerated command');rec['calls'].append(copy.deepcopy(c));w.save(path,rec);return c['response']['commands'][0]['stdout']
 cp=record['wakeCheckpoint'];clock=iter([cp['startedHostMonotonicNs'],cp['wakeBeforeHostMonotonicNs'],cp['wakeReturnedHostMonotonicNs'],cp['snapshots'][0]['queryBeforeHostMonotonicNs'],cp['snapshots'][0]['queryReturnedHostMonotonicNs'],cp['nativeCommandSubmitHostMonotonicNs']]);w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].rsplit('-',1)[-1]));replay=Replay();artifacts=0
 with tempfile.TemporaryDirectory(dir=D/'private',prefix='replay-')as td:
  out=Path(td)/'capture';reason=None
  try:w.execute(out,ready,rr,manifest,payload,replay,p,clock=lambda:next(clock),sleeper=lambda _:ck(False,'no unexpected settle'))
  except ValueError as e:reason=str(e)
  ck(reason=='original native refusal preserved: InvalidOperationException: initial clean R'and replay.at==40,'original refusal exact replay')
  for f in out.iterdir():ck(f.read_bytes()==(capture/f.name).read_bytes(),'byte-exact artifact '+f.name);artifacts+=1
 wake=load(U/'wake-check.py');ck(wake.validate(capture,cp)['accepted'],'poststaging strict Live checkpoint')
 ep=load(E/'parse-result.py');bn,raws,bd=ep.parse_native((F/'baseline-capture/native.receipt.json').read_text());ck(bn['accepted']and bn['device']==65,'prior strict accepted baseline')
 for name,data,h in raws:ck(data==(F/'baseline-capture'/name).read_bytes()and sha(data)==h,'baseline raw binding '+name)
 baseline_end=bn['steps'][-1]['afterUs'];ck(tuple_r((F/'baseline-capture/end-R.bin').read_bytes())==[0,0,1,40]and struct.unpack_from('<H',(F/'baseline-capture/end-R.bin').read_bytes(),6)[0]==0,'baseline clean40/logger0')
 engine=(N/'Engine.cs').read_text();ck('RingRead(ops,clock,x,fd,ref phase,false)'in engine and 'LoggerR(pre,0);Need(ClassifyRt(pre)==RtState.Clean,"initial clean R");'in engine,'source refusal guard before context/arm')
 malformed=0
 for field,value in [('accepted',True),('phase','Unknown'),('headers',1),('bulks',3),('inputs',1),('writes',1),('armAttempted',True),('restoreAttempted',True),('loggerMayRemain',True),('released',False),('closed',False)]:
  bad=copy.deepcopy(n);bad[field]=value
  try:classify(bad,p)
  except (ValueError,TypeError,KeyError):malformed+=1
  else:raise ValueError('malformed accepted '+field)
 for kind in ['short-IN','fault-change','clock-order','Left-start']:
  bad=copy.deepcopy(n)
  if kind=='short-IN':bad['controls'][0]['transfers'][-1][2]=255
  if kind=='fault-change':b=bytearray(raw);b[0]=0;bad['controls'][0]['windows'][0]['raw']=base64.b64encode(b).decode()
  if kind=='clock-order':bad['controls'][0]['transfers'][0][4]=n['startUs']-1
  if kind=='Left-start':bad['intervention']['calls'][0]['started']=True
  try:classify(bad,p)
  except (ValueError,TypeError,KeyError):malformed+=1
  else:raise ValueError('malformed accepted '+kind)
 summary={'schema':'fw-independent-prearm-refusal-v1','originalNativeAccepted':False,'originalWrapperAccepted':False,'refusal':'initial clean R','device':65,'phase':'ReadyForHeader','released':True,'closed':True,'headers':2,'bulks':4,'inputs':2,'writes':0,'leftAttempted':False,'loggerArmAttempted':False,'loggerRestoreAttempted':False,'prearmR':{'rtLimitTuple':tuple_r(raw),'loggerWord':struct.unpack_from('<H',raw,6)[0],'bytes':256,'sha256':sha(raw),'headerBeforeUs':steps[2][4],'dataAfterUs':steps[3][5]},'nativeStartUs':n['startUs'],'nativeEndUs':n['endUs'],'baselineCleanEndUs':baseline_end,'baselineToFaultReadGapUs':steps[3][5]-baseline_end,'onsetTimeKnown':False,'baselineRingRemoteBytes':n['baselineRing']['bytes'],'baselineRingHash':n['baselineRing']['sha256'],'baselineRingFetched':False,'postRingRead':False,'restorationEstablished':False,'loggerMayRemain':False,'remoteStageRemoved':False,'remoteStageInventoryFetched':False,'rootCommandsReplayed':replay.at,'generatedArtifactsByteExact':artifacts,'maxCommandBytes':max(c['command_bytes']for c in calls),'preparationRequests':7,'preparationUpPairs':2,'preparationOptionalVolupPairs':1,'poststagingVolupPairs':1,'cachedLiveNoSaverBeforeNative':True,'hostQueryToSubmissionNs':cp['hostSubmissionAgeNs'],'scientificExposureQualified':False,'physicalPictureObserved':False,'causalUiStepIdentified':False,'checksPassed':checks,'malformedRefusals':malformed,'inputPins':len(j(D/'input-pins.json')['files']),'targetOperations':0,'rootCalls':0,'networkOperations':0}
 proof={'schema':'fw-independent-terminal-phase-proof-v1','status':'NATIVE_TERMINAL_KNOWN_READY_NOT_WRAPPER_ACCEPTANCE','originalNativeAccepted':False,'originalWrapperAccepted':False,'nativeReceiptSha256':sha((capture/'native.receipt.json').read_bytes()),'rootRecordSha256':sha((capture/'record.json').read_bytes()),'reviewedManifestSha256':sha(manifest),'readinessSha256':sha(rr),'phase':'ReadyForHeader','bindingQualified':True,'released':True,'closed':True,'headers':2,'bulks':4,'matchedReadPairs':2,'allPairsIndividuallyRetained':True,'noPendingInOrPayload':True,'writes':0,'loggerArmAttempted':False,'loggerRestoreAttempted':False,'loggerObservedWord':0,'loggerMayRemain':False,'leftAttempted':False,'nativeRootRequestIsLast':True,'rootRequestsAfterNative':0,'stageHeld':True,'stageInventoryKnownFromPostTrialFetch':False,'remoteStage':record['remote_stage'],'stageCleanupGranted':False,'recoveryGranted':False,'physicalPictureObserved':False,'checksPassed':checks,'sourceEngineSha256':sha((N/'Engine.cs').read_bytes()),'targetOperations':0,'rootCalls':0}
 return summary,proof
if __name__=='__main__':
 summary,proof=run()
 for name,v in [('decoded.json',summary),('phase-proof.json',proof)]:
  raw=(json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
  if sys.argv[1:]==['--write']:(D/name).write_bytes(raw)
  else:ck((D/name).read_bytes()==raw,'derived output exact '+name)
 print(json.dumps({'schema':'fw-refusal-analysis-validation-v1','checks':checks,'malformedRefusals':summary['malformedRefusals'],'exactCommands':summary['rootCommandsReplayed'],'exactArtifacts':summary['generatedArtifactsByteExact'],'maxCommandBytes':summary['maxCommandBytes'],'decodedSha256':sha((D/'decoded.json').read_bytes()),'phaseProofSha256':sha((D/'phase-proof.json').read_bytes()),'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
