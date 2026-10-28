#!/usr/bin/env python3
"""Offline archive verification. Parent executor is inspected as AST/text, never imported."""
import ast,base64,hashlib,json,stat,types,sys
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;F=D.parent;B=F.parent;A=F/'retained-stage-archive-01';Y=B/'retained-stage-archive-plan-20261028fy';checks=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,s):
 global checks
 if not v:raise ValueError(s)
 checks+=1
def j(p):return json.loads(p.read_bytes())
def run():
 pins=j(D/'input-pins.json')['files']
 for row in pins:
  raw=(B/row['path']).read_bytes();ck(len(raw)==row['bytes']and sha(raw)==row['sha256'],'pinned '+row['path'])
 ck(sha((Y/'source-inventory.json').read_bytes())=='fb51ba12c72597d6af2f73764c0210e0a9e983782ad7f538c9b8ec02abc4d306','sealed FY')
 for row in j(Y/'source-inventory.json')['files']:
  raw=(Y/row['path']).read_bytes();ck(len(raw)==row['bytes']and sha(raw)==row['sha256'],'FY source inventory')
 # This one imported module is pure and has no transport executor.
 m=types.ModuleType('fixed_fy_parser');m.__file__=str(Y/'build-plan.py');exec(compile((Y/'build-plan.py').read_bytes(),str(Y/'build-plan.py'),'exec'),m.__dict__);p=m.build();planraw=(json.dumps(p,sort_keys=True,indent=2)+'\n').encode()
 index=j(A/'archive-complete.json');record=j(A/'root-record.json');intent=j(A/'intent.json')
 ck(planraw==(Y/'archive-plan.json').read_bytes()and sha(planraw)==index['planSha256']==intent['planSha256'],'plan exact binding')
 ck(index['schema']=='fw-fixed-stage-archive-complete-v1'and index['archiveComplete']is True and index['archiveOnly']is True and index['rootCalls']==2,'archive-only success index')
 ck(index['phaseProofSha256']==p['phaseProofSha256']and index['remoteStage']==p['remoteStage']and index['remoteStageRetained']is True,'original phase/stage binding')
 for name in ['originalNativeAccepted','originalWrapperAccepted','loggerArmed','leftAttempted','remoteCleanup','baselineIsPrefaultProven','postRingIsCompletedObservation','ringWrapExcluded','physicalPictureObserved']:ck(index[name]is False,'claim boundary '+name)
 for name in ['usbOperations','uiOperations','remoteWrites','retries']:ck(type(index[name])is int and index[name]==0,'zero operation '+name)
 ck(record['schema']=='fw-fixed-stage-archive-root-v1'and len(record['calls'])==2 and sha((A/'root-record.json').read_bytes())==index['rootRecordSha256'],'exact two-call ledger')
 files=[];maxresponse=0;maxcommand=0
 for i,(row,call)in enumerate(zip(p['commands'],record['calls']),1):
  command=(A/f'command-{i:02}.txt').read_text();response=(A/f'response-{i:02}.txt').read_text();raw=(A/row['file']).read_bytes()
  ck(command==row['command']==call['command']and sha(command.encode())==row['commandSha256']and call['command_bytes']==len(command.encode())<=8192,'exact command/size/hash')
  ck(call['transport_exit']==0 and type(call['transport_exit'])is int and call['host_timeout']is False and call['remote_timeout_seconds']==45 and call['host_timeout_limit_seconds']==75 and call['transport_stderr']=={'data':'','encoding':'base64'},'bounded successful root transport')
  env=call['response'];child=env['commands'];ck(env['authenticated']is True and env['uid']==env['euid']==0 and len(child)==1 and child[0]['command']==command and child[0]['exit_code']==0 and type(child[0]['exit_code'])is int and child[0]['timed_out']is False and child[0]['stderr']==''and child[0]['stdout']==response,'authenticated child/retained stdout')
  outer=call['transport_stdout'];ck(set(outer)=={'data','encoding'}and outer['encoding']=='base64','raw transport envelope encoding');encoded=base64.b64decode(outer['data'],validate=True);ck(json.loads(encoded)==env and len(encoded)<=65536,'raw transport bytes bind envelope/cap')
  ck(m.parse_ring(response,row['file'],p)==raw and len(raw)==row['expectedBytes']and sha(raw)==row['expectedSha256'],'strict actual ring framing/raw/hash')
  files.append({'path':row['file'],'bytes':len(raw),'sha256':sha(raw),'responseSha256':sha(response.encode()),'commandSha256':row['commandSha256']});maxresponse=max(maxresponse,len(encoded));maxcommand=max(maxcommand,len(command.encode()))
 ck(files==index['files'],'index all new file/response/command bytes')
 ck(index['knownHostFiles']==p['knownHostFiles']and len(index['knownHostFiles'])==9,'exact referenced nine host originals')
 for name,meta in index['knownHostFiles'].items():
  raw=(B/meta['hostSource']).read_bytes();ck(len(raw)==meta['bytes']and sha(raw)==meta['sha256'],'unchanged original '+name)
 ck(intent['automaticRetry']is False and intent['remoteCleanup']is False and intent['usbOperations']==intent['uiOperations']==0 and intent['commands']==[{k:v for k,v in row.items()if k!='command'}for row in p['commands']],'intent command bounds')
 expected={'archive-complete.json','intent.json','root-record.json','command-01.txt','command-02.txt','response-01.txt','response-02.txt','baseline-ring.bin','post-ring.bin'}
 ck({x.name for x in A.iterdir()}==expected,'exact host archive9 files/no refusal marker')
 ck(stat.S_IMODE(A.stat().st_mode)==0o700 and not A.is_symlink(),'private host directory')
 for f in A.iterdir():ck(f.is_file()and not f.is_symlink()and stat.S_IMODE(f.stat().st_mode)==0o600,'private regular host file '+f.name)
 original=j(F/'capture-01/result.json');ck(original['accepted']is False and original['cleanup']=='retained'and original['keyExposureQualified']is False,'original wrapper refusal unchanged')
 source=(F/'archive-retained-stage.py').read_text();tree=ast.parse(source)
 calls=[x for x in ast.walk(tree)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and isinstance(x.func.value,ast.Name)and x.func.value.id=='root'and x.func.attr=='root']
 ck(len(calls)==1 and 'for i,row in enumerate(plan[\'commands\'],1):'in source and not any(isinstance(x,ast.While)for x in ast.walk(tree)),'one call site finite two-command loop/no retry loop')
 ck('os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600'in source and 'f.flush();os.fsync(f.fileno())'in source and 'out.mkdir(mode=0o700)'in source,'source exclusive/no-follow writes and file fsync')
 ck(source.index("json_new(out/'archive-complete.json',index)")<source.index('try:os.fsync(fd)')<source.index("print(json.dumps({'archiveComplete':True"),'index then directory fsync before success print')
 ck('root=load(ROOT,'in source and source.index('root=load(ROOT,')<source.index('for i,row in enumerate(plan[\'commands\'],1):',source.index('record=')),'executor has top-level live call hazard, never import it')
 logs=F/'retained-stage-archive-logs';outer_intent=j(logs/'intent.json');completion=j(logs/'completion.json');success=j(logs/'stdout.txt')
 ck(outer_intent['argv']==['python3','-B',str(F/'archive-retained-stage.py')]and outer_intent['automaticRetry']is False,'single fixed executor intent')
 ck(type(completion['exitCode'])is int and completion['exitCode']==0 and completion['endedHostMonotonicNs']>=outer_intent['startedHostMonotonicNs']and(logs/'stderr.txt').read_bytes()==b'','retained outer execution completed cleanly')
 ck(success=={'archiveComplete':True,'existingHostFilesReferenced':9,'newArchivedBytes':15372,'remoteStageRetained':True,'remoteWrites':0,'rootCalls':2,'usbOperations':0},'source-final success print after directory fsync returned')
 summary={'schema':'fw-independent-archive-analysis-v1','archiveVerified':True,'rootCommands':2,'ringFiles':files,'newRingBytes':sum(x['bytes']for x in files),'existingHostFileReferences':9,'all11RemoteFilesGuardedEachRequest':True,'hostPrivateModeChecksPassed':True,'originalNativeAccepted':False,'originalWrapperAccepted':False,'loggerArmed':False,'leftAttempted':False,'remoteStageRetained':True,'remoteCleanup':False,'baselineIsPrefaultProven':False,'postRingIsCompletedObservation':False,'ringWrapExcluded':False,'physicalPictureObserved':False,'maxCommandBytes':maxcommand,'maxActualRootEnvelopeBytes':maxresponse,'fsyncSequenceSourceSupported':True,'finalDirectoryFsyncReturnedAccordingToSourceAndCompletedProcess':True,'outerExecutorSucceeded':True,'powerLossDurabilityProven':False,'executorImportedOrRun':False,'inputPins':len(pins),'checksPassed':checks,'targetOperations':0,'rootCalls':0,'networkOperations':0}
 return summary
if __name__=='__main__':
 s=run();raw=(json.dumps(s,sort_keys=True,indent=2)+'\n').encode()
 if sys.argv[1:]==['--write']:(D/'decoded.json').write_bytes(raw)
 else:ck((D/'decoded.json').read_bytes()==raw,'exact summary replay')
 print(json.dumps({'schema':'fw-archive-analysis-validation-v1','checks':checks,'rootCommandsReplayed':2,'decodedSha256':sha(raw),'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
