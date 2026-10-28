#!/usr/bin/env python3
"""Fixed FW ordinary-file archive command builder/parser; never calls any transport."""
import base64,hashlib,json,re,shlex,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;B=D.parent;U=B/'combined-live-trigger-adapter-20261028fu';F=B/'combined-live-trigger-trial-20261028fw';C=F/'capture-01'
STAGE='/tmp/researcher-fn-2c325f839a9d44b1bbf8d98380889cb5'
PROOF_SHA='88c4dcbb4a3d8cd73741325cf0d8a04751e1d72cbc6171440036c6c0ae7c1542'
WRAPPER_SHA='6f718399b98faa0226f97072d149803bfe96b03da5ff4a3b15d9f13afbc4bfae'
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def strict(raw):
 def pairs(xs):
  out={}
  for k,v in xs:need(k not in out,'duplicate key');out[k]=v
  return out
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'nonfinite'))
def load(path,pin):
 need(sha(path.read_bytes())==pin,'fixed source digest');m=types.ModuleType(path.stem);m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def build():
 for row in strict((D/'input-pins.json').read_bytes())['files']:
  raw=(B/row['path']).read_bytes();need(len(raw)==row['bytes']and sha(raw)==row['sha256'],'pinned input '+row['path'])
 proofraw=(F/'refusal-analysis/phase-proof.json').read_bytes();need(sha(proofraw)==PROOF_SHA,'known terminal proof')
 proof=strict(proofraw);need(proof['status']=='NATIVE_TERMINAL_KNOWN_READY_NOT_WRAPPER_ACCEPTANCE'and proof['phase']=='ReadyForHeader'and proof['released']and proof['closed']and proof['noPendingInOrPayload']and proof['writes']==0 and not proof['loggerArmAttempted']and proof['remoteStage']==STAGE,'exact no-arm known-phase premise')
 w=load(U/'run-once.py',WRAPPER_SHA);p=w.load_pinned(w.FN/'parse-result.py',w.PARSER_SHA,'fy_fixed_fn_parser');native,rows,interp=p.parse_native((C/'native.receipt.json').read_text());need(native['accepted']is False and native['headers']==2 and native['bulks']==4 and native['writes']==0 and native['phase']=='ReadyForHeader'and native['released']and native['closed']and not native['armAttempted'],'strict original refusal')
 need(sha((C/'native.receipt.json').read_bytes())==proof['nativeReceiptSha256']and sha((C/'record.json').read_bytes())==proof['rootRecordSha256'],'original proof receipt/root ledger')
 manifest,payload=w.build_manifest();need(w.manifest_bytes(manifest)==(C/'reviewed-manifest.json').read_bytes(),'reviewed source/payload bytes')
 known={name:{'bytes':len(raw),'sha256':sha(raw),'hostSource':str((w.FN/'bin/Release/net6.0'/name).relative_to(B))}for name,raw in payload.items()}
 for tag in ['selftest','native']:
  for suffix in ['receipt.json','stdout','stderr']:
   name=tag+'.'+suffix;raw=(C/name).read_bytes();known[name]={'bytes':len(raw),'sha256':sha(raw),'hostSource':str((C/name).relative_to(B))}
 need(len(known)==9,'nine existing host files')
 rings={}
 for label,name in [('baselineRing','baseline-ring.bin'),('postRing','post-ring.bin')]:
  meta=native[label];rings[name]={'bytes':meta['bytes'],'sha256':meta['sha256'],'nativeReceiptField':label}
 need(rings['baseline-ring.bin']['bytes']==15372 and rings['post-ring.bin']=={'bytes':0,'sha256':sha(b''),'nativeReceiptField':'postRing'},'exact two ring extents')
 allfiles=known|rings;old=w.old();commands=[]
 prefix='set -eu\numask 077\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {w.BOOT}\n'+'test "$(id -u)" = 0\ntest "$(id -g)" = 0\n'
 guard=old.dir_guard(STAGE)+old.exact_inventory(STAGE,list(allfiles))
 for name,meta in allfiles.items():
  target=STAGE+'/'+name;guard+=old.file_guard(target,meta['bytes'])+f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {meta["sha256"]}\n'
 for name,meta in rings.items():
  target=STAGE+'/'+name
  command=prefix+guard+'echo FN_SIDECAR_BEGIN\nbase64 '+target+'\necho FN_SIDECAR_END\n'
  need(len(command.encode())<=8192,'fixed command cap')
  commands.append({'file':name,'command':command,'commandBytes':len(command.encode()),'commandSha256':sha(command.encode()),'expectedBytes':meta['bytes'],'expectedSha256':meta['sha256']})
 return {'schema':'fy-fixed-fw-stage-archive-plan-v1','sourceWrapperSha256':WRAPPER_SHA,'phaseProofSha256':PROOF_SHA,'remoteStage':STAGE,'knownHostFiles':known,'ringFiles':rings,'commands':commands,'remoteFiles':11,'rootTimeoutSeconds':45,'hostTimeoutSeconds':75,'rootCommandCap':8192,'rootResponseCap':65536,'nativeInvocations':0,'usbOperations':0,'uiOperations':0,'loggerWrites':0,'thresholdWrites':0,'remoteCleanup':False,'retries':0,'endpointQueueProof':False,'loadedCodeInvoked':False}
def parse_ring(text,name,plan):
 need(name in ['baseline-ring.bin','post-ring.bin'],'fixed ring name')
 need(type(text)is str and len(text.encode())<=65536,'response cap')
 m=re.fullmatch(r'FN_SIDECAR_BEGIN\n([A-Za-z0-9+/=\n]*)FN_SIDECAR_END\n',text);need(m is not None,'exact inherited sidecar framing')
 compact=m[1].replace('\n','');raw=base64.b64decode(compact,validate=True);meta=plan['ringFiles'][name]
 need(base64.b64encode(raw).decode()==compact and len(raw)==meta['bytes']and sha(raw)==meta['sha256'],'strict canonical ring bytes/hash')
 return raw
if __name__=='__main__':
 need(sys.argv[1:]in [[],['--write']],'fixed dry modes only')
 plan=build();raw=(json.dumps(plan,indent=2,sort_keys=True)+'\n').encode()
 if sys.argv[1:]==['--write']:
  (D/'archive-plan.json').write_bytes(raw);(D/'archive-plan.json').chmod(0o600)
  for i,row in enumerate(plan['commands'],1):(D/f'command-{i:02}.sh').write_text(row['command']);(D/f'command-{i:02}.sh').chmod(0o600)
 else:need((D/'archive-plan.json').read_bytes()==raw,'exact sealed plan')
 print(json.dumps({'schema':'fy-dry-plan-result-v1','planSha256':sha(raw),'commands':2,'maxCommandBytes':max(x['commandBytes']for x in plan['commands']),'remoteFiles':11,'knownHostFiles':9,'archiveRingBytes':15372,'targetOperations':0,'rootCalls':0,'networkOperations':0},sort_keys=True))
