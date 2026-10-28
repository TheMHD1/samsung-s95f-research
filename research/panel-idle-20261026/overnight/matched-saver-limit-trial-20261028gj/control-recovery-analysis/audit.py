#!/usr/bin/env python3
"""Independent actual GJ initialization/control/recovery audit; saved responses only."""
import ast,base64,contextlib,copy,datetime,hashlib,io,json,re,struct,subprocess,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;F=D.parent;B=F.parent
checks=0;negative=0;replayed=[];inputs={}
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def read(p):
 raw=p.read_bytes()
 if not p.is_relative_to(D):inputs[str(p.relative_to(B))]={'path':str(p.relative_to(B)),'bytes':len(raw),'sha256':sha(raw)}
 return raw
def j(p):return json.loads(read(p))
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def load(p):
 m=types.ModuleType('replay_'+p.stem);m.__file__=str(p);exec(compile(read(p),str(p),'exec'),m.__dict__);return m
def rejects(f):
 global negative
 try:f()
 except(ValueError,KeyError,TypeError,UnicodeError,IndexError,struct.error):negative+=1;return
 raise ValueError('unexpected acceptance')
r=load(B/'rtp-lane-gate-capture-20261028eb/run-once.py');ep=load(r.HERE/'parse-result.py');fn=load(B/'combined-event-successor-20261028fn/parse-result.py');status=load(B/'managed-tcon-status-read/run-status-read.py')
# Constrain all nested pure-source admission temporary directories to this task.
TD=tempfile.TemporaryDirectory
def private_tmp(*args,**kwargs):kwargs['dir']=D/'tmp';return TD(*args,**kwargs)
tempfile.TemporaryDirectory=private_tmp

def validate(c):
 need(c['host_timeout']is False and type(c['transport_exit'])is int and c['transport_exit']==0,'terminal transport')
 need(type(c['command_bytes'])is int and c['command_bytes']==len(c['command'].encode())<=8192 and c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75,'command/budgets')
 blobs=[]
 for key in ['transport_stdout','transport_stderr']:
  item=c[key];need(set(item)=={'encoding','data'}and item['encoding']=='base64','root blob shape');raw=base64.b64decode(item['data'],validate=True);need(base64.b64encode(raw).decode()==item['data'],'canonical blob');blobs.append(raw)
 need(len(blobs[0])+len(blobs[1])<=65536 and blobs[1]==b'','response cap/transport stderr')
 response=r.strict_json(blobs[0]);need(response==c['response'],'raw authenticated response binding')
 need(type(response['uid'])is type(response['euid'])is int and type(response['commands'][0]['exit_code'])is int,'exact response integer types')
 text=status.validate_response(response,c['command']);need(len(text.encode())<=65536,'semantic response bound')
 need(datetime.datetime.fromisoformat(c['started_utc'])<=datetime.datetime.fromisoformat(c['finished_utc']),'call UTC ordering')
 need(subprocess.run(['sh','-n'],input=c['command'].encode(),capture_output=True).returncode==0,'shell syntax')
 return text
class Replay:
 def __init__(self,calls,label):self.calls=copy.deepcopy(calls);self.at=0;self.label=label
 def root(self,command,record,path):
  need(self.at<len(self.calls),'no extra call '+self.label);c=self.calls[self.at];self.at+=1;need(command==c['command'],'exact regenerated request '+self.label);text=validate(c);record.setdefault('calls',[]).append(c);save(path,record);replayed.append(c);return text
 def complete(self):need(self.at==len(self.calls),'all retained calls consumed '+self.label)
def calls(p):return j(p)['calls']
def invoke(module,args):
 old=sys.argv;sys.argv=[str(module.__file__),*map(str,args)]
 try:
  with contextlib.redirect_stdout(io.StringIO()):module.main()
 finally:sys.argv=old
def same_files(generated,original):
 need({p.name for p in generated.iterdir()}=={p.name for p in original.iterdir()},'exact artifact membership '+original.name)
 for p in generated.iterdir():need(p.read_bytes()==read(original/p.name),'every replayed artifact '+p.name)
