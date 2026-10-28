#!/usr/bin/env python3
"""Finite GG fixed200 native-fixture/parser/wrapper tests; all transports mocked."""
import base64,copy,contextlib,io,json,shlex,subprocess,sys,tempfile,types
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent;checks=0;cases=0

def load(path):
 m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def rejects(f):
 try:f()
 except(ValueError,KeyError,TypeError,OSError,UnicodeError):ck(True,'expected refusal');return
 raise ValueError('unexpected acceptance')
r=load(P/'run-once.py');parser=load(P/'parse-result.py');cached=load(P/'cached-check.py')
f=json.loads((P/'fixture.json').read_bytes());native_report=json.loads((P/'native-tests.json').read_bytes())
ck(native_report['targetOperations']==0 and native_report['maxReceiptBytes']<24576 and native_report['maxControlPairs']==12 and native_report['maxRows']==56,'native selftest stress/budget contract')
v,rows,q=parser.parse_native((P/'fixture.json').read_text());ck(v['accepted']and len(rows)==56 and v['threshold']==200,'native generated fixed200 fixture')
branches=json.loads((P/'branch-fixtures.json').read_bytes())
for name,text in branches.items():
 cases+=1;n,rr,qq=parser.parse_native(text+'\n');ck(n['threshold']==200 and qq['accepted']is n['accepted'],'native branch schema/acceptance')
 if name in ['clean','clean-above40','quiescent','fault']:ck(n['accepted']and n['restore']=='readback-zero'and qq['terminalKnownPhase'],'accepted branch guarded cleanup '+name)
 else:ck(not n['accepted'],'native refusal not promoted '+name)
 if name=='clean-above40':ck(all(x['a0']==76 and x['c7']==1 and x['startRt']==x['endRt']==0 for x in rr),'sampled >40/C7 witness clean at200 is source context only')
 if name=='quiescent':ck(n['quiescentCycles']>0,'Q never projected clean')
 if name=='fault':ck(n['terminal']=='TransitionCaptured'and any(x['endRt']==1 for x in rr),'fault branch at200 retained')
 if name in ['initial-fault','initial-scan0']:ck(not n['armAttempted']and n['writes']==0 and not n.get('intervention',{}).get('attempted',False),'invalid initial no arm/key')
 if name in ['partial','armed-q']:ck(n['restore']=='readback-zero'and not n.get('intervention',{}).get('attempted',False),'partial/armedQ no key guarded restore')
 if name=='unknown':ck(n['phase']=='Unknown'and n['headers']==n['bulks']==1 and not n['armAttempted'],'ambiguous header no nextpair')
 if name=='clock-after-header':ck(n['phase']=='ReadyForHeader'and n['headers']==1 and n['bulks']==2,'clock error completes accepted pair')
 if name=='cleanup-drift':ck(n['loggerMayRemain']and n['restore']=='not-attempted','upper drift no guessed restoration')
# Cross-family validation never treats the40-family as200.
fnparser=load(B/'combined-event-successor-20261028fn/parse-result.py')
rejects(lambda:fnparser.parse_native((P/'fixture.json').read_text()))
rejects(lambda:parser.parse_native((B/'combined-event-successor-20261028fn/fixture.json').read_text()))
for key in ['threshold','rows','schema']:
 bad=copy.deepcopy(f)
 if key=='threshold':bad[key]=40
 elif key=='rows':bad[key]['schema']='fg-stockevent-checkpoints-v1'
 else:bad[key]='combined-event-checkpoints-fn-v1'
 rejects(lambda:parser.parse_native(json.dumps(bad)+'\n'))
for limit in [0,39,40,199,201,65535]:
 raw=bytearray(base64.b64decode(f['controls'][0]['windows'][0]['raw']));raw[0xc4:0xc6]=limit.to_bytes(2,'little');rejects(lambda:parser.rt(raw))
