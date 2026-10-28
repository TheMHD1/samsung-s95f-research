#!/usr/bin/env python3
"""Independent strict EL host replay. No root transport, target or network binding."""
import base64,copy,hashlib,importlib.util,json,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;EL=H.parent;B=EL.parent;ROOT=B.parent
checks=0;negatives=0
EB='rtp-lane-gate-capture-20261028eb';EH='rtp-refresh-checkpoints-20261028eh'
PINS={EB:{'inventory':'271061f8c60ee75f219b56217ac6dfcf3aa13616d67c3d4f54e46f655c13bdec','wrapper':'886bdc05bb8eb5a255443f95a964f2bae947fc758b18ea0e4893f42c3e4ad9a8','parser':'e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523','manifest':'e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11'},EH:{'inventory':'38ae37ba3e64c516d0e9aa5d2e811d7c6d85e0164f6a155e3bb93ff0990991fd','wrapper':'4870a6a0c089a739e6bc8af4f3b9076dc73bc5cf21123a2a0b8305ef206dfc15','parser':'1de2a8f769f4a801b85f2dff74bb840221e0394db8ec7acb9cffdd7a763d5229','manifest':'d0059b32e4e3d99a398a3763934e8927cd2967126c6d1ad9e76d8bf069f3059e'}}
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_text())
def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)
def reject(fn):
 global negatives
 try:fn()
 except (ValueError,KeyError,TypeError):negatives+=1;need(True,'negative rejected');return
 raise ValueError('malformed clone accepted')
def module(path,name,pin):
 need(sha(path.read_bytes())==pin,'module pin '+name);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def blob(x):
 need(type(x)is dict and set(x)=={'encoding','data'}and x['encoding']=='base64','blob schema')
 b=base64.b64decode(x['data'],validate=True);need(base64.b64encode(b).decode()==x['data'],'canonical base64');return b
def call_check(c):
 need(c['command_bytes']==len(c['command'].encode())<=8192,'command size')
 need(c['transport_exit']==0 and c['host_timeout']is False and c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75,'transport status/deadlines')
 need(blob(c['transport_stderr'])==b'','transport stderr')
 raw=blob(c['transport_stdout']);need(len(raw)<=65536 and json.loads(raw)==c['response'],'exact transport response')
 r=c['response'];need(r['authenticated']is True and r['uid']==r['euid']==0 and r['model']=='QN77S95FAFXZC','root identity')
 need(type(r['commands'])is list and len(r['commands'])==1,'one command')
 row=r['commands'][0];need(row['command']==c['command']and row['exit_code']==0 and row['timed_out']is False and row['stderr']=='','root command/status')
 need(type(row['stdout'])is str and len(row['stdout'].encode())<=65536,'root stdout size');need(c['started_utc']<=c['finished_utc'],'host timestamp ordering')
 return row['stdout']
