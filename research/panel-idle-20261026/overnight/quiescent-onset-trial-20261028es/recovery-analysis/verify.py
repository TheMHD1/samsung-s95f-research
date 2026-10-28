#!/usr/bin/env python3
"""Host-only independent ES recovery verification; no adapter or target calls."""
import base64,copy,hashlib,json,re,struct,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;S=D.parent;B=S.parent;T=S/'trial-01';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,s):
 global checks
 checks+=1
 if not ok:raise ValueError(s)
def j(p):return json.loads(p.read_bytes())
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def pins():
 rows=j(D/'input-pins.json')['files']
 for r in rows:
  raw=(B/r['path']).read_bytes();need(len(raw)==r['bytes']and sha(raw)==r['sha256'],'input '+r['path'])
 return len(rows)
def root_calls(record):
 for c in record['calls']:
  n=c['response'];cmd=n['commands']
  need(c['host_timeout']is False and c['transport_exit']==0 and c['transport_stderr']=={'data':'','encoding':'base64'},'root transport completed')
  need(n['authenticated']is True and n['uid']==n['euid']==0 and len(cmd)==1,'root identity')
  need(cmd[0]['command']==c['command']and cmd[0]['exit_code']==0 and cmd[0]['timed_out']is False and cmd[0]['stderr']=='','root command completion')
 return len(record['calls'])
def lifecycle(text):
 old=re.search(r'^\[([0-9.]+)\] usb 7-1:.*USB disconnect,.*device number 62>',text,re.M)
 new=re.search(r'^\[([0-9.]+)\] usb 7-1:.*new high-speed USB device number 63\b',text,re.M)
 ids=re.search(r'^\[([0-9.]+)\] usb 7-1:.*New USB device found, idVendor=04e8, idProduct=2001, bcdDevice=\s*2\.50',text,re.M)
 cfg=re.search(r'^\[([0-9.]+)\] usb 7-1: USB Config =+> 1\s*$',text,re.M)
 need(all(x is not None for x in [old,new,ids,cfg]),'positive lifecycle fields')
 values=[float(x[1])for x in [old,new,ids,cfg]];need(values==sorted(values)and len(set(values))==4,'strict kernel lifecycle order')
 return {'oldDevice':62,'newDevice':63,'positiveDisconnectThenEnumeration':True,'samePort':True,'descriptorIdentityAnnounced':True,'kernelClockSeconds':dict(zip(['disconnect','newEnumeration','idAnnouncement','configuration1'],values)),'nativeClockMappingProven':False}
