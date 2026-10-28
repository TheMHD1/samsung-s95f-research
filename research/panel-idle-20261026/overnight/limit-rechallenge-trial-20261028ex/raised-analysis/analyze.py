#!/usr/bin/env python3
"""Bounded offline strict replay of the frozen first raised-limit exposure. No device I/O."""
import base64,copy,hashlib,json,statistics,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;X=D.parent;B=X.parent;T=X/'raised-01';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def j(p):return json.loads(p.read_bytes())
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
FOLDERS={'set':'selective-endpoint-limit-writer-20261028fa','onset':'rtp-limit200-checkpoints-20261028ey','post-tables':'rtp-lane-gate-capture-20261028eb'}
def pins():
 rows=j(D/'input-pins.json')['files']
 for f in rows:
  raw=(B/f['path']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'input '+f['path'])
 return len(rows)
def callcheck(c):
 a=c['response'];q=a['commands'];need(c['transport_exit']==0 and c['host_timeout']is False and c['transport_stderr']=={'data':'','encoding':'base64'},'root transport')
 need(a['authenticated']is True and a['uid']==a['euid']==0 and len(q)==1,'root identity')
 need(q[0]['command']==c['command'] and q[0]['exit_code']==0 and q[0]['timed_out']is False and q[0]['stderr']=='','completed root command')
def replay(role):
 p=T/role;folder=B/FOLDERS[role];w=load(folder/'run-once.py');parser=load(folder/'parse-result.py')
 inv=j(folder/'source-inventory.json')
 for f in inv['files']:
  raw=(folder/f['path']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'frozen source '+role+f['path'])
 man,payload=w.build_manifest();mr=w.manifest_bytes(man);need(mr==(folder/'deployment-manifest.json').read_bytes()==(p/'reviewed-manifest.json').read_bytes(),'regenerated manifest '+role)
 result=j(p/'result.json');record=j(p/'record.json');ready,rr=w.load_readiness(p/'readiness-decision.json',result['readinessSha256'])
 need(result['manifestSha256']==sha(mr) and result['accepted']is True and result['cleanup']=='STAGE_ABSENT','wrapper accepted/cleanup')
 for f in ready['evidence']:need(sha(Path(f['path']).read_bytes())==f['sha256'],'readiness evidence')
 parsed=parser.parse_native((p/'native.receipt.json').read_text())
 if role=='set':n,raws,gc=parsed;q=None;need(gc==[],'exclusive FA')
 elif role=='onset':n,_,raws,gc,q=parsed;need(gc==[]and q['trialQualified'],'qualified exclusive EY')
 else:n,raws,q=parsed
 need(n['protocolPhase']=='ReadyForHeader'and n['accepted']and n['released']and n['closed']and n['device']==63,'native completion USB63')
 if q is not None:need(q==j(p/'interpretation.json'),'saved interpretation')
 for kind in ('selftest','native'):
  text=(p/(kind+'-envelope.txt')).read_text()
  if kind=='native':need(text.startswith('IMMEDIATE_READY\n'),'fresh invoke metadata');text=text.removeprefix('IMMEDIATE_READY\n')
  term,r,out,err=w.receipt_envelope(text)
  need(term==record[kind+'Terminal']and term['exit_code']==0 and err==b'','three blob terminal')
  for suffix,v in [('receipt.json',r),('stdout',out),('stderr',err)]:need(v==(p/(kind+'.'+suffix)).read_bytes(),'exclusive saved blob')
  need(record[kind+'DiagnosticStdout']=={'bytes':len(out),'sha256':sha(out),'semanticReceipt':False},'opaque diagnostics')
 inventory=[];raw={}
 for name,data,h in raws:
  need(sha(data)==h and data==(p/name).read_bytes(),'saved raw '+name);raw[name]=data;inventory.append({'name':name,'bytes':len(data),'sha256':h})
 need(inventory==result['rawFiles']==record['retained_raw_files'],'raw inventory')
 need(record['native_invocations']==result['nativeInvocations']==1 and result['retries']==0 and record['no_retry']is True and not record['cleanup_required']and record['cleanup_stdout']=='STAGE_ABSENT\n','one invocation/no retry/cleanup')
 for key in ('preCensus','beforeInvokeCensus','postCensus'):need(record[key]['observedHolders']==record[key]['otherErrors']==0 and record[key]['continuousAbsenceEstablished']is False,'snapshot census')
 calls=record['calls']
 for c in calls:callcheck(c)
 class Replay:
  position=0
  def root(self,command,rec,path):
   need(self.position<len(calls),'no extra request');c=calls[self.position];self.position+=1;need(command==c['command'],'exact generated root command');rec['calls'].append(copy.deepcopy(c));w.save(path,rec);return c['response']['commands'][0]['stdout']
 r=Replay();w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].split('-')[-1]))
 with tempfile.TemporaryDirectory(prefix='replay-',dir=D)as tmp:
  out=Path(tmp)/'result';args=[out,ready,rr,mr,payload,r,parser]
  if role=='set':args.append('set')
  observed=w.execute(*args);need(observed==result and r.position==len(calls),'exact wrapper result/all calls')
  # Analyzer-generated interpretations are added by coordinator; every wrapper output must match.
  for f in out.iterdir():need(f.read_bytes()==(p/f.name).read_bytes(),'exact replay artifact '+f.name)
 return n,q,raw,{'manifestSha256':sha(mr),'readinessSha256':sha(rr),'identity':ready['identity'],'headers':n['headersSent'],'bulks':n['bulkTransfers'],'rawFiles':inventory,'rootCallsReplayed':len(calls),'allReplayedArtifactsByteExact':True,'cleanup':'STAGE_ABSENT','phase':'ReadyForHeader','released':True,'closed':True,'nativeInvocations':1,'retries':0},parser

