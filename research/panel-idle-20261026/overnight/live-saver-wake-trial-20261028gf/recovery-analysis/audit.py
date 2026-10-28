#!/usr/bin/env python3
"""Independent fixed GF actual recovery replay; all transport callbacks are retained data."""
import ast,base64,contextlib,copy,datetime,hashlib,importlib.util,io,json,re,struct,subprocess,sys,tempfile,types
from pathlib import Path
P=Path(__file__).resolve().parent;FW=P.parent;B=FW.parent;checks=0;replayed=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def rejects(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):need(True,'expected refusal');return
 raise ValueError('unexpected acceptance')
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def j(path):return json.loads(path.read_bytes())
def save(path,v):path.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
for row in j(P/'input-pins.json')['files']:
 raw=(B/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'input pin '+row['path'])
r=load(B/'rtp-lane-gate-capture-20261028eb/run-once.py');parser=load(r.HERE/'parse-result.py');status=load(B/'managed-tcon-status-read/run-status-read.py');nav=load(B/'ui-navigation-20261027br/navigate.py');fn_parser=load(B/'combined-event-successor-20261028fn/parse-result.py')
manifest,payload=r.build_manifest();raw_manifest=r.manifest_bytes(manifest);need(sha(raw_manifest)=='e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11','exact frozen EB manifest')
def retained(v):
 need(type(v)is dict and set(v)=={'encoding','data'}and v['encoding']=='base64'and type(v['data'])is str,'exact root retained bytes')
 raw=base64.b64decode(v['data'],validate=True);need(base64.b64encode(raw).decode()==v['data'],'canonical retained root encoding');return raw
def validated(c):
 need(type(c)is dict and c['host_timeout']is False and type(c['transport_exit'])is int and c['transport_exit']==0,'root transport terminal')
 command=c['command'];need(type(command)is str and type(c['command_bytes'])is int and c['command_bytes']==len(command.encode())and 0<c['command_bytes']<=8192,'root command exact size/cap')
 need(c['remote_timeout_seconds']==45 and c['host_timeout_limit_seconds']==75,'serialized root45/75 bounds')
 raw=retained(c['transport_stdout']);err=retained(c['transport_stderr']);need(len(raw)+len(err)<=65536 and err==b'','root response cap/empty transport stderr')
 response=r.strict_json(raw.decode());need(response==c['response'],'retained transport response binding')
 need(type(response.get('uid'))is int and type(response.get('euid'))is int,'root exact UID types')
 item=response['commands'][0];need(type(item.get('exit_code'))is int,'root exact exit type')
 text=status.validate_response(response,command);need(len(text.encode())<=65536,'bounded semantic stdout')
 need(datetime.datetime.fromisoformat(c['started_utc'])<=datetime.datetime.fromisoformat(c['finished_utc']),'root clock order')
 need(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'retained root shell syntax')
 return text
class Replay:
 def __init__(self,calls,label):self.calls=copy.deepcopy(calls);self.at=0;self.label=label
 def root(self,command,record,path):
  need(self.at<len(self.calls),'no extra root request '+self.label);c=self.calls[self.at];self.at+=1;need(command==c['command'],'exact regenerated request '+self.label);text=validated(c);record.setdefault('calls',[]).append(c);save(path,record);replayed.append(c);return text
 def complete(self):need(self.at==len(self.calls),'all retained requests consumed '+self.label)
def calls(path):return j(path)['calls']
def invoke(module,args):
 before=sys.argv;sys.argv=[str(module.__file__),*map(str,args)]
 try:
  with contextlib.redirect_stdout(io.StringIO()):module.main()
 finally:sys.argv=before
