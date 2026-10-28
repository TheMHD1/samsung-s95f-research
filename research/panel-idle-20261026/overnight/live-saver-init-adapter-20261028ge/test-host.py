#!/usr/bin/env python3
"""Bounded GE mock/source refusal tests; no real root adapter or network load."""
import base64,copy,contextlib,hashlib,io,json,shutil,subprocess,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent;checks=0;cases=0;commands=[]
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def rejects(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):ck(True,'expected refusal');return
 raise ValueError('unexpected acceptance')
def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
w=load(P/'run-once.py');policy=load(P/'policy.py');h=load(P/'helper.py');admit=load(P/'admit-fault.py')
DH=B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py';dh=load(DH)
FW=B/'combined-live-trigger-trial-20261028fw';cap=FW/'fault-capture-01';ready=json.loads((cap/'readiness-decision.json').read_bytes());identity=ready['identity'];result_pin=sha((cap/'result.json').read_bytes())
proof=admit.admit(cap,result_pin,identity);ck(proof['accepted']and proof['exactRootCommandsReplayed']==28,'strict actual full fault source replay')
manifest,payload=w.build_manifest();manifest_raw=w.manifest_bytes(manifest);ck(manifest_raw==(P/'deployment-manifest.json').read_bytes(),'sealed manifest')
ck(payload==dh.contract(),'exact native payloads')
framed=(FW/'recovery-01/mode2/framed.txt').read_text();receipt=(FW/'recovery-01/mode2/receipt.txt').read_bytes();policy.validate_framed(framed)
metadata=(cap/'metadata-pre.txt').read_text()
valid_snapshot=policy.BOOT+'\n1.00 2.00\nmemory/eden/current_tab, value = d/ug.tab@Live (String)\nScreenSaver.dll\n/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll\n1.01 2.00\n'
public=policy.BOOT+'\n1.00 2.00\nmemory/enterprise/swupgrade/working_status, value = 0 (Int32)\n   string "lcdon"\n   int32 1\n   int32 0\n1.01 2.00\n'

def snapshot(kind):
 text=valid_snapshot
 if kind=='apps':text=text.replace('d/ug.tab@Live','d/apps.tab')
 if kind=='no-saver':text=text.replace('ScreenSaver.dll','unrelated')
 if kind=='no-csfs':text=text.replace('/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll','unrelated')
 if kind=='duplicate':text=text.replace('memory/eden/current_tab, value = d/ug.tab@Live (String)\n','memory/eden/current_tab, value = d/ug.tab@Live (String)\n'*2)
 if kind=='wrong-boot':text=text.replace(policy.BOOT,'bad-boot')
 if kind=='truncated':text=text[:-1]
 if kind=='oversized':text+='x'*65536
 if kind=='uptime':text=text.replace('1.01 2.00','0.99 2.00')
 return text
class Clock:
 def __init__(self,kind):self.kind=kind;self.n=0;self.value=1000000000
 def __call__(self):
  self.n+=1;self.value+=1000000
  if self.n==5:
   if self.kind=='stale':self.value+=policy.AGE_NS+1
   if self.kind=='future':self.value-=10000000
   if self.kind=='clock-error':raise OSError('synthetic dispatch clock')
  return self.value
