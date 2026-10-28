#!/usr/bin/env python3
"""Inventory only local evidence; never include OEM contents or private disassembly."""
import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;B=D.parent;R=B.parent

def rec(p,label):
 return {'path':label,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
E=json.loads((D/'evidence.json').read_text())
deps=[
 B/'firmware-platform-analysis-20261028db/accepted-report.md',
 B/'firmware-platform-analysis-20261028db/accepted-outcomes.json',
 B/'firmware-platform-analysis-20261028db/source-inventory.json',
 B/'firmware-kernel-analysis-20261028cs/dtb-summary.json',
 B/'vlogutil-help-discovery-20261026T145901Z.json',
 B/'vlogutil-kerneltime-format-20261026T150016Z.json',
 B/'vlog-capture-contract.md',
 B/'autonomous-fault-harness-20261028dh/instrumentation-capability.txt',
 B/'autonomous-fault-harness-20261028dh/instrumentation-capability-02.json',
 B/'autonomous-fault-harness-20261028dh/instrumentation-capability-03.txt',
 B/'autonomous-fault-harness-20261028dh/ave-baseline-01/raw.log',
 B/'autonomous-fault-harness-20261028dh/ave-baseline-01/result.json',
]
for name in ['content-static-power-path.md','qd-monitor-exact-recovery-predicates.md','qd-monitor-runtime-map.md','qd-current-fault-gpio-read-abi.md','overnight-gpio-dt-driver-chain.md','qd-power-control-hardware-sequence.md','frc-duty-write-recovery.md','frc-extension-and-sdp-register-path.md','qd-onecommand-buffer-dataflow.md','qd-content-duty-policy.md']:
 deps.append(R/'tcon-research'/name)
public=[p for p in sorted(D.iterdir()) if p.is_file() and p.name!='source-inventory.json']
missing=[str(p.relative_to(R)) for p in deps if not p.is_file()]
if missing:raise ValueError('missing dependency '+repr(missing))
output={'schema':'display-path-source-inventory-v1','scope':'local-host-only; no TV/root/network/OEM execution by DE','binary_sources':E['sources'],'evidence_dependencies':[rec(p,str(p.relative_to(R))) for p in deps],'public_artifacts':[rec(p,p.name) for p in public],'private_artifacts':{'excluded_from_public':True,'directory':'private/','policy':'0700 directory / 0600 disassembly and metadata; contains no newly copied OEM binary'},'qualification':['Source dependencies are frozen snapshots, not live-time guarantees.','No complete running-image0 identity or AP_EXCO register-field link claimed.','Normal/-O exact-source verification results are in verification.json.']}
(D/'source-inventory.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'source_inventory_sha256':hashlib.sha256((D/'source-inventory.json').read_bytes()).hexdigest(),'public_files':len(public),'source_dependencies':len(deps)}))