def run():
 count=pins();EB=B/'rtp-lane-gate-capture-20261028eb';p=load(EB/'parse-result.py');w=load(EB/'run-once.py');v=T/'recovery-validation'
 n,raws,q=p.parse_native((v/'native.receipt.json').read_text());r=j(v/'result.json');record=j(v/'record.json')
 need(q==j(v/'interpretation.json'),'saved interpretation exact')
 need(r['accepted']is True and r['cleanup']=='STAGE_ABSENT'and r['headersSent']==16 and r['bulkTransfers']==32 and r['nativeInvocations']==1 and r['retries']==0,'wrapper exact validation')
 need(r['manifestSha256']==sha((v/'reviewed-manifest.json').read_bytes())==sha((EB/'deployment-manifest.json').read_bytes()),'EB manifest')
 need(n['device']==63 and n['accepted']is True and n['protocolPhase']=='ReadyForHeader'and n['released']and n['closed'],'native exact63 boundary')
 inventory=[];data={}
 for name,b,digest in raws:
  need((v/name).read_bytes()==b and sha(b)==digest,'saved raw '+name);inventory.append({'name':name,'bytes':len(b),'sha256':digest});data[name]=b
 need(r['rawFiles']==inventory,'exact raw inventory')
 ready,readyraw=w.load_readiness(v/'readiness-decision.json',r['readinessSha256']);need(ready['identity']['devnum']=='63','readiness63')
 for e in ready['evidence']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'readiness evidence')
 for kind in ['selftest','native']:
  text=(v/(kind+'-envelope.txt')).read_text()
  if kind=='native':need(text.startswith('IMMEDIATE_READY\n'),'immediate identity');text=text.removeprefix('IMMEDIATE_READY\n')
  terminal,receipt,out,err=w.receipt_envelope(text);need(terminal['exit_code']==0 and err==b'','envelope exit')
  for suffix,b in [('receipt.json',receipt),('stdout',out),('stderr',err)]:need((v/(kind+'.'+suffix)).read_bytes()==b,'envelope bytes')
 calls=root_calls(record);need(record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','exact validation cleanup')
 for x in ['startR','endR']:need(q[x]=={'stop':0,'fault':0,'ordinaryGate':1,'alternateLimit':40,'mode1RecordLatch':0},'clean40 latch0')
 for x in ['startN','endN']:need(q[x]['ordinals']==[0,0,0,0,0,36]and q[x]['sourceCounts']==[0]*6,'N residual ordinal5 not allzero')
 recovery=j(T/'fault-recovery/result.json');mode=j(T/'fault-recovery/mode2/result.json');need(recovery['accepted']is True and recovery['mode2_invocations']==1 and recovery['threshold_writes']==recovery['automatic_retries']==0,'separate single recovery')
 need(recovery['final']['cached_current_tab']=='d/apps.tab'and recovery['physical_picture_observed']is False,'cached Apps only')
 helper=load(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py');stock=load(B/'managed-tcon-power-cycle-once/run-power-cycle-once.py');receipt=(T/'fault-recovery/mode2/receipt.txt').read_bytes();parsed=helper.parse_receipt(receipt.decode(),stock)
 need(mode['accepted']is True and mode['request_count']==1 and mode['helper_exit']==0 and mode['cleanup_confirmed']is True and mode['receipt_sha256']==sha(receipt)and parsed['classification']=='kernel_return_zero_only','original strict MODE2 parser/result')
 framed=(T/'fault-recovery/mode2/framed.txt').read_text();enc=framed.split('RECEIPT_BASE64\n')[1].split('NATIVE_STDERR_BASE64\n')[0];need(base64.b64decode(''.join(enc.split()),validate=True)==receipt and '\nHELPER_EXIT\n0\n'in framed,'framed MODE2 receipt')
 err=framed.split('NATIVE_STDERR_BASE64\n')[1].split('AFTER\n')[0];need(base64.b64decode(''.join(err.split()),validate=True)==(T/'fault-recovery/mode2/native.stderr').read_bytes()==b'','MODE2 stderr empty')
 mr=j(T/'fault-recovery/mode2/root.json');modecalls=root_calls(mr);need('rmdir '+mr['remote_private_directory']in mr['calls'][-1]['command'],'MODE2 stage removal attempted/completed')
 refusal=j(T/'recovery-apps-preparation/result.json');before=j(T/'recovery-apps-preparation/before-summary.json');need(refusal['accepted']is False and refusal['vendor_operations']==refusal['threshold_writes']==refusal['key_retries']==0 and before['cached_current_tab']=='d/ug.tab@ForYou'and before['screensaver_windows_present']is True,'original preparation refusal retained')
 need(sorted(x.name for x in(T/'recovery-apps-preparation').iterdir())==['before-snapshot.json','before-snapshot.txt','before-summary.json','result.json'],'refusal has no key/reset artifacts')
 key_count=0
 for folder,names in [('recovery-navigation',['local-key-wake-once']),('normal-apps-navigation',['local-key-01-right','local-key-02-right'])]:
  for name in names:
   k=j(T/folder/(name+'.json'));need(k['automatic_retry']is False and k['down_attempts']==k['up_attempts']==1,'ordinary key no retry')
   need((T/folder/(name+'.txt')).read_text()=='LOCAL_KEY_DOWN_EXIT=0\nLOCAL_KEY_UP_EXIT=0\n','ordinary key down/up success');root_calls(k);key_count+=1
 nav=j(T/'normal-apps-navigation/result.json');need(nav['cached_target_match']is True and nav['page']=='d/apps.tab'and len(nav['normal_key_steps'])==2 and nav['retries']==0 and nav['controller_usb_power_settings_firmware_operations']==0,'normal ForYou→Live→Apps navigation')
 need([x['summary']['cached_current_tab']for x in nav['normal_key_steps']]==['d/ug.tab@Live','d/apps.tab'],'intermediate cached tabs')
 public=j(T/'fault-recovery/recovery-gates/public-gate-summary.json');need(public['accepted']is True and public['upgrade_working_status']==public['burn_in_protection_in_progress']==0 and public['power_state']=='lcdon'and public['screen_state']==1,'public rejection gates passed')
 proof=j(T/'after-recovery-identity/instance-check.json');need(proof['accepted']is True and proof['old_device']==62 and proof['new_device']==63 and proof['same_boot']is True and proof['same_descriptors']is True and proof['positive_disconnect_then_enumeration']is True and proof['endpointQueueProof']is False,'identity proof')
 for e in proof['inputs']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'identity proof input')
 old=j(Path(proof['inputs'][0]['path']));new=j(T/'after-recovery-identity/identity.json');need(old['boot']==new['boot']and old['descriptorsSha256']==new['descriptorsSha256']and(old['devnum'],new['devnum'])==('62','63'),'actual old/new identity')
 life=lifecycle((T/'after-recovery-identity/metadata.txt').read_text());negative=0
 for text in [(T/'after-recovery-identity/metadata.txt').read_text().replace('device number 62>','device number 61>'),(T/'after-recovery-identity/metadata.txt').read_text().replace('device number 63 using','device number 64 using'),(T/'after-recovery-identity/metadata.txt').read_text().replace('idProduct=2001','idProduct=2002')]:
  try:lifecycle(text)
  except ValueError:negative+=1
  else:raise ValueError('bad lifecycle accepted')
 for field,val in [('accepted',False),('protocolPhase','Unknown'),('closed',False),('released',False)]:
  z=copy.deepcopy(n);z[field]=val
  try:p.parse_native(json.dumps(z))
  except(ValueError,TypeError,KeyError):negative+=1
  else:raise ValueError('malformed native accepted')
 parent=j(S/'parent-final-checkpoint.json')
 for f in parent['inputs']:
  b=(B/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'parent final input')
 need(parent['validation']['startR']==q['startR']and parent['validation']['endR']==q['endR']and parent['validation']['startN']==q['startN']and parent['validation']['endN']==q['endN'],'parent decoded facts')
 need(parent['validation']['all_record_ram_zero_at_validation']is False and parent['validation']['universal_mode2_clearing_established']is False,'parent revised clearing limits')
 columns={key:sum(x[field]!=0 for x in q['candidateTuples'])for key,field in [('X','x'),('Y','y'),('RGB','rgb'),('B','b'),('Diff','absoluteDifferenceOrMode6Zero')]}
 pins()
 return {'schema':'es-independent-recovery-analysis-v1','acceptedRecoveryAndCleanValidationVerified':True,'inputFilesVerified':count,'refusedPreparation':{'accepted':False,'cachedForYouAndSaver':True,'keysIssued':0,'vendorOperations':0,'resetInvocations':0},'subsequentOrdinaryKeys':{'wake':1,'Right':2,'cachedPath':['ForYou','Live','Apps'],'physicalPictureObserved':False},'mode2':{'accepted':True,'invocations':1,'thresholdWrites':0,'automaticRetries':0,'strictReceiptSha256':sha(receipt),'classification':parsed['classification'],'cleanupConfirmed':True,'rootCallsVerified':modecalls,'rootAuditInitialAcceptedFlag':mr['accepted'],'rootAuditFlagMeaning':'Initial placeholder is never updated by frozen helper; separate final result and receipts provide accepted outcome.'},'usbIdentity':life,'validation':{'accepted':True,'nativeDevice':63,'headers':16,'bulks':32,'phase':'ReadyForHeader','released':True,'closed':True,'cleanup':'STAGE_ABSENT','rootCallsVerified':calls,'rawFiles':inventory,'startR':q['startR'],'endR':q['endR'],'startN':q['startN'],'endN':q['endN'],'rBytesEqual':q['rBytesEqual'],'nBytesEqual':q['nBytesEqual'],'sourceContext':q['sourceContext'],'columnNonzeroCounts':columns,'all68PrimaryZero':not any(data['primary-lane-gate.bin']),'all68SecondaryZero':not any(data['secondary-lane-gate.bin']),'bothFixedWindowsZero':not any(data['fixed-top-candidate.bin']+data['fixed-bottom-candidate.bin']),'fullBindingStagesValidated':3,'recordEpochProven':False,'allRecordRamZeroAtValidation':False,'UniversalClearingByMode2Proven':False},'parentDocsReviewed':{'findingsSha256':sha((S/'findings.md').read_bytes()),'checkpointSha256':sha((S/'parent-final-checkpoint.json').read_bytes()),'meaningfulUnresolvedDiscrepancies':[]},'malformedRefusals':negative,'physicalPictureObserved':False,'instructionReloadProven':False,'allDomainColdBootProven':False,'targetOperations':0,'rootCalls':0,'networkOperations':0,'checksPassed':checks}
if __name__=='__main__':
 value=run();raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 if '--write'in sys.argv:(D/'decoded.json').write_bytes(raw)
 else:need((D/'decoded.json').read_bytes()==raw,'byte-exact derived output')
 print(json.dumps({'accepted':True,'checksPassed':checks,'inputFilesVerified':value['inputFilesVerified'],'malformedRefusals':value['malformedRefusals'],'decodedSha256':sha(raw),'targetOperations':0,'rootCalls':0,'networkOperations':0}))