class Mock:
 def __init__(self,kind='success'):self.kind=kind;self.commands=[];self.snapshots=0;self.publics=0;self.native=0;self.cleanup=0;self.stage=0
 def root(self,command,record,path):
  ck(type(command)is str and 0<len(command.encode())<=8192,'command bound');commands.append(command);self.commands.append(command)
  syntax=subprocess.run(['sh','-n'],input=command.encode(),capture_output=True);ck(syntax.returncode==0,'generated shell syntax')
  if 'enlightenment_info -topvwins'in command:
   self.snapshots+=1;kind=self.kind[8:]if self.kind.startswith('initial-')and self.snapshots==1 else self.kind[4:]if self.kind.startswith('pre-')and self.snapshots==2 else self.kind[5:]if self.kind.startswith('post-')and self.snapshots==3 else'success';text=snapshot(kind)
  elif 'BurnInProtectionInProgress'in command:
   self.publics+=1;text=public
   if self.kind=='initial-public'and self.publics==1 or self.kind=='pre-public'and self.publics==2:text=text.replace('lcdon','lcdoff')
  elif 'GE_INITIAL_READY'in command or 'GE_BEFORE_NATIVE'in command:
   marker='GE_INITIAL_READY'if 'GE_INITIAL_READY'in command else'GE_BEFORE_NATIVE';text=metadata.replace('PRE_READY',marker)
   if self.kind=='pre-identity'and marker=='GE_BEFORE_NATIVE':text=text.replace(marker,'WRONG')
  elif 'mkdir /tmp/s95f-mode2-'in command:
   self.stage+=1;text=''
   if self.kind=='stage-error':raise OSError('synthetic staging failure')
  elif 'echo HELPER_EXIT'in command:
   self.native+=1
   if self.kind=='native-ambiguous':raise OSError('synthetic native ambiguity')
   text=framed
   if self.kind in ['native-exit','native-timeout']:text=text.replace('HELPER_EXIT\n0\n','HELPER_EXIT\n'+('142'if self.kind=='native-timeout'else'1')+'\n')
   if self.kind=='native-stderr':text=text.replace('NATIVE_STDERR_BASE64\n','NATIVE_STDERR_BASE64\neA==\n')
   if self.kind=='native-oversized':text+='x'*65536
   if self.kind=='native-frame':text=text+'TRAILING\n'
   if self.kind in ['native-ioctl','native-close','native-abi']:
    changed=receipt.replace(b'IOCTL_RETURN=0',b'IOCTL_RETURN=-1')if self.kind=='native-ioctl'else receipt.replace(b'CLOSE_RETURN=0',b'CLOSE_RETURN=-1')if self.kind=='native-close'else receipt.replace(b'PTR_BYTES=4',b'PTR_BYTES=8')
    before=text.split('RECEIPT_BASE64\n')[0]+'RECEIPT_BASE64\n';tail='NATIVE_STDERR_BASE64\n'+text.split('NATIVE_STDERR_BASE64\n')[1];text=before+base64.b64encode(changed).decode()+'\n'+tail
  elif 'rm -- DeadlineMode2.dll'in command:
   self.cleanup+=1;text=''
   if self.kind=='cleanup-error':raise OSError('synthetic cleanup failure')
  else:text=''
  record.setdefault('calls',[]).append({'command':command,'stdout':text});w.save(path,record);return text

