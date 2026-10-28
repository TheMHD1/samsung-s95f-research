#!/usr/bin/env python3
"""Host-only DM mocks/parser mutations; never imports root transport."""
from pathlib import Path
import base64,copy,json,subprocess,sys,tempfile,types,uuid,os,stat,resource
P=Path(__file__).resolve().parent
r=types.ModuleType('dm');r.__file__=str(P/'run-once.py');exec(compile(Path(r.__file__).read_bytes(),r.__file__,'exec'),r.__dict__)
p=r.load_pinned(P/'parse-result.py',r.PARSER_SHA,'dm_parser');checks=0;commands=[]
def check(x,s):
 global checks
 if not x:raise ValueError(s)
 checks+=1
def reject(f):
 try:f()
 except (ValueError,KeyError,TypeError,OSError,UnicodeError):check(True,'refusal');return
 raise ValueError('unexpected acceptance')
def decision():
 identity=json.loads((P/'../hdmi-endpoint-trial-20261028gp/post-back-identity/identity.json').read_text())
 return {'schema':'ha-ap-fault-witness-readiness-decision-v1','accepted':True,'identity':identity,'interfaceUnbound':True,'noHolders':True,'closedWorldVendorOutLineage':{'accepted':True,'statement':'SYNTHETIC HOST TEST ONLY using retained USB70 identity fields: not fresh queue readiness.','evidenceSha256':'a'*64},'evidence':[{'path':'/host/fake-only','sha256':'b'*64}],'endpointQueueProof':False}
def envelope(receipt,code=0,stdout=b'[GC_INF{not semantic receipt}\nO] arbitrary diagnostics',stderr=b''):
 vals=(receipt,stdout,stderr);s='HAMETA_BEGIN\n'+r.BOOT+'\n1.0 2.0\n'+str(code)+'\n'
 for b in vals:s+=str(len(b))+'\n'+r.sha(b)+'\n'
 s+='HAMETA_END\n'
 for name,b in zip(('RECEIPT','STDOUT','STDERR'),vals):s+=name+'_B64_BEGIN\n'+base64.b64encode(b).decode()+'\n'+name+'_B64_END\n'
 return s+'HARUN_COMPLETE\n'
class FakeRoot:
 def __init__(self,kind='success'):self.kind=kind;self.invocations=0;self.cleanups=0
 def root(self,command,record,path):
  commands.append(command);check(len(command.encode())<=8192,'root command bound');check(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'shell syntax');check(not any(x in command for x in ['input_keyevent','vconftool','killall','MODE2','--execute-set','--execute-restore']),'no UI/write/recovery');r.save(path,record)
  for name in ['PRE_READY','BEFORE_INVOKE_READY','POST_READY']:
   if command.endswith('echo '+name+'\n'):
    if self.kind==name:raise ValueError('identity/census refusal')
    return 'FDCENSUS expected=120 missing=1 holders=0 errors=0\n'+name+'\n'
  for marker in ['PRIVATE_STAGE_CREATED','STAGED_CHUNK','STAGED_FILE','FINAL_INTEGRITY_OK']:
   if command.endswith('echo '+marker+'\n'):return marker+'\n'
  if ' --receipt-self-test > ' in command:
   if self.kind=='selftest':return envelope(b'{"selfTestsPassed":false,"targetOperations":0}\n')
   return envelope(b'{"selfTestsPassed":516,"targetOperations":0}\n')
  if ' --execute --device ' in command:
   self.invocations+=1;check(' --execute --device 70 > ' in command,'fixed device invocation')
   if self.kind=='timeout':raise OSError('ambiguous invoke; no retry')
   if self.kind=='partial':return 'IMMEDIATE_READY\nHAMETA_BEGIN\n'
   raw=(P/'fixture.json').read_bytes()
   if self.kind=='malformed':raw=b'{"schema":'
   if self.kind=='wrong-device':n=json.loads(raw);n['device']=71;raw=json.dumps(n).encode()
   return 'IMMEDIATE_READY\n'+envelope(raw,1 if self.kind=='bad-exit' else 0,stderr=b'x' if self.kind=='stderr' else b'')
  if command.endswith('echo STAGE_ABSENT\n'):
   self.cleanups+=1
   if self.kind=='cleanup':raise OSError('cleanup ambiguity')
   return 'STAGE_ABSENT\n'
  raise ValueError('unclassified fake command')
