#!/usr/bin/env python3
"""Host-only fixed rejected-stage cleanup guards; no actual root adapter load."""
from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess,sys,tempfile
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent.parent;P=D/'cleanup-rejected-stage.py'
spec=importlib.util.spec_from_file_location('ei_cleanup_under_test',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=0;commands=[]
def check(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1
def reject(fn):
 try:fn()
 except (ValueError,KeyError,TypeError,OSError):check(True,'refused');return
 raise ValueError('unexpected acceptance')
def sha(b):return hashlib.sha256(b).hexdigest()
original_read=m.ordinary
before={p:sha(original_read(p))for p in (m.ORIGINAL/'record.json',m.ORIGINAL/'native.receipt.json',m.ORIGINAL/'reviewed-manifest.json',m.ORIGINAL/'readiness-decision.json')}
plan=m.validate(m.PROOF,m.PROOF_SHA)
check(len(plan['commands'])==3 and len(plan['stageFiles'])==9,'exact3cleanupcommands9files')
check(len({r['name']for r in plan['stageFiles']})==9,'unique exact stage names')
for index,command in enumerate(plan['commands']):
 check(0<len(command.encode())<=8192,'root8KiBcommandbound')
 check(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'shell syntax')
 check(not any(x in command for x in ('/usr/bin/dotnet',' --execute','--receipt-self-test','input_keyevent','vconftool','killall','usbreset','reboot','ioctl','libusb','MODE2','> /sys/')),'no native/controller/UI/reset operation')
 check('cat /proc/sys/kernel/random/boot_id'in command,'sameboot everycommand')
 if index in (1,2):
  for row in plan['stageFiles']:
   path=plan['stage']+'/'+row['name']
   check('test ! -L '+path+'\n'in command and 'test -f '+path+'\n'in command,'each file ordinary and no symlink')
   check('sha256sum '+path+' |'in command and row['sha256']in command,'each file exact content hash')
   check('wc -c < '+path in command,'each file exact size')
rm=next(x for x in plan['commands'][2].splitlines()if x.startswith('rm -- '))
check(rm.split()[2:]==[plan['stage']+'/'+r['name']for r in plan['stageFiles']],'rm exactly9namedpaths')
check('*'not in rm and '-r'not in rm and 'rmdir -- '+plan['stage']in plan['commands'][2],'no wildcard/recursive removal')
reject(lambda:m.validate(m.PROOF,'0'*64));reject(lambda:m.validate(m.PROOF.parent/'other.json',m.PROOF_SHA))
# Override only host reads in memory; original files and production pins untouched.
proof=json.loads(original_read(m.PROOF));proof_sha=m.PROOF_SHA
for key,value in [('headers',0),('bulks',15),('nativeAccepted',True),('wrapperAccepted',True),('keyAttempted',True),('cleanCyclesCompleted',1),('phase','AwaitingIn'),('released',False),('closed',False),('stageCleanupPerformed',True)]:
 z=copy.deepcopy(proof);z['refusalClassification'][key]=value;raw=(json.dumps(z)+'\n').encode();m.PROOF_SHA=sha(raw);m.ordinary=lambda p,maximum=2*1024*1024,raw=raw:raw if p==m.PROOF else original_read(p,maximum)
 reject(lambda:m.validate(m.PROOF,m.PROOF_SHA))
for i in range(9):
 for key,value in [('bytes',proof['stageFiles'][i]['bytes']+1),('sha256','0'*64),('name','../unowned')]:
  z=copy.deepcopy(proof);z['stageFiles'][i][key]=value;raw=(json.dumps(z)+'\n').encode();m.PROOF_SHA=sha(raw);m.ordinary=lambda p,maximum=2*1024*1024,raw=raw:raw if p==m.PROOF else original_read(p,maximum);reject(lambda:m.validate(m.PROOF,m.PROOF_SHA))
m.PROOF_SHA=proof_sha;m.ordinary=original_read
pins=json.loads(original_read(m.PROOF.parent/'input-pins.json'))
for row in pins['files']:
 path=Path(row['path']);data=original_read(path)+b'!'
 m.ordinary=lambda p,maximum=2*1024*1024,path=path,data=data:data if p==path else original_read(p,maximum)
 reject(lambda:m.validate(m.PROOF,m.PROOF_SHA))
m.ordinary=original_read
class FakeRoot:
 def __init__(self,kind='success'):self.kind=kind;self.calls=0
 def root(self,command,record,path):
  self.calls+=1;commands.append(command);check(command==plan['commands'][self.calls-1],'fixedcallorder')
  record['calls'].append({'command':command,'mockOnly':True});path.write_text(json.dumps(record))
  if self.kind=='timeout'+str(self.calls):raise OSError('ambiguous mock response; preserve/no retry')
  if self.calls==1:return 'FDCENSUS expected=120 missing=1 holders='+('1'if self.kind=='metadata'else'0')+' errors=0\nEI_REJECTED_CLEANUP_READY\n'
  if self.calls==2:return 'WRONG\n'if self.kind=='integrity'else'EXACT_NINE_INTEGRITY_OK\n'
  return 'WRONG\n'if self.kind=='cleanup'else'STAGE_ABSENT\n'
tmpdir=D/'cleanup-reviews/host-environment/tmp'
with tempfile.TemporaryDirectory(prefix='ei-cleanup-',dir=tmpdir)as temp:
 temp=Path(temp);f=FakeRoot();r=m.execute(plan,f,temp/'success');check(r['accepted']is True and r['removedFiles']==9 and r['additionalVendorTransfers']==0 and r['originalWrapperRejectionPreserved']is True and r['nativeAccepted']is False and f.calls==3,'accepted cleanup only, original refusal not promoted')
 for kind,expected in [('metadata',1),('integrity',2),('cleanup',3),('timeout1',1),('timeout2',2),('timeout3',3)]:
  f=FakeRoot(kind);out=temp/kind;reject(lambda:m.execute(plan,f,out));check(f.calls==expected and not(out/'result.json').exists(),'failure stops/preserves/no retry or success')
 regular=temp/'file';regular.write_bytes(b'x');link=temp/'alias';link.symlink_to(regular)
 reject(lambda:m.ordinary(link));reject(lambda:m.ordinary(temp))
 dry=subprocess.run([sys.executable,'-B',str(P)],check=True,capture_output=True);j=json.loads(dry.stdout);check(j['targetOperations']==j['rootCalls']==0 and j['sourceSha256']==sha(P.read_bytes()),'defaultdry no target/sourcebound')
 bad=subprocess.run([sys.executable,'-B',str(P),'--execute','--source-sha256','0'*64],capture_output=True);check(bad.returncode!=0,'wrong source digest refuses before proof/root')
for p,pin in before.items():check(sha(original_read(p))==pin,'original input unchanged')
print(json.dumps({'schema':'ei-rejected-cleanup-host-tests-v1','checksPassed':checks,'rootCalls':0,'targetOperations':0,'networkOperations':0,'mockRootCalls':len(commands),'commandBytes':[len(c.encode())for c in plan['commands']],'maximumCommandBytes':max(len(c.encode())for c in plan['commands']),'frozenInputFilesMutatedInMemoryOnly':len(pins['files']),'sourceSha256':sha(P.read_bytes()),'proofSha256':m.PROOF_SHA},sort_keys=True))
