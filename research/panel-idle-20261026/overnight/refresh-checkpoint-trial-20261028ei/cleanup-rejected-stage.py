#!/usr/bin/env python3
"""Dry-default exact-nine-file EH AlreadyFaulted stage cleanup; no USB/UI/reset."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;B=HERE.parent
ORIGINAL=HERE/'onset-01';PROOF=HERE/'refusal-analysis/decoded.json';OUTPUT=HERE/'onset-01-cleanup'
WRAPPER=B/'rtp-refresh-checkpoints-20261028eh/run-once.py'
WRAPPER_SHA='4870a6a0c089a739e6bc8af4f3b9076dc73bc5cf21123a2a0b8305ef206dfc15'
MANIFEST_SHA='d0059b32e4e3d99a398a3763934e8927cd2967126c6d1ad9e76d8bf069f3059e'
ROOT=B/'managed-ui-tab-launch/root-with-margin.py';ROOT_SHA='bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
PROOF_SHA='38357e12c60aae689e546f19a744c98e7d4c83bd1b756541f0955e9537fdf5de'
ANALYZER_SHA='07eea42e29abbc20fe2776f43083a5bf71005e2b2084780dae79e768d619c641'
ANALYSIS_INVENTORY_SHA='4e5ae2b0da9553890e4a981d90868a41a2a31c7b226c27ce53fba347a6434a6b'
PINS_SHA='8cc7a56f867f28228f3ff37b2cf527dcbac7309084923bcfc0199e4e122ab050'
OUTPUT_NAMES=tuple(tag+suffix for tag in ('selftest','native')for suffix in ('.receipt.json','.stdout','.stderr'))

def need(ok,reason):
 if not ok:raise ValueError(reason)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ordinary(path,maximum=2*1024*1024):
 st=path.lstat();need(stat.S_ISREG(st.st_mode)and not path.is_symlink()and 0<=st.st_size<=maximum,'bounded ordinary local file '+path.name)
 return path.read_bytes()
def load(path,pin,name):
 raw=ordinary(path);need(sha(raw)==pin,'frozen source '+name)
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def validate(proof_path,proof_sha):
 need(proof_path==PROOF and proof_path.is_absolute()and proof_sha==PROOF_SHA and re.fullmatch('[0-9a-f]{64}',proof_sha)is not None,'exact frozen classifier proof/path/digest')
 need(sha(ordinary(PROOF))==PROOF_SHA,'classifier proof bytes')
 need(sha(ordinary(PROOF.parent/'analyze.py'))==ANALYZER_SHA,'classifier source bytes')
 need(sha(ordinary(PROOF.parent/'source-inventory.json'))==ANALYSIS_INVENTORY_SHA,'classifier inventory bytes')
 need(sha(ordinary(PROOF.parent/'input-pins.json'))==PINS_SHA,'classifier input pins bytes')
 eh=load(WRAPPER,WRAPPER_SHA,'cleanup_frozen_eh');strict=eh.strict_json
 pins=strict(ordinary(PROOF.parent/'input-pins.json').decode());need(pins.get('schema')=='ei-refusal-input-pins-v1'and type(pins.get('files'))is list and 1<=len(pins['files'])<=128,'bounded frozen classifier inputs')
 seen=set()
 for row in pins['files']:
  need(type(row)is dict and set(row)=={'path','bytes','sha256'}and type(row['path'])is str and type(row['bytes'])is int and 0<=row['bytes']<=2*1024*1024,'exact bounded classifier input row')
  path=Path(row['path']);need(path.is_absolute()and path.is_relative_to(B)and path not in seen,'fixed distinct local classifier input path');seen.add(path)
  data=ordinary(path);need(len(data)==row['bytes']and sha(data)==row['sha256'],'classifier input remains byte-exact '+path.name)
 need(all(ORIGINAL/name in seen for name in ('record.json','native.receipt.json','readiness-decision.json','reviewed-manifest.json','native-envelope.txt','selftest-envelope.txt',*OUTPUT_NAMES)),'classifier pins every original cleanup input')
 proof=strict(ordinary(PROOF).decode());need(proof.get('schema')=='ei-already-faulted-analysis-v1','completed refusal classifier schema')
 expected={'nativeObservationCompleted':True,'nativeAccepted':False,'wrapperAccepted':False,'wrapperStoppedAtNonzeroNativeExit':True,'terminalReason':'AlreadyFaulted','keyAttempted':False,'cleanCyclesCompleted':0,'headers':8,'bulks':16,'phase':'ReadyForHeader','released':True,'closed':True,'stageCleanupPerformed':False}
 c=proof.get('refusalClassification');need(type(c)is dict,'refusal classification object')
 for k,value in expected.items():need(type(c.get(k))is type(value)and c[k]==value,'exact refusal classification '+k)
 need(proof.get('manifestSha256')==MANIFEST_SHA and proof.get('inputPinsSha256')==PINS_SHA,'classified manifest/input identities')
 replay=proof.get('exactRootCommandReplay');need(type(replay)is dict and type(replay.get('calls'))is int and replay['calls']==36 and replay.get('allSavedArtifactsByteExact')is True,'completed exact original command/artifact replay')
 manifest,payload=eh.build_manifest();manifest_raw=eh.manifest_bytes(manifest)
 need(sha(manifest_raw)==MANIFEST_SHA and ordinary(ORIGINAL/'reviewed-manifest.json')==manifest_raw,'original frozen EH manifest')
 record_raw=ordinary(ORIGINAL/'record.json');record=strict(record_raw.decode())
 need(record.get('schema')=='eh-refresh-checkpoint-wrapper-record-v1'and record.get('manifestSha256')==MANIFEST_SHA,'original wrapper record')
 stage=record.get('remote_stage');need(type(stage)is str and re.fullmatch('/tmp/researcher-eh-[0-9a-f]{32}',stage)is not None,'exact original EH stage')
 need(sha(stage.encode())==proof.get('privateStageSha256'),'classifier original stage binding')
 need(type(record.get('native_invocations'))is int and record['native_invocations']==1 and record.get('cleanup_required')is True and record.get('no_retry')is True and record.get('phase')=='native'and record.get('wrapperUiOperations')==0,'original rejected invocation/cleanup status')
 need(not (ORIGINAL/'result.json').exists()and not (ORIGINAL/'interpretation.json').exists(),'original wrapper refusal retained without success result/projection')
 ready_raw=ordinary(ORIGINAL/'readiness-decision.json');ready=strict(ready_raw.decode());need(sha(ready_raw)==record.get('readinessSha256')==proof.get('readinessSha256'),'original readiness proof identity')
 identity=ready['identity'];need(identity['boot']==eh.BOOT and identity['devnum']=='60'and identity['busnum']=='7'and identity['interfaceNumber']=='02','fixed boot/bus/device/interface')
 need(ready.get('schema')=='eh-refresh-checkpoint-readiness-decision-v1'and ready.get('accepted')is True and ready.get('interfaceUnbound')is True and ready.get('noHolders')is True,'original accepted cached readiness')
 # EH's frozen loader validates the entire identity/evidence shape without a call.
 eh.load_readiness(ORIGINAL/'readiness-decision.json',sha(ready_raw))
 need(type(record.get('calls'))is list and len(record['calls'])==36,'exact original completed call count')
 for item in record['calls']:
  need(item.get('host_timeout')is False and type(item.get('transport_exit'))is int and item['transport_exit']==0,'unambiguous root transport return')
  response=item['response'];need(response.get('authenticated')is True and type(response.get('uid'))is int and response['uid']==0 and type(response.get('euid'))is int and response['euid']==0,'authenticated ordinary root result')
  commands=response['commands'];need(type(commands)is list and len(commands)==1,'one exact root command')
  row=commands[0];need(row['command']==item['command']and type(row.get('exit_code'))is int and row['exit_code']==0 and row.get('timed_out')is False and row.get('stderr')=='','unambiguous completed root command')
 all_remote=dict(payload);need(set(payload)==set(eh.NAMES)and len(payload)==3,'three exact managed payloads')
 for tag,exit_code in (('selftest',0),('native',1)):
  text=ordinary(ORIGINAL/(tag+'-envelope.txt')).decode()
  response=next((x['response']['commands'][0]for x in reversed(record['calls'])if (' --receipt-self-test > 'if tag=='selftest'else' --execute --device 60 > ')in x['command']),None)
  need(response is not None and response['stdout']==text,'original root envelope '+tag)
  if tag=='native':need(text.startswith('IMMEDIATE_READY\n'),'original immediate cached identity');text=text[len('IMMEDIATE_READY\n'):]
  terminal,receipt,stdout,stderr=eh.receipt_envelope(text)
  need(terminal==record[tag+'Terminal']and terminal['boot']==eh.BOOT and type(terminal['exit_code'])is int and terminal['exit_code']==exit_code and stderr==b'','original native/selftest terminal '+tag)
  for suffix,raw in (('.receipt.json',receipt),('.stdout',stdout),('.stderr',stderr)):
   name=tag+suffix;need(ordinary(ORIGINAL/name)==raw,'original envelope output '+name);all_remote[name]=raw
 need(set(all_remote)==set(eh.NAMES)|set(OUTPUT_NAMES)and len(all_remote)==9,'exact nine stage files')
 selftest=strict(all_remote['selftest.receipt.json'].decode());need(selftest=={'selfTestsPassed':93,'keyTestsPassed':22,'checkpointTestsPassed':46,'targetOperations':0}and all(type(v)is int for v in selftest.values()),'original zero-I/O host fake selftest')
 native=strict(all_remote['native.receipt.json'].decode())
 for k,value in {'schema':'managed-usb-rt-synchronized-key-eh-v1','device':60,'bindingQualified':True,'observationAccepted':True,'accepted':False,'terminalReason':'AlreadyFaulted','protocolPhase':'ReadyForHeader','opened':True,'claimed':True,'released':True,'closed':True,'headersSent':8,'inputsCompleted':8,'bulkTransfers':16,'cyclesStarted':1,'cleanCyclesCompleted':0,'cleanCyclesDiscarded':0,'writes':0,'retries':0,'onsetObserved':False,'onsetMissed':True}.items():need(type(native.get(k))is type(value)and native[k]==value,'original native refusal '+k)
 need(native['intervention']['attempted']is False and native['intervention']['completed']is False and all(x['started']is False and x['reaped']is False for x in native['intervention']['calls']),'no Left child started')
 need(native['scoreCheckpoints']['count']==0 and native['scoreCheckpoints']['rawBase64']=='','no full checkpoint promoted')
 expected_files=[{'name':name,'bytes':len(raw),'sha256':sha(raw)}for name,raw in all_remote.items()]
 need(type(proof.get('stageFiles'))is list and len(proof['stageFiles'])==9 and all(type(x)is dict and set(x)=={'name','bytes','sha256'}and type(x['bytes'])is int for x in proof['stageFiles']),'classifier stage inventory exact fields')
 need(sorted(proof['stageFiles'],key=lambda x:x['name'])==sorted(expected_files,key=lambda x:x['name']),'classifier exact payload/output file binding')
 frozen=eh.old();prefix='set -eu\numask 077\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {eh.BOOT}\n'
 metadata=prefix+eh.metadata_body(identity,'EI_REJECTED_CLEANUP_READY')
 integrity=prefix+frozen.integrity(stage,all_remote,list(all_remote))+'echo EXACT_NINE_INTEGRITY_OK\n'
 cleanup=prefix+frozen.integrity(stage,all_remote,list(all_remote))
 cleanup+='rm -- '+' '.join(stage+'/'+name for name in all_remote)+'\n'
 cleanup+=f'rmdir -- {stage}\ntest ! -e {stage}\ntest ! -L {stage}\necho STAGE_ABSENT\n'
 commands=(metadata,integrity,cleanup)
 need(all(0<len(x.encode())<=8192 for x in commands),'bounded cleanup commands')
 return {'eh':eh,'stage':stage,'commands':commands,'stageFiles':expected_files,'proofSha256':PROOF_SHA,'originalRecordSha256':sha(record_raw),'nativeReceiptSha256':sha(all_remote['native.receipt.json'])}

def execute(plan,root,out):
 out.mkdir(mode=0o700,parents=False,exist_ok=False)
 log={'schema':'ei-already-faulted-exact-stage-cleanup-record-v1','calls':[],'originalWrapperRejectionPreserved':True,'cleanupAttempted':False,'targetVendorTransfers':0,'writes':0,'uiCalls':0,'resets':0,'retries':0,'proofSha256':plan['proofSha256'],'originalRecordSha256':plan['originalRecordSha256'],'nativeReceiptSha256':plan['nativeReceiptSha256'],'stageSha256':sha(plan['stage'].encode()),'stageFiles':plan['stageFiles']}
 path=out/'root.json'
 def save():path.write_text(json.dumps(log,indent=2)+'\n')
 save()
 text=root.root(plan['commands'][0],log,path);need(type(text)is str and len(text.encode())<=65536,'bounded current metadata response')
 census=plan['eh'].parse_metadata(text,'EI_REJECTED_CLEANUP_READY');(out/'metadata.txt').write_text(text);log['freshCensus']=census;save()
 need(root.root(plan['commands'][1],log,path)=='EXACT_NINE_INTEGRITY_OK\n','exact ordinary nine-file/hash inventory')
 log['cleanupAttempted']=True;save()
 need(root.root(plan['commands'][2],log,path)=='STAGE_ABSENT\n','exact removal receipt')
 result={'schema':'ei-already-faulted-exact-stage-cleanup-v1','accepted':True,'exactStageRemoved':True,'removedFiles':9,'originalWrapperRejectionPreserved':True,'nativeAccepted':False,'originalNativeHeaders':8,'originalNativeBulks':16,'additionalVendorTransfers':0,'writes':0,'uiCalls':0,'resets':0,'retries':0,'claimPreviouslyReleasedAndFdClosed':True,'endpointQueueProof':False,'proofSha256':plan['proofSha256']}
 log['accepted']=True;save();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
 cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--execute',action='store_true');cli.add_argument('--proof',type=Path);cli.add_argument('--proof-sha256');cli.add_argument('--source-sha256');args=cli.parse_args()
 if not args.execute:
  need(args.proof is None and args.proof_sha256 is None and args.source_sha256 is None,'default dry has no execution arguments')
  print(json.dumps({'schema':'ei-rejected-stage-cleanup-dry-v1','targetOperations':0,'rootCalls':0,'vendorTransfers':0,'writes':0,'uiCalls':0,'resets':0,'requiresFrozenClassifier':True,'sourceSha256':sha(ordinary(Path(__file__).resolve()))}));return
 need(args.source_sha256==sha(ordinary(Path(__file__).resolve())),'reviewed cleanup source digest required')
 plan=validate(args.proof,args.proof_sha256)
 root=load(ROOT,ROOT_SHA,'ei_rejected_cleanup_root')
 print(json.dumps(execute(plan,root,OUTPUT),sort_keys=True))
if __name__=='__main__':main()
