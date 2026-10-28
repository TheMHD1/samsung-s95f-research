#!/usr/bin/env python3
"""Bounded offline strict replay of the frozen first raised-limit exposure. No device I/O."""
import base64,copy,hashlib,json,statistics,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;X=D.parent;B=X.parent;checks=0
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
FOLDERS={'fa':'selective-endpoint-limit-writer-20261028fa','er':'rtp-quiescent-checkpoints-20261028er','eb':'rtp-lane-gate-capture-20261028eb'}
def pins():
 rows=j(D/'input-pins.json')['files']
 for f in rows:
  raw=(B/f['path']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'input '+f['path'])
 return len(rows)
def callcheck(c):
 a=c['response'];q=a['commands'];need(c['transport_exit']==0 and c['host_timeout']is False and c['transport_stderr']=={'data':'','encoding':'base64'},'root transport')
 need(a['authenticated']is True and a['uid']==a['euid']==0 and len(q)==1,'root identity')
 need(q[0]['command']==c['command'] and q[0]['exit_code']==0 and q[0]['timed_out']is False and q[0]['stderr']=='','completed root command')
def replay(role,path,kind,action=None):
 p=X/path;folder=B/FOLDERS[kind];w=load(folder/'run-once.py');parser=load(folder/'parse-result.py')
 inv=j(folder/'source-inventory.json')
 for f in inv['files']:
  raw=(folder/f['path']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'frozen source '+role+f['path'])
 man,payload=w.build_manifest();mr=w.manifest_bytes(man);need(mr==(folder/'deployment-manifest.json').read_bytes()==(p/'reviewed-manifest.json').read_bytes(),'regenerated manifest '+role)
 result=j(p/'result.json');record=j(p/'record.json');ready,rr=w.load_readiness(p/'readiness-decision.json',result['readinessSha256'])
 need(result['manifestSha256']==sha(mr) and result['accepted']is True and result['cleanup']=='STAGE_ABSENT','wrapper accepted/cleanup')
 for f in ready['evidence']:need(sha(Path(f['path']).read_bytes())==f['sha256'],'readiness evidence')
 parsed=parser.parse_native((p/'native.receipt.json').read_text())
 if kind=='fa':n,raws,gc=parsed;q=None;need(gc==[],'exclusive FA')
 elif kind=='er':n,_,raws,gc,q=parsed;need(gc==[]and q['trialQualified'],'qualified exclusive EY')
 else:n,raws,q=parsed
 need(n['protocolPhase']=='ReadyForHeader'and n['accepted']and n['released']and n['closed']and n['device']==63,'native completion USB63')
 if q is not None:need(q==j(p/'interpretation.json'),'saved interpretation')
 for blobkind in ('selftest','native'):
  text=(p/(blobkind+'-envelope.txt')).read_text()
  if blobkind=='native':need(text.startswith('IMMEDIATE_READY\n'),'fresh invoke metadata');text=text.removeprefix('IMMEDIATE_READY\n')
  term,r,out,err=w.receipt_envelope(text)
  need(term==record[blobkind+'Terminal']and term['exit_code']==0 and err==b'','three blob terminal')
  for suffix,v in [('receipt.json',r),('stdout',out),('stderr',err)]:need(v==(p/(blobkind+'.'+suffix)).read_bytes(),'exclusive saved blob')
  need(record[blobkind+'DiagnosticStdout']=={'bytes':len(out),'sha256':sha(out),'semanticReceipt':False},'opaque diagnostics')
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
  if kind=='fa':args.append(action)
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

def summary_snapshot(p):
 r=j(p.with_suffix('.json'));need(len(r['calls'])==1,'one snapshot request');c=r['calls'][0];callcheck(c);text=c['response']['commands'][0]['stdout'];need(text==p.with_suffix('.txt').read_text(),'snapshot stdout')
 tab=next((s.removeprefix('memory/eden/current_tab, value = ').split(' (',1)[0]for s in text.splitlines()if s.startswith('memory/eden/current_tab, value = ')),None)
 out={'cached_current_tab':tab,'csfs_window_present':'/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll'in text,'physical_picture_observed':False,'screensaver_windows_present':'ScreenSaver.dll'in text or 'ScreenSaverContent.dll'in text}
 need(out==j(p.with_name(p.name.replace('-snapshot','-summary')+'.json')),'cached summary recomputed')
 return out

