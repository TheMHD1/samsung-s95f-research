#!/usr/bin/env python3
"""Freeze this completed local RE phase without overwriting evidence or contacting TV."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import stat
import tempfile
import types

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'overnight/pqe-policy-followup-evidence-manifest.json'
PREVIOUS = BASE / 'overnight/onset-observer-validation-evidence-manifest.json'
PREVIOUS_SHA = '23e672c75cb264b09b6a4e7943c183b3011ba01933b9b40d827201143c6f261f'
OLDER = BASE / 'overnight/backend-storage-onset-evidence-manifest.json'
OLDER_SHA = '7f25ea9e4048cc10654e2cb17fb99495a6d265178809cf0db4696a900cebbfd7'
FINAL_SOURCE_SHA = '161af4bd011cb81f32cf69e8e189ced3b15045c0eaf7df5820120cf2ff99bb07'
FINAL_TEST_SHA = '1199faf2dbb695a9af79474737b4ba71bf64c0bd2785b59824a0e74e35ab977c'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_stable(path, retain=False):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), f'Not a regular file: {path}')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    digest = hashlib.sha256()
    size = 0
    chunks = []
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        require((before.st_dev, before.st_ino) == (opened.st_dev, opened.st_ino),
                f'File replaced at open: {path}')
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            size += len(block)
            digest.update(block)
            if retain:
                chunks.append(block)
        ended = os.fstat(stream.fileno())
    after = path.lstat()
    def signature(value):
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
                value.st_ctime_ns)
    require(signature(before) == signature(opened) == signature(ended) == signature(after),
            f'File changed during read: {path}')
    require(size == after.st_size, f'File size mismatch: {path}')
    return {'bytes': size, 'sha256': digest.hexdigest()}, b''.join(chunks) if retain else None


def identity(path):
    return read_stable(path)[0]


def checked_json(path):
    fingerprint, raw = read_stable(path, retain=True)
    return json.loads(raw), fingerprint


def resolve(row):
    path = Path(row['path'])
    return path if path.is_absolute() else BASE / path


def verify_rows(rows):
    require(len({row['path'] for row in rows}) == len(rows), 'Duplicate file entries')
    for row in rows:
        require(identity(resolve(row)) == {'bytes': row['bytes'], 'sha256': row['sha256']},
                f'Evidence changed: {row["path"]}')


def previous_snapshots():
    result = []
    for path, expected_sha, count in [(PREVIOUS, PREVIOUS_SHA, 176),
                                      (OLDER, OLDER_SHA, 43)]:
        record, fingerprint = checked_json(path)
        require(fingerprint['sha256'] == expected_sha, f'Historical snapshot changed: {path}')
        require(len(record['files']) == count, 'Historical file count changed')
        verify_rows(record['files'])
        result.append({'path': str(path.relative_to(BASE)), **fingerprint,
                       'files_verified': count})
    return result


def verify_snapshot():
    record, fingerprint = checked_json(OUT)
    require(record['goal_complete'] is False and record['repair_deployed'] is False,
            'Unsupported completion/repair claim')
    require(record['previous_snapshots'] == previous_snapshots(), 'Historical anchors differ')
    verify_rows(record['files'])
    print(json.dumps({'verified': True, 'path': str(OUT),
                      'files': len(record['files']), **fingerprint}))


def load_final_reader():
    # Execute only the hash-pinned local module's definitions, never its CLI/main.
    path = BASE / 'overnight/pqe-policy-baseline.py'
    fingerprint, raw = read_stable(path, retain=True)
    require(fingerprint['sha256'] == FINAL_SOURCE_SHA, 'Active final reader changed')
    require(identity(BASE / 'overnight/pqe-policy-baseline-tests.py')['sha256'] ==
            FINAL_TEST_SHA, 'Active final tests changed')
    module = types.ModuleType('snapshot_reviewed_policy_reader')
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        verify_snapshot()
        return
    require(not OUT.exists() and not OUT.is_symlink(), 'Snapshot destination already exists')
    previous = previous_snapshots()
    names = [
        'snapshot-pqe-policy-followup.py', 'trace-newhome-exit.py',
        'pqe-policy-and-home-exit-progress.md', 'pqe-policy-baseline-runtime-results.md',
        'pqe-policy-baseline-independent-review.md', 'pqe-policy-followup-independent-review.md',
        'pqe-final-duty-independent-review.md',
        'pqe-policy-baseline.py', 'pqe-policy-baseline-tests.py',
        'trace-newhome-frc.py',
    ]
    paths = {BASE / 'overnight' / name for name in names}
    paths.update([PREVIOUS, OLDER])
    names = [
        'pqe-kernel-event-records.md', 'pqe-event-userspace-consumer.md',
        'pqe-consumer-reproduce.py', 'gsr-npu-pq-edge-review.md',
        'frc-ioctl-6626-analysis.md', 'reproduce-frc-ioctl-6626-analysis.py',
        'newhome-exit-restore-path.md', 'newhome-exit-resolution-disassembly.txt',
        'dlsr-class-pq-route.md', 'dlsr-class-pq-reproduce.py',
        'qd-weber-input-producer.md', 'qd-weber-input-reproduce.py',
        'qd-weber-input-reproduced.disasm',
        'qd-final-duty-branch-analysis.md', 'qd-final-duty-reproduce.py',
    ]
    paths.update(BASE / 'tcon-research' / name for name in names)
    # Preserve the Home-exit report's preceding dispatch/timing prerequisites.
    paths.update((BASE / 'tcon-research').glob('newhome-*.md'))
    paths.update((BASE / 'tcon-research').glob('newhome-*.py'))
    paths.update(path for path in (BASE / 'overnight').glob('newhome-*')
                 if path.is_file())
    for label in ['apps-visible-control', 'black-after-live-b0', 'black-volume-b1']:
        for suffix in ['.json', '-summary.json']:
            paths.add(BASE / 'paired-capture' / (label + suffix))
    paths.add(BASE / 'overnight/current-kernel-vlog.json')
    frc_scratch = list((BASE / 'tcon-research').glob('frc6626-*.raw.disasm'))
    require(len(frc_scratch) == 5, 'FRC scratch set changed')
    paths.update(frc_scratch)
    paths.update((BASE / 'tcon-research').glob('qd-final-duty-*.disasm'))
    paths.update((BASE / 'tcon-research').glob('dlsr-class-*.disasm'))
    for name in ['libave.so.0.1', 'avocd', 'sdp_pqe_dp.ko', 'qdf_tcon.ko',
                 'rosem_frc.ko', 'tztv_frc_tcon.ko', 'tztv_frc_tcon_api.ko']:
        paths.add(BASE / 'binaries' / name)
    for name in ['trace', 'meta.txt', 'vlog-after.txt', 'fds.txt']:
        paths.add(BASE / 'overnight/capacity-20261026t1648.onset' / name)

    archive_root = BASE / 'overnight/pqe-policy-reader-reviews'
    expected_archives = {'a966e83501294027-94ccef13d3b7',
                         '8575b16accb3f3b6-5b1698caac0f',
                         '161af4bd011cb81f-1199faf2dbb6'}
    require({path.name for path in archive_root.iterdir()} == expected_archives,
            'Reader archive set changed')
    parsed = {}
    archives = {}
    for name in sorted(expected_archives):
        directory = archive_root / name
        require(directory.is_dir() and not directory.is_symlink(), 'Invalid archive directory')
        manifest_path = directory / 'manifest.json'
        manifest, fingerprint = checked_json(manifest_path)
        parsed[manifest_path] = fingerprint
        require(set(manifest['files']) == {'pqe-policy-baseline.py',
                'pqe-policy-baseline-tests.py', 'remote-read-command.sh'}, 'Archive payload set')
        entries = {path.name for path in directory.iterdir()}
        cache = directory / '__pycache__'
        if '__pycache__' in entries:
            require(cache.is_dir() and not cache.is_symlink(), 'Invalid bytecode cache directory')
            entries.remove('__pycache__')
        require(entries == {'manifest.json', *manifest['files']}, 'Unexpected archive entry')
        archives[name] = manifest
        paths.add(manifest_path)
        for payload, expected in manifest['files'].items():
            require(Path(payload).name == payload, 'Invalid payload name')
            path = directory / payload
            require(identity(path) == expected, f'Archive payload changed: {path}')
            paths.add(path)

    final = archives['161af4bd011cb81f-1199faf2dbb6']['files']
    for name in ['pqe-policy-baseline.py', 'pqe-policy-baseline-tests.py']:
        require(identity(BASE / 'overnight' / name) == final[name],
                f'Active source differs from final archive: {name}')
    reader = load_final_reader()
    source_contract = reader.static_contract()

    captures = []
    for label, expected in [('20261026T173952Z', False), ('20261026T174544Z', True)]:
        stem = BASE / 'overnight' / f'pqe-policy-baseline-{label}'
        record_path = Path(str(stem) + '.json')
        record, fingerprint = checked_json(record_path)
        parsed[record_path] = fingerprint
        intent_path = Path(str(stem) + '.intent.json')
        intent, intent_id = checked_json(intent_path)
        parsed[intent_path] = intent_id
        archive_name = ('161af4bd011cb81f-1199faf2dbb6' if expected else
                        '8575b16accb3f3b6-5b1698caac0f')
        archive = archives[archive_name]
        require(intent['archive'] == str(archive_root / archive_name), 'Intent archive mismatch')
        require(intent['physical_state'] == 'unobserved', 'Intent physical-state mismatch')
        require(intent['hashes'] == {name: archive['files'][name]['sha256'] for name in
                ['pqe-policy-baseline.py', 'pqe-policy-baseline-tests.py']}, 'Intent source mismatch')
        command = record['command'].encode()
        command_id = {'bytes': len(command), 'sha256': hashlib.sha256(command).hexdigest()}
        require(command_id == archive['files']['remote-read-command.sh'], 'Capture command mismatch')
        require(intent['command_bytes'] == record['command_bytes'] == command_id['bytes'] ==
                archive['command_bytes'], 'Command byte-length mismatch')
        require(intent['command_sha256'] == command_id['sha256'], 'Intent command hash mismatch')
        require(record['accepted'] is expected and record['physical_state'] == 'unobserved',
                'Capture status/qualification changed')
        require(record['contract'] == source_contract and record['atomic'] is False,
                'Capture contract changed')
        transport = record['transport']
        require(transport['stderr'] == '', 'Unexpected controller stderr')
        response = json.loads(transport['stdout'])
        require(response['model'] == 'QN77S95FAFXZC' and response['authenticated'] is True and
                response['uid'] == response['euid'] == 0 and
                response['root_persistence'] == 'host-assisted' and
                response['global_system_files_unchanged_at_acquisition'] is True,
                'Root response identity changed')
        require(len(response['commands']) == 1, 'Expected exactly one finite command')
        remote = response['commands'][0]
        require(remote['command'] == record['command'], 'Nested root command mismatch')
        if expected:
            require(transport['exit_code'] == 0 and remote['exit_code'] == 0 and
                    remote['timed_out'] is False, 'Successful transport status changed')
            require(reader.validate_response(response, record['contract']) == record['summary'],
                    'Accepted raw response no longer validates to saved summary')
            require(record['summary']['physical_state_inferred_from_software'] is False,
                    'Unsupported physical inference')
        else:
            require('summary' not in record and bool(record.get('error')), 'Incomplete capture status')
            require(transport['exit_code'] == 1 and remote['exit_code'] == 124 and
                    remote['timed_out'] is True, 'Incomplete timeout status changed')
        for suffix in ['.json', '.intent.json', '.driver.stdout', '.driver.stderr']:
            paths.add(Path(str(stem) + suffix))
        captures.append({'path': str(record_path.relative_to(BASE)),
                         'accepted': expected, 'physical_state': 'unobserved',
                         'error': record.get('error'), **fingerprint})

    files = []
    for path in sorted(paths):
        fingerprint = identity(path)
        if path in parsed:
            require(fingerprint == parsed[path], f'Parsed input changed: {path}')
        files.append({'path': str(path.relative_to(BASE)), **fingerprint})
    require(previous_snapshots() == previous, 'Historical inputs changed during snapshot')
    verify_rows(files)
    payload = {
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'goal_complete': False, 'repair_deployed': False,
        'root_status': 'host-assisted; untethered persistence unverified',
        'physical_picture_state': 'unobserved during both baseline attempts',
        'previous_snapshots': previous, 'reader_archives': sorted(expected_archives),
        'captures': captures,
        'actual_actions': ['Offline binary/CFG analysis, local reproduction and independent review',
                           'Two finite read-only baseline attempts: one incomplete timeout, one accepted'],
        'not_performed': ['Remote keys, display/power/factory controls, target getters/setters/ioctls',
                          'Kernel/firmware changes or service restarts',
                          'Physical recovery/prevention validation'],
        'qualification': 'Hashes preserve evidence, not truth of all interpretations. Reproducer landmarks are bounded; manual CFG and physical/causal limits remain in reports. Historical files unchanged. Mutable CURRENT-INVESTIGATION navigation and generated bytecode caches excluded. Archived revisions are reviewed stages, not every intermediate draft.',
        'files': files,
    }
    descriptor, temporary = tempfile.mkstemp(prefix='.pqe-policy-followup-', dir=OUT.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(payload, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, OUT)
        parent = os.open(OUT.parent, os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        os.unlink(temporary)
    print(json.dumps({'path': str(OUT), 'files': len(files), **identity(OUT)}))


if __name__ == '__main__':
    main()
