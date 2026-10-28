#!/usr/bin/env python3
"""Pinned offline actual DX replay, including exact mock transport command replay."""
import base64,copy,hashlib,importlib.util,json,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;DY=HERE.parent;B=DY.parent;D=B/'live-code-fingerprint-20261028dx';P=DY/'code-read-01';W=B/'code-alias-qualification-20261028dw';checks=0;negative_cases=0
MAN='c4d51611cf638f0ac4e9e3003c3b72ee592f460df19ed6138ce57ae7e6e92fac';READY='340ea97bed1743a9bde185f9bbd2c276dfdc8a4ed19cee40219318821070573e'
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
 need(sha((D/'source-inventory.json').read_bytes())=='9be78b2fcd8b8340b00fab5ba85008a63142acbaec121107b941dd64d564140f','frozen inventory pin')
 inv=j(D/'source-inventory.json');need(len(inv['files'])==21,'21 frozen sources/payloads')
 for f in inv['files']:
  b=(D/f['path']).read_bytes();need(len(b)==f['bytes']and sha(b)==f['sha256'],'source inventory '+f['path'])
 wrapper=module(D/'run-once.py','dy_offline_wrapper','0ab205eb9204c14b049dacb1b936f4e263c1fa7a8b6c2c457e0e8c3d8a2199e0')
 parser=module(D/'parse-result.py','dy_offline_parser','70efd3096ec5b1cef37fabd74f3e6c3fb63ca72d847bd79500bdb31d74c9dd05')
 manifest,payload=wrapper.build_manifest();manifest_raw=wrapper.manifest_bytes(manifest)
 need(manifest_raw==(D/'deployment-manifest.json').read_bytes()==(P/'reviewed-manifest.json').read_bytes(),'exact regenerated/captured manifests')
 source_check={'schema':'dy-parent-offline-source-check-v1','accepted':True,'sourceFilesMatched':len(inv['files']),'manifestSha256':sha(manifest_raw),'payloadNames':sorted(payload),'targetOperations':0}
 need(source_check==j(DY/'source-check.json'),'reproduce parent source-check')
 ready,readyraw=wrapper.load_readiness(DY/'readiness-01/readiness.json',READY)
 need(readyraw==(P/'readiness-decision.json').read_bytes(),'same saved readiness bytes')
 for e in ready['evidence']:
  need(sha(Path(e['path']).read_bytes())==e['sha256'],'every readiness evidence reference '+e['path'])
 premise=(DY/'first-read-phase.md').read_bytes();need(sha(premise)==ready['closedWorldVendorOutLineage']['evidenceSha256']and premise.decode().strip()==ready['closedWorldVendorOutLineage']['statement'],'phase premise exact bytes')
 need(ready['identity']['devnum']=='60','USB60')
 metadata=j(DY/'readiness-01/metadata-root.json');need(len(metadata['calls'])==1,'one cached readiness request')
 meta=metadata['calls'][0];need(meta['command']=='set -eu\n'+wrapper.metadata_body(ready['identity'],'DY_CURRENT_READY'),'exact cached-only readiness command')
 text=call_check(meta);need(text==(DY/'readiness-01/metadata.txt').read_text(),'cached metadata saved stdout')
 census=wrapper.parse_metadata(text,'DY_CURRENT_READY');need(census==j(DY/'readiness-01/census-summary.json'),'cached census exact')
 receipt=(P/'native.receipt.json').read_bytes();native,raws,interpret=parser.parse_native(receipt.decode())
 need(interpret==j(P/'interpretation.json'),'exact strict interpretation')
 record=j(P/'record.json');result=j(P/'result.json')
 need(result['accepted']is True and result['cleanup']=='STAGE_ABSENT' and result['manifestSha256']==MAN and result['readinessSha256']==READY,'accepted exact wrapper result')
 need(record['manifestSha256']==MAN and record['readinessSha256']==READY and record['native_invocations']==1 and record['target_operations']==4 and record['no_retry']is True,'record one production invocation')
 need(record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','record exact cleanup')
 for tag in ('selftest','native'):
  envelope=(P/(tag+'-envelope.txt')).read_text()
  if tag=='native':need(envelope.startswith('IMMEDIATE_READY\n'),'immediate native metadata');envelope=envelope[len('IMMEDIATE_READY\n'):]
  terminal,private,stdout,stderr=wrapper.receipt_envelope(envelope)
  need(terminal==record[tag+'Terminal']and terminal['exit_code']==0,'recorded terminal '+tag)
  need(private==(P/(tag+'.receipt.json')).read_bytes()and stdout==(P/(tag+'.stdout')).read_bytes()and stderr==(P/(tag+'.stderr')).read_bytes()==b'','three-blob saved extents '+tag)
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'diagnostics separate '+tag)
  if tag=='selftest':need(wrapper.strict_json(private.decode())=={'selfTestsPassed':724,'targetOperations':0},'zero-IO724 selftest')
 for filename,b,h in raws:need(sha(b)==h and (P/filename).read_bytes()==b,'four saved raw payloads '+filename)
 need(record['retained_raw_files']==result['rawFiles']==[{'name':n,'bytes':len(b),'sha256':h}for n,b,h in raws],'exact saved raw file inventories')
 for label,key in [('PRE_READY','preCensus'),('BEFORE_INVOKE_READY','beforeInvokeCensus'),('POST_READY','postCensus')]:
  filename={'preCensus':'metadata-pre.txt','beforeInvokeCensus':'metadata-before-invoke.txt','postCensus':'metadata-post.txt'}[key]
  need(wrapper.parse_metadata((P/filename).read_text(),label)==record[key],'three cached census snapshots '+label)
 # Reproduce every generated command and every saved output with frozen wrapper + a no-I/O replay root.
 calls=record['calls'];need(len(calls)==27,'27 actual orchestration requests')
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
  need(replay.position==27 and res==result,'exact completed wrapper replay result')
  need({f.name for f in out.iterdir()}=={f.name for f in P.iterdir()},'same replayed artifact names')
  for f in out.iterdir():need(f.read_bytes()==(P/f.name).read_bytes(),'byte-exact generated saved artifact '+f.name)
 # Independently replay the parent predecessor without executing its exclusive-writing script.
 pred=j(DY/'predecessor-check.json')
 for e in pred['inputs']:need(sha(Path(e['path']).read_bytes())==e['sha256'],'predecessor source/raw pin')
 dm=module(B/'rtp-record-capture-20261028dm/parse-result.py','dy_predecessor_dm','fa2401bf270583fd793d44150b5db70915504c72e39878a8dd9f24a9be6446ca')
 pp=B/'volatile-limit-trial-20261028dk/dv-final-clean-01';pn,praw,pi=dm.parse_native((pp/'native.receipt.json').read_text());pr=j(pp/'result.json')
 need(pr['manifestSha256']=='e62b2906734a2814f2165749eb8ab230d5dd8e8dfd37f257ce5962ea20850c53'and pr['accepted']and pr['cleanup']=='STAGE_ABSENT'and pn['headersSent']==12 and pn['bulkTransfers']==24 and pn['protocolPhase']=='ReadyForHeader'and pn['released']and pn['closed'],'accepted known-phase predecessor')
 for name,b,h in praw:need((pp/name).read_bytes()==b and sha(b)==h,'predecessor actual raw '+name)
 need(pr['rawFiles']==[{'name':n,'bytes':len(b),'sha256':h}for n,b,h in praw],'predecessor raw declaration')
 rr=(pp/'start-R.bin').read_bytes();state=[struct.unpack_from('<H',rr,o)[0]for o in (0,10,14,0xc4)]
 need(rr==(pp/'end-R.bin').read_bytes()and state==[0,0,1,40],'predecessor clean40 stable R')
 expected_pred={'schema':'dy-offline-predecessor-check-v1','accepted':True,'headers':12,'bulks':24,'phase':'ReadyForHeader','released':True,'closed':True,'stageAbsent':True,'actualLimit':40,'rtState':[0,0,1],'targetOperations':0,'physicalPictureObserved':False,'endpointQueueProof':False,'inputs':[{'path':str(path),'sha256':sha(path.read_bytes())}for path in [B/'rtp-record-capture-20261028dm/parse-result.py',pp/'native.receipt.json',pp/'result.json',*[pp/name for name,_,_ in praw]]]}
 need(pred==expected_pred,'exact complete parent predecessor summary reproduction')
 need(ready['identity']==j(pp/'readiness-decision.json')['identity'],'predecessor same saved USB instance')
 # Independent selected-package/bank/header comparison; never print the actual instruction bytes.
 for name,pin in j(D/'dw-source-pins.json')['pins'].items():need(sha((W/name).read_bytes())==pin,'frozen DW source '+name)
 plan=j(W/'fixed-read-plan.json');need(sha((W/'fixed-read-plan.json').read_bytes())=='bd2c510523d41bb1e4dd5bd37a683f2b8066a8e69708a01e614464979763ceb2','DW plan pin')
 source=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(sha(source)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected package')
 samples=[]
 for i,(row,(filename,b,h))in enumerate(zip(plan['windows'],raws)):
  va=int(row['linkedVa'],16);off=int(row['fileOffset'],16);address=int(row['busAddress'],16)
  need(off==0x40200+va and address==0x46000000+va and va+16<=0x20000 and address%4==0,'image1 complete interval')
  need(b==source[off:off+16]and h==row['expectedSha256'],'actual exact selected bytes')
  need(struct.pack('<III',0x101,address,16).hex()==row['headerLittleEndianHex'],'independent target/address/count header')
  samples.append({'name':row['name'],'busAddress':row['busAddress'],'image':1,'linkedVa':row['linkedVa'],'fileOffset':row['fileOffset'],'bytes':16,'sha256':h,'headerLittleEndianHex':row['headerLittleEndianHex'],'readBracket':interpret['readBrackets'][row['name']]})
 # Negative tests use only cloned actual data, never mutate preserved inputs.
 for i in range(4):
  for at in range(16):
   bad=copy.deepcopy(native);w=bad['windows'][i];b=bytearray(base64.b64decode(w['base64']));b[at]^=1;w['base64']=base64.b64encode(b).decode();w['sha256']=sha(b);reject(lambda:parser.parse_native(json.dumps(bad)))
  bad=copy.deepcopy(native);bad['windows'][i]['address']-=0x02000000;reject(lambda:parser.parse_native(json.dumps(bad)))
 for flag in ('wholeRunningImageAttested','executableWriteQualified','atomicSnapshot','physicalPictureObserved'):
  bad=copy.deepcopy(native);bad[flag]=True;reject(lambda:parser.parse_native(json.dumps(bad)))
 for i in range(8):
  bad=copy.deepcopy(native);bad['steps'][i]['count']-=1;reject(lambda:parser.parse_native(json.dumps(bad)))
  bad=copy.deepcopy(native);bad['steps'][i]['before']='Unknown';reject(lambda:parser.parse_native(json.dumps(bad)))
 actual=(P/'native-envelope.txt').read_text()[len('IMMEDIATE_READY\n'):]
 for bad in (actual[:-1],actual+'extra', '[GC_INFO]\n'+actual):reject(lambda:wrapper.receipt_envelope(bad))
 for field,value in [('transport_exit',1),('host_timeout',True),('remote_timeout_seconds',44),('host_timeout_limit_seconds',74),('command_bytes',0)]:
  bad=copy.deepcopy(calls[0]);bad[field]=value;reject(lambda:call_check(bad))
 bad=copy.deepcopy(calls[0]);bad['response']['commands'][0]['command']+='\n';reject(lambda:call_check(bad))
 need(native['headersSent']==4 and native['bulkTransfers']==8 and native['writes']==native['uiOperations']==0 and native['released']and native['closed']and native['protocolPhase']=='ReadyForHeader','exact native transport result')
 need(result['nativeInvocations']==1 and result['retries']==result['wrapperUiOperations']==0 and result['wholeRunningImageAttested']is False and result['executableWriteQualified']is False,'narrow actual wrapper contract')
 return {'schema':'dy-code-fingerprint-live-analysis-v1','checks':checks,'manifestSha256':MAN,'readinessSha256':READY,'savedIdentity':ready['identity'],'samples':samples,'sampledBytes':64,'sampledCodeMatch':True,'nativeSteps':native['steps'],'bindingProofCount':len(native['bindingChecks']),'selftest':{'selfTestsPassed':724,'targetOperations':0},'diagnostics':{k:record[k]for k in ('selftestDiagnosticStdout','nativeDiagnosticStdout')},'sourceCheckReproduced':source_check,'predecessorCheckVerified':pred,'readinessCensus':census,'threeWrapperCensuses':{k:record[k]for k in ('preCensus','beforeInvokeCensus','postCensus')},'exactRootCommandReplay':{'calls':27,'maximumCommandBytes':max(c['command_bytes']for c in calls),'allSavedArtifactsByteExact':True,'noRealRootAdapterImported':True},'actualTransport':{'headers':4,'bulks':8,'nativeInvocations':1,'writes':0,'uiOperations':0,'retries':0,'terminalPhase':'ReadyForHeader','released':True,'closed':True,'cleanup':'STAGE_ABSENT'},'timing':{'firstHeaderBeforeUs':native['steps'][0]['beforeUs'],'lastDataAfterUs':native['steps'][-1]['afterUs'],'numericFullReadSpanUs':native['steps'][-1]['afterUs']-native['steps'][0]['beforeUs'],'scope':'full OUT-before/IN-after brackets; neither an instruction-fetch timestamp nor physical-light timestamp'},'negativeTestsPassed':negative_cases,'claims':{'sampledDmaReadReachabilityObserved':True,'exactFourLocationSelectedPackageIdentityObserved':True,'wholeBankDmaReachabilityProven':False,'activeInstructionFetchProven':False,'wholeRunningImageAttested':False,'executableWriteQualified':False,'scratchOwnershipQualified':False,'cacheCoherencyQualified':False,'hookInstallOrRollbackQualified':False,'physicalPictureObserved':False,'atomicSnapshot':False,'currentRtOrLimitResampledByProbe':False,'endpointQueueProof':False},'lineageScope':'Parent closed-world sole-vendor-OUT premise is byte-pinned and predecessor strict-replayed. Saved identities and bounded holder snapshots do not prove continuous absence of unrelated activity.'}

if __name__=='__main__':
 data=analyze();raw=json.dumps(data,indent=2,sort_keys=True)+'\n'
 if sys.argv[1:]==['--check']:need((HERE/'decoded.json').read_text()==raw,'exact frozen decoded artifact')
 elif not sys.argv[1:]:(HERE/'decoded.json').write_text(raw)
 else:raise SystemExit('usage: analyze.py [--check]')
 print(json.dumps({'accepted':True,'checks':checks,'decodedSha256':sha(raw.encode()),'sampledBytes':64,'sampledCodeMatch':True,'wholeRunningImageAttested':False,'executableWriteQualified':False,'hostOnly':True}))