def wrapper(folder,mod,parser,tmp,action=None,clock=None):
 record=j(folder/'record.json');ready,rr=mod.load_readiness(folder/'readiness-decision.json',sha(read(folder/'readiness-decision.json')))
 for ref in ready['evidence']:need(sha(read(Path(ref['path'])))==ref['sha256'],'readiness reference hash')
 manifest,payload=mod.build_manifest();mr=mod.manifest_bytes(manifest);need(mr==read(folder/'reviewed-manifest.json'),'reviewed manifest')
 mod.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].rsplit('-',1)[-1]))
 root=Replay(record['calls'],folder.name);out=tmp/folder.name;kwargs={}if clock is None else{'clock':clock,'sleeper':lambda _:need(False,'unexpected settle repetition')}
 if action is not None:kwargs['action']=action
 result=mod.execute(out,ready,rr,mr,payload,root,parser,**kwargs);root.complete();same_files(out,folder);need(result==j(folder/'result.json'),'result exact')
 return result,record,ready
def eb(folder,device,tmp):
 result,record,ready=wrapper(folder,r,ep,tmp);n,raws,q=ep.parse_native(read(folder/'native.receipt.json').decode());need(j(folder/'interpretation.json')==q,'strict EB interpretation')
 need(n['accepted']and n['protocolPhase']=='ReadyForHeader'and n['released']and n['closed']and n['device']==device and n['headersSent']==16 and n['bulkTransfers']==32 and n['writes']==n['uiOperations']==0,'EB phase/lifecycle/fixed reads')
 need(len(raws)==16 and all(read(folder/name)==raw and sha(raw)==digest for name,raw,digest in raws),'all16 raw binding')
 a=read(folder/'start-R.bin');z=read(folder/'end-R.bin');half=lambda b,o:struct.unpack_from('<H',b,o)[0]
 need(a==z,'full R stable across source snapshot')
 n0=read(folder/'start-N.bin');n1=read(folder/'end-N.bin')
 return {'device':device,'r':[half(a,o)for o in [0,10,14,196]],'logger':half(a,6),'RReadBracketsUs':[[n['steps'][0]['beforeUs'],n['steps'][1]['afterUs']],[n['steps'][-2]['beforeUs'],n['steps'][-1]['afterUs']]],'scan':read(folder/'M.bin')[56],'C7':read(folder/'C.bin')[7],'C8':read(folder/'C.bin')[8],'RStartEqualsEnd':True,'rootRequests':len(record['calls']),'headers':16,'bulks':32,'NZero':[not any(n0),not any(n1)],'NIds':[list(struct.unpack_from('<6I',x))for x in [n0,n1]],'NCounts':[list(struct.unpack_from('<6H',x,24))for x in [n0,n1]],'columns':{name:sum(v!=0 for v in struct.unpack('<48H',read(folder/(name+'.bin'))))for name in ['X','Y','RGB','B','Diff']},'sourceContext':q['sourceContext'],'identity':ready['identity'],'phase':'ReadyForHeader','cleanup':result['cleanup']}
def identity(folder,tmp):
 module=load(B/'volatile-limit-trial-20261028dk/capture-usb-identity.py');old=module.load;root=Replay(calls(folder/'census-root.json'),folder.name)
 module.load=lambda path,pin,name:root if name=='dk_identity_root'else old(path,pin,name)
 out=tmp/folder.name;invoke(module,['--output',out]);root.complete();same_files(out,folder)
 return j(folder/'identity.json')
def lifecycle(old,new,metadata,framed):
 changed=sorted(k for k in old if old[k]!=new[k]);need(len(old)==len(new)==16 and changed==['deviceNode','devnum','nodeStat','sysfsStat'],'four instance fields only')
 need(old['boot']==new['boot']and old['descriptorsSha256']==new['descriptorsSha256'],'same boot/descriptors')
 text=read(metadata).decode();a=re.search(r'^\[([0-9.]+)\] usb 7-1:.*USB disconnect,.*device number '+old['devnum']+'>',text,re.M);b=re.search(r'^\[([0-9.]+)\] usb 7-1:.*new high-speed USB device number '+new['devnum']+' using sdp-xhci$',text,re.M)
 need(a is not None and b is not None and float(a[1])<float(b[1]),'positive ordered same-port disconnect/enum')
 body=read(framed).decode();u=float(re.search(r'^BEFORE\n([0-9.]+) ',body,re.M)[1]);v=float(re.search(r'^AFTER\n([0-9.]+) ',body,re.M)[1]);need(u<=float(a[1])<float(b[1])<=v,'numeric lifecycle inside helper uptime bracket')
 return {'oldDevice':int(old['devnum']),'newDevice':int(new['devnum']),'changedFields':changed,'sameBootAndDescriptors':True,'numericUptimeBracket':[u,float(a[1]),float(b[1]),v],'crossClockMappingEstablished':False,'instructionReloadProven':False}
