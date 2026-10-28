#!/usr/bin/env python3
"""Explicit original UnexpectedRt classifier. Never projects refused native bytes into success."""
import base64,copy,hashlib,importlib.util,json,struct,sys,tempfile,types,os
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EO=HERE.parent;B=EO.parent;D=B/'rtp-refresh-dense-checkpoints-20261028em';P=EO/'trial-01/onset';checks=0;negatives=0
MAN='83382d9a55271194480cb17d777a0d45737128f3dd849228b9517c3d2284c522';READY='26271063ee16e3c02e8ac0cc2bcc8e19b5a38c144d5a5d8d79daa24dd82e71be'
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_text())
def need(ok,label):
 global checks
 checks+=1
 if not ok:raise ValueError(label)
def reject(fn):
 global negatives
 try:fn()
 except (ValueError,KeyError,TypeError):negatives+=1;need(True,'negative rejected');return
 raise ValueError('malformed clone accepted')
def module(path,name,pin):
 need(sha(path.read_bytes())==pin,'pinned module '+name)
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def blob(v):
 need(type(v)is dict and set(v)=={'encoding','data'} and v['encoding']=='base64','blob shape')
 b=base64.b64decode(v['data'],validate=True);need(base64.b64encode(b).decode()==v['data'],'blob canonical');return b
def call_check(c):
 need(c['command_bytes']==len(c['command'].encode())<=8192,'command length')
 need(c['transport_exit']==0 and c['host_timeout']is False and c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75,'transport status/deadlines')
 need(blob(c['transport_stderr'])==b'','empty transport stderr')
 raw=blob(c['transport_stdout']);need(len(raw)<=65536 and json.loads(raw)==c['response'],'saved response identity')
 r=c['response'];need(r['authenticated']is True and r['uid']==r['euid']==0 and r['model']=='QN77S95FAFXZC','response identity')
 need(len(r['commands'])==1,'single command');row=r['commands'][0]
 need(row['command']==c['command']and row['exit_code']==0 and row['timed_out']is False and row['stderr']=='','command echo/status')
 need(type(row['stdout'])is str and len(row['stdout'].encode())<=65536,'stdout cap')
 need(c['started_utc']<=c['finished_utc'],'host ordering');return row['stdout']
def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def fields(r):return {'rt':[u16(r,o)for o in (0,10,14)],'alternateLimit':u16(r,0xc4),'normalMode1Limit':u16(r,0x30),'mode1Latch':u16(r,0x90),'operatingMode':u16(r,0x10),'ordinaryBUpper':u16(r,0x20),'alternateBUpper':u16(r,0xbc),'temperature':u16(r,0x98),'echo':u16(r,0xac)}
TOP={'schema','scoreCheckpoints','device','bindingQualified','intervention','observationAccepted','stage','terminalReason','protocolPhase','opened','claimed','released','closed','accepted','onsetObserved','onsetMissed','physicalPictureObserved','busContentsAltered','writes','retries','cyclesStarted','cleanCyclesCompleted','cleanCyclesDiscarded','bulkTransfers','headersSent','inputsCompleted','startUs','deadlineUs','endUs','overshootUs','retentionPolicy','retained'}
SPECS=[('R',0x47012400,256),('M',0x470004a0,68),('C',0x47000bc0,16),('P',0x47000490,16),('N',0x4700ba28,36),('H',0x4700d0e0,96),('L',0x47010f00,64),('R',0x47012400,256)]
def integer(x,lo=0,hi=(1<<63)-1):need(type(x)is int and lo<=x<=hi,'strict bounded integer');return x
TRANSPORT=None

