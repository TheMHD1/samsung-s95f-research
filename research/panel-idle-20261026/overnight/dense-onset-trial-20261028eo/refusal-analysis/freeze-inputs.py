from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;EO=H.parent;B=EO.parent;T=EO/'trial-01';paths=set()
def add(p):
 if not p.is_file()or p.is_symlink():raise ValueError('ordinary input')
 p.relative_to(B);paths.add(p)
for rel in ['onset','baseline','onset-readiness','baseline-readiness','ui-after','ledger']:
 for p in (T/rel).iterdir():
  if p.is_file():add(p)
for rel in ['result.json','onset-phase.md','baseline-phase.md','kernel-trace/result.json','kernel-trace/trace.txt']:add(T/rel)
for p in ['run-instrumented.py','orchestration-input-pins.json','verify-observation.py']:add(EO/p)
for rel,pin in json.loads((EO/'orchestration-input-pins.json').read_text()).items():add(B/rel)
for rel in ['onset-readiness','baseline-readiness']:
 for row in json.loads((T/rel/'readiness.json').read_text())['evidence']:add(Path(row['path']))
for rel in ['rtp-refresh-dense-checkpoints-20261028em','rtp-lane-gate-capture-20261028eb']:
 d=B/rel;add(d/'source-inventory.json')
 for row in json.loads((d/'source-inventory.json').read_text())['files']:add(d/row['path'])
for rel in ['selector-origin-20261028ej/README.md','selector-origin-20261028ej/source-audit.json']:add(B/rel)
rows=[]
for p in sorted(paths):
 b=p.read_bytes();rows.append({'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
with (H/'input-pins.json').open('x')as f:json.dump({'schema':'eo-refusal-input-pins-v1','files':rows,'rawInputsCopied':False},f,indent=2);f.write('\n')
print(json.dumps({'files':len(rows)}))
