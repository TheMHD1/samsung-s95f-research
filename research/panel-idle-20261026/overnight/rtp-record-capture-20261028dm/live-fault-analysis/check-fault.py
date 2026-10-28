#!/usr/bin/env python3
"""Verify/decode only the retained fixed DM fault. No target, transport or network calls."""
from pathlib import Path
import collections,hashlib,json,struct,sys,types
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent.parent;C=B/'volatile-limit-trial-20261028dk/record-fault-01';DM=D.parent
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0

def need(ok,label):
 global checks
 if not ok:raise ValueError(label)
 checks+=1

def readj(p):return json.loads(p.read_bytes())
def module(p,digest,name):
 raw=p.read_bytes();need(sha(raw)==digest,'source pin '+p.name);m=types.ModuleType(name);m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__);return m
for f in readj(D/'input-manifest.json')['files']:
 raw=(B/f['path']).read_bytes();need(len(raw)==f['bytes'] and sha(raw)==f['sha256'],'input pin '+f['path'])
p=module(DM/'parse-result.py','fa2401bf270583fd793d44150b5db70915504c72e39878a8dd9f24a9be6446ca','baseline_parser')
w=module(DM/'run-once.py','805bde0cac28e7b586a75978e899d7daa1cf4fd5509e50744208f714c6d5d203','baseline_wrapper')
manifest=(C/'reviewed-manifest.json').read_bytes();need(sha(manifest)=='e62b2906734a2814f2165749eb8ab230d5dd8e8dfd37f257ce5962ea20850c53','accepted manifest');need(manifest==w.manifest_bytes(w.build_manifest()[0]),'frozen manifest exact')
result=readj(C/'result.json');record=readj(C/'record.json');native_raw=(C/'native.receipt.json').read_bytes();n,windows,interp=p.parse_native(native_raw.decode())
need(interp==readj(C/'interpretation.json'),'independent strict interpretation matches')
need(result['accepted']is True and result['headersSent']==12 and result['bulkTransfers']==24 and result['cleanup']=='STAGE_ABSENT','wrapper acceptance')
need(record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n' and record['native_invocations']==1 and record['no_retry']is True,'record lifecycle')
need(n['accepted']is True and n['released']is True and n['closed']is True and n['writes']==n['uiOperations']==0,'native lifecycle')
need(result['manifestSha256']==sha(manifest)==record['manifestSha256'],'manifest bindings')
readiness=(C/'readiness-decision.json').read_bytes();need(sha(readiness)==result['readinessSha256']==record['readinessSha256'],'readiness hash');rd=readj(C/'readiness-decision.json');need(rd['accepted']is True and rd['identity']['devnum']==str(n['device'])=='58','readiness device')
need(rd['closedWorldVendorOutLineage']['accepted']is True and rd['endpointQueueProof']is False,'conditional lineage no queue proof')
for tag in ['selftest','native']:
 env=(C/(tag+'-envelope.txt')).read_text();env=env.removeprefix('IMMEDIATE_READY\n');terminal,receipt,stdout,stderr=w.receipt_envelope(env)
 need(terminal['exit_code']==0 and not stderr,'root envelope exit/stderr '+tag)
 for suffix,raw in [('receipt.json',receipt),('stdout',stdout),('stderr',stderr)]:need(raw==(C/(tag+'.'+suffix)).read_bytes(),'root framed file '+tag+'.'+suffix)
 need(terminal==record[tag+'Terminal'],'record terminal '+tag)
need(readj(C/'selftest.receipt.json')=={'selfTestsPassed':485,'targetOperations':0},'actual zero-I/O selftest')
need(len(record['calls'])==27,'fixed capture root call count')
for call in record['calls']:
 need(call['transport_exit']==0 and not call['host_timeout'] and call['transport_stderr']=={'data':'','encoding':'base64'},'transport status')
 response=call['response'];need(response['authenticated']is True and response['uid']==response['euid']==0,'authenticated root response')
 need(len(response['commands'])==1,'single foreground command');cmd=response['commands'][0]
 need(cmd['exit_code']==0 and cmd['timed_out']is False and not cmd['stderr'] and cmd['command']==call['command'],'foreground command completion')
need(record['calls'][-1]['response']['commands'][0]['stdout']=='STAGE_ABSENT\n','actual final cleanup receipt')
for marker,name in [('PRE_READY','metadata-pre.txt'),('BEFORE_INVOKE_READY','metadata-before-invoke.txt'),('POST_READY','metadata-post.txt')]:
 census=w.parse_metadata((C/name).read_text(),marker);need(census['observedHolders']==census['otherErrors']==0,'snapshot census '+marker)
rawmap={};rawindex=[]
for name,raw,h in windows:
 need((C/name).read_bytes()==raw,'retained raw '+name);entry={'name':name,'bytes':len(raw),'sha256':h};need(entry in result['rawFiles'] and entry in record['retained_raw_files'],'raw indexes '+name);rawmap[name[:-4]]=raw;rawindex.append(entry)
need(len(windows)==12,'all raw windows')
half=lambda b,o:struct.unpack_from('<H',b,o)[0];word=lambda b,o:struct.unpack_from('<I',b,o)[0]
r,m,c,d=map(rawmap.get,['start-R','M','C','D']);aa,ac=half(m,10),half(m,12);mode=4 if aa==1 else 6 if ac==1 else 1
rstate={'stop':half(r,0),'fault':half(r,10),'ordinaryGate':half(r,14),'normalMode1Threshold':half(r,0x30),'normalMode6Threshold':half(r,0xc0),'alternateThreshold':half(r,0xc4),'aggregateGate':half(r,0x9e),'mode1Bucket':half(r,0x86),'mode1RecordLatch':half(r,0x90)}
need(rstate['stop']==1 and rstate['fault']==0x1001 and rstate['ordinaryGate']==0 and rstate['alternateThreshold']==40,'fault state with unchanged limit')
need(rawmap['start-R']==rawmap['end-R'] and rawmap['start-N']==rawmap['end-N'],'stable R/N');need(interp['startN']=={'ordinals':[41,0,0,0,0,0],'sourceCounts':[0]*6},'ordinal41 and zero per-dispatch counts')
need(rawmap['RGB']==bytes(96) and all(any(rawmap[k])for k in ['X','Y','Diff']),'nonzero coordinates/difference with zero RGB')
bs=list(struct.unpack('<48H',rawmap['B']));need(any(bs),'nonzero retained B');need(all(x<=4095 for x in bs),'B twelve bit range')
# Verify selected source range hashes instead of copying proprietary instructions.
proof=readj(B/'firmware-display-path-20261028de/record-verification.json')['normal'];asset=B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin';ab=asset.read_bytes();need(sha(ab)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected asset identity')
for x in proof['ranges']:off=int(x['file_offset'],16);need(sha(ab[off:off+x['length']])==x['sha256'],'formatter source range '+x['label'])
# Reparse original baseline and compare exact retained bytes, without changing its analysis.
BC=B/'volatile-limit-trial-20261028dk/record-baseline-01';bn,bwins,bi=p.parse_native((BC/'native.receipt.json').read_text());br={name[:-4]:raw for name,raw,h in bwins}
for name,raw,h in bwins:need((BC/name).read_bytes()==raw,'baseline retained raw '+name)
column_changes={k:{'changedHalfwordIndices':[j for j,(x,y)in enumerate(zip(struct.unpack('<48H',br[k]),struct.unpack('<48H',rawmap[k])))if x!=y],'baselineSha256':sha(br[k]),'faultSha256':sha(rawmap[k])}for k in ['X','Y','RGB','B','Diff']}
prefix=[];groups=collections.defaultdict(list)
for t in interp['candidateTuples']:
 bval=t['b'];diff=t['absoluteDifferenceOrMode6Zero'];candidates=sorted({x for x in [bval-diff,bval+diff]if 0<=x<=4095})
 row={**t,'conditional12bitACandidates':candidates if t['index']<=40 else None,'sourceCompatiblePrefixCandidate':t['index']<=40,'interpretation':'conditional same-type/same-epoch pair, not actual selected-A observation'};prefix.append(row)
 if t['index']<=40:groups[t['x']].append({'index':t['index'],'b':bval,'diff':diff,'aCandidates':candidates})