state={}
with tempfile.TemporaryDirectory(dir=P/'tmp',prefix='fw-replay-')as td:
 tmp=Path(td)
 for label,device,want in [('fault-capture',66,[1,4097,0,40]),('validation-capture',67,[0,0,1,40])]:
  capture=FW/label;native,raws,interpretation=parser.parse_native((capture/'native.receipt.json').read_text());need(native['device']==device and native['writes']==native['uiOperations']==0,'fixed EB device/no writes/UI')
  need(native['headersSent']==16 and native['bulkTransfers']==32 and native['released']and native['closed']and native['protocolPhase']=='ReadyForHeader','strict EB terminal')
  need(len(raws)==16 and all((capture/name).read_bytes()==raw and sha(raw)==digest for name,raw,digest in raws),'all16 raw files match strict receipt')
  need(j(capture/'interpretation.json')==interpretation,'derived EB interpretation exact')
  start=(capture/'start-R.bin').read_bytes();end=(capture/'end-R.bin').read_bytes();tuples=[[struct.unpack_from('<H',raw,at)[0]for at in [0,10,14,196]]for raw in [start,end]];loggers=[struct.unpack_from('<H',raw,6)[0]for raw in [start,end]]
  fn_parser.logger(start,0);fn_parser.logger(end,0)
  need(start==end and tuples==[want,want]and loggers==[0,0],'stable sampled R/limit40/logger0')
  rd,rr=r.load_readiness(capture/'readiness-decision.json',sha((capture/'readiness-decision.json').read_bytes()))
  for ref in rd['evidence']:need(sha(Path(ref['path']).read_bytes())==ref['sha256'],'readiness evidence binding')
  need(rd['identity']==j(FW/('identity-01/identity.json'if device==66 else'after-recovery-identity/identity.json')),'full cached identity binding')
  need((capture/'reviewed-manifest.json').read_bytes()==raw_manifest,'actual reviewed EB manifest')
  record=j(capture/'record.json');r.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=record['remote_stage'].removeprefix('/tmp/researcher-eb-')))
  root=Replay(record['calls'],label);out=tmp/label;result=r.execute(out,rd,rr,raw_manifest,payload,root,parser);root.complete();need(result==j(capture/'result.json'),'exact replayed EB result')
  for p in out.iterdir():
   need(p.read_bytes()==(capture/p.name).read_bytes(),'complete EB artifact replay '+p.name)
  need(len(root.calls)==28 and record['cleanup_required']is False and record['cleanup_stdout']=='STAGE_ABSENT\n','EB exact28 requests/cleanup')
  need(sum(' --execute --device 'in c['command']for c in root.calls)==1,'single fixed EB native invocation')
  n0=(capture/'start-N.bin').read_bytes();n1=(capture/'end-N.bin').read_bytes();columns={name:sum(v!=0 for v in struct.unpack('<48H',(capture/(name+'.bin')).read_bytes()))for name in ['X','Y','RGB','B','Diff']}
  state[label]={'device':device,'headers':16,'bulks':32,'rawFiles':16,'rootRequests':28,'rTuples':tuples,'loggerHalfwords':loggers,'NZero':[not any(n0),not any(n1)],'nonzeroColumnHalfwords':columns,'sourceContext':interpretation['sourceContext'],'cleanup':'STAGE_ABSENT','physicalPictureObserved':False}
 need(state['validation-capture']['NZero']==[True,True]and state['validation-capture']['nonzeroColumnHalfwords']=={'X':0,'Y':0,'RGB':0,'B':22,'Diff':0},'final N0 and22 nonzero B halfwords')
 # Replay separate ordinary Apps preparation using the unchanged DK main and pinned NAV functions.
 prep=load(B/'volatile-limit-trial-20261028dk/prepare-score-header-v2.py');prep_records=[]
 for path in (FW/'recovery-apps-preparation').glob('*.json'):
  value=j(path)
  if 'calls'in value:prep_records.extend(value['calls'])
 prep_records.sort(key=lambda c:c['started_utc']);root=Replay(prep_records,'recovery Apps preparation');nav.adapter=lambda:root
 prep.importlib=types.SimpleNamespace(util=types.SimpleNamespace(spec_from_file_location=lambda name,path:types.SimpleNamespace(loader=types.SimpleNamespace(exec_module=lambda module:module.__dict__.update(nav.__dict__))),module_from_spec=lambda spec:types.ModuleType('replay_nav')))
 prep.time=types.SimpleNamespace(sleep=lambda seconds:need(False,'unexpected preparation sleep'))
 invoke(prep,['--output',tmp/'apps-preparation']);root.complete();need(j(tmp/'apps-preparation/result.json')==j(FW/'recovery-apps-preparation/result.json'),'exact ordinary preparation result')
 need(len(prep_records)==9 and [len(re.findall(r'^/usr/bin/input_keyevent [A-Za-z0-9]+ (?:down|up) ',c['command'],re.M))for c in prep_records]==[0,2,0,2,0,2,0,2,0],'one volume/right/twoUp preparation with no key retry')
 # Replay the entire unchanged EI recovery source, including Apps no-op/public gate and deadline helper.
 recovery=load(B/'refresh-checkpoint-trial-20261028ei/recover-eb-fault.py');g=load(B/'recovery-quickpath-20261027bv/recover.py');h=load(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py');stock=load(B/'managed-tcon-power-cycle-once/run-power-cycle-once.py')
 payload2=h.contract();stock.contract();mode2=j(FW/'recovery-01/mode2/root.json');h.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex=mode2['remote_private_directory'].removeprefix('/tmp/s95f-mode2-')))
 original_load=h.load
 recovery_calls=calls(FW/'recovery-01/before-snapshot.json')+calls(FW/'recovery-01/recovery-gates/navigate-apps/before-snapshot.json')+calls(FW/'recovery-01/recovery-gates/public-gate.json')+mode2['calls']+calls(FW/'recovery-01/final-snapshot.json')
 root=Replay(recovery_calls,'complete EI stock recovery');g.load_adapter=lambda:root;nav.adapter=lambda:root;h.load=lambda path,pin,name:root if path==h.ADAPTER else original_load(path,pin,name)
 def nav_run(argv,output,label):
  need(label=='navigate'and argv[:3]==['python3',str(g.NAV),'apps'],'only normal Apps navigation subprocess')
  capture=io.StringIO();before=sys.argv;sys.argv=argv[1:]
  try:
   with contextlib.redirect_stdout(capture):nav.main()
  finally:sys.argv=before
  done=types.SimpleNamespace(returncode=0,stdout=capture.getvalue().encode(),stderr=b'');(output/(label+'.stdout.txt')).write_bytes(done.stdout);(output/(label+'.stderr.txt')).write_bytes(done.stderr);save(output/(label+'.result.json'),{'argv':argv,'exit_code':0});return done
 g.run=nav_run
 modules={'ei_eb_recovery_parser':parser,'dk_recovery_gates':g,'dk_recovery_nav':nav,'dk_stock_recovery':h}
 def recovery_load(path,pin,name):need(sha(path.read_bytes())==pin,'recovery module source pin');return modules[name]
 recovery.load=recovery_load;invoke(recovery,['--capture',FW/'fault-capture','--output',tmp/'recovery']);root.complete();need(j(tmp/'recovery/result.json')==j(FW/'recovery-01/result.json'),'exact complete recovery result')
 for name in ['framed.txt','receipt.txt','native.stderr','result.json']:need((tmp/'recovery/mode2'/name).read_bytes()==(FW/'recovery-01/mode2'/name).read_bytes(),'deadline helper artifact replay')
 receipt=(FW/'recovery-01/mode2/receipt.txt').read_text();parsed=h.parse_receipt(receipt,stock);need(parsed['classification']=='kernel_return_zero_only'and parsed['mode']==2 and parsed['physical_state_inferred']is False,'strict stock operation41/mode2 receipt')
 need(len(mode2['calls'])==12 and sum('./DeadlineMode2.dll >native.stdout'in c['command']for c in mode2['calls'])==1 and len(recovery_calls)==16,'one guarded deadline-helper invocation in16-request EI recovery')
 source=(B/'managed-tcon-power-cycle-once/Program.cs').read_text();deadline=(h.BUILD/'Program.cs').read_text();anchor='        TconRequest value = new TconRequest {'
 need(source[source.index(anchor):]==deadline[deadline.index(anchor):],'stock fixed payload/open/ioctl/close/result body unchanged')
 need(deadline.count('ioctlReturn = ioctl(fd, Request, ref value);')==1 and 'uint previousAlarm = alarm(12);'in deadline and 'FileMode.CreateNew'in deadline,'one fixed syscall body/exclusive receipt/native deadline')
 # Recompute post-recovery identity and census from both retained source-exact requests.
 identity_helper=load(B/'volatile-limit-trial-20261028dk/capture-usb-identity.py');df=load(B/'firmware-rtp-producer-20261028df/capture/run-once.py');original_identity_load=identity_helper.load
 root=Replay(calls(FW/'after-recovery-identity/census-root.json'),'post-recovery identity/census')
 identity_helper.load=lambda path,pin,name:root if name=='dk_identity_root'else original_identity_load(path,pin,name)
 invoke(identity_helper,['--output',tmp/'identity']);root.complete()
 for name in ['identity.json','metadata.txt','census.txt','census-summary.json']:need((tmp/'identity'/name).read_bytes()==(FW/'after-recovery-identity'/name).read_bytes(),'cached identity artifact replay')
 old=j(FW/'identity-01/identity.json');new=j(FW/'after-recovery-identity/identity.json');changed=sorted(k for k in old if old[k]!=new[k]);need(changed==['deviceNode','devnum','nodeStat','sysfsStat']and old['devnum']=='66'and new['devnum']=='67','exact four instance changes66to67')
 need(old['boot']==new['boot']and old['descriptorsSha256']==new['descriptorsSha256'],'same boot/descriptors across re-enumeration')
 meta=(FW/'after-recovery-identity/metadata.txt').read_text();disconnect=re.search(r'^\[([0-9.]+)\] usb 7-1:.*USB disconnect,.*device number 66>',meta,re.M);enumeration=re.search(r'^\[([0-9.]+)\] usb 7-1:.*new high-speed USB device number 67 using sdp-xhci$',meta,re.M)
 need(disconnect is not None and enumeration is not None and float(disconnect[1])<float(enumeration[1]),'positive Samsung-prefixed disconnect66 then enumeration67')
 # Both readiness decisions are regenerated from their exact saved CLI arguments, with local output only.
 ei=load(B/'refresh-checkpoint-trial-20261028ei/prepare-readiness.py');real_load=ei.load
 for readiness_label in ['fault-readiness','validation-readiness']:
  root=Replay(calls(FW/readiness_label/'metadata-root.json'),readiness_label);ei.load=lambda path,pin,name:root if path==ei.ROOT else real_load(path,pin,name)
  argv=j(FW/(readiness_label+'-logs')/'intent.json')['argv'][2:];argv=list(argv);argv[argv.index('--output')+1]=str(tmp/readiness_label)
  invoke(ei,argv);root.complete();got=j(tmp/readiness_label/'readiness.json');actual=j(FW/readiness_label/'readiness.json')
  need({k:v for k,v in got.items()if k!='evidence'}=={k:v for k,v in actual.items()if k!='evidence'},'readiness semantic replay '+readiness_label)
  need(got['evidence'][:-2]==actual['evidence'][:-2]and [v['sha256']for v in got['evidence'][-2:]]==[v['sha256']for v in actual['evidence'][-2:]],'readiness evidence exact modulo scratch paths')
 # Final UI is cached Apps+saver/CSFS only.
 root=Replay(calls(FW/'final-ui/before-snapshot.json'),'final cached UI');nav.adapter=lambda:root;invoke(nav,['snapshot','--execute','--backend','local','--output',tmp/'final-ui']);root.complete();need(j(tmp/'final-ui/result.json')==j(FW/'final-ui/result.json'),'final cached UI result replay')
 need(j(FW/'final-ui/result.json')['after']=={'cached_current_tab':'d/apps.tab','csfs_window_present':True,'physical_picture_observed':False,'screensaver_windows_present':True},'final Apps/saver/CSFS does not observe light')
