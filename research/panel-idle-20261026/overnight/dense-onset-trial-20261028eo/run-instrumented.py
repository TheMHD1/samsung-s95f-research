#!/usr/bin/env python3
"""One explicit, serialized diagnostic sequence using frozen existing helpers."""
import argparse, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;B=HERE.parent
EB=B/'rtp-lane-gate-capture-20261028eb';EM=B/'rtp-refresh-dense-checkpoints-20261028em';EI=B/'refresh-checkpoint-trial-20261028ei'
EBM='e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11';EMM='83382d9a55271194480cb17d777a0d45737128f3dd849228b9517c3d2284c522'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 with p.open('x') as f:f.write(json.dumps(d,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 if not a.execute:print(json.dumps({'dry':True,'target_operations':0,'planned':'one private trace, normal preparation, EB baseline, EM, offline admission, EB post; no automatic recovery/retry'}));return
 pins=json.loads((HERE/'orchestration-input-pins.json').read_text())
 for rel,d in pins.items():need(sha(B/rel)==d,'frozen helper changed: '+rel)
 need(sha(EB/'deployment-manifest.json')==EBM and sha(EM/'deployment-manifest.json')==EMM,'fixed manifests')
 out=HERE/'trial-01';out.mkdir(mode=0o700);ledger=out/'ledger';ledger.mkdir(mode=0o700)
 result={'accepted_pair':False,'target_recovery_invocations':0,'ordinary_limit':40,'physical_picture_observed':False,'phase':'not_started'}
 def run(name,helper,args):
  argv=[sys.executable,str(helper),*[str(x) for x in args]]
  save(ledger/(name+'-intent.json'),{'argv':argv,'helper_sha256':sha(helper),'automatic_retry':False})
  r=subprocess.run(argv,capture_output=True)
  (ledger/(name+'.stdout')).write_bytes(r.stdout);(ledger/(name+'.stderr')).write_bytes(r.stderr)
  save(ledger/(name+'-completion.json'),{'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()})
  print(json.dumps({'stage':name,'exit_code':r.returncode}),flush=True)
  need(r.returncode==0,'stage refused: '+name)
 def readiness(name,family,helper,wrapper,phase,evidence):
  args=['--wrapper',family,'--wrapper-sha256',sha(wrapper),'--identity',EI/'after-recovery-identity/identity.json','--phase-note',phase,'--output',out/name]
  for p in evidence:args+=['--evidence',p]
  run(name,helper,args);return out/name/'readiness.json'
 def eb(name,ready):
  run(name,EB/'run-once.py',['--execute','--manifest-sha256',EBM,'--readiness',ready,'--readiness-sha256',sha(ready),'--output',out/name])
  p=EB/'parse-result.py';sp=importlib.util.spec_from_file_location('eo_eb',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  n,raw,q=m.parse_native((out/name/'native.receipt.json').read_text());r=json.loads((out/name/'result.json').read_text())
  need(r.get('accepted') is True and r.get('cleanup')=='STAGE_ABSENT' and n['protocolPhase']=='ReadyForHeader' and n['released'] is True and n['closed'] is True,'accepted closed EB boundary')
  for field in ('startR','endR'):need(q[field]['alternateLimit']==40,'EB original40')
  return q
 trace=out/'kernel-trace';trace_started=False
 try:
  run('trace-start',B/'autonomous-fault-harness-20261028dh/kernel-trace.py',['start','--output',trace]);trace_started=True
  run('prepare',B/'volatile-limit-trial-20261028dk/prepare-score-header-v2.py',['--output',out/'header-preparation'])
  prep=json.loads((out/'header-preparation/result.json').read_text());need(prep.get('accepted') is True,'accepted ordinary preparation')
  phase=out/'baseline-phase.md';phase.write_text('Latest vendor predecessor is accepted EL/post-tables-01 at original40, ReadyForHeader/released/closed/exactcleanup, sameboot USB61. Since then only cached UI and this ordinary preparation/private static trace. No known outstanding vendor header or helper. This is a closed-world premise, not endpoint queue proof.\n')
  old=B/'saver-wake-capture-20261028el/post-tables-01'
  ready=readiness('baseline-readiness','eb',EI/'prepare-readiness.py',EB/'run-once.py',phase,[old/'result.json',old/'native.receipt.json',out/'header-preparation/result.json'])
  q=eb('baseline',ready)
  need(all([q[k]['stop'],q[k]['fault'],q[k]['ordinaryGate']]==[0,0,1] for k in ('startR','endR')),'baseline is not clean; no EM/key follows')
  phase=out/'onset-phase.md';phase.write_text('Latest vendor operation is accepted baseline EB16readpairs at40, clean0/0/1 at both boundaries, release/close and exactcleanup. No intervening vendor actor known. One Left intends Apps-header-to-Live; UI consumption and physical panel are unobserved.\n')
  ready=readiness('onset-readiness','em',EM/'prepare-readiness.py',EM/'run-once.py',phase,[out/'baseline/result.json',out/'baseline/native.receipt.json',out/'header-preparation/result.json'])
  run('onset',EM/'run-once.py',['--execute','--manifest-sha256',EMM,'--readiness',ready,'--readiness-sha256',sha(ready),'--output',out/'onset'])
  run('admission',HERE/'verify-observation.py',['--capture',out/'onset','--output',out/'onset-admission.json'])
  proof=json.loads((out/'onset-admission.json').read_text());need(proof.get('accepted') is True,'offline EM admission')
  phase=out/'post-phase.md';phase.write_text('Latest vendor operation is accepted/reconciled EM at unchanged40, ReadyForHeader/released/closed/exactcleanup, key child joined, no retries. Separate EB read is permitted by this closed-world premise; it is not a physical endpoint queue proof or atomic post-onset sample.\n')
  ready=readiness('post-readiness','eb',EI/'prepare-readiness.py',EB/'run-once.py',phase,[out/'onset-admission.json',out/'onset/result.json',out/'onset/native.receipt.json'])
  q=eb('post-tables',ready);expected=proof['lastRtTuple']
  need(all([q[k]['stop'],q[k]['fault'],q[k]['ordinaryGate']]==expected for k in ('startR','endR')),'separate EB state disagrees with EM terminal')
  result.update(accepted_pair=True,phase='complete',terminal=proof['terminal'],checkpoints=proof['checkpoints'],maximum_sampled_A0=proof['maximumSampledA0'])
 except Exception as e:
  result.update(phase='stopped',error=type(e).__name__+': '+str(e));raise
 finally:
  if trace_started:
   try:run('trace-stop',B/'autonomous-fault-harness-20261028dh/kernel-trace.py',['stop','--output',trace]);result['trace_collected']=True
   except Exception as e:result['trace_collected']=False;result['trace_error']=type(e).__name__+': '+str(e)
  save(out/'result.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
