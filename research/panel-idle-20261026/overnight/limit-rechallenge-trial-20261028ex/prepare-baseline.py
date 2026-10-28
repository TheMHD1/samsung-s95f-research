#!/usr/bin/env python3
"""Ordinary Apps preparation and one fixed read-only baseline. No limit writes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
B = HERE.parent
PINS = {
 'volatile-limit-trial-20261028dk/prepare-score-header-v2.py': 'fa4ae5558b008f62bd17494e3a6c3feff71ff4065cdef2cbdc4f32b379dd017b',
 'refresh-checkpoint-trial-20261028ei/prepare-readiness.py': 'c846e3a8f95ed2e7d8ebf14eb0e08195c3fa14b7406940efd404bccceebded53',
 'rtp-lane-gate-capture-20261028eb/run-once.py': '886bdc05bb8eb5a255443f95a964f2bae947fc758b18ea0e4893f42c3e4ad9a8',
 'rtp-lane-gate-capture-20261028eb/parse-result.py': 'e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523',
 'rtp-lane-gate-capture-20261028eb/deployment-manifest.json': 'e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, data):
 with p.open('x') as f: f.write(json.dumps(data, indent=2, sort_keys=True)+'\n')
def need(ok, message):
 if not ok: raise ValueError(message)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 if not a.execute:
  print(json.dumps({'dry':True,'target_operations':0,'planned':'normal Apps header preparation and one EB baseline; no writes/reset'}));return
 for rel, digest in PINS.items(): need(sha(B/rel)==digest,'frozen helper '+rel)
 out=HERE/'preparation-01';out.mkdir(mode=0o700)
 def run(name, rel, args):
  argv=[sys.executable,str(B/rel),*[str(x) for x in args]]
  save(out/(name+'-intent.json'),{'argv':argv,'helper_sha256':sha(B/rel),'automatic_retry':False})
  r=subprocess.run(argv,capture_output=True)
  (out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr)
  save(out/(name+'-completion.json'),{'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()})
  print(json.dumps({'stage':name,'exit_code':r.returncode}),flush=True)
  need(r.returncode==0,'stage refused '+name)
 run('header','volatile-limit-trial-20261028dk/prepare-score-header-v2.py',['--output',out/'header'])
 need(json.loads((out/'header/result.json').read_text())['accepted'] is True,'accepted header')
 phase=out/'phase.md'
 phase.write_text('Latest vendor predecessor is accepted ES/trial-01/recovery-validation EB16/32, clean0/0/1 at40, ReadyForHeader/released/closed/STAGE_ABSENT on positively identified same-boot USB63. Since then only host analysis/publication and this ordinary UI preparation. No outstanding vendor transfer/helper known. Closed-world phase premise, not physical endpoint queue proof.\n')
 old=B/'quiescent-onset-trial-20261028es/trial-01/recovery-validation'
 args=['--wrapper','eb','--wrapper-sha256',PINS['rtp-lane-gate-capture-20261028eb/run-once.py'],'--identity',B/'quiescent-onset-trial-20261028es/trial-01/after-recovery-identity/identity.json','--phase-note',phase,'--output',out/'readiness']
 for p in [old/'result.json',old/'native.receipt.json',out/'header/result.json']:args+=['--evidence',p]
 run('readiness','refresh-checkpoint-trial-20261028ei/prepare-readiness.py',args)
 ready=out/'readiness/readiness.json'
 run('baseline','rtp-lane-gate-capture-20261028eb/run-once.py',['--execute','--manifest-sha256',PINS['rtp-lane-gate-capture-20261028eb/deployment-manifest.json'],'--readiness',ready,'--readiness-sha256',sha(ready),'--output',out/'baseline'])
 parser=B/'rtp-lane-gate-capture-20261028eb/parse-result.py'
 sp=importlib.util.spec_from_file_location('ex_eb',parser);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 n,raws,q=m.parse_native((out/'baseline/native.receipt.json').read_text())
 result=json.loads((out/'baseline/result.json').read_text())
 need(result['accepted'] is True and result['cleanup']=='STAGE_ABSENT','accepted closed baseline')
 for name,data,digest in raws: need((out/'baseline'/name).read_bytes()==data,'raw '+name)
 for k in ('startR','endR'):
  need([q[k]['stop'],q[k]['fault'],q[k]['ordinaryGate'],q[k]['alternateLimit']]==[0,0,1,40],'clean40 baseline')
 summary={'accepted':True,'threshold_writes':0,'reset_requests':0,'physical_picture_observed':False,'device':n['device'],'startR':q['startR'],'endR':q['endR'],'context':q['sourceContext'],'raw_files_verified':len(raws),'phase':n['protocolPhase'],'released':n['released'],'closed':n['closed']}
 save(out/'parent-baseline-check.json',summary);print(json.dumps(summary),flush=True)
if __name__=='__main__': main()
