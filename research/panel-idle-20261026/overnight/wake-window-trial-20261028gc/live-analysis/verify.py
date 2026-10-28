#!/usr/bin/env python3
"""Frozen host-only GC/FZ receipt, command replay and stock-ring analysis. No live adapter."""
import base64,copy,hashlib,importlib.util,json,pathlib,re,struct,tempfile,types,sys
sys.dont_write_bytecode=True
D=pathlib.Path(__file__).resolve().parent; F=D.parent; B=F.parent; N=B/'combined-event-81-successor-20261028fz';P=F/'capture-01'
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=0
def need(v,s):
 global checks
 checks+=1
 if not v:raise ValueError(s)
def j(p):return json.loads(p.read_bytes())
def load(p):
 spec=importlib.util.spec_from_file_location('offline_'+p.stem.replace('-','_'),p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def pins():
 refs=j(D/'input-pins.json')['files']
 for r in refs:
  b=(B/r['path']).read_bytes();need(len(b)==r['bytes']and sha(b)==r['sha256'],'input pin '+r['path'])
 return len(refs)
def reject(fn,label):
 try:fn()
 except (ValueError,KeyError,TypeError,IndexError,struct.error):return
 raise ValueError('malformed accepted '+label)
def decode_row(raw,i,start):
 b=raw[i*58:(i+1)*58];u=lambda at:struct.unpack_from('<H',b,at)[0];v=lambda at:struct.unpack_from('<I',b,at)[0]
 return dict(cycle=i+1,startRt=b[0]>>4,endRt=b[0]&15,c7=b[1],startLimit=u(2),endLimit=u(4),h0=v(6),hHalf28=u(10),history=[u(k)for k in [12,14,16,18]],ordinalSlot0=v(20),hHeaderBeforeUs=start+v(24),hDataAfterUs=start+v(28),m4ca=u(32),m4a2=u(34),m4a4=u(36),m4c2=u(38),m4c4=u(40),r2460=u(42),r246e=u(44),pointer494=v(46),pointer498=v(50),r24ca=u(54),r2468=u(56))
def run():
 inputs=pins();w=load(N/'run-once.py');parser=load(N/'parse-result.py');text=(P/'native.receipt.json').read_text();n,rows,interpretation=parser.parse_native(text);record=j(P/'record.json');result=j(P/'result.json')
 admission=j(F/'fz-final-review-admission.json')
 for name,digest in admission['pins'].items():need(sha((N/name).read_bytes())==digest,'parent final admission source pin')
 need(admission['readinessSha256']==record['readinessSha256'] and admission['device']==n['device']==66,'parent admission instance/readiness binding')
 ui_text=(F/'post-capture-ui/before-snapshot.txt').read_text();saved_ui=j(F/'post-capture-ui/before-summary.json');tabs=[x for x in ui_text.splitlines()if x.startswith('memory/eden/current_tab')];need(tabs==['memory/eden/current_tab, value = d/ug.tab@Live (String)'],'separate cached Live row')
 need(saved_ui=={'cached_current_tab':'d/ug.tab@Live','csfs_window_present':'/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll'in ui_text,'screensaver_windows_present':any(x in ui_text for x in ['ScreenSaver.dll','ScreenSaverContent.dll']),'physical_picture_observed':False},'separate cached UI summary replay')
 need(n['accepted']and result['accepted']and interpretation==j(P/'interpretation.json'),'accepted original semantic result')
 need((n['headers'],n['bulks'],n['inputs'],n['writes'])==(628,1256,626,2),'exact accounting 77*8+12, two logger payloads')
 need(n['phase']=='ReadyForHeader'and n['released']and n['closed']and n['restore']=='readback-zero'and not n['loggerMayRemain']and n['terminal']=='TimeLimit','terminal/restoration')
 need(n['cleanCycles']==76 and n['quiescentCycles']==1 and n['rows']['count']==77,'76 Clean 1 Quiescent')
 man,payload=w.build_manifest();manifest=w.manifest_bytes(man);need(manifest==(N/'deployment-manifest.json').read_bytes()==(P/'reviewed-manifest.json').read_bytes(),'regenerated exact manifest')
 ready,rr=w.load_readiness(P/'readiness-decision.json',record['readinessSha256']);need(ready['identity']['devnum']=='66','bound device66')
 for r in ready['evidence']:need(sha(pathlib.Path(r['path']).read_bytes())==r['sha256'],'readiness evidence hash')
 calls=record['calls'];need(len(calls)==45,'45 root calls')
 for c in calls:
  r=c['response'];x=r['commands'];need(c['transport_exit']==0 and c['host_timeout']is False and c['transport_stderr']=={'data':'','encoding':'base64'}and r['authenticated']is True and r['uid']==r['euid']==0 and len(x)==1 and x[0]['command']==c['command']and x[0]['exit_code']==0 and x[0]['timed_out']is False and x[0]['stderr']=='','root transport/child exact success')
  need(c['command_bytes']==len(c['command'].encode())<=8192 and c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75,'root budgets')
  need(len(base64.b64decode(c['transport_stdout']['data']))<=65536 and json.loads(base64.b64decode(c['transport_stdout']['data']))==r,'bounded raw root transport JSON binding')
 for tag in ['selftest','native']:
  envelope=(P/(tag+'-envelope.txt')).read_text();xs=[c for c in calls if (' --receipt-self-test > 'if tag=='selftest'else' --execute --device ')in c['command']];need(len(xs)==1 and envelope==xs[0]['response']['commands'][0]['stdout'],'exclusive root envelope '+tag)
  if tag=='native':need(envelope.startswith('IMMEDIATE_READY\n'),'immediate identity metadata');envelope=envelope.removeprefix('IMMEDIATE_READY\n')
  term,receipt,stdout,stderr=w.receipt_envelope(envelope);need(term==record[tag+'Terminal']and term['exit_code']==0 and not stderr,'terminal '+tag)
  for suffix,data in [('receipt.json',receipt),('stdout',stdout),('stderr',stderr)]:need(data==(P/(tag+'.'+suffix)).read_bytes(),'saved exclusive blob '+tag+suffix)
  need(record[tag+'DiagnosticStdout']=={'bytes':len(stdout),'sha256':sha(stdout),'semanticReceipt':False},'separate GC stdout')
 baseline=(P/'baseline-ring.bin').read_bytes();post=(P/'post-ring.bin').read_bytes();ringmeta=parser.bind_rings(n,baseline,post);need(ringmeta==j(P/'ring-metadata.json'),'full sidecar binding')
 class Replay:
  at=0
  def root(self,command,rec,path):
   need(self.at<len(calls),'no extra command');c=calls[self.at];self.at+=1;need(command==c['command'],'byte-exact generated root command');rec['calls'].append(copy.deepcopy(c));w.save(path,rec);return c['response']['commands'][0]['stdout']
 cp=record['wakeCheckpoint'];clock=iter([cp['startedHostMonotonicNs'],cp['wakeBeforeHostMonotonicNs'],cp['wakeReturnedHostMonotonicNs'],cp['snapshots'][0]['queryBeforeHostMonotonicNs'],cp['snapshots'][0]['queryReturnedHostMonotonicNs'],cp['nativeCommandSubmitHostMonotonicNs']]);w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].rsplit('-',1)[-1]));replay=Replay();artifacts=0
 with tempfile.TemporaryDirectory(dir=D/'private',prefix='replay-')as tmp:
  out=pathlib.Path(tmp)/'capture';rep=w.execute(out,ready,rr,manifest,payload,replay,parser,clock=lambda:next(clock),sleeper=lambda _:need(False,'unexpected UI settle repeat'))
  need(rep==result and replay.at==45,'complete original accepted wrapper replay')
  for path in out.iterdir():need(path.read_bytes()==(P/path.name).read_bytes(),'byte-exact artifact '+path.name);artifacts+=1
 packed=parser.b64(n['rows']['rawBase64']);decoded=[decode_row(packed,i,n['startUs'])for i in range(77)];need(max(r['h0']for r in decoded)==36 and decoded[0]['h0']==decoded[-1]['h0']==0,'all-row max36 and endpoint0')
 retained=[]
 for cap in n['retained']:
  raws=parser.capture(cap);need(parser.pack_row(cap,raws,n['startUs'])==packed[(cap['cycle']-1)*58:cap['cycle']*58],'all58 retained fields bind');m,c=raws[1:3]
  retained.append(dict(m4a0=parser.half(m,0),ordinals=list(struct.unpack_from('<6I',raws[4])),sourceCounts=list(struct.unpack_from('<6H',raws[4],24)),rtStart=[parser.half(raws[0],k)for k in [0,10,14,0xc4,6]],rtEnd=[parser.half(raws[7],k)for k in [0,10,14,0xc4,6]],role=cap['role'],cycle=cap['cycle'],aa=parser.half(m,10),ac=parser.half(m,12),scan=m[56],c7=c[7],c8=c[8],root=struct.unpack_from('<I',m,64)[0],firstHeaderBeforeUs=cap['transfers'][0][4],lastDataAfterUs=cap['transfers'][-1][5],rawWindows=[dict(name=x['name'],bytes=len(b),sha256=sha(b))for x,b in zip(cap['windows'],raws)]))
 a=struct.unpack_from('<III',baseline);z=struct.unpack_from('<III',post);need(a==(5,5,0)and z==(2270,2270,0),'ring endpoint tuples')
 candidate=post[12+a[0]:12+z[0]];pattern=rb'\[RTP\s+(\d+)\]RGB:(\d+) x:\s*(\d+) y:\s*(\d+)/c:\s*(\d+)/diff:(\d+)/m:(\w+)\n';lines=candidate.splitlines(keepends=True);need(lines[:2]==[b'[RTP]END\n',b'[RTP:NORMAL][44]\n']and len(lines)==43,'candidate exact header/line count');tuples=[]
 for line in lines[2:]:
  match=re.fullmatch(pattern,line);need(match is not None,'exact stock row format');num=list(map(int,match.groups()[:6]));i,rgb,x,y,b,diff=num;tuples.append(dict(ordinal=i,rgb=rgb,x=x,y=y,b=b,diff=diff,mode=match[7].decode(),conditional12bitACandidates=[q for q in sorted(set([b-diff,b+diff]))if 0<=q<=4095]))
 need([t['ordinal']for t in tuples]==list(range(41))and all(t['y']==2159 and t['rgb']==0 for t in tuples),'41 ordered terminal-row-like RGB0 tuples')
 malformed=0
 for field,value in [('accepted',False),('phase','Unknown'),('headers',627),('bulks',1255),('inputs',625),('writes',1),('threshold',200),('cleanCycles',77),('quiescentCycles',0),('loggerMayRemain',True),('released',False),('closed',False)]:
  v=copy.deepcopy(n);v[field]=value
  def bad(v=v):
   nn,_,ii=parser.parse_native(json.dumps(v)+'\n');need(nn['accepted']and ii['accepted'],'mutation must remain accepted')
  reject(bad,field);malformed+=1
 for k in range(58):
  v=copy.deepcopy(n);vraw=bytearray(packed);vraw[76*58+k]^=1;v['rows']['rawBase64']=base64.b64encode(vraw).decode();v['rows']['sha256']=sha(vraw);reject(lambda:parser.parse_native(json.dumps(v)+'\n'),'retained field'+str(k));malformed+=1
 for tag,buf in [('baseline',baseline),('post',post)]:
  for kind in ['short','bitflip','bad-index']:
   altered=bytearray(buf)
   if kind=='short':altered=altered[:-1]
   elif kind=='bitflip':altered[-1]^=1
   else:struct.pack_into('<I',altered,0,15361)
   reject(lambda:parser.bind_rings(n,bytes(altered)if tag=='baseline'else baseline,bytes(altered)if tag=='post'else post),tag+kind);malformed+=1
 for delta in [-1,0,1]:
  v=copy.deepcopy(n);witness=interpretation['keyExposure']['witnessOptionalRHeader']['headerBeforeUs'];v['intervention']['calls'][0]['beforeUs']=witness+delta;ex=parser.key_exposure(v);need(ex['keyExposureQualified']==(delta<0 or any(c['headerBeforeUs']>witness+delta for c in ex['candidateOptionalRHeaders'])),'strict later optional header boundary')
 for tag,buf in [('baseline',baseline),('post',post)]:
  v=copy.deepcopy(n);altered=bytearray(buf);struct.pack_into('<I',altered,0,15361);v[tag+'Ring']['sha256']=sha(altered)
  reject(lambda:parser.bind_rings(v,bytes(altered)if tag=='baseline'else baseline,bytes(altered)if tag=='post'else post),'rehash cursor bound');malformed+=1
 reject(lambda:parser.parse_native(text.replace('{','{\"accepted\":true,',1)),'duplicate key');malformed+=1
 asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();im=asset[0x40200:0x60200];need(len(asset)==0x500000 and sha(asset)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','known selected source identity')
 need(im[0xbb48:0xbb55]==b'[RTP:%s][%d]\n'and struct.unpack_from('<I',im,0xbaf4)[0]==0x200004a0,'header literal/counter source')
 for at,hexbytes in [(0xbab0,'0288'),(0xbab2,'3146'),(0xbabe,'401c'),(0xbac2,'0880'),(0xc5d4,'0746'),(0xc5d6,'0e46'),(0xc5d8,'9046'),(0xc5da,'9946'),(0xc604,'6bd8')]:need(im[at:at+len(bytes.fromhex(hexbytes))]==bytes.fromhex(hexbytes),'source anchor '+hex(at))
 sourceSpans=[dict(image=1,va=hex(a),fileOffset=hex(a+0x40200),bytes=size,sha256=sha(im[a:a+size]))for a,size in [(0xb9f4,0xc0),(0x1b72c,0x28),(0xc5d0,0x150),(0xc858,0x30)]]
 fields=['startRt','endRt','c7','h0','hHalf28','history','ordinalSlot0','m4ca','m4a2','m4a4','m4c2','m4c4','r2460','r246e','r24ca','r2468','pointer494','pointer498'];runs={}
 for field in fields:
  seq=[]
  for row in decoded:
   if not seq or seq[-1]['value']!=row[field]:seq.append({'firstCycle':row['cycle'],'lastCycle':row['cycle'],'value':row[field]})
   else:seq[-1]['lastCycle']=row['cycle']
  runs[field]=seq
 gaps=[decoded[i]['hHeaderBeforeUs']-decoded[i-1]['hHeaderBeforeUs']for i in range(1,len(decoded))]
 outside=post[12:12+a[0]]+post[12+z[0]:];oldoutside=baseline[12:12+a[0]]+baseline[12+z[0]:]
 return dict(schema='gc-independent-accepted-capture-analysis-v1',nativeAccepted=True,wrapperAccepted=True,phase=n['phase'],released=n['released'],closed=n['closed'],cleanup=result['cleanup'],headers=628,bulks=1256,readPairs=626,loggerPayloadPairs=2,thresholdWrites=0,terminal=n['terminal'],nativeStartUs=n['startUs'],nativeEndUs=n['endUs'],nativeDurationUs=n['endUs']-n['startUs'],cleanCycles=76,quiescentCycles=1,maximumSampledH0=max(r['h0']for r in decoded),sourceSpans=sourceSpans,controlBrackets=[dict(role=c['role'],headerBeforeUs=c['transfers'][0][4],dataAfterUs=c['transfers'][-1][5])for c in n['controls']],ringReadBrackets=[dict(role=role,headerBeforeUs=n[role]['transfer']['transfers'][0][4],dataAfterUs=n[role]['transfer']['transfers'][-1][5])for role in ['baselineRing','postRing']],rows=decoded,fieldRuns=runs,hHeaderSpacingUs={'min':min(gaps),'max':max(gaps),'median':sorted(gaps)[len(gaps)//2]},retained=retained,key=n['intervention'],keyExposure=interpretation['keyExposure'],ring=dict(baseline=dict(bytes=len(baseline),sha256=sha(baseline),tuple=list(a)),post=dict(bytes=len(post),sha256=sha(post),tuple=list(z)),endpointCandidateBytes=len(candidate),endpointCandidateSha256=sha(candidate),dataBytesDifferent=sum(x!=y for x,y in zip(baseline[12:],post[12:])),outsideCandidateDataUnchanged=outside==oldoutside,candidateHeader=dict(mode='NORMAL',numeric=44,numericSource='u16 CPU200004a0, pre-increment bounded stock counter; not FP'),candidateRows=tuples,rtpActOccurrencesFullBaseline=baseline[12:].lower().count(b'rtp_act'),rtpActOccurrencesFullPost=post[12:].lower().count(b'rtp_act'),rtSpacePactOccurrencesFullBaseline=baseline[12:].lower().count(b'rt p_act'),rtSpacePactOccurrencesFullPost=post[12:].lower().count(b'rt p_act'),candidatePreamble='[RTP]END',chronologicalDeltaProven=False,noWrapProven=False,recordEpochProven=False),uiAfter=j(F/'post-capture-ui/before-summary.json'),rootCallsReplayed=replay.at,generatedArtifactsByteExact=artifacts,maxRootCommandBytes=max(c['command_bytes']for c in calls),maxRawTransportBytes=max(len(base64.b64decode(c['transport_stdout']['data']))for c in calls),inputFilesVerified=inputs,malformedRefusals=malformed,checksPassed=checks,physicalPictureObserved=False,executingPcProven=False,actualFpProven=False,rootCauseEstablished=False,targetOperations=0,networkOperations=0)
if __name__=='__main__':
 value=run();raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
 if '--write' in sys.argv:(D/'decoded.json').write_bytes(raw)
 else:need(raw==(D/'decoded.json').read_bytes(),'derived summary exact')
 print(json.dumps({k:value[k]for k in ['checksPassed','inputFilesVerified','rootCallsReplayed','generatedArtifactsByteExact','malformedRefusals','maxRootCommandBytes']},sort_keys=True))
