#!/usr/bin/env python3
"""Publish once, or verify without writing, the local qualification evidence."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / 'logger-qualification-evidence-manifest.json'


def inventory():
    rows = []
    for path in sorted(HERE.rglob('*')):
        relative = path.relative_to(HERE)
        if '__pycache__' in relative.parts or path == MANIFEST or relative == Path('README.md'):
            continue
        if path.is_symlink():
            raise ValueError('symlink in evidence: ' + str(relative))
        if path.is_file():
            raw = path.read_bytes()
            rows.append(dict(path=str(relative), size=len(raw),
                             sha256=hashlib.sha256(raw).hexdigest()))
    if not rows:
        raise ValueError('empty evidence')
    return dict(schema='finite-logger-qualification-evidence-v1',
                files=rows, file_count=len(rows), total_bytes=sum(x['size'] for x in rows),
                mutable_exclusions=['README.md', '__pycache__/**'],
                physical_picture_observed=False, repair_established=False)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--publish', action='store_true')
    group.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    current = inventory()
    if args.publish:
        with MANIFEST.open('x') as stream:
            stream.write(json.dumps(current, indent=2) + '\n')
    else:
        if current != json.loads(MANIFEST.read_text()):
            raise ValueError('evidence inventory/content changed')
    print(json.dumps(dict(status='PASS', mode='publish' if args.publish else 'verify',
                          file_count=current['file_count'], total_bytes=current['total_bytes'],
                          manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
                          target_operations=0)))


if __name__ == '__main__':
    main()