for offset in [0x30,0xc0]:
 for invalid in [0,40,199,201]:
  bad=copy.deepcopy(f);raw=bytearray(base64.b64decode(bad['controls'][0]['windows'][0]['raw']));raw[offset:offset+2]=invalid.to_bytes(2,'little');bad['controls'][0]['windows'][0]['raw']=base64.b64encode(raw).decode();rejects(lambda:parser.parse_native(json.dumps(bad)+'\n'))
# Fixed200 applies to every compact row, not just retained endpoints.
for cycle in range(56):
 bad=copy.deepcopy(f);raw=bytearray(base64.b64decode(bad['rows']['rawBase64']));raw[58*cycle+2:58*cycle+4]=(40).to_bytes(2,'little');bad['rows']['rawBase64']=base64.b64encode(raw).decode();bad['rows']['sha256']=r.sha(raw);rejects(lambda:parser.parse_native(json.dumps(bad)+'\n'))
for offset in range(58):
 bad=copy.deepcopy(f);raw=bytearray(base64.b64decode(bad['rows']['rawBase64']));raw[offset]^=1;bad['rows']['rawBase64']=base64.b64encode(raw).decode();bad['rows']['sha256']=r.sha(raw);rejects(lambda:parser.parse_native(json.dumps(bad)+'\n'))
for key in ['headers','bulks','inputs','writes','threshold','retries','cyclesStarted']:
 bad=copy.deepcopy(f);bad[key]=False;rejects(lambda:parser.parse_native(json.dumps(bad)+'\n'))
for ci,c in enumerate(f['controls']):
 for ti,t in enumerate(c['transfers']):
  bad=copy.deepcopy(f);bad['controls'][ci]['transfers'][ti][2]-=1;rejects(lambda:parser.parse_native(json.dumps(bad)+'\n'))
ring=bytearray(15372);ring[:2]=(4).to_bytes(2,'little');ring[12]=7;ring=bytes(ring);ck(parser.bind_rings(f,ring,ring)['postRing']['write']==4,'native sidecar hash/extent')
for bad in [b'',ring[:-1],ring[:-1]+b'x']:rejects(lambda:parser.bind_rings(f,ring,bad))
# Only fixture transport classes are loaded from FC; none of its tests/real root run.
fc=B/'reader-wake-checkpoints-20261028fc/test-runner.py';m=types.ModuleType('gg_fc_mock');m.__file__=str(fc);exec(compile(fc.read_text().split('manifest,payload=r.build_manifest();')[0],str(fc),'exec'),m.__dict__)
class Clock(m.Clock):
 def __call__(self):
  value=super().__call__()
  if self.kind=='stale'and self.calls==4:self.now+=cached.AGE_NS+1;return self.now
  if self.kind=='future'and self.calls==4:self.now-=10000000;return self.now
  return value
class Mock(m.FakeRoot):
 def __init__(self,kind='success',device=66):super().__init__(kind);self.device=device;self.fetch=0
 def response(self,c):
  if ' --receipt-self-test > 'in c:return m.envelope(b'{}'if self.kind=='selftest'else b'{"smokeTestsPassed":8,"targetOperations":0}\n')
  if 'enlightenment_info -topvwins'in c:
   self.snapshots+=1;text=m.snapshot().replace('d/apps.tab','d/ug.tab@Live')
   if self.kind!='no-saver'and not(self.kind=='settle'and self.snapshots==1):text=text.replace('volume-app ordinary OSD','ScreenSaver.dll\nvolume-app ordinary OSD')
   if self.kind=='apps':text=text.replace('d/ug.tab@Live','d/apps.tab')
   if self.kind=='no-csfs':text=text.replace('/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll','unrelated')
   return text
  if ' --execute --device 'in c:
   self.native+=1
   if self.kind=='native-ambiguous':raise OSError('synthetic native ambiguity')
   native=copy.deepcopy(f)
   if self.kind in ['initial-fault','partial','unknown']:native=json.loads(branches[self.kind])
   native['device']=self.device
   if self.kind=='wrong-limit':native['threshold']=40
   if self.kind=='late-key':
    when=native['endUs']-1;native['intervention']['endUs']=when
    for call in native['intervention']['calls']:call['beforeUs']=call['afterUs']=when
   value=m.envelope((json.dumps(native)+'\n').encode())
   if self.kind in ['initial-fault','partial','unknown']:value=value.replace('\n1.0 2.0\n0\n','\n1.0 2.0\n1\n')
   return 'IMMEDIATE_READY\n'+value
  if 'echo FN_SIDECAR_BEGIN'in c:
   self.fetch+=1;data=ring if self.kind!='sidecar-bad'else ring[:-1];return 'FN_SIDECAR_BEGIN\n'+base64.b64encode(data).decode()+'\nFN_SIDECAR_END\n'
  return super().response(c)
