#!/usr/bin/env python3
"""Offline pinned replay of completed fixed-limit comparison; no device operations."""
import base64, hashlib, importlib.util, json, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE=Path(__file__).resolve().parent; BASE=HERE.parent.parent; DK=BASE/'volatile-limit-trial-20261028dk'
checks=0
PIN={
 'dv':('volatile-limit-dynamic-profile-20261028dv','ef6a62a10b2bba004c405e14ac75fc927b4e20803448732b2b111177d6e4aab0','9a1fd4db858212e06afdb18bb6de0a23bd4abd01cf74a41876e422cd26f93bb5'),
 'dp':('rtp-score-checkpoints-20261028dp','ba02517d7f8bb5cae6aa4257c426b7cc50780bfdfd5e0a73a7838e2386dff9ee','9b5e476a50e73439e11a6e5ed78bae0079a1d802c054212a8974e079f77d6b3a'),
 'dt':('rtp-fixed-reference-capture-20261028dt','ed1e1594f3dc23528c69894c21a19c214593a0ae12c0dd20ec5ceebc9fda4d80','85e6d0783dc0455d4002e6e0332e23eed15d7d8b21c5ece3b3443c5529428b47'),
 'dm':('rtp-record-capture-20261028dm','e62b2906734a2814f2165749eb8ab230d5dd8e8dfd37f257ce5962ea20850c53','fa2401bf270583fd793d44150b5db70915504c72e39878a8dd9f24a9be6446ca')}
TRIALS=[('dv-set-01','dv'),('dv-observation-01','dp'),('dv-restore-01','dv'),('dv-rechallenge-01','dp'),('dv-clean-reference-01','dt'),('dv-final-clean-01','dm')]
def need(ok,why):
 global checks
 checks+=1
 if not ok: raise ValueError(why)
def sha(b): return hashlib.sha256(b).hexdigest()
def j(p): return json.loads(p.read_text())
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def load(path,name,pin):
 need(sha(path.read_bytes())==pin,'module pin '+name)
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def model(b):
 return {'ordinaryUpper':u16(b,0x20),'alternateUpper':u16(b,0xbc),'base':u16(b,0x94),'referenceTemperature':u16(b,0x96),'temperature':u16(b,0x98),'echo':u16(b,0xac),'alternateLimit':u16(b,0xc4),'normalMode1Limit':u16(b,0x30),'mode1RecordLatch':u16(b,0x90),'rt':[u16(b,0),u16(b,0xa),u16(b,0xe)]}
def independent_checkpoint(raw,start,parserrows):
 need(len(raw)==80*34 and len(parserrows)==80,'80 x34B checkpoint extent')
 rows=[]
 for i in range(80):
  b=raw[i*34:(i+1)*34];packed,c7,s,e,a,q,*rest=struct.unpack('<BBHHIH4HIIIH',b)
  history=rest[:4];ordinal,h0,h1,mirror=rest[4:]
  p=parserrows[i]
  d={'cycleIndex':i+1,'startRtCode':packed>>4,'endRtCode':packed&15,'selectorC7':c7,'startAlternateThreshold':s,'endAlternateThreshold':e,'a0U32':a,'a0Low16':a&65535,'q0U16':q,'history0U16x4':history,'recordOrdinal0U32':ordinal,'hReadBracket':{'headerBeforeUs':start+h0,'dataAfterUs':start+h1},'publicationBoundMirror':mirror}
  need(packed==0 and c7 in (0,1) and h0<=h1,'clean paired checkpoint')
  for key in ('cycleIndex','selectorC7','startAlternateThreshold','endAlternateThreshold','a0U32','a0Low16','q0U16','history0U16x4','recordOrdinal0U32','hReadBracket','publicationBoundMirror'):need(d[key]==p[key],'independent checkpoint '+key)
  rows.append(d)
 return rows
