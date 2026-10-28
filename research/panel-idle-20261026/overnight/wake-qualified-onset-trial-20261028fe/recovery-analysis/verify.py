#!/usr/bin/env python3
"""Bounded offline strict replay of FE fault, stock recovery, and validation. No device I/O."""
import base64,copy,hashlib,json,re,statistics,struct,sys,tempfile,types
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
FOLDERS={'eb':'rtp-lane-gate-capture-20261028eb'}
def pins():
 rows=j(D/'input-pins.json')['files']
 for f in rows:
  raw=(B/f['path']).read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'input '+f['path'])
 return len(rows)
def callcheck(c):
 a=c['response'];q=a['commands'];need(c['transport_exit']==0 and c['host_timeout']is False and c['transport_stderr']=={'data':'','encoding':'base64'},'root transport')
 need(a['authenticated']is True and a['uid']==a['euid']==0 and len(q)==1,'root identity')
 need(q[0]['command']==c['command'] and q[0]['exit_code']==0 and q[0]['timed_out']is False and q[0]['stderr']=='','completed root command')
def replay(role,path,kind,action=None,device=65):
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
 need(n['protocolPhase']=='ReadyForHeader'and n['accepted']and n['released']and n['closed']and n['device']==device,'native completed qualified device')
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

def save(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def root_calls(record):
 calls=record['calls'];need(type(calls)is list and 1<=len(calls)<=128,'bounded root calls')
 for c in calls:
  callcheck(c)
  need(type(c['command_bytes'])is int and c['command_bytes']==len(c['command'].encode())and c['command_bytes']<=8192,'root command exact bound')
  row=c['response']['commands'][0];need(all(type(v)is int for v in [c['transport_exit'],c['response']['uid'],c['response']['euid'],row['exit_code']]),'root integer statuses')
 return len(calls)
class Replay:
 def __init__(self,calls):self.calls=calls;self.position=0
 def root(self,command,record,path):
  need(self.position<len(self.calls),'no extra request');c=self.calls[self.position];self.position+=1;need(command==c['command'],'exact source-generated command');record['calls'].append(copy.deepcopy(c));save(path,record);return c['response']['commands'][0]['stdout']
def same_files(out,original):
 for file in out.iterdir():need(file.read_bytes()==(original/file.name).read_bytes(),'exact replay file '+file.name)
def lifecycle(text):
 patterns=[r'^\[([0-9.]+)\] usb 7-1:.*USB disconnect,.*device number 64>',r'^\[([0-9.]+)\] usb 7-1:.*new high-speed USB device number 65\b',r'^\[([0-9.]+)\] usb 7-1:.*New USB device found, idVendor=04e8, idProduct=2001, bcdDevice=\s*2\.50',r'^\[([0-9.]+)\] usb 7-1: USB Config =+> 1\s*$']
 found=[re.search(v,text,re.M)for v in patterns];need(all(v is not None for v in found),'positive disconnect/enumeration/ID/config')
 values=[v[1]for v in found];need([float(v)for v in values]==sorted(set(float(v)for v in values)),'strict lifecycle ordering')
 return dict(zip(['disconnect64','enumeration65','idAnnouncement','configuration1'],values))
def framed(text):
 m=re.fullmatch(r'BEFORE\n([0-9.]+ [0-9.]+)\nHELPER_EXIT\n0\nRECEIPT_BASE64\n([A-Za-z0-9+/=\n]*)NATIVE_STDERR_BASE64\n([A-Za-z0-9+/=\n]*)AFTER\n([0-9.]+ [0-9.]+)\n',text)
 need(m is not None,'exact successful MODE2 framing')
 return m

def stock_recovery():
 p=X/'recovery-01';result=j(p/'result.json');mode=j(p/'mode2/result.json');record=j(p/'mode2/root.json');root_calls(record)
 need(result['accepted']is True and type(result['mode2_invocations'])is int and result['mode2_invocations']==1 and result['threshold_writes']==result['automatic_retries']==0,'one stock recovery, no threshold-write/retry')
 helper=load(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py');stock=load(B/'managed-tcon-power-cycle-once/run-power-cycle-once.py');payload=helper.contract()
 receipt=(p/'mode2/receipt.txt').read_bytes();parsed=helper.parse_receipt(receipt.decode(),stock);text=(p/'mode2/framed.txt').read_text();m=framed(text)
 need(base64.b64decode(''.join(m[2].split()),validate=True)==receipt and base64.b64decode(''.join(m[3].split()),validate=True)==(p/'mode2/native.stderr').read_bytes()==b'','framed receipt/stderr bytes')
 need(mode==result['recovery']and mode['accepted']is True and mode['helper_exit']==0 and mode['request_count']==1 and mode['cleanup_confirmed']is True and mode['receipt_sha256']==sha(receipt)and parsed['classification']=='kernel_return_zero_only','original strict stock result')
 need(record['max_requests']==1 and record['automatic_retries']==0,'one stock request audit')
 r=Replay(record['calls']);helper.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_private_directory'].split('-')[-1]))
 original_load=helper.load
 def mocked_load(path,pin,name):
  need(sha(path.read_bytes())==pin,'helper dependency pin')
  if path==helper.ADAPTER:return r
  need(path==helper.STOCK,'only stock parser dependency');return stock
 helper.load=mocked_load
 with tempfile.TemporaryDirectory(prefix='stock-replay-',dir=D)as tmp:
  out=Path(tmp)/'mode2';observed=helper.execute(out,payload)
  need(observed==mode and r.position==len(record['calls']),'all exact stage/invoke/cleanup commands');same_files(out,p/'mode2')
 helper.load=original_load
 gates=load(B/'recovery-quickpath-20261027bv/recover.py');gdir=p/'recovery-gates';gr=j(gdir/'public-gate.json');root_calls(gr);g=Replay(gr['calls'])
 with tempfile.TemporaryDirectory(prefix='public-gate-',dir=D)as tmp:
  out=Path(tmp);gates.public_gate(out,adapter_module=g);need(g.position==1,'one public reject read');same_files(out,gdir)
 public=j(gdir/'public-gate-summary.json');need(public['accepted']and public['upgrade_working_status']==0 and public['power_state']=='lcdon'and public['screen_state']==1 and public['burn_in_protection_in_progress']==0,'public reject states')
 return {'accepted':True,'requestCount':1,'operation':41,'mode':2,'thresholdWrites':0,'classification':parsed['classification'],'nativeDeadlineSeconds':12,'physicalActionAcknowledged':False,'physicalStateObserved':False,'receiptSha256':sha(receipt),'rootRequestsReplayed':r.position,'allHelperFilesAndCommandsByteExact':True,'stageCleanupConfirmed':True,'initialRootAuditAcceptedFlag':record['accepted'],'auditFlagScope':'Frozen helper leaves its initial placeholder false; strict receipt and separate final result establish acceptance.','uptimeBefore':m[1],'uptimeAfter':m[4],'publicRejectSummary':public},helper,stock,text,receipt

def identity():
 p=X/'after-recovery-identity';proof=j(p/'instance-check.json');old=j(B/'limit-rechallenge-trial-20261028ex/after-recovery-identity/identity.json');new=j(p/'identity.json')
 need(proof['accepted']is True and proof['old_device']==64 and proof['new_device']==65 and proof['same_boot']is True and proof['same_descriptors']is True and proof['positive_disconnect_then_enumeration']is True and proof['endpointQueueProof']is False,'parent identity claims')
 for row in proof['inputs']:need(sha(Path(row['path']).read_bytes())==row['sha256'],'parent identity input')
 need(old['boot']==new['boot']and old['descriptorsSha256']==new['descriptorsSha256']and(old['devnum'],new['devnum'])==('64','65'),'same boot/descriptors, changed devnum')
 changed=sorted(k for k in old if old[k]!=new[k]);need(changed==proof['changedIdentityFields'],'actual changed identity fields')
 events=lifecycle((p/'metadata.txt').read_text());mr=j(p/'metadata-root.json');cr=j(p/'census-root.json');need(len(mr['calls'])==1 and len(cr['calls'])==2 and mr['calls'][0]==cr['calls'][0],'one metadata and one census request');root_calls(cr)
 capture=load(B/'volatile-limit-trial-20261028dk/capture-usb-identity.py');r=Replay(cr['calls']);origload=capture.load
 def mocked_load(path,pin,name):
  need(sha(path.read_bytes())==pin,'identity dependency pin')
  if path==B/'managed-ui-tab-launch/root-with-margin.py':return r
  return origload(path,pin,name)
 capture.load=mocked_load;argv=sys.argv[:]
 import contextlib,io
 with tempfile.TemporaryDirectory(prefix='identity-replay-',dir=D)as tmp:
  out=Path(tmp)/'identity';sys.argv=['capture-usb-identity.py','--output',str(out)]
  try:
   with contextlib.redirect_stdout(io.StringIO()):capture.main()
  finally:sys.argv=argv
  need(r.position==2,'exact two cached-only identity commands');same_files(out,p)
 capture.load=origload
 return {'oldDevice':64,'newDevice':65,'sameBoot':True,'sameDescriptors':True,'changedIdentityFields':changed,'positiveDisconnectThenEnumeration':True,'kernelTimestampSeconds':events,'sourceCommandsAndArtifactsReplayed':2,'endpointQueueProof':False,'continuousIdentityProven':False,'nativeOrHostClockMappingProven':False},new

def ui():
 nav=load(B/'ui-navigation-20261027br/navigate.py');rows=[]
 for directory,phase in [('recovery-01','before'),('recovery-01','final'),('final-ui','before')]:
  p=X/directory;record=j(p/(phase+'-snapshot.json'));root_calls(record);r=Replay(record['calls'])
  with tempfile.TemporaryDirectory(prefix='ui-replay-',dir=D)as tmp:
   out=Path(tmp);value=nav.command_snapshot(r,out,phase);same_files(out,p)
  need(value==j(p/(phase+'-summary.json'))and value['cached_current_tab']=='d/apps.tab'and value['csfs_window_present']and value['physical_picture_observed']is False,'cached Apps scope')
  rows.append({'directory':directory,'phase':phase,'summary':value})
 final=j(X/'final-ui/result.json');need(final['action']=='snapshot'and final['before']==final['after']==rows[-1]['summary']and final['controller_usb_power_settings_firmware_operations']==final['target_operations']==0 and final['physical_picture_observed']is False,'final cached result')
 need(rows[-1]['summary']['screensaver_windows_present']is True,'final saver present')
 prep=X/'recovery-apps-preparation-01';pr=j(prep/'result.json');need(pr['accepted']and pr['vendor_operations']==pr['threshold_writes']==pr['key_retries']==0,'ordinary prep no threshold/vendor retry')
 keys=[]
 for label in ['wake-once','live-right-once','header-up-1','header-up-2']:
  key=j(prep/('local-key-'+label+'.json'));root_calls(key);need(key['automatic_retry']is False and key['down_attempts']==key['up_attempts']==1,'one down/up per ordinary key');need(key['calls'][0]['response']['commands'][0]['stdout']==(prep/('local-key-'+label+'.txt')).read_text()=='LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n','ordinary key child statuses');keys.append({'label':label,'keysym':key['keysym']})
 return {'cachedSnapshots':rows,'finalAppsAndSaver':True,'ordinaryPreparationKeys':keys,'physicalPictureObserved':False,'keyUiConsumptionProven':False}

def ledger():
 phases=['fault-readiness','fault-capture','recovery-apps-prepare','stock-recovery','after-recovery-identity','validation-readiness','recovery-validation','final-ui'];values=[]
 for phase in phases:
  p=X/(phase+'-logs');intent=j(p/'intent.json');done=j(p/'completion.json');need(intent['automaticRetry']is False and type(done['exitCode'])is int and done['exitCode']==0 and (p/'stderr.txt').read_bytes()==b'','completed parent step '+phase)
  need(type(intent['startedHostMonotonicNs'])is type(done['endedHostMonotonicNs'])is int and intent['startedHostMonotonicNs']<=done['endedHostMonotonicNs'],'parent host ordering')
  args=intent['argv'];need(args[:2]==['python3','-B']and Path(args[2]).is_file(),'fixed helper source exists');need(not any('selective-endpoint-limit-writer' in arg for arg in args),'no FA threshold writer in recovery ledger')
  values.append({'phase':phase,'hostStartedUtc':intent['startedUtc'],'hostEndedUtc':done['endedUtc'],'startedHostMonotonicNs':intent['startedHostMonotonicNs'],'endedHostMonotonicNs':done['endedHostMonotonicNs'],'helperSha256':sha(Path(args[2]).read_bytes()),'stdoutSha256':sha((p/'stdout.txt').read_bytes())})
 need(all(a['endedHostMonotonicNs']<=b['startedHostMonotonicNs']for a,b in zip(values,values[1:])),'ordered serialized parent phases')
 return values

def run():
 count=pins();fault,fq,fr,fl,parser=replay('fault','fault-capture-01','eb',device=64);n,q,raw,vl,_=replay('validation','recovery-validation-01','eb',device=65)
 need(fl['headers']==vl['headers']==16 and fl['bulks']==vl['bulks']==32,'both16/32 read-only pairs')
 need(fq['rBytesEqual']and fr['start-R.bin']==fr['end-R.bin'],'full equal prior fault R')
 need(all(fq[k]['stop']==1 and fq[k]['fault']==4097 and fq[k]['ordinaryGate']==0 and fq[k]['alternateLimit']==40 for k in ['startR','endR']),'prior stable sampled fault40')
 need(q['rBytesEqual']and raw['start-R.bin']==raw['end-R.bin']and all(q[k]=={'stop':0,'fault':0,'ordinaryGate':1,'alternateLimit':40,'mode1RecordLatch':0}for k in ['startR','endR']),'full equal clean40 R/latch0')
 need(raw['start-N.bin']==raw['end-N.bin']==bytes(36)and all(q[k]['ordinals']==q[k]['sourceCounts']==[0]*6 for k in ['startN','endN']),'all zero validation N')
 need(n['writes']==fault['writes']==n['uiOperations']==fault['uiOperations']==0,'EB zero writes/UI')
 mode,helper,stock,frame,receipt=stock_recovery();ident,new=identity();uis=ui();steps=ledger();need(new==vl['identity']and fl['identity']['devnum']=='64','validation native binds new identity')
 for path,actual,device in [('fault-parent-check.json',fq,64),('validation-parent-check.json',q,65)]:
  parent=j(X/path);need(parent['accepted']and parent['interpretation']==actual and parent['rawFilesVerified']==16,'parent interpretation/count')
  folder='fault-capture-01'if device==64 else'recovery-validation-01';need(parent['nativeSha256']==sha((X/folder/'native.receipt.json').read_bytes())and parent['resultSha256']==sha((X/folder/'result.json').read_bytes()),'parent native/result hashes')
 summary={}
 for role,data in [('fault',fr),('validation',raw)]:
  summary[role]={}
  for name in ['X','Y','RGB','B','Diff']:
   b=data[name+'.bin'];vals=list(struct.unpack('<48H',b));summary[role][name]={'u16Nonzero':sum(v!=0 for v in vals),'byteNonzero':sum(v!=0 for v in b),'valuesU16':vals}
  for name in ['primary-lane-gate.bin','secondary-lane-gate.bin','fixed-top-candidate.bin','fixed-bottom-candidate.bin']:summary[role][name]={'byteNonzero':sum(v!=0 for v in data[name]),'bytes':len(data[name])}
 need([summary['validation'][k]['u16Nonzero']for k in ['X','Y','RGB','B','Diff']]==[48,48,26,22,0],'actual nonzero validation columns')
 negatives=0
 def reject(f):
  nonlocal negatives
  try:f()
  except(ValueError,KeyError,TypeError,StopIteration):negatives+=1;return
  raise ValueError('malformed input accepted')
 for bad in [frame.replace('HELPER_EXIT\n0\n','HELPER_EXIT\n1\n'),frame+'garbage']:reject(lambda:framed(bad))
 for old,newv in [('OPERATION_DECIMAL=41','OPERATION_DECIMAL=40'),('MODE_DECIMAL=2','MODE_DECIMAL=3'),('CLASSIFICATION=kernel_return_zero_only','CLASSIFICATION=unknown')]:reject(lambda:helper.parse_receipt(receipt.decode().replace(old,newv),stock))
 reject(lambda:lifecycle((X/'after-recovery-identity/metadata.txt').read_text().replace('device number 64>','device number 63>')))
 for field,value in [('accepted',False),('protocolPhase','Unknown'),('released',False),('closed',False),('bulkTransfers',31)]:
  z=copy.deepcopy(n);z[field]=value;reject(lambda:parser.parse_native(json.dumps(z)))
 pins()
 return {'schema':'fe-independent-recovery-analysis-v1','inputFilesVerified':count,'faultCapture':{'lifecycle':fl,'interpretation':fq},'recovery':mode,'identity':ident,'validation':{'lifecycle':vl,'interpretation':q,'fullRBytesEqual':True,'bothNAllBytesZero':True,'scanEnabledByte':raw['M.bin'][56],'bindingStageCount':len(n['bindingChecks'])},'columnAndWindowNonzeroCounts':summary,'ui':uis,'parentLedger':steps,'malformedRefusals':negatives,'claims':{'oneAcceptedStockMode2':True,'noThresholdWriteInRecordedRecoverySequence':True,'sameBootUsb64To65Observed':True,'finalSampledClean40':True,'universalRamClearingProven':False,'instructionReloadProven':False,'allDomainsColdBootProven':False,'mode2Reset200To40Proven':False,'feHad200ThresholdWrite':False,'actualComparatorCallOrHistoricalReferenceEpochProven':False,'physicalPictureObserved':False,'permanentFixOrRootCauseProven':False},'targetOperations':0,'rootCalls':0,'networkOperations':0,'checksPassed':checks}
if __name__=='__main__':
 value=run();raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 if sys.argv[1:]==['--write']:(D/'decoded.json').write_bytes(raw)
 else:need((D/'decoded.json').read_bytes()==raw,'exact decoded replay')
 print(json.dumps({'accepted':True,'checksPassed':checks,'inputFilesVerified':value['inputFilesVerified'],'malformedRefusals':value['malformedRefusals'],'decodedSha256':sha(raw),'targetOperations':0,'rootCalls':0,'networkOperations':0}))
