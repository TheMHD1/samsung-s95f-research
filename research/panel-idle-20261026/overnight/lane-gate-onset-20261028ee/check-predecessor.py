#!/usr/bin/env python3
"""Offline proof of the exact completed vendor-OUT predecessor; no target tools."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
P = B / 'rtp-lane-gate-trial-20261028ed/table-read-01'

def need(value, why):
    if not value:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

source = B / 'rtp-lane-gate-capture-20261028eb/parse-result.py'
need(sha(source.read_bytes()) == 'e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523', 'frozen EB parser')
spec = importlib.util.spec_from_file_location('ee_predecessor_eb', source)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
n, raws, interpretation = parser.parse_native((P / 'native.receipt.json').read_text())
r = json.loads((P / 'result.json').read_text())
need(r['accepted'] is True and r['manifestSha256'] == 'e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11', 'accepted exact predecessor manifest')
need(r['headersSent'] == 16 and r['bulkTransfers'] == 32 and r['cleanup'] == 'STAGE_ABSENT', 'completed exact predecessor cleanup')
need(n['protocolPhase'] == 'ReadyForHeader' and n['released'] is True and n['closed'] is True, 'native closed predecessor boundary')
expected = []
for name, raw, digest in raws:
    need((P / name).read_bytes() == raw, 'predecessor raw binding ' + name)
    expected.append({'name': name, 'bytes': len(raw), 'sha256': digest})
need(r['rawFiles'] == expected, 'predecessor complete raw inventory')
start, end = (P / 'start-R.bin').read_bytes(), (P / 'end-R.bin').read_bytes()
need(start == end, 'stable final R')
need([struct.unpack_from('<H', start, at)[0] for at in (0, 10, 14, 0xc4)] == [0, 0, 1, 40], 'final clean original limit')
need(all(row['primaryHalfword'] == 0 and row['secondaryByte'] == 0 for row in interpretation['laneGateSamples']), 'captured zero eligibility tables')
result = {'schema': 'ee-offline-predecessor-check-v1', 'accepted': True,
          'headers': 16, 'bulks': 32, 'phase': 'ReadyForHeader',
          'released': True, 'closed': True, 'stageAbsent': True,
          'actualLimit': 40, 'rtState': [0, 0, 1], 'targetOperations': 0,
          'physicalPictureObserved': False, 'endpointQueueProof': False,
          'inputs': [{'path': str(path), 'sha256': sha(path.read_bytes())}
                     for path in [source, P / 'native.receipt.json', P / 'result.json',
                                  *[P / row['name'] for row in expected]]]}
raw = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
with (HERE / 'predecessor-check.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}, sort_keys=True))