def ui():
 after=summary_snapshot(X/'after-control-ui/before-snapshot');need(after['cached_current_tab']=='d/apps.tab'and after['screensaver_windows_present'],'later Apps+saver')
 p=X/'explicit-for-you-01';r=j(p/'result.json');before=summary_snapshot(p/'before-snapshot');need(before==r['before'],'UI before')
 need(r['action']=='for-you'and r['cached_target_match']is True and r['execution_confirmed']is False and r['controller_usb_power_settings_firmware_operations']==0 and r['retries']==0,'cached UI scope')
 steps=r['normal_key_steps'];need([s['action']for s in steps]==['up','up','left','left'],'exact four normal keys')
 verified=[]
 for i,s in enumerate(steps,1):
  label=f'{i:02d}-'+s['action'];key=j(p/('local-key-'+label+'.json'));need(key['down_attempts']==key['up_attempts']==1 and key['automatic_retry']is False and key['backend']=='local','one local down/up')
  need(len(key['calls'])==1,'one key root request');callcheck(key['calls'][0]);text=key['calls'][0]['response']['commands'][0]['stdout'];need(text=='LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n','key process exit')
  v=summary_snapshot(p/('after-'+label+'-snapshot'));need(v==s['summary'],'exact key cached observation');verified.append({'action':s['action'],'cachedSummary':v,'rootStartedUtc':key['calls'][0]['started_utc'],'rootFinishedUtc':key['calls'][0]['finished_utc']})
 need(verified[-1]['cachedSummary']==r['after']and r['after']['cached_current_tab']=='d/ug.tab@ForYou'and not r['after']['screensaver_windows_present'],'final cached ForYou')
 wake=j(X/'explicit-control-preparation-01/local-key-wake-once.json');need(len(wake['calls'])==1,'one wake request');callcheck(wake['calls'][0]);need(wake['calls'][0]['response']['commands'][0]['stdout']=='LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n','wake process exit')
 # Replay the frozen NAV functions with saved responses; never call adapter().
 nav=load(B/'ui-navigation-20261027br/navigate.py');calls=[j(p/'before-snapshot.json')['calls'][0]]
 for i,step in enumerate(steps,1):
  label=f'{i:02d}-'+step['action'];calls.extend([j(p/('local-key-'+label+'.json'))['calls'][0],j(p/('after-'+label+'-snapshot.json'))['calls'][0]])
 class NavigationReplay:
  position=0
  def root(self,command,record,path):
   need(self.position<len(calls),'no extra NAV request');c=calls[self.position];self.position+=1;need(c['command']==command,'exact NAV generated command');record['calls'].append(copy.deepcopy(c));nav.save(path,record);return c['response']['commands'][0]['stdout']
 replay=NavigationReplay()
 with tempfile.TemporaryDirectory(prefix='ui-replay-',dir=D)as tmp:
  out=Path(tmp);v=nav.command_snapshot(replay,out,'before');observed=nav.normal_page_navigation('for-you','local',out,replay,v)
  for key,value in observed.items():need(value==r[key],'exact NAV result field')
  need(replay.position==9,'nine NAV requests')
  for file in out.iterdir():need(file.read_bytes()==(p/file.name).read_bytes(),'exact NAV output '+file.name)
 return {'exactFrozenNavigationCommandReplay':9,'allGeneratedNavigationArtifactsByteExact':True,'laterFirstControlSnapshot':after,'explicitBefore':before,'normalKeys':verified,'explicitAfter':r['after'],'wakeProcessExitedZero':True,'uiKeyConsumptionProven':False,'physicalPictureObserved':False,'firstControlWakeFailureCauseProven':False}

def clone_tests(parser,n,fields):
 count=0
 for key,value in fields:
  z=copy.deepcopy(n);z[key]=value
  try:parser.parse_native(json.dumps(z))
  except(ValueError,TypeError,KeyError,StopIteration):count+=1
  else:raise ValueError('malformed actual accepted '+key)
 return count

