#!/usr/bin/env python3
"""Freeze local onset-validation evidence; never contact the TV or overwrite a snapshot."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import stat
import tempfile

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'overnight/onset-observer-validation-evidence-manifest.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(path):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), f'Not a regular file: {path}')
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(block)
            digest.update(block)
    after = path.lstat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
            f'File changed while hashing: {path}')
    require(size == after.st_size, f'Size mismatch: {path}')
    return {'bytes': size, 'sha256': digest.hexdigest()}


def read_json_checked(path):
    expected = identity(path)
    raw = path.read_bytes()
    require({'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} == expected,
            f'Manifest changed before parsing: {path}')
    result = json.loads(raw)
    require(identity(path) == expected, f'Manifest changed after parsing: {path}')
    return result, expected


def main():
    require(not OUT.exists() and not OUT.is_symlink(), 'Snapshot destination already exists')
    previous = BASE / 'overnight/backend-storage-onset-evidence-manifest.json'
    prior, previous_id = read_json_checked(previous)
    checked_manifests = {previous: previous_id}
    require(previous_id['sha256'] ==
            '7f25ea9e4048cc10654e2cb17fb99495a6d265178809cf0db4696a900cebbfd7',
            'Historical snapshot identity changed')
    for row in prior['files']:
        path = Path(row['path'])
        if not path.is_absolute():
            path = BASE / path
        require(identity(path) == {'bytes': row['bytes'], 'sha256': row['sha256']},
                f'Historical evidence changed: {path}')

    names = [
        'archive-onset-review.py', 'snapshot-onset-validation.py',
        'onset-thread-coverage-metadata-20261026T155621Z.json',
        'onset-thread-following-assessment.md', 'onset-smoke-uep-launch-failure.md',
        'onset-second-smoke-partial-result.md', 'onset-third-smoke-accepted.md',
        'onset-capacity-90s-result.md', 'onset-observer-validation-progress.md',
        'onset-drain-smoke-accepted.md', 'decode-qd-trace.py',
    ]
    paths = {BASE / 'overnight' / name for name in names}
    for name in ['pqe-query-event-analysis.md', 'pqe-query-event-disassembly.txt',
                 'tcon-monitor-selector-0c-analysis.md',
                 'selector0c-qdf-monitor.raw.disasm', 'selector0c-read-helper.raw.disasm']:
        paths.add(BASE / 'tcon-research' / name)
    paths.update([BASE / 'binaries/sdp_pqe_dp.ko', BASE / 'binaries/qdf_tcon.ko'])
    paths.add(previous)
    archive_parent = BASE / 'overnight/onset-review-archives'
    archives = sorted(path for path in archive_parent.iterdir() if path.is_dir())
    expected_archives = {
        '0725e9c3c58418b1-842d888140dc', '51e00a387036f1a1-f487b4d4bf75',
        'ed257ee5f53fbddb-0ad774ba45ca', '84829647640c1f50-11113f3b7d0d',
        '9d5c19ba1fd1bb9b-b663f05b5b9b', '3a83318a23665919-413ba238820e',
        '17a30cbee3d0d6ce-ab6c4307d611',
    }
    require({path.name for path in archives} == expected_archives,
            'Review revision set differs from this phase')
    for archive in archives:
        require(not archive.is_symlink(), 'Symlink archive rejected')
        manifest_path = archive / 'manifest.json'
        manifest, manifest_id = read_json_checked(manifest_path)
        checked_manifests[manifest_path] = manifest_id
        require(set(manifest['files']) == {
            'observed-onset-capture.py', 'observed-onset-capture-tests.py',
            'remote-5.sh', 'remote-10.sh', 'remote-85.sh', 'remote-90.sh'},
            'Unexpected archive payload set')
        paths.add(manifest_path)
        for name, expected in manifest['files'].items():
            require(Path(name).name == name, 'Invalid archive payload name')
            path = archive / name
            require(identity(path) == expected, f'Archive payload changed: {path}')
            paths.add(path)
    labels = ['smoke-20261026t1620', 'smoke-20261026t1625b',
              'smoke-20261026t1642c', 'capacity-20261026t1648',
              'smoke-20261026t-drain1']
    records = []
    for label in labels:
        directory = BASE / 'overnight' / f'{label}.onset'
        require(directory.is_dir() and not directory.is_symlink(), f'Missing capture: {label}')
        for path in directory.iterdir():
            require(path.is_file() and not path.is_symlink(), f'Unexpected capture entry: {path}')
            paths.add(path)
        for suffix in ('.driver.stdout', '.driver.stderr'):
            paths.add(BASE / 'overnight' / (label + suffix))
        intent = BASE / 'overnight' / (label + '.intent.json')
        if intent.exists():
            paths.add(intent)
        record_path = directory / 'record.json'
        record, record_id = read_json_checked(record_path)
        checked_manifests[record_path] = record_id
        records.append({'label': label, 'accepted': record['accepted'],
                        'diagnostic_eligible': record['diagnostic_eligible'],
                        'cleanup_verified': record['cleanup_verified'],
                        'error': record.get('error')})
    files = []
    for path in sorted(paths):
        captured_id = identity(path)
        if path in checked_manifests:
            require(captured_id == checked_manifests[path], f'Parsed manifest changed: {path}')
        files.append({'path': str(path.relative_to(BASE)), **captured_id})
    payload = {
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'goal_complete': False, 'repair_deployed': False,
        'physical_picture_state': 'unobserved during this phase',
        'root_status': 'host-assisted; not untethered',
        'previous_snapshot_identity': previous_id,
        'previous_snapshot_files_verified': len(prior['files']),
        'archive_revisions': len(archives), 'capture_records': records,
        'actual_actions': ['Passive private-instance traces and read-only samples/logs',
                           'Offline decoder, source correction, fixtures and review'],
        'not_performed': ['Remote keys or display/power/factory controls',
                          'Kernel/firmware or execution-policy changes',
                          'Physical recovery/prevention validation'],
        'qualification': 'Preserved rejected captures remain rejected. Archive inclusion is not live clearance. Mutable observer source/tests are excluded; archived bytes are authoritative.',
        'files': files,
    }
    descriptor, temporary = tempfile.mkstemp(prefix='.onset-validation-', dir=OUT.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(payload, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, OUT)
        parent_fd = os.open(OUT.parent, os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        os.unlink(temporary)
    print(json.dumps({'path': str(OUT), 'files': len(files), **identity(OUT)}))


if __name__ == '__main__':
    main()
