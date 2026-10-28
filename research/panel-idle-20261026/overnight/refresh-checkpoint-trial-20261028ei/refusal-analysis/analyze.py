#!/usr/bin/env python3
"""Explicit original AlreadyFaulted refusal classifier, not a success-parser projection."""
import base64,copy,hashlib,importlib.util,json,struct,sys,tempfile,types,os
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EI=HERE.parent;B=EI.parent;D=B/'rtp-refresh-checkpoints-20261028eh';P=EI/'onset-01';checks=0;negatives=0
MAN='d0059b32e4e3d99a398a3763934e8927cd2967126c6d1ad9e76d8bf069f3059e';READY='61c965a32f2dc169a0a7e954d92b684dd7cc9777b14add3b2d5cc620a1556ea4'
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
def classify(n):
 need(type(n)is dict and set(n)==TOP,'original exact refusal fields')
 need(n['schema']=='managed-usb-rt-synchronized-key-eh-v1','native EH schema')
 for k in ('bindingQualified','observationAccepted','opened','claimed','released','closed','onsetMissed'):need(n[k]is True,'required native flag '+k)
 for k in ('accepted','onsetObserved','physicalPictureObserved','busContentsAltered'):need(n[k]is False,'required native false '+k)
 for k,v in {'device':60,'writes':0,'retries':0,'cyclesStarted':1,'cleanCyclesCompleted':0,'cleanCyclesDiscarded':0,'bulkTransfers':16,'headersSent':8,'inputsCompleted':8,'overshootUs':0}.items():need(type(n[k])is int and n[k]==v,'refusal exact count '+k)
 need(n['stage']=='terminal'and n['terminalReason']=='AlreadyFaulted'and n['protocolPhase']=='ReadyForHeader','explicit reason/phase')
 need(n['retentionPolicy']=='last-fully-clean+transition+one-postfault-set+current-partial; older-clean-discarded','retention policy')
 start=integer(n['startUs']);deadline=integer(n['deadlineUs'],start);end=integer(n['endUs'],start);need(deadline-start==15000000 and end<=deadline,'fixed15s budget/native end')
 cp=n['scoreCheckpoints'];need(type(cp)is dict and type(cp.get('recordBytes'))is int and type(cp.get('count'))is int,'checkpoint strict integer types')
 need(n['scoreCheckpoints']=={'schema':'eh-refresh-checkpoints-v1','recordBytes':54,'count':0,'rawBase64':'','sha256':sha(b'')},'zero completed checkpoint raw')
 key=n['intervention'];need(type(key)is dict and set(key)=={'key','trigger','attempted','completed','uiReceiptObserved','physicalPictureObserved','calls'},'unarmed key exact fields')
 need(key['key']=='Left'and key['trigger']=='first-full-clean-cycle','fixed unarmed action')
 for k in ('attempted','completed','uiReceiptObserved','physicalPictureObserved'):need(key[k]is False,'no key activity '+k)
 need(type(key['calls'])is list and len(key['calls'])==2,'exact unstarted keycalls')
 for call,phase in zip(key['calls'],('down','up')):
  need(type(call)is dict and set(call)=={'phase','started','reaped','timedOut','stdoutBytes','stderrBytes'},'no key times/return fields')
  need(call['phase']==phase and all(call[k]is False for k in ('started','reaped','timedOut'))and type(call['stdoutBytes'])is int and call['stdoutBytes']==0 and type(call['stderrBytes'])is int and call['stderrBytes']==0,'unstarted zero-output keycall')
 caps=n['retained'];need(type(caps)is list and len(caps)==2,'two retained captures')
 need([(c['role'],c['cycleIndex'],len(c['windows']),len(c['transfers']))for c in caps]==[('initial-faulted',1,1,2),('post-fault',1,7,14)],'initial R +post7 exact shapes')
 out=[];last=start
 for ci,cap in enumerate(caps):
  need(set(cap)=={'role','cycleIndex','windows','transfers'}and type(cap['cycleIndex'])is int,'capture exact fields');specs=SPECS[:1]if ci==0 else SPECS[1:]
  for wi,(name,address,size)in enumerate(specs):
   w=cap['windows'][wi];keys={'name','address','expected','count','complete','rawBase64','sha256'}|({'observedRtState'}if name=='R'else set());need(type(w)is dict and set(w)==keys,'exact window fields')
   need(w['name']==name and w['address']==f'0x{address:08x}'and type(w['expected'])is int and w['expected']==size and type(w['count'])is int and w['count']==size and w['complete']is True,'exact readonly spec/count')
   need(type(w['rawBase64'])is str and type(w['sha256'])is str,'raw types');raw=base64.b64decode(w['rawBase64'],validate=True);need(len(raw)==size and base64.b64encode(raw).decode()==w['rawBase64']and sha(raw)==w['sha256'],'canonical full raw/hash')
   if name=='R':
    need(type(w['observedRtState'])is dict and all(type(w['observedRtState'].get(k))is int for k in ('stop','fault','ordinaryGate')),'RT strict types')
    need(w['observedRtState']=={'stop':1,'fault':4097,'ordinaryGate':0,'classification':'Faulted'}and [u16(raw,o)for o in (0,10,14)]==[1,4097,0],'exact raw faulted state')
   pair=cap['transfers'][2*wi:2*wi+2]
   for t,direction,expected in zip(pair,('OUT','IN'),(12,size)):
    need(type(t)is dict and set(t)=={'name','direction','expected','count','errno','beforeUs','afterUs'},'transfer complete/error-free fields')
    need(t['name']==name+('-header'if direction=='OUT'else'-data')and t['direction']==direction and type(t['expected'])is int and t['expected']==expected and type(t['count'])is int and t['count']==expected and type(t['errno'])is int and t['errno']==0,'exact paired transfer')
    before=integer(t['beforeUs'],last,end);after=integer(t['afterUs'],before,end);last=after
   fn=('initial-'if ci==0 else'post-')+name+'.bin'
   out.append({'name':fn,'raw':raw,'sha256':sha(raw),'address':address,'bytes':size,'headerLittleEndianHex':struct.pack('<III',0x101,address,size).hex(),'headerBeforeUs':pair[0]['beforeUs'],'dataAfterUs':pair[1]['afterUs']})
 return out

