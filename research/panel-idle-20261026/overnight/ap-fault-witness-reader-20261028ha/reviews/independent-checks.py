#!/usr/bin/env python3
import base64,copy,hashlib,json,os,struct,subprocess,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;P=H.parent;CHECKS=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 global CHECKS
 if not v:raise ValueError(s)
 CHECKS+=1

def module(name,file):
 m=types.ModuleType(name);m.__file__=str(file);exec(compile(file.read_bytes(),str(file),'exec'),m.__dict__);return m

def rejected(f):
 try:f()
 except (ValueError,TypeError,KeyError,UnicodeError):need(True,'rejected');return
 raise ValueError('unexpected acceptance')

def main():
 pins={'source-inventory.json':'f723782a84e856021ae60ca34df9e2274ea08b1777c7fda12da66691d7046ff3','deployment-manifest.json':'727a80b6091c8a58b297cec50cab103ee4e13873528c7475544ef2b9a3626437','run-once.py':'5d1af2292602df25f0bd84e4ea27e1894356e677daf2d2b81aaecb55bb305492','parse-result.py':'72fdfc382529e15688b762d2077ab3b009364d47b37ced99c7b3b679f9c74d24','bin/Release/net6.0/APFaultWitness.dll':'9a89568a1ea6788c46b38e73b49ac021e88b4ad7ad1453dfdb3693befdc50c3b','host-build-checkpoint.json':'6ff6ac0bb114fd6fcce0fb26f8736e6271fefcb55ed19e8c13ff0bd1d7266104','prepare-readiness.py':'b2f506847206b5ef1a5a31c45e98791283ae40011ba1d96b2ff7f50796352eb6'}
 for name,want in pins.items():need(sha((P/name).read_bytes())==want,'frozen pin '+name)
 inv=json.loads((P/'source-inventory.json').read_text());need(len(inv['files'])==27,'inventory count')
 for row in inv['files']:
  f=P/row['path'];need(not f.is_symlink() and f.is_file() and len(f.read_bytes())==row['bytes'] and sha(f.read_bytes())==row['sha256'],'inventory '+row['path'])
 r=module('ha_review_wrapper',P/'run-once.py');p=module('ha_review_parser',P/'parse-result.py')
 m,payload=r.build_manifest();need(r.manifest_bytes(m)==(P/'deployment-manifest.json').read_bytes(),'regenerated manifest exact')
 need(len(r.META_KEYS)==16 and len(payload)==3,'full identity and three payloads')
 need(p.SPECS==[('start-R',0x47012400,256),('AP',0x4500f0e0,20),('AP-EXCO-data',0x4500ff14,12),('AP-EXCO-context',0x45015924,4),('end-R',0x47012400,256)],'five exact specs')
 fixture=(P/'fixture.json').read_bytes();n,raws,i=p.parse_native(fixture.decode());need(len(raws)==5 and sum(len(v)for _,v,_ in raws)==548,'positive native fixture')
 for field in ['headersSent','bulkTransfers','writes','uiOperations','device']:
  b=copy.deepcopy(n);b[field]=True;rejected(lambda:p.parse_native(json.dumps(b)))
 for index in range(10):
  b=copy.deepcopy(n);b['steps'][index]['afterUs']=b['steps'][index]['beforeUs']-1;rejected(lambda:p.parse_native(json.dumps(b)))
 for index in range(3):
  b=copy.deepcopy(n);b['bindingChecks'][index]['ownClaim']=not b['bindingChecks'][index]['ownClaim'];rejected(lambda:p.parse_native(json.dumps(b)))
 b=copy.deepcopy(n);b['bindingChecks'][2]['follow']['inode']+=1;rejected(lambda:p.parse_native(json.dumps(b)))
 for field in ['atomicSnapshot','physicalPictureObserved','accepted','closed','released']:
  b=copy.deepcopy(n);b[field]=int(b[field]);rejected(lambda:p.parse_native(json.dumps(b)))
 for index in range(5):
  b=copy.deepcopy(n);b['windows'][index]['base64']=base64.b64encode(bytes(p.SPECS[index][2]+4)).decode();b['windows'][index]['bytes']+=4;b['windows'][index]['sha256']=sha(bytes(p.SPECS[index][2]+4));rejected(lambda:p.parse_native(json.dumps(b)))
 # Read-only acceptance must retain arbitrary complete contents without imposing a clean/magic predicate.
 for ap,data,reason,word in [(0,0,0,0),(0x1234,0xabcd,16,4096),(65535,1,65535,0xffffffff)]:
  b=copy.deepcopy(n)
  for idx,updates in [(1,[(0,'<H',ap),(16,'<H',reason)]),(2,[(0,'<H',data)]),(3,[(0,'<I',word)])]:
   v=bytearray(base64.b64decode(b['windows'][idx]['base64']))
   for offset,fmt,value in updates:struct.pack_into(fmt,v,offset,value)
   b['windows'][idx]['base64']=base64.b64encode(v).decode();b['windows'][idx]['sha256']=sha(v)
  _,_,d=p.parse_native(json.dumps(b));need(d['apReasonHalfword10']==reason and d['apExcoContextWord7c']==word,'exact independent field decode')
  need(d['sampledMagicPairMatchesInitialBypass']==(ap==0x1234 and data==0xabcd),'sampled magic only')
  need(all(d[k]is False for k in ['historicalInitialBypassProven','currentPcProven','emergencyLoopExitProven','rootResetProven','recoveryProven','physicalPictureObserved','atomicSnapshot']),'strong claims remain false')
 # Three source-only SRAM intervals are complete and cannot spill into MMIO or another bank.
 for _,a,z in p.SPECS[1:4]:need(0x45000000<=a<a+z<=0x45020000 and a%4==z%4==0,'full alias interval')
 need((P/'NativeBinding.cs').read_bytes()==(P.parent/'rtp-lane-gate-capture-20261028eb/NativeBinding.cs').read_bytes(),'native binding byte exact')
 for kind in ['source','wrapper']:
  a=(H/(kind+'.normal.json')).read_bytes();b=(H/(kind+'.optimized.json')).read_bytes();need(a==b,'normal/-O '+kind)
 env=os.environ.copy();env.update(DOTNET_CLI_HOME=str(H/'private'),TMPDIR=str(H/'private'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1',DOTNET_NOLOGO='1')
 dotnet='${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet'
 result=subprocess.run([dotnet,str(P/'bin/Release/net6.0/APFaultWitness.dll'),'--self-test'],capture_output=True,env=env,timeout=20)
 need(result.returncode==0 and result.stderr==b'' and json.loads(result.stdout)=={'selfTestsPassed':516,'targetOperations':0},'frozen DLL selftests')
 (H/'native-selftest.json').write_bytes(result.stdout)
 refusal=subprocess.run([dotnet,str(P/'bin/Release/net6.0/APFaultWitness.dll'),'--execute','--device','70'],capture_output=True,env=env,cwd=H/'private',timeout=10)
 need(refusal.returncode==64 and refusal.stdout==b'REFUSED_ARM32_ABI\n' and refusal.stderr==b'','host production refused before receipt/device access')
 need(all(sha((P/name).read_bytes())==want for name,want in pins.items()),'all final pins unchanged')
 print(json.dumps({'schema':'ha-independent-focused-validation-v1','decision':'PASS_HOST_ONLY','checks':CHECKS,'frozenPins':pins,'inventoryFiles':27,'regeneratedManifestExact':True,'inheritedSourceChecks':65,'inheritedWrapperChecks':978,'inheritedMockShells':269,'maximumMockCommandBytes':7734,'nativeSelfTests':516,'pythonNormalOptimizedExact':True,'noFunctionalSourceChanges':True,'newApIntervalsLiveQualified':False,'targetOperations':0,'networkOperations':0},indent=2,sort_keys=True))
if __name__=='__main__':main()
