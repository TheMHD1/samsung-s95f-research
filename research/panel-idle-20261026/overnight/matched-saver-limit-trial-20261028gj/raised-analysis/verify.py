#!/usr/bin/env python3
"""GJ actual raised-leg reconstruction only. No root transport/native entrypoint."""
import base64,copy,hashlib,json,re,statistics,struct,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;T=D.parent;B=T.parent;checks=0;negative=0
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def reject(fn):
 global negative
 try:fn()
 except(ValueError,TypeError,KeyError,IndexError,struct.error):negative+=1;return
 raise ValueError('malformed clone unexpectedly accepted')
def j(p):return json.loads(p.read_bytes())
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def load(p):
 m=types.ModuleType('offline_'+p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def half(b,i):return struct.unpack_from('<H',b,i)[0]
def word(b,i):return struct.unpack_from('<I',b,i)[0]
def pincheck():
 rows=j(D/'input-pins.json')['files']
 for r in rows:
  raw=(B/r['path']).read_bytes();need(len(raw)==r['bytes']and sha(raw)==r['sha256'],'input pin '+r['path'])
 return len(rows)
def audit(calls):
 need(type(calls)is list and bool(calls),'actual root ledger')
 for c in calls:
  a=c['response'];rows=a['commands'];need(type(c['transport_exit'])is int and c['transport_exit']==0 and c['host_timeout']is False and c['transport_stderr']=={'encoding':'base64','data':''},'root transport success')
  need(a['authenticated']is True and type(a['uid'])is type(a['euid'])is int and a['uid']==a['euid']==0 and a['model']=='QN77S95FAFXZC'and len(rows)==1,'authenticated model/root child')
  q=rows[0];need(q['command']==c['command']and type(q['exit_code'])is int and q['exit_code']==0 and q['timed_out']is False and q['stderr']=='','exact successful command echo')
  raw=base64.b64decode(c['transport_stdout']['data'],validate=True);need(base64.b64encode(raw).decode()==c['transport_stdout']['data']and json.loads(raw)==a and len(raw)<=65536 and len(q['stdout'].encode())<=65536,'raw transport/response binding and caps')
  need(type(c['command_bytes'])is int and c['command_bytes']==len(c['command'].encode())<=8192 and c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75 and c['started_utc']<=c['finished_utc'],'command extent/deadlines/time')
class Replay:
 def __init__(self,calls):self.calls=calls;self.at=0
 def root(self,command,rec,path):
  need(self.at<len(self.calls),'no extra replay request');c=self.calls[self.at];self.at+=1;need(command==c['command'],'exact generated source command');rec['calls'].append(copy.deepcopy(c));save(path,rec);return c['response']['commands'][0]['stdout']
FAMILIES={'set-01':'selective-endpoint-limit-writer-20261028fa','raised-capture-01':'live-saver-200-recorder-20261028gg','raised-post-capture':'rtp-lane-gate-capture-20261028eb'}
def replay(role):
 p=T/role;f=B/FAMILIES[role];w=load(f/'run-once.py');parser=load(f/'parse-result.py');rec=j(p/'record.json');result=j(p/'result.json');audit(rec['calls'])
 manifest,payload=w.build_manifest();mr=w.manifest_bytes(manifest);need(mr==(p/'reviewed-manifest.json').read_bytes()==(f/'deployment-manifest.json').read_bytes()and sha(mr)==result['manifestSha256'],'full frozen manifest '+role)
 ready,rr=w.load_readiness(p/'readiness-decision.json',result['readinessSha256']);need(ready['identity']==j(T/'identity-02/identity.json')and ready['identity']['devnum']=='68'and len(ready['identity'])==16,'all16 same USB68 identity fields')
 for row in ready['evidence']:need(sha(Path(row['path']).read_bytes())==row['sha256'],'saved phase/evidence bytes')
 for tag in ['selftest','native']:
  text=(p/(tag+'-envelope.txt')).read_text();matches=[c for c in rec['calls']if (' --receipt-self-test > 'if tag=='selftest'else' --execute')in c['command']];need(len(matches)==1 and matches[0]['response']['commands'][0]['stdout']==text,'one native/selftest source envelope')
  if tag=='native':need(text.startswith('IMMEDIATE_READY\n'),'immediate identity');text=text[len('IMMEDIATE_READY\n'):]
  term,receipt,out,err=w.receipt_envelope(text);need(term==rec[tag+'Terminal']and term['exit_code']==0 and err==b'','three-blob terminal framing')
  for suffix,raw in [('receipt.json',receipt),('stdout',out),('stderr',err)]:need((p/(tag+'.'+suffix)).read_bytes()==raw,'saved exclusive/diagnostic blob')
  need(rec[tag+'DiagnosticStdout']=={'bytes':len(out),'sha256':sha(out),'semanticReceipt':False},'opaque diagnostic stdout')
 need(result['accepted']is True and result['nativeInvocations']==1 and result['retries']==0 and result['cleanup']=='STAGE_ABSENT'and rec['native_invocations']==1 and rec['no_retry']is True and rec['cleanup_required']is False and rec['cleanup_stdout']=='STAGE_ABSENT\n','one accepted attempt and cleanup')
 w.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=rec['remote_stage'].rsplit('-',1)[-1]));root=Replay(rec['calls']);kw={};extra=[]
 if role=='set-01':extra=['set']
 if role=='raised-capture-01':
  cp=rec['cachedCheckpoint'];c=cp['snapshots'][0];clock=iter([cp['startedHostMonotonicNs'],c['queryBeforeHostMonotonicNs'],c['queryReturnedHostMonotonicNs'],cp['nativeCommandSubmitHostMonotonicNs']]);kw={'clock':lambda:next(clock),'sleeper':lambda _:need(False,'unexpected extra settle')}
 scratch=D/'private';scratch.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='actual-replay-',dir=scratch)as tmp:
  out=Path(tmp)/'capture';observed=w.execute(out,ready,rr,mr,payload,root,parser,*extra,**kw);need(root.at==len(rec['calls'])and observed==result,'all actual requests replayed')
  need({x.name for x in out.iterdir()}=={x.name for x in p.iterdir()},'complete exact artifact set')
  artifacts=0
  for x in out.iterdir():need(x.read_bytes()==(p/x.name).read_bytes(),'byte-exact replay artifact '+x.name);artifacts+=1
 parsed=parser.parse_native((p/'native.receipt.json').read_text());native=parsed[0];phase=native['phase']if role=='raised-capture-01'else native['protocolPhase'];need(native['accepted']and phase=='ReadyForHeader'and native['released']and native['closed'],'native ready/released/closed')
 return native,parsed,parser,rec,{'commands':root.at,'artifacts':artifacts,'maxCommandBytes':max(c['command_bytes']for c in rec['calls']),'manifestSha256':sha(mr),'readinessSha256':sha(rr),'identity':ready['identity'],'allArtifactsByteExact':True}