def retained(n):
 out=[]
 for cap in n['retained']:
  data={};brackets={}
  for i,w in enumerate(cap['windows']):
   b=base64.b64decode(w['rawBase64'],validate=True);name=w['name'];t=cap['transfers'][2*i:2*i+2]
   need(sha(b)==w['sha256'],'retained source hash')
   brackets.setdefault(name,[]).append({'headerBeforeUs':t[0]['beforeUs'],'dataAfterUs':t[1]['afterUs']})
   if name=='R': data.setdefault('R',[]).append(model(b))
   if name=='H': data['H']={'a':list(struct.unpack_from('<6I',b,4)),'q':list(struct.unpack_from('<6H',b,28)),'history':[list(struct.unpack_from('<4H',b,40+8*k))for k in range(6)]}
   if name=='N': data['N']={'ordinals':list(struct.unpack_from('<6I',b)),'sourceCounts':list(struct.unpack_from('<6H',b,24))}
   if name=='C': data['C']={'geometry':list(struct.unpack_from('<3H',b)),'selectorC7':b[7]}
   if name=='M': data['M']={'modeAa':u16(b,10),'modeAc':u16(b,12),'currentRow':u16(b,20),'xBase':u16(b,32),'publicationBoundMirror':u16(b,42),'savedRow':u16(b,48),'scanByte':b[56],'BUpperMirror':u16(b,38)}
  out.append({'role':cap['role'],'cycleIndex':cap['cycleIndex'],'decoded':data,'brackets':brackets})
 return out

