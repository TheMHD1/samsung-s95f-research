#!/usr/bin/env python3
"""Hash this follow-up phase without rewriting the historical snapshot."""
from pathlib import Path
import datetime
import hashlib
import json

BASE = Path(__file__).resolve().parents[1]


def digest(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    acquisition_path = BASE / 'overnight/matching-optimization-ui-manifest.json'
    acquisitions = json.loads(acquisition_path.read_text())
    for name, entry in acquisitions.items():
        actual = digest(BASE / 'binaries' / name)
        assert actual == {'bytes': entry['size'], 'sha256': entry['sha256']}, name
    photo_manifest = BASE / 'overnight/owner-photo-manifest.json'
    for entry in json.loads(photo_manifest.read_text()):
        actual = digest(Path(entry['path']))
        assert actual == {'bytes': entry['size'], 'sha256': entry['sha256']}, entry['path']
    managed = BASE / 'overnight/managed-kernel-abi-probe'
    for name, sha in json.loads((managed / 'build-manifest.json').read_text())['files'].items():
        assert digest(managed / name)['sha256'] == sha, name
    result = json.loads((managed / 'result-20261026T142228Z.json').read_text())
    assert result['accepted'] is True and result['cleanup_confirmed'] is True
    assert result['decoded']['BPF_ERRNO'] == result['decoded']['PERF_ERRNO'] == '38'
    prior_path = BASE / 'overnight/automatic-optimization-evidence-manifest.json'
    prior = json.loads(prior_path.read_text())
    drift = []
    for entry in prior['files']:
        path = Path(entry['path'])
        if not path.is_absolute():
            path = BASE / path
        if digest(path) != {'bytes': entry['bytes'], 'sha256': entry['sha256']}:
            drift.append(entry['path'])
    expected_drift = {
        'overnight/automatic-optimization-end-to-end.md',
        'overnight/diagnosis-20261026.md', 'overnight/RE-INDEX.md',
        'overnight/next-observed-session.md', 'overnight/pull-optimization-ui.py',
        'overnight/matching-optimization-ui-manifest.json',
        '/home/researcher/researcher-server/samsung-s95f-access-plan-2026-10-11.md',
    }
    assert set(drift) == expected_drift, drift
    paths = set(expected_drift)
    paths.update({
        'overnight/notification-factory-and-compat-abi-followup.md',
        'overnight/factory-notification-abi-independent-review.md',
        'overnight/snapshot-notification-factory-compat.py',
        'overnight/owner-photo-manifest.json',
        'tcon-research/owner-photo-board-map.md',
        'tcon-research/factory-off-sensing-test-period.md',
        'tcon-research/factory-off-sensing-transmit-target.md',
        'tcon-research/factory-off-sensing-transmit-target-reproduce.py',
        'idle-research/stock-notification-cancellation-contract.md',
        'binaries/TIFSDaemon', 'binaries/libfactory-interface-ATSC.so',
        'binaries/libvideoenhance.so.0', 'binaries/libave.so.0.1',
        'binaries/factory-data/FactoryIndexFile_Part1.dat',
        'binaries/factory-data/Factory_Part1.dat',
        'overnight/kernel-abi-probe/result-20261026T124321Z.json',
    })
    for name in acquisitions:
        if name in {'libnotification.so.0', 'data-provider-master', 'libnotification-ex.so.1',
                    'libpower-control-diagnosis.so', 'libppi-factory-api.so',
                    'libvideo-misc.so.0.1.0', 'libvideo-ft-control-impl-sec.so.0.1.0'}:
            paths.add('binaries/' + name)
    patterns = [
        'installed-observer-runtime-lookup-*.json', 'installed-dotnet-runtime-discovery-*.json',
        'runtime-and-notification-provider-discovery-*.json', 'runtime-and-provider-targets-*.json',
        'installed-clr-identity-*.json', 'factory-diagnosis-library-path-*.json',
        'factory-daemon-runtime-maps-*.json', 'factory-live-ppi-got-*.json',
    ]
    raw = []
    for pattern in patterns:
        for path in (BASE / 'overnight').glob(pattern):
            name = str(path.relative_to(BASE))
            paths.add(name)
            raw.append(name)
    for name in ['README.md', 'Program.cs', 'ArmKernelProbe.csproj', 'run-probe.py',
                 'build-manifest.json', 'result-20261026T142228Z.json']:
        paths.add('overnight/managed-kernel-abi-probe/' + name)
    for path in (managed / 'bin/Release/net6.0').iterdir():
        if path.suffix in {'.dll', '.json'}:
            paths.add(str(path.relative_to(BASE)))
    for path in (BASE / 'idle-research').glob('stock-notification-cancellation*reproduce.py'):
        paths.add(str(path.relative_to(BASE)))
    entries = []
    for name in sorted(paths):
        path = Path(name)
        if not path.is_absolute():
            path = BASE / path
        entries.append({'path': name, **digest(path)})
    record = {
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'goal_complete': False, 'repair_deployed': False,
        'physical_picture_state': 'unobserved', 'root_status': 'host-assisted; not untethered',
        'actual_actions': ['Installed-file, metadata, service-unit and exact userspace GOT reads',
                           'One stock-CLR ARM32 invalid-syscall probe with private temporary data staging; cleanup confirmed'],
        'not_performed': ['Factory writes', 'Notification delete/lookup or synthetic event',
                          'Display/power/sensing control', 'Execution-policy or kernel/firmware change'],
        'probe_scope': 'BPF/perf errno38 ENOSYS only for tested ARM32 EABI interface; native ARM64 unresolved',
        'acquisition_entries_verified': len(acquisitions), 'owner_photos_verified': 10,
        'previous_snapshot': str(prior_path.relative_to(BASE)),
        'previous_snapshot_identity': digest(prior_path),
        'intentional_previous_snapshot_drift': sorted(drift),
        'raw_responses': sorted(raw) + ['overnight/managed-kernel-abi-probe/result-20261026T142228Z.json'],
        'remaining_requirements': ['Physically observed recovery/prevention proof',
                                   'Incident-aligned menu blackout versus warning expiry distinction',
                                   'Factory reload/all-route coverage and absent-record rollback before candidate use',
                                   'Permanent root and permanent blackout repair remain unverified'],
        'files': entries,
    }
    destination = BASE / 'overnight/notification-factory-compat-evidence-manifest.json'
    destination.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'manifest': str(destination), 'files': len(entries),
                      'raw_responses': len(record['raw_responses']),
                      'acquisitions_verified': len(acquisitions), 'prior_drift': sorted(drift)}))


if __name__ == '__main__':
    main()
