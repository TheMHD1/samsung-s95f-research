#!/usr/bin/env python3
"""Pinned offline actual EB replay, including exact mock transport command replay."""
import base64,copy,hashlib,importlib.util,json,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ED=HERE.parent;B=ED.parent;D=B/'rtp-lane-gate-capture-20261028eb';P=ED/'table-read-01';W=B/'rtp-lane-gate-qualification-20261028ea';checks=0;negative_cases=0
MAN='e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11';READY='57c5888f37e7b8837c8d66b9666ede5627a0096ce1cda2a8afafeee46e1e71c3'
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
 for f in j(HERE/'input-pins.json')['files']:
  b=Path(f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'input pin '+f['path'])
 need(sha((D/'deployment-manifest.json').read_bytes())==MAN,'manifest known pin')
 need(sha((D/'source-inventory.json').read_bytes())=='271061f8c60ee75f219b56217ac6dfcf3aa13616d67c3d4f54e46f655c13bdec','frozen inventory pin')
 inv=j(D/'source-inventory.json');need(len(inv['files'])==30,'30 frozen sources/payloads')
 for f in inv['files']:
  b=(D/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'source inventory '+f['path'])
 wrapper=module(D/'run-once.py','ed_offline_wrapper','886bdc05bb8eb5a255443f95a964f2bae947fc758b18ea0e4893f42c3e4ad9a8')
 parser=module(D/'parse-result.py','ed_offline_parser','e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523')
 manifest,payload=wrapper.build_manifest();manifest_raw=wrapper.manifest_bytes(manifest)
 need(manifest_raw==(D/'deployment-manifest.json').read_bytes()==(P/'reviewed-manifest.json').read_bytes(),'exact regenerated/captured manifests')
 source_check={'schema':'ed-parent-offline-source-check-v1','accepted':True,'sourceFilesMatched':len(inv['files']),'manifestSha256':sha(manifest_raw),'payloadNames':sorted(payload),'targetOperations':0}
 need(source_check==j(ED/'source-check.json'),'reproduce parent source-check')
 ready,readyraw=wrapper.load_readiness(ED/'readiness-01/readiness.json',READY)
 need(readyraw==(P/'readiness-decision.json').read_bytes(),'same saved readiness bytes')
 for e in ready['evidence']:
  need(sha(Path(e['path']).read_bytes())==e['sha256'],'every readiness evidence reference '+e['path'])
 premise=(ED/'first-read-phase.md').read_bytes();need(sha(premise)==ready['closedWorldVendorOutLineage']['evidenceSha256']and premise.decode().strip()==ready['closedWorldVendorOutLineage']['statement'],'phase premise exact bytes')
 need(ready['identity']['devnum']=='60','USB60')
 metadata=j(ED/'readiness-01/metadata-root.json');need(len(metadata['calls'])==1,'one cached readiness request')
 meta=metadata['calls'][0];need(meta['command']=='set -eu\n'+wrapper.metadata_body(ready['identity'],'ED_CURRENT_READY'),'exact cached-only readiness command')
 text=call_check(meta);need(text==(ED/'readiness-01/metadata.txt').read_text(),'cached metadata saved stdout')
 census=wrapper.parse_metadata(text,'ED_CURRENT_READY');need(census==j(ED/'readiness-01/census-summary.json'),'cached census exact')
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
 # Independently reconstruct the accepted preceding code-read boundary.
 pred=j(ED/'predecessor-check.json')
 for e in pred['inputs']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'predecessor source/raw pin')
 dx=module(B/'live-code-fingerprint-20261028dx/parse-result.py','ed_predecessor_dx','70efd3096ec5b1cef37fabd74f3e6c3fb63ca72d847bd79500bdb31d74c9dd05')
 pp=B/'live-code-fingerprint-trial-20261028dy/code-read-01';pn,praw,pi=dx.parse_native((pp/'native.receipt.json').read_text());pr=j(pp/'result.json')
 need(pr['accepted']is True and pr['manifestSha256']=='c4d51611cf638f0ac4e9e3003c3b72ee592f460df19ed6138ce57ae7e6e92fac'and pr['cleanup']=='STAGE_ABSENT'and pn['protocolPhase']=='ReadyForHeader'and pn['released']and pn['closed'],'accepted code-read predecessor')
 for name,b,h in praw:need((pp/name).read_bytes()==b and sha(b)==h,'predecessor actual raw '+name)
 expected_pred={'schema':'ed-offline-predecessor-check-v1','accepted':True,'headers':4,'bulks':8,'phase':'ReadyForHeader','released':True,'closed':True,'stageAbsent':True,'sampledCodeMatch':True,'targetOperations':0,'physicalPictureObserved':False,'endpointQueueProof':False,'inputs':[{'path':str(path),'sha256':sha(path.read_bytes())}for path in [B/'live-code-fingerprint-20261028dx/parse-result.py',pp/'native.receipt.json',pp/'result.json',*[pp/name for name,_,_ in praw]]]}
 need(pred==expected_pred,'complete exact parent predecessor check')
 need(ready['identity']==j(pp/'readiness-decision.json')['identity'],'same saved USB60 predecessor identity')
 # Verify new complete intervals against frozen EA and selected source range hashes.
 need(sha((W/'source-inventory.json').read_bytes())=='44fe321b0445c5ca41c7ac4a1b34590c75faa8713e49fd45d751d062ff957371','EA source inventory')
 for f in j(W/'source-inventory.json')['files']:
  b=(W/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'EA frozen source '+f['path'])
 need(sha((W/'fixed-read-plan.json').read_bytes())=='35cf50b7794d859629c7dd526c455af2756585d0b7269f5d071fa5f0f5d76878','EA fixed readplan')
 plan=j(W/'fixed-read-plan.json');source=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
 need(sha(source)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package')
 for row in j(W/'source-qualification.json')['sourceRanges']:
  off=int(row['fileOffset'],16);need(sha(source[off:off+row['bytes']])==row['sha256'],'EA exact source slice')
 data={name:b for name,b,_ in raws}
 primary=struct.unpack('<68H',data['primary-lane-gate.bin']);secondary=list(data['secondary-lane-gate.bin']);m=data['M.bin'];c=data['C.bin'];r=data['start-R.bin']
 half=lambda b,o:struct.unpack_from('<H',b,o)[0]
 root=struct.unpack_from('<I',m,64)[0];aa,ac=half(m,10),half(m,12);cc=m[44];sb=(aa==1 or ac==1)and cc!=0
 need(root==0x20010000 and half(m,32)==0 and (half(m,6),half(m,8))==(2880,1920),'independent M root/xbase/span')
 need((aa,ac,cc)==(0,2,0)and half(r,16)==4 and struct.unpack_from('<3H',c)==(2160,1920,2880)and c[7]==0 and half(m,42)==200,'actual captured mode/selector/publication')
 need(primary==(0,)*68 and secondary==[0]*68 and sb is False,'actual complete zero tables/SBfalse')
 gate_rows=[]
 for k,(v,b)in enumerate(zip(primary,secondary)):
  row={'lane':568+k,'primaryHalfword':v,'primaryLowBit':v&1,'secondaryByte':b,'secondaryOverrideSB':sb,'locallyAdmittedByCapturedTables':v%2==0 and (b==0 or sb)}
  need(row==interpret['laneGateSamples'][k],'independent complete gate row');gate_rows.append(row)
 for spec,proposal in zip(parser.SPECS[10:12],plan['windows']):
  need(spec[1]==int(proposal['busAddress'],16)and spec[2]==proposal['bytes']and struct.pack('<III',0x101,spec[1],spec[2]).hex()==proposal['headerLittleEndianHex'],'EA independent header/range')
 need(data['start-R.bin']==data['end-R.bin']and [half(r,o)for o in (0,10,14,0xc4,0x90)]==[0,0,1,40,69],'clean stable RT40/latch69')
 need(data['start-N.bin']==data['end-N.bin']==bytes(36),'stable zero ordinals/source counts')
 need(data['X.bin']==data['Y.bin']==data['RGB.bin']==bytes(96),'no published coordinate prefix')
 cols={name:list(struct.unpack('<48H',data[name+'.bin']))for name in ('X','Y','RGB','B','Diff')}
 need(any(cols['B'])and any(cols['Diff']),'nonzero B/Diff candidate remnants')
 prior=B/'volatile-limit-trial-20261028dk/dv-final-clean-01'
 priorcolumns={name:{'currentSha256':sha(data[name+'.bin']),'priorSha256':sha((prior/(name+'.bin')).read_bytes()),'bytesEqual':data[name+'.bin']==(prior/(name+'.bin')).read_bytes()}for name in ('X','Y','RGB','B','Diff')}
 need(priorcolumns['B']['bytesEqual']and priorcolumns['Diff']['bytesEqual'],'exact priorApps B/Diff retained bytes')
 need(not priorcolumns['X']['bytesEqual']and not priorcolumns['Y']['bytesEqual'],'current cleared coordinates differ from priorApps records')
 fixed={}
 for side in ('top','bottom'):
  raw=data['fixed-'+side+'-candidate.bin'];need(len(raw)==104,'fixed104');bits=int.from_bytes(raw[:102],'little');fixed[side]={str(lane):(bits>>(12*(lane-568)))&4095 for lane in range(568,636)}
  need({x:fixed[side][x]for x in interpret['fixedReferenceCandidates'][side]}==interpret['fixedReferenceCandidates'][side],'independent all68 packed12 decode '+side)
 # Negative tests use only cloned actual data, never mutate preserved inputs.
 for index in range(16):
  bad=copy.deepcopy(native);bad['windows'][index]['address']+=4;reject(lambda:parser.parse_native(json.dumps(bad)))
 for flag in ('packingQualified','laneGateContextQualified','accepted','released','closed'):
  bad=copy.deepcopy(native);bad[flag]=False;reject(lambda:parser.parse_native(json.dumps(bad)))
 for index in range(32):
  bad=copy.deepcopy(native);bad['steps'][index]['count']-=1;reject(lambda:parser.parse_native(json.dumps(bad)))
  bad=copy.deepcopy(native);bad['steps'][index]['after']='Unknown';reject(lambda:parser.parse_native(json.dumps(bad)))
 for name,offset in [('M',64),('M',6),('M',8),('M',32),('C',0),('C',2),('C',4),('start-R',16)]:
  bad=copy.deepcopy(native);row=next(w for w in bad['windows']if w['name']==name);raw=bytearray(base64.b64decode(row['base64']));raw[offset]^=2 if name=='start-R'else 1;row['base64']=base64.b64encode(raw).decode();row['sha256']=sha(raw);reject(lambda:parser.parse_native(json.dumps(bad)))
 # Honest alternative table values are accepted and their derived local flags change; they are not fixed expected-zero hashes.
 for name,index in [('primary-lane-gate',0),('secondary-lane-gate',0)]:
  changed=copy.deepcopy(native);row=next(w for w in changed['windows']if w['name']==name);raw=bytearray(base64.b64decode(row['base64']));raw[index]=1;row['base64']=base64.b64encode(raw).decode();row['sha256']=sha(raw)
  _,_,q=parser.parse_native(json.dumps(changed));need(q['laneGateSamples'][0]['locallyAdmittedByCapturedTables']is False,'honest changed table input is decoded, not forced to zero')
 actual=(P/'native-envelope.txt').read_text()[len('IMMEDIATE_READY\n'):]
 for bad in (actual[:-1],actual+'extra', '[GC_INFO]\n'+actual):reject(lambda:wrapper.receipt_envelope(bad))
 for field,value in [('transport_exit',1),('host_timeout',True),('remote_timeout_seconds',44),('host_timeout_limit_seconds',74),('command_bytes',0)]:
  bad=copy.deepcopy(calls[0]);bad[field]=value;reject(lambda:call_check(bad))
 bad=copy.deepcopy(calls[0]);bad['response']['commands'][0]['command']+='\n';reject(lambda:call_check(bad))
 need(native['headersSent']==16 and native['bulkTransfers']==32 and native['writes']==native['uiOperations']==0 and native['released']and native['closed']and native['protocolPhase']=='ReadyForHeader','exact native16/32 result')
 need(result['nativeInvocations']==1 and result['retries']==result['wrapperUiOperations']==0,'one native no retry/UI')
 return {'schema':'ed-lane-gate-live-analysis-v1','checks':checks,'manifestSha256':MAN,'readinessSha256':READY,'savedIdentity':ready['identity'],'interpretation':interpret,'independentGateRows':gate_rows,'primaryAll68HalfwordsZero':True,'secondaryAll68BytesZero':True,'all68LocallyAdmittedByCapturedTables':True,'secondaryOverrideSB':sb,'independentContext':{'root':hex(root),'xBase':0,'packedBytes':2880,'lanes':1920,'aa':aa,'ac':ac,'byte4cc':cc,'operatingMode':4,'selectorC7':0,'publicationBoundMirror':200,'rtState':[0,0,1],'alternateLimit':40,'mode1RecordLatch':69,'currentMetadataRow':half(m,20),'savedMetadataRow':half(m,48),'scanByte':m[56]},'priorFinalAppsColumnComparison':priorcolumns,'independentRecordColumns':cols,'validRecordPrefixEstablished':False,'independentFixed68LaneValues':fixed,'nativeSteps':native['steps'],'bindingProofCount':len(native['bindingChecks']),'selftest':{'selfTestsPassed':2071,'targetOperations':0},'diagnostics':{k:record[k]for k in ('selftestDiagnosticStdout','nativeDiagnosticStdout')},'sourceCheckReproduced':source_check,'predecessorCheckVerified':pred,'readinessCensus':census,'threeWrapperCensuses':{k:record[k]for k in ('preCensus','beforeInvokeCensus','postCensus')},'exactRootCommandReplay':{'calls':28,'maximumCommandBytes':max(c['command_bytes']for c in calls),'allSavedArtifactsByteExact':True,'noRealRootAdapterImported':True},'actualTransport':{'headers':16,'bulks':32,'nativeInvocations':1,'writes':0,'uiOperations':0,'retries':0,'terminalPhase':'ReadyForHeader','released':True,'closed':True,'cleanup':'STAGE_ABSENT'},'timing':{'firstHeaderBeforeUs':native['steps'][0]['beforeUs'],'lastDataAfterUs':native['steps'][-1]['afterUs'],'numericFullReadSpanUs':native['steps'][-1]['afterUs']-native['steps'][0]['beforeUs'],'scope':'sequential full OUT-before/IN-after brackets, not atomic controller/gate-call/physical-light timestamps'},'negativeTestsPassed':negative_cases,'claims':{'actualTableSamplesObserved':True,'tableSampleScope':'only68 lanes568..635 in this capture','historicalGateExecutionProven':False,'actualComparatorCallProven':False,'gateBodyLiveFingerprinted':False,'recordEpochProven':False,'physicalLaneMappingProven':False,'physicalPictureObserved':False,'atomicSnapshot':False,'tableWriterOrResetCauseProven':False,'safeModificationQualified':False,'rootCauseOrPreventionEstablished':False,'endpointQueueProof':False},'lineageScope':'Parent closed-world vendor-OUT predecessor premise is byte-pinned and independently replayed. Cached identities/censuses are not continuous client/queue proof.'}

if __name__=='__main__':
 data=analyze();raw=json.dumps(data,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--check']:need((HERE/'decoded.json').read_text()==raw,'exact frozen decoded artifact')
 elif not sys.argv[1:]:(HERE/'decoded.json').write_text(raw)
 else:raise SystemExit('usage: analyze.py [--check]')
 print(json.dumps({'accepted':True,'checks':checks,'decodedSha256':sha(raw.encode()),'all68PrimaryZero':True,'all68SecondaryZero':True,'localEligibilityOnly':True,'actualComparatorCallProven':False,'hostOnly':True}))
