#!/usr/bin/env python3
"""One fixed200 observation: set, sample, post-read. No automatic recovery/restore."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
B=HERE.parent
FA=B/'selective-endpoint-limit-writer-20261028fa'
EY=B/'rtp-limit200-checkpoints-20261028ey'
EB=B/'rtp-lane-gate-capture-20261028eb'
EI=B/'refresh-checkpoint-trial-20261028ei'
IDENTITY=B/'quiescent-onset-trial-20261028es/trial-01/after-recovery-identity/identity.json'
def need(ok,message):
 if not ok: raise ValueError(message)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
 with p.open('x') as f: f.write(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def module(path,name):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 if not a.execute:
  print(json.dumps({'dry':True,'target_operations':0,'planned':'Apps header, fixed40to200, fixed200 one-Left observer, separate EB200; no automatic reset/restore/retry'}));return
 pins=json.loads((HERE/'raised-input-pins.json').read_text())
 required={'volatile-limit-trial-20261028dk/prepare-score-header-v2.py'}
 for family,names in [
  ('selective-endpoint-limit-writer-20261028fa',('run-once.py','parse-result.py','prepare-readiness.py','deployment-manifest.json')),
  ('rtp-limit200-checkpoints-20261028ey',('run-once.py','parse-result.py','prepare-readiness.py','verify-observation.py','deployment-manifest.json')),
  ('rtp-lane-gate-capture-20261028eb',('run-once.py','parse-result.py','deployment-manifest.json')),
  ('refresh-checkpoint-trial-20261028ei',('prepare-readiness.py',)),
  ('quiescent-onset-trial-20261028es',('trial-01/after-recovery-identity/identity.json',)),
  ('limit-rechallenge-trial-20261028ex',('preparation-01/baseline/result.json','preparation-01/baseline/native.receipt.json','preparation-01/parent-baseline-check.json')),
 ]: required.update(family+'/'+name for name in names)
 need(type(pins)is dict and required<=set(pins) and len(pins)<=40,'bounded complete reviewed inputs')
 for rel,digest in pins.items():
  need(type(rel)is str and not Path(rel).is_absolute() and '..' not in Path(rel).parts,'relative input path')
  need(not (B/rel).is_symlink() and sha(B/rel)==digest,'frozen input '+rel)
 out=HERE/'raised-01';out.mkdir(mode=0o700);ledger=out/'ledger';ledger.mkdir(mode=0o700)
 state={'schema':'ex-raised200-trial-v1','accepted':False,'target_recovery_invocations':0,'automatic_restore':False,'automatic_retries':0,'physical_picture_observed':False,'phase':'not_started','set_invocations':0,'write_outcome_qualified':False,'last_qualified_c4':40,'restoration_required':False}
 def run(name,helper,args):
  argv=[sys.executable,str(helper),*[str(x) for x in args]]
  save(ledger/(name+'-intent.json'),{'argv':argv,'helper_sha256':sha(helper),'automatic_retry':False})
  r=subprocess.run(argv,capture_output=True)
  (ledger/(name+'.stdout')).write_bytes(r.stdout);(ledger/(name+'.stderr')).write_bytes(r.stderr)
  save(ledger/(name+'-completion.json'),{'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()})
  print(json.dumps({'stage':name,'exit_code':r.returncode}),flush=True)
  need(r.returncode==0,'stage refused '+name)
 def ready(name,family,builder,wrapper,statement,evidence):
  note=out/(name+'-phase.md');note.write_text(statement+'\n')
  args=['--wrapper',family,'--wrapper-sha256',sha(wrapper),'--identity',IDENTITY,'--phase-note',note,'--output',out/name]
  for p in evidence: args+=['--evidence',p]
  run(name,builder,args);return out/name/'readiness.json'
 try:
  state['phase']='ordinary_preparation'
  run('prepare',B/'volatile-limit-trial-20261028dk/prepare-score-header-v2.py',['--output',out/'header-preparation'])
  need(json.loads((out/'header-preparation/result.json').read_text())['accepted'] is True,'accepted Apps header')
  old=HERE/'preparation-01/baseline'
  ready_set=ready('set-readiness','fa',FA/'prepare-readiness.py',FA/'run-once.py',
   'Latest vendor predecessor is accepted EX/preparation-01/baseline EB16/32 clean40 at both R boundaries, ReadyForHeader/released/closed/STAGE_ABSENT on same-boot USB63. Only host work and ordinary Apps preparation since then; no known outstanding vendor transfer or other helper. Fixed FA40to200 only, no automatic restore/retry. Closed-world premise, not physical endpoint queue proof.',
   [old/'result.json',old/'native.receipt.json',HERE/'preparation-01/parent-baseline-check.json',out/'header-preparation/result.json'])
  state.update(phase='set_attempted',set_invocations=1,restoration_required=True)
  run('set',FA/'run-once.py',['--execute','--action','set','--manifest-sha256',sha(FA/'deployment-manifest.json'),'--readiness',ready_set,'--readiness-sha256',sha(ready_set),'--output',out/'set'])
  n,raws,gc=module(FA/'parse-result.py','ex_fa').parse_native((out/'set/native.receipt.json').read_text())
  result=json.loads((out/'set/result.json').read_text())
  need(all(type(result[k]) is int for k in ('headersSent','bulkTransfers','nativeInvocations','retries')),'set result exact integer counts')
  need(gc==[] and n['action']=='set40to200' and n['device']==63 and result['accepted'] is True and result['cleanup']=='STAGE_ABSENT','accepted closed fixed set')
  need(result['schema']=='fa-fixed-limit-wrapper-result-v1' and result['action']==n['action'] and result['manifestSha256']==sha(FA/'deployment-manifest.json') and result['readinessSha256']==sha(ready_set),'fixed set result/source/readiness binding')
  need(result['headersSent']==n['headersSent']==7 and result['bulkTransfers']==n['bulkTransfers']==14 and result['nativeInvocations']==1 and result['retries']==0,'fixed set invocation/counts')
  need(result['rawFiles']==[{'name':name,'bytes':len(raw),'sha256':digest} for name,raw,digest in raws],'set raw inventory')
  for name,raw,digest in raws: need((out/'set'/name).read_bytes()==raw,'set raw '+name)
  state.update(phase='set_qualified_ready',write_outcome_qualified=True,last_qualified_c4=200)
  save(out/'set-parent-check.json',{'accepted':True,'action':n['action'],'device':n['device'],'headers':n['headersSent'],'bulks':n['bulkTransfers'],'phase':n['protocolPhase'],'released':n['released'],'closed':n['closed'],'raw_files_verified':len(raws),'source_result_sha256':sha(out/'set/result.json'),'native_sha256':sha(out/'set/native.receipt.json'),'restoration_required':True})
  ready_ey=ready('onset-readiness','ey',EY/'prepare-readiness.py',EY/'run-once.py',
   'Latest vendor predecessor is accepted fixed FA set40to200:7headers14bulks, full guarded200 readback, ReadyForHeader/released/closed/STAGE_ABSENT on same-boot USB63. No intervening vendor operation known. EY observes fixed200, one Left intends Apps header departure; UI consumption/destination and emitted light unobserved. Closed-world premise, not endpoint queue proof.',
   [out/'set/result.json',out/'set/native.receipt.json',out/'set-parent-check.json'])
  state['phase']='ey_attempted'
  run('onset',EY/'run-once.py',['--execute','--manifest-sha256',sha(EY/'deployment-manifest.json'),'--readiness',ready_ey,'--readiness-sha256',sha(ready_ey),'--output',out/'onset'])
  run('admission',EY/'verify-observation.py',['--capture',out/'onset','--output',out/'onset-admission.json'])
  proof=json.loads((out/'onset-admission.json').read_text());need(proof['accepted'] is True,'qualified EY')
  recomputed=module(EY/'verify-observation.py','ex_ey_admission').verify(out/'onset')
  need(proof==recomputed,'complete EY proof must match fresh offline recomputation before post-read')
  state['phase']='ey_qualified_ready'
  ready_eb=ready('post-readiness','eb',EI/'prepare-readiness.py',EB/'run-once.py',
   'Latest vendor predecessor is accepted and independently admitted EY fixed200 observation:ReadyForHeader/released/closed/STAGE_ABSENT, key worker joined, one invocation/no retry on same-boot USB63. No other vendor actor known. This later EB is separate, not atomic with earlier samples; closed-world premise is not endpoint queue proof.',
   [out/'onset/result.json',out/'onset/native.receipt.json',out/'onset-admission.json'])
  state['phase']='post_eb_attempted'
  run('post-tables',EB/'run-once.py',['--execute','--manifest-sha256',sha(EB/'deployment-manifest.json'),'--readiness',ready_eb,'--readiness-sha256',sha(ready_eb),'--output',out/'post-tables'])
  n,raws,q=module(EB/'parse-result.py','ex_eb').parse_native((out/'post-tables/native.receipt.json').read_text())
  result=json.loads((out/'post-tables/result.json').read_text());need(result['accepted'] is True and result['cleanup']=='STAGE_ABSENT' and n['device']==63,'accepted closed EB')
  need(all(type(result[k]) is int for k in ('headersSent','bulkTransfers','nativeInvocations','retries')),'EB result exact integer counts')
  need(result['schema']=='eb-rtp-lane-gate-wrapper-result-v1' and result['manifestSha256']==sha(EB/'deployment-manifest.json') and result['readinessSha256']==sha(ready_eb),'EB result/source/readiness binding')
  need(result['headersSent']==n['headersSent']==16 and result['bulkTransfers']==n['bulkTransfers']==32 and result['nativeInvocations']==1 and result['retries']==0,'EB invocation/counts')
  need(result['rawFiles']==[{'name':name,'bytes':len(raw),'sha256':digest} for name,raw,digest in raws],'EB complete raw inventory')
  for name,raw,digest in raws: need((out/'post-tables'/name).read_bytes()==raw,'EB raw '+name)
  need(all(q[k]['alternateLimit']==200 for k in ('startR','endR')),'EB both observed200')
  state.update(accepted=True,phase='complete_ready',terminal=proof['terminal'],checkpoints=proof['checkpoints'],maximum_sampled_A0=proof['maximumSampledA0'],fixed200Evidence=proof['fixed200Evidence'],EY_last_R=proof['lastRtTuple'],post_startR=q['startR'],post_endR=q['endR'],post_context=q['sourceContext'])
 except Exception as e:
  state['stopped_after_phase']=state['phase'];state['phase']='stopped_requires_reconciliation';state['error']=type(e).__name__+': '+str(e);raise
 finally:
  save(out/'result.json',state);print(json.dumps(state),flush=True)
if __name__=='__main__': main()
