#!/usr/bin/env python3
"""Finite host source/pin and fixed command review; no root transport import."""
from pathlib import Path
import ast,hashlib,json,subprocess,types
P=Path(__file__).resolve().parent;checks=0
def check(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
m=types.ModuleType('fp_source');m.__file__=str(P/'run-once.py');exec(compile((P/'run-once.py').read_bytes(),m.__file__,'exec'),m.__dict__)
check(m.sha((m.FK/'host-build-checkpoint.json').read_bytes())==m.CHECKPOINT_SHA,'sealed FK checkpoint')
check(m.sha((m.FK/'source-inventory.json').read_bytes())==m.FK_INVENTORY_SHA,'sealed FK inventory')
for row in json.loads((m.FK/'source-inventory.json').read_bytes())['files']:
 b=(m.FK/row['path']).read_bytes();check(len(b)==row['bytes']and m.sha(b)==row['sha256'],'FK source '+row['path'])
for row in json.loads((m.FK/'input-pins.json').read_bytes())['inputs']:
 b=(m.B/row['path']).read_bytes();check(len(b)==row['bytes']and m.sha(b)==row['sha256'],'FK retained input '+row['path'])
for name,digest in [('independent-source-review.md','d5bc228d9379254420becf70ff4ef2601c515f258144976916d8b9eb286919a1'),('independent-validation.json','61e0721a98fa38d8e4d80bd7a8fe379af5b4a25c45069665c1ce2561ba6f23a2'),('independent-inventory.json','092a2a2ae1b57a4474c3bd227005701b12b0f2d1410563db2f724d8b6944db12')]:check(m.sha((m.FK/'reviews'/name).read_bytes())==digest,'sealed FK review '+name)
manifest,payload=m.build_manifest();check(m.manifest_bytes(manifest)==(P/'deployment-manifest.json').read_bytes(),'exact manifest')
s=(m.FK/'Program.cs').read_text()
for text in ['internal const int Capacity = 4096','internal const string Target = "/sys/kernel/debug/tcon/tcon_micom_log"','internal const string Stage = "/tmp/tcon-log-single-read-20261028fk"','RealOps.open(ReceiptPath,1|0x40|0x80|0x80000|0x8000,0x180)','ops.Read(fd,pointer)','read(fd,pointer,(UIntPtr)Capacity)']:
 check(text in s,'fixed FK source '+text)
check(m.sha((m.FK/'parse-receipt.py').read_bytes())==m.PARSER_SHA,'strict FK parser used in place')
check(m.sha(m.ROOT.read_bytes())==m.ROOT_SHA,'serialized root adapter unchanged')
root=m.ROOT.read_text()
for text in ['REMOTE_TIMEOUT_SECONDS = 45','HOST_TIMEOUT_SECONDS = 75','MAX_COMMAND = 8192','MAX_RESPONSE = 65536','timeout=HOST_TIMEOUT_SECONDS']:check(text in root,'root bound '+text)
command=m.run_command(payload);check(len(command.encode())<=8192,'native command cap');check(subprocess.run(['sh','-n'],input=command.encode(),capture_output=True).returncode==0,'native shell syntax')
check(command.count(' --execute > ')==1,'one fixed native invocation')
check('cat '+m.TARGET not in command and 'base64 '+m.TARGET not in command,'debugfs contents never read by shell')
check(command.index(m.metadata_body())<command.index(' --execute > '),'metadata guards before native invocation')
for word in ['/dev/mem','/dev/bus/usb','input_keyevent','insmod ','rmmod ','ioctl ']:check(word not in command,'no unrelated target operation '+word)
source=(P/'run-once.py').read_text();tree=ast.parse(source)
execute=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='execute')
check(sum(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='run_command'for n in ast.walk(execute))==1,'exactly one submission builder call')
check('except Exception as e:'in source and "'retries':0"in source,'refusal state/no retry declaration')
for text in ['--target','--count','--address','--timeout','--stage']:check('cli.add_argument(\''+text not in source,'no generalized CLI '+text)
print(json.dumps({'schema':'fp-source-checks-v1','checks':checks,'targetRootCalls':0,'targetReads':0,'fkCheckpointSha256':m.CHECKPOINT_SHA,'fkSourceUnchanged':True,'payloadBytes':sum(map(len,payload.values())),'nativeCommandBytes':len(command.encode()),'fixedStage':m.STAGE},sort_keys=True))
