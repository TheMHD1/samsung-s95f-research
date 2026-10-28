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
P = B / 'volatile-limit-trial-20261028dk/dv-final-clean-01'

def need(value, why):
    if not value:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

source = B / 'rtp-record-capture-20261028dm/parse-result.py'
need(sha(source.read_bytes()) == 'fa2401bf270583fd793d44150b5db70915504c72e39878a8dd9f24a9be6446ca', 'frozen DM parser')
spec = importlib.util.spec_from_file_location('dy_predecessor_dm', source)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
n, raws, interpretation = parser.parse_native((P / 'native.receipt.json').read_text())
r = json.loads((P / 'result.json').read_text())
need(r['accepted'] is True and r['manifestSha256'] == 'e62b2906734a2814f2165749eb8ab230d5dd8e8dfd37f257ce5962ea20850c53', 'accepted exact predecessor manifest')
need(r['headersSent'] == 12 and r['bulkTransfers'] == 24 and r['cleanup'] == 'STAGE_ABSENT', 'completed exact predecessor cleanup')
need(n['protocolPhase'] == 'ReadyForHeader' and n['released'] is True and n['closed'] is True, 'native closed predecessor boundary')
expected = []
for name, raw, digest in raws:
    need((P / name).read_bytes() == raw, 'predecessor raw binding ' + name)
    expected.append({'name': name, 'bytes': len(raw), 'sha256': digest})
need(r['rawFiles'] == expected, 'predecessor complete raw inventory')
start, end = (P / 'start-R.bin').read_bytes(), (P / 'end-R.bin').read_bytes()
need(start == end, 'stable final R')
need([struct.unpack_from('<H', start, at)[0] for at in (0, 10, 14, 0xc4)] == [0, 0, 1, 40], 'final clean original limit')
result = {'schema': 'dy-offline-predecessor-check-v1', 'accepted': True,
          'headers': 12, 'bulks': 24, 'phase': 'ReadyForHeader',
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
