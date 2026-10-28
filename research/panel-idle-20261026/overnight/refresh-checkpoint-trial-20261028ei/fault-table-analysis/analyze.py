#!/usr/bin/env python3
"""Independent offline EI EB fault analysis; frozen wrapper + no-I/O exact replay."""
import base64,copy,hashlib,importlib.util,json,re,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EI=HERE.parent;B=EI.parent;D=B/'rtp-lane-gate-capture-20261028eb';P=EI/'fault-tables-01';W=B/'rtp-lane-gate-qualification-20261028ea';checks=0;negative_cases=0
MAN='e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11';READY='5225f523eae30988be7445770263bb70e99d1a5eaff1df57e9b8faf9dca70244'
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_text())
def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)
def module(path,name,pin):
 need(sha(path.read_bytes())==pin,'module pin '+name)
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def reject(fn):
 global negative_cases
 try:fn()
 except (ValueError,KeyError,TypeError):negative_cases+=1;need(True,'negative rejected');return
 raise ValueError('negative unexpectedly accepted')
def blob(x):
 need(type(x)is dict and set(x)=={'encoding','data'} and x['encoding']=='base64','transport blob schema')
 raw=base64.b64decode(x['data'],validate=True);need(base64.b64encode(raw).decode()==x['data'],'transport canonical base64');return raw

def call_check(c):
 need(c['command_bytes']==len(c['command'].encode())<=8192,'recorded command extent')
 need(c['transport_exit']==0 and c['host_timeout']is False and c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75,'recorded transport status/bounds')
 need(blob(c['transport_stderr'])==b'','transport empty stderr')
 transport=blob(c['transport_stdout']);need(len(transport)<=65536 and json.loads(transport)==c['response'],'transport JSON response identity')
 r=c['response'];need(r['authenticated']is True and r['uid']==r['euid']==0 and r['model']=='QN77S95FAFXZC','ordinary root response identity')
 need(type(r['commands'])is list and len(r['commands'])==1,'one exact root command')
 row=r['commands'][0];need(row['command']==c['command']and row['exit_code']==0 and row['timed_out']is False and row['stderr']=='','root command echo/status')
 need(type(row['stdout'])is str and len(row['stdout'].encode())<=65536,'command stdout extent')
 need(c['started_utc']<=c['finished_utc'],'host ordered receipt timestamps')
 return row['stdout']

