#!/usr/bin/env python3
"""Narrow derivative qualification: pure source, retained metadata, mocked root."""
import base64
import hashlib
import json
import subprocess
import tempfile
import types
from pathlib import Path
P=Path(__file__).resolve().parent
m=types.ModuleType('fv_qualification');m.__file__=str(P/'run-once.py');exec(compile((P/'run-once.py').read_bytes(),m.__file__,'exec'),m.__dict__)
checks=0
def check(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def refuses(fn):
 try:fn()
 except (ValueError,OSError,KeyError):check(True,'expected refusal');return
 raise ValueError('unexpected acceptance')
manifest,b,payload=m.build_manifest();old=m.load_base();_,old_payload=old.build_manifest()
check(payload==old_payload,'all existing FK payload bytes unchanged')
check(b.run_command(payload)==old.run_command(payload).replace(m.OLD,m.NEW,1),'only native command delta is one mountpoint stat guard')
check(b.prefix()+b.metadata_body()==(old.prefix()+old.metadata_body()).replace(m.OLD,m.NEW,1),'only preflight command delta is one mountpoint stat guard')
check(b.execute.__code__.co_code==old.execute.__code__.co_code,'delegate lifecycle unchanged')
check(b.parse_envelope.__code__.co_code==old.parse_envelope.__code__.co_code,'delegate framing unchanged')
private=(m.FS/'guard-metadata-01/metadata.txt').read_text().splitlines()
metadata='\n'.join(['FP_METADATA_BEGIN',*private[3:7],*[s.rsplit(':',1)[0] if i<2 else s.rsplit(':',1)[0] for i,s in enumerate(private[7:11])],private[11].split()[0],'FP_METADATA_END'])+'\n'
# Directory stat rows have one fewer field than ordinary-file rows.
rows=metadata.splitlines();rows[5]=private[7].rsplit(':',2)[0];rows[6]=private[8].rsplit(':',2)[0]
metadata='\n'.join(rows)+'\n'
check(b.parse_metadata(metadata)['loadedModuleBytesAttested']is False,'actual retained metadata qualifies exact derivative')
refuses(lambda:old.parse_metadata(metadata))
for gid in range(201):
 if gid!=100:refuses(lambda gid=gid:b.parse_metadata(metadata.replace('0:100:755','0:'+str(gid)+':755')))
for before,after in [('0:100:755','1:100:755'),('0:100:755','0:100:777'),('0:0:755','0:100:755'),('0:0:644:0','0:100:644:0'),('0:0:644:226262','0:100:644:226262'),(b.MODULE_SHA,'f'*64),(' Live ',' Loading '),('FP_METADATA_END','FP_METADATA_END\nextra')]:refuses(lambda before=before,after=after:b.parse_metadata(metadata.replace(before,after)))
for command in [b.prefix()+b.metadata_body(),b.run_command(payload)]:
 check(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'shell syntax without execution')
 check(len(command.encode())<=8192,'unchanged command cap')
fixture=(b.FK/'fixture.json').read_bytes();parser=types.ModuleType('fv_fixture_parser');parser.__file__=str(b.FK/'parse-receipt.py');exec(compile((b.FK/'parse-receipt.py').read_bytes(),parser.__file__,'exec'),parser.__dict__)
def frame(receipt,rc=0):
 vals=[receipt,b'[GC_INFO]\n',b''];s='FP_RUN_BEGIN\n'+b.BOOT+'\n1.0 2.0\n'+str(rc)+'\n1\n'
 for raw in vals:s+=str(len(raw))+'\n'+m.sha(raw)+'\n'
 s+='FP_RUN_META_END\n'
 for label,raw in zip(['RECEIPT','STDOUT','STDERR'],vals):s+=label+'_B64_BEGIN\n'+base64.b64encode(raw).decode()+'\n'+label+'_B64_END\n'
 return s+'FP_RUN_COMPLETE\n'
class Fake:
 def __init__(self,kind):self.kind=kind;self.calls=[];self.native=0;self.after=0;self.did=False
 def root(self,c,record,path):
  self.calls.append(c);record['calls'].append({'command':c,'mock':True});b.save(path,record)
  if self.did:self.after+=1
  if c==b.prefix()+b.metadata_body():return metadata.replace('0:100:755','0:0:755')if self.kind=='wrong-gid'else metadata
  if c.endswith('echo FP_STAGE_CREATED\n'):return 'FP_STAGE_CREATED\n'
  if c.endswith('echo FP_STAGED_CHUNK\n'):return 'FP_STAGED_CHUNK\n'
  if c.endswith('echo FP_STAGED_FILE\n'):return 'FP_STAGED_FILE\n'
  if ' --execute > 'in c:
   self.native+=1;self.did=True
   if self.kind=='ambiguous':raise OSError('mock ambiguity')
   v=json.loads(fixture);rc=0
   if self.kind in ['zero','short']:
    n=0 if self.kind=='zero'else 1;v.update(readResult=n,returnedPrefixBytes=n,returnedPrefixSha256=m.sha(base64.b64decode(v['rawAllocationBase64'])[:n]))
   if self.kind=='native-refusal':v.update(accepted=False,readResult=-1,readErrno=5,returnedPrefixBytes=0,returnedPrefixSha256=None);rc=1
   return metadata+frame((json.dumps(v)+'\n').encode(),rc)
  if c.endswith('echo FP_FINAL_INTEGRITY_OK\n'):return 'FP_FINAL_INTEGRITY_OK\n'
  if c.endswith('echo FP_STAGE_ABSENT\n'):return 'FP_STAGE_ABSENT\n'
  raise ValueError('unexpected mock command')
(P/'host-environment/tmp').mkdir(parents=True,exist_ok=True)
cases=['success','zero','short','wrong-gid','ambiguous','native-refusal'];commands=[]
with tempfile.TemporaryDirectory(dir=P/'host-environment/tmp',prefix='fv-mock-')as temp:
 for kind in cases:
  f=Fake(kind);out=Path(temp)/kind
  if kind in ['success','zero','short']:
   result=m.execute(out,manifest,b,payload,f,parser)
   check(result['accepted']and f.native==1 and f.after==2,'single invocation and exact accepted cleanup')
   check(result['debugfsMountpointGid']==100 and result['baseResultSha256']==m.row(out/'result.json')['sha256'],'separate derivative provenance and immutable base result')
   check((out/'allocation.bin').stat().st_size==4096 and(out/'returned-prefix.bin').stat().st_size==result['returnedBytes'],'private raw retention')
   check(json.loads((out/'reviewed-manifest.json').read_bytes())['schema']=='fv-runtime-gid100-manifest-v1','composite manifest retained by base lifecycle')
  else:
   refuses(lambda:m.execute(out,manifest,b,payload,f,parser))
   check(f.after==0 and f.native==(0 if kind=='wrong-gid'else 1),'no follow-up on preflight/native refusal or ambiguity')
   check(not(out/'fv-result.json').exists(),'no derivative success artifact after refusal')
  commands.extend(f.calls)
check(all(len(c.encode())<=8192 for c in commands),'all mocked command caps')
check(all('chown 'not in c and'cat '+b.TARGET not in c for c in commands),'no ownership mutation or shell content read')
summary={'schema':'fv-host-qualification-v1','checks':checks,'mockCases':len(cases),'mockCommands':len(commands),'maxCommandBytes':max(len(c.encode())for c in commands),'metadataGidsTested':201,'rootCalls':0,'targetReads':0,'payloadsRebuilt':False,'nativeAndLifecycleUnchanged':True,'normalOptimizedChecksUseExplicitConditions':True}
print(json.dumps(summary,sort_keys=True))
