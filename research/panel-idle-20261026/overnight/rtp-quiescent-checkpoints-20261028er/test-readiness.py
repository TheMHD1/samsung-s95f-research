#!/usr/bin/env python3
"""Mock the EM-only cached readiness builder; never imports a root adapter."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,types
D=Path(__file__).resolve().parent;checks=0

def check(ok,s):
 global checks
 if not ok:raise ValueError(s)
 checks+=1

def module(name,path):
 m=types.ModuleType(name);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
r=module('er_readiness_mock_wrapper',D/'run-once.py');builder=module('er_readiness_builder',D/'prepare-readiness.py')
check(builder.WRAPPERS=={'er':('rtp-quiescent-checkpoints-20261028er/run-once.py','er-quiescent-checkpoint-readiness-decision-v1')},'onlyEM wrapper exposed')
id={'boot':r.BOOT,'sysfsRealpath':'/sys/devices/platform/usb/usb7/7-1','sysfsStat':'42:1234','busnum':'7','devnum':'61','deviceNode':'/dev/bus/usb/007/061','nodeStat':'bd:33c:12345','descriptorsSha256':r.sha(bytes.fromhex(r.DESCRIPTORS)),'configuration':'1','authorized':'1','runtimeStatus':'active','interfaceNumber':'02','alternate':'0','interfaceClass':'ff','interfaceSubClass':'00','interfaceProtocol':'00'}
class Root:
 calls=0
 def root(self,command,record,path):
  self.calls+=1;check(self.calls==1,'onecachedmetadata request')
  check(command=='set -eu\n'+r.metadata_body(id,'ER_CURRENT_READY'),'exact inheritedcachedmetadata command')
  check(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'cached shell syntax')
  check(len(command.encode())<=8192,'cached shell bound')
  check(not any(x in command for x in ('--execute','dotnet','MODE2','input_keyevent')),'no managed/vendor/UI invocation')
  path.write_text(json.dumps({'hostMockOnly':True}))
  return 'FDCENSUS expected=120 missing=1 holders=0 errors=0\nER_CURRENT_READY\n'
root=Root();loads=[]
def mock_load(path,digest,name):
 loads.append((path,digest,name));check(digest==r.sha(path.read_bytes()),'source pin passed correctly')
 if path==D/'run-once.py':return r
 check(path==builder.ROOT and digest==builder.ROOT_SHA,'fixed root source dependency identity only');return root
builder.load=mock_load
with tempfile.TemporaryDirectory(prefix='er-readiness-host-',dir=D/'host-environment/tmp')as t:
 b=Path(t);identity=b/'identity.json';identity.write_text(json.dumps(id));note=b/'phase.md';note.write_text('SYNTHETIC HOST FIXTURE ONLY. No real target phase or endpoint queue readiness is asserted.\n');out=b/'decision'
 sys.argv=['prepare-readiness.py','--wrapper','er','--wrapper-sha256',r.sha((D/'run-once.py').read_bytes()),'--identity',str(identity),'--phase-note',str(note),'--output',str(out)]
 builder.main();n=json.loads((out/'readiness.json').read_text())
 check(n['schema']=='er-quiescent-checkpoint-readiness-decision-v1' and n['accepted']is True,'EM decision schema')
 check(n['endpointQueueProof']is False and n['identity']==id,'no queueproof invented')
 check(len(n['evidence'])==4 and r.load_readiness(out/'readiness.json',r.sha((out/'readiness.json').read_bytes()))[0]==n,'allhistorical+fresh evidenceacceptedbywrapper')
 for row in n['evidence']:check(r.sha(Path(row['path']).read_bytes())==row['sha256'],'every evidencepin current')
check(root.calls==1 and len(loads)==2,'nohidden rootretries')
print(json.dumps({'schema':'er-readiness-host-validation-v1','checksPassed':checks,'mockCachedCalls':root.calls,'targetOperations':0},sort_keys=True))