# Finite negative checks verify strict receipt and authenticated-envelope failure boundaries.
negative_cases=0
for i in range(32):
 v=copy.deepcopy(j(FW/'validation-capture/native.receipt.json'));v['steps'][i]['count']-=1;rejects(lambda:parser.parse_native(json.dumps(v)));negative_cases+=1
for i in range(16):
 v=copy.deepcopy(j(FW/'validation-capture/native.receipt.json'));v['windows'][i]['sha256']='0'*64;rejects(lambda:parser.parse_native(json.dumps(v)));negative_cases+=1
for key,value in [('device',False),('writes',1),('physicalPictureObserved',True),('released',False),('protocolPhase','Unknown')]:
 v=copy.deepcopy(j(FW/'validation-capture/native.receipt.json'));v[key]=value;rejects(lambda:parser.parse_native(json.dumps(v)));negative_cases+=1
for field,original,replacement in [('MODE_DECIMAL','2','1'),('OPERATION_DECIMAL','41','40'),('IOCTL_REQUEST','0xc010749f','0xc010749e'),('IOCTL_RETURN','0','1'),('CLOSE_RETURN','0','1'),('POWER_ACTION_ACKNOWLEDGED','0','1'),('RECOVERY_INFERRED','0','1')]:
 bad=receipt.replace(field+'='+original+'\n',field+'='+replacement+'\n');rejects(lambda:h.parse_receipt(bad,stock));negative_cases+=1
