#!/usr/bin/env python3
"""Fixed runtime-qualified debugfs mount GID derivative of immutable FP."""
import argparse
import hashlib
import json
import types
from pathlib import Path

HERE=Path(__file__).resolve().parent
B=HERE.parent
FP=B/'tcon-log-single-read-adapter-20261028fp'
FS=B/'internal-log-trial-20261028fs'
FP_WRAPPER='787ee87835b8b88a980b7cac1f26a30badb09cff80ab344cd0246164756037c0'
FP_MANIFEST='a31f30847f9c5ac8de666a29183c8c8256c846164b432164c28fa1912d11f350'
FP_INVENTORY='b754f996b570ff944730e1084178144b0b4a25c411fab8a724905f46b3cbf0f2'
FP_REVIEW='857d83329027a5ea680b06a0fc8d9f5bc4759294ed9196415b83d17962a175c4'
FP_VALIDATION='b39aaad5865fc9cdb7d43b973b952650c6edaaa85fd54c2e41af7bb0aefa6b70'
CHECKPOINT='edf69678846b979d8e0be85e12745ce51e966d6bb0c0e9c96c11f152c180906c'
OLD='test "$(stat -c "%u:%g:%a" /sys/kernel/debug)" = 0:0:755\n'
NEW='test "$(stat -c "%u:%g:%a" /sys/kernel/debug)" = 0:100:755\n'
SOURCES=['run-once.py','qualify.py','finalize.py','README.md','input-pins.json']

def need(v,s):
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def row(p):
 b=p.read_bytes();return {'bytes':len(b),'sha256':sha(b)}
def raw_manifest(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def load_base():
 raw=(FP/'run-once.py').read_bytes();need(sha(raw)==FP_WRAPPER,'sealed FP wrapper')
 m=types.ModuleType('fv_frozen_fp');m.__file__=str(FP/'run-once.py');exec(compile(raw,m.__file__,'exec'),m.__dict__)
 return m
def qualify_mount(m):
 original_body=m.metadata_body;original_parser=m.parse_metadata
 def body():
  s=original_body();need(s.count(OLD)==1 and NEW not in s,'one exact fixed mountpoint guard')
  return s.replace(OLD,NEW,1)
 def parse(text):
  lines=text.splitlines()
  need(len(lines)==11 and lines[5]=='0:100:755','exact runtime-qualified mountpoint root UID/GID100/0755')
  lines[5]='0:0:755'
  return original_parser('\n'.join(lines)+'\n')
 m.metadata_body=body;m.parse_metadata=parse
 return m
def build_manifest():
 for name,h in [('deployment-manifest.json',FP_MANIFEST),('source-inventory.json',FP_INVENTORY),('reviews/independent-adapter-review.md',FP_REVIEW),('reviews/independent-validation.json',FP_VALIDATION)]:need(row(FP/name)['sha256']==h,'sealed FP '+name)
 inventory=json.loads((FP/'source-inventory.json').read_bytes())
 for r in inventory['files']:need(row(FP/r['path'])=={'bytes':r['bytes'],'sha256':r['sha256']},'FP authored pin '+r['path'])
 inputs=json.loads((HERE/'input-pins.json').read_bytes())
 for r in inputs['files']:need(row(B/r['path'])=={'bytes':r['bytes'],'sha256':r['sha256']},'retained runtime pin '+r['path'])
 metadata=(FS/'guard-metadata-01/metadata.txt').read_text().splitlines()
 need(len(metadata)==13 and metadata[7]=='0:100:755:0:directory','retained actual root/GID100 debugfs mountpoint')
 comparison=json.loads((FS/'guard-metadata-01/comparison.json').read_bytes())
 need(comparison['sameExpectedBoot']and comparison['sameExpectedKernel']and comparison['onDiskModuleHashMatches']and comparison['nativeInvocations']==comparison['debugfsContentReads']==0,'separate runtime metadata qualification')
 base=load_base();old,payload=base.build_manifest();need(base.manifest_bytes(old)==(FP/'deployment-manifest.json').read_bytes(),'base manifest byte exact')
 qualify_mount(base)
 manifest={'schema':'fv-runtime-gid100-manifest-v1','baseManifestSha256':FP_MANIFEST,'baseInventorySha256':FP_INVENTORY,'baseReviewSha256':FP_REVIEW,'baseValidationSha256':FP_VALIDATION,'fkCheckpointSha256':CHECKPOINT,'sources':{n:row(HERE/n)for n in SOURCES},'runtimeMountpoint':{'path':'/sys/kernel/debug','uid':0,'gid':100,'mode':'755','symlinkAllowed':False},'otherMetadataGuardsUnchanged':True,'nativePayloadsUnchanged':True,'fixedStage':base.STAGE,'fixedTarget':base.TARGET,'allocation':4096,'readCount':4096,'nativeInvocations':1,'retries':0,'commandCap':8192,'responseCap':65536,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'completeLogProven':False,'loadedModuleBytesAttested':False,'physicalPictureObserved':False}
 return manifest,base,payload
def execute(output,manifest,base,payload,root,parser):
 # FP owns lifecycle, raw retention, one native invocation and exact cleanup.
 # Exceptions propagate without a second target call or hidden cleanup.
 result=base.execute(output,raw_manifest(manifest),payload,root,parser)
 family={'schema':'fv-wrapper-result-v1','accepted':result['accepted'],'manifestSha256':sha(raw_manifest(manifest)),'baseFamily':'fp-wrapper-result-v1','baseResultSha256':row(output/'result.json')['sha256'],'debugfsMountpointUid':0,'debugfsMountpointGid':100,'otherGuardsUnchanged':True,'nativePayloadsUnchanged':True,'nativeInvocations':result['nativeInvocations'],'readAttempted':result['readAttempted'],'returnedBytes':result['returnedBytes'],'cleanup':result['cleanup'],'retries':0,'completeLogProven':False,'copyCompletionAttested':False,'loadedModuleBytesAttested':False,'externalRtpProducerProven':False,'physicalPictureObserved':False}
 base.save(output/'fv-result.json',family)
 return family
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--print-manifest',action='store_true');p.add_argument('--manifest-sha256');p.add_argument('--checkpoint-sha256');p.add_argument('--output',type=Path);a=p.parse_args()
 need(not(a.execute and a.print_manifest),'one mode')
 if not a.execute and not a.print_manifest:
  print(json.dumps({'schema':'fv-dry-v1','rootCalls':0,'targetReads':0,'nativeInvocations':0,'explicitExecuteRequired':True},sort_keys=True));return
 manifest,base,payload=build_manifest();raw=raw_manifest(manifest)
 if a.print_manifest:print(raw.decode(),end='');return
 need(a.manifest_sha256==sha(raw)and a.checkpoint_sha256==CHECKPOINT and a.output is not None,'exact reviewed manifest/checkpoint and fresh output required')
 parser=base.load_pinned(base.FK/'parse-receipt.py',base.PARSER_SHA,'fv_frozen_fk_parser')
 root=base.load_pinned(base.ROOT,base.ROOT_SHA,'fv_serial_root')
 need((root.REMOTE_TIMEOUT_SECONDS,root.HOST_TIMEOUT_SECONDS,root.MAX_COMMAND,root.MAX_RESPONSE)==(45,75,8192,65536),'unchanged root bounds')
 print(json.dumps(execute(a.output,manifest,base,payload,root,parser),sort_keys=True))
if __name__=='__main__':main()