def decode58(data,start,pr):
 need(len(data)==58*56 and len(pr)==56,'56x58 extent');rows=[]
 states=['Clean','Faulted','Unexpected','Quiescent']
 for i,p in enumerate(pr):
  b=data[i*58:(i+1)*58];s,e=b[0]>>4,b[0]&15;need(s<4 and e<4,'state nibble')
  d={'cycleIndex':i+1,'startRtClassification':states[s],'endRtClassification':states[e],'selectorC7':b[1],'startAlternateThreshold':u16(b,2),'endAlternateThreshold':u16(b,4),'a0U32':u32(b,6),'a0Low16':u32(b,6)&65535,'q0U16':u16(b,10),'history0U16x4':list(struct.unpack_from('<4H',b,12)),'recordOrdinal0U32':u32(b,20),'hReadBracket':{'headerBeforeUs':start+u32(b,24),'dataAfterUs':start+u32(b,28)},'publicationBoundMirror':u16(b,32),'mCpu4a2U16':u16(b,34),'mCpu4a4U16':u16(b,36),'mCpu4c2U16':u16(b,38),'mCpu4c4U16':u16(b,40),'endRRoot2460U16':u16(b,42),'endRRoot246eU16':u16(b,44),'capturedDynamicAPointerU32':u32(b,46),'capturedDynamicBPointerU32':u32(b,50),'endRRoot24caU16':u16(b,54),'endRRoot2468U16':u16(b,56)}
  for k,v in d.items():need(v==p[k],'independent58 '+k)
  rows.append(d)
 return rows

def mutations(parser,n):
 count=0
 def reject(z):
  nonlocal count
  try:parser.parse_native(json.dumps(z))
  except(ValueError,TypeError,KeyError,StopIteration):count+=1;return
  raise ValueError('malformed actual accepted')
 for k,v in [('accepted',False),('observationAccepted',False),('closed',False),('released',False),('protocolPhase','Unknown'),('bindingQualified',False),('quiescentCyclesCompleted',0),('headersSent',447),('bulkTransfers',895)]:
  z=copy.deepcopy(n);z[k]=v;reject(z)
 for at in [0,18*58,55*58+54]:
  z=copy.deepcopy(n);b=bytearray(base64.b64decode(z['scoreCheckpoints']['rawBase64']));b[at]^=2;z['scoreCheckpoints']['rawBase64']=base64.b64encode(b).decode();z['scoreCheckpoints']['sha256']=sha(b);reject(z)
 z=copy.deepcopy(n);z['intervention']['calls'][0]['reaped']=False;reject(z)
 return count