def classify(n):
 need(type(n)is dict and set(n)==TOP,'original exact refused outcome fields')
 need(n['schema']=='managed-usb-rt-synchronized-key-em-v1','EM original schema')
 for k in ('bindingQualified','opened','claimed','released','closed'):need(n[k]is True,'native true '+k)
 for k in ('accepted','observationAccepted','onsetObserved','onsetMissed','physicalPictureObserved','busContentsAltered'):need(n[k]is False,'native false '+k)
 for k,v in {'device':61,'writes':0,'retries':0,'cyclesStarted':19,'cleanCyclesCompleted':18,'cleanCyclesDiscarded':17,'bulkTransfers':290,'headersSent':145,'inputsCompleted':145,'overshootUs':0}.items():need(type(n[k])is int and n[k]==v,'exact refused count '+k)
 need(n['stage']=='terminal'and n['terminalReason']=='UnexpectedRt'and n['protocolPhase']=='ReadyForHeader','refused reason phase')
 need(n['retentionPolicy']=='last-fully-clean+transition+one-postfault-set+current-partial; older-clean-discarded','retention policy')
 start=integer(n['startUs']);deadline=integer(n['deadlineUs'],start);end=integer(n['endUs'],start);need(deadline-start==2_000_000 and end<=deadline,'2s cooperative budget')
 caps=n['retained'];need(type(caps)is list and [(c['role'],c['cycleIndex'],len(c['windows']),len(c['transfers']))for c in caps]==[('trigger-baseline',1,8,16),('last-clean',18,8,16),('current-partial',19,1,2)],'retained refusal exact shape')
 raws=[];last=start
 for ci,cap in enumerate(caps):
  summary,decoded=TRANSPORT.parse_capture(cap,cap['role'],['R','M','C','P','N','H','L','R']if ci<2 else['R'],ci)
  need(summary['first_us']>=last and summary['last_us']<=end,'retained chronological bounded captures');last=summary['last_us']
  for wi,(name,b,digest)in enumerate(decoded):
   need(base64.b64encode(b).decode()==cap['windows'][wi]['rawBase64'],'canonical retained raw')
   if cap['windows'][wi]['name']=='R':need(fields(b)['rt']==([0,0,1]if ci<2 else[0,0,0])and u16(b,0xc4)==40,'exact retained R context')
   raws.append({'name':name,'raw':b,'sha256':digest,'bytes':len(b),'headerBeforeUs':cap['transfers'][2*wi]['beforeUs'],'dataAfterUs':cap['transfers'][2*wi+1]['afterUs']})
 cp=n['scoreCheckpoints'];need(type(cp)is dict and set(cp)=={'schema','recordBytes','count','rawBase64','sha256'},'compact exactfields')
 need(cp['schema']=='em-dense-refresh-checkpoints-v1'and type(cp['recordBytes'])is int and cp['recordBytes']==54 and type(cp['count'])is int and cp['count']==18,'18 full54B compact rows')
 packed=base64.b64decode(cp['rawBase64'],validate=True);need(len(packed)==18*54 and sha(packed)==cp['sha256']and base64.b64encode(packed).decode()==cp['rawBase64'],'compact canonical extent/hash')
 rows=[];last=start
 for i in range(18):
  b=packed[i*54:(i+1)*54];hb,ha=struct.unpack_from('<2I',b,24);taps=struct.unpack_from('<6H2I',b,34)
  need(b[0]==0 and u16(b,2)==u16(b,4)==40,'clean compact state and unchanged40')
  need(last<=start+hb<=start+ha<=end,'compact Hbracket ordering');last=start+ha
  row={'cycleIndex':i+1,'selectorC7':b[1],'a0U32':struct.unpack_from('<I',b,6)[0],'q0':u16(b,10),'history':list(struct.unpack_from('<4H',b,12)),'ordinal0':struct.unpack_from('<I',b,20)[0],'publicationMirror':u16(b,32),'trainer4a2':taps[0],'trainerAggregate4a4':taps[1],'selectorMirror4c2':taps[2],'refreshCounter4c4':taps[3],'endR2460':taps[4],'endR246e':taps[5],'dynamicA':hex(taps[6]),'dynamicB':hex(taps[7]),'hReadBracketUs':[start+hb,start+ha]}
  need(row['publicationMirror']==200 and all(row[k]==0 for k in ('selectorC7','a0U32','q0','ordinal0','trainer4a2','trainerAggregate4a4','selectorMirror4c2','refreshCounter4c4','endR2460','endR246e'))and row['history']==[0]*4,'actual previous18rows source taps')
  rows.append(row)
 for ci in (0,1):
  cap=caps[ci];w=[base64.b64decode(x['rawBase64'])for x in cap['windows']];b=bytearray(54);b[0]=0;b[1]=w[2][7];b[2:4]=w[0][0xc4:0xc6];b[4:6]=w[7][0xc4:0xc6];b[6:10]=w[5][4:8];b[10:12]=w[5][28:30];b[12:20]=w[5][40:48];b[20:24]=w[4][:4];b[32:34]=w[1][42:44]
  struct.pack_into('<2I',b,24,cap['transfers'][10]['beforeUs']-start,cap['transfers'][11]['afterUs']-start)
  for dest,src,off,length in ((34,1,2,2),(36,1,4,2),(38,1,34,2),(40,1,36,2),(42,7,0x60,2),(44,7,0x6e,2),(46,3,4,4),(50,3,8,4)):b[dest:dest+length]=w[src][off:off+length]
  idx=cap['cycleIndex']-1;need(packed[idx*54:(idx+1)*54]==b,'retained fullcycle compact byte equality')
 key=n['intervention'];need(type(key)is dict and set(key)=={'key','trigger','attempted','completed','armedUs','endUs','uiReceiptObserved','physicalPictureObserved','calls'},'key exactfields')
 need(key['key']=='Left'and key['trigger']=='first-full-clean-cycle'and key['attempted']is True and key['completed']is True and key['uiReceiptObserved']is False and key['physicalPictureObserved']is False,'one completed fixedkey noUIreceipt')
 need(caps[0]['transfers'][-1]['afterUs']<=integer(key['armedUs'],start,end),'key arms after firstfullclean')
 need(type(key['calls'])is list and len(key['calls'])==2,'two key children');prior=key['armedUs']
 for call,phase in zip(key['calls'],('down','up')):
  need(type(call)is dict and set(call)=={'phase','beforeUs','afterUs','exitCode','started','reaped','timedOut','stdoutBytes','stderrBytes'},'key child fields')
  need(call['phase']==phase and call['started']is True and call['reaped']is True and call['timedOut']is False and all(type(call[k])is int and call[k]==0 for k in ('exitCode','stdoutBytes','stderrBytes')),'reaped zeroexit key')
  before=integer(call['beforeUs'],prior,end);prior=integer(call['afterUs'],before,end)
 need(prior<=integer(key['endUs'],prior,end),'worker reconciled')
 return raws,rows

