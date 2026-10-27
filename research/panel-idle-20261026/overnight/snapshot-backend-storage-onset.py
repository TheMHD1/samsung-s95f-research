#!/usr/bin/env python3
"""Freeze this diagnostic phase without rewriting historical evidence."""
from pathlib import Path
import ast
import datetime
import hashlib
import json
import os
import tempfile

BASE = Path(__file__).resolve().parents[1]


def digest(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    destination = BASE / 'overnight/backend-storage-onset-evidence-manifest.json'
    assert not destination.exists(), 'Historical snapshot already exists; use a new phase name'
    prior_path = BASE / 'overnight/notification-factory-compat-evidence-manifest.json'
    prior = json.loads(prior_path.read_text())
    drift = set()
    for entry in prior['files']:
        path = Path(entry['path'])
        if not path.is_absolute():
            path = BASE / path
        if digest(path) != {'bytes': entry['bytes'], 'sha256': entry['sha256']}:
            drift.add(entry['path'])
    expected_drift = {
        '/home/researcher/researcher-server/samsung-s95f-access-plan-2026-10-11.md',
        'overnight/RE-INDEX.md', 'overnight/diagnosis-20261026.md',
        'overnight/matching-optimization-ui-manifest.json',
        'overnight/next-observed-session.md', 'overnight/pull-optimization-ui.py',
        'tcon-research/factory-off-sensing-transmit-target.md',
    }
    assert drift == expected_drift, sorted(drift)
    acquisitions_path = BASE / 'overnight/matching-optimization-ui-manifest.json'
    acquisitions = json.loads(acquisitions_path.read_text())
    for name, entry in acquisitions.items():
        assert digest(BASE / 'binaries' / name) == {
            'bytes': entry['size'], 'sha256': entry['sha256']}, name
    photos_path = BASE / 'overnight/owner-photo-manifest.json'
    photos = json.loads(photos_path.read_text())
    for entry in photos:
        assert digest(Path(entry['path'])) == {
            'bytes': entry['size'], 'sha256': entry['sha256']}, entry['path']
    live_path = BASE / 'overnight/factory-backend-runtime-20261026T145801Z.json'
    live = json.loads(live_path.read_text())
    assert live['accepted'] is True and live['atomic'] is False
    assert live['source_hashes_are_live_text_hashes'] is False
    assert live['summary']['memory_bytes_read'] == 44
    assert live['summary']['capture_invoked_factory_function'] is False
    assert live['summary']['concurrent_daemon_activity_excluded'] is False
    assert live['physical_state'] == 'unobserved'

    paths = expected_drift | {
        'overnight/backend-storage-and-onset-preparation.md',
        'overnight/backend-storage-independent-review.md',
        'overnight/snapshot-backend-storage-onset.py',
        'overnight/factory-backend-runtime.md',
        'overnight/snapshot-factory-backend.py',
        'overnight/snapshot-factory-backend-tests.py',
        'overnight/snapshot-qd-runtime.py', 'overnight/test-snapshot-qd-runtime.py',
        'overnight/diagnostic-trace.py',
        'overnight/onset-capture-requirements.md',
        'overnight/onset-capture-review.md',
        'overnight/vlog-capture-contract.md',
        'overnight/owner-photo-manifest.json',
        'tcon-research/owner-photo-board-map.md',
        'tcon-research/factory-off-sensing-storage-readback.md',
        'tcon-research/factory-off-sensing-storage-readback-reproduce.py',
        'tcon-research/off-sensing-disable-route-coverage.md',
        'tcon-research/factory-off-sensing-transmit-target-reproduce.py',
        'binaries/TIFSDaemon', 'binaries/libvideo-misc.so.0.1.0',
        'binaries/libvideo-ft-control-impl-sec.so.0.1.0',
        'binaries/libnvram.so.0.1', 'binaries/libnvram-impl-sec.so.0.1',
        'binaries/libeeprom-map.so.0.1',
    }
    # Pin every binary the storage verifier itself declares, without executing it.
    checker = BASE / 'tcon-research/factory-off-sensing-storage-readback-reproduce.py'
    declared = None
    for node in ast.parse(checker.read_text()).body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == 'FILES'
                for target in node.targets):
            declared = ast.literal_eval(node.value)
    assert isinstance(declared, dict) and declared
    for relative, expected in declared.items():
        assert digest(BASE / relative)['sha256'] == expected, relative
        paths.add(relative)
    raw = {
        'overnight/factory-backend-runtime-20261026T145801Z.json',
        'overnight/vlogutil-help-discovery-20261026T145901Z.json',
        'overnight/vlogutil-kerneltime-format-20261026T150016Z.json',
        'overnight/onset-capture-environment-20261026T151541Z.json',
        'overnight/onset-shell-file-limit-unit-20261026T151619Z.json',
        'overnight/factory-nvram-library-discovery-20261026T153211Z.json',
    }
    for relative in raw:
        assert (BASE / relative).is_file(), 'Missing required raw source: ' + relative
    paths |= raw
    entries = []
    for relative in sorted(paths):
        path = Path(relative)
        if not path.is_absolute():
            path = BASE / path
        entries.append({'path': relative, **digest(path)})
    result = {
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'goal_complete': False, 'repair_deployed': False,
        'physical_picture_state': 'unobserved',
        'root_status': 'host-assisted; not untethered',
        'observer_status': 'unexecuted draft under correction/review',
        'excluded_in_progress_artifacts': [
            'overnight/observed-onset-capture.py',
            'overnight/observed-onset-capture-tests.py',
        ],
        'observer_exclusion_reason': 'Source is actively changing; this snapshot freezes reviewed storage/backend evidence and capture requirements/review only.',
        'actual_actions': [
            '44-byte source/mapping-associated process-memory capture, no factory invocation',
            'Installed vlog help and a two-second historical log dump',
            'Read-only shell/resource metadata; child-only file-limit unit probe',
            'Read-only acquisition of exact mapped NVRAM wrapper/implementation files',
            'Offline disassembly, fixtures, review, and documentation',
        ],
        'not_performed': [
            'Observer live smoke or physically observed onset capture',
            'Factory writes, getter invocation, or notification deletion',
            'Display/power/sensing control or service restart',
            'Kernel/firmware patch or execution-policy change',
        ],
        'acquisition_entries_verified': len(acquisitions),
        'owner_photos_verified': len(photos),
        'previous_snapshot': str(prior_path.relative_to(BASE)),
        'previous_snapshot_identity': digest(prior_path),
        'intentional_previous_snapshot_drift': sorted(drift),
        'raw_responses': sorted(raw),
        'remaining_requirements': [
            'Independent final review of corrected observer before any live smoke',
            'Physically observed recovery/prevention and aligned onset evidence',
            'Factory live getter binding, backing persistence and exact rollback',
            'Permanent root and permanent blackout repair remain unverified',
        ],
        'files': entries,
    }
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                dir=destination.parent, prefix='.backend-storage-onset-', delete=False) as stream:
            temporary_path = Path(stream.name)
            stream.write(json.dumps(result, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        # Same-filesystem link publishes complete data atomically and refuses
        # to overwrite an existing snapshot, including a concurrent creator.
        os.link(temporary_path, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    print(json.dumps({'manifest': str(destination), 'files': len(entries),
                      'raw_responses': len(raw), 'acquisitions': len(acquisitions),
                      'owner_photos': len(photos), 'observer_status': result['observer_status']}))


if __name__ == '__main__':
    main()
