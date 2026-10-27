#!/usr/bin/env python3
"""Publish once or verify the private-resume/OCIF phase; no TV access."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
MANIFEST = HERE/'private-resume-ocif-evidence-manifest.json'
PRIOR = {
    'cache-replay-followup': ('3b784160b3ba9566c93270d01d1099000347253789f5f02664601ee9b6d429ac', 31),
    'pqe-policy-followup': ('775f470de4109b6fc66996fc0408f431fcac94ea424068a3dddd71ae8ff534af', 81),
    'onset-observer-validation': ('23e672c75cb264b09b6a4e7943c183b3011ba01933b9b40d827201143c6f261f', 176),
    'backend-storage-onset': ('7f25ea9e4048cc10654e2cb17fb99495a6d265178809cf0db4696a900cebbfd7', 43),
    'resource-preroll-serdes': ('f84677589fadefb42eb40214683d6da27539f7f4b5356ed91b85738007353906', 163),
}
DIRECTORIES = (
    'formfactor-boot-metadata-20261026', 'pm-idle-tracepoint-format-20261026',
    'private-rpm-log-baseline-20261026', 'ocif-ack-provider-discovery-20261026',
    'serdes-ack-copy-20261026', 'observed-pm-rejected-eabe5bde',
    'pm-smoke-20261026t2023.onset',
    'pm-idle-smoke-20261026.onset',
)
FILES = (
    'overnight/snapshot-private-resume-ocif.py',
    'overnight/private-resume-and-ocif-progress.md',
    'overnight/read-formfactor-boot-metadata.py', 'overnight/read-pm-idle-format.py',
    'overnight/read-private-rpm-log-baseline.py', 'overnight/pull-ocif-ack-module.py',
    'overnight/observed-pm-onset-capture.py', 'overnight/observed-pm-onset-capture-tests.py',
    'overnight/pm-rpm-idle-extension-addendum.md',
    'overnight/pm-smoke-20261026t2023.driver.stdout',
    'overnight/pm-smoke-20261026t2023.driver.stderr',
    'overnight/pm-idle-smoke-20261026.driver.stdout',
    'overnight/pm-idle-smoke-20261026.driver.stderr',
    'overnight/pm-idle-correction-offline-tests.txt',
    'overnight/pm-idle-smoke-runtime-audit.md',
    'overnight/pm-prestart-quiescence-review.md',
    'tcon-research/hdmi-private-resume-dispatch-reproduce.py',
    'tcon-research/hdmi-private-resume-dispatch.disasm',
    'tcon-research/hdmi-private-resume-dispatch.md',
    'tcon-research/ocif-cache-producer-reproduce.py',
    'tcon-research/ocif-cache-producer.disasm', 'tcon-research/ocif-cache-producer.md',
    'tcon-research/serdes-support-boot-provenance.py',
    'tcon-research/serdes-support-boot-provenance.disasm',
    'tcon-research/serdes-support-boot-provenance.md',
    'tcon-research/hdmi-private-power-log-markers.py',
    'tcon-research/hdmi-private-power-log-markers.disasm',
    'tcon-research/hdmi-private-power-log-markers.json',
    'tcon-research/hdmi-private-power-log-markers.md',
    'tcon-research/ocif-ack-polling-reproduce.py',
    'tcon-research/ocif-ack-polling.disasm', 'tcon-research/ocif-ack-polling.md',
    'tcon-research/private-rpm-state-outcomes.py',
    'tcon-research/private-rpm-state-outcomes.disasm',
    'tcon-research/private-rpm-state-outcomes.md',
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def row(path):
    require(path.is_file() and not path.is_symlink(), 'missing/nonregular evidence '+str(path))
    raw = path.read_bytes()
    name = str(path.relative_to(BASE)) if path.is_relative_to(BASE) else str(path)
    return dict(path=name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def check_rows(rows):
    require(len({r['path'] for r in rows}) == len(rows), 'duplicate evidence paths')
    for expected in rows:
        require(row(BASE/expected['path']) == expected, 'changed evidence '+expected['path'])


def prior_verify():
    rows = []
    for stem, (digest, count) in PRIOR.items():
        path = HERE/(stem+'-evidence-manifest.json')
        identity = row(path)
        require(identity['sha256'] == digest, 'prior manifest changed '+stem)
        entries = json.loads(path.read_text())['files']
        require(len(entries) == count, 'prior file count '+stem)
        check_rows(entries)
        rows.append(dict(**identity, files_verified=count))
    return rows


def curated_paths():
    paths = {BASE/name for name in FILES}
    for dirname in DIRECTORIES:
        directory = HERE/dirname
        require(directory.is_dir() and not directory.is_symlink(), 'evidence directory '+dirname)
        paths.update(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return sorted(paths)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()
    previous = prior_verify()
    entries = [row(p) for p in curated_paths()]
    if args.verify_only:
        saved = json.loads(MANIFEST.read_text())
        require(saved['previous_snapshots'] == previous and saved['files'] == entries,
                'snapshot curated set or prior binding changed')
        print(json.dumps(dict(verified=True, files=len(entries), prior_rows_verified=494, **row(MANIFEST))))
        return
    require(not MANIFEST.exists(), 'snapshot exists; use --verify-only')
    rejected = json.loads((HERE/'pm-smoke-20261026t2023.onset/record.json').read_text())
    require(rejected['accepted'] is False and rejected['technical_capture_complete'] is False and
            rejected['cleanup_verified'] is True, 'original rejected smoke must remain rejected/clean')
    incomplete = json.loads((HERE/'pm-idle-smoke-20261026.onset/record.json').read_text())
    require(incomplete['accepted'] is False and incomplete['technical_capture_complete'] is False and
            incomplete['diagnostic_eligible'] is False and incomplete['cleanup_verified'] is True and
            incomplete['error'] == 'ValueError: capture completion missing',
            'separate incomplete smoke must remain rejected/clean')
    payload = dict(
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        goal_complete=False, repair_deployed=False,
        root_status='host-assisted; untethered unverified',
        physical_picture_state='new captures physically unobserved', diagnostic_eligible=False,
        original_pm_smoke='overnight/pm-smoke-20261026t2023.onset/record.json',
        original_pm_smoke_accepted=False, original_pm_smoke_cleanup_verified=True,
        idle_corrected_smoke='overnight/pm-idle-smoke-20261026.onset/record.json',
        idle_corrected_smoke_accepted=False, idle_corrected_smoke_cleanup_verified=True,
        idle_corrected_smoke_failure='pre-start quiescence rejected a syscall-54 point sample; parser correction not exercised live',
        previous_snapshots=previous, files=entries,
        scope='Content integrity/index only. Private callback/state, cache, boot-input and transport paths are static evidence; no incident causality or physical repair. Both failed PM smokes and the first exact rejected source are preserved; subsequent parser/design work does not retroactively accept either run. Pending quiescence derivative implementation is outside this snapshot.')
    with MANIFEST.open('x') as out:
        json.dump(payload, out, indent=2)
        out.write('\n')
    MANIFEST.chmod(0o400)
    print(json.dumps(dict(published=True, files=len(entries), prior_rows_verified=494, **row(MANIFEST))))


if __name__ == '__main__':
    main()