need(all(t['y']==2159 and t['rgb']==0 and t['b']<500 and t['absoluteDifferenceOrMode6Zero']>500 and len(t['conditional12bitACandidates'])==1 for t in prefix[:41]),'coherent source-compatible first41')
need(all(t['x']==t['y']==t['rgb']==t['absoluteDifferenceOrMode6Zero']==0 for t in prefix[41:]),'cleared tail coordinates')
need(rawmap['B'][82:]==br['B'][82:],'tail B unchanged from baseline')
paired=all(all(prefix[j][k]==prefix[j+1][k]for k in ['y','rgb','b','absoluteDifferenceOrMode6Zero']) and prefix[j+1]['x']==prefix[j]['x']+1 for j in range(0,40,2));need(paired,'twenty adjacent-X equal-data pairs plus singleton')
bylane={str(k):{'records':v,'uniqueACandidates':sorted({a for r in v for a in r['aCandidates']})}for k,v in sorted(groups.items())}
need(all(len(v['uniqueACandidates'])==1 for v in bylane.values()),'stable A candidate within x groups')
S=B/'volatile-limit-trial-20261028dk/score-baseline-01';sn=readj(S/'native.receipt.json');si=readj(S/'interpretation.json');sr=readj(S/'result.json')
need(sr['accepted']is True and sr['trialQualified']is True and sn['accepted']is True and sn['onsetObserved']is True and sn['headersSent']==48 and sn['bulkTransfers']==96 and sn['cleanCyclesCompleted']==5,'coordinator accepted DP onset receipt')
need(sn['endUs']<n['steps'][0]['beforeUs'],'DM after DP native end')
summary={'schema':'dm-live-fault-analysis-v1','status':'independently_verified','target_operations_by_analysis':0,'capture':{'manifestSha256':sha(manifest),'nativeReceiptSha256':sha(native_raw),'headers':12,'bulks':24,'writes':0,'rootCalls':27,'cleanup':'STAGE_ABSENT','firstHeaderBeforeUs':n['steps'][0]['beforeUs'],'lastDataAfterUs':n['steps'][-1]['afterUs'],'totalReadBracketUs':n['steps'][-1]['afterUs']-n['steps'][0]['beforeUs'],'readBrackets':interp['readBrackets']},'R':rstate,'M':{'aa':aa,'ac':ac,'sourceConditionalPredicateMode':mode,'scanEnabled':m[56],'root':hex(word(m,64)),'publicationBoundMirror':half(m,42),'xBase':half(m,32),'cyclingSelectorCounter':half(m,36),'currentRowMetadata':half(m,20),'dispatchRowMetadata':half(m,48),'dispatchChannelMetadata':half(m,52),'differenceThresholds':[half(m,x)for x in [22,24,26,28]]},'C':{'geometry':list(struct.unpack_from('<3H',c)),'byte6':c[6],'alternateSelectorC7':c[7],'runtimeContextByte8':c[8],'sourceConditionalMode1Threshold':half(r,0xc4) if c[7] else half(r,0x30)},'N':{'start':interp['startN'],'end':interp['endN']},'records':{'candidateTuples':prefix,'conditionalAByX':bylane,'nonzeroBIndices':[i for i,x in enumerate(bs)if x],'bHistogram':dict(sorted(collections.Counter(bs).items())),'zeroColumns':['RGB'],'validCurrentPrefixProven':False,'interpretation':'First41 coherent nonzero coordinate/difference rows match ordinal41/bound40 and type1 qualification; tail41..47 remains cleared coordinates with baseline-identical B. Consistent prefix is not proven current epoch.'},'D':{'baseBus':'0x4700a60a','halfwords':[{'offset':hex(i),'value':half(d,i)}for i in range(0,48,2)],'previousDescriptorTailD4toB':[half(d,i)for i in range(4,12,2)],'currentDescriptorTailD16to1D':[half(d,i)for i in range(0x16,0x1e,2)],'D18':half(d,0x18),'savedD1E':half(d,0x1e),'pendingByteD2B':d[0x2b],'limitations':'Source-conditional RAM mirror; words retained without invented physical units, not actual B ring header at predicate time.'},'bindingChecks':[{**{k:v for k,v in b.items()if k!='kernel'},'kernel':None if b['kernel']is None else {k:v for k,v in b['kernel'].items()if k!='rawBase64'}}for b in n['bindingChecks']],'comparison':{'columnChanges':column_changes,'baselineNativeReceiptSha256':sha((BC/'native.receipt.json').read_bytes()),'baselineDHalfwords':list(struct.unpack('<24H',br['D'])),'baselineInterpretation':{'startR':bi['startR'],'sourceContext':bi['sourceContext'],'startN':bi['startN']},'twentyAdjacentEqualDataPairs':paired,'lastSingletonIndex':40,'coherentPrefixLength':41,'prefixEpochProven':False,'tailBUnchanged':True},'precedingScoreCapture':{'nativeReceiptSha256':sha((S/'native.receipt.json').read_bytes()),'resultSha256':sha((S/'result.json').read_bytes()),'acceptedByCoordinator':True,'independentCompleteDpReparsePerformedHere':False,'headers':48,'bulks':96,'cleanCycles':5,'firstFaultCycle':6,'softwareBracket':si['ordering']['softwareTransitionBracket'],'nativeEndUs':sn['endUs'],'gapFromDpEndToDmFirstHeaderUs':n['steps'][0]['beforeUs']-sn['endUs'],'noInterveningUiOrReset':'central coordinator premise; captures themselves show no DM UI/reset path','physicalPictureObserved':False},'rawHashes':rawindex,'sourceProvenance':{'selectedAssetSha256':sha(ab),'image1FileOffsetFormula':'VA+0x40200','recordSourceRanges':proof['ranges'],'additionalFieldWidthAnchors':{'selectorCounter':{'va':'0x1c148..0x1c150','fileOffset':'0x5c348','bytes':10,'sha256':sha(ab[0x5c348:0x5c352]),'width':'u16'},'rowChannel':{'va':'0xb68c..0xb69e and0xb732..0xb748','width':'u16','source':'orchestrator-with-literals.disasm.txt'}},'formatterStores':{'X':'0xc666','Y':'0xc676','RGB':'0xc686','B':'0xc696','Diff':'0xc6a6'},'partialClear':'frame-end/init clear first3 arrays; B and Diff are retained on checked paths','modeSelection':'predicate0x1e68..0x203e aa==1→4, ac==1→6, otherwise1; mode1 C7==0 selects root2430, nonzero selects root24c4','descriptorCopy':'refresh0x3934..0x3a64;0x3974..0x397e copies D16..1d→D4..b; current stores0x3992/39a2/39b2/39c4','layoutIdentityIsRunningAttestation':False},'limitations':{'atomicSnapshot':False,'recordEpochProven':False,'actualFixedABranchProven':False,'physicalPictureObserved':False,'endpointQueueProof':False,'sourceContextConditional':True},'checksPassed':checks}
(D/'decoded-fault.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps({'status':'PASS','checksPassed':checks,'readBracketUs':summary['capture']['totalReadBracketUs'],'bNonzero':len(summary['records']['nonzeroBIndices']),'mode':mode,'selectedThreshold':summary['C']['sourceConditionalMode1Threshold'],'decodedSha256':sha((D/'decoded-fault.json').read_bytes())}))