def run():
 count=pins();a,_,ar,aset,ap=replay('set');n,q,raw,onset,parser=replay('onset');e,eq,er,post,ep=replay('post-tables')
 need(a['headersSent']==7 and a['bulkTransfers']==14 and a['readbackVerified']and not a['limitMayHaveChanged'],'fixed writer complete')
 model=load(B/'selective-endpoint-limit-design-20261028ez/profile_model.py')
 pred={k:model.profile_prediction(ar[k+'.bin'])for k in ('baseline-R','fresh-R','readback-R')}
 model.validate_candidate_context(ar['pre-M.bin'],ar['pre-C.bin'],ar['baseline-R.bin']);model.validate_transaction_pair(ar['fresh-R.bin'],ar['readback-R.bin'],40,200,ar['baseline-R.bin'])
 need([u16(ar[k+'.bin'],196)for k in ('baseline-R','fresh-R','readback-R')]==[40,40,200],'40 to200 readback')
 need([i for i in range(256)if ar['fresh-R.bin'][i]!=ar['readback-R.bin'][i]]==[196],'only observed c4 byte differs')
 rows=decode58(raw['score-checkpoints.bin'],n['startUs'],q['scoreCheckpoints']['rows'])
 clean=[r for r in rows if r['startRtClassification']==r['endRtClassification']=='Clean'];qs=[r['cycleIndex']for r in rows if 'Quiescent'in [r['startRtClassification'],r['endRtClassification']]]
 witness=[r['cycleIndex']for r in clean if r['a0Low16']>40 and r['selectorC7']==1]
 need(n['cyclesStarted']==56 and n['cleanCyclesCompleted']==55 and n['quiescentCyclesCompleted']==1 and qs==[19],'55clean1Q')
 need(n['headersSent']==448 and n['bulkTransfers']==896 and n['terminalReason']=='CycleLimit'and not n['onsetObserved'],'completed finite observation')
 need(len(witness)==23 and witness==q['fixed200Evidence']['cleanBracketAbove40SelectorOneCycles'],'23 witnesses')
 need(max(r['a0U32']for r in rows)==76 and rows[-1]['a0U32']==52,'max76 final52')
 need(all(r['startAlternateThreshold']==r['endAlternateThreshold']==200 for r in rows),'all endpoint limits200')
 helper=load(B/'quiescent-onset-trial-20261028es/live-analysis/analyze.py');retained=helper.decode_retained(n)
 last=next(c for c in retained if c['role']=='last-clean');m=next(w for w in last['windows']if w['name']=='M');c=next(w for w in last['windows']if w['name']=='C');h=next(w for w in last['windows']if w['name']=='H');rs=[w for w in last['windows']if w['name']=='R']
 need(last['cycle']==56 and m['aa']==0 and m['ac']==2 and c['selectorC7']==1 and h['a0U32']==52 and all(w['rt']==[0,0,1]and w['limit']==200 and w['selectorMirror']==1 for w in rs),'retained56 source-compatible alternate witness')
 need(e['headersSent']==16 and e['bulkTransfers']==32 and eq['rBytesEqual']and all(u16(er[k],196)==200 and [u16(er[k],o)for o in (0,10,14)]==[0,0,1]for k in ('start-R.bin','end-R.bin')),'separate post clean200')
 need(u16(er['end-R.bin'],144)==201,'post publication latch201')
 prior=load(B/'rtp-quiescent-checkpoints-20261028er/parse-result.py');es=B/'quiescent-onset-trial-20261028es/trial-01/onset';pn,_,prf,pg,pq=prior.parse_native((es/'native.receipt.json').read_text())
 for name,data,digest in prf:need((es/name).read_bytes()==data and sha(data)==digest,'ES raw comparison')
 oldpost=next(w for c in pn['retained']if c['role']=='post-fault'for w in c['windows']if w['name']=='H');oldposth=u32(base64.b64decode(oldpost['rawBase64'],validate=True),4);need(oldposth==48,'ES postfault H48')
 oldmax=max(r['a0U32']for r in pq['scoreCheckpoints']['rows']);need(oldmax==40 and pn['onsetObserved']and pn['quiescentCyclesCompleted']==2,'ES source observations')
 delta=[b['hReadBracket']['headerBeforeUs']-a['hReadBracket']['headerBeforeUs']for a,b in zip(rows,rows[1:])]
 t0=a['steps'][0]['beforeUs'];t1=a['steps'][-1]['afterUs'];p0=e['steps'][0]['beforeUs'];p1=e['steps'][-1]['afterUs'];need(t0<t1<n['startUs']<n['endUs']<p0<p1,'same-clock sequence numerical order')
 identity=aset['identity'];need(identity==onset['identity']==post['identity'],'saved same identity USB63')
 malformed=mutations(parser,n)
 othermut=0
 for par,original,changes in [(ap,a,[('accepted',False),('readbackVerified',False),('limitMayHaveChanged',True),('protocolPhase','Unknown'),('bulkTransfers',13)]),(ep,e,[('accepted',False),('closed',False),('packingQualified',False),('headersSent',15),('protocolPhase','Unknown')])]:
  for field,value in changes:
   z=copy.deepcopy(original);z[field]=value
   try:par.parse_native(json.dumps(z))
   except(ValueError,TypeError,KeyError,StopIteration):othermut+=1
   else:raise ValueError('malformed FA/EB clone accepted '+field)
 pins()
 return {'schema':'ex-raised-independent-analysis-v1','inputFilesVerified':count,'lifecycle':{'set':aset,'onset':onset,'postTables':post},'writerModelReplay':pred,'writerObservedRByteDifferences':[196],'compactRows':rows,'completeCycles':56,'cleanCycles':55,'quiescentCycles':1,'quiescentCycleIndices':qs,'maximumSampledH0':76,'maximumCycles':[r['cycleIndex']for r in rows if r['a0U32']==76],'lastRetainedH0':52,'cleanSelectorOneAbove40Cycles':witness,'cleanSelectorOneAbove40Count':len(witness),'retained':retained,'eyFixed200Interpretation':q['fixed200Evidence'],'postTablesInterpretation':eq,'key':n['intervention'],'timing':{'startUs':n['startUs'],'deadlineUs':n['deadlineUs'],'endUs':n['endUs'],'cooperativeNativeDurationUs':n['endUs']-n['startUs'],'hStartSpacingUs':{'all':delta,'minimum':min(delta),'median':statistics.median(delta),'maximum':max(delta)},'setFirstOutBeforeUs':t0,'setFinalReadbackAfterUs':t1,'postFirstOutBeforeUs':p0,'postFinalInAfterUs':p1,'setReadbackToPostFinalNumericalSpanUs':p1-t1,'onsetEndToPostFirstOutUs':p0-n['endUs'],'scope':'Native common monotonic-clock premise. Full request/reply brackets are not exact controller RAM sampling; compact non-H taps are sequential. Raised-value exposure starts before observation and restoration is outside this report.'},'priorES40':{'compactCount':len(pq['scoreCheckpoints']['rows']),'cleanCycles':pn['cleanCyclesCompleted'],'quiescentCycles':pn['quiescentCyclesCompleted'],'maximumCompactH0':oldmax,'postFaultH0':oldposth,'onsetObserved':True,'softwareTransitionBracket':pq['ordering']['softwareTransitionBracket'],'sameSceneOrEpochProven':False},'publicationScope':{'alternateThresholdAndPublicationBoundChangedTogether':True,'configuredAlternateLimit':200,'postObservedLatch':201,'sourceInclusiveOrdinals':'0..200 inclusive; 201 published records when that source path runs','pureThresholdOnlyIntervention':False},'negativeMalformedClonesRejected':malformed+othermut,'claims':{'sampledCleanAbove40Witness':True,'retainedCycle56Mode1AlternateContextSupported':True,'actualFpRegisterProven':False,'actualComparatorDecisionLogged':False,'allComparatorInvocationsObserved':False,'wholeExposureContinuous200Proven':False,'thresholdPreventionEstablished':False,'sameSceneOrReferenceEpochAsESProven':False,'physicalPictureObserved':False,'rootCauseOrElectricalSafetyEstablished':False,'restoreIncluded':False},'checksPassed':checks,'targetOperations':0,'networkOperations':0,'rootCalls':0}
if __name__=='__main__':
 value=run();raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 if sys.argv[1:]==['--write']:(D/'decoded.json').write_bytes(raw)
 else:need((D/'decoded.json').read_bytes()==raw,'exact decoded replay')
 print(json.dumps({'accepted':True,'checksPassed':checks,'inputFilesVerified':value['inputFilesVerified'],'negativeCases':value['negativeMalformedClonesRejected'],'decodedSha256':sha(raw),'hostOnly':True}))