manifest,payload=r.build_manifest();rawmanifest=r.manifest_bytes(manifest);ck(rawmanifest==(P/'deployment-manifest.json').read_bytes(),'exact GG manifest')
r.uuid=types.SimpleNamespace(uuid4=lambda:types.SimpleNamespace(hex='a'*32))
actual66=json.loads((B/'wake-window-trial-20261028gc/identity-01/identity.json').read_bytes());ck(actual66['devnum']=='66'and len(actual66)==16,'full retained66 identity')
scratch=P/'host-environment/tmp';scratch.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='gg-mock-',dir=scratch)as temp:
 base=Path(temp);ready=m.ready();ready['schema']='gg-live-saver200-event-readiness-decision-v1';ready['identity']=actual66;evidence=base/'evidence.md';evidence.write_text('SYNTHETIC HOST ONLY explicit known-phase lineage. Not actual current queue or raised-limit readiness.');ready['evidence']=[{'path':str(evidence),'sha256':r.sha(evidence.read_bytes())}]
 for index,kind in enumerate(['success','success67','settle','late-key','apps','no-saver','no-csfs','stale','future','selftest','PRE_READY','native-ambiguous','initial-fault','partial','unknown','wrong-limit','sidecar-bad','POST_READY','cleanup']):
  cases+=1;case=copy.deepcopy(ready);device=67 if kind=='success67'else 66
  if device==67:case['identity'].update(devnum='67',deviceNode='/dev/bus/usb/007/067',nodeStat='bd:342:12345')
  rawready=json.dumps(case).encode();rp=base/'readiness.json';rp.write_bytes(rawready);ck(r.load_readiness(rp,r.sha(rawready))[0]==case,'complete exact16-field candidate identity')
  root=Mock('success'if kind=='success67'else kind,device);clock=Clock(kind);output=base/str(index)
  if kind in ['success','success67','settle','late-key']:
   result=r.execute(output,case,rawready,rawmanifest,payload,root,parser,clock,clock.sleep)
   ck(result['accepted']and result['thresholdWrites']==0 and result['wrapperUiOperations']==0 and root.ui==0 and root.native==root.cleanup==1 and root.fetch==2,'one native/no wrapperkey/guarded sidecars cleanup')
   ck(result['keyExposureQualified']is(kind!='late-key'),'protocol vs scientific key overlap separate')
   record=json.loads((output/'record.json').read_bytes());ck(record['remote_stage'].startswith('/tmp/researcher-gg-')and not record['cleanup_required'],'unique GG stage and completed lifecycle')
   line=next(line for line in root.commands[-1].splitlines()if line.startswith('rm -- '));names=[Path(s).name for s in shlex.split(line)[2:]];ck(len(names)==len(set(names))==11 and set(names)==set(r.NAMES+['selftest.receipt.json','selftest.stdout','selftest.stderr','native.receipt.json','native.stdout','native.stderr','baseline-ring.bin','post-ring.bin']),'exact eleven owned files')
   cached.validate(output,record['cachedCheckpoint'])
  else:
   rejects(lambda:r.execute(output,case,rawready,rawmanifest,payload,root,parser,clock,clock.sleep));ck(root.native<=1 and root.ui==0,'zero wrapper keys/no retries')
   if kind in ['initial-fault','partial','unknown']:
    record=json.loads((output/'record.json').read_bytes());result=json.loads((output/'result.json').read_bytes());ck(not result['accepted']and result['cleanup']=='retained'and root.fetch==root.cleanup==0,'original refused outcome no sidecar/cleanup')
    ck(' --execute --device 'in root.commands[-1]and record['target_operations_status']=='native_refused','no request after native refusal')
    if kind=='initial-fault':ck(not result['loggerMayRemain']and record['loggerPayloads']==0,'initial fault no arm payload')
   if kind in ['native-ambiguous','wrong-limit']:ck(root.fetch==root.cleanup==0,'unknown/malformed receipt no new root')
   if kind in ['apps','no-saver','no-csfs','stale','future','selftest','PRE_READY']:ck(root.native==0,'invalid cached/time/preflight prevents native')
   if kind in ['no-saver','no-csfs']:ck(root.snapshots==10,'bounded cached exhaustion no keys')
 for command in m.commands:ck(len(command.encode())<=8192 and subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'all wrapper shells bounded/syntax')
 # Readiness dry/local refusal before any root adapter import, one optional cached query only.
 pr=load(P/'prepare-readiness.py');original_load=pr.load;rootloads=[];querycommands=[]
 class CachedRoot:
  def root(self,command,record,path):
   querycommands.append(command);ck(len(command.encode())<=8192 and subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'readiness shell bounds');return 'FDCENSUS expected=100 missing=1 holders=0 errors=0\nGG_CURRENT_READY\n'
 def local_load(path,pin,name):
  if path==pr.ROOT:rootloads.append(path);return CachedRoot()
  return original_load(path,pin,name)
 pr.load=local_load;oldargv=sys.argv;identity=base/'identity.json';phase=base/'phase.md';phase.write_text('SYNTHETIC HOST ONLY current known-phase and closed world lineage, not a real queue readiness decision.')
 try:
  for kind in ['dry','bad-manifest','bad-identity','execute']:
   cases+=1;value=copy.deepcopy(actual66)
   if kind=='bad-identity':value['authorized']='0'
   r.save(identity,value);out=base/('readiness-'+kind);sys.argv=[str(P/'prepare-readiness.py'),'--wrapper','gg','--wrapper-sha256',r.sha((P/'run-once.py').read_bytes()),'--manifest-sha256','0'*64 if kind=='bad-manifest'else r.sha(rawmanifest),'--identity',str(identity),'--phase-note',str(phase),'--output',str(out)]
   if kind=='execute':sys.argv.append('--execute')
   with contextlib.redirect_stdout(io.StringIO()):
    if kind in ['bad-manifest','bad-identity']:rejects(pr.main)
    else:pr.main()
   ck(len(rootloads)==len(querycommands)==int(kind=='execute'),'zero live import before local admission/one explicit cached query')
   if kind=='execute':ck(r.load_readiness(out/'readiness.json',r.sha((out/'readiness.json').read_bytes()))[0]['accepted'],'new readiness exact contract')
   else:ck(not out.exists(),'dry or refusal no stage')
 finally:pr.load=original_load;sys.argv=oldargv
 dry=subprocess.run([sys.executable,'-B',str(P/'run-once.py')],capture_output=True);ck(dry.returncode==0 and json.loads(dry.stdout)['targetOperations']==0,'dry zero I/O')
print(json.dumps({'schema':'gg-host-validation-v1','checks':checks,'cases':cases,'shellCommands':len(m.commands)+len(querycommands),'maxCommandBytes':max(len(c.encode())for c in m.commands+querycommands),'nativeMaxReceiptBytes':native_report['maxReceiptBytes'],'completeNativeBranchFixtures':len(branches),'actualIdentityFields':len(actual66),'syntheticNextAddress':67,'wrapperUiOperations':0,'thresholdWrites':0,'targetOperations':0,'networkOperations':0},sort_keys=True))