def run():
 count=pins();a,_,ar,restore,ap=replay('restore','restore-01','fa','restore');n,q,raw,ctrl,cp=replay('first-control','control-01/onset','er');e,eq,er,post,ep=replay('first-post','control-01/post-tables','eb');f,fq,fr,fault,fp=replay('explicit-fault','explicit-control-01','eb')
 model=load(B/'selective-endpoint-limit-design-20261028ez/profile_model.py');pred={k:model.profile_prediction(ar[k+'.bin'])for k in ('baseline-R','fresh-R','readback-R')};model.validate_candidate_context(ar['pre-M.bin'],ar['pre-C.bin'],ar['baseline-R.bin']);model.validate_transaction_pair(ar['fresh-R.bin'],ar['readback-R.bin'],200,40,ar['baseline-R.bin'])
 need(a['action']=='restore200to40'and a['headersSent']==7 and a['bulkTransfers']==14 and a['readbackVerified']and not a['limitMayHaveChanged'],'restore complete')
 need([u16(ar[k+'.bin'],196)for k in ('baseline-R','fresh-R','readback-R')]==[200,200,40],'200 to40 readback');need([i for i in range(256)if ar['fresh-R.bin'][i]!=ar['readback-R.bin'][i]]==[196],'only c4 observed difference')
 pc=j(X/'restore-parent-check.json');need(pc['accepted']and pc['actual_c4_readback']==40 and pc['native_sha256']==sha((X/'restore-01/native.receipt.json').read_bytes())and pc['result_sha256']==sha((X/'restore-01/result.json').read_bytes()),'parent restore proof binds originals')
 rows=decode58(raw['score-checkpoints.bin'],n['startUs'],q['scoreCheckpoints']['rows']);need(len(rows)==56 and n['cleanCyclesCompleted']==56 and n['quiescentCyclesCompleted']==0 and n['terminalReason']=='CycleLimit','56clean control')
 need(all(r['a0U32']==0 and r['selectorC7']==0 and r['startAlternateThreshold']==r['endAlternateThreshold']==40 for r in rows),'control H0 C70 c440')
 need(eq['rBytesEqual']and [u16(er['start-R.bin'],o)for o in (0,10,14)]==[0,0,1]and u16(er['end-R.bin'],196)==40 and u16(er['end-R.bin'],144)==201,'control EB stableclean40/latch201')
 need(fq['rBytesEqual']and all([u16(fr[k],o)for o in (0,10,14)]==[1,4097,0]and u16(fr[k],196)==40 and u16(fr[k],144)==41 for k in ('start-R.bin','end-R.bin')),'explicit EB stablefault40/latch41')
 m,c=fr['M.bin'],fr['C.bin'];need(u16(m,10)==0 and u16(m,12)==2 and c[7]==1 and u16(m,42)==40,'explicit mode1 selector1 publication40')
 need(fq['startN']['ordinals']==fq['endN']['ordinals']==[41,0,0,0,0,0]and fq['startN']['sourceCounts']==fq['endN']['sourceCounts']==[0]*6,'stable ordinal41 counts0')
 need(not any(fr['primary-lane-gate.bin'])and not any(fr['secondary-lane-gate.bin']),'all captured masks0')
 def packed(b):return {i:(int.from_bytes(b[:102],'little')>>(12*(i-568)))&4095 for i in range(568,636)}
 bottom=packed(fr['fixed-bottom-candidate.bin']);top=packed(fr['fixed-top-candidate.bin']);tuples=[]
 for t in fq['candidateTuples'][:41]:
  b=t['b'];diff=t['absoluteDifferenceOrMode6Zero'];x=t['x'];need(568<=x<=635 and t['y']==2159 and t['rgb']==0 and diff>500,'source-compatible tuple coordinate/diff')
  candidates=sorted(set(v for v in [b+diff,b-diff]if 0<=v<=4095 and abs(v-b)==diff));need(len(candidates)==1,'unique conditional12bit A')
  tuples.append({**t,'conditionalAIfCoherentMode1Tuple':candidates[0],'fixedBottomMatches':candidates[0]==bottom[x],'fixedTopMatches':candidates[0]==top[x]})
 interface=ui();helper=load(B/'quiescent-onset-trial-20261028es/live-analysis/analyze.py');retained=helper.decode_retained(n)
 raised=j(X/'raised-analysis/decoded.json');need(raised['maximumSampledH0']==76 and raised['cleanSelectorOneAbove40Count']==23,'frozen raised comparison')
 identities=[o['identity']for o in [restore,ctrl,post,fault]];need(all(i==identities[0]for i in identities)and identities[0]['devnum']=='63','same saved USB63 identity')
 start=a['steps'][0]['beforeUs'];end=a['steps'][-1]['afterUs'];ep0=e['steps'][0]['beforeUs'];fp0=f['steps'][0]['beforeUs'];need(start<end<n['startUs']<n['endUs']<ep0<fp0,'numerical native order')
 negatives=sum([clone_tests(ap,a,[('accepted',False),('readbackVerified',False),('limitMayHaveChanged',True),('protocolPhase','Unknown')]),clone_tests(cp,n,[('accepted',False),('quiescentCyclesCompleted',1),('bulkTransfers',895),('closed',False)]),clone_tests(fp,f,[('accepted',False),('headersSent',15),('laneGateContextQualified',False),('protocolPhase','Unknown')])]);pins()
 return {'schema':'ex-restoration-control-analysis-v1','inputFilesVerified':count,'lifecycle':{'restore':restore,'firstControl':ctrl,'firstControlPost':post,'explicitFault':fault},'restoration':{'sourceModelReplay':pred,'rObservedChangedBytes':[196],'verifiedReadbackLimit':40,'noAutomaticResetOrRetry':True},'firstControl':{'rows':rows,'retained':retained,'cleanComplete':56,'quiescentComplete':0,'maximumSampledH0':0,'selectorC7AllZero':True,'key':n['intervention'],'postInterpretation':eq,'exposureEquivalenceEstablished':False},'ui':interface,'explicitFault':{'interpretation':fq,'conditionalPrefix41':tuples,'allConditionalPrefixAEqualsBottom':all(t['fixedBottomMatches']for t in tuples),'historicalSameEpochProven':False,'conditionalBottomAll68':bottom,'conditionalTopAll68':top,'allCapturedTablesZero':True},'comparisonMatrix':[{'exposure':'raised EY','limit':200,'sampledMaxH0':76,'cleanComplete':55,'quiescentComplete':1,'cleanSelectorOneAbove40':23,'terminal':'CycleLimit','retainedEndC7':1,'recordLatchOrOrdinal':201},{'exposure':'restored first ER','limit':40,'sampledMaxH0':0,'cleanComplete':56,'quiescentComplete':0,'cleanSelectorOneAbove40':0,'terminal':'CycleLimit','retainedEndC7':0,'recordLatchOrOrdinal':201},{'exposure':'restored explicit ForYou EB','limit':40,'sampledMaxH0':None,'cleanComplete':None,'quiescentComplete':None,'cleanSelectorOneAbove40':None,'terminal':'stable sampled fault1/4097/0','retainedEndC7':1,'recordLatchOrOrdinal':41}],'timing':{'restoreFirstOutUs':start,'restoreReadbackInAfterUs':end,'firstControlStartUs':n['startUs'],'firstControlEndUs':n['endUs'],'firstPostStartUs':ep0,'explicitFaultStartUs':fp0,'restoreReadbackToExplicitFaultStartUs':fp0-end,'scope':'Common native monotonic-clock premise; full requests/replies are not exact RAM/optical timestamps. UI host UTC remains a separate timeline; no exact crossclock mapping claimed.'},'negativeCases':negatives,'claims':{'restoreReadback40Established':True,'faultObservedAfterExplicitForYouAt40':True,'sameSavedBootAndUsb63':True,'noResetBetweenRaisedAndControl':'parent coordinated lineage premise, not continuous identity proof','firstControlExposureEquivalent':False,'firstControlWakeFailureProven':False,'matchedThresholdCausalityEstablished':False,'publicationCapAlsoChanged':True,'actualFpOrHistoricalSelectedABranchProven':False,'sameRecordEpochProven':False,'physicalPictureObserved':False,'rootCauseOrPreventionEstablished':False,'laterRecoveryIncluded':False},'checksPassed':checks,'targetOperations':0,'rootCalls':0,'networkOperations':0}
if __name__=='__main__':
 value=run();raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 if sys.argv[1:]==['--write']:(D/'decoded.json').write_bytes(raw)
 else:need((D/'decoded.json').read_bytes()==raw,'exact derived replay')
 print(json.dumps({'accepted':True,'checksPassed':checks,'inputFilesVerified':value['inputFilesVerified'],'negativeCases':value['negativeCases'],'decodedSha256':sha(raw),'hostOnly':True}))
