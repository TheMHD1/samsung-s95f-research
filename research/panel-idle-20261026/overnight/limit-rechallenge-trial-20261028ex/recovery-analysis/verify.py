#!/usr/bin/env python3
"""Host-only EX recovery receipt/raw/source verification. No adapter calls."""
from pathlib import Path
import base64,copy,datetime,hashlib,json,re,struct,sys,types
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;T=D.parent;B=T.parent;checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,s):
 global checks
 checks+=1
 if not ok:raise ValueError(s)
def j(p):return json.loads(p.read_bytes())
def load(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def pins():
 rows=j(D/'input-pins.json')['files']
 for r in rows:
  b=(B/r['path']).read_bytes();need(len(b)==r['bytes']and sha(b)==r['sha256'],'input '+r['path'])
 return len(rows)
def root_calls(n):
 for c in n['calls']:
  x=c['response'];commands=x['commands'];need(c['command_bytes']==len(c['command'].encode())and 0<c['command_bytes']<=8192,'bounded exact command bytes');need(not c['host_timeout']and c['transport_exit']==0 and c['transport_stderr']=={'data':'','encoding':'base64'},'completed root transport')
  need(x['authenticated']is True and x['uid']==x['euid']==0 and len(commands)==1,'authenticated root identity')
  z=commands[0];need(z['command']==c['command']and z['exit_code']==0 and z['timed_out']is False and z['stderr']=='','root command completion')
 return len(n['calls'])
def lifecycle(text):
 patterns=[r'^\[([0-9.]+)\] usb 7-1:.*USB disconnect,.*device number 63>',r'^\[([0-9.]+)\] usb 7-1:.*new high-speed USB device number 64\b',r'^\[([0-9.]+)\] usb 7-1:.*New USB device found, idVendor=04e8, idProduct=2001, bcdDevice=\s*2\.50',r'^\[([0-9.]+)\] usb 7-1: USB Config =+> 1\s*$']
 found=[re.search(p,text,re.M)for p in patterns];need(all(x is not None for x in found),'positive USB lifecycle fields');v=[float(x[1])for x in found];need(v==sorted(v)and len(set(v))==4,'strict disconnect/enumeration/identity/configuration order');return dict(zip(['disconnect','newEnumeration','idAnnouncement','configuration1'],v))
def receipt_envelopes(w,folder):
 for tag in ['selftest','native']:
  text=(folder/(tag+'-envelope.txt')).read_text()
  flag='--receipt-self-test'if tag=='selftest'else'--execute';matches=[x for x in j(folder/'record.json')['calls']if '/usr/bin/dotnet 'in x['command']and flag in x['command']];need(len(matches)==1 and matches[0]['response']['commands'][0]['stdout']==text,'envelope exactly equals saved root stdout')
  if tag=='native':need(text.startswith('IMMEDIATE_READY\n'),'immediate identity receipt');text=text.removeprefix('IMMEDIATE_READY\n')
  terminal,receipt,out,err=w.receipt_envelope(text);need(terminal['exit_code']==0 and err==b'','successful exclusive receipt envelope')
  for suffix,b in [('receipt.json',receipt),('stdout',out),('stderr',err)]:need((folder/(tag+'.'+suffix)).read_bytes()==b,'saved envelope byte binding')
def run():
 count=pins();EB=B/'rtp-lane-gate-capture-20261028eb';p=load(EB/'parse-result.py','ex_recovery_eb');w=load(EB/'run-once.py','ex_recovery_wrapper');V=T/'recovery-validation';n,raws,q=p.parse_native((V/'native.receipt.json').read_text());r=j(V/'result.json');record=j(V/'record.json')
 need(q==j(V/'interpretation.json'),'saved EB interpretation exact');need(r['schema']=='eb-rtp-lane-gate-wrapper-result-v1'and r['accepted']is True and r['cleanup']=='STAGE_ABSENT'and r['nativeInvocations']==1 and r['retries']==0,'accepted single EB wrapper')
 need(r['headersSent']==n['headersSent']==16 and r['bulkTransfers']==n['bulkTransfers']==32,'exact16/32 counts');need(n['device']==64 and n['accepted']is True and n['protocolPhase']=='ReadyForHeader'and n['released']is True and n['closed']is True,'native64 clean boundary')
 need(r['manifestSha256']==sha((V/'reviewed-manifest.json').read_bytes())==sha((EB/'deployment-manifest.json').read_bytes()),'exact EB source manifest');need(w.manifest_bytes(w.build_manifest()[0])==(EB/'deployment-manifest.json').read_bytes(),'regenerated current EB source/payload manifest');inventory=[];data={}
 for name,b,digest in raws:need((V/name).read_bytes()==b and sha(b)==digest,'raw '+name);inventory.append({'name':name,'bytes':len(b),'sha256':digest});data[name]=b
 need(len(inventory)==16 and inventory==r['rawFiles'],'complete sixteen-file raw inventory')
 ready,_=w.load_readiness(V/'readiness-decision.json',r['readinessSha256']);need(ready['identity']['devnum']=='64','readiness binds64')
 for e in ready['evidence']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'readiness evidence')
 receipt_envelopes(w,V);ebcalls=root_calls(record);need(record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','EB exact cleanup')
 for name in ['startR','endR']:need(q[name]=={'stop':0,'fault':0,'ordinaryGate':1,'alternateLimit':40,'mode1RecordLatch':0},'clean40/latch0')
 for name in ['startN','endN']:need(q[name]['ordinals']==q[name]['sourceCounts']==[0]*6,'all six ordinals/counts zero at validation')
 need(data['M.bin'][56]==1,'captured scan enabled byte')
 parent=j(T/'recovery-validation-parent-check.json');need(parent['accepted']is True and parent['device']==64 and parent['native_sha256']==sha((V/'native.receipt.json').read_bytes())and parent['result_sha256']==sha((V/'result.json').read_bytes()),'parent validation hash binding')
 for key in ['startR','endR','startN','endN']:need(parent[key]==q[key],'parent decoded '+key)
 need(parent['context']==q['sourceContext']and parent['universal_c4_reset_or_ram_clearing_proven']is False,'parent context and claim limits')
 F=T/'fault-recovery-01';rec=j(F/'result.json');mode=j(F/'mode2/result.json');need(rec['accepted']is True and rec['mode2_invocations']==1 and rec['threshold_writes']==rec['automatic_retries']==0,'one separate MODE2/zero threshold writes')
 need(rec['final']['cached_current_tab']=='d/apps.tab'and rec['physical_picture_observed']is False,'cached Apps without optical claim')
 helper=load(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py','ex_stock_helper');stock=load(B/'managed-tcon-power-cycle-once/run-power-cycle-once.py','ex_stock_parser');payload=helper.contract();receipt=(F/'mode2/receipt.txt').read_bytes();parsed=helper.parse_receipt(receipt.decode(),stock)
 need(mode==rec['recovery']and mode['accepted']is True and mode['request_count']==1 and mode['helper_exit']==0 and mode['cleanup_confirmed']is True and mode['receipt_sha256']==sha(receipt)and parsed['classification']=='kernel_return_zero_only','original strict MODE2 parser/result')
 framed=(F/'mode2/framed.txt').read_text();fm=re.fullmatch(r'BEFORE\n([0-9.]+ [0-9.]+)\nHELPER_EXIT\n0\nRECEIPT_BASE64\n([A-Za-z0-9+/=\n]*)NATIVE_STDERR_BASE64\n([A-Za-z0-9+/=\n]*)AFTER\n([0-9.]+ [0-9.]+)\n',framed);need(fm is not None,'complete exact MODE2 framing')
 need(base64.b64decode(''.join(fm[2].split()),validate=True)==receipt,'framed receipt bytes');need(base64.b64decode(''.join(fm[3].split()),validate=True)==(F/'mode2/native.stderr').read_bytes()==b'','native stderr empty')
 mr=j(F/'mode2/root.json');mcalls=root_calls(mr);need(mr['max_requests']==1 and mr['automatic_retries']==0,'one helper/no retry')
 remote=mr['remote_private_directory'];modecalls=[x for x in mr['calls']if '/usr/bin/dotnet --clr-path'in x['command']];need(len(modecalls)==1 and modecalls[0]['response']['commands'][0]['stdout']==framed,'one helper submission/framed exact root stdout')
 need(mr['calls'][-1]['command'].endswith('cd /\nrmdir '+remote+'\ntest ! -e '+remote+'\n'),'exact stock cleanup command completed')
 expected=helper.render_stage(remote,payload);need([x['command']for x in mr['calls'][:len(expected)]]==expected,'exact original payload stage commands')
 public=j(F/'recovery-gates/public-gate-summary.json');need(public['accepted']is True and public['upgrade_working_status']==public['burn_in_protection_in_progress']==0 and public['power_state']=='lcdon'and public['screen_state']==1,'public rejection gates')
 intent=j(T/'recovery-logs/recovery-intent.json');need(intent['helper_sha256']==sha((B/'refresh-checkpoint-trial-20261028ei/recover-eb-fault.py').read_bytes()),'original EI helper invocation pin')
 # Restore happened before this MODE2. It is independently parsed here only to bind ordering/limit.
 FA=B/'selective-endpoint-limit-writer-20261028fa';fp=load(FA/'parse-result.py','ex_prior_restore');fw=load(FA/'run-once.py','ex_prior_restore_wrapper');A=T/'restore-01';an,araws,gc=fp.parse_native((A/'native.receipt.json').read_text());ar=j(A/'result.json');arecord=j(A/'record.json')
 need(gc==[]and an['action']=='restore200to40'and an['device']==63 and ar['accepted']is True and ar['cleanup']=='STAGE_ABSENT'and ar['headersSent']==7 and ar['bulkTransfers']==14,'prior accepted FA restore')
 need(ar['manifestSha256']==sha((FA/'deployment-manifest.json').read_bytes())==sha((A/'reviewed-manifest.json').read_bytes()),'FA source binding');need(fw.manifest_bytes(fw.build_manifest()[0])==(FA/'deployment-manifest.json').read_bytes(),'regenerated current FA source/payload manifest')
 need(ar['rawFiles']==[{'name':name,'bytes':len(b),'sha256':h}for name,b,h in araws],'restore six raw inventory')
 for name,b,h in araws:need((A/name).read_bytes()==b and sha(b)==h,'restore raw '+name)
 need(struct.unpack_from('<H',(A/'readback-R.bin').read_bytes(),0xc4)[0]==40,'40 established before reset');root_calls(arecord);receipt_envelopes(fw,A)
 restore_end=datetime.datetime.fromisoformat(arecord['calls'][-1]['finished_utc']);reset_begin=datetime.datetime.fromisoformat(mr['calls'][0]['started_utc']);need(restore_end<reset_begin,'host-record restore-before-reset order')
 proof=j(T/'after-recovery-identity/instance-check.json');need(proof['accepted']is True and(proof['old_device'],proof['new_device'])==(63,64)and proof['same_boot']is True and proof['same_descriptors']is True and proof['positive_disconnect_then_enumeration']is True and proof['endpointQueueProof']is False,'positive sameboot descriptor identity transition')
 for e in proof['inputs']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'identity proof input')
 old=j(Path(proof['inputs'][0]['path']));new=j(T/'after-recovery-identity/identity.json');need(old['boot']==new['boot']and old['descriptorsSha256']==new['descriptorsSha256']and(old['devnum'],new['devnum'])==('63','64'),'actual old/new identities')
 life=lifecycle((T/'after-recovery-identity/metadata.txt').read_text());keycalls=0
 prep=j(T/'recovery-apps-preparation-01/result.json');need(prep['accepted']is True and prep['vendor_operations']==prep['threshold_writes']==prep['reset_requests']==0,'ordinary preparation has no reset/vendor/write')
 K=T/'recovery-apps-preparation-01'
 for pth in [K/'local-key-wake-once',K/'normal-apps/local-key-01-right',K/'normal-apps/local-key-02-right']:
  kn=j(pth.with_suffix('.json'));need(kn['automatic_retry']is False and kn['down_attempts']==kn['up_attempts']==1,'fixed ordinary key counts');need(pth.with_suffix('.txt').read_text()=='LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n','ordinary key rc');root_calls(kn);keycalls+=1
 nav=j(K/'normal-apps/result.json');need(nav['cached_target_match']is True and nav['page']=='d/apps.tab'and[x['summary']['cached_current_tab']for x in nav['normal_key_steps']]==['d/ug.tab@Live','d/apps.tab'],'cached normal ForYou/Live/Apps path')
 negatives=0
 for bad in [framed.replace('HELPER_EXIT\n0\n','HELPER_EXIT\n1\n'),framed+'garbage']:
  need(re.fullmatch(r'BEFORE\n([0-9.]+ [0-9.]+)\nHELPER_EXIT\n0\nRECEIPT_BASE64\n([A-Za-z0-9+/=\n]*)NATIVE_STDERR_BASE64\n([A-Za-z0-9+/=\n]*)AFTER\n([0-9.]+ [0-9.]+)\n',bad)is None,'framing mutation rejected');negatives+=1
 for field,val in [('accepted',False),('protocolPhase','Unknown'),('released',False),('closed',False)]:
  z=copy.deepcopy(n);z[field]=val
  try:p.parse_native(json.dumps(z))
  except(ValueError,KeyError,TypeError):negatives+=1
  else:raise ValueError('mutated validation accepted')
 columns={name:sum(row[key]!=0 for row in q['candidateTuples'])for name,key in [('X','x'),('Y','y'),('RGB','rgb'),('B','b'),('Diff','absoluteDifferenceOrMode6Zero')]}
 final=j(T/'parent-final-checkpoint.json')
 for row in final['inputs']:
  rb=(B/row['path']).read_bytes();need(len(rb)==row['bytes']and sha(rb)==row['sha256'],'parent final input')
 need(final['validation']==parent and final['validation_nonzero_columns']==columns,'parent final validation facts')
 need(final['recovery']['accepted_MODE2_invocations']==1 and final['recovery']['recovery_threshold_writes']==0 and final['recovery']['MODE2_200to40_reset_proven']is False and final['recovery']['physical_light_observed']is False and(final['recovery']['old_usb'],final['recovery']['new_usb'])==(63,64),'parent recovery claims bounded')
 need(final['permanent_fix_established']is False and final['pure_threshold_causality_established']is False,'parent causal limits')
 pins()
 return {'schema':'ex-independent-recovery-analysis-v1','acceptedRecoveryAndCleanValidationVerified':True,'inputFilesVerified':count,'priorRestore':{'action':'restore200to40','accepted':True,'headers':7,'bulks':14,'actualReadback40BeforeMODE2':True,'hostReceiptOrderingVerified':True},'ordinaryPreparation':{'wakeWorkflows':1,'rightWorkflows':2,'cachedPath':['ForYou','Live','Apps'],'vendorOperations':0,'resetRequests':0,'physicalPictureObserved':False},'mode2':{'accepted':True,'invocations':1,'thresholdWrites':0,'classification':parsed['classification'],'receiptSha256':sha(receipt),'cleanupConfirmed':True,'rootCallsVerified':mcalls,'rootAuditInitialAcceptedFlag':mr['accepted'],'rootAuditFlagMeaning':'Frozen helper never updates initial placeholder; separate final result/strict receipts establish acceptance'},'identity':{'oldDevice':63,'newDevice':64,'sameBoot':True,'sameDescriptors':True,'positiveDisconnectThenEnumeration':True,'kernelClockSeconds':life,'nativeClockMappingProven':False},'validation':{'accepted':True,'device':64,'headers':16,'bulks':32,'phase':'ReadyForHeader','released':True,'closed':True,'cleanup':'STAGE_ABSENT','rootCallsVerified':ebcalls,'rawFiles':inventory,'readBrackets':q['readBrackets'],'startR':q['startR'],'endR':q['endR'],'startN':q['startN'],'endN':q['endN'],'sourceContext':q['sourceContext'],'scanEnabledU8':data['M.bin'][56],'rBytesEqual':q['rBytesEqual'],'nBytesEqual':q['nBytesEqual'],'columnNonzeroCounts':columns,'all68PrimaryZero':not any(data['primary-lane-gate.bin']),'all68SecondaryZero':not any(data['secondary-lane-gate.bin']),'bothFixedWindowsZero':not any(data['fixed-top-candidate.bin']+data['fixed-bottom-candidate.bin']),'fullBindingStagesValidated':3,'recordEpochProven':False},'parentDocsReviewed':{'findingsSha256':sha((T/'findings.md').read_bytes()),'checkpointSha256':sha((T/'parent-final-checkpoint.json').read_bytes()),'scope':'Recovery/validation and bounded inference claims only; earlier raised/control replay remains separate','meaningfulRecoveryDiscrepancies':[]},'malformedRefusals':negatives,'reset200to40InferenceEstablished':False,'universalRamClearingProven':False,'instructionReloadProven':False,'allDomainColdBootProven':False,'physicalPictureObserved':False,'targetOperations':0,'rootCalls':0,'networkOperations':0,'checksPassed':checks}
if __name__=='__main__':
 out=run();raw=(json.dumps(out,indent=2,sort_keys=True)+'\n').encode()
 if '--write'in sys.argv:(D/'decoded.json').write_bytes(raw)
 else:need((D/'decoded.json').read_bytes()==raw,'exact reproducible decoded output')
 print(json.dumps({'schema':'ex-recovery-validation-v1','accepted':True,'checksPassed':checks,'inputFilesVerified':out['inputFilesVerified'],'malformedRefusals':out['malformedRefusals'],'decodedSha256':sha(raw),'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