def analyze():
 global TRANSPORT
 for row in j(HERE/'input-pins.json')['files']:
  b=Path(row['path']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'original immutable input')
 need(sha((D/'source-inventory.json').read_bytes())=='57f39a8f4041944d4cb2515b03c25fabedcc6b5de37206d65bbeb23306ee8be2','frozen EM inventory')
 for row in j(D/'source-inventory.json')['files']:
  b=(D/row['path']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'all44 EM source/payload pins')
 wrapper=module(D/'run-once.py','eo_refusal_wrapper','01b5937f625e45516d435e6093cef47aebde9cbf1380e997173f238eab9e9308');parser=module(D/'parse-result.py','eo_strict_success_parser','cfa98869b725ce86d9bab876e7a59c554f690b75f77e17e22de035b214cdc49c');TRANSPORT=module(D/'transport-parser.py','eo_lower_transport','aa039a8250a0581c063f8e96bf877a6b3dcb7f3e050783b592106c5d23ec2f9e')
 manifest,payload=wrapper.build_manifest();mr=wrapper.manifest_bytes(manifest);need(sha(mr)==MAN and mr==(P/'reviewed-manifest.json').read_bytes(),'same regenerated capturedmanifest')
 ready,rr=wrapper.load_readiness(EO/'trial-01/onset-readiness/readiness.json',READY);need(rr==(P/'readiness-decision.json').read_bytes(),'same original readiness')
 for row in ready['evidence']:need(sha(Path(row['path']).read_bytes())==row['sha256'],'original readiness evidence')
 phase=(EO/'trial-01/onset-phase.md').read_bytes();need(sha(phase)==ready['closedWorldVendorOutLineage']['evidenceSha256']and phase.decode().strip()==ready['closedWorldVendorOutLineage']['statement'],'phase premise exact')
 cached=j(EO/'trial-01/onset-readiness/metadata-root.json');need(len(cached['calls'])==1,'one cached readiness request');ct=cached['calls'][0];text=call_check(ct);need(ct['command']=='set -eu\n'+wrapper.metadata_body(ready['identity'],'EM_CURRENT_READY'),'exactcachedmetadata command');need(text==(EO/'trial-01/onset-readiness/metadata.txt').read_text()and wrapper.parse_metadata(text,'EM_CURRENT_READY')==j(EO/'trial-01/onset-readiness/census-summary.json'),'cached metadata/census bytes')
 record=j(P/'record.json');need(record['manifestSha256']==MAN and record['readinessSha256']==READY and record['native_invocations']==1 and record['cleanup_required']is True and record['target_operations']is None and record['target_operations_status']=='inflight_or_unknown'and record['phase']=='native'and record['no_retry']is True,'original refused record preserved')
 need(not(P/'result.json').exists()and not(P/'interpretation.json').exists()and 'postCensus'not in record and 'cleanup_stdout'not in record,'no success/postcensus/cleanup promoted')
 for tag in ('selftest','native'):
  env=(P/(tag+'-envelope.txt')).read_text()
  if tag=='native':need(env.startswith('IMMEDIATE_READY\n'),'immediate identity');env=env[len('IMMEDIATE_READY\n'):]
  terminal,private,stdout,stderr=wrapper.receipt_envelope(env)
  need(terminal==record[tag+'Terminal']and terminal['boot']==ready['identity']['boot']and terminal['exit_code']==(1 if tag=='native'else 0),'actual nativeexit1 selftest0')
  need(private==(P/(tag+'.receipt.json')).read_bytes()and stdout==(P/(tag+'.stdout')).read_bytes()and stderr==(P/(tag+'.stderr')).read_bytes()==b'','private receipt separateopaqueGC exact')
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'diagnostic separate')
  if tag=='selftest':need(wrapper.strict_json(private.decode())=={'selfTestsPassed':93,'keyTestsPassed':22,'checkpointTestsPassed':46,'targetOperations':0},'zeroIO selftest')
 raw=(P/'native.receipt.json').read_bytes();need(len(raw)<=24576,'receipt cap');n=wrapper.strict_json(raw.decode());raws,rows=classify(n)
 reject(lambda:parser.parse_native(raw.decode()))
 need(n['device']==int(ready['identity']['devnum'])==61,'compact binding toUSB61')
 for marker,key,name in [('PRE_READY','preCensus','metadata-pre.txt'),('BEFORE_INVOKE_READY','beforeInvokeCensus','metadata-before-invoke.txt')]:need(wrapper.parse_metadata((P/name).read_text(),marker)==record[key],'cached census snapshots')
 calls=record['calls'];need(len(calls)==36,'36 original pre-refusal requests')
 for row in calls:call_check(row)
 class Mock:
  def __init__(self):self.i=0
  def root(self,command,rec,path):
   need(self.i<len(calls),'no following rootrequest');row=calls[self.i];self.i+=1;need(command==row['command'],'exact original generated command');rec['calls'].append(copy.deepcopy(row));wrapper.save(path,rec);return row['response']['commands'][0]['stdout']
 mock=Mock();wrapper.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].split('-')[-1]))
 with tempfile.TemporaryDirectory(prefix='mock-refusal-',dir=HERE)as tmp:
  out=Path(tmp)/'capture'
  try:wrapper.execute(out,ready,rr,mr,payload,mock,parser)
  except ValueError as e:need(str(e)=='exact successful exit and empty stderr','same native nonzero-exit gate')
  else:raise ValueError('refusal became acceptance')
  need(mock.i==36 and {p.name for p in out.iterdir()}=={p.name for p in P.iterdir()},'same stoppedrequestcount/artifacts')
  for f in out.iterdir():need(f.read_bytes()==(P/f.name).read_bytes(),'every rejectedartifact exact')
 stagefiles=[{'name':name,'bytes':len(b),'sha256':sha(b)}for name,b in payload.items()]
 for tag in ('selftest','native'):
  for suffix in ('.receipt.json','.stdout','.stderr'):
   name=tag+suffix;b=(P/name).read_bytes();stagefiles.append({'name':name,'bytes':len(b),'sha256':sha(b)})
 need(len(stagefiles)==9,'exactninefiles')
 # EB baseline independently strict-parsed; all16 raw/hash/index and28 transportresponses checked.
 eb=B/'rtp-lane-gate-capture-20261028eb';ep=module(eb/'parse-result.py','eo_baseline_parser','e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523');q=EO/'trial-01/baseline';bn,br,bq=ep.parse_native((q/'native.receipt.json').read_text());bres=j(q/'result.json')
 need(bres['accepted']is True and bres['cleanup']=='STAGE_ABSENT'and bres['manifestSha256']=='e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11','baseline accepted exactmanifest')
 for name,b,digest in br:need((q/name).read_bytes()==b and sha(b)==digest,'baseline everyrawhash')
 need(bres['rawFiles']==[{'name':name,'bytes':len(b),'sha256':digest}for name,b,digest in br],'baseline rawindex')
 for key in ('startR','endR'):need([bq[key][k]for k in ('stop','fault','ordinaryGate','alternateLimit')]==[0,0,1,40],'baseline clean40')
 for call in j(q/'record.json')['calls']:call_check(call)
 driver=j(EO/'trial-01/result.json');need(driver['accepted_pair']is False and driver['phase']=='stopped'and driver['target_recovery_invocations']==0 and driver['trace_collected']is True,'driver stopped no recovery')
 for name in ('admission-intent.json','post-readiness-intent.json','post-tables-intent.json'):need(not(EO/'trial-01/ledger'/name).exists(),'no admission/poststage dispatched')
 trace=j(EO/'trial-01/kernel-trace/result.json');tb=(EO/'trial-01/kernel-trace/trace.txt').read_bytes();need(trace['accepted']is True and trace['instance_removed']is True and trace['global_tracer_modified']is False and trace['retained_bytes']==len(tb)==1557 and trace['sha256']==sha(tb),'trace separate exact cleanup')
 ui=j(EO/'trial-01/ui-after/after-summary.json');need(ui=={'cached_current_tab':'d/ug.tab@Live','csfs_window_present':True,'physical_picture_observed':False,'screensaver_windows_present':False},'latercachedLive no optical')
 uiobj=j(EO/'trial-01/ui-after/after-snapshot.json');need(len(uiobj['calls'])==1,'onecachedUI');ut=call_check(uiobj['calls'][0]);need(ut==(EO/'trial-01/ui-after/after-snapshot.txt').read_text()and 'memory/eden/current_tab, value = d/ug.tab@Live (String)'in ut and 'ScreenSaverContent.dll'not in ut,'cachedUI summary savedgetter')
 for key,v in [('accepted',True),('observationAccepted',True),('released',False),('closed',False),('bindingQualified',False),('protocolPhase','Unknown'),('terminalReason','AlreadyFaulted'),('device',60),('headersSent',146),('bulkTransfers',289),('inputsCompleted',144),('cleanCyclesCompleted',19)]:
  bad=copy.deepcopy(n);bad[key]=v;reject(lambda:classify(bad))
 for ci,cap in enumerate(n['retained']):
  for wi,w in enumerate(cap['windows']):
   for key,value in [('sha256','0'*64),('address','0x47000000'),('count',0)]:
    bad=copy.deepcopy(n);bad['retained'][ci]['windows'][wi][key]=value;reject(lambda:classify(bad))
  for ti,t in enumerate(cap['transfers']):
   for key,value in [('count',0),('afterUs',n['endUs']+1)]:
    bad=copy.deepcopy(n);bad['retained'][ci]['transfers'][ti][key]=value;reject(lambda:classify(bad))
 for i in range(18):
  bad=copy.deepcopy(n);cp=bytearray(base64.b64decode(bad['scoreCheckpoints']['rawBase64']));cp[i*54]=0x20;bad['scoreCheckpoints']['rawBase64']=base64.b64encode(cp).decode();bad['scoreCheckpoints']['sha256']=sha(cp);reject(lambda:classify(bad))
 for idx in range(2):
  for key,value in [('reaped',False),('started',False),('timedOut',True),('exitCode',1)]:
   bad=copy.deepcopy(n);bad['intervention']['calls'][idx][key]=value;reject(lambda:classify(bad))
 prev=base64.b64decode(n['retained'][1]['windows'][-1]['rawBase64']);current=base64.b64decode(n['retained'][2]['windows'][0]['rawBase64']);changes=[i for i in range(256)if prev[i]!=current[i]];need(changes==[0x0e,0xca]and u16(current,0xca)==1 and u16(prev,0xca)==0,'only gate and root24ca mirror changed')
 priorpair=n['retained'][1]['transfers'][-2:];lastpair=n['retained'][2]['transfers'];down=n['intervention']['calls'][0]['beforeUs']
 need(not any(getattr(m,'__file__','')and Path(str(getattr(m,'__file__',''))).name=='root-with-margin.py'for m in sys.modules.values()),'no real rootadapter imported')
 return {'schema':'eo-unexpected-rt-analysis-v1','checks':checks,'manifestSha256':MAN,'readinessSha256':READY,'inputPinsSha256':sha((HERE/'input-pins.json').read_bytes()),'privateStageSha256':sha(record['remote_stage'].encode()),'stageFiles':sorted(stagefiles,key=lambda r:r['name']),'refusalClassification':{'nativeAccepted':False,'nativeObservationAccepted':False,'wrapperAccepted':False,'wrapperStoppedAtNonzeroNativeExit':True,'terminalReason':'UnexpectedRt','keyAttempted':True,'keyCompleted':True,'cleanCyclesCompleted':18,'cyclesStarted':19,'headers':145,'bulks':290,'phase':'ReadyForHeader','released':True,'closed':True,'stageCleanupPerformed':False},'originalRecordPreserved':{'cleanupRequired':True,'targetOperations':None,'targetOperationsStatus':'inflight_or_unknown','noResultJson':True},'exactRootCommandReplay':{'calls':36,'allSavedArtifactsByteExact':True,'maximumCommandBytes':max(row['command_bytes']for row in calls),'stoppedAtOriginalNonzeroExitGate':True,'noRealRootAdapterImported':True},'rawFiles':[{k:v for k,v in row.items()if k!='raw'}for row in raws],'checkpointRows':rows,'previousCleanR':fields(prev),'latestUnexpectedR':fields(current),'changedRByteOffsets':changes,'root24caMirror':{'previous':u16(prev,0xca),'latest':u16(current,0xca),'newC7WindowCaptured':False,'sourceInterpretation':'EJ source-copy mirror only; not a direct C+7 read at cycle19'},'key':n['intervention'],'nativeTiming':{'startUs':n['startUs'],'endUs':n['endUs'],'latestCleanRBracketUs':[priorpair[0]['beforeUs'],priorpair[1]['afterUs']],'unexpectedRBracketUs':[lastpair[0]['beforeUs'],lastpair[1]['afterUs']],'nonAtomicStateChangeBracketUs':[priorpair[0]['beforeUs'],lastpair[1]['afterUs']],'nonAtomicStateChangeBracketWidthUs':lastpair[1]['afterUs']-priorpair[0]['beforeUs'],'lastDataAfterDownBeginsUs':lastpair[1]['afterUs']-down,'physicalOrFaultOnsetTimestampProven':False},'baselineAccepted':True,'baselineReadBrackets':bq['readBrackets'],'laterCachedUi':ui,'driverStoppedBeforeAdmissionAndEbPost':True,'separateTrace':trace,'negativeCasesRejected':negatives,'claims':{'successfulObservationTrial':False,'latchedFault1001Proven':False,'gateWriteCauseProven':False,'atomicSnapshot':False,'allComparatorCallsObserved':False,'physicalPictureObserved':False,'cleanupAuthorizedByThisClassifier':False,'rootCauseOrFixEstablished':False,'newControllerReadAuthorizedByThisClassifier':False}}

if __name__=='__main__':
 value=analyze();raw=json.dumps(value,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--record']:
  with (HERE/'decoded.json').open('x')as f:f.write(raw)
 elif sys.argv[1:]==['--check']:need((HERE/'decoded.json').read_text()==raw,'exact frozen proof')
 else:raise SystemExit('usage: analyze.py --record|--check')
 print(json.dumps({'classified':True,'originalAccepted':False,'checks':checks,'negativeCases':negatives,'proofSha256':sha(raw.encode()),'targetCalls':0,'networkCalls':0},sort_keys=True))