for change in ['uid-bool','unauthenticated','wrong-model','extra-command','wrong-command','remote-timeout','transport-stderr','host-timeout','wrong-command-size']:
 c=copy.deepcopy(replayed[0]);response=c['response']
 if change=='uid-bool':response['uid']=False
 if change=='unauthenticated':response['authenticated']=False
 if change=='wrong-model':response['model']='other'
 if change=='extra-command':response['commands'].append(copy.deepcopy(response['commands'][0]))
 if change=='wrong-command':response['commands'][0]['command']+=':\n'
 if change=='remote-timeout':response['commands'][0]['timed_out']=True
 if change=='transport-stderr':c['transport_stderr']={'encoding':'base64','data':base64.b64encode(b'error').decode()}
 if change=='host-timeout':c['host_timeout']=True
 if change=='wrong-command-size':c['command_bytes']-=1
 c['transport_stdout']={'encoding':'base64','data':base64.b64encode(json.dumps(response).encode()).decode()}
 rejects(lambda:validated(c));negative_cases+=1
# The source-fixed declarations and stock request body are separate from the exclusive receipt/deadline wrapper.
for literal in ['private const string Device = "/dev/tztv_tcon";','private const uint Request = 0xc010749f;','private const uint Operation = 41;','private const uint Mode = 2;']:
 need(literal in source and literal in deadline,'unchanged fixed request declaration')