scratch=P/'host-environment/tmp';scratch.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='ge-tests-',dir=scratch)as temp:
 base=Path(temp)
 # Real frozen source replays and focused corruption refusals stay entirely local.
 for case in ['accepted-false','bad-manifest','wrong-count','uncleaned','raw-mismatch','raw-inventory','release-false','unknown-phase','limit200','logger-owned','unstable-R','missing-tail','cleanup-stdout','identity']:
  cases+=1;d=base/('source-'+case);shutil.copytree(cap,d);rr=json.loads((d/'result.json').read_bytes());nn=json.loads((d/'native.receipt.json').read_bytes());ii=copy.deepcopy(identity)
  if case=='accepted-false':rr['accepted']=False
  if case=='bad-manifest':rr['manifestSha256']='0'*64
  if case=='wrong-count':rr['headersSent']=14
  if case=='uncleaned':rr['cleanup']='retained'
  if case=='raw-mismatch':(d/'X.bin').write_bytes(bytes(96))
  if case=='raw-inventory':rr['rawFiles'][0]['sha256']='0'*64
  if case=='release-false':nn['released']=False
  if case=='unknown-phase':nn['protocolPhase']='Unknown'
  if case in ['limit200','logger-owned','unstable-R']:
   for win in nn['windows']:
    if win['name']in ['start-R','end-R']and(case!='unstable-R'or win['name']=='end-R'):
     raw=bytearray(base64.b64decode(win['base64']));offset=0xc4 if case=='limit200'else 6 if case=='logger-owned'else 0x20;raw[offset:offset+2]=(200 if case=='limit200'else 1).to_bytes(2,'little');win['base64']=base64.b64encode(raw).decode();win['sha256']=sha(raw)
  if case in ['missing-tail','cleanup-stdout']:
   rec=json.loads((d/'record.json').read_bytes())
   if case=='missing-tail':rec['calls'].pop()
   else:rec['calls'][-1]['response']['commands'][0]['stdout']='NOT_REMOVED\n'
   w.save(d/'record.json',rec)
  if case=='identity':ii['devnum']='66'
  w.save(d/'result.json',rr);w.save(d/'native.receipt.json',nn)
  rejects(lambda:admit.admit(d,sha((d/'result.json').read_bytes()),ii))
 # Complete orchestrated helper attempts, with exact zero-UI and no-fallback assertions.
 kinds=['success','initial-apps','initial-no-saver','initial-no-csfs','initial-duplicate','initial-wrong-boot','initial-truncated','initial-oversized','initial-uptime','initial-public','stage-error','pre-identity','pre-public','pre-apps','pre-no-saver','stale','future','clock-error','native-ambiguous','native-exit','native-timeout','native-stderr','native-oversized','native-frame','native-ioctl','native-close','native-abi','cleanup-error','post-apps','post-no-saver']
 h.uuid=dh.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32))
 original_load=w.load
 def test_load(path,pin,name):
  ck(sha(path.read_bytes())==pin,'local import pin')
  if path==P/'helper.py':return h
  return original_load(path,pin,name)
 w.load=test_load
 for kind in kinds:
  cases+=1;root=Mock(kind);out=base/('execute-'+kind);error=None
  try:returned=w.execute(out,ready,(cap/'readiness-decision.json').read_bytes(),manifest_raw,payload,proof,root,Clock(kind))
  except(ValueError,OSError,KeyError,TypeError)as exc:error=exc
  record=json.loads((out/'result.json').read_bytes());ck(record['wrapperUiOperations']==record['automaticRetries']==record['thresholdWrites']==record['vendorReads']==0,'zero unrelated actions')
  ck(root.native<=1 and root.cleanup<=1 and not any('input_keyevent'in c for c in root.commands),'one shot no keys')
  ck(record['initializationPrerequisiteQualified']is False and record['newInstanceQualified']is False and record['freshEbBaselineQualified']is False,'parent postconditions stay unproven')
  if kind=='success':
   ck(error is None and returned['accepted']and root.native==root.cleanup==1 and root.snapshots==3 and root.publics==2,'full positive sequence')
   ck(returned['nativeTerminalAccepted']and returned['helperCleanupConfirmed']and returned['postCachedContextQualified'],'separate successful outcome fields')
   successful_commands=list(root.commands)
  else:
   ck(error is not None and record['accepted']is False,'negative overall admission '+kind)
   if kind.startswith('initial-'):ck(root.stage==root.native==root.cleanup==0,'no staging after initial rejection')
   elif kind.startswith('pre-')or kind in ['stale','future','clock-error','stage-error']:ck(root.native==root.cleanup==0,'no native after preinvoke refusal')
   elif kind.startswith('post-'):ck(root.native==root.cleanup==1 and record['nativeTerminalAccepted']and record['helperCleanupConfirmed']and not record['postCachedContextQualified'],'post failure preserves terminal success')
   else:
    ck(root.native==1 and root.snapshots==2 and root.cleanup==int(kind=='cleanup-error'),'native ambiguity/refusal has no postquery/retry')
    if kind=='cleanup-error':ck(record['nativeTerminalAccepted']and not record['helperCleanupConfirmed'],'terminal success separate from cleanup failure')
 # Generate original DH execution through the same mock, compare every inherited command byte.
 original=Mock();oldload=dh.load
 def dhload(path,pin,name):return original if path==dh.ADAPTER else oldload(path,pin,name)
 dh.load=dhload;dh.execute(base/'original-dh',payload)
 inherited=[c for c in successful_commands if 'enlightenment_info -topvwins'not in c and 'BurnInProtectionInProgress'not in c and 'GE_INITIAL_READY'not in c and 'GE_BEFORE_NATIVE'not in c]
 ck(inherited==original.commands,'all staging/native/cleanup commands byte-identical DH')
 # Framing and predicate independent finite boundaries.
 for kind in ['apps','no-saver','no-csfs','duplicate','wrong-boot','truncated','oversized','uptime']:cases+=1;rejects(lambda:policy.parse_snapshot(snapshot(kind)))
 for broken in [framed[:-1],framed+'x',framed.replace('BEFORE\n','BEFORE\nBEFORE\n'),framed.replace('HELPER_EXIT\n0\n','HELPER_EXIT\ntrue\n'),framed.replace('NATIVE_STDERR_BASE64\n','NATIVE_STDERR_BASE64\n!!!!'),framed.replace('RECEIPT_BASE64\n','RECEIPT_BASE64\n'+'A'*12000)]:cases+=1;rejects(lambda:policy.validate_framed(broken))
 for age in [-1,0,1000000000,1000000001]:
  cases+=1;checkpoint={'queryReturnedHostMonotonicNs':2000000000}
  if 0<=age<=1000000000:policy.dispatch(checkpoint,lambda:2000000000+age);ck(checkpoint['hostSubmissionAgeNs']==age,'inclusive freshness bound')
  else:rejects(lambda:policy.dispatch(checkpoint,lambda:2000000000+age))
 for bad in [True,1.5,-1]:cases+=1;rejects(lambda:policy.stamp(lambda:bad))
 # Dry CLI never imports root or stages a target helper.
 dry=subprocess.run([sys.executable,'-B',str(P/'run-once.py')],capture_output=True);ck(dry.returncode==0 and json.loads(dry.stdout)['targetOperations']==0,'dry zero I/O')
 # Same exact cached readiness identity check with only GE schema substitution.
 valid=copy.deepcopy(ready);valid['schema']='ge-live-saver-init-readiness-decision-v1';rd=base/'ready.json';w.save(rd,valid);ck(w.load_readiness(rd,sha(rd.read_bytes()))[0]==valid,'unique readiness family exact identity')
 for key,value in [('accepted',False),('interfaceUnbound',False),('noHolders',False),('schema','eb-rtp-lane-gate-readiness-decision-v1')]:
  cases+=1;bad=copy.deepcopy(valid);bad[key]=value;w.save(rd,bad);rejects(lambda:w.load_readiness(rd,sha(rd.read_bytes())))
 # Local main refusal happens before the real root module can be loaded.
 oldargv=sys.argv;root_loads=[]
 def prohibit_root(path,pin,name):
  if path==w.ROOT:root_loads.append(path);raise ValueError('live import forbidden')
  return original_load(path,pin,name)
 w.load=prohibit_root;w.save(rd,valid)
 sys.argv=[str(P/'run-once.py'),'--execute','--manifest-sha256',sha(manifest_raw),'--capture',str(cap),'--capture-result-sha256','0'*64,'--readiness',str(rd),'--readiness-sha256',sha(rd.read_bytes()),'--output',str(base/'must-not-exist')]
 try:rejects(w.main)
 finally:sys.argv=oldargv
 ck(root_loads==[]and not(base/'must-not-exist').exists(),'source fault rejection before root import/output')
 # Readiness builder admits locally before exactly one optional cached request.
 pr=load(P/'prepare-readiness.py');prload=pr.load;rootloads=[];readycommands=[]
 class CachedRoot:
  def root(self,command,record,path):
   commands.append(command);readycommands.append(command)
   ck(len(command.encode())<=8192 and subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'readiness command bound/syntax')
   ck('input_keyevent'not in command and 'DeadlineMode2.dll'not in command,'cached readiness only')
   return 'FDCENSUS expected=100 missing=1 holders=0 errors=0\nGE_CURRENT_READY\n'
 def pr_local(path,pin,name):
  if path==pr.ROOT:rootloads.append(path);return CachedRoot()
  return prload(path,pin,name)
 pr.load=pr_local;oldargv=sys.argv;identitypath=base/'identity.json';phase=base/'phase.txt';phase.write_text('SYNTHETIC HOST ONLY explicit known phase and closed world lineage. Not actual queue readiness.')
 try:
  for kind in ['dry','bad-manifest','bad-identity','execute']:
   cases+=1;value=copy.deepcopy(identity)
   if kind=='bad-identity':value['authorized']='0'
   w.save(identitypath,value);out=base/('readiness-'+kind)
   sys.argv=['prepare-readiness.py','--wrapper','ge','--wrapper-sha256',sha((P/'run-once.py').read_bytes()),'--manifest-sha256','0'*64 if kind=='bad-manifest'else sha(manifest_raw),'--identity',str(identitypath),'--phase-note',str(phase),'--output',str(out)]
   if kind=='execute':sys.argv.append('--execute')
   with contextlib.redirect_stdout(io.StringIO()):
    if kind in ['bad-manifest','bad-identity']:rejects(pr.main)
    else:pr.main()
   ck(len(rootloads)==len(readycommands)==int(kind=='execute'),'no readiness target import before local admission')
   if kind=='execute':ck(w.load_readiness(out/'readiness.json',sha((out/'readiness.json').read_bytes()))[0]['accepted'],'fresh GE readiness exact loader')
   else:ck(not out.exists(),'dry/refused readiness no output stage')
 finally:pr.load=prload;sys.argv=oldargv
print(json.dumps({'schema':'ge-host-validation-v1','checks':checks,'cases':cases,'shellCommands':len(commands),'maxCommandBytes':max(len(c.encode())for c in commands),'actualEbSourceCommandsReplayed':28,'identityFields':len(identity),'nativeDeadlineSeconds':12,'wrapperUiOperations':0,'nativePayloadAndCommandsUnchanged':True,'targetOperations':0,'networkOperations':0},sort_keys=True))
