"""Pin only named frozen sources/captures; no acquisition or live imports."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;EI=H.parent;B=EI.parent;ROOT=B.parent
paths=set()
def add(p):
 if not p.is_file()or p.is_symlink():raise ValueError('ordinary input required')
 p.relative_to(ROOT);paths.add(p)
def add_files(p):
 for f in p.iterdir():
  if f.is_file():add(f)
for rel in ['refresh-checkpoint-trial-20261028ei/fault-tables-01',
'refresh-checkpoint-trial-20261028ei/fault-readiness-01',
'lane-gate-onset-20261028ee/post-tables-01',
'volatile-limit-trial-20261028dk/reference-fault-01',
'volatile-limit-trial-20261028dk/record-fault-01']:add_files(B/rel)
for directory in ['recovery-validation-01','validation-readiness-01','after-recovery-identity','fault-recovery-01']:add_files(EI/directory)
for rel in ['fault-readiness-01/readiness.json','validation-readiness-01/readiness.json']:
 for row in json.loads((EI/rel).read_text())['evidence']:add(Path(row['path']))
for rel in ['after-recovery-identity/instance-check.json','recovery-validation-check.json']:
 add(EI/rel)
 for row in json.loads((EI/rel).read_text())['inputs']:add(Path(row['path']))
for rel in ['validation-preparation-note.md','recovery-validation-phase.md']:add(EI/rel)
for f in (EI/'fault-recovery-01').rglob('*'):
 if f.is_file():add(f)
for rel in ['onset-01/native.receipt.json','onset-01/record.json','onset-01/readiness-decision.json',
'onset-01-cleanup/result.json','reconciled-fault-phase.md','refusal-analysis/decoded.json']:add(EI/rel)
for rel in ['rtp-lane-gate-capture-20261028eb','rtp-lane-gate-qualification-20261028ea']:
 d=B/rel;add(d/'source-inventory.json')
 for row in json.loads((d/'source-inventory.json').read_text())['files']:add(d/row['path'])
for rel in ['rtp-fixed-reference-capture-20261028dt/parse-result.py',
'rtp-record-capture-20261028dm/parse-result.py',
'rtp-record-capture-20261028dm/live-fault-analysis/decoded-fault.json',
'firmware-display-path-20261028de/record-formatter-appendix.md',
'rtp-fixed-reference-qualification-20261028dr/qualification.json',
'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin']:add(B/rel)
rows=[]
for p in sorted(paths):
 raw=p.read_bytes();rows.append({'path':str(p.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
with (H/'input-provenance.json').open('x')as out:
 json.dump({'schema':'ei-fault-table-input-provenance-v1','pathBase':'panel-idle-20261026','files':rows,'rawInputsCopied':False},out,indent=2);out.write('\n')
print(json.dumps({'filesPinned':len(rows),'rawInputsCopied':False}))
