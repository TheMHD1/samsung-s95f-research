#!/usr/bin/env python3
"""Publish once, or verify, this phase's local evidence index; never contact TV."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
MANIFEST=HERE/'resource-preroll-serdes-evidence-manifest.json'
PRIOR={
    'cache-replay-followup':('3b784160b3ba9566c93270d01d1099000347253789f5f02664601ee9b6d429ac',31),
    'pqe-policy-followup':('775f470de4109b6fc66996fc0408f431fcac94ea424068a3dddd71ae8ff534af',81),
    'onset-observer-validation':('23e672c75cb264b09b6a4e7943c183b3011ba01933b9b40d827201143c6f261f',176),
    'backend-storage-onset':('7f25ea9e4048cc10654e2cb17fb99495a6d265178809cf0db4696a900cebbfd7',43),
}
DIRECTORIES=(
    'sdp-resource-parent-metadata-20261026','sdp-hdmi-gate-provider-discovery-20261026',
    'sdp-sys-provider-copy-20261026','sdp-sys-provider-copy-20261026-followup',
    'sdp-hdmi-gate-symbol-search-20261026','hdmi-cell-provider-copy-20261026',
    'hdmi-cell-production-cache-20261026','serdes-symbol-discovery-20261026',
    'serdes-support-copy-20261026','serdes-ocif-copy-20261026','pm-tracepoint-formats-20261026',
    'preroll-smoke-20261026t1942.onset','observed-preroll-onset-reviewed-355d98b',
)
FILES=(
    'overnight/snapshot-resource-preroll-serdes.py',
    'overnight/pull-sdp-sys-provider.py','overnight/complete-sdp-sys-provider-copy.py',
    'overnight/pull-hdmi-cell-provider.py','overnight/pull-serdes-modules.py',
    'overnight/observed-preroll-onset-capture.py','overnight/observed-preroll-onset-capture-tests.py',
    'overnight/observed-preroll-onset-design.md','overnight/preroll-observer-runtime-progress.md',
    'overnight/pm-rpm-onset-extension-design.md',
    'overnight/observed-branch-onset-capture.py','overnight/observed-branch-onset-capture-tests.py',
    'overnight/observed-branch-onset-design.md',
    'tcon-research/sdp-resource-parent-decode.py','tcon-research/sdp-resource-parent-decode-tests.py',
    'tcon-research/sdp-hdmi-cell-gate-reproduce.py','tcon-research/sdp-hdmi-cell-gate.disasm',
    'tcon-research/sdp-hdmi-cell-gate-with-gpio.disasm','tcon-research/sdp-resource-and-production-gate.md',
    'tcon-research/serdes-lock-path-reproduce.py','tcon-research/serdes-lock-path.disasm',
    'tcon-research/serdes-probe-resume-path.md',
    'tcon-research/frc-extension-and-sdp-register-path.md',
    'tcon-research/frc-extension-bridge-reproduce.py','tcon-research/frc-extension-bridge.disasm',
    'tcon-research/sdp-frc-register-write-reproduce.py','tcon-research/sdp-frc-register-write.disasm',
)


def require(ok,message):
    if not ok:raise ValueError(message)


def row(path):
    raw=path.read_bytes()
    return dict(path=str(path.relative_to(BASE)) if path.is_relative_to(BASE) else str(path),
                bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def verify_rows(rows):
    for expected in rows:
        require(row(BASE/expected['path'])==expected,'changed evidence: '+expected['path'])


def prior_verify():
    rows=[]
    for stem,(digest,count) in PRIOR.items():
        path=HERE/(stem+'-evidence-manifest.json')
        require(row(path)['sha256']==digest,'previous manifest changed')
        entries=json.loads(path.read_text())['files']
        require(len(entries)==count,'previous row count')
        verify_rows(entries)
        rows.append(dict(**row(path),files_verified=count))
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    previous=prior_verify()
    if args.verify_only:
        saved=json.loads(MANIFEST.read_text())
        require(saved['previous_snapshots']==previous,'previous snapshot binding')
        verify_rows(saved['files'])
        print(json.dumps(dict(verified=True,files=len(saved['files']),prior_rows_verified=331,**row(MANIFEST))))
        return
    require(not MANIFEST.exists(),'snapshot exists; use --verify-only')
    paths={BASE/name for name in FILES}
    for dirname in DIRECTORIES:
        directory=HERE/dirname
        require(directory.is_dir(),'missing evidence directory: '+dirname)
        paths.update(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    entries=[row(p) for p in sorted(paths)]
    payload=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),goal_complete=False,
        repair_deployed=False,root_status='host-assisted; untethered unverified',
        physical_picture_state='new captures physically unobserved',
        accepted_smoke='overnight/preroll-smoke-20261026t1942.onset/record.json',
        diagnostic_eligible=False,previous_snapshots=previous,files=entries,
        scope='Content integrity/index only; does not upgrade static or passive evidence into incident causality, physical recovery or a permanent repair. PM/RPM extension is reviewed design only, not implemented or enabled.')
    with MANIFEST.open('x') as out:json.dump(payload,out,indent=2);out.write('\n')
    MANIFEST.chmod(0o400)
    print(json.dumps(dict(published=True,files=len(entries),prior_rows_verified=331,**row(MANIFEST))))


if __name__=='__main__':main()