def analyze():
 for f in j(HERE/'input-provenance.json')['files']:
  b=(B.parent/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'input pin '+f['path'])
 need(sha((D/'deployment-manifest.json').read_bytes())==MAN,'manifest known pin')
 need(sha((D/'source-inventory.json').read_bytes())=='271061f8c60ee75f219b56217ac6dfcf3aa13616d67c3d4f54e46f655c13bdec','frozen inventory pin')
 inv=j(D/'source-inventory.json');need(len(inv['files'])==30,'30 frozen sources/payloads')
 for f in inv['files']:
  b=(D/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'source inventory '+f['path'])
 wrapper=module(D/'run-once.py','ei_fault_offline_wrapper','886bdc05bb8eb5a255443f95a964f2bae947fc758b18ea0e4893f42c3e4ad9a8')
 parser=module(D/'parse-result.py','ei_fault_offline_parser','e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523')
 manifest,payload=wrapper.build_manifest();manifest_raw=wrapper.manifest_bytes(manifest)
 need(manifest_raw==(D/'deployment-manifest.json').read_bytes()==(P/'reviewed-manifest.json').read_bytes(),'exact regenerated/captured manifests')
 source_check={'sourceFilesMatched':len(inv['files']),'manifestSha256':sha(manifest_raw),'payloadNames':sorted(payload),'targetOperations':0}
 ready,readyraw=wrapper.load_readiness(EI/'fault-readiness-01/readiness.json',READY)
 need(readyraw==(P/'readiness-decision.json').read_bytes(),'same saved readiness bytes')
 for e in ready['evidence']:
  need(sha(Path(e['path']).read_bytes())==e['sha256'],'every readiness evidence reference '+e['path'])
 premise=(EI/'reconciled-fault-phase.md').read_bytes();need(sha(premise)==ready['closedWorldVendorOutLineage']['evidenceSha256']and premise.decode().strip()==ready['closedWorldVendorOutLineage']['statement'],'phase premise exact bytes')
 need(ready['identity']['devnum']=='60','USB60')
 metadata=j(EI/'fault-readiness-01/metadata-root.json');need(len(metadata['calls'])==1,'one cached readiness request')
 meta=metadata['calls'][0];need(meta['command']=='set -eu\n'+wrapper.metadata_body(ready['identity'],'EI_CURRENT_READY'),'exact cached-only readiness command')
 text=call_check(meta);need(text==(EI/'fault-readiness-01/metadata.txt').read_text(),'cached metadata saved stdout')
 census=wrapper.parse_metadata(text,'EI_CURRENT_READY');need(census==j(EI/'fault-readiness-01/census-summary.json'),'cached census exact')
 receipt=(P/'native.receipt.json').read_bytes();native,raws,interpret=parser.parse_native(receipt.decode())
 need(interpret==j(P/'interpretation.json'),'exact strict interpretation')
 record=j(P/'record.json');result=j(P/'result.json')
 need(result['accepted']is True and result['cleanup']=='STAGE_ABSENT' and result['manifestSha256']==MAN and result['readinessSha256']==READY,'accepted exact wrapper result')
 need(record['manifestSha256']==MAN and record['readinessSha256']==READY and record['native_invocations']==1 and record['target_operations']==16 and record['no_retry']is True,'record one production invocation')
 need(record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','record exact cleanup')
 for tag in ('selftest','native'):
  envelope=(P/(tag+'-envelope.txt')).read_text()
  if tag=='native':need(envelope.startswith('IMMEDIATE_READY\n'),'immediate native metadata');envelope=envelope[len('IMMEDIATE_READY\n'):]
  terminal,private,stdout,stderr=wrapper.receipt_envelope(envelope)
  need(terminal==record[tag+'Terminal']and terminal['exit_code']==0,'recorded terminal '+tag)
  need(private==(P/(tag+'.receipt.json')).read_bytes()and stdout==(P/(tag+'.stdout')).read_bytes()and stderr==(P/(tag+'.stderr')).read_bytes()==b'','three-blob saved extents '+tag)
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'diagnostics separate '+tag)
  if tag=='selftest':need(wrapper.strict_json(private.decode())=={'selfTestsPassed':2071,'targetOperations':0},'zero-IO2071 selftest')
 for filename,b,h in raws:need(sha(b)==h and (P/filename).read_bytes()==b,'sixteen saved raw payloads '+filename)
 need(record['retained_raw_files']==result['rawFiles']==[{'name':n,'bytes':len(b),'sha256':h}for n,b,h in raws],'exact saved raw file inventories')
 for label,key in [('PRE_READY','preCensus'),('BEFORE_INVOKE_READY','beforeInvokeCensus'),('POST_READY','postCensus')]:
  filename={'preCensus':'metadata-pre.txt','beforeInvokeCensus':'metadata-before-invoke.txt','postCensus':'metadata-post.txt'}[key]
  need(wrapper.parse_metadata((P/filename).read_text(),label)==record[key],'three cached census snapshots '+label)
 # Reproduce every generated command and every saved output with frozen wrapper + a no-I/O replay root.
 calls=record['calls'];need(len(calls)==28,'28 actual orchestration requests')
 for c in calls:call_check(c)
 class ReplayRoot:
  def __init__(self):self.position=0
  def root(self,command,replay_record,path):
   need(self.position<len(calls),'no extra root request')
   c=calls[self.position];self.position+=1;need(command==c['command'],'exact frozen-wrapper generated command')
   replay_record['calls'].append(copy.deepcopy(c));wrapper.save(path,replay_record);return c['response']['commands'][0]['stdout']
 replay=ReplayRoot();wrapper.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].split('-')[-1]))
 with tempfile.TemporaryDirectory(prefix='offline-replay-',dir=HERE)as tmp:
  out=Path(tmp)/'result';res=wrapper.execute(out,ready,readyraw,manifest_raw,payload,replay,parser)
  need(replay.position==28 and res==result,'exact completed wrapper replay result')
  need({f.name for f in out.iterdir()}=={f.name for f in P.iterdir()},'same replayed artifact names')
  for f in out.iterdir():need(f.read_bytes()==(P/f.name).read_bytes(),'byte-exact generated saved artifact '+f.name)
 # Recovery validation is a second independently accepted capture, not an EH promotion.
 q=EI/'recovery-validation-01';qr=j(q/'result.json');qrecord=j(q/'record.json')
 qready,qreadyraw=wrapper.load_readiness(EI/'validation-readiness-01/readiness.json',qr['readinessSha256'])
 need(qreadyraw==(q/'readiness-decision.json').read_bytes(),'recovery saved readiness exact')
 for e in qready['evidence']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'recovery readiness evidence')
 phase=(EI/'recovery-validation-phase.md').read_bytes()
 need(sha(phase)==qready['closedWorldVendorOutLineage']['evidenceSha256']and phase.decode().strip()==qready['closedWorldVendorOutLineage']['statement'],'recovery phase exact')
 need(qready['identity']['devnum']=='61'and qready['identity']['boot']==ready['identity']['boot'],'same boot new USB61')
 need((q/'reviewed-manifest.json').read_bytes()==manifest_raw,'recovery same pinned manifest')
 qnative,qraws,qi=parser.parse_native((q/'native.receipt.json').read_text())
 need(qi==j(q/'interpretation.json'),'recovery strict interpretation exact')
 need(qr['accepted']is True and qr['cleanup']=='STAGE_ABSENT'and qr['manifestSha256']==MAN and qr['headersSent']==16 and qr['bulkTransfers']==32,'recovery accepted16/32')
 need(qrecord['native_invocations']==1 and qrecord['target_operations']==16 and qrecord['no_retry']is True and qrecord['cleanup_required']is False and qrecord['cleanup_stdout']=='STAGE_ABSENT\n','recovery one invocation cleanup')
 for tag in ('selftest','native'):
  env=(q/(tag+'-envelope.txt')).read_text()
  if tag=='native':need(env.startswith('IMMEDIATE_READY\n'),'recovery immediate metadata');env=env[len('IMMEDIATE_READY\n'):]
  term,private,stdout,stderr=wrapper.receipt_envelope(env)
  need(term==qrecord[tag+'Terminal']and term['exit_code']==0,'recovery terminal '+tag)
  need(private==(q/(tag+'.receipt.json')).read_bytes()and stdout==(q/(tag+'.stdout')).read_bytes()and stderr==(q/(tag+'.stderr')).read_bytes()==b'','recovery separate exact blobs '+tag)
  need(qrecord[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'recovery GC diagnostic separation')
  if tag=='selftest':need(wrapper.strict_json(private.decode())=={'selfTestsPassed':2071,'targetOperations':0},'recovery zeroIO selftest')
 for name,b,h in qraws:need((q/name).read_bytes()==b and sha(b)==h,'recovery raw hash '+name)
 need(qr['rawFiles']==qrecord['retained_raw_files']==[{'name':n,'bytes':len(b),'sha256':h}for n,b,h in qraws],'recovery all16raw indices exact')
 for label,key,filename in [('PRE_READY','preCensus','metadata-pre.txt'),('BEFORE_INVOKE_READY','beforeInvokeCensus','metadata-before-invoke.txt'),('POST_READY','postCensus','metadata-post.txt')]:
  need(wrapper.parse_metadata((q/filename).read_text(),label)==qrecord[key],'recovery census '+label)
 qcalls=qrecord['calls'];need(len(qcalls)==28,'recovery28requests')
 for ccall in qcalls:call_check(ccall)
 class RecoveryReplayRoot:
  def __init__(self):self.position=0
  def root(self,command,rec,path):
   need(self.position<len(qcalls),'recovery no extra request');row=qcalls[self.position];self.position+=1
   need(command==row['command'],'recovery exact generated command');rec['calls'].append(copy.deepcopy(row));wrapper.save(path,rec);return row['response']['commands'][0]['stdout']
 qreplay=RecoveryReplayRoot();wrapper.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=qrecord['remote_stage'].split('-')[-1]))
 with tempfile.TemporaryDirectory(prefix='recovery-replay-',dir=HERE)as tmp:
  out=Path(tmp)/'result';rr=wrapper.execute(out,qready,qreadyraw,manifest_raw,payload,qreplay,parser)
  need(qreplay.position==28 and rr==qr,'recovery exact mock result')
  need({f.name for f in out.iterdir()}=={f.name for f in q.iterdir()},'recovery exact artifact names')
  for f in out.iterdir():need(f.read_bytes()==(q/f.name).read_bytes(),'recovery artifact byte exact '+f.name)
 qdata={n:b for n,b,h in qraws};u16=lambda b,o:struct.unpack_from('<H',b,o)[0]
 need(qdata['start-R.bin']==qdata['end-R.bin']and [u16(qdata['start-R.bin'],o)for o in (0,10,14,0xc4,0x90)]==[0,0,1,40,0],'recovery clean40 latch0 stableR')
 for name in ('start-N.bin','end-N.bin','primary-lane-gate.bin','secondary-lane-gate.bin','fixed-top-candidate.bin','fixed-bottom-candidate.bin','X.bin','Y.bin','RGB.bin','Diff.bin'):need(not any(qdata[name]),'recovery sampled zero '+name)
 need(any(qdata['B.bin']),'recovery B remains nonzero: partial clear caveat')
 recovery=j(EI/'fault-recovery-01/result.json');mode2=j(EI/'fault-recovery-01/mode2/result.json')
 need(recovery['accepted']is True and recovery['mode2_invocations']==1 and recovery['threshold_writes']==recovery['automatic_retries']==0,'one separate stockMODE2 no threshold/retry')
 need(mode2==recovery['recovery']and mode2['accepted']is True and mode2['cleanup_confirmed']is True and mode2['request_count']==1,'stock wrapper structured result')
 need(sha((EI/'fault-recovery-01/mode2/receipt.txt').read_bytes())==mode2['receipt_sha256'],'stock receipt hash')
 instance=j(EI/'after-recovery-identity/instance-check.json');validation=j(EI/'recovery-validation-check.json')
 for proof in (instance,validation):
  need(proof['accepted']is True,'parent proof accepted')
  for item in proof['inputs']:need(sha(Path(item['path']).read_bytes())==item['sha256'],'parent proof input exact')
 need(instance['sameBoot']is True and instance['oldDevice']==60 and instance['newDevice']==61 and instance['positiveOldDisconnectThenNewEnumeration']is True and instance['sameDescriptors']is True,'parent specific instance proof')
 oldidentity=j(Path(instance['inputs'][0]['path']));newidentity=j(EI/'after-recovery-identity/identity.json')
 need(newidentity==qready['identity']and oldidentity['boot']==newidentity['boot']and oldidentity['descriptorsSha256']==newidentity['descriptorsSha256'],'actual identity/descriptor equality')
 lifecycle=(EI/'after-recovery-identity/metadata.txt').read_text()
 disconnect=re.search(r'usb 7-1: .*USB disconnect,<[^\n]*device number 60>',lifecycle)
 enumeration=re.search(r'usb 7-1: .*new high-speed USB device number 61 using sdp-xhci',lifecycle)
 need(disconnect is not None and enumeration is not None and disconnect.start()<enumeration.start(),'actual SamsungSDU disconnect then enum lines')
 need(validation['rtState']==[0,0,1]and validation['actualLimit']==40 and validation['tablesAllZero']is True and validation['fixedSampleWindowsAllZero']is True and validation['stageAbsent']is True,'parent validation fields independently agree')
 recovery_summary={'accepted':True,'manifestSha256':MAN,'readinessSha256':qr['readinessSha256'],'headers':16,'bulks':32,'phase':'ReadyForHeader','bindingStagesVerified':3,'cleanup':'STAGE_ABSENT','exactMockCalls':28,'allSavedArtifactsByteExact':True,'maximumCommandBytes':max(c['command_bytes']for c in qcalls),'rawFiles':qr['rawFiles'],'readBrackets':qi['readBrackets'],'rtState':[0,0,1],'limit':40,'latched':0,'allSixOrdinalsAndCountsZero':True,'all68PrimaryAndSecondaryZero':True,'both104ByteFixedWindowsZero':True,'coordinateAndDifferenceArraysZero':True,'bArrayStillNonzero':True,'stockMode2Invocations':1,'oldUsbDevice':60,'newUsbDevice':61,'sameBootAndDescriptors':True,'positiveDisconnectThenEnumeration':True,'instructionReloadProven':False,'allRamResetProven':False,'physicalPictureObserved':False,'lifecycleClockMappedToNative':False,'parentValidationInputsVerified':len(validation['inputs'])}
 # Source proof: EA exact gate intervals and prior formatter/epoch checks.
 need(sha((W/'source-inventory.json').read_bytes())=='44fe321b0445c5ca41c7ac4a1b34590c75faa8713e49fd45d751d062ff957371','EA frozen inventory')
 for f in j(W/'source-inventory.json')['files']:
  b=(W/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'EA source '+f['path'])
 source=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
 need(sha(source)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package identity')
 need(sha(source[0x43b34:0x43c64])=='53411e0b9f2eb3e3ed2aa00b6b9da29beb159ae368b7408db948445a32b36e00','descriptor refresh/copy source3934..3a64')
 oldsource=j(B/'rtp-record-capture-20261028dm/live-fault-analysis/decoded-fault.json')['sourceProvenance']
 for row in oldsource['recordSourceRanges']:
  off=int(row['file_offset'],16);need(sha(source[off:off+row['length']])==row['sha256'],'formatter/comparator/partial-clear source '+row['label'])
 for row in j(W/'source-qualification.json')['sourceRanges']:
  off=int(row['fileOffset'],16);need(sha(source[off:off+row['bytes']])==row['sha256'],'gate source range')
 data={name:b for name,b,_ in raws};half=lambda b,o:struct.unpack_from('<H',b,o)[0]
 primary=struct.unpack('<68H',data['primary-lane-gate.bin']);secondary=list(data['secondary-lane-gate.bin']);m=data['M.bin'];c=data['C.bin'];r=data['start-R.bin']
 need(data['start-R.bin']==data['end-R.bin']and[half(r,o)for o in (0,10,14,0xc4,0x90)]==[1,0x1001,0,40,41],'stable fault40/latched41')
 need(data['start-N.bin']==data['end-N.bin']and struct.unpack('<6I6H',data['start-N.bin'])==(41,0,0,0,0,0,0,0,0,0,0,0),'ordinal41 current counts0')
 need(primary==(0,)*68 and secondary==[0]*68,'all68 sampled table entries zero')
 need((half(m,10),half(m,12),m[44],c[7],half(r,16))==(0,2,0,0,4),'actual current Apps-like source context')
 need(half(m,42)==40,'current publication mirror40')
 cols={name:list(struct.unpack('<48H',data[name+'.bin']))for name in ('X','Y','RGB','B','Diff')}
 need(cols['X'][:41]!=[0]*41 and all(cols['Y'][i]==2159 for i in range(41))and cols['RGB']==[0]*48,'coordinate-bearing retained entries')
 need(cols['X'][41:]==cols['Y'][41:]==cols['RGB'][41:]==[0]*7 and all(cols['Diff'][i]>0 for i in range(41,48)),'cleared-coordinate tail retains difference values')
 def fixed_values(b):
  need(len(b)==104,'fixed reference extent');bits=int.from_bytes(b[:102],'little')
  return {str(568+i):(bits>>(12*i))&4095 for i in range(68)}
 fixed={side:fixed_values(data['fixed-'+side+'-candidate.bin'])for side in ('top','bottom')}
 for side in fixed:
  need({k:fixed[side][k]for k in interpret['fixedReferenceCandidates'][side]}==interpret['fixedReferenceCandidates'][side],'independent full68 packed decode '+side)
 records=[];groups={}
 for i in range(48):
  row={'index':i,**{k.lower():v[i]for k,v in cols.items()},'validCurrentEpochProven':False}
  if i<41:
   b,diff=cols['B'][i],cols['Diff'][i];xs=cols['X'][i]
   possible=sorted({v for v in (b-diff,b+diff)if 0<=v<=4095})
   need(len(possible)==1 and possible[0]==b+diff,'conditional unique type1/12bit candidate')
   need(568<=xs<636 and possible[0]==fixed['bottom'][str(xs)]and possible[0]!=fixed['top'][str(xs)],'conditional bottom match, not top')
   row['conditionalType1A']={'premises':['same historical tuple/type1','12bit operands','selected formatter interpretation','matching lane/x-base epoch'],'candidates':possible,'matchesLaterBottom':True,'matchesLaterTop':False,'historicalFixedBranchProven':False}
   groups.setdefault(str(xs),[]).append({'index':i,'b':b,'difference':diff,'conditionalA':possible[0]})
  else:row['conditionalType1A']=None
  records.append(row)
 need(all(row['locallyAdmittedByCapturedTables']is True for row in interpret['laneGateSamples']),'all68 local permission only')
 # Compare original strict-parsed captures; never substitute a prior valid epoch.
 def comparison(rel,par):
  q=B/rel;pn,pr,pi=par.parse_native((q/'native.receipt.json').read_text());res=j(q/'result.json')
  need(res['accepted']is True and res['cleanup']=='STAGE_ABSENT','comparison capture accepted')
  for name,b,h in pr:need((q/name).read_bytes()==b and sha(b)==h,'comparison raw hash '+rel+'/'+name)
  need(res['rawFiles']==[{'name':name,'bytes':len(b),'sha256':h}for name,b,h in pr],'comparison exact raw index')
  raw={name:b for name,b,h in pr};oldcols={k:list(struct.unpack('<48H',raw[k+'.bin']))for k in cols}
  contrasts={k:{'bytesEqual':raw[k+'.bin']==data[k+'.bin'],'changedIndices':[i for i in range(48)if oldcols[k][i]!=cols[k][i]],'priorSha256':sha(raw[k+'.bin']),'currentSha256':sha(data[k+'.bin'])}for k in cols}
  f={side:fixed_values(raw['fixed-'+side+'-candidate.bin'])for side in ('top','bottom')}if 'fixed-top-candidate.bin'in raw else None
  oldr=raw['start-R.bin'];oldc=raw['C.bin']
  return {'capture':rel,'strictParserAccepted':True,'alternateLimit':half(oldr,0xc4),'selectorC7':oldc[7],'startN':pi['startN'],'endN':pi['endN'],'columns':contrasts,'priorColumns':oldcols,'fixed68':f,'readBrackets':pi['readBrackets']}
 dt=module(B/'rtp-fixed-reference-capture-20261028dt/parse-result.py','ei_prior_dt','85e6d0783dc0455d4002e6e0332e23eed15d7d8b21c5ece3b3443c5529428b47')
 dm=module(B/'rtp-record-capture-20261028dm/parse-result.py','ei_prior_dm','fa2401bf270583fd793d44150b5db70915504c72e39878a8dd9f24a9be6446ca')
 comparisons=[comparison('lane-gate-onset-20261028ee/post-tables-01',parser),comparison('volatile-limit-trial-20261028dk/reference-fault-01',dt),comparison('volatile-limit-trial-20261028dk/record-fault-01',dm)]
 need(comparisons[0]['priorColumns']['Diff'][41:]==cols['Diff'][41:],'stale-coordinate tail Diff byte values persist from EE')
 # Prior EH stays rejected. Check its actual boundary and stored H, not an onset time.
 eh=j(EI/'onset-01/native.receipt.json');er=j(EI/'onset-01/record.json');clean=j(EI/'onset-01-cleanup/result.json')
 need(eh['accepted']is False and eh['observationAccepted']is True and eh['terminalReason']=='AlreadyFaulted'and eh['onsetMissed']is True and eh['onsetObserved']is False,'EH refusal remains refusal')
 need(eh['headersSent']==8 and eh['bulkTransfers']==16 and eh['protocolPhase']=='ReadyForHeader'and eh['released']is True and eh['closed']is True,'earlier EH known pair boundary')
 need(eh['intervention']['attempted']is False and eh['intervention']['completed']is False and not any(c['started']for c in eh['intervention']['calls']),'no EH Left')
 need(clean['accepted']is True and clean['exactStageRemoved']is True and clean['originalWrapperRejectionPreserved']is True and clean['additionalVendorTransfers']==clean['writes']==clean['uiCalls']==clean['resets']==clean['retries']==0,'separate zero-vendor cleanup')
 transfers=[t for cap in eh['retained']for t in cap['transfers']];last_eh_in=max(t['afterUs']for t in transfers if t['direction']=='IN')
 post=next(c for c in eh['retained']if c['role']=='post-fault');hw=next(w for w in post['windows']if w['name']=='H');hb=base64.b64decode(hw['rawBase64'],validate=True)
 need(len(hb)==96 and sha(hb)==hw['sha256'],'earlier H extent/hash')
 score=struct.unpack_from('<I',hb,4)[0];need(score==42,'earlier latched H score42')
 hp=[t for t in post['transfers']if t['name'].startswith('H-')];need(len(hp)==2,'earlier H pair')
 first_eb=native['steps'][0]['beforeUs'];last_eb=native['steps'][-1]['afterUs'];need(first_eb>last_eh_in,'positive native-clock gap')
 need(ready['identity']==j(EI/'onset-01/readiness-decision.json')['identity'],'same saved boot/USB identity')
 # Malformed clones and transport envelopes never touch original data.
 for i in range(16):
  bad=copy.deepcopy(qnative);bad['windows'][i]['sha256']='0'*64;reject(lambda:parser.parse_native(json.dumps(bad)))
 for i in range(32):
  bad=copy.deepcopy(qnative);bad['steps'][i]['count']=-1;reject(lambda:parser.parse_native(json.dumps(bad)))
 for i in range(16):
  for key,value in [('address',0),('sha256','0'*64),('bytes',1)]:
   bad=copy.deepcopy(native);bad['windows'][i][key]=value;reject(lambda:parser.parse_native(json.dumps(bad)))
 for i in range(32):
  for key,value in [('count',-1),('beforeUs',-1),('after','Unknown')]:
   bad=copy.deepcopy(native);bad['steps'][i][key]=value;reject(lambda:parser.parse_native(json.dumps(bad)))
 for flag in ('packingQualified','laneGateContextQualified','accepted','released','closed'):
  bad=copy.deepcopy(native);bad[flag]=False;reject(lambda:parser.parse_native(json.dumps(bad)))
 for idx in range(3):
  bad=copy.deepcopy(native);bad['bindingChecks'][idx]['ownClaim']=not bad['bindingChecks'][idx]['ownClaim'];reject(lambda:parser.parse_native(json.dumps(bad)))
 for label,offset in [('M',64),('M',6),('M',8),('M',32),('C',0),('C',2),('C',4),('start-R',16)]:
  bad=copy.deepcopy(native);w=next(w for w in bad['windows']if w['name']==label);b=bytearray(base64.b64decode(w['base64']));b[offset]^=2 if label=='start-R'else 1;w['base64']=base64.b64encode(b).decode();w['sha256']=sha(b);reject(lambda:parser.parse_native(json.dumps(bad)))
 for text in (receipt.decode()+receipt.decode(),receipt.decode().replace('"schema":','"schema":"duplicate","schema":',1),'[GC_INFO]\n'+receipt.decode()):reject(lambda:parser.parse_native(text))
 envelope=(P/'native-envelope.txt').read_text()[len('IMMEDIATE_READY\n'):]
 for bad in (envelope[:-1],envelope+'extra','[GC_INFO]\n'+envelope):reject(lambda:wrapper.receipt_envelope(bad))
 for field,value in [('transport_exit',1),('host_timeout',True),('remote_timeout_seconds',44),('host_timeout_limit_seconds',74),('command_bytes',0)]:
  bad=copy.deepcopy(calls[0]);bad[field]=value;reject(lambda:call_check(bad))
 for key in ('accepted','interfaceUnbound','noHolders'):
  bad=copy.deepcopy(ready);bad[key]=False
  with tempfile.TemporaryDirectory(prefix='bad-ready-',dir=HERE)as tmp:
   path=Path(tmp)/'readiness.json';raw=json.dumps(bad).encode();path.write_bytes(raw);reject(lambda:wrapper.load_readiness(path,sha(raw)))
 # Do not hardcode zero tables as an acceptance condition for future truthful data.
 for label in ('primary-lane-gate','secondary-lane-gate'):
  bad=copy.deepcopy(native);w=next(w for w in bad['windows']if w['name']==label);b=bytearray(base64.b64decode(w['base64']));b[0]=1;w['base64']=base64.b64encode(b).decode();w['sha256']=sha(b)
  _,_,other=parser.parse_native(json.dumps(bad));need(other['laneGateSamples'][0]['locallyAdmittedByCapturedTables']is False,'honest table change decoded')
 need(not any(getattr(m,'__file__','')and str(getattr(m,'__file__','')).endswith('managed-ui-tab-launch/root-with-margin.py')for m in sys.modules.values()),'no real root adapter imported')
 return {'schema':'ei-independent-fault-table-analysis-v1','checks':checks,'manifestSha256':MAN,'readinessSha256':READY,'identitySha256':sha(json.dumps(ready['identity'],sort_keys=True).encode()),'interpretation':interpret,'independentColumns':cols,'records':records,'conditionalGroups':groups,'independentFixed68':fixed,'comparisons':comparisons,'recoveryValidation':recovery_summary,'tailDiffMatchesEarlierEe':True,'descriptorRawHalfwords':list(struct.unpack('<24H',data['D.bin'])),'descriptorConditionalMetadata':{'previousTailAtOffsets04To0b':list(struct.unpack_from('<4H',data['D.bin'],4)),'currentTailAtOffsets16To1d':list(struct.unpack_from('<4H',data['D.bin'],0x16)),'currentAt18':half(data['D.bin'],0x18),'savedAt1e':half(data['D.bin'],0x1e),'pendingByteAt2b':data['D.bin'][0x2b],'actualBHeaderOrFixedABranchProven':False,'sourceImage1Va':'0x3934..0x3a64','sourceFileOffset':'0x43b34','sourceBytes':304,'sourceSha256':'53411e0b9f2eb3e3ed2aa00b6b9da29beb159ae368b7408db948445a32b36e00'},'sourceProvenance':oldsource,'sourceCheck':source_check,'nativeSteps':native['steps'],'bindingStagesVerified':3,'exactMockRootReplay':{'calls':len(calls),'maximumCommandBytes':max(x['command_bytes']for x in calls),'allSavedArtifactsByteExact':True,'realRootImported':False},'transport':{'accepted':True,'headers':16,'bulks':32,'phase':'ReadyForHeader','released':True,'closed':True,'cleanup':'STAGE_ABSENT','writes':0,'uiCalls':0,'retries':0},'earlierEh':{'accepted':False,'terminal':'AlreadyFaulted','headers':8,'bulks':16,'leftAttempted':False,'separateCleanupAccepted':True,'postHScore42IsEarlierObservation':True,'postHBracketUs':[hp[0]['beforeUs'],hp[1]['afterUs']],'lastCompletedInUs':last_eh_in,'onsetObserved':False},'timing':{'firstEbHeaderBeforeUs':first_eb,'lastEbDataAfterUs':last_eb,'ebSpanUs':last_eb-first_eb,'gapAfterEhLastInUs':first_eb-last_eh_in,'gapAfterEhPostHUs':first_eb-hp[1]['afterUs'],'sameSavedBootAndNativeMonotonicTimebase':True,'exactOnsetOrPhysicalTimestampProven':False},'negativeCasesRejected':negative_cases,'claims':{'recordEpochProven':False,'currentPrefixValidityProven':False,'historicalSelectedABranchProven':False,'historicalGateExecutionProven':False,'actualComparatorCallProven':False,'physicalPictureObserved':False,'atomicSnapshot':False,'rootCauseOrPreventionEstablished':False,'endpointQueueProof':False},'lineageScope':'Pinned central predecessor/cleanup statement is an explicit premise, not continuous proof of all clients or reply queues.'}

if __name__=='__main__':
 value=analyze();raw=json.dumps(value,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--check']:need((HERE/'decoded.json').read_text()==raw,'exact frozen decoded artifact')
 elif sys.argv[1:]==['--record']:
  with (HERE/'decoded.json').open('x')as out:out.write(raw)
 else:raise SystemExit('usage: analyze.py --record|--check')
 print(json.dumps({'accepted':True,'checks':checks,'negativeCasesRejected':negative_cases,'decodedSha256':sha(raw.encode()),'targetCalls':0,'networkCalls':0},sort_keys=True))