def half(b,o):return struct.unpack_from('<H',b,o)[0]
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def verify_capture(name,source,readydir):
 d=B/source;p=EL/name;pins=PINS[source]
 need(sha((d/'source-inventory.json').read_bytes())==pins['inventory'],'source inventory pin')
 inv=j(d/'source-inventory.json')
 for row in inv['files']:
  raw=(d/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'source file '+row['path'])
 wrapper=module(d/'run-once.py',name.replace('-','_')+'_wrapper',pins['wrapper']);parser=module(d/'parse-result.py',name.replace('-','_')+'_parser',pins['parser'])
 manifest,payload=wrapper.build_manifest();mr=wrapper.manifest_bytes(manifest)
 need(sha(mr)==pins['manifest']and mr==(d/'deployment-manifest.json').read_bytes()==(p/'reviewed-manifest.json').read_bytes(),'regenerated frozen/captured manifest')
 result=j(p/'result.json');record=j(p/'record.json');ready,rr=wrapper.load_readiness(EL/readydir/'readiness.json',result['readinessSha256'])
 need(rr==(p/'readiness-decision.json').read_bytes(),'saved readiness exact')
 for ref in ready['evidence']:need(sha(Path(ref['path']).read_bytes())==ref['sha256'],'readiness evidence pin')
 phasename={'baseline-01':'baseline-phase.md','onset-01':'onset-phase.md','post-tables-01':'post-phase.md'}[name];phase=(EL/phasename).read_bytes()
 need(sha(phase)==ready['closedWorldVendorOutLineage']['evidenceSha256']and phase.decode().strip()==ready['closedWorldVendorOutLineage']['statement'],'explicit phase premise bytes')
 meta=j(EL/readydir/'metadata-root.json');need(len(meta['calls'])==1,'one cached readiness request')
 row=meta['calls'][0];need(row['command']=='set -eu\n'+wrapper.metadata_body(ready['identity'],'EI_CURRENT_READY'),'cached-only metadata command')
 text=call_check(row);need(text==(EL/readydir/'metadata.txt').read_text(),'cached metadata stdout')
 need(wrapper.parse_metadata(text,'EI_CURRENT_READY')==j(EL/readydir/'census-summary.json'),'readiness census')
 parsed=parser.parse_native((p/'native.receipt.json').read_text())
 if source==EH:
  native,caps,raws,gc,interpret=parsed;need(gc==[],'no diagnostic JSON contamination')
 else:native,raws,interpret=parsed
 need(interpret==j(p/'interpretation.json'),'strict interpretation exact')
 need(result['accepted']is True and result['cleanup']=='STAGE_ABSENT'and result['manifestSha256']==pins['manifest'],'accepted wrapper exact manifest')
 need(record['native_invocations']==1 and record['target_operations']==native['headersSent']and record['no_retry']is True and record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','one native invocation known cleanup')
 for tag in ('selftest','native'):
  text=(p/(tag+'-envelope.txt')).read_text()
  if tag=='native':need(text.startswith('IMMEDIATE_READY\n'),'immediate native readiness');text=text[len('IMMEDIATE_READY\n'):]
  terminal,private,stdout,stderr=wrapper.receipt_envelope(text)
  need(terminal==record[tag+'Terminal']and terminal['exit_code']==0,'terminal')
  need(private==(p/(tag+'.receipt.json')).read_bytes()and stdout==(p/(tag+'.stdout')).read_bytes()and stderr==(p/(tag+'.stderr')).read_bytes()==b'','three separate receipt/diagnostic blobs')
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'GC diagnostic is nonsemantic')
  if tag=='selftest':need(wrapper.strict_json(private.decode())==({'selfTestsPassed':93,'keyTestsPassed':22,'checkpointTestsPassed':46,'targetOperations':0}if source==EH else{'selfTestsPassed':2071,'targetOperations':0}),'zeroIO selftest exact')
 for filename,raw,digest in raws:need(sha(raw)==digest and (p/filename).read_bytes()==raw,'every retained raw window/hash')
 need(record['retained_raw_files']==result['rawFiles']==[{'name':n,'bytes':len(b),'sha256':digest}for n,b,digest in raws],'raw file index exact')
 for label,key,filename in [('PRE_READY','preCensus','metadata-pre.txt'),('BEFORE_INVOKE_READY','beforeInvokeCensus','metadata-before-invoke.txt'),('POST_READY','postCensus','metadata-post.txt')]:need(wrapper.parse_metadata((p/filename).read_text(),label)==record[key],'cached census snapshots')
 calls=record['calls'];need(len(calls)==(39 if source==EH else 28),'request count')
 for row in calls:call_check(row)
 class Replay:
  def __init__(self):self.i=0
  def root(self,command,rec,path):
   need(self.i<len(calls),'no extra root request');row=calls[self.i];self.i+=1;need(command==row['command'],'exact generated root command')
   rec['calls'].append(copy.deepcopy(row));wrapper.save(path,rec);return row['response']['commands'][0]['stdout']
 replay=Replay();wrapper.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].split('-')[-1]))
 with tempfile.TemporaryDirectory(prefix='offline-replay-',dir=H)as tmp:
  out=Path(tmp)/'result';res=wrapper.execute(out,ready,rr,mr,payload,replay,parser)
  need(replay.i==len(calls)and res==result,'exact completed wrapper result')
  need({f.name for f in out.iterdir()}=={f.name for f in p.iterdir()},'replayed artifact names')
  for f in out.iterdir():need(f.read_bytes()==(p/f.name).read_bytes(),'every saved artifact byte exact')
 # Independent rejection cases work under -O and never touch original captures.
 for window in range(len(native.get('windows',[]))):
  for field,value in [('sha256','0'*64),('address',0),('bytes',1)]:
   bad=copy.deepcopy(native);bad['windows'][window][field]=value;reject(lambda:parser.parse_native(json.dumps(bad)))
 for i in range(len(native.get('steps',[]))):
  for key,value in [('count',-1),('after','Unknown')]:
   bad=copy.deepcopy(native);bad['steps'][i][key]=value;reject(lambda:parser.parse_native(json.dumps(bad)))
 for key in ('accepted','released','closed'):
  bad=copy.deepcopy(native);bad[key]=False;reject(lambda:parser.parse_native(json.dumps(bad)))
 for tag in ('selftest','native'):
  text=(p/(tag+'-envelope.txt')).read_text()
  if tag=='native':text=text[len('IMMEDIATE_READY\n'):]
  for wrong in (text[:-1],text+'extra','[GC_INFO]\n'+text):reject(lambda:wrapper.receipt_envelope(wrong))
 for row in calls:
  bad=copy.deepcopy(row);bad['command_bytes']+=1;reject(lambda:call_check(bad))
 return {'source':source,'sourceFilesVerified':len(inv['files']),'manifestSha256':pins['manifest'],'readinessSha256':result['readinessSha256'],'identitySha256':sha(json.dumps(ready['identity'],sort_keys=True).encode()),'device':int(ready['identity']['devnum']),'accepted':True,'headers':native['headersSent'],'bulks':native['bulkTransfers'],'cleanup':'STAGE_ABSENT','mockRequests':len(calls),'maximumCommandBytes':max(c['command_bytes']for c in calls),'allSavedArtifactsByteExact':True,'rawFiles':result['rawFiles'],'interpretation':interpret},native,{n:b for n,b,digest in raws},parser,ready