def decode(raw,i,start):
 b=raw[58*i:58*(i+1)];h=lambda o:struct.unpack_from('<H',b,o)[0];u=lambda o:struct.unpack_from('<I',b,o)[0]
 return {'cycle':i+1,'startRt':b[0]>>4,'endRt':b[0]&15,'c7':b[1],'startLimit':h(2),'endLimit':h(4),'H':u(6),'q':h(10),'history':[h(o)for o in [12,14,16,18]],'ordinal':u(20),'hHeaderBeforeUs':start+u(24),'hDataAfterUs':start+u(28),'publication':h(32),'trainer':h(34),'trainedCount':h(36),'selectorMirror':h(38),'referenceCounter':h(40),'r2460':h(42),'r246e':h(44),'pointer494':u(46),'pointer498':u(50),'r24ca':h(54),'r2468':h(56)}
state={}
with TD(dir=D/'tmp',prefix='gj-control-')as td:
 tmp=Path(td);old=identity(F/'identity-01',tmp);need(old['devnum']=='67','initialUSB67')
 # Initial GE admits its actual complete stable Fault40 source; initialization
 # happens before any threshold intervention and must not be called a200reset.
 state['initialFault']=eb(F/'live-baseline-capture',67,tmp)
 need(state['initialFault']['r']==[1,4097,0,40]and state['initialFault']['logger']==0,'GE source stable Fault40/logger0')
 ge=load(B/'live-saver-init-adapter-20261028ge/run-once.py');ad=load(ge.HERE/'admit-fault.py');helper=load(ge.HERE/'helper.py');stock=load(helper.STOCK)
 source=ad.admit(F/'live-baseline-capture',sha(read(F/'live-baseline-capture/result.json')),old);need(source==j(F/'live-init-01/source-fault-admission.json'),'complete GE source admission exact')
 folder=F/'live-init-01';ready,rr=ge.load_readiness(folder/'readiness-decision.json',sha(read(folder/'readiness-decision.json')))
 need(ready['identity']==old,'GE same initial instance');mr,payload=ge.build_manifest();mr=ge.manifest_bytes(mr);need(mr==read(folder/'reviewed-manifest.json'),'GE manifest exact')
 allcalls=[]
 for p in folder.rglob('*.json'):
  value=j(p)
  if isinstance(value,dict)and isinstance(value.get('calls'),list):allcalls+=value['calls']
 allcalls.sort(key=lambda c:c['started_utc']);root=Replay(allcalls,'initial GE')
 md=j(folder/'mode2/root.json');helper.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=md['remote_private_directory'].rsplit('-',1)[-1]))
 oldload=ge.load;ge.load=lambda path,pin,name:helper if path==ge.HERE/'helper.py'else oldload(path,pin,name)
 c0=j(folder/'initial-checkpoint.json');c1=j(folder/'mode2/pre-native-checkpoint.json');c2=j(folder/'post-checkpoint.json');times=iter([c0['queryBeforeHostMonotonicNs'],c0['queryReturnedHostMonotonicNs'],c1['queryBeforeHostMonotonicNs'],c1['queryReturnedHostMonotonicNs'],c1['nativeSubmitHostMonotonicNs'],c2['queryBeforeHostMonotonicNs'],c2['queryReturnedHostMonotonicNs']])
 result=ge.execute(tmp/'ge',ready,rr,mr,payload,source,root,lambda:next(times));root.complete();need(result==j(folder/'result.json'),'GE full result replay');need(result['nativeTerminalAccepted']and result['helperCleanupConfirmed']and result['postCachedContextQualified'],'GE three separate success fields')
 for name in ['initial-checkpoint.json','initial-command.txt','initial-response.txt','post-checkpoint.json','post-command.txt','post-response.txt','result.json']:need((tmp/'ge'/name).read_bytes()==read(folder/name),'GE artifact '+name)
 for name in ['framed.txt','receipt.txt','native.stderr','result.json','helper-terminal.json']:need((tmp/'ge/mode2'/name).read_bytes()==read(folder/'mode2'/name),'GE helper artifact '+name)
 parsed=helper.parse_receipt(read(folder/'mode2/receipt.txt').decode(),stock);need(parsed['classification']=='kernel_return_zero_only','strict GE stock terminal classification')
 state['initialStockInitialization']={'nativeInvocations':1,'rootRequests':len(allcalls),'wrapperUiOperations':result['wrapperUiOperations'],'thresholdWrites':result['thresholdWrites'],'nativeTerminalAccepted':result['nativeTerminalAccepted'],'cleanupConfirmed':result['helperCleanupConfirmed'],'postCachedLiveSaverQualified':result['postCachedContextQualified'],'classification':parsed['classification'],'initializationPrerequisiteQualified':False,'physicalPictureObserved':False}
 new=identity(F/'identity-02',tmp);need(new['devnum']=='68','initial stock reenumeration68')
 state['initialLifecycle']=lifecycle(old,new,F/'identity-02/metadata.txt',folder/'mode2/framed.txt')
 state['postInit']=eb(F/'post-init-capture',68,tmp);need(state['postInit']['r']==[0,0,1,40]and state['postInit']['logger']==0,'fresh EB68 Clean40 after GE before write')
 # Explicit FA restore200->40 follows the other agent's raised200 cutoff.
 fa=load(B/'selective-endpoint-limit-writer-20261028fa/run-once.py');fp=load(fa.HERE/'parse-result.py')
 result,record,ready=wrapper(F/'restore-01',fa,fp,tmp,action='restore');native,raws,q=fp.parse_native(read(F/'restore-01/native.receipt.json').decode())
 need(native['accepted']and native['writeAttempted']and native['writeTransportComplete']and native['readbackVerified'],'FA accepted exact write/readback')
 for name,raw,digest in raws:need(read(F/'restore-01'/name)==raw and sha(raw)==digest,'FA all raw bytes')
 need(ready['identity']==new and native['device']==68,'restore sameUSB68')
 before=read(F/'restore-01/fresh-R.bin');after=read(F/'restore-01/readback-R.bin');delta=[i for i in range(256)if before[i]!=after[i]];need(delta==[196]and before[196:198]==b'\xc8\0'and after[196:198]==b'\x28\0','only primary limit byte changed200->40')
 state['restore']={'headers':native['headersSent'],'bulks':native['bulkTransfers'],'rootRequests':len(record['calls']),'before':200,'after':40,'changedByteOffsets':delta,'writeAttempted':native['writeAttempted'],'readbackVerified':native['readbackVerified'],'phase':native['protocolPhase'],'released':native['released'],'closed':native['closed'],'cleanup':result['cleanup'],'automaticRestore':result['automaticRestore']}
 state['fortyBaseline']=eb(F/'forty-baseline-capture',68,tmp);need(state['fortyBaseline']['r']==[0,0,1,40]and state['fortyBaseline']['logger']==0 and state['fortyBaseline']['NZero']==[True,True],'40 control fresh clean/N0 baseline')
 ga=load(B/'live-saver-onset-adapter-20261028ga/run-once.py');record=j(F/'forty-capture-01/record.json');cp=record['cachedCheckpoint'];times=iter([cp['startedHostMonotonicNs'],cp['snapshots'][0]['queryBeforeHostMonotonicNs'],cp['snapshots'][0]['queryReturnedHostMonotonicNs'],cp['nativeCommandSubmitHostMonotonicNs']])
 result,record,ready=wrapper(F/'forty-capture-01',ga,fn,tmp,clock=lambda:next(times));native,_,q=fn.parse_native(read(F/'forty-capture-01/native.receipt.json').decode());need(q==j(F/'forty-capture-01/interpretation.json'),'strict GA interpretation')
 need(ready['identity']==new and native['device']==68,'40 control sameUSB68');need(native['accepted']and native['terminal']=='TransitionCaptured'and native['phase']=='ReadyForHeader'and native['released']and native['closed']and not native['loggerMayRemain'],'GA fault/restored/closed')
 need((native['headers'],native['bulks'],native['inputs'],native['writes'])==(228,456,226,2),'27cycles/controlpairs exact')
 packed=base64.b64decode(native['rows']['rawBase64'],validate=True);rows=[decode(packed,i,native['startUs'])for i in range(27)];need(len(packed)==27*58 and sha(packed)==native['rows']['sha256'],'all58byte rows')
 need([(x['cycle'],x['startRt'],x['endRt'])for x in rows if x['startRt']or x['endRt']]==[(15,3,3),(27,1,1)],'Q15/fault27')
 need([x['H']for x in rows[-7:]]==[8,16,24,32,32,40,48]and rows[-2]['startRt']==0,'cleanH40 thenfault48')
 baseline=read(F/'forty-capture-01/baseline-ring.bin');post=read(F/'forty-capture-01/post-ring.bin');rings=fn.bind_rings(native,baseline,post)
 cursors=[list(struct.unpack_from('<III',data))for data in [baseline,post]];a,b=[x[0]for x in cursors];need(0<=a<=b<=15360,'bounded endpoint ringcandidate');candidate=post[12+a:12+b]
 need(baseline[12:12+a]==post[12:12+a]and baseline[12+b:]==post[12+b:],'all changed ring backing within candidate')
 events=b'rtp_act_736\n';need(baseline[12:].count(events)==0 and post[12:].count(events)==candidate.count(events)==2 and candidate.endswith(events*2),'fresh paired736 suffix scopedtoendpoint')
 details=[]
 for match in re.finditer(rb'\[RTP\s+(\d+)\]RGB:(\d+) x:\s*(\d+) y:\s*(\d+)/c:\s*(\d+)/diff:\s*(\d+)/m:(NORMAL)\n',candidate):
  ordinal,rgb,x,y,bv,diff=map(int,match.groups()[:6]);details.append({'ordinal':ordinal,'rgb':rgb,'x':x,'y':y,'B':bv,'diff':diff,'conditional12bitA':sorted(set(z for z in [bv+diff,bv-diff]if 0<=z<=4095))})
 header=re.findall(rb'\[RTP:NORMAL\]\[(\d+)\]',candidate);need(len(header)==1,'one typed NORMAL header')
 fault=[c for c in native['retained']if c['cycle']==27][0];faultRend=fault['transfers'][1][5];enclosure=faultRend-rows[-2]['hDataAfterUs'];need(enclosure>0,'conservative status enclosure')
 state['fortyControl']={'rows':rows,'rowsCount':27,'clean':25,'quiescent':1,'faulted':1,'headers':228,'bulks':456,'rootRequests':len(record['calls']),'startUs':native['startUs'],'endUs':native['endUs'],'key':native['intervention'],'keyExposure':q['keyExposure'],'keyExposureQualified':q['keyExposureQualified'],'wrapperUiOperations':result['wrapperUiOperations'],'cachedCheckpoint':cp,'phase':native['phase'],'loggerRestore':native['restore'],'cleanup':result['cleanup'],'conservativeStatusEnclosureUs':enclosure,'ring':{'baseline':cursors[0],'post':cursors[1],'candidateBytes':len(candidate),'candidateSha256':sha(candidate),'normalInvocationCounter':int(header[0]),'details':details,'paired736Lines':2,'noLapsProven':False,'sharedEpochProven':False,'executingPcProven':False},'fullRetainedMode':[{'role':c['role'],'cycle':c['cycle'],'Maa':struct.unpack_from('<H',base64.b64decode(next(w['raw']for w in c['windows']if w['name']=='M')),10)[0],'Mac':struct.unpack_from('<H',base64.b64decode(next(w['raw']for w in c['windows']if w['name']=='M')),12)[0]}for c in native['retained']]}
 state['finalFault']=eb(F/'fault-capture',68,tmp);need(state['finalFault']['r']==[1,4097,0,40]and state['finalFault']['logger']==0,'separate stable Fault40 before recovery')
 nav=load(B/'ui-navigation-20261027br/navigate.py')
 # Replay separate ordinary Apps preparation using the unchanged DK main and pinned NAV functions.
 prep=load(B/'volatile-limit-trial-20261028dk/prepare-score-header-v2.py');prep_records=[]
 for path in (F/'final-apps-prep').glob('*.json'):
  value=j(path)
  if 'calls'in value:prep_records.extend(value['calls'])
 prep_records.sort(key=lambda c:c['started_utc']);root=Replay(prep_records,'recovery Apps preparation');nav.adapter=lambda:root
 prep.importlib=types.SimpleNamespace(util=types.SimpleNamespace(spec_from_file_location=lambda name,path:types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda module:module.__dict__.update(nav.__dict__))),module_from_spec=lambda spec:types.ModuleType('replay_nav')))
 prep.time=types.SimpleNamespace(sleep=lambda seconds:need(False,'unexpected preparation sleep'))
 invoke(prep,['--output',tmp/'apps-preparation']);root.complete();need(j(tmp/'apps-preparation/result.json')==j(F/'final-apps-prep/result.json'),'exact ordinary preparation result')
 need(len(prep_records)==9 and [len(re.findall(r'^/usr/bin/input_keyevent [A-Za-z0-9]+ (?:down|up) ',c['command'],re.M))for c in prep_records]==[0,2,0,2,0,2,0,2,0],'one volume/right/twoUp preparation with no key retry')
 # Replay the entire unchanged EI recovery source, including Apps no-op/public gate and deadline helper.
 recovery=load(B/'refresh-checkpoint-trial-20261028ei/recover-eb-fault.py');g=load(B/'recovery-quickpath-20261027bv/recover.py');h=load(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py');stock=load(B/'managed-tcon-power-cycle-once/run-power-cycle-once.py')
 payload2=h.contract();stock.contract();mode2=j(F/'final-recovery-01/mode2/root.json');h.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=mode2['remote_private_directory'].removeprefix('/tmp/s95f-mode2-')))
 original_load=h.load
 recovery_calls=calls(F/'final-recovery-01/before-snapshot.json')+calls(F/'final-recovery-01/recovery-gates/navigate-apps/before-snapshot.json')+calls(F/'final-recovery-01/recovery-gates/public-gate.json')+mode2['calls']+calls(F/'final-recovery-01/final-snapshot.json')
 root=Replay(recovery_calls,'complete EI stock recovery');g.load_adapter=lambda:root;nav.adapter=lambda:root;h.load=lambda path,pin,name:root if path==h.ADAPTER else original_load(path,pin,name)
 def nav_run(argv,output,label):
  need(label=='navigate'and argv[:3]==['python3',str(g.NAV),'apps'],'only normal Apps navigation subprocess')
  capture=io.StringIO();before=sys.argv;sys.argv=argv[1:]
  try:
   with contextlib.redirect_stdout(capture):nav.main()
  finally:sys.argv=before
  done=types.SimpleNamespace(returncode=0,stdout=capture.getvalue().encode(),stderr=b'');(output/(label+'.stdout.txt')).write_bytes(done.stdout);(output/(label+'.stderr.txt')).write_bytes(done.stderr);save(output/(label+'.result.json'),{'argv':argv,'exit_code':0});return done
 g.run=nav_run
 modules={'ei_eb_recovery_parser':ep,'dk_recovery_gates':g,'dk_recovery_nav':nav,'dk_stock_recovery':h}
 def recovery_load(path,pin,name):need(sha(path.read_bytes())==pin,'recovery module source pin');return modules[name]
 recovery.load=recovery_load;invoke(recovery,['--capture',F/'fault-capture','--output',tmp/'recovery']);root.complete();need(j(tmp/'recovery/result.json')==j(F/'final-recovery-01/result.json'),'exact complete recovery result')
 for name in ['framed.txt','receipt.txt','native.stderr','result.json']:need((tmp/'recovery/mode2'/name).read_bytes()==(F/'final-recovery-01/mode2'/name).read_bytes(),'deadline helper artifact replay')
 receipt=(F/'final-recovery-01/mode2/receipt.txt').read_text();parsed=h.parse_receipt(receipt,stock);need(parsed['classification']=='kernel_return_zero_only'and parsed['mode']==2 and parsed['physical_state_inferred']is False,'strict stock operation41/mode2 receipt')
 need(len(mode2['calls'])==12 and sum('./DeadlineMode2.dll >native.stdout'in c['command']for c in mode2['calls'])==1 and len(recovery_calls)==16,'one guarded deadline-helper invocation in16-request EI recovery')
 source=(B/'managed-tcon-power-cycle-once/Program.cs').read_text();deadline=(h.BUILD/'Program.cs').read_text();anchor='        TconRequest value = new TconRequest {'
 need(source[source.index(anchor):]==deadline[deadline.index(anchor):],'stock fixed payload/open/ioctl/close/result body unchanged')
 need(deadline.count('ioctlReturn = ioctl(fd, Request, ref value);')==1 and 'uint previousAlarm = alarm(12);'in deadline and 'FileMode.CreateNew'in deadline,'one fixed syscall body/exclusive receipt/native deadline')
 state['finalRecovery']={'mode2Invocations':1,'rootRequests':len(recovery_calls),'helperRequests':len(mode2['calls']),'classification':parsed['classification'],'cleanupConfirmed':True,'thresholdWrites':0,'physicalPictureObserved':False}
 final=identity(F/'identity-03',tmp);need(final['devnum']=='69','finalUSB69')
 state['finalLifecycle']=lifecycle(new,final,F/'identity-03/metadata.txt',F/'final-recovery-01/mode2/framed.txt')
 state['validation']=eb(F/'validation-capture',69,tmp);need(state['validation']['r']==[0,0,1,40]and state['validation']['logger']==0,'final Clean40/logger0')
 need([state['validation'][k]for k in ['C7','C8','scan']]==[0,3,1],'final exact C7/C8/scan');need(state['validation']['NZero']==[False,False],'do not borrow prior GF N0 claim')
 parent=j(F/'validation-parent-check.json');need(parent['accepted']and parent['bothNZero']is False and parent['device']==69,'parent endpoint matches fresh data')
 need(read(F/'validation-capture/start-N.bin')==read(F/'validation-capture/end-N.bin'),'current N stable but populated')
 root=Replay(calls(F/'final-ui/before-snapshot.json'),'final cached UI');nav.adapter=lambda:root;invoke(nav,['snapshot','--execute','--backend','local','--output',tmp/'final-ui']);root.complete();need(j(tmp/'final-ui/result.json')==j(F/'final-ui/result.json'),'final UI replay exact')
 state['finalUi']=j(F/'final-ui/result.json')['after'];need(state['finalUi']=={'cached_current_tab':'d/apps.tab','csfs_window_present':True,'screensaver_windows_present':True,'physical_picture_observed':False},'cached Apps+saver not optical')
 # Modest cross-run comparison: equal initial C/N/H is not a matched history.
 raised=j(F/'raised-capture-01/native.receipt.json');ggparser=load(B/'live-saver-200-recorder-20261028gg/parse-result.py');ggparser.parse_native(read(F/'raised-capture-01/native.receipt.json').decode());a=next(c for c in raised['retained']if c['role']=='trigger-baseline');b=next(c for c in native['retained']if c['role']=='trigger-baseline')
 def win(c,name):return base64.b64decode(next(w['raw']for w in c['windows']if w['name']==name),validate=True)
 equal={name:win(a,name)==win(b,name)for name in ['C','N','H']};need(all(equal.values()),'trigger C/N/H bytes equal across200 and40')
 ra,rb=win(a,'R'),win(b,'R');rdiff=[i for i in range(256)if ra[i]!=rb[i]];need(rdiff==[0x90,0xc4],'two trigger R bytes differ')
 need(ra[0x90]==0 and rb[0x90]==201 and struct.unpack_from('<H',ra,196)[0]==200 and struct.unpack_from('<H',rb,196)[0]==40,'history and threshold difference actualbytes')
 ma,mb=win(a,'M'),win(b,'M');raisedPacked=base64.b64decode(raised['rows']['rawBase64'],validate=True);raisedH=[struct.unpack_from('<I',raisedPacked,i+6)[0]for i in range(0,len(raisedPacked),58)];need(max(raisedH)==36,'no raised200 sample above40');state['raisedSampleSummary']={'rows':len(raisedH),'maxH':max(raisedH),'above40':any(x>40 for x in raisedH),'fullOutcomeAudit':'separate frozen raised-analysis'};state['triggerComparison']={'sameUsbInstance':raised['device']==native['device']==68,'C_N_H_ByteEqual':equal,'RChangedByteOffsets':rdiff,'R90':[ra[0x90],rb[0x90]],'primaryLimits':[200,40],'MChangedByteOffsets':[i for i in range(68)if ma[i]!=mb[i]],'currentC7':[win(a,'C')[7],win(b,'C')[7]],'currentH':[struct.unpack_from('<I',win(c,'H'),4)[0]for c in [a,b]],'sameHistoryProven':False,'matchedCausalEffectProven':False}
 for label in ['initialLifecycle','finalLifecycle']:
  proof=j(F/('live-init-lifecycle-proof.json'if label=='initialLifecycle'else'final-recovery-lifecycle-proof.json'));v=state[label];need(proof['accepted']and proof['oldDevice']==v['oldDevice']and proof['newDevice']==v['newDevice']and proof['changedFields']==v['changedFields'],'parent lifecycle proof independently confirmed')
 # Saved readiness queries are actual source-regenerated cached-only requests,
 # separate from each wrapper's immediate identity guards.
 for label,mod,marker in [('live-baseline-readiness',r,'EI_CURRENT_READY'),('live-init-readiness',ge,'GE_CURRENT_READY'),('post-init-readiness',r,'EI_CURRENT_READY'),('restore-readiness',fa,'FA_CURRENT_READY'),('forty-baseline-readiness',r,'EI_CURRENT_READY'),('forty-readiness',ga,'GA_CURRENT_READY'),('fault-readiness',r,'EI_CURRENT_READY'),('validation-readiness',r,'EI_CURRENT_READY')]:
  folder=F/label;decision=j(folder/'readiness.json');rr=calls(folder/'metadata-root.json');need(len(rr)==1,'one cached readiness request');root=Replay(rr,label);out=tmp/(label+'.json');record={'calls':[]}
  text=root.root('set -eu\n'+mod.metadata_body(decision['identity'],marker),record,out);root.complete();need(text==read(folder/'metadata.txt').decode(),'readiness saved response');need(mod.parse_metadata(text,marker)==j(folder/'census-summary.json'),'readiness source census')
 # The ordered parent workflows are complete and never automatically replayed.
 steps=['identity-01','live-baseline-capture','live-init-01','identity-02','post-init-capture','restore-01','forty-baseline-capture','forty-capture-01','fault-capture','final-apps-prep','final-recovery-01','identity-03','validation-capture','final-ui'];timeline=[]
 for step in steps:
  start=j(F/(step+'-logs')/'intent.json');end=j(F/(step+'-logs')/'completion.json');need(start['automaticRetry']is False and end['exitCode']==0 and start['startedHostMonotonicNs']<=end['endedHostMonotonicNs'],'completed one-shot parent step')
  argv=start['argv'];script=next(Path(s)for s in argv[1:]if not s.startswith('-'));read(script)
  timeline.append({'step':step,'startNs':start['startedHostMonotonicNs'],'endNs':end['endedHostMonotonicNs']})
 need(all(x['endNs']<=y['startNs']for x,y in zip(timeline,timeline[1:])),'selected workflow ordered')
 state['parentTimeline']=timeline