framed=(FW/'recovery-01/mode2/framed.txt').read_text();before_uptime=float(re.search(r'^BEFORE\n([0-9.]+) ',framed,re.M)[1]);after_uptime=float(re.search(r'^AFTER\n([0-9.]+) ',framed,re.M)[1])
need(before_uptime<=float(disconnect[1])<float(enumeration[1])<=after_uptime,'USB lifecycle events bracketed by foreground MODE2 helper command uptime')
frame=re.fullmatch(r'BEFORE\n([0-9]+\.[0-9]+ [0-9]+\.[0-9]+)\nHELPER_EXIT\n([0-9]{1,3})\nRECEIPT_BASE64\n([A-Za-z0-9+/=\n]*)NATIVE_STDERR_BASE64\n([A-Za-z0-9+/=\n]*)AFTER\n([0-9]+\.[0-9]+ [0-9]+\.[0-9]+)\n',framed)
need(frame is not None and int(frame[2])==0 and len(framed.encode())<=65536,'strict complete original helper framing')
for encoded,cap,expected in [(frame[3],8192,(FW/'recovery-01/mode2/receipt.txt').read_bytes()),(frame[4],4096,b'')]:
 compact=encoded.replace('\n','');blob=base64.b64decode(compact,validate=True);need(base64.b64encode(blob).decode()==compact and len(blob)<=cap and blob==expected,'canonical helper blob and exact stored bytes')
