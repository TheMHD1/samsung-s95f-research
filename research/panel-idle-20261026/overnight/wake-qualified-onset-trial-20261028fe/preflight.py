#!/usr/bin/env python3
"""Host-only FC frozen-input/dry admission before parent-owned target work."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
FC = BASE/'reader-wake-checkpoints-20261028fc'
PIN = '225011942323f7be66baf69212415c699c9e3aa4f9b103c02a540385d48913f9'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


inventory_path = FC/'source-inventory.json'
need(digest(inventory_path) == PIN, 'frozen FC inventory')
inventory = json.loads(inventory_path.read_text())
need(inventory['schema'] == 'fc-source-inventory-v2' and len(inventory['files']) == 13, 'FC inventory schema/count')
names = set()
for row in inventory['files']:
    name = row['path']
    need(Path(name).name == name and name not in names, 'unique local FC path')
    names.add(name)
    path = FC/name
    need(not path.is_symlink() and path.is_file(), 'ordinary FC file')
    need(type(row['bytes']) is int and path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], 'FC pinned bytes')
argv = [sys.executable, '-B', str(FC/'run-once.py')]
done = subprocess.run(argv, capture_output=True, timeout=30)
need(done.returncode == 0 and done.stderr == b'', 'successful local dry CLI')
dry = json.loads(done.stdout)
need(dry['schema'] == 'fc-reader-wake-wrapper-dry-v1', 'dry schema')
need(type(dry['targetOperations']) is int and dry['targetOperations'] == 0, 'dry target count')
need(dry['nativeInvocations'] == dry['wrapperUiOperations'] == dry['writes'] == 0, 'dry makes no operations')
need(dry['plannedNativeInvocations'] == dry['plannedWrapperUiOperations'] == 1 and dry['plannedWrapperKeyChildren'] == 2, 'planned visible operations')
need((dry['nativeDurationUs'], dry['nativeMaxCycles'], dry['checkpointRecordBytes'], dry['nominalPeriodUs']) == (2000000, 56, 58, 25000), 'unchanged finite native settings')
report = {'schema':'fe-parent-host-preflight-v1', 'accepted':True,
          'sourceInventorySha256':PIN, 'checkedFcFiles':13,
          'dryArgv':argv, 'dryResult':dry, 'targetOperations':0,
          'scope':'Host source/dry qualification only; independent review and current target readiness remain separate.'}
(HERE/'preflight-result.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps({'accepted':True, 'checkedFcFiles':13, 'targetOperations':0}, sort_keys=True))
