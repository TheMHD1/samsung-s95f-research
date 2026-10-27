#!/usr/bin/env python3
"""Inventory/publish/verify this work block, without any TV/network access.

The explicit file list freezes retained bytes. Mutable navigation and test
plans are excluded; future additional files are outside this snapshot.
Publication refuses an existing manifest. Verification never republishes.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = HERE.parent
T = B.parent / 'tcon-research'
ROOT = HERE.parents[2]
OUTPUT = HERE / 'sleep-evidence-manifest.json'
MUTABLE = {'README.md', 'diagnostic-next-tests.md', OUTPUT.name}
EXCLUSIONS = ['__pycache__', 'obj', 'mutable README.md',
              'mutable diagnostic-next-tests.md', OUTPUT.name]
SCOPE_TEXT = 'Explicit retained file list; future additions are outside this snapshot.'
SCOPES = [HERE, B/'sleep-mode2-20261027a.onset',
          B/'sleep-smoke-20261027a.onset',
          B/'managed-tcon-duty-read', B/'managed-tcon-power-cycle-once',
          B/'managed-tcon-status-read', B/'managed-errpin-cdev']
EXTRA_NAMES = [
    'observed-hdmi-onset-capture.py',
    'observed-hdmi-onset-capture-tests.py',
    'observed-hdmi-long-onset-capture.py',
    'observed-hdmi-long-onset-capture-tests.py',
    'hdmi-long-parent-review-20261027.md',
    'hdmi-long-window-design-20261027.md',
    'observed-hdmi-budgeted-onset-capture.py',
    'observed-hdmi-budgeted-onset-capture-tests.py',
    'budgeted-onset-independent-review.md',
]
STATIC_NAMES = [
    'qd-power-control-userspace-abi.md',
    'qd-power-control-userspace-abi-reproduce.py',
    'qd-full-reset-versus-mode2.md',
    'qd-function-logging-plan-20261027.md',
    'qd-rtp-scan-invocation.md',
    'drm-histogram-logging-provenance.md',
    'qd-controller-fault-telemetry-getters.md',
    'qd-f38009-stock-telemetry.md',
    'qd-f38009-latch-producer.md',
    'qd-content-protection-primary-research.md',
    'qd-mode2-reported-fault-clear-semantics.md',
    'qd-rt-window-alias-evidence-20261027.md',
    'qd-rt-window-alias-evidence-20261027.py',
    'qd-usb-ap-rtp-logical-read-route.md',
    'qd-usb-ap-rtp-logical-read-route-reproduce.py',
    'qd-usb-ap-rtp-logical-read-route-review-erratum.md',
    'qd-usb-ap-rtp-logical-read-route-branch-check.py',
    'qd-rt-window-reset-output-20261027.md',
    'qd-rt-window-reset-output-reproduce.py',
    'kernel-instrumentation-capability-audit-20261027.md',
    'kernel-instrumentation-capability-audit-20261027-reproduce.py',
]


def require(value, message):
    if not value:
        raise ValueError(message)


def entry(path):
    require(not any(parent.is_symlink() for parent in (ROOT, *ROOT.parents)),
            'symlink evidence root or ancestor')
    parts = path.relative_to(ROOT).parts
    require(parts and not any(ROOT.joinpath(*parts[:n]).is_symlink()
                              for n in range(1, len(parts)+1)),
            'symlink input or ancestor: ' + str(path))
    require(path.is_file() and not path.is_symlink(), 'nonregular input: ' + str(path))
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def inventory():
    paths = set()
    for scope in SCOPES:
        require(scope.is_dir(), 'missing scope: ' + str(scope))
        for path in scope.rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts or 'obj' in path.parts:
                continue
            if path.parent == HERE and path.name in MUTABLE:
                continue
            paths.add(path)
    paths.update(B/name for name in EXTRA_NAMES)
    paths.update(T/name for name in STATIC_NAMES)
    paths.add(ROOT/'root-access/s95f-access.py')
    return [entry(path) for path in sorted(paths)]


def verify():
    manifest = json.loads(OUTPUT.read_text())
    require(manifest['schema'] == 'samsung-tv-sleep-evidence-v1', 'manifest schema')
    require(manifest['root'] == str(ROOT) and manifest['scope'] == SCOPE_TEXT
            and manifest['exclusions'] == EXCLUSIONS, 'manifest scope changed')
    require(manifest['physical_recovery_confirmed'] is False
            and manifest['whole_mode2_capture_accepted'] is False,
            'manifest evidence classification changed')
    entries = manifest['entries']
    require(entries and len({row['path'] for row in entries}) == len(entries),
            'empty/duplicate manifest entries')
    for row in entries:
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts,
                'manifest path escape')
        require(entry(ROOT/relative) == row, 'changed evidence: ' + str(relative))
    return len(entries), sum(row['bytes'] for row in entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--publish', action='store_true')
    mode.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        count, total = verify()
        print(json.dumps({'verified_files': count, 'bytes': total,
                          'manifest_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}))
        return
    require(not OUTPUT.exists(), 'existing evidence manifest refused')
    entries = inventory()
    if args.publish:
        manifest = {'schema': 'samsung-tv-sleep-evidence-v1',
                    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'root': str(ROOT), 'entries': entries,
                    'scope': SCOPE_TEXT,
                    'exclusions': EXCLUSIONS,
                    'physical_recovery_confirmed': False,
                    'whole_mode2_capture_accepted': False}
        with OUTPUT.open('x') as stream:
            json.dump(manifest, stream, indent=2, sort_keys=True)
            stream.write('\n')
        count, total = verify()
        print(json.dumps({'published_files': count, 'bytes': total,
                          'manifest_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}))
    else:
        print(json.dumps({'candidate_files': len(entries),
                          'bytes': sum(row['bytes'] for row in entries),
                          'published': False}))


if __name__ == '__main__':
    main()
