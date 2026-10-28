#!/usr/bin/env python3
"""Independent GF actual-artifact replay; host only, no real root adapter imported."""
import ast,base64,contextlib,copy,hashlib,io,json,re,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;F=D.parent;B=F.parent;GA=B/'live-saver-onset-adapter-20261028ga';FN=B/'combined-event-successor-20261028fn';EB=B/'rtp-lane-gate-capture-20261028eb';P=F/'capture-01'
checks=0;negative=0
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def need(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1
def reject(action,label):
 global negative
 try:action()
 except(ValueError,KeyError,TypeError,IndexError,UnicodeError,struct.error):negative+=1;return
 raise ValueError('unexpected acceptance '+label)
def j(path):return json.loads(path.read_bytes())
def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def load(path):
 m=types.ModuleType('offline_'+path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def pinned_inputs():
 rows=j(D/'input-pins.json')['files']
 for row in rows:
  raw=(B/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'input '+row['path'])
 return len(rows)
def audit_calls(calls):
 need(type(calls)is list and calls,'nonempty actual requests')
 for call in calls:
  response=call['response'];children=response['commands']
  need(type(call['transport_exit'])is int and call['transport_exit']==0 and call['host_timeout']is False and call['transport_stderr']=={'data':'','encoding':'base64'},'host transport success')
  need(response['authenticated']is True and type(response['uid'])is type(response['euid'])is int and response['uid']==response['euid']==0 and len(children)==1,'authenticated sole root child')
  child=children[0];need(child['command']==call['command']and type(child['exit_code'])is int and child['exit_code']==0 and child['timed_out']is False and child['stderr']=='','exact child success')
  need(call['command_bytes']==len(call['command'].encode())<=8192 and call['remote_timeout_seconds']==45 and call['host_timeout_limit_seconds']==75,'recorded command/budget caps')
  raw=base64.b64decode(call['transport_stdout']['data'],validate=True);need(json.loads(raw)==response and len(raw)<=65536 and len(child['stdout'].encode())<=65536,'raw transport JSON binding/caps')
def envelopes(folder,w,record):
 for tag in ['selftest','native']:
  text=(folder/(tag+'-envelope.txt')).read_text();needle=' --receipt-self-test > 'if tag=='selftest'else' --execute --device '
  matches=[c for c in record['calls']if needle in c['command']];need(len(matches)==1 and matches[0]['response']['commands'][0]['stdout']==text,'one original '+tag+' envelope')
  if tag=='native':need(text.startswith('IMMEDIATE_READY\n'),'immediate native identity guard');text=text.removeprefix('IMMEDIATE_READY\n')
  terminal,receipt,stdout,stderr=w.receipt_envelope(text);need(terminal==record[tag+'Terminal']and terminal['exit_code']==0 and stderr==b'','successful exclusive terminal')
  for suffix,raw in [('receipt.json',receipt),('stdout',stdout),('stderr',stderr)]:need(raw==(folder/(tag+'.'+suffix)).read_bytes(),'saved exclusive blob')
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'diagnostic stdout remains separate')
class Replay:
 def __init__(self,calls):self.calls=calls;self.at=0
 def root(self,command,record,path):
  need(self.at<len(self.calls),'no extra request');call=self.calls[self.at];self.at+=1;need(command==call['command'],'exact generated request');record['calls'].append(copy.deepcopy(call));save(path,record);return call['response']['commands'][0]['stdout']
def wrapper_replay(folder,w,parser,clock=None):
 record=j(folder/'record.json');audit_calls(record['calls']);envelopes(folder,w,record)
 manifest,payload=w.build_manifest();mr=w.manifest_bytes(manifest);need(mr==(folder/'reviewed-manifest.json').read_bytes()and sha(mr)==record['manifestSha256'],'exact reviewed source manifest')
 ready,raw=w.load_readiness(folder/'readiness-decision.json',record['readinessSha256'])
 need(len(ready['identity'])==16 and ready['identity']==j(F/'identity-01/identity.json')and ready['identity']['devnum']=='66','full same USB66 identity')
 for row in ready['evidence']:need(sha(Path(row['path']).read_bytes())==row['sha256'],'referenced lineage evidence pin')
 w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].rsplit('-',1)[-1]));root=Replay(record['calls'])
 with tempfile.TemporaryDirectory(dir=D/'private',prefix='replay-')as td:
  out=Path(td)/'capture';args={}if clock is None else{'clock':clock,'sleeper':lambda _:need(False,'unexpected repeat settle')}
  result=w.execute(out,ready,raw,mr,payload,root,parser,**args)
  need(root.at==len(record['calls'])and result==j(folder/'result.json'),'complete original wrapper replay')
  artifacts=0
  for path in out.iterdir():need(path.read_bytes()==(folder/path.name).read_bytes(),'byte-exact artifact '+path.name);artifacts+=1
 return {'commands':root.at,'artifacts':artifacts,'maxCommandBytes':max(c['command_bytes']for c in record['calls']),'manifestSha256':sha(mr)},record