def analyze():
 for f in j(HERE/'input-pins.json')['files']:
  b=Path(f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'immutable input '+f['path'])
 need(sha((D/'source-inventory.json').read_bytes())=='38ae37ba3e64c516d0e9aa5d2e811d7c6d85e0164f6a155e3bb93ff0990991fd','frozen EH inventory')
 for f in j(D/'source-inventory.json')['files']:
  b=(D/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'all EH sources/payloads')
 wrapper=module(D/'run-once.py','ei_refusal_wrapper','4870a6a0c089a739e6bc8af4f3b9076dc73bc5cf21123a2a0b8305ef206dfc15')
 # The original strict decoder may recognize transport-only AlreadyFaulted; qualification stays false. No projection/accepted mutation.
 parser=module(D/'parse-result.py','ei_original_parser','1de2a8f769f4a801b85f2dff74bb840221e0394db8ec7acb9cffdd7a763d5229')
 manifest,payload=wrapper.build_manifest();mr=wrapper.manifest_bytes(manifest);need(mr==(D/'deployment-manifest.json').read_bytes()==(P/'reviewed-manifest.json').read_bytes()and sha(mr)==MAN,'regenerated exact manifest')
 ready,readyraw=wrapper.load_readiness(EI/'onset-readiness-01/readiness.json',READY);need(readyraw==(P/'readiness-decision.json').read_bytes(),'same captured readiness')
 cached=j(EI/'onset-readiness-01/metadata-root.json');need(len(cached['calls'])==1,'one cached readiness request');ct=cached['calls'][0];text=call_check(ct)
 need(ct['command']=='set -eu\n'+wrapper.metadata_body(ready['identity'],'EI_CURRENT_READY')and text==(EI/'onset-readiness-01/metadata.txt').read_text(),'exact cached-only readiness command/response')
 need(wrapper.parse_metadata(text,'EI_CURRENT_READY')==j(EI/'onset-readiness-01/census-summary.json'),'strict cached readiness census')
 for e in ready['evidence']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'all readiness evidence refs')
 phase=(EI/'onset-phase.md').read_bytes();need(sha(phase)==ready['closedWorldVendorOutLineage']['evidenceSha256']and phase.decode().strip()==ready['closedWorldVendorOutLineage']['statement'],'exact lineage premise')
 record=j(P/'record.json');need(record['manifestSha256']==MAN and record['readinessSha256']==READY and record['native_invocations']==1 and record['cleanup_required']is True and record['target_operations']is None and record['target_operations_status']=='inflight_or_unknown'and record['phase']=='native'and record['no_retry']is True and record['wrapperUiOperations']==0,'original wrapper refusal/inflight fields retained')
 need(not(P/'result.json').exists()and not(P/'interpretation.json').exists()and 'postCensus'not in record and 'cleanup_stdout'not in record,'no success/postcensus/cleanup artifacts')
 for tag in ('selftest','native'):
  envelope=(P/(tag+'-envelope.txt')).read_text()
  if tag=='native':need(envelope.startswith('IMMEDIATE_READY\n'),'native immediate cachedidentity');envelope=envelope[len('IMMEDIATE_READY\n'):]
  term,private,stdout,stderr=wrapper.receipt_envelope(envelope)
  need(term==record[tag+'Terminal']and term['boot']==ready['identity']['boot']and term['exit_code']==(1 if tag=='native'else 0),'actual nativeexit1/selftest0 sameboot')
  need(private==(P/(tag+'.receipt.json')).read_bytes()and stdout==(P/(tag+'.stdout')).read_bytes()and stderr==(P/(tag+'.stderr')).read_bytes()==b'','exclusive semantic/opaque diagnostic blobs')
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'opaque stdout independenthash')
  if tag=='selftest':need(wrapper.strict_json(private.decode())=={'selfTestsPassed':93,'keyTestsPassed':22,'checkpointTestsPassed':46,'targetOperations':0},'all zeroIO selftests')
 native_raw=(P/'native.receipt.json').read_bytes();need(len(native_raw)<=24576,'bounded native receipt');n=wrapper.strict_json(native_raw.decode());raws=classify(n);_,_,_,_,transportq=parser.parse_native(native_raw.decode());need(transportq['transportAccepted']is True and transportq['trialQualified']is False and transportq['observationAccepted']is True,'original decoder transport-only/nontrial result')
 need(n['device']==int(ready['identity']['devnum'])==60 and n['bindingQualified']is True,'native compactbinding/device60')
 for marker,key,filename in [('PRE_READY','preCensus','metadata-pre.txt'),('BEFORE_INVOKE_READY','beforeInvokeCensus','metadata-before-invoke.txt')]:need(wrapper.parse_metadata((P/filename).read_text(),marker)==record[key],'cached census parse')
 # Replay the original complete request sequence until its deliberate nonzero-exit gate.
 calls=record['calls'];need(len(calls)==36,'36 pre-refusal orchestration requests')
 for c in calls:call_check(c)
 class Mock:
  def __init__(self):self.position=0
  def root(self,command,replay_record,path):
   need(self.position<len(calls),'no extra request afterrefusal');c=calls[self.position];self.position+=1;need(command==c['command'],'exact generated command');replay_record['calls'].append(copy.deepcopy(c));wrapper.save(path,replay_record);return c['response']['commands'][0]['stdout']
 mock=Mock();wrapper.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].split('-')[-1]))
 with tempfile.TemporaryDirectory(prefix='mock-',dir=HERE)as t:
  out=Path(t)/'capture'
  try:wrapper.execute(out,ready,readyraw,mr,payload,mock,parser)
  except ValueError as e:need(str(e)=='exact successful exit and empty stderr','exact nonzero-exit gate refusal')
  else:raise ValueError('refused original unexpectedly accepted')
  need(mock.position==36,'stopped after original native response')
  need({p.name for p in out.iterdir()}=={p.name for p in P.iterdir()},'same refused saved artifacts')
  for f in out.iterdir():need(f.read_bytes()==(P/f.name).read_bytes(),'every refused saved artifact byteexact '+f.name)
 # No stage path is printed. The cleanup owner derives it from the original record and binds this digest.
 stagefiles=[{'name':name,'bytes':len(b),'sha256':sha(b)}for name,b in payload.items()]
 for tag in ('selftest','native'):
  for suffix in ('.receipt.json','.stdout','.stderr'):
   name=tag+suffix;b=(P/name).read_bytes();stagefiles.append({'name':name,'bytes':len(b),'sha256':sha(b)})
 need(len(stagefiles)==9 and len({f['name']for f in stagefiles})==9,'exact9stage file inventory')
 rawmap={r['name']:r['raw']for r in raws};m=rawmap['post-M.bin'];c=rawmap['post-C.bin'];p=rawmap['post-P.bin'];h=rawmap['post-H.bin'];nn=rawmap['post-N.bin'];rr=rawmap['post-R.bin']
 derived={'initialR':fields(rawmap['initial-R.bin']),'postR':fields(rr),'rBytesEqual':rawmap['initial-R.bin']==rr,'M':{'trainer4a2':u16(m,2),'trainerAggregate4a4':u16(m,4),'aa':u16(m,10),'ac':u16(m,12),'selectorMirror4c2':u16(m,34),'referenceRefreshCounter4c4':u16(m,36),'publicationBoundMirror':u16(m,42),'currentMetadataRow':u16(m,20),'savedMetadataRow':u16(m,48),'xBase':u16(m,32),'root':hex(struct.unpack_from('<I',m,64)[0])},'C':{'geometry':list(struct.unpack_from('<3H',c)),'selectorC7':c[7]},'P':{'dynamicA':hex(struct.unpack_from('<I',p,4)[0]),'dynamicB':hex(struct.unpack_from('<I',p,8)[0])},'N':{'ordinals':list(struct.unpack_from('<6I',nn)),'sourceCounts':list(struct.unpack_from('<6H',nn,24))},'H':{'a':list(struct.unpack_from('<6I',h,4)),'q':list(struct.unpack_from('<6H',h,28)),'history':[list(struct.unpack_from('<4H',h,40+8*k))for k in range(6)]},'endRControls':{'root2460':u16(rr,0x60),'root246e':u16(rr,0x6e)}}
 # Structural/malformed cases use cloned objects only, never force accepted=true for parsing.
 for key,v in [('accepted',True),('observationAccepted',False),('bindingQualified',False),('released',False),('closed',False),('protocolPhase','Unknown'),('device',59),('headersSent',9),('bulkTransfers',17),('inputsCompleted',7),('cleanCyclesCompleted',1),('onsetMissed',False),('terminalReason','TimeLimit')]:
  bad=copy.deepcopy(n);bad[key]=v;reject(lambda:classify(bad))
 for ci,cap in enumerate(n['retained']):
  for wi,w in enumerate(cap['windows']):
   bad=copy.deepcopy(n);bad['retained'][ci]['windows'][wi]['address']='0x47000000';reject(lambda:classify(bad))
   bad=copy.deepcopy(n);bad['retained'][ci]['windows'][wi]['count']-=1;reject(lambda:classify(bad))
   bad=copy.deepcopy(n);bad['retained'][ci]['windows'][wi]['sha256']='0'*64;reject(lambda:classify(bad))
  for ti,t in enumerate(cap['transfers']):
   bad=copy.deepcopy(n);bad['retained'][ci]['transfers'][ti]['count']-=1;reject(lambda:classify(bad))
   bad=copy.deepcopy(n);bad['retained'][ci]['transfers'][ti]['afterUs']=n['endUs']+1;reject(lambda:classify(bad))
 for key,value in [('count',False),('recordBytes',True)]:
  bad=copy.deepcopy(n);bad['scoreCheckpoints'][key]=value;reject(lambda:classify(bad))
 bad=copy.deepcopy(n);bad['retained'][0]['windows'][0]['observedRtState']['stop']=True;reject(lambda:classify(bad))
 for phaseindex in (0,1):
  bad=copy.deepcopy(n);bad['intervention']['calls'][phaseindex]['started']=True;reject(lambda:classify(bad))
  bad=copy.deepcopy(n);bad['intervention']['calls'][phaseindex]['beforeUs']=n['startUs'];reject(lambda:classify(bad))
 return {'schema':'ei-already-faulted-analysis-v1','checks':checks,'manifestSha256':MAN,'readinessSha256':READY,'inputPinsSha256':sha((HERE/'input-pins.json').read_bytes()),'privateStageSha256':sha(record['remote_stage'].encode()),'stageFiles':sorted(stagefiles,key=lambda x:x['name']),'refusalClassification':{'nativeObservationCompleted':True,'nativeAccepted':False,'wrapperAccepted':False,'wrapperStoppedAtNonzeroNativeExit':True,'terminalReason':'AlreadyFaulted','keyAttempted':False,'cleanCyclesCompleted':0,'headers':8,'bulks':16,'phase':'ReadyForHeader','released':True,'closed':True,'stageCleanupPerformed':False},'originalRecordPreserved':{'cleanupRequired':True,'targetOperations':None,'targetOperationsStatus':'inflight_or_unknown','noResultJson':True},'exactRootCommandReplay':{'calls':36,'allSavedArtifactsByteExact':True,'maximumCommandBytes':max(c['command_bytes']for c in calls),'stoppedAtOriginalNonzeroExitGate':True,'noRealRootAdapterImported':True},'bindingScope':{'nativeCompactQualifiedFlag':True,'sameSavedBootAndDevice60':True,'fullNativeBindingAuditRetained':False,'endpointQueueProof':False},'rawFiles':[{k:v for k,v in r.items()if k!='raw'}for r in raws],'derived':derived,'nativeTiming':{'startUs':n['startUs'],'endUs':n['endUs'],'firstHeaderBeforeUs':raws[0]['headerBeforeUs'],'lastDataAfterUs':raws[-1]['dataAfterUs'],'fullSequentialReadSpanUs':raws[-1]['dataAfterUs']-raws[0]['headerBeforeUs'],'scope':'conditional full OUT-before/IN-after software brackets; no physical onset timestamp'},'nativeTerminal':record['nativeTerminal'],'negativeCasesRejected':negatives,'claims':{'successfulObservationTrial':False,'faultPredatedAnyKeyInThisRun':True,'whenFaultBeganKnown':False,'historicalGateOrReferenceRefreshSequenceProven':False,'actualPointerHeaderOrEpochProven':False,'physicalPictureObserved':False,'cleanupAuthorizedByThisClassifier':False,'rootCauseOrFixEstablished':False}}

if __name__=='__main__':
 data=analyze();out=json.dumps(data,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--check']:
  need((HERE/'decoded.json').read_text()==out,'exact frozen proof')
  for f in data['rawFiles']:need((HERE/'raw'/f['name']).stat().st_size==f['bytes']and sha((HERE/'raw'/f['name']).read_bytes())==f['sha256'],'exact extracted raw')
 elif not sys.argv[1:]:
  # Export only the already-classified immutable raw content, under this owned private directory.
  wrapper=module(D/'run-once.py','ei_export_wrapper','4870a6a0c089a739e6bc8af4f3b9076dc73bc5cf21123a2a0b8305ef206dfc15');native=wrapper.strict_json((P/'native.receipt.json').read_text())
  (HERE/'raw').mkdir(mode=0o700,exist_ok=True)
  for r in classify(native):
   f=HERE/'raw'/r['name'];f.write_bytes(r['raw']);f.chmod(0o600)
  (HERE/'decoded.json').write_text(out)
 else:raise SystemExit('usage: analyze.py [--check]')
 print(json.dumps({'classified':True,'wrapperAccepted':False,'nativeReason':'AlreadyFaulted','checks':checks,'negativeCases':negatives,'proofSha256':sha(out.encode()),'hostOnly':True}))
