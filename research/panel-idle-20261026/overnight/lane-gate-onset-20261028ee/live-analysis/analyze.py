#!/usr/bin/env python3
"""Immutable-input EE replay. Mock transport only; no real root adapter import."""
import base64,copy,hashlib,importlib.util,json,struct,sys,tempfile,types
from datetime import datetime
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EE=HERE.parent;B=EE.parent;ED=B/'rtp-lane-gate-trial-20261028ed';checks=0;negatives=0
PACKAGES={
'dp':('rtp-score-checkpoints-20261028dp','ba02517d7f8bb5cae6aa4257c426b7cc50780bfdfd5e0a73a7838e2386dff9ee','9b5e476a50e73439e11a6e5ed78bae0079a1d802c054212a8974e079f77d6b3a'),
'eb':('rtp-lane-gate-capture-20261028eb','e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11','e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523')}
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
def checkpoint_rows(raw,start,expected):
 need(len(raw)==80*34 and len(expected)==80,'80x34 extent');rows=[]
 for i in range(80):
  packed,c7,s,e,a,q,*rest=struct.unpack('<BBHHIH4HIIIH',raw[i*34:(i+1)*34]);hist=rest[:4];ordinal,h0,h1,mirror=rest[4:]
  d={'cycleIndex':i+1,'selectorC7':c7,'startAlternateThreshold':s,'endAlternateThreshold':e,'a0U32':a,'a0Low16':a&65535,'q0U16':q,'history0U16x4':hist,'recordOrdinal0U32':ordinal,'hReadBracket':{'headerBeforeUs':start+h0,'dataAfterUs':start+h1},'publicationBoundMirror':mirror}
  need(packed==0 and c7 in (0,1)and h0<=h1,'clean H bracket')
  for key,value in d.items():need(expected[i][key]==value,'checkpoint independent '+key)
  rows.append(d)
 return rows
def retained(native):
 out=[]
 for cap in native['retained']:
  item={'role':cap['role'],'cycleIndex':cap['cycleIndex'],'windows':[]}
  for i,w in enumerate(cap['windows']):
   raw=base64.b64decode(w['rawBase64'],validate=True);ts=cap['transfers'][2*i:2*i+2];name=w['name'];d={}
   need(sha(raw)==w['sha256'],'retained hash')
   if name=='R':d=fields(raw)
   if name=='H':d={'a':list(struct.unpack_from('<6I',raw,4)),'q':list(struct.unpack_from('<6H',raw,28)),'history':[list(struct.unpack_from('<4H',raw,40+8*k))for k in range(6)]}
   if name=='N':d={'ordinals':list(struct.unpack_from('<6I',raw)),'sourceCounts':list(struct.unpack_from('<6H',raw,24))}
   if name=='M':d={'aa':u16(raw,10),'ac':u16(raw,12),'publicationBoundMirror':u16(raw,42),'currentMetadataRow':u16(raw,20),'savedMetadataRow':u16(raw,48),'xBase':u16(raw,32),'root':hex(struct.unpack_from('<I',raw,64)[0])}
   if name=='C':d={'geometry':list(struct.unpack_from('<3H',raw)),'selectorC7':raw[7]}
   item['windows'].append({'name':name,'sha256':sha(raw),'headerBeforeUs':ts[0]['beforeUs'],'dataAfterUs':ts[1]['afterUs'],'decoded':d})
  out.append(item)
 return out