need('for name,data,digest in raws:'in(FW/'check-eb.py').read_text(),'parent corrected offline tuple contract source')
for name,want in [('fault-parent-check.json',[1,4097,0,40]),('validation-parent-check.json',[0,0,1,40])]:
 parent=j(FW/name);need(parent['accepted']is True and parent['rawFilesVerified']==16 and parent['rTuples']==[want,want]and parent['loggerHalfwords']==[0,0],'parent EB checks match independent strict replay')
life=j(FW/'recovery-lifecycle-proof.json');need(life['accepted']is True and life['oldDevice']==66 and life['newDevice']==67 and life['changedFields']==changed and life['mode2Requests']==1 and life['thresholdWrites']==0,'parent lifecycle proof facts match independent originals')
need([float(life[k])for k in ['helperUptimeBefore','disconnectDmesgSeconds','enumerationDmesgSeconds','helperUptimeAfter']]==[before_uptime,float(disconnect[1]),float(enumeration[1]),after_uptime],'parent numeric lifecycle bracket exact')
# Finite recorded workflow chronology, with no claim of observing unrecorded clients.
workflow=['fault-readiness','fault-capture','recovery-apps-preparation','recovery-01','after-recovery-identity','validation-readiness','validation-capture','final-ui'];chronology=[]
for name in workflow:
 start=j(FW/(name+'-logs')/'intent.json');end=j(FW/(name+'-logs')/'completion.json');need(start['automaticRetry']is False and end['exitCode']==0 and start['startedHostMonotonicNs']<=end['endedHostMonotonicNs'],'parent workflow completion/clocks')
 chronology.append({'step':name,'startNs':start['startedHostMonotonicNs'],'endNs':end['endedHostMonotonicNs']})
need(all(a['endNs']<=b['startNs']for a,b in zip(chronology,chronology[1:])),'ordered recovery workflow')
need(len(replayed)==86 and sum('./DeadlineMode2.dll >native.stdout'in c['command']for c in replayed)==1,'exact86 regenerated source-bound requests/single MODE2')
print(json.dumps({'schema':'gf-independent-recovery-replay-v1','accepted':True,'checks':checks,'negativeCases':negative_cases,'actualReplayedRootRequests':len(replayed),'maxCommandBytes':max(c['command_bytes']for c in replayed),'maxTransportResponseBytes':max(len(base64.b64decode(c['transport_stdout']['data']))+len(base64.b64decode(c['transport_stderr']['data']))for c in replayed),'state':state,'mode2Requests':1,'helperRequestCount':12,'eiRecoveryRootRequests':16,'helperOperation':41,'helperMode':2,'helperIoctlRequest':'0xc010749f','helperClassification':'kernel_return_zero_only','nativeDeadlineSeconds':12,'lifecycleUptimeBracket':[before_uptime,float(disconnect[1]),float(enumeration[1]),after_uptime],'positiveDisconnect66ThenEnumeration67':True,'identityChangedFields':changed,'sameBootAndDescriptors':True,'numericLifecycleWithinHelperUptimeBracket':True,'crossClockMappingEstablished':False,'instructionReloadProven':False,'parentOfflineTupleContract':'name,bytes,hash','finalCachedUi':j(FW/'final-ui/result.json')['after'],'chronology':chronology,'physicalPictureObserved':False,'allRamClearedProven':False,'causalRootFixProven':False,'targetOperationsByAnalyzer':0,'rootCallsByAnalyzer':0,'networkCalls':0,'gitCalls':0},sort_keys=True))
