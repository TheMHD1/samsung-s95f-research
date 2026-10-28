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
P = B / 'live-code-fingerprint-trial-20261028dy/code-read-01'

def need(value, why):
    if not value:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

source = B / 'live-code-fingerprint-20261028dx/parse-result.py'
need(sha(source.read_bytes()) == '70efd3096ec5b1cef37fabd74f3e6c3fb63ca72d847bd79500bdb31d74c9dd05', 'frozen DX parser')
spec = importlib.util.spec_from_file_location('ed_predecessor_dx', source)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)
n, raws, interpretation = parser.parse_native((P / 'native.receipt.json').read_text())
r = json.loads((P / 'result.json').read_text())
need(r['accepted'] is True and r['manifestSha256'] == 'c4d51611cf638f0ac4e9e3003c3b72ee592f460df19ed6138ce57ae7e6e92fac', 'accepted exact predecessor manifest')
need(r['headersSent'] == 4 and r['bulkTransfers'] == 8 and r['cleanup'] == 'STAGE_ABSENT', 'completed exact predecessor cleanup')
need(n['protocolPhase'] == 'ReadyForHeader' and n['released'] is True and n['closed'] is True, 'native closed predecessor boundary')
expected = []
for name, raw, digest in raws:
    need((P / name).read_bytes() == raw, 'predecessor raw binding ' + name)
    expected.append({'name': name, 'bytes': len(raw), 'sha256': digest})
need(r['rawFiles'] == expected, 'predecessor complete raw inventory')
result = {'schema': 'ed-offline-predecessor-check-v1', 'accepted': True,
          'headers': 4, 'bulks': 8, 'phase': 'ReadyForHeader',
          'released': True, 'closed': True, 'stageAbsent': True,
          'sampledCodeMatch': True, 'targetOperations': 0,
          'physicalPictureObserved': False, 'endpointQueueProof': False,
          'inputs': [{'path': str(path), 'sha256': sha(path.read_bytes())}
                     for path in [source, P / 'native.receipt.json', P / 'result.json',
                                  *[P / row['name'] for row in expected]]]}
raw = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
with (HERE / 'predecessor-check.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}, sort_keys=True))