def analyze():
 for f in j(HERE/'input-pins.json')['files']:
  b=Path(f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'input pin '+f['path'])
 dupath=BASE/'volatile-limit-dynamic-profile-design-20261028du/profile_model.py'
 du=load(dupath,'du_frozen','7a1c2d9b9f5cc5d9136166b79be7ba16d639d18c7d92450b546db8476b3f937a')
 package=(BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
 need(sha(package)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected source package')
 source_ranges=j(BASE/'rtp-fixed-reference-capture-20261028dt/reviews/independent-validation.json')['sourceRangeEvidence']
 source_ranges=[*source_ranges,{'label':'mode predicate','file_offset':'0x42068','bytes':0x1d6,'sha256':sha(package[0x42068:0x4223e])}]
 for r in source_ranges:
  off=int(r['file_offset'],16);need(sha(package[off:off+r['bytes']])==r['sha256'],'selected source range '+r['label'])
 modules={};wrappers={}
 for kind,(dirname,manifestpin,parserpin) in PIN.items():
  p=BASE/dirname;raw=(p/'deployment-manifest.json').read_bytes();need(sha(raw)==manifestpin,'manifest '+kind);man=json.loads(raw)
  for section in ('nativeFiles','wrapperFiles'):
   for name,f in man.get(section,{}).items():
    b=(p/name).read_bytes();need(len(b)==f['bytes'] and sha(b)==f['sha256'],'manifest source/payload '+name)
  modules[kind]=load(p/'parse-result.py',kind+'_parser',parserpin)
  wp=man['wrapperFiles']['run-once.py']['sha256'];wrappers[kind]=load(p/'run-once.py',kind+'_wrapper',wp)
 allout={};identities=[];raws={};natives={}
 def replay(name,kind,main=True):
  p=DK/name;mod=modules[kind];nraw=(p/'native.receipt.json').read_bytes();parsed=mod.parse_native(nraw.decode())
  if kind=='dv': n,files,gc=parsed;q=None;need(gc==[],'exclusive DV no GC semantic')
  elif kind=='dp': n,_,files,gc,q=parsed;need(gc==[] and q['trialQualified']is True,'qualified exclusive DP')
  else:n,files,q=parsed
  result=j(p/'result.json');ready=j(p/'readiness-decision.json');record=j(p/'record.json')
  need(result['accepted']is True and result['cleanup']=='STAGE_ABSENT' and result['nativeInvocations']==1 and result['retries']==0,'wrapper lifecycle '+name)
  need(n['accepted']is True and n['protocolPhase']=='ReadyForHeader' and n['released']and n['closed'],'native lifecycle '+name)
  need((p/'reviewed-manifest.json').read_bytes()==(BASE/PIN[kind][0]/'deployment-manifest.json').read_bytes() and result['manifestSha256']==PIN[kind][1],'captured manifest '+name)
  need(sha((p/'readiness-decision.json').read_bytes())==result['readinessSha256'],'readiness digest '+name)
  for f in ready['evidence']:need(sha(Path(f['path']).read_bytes())==f['sha256'],'readiness referenced evidence '+f['path'])
  envelope=(p/'native-envelope.txt').read_text();need(envelope.startswith('IMMEDIATE_READY\n'),'immediate ready '+name)
  terminal,receipt,stdout,stderr=wrappers[kind].receipt_envelope(envelope[len('IMMEDIATE_READY\n'):])
  need(terminal['exit_code']==0 and receipt==nraw and stdout==(p/'native.stdout').read_bytes() and stderr==(p/'native.stderr').read_bytes()==b'','three-blob envelope '+name)
  need(n['device']==int(ready['identity']['devnum']),'native device decision '+name)
  need(record['manifestSha256']==result['manifestSha256'] and record['readinessSha256']==result['readinessSha256'] and record['native_invocations']==1 and record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','saved record consistency '+name)
  need(record['nativeTerminal']==terminal,'native terminal receipt '+name)
  stermin,streceipt,stout,sterr=wrappers[kind].receipt_envelope((p/'selftest-envelope.txt').read_text())
  need(stermin['exit_code']==0 and stermin==record['selftestTerminal'] and streceipt==(p/'selftest.receipt.json').read_bytes() and stout==(p/'selftest.stdout').read_bytes() and sterr==(p/'selftest.stderr').read_bytes()==b'','selftest three-blob envelope '+name)
  for census in ('preCensus','beforeInvokeCensus','postCensus'):need(record[census]['observedHolders']==record[census]['otherErrors']==0 and record[census]['continuousAbsenceEstablished']is False,'bounded census no continuous claim '+name)
  if (p/'interpretation.json').exists():need(q==j(p/'interpretation.json'),'strict interpretation replay '+name)
  raw={}
  for filename,b,h in files:need(sha(b)==h and (p/filename).read_bytes()==b,'saved raw '+name+'/'+filename);raw[filename]=b
  need(result['rawFiles']==[{'name':f,'bytes':len(b),'sha256':h}for f,b,h in files],'raw file declaration '+name)
  out={'kind':kind,'transportAccepted':True,'nativeCounters':{'headers':n['headersSent'],'bulks':n['bulkTransfers']},'savedIdentity':ready['identity'],'manifestSha256':result['manifestSha256'],'readinessSha256':result['readinessSha256'],'cleanup':result['cleanup'],'qualification':q}
  if kind=='dv':
   need(n['headersSent']==7 and n['bulkTransfers']==14 and n['readbackVerified'] and not n['limitMayHaveChanged'] and n['errors']==[],'writer final status')
   need([i for i in range(256)if raw['fresh-R.bin'][i]!=raw['readback-R.bin'][i]]==[0xc4],'only c4 low byte changed in observed fresh/readback R')
   out.update({'observedFreshReadbackRByteDifferences':[0xc4],'sourceModelReplay':{k:du.profile_prediction(raw[k+'.bin'])for k in ('baseline-R','fresh-R','readback-R')},'sourceContextReplayAccepted':du.validate_candidate_context(raw['pre-M.bin'],raw['pre-C.bin'],raw['baseline-R.bin'])is None,'action':n['action'],'profiles':{k:model(raw[k+'.bin'])for k in ('baseline-R','fresh-R','readback-R')},'steps':n['steps'],'bindingProofCount':len(n['bindingChecks'])})
  elif kind=='dp':
   need(n['cyclesStarted']==n['cleanCyclesCompleted']==80 and n['headersSent']==640 and n['bulkTransfers']==1280 and n['terminalReason']=='TimeLimit' and not n['onsetObserved'],'80 clean observed')
   rows=independent_checkpoint(raw['score-checkpoints.bin'],n['startUs'],q['scoreCheckpoints']['rows']);out.update({'checkpointRows':rows,'a0Maximum':max(x['a0U32']for x in rows),'sampledCleanAbove40Count':sum(x['a0Low16']>40 for x in rows),'nonzeroA0':[{k:x[k]for k in ('cycleIndex','a0U32','history0U16x4','recordOrdinal0U32')}for x in rows if x['a0U32']],'timing':{k:n[k]for k in ('startUs','deadlineUs','endUs','overshootUs')},'intervention':n['intervention'],'retainedSourceEndpointObservations':[{ 'role':c['role'],'R':[du.endpoint_observations(base64.b64decode(w['rawBase64'],validate=True))for w in c['windows']if w['name']=='R']}for c in n['retained']],'retained':retained(n)})
  else:
   out.update({'profiles':{k:model(raw[k+'.bin'])for k in ('start-R','end-R')},'M':{'modeAa':u16(raw['M.bin'],10),'modeAc':u16(raw['M.bin'],12),'scanByte':raw['M.bin'][56],'publicationBoundMirror':u16(raw['M.bin'],42),'BUpperMirror':u16(raw['M.bin'],38)},'bindingProofCount':len(n['bindingChecks']),'sourceEndpointObservations':{k:du.endpoint_observations(raw[k+'.bin'])for k in ('start-R','end-R')}})
  if main: identities.append(ready['identity']);allout[name]=out
  raws[name]=raw;natives[name]=n
  return out
 for name,kind in TRIALS:replay(name,kind)
 # Independently replay prior zero baseline and fault DT; comparison is across separate epochs/USB lineage.
 priorfault=replay('reference-fault-01','dt',False);priorzero=replay('reference-baseline-01','dt',False)
 need(all(i==identities[0]for i in identities),'six identical saved identities USB60')
 need(identities[0]['devnum']=='60','USB60')
 setout=allout['dv-set-01'];restore=allout['dv-restore-01'];obs=allout['dv-observation-01'];rec=allout['dv-rechallenge-01'];clean=allout['dv-clean-reference-01'];final=allout['dv-final-clean-01']
 need(setout['action']=='set40to200' and restore['action']=='restore200to40','separate fixed actions')
 for obj,expected in ((setout,[40,40,200]),(restore,[200,200,40])):
  profiles=list(obj['profiles'].values());need([x['alternateLimit']for x in profiles]==expected,'verified fixed change')
  need(all(x['temperature']==24 and x['ordinaryUpper']==x['alternateUpper']==3161 and x['echo']==0 and x['rt']==[0,0,1]for x in profiles),'writer source-model state')
 for obj,limit,maximum in ((obs,200,26),(rec,40,24)):
  need(obj['a0Maximum']==maximum and obj['sampledCleanAbove40Count']==0,'actual clean maxima, no discriminating score witness')
  need(all(x['startAlternateThreshold']==x['endAlternateThreshold']==limit for x in obj['checkpointRows']),'observed c4 throughout')
  need(set(x['selectorC7']for x in obj['checkpointRows'])=={0,1},'both sampled selector states')
  need(all(x['q0U16']==0 for x in obj['checkpointRows']),'q0 all zero')
 need(clean['qualification']['startR']['stop']==clean['qualification']['startR']['fault']==0 and clean['qualification']['startR']['ordinaryGate']==1 and clean['qualification']['rBytesEqual'],'later DT clean stable R')
 need(clean['qualification']['startN']['ordinals']==clean['qualification']['endN']['ordinals']==[41,0,0,0,0,0] and clean['qualification']['startN']['sourceCounts'][0]==4 and clean['qualification']['endN']['sourceCounts'][0]==0 and not clean['qualification']['nBytesEqual'],'active sequential N change')
 need(final['profiles']['start-R']['alternateLimit']==40 and final['profiles']['start-R']['rt']==[0,0,1] and final['qualification']['rBytesEqual'],'final clean40')
 need(final['M']['publicationBoundMirror']==200 and final['qualification']['startR']['mode1RecordLatch']==67 and final['M']['modeAa']==0 and final['M']['modeAc']==2,'final normal-mode publication context')
 def lanes(b):
  need(len(b)==104,'packed104');v=int.from_bytes(b[:102],'little');return {str(x):(v>>(12*(x-568)))&4095 for x in range(568,636)}
 references={}
 for name,out in [('reference-baseline-01',priorzero),('reference-fault-01',priorfault),('dv-clean-reference-01',clean)]:
  references[name]={}
  for which in ('top','bottom'):
   v=lanes(raws[name]['fixed-'+which+'-candidate.bin']);references[name][which]=v
   need({x:v[x]for x in out['qualification']['fixedReferenceCandidates'][which]}==out['qualification']['fixedReferenceCandidates'][which],'independent all-bit packed reference '+name+'/'+which)
 xs=['570','571','622','623','624','625','632','633'];deltas=[]
 for x in xs:deltas.append({'lane':int(x),'priorFaultTop':references['reference-fault-01']['top'][x],'priorFaultBottom':references['reference-fault-01']['bottom'][x],'laterCleanTop':references['dv-clean-reference-01']['top'][x],'laterCleanBottom':references['dv-clean-reference-01']['bottom'][x]})
 # Conditional source-compatible clean prefix, explicitly not certified as one epoch.
 cleanprefix=[]
 for t in clean['qualification']['candidateTuples'][:41]:
  b=t['b'];diff=t['absoluteDifferenceOrMode6Zero'];x=str(t['x'])
  need(t['y']==2159 and t['rgb']==0 and 0<=b<500 and diff>500,'clean prefix source-compatible tuple')
  candidates=[a for a in (b+diff,b-diff)if 0<=a<=4095 and abs(a-b)==diff]
  need(len(candidates)==1 and candidates[0]==references['dv-clean-reference-01']['bottom'][x] and candidates[0]!=references['dv-clean-reference-01']['top'][x],'unique conditional A matches later bottom only')
  cleanprefix.append({**t,'conditionalAIfMode1Tuple':candidates[0],'laterBottomMatches':True,'laterTopMatches':False})
 for a in (460,377):
  for b in range(500):need(abs(a-b)<=500,'constrained absent-lane low-B counterfactual')
 # Earlier fault tuples retain their own scope; later clean records are not relabeled as the same epoch.
 need(all(priorzero['qualification']['fixedReferenceCandidates'][side][x]==0 for side in ('top','bottom')for x in xs),'earlier zero references')
 sb={x['name']:x for x in natives['dv-set-01']['steps']};rb={x['name']:x for x in natives['dv-restore-01']['steps']}
 outer0=sb['write-payload']['beforeUs'];outer1=rb['readback-R-data']['afterUs']
 inner0=sb['readback-R-data']['afterUs'];inner1=rb['write-payload']['beforeUs']
 need(outer0<inner0<obs['timing']['startUs']<obs['timing']['endUs']<inner1<outer1<rec['timing']['startUs']<rec['timing']['endUs']<clean['qualification']['readBrackets']['start-R']['headerBeforeUs']<final['qualification']['readBrackets']['start-R']['headerBeforeUs'],'numeric ordered completed sequence')
 return {'schema':'dv-live-comparison-analysis-v1','checks':checks,'runs':allout,'priorFaultReferenceQualification':priorfault['qualification'],'priorZeroReferenceQualification':priorzero['qualification'],'referenceWindowsDecoded':references,'selectedLaneReferenceComparison':deltas,'laterCleanSourceCompatiblePrefix':cleanprefix,'laterCleanPrefixLaneCounts':{str(x):sum(t['x']==x for t in cleanprefix)for x in sorted(set(t['x']for t in cleanprefix))},'conditionalLowBCounterfactual':{'BRange':[0,499],'laterBottom570_571':460,'laterBottom624_625':377,'strictDifferenceGreaterThan500Impossible':True,'currentBForAbsentLanesCaptured':False,'absenceCauseProven':False},'exposure':{'setWriteHeaderBeforeUs':sb['write-header']['beforeUs'],'fullHeaderToRestoreReadbackOuterNumericalSpanUs':outer1-sb['write-header']['beforeUs'],'setPayloadBeforeUs':outer0,'setReadbackDataAfterUs':inner0,'restorePayloadBeforeUs':inner1,'restoreReadbackDataAfterUs':outer1,'outerNumericalSpanUs':outer1-outer0,'conditionalInnerNumericalSpanUs':inner1-inner0,'scope':'Common native monotonic clock/source freshness and no intervening firmware writer are premises. Completion is not exact RAM commit time. Neither span is unconditional proof of continuous200. DP20s is observation budget, not total altered-value exposure.'},'conclusion':{'thresholdCausalEffect':'inconclusive','original40RechallengeAlsoClean':True,'sampledAbove40WhileCleanWitness':False,'preventionEstablished':False,'reversibleFixedWriteAndFinal40ReadbackEstablished':True,'sameSavedBootAndUsbInstance':True,'noReinitializationBetween200And40':'parent coordinated lineage premise; saved same identity alone is not continuous proof','referenceValuesChangedAcrossCaptures':True,'referenceAgeOrInputChangeCauseProven':False,'historicalActualFixedABranchProven':False,'sameRecordEpochProven':False,'actualFpRegisterObserved':False,'physicalPictureObserved':False,'rootCauseOrElectricalSafetyProven':False},'selectedPackageSha256':sha(package),'selectedSourceRanges':source_ranges,'sourceScope':{'mode1Threshold':'image1 VA1e68..203e (file42068..4223e): C7 selects normal R+30 or alternate R+c4, score comparison uses low16 A; actual FP register not sampled','publication':'image1 c5f6..c604 inclusive ordinal<=mirror; source counts continue c708; latch/ordinal alone not aggregate score proof','referenceDecode':'source-qualified fixed top/bottom candidate104B; independent 68x12bit little-endian; later bytes not historical pointer/epoch proof','sampledCadence':'80 sequential eight-pair cycles over20s; no instrumentation of every comparator invocation; no >40 checkpoint does not exclude an unsampled crossing'}}

if __name__=='__main__':
 data=analyze();out=json.dumps(data,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--check']:need((HERE/'decoded.json').read_text()==out,'exact decoded artifact')
 elif not sys.argv[1:]:(HERE/'decoded.json').write_text(out)
 else:raise SystemExit('usage: analyze.py [--check]')
 print(json.dumps({'accepted':True,'checks':checks,'decodedSha256':sha(out.encode()),'thresholdEffect':'inconclusive','physicalPictureObserved':False,'hostOnly':True}))