raw=(P/'fixture.json').read_bytes();n,files,interpret=p.parse_native(raw.decode())
check(len(files)==5 and interpret['transportAccepted'] and not interpret['atomicSnapshot'] and not interpret['recoveryProven'],'prospective witness capture only')
check(interpret['apMagic']==0x1234 and interpret['apReasonHalfword10']==16 and interpret['apExcoDataMagic']==0xabcd and interpret['apExcoContextBit12']==1,'synthetic field decoding')
check(interpret['sampledMagicPairMatchesInitialBypass'] and not interpret['historicalInitialBypassProven'] and not interpret['currentPcProven'],'no historical/PC inference')
for field in p.FIELDS:
 x=copy.deepcopy(n);x.pop(field);reject(lambda:p.parse_native(json.dumps(x)))
for i in range(10):
 for key,value in [('count',-1),('beforeUs',-1),('after','Unknown'),('direction','BAD'),('errno',5),('expected',True)]:
  x=copy.deepcopy(n);x['steps'][i][key]=value;reject(lambda:p.parse_native(json.dumps(x)))
for i in range(5):
 for key,value in [('sha256','0'*64),('address',0x4013400c),('bytes',95),('name','arbitrary')]:
  x=copy.deepcopy(n);x['windows'][i][key]=value;reject(lambda:p.parse_native(json.dumps(x)))
for field,value in [('schema','eb-rtp-lane-gate-v1'),('headersSent',16),('bulkTransfers',32),('accepted',False),('released',False),('closed',False),('writes',1)]:
 x=copy.deepcopy(n);x[field]=value;reject(lambda:p.parse_native(json.dumps(x)))
for text in [raw.decode()+raw.decode(),'[GC_INFO]\n'+raw.decode(),raw.decode().replace('"schema":','"schema":"dup","schema":',1)]:reject(lambda:p.parse_native(text))
check(sum(len(v)for _,v,_ in files)==548 and len(raw)<24576,'full payload and receipt caps')
manifest,payload=r.build_manifest();reviewed=r.manifest_bytes(manifest);check(reviewed==r.manifest_bytes(r.build_manifest()[0]),'deterministic manifest')
with tempfile.TemporaryDirectory(dir=P,prefix='host-only-')as td:
 base=Path(td);ready=decision();b=json.dumps(ready).encode();rp=base/'ready.json';rp.write_bytes(b);check(r.load_readiness(rp,r.sha(b))[0]==ready,'retained actual16field identity in synthetic fresh premise')
 for k in ('accepted','interfaceUnbound','noHolders'):
  bad=copy.deepcopy(ready);bad[k]=False;br=json.dumps(bad).encode();rp.write_bytes(br);reject(lambda:r.load_readiness(rp,r.sha(br)))
 f=FakeRoot();result=r.execute(base/'success',ready,b,reviewed,payload,f,p)
 check(result['accepted'] and result['headersSent']==5 and result['bulkTransfers']==10 and len(result['rawFiles'])==5 and f.invocations==f.cleanups==1,'one read invocation and guarded cleanup')
 for kind in ('PRE_READY','BEFORE_INVOKE_READY','POST_READY','selftest','timeout','partial','malformed','wrong-device','bad-exit','stderr','cleanup'):
  f=FakeRoot(kind);out=base/kind;reject(lambda:r.execute(out,ready,b,reviewed,payload,f,p));check(f.invocations<=1,'no retry');check(f.cleanups==(1 if kind=='cleanup' else 0),'refusal retains stage')
  if kind in ('partial','malformed','wrong-device','bad-exit','stderr'):check((out/'native-envelope.txt').exists(),'envelope retained before refusal')
 for text in [envelope(b'{}')+'x',envelope(b'x'*24577),envelope(b'{}',stdout=b'x'*16385),envelope(b'{}',stderr=b'x'*2049)]:reject(lambda:r.receipt_envelope(text))
check(json.loads(subprocess.run([sys.executable,'-B',str(P/'run-once.py')],check=True,capture_output=True).stdout)['targetOperations']==0,'dry default')
body=r.metadata_body(decision()['identity'],'PRE_READY');check(body.count('bx_fd_snapshot=$(LC_ALL=C stat ')==1 and 'test "$#" -le 32768' in body,'unchanged bounded fresh FD census')
print(json.dumps({'schema':'ha-host-wrapper-qualification-v1','checksPassed':checks,'targetOperations':0,'commandsSyntaxChecked':len(commands),'maximumCommandBytes':max(len(s.encode())for s in commands),'actualIdentityReusedOnlyInHostMock':'USB70; source/R payloads are synthetic','payloadBytes':sum(len(x)for x in payload.values())},indent=2,sort_keys=True))