def raw_inventory(p,parsed,rec):
 rawfiles=parsed[1];result=j(p/'result.json');inventory=[];out={}
 for name,raw,digest in rawfiles:need(sha(raw)==digest and (p/name).read_bytes()==raw,'every retained raw binding');inventory.append({'name':name,'bytes':len(raw),'sha256':digest});out[name]=raw
 need(result['rawFiles']==rec['retained_raw_files']==inventory,'complete raw inventory');return out

def decode58(raw,i,start):
 b=raw[i*58:(i+1)*58];h=lambda at:half(b,at);u=lambda at:word(b,at)
 return dict(cycle=i+1,startRt=b[0]>>4,endRt=b[0]&15,c7=b[1],startLimit=h(2),endLimit=h(4),h0=u(6),h0Low16=u(6)&65535,q0=h(10),history=[h(k)for k in [12,14,16,18]],ordinal=u(20),hHeaderBeforeUs=start+u(24),hDataAfterUs=start+u(28),publicationBound=h(32),m4a2=h(34),m4a4=h(36),m4c2=h(38),m4c4=h(40),r2460=h(42),r246e=h(44),dynamicAPointer=u(46),dynamicBPointer=u(50),r24ca=h(54),r2468=h(56))
def run():
 count=pincheck();a,ap,fa,ar,ars=replay('set-01');n,np,gp,nr,nrs=replay('raised-capture-01');e,ep,eb,er,ers=replay('raised-post-capture');arsraw=raw_inventory(T/'set-01',ap,ar);post=raw_inventory(T/'raised-post-capture',ep,er)
 need(a['headersSent']==7 and a['bulkTransfers']==14 and a['writeAttempted']and a['writeTransportComplete']and a['readbackVerified']and not a['limitMayHaveChanged'],'exact fixed FA set outcome')
 r0,rf,r1=[arsraw[x]for x in ['baseline-R.bin','fresh-R.bin','readback-R.bin']];need([half(x,196)for x in [r0,rf,r1]]==[40,40,200]and [i for i in range(256)if rf[i]!=r1[i]]==[196],'actual two-byte action/readback changed only c4 lowbyte')
 fa.validate_candidate_context(arsraw['pre-M.bin'],arsraw['pre-C.bin'],r0);fa.validate_transaction_pair(rf,r1,40,200,fa.PROFILE);need(True,'exact selective endpoint profile/thermal pair')
 writer={'baselineThermal':{str(i):half(r0,i)for i in [0x20,0x98,0xbc,0xac]},'freshThermal':{str(i):half(rf,i)for i in [0x20,0x98,0xbc,0xac]},'readbackThermal':{str(i):half(r1,i)for i in [0x20,0x98,0xbc,0xac]},'observedFreshReadbackByteDifferences':[196],'headers':7,'bulks':14,'rawFiles':6,'readbackLimit':200,'automaticRestore':False}
 need(np[2]==j(T/'raised-capture-01/interpretation.json'),'saved GG interpretation')
 need(n['rows']['count']==56 and n['cleanCycles']==55 and n['quiescentCycles']==1 and n['terminal']=='CycleLimit'and (n['headers'],n['inputs'],n['bulks'],n['writes'])==(460,458,920,2),'56 cycles plus twelve control pairs')
 need(n['restore']=='readback-zero'and n['loggerMayRemain']is False and n['threshold']==200,'logger restored under fixed200')
 packed=gp.b64(n['rows']['rawBase64']);need(len(packed)==56*58 and sha(packed)==n['rows']['sha256'],'complete58-byte rows');rows=[decode58(packed,i,n['startUs'])for i in range(56)]
 need(all(x['startLimit']==x['endLimit']==200 for x in rows),'every compact limit200');need(sum(x['startRt']==x['endRt']==0 for x in rows)==55 and [(x['cycle'],x['startRt'],x['endRt'])for x in rows if x['startRt']or x['endRt']]==[(16,3,3)],'exact Q cycle16, no sampled fault')
 need(max(x['h0']for x in rows)==36 and not any(x['h0Low16']>40 for x in rows),'no sampled above40 witness')
 retained=[]
 for cap in n['retained']:
  buf=gp.capture(cap);need(gp.pack_row(cap,buf,n['startUs'])==packed[(cap['cycle']-1)*58:cap['cycle']*58],'retained full58-byte binding');m,c=buf[1:3]
  retained.append({'role':cap['role'],'cycle':cap['cycle'],'aa':half(m,10),'ac':half(m,12),'scan':m[56],'root':word(m,64),'c7':c[7],'c8':c[8],'invocationCounter':half(m,0),'startR':[half(buf[0],i)for i in [0,6,10,14,196]],'endR':[half(buf[7],i)for i in [0,6,10,14,196]],'sourceCounts':list(struct.unpack_from('<6H',buf[4],24)),'readBrackets':[{'name':z['name'],'headerBeforeUs':cap['transfers'][2*i][4],'inputAfterUs':cap['transfers'][2*i+1][5],'bytes':len(buf[i]),'sha256':sha(buf[i])}for i,z in enumerate(cap['windows'])]})
 need(all(x['aa']==0 and x['ac']==2 and x['scan']==1 and x['root']==0x20010000 and x['c8']==3 for x in retained),'full retained source context')
 cp=nr['cachedCheckpoint'];cached=load(B/'live-saver-200-recorder-20261028gg/cached-check.py');need(cached.validate(T/'raised-capture-01',cp)['accepted']and cp['hostSubmissionAgeNs']==6779603 and cp['acceptedSnapshotIndex']==1,'one cached Live+saver checkpoint/6.779603ms age')
 need(nr['wrapperUiOperations']==0 and not any('input_keyevent'in c['command']for c in nr['calls']),'zero wrapper keys')
 key=n['intervention'];need(key['key']=='Left'and key['attempted']and key['completed']and len(key['calls'])==2 and all(c['started']and c['reaped']and c['exitCode']==0 and not c['timedOut']for c in key['calls'])and np[2]['keyExposureQualified'],'successful single native Left and optional-R exposure')
 controls=[]
 for cap in n['controls']:
  buf=gp.capture(cap,False);wins=[]
  for meta,raw in zip(cap['windows'],buf):
   row={'name':meta['name'],'bytes':len(raw),'sha256':sha(raw)}
   if meta['name']=='R':row['stopLoggerFaultOrdinaryLimit']=[half(raw,k)for k in [0,6,10,14,196]]
   wins.append(row)
  controls.append({'role':cap['role'],'beforeUs':cap['transfers'][0][4],'afterUs':cap['transfers'][-1][5],'windows':wins})
 need(controls[-3]['windows'][0]['stopLoggerFaultOrdinaryLimit']==[0,1,0,1,200]and controls[-1]['windows'][0]['stopLoggerFaultOrdinaryLimit']==[0,0,0,1,200],'fresh restore and final checked logger zero')
 p=T/'raised-capture-01';baseline=(p/'baseline-ring.bin').read_bytes();postring=(p/'post-ring.bin').read_bytes();need(gp.bind_rings(n,baseline,postring)==j(p/'ring-metadata.json'),'both full15372-byte ring sidecars')
 first=struct.unpack_from('<3I',baseline);last=struct.unpack_from('<3I',postring);need(first==(5,5,0)and last==(6158,6145,1),'actual ring endpoint fields');candidate=postring[12+first[0]:12+last[0]]
 need(len(candidate)==6153 and candidate.startswith(b'[RTP]END\n[RTP:NORMAL][3]\n'),'cursor-selected candidate prefix');details=[]
 pattern=rb'\[RTP\s+(\d+)\]RGB:(\d+) x:\s*(\d+) y:\s*(\d+)/c:\s*(\d+)/diff:(\d+)/m:(\w+)\n'
 for line in candidate.splitlines(keepends=True)[2:]:
  m=re.fullmatch(pattern,line);need(m is not None,'complete RTP detail row');v=list(map(int,m.groups()[:6]));details.append(dict(zip(['ordinal','rgb','x','y','b','diff'],v),mode=m[7].decode(),conditional12bitACandidates=[x for x in sorted(set([v[4]-v[5],v[4]+v[5]]))if 0<=x<=4095]))
 need([x['ordinal']for x in details]==list(range(112))and all(x['rgb']==0 and x['y']==2159 and x['mode']=='NORMAL'for x in details),'112 contiguous detail IDs, no201 saturation')
 need(baseline.count(b'rtp_act_736\n')==postring.count(b'rtp_act_736\n')==0,'no exact736 text in either retained snapshot')
 outside=lambda b:b[12:12+first[0]]+b[12+last[0]:];need(outside(baseline)==outside(postring),'unchanged backing data outside endpoint candidate')
 advance=lambda index,n:(index+n-1)%15360+1;need(advance(first[0],6153)==advance(first[0],6153+15360)==last[0],'endpoint compatible with additional whole lap')
 need(e['headersSent']==16 and e['bulkTransfers']==32 and post['start-R.bin']==post['end-R.bin']and [half(post['start-R.bin'],k)for k in [0,6,10,14,196]]==[0,0,0,1,200],'fresh full post-EB clean200/logger0')
 need(post['start-N.bin']==post['end-N.bin']and any(post['start-N.bin'])and post['M.bin'][56]==1 and post['C.bin'][7:9]==b'\1\3','postN nonzero, C7one/C8three/scan1')
 need(ep[2]==j(T/'raised-post-capture/interpretation.json'),'post EB interpretation');parent=j(T/'raised-post-parent-check.json');need(parent['accepted']and parent['bothNZero']is False and parent['device']==68,'parent endpoint independently agrees')
 # Fresh cached readiness command equality: metadata/census is not queue proof.
 ready_calls=0
 for folder,wrapper,marker in [('set-readiness',load(B/FAMILIES['set-01']/'run-once.py'),'FA_CURRENT_READY'),('raised-readiness',load(B/FAMILIES['raised-capture-01']/'run-once.py'),'GG_CURRENT_READY'),('raised-post-readiness',load(B/FAMILIES['raised-post-capture']/'run-once.py'),'EI_CURRENT_READY')]:
  d=T/folder;rec=j(d/'metadata-root.json');audit(rec['calls']);rd=j(d/'readiness.json');need(len(rec['calls'])==1 and rd['identity']==ars['identity'],'same fresh readiness instance');c=rec['calls'][0];need(c['command']=='set -eu\n'+wrapper.metadata_body(rd['identity'],marker)and c['response']['commands'][0]['stdout']==(d/'metadata.txt').read_text(),'exact source readiness getter');need(wrapper.parse_metadata((d/'metadata.txt').read_text(),marker)==j(d/'census-summary.json'),'readiness census output');ready_calls+=1
 # Source-pinned parent CLI bindings for these three attempts and readiness steps.
 for step in ['set-01','raised-capture-01','raised-post-capture','set-readiness','raised-readiness','raised-post-readiness']:
  d=T/(step+'-logs');intent=j(d/'intent.json');completion=j(d/'completion.json');argv=intent['argv'];script=Path(next(v for v in argv[1:]if v.endswith('.py')));need(completion['exitCode']==0 and intent['automaticRetry']is False and not(d/'stderr.txt').read_bytes(),'parent CLI completed once');need(any(r['path']==str(script.relative_to(B))and r['sha256']==sha(script.read_bytes())for r in j(D/'input-pins.json')['files']),'executed CLI source pin')
  if step in FAMILIES:
   result=j(T/step/'result.json');need(json.loads((d/'stdout.txt').read_bytes())==result and argv[argv.index('--manifest-sha256')+1]==result['manifestSha256']and argv[argv.index('--readiness-sha256')+1]==result['readinessSha256'],'CLI explicit source/readiness pins')
 # Positive selected-source provenance. This does not identify a running PC/FP.
 asset=(B/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes();need(sha(asset)=='bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0','selected source whole asset');image=asset[0x40200:0x60200];spans=[]
 for row in j(B/'rtp-normal-header-trace-20261028fr/source-audit.json')['sourceSpans']:
  start=int(row['va'],16);end=int(row['endExclusive'],16);need(sha(image[start:end])==row['sha256'],'source aggregate/publication/epoch span');spans.append(row)
 for row in j(B/'fault-event-logging-options-20261028et/source-audit.json')['sourceRanges']:
  start=int(row['address'],16);need(sha(image[start:start+row['bytes']])==row['sha256'],'source setter/logger span');spans.append(row)
 def bl(at):
  a,b=struct.unpack_from('<HH',image,at);need(a&0xf800==0xf000 and b&0xd000==0xd000,'Thumb BL');s=(a>>10)&1;v=s<<24|(1^((b>>13)&1)^s)<<23|(1^((b>>11)&1)^s)<<22|(a&0x3ff)<<12|(b&0x7ff)<<1;return at+4+(v-(1<<25)if v&(1<<24)else v)
 for at,target in [(0x203a,0xc1e0),(0xc206,0x1b8c8),(0xc20e,0x1b8c8)]:need(bl(at)==target,'positive source setter/sink edge')
 need(image[0xc214:0xc220]==b'rtp_act_%d\n\0'and image[0xbb48:0xbb55]==b'[RTP:%s][%d]\n'and word(image,0xbaf4)==0x200004a0,'source event/header literals and invocation counter')
 # Independently decoded common compact fields agree with strict parser's smaller summary.
 for row,decoded in zip(rows,np[1]):need((row['cycle'],row['startRt'],row['endRt'],row['c7'],row['h0'],row['r24ca'],row['m4c2'])==(decoded['cycle'],decoded['startRt'],decoded['endRt'],decoded['c7'],decoded['a0'],decoded['selectorMirror'],decoded['referenceCounter']),'independent row decode agrees')
 # Parent-authorized bounded entry comparison only; the40 workflow is separately owned.
 original40=load(B/'combined-event-successor-20261028fn/parse-result.py');forty=original40.parse_native((T/'forty-capture-01/native.receipt.json').read_text())[0];fortyready=j(T/'forty-capture-01/readiness-decision.json');need(fortyready['identity']==ars['identity']and forty['device']==68,'bounded same-instance40 baseline comparison')
 raisedbuf=gp.capture(n['retained'][0]);fortybuf=original40.capture(forty['retained'][0]);parentcomparison=j(T/'baseline-context-comparison.json')
 def halfdiff(x,y):return [{'offset':hex(i),'raised':half(x,i),'forty':half(y,i)}for i in range(0,len(x),2)if half(x,i)!=half(y,i)]
 rd=halfdiff(raisedbuf[0],fortybuf[0]);md=halfdiff(raisedbuf[1],fortybuf[1]);cd=[i for i,(x,y)in enumerate(zip(raisedbuf[2],fortybuf[2]))if x!=y]
 need(rd==parentcomparison['fullBaselineRHalfwordDifferences']and md==parentcomparison['fullBaselineMHalfwordDifferences']and cd==parentcomparison['fullBaselineCByteDifferences'],'independent complete R/M/C entry differences')
 need(raisedbuf[5]==fortybuf[5]and raisedbuf[4]==fortybuf[4]and not cd,'full H/N/C entry bytes equal');need(word(raisedbuf[5],4)==word(fortybuf[5],4)==0 and raisedbuf[2][7]==fortybuf[2][7]==0,'both entry H0zero/C7zero')
 comparison={'scope':'only stored native receipt trigger-baseline windows and saved readiness identity; full40 workflow/recovery excluded','sameUsbInstance':True,'baselineRHalfwordDifferences':rd,'baselineMHalfwordDifferences':md,'baselineCBytesEqual':True,'baselineHBytesEqual':True,'baselineNBytesEqual':True,'baselineLBytesEqual':raisedbuf[6]==fortybuf[6],'baselinePByteDifferences':[i for i,(x,y)in enumerate(zip(raisedbuf[3],fortybuf[3]))if x!=y],'bothH0':0,'bothC7':0,'sameFullControllerStateProven':False,'causalEffectEstablished':False}
 # Focused actual malformed clones: no generic synthetic success projection.
 for field,value in [('phase','Unknown'),('threshold',40),('headers',459),('bulks',919),('inputs',457),('writes',1),('loggerMayRemain',True),('released',False),('closed',False)]:
  bad=copy.deepcopy(n);bad[field]=value;reject(lambda:gp.parse_native(json.dumps(bad)))
 for i in [0,2,6,20,55*58+2,55*58+6]:
  bad=copy.deepcopy(n);b=bytearray(packed);b[i]^=1;bad['rows']['rawBase64']=base64.b64encode(b).decode();bad['rows']['sha256']=sha(b);reject(lambda:gp.parse_native(json.dumps(bad)))
 for par,orig,field,value in [(fa,a,'readbackVerified',False),(fa,a,'limitMayHaveChanged',True),(eb,e,'headersSent',15),(eb,e,'closed',False)]:
  bad=copy.deepcopy(orig);bad[field]=value;reject(lambda:par.parse_native(json.dumps(bad)))
 for which in [0,1]:
  b=bytearray([baseline,postring][which]);b[-1]^=1;reject(lambda:gp.bind_rings(n,bytes(b)if which==0 else baseline,bytes(b)if which==1 else postring))
 bad=copy.deepcopy(nr['calls'][:1]);bad[0]['command_bytes']=0;reject(lambda:audit(bad))
 need(a['steps'][-1]['afterUs']<n['startUs']<n['endUs']<e['steps'][0]['beforeUs'],'native-clock numerical event ordering')
 delta=[z['hHeaderBeforeUs']-x['hHeaderBeforeUs']for x,z in zip(rows,rows[1:])];need(pincheck()==count,'input cutoff unchanged')
 return dict(schema='gj-independent-raised-analysis-v1',scope='FA set-01 through raised-post-capture; later restore/control excluded',inputFilesVerified=count,checksPassed=checks,malformedRefusals=negative,replays={'set':ars,'gg':nrs,'postEb':ers},freshReadinessCommands=ready_calls,totalUniqueRootRequestsVerified=ars['commands']+nrs['commands']+ers['commands']+ready_calls,writer=writer,native={'terminal':n['terminal'],'headers':n['headers'],'inputs':n['inputs'],'bulks':n['bulks'],'writes':n['writes'],'rows':56,'clean':55,'quiescent':1,'fault':0,'restore':n['restore'],'startUs':n['startUs'],'endUs':n['endUs'],'durationUs':n['endUs']-n['startUs'],'nominalWindowUs':2000000,'cycleCap':56,'maximumH0':36,'above40Rows':[],'phase':n['phase'],'released':True,'closed':True},rows=rows,retained=retained,controls=controls,key=key,keyExposure=np[2]['keyExposure'],cachedCheckpoint=cp,ring={'baselineHeader':list(first),'postHeader':list(last),'baselineSha256':sha(baseline),'postSha256':sha(postring),'candidateBytes':len(candidate),'candidateSha256':sha(candidate),'prefixEndLine':True,'headerMode':'NORMAL','headerPreincrementInvocationCounter':3,'details':details,'detailCount':112,'candidateRecordIds':[0,111],'fullSnapshotExact736Counts':[0,0],'backingOutsideCandidateUnchanged':True,'dataChangedBytes':sum(x!=y for x,y in zip(baseline[12:],postring[12:])),'postCursorDistance':last[0]-last[1],'noWrapOrFreshnessProven':False,'consumerOwnershipProven':False,'sameDispatchOrEpochAsRowsProven':False},postEb={'all16RawFilesVerified':True,'stableR':True,'rStopLoggerFaultOrdinaryLimit':[0,0,0,1,200],'nStartEqualsEnd':True,'nAllZero':False,'nOrdinals':list(struct.unpack_from('<6I',post['start-N.bin'])),'nCounts':list(struct.unpack_from('<6H',post['start-N.bin'],24)),'c7':1,'c8':3,'scan':1,'publicationBound':half(post['M.bin'],42),'invocationCounter':half(post['M.bin'],0),'recordLatch':half(post['end-R.bin'],144)},timing={'setReadbackAfterUs':a['steps'][-1]['afterUs'],'ggEndToPostFirstHeaderUs':e['steps'][0]['beforeUs']-n['endUs'],'hStartSpacingUs':{'minimum':min(delta),'median':statistics.median(delta),'maximum':max(delta)},'source':'numerical common native monotonic-clock premise; request brackets not exact RAM samples'},sourceSpans=spans,boundedLater40EntryComparison=comparison,claims={'sampledAbove40CounterfactualWitness':False,'faultPreventionProven':False,'sameContentOrReferenceEpochAsGfProven':False,'actualFpOrCallerProven':False,'completeLogOrEventAbsenceProven':False,'physicalPictureObserved':False,'mode2Under200PerformedInScope':False,'restoreIncluded':False},wrapperKeys=0,ggThresholdWrites=0,setThresholdWrites=1,targetOperations=0,networkOperations=0)
if __name__=='__main__':
 value=run();raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
 if sys.argv[1:]==['--write']:(D/'decoded.json').write_bytes(raw)
 else:need(raw==(D/'decoded.json').read_bytes(),'frozen derived replay')
 print(json.dumps({k:value[k]for k in ['checksPassed','inputFilesVerified','malformedRefusals','replays','freshReadinessCommands','totalUniqueRootRequestsVerified','targetOperations','networkOperations']},sort_keys=True))