def eb_summary(d):
 r=d['start-R.bin'];m=d['M.bin'];c=d['C.bin'];cols={k:list(struct.unpack('<48H',d[k+'.bin']))for k in ('X','Y','RGB','B','Diff')}
 return {'rStartEndEqual':r==d['end-R.bin'],'rtState':[half(r,o)for o in (0,10,14)],'operatingMode':half(r,16),'limit':half(r,0xc4),'latched':half(r,0x90),'configuredDelayRoot240c':half(r,12),'aa':half(m,10),'ac':half(m,12),'trainerGate4a2':half(m,2),'trainerAggregate4a4':half(m,4),'selectorC7':c[7],'selectorMirror4c2':half(m,34),'referenceCounter4c4':half(m,36),'publicationMirror':half(m,42),'controlRoot2460':half(r,0x60),'controlRoot246e':half(r,0x6e),'nStartEndEqual':d['start-N.bin']==d['end-N.bin'],'n':list(struct.unpack('<6I6H',d['start-N.bin'])),'primary68':list(struct.unpack('<68H',d['primary-lane-gate.bin'])),'secondary68':list(d['secondary-lane-gate.bin']),'fixedTopZero':not any(d['fixed-top-candidate.bin']),'fixedBottomZero':not any(d['fixed-bottom-candidate.bin']),'columns':cols,'descriptor24Halfwords':list(struct.unpack('<24H',d['D.bin'])),'mHalfwordsAtChangedOffsets':{hex(o):half(m,o)for o in (0,18,20,48,50)}}