def analyze():
 for f in j(HERE/'input-pins.json')['files']:
  raw=Path(f['path']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'input '+f['path'])
 mods={};wraps={};manifests={};payloads={}
 for kind,(dirname,mp,pp)in PACKAGES.items():
  d=B/dirname;mr=(d/'deployment-manifest.json').read_bytes();need(sha(mr)==mp,'manifest '+kind);man=json.loads(mr)
  for f in j(d/'source-inventory.json')['files']:
   raw=(d/f['path']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'all frozen files '+kind+'/'+f['path'])
  mods[kind]=module(d/'parse-result.py','ee_'+kind+'_parser',pp)
  wraps[kind]=module(d/'run-once.py','ee_'+kind+'_wrapper',man['wrapperFiles']['run-once.py']['sha256'])
  m,p=wraps[kind].build_manifest();need(wraps[kind].manifest_bytes(m)==mr,'regenerated '+kind);manifests[kind]=mr;payloads[kind]=p
 runs={};natives={};rawmaps={};readyids=[]
 for name,kind,readydir in [('onset-01','dp','onset-readiness-01'),('post-tables-01','eb','post-readiness-01')]:
  p=EE/name;wp=wraps[kind];parser=mods[kind];result=j(p/'result.json');record=j(p/'record.json')
  ready,readyraw=wp.load_readiness(EE/readydir/'readiness.json',result['readinessSha256']);readyids.append(ready['identity'])
  need(readyraw==(p/'readiness-decision.json').read_bytes(),'captured readiness')
  cached=j(EE/readydir/'metadata-root.json');need(len(cached['calls'])==1,'one cached readiness request')
  cachedcall=cached['calls'][0];cachedtext=call_check(cachedcall)
  need(cachedtext==(EE/readydir/'metadata.txt').read_text(),'cached readiness stdout')
  # Marker is part of the recorded fixed command, independently match the entire generated body.
  marker='EE_CURRENT_READY'
  need(cachedcall['command']=='set -eu\n'+wp.metadata_body(ready['identity'],marker),'cached-only readiness generated command')
  need(wp.parse_metadata(cachedtext,marker)==j(EE/readydir/'census-summary.json'),'readiness census strict replay')
  for e in ready['evidence']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'all readiness refs')
  premise=ready['closedWorldVendorOutLineage'];premisebytes=Path(premise['evidencePath']).read_bytes() if 'evidencePath'in premise else (EE/('onset-phase.md'if kind=='dp'else'post-phase.md')).read_bytes()
  need(sha(premisebytes)==premise['evidenceSha256']and premisebytes.decode().strip()==premise['statement'],'exact coordinator premise')
  need((p/'reviewed-manifest.json').read_bytes()==manifests[kind]and result['manifestSha256']==PACKAGES[kind][1],'reviewed manifest')
  parsed=parser.parse_native((p/'native.receipt.json').read_text())
  if kind=='dp':n,caps,files,gc,q=parsed;need(gc==[]and q['trialQualified']is True,'qualified DP')
  else:n,files,q=parsed
  need(q==j(p/'interpretation.json'),'saved strict interpretation')
  need(n['accepted']and n['released']and n['closed']and n['protocolPhase']=='ReadyForHeader','native lifecycle')
  need(result['accepted']and result['cleanup']=='STAGE_ABSENT'and result['nativeInvocations']==1 and result['retries']==0,'accepted one invocation/cleanup')
  need(n['writes']==0 and result['wrapperUiOperations']==0,'no native writes/wrapper UI')
  need(n['device']==int(ready['identity']['devnum']),'same device decision')
  rawmap={}
  for fn,raw,h in files:need((p/fn).read_bytes()==raw and sha(raw)==h,'all actual raw '+fn);rawmap[fn]=raw
  need(result['rawFiles']==record['retained_raw_files']==[{'name':fn,'bytes':len(raw),'sha256':h}for fn,raw,h in files],'raw exact inventory')
  for tag in ('native','selftest'):
   er=(p/(tag+'-envelope.txt')).read_text()
   if tag=='native':need(er.startswith('IMMEDIATE_READY\n'),'immediate ready');er=er[len('IMMEDIATE_READY\n'):]
   term,private,stdout,stderr=wp.receipt_envelope(er)
   need(term==record[tag+'Terminal']and term['exit_code']==0,'terminal')
   need(private==(p/(tag+'.receipt.json')).read_bytes()and stdout==(p/(tag+'.stdout')).read_bytes()and stderr==(p/(tag+'.stderr')).read_bytes()==b'','exclusive semantic receipt + opaque diagnostics')
   need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'diagnostic declaration')
   if tag=='selftest':need(wp.strict_json(private.decode())==({'selfTestsPassed':93,'keyTestsPassed':22,'checkpointTestsPassed':44,'targetOperations':0} if kind=='dp' else {'selfTestsPassed':2071,'targetOperations':0}),'zeroIO selftest')
  for marker,key,filename in [('PRE_READY','preCensus','metadata-pre.txt'),('BEFORE_INVOKE_READY','beforeInvokeCensus','metadata-before-invoke.txt'),('POST_READY','postCensus','metadata-post.txt')]:need(wp.parse_metadata((p/filename).read_text(),marker)==record[key],'cached census')
  # Exact recorded root requests and every generated artifact; no real adapter object/import.
  calls=record['calls']
  for call in calls:call_check(call)
  class Mock:
   def __init__(self):self.position=0
   def root(self,command,replay_record,path):
    need(self.position<len(calls),'no extra command');call=calls[self.position];self.position+=1;need(command==call['command'],'exact generated command');replay_record['calls'].append(copy.deepcopy(call));wp.save(path,replay_record);return call['response']['commands'][0]['stdout']
  mock=Mock();wp.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].split('-')[-1]))
  with tempfile.TemporaryDirectory(prefix='mock-',dir=HERE)as t:
   out=Path(t)/'capture';rr=wp.execute(out,ready,readyraw,manifests[kind],payloads[kind],mock,parser)
   need(mock.position==len(calls)and rr==result,'exact wrapper result')
   need({x.name for x in out.iterdir()}=={x.name for x in p.iterdir()},'exact output files')
   for f in out.iterdir():need(f.read_bytes()==(p/f.name).read_bytes(),'every output byte exact '+f.name)
  need(record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','exact cleanup')
  for key,value in [('transport_exit',1),('host_timeout',True),('command_bytes',0)]:
   bad=copy.deepcopy(calls[0]);bad[key]=value;reject(lambda:call_check(bad))
  for bad in (er[:-1],er+'extra','[GC_INFO]\n'+er):reject(lambda:wp.receipt_envelope(bad))
  run={'manifestSha256':result['manifestSha256'],'readinessSha256':result['readinessSha256'],'transportAccepted':True,'cleanup':'STAGE_ABSENT','headers':n['headersSent'],'bulkTransfers':n['bulkTransfers'],'nativeInvocations':1,'writes':0,'retries':0,'wrapperUiOperations':0,'strictInterpretation':q,'rootCommandReplay':{'calls':len(calls),'maximumCommandBytes':max(c['command_bytes']for c in calls),'everyCommandAndOutputByteExact':True},'hostFirstRootStart':calls[0]['started_utc'],'hostLastRootFinish':calls[-1]['finished_utc'],'diagnostics':{k:record[k]for k in ('selftestDiagnosticStdout','nativeDiagnosticStdout')},'cachedCensuses':{k:record[k]for k in ('preCensus','beforeInvokeCensus','postCensus')}}
  if kind=='dp':
   need(n['cleanCyclesCompleted']==n['cyclesStarted']==80 and n['headersSent']==640 and n['bulkTransfers']==1280 and not n['onsetObserved']and n['terminalReason']=='TimeLimit','80 clean control')
   rows=checkpoint_rows(rawmap['score-checkpoints.bin'],n['startUs'],q['scoreCheckpoints']['rows']);need(all(x['startAlternateThreshold']==x['endAlternateThreshold']==40 for x in rows),'unchanged sampled40');need(max(x['a0U32']for x in rows)==24,'max24')
   run.update({'checkpointRows':rows,'a0Maximum':24,'nonzeroA0Rows':[x for x in rows if x['a0U32']],'retained':retained(n),'intervention':n['intervention'],'timing':{k:n[k]for k in ('startUs','deadlineUs','endUs','overshootUs')},'sampledAbove40':sum(x['a0Low16']>40 for x in rows)})
   for offset in (0,1,2,4,6,10,20,24,28,32):
    bad=copy.deepcopy(n);cp=bad['scoreCheckpoints'];raw=bytearray(base64.b64decode(cp['rawBase64']));raw[offset]^=0x80;cp['rawBase64']=base64.b64encode(raw).decode();cp['sha256']=sha(raw)
    reject(lambda:parser.parse_native(json.dumps(bad)))
   for key,value in [('count',79),('recordBytes',32)]:
    bad=copy.deepcopy(n);bad['scoreCheckpoints'][key]=value;reject(lambda:parser.parse_native(json.dumps(bad)))
   bad=copy.deepcopy(n);cp=bad['scoreCheckpoints'];raw=base64.b64decode(cp['rawBase64'])[:-1];cp['rawBase64']=base64.b64encode(raw).decode();cp['sha256']=sha(raw);reject(lambda:parser.parse_native(json.dumps(bad)))
   bad=copy.deepcopy(n);bad['intervention']['calls'][0]['exitCode']=1;reject(lambda:parser.parse_native(json.dumps(bad)))
   bad=copy.deepcopy(n);bad['intervention']['calls'][0]['beforeUs']=n['endUs']+1;reject(lambda:parser.parse_native(json.dumps(bad)))
  else:
   need(n['headersSent']==16 and n['bulkTransfers']==32,'16exact pairs')
   need(rawmap['start-R.bin']==rawmap['end-R.bin']and fields(rawmap['start-R.bin'])['rt']==[0,0,1]and u16(rawmap['start-R.bin'],0xc4)==40,'clean40 R')
   need(rawmap['start-N.bin']==rawmap['end-N.bin']==bytes(36),'N allzero')
   need(rawmap['primary-lane-gate.bin']==bytes(136)and rawmap['secondary-lane-gate.bin']==bytes(68),'all tables zero')
   for idx in range(16):
    bad=copy.deepcopy(n);bad['windows'][idx]['address']+=4;reject(lambda:parser.parse_native(json.dumps(bad)))
   for idx in range(32):
    bad=copy.deepcopy(n);bad['steps'][idx]['after']='Unknown';reject(lambda:parser.parse_native(json.dumps(bad)))
   run.update({'profiles':{x:fields(rawmap[x+'.bin'])for x in ('start-R','end-R')},'fullReadSpanUs':n['steps'][-1]['afterUs']-n['steps'][0]['beforeUs'],'nativeSteps':n['steps']})
  runs[name]=run;natives[name]=n;rawmaps[name]=rawmap
 # Baseline is immutable accepted ED and parent predecessor references must all match.
 pred=j(EE/'predecessor-check.json')
 for f in pred['inputs']:need(sha(Path(f['path']).read_bytes())==f['sha256'],'parent predecessor pin')
 bn,bfiles,bq=mods['eb'].parse_native((ED/'table-read-01/native.receipt.json').read_text());br=j(ED/'table-read-01/result.json')
 need(pred['rtState']==[0,0,1]and pred['phase']=='ReadyForHeader'and pred['stageAbsent']and pred['released']and pred['closed'],'parent predecessor full lifecycle')
 need(pred['accepted']and pred['actualLimit']==40 and pred['headers']==16 and pred['bulks']==32 and br['accepted']and br['cleanup']=='STAGE_ABSENT','accepted ED predecessor')
 base={}
 for fn,raw,h in bfiles:need((ED/'table-read-01'/fn).read_bytes()==raw and sha(raw)==h,'baseline raw');base[fn]=raw
 need(readyids[0]==readyids[1]==j(ED/'table-read-01/readiness-decision.json')['identity']and readyids[0]['devnum']=='60','same saved USB60identity')
 comparisons={}
 for fn in ('primary-lane-gate.bin','secondary-lane-gate.bin','X.bin','Y.bin','RGB.bin','B.bin','Diff.bin','fixed-top-candidate.bin','fixed-bottom-candidate.bin'):
  a=base[fn];b=rawmaps['post-tables-01'][fn];comparisons[fn]={'baselineSha256':sha(a),'postSha256':sha(b),'byteIdentical':a==b,'changedByteOffsets':[i for i in range(len(a))if a[i]!=b[i]]}
 post=rawmaps['post-tables-01'];need(post['X.bin']==post['Y.bin']==post['RGB.bin']==bytes(96),'no current coordinates')
 fixed={}
 for side in ('top','bottom'):
  fixed[side]={}
  for label,rm in [('baseline',base),('post',post)]:
   raw=rm['fixed-'+side+'-candidate.bin'];v=int.from_bytes(raw[:102],'little');fixed[side][label]={str(lane):(v>>(12*(lane-568)))&4095 for lane in range(568,636)}
 # Check normal UI receipts separately. They are not optical/UI-consumption proof.
 prep={}
 for name in ('header-preparation-01','final-apps-preparation'):
  p=EE/name;r=j(p/'result.json');need(r['accepted']and r['vendor_operations']==r['threshold_writes']==r['key_retries']==0 and r['physical_picture_observed']is False,'accepted cached UI preparation')
  need(r['final']['cached_current_tab']=='d/apps.tab'and r['final']['screensaver_windows_present']is False,'cached Apps focus')
  prep[name]=r
 n=natives['onset-01'];postn=natives['post-tables-01'];lastread=runs['onset-01']['strictInterpretation']['observationWindow']['lastCompletedReadDataAfterUs'];poststart=postn['steps'][0]['beforeUs']
 need(poststart>n['endUs']>lastread,'later post read gap')
 rr=j(EE/'post-readiness-01/metadata-root.json');need(len(rr['calls'])==1,'one cached readiness snapshot');readycall=rr['calls'][0];call_check(readycall)
 need(readycall['finished_utc']<runs['post-tables-01']['hostFirstRootStart'],'cached readiness predatesactualEB')
 return {'schema':'ee-unchanged40-live-analysis-v1','checks':checks,'savedIdentity':readyids[0],'runs':runs,'baselineInterpretation':bq,'baselineComparison':comparisons,'fixed68LaneCandidates':fixed,'parentPredecessorChecked':True,'uiPreparations':prep,'timingSeparation':{'lastDPCompletedReadDataAfterUs':lastread,'dpOutcomeEndUs':n['endUs'],'postFirstHeaderBeforeUs':poststart,'lastDPReadToPostFirstHeaderUs':poststart-lastread,'dpOutcomeEndToPostFirstHeaderUs':poststart-n['endUs'],'postReadinessHostStarted':readycall['started_utc'],'postReadinessHostFinished':readycall['finished_utc'],'postActualRootStarted':runs['post-tables-01']['hostFirstRootStart'],'scope':'Common monotonic/source freshness premises; separate sequential captures with explicit host gap, no atomic or immediate post-transition snapshot.'},'negativeCasesRejected':negatives,'conclusion':{'warmControlFailedToReproduceSoftwareFault':True,'alternateLimitUnchanged40AtAllCheckpointsAndPost':True,'thresholdPreventionEstablished':False,'tableInterventionPerformed':False,'resetPerformed':False,'sampledAbove40Witness':False,'unsampledCrossingExcluded':False,'baselineAndPostLocalEligibilityOnly':True,'historicalGateExecutionProven':False,'actualComparatorCallProven':False,'recordEpochProven':False,'actualFixedABranchProven':False,'physicalPictureObserved':False,'rootCauseOrFixEstablished':False,'endpointQueueProof':False},'noRealRootAdapterImported':True,'hostOnly':True}

if __name__=='__main__':
 data=analyze();out=json.dumps(data,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--check']:need((HERE/'decoded.json').read_text()==out,'exact frozen decoded')
 elif not sys.argv[1:]:(HERE/'decoded.json').write_text(out)
 else:raise SystemExit('usage: analyze.py [--check]')
 print(json.dumps({'accepted':True,'checks':checks,'decodedSha256':sha(out.encode()),'negativeCases':negatives,'thresholdPreventionEstablished':False,'hostOnly':True}))
