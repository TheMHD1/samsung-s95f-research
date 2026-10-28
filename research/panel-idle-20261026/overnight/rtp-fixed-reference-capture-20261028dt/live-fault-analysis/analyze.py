#!/usr/bin/env python3
"""Actual DP onset + later DT reference capture, with conditional source comparison."""
import base64,hashlib,importlib.util,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent.parent;DK=BASE/'volatile-limit-trial-20261028dk'
checks=0

def need(ok,why):
 global checks
 checks+=1
 if not ok:raise ValueError(why)

def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_text())
def half(b,o):return struct.unpack_from('<H',b,o)[0]
def module(path,name,pin):
 need(sha(path.read_bytes())==pin,'frozen parser '+name)
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def analyze():
 for f in j(HERE/'input-pins.json')['files']:
  b=Path(f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'input pin '+f['path'])
 for directory,digest in [('rtp-score-checkpoints-20261028dp','ba02517d7f8bb5cae6aa4257c426b7cc50780bfdfd5e0a73a7838e2386dff9ee'),('rtp-fixed-reference-capture-20261028dt','ed1e1594f3dc23528c69894c21a19c214593a0ae12c0dd20ec5ceebc9fda4d80'),('rtp-record-capture-20261028dm','e62b2906734a2814f2165749eb8ab230d5dd8e8dfd37f257ce5962ea20850c53')]:
  manifest=j(BASE/directory/'deployment-manifest.json');need(sha((BASE/directory/'deployment-manifest.json').read_bytes())==digest,'frozen manifest '+directory)
  for section in ('nativeFiles','wrapperFiles'):
   for name,pin in manifest.get(section,{}).items():
    b=(BASE/directory/name).read_bytes();need(len(b)==pin['bytes']and sha(b)==pin['sha256'],'source/payload manifest '+name)
 dt=module(BASE/'rtp-fixed-reference-capture-20261028dt/parse-result.py','dt_frozen','85e6d0783dc0455d4002e6e0332e23eed15d7d8b21c5ece3b3443c5529428b47')
 dp=module(BASE/'rtp-score-checkpoints-20261028dp/parse-result.py','dp_frozen','9b5e476a50e73439e11a6e5ed78bae0079a1d802c054212a8974e079f77d6b3a')
 dm=module(BASE/'rtp-record-capture-20261028dm/parse-result.py','dm_frozen','fa2401bf270583fd793d44150b5db70915504c72e39878a8dd9f24a9be6446ca')
 n,_,files,gc,q=dp.parse_native((DK/'reference-onset-01/native.receipt.json').read_text())
 need(gc==[]and q['trialQualified']is True,'qualified exclusive DP')
 need(q==j(DK/'reference-onset-01/interpretation.json'),'DP interpretation replay')
 for name,b,h in files:need(sha(b)==h and (DK/'reference-onset-01'/name).read_bytes()==b,'DP raw '+name)
 need(n['headersSent']==48 and n['bulkTransfers']==96 and n['cleanCyclesCompleted']==5 and n['cyclesStarted']==6,'actual DP counters')
 captures=[]
 for cap in n['retained']:
  decoded={};brackets={}
  for i,w in enumerate(cap['windows']):
   b=base64.b64decode(w['rawBase64'],validate=True);name=w['name'];t=cap['transfers'][2*i:2*i+2]
   need(sha(b)==w['sha256'],'DP retained hash')
   brackets.setdefault(name,[]).append({'headerBeforeUs':t[0]['beforeUs'],'dataAfterUs':t[1]['afterUs']})
   if name=='H':decoded['H']={'a':list(struct.unpack_from('<6I',b,4)),'q':list(struct.unpack_from('<6H',b,28)),'history':[list(struct.unpack_from('<4H',b,40+8*k))for k in range(6)]}
   if name=='N':decoded['N']={'ordinals':list(struct.unpack_from('<6I',b)),'sourceCounts':list(struct.unpack_from('<6H',b,24))}
  captures.append({'role':cap['role'],'cycleIndex':cap['cycleIndex'],'decoded':decoded,'brackets':brackets})
 byrole={c['role']:c for c in captures};last=byrole['last-clean']['decoded'];post=byrole['post-fault']['decoded']
 need(last['H']['a'][0]==28 and post['H']['a'][0]==42,'actual 28 to42')
 need(last['H']['history'][0]==[0,2,0,2] and post['H']['history'][0]==[2,0,2,0],'actual delayed history')
 need(last['N']['ordinals'][0]==32 and post['N']['ordinals'][0]==41,'ordinal progression32 to41')
 need(last['N']['sourceCounts']==[2,0,0,0,0,0] and post['N']['sourceCounts']==[0]*6,'working source counts')
 need([r['a0U32']for r in q['scoreCheckpoints']['rows']]==[0,0,0,0,28],'actual compact scores')
 def replay(name,parser):
  p=DK/name;native,files,interpretation=parser.parse_native((p/'native.receipt.json').read_text())
  need(interpretation==j(p/'interpretation.json'),'exact interpretation '+name)
  result=j(p/'result.json');need(result['accepted']is True and result['cleanup']=='STAGE_ABSENT','accepted/cleanup '+name)
  m=(BASE/('rtp-record-capture-20261028dm'if parser is dm else'rtp-fixed-reference-capture-20261028dt')/'deployment-manifest.json').read_bytes()
  need((p/'reviewed-manifest.json').read_bytes()==m and result['manifestSha256']==sha(m),'manifest '+name)
  raw={}
  for filename,b,h in files:
   need(sha(b)==h and (p/filename).read_bytes()==b,'saved raw '+name+'/'+filename);raw[filename]=b
  need(result['rawFiles']==[{'name':f,'bytes':len(b),'sha256':h}for f,b,h in files],'wrapper raw declarations '+name)
  return native,raw,interpretation
 fault,raw,fi=replay('reference-fault-01',dt)
 _,baseline,bi=replay('reference-baseline-01',dt)
 _,oldraw,oi=replay('record-fault-01',dm)
 def decodeAll(b):
  need(len(b)==104,'fixed window104');bits=int.from_bytes(b[:102],'little')
  return {x:(bits>>(12*(x-568)))&4095 for x in range(568,636)}
 top=decodeAll(raw['fixed-top-candidate.bin']);bottom=decodeAll(raw['fixed-bottom-candidate.bin'])
 for k,values in [('top',top),('bottom',bottom)]:need({str(x):values[x]for x in (570,571,622,623,624,625,632,633)}==fi['fixedReferenceCandidates'][k],'independent fixed decode '+k)
 need(baseline['fixed-top-candidate.bin']==baseline['fixed-bottom-candidate.bin']==bytes(104),'earlier zero baseline')
 need(fi['rBytesEqual']and fi['nBytesEqual']and fi['startN']['ordinals']==[41,0,0,0,0,0],'sequential fault ordinal41')
 need(fi['startR']['fault']==4097 and fi['startR']['alternateLimit']==40,'fault40')
 # Source-compatible prefix only. We do not certify one epoch or original decision-time memory.
 rows=[]
 for t in fi['candidateTuples'][:41]:
  b=t['b'];d=t['absoluteDifferenceOrMode6Zero'];x=t['x']
  need(t['y']==2159 and t['rgb']==0 and 0<=b<500 and d>500,'prefix coordinate/B/diff domain')
  candidates=[a for a in (b+d,b-d)if 0<=a<=4095 and abs(a-b)==d]
  need(len(candidates)==1,'unique conditional12bit A')
  a=candidates[0];need(x in bottom and a==bottom[x] and a!=top[x],'bottom matches and top does not')
  rows.append({**t,'conditionalAIfMode1Tuple':a,'bottomCandidateLater':bottom[x],'topCandidateLater':top[x],'bottomMatches':True,'topMatches':False})
 need(set(t['x']for t in rows)=={570,571,624,625,632,633},'new recorded clusters')
 oldA={}
 for t in oi['candidateTuples'][:41]:
  b=t['b'];d=t['absoluteDifferenceOrMode6Zero'];need(0<=b<500 and d>500,'prior source-compatible domain')
  a=b+d;need(0<=a<=4095 and b-d<0,'prior unique conditional A')
  oldA.setdefault(t['x'],set()).add(a)
 need(all(len(v)==1 for v in oldA.values()),'prior per-lane constant reconstruction')
 oldA={x:next(iter(v))for x,v in oldA.items()}
 need(oldA[622]==oldA[623]==550 and bottom[622]==bottom[623]==454,'changed absent cluster reference')
 m=raw['M.bin'];r=raw['start-R.bin'];need(half(m,22)==half(m,26)==500,'both directional mode1 diff thresholds500')
 need(half(m,38)==half(r,0x20)==3183 and half(m,40)==half(r,0x22)==500,'sampled B acceptance bounds')
 # Exhaustive constrained counterfactual: contemporaneous B is NOT captured for absent lanes.
 for b in range(500):need(abs(454-b)<=454 and not(abs(454-b)>500),'low-B counterfactual')
 need(abs(550-0)>500 and not(abs(454-0)>500),'same-B0 old/new counterfactual')
 need(abs(454-3184)>500,'high-B alternative remains possible')
 package=(BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
 need(sha(package)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','source package')
 for source in j(BASE/'rtp-fixed-reference-capture-20261028dt/reviews/independent-validation.json')['sourceRangeEvidence']:
  off=int(source['file_offset'],16);need(sha(package[off:off+source['bytes']])==source['sha256'],'selected source range '+source['label'])
 # Readiness/boot identity consistency is checked without treating snapshots as continuous absence.
 readyDP=j(DK/'reference-onset-01/readiness-decision.json');readyDT=j(DK/'reference-fault-01/readiness-decision.json')
 need(readyDP['identity']['boot']==readyDT['identity']['boot']and readyDP['identity']['devnum']==readyDT['identity']['devnum']=='59','same boot/USBinstance saved decisions')
 for name in ('reference-onset-01','reference-fault-01'):
  need(sha((DK/name/'readiness-decision.json').read_bytes())==j(DK/name/'result.json')['readinessSha256'],'saved readiness digest '+name)
 return {'schema':'dt-live-fault-analysis-v1','checks':checks,'dpQualification':q,'dpRetainedDecoded':captures,
 'dtInterpretation':fi,'dtCurrentMetadataRow':half(raw['M.bin'],20),'dtSavedMetadataRow':half(raw['M.bin'],48),'dtFullWindowLaneValues':{'top':top,'bottom':bottom},'sourceCompatiblePrefixRows':rows,
 'prefixCount':41,'prefixBottomMatches':41,'prefixTopMatches':0,'prefixXs':{x:sum(t['x']==x for t in rows)for x in sorted(set(t['x']for t in rows))},
 'previousConditionalAByLane':oldA,'currentBottomDeltaFromPreviousConditionalA':{x:bottom[x]-a for x,a in oldA.items()},
 'baselineFixedWindowsAllZero':True,'referenceFaultWindowsAllZero':False,
 'counterfactual':{'absentNewRecordLanes':[622,623],'previousConditionalA':550,'currentBottomCandidate':454,'priorObservedBForTheseRows':[t['b']for t in oi['candidateTuples'][:41]if t['x']in(622,623)],
 'directionalDifferenceThresholds':500,'BLowerBoundary':500,'BUpperBoundary':3183,'allBLowOutsideBand0Through499FailDiffForA454':True,
 'sameB0_A550DiffPasses_A454Fails':True,'highB3184CouldStillPassWithA454':True,'currentBForAbsentLanesObserved':False,'skipMasksAndSchedulingUnobserved':True,'absenceCauseProven':False},
 'timing':{'dpSoftwareTransitionBracket':q['ordering']['softwareTransitionBracket'],
 'dpPostfaultHBracket':byrole['post-fault']['brackets']['H'][0],'dtReadBrackets':fi['readBrackets'],
 'numericCounterGapPostfaultHAfterToDtStartHeaderUs':fi['readBrackets']['start-R']['headerBeforeUs']-byrole['post-fault']['brackets']['H'][0]['dataAfterUs'],
 'gapScope':'numeric difference conditional on shared native monotonic timebase in same saved boot; not a physical-light interval'},
 'sourcePredicates':{'BOutOfBand':'formatterc5e6..c5f4: B>upper OR B<lower; boundaries excluded',
 'difference':'comparatorbbbc..bc4a derives unsigned abs(A-B), directional thresholds; mode1bcbc/bcfc strict greater',
 'publication':'formatterc5f6..c604 inclusive ordinal<=mirror; capacityc64c<512; source count incrementc708 independent of publication saturation',
 'upstreamSkip':'unpackerbeb4..bec8 and analogous lanes: per-lane flags, masks and source mode can skip comparator',
 'Aselection':'dispatcherb832..b88a uses currentBheader+6,counter4c4,C7 to choose fixed-top/fixed-bottom/dynamic; later D/M/C are not actual historical header'},
 'limitations':{'atomicSnapshot':False,'singleRecordEpochProven':False,'actualDecisionTimeFixedBranchProven':False,'actualFpRegisterCaptured':False,
 'physicalPackedProducerIdentified':False,'physicalPictureObserved':False,'rootCauseOrElectricalSafetyProven':False,
 'matchingLaterBottomIsHistoricalPointerProof':False,'saturationMeansAllQualifyingSamplesRetained':False},
 'originalTransportCounters':{'DPheaders':48,'DPbulks':96,'DTheaders':14,'DTbulks':28,'writes':0,'retries':0}}

if __name__=='__main__':
 d=analyze();s=json.dumps(d,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--check']:need((HERE/'decoded.json').read_text()==s,'exact decoded artifact')
 elif not sys.argv[1:]:(HERE/'decoded.json').write_text(s)
 else:raise SystemExit('usage: analyze.py [--check]')
 print(json.dumps({'accepted':True,'checks':checks,'decodedSha256':sha(s.encode()),'bottomMatches':41,'historicalBranchProven':False,'hostOnly':True}))