for name,digest in [('decoded.json','885125ed6c77d9a4bacf2fa63bbb3d746a09e3f8305cc613f36d1f67ef297b45'),('source-inventory.json','5e6423f25842b6efb262576605e5b161a993052c44c2a1aa63888473ec6d2359'),('README.md','6301e14c725f0648c53b4706b97327144290dd67e03c04c113c93185174b9d72')]:
 need(sha(read(F/'raised-analysis'/name))==digest,'separate raised-analysis frozen predecessor')
# Focused semantic negatives; not a replay of historical mock campaigns.
for key,value in [('threshold',200),('released',False),('phase','Unknown'),('physicalPictureObserved',True)]:
 bad=copy.deepcopy(native);bad[key]=value;rejects(lambda:fn.parse_native(json.dumps(bad)))
for offset in [0,1,2,6,20,24,32,38,40,54,56]:
 bad=copy.deepcopy(native);raw=bytearray(packed);raw[offset]^=1;bad['rows']['rawBase64']=base64.b64encode(raw).decode();bad['rows']['sha256']=sha(raw);rejects(lambda:fn.parse_native(json.dumps(bad)))
for key in ['uid-bool','unauthenticated','wrong-command','timeout']:
 bad=copy.deepcopy(replayed[0]);response=bad['response']
 if key=='uid-bool':response['uid']=False
 if key=='unauthenticated':response['authenticated']=False
 if key=='wrong-command':response['commands'][0]['command']+='x'
 if key=='timeout':response['commands'][0]['timed_out']=True
 bad['transport_stdout']['data']=base64.b64encode(json.dumps(response).encode()).decode();rejects(lambda:validate(bad))
for c in replayed:
 need(c['host_timeout']is False,'no replay timeout');need(not any(s in c['command']for s in ['--action set',' --set-limit']),'scope no new200set command')
for row in inputs.values():
 raw=(B/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'consumed input unchanged')
result={'schema':'gj-independent-control-recovery-v1','checks':checks,'negativeCases':negative,'state':state,'replayedRootRequests':len(replayed),'maxCommandBytes':max(c['command_bytes']for c in replayed),'targetOperationsByAnalyzer':0,'networkOperations':0,'actualFpProven':False,'physicalPictureObserved':False,'causalFixProven':False,'raisedAbove40WitnessObserved':False,'coupledPublicationBound':True,'sameUiHistoryProven':False,'inputPins':sorted(inputs.values(),key=lambda x:x['path'])}
print(json.dumps(result,indent=2,sort_keys=True))
