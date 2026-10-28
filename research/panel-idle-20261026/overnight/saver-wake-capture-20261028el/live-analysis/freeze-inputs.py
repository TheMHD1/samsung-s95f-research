"""Capture only named completed EL inputs and frozen host sources; no acquisition."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;EL=H.parent;B=EL.parent;ROOT=B.parent
paths=set()
def add(p):
 if not p.is_file()or p.is_symlink():raise ValueError('ordinary input required')
 p.relative_to(ROOT);paths.add(p)
for rel in ['baseline-01','onset-01','post-tables-01','baseline-readiness-01','onset-readiness-01','post-readiness-01','pair-ledger-01','ui-before','ui-after']:
 for p in (EL/rel).rglob('*'):
  if p.is_file():add(p)
for rel in ['baseline-phase.md','onset-phase.md','post-phase.md','onset-admission.json','prepare-readiness.py','ui-before-summary.json']:add(EL/rel)
for rel in ['baseline-readiness-01','onset-readiness-01','post-readiness-01']:
 for row in json.loads((EL/rel/'readiness.json').read_text())['evidence']:add(Path(row['path']))
for row in json.loads((EL/'onset-admission.json').read_text())['inputs']:add(Path(row['path']))
for rel in ['rtp-refresh-checkpoints-20261028eh','rtp-lane-gate-capture-20261028eb','reference-refresh-control-20261028eg']:
 d=B/rel;add(d/'source-inventory.json')
 for row in json.loads((d/'source-inventory.json').read_text())['files']:add(d/row.get('path',row.get('name')))
for rel in ['selector-origin-20261028ej/README.md','selector-origin-20261028ej/source-audit.json','selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin']:add(B/rel)
rows=[]
for p in sorted(paths):
 b=p.read_bytes();rows.append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
with (H/'input-provenance.json').open('x')as f:json.dump({'schema':'el-live-analysis-inputs-v1','pathBase':'panel-idle-20261026','files':rows,'rawInputsCopied':False},f,indent=2);f.write('\n')
print(json.dumps({'filesPinned':len(rows)}))