def analyze():
 for item in j(H/'input-provenance.json')['files']:
  b=(ROOT/item['path']).read_bytes();need(len(b)==item['bytes']and sha(b)==item['sha256'],'original input pin '+item['path'])
 baseline,bn,bd,bp,br=verify_capture('baseline-01',EB,'baseline-readiness-01')
 onset,en,ed,ep,er=verify_capture('onset-01',EH,'onset-readiness-01')
 post,pn,pd,pp,pr=verify_capture('post-tables-01',EB,'post-readiness-01')
 need(br['identity']==er['identity']==pr['identity']and br['identity']['devnum']=='61','same saved boot/USB61 identity')
 before=eb_summary(bd);after=eb_summary(pd)
 for snapshot in (before,after):
  need(snapshot['rtState']==[0,0,1]and snapshot['limit']==40 and snapshot['latched']==0 and snapshot['rStartEndEqual'],'clean40 exact boundaries')
  need(snapshot['n']==[0]*12 and snapshot['nStartEndEqual'],'N remains zero')
  need(snapshot['primary68']==[0]*68 and snapshot['secondary68']==[0]*68 and snapshot['fixedTopZero']and snapshot['fixedBottomZero'],'zero gates and fixed samples')
  need(all(snapshot['columns'][k]==[0]*48 for k in ('X','Y','RGB','Diff'))and any(snapshot['columns']['B']),'coordinate/diff clear with nonzero B')
 need(en['accepted']is True and en['terminalReason']=='TimeLimit'and en['cleanCyclesCompleted']==en['cyclesStarted']==60 and en['onsetObserved']is False and en['onsetMissed']is False,'completed clean EH window')
 need(en['protocolPhase']=='ReadyForHeader'and en['released']is True and en['closed']is True and en['writes']==en['retries']==0,'known EH phase cleanup0writes')
 # Independent 54-byte compact decoding, then compare each field with strict parser.
 packed=ed['score-checkpoints.bin'];need(len(packed)==54*60,'54B60 records')
 rows=[];parsed=onset['interpretation']['scoreCheckpoints']['rows']
 for i in range(60):
  b=packed[i*54:(i+1)*54];taps=struct.unpack_from('<6H2I',b,34);hb,ha=struct.unpack_from('<2I',b,24)
  row={'cycleIndex':i+1,'selectorC7':b[1],'startAlternateThreshold':half(b,2),'endAlternateThreshold':half(b,4),'a0U32':u32(b,6),'q0U16':half(b,10),'history0U16x4':list(struct.unpack_from('<4H',b,12)),'recordOrdinal0U32':u32(b,20),'hReadBracket':{'headerBeforeUs':en['startUs']+hb,'dataAfterUs':en['startUs']+ha},'publicationBoundMirror':half(b,32),'mCpu4a2U16':taps[0],'mCpu4a4U16':taps[1],'mCpu4c2U16':taps[2],'mCpu4c4U16':taps[3],'endRRoot2460U16':taps[4],'endRRoot246eU16':taps[5],'capturedDynamicAPointerU32':taps[6],'capturedDynamicBPointerU32':taps[7]}
  need(b[0]==0 and all(parsed[i][k]==v for k,v in row.items()),'independent compact row decode')
  need(row['startAlternateThreshold']==row['endAlternateThreshold']==40 and row['publicationBoundMirror']==200,'limit40 versus mirror200')
  for k in ('selectorC7','a0U32','q0U16','recordOrdinal0U32','mCpu4a2U16','mCpu4a4U16','mCpu4c2U16','mCpu4c4U16','endRRoot2460U16','endRRoot246eU16'):need(row[k]==0,'zero sampled tap '+k)
  need(row['history0U16x4']==[0]*4,'zero history');rows.append(row)
  bad=copy.deepcopy(en);raw=bytearray(packed);raw[i*54]=0x20;bad['scoreCheckpoints']['rawBase64']=base64.b64encode(raw).decode();bad['scoreCheckpoints']['sha256']=sha(raw);reject(lambda:ep.parse_native(json.dumps(bad)))
  bad=copy.deepcopy(en);raw=bytearray(packed);struct.pack_into('<I',raw,i*54+24,en['endUs']-en['startUs']+1);bad['scoreCheckpoints']['rawBase64']=base64.b64encode(raw).decode();bad['scoreCheckpoints']['sha256']=sha(raw);reject(lambda:ep.parse_native(json.dumps(bad)))
 for field,value in [('count',59),('recordBytes',34),('sha256','0'*64),('rawBase64','')]:
  bad=copy.deepcopy(en);bad['scoreCheckpoints'][field]=value;reject(lambda:ep.parse_native(json.dumps(bad)))
 for ci in range(2):
  for field,value in [('reaped',False),('started',False),('exitCode',1),('timedOut',True)]:
   bad=copy.deepcopy(en);bad['intervention']['calls'][ci][field]=value;reject(lambda:ep.parse_native(json.dumps(bad)))
 for cap in range(len(en['retained'])):
  for window in range(len(en['retained'][cap]['windows'])):
   bad=copy.deepcopy(en);bad['retained'][cap]['windows'][window]['sha256']='0'*64;reject(lambda:ep.parse_native(json.dumps(bad)))
 pointers=sorted({v for row in rows for v in (row['capturedDynamicAPointerU32'],row['capturedDynamicBPointerU32'])})
 need(len(pointers)==3 and [pointers[i+1]-pointers[i]for i in range(2)]==[0xb68]*2,'three captured pointer values/stride')
 key=en['intervention'];need(key['key']=='Left'and key['trigger']=='first-full-clean-cycle'and key['attempted']is True and key['completed']is True,'one intended wake Left')
 need([c['phase']for c in key['calls']]==['down','up']and all(c['started']is True and c['reaped']is True and c['exitCode']==0 and c['timedOut']is False and c['stdoutBytes']==c['stderrBytes']==0 for c in key['calls']),'bounded reaped down/up')
 trigger=next(cap for cap in en['retained']if cap['role']=='trigger-baseline');last=next(cap for cap in en['retained']if cap['role']=='last-clean')
 need(trigger['cycleIndex']==1 and last['cycleIndex']==60 and trigger['transfers'][-1]['afterUs']<=key['armedUs']<=key['calls'][0]['beforeUs'],'key only after full clean first cycle')
 admission=j(EL/'onset-admission.json')
 for ref in admission['inputs']:need(sha(Path(ref['path']).read_bytes())==ref['sha256'],'admission original pin')
 need(admission['accepted']is True and admission['headers']==480 and admission['bulks']==960 and admission['checkpoints']==60 and admission['maximumSampledA0']==0 and admission['lastRtTuple']==[0,0,1]and admission['lastCompletedDataAfterUs']==last['transfers'][-1]['afterUs']and admission['cleanup']=='STAGE_ABSENT','admission recomputed fields')
 # Six separately consumed coordinator slots: no resume or hidden target retry.
 ledger=[]
 for slot in ['eb-baseline','eh-readiness','eh','eh-admission','eb-post-readiness','eb-post']:
  intent=j(EL/'pair-ledger-01'/f'{slot}-intent.json');done=j(EL/'pair-ledger-01'/f'{slot}-completion.json')
  need(intent['stage']==slot and intent['resumeAllowed']is False and done['returncode']==0 and intent['hostIntentUnixSeconds']<=done['hostCompletedUnixSeconds'],'coordinator slot consumed/completed '+slot)
  need(not (EL/'pair-ledger-01'/f'{slot}.stderr').read_bytes(),'slot stderrempty '+slot)
  ledger.append({'stage':slot,'hostIntentUnixSeconds':intent['hostIntentUnixSeconds'],'hostCompletedUnixSeconds':done['hostCompletedUnixSeconds'],'resumeAllowed':False,'returncode':0,'argvSha256':sha(json.dumps(intent['argv']).encode())})
 need(all(ledger[i]['hostCompletedUnixSeconds']<=ledger[i+1]['hostIntentUnixSeconds']for i in range(len(ledger)-1)),'serialized slot host ordering')
 ui_before=j(EL/'ui-before-summary.json');need(ui_before==j(EL/'ui-before/before-summary.json'),'same initial UI summary');ui_after=j(EL/'ui-after/after-summary.json')
 need(all(u=={'screensaver_windows_present':True,'csfs_window_present':True,'cached_current_tab':'d/apps.tab','physical_picture_observed':False}for u in (ui_before,ui_after)),'cached Apps+saver before and later after')
 for directory,tag,summary in [('ui-before','before',ui_before),('ui-after','after',ui_after)]:
  obj=j(EL/directory/(tag+'-snapshot.json'));need(len(obj['calls'])==1,'one cached UI snapshot')
  row=obj['calls'][0];text=call_check(row);need(text==(EL/directory/(tag+'-snapshot.txt')).read_text(),'UI retained stdout exact')
  expected='set -eu\ntest \"$(cat /proc/sys/kernel/random/boot_id)\" = '+br['identity']['boot']+'\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\nvconftool get memory/eden/current_tab\nenlightenment_info -topvwins\ncat /proc/uptime\n'
  need(row['command']==expected,'cached UI getters only')
  need('memory/eden/current_tab, value = d/apps.tab (String)'in text and 'ScreenSaverContent.dll'in text and 'ScreenSaver.dll'in text and '/csfs.dll'in text,'cached UI summary derived from saved getter output')
 changed={name:{'equal':bd[name]==pd[name],'changedByteOffsets':[i for i in range(len(bd[name]))if bd[name][i]!=pd[name][i]]}for name in bd}
 timing={'baselineFirstHeaderBeforeUs':bn['steps'][0]['beforeUs'],'baselineLastDataAfterUs':bn['steps'][-1]['afterUs'],'ehStartUs':en['startUs'],'ehFirstHeaderBeforeUs':trigger['transfers'][0]['beforeUs'],'ehLastDataAfterUs':last['transfers'][-1]['afterUs'],'ehEndUs':en['endUs'],'postFirstHeaderBeforeUs':pn['steps'][0]['beforeUs'],'postLastDataAfterUs':pn['steps'][-1]['afterUs'],'baselineToEhReadGapUs':trigger['transfers'][0]['beforeUs']-bn['steps'][-1]['afterUs'],'ehToPostReadGapUs':pn['steps'][0]['beforeUs']-last['transfers'][-1]['afterUs'],'hFirstToLastSpanUs':rows[-1]['hReadBracket']['dataAfterUs']-rows[0]['hReadBracket']['headerBeforeUs'],'sameSavedNativeBootTimebase':True,'onsetTimestampProven':False}
 need(timing['baselineToEhReadGapUs']>0 and timing['ehToPostReadGapUs']>0,'positive actual native gaps')
 # Rehash selected instruction/literal ranges behind the refresh interpretation.
 asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(sha(asset)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','source selected package')
 eg=j(B/'reference-refresh-control-20261028eg/source-audit.json')
 need(sha((B/'reference-refresh-control-20261028eg/source-audit.json').read_bytes())=='be0481dcd3f122122132c8b64e33d32c961a433f800fb5d1df71e7ee6cc74ce3','EG source qualification pin')
 for row in eg['sourceRanges']+eg['anchors']:
  off=int(row['va'],16)+0x40200;need(sha(asset[off:off+row['bytes']])==row['sha256'],'selected refresh instruction/range anchor')
 for addr,value in eg['literals'].items():need(u32(asset,int(addr,16)+0x40200)==int(value,16),'selected refresh literal')
 gi=B/'reference-refresh-control-20261028eg/source-inventory.json'
 need(sha(gi.read_bytes())=='972fa87454ff935b42c1c5d3e1d380a2a64baa5893313809b7e7d8765696d8fe','frozen EG inventory')
 for row in j(gi)['files']:
  b=(gi.parent/row['name']).read_bytes();need(len(b)==row['bytes']and sha(b)==row['sha256'],'frozen EG file')
 need(not any(getattr(m,'__file__','')and Path(str(getattr(m,'__file__',''))).name=='root-with-margin.py'for m in sys.modules.values()),'real root adapter never imported')
 return {'schema':'el-independent-live-analysis-v1','checks':checks,'malformedCasesRejected':negatives,'captures':{'baseline':baseline,'eh':onset,'post':post},'baseline':before,'post':after,'checkpointRows':rows,'dynamicPointerValuesHex':[hex(v)for v in pointers],'dynamicPointerStrideBytes':0xb68,'checkpointChanges':{k:[i+1 for i in range(1,60)if rows[i][k]!=rows[i-1][k]]for k in rows[0]if k not in ('cycleIndex','hReadBracket')},'baselinePostChangedByteOffsets':changed,'key':key,'admissionVerified':True,'ledger':ledger,'timing':timing,'cachedUiBefore':ui_before,'cachedUiLaterAfter':ui_after,'source':{'eb':PINS[EB],'eh':PINS[EH],'egSourceAuditSha256':sha((B/'reference-refresh-control-20261028eg/source-audit.json').read_bytes()),'egSourceRangesRehashed':len(eg['sourceRanges']),'egInstructionAnchorsRehashed':len(eg['anchors']),'egLiteralsVerified':len(eg['literals']),'selectedAssetSha256':sha(asset),'image1FileOffsetFormula':'VA+0x40200'},'claims':{'validAppsToLiveExposure':False,'saverWakeConsumptionProven':False,'continuousSaverPresenceProven':False,'allComparatorCallsObserved':False,'referenceRefreshSequenceExcluded':False,'faultCrossingExcluded':False,'physicalLightObserved':False,'rootCauseOrFixProven':False,'atomicState':False,'endpointQueueProof':False},'targetCalls':0,'networkCalls':0}
if __name__=='__main__':
 value=analyze();raw=json.dumps(value,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--record']:
  with (H/'decoded.json').open('x')as f:f.write(raw)
 elif sys.argv[1:]==['--check']:need((H/'decoded.json').read_text()==raw,'exact frozen decoded artifact')
 else:raise SystemExit('usage: analyze.py --record|--check')
 print(json.dumps({'accepted':True,'checks':checks,'malformedCasesRejected':negatives,'decodedSha256':sha(raw.encode()),'targetCalls':0,'networkCalls':0},sort_keys=True))
