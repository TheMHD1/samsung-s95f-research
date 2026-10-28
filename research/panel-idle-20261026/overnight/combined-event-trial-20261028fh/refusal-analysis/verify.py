#!/usr/bin/env python3
"""Offline FH rejection classifier and exact saved-response wrapper replay. No target I/O."""
import base64,copy,hashlib,json,pathlib,struct,sys,tempfile,types
sys.dont_write_bytecode=True
D=pathlib.Path(__file__).resolve().parent;F=D.parent;B=F.parent;G=B/'combined-event-checkpoints-20261028fg';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def j(p):return json.loads(p.read_bytes())
def load(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def pins():
 rows=j(D/'input-pins.json')['files']
 for f in rows:
  p=B/f['path'];raw=p.read_bytes();need(len(raw)==f['bytes']and sha(raw)==f['sha256'],'pinned input '+f['path'])
 return len(rows)
def classify(n,parser):
 need(n['accepted']is False and n['observationComplete']is False,'original refusal preserved')
 need(n['phase']=='ReadyForHeader'and all(n[k]is True for k in ['bindingQualified','opened','claimed','released','closed']),'native known closed ownership')
 need(n['device']==65 and n['terminal']=='Refused'and n['error']=='InvalidOperationException: C geometry/category/selector','exact semantic refusal')
 need(n['cleanupError']=='no new header permitted: ambiguity, clock failure, or prior error','documented skipped cleanup')
 for k,v in [('headers',158),('bulks',316),('inputs',157),('writes',1),('retries',0),('threshold',40),('cyclesStarted',19),('cleanCycles',18),('quiescentCycles',0)]:need(type(n[k])is int and n[k]==v,'exact native '+k)
 need(n['arm']=='readback-one'and n['armAttempted']is True and n['restore']=='not-attempted'and n['restoreAttempted']is False and n['loggerMayRemain']is True,'logger unresolved, no restore')
 need(all(type(n[k])is int for k in ['startUs','endUs','wholeDeadlineUs','observationDeadlineUs'])and n['startUs']<=n['endUs']<=n['wholeDeadlineUs']==n['startUs']+40000000,'native clock extent')
 need([c['role']for c in n['controls']]==['prearm-R','prearm-M','prearm-C','arm','armed-R'],'five control pairs only')
 raws={};extracted=[]
 for i,c in enumerate(n['controls']):
  data=parser.capture(c)
  if c['role']=='arm':need(c['windows']==[]and[c['transfers'][z][:3]for z in range(2)]==[['OUT',12,12],['OUT',2,2]],'one fixed arm pair')
  else:need(len(data)==1 and c['windows'][0]['name']==c['role'].split('-')[-1],'control map');raws[c['role']]=data[0];extracted.append((f'control-{i:02}-{c["role"]}.bin',data[0]))
 parser.logger(raws['prearm-R'],0);parser.logger(raws['armed-R'],1);parser.context(raws['prearm-M'],raws['prearm-C'],True)
 need(parser.rt(raws['prearm-R'])==parser.rt(raws['armed-R'])==0,'clean prearm/readback')
 need([(c['role'],c['cycle'])for c in n['retained']]==[('trigger-baseline',1),('last-complete',18),('current',19)],'retained cycles')
 packed=parser.b64(n['rows']['rawBase64']);need(n['rows']['count']==18 and len(packed)==18*58 and sha(packed)==n['rows']['sha256'],'published rows count/hash')
 for z in range(18):need(packed[z*58]==0 and struct.unpack_from('<HH',packed,z*58+2)==(40,40),'published clean40 rows')
 for slot,c in enumerate(n['retained']):
  data=parser.capture(c);need([w['name']for w in c['windows']]==parser.CYCLE and len(c['transfers'])==16,'retained complete fixed eight-pair map')
  raws[c['role']]=data
  for w,d in zip(c['windows'],data):extracted.append((f'retained-{slot:02}-cycle{c["cycle"]:03}-{len(extracted):02}-{w["name"]}.bin',d))
  for r in [data[0],data[7]]:parser.logger(r,1)
  if c['cycle']<19:parser.context(data[1],data[2],c['cycle']==1);need(parser.pack_row(c,data,n['startUs'])==packed[(c['cycle']-1)*58:c['cycle']*58],'all58 bytes retained published row')
 last=raws['last-complete'];cur=raws['current'];diff=[i for i in range(16)if last[2][i]!=cur[2][i]]
 need(diff==[7,8]and last[2][7:9]==bytes([0,3])and cur[2][7:9]==bytes([1,0]),'C7/C8 exact transition')
 need(cur[2][:7]==last[2][:7]and cur[2][9:]==last[2][9:]and cur[1][56]==1,'other C bytes stable and scan1')
 need(struct.unpack_from('<I',cur[1],64)[0]==0x20010000 and struct.unpack_from('<HH',cur[1],10)==(0,2),'current root/AA/AC')
 need(parser.rt(cur[0])==parser.rt(cur[7])==3,'current complete unpublished Quiescent set')
 need(n['baselineRing']['complete']is True and n['baselineRing']['bytes']==15372,'baseline ring complete')
 t=n['baselineRing']['transfer']['transfers'];need(len(t)==2 and[t[i][:3]for i in range(2)]==[['OUT',12,12],['IN',15372,15372]]and all(x[3]==0 and x[6]is None for x in t),'baseline ring exact pair')
 post=n['postRing'];need(post['complete']is False and post['bytes']==0 and post['sha256']==sha(b'')and post['transfer']['windows']==post['transfer']['transfers']==[],'no post-ring header')
 key=n['intervention'];need(key['key']=='Left'and key['attempted']is True and key['completed']is True and 'error'not in key and[x['phase']for x in key['calls']]==['down','up'],'one completed Left')
 previous=key['armedUs'];need(n['retained'][0]['transfers'][-1][5]<=previous,'key follows baseline')
 for x in key['calls']:need(x['started']is True and x['reaped']is True and x['timedOut']is False and type(x['exitCode'])is int and x['exitCode']==0 and 'error'not in x and previous<=x['beforeUs']<=x['afterUs']<=key['endUs']<=n['endUs'],'key child/times');previous=x['afterUs']
 need(1+3+1+1+19*8==n['headers']and 5+19*8==n['inputs']and n['headers']+n['inputs']+n['writes']==n['bulks'],'source pair accounting')
 return raws,extracted

def run():
 count=pins();p=F/'capture-01';w=load(G/'run-once.py');parser=load(G/'parse-result.py');n,rows,q=parser.parse_native((p/'native.receipt.json').read_text());raws,extracted=classify(n,parser);record=j(p/'record.json')
 man,payload=w.build_manifest();manifest=w.manifest_bytes(man);need(manifest==(G/'deployment-manifest.json').read_bytes()==(p/'reviewed-manifest.json').read_bytes(),'exact regenerated/captured manifest')
 ready,rr=w.load_readiness(p/'readiness-decision.json',record['readinessSha256']);need(ready['identity']['devnum']=='65','same device readiness')
 for ref in ready['evidence']:need(sha(pathlib.Path(ref['path']).read_bytes())==ref['sha256'],'readiness evidence')
 need(q==j(p/'interpretation.json')and q['accepted']is False and q['terminalKnownPhase']is True,'native parse refusal interpretation')
 for tag,rc in [('selftest',0),('native',1)]:
  text=(p/(tag+'-envelope.txt')).read_text();matches=[c for c in record['calls']if (' --receipt-self-test > 'if tag=='selftest'else' --execute --device ')in c['command']];need(len(matches)==1 and text==matches[0]['response']['commands'][0]['stdout'],'root-bound '+tag+' envelope')
  if tag=='native':need(text.startswith('IMMEDIATE_READY\n'),'immediate metadata');text=text.removeprefix('IMMEDIATE_READY\n')
  term,receipt,stdout,stderr=w.receipt_envelope(text);need(term==record[tag+'Terminal']and term['exit_code']==rc and stderr==b'','terminal '+tag)
  for suffix,data in [('receipt.json',receipt),('stdout',stdout),('stderr',stderr)]:need(data==(p/(tag+'.'+suffix)).read_bytes(),'exclusive saved blob')
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'diagnostic separate')
  if tag=='selftest':need(json.loads(receipt)=={'smokeTestsPassed':8,'targetOperations':0},'zero I/O smoke')
 for label,name in [('baselineRing','baseline-ring.bin'),('postRing','post-ring.bin')]:
  data=(p/name).read_bytes();need(len(data)==n[label]['bytes']and sha(data)==n[label]['sha256'],'sidecar metadata binding')
 need(len((p/'baseline-ring.bin').read_bytes())==15372 and (p/'post-ring.bin').read_bytes()==b'','actual full/empty ring files')
 need(record['cleanup_required']is True and record['native_invocations']==1 and record['target_operations']is None and record['target_operations_status']=='inflight_or_unknown'and not(p/'result.json').exists(),'original wrapper rejection retained')
 calls=record['calls'];need(len(calls)==41,'root ledger count')
 for c in calls:
  a=c['response'];t=a['commands'];need(type(c['transport_exit'])is int and c['transport_exit']==0 and c['host_timeout']is False and c['transport_stderr']=={'data':'','encoding':'base64'}and a['authenticated']is True and a['uid']==a['euid']==0 and len(t)==1 and t[0]['command']==c['command']and type(t[0]['exit_code'])is int and t[0]['exit_code']==0 and t[0]['timed_out']is False and t[0]['stderr']=='','root transport/child')
  need(c['command_bytes']==len(c['command'].encode())<=8192,'command exact size')
 class Replay:
  at=0
  def root(self,command,rec,path):
   need(self.at<len(calls),'no extra root request');c=calls[self.at];self.at+=1;need(command==c['command'],'exact generated root command');rec['calls'].append(copy.deepcopy(c));w.save(path,rec);return c['response']['commands'][0]['stdout']
 checkpoint=record['wakeCheckpoint'];clock=iter([checkpoint['startedHostMonotonicNs'],checkpoint['wakeBeforeHostMonotonicNs'],checkpoint['wakeReturnedHostMonotonicNs'],checkpoint['snapshots'][0]['queryBeforeHostMonotonicNs'],checkpoint['snapshots'][0]['queryReturnedHostMonotonicNs'],checkpoint['nativeCommandSubmitHostMonotonicNs']]);w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].rsplit('-',1)[-1]));replay=Replay();artifacts=0
 with tempfile.TemporaryDirectory(prefix='exact-wrapper-',dir=D/'private')as tmp:
  out=pathlib.Path(tmp)/'capture';reason=None
  try:w.execute(out,ready,rr,manifest,payload,replay,parser,clock=lambda:next(clock),sleeper=lambda _:need(False,'unexpected settle sleep'))
  except ValueError as exc:reason=str(exc)
  need(reason=='complete ring'and replay.at==41,'original rejection reproduced after exact41calls')
  for path in out.iterdir():need(path.read_bytes()==(p/path.name).read_bytes(),'exact generated artifact '+path.name);artifacts+=1
 need(w.load_pinned(G/'wake-check.py',w.WAKE_SHA,'wake').validate(p,checkpoint)['accepted'],'strict visible wake checkpoint')
 malformed=0
 for field,value in [('accepted',True),('phase','Unknown'),('headers',157),('bulks',315),('inputs',156),('restoreAttempted',True),('loggerMayRemain',False)]:
  z=copy.deepcopy(n);z[field]=value
  try:classify(z,parser)
  except (ValueError,KeyError,TypeError):malformed+=1
  else:raise ValueError('malformed accepted '+field)
 for kind in ['short-final-IN','wrong-C8']:
  z=copy.deepcopy(n)
  if kind=='short-final-IN':z['retained'][-1]['transfers'][-1][2]=255
  else:
   d=bytearray(parser.b64(z['retained'][-1]['windows'][2]['raw']));d[8]=4;z['retained'][-1]['windows'][2]['raw']=base64.b64encode(d).decode()
  try:classify(z,parser)
  except (ValueError,KeyError,TypeError):malformed+=1
  else:raise ValueError('malformed accepted '+kind)
 fl=B/'logger-context-transient-20261028fl';source=j(fl/'source-audit.json');need(sha((fl/'source-audit.json').read_bytes())=='804cf3e296660bc398d14061eadc8ff2db62c2621a67ad74c43fee1e4a44b083','FL source audit pin');asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(sha(asset)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected source asset')
 for span in source['source_spans']:
  at=int(span['file_offset'],16);va=int(span['va'],16);end=int(span['end_exclusive'],16);need(at==va+(0x40200 if span['image']==1 else 0x200)and sha(asset[at:at+end-va])==span['sha256'],'FL mapped source span '+span['role'])
 need(source['source_supports_restore_only_c8_zero']is True and source['zero_requires_reset']is False and source['global_value_domain_complete']is False,'bounded source zero witness, no global exclusivity')
 pins();summary={'schema':'fh-independent-semantic-refusal-analysis-v1','originalNativeAccepted':False,'originalWrapperAccepted':False,'nativeTerminalPhase':'ReadyForHeader','released':True,'closed':True,'loggerMayRemain':True,'restoreAttempted':False,'thresholdWrites':0,'device':65,'headers':158,'bulks':316,'matchedInputs':157,'loggerPayloads':1,'publishedCleanRows':18,'currentCompleteUnpublishedQuiescentCycle':19,'currentCChangedOffsets':[7,8],'currentC7':1,'currentC8':0,'lastCompleteC7':0,'lastCompleteC8':3,'currentScan':raws['current'][1][56],'sourceAccountedPairs':158,'fullPairRecordsRetained':30,'pairsNotIndividuallyRetained':128,'wrapperFailure':'complete ring: post-ring sidecar is correctly empty because no post-ring read was attempted','rootCallsReplayed':41,'generatedArtifactsByteExact':artifacts,'scientificOrRecoveryAdmissionGranted':False,'sourceAlternateCAdmission':'FL positively source-qualifies stock zero and independent C7/C8 copies; no actual writer invocation or FG guard relaxation; FM is separate','sourceC8ZeroCompatible':True,'sourcePositiveValuesNotComplete':[0,1,2,3,4],'sourceAuditSha256':sha((fl/'source-audit.json').read_bytes()),'nativeStartUs':n['startUs'],'nativeEndUs':n['endUs'],'durationUs':n['endUs']-n['startUs'],'rawFiles':[{'name':name,'bytes':len(data),'sha256':sha(data)}for name,data in extracted],'inputFilesVerified':count,'malformedRefusals':malformed,'checksPassed':checks,'targetOperations':0,'rootCalls':0,'networkOperations':0}
 return summary,extracted
if __name__=='__main__':
 result,extracted=run();raw=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
 if sys.argv[1:]==['--write']:
  (D/'decoded.json').write_bytes(raw)
  for name,data in extracted:(D/'private'/name).write_bytes(data)
 else:
  need((D/'decoded.json').read_bytes()==raw,'exact decoded replay')
  for name,data in extracted:need((D/'private'/name).read_bytes()==data,'exact extracted raw')
 print(json.dumps({'acceptedAsRefusalClassification':True,'nativeAccepted':False,'wrapperAccepted':False,'checksPassed':checks,'inputFilesVerified':result['inputFilesVerified'],'malformedRefusals':result['malformedRefusals'],'decodedSha256':sha(raw),'targetOperations':0,'rootCalls':0,'networkOperations':0}))