def decode_row(raw,index,start):
 b=raw[index*58:(index+1)*58];h=lambda at:struct.unpack_from('<H',b,at)[0];u=lambda at:struct.unpack_from('<I',b,at)[0]
 return dict(cycle=index+1,startRt=b[0]>>4,endRt=b[0]&15,c7=b[1],startLimit=h(2),endLimit=h(4),mode1Aggregate=u(6),q=h(10),history=[h(k)for k in [12,14,16,18]],publicationOrdinal=u(20),hHeaderBeforeUs=start+u(24),hDataAfterUs=start+u(28),m4ca=h(32),m4a2=h(34),m4a4=h(36),m4c2=h(38),m4c4=h(40),r2460=h(42),r246e=h(44),pointer494=u(46),pointer498=u(50),r24ca=h(54),r2468=h(56))
def bl(raw,va):
 a,b=struct.unpack('<HH',raw);need(a&0xf800==0xf000 and b&0xd000==0xd000,'Thumb BL encoding');s=(a>>10)&1;v=s<<24|(1^((b>>13)&1)^s)<<23|(1^((b>>11)&1)^s)<<22|(a&0x3ff)<<12|(b&0x7ff)<<1
 return va+4+(v-(1<<25)if v&(1<<24)else v)
def run():
 count=pinned_inputs();w=load(GA/'run-once.py');parser=load(FN/'parse-result.py');cached=load(GA/'cached-check.py');ew=load(EB/'run-once.py');ep=load(EB/'parse-result.py')
 # Bind the parent's seven explicit CLIs and actual cached identity/readiness requests.
 for step in ['passive-premise-01','identity-01','baseline-readiness','baseline-capture','capture-readiness-01','capture-01','post-capture-ui']:
  folder=F/(step+'-logs');intent=j(folder/'intent.json');completion=j(folder/'completion.json');argv=intent['argv'];script=next(Path(v)for v in argv[1:]if not v.startswith('-'))
  need(intent['automaticRetry']is False and completion['exitCode']==0 and completion['endedHostMonotonicNs']>=intent['startedHostMonotonicNs']and not(folder/'stderr.txt').read_bytes(),'one completed explicit parent step')
  need(any(row['path']==str(script.relative_to(B))and row['sha256']==sha(script.read_bytes())for row in j(D/'input-pins.json')['files']),'parent executed script source pin')
  if step in ['baseline-capture','capture-01']:
   result=j(F/step/'result.json');need(json.loads((folder/'stdout.txt').read_bytes())==result,'parent stdout result equality')
   need(argv[argv.index('--manifest-sha256')+1]==result['manifestSha256']and argv[argv.index('--readiness-sha256')+1]==result['readinessSha256'],'parent explicit manifest/readiness pins')
 identity_record=j(F/'identity-01/census-root.json');audit_calls(identity_record['calls']);need(len(identity_record['calls'])==2,'two actual cached identity/census calls')
 dk=load(B/'volatile-limit-trial-20261028dk/capture-usb-identity.py');df=load(B/'firmware-rtp-producer-20261028df/capture/run-once.py');root=Replay(identity_record['calls']);original=dk.load;argv=sys.argv
 def substitute(path,pin,name):
  need(sha(path.read_bytes())==pin,'identity helper supplied source pin')
  return root if path==B/'managed-ui-tab-launch/root-with-margin.py'else df
 dk.load=substitute
 try:
  with tempfile.TemporaryDirectory(dir=D/'private',prefix='identity-replay-')as td:
   out=Path(td)/'identity';sys.argv=['capture-usb-identity.py','--output',str(out)]
   with contextlib.redirect_stdout(io.StringIO()):dk.main()
   for path in out.iterdir():need(path.read_bytes()==(F/'identity-01'/path.name).read_bytes(),'exact identity helper artifact')
 finally:dk.load=original;sys.argv=argv
 need(root.at==2,'complete original identity helper replay')
 for folder,wrapper,marker in [(F/'baseline-readiness',ew,'EI_CURRENT_READY'),(F/'capture-readiness-01',w,'GA_CURRENT_READY')]:
  record=j(folder/'metadata-root.json');audit_calls(record['calls']);ready=j(folder/'readiness.json');need(len(record['calls'])==1 and ready['identity']==j(F/'identity-01/identity.json'),'same identity in fresh cached readiness')
  call=record['calls'][0];need(call['command']=='set -eu\n'+wrapper.metadata_body(ready['identity'],marker)and call['response']['commands'][0]['stdout']==(folder/'metadata.txt').read_text(),'exact source cached readiness request/response')
  need(wrapper.parse_metadata((folder/'metadata.txt').read_text(),marker)==j(folder/'census-summary.json'),'actual cached readiness census')
 # Replay both actual wrappers in memory, using no real root adapter or native entrypoint.
 eb_replay,er=wrapper_replay(F/'baseline-capture',ew,ep);en,raws,ei=ep.parse_native((F/'baseline-capture/native.receipt.json').read_text())
 need(en['accepted']and en['device']==66 and en['headersSent']==16 and en['bulkTransfers']==32 and en['writes']==en['uiOperations']==0 and en['released']and en['closed'],'fresh accepted zero-write EB baseline')
 for name,raw,digest in raws:need(raw==(F/'baseline-capture'/name).read_bytes()and sha(raw)==digest,'all sixteen EB raw files')
 rb=[(F/'baseline-capture'/name).read_bytes()for name in ['start-R.bin','end-R.bin']];half=lambda raw,at:struct.unpack_from('<H',raw,at)[0]
 need(rb[0]==rb[1]and all([half(raw,at)for at in [0,6,10,14,196]]==[0,0,0,1,40]for raw in rb),'equal full Clean40/logger0 R brackets')
 ebm=(F/'baseline-capture/M.bin').read_bytes();ebc=(F/'baseline-capture/C.bin').read_bytes();need(ebm[56]==1 and ebc[7:9]==b'\0\3'and all(not any((F/'baseline-capture'/name).read_bytes())for name in ['start-N.bin','end-N.bin']),'baseline scan1/C8three/Nzero')
 record=j(P/'record.json');cp=record['cachedCheckpoint'];clock=iter([cp['startedHostMonotonicNs'],cp['snapshots'][0]['queryBeforeHostMonotonicNs'],cp['snapshots'][0]['queryReturnedHostMonotonicNs'],cp['nativeCommandSubmitHostMonotonicNs']])
 ga_replay,record=wrapper_replay(P,w,parser,lambda:next(clock));need(ga_replay['commands']==44 and eb_replay['commands']==28,'exact 44 GA and 28 EB requests')
 n,_,interpretation=parser.parse_native((P/'native.receipt.json').read_text());need(n['accepted']and interpretation==j(P/'interpretation.json')and n['terminal']=='TransitionCaptured','accepted onset semantics')
 need((n['headers'],n['inputs'],n['bulks'],n['writes'])==(220,218,440,2)and n['cleanCycles']==24 and n['quiescentCycles']==1 and n['rows']['count']==26,'26 cycles plus twelve control pairs')
 need(n['restore']=='readback-zero'and n['phase']=='ReadyForHeader'and n['released']and n['closed']and not n['loggerMayRemain'],'restored/released/closed')
 need(cached.validate(P,cp)['accepted']and cp['hostSubmissionAgeNs']==8400128 and cp['acceptedSnapshotIndex']==1,'actual cached premise and 8.400128ms submission gap')
 need(record['wrapperUiOperations']==0 and not any('input_keyevent'in c['command']for c in record['calls']),'no wrapper key request')
 packed=parser.b64(n['rows']['rawBase64']);rows=[decode_row(packed,i,n['startUs'])for i in range(26)]
 need([(r['cycle'],r['startRt'],r['endRt'])for r in rows if r['startRt']or r['endRt']]==[(14,3,3),(26,1,1)],'one Quiescent and final Faulted cycle')
 need(all(r['startLimit']==r['endLimit']==40 for r in rows)and [r['mode1Aggregate']for r in rows[19:]]==[8,16,24,24,32,40,48],'all sampled limit40 and final aggregate sequence')
 need([r['c7']for r in rows]==[0]*13+[1]*13 and all(r['m4c2']==r['c7']for r in rows),'selector changes at cycle14')
 retained=[]
 for cap in n['retained']:
  buffers=parser.capture(cap);need(parser.pack_row(cap,buffers,n['startUs'])==packed[(cap['cycle']-1)*58:cap['cycle']*58],'all58 retained-byte binding')
  m,c=buffers[1:3];r0,r1=buffers[0],buffers[7]
  retained.append(dict(role=cap['role'],cycle=cap['cycle'],aa=half(m,10),ac=half(m,12),scan=m[56],root=struct.unpack_from('<I',m,64)[0],c7=c[7],c8=c[8],invocationCounter=half(m,0),publicationBound=half(m,42),currentCounts=list(struct.unpack_from('<6H',buffers[4],24)),startR=[half(r0,k)for k in [0,6,10,14,196]],endR=[half(r1,k)for k in [0,6,10,14,196]],readBrackets=[dict(name=z['name'],headerBeforeUs=cap['transfers'][2*i][4],dataAfterUs=cap['transfers'][2*i+1][5],bytes=len(buffers[i]),sha256=sha(buffers[i]))for i,z in enumerate(cap['windows'])]))
 need(retained[0]['invocationCounter']==56 and retained[-1]['invocationCounter']==57 and all(r['aa']==0 and r['ac']==2 and r['scan']==1 and r['c8']==3 and r['root']==0x20010000 for r in retained),'retained full mode/root/context and counter56to57')
 key=n['intervention'];down,up=key['calls'];need(key['attempted']and key['completed']and all(c['started']and c['reaped']and not c['timedOut']and c['exitCode']==0 for c in key['calls']),'one successful native Left down/up')
 last=n['retained'][-1];first_fault=last['transfers'][0][4:6];fault_data_after=last['transfers'][1][5]
 need(interpretation['keyExposureQualified']and retained[0]['readBrackets'][-1]['dataAfterUs']<down['beforeUs']<up['afterUs']<first_fault[0],'full baseline then successful key before later optional fault R')
 baseline=(P/'baseline-ring.bin').read_bytes();post=(P/'post-ring.bin').read_bytes();need(parser.bind_rings(n,baseline,post)==j(P/'ring-metadata.json'),'complete two ring sidecar binding')
 a=struct.unpack_from('<III',baseline);z=struct.unpack_from('<III',post);need(a==(2270,2270,0)and z==(3466,3442,1),'exact ring endpoint fields')
 candidate=post[12+a[0]:12+z[0]];need(len(candidate)==1196 and candidate.startswith(b'[RTP:NORMAL][56]\n')and candidate.endswith(b'rtp_act_736\n'*2),'candidate header/event pair')
 pattern=rb'\[RTP\s+(\d+)\]RGB:(\d+) x:\s*(\d+) y:\s*(\d+)/c:\s*(\d+)/diff:(\d+)/m:(\w+)\n';details=[]
 for line in candidate.splitlines(keepends=True)[1:-2]:
  match=re.fullmatch(pattern,line);need(match is not None,'complete detail row');num=list(map(int,match.groups()[:6]));ordinal,rgb,x,y,b,diff=num;details.append(dict(ordinal=ordinal,rgb=rgb,x=x,y=y,b=b,diff=diff,mode=match[7].decode(),conditional12bitACandidates=[v for v in sorted(set([b-diff,b+diff]))if 0<=v<=4095]))
 need([r['ordinal']for r in details]==[0,1,2,3,8,9,10,11,16,17,18,19,24,25,26,27,32,33,34,35,40]and all(r['rgb']==0 and r['y']==2159 and r['mode']=='NORMAL'for r in details),'21 formatted rows with source-compatible print-throttle gaps')
 outside=lambda raw:raw[12:12+a[0]]+raw[12+z[0]:]
 need(outside(baseline)==outside(post),'data outside cursor-selected candidate unchanged')
 need(post[12+z[1]:12+z[0]]==b'rtp_act_736\n'*2 and z[0]-z[1]==24,'second field ends just before event-pair suffix; ownership not inferred')
 # Validate selected source spans and positive direct edges, without copying OEM bytes.
 asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(sha(asset)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package identity')
 image=asset[0x40200:0x60200];spans=[]
 for row in j(B/'fault-event-logging-options-20261028et/source-audit.json')['sourceRanges']:
  at=int(row['address'],16);need(sha(image[at:at+row['bytes']])==row['sha256'],'selected event/source span');spans.append(row)
 for at,target in [(0x203a,0xc1e0),(0xc206,0x1b8c8),(0xc20e,0x1b8c8)]:need(bl(image[at:at+4],at)==target,'selected caller/sink edge')
 need(image[0xc214:0xc220]==b'rtp_act_%d\n\0'and image[0xbb48:0xbb55]==b'[RTP:%s][%d]\n'and struct.unpack_from('<I',image,0xbaf4)[0]==0x200004a0,'event/header literal and invocation counter source')
 for row in j(B/'combined-event-successor-trial-20261028fo/live-analysis/decoded.json')['sourceSpans']:
  at=int(row['va'],16);need(sha(image[at:at+row['bytes']])==row['sha256'],'header/formatter source span');spans.append(row)
 for row in j(B/'rtp-normal-header-trace-20261028fr/source-audit.json')['sourceSpans']:
  at=int(row['va'],16);end=int(row['endExclusive'],16);need(sha(image[at:end])==row['sha256'],'aggregate/selection/epoch source span');spans.append(row)
 advance=lambda index,count:(index+count-1)%15360+1
 need(advance(a[0],1196)==advance(a[0],1196+15360)==advance(a[0],1196+2*15360)==z[0],'same endpoint compatible with zero/one/two additional whole laps')
 need(advance(15360,1)==1 and advance(15359,1)==15360,'source bytewise cursor boundary')
 # Execute only the extracted cached snapshot function, supplying an in-memory root replay.
 nav_path=B/'ui-navigation-20261027br/navigate.py';nav_ast=ast.parse(nav_path.read_bytes());func=next(v for v in nav_ast.body if isinstance(v,ast.FunctionDef)and v.name=='command_snapshot');namespace={'BOOT':w.BOOT,'save':save};exec(compile(ast.Module(body=[func],type_ignores=[]),str(nav_path),'exec'),namespace)
 ui=[]
 for folder,saver in [(F/'passive-premise-01/query-1',True),(F/'post-capture-ui',False)]:
  rec=j(folder/'before-snapshot.json');audit_calls(rec['calls']);need(len(rec['calls'])==1 and rec['calls'][0]['command']==cached.snapshot_command(),'cached-only UI request source')
  replay=Replay(rec['calls'])
  with tempfile.TemporaryDirectory(dir=D/'private',prefix='ui-replay-')as td:
   out=Path(td);summary=namespace['command_snapshot'](replay,out,'before')
   for path in out.iterdir():need(path.read_bytes()==(folder/path.name).read_bytes(),'byte-exact UI artifact')
  raw=(folder/'before-snapshot.txt').read_text();strict=cached.parse_snapshot(raw);need(strict['cachedTab']=='d/ug.tab@Live'and strict['screensaverWindowsPresent']==saver and strict['csfsWindowPresent'],'actual passive/post Live/saver semantics');ui.append(summary)
 passive=j(F/'passive-premise-01/result.json');need(passive['accepted']and len(passive['queries'])==1 and passive['keys']==passive['vendorOperations']==passive['resetRequests']==0,'one passive query, no key/vendor/reset')
 # Focused malformed fixtures preserve original strict parser acceptance and raw binding.
 for field,value in [('phase','Unknown'),('headers',219),('inputs',217),('bulks',439),('writes',1),('threshold',200),('cleanCycles',25),('quiescentCycles',0),('loggerMayRemain',True),('released',False),('closed',False)]:
  bad=copy.deepcopy(n);bad[field]=value;reject(lambda:parser.parse_native(json.dumps(bad)+'\n'),field)
 for cycle in [1,26]:
  for offset in range(58):
   bad=copy.deepcopy(n);raw=bytearray(packed);raw[(cycle-1)*58+offset]^=1;bad['rows']['rawBase64']=base64.b64encode(raw).decode();bad['rows']['sha256']=sha(raw);reject(lambda:parser.parse_native(json.dumps(bad)+'\n'),'retained58 byte')
 for target in [0,1]:
  for kind in ['short','changed','index']:
   raw=bytearray([baseline,post][target])
   if kind=='short':raw=raw[:-1]
   elif kind=='changed':raw[-1]^=1
   else:struct.pack_into('<I',raw,0,15361)
   reject(lambda:parser.bind_rings(n,bytes(raw)if target==0 else baseline,bytes(raw)if target==1 else post),'ring '+kind)
 for field,value in [('transport_exit',False),('host_timeout',True),('command_bytes',0)]:
  altered=copy.deepcopy(record['calls'][:1]);altered[0][field]=value;reject(lambda:audit_calls(altered),'transport '+field)
 controls=[]
 for c in n['controls']:
  raw=parser.capture(c,False);windows=[]
  for z,b in zip(c['windows'],raw):
   item={'name':z['name'],'bytes':len(b),'sha256':sha(b)}
   if z['name']=='R':item['rStopLoggerFaultGateLimit']=[half(b,k)for k in [0,6,10,14,196]]
   if z['name']=='M':item.update(aa=half(b,10),ac=half(b,12),scan=b[56],root=struct.unpack_from('<I',b,64)[0])
   if z['name']=='C':item.update(c7=b[7],c8=b[8])
   windows.append(item)
  controls.append({'role':c['role'],'beforeUs':c['transfers'][0][4],'afterUs':c['transfers'][-1][5],'windows':windows})
 need(controls[-1]['windows'][0]['rStopLoggerFaultGateLimit']==[1,0,4097,0,40]and controls[-3]['windows'][0]['rStopLoggerFaultGateLimit']==[1,1,4097,0,40],'restore changes logger only while fault tuple remains latched')
 need(pinned_inputs()==count,'final cutoff unchanged')
 return dict(schema='gf-independent-live-analysis-v1',scope='through post-capture-ui; later fault EB/recovery excluded',inputFilesVerified=count,checksPassed=checks,malformedRefusals=negative,gaReplay=ga_replay,baselineEbReplay=eb_replay,identityReplayCommands=2,freshReadinessCommands=2,totalUniqueRootRequestsVerified=78,baselineEb=dict(accepted=True,device=66,rawFiles=16,headers=16,bulks=32,fullRStartEndEqual=True,rTuples=[[0,0,0,1,40]]*2,c7=ebc[7],c8=ebc[8],scan=ebm[56],nZero=True),native=dict(accepted=True,terminal=n['terminal'],headers=n['headers'],inputs=n['inputs'],bulks=n['bulks'],writes=n['writes'],startUs=n['startUs'],endUs=n['endUs'],durationUs=n['endUs']-n['startUs'],cleanRows=24,quiescentRows=1,faultRows=1,restore=n['restore'],phase=n['phase'],released=n['released'],closed=n['closed']),rows=rows,retained=retained,key=key,keyExposure=interpretation['keyExposure'],transitionObservationEnclosure=dict(lastCleanCycle=25,lastCleanEndRExactTimestampRetained=False,lowerBoundUs=rows[24]['hDataAfterUs'],lowerBoundSource='cycle25 H input completed before its later end-R Clean sample',firstFaultCycle=26,firstFaultRHeaderBeforeUs=first_fault[0],firstFaultRInputAfterUs=fault_data_after,upperBoundUs=fault_data_after,exactSetterTimeProven=False),controls=controls,ringReadBrackets=[dict(role=role,beforeUs=n[role]['transfer']['transfers'][0][4],afterUs=n[role]['transfer']['transfers'][-1][5])for role in ['baselineRing','postRing']],cachedCheckpoint=cp,passiveAndPostUi=ui,ring=dict(baselineHeader=list(a),postHeader=list(z),baselineSha256=sha(baseline),postSha256=sha(post),candidateBytes=len(candidate),candidateSha256=sha(candidate),dataBytesChanged=sum(x!=y for x,y in zip(baseline[12:],post[12:])),outsideCandidateDataUnchanged=True,normalHeaderInvocationCounter=56,detailRows=details,event736Lines=2,baselineFullEventLines=baseline.count(b'rtp_act_736\n'),postFullEventLines=post.count(b'rtp_act_736\n'),secondToFirstCursorDifference=24,lapCountProven=False,chronologicalDeltaProven=False,consumerOwnershipProven=False,sharedRecordEpochProven=False),sourceSpans=spans,wrapperKeys=0,thresholdWrites=0,physicalPictureObserved=False,forYouTransitionProven=False,actualFpProven=False,executingCallerPcProven=False,exactEventTimestampProven=False,rootCauseFixEstablished=False,targetOperations=0,networkOperations=0)
if __name__=='__main__':
 value=run();raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 if '--write'in sys.argv:(D/'decoded.json').write_bytes(raw)
 else:need(raw==(D/'decoded.json').read_bytes(),'derived result matches frozen summary')
 print(json.dumps({key:value[key]for key in ['checksPassed','inputFilesVerified','malformedRefusals','gaReplay','baselineEbReplay','targetOperations']},sort_keys=True))
