#!/usr/bin/env python3
"""Local package/map/lineage audit only; never imports a target adapter."""
import hashlib
import json
import re
import struct
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
D = Path(__file__).resolve().parent
B = D.parent
X = B / 'live-code-fingerprint-20261028dx'
E = B / 'single-lane-diagnostic-design-20261028ek'
checks = 0

def need(ok, why):
    global checks
    checks += 1
    if not ok:
        raise ValueError(why)

def sha(data):
    return hashlib.sha256(data).hexdigest()

lineage = json.loads((D / 'source-lineage.json').read_text())
for name, digest in lineage['parentFiles'].items():
    need(sha((X / name).read_bytes()) == digest, 'frozen parent source')
pins = json.loads((D / 'ek-source-pins.json').read_text())
for name, digest in pins['pins'].items():
    need(sha((E / name).read_bytes()) == digest, 'frozen EK input')
need((D / 'NativeBinding.cs').read_bytes() == (X / 'NativeBinding.cs').read_bytes() == (B / 'rtp-lane-gate-capture-20261028eb/NativeBinding.cs').read_bytes(), 'reviewed corrected binding byte identical')
old = (X / 'Program.cs').read_text()
new = (D / 'Program.cs').read_text()
for start, end in [(' sealed class Controller', ' static Outcome Run'), (' static byte[] Header', ' static string ShortError'), (' readonly record struct Identity', ' static readonly Spec[] Specs')]:
    if start == ' static byte[] Header':
        old_end = ' sealed class Outcome'
    else:
        old_end = end
    need(old[old.index(start):old.index(old_end)] == new[new.index(start):new.index(end)], 'unchanged transport/header/interface source')
for start, end in [('try{long deadline', 'var engine='), ('catch(Exception e){o.Errors.Add(e.GetType().Name', 'o.Accepted=')]:
    need(old[old.index(start):old.index(end)] == new[new.index(start):new.index(end)], 'unchanged lifecycle/cleanup source')
old_parser = (X / 'parse-result.py').read_text()
new_parser = (D / 'parse-result.py').read_text()
start, end = 'def binding_checks(', 'def parse_native('
need(old_parser[old_parser.index(start):old_parser.index(end)] == new_parser[new_parser.index(start):new_parser.index(end)], 'same strict corrected binding decoder')
for start, end in [('def metadata_body(', 'def parse_metadata('), ('def receipt_envelope(', 'def execute(')]:
    old_wrapper = (X / 'run-once.py').read_text()
    new_wrapper = (D / 'run-once.py').read_text()
    need(old_wrapper[old_wrapper.index(start):old_wrapper.index(end)] == new_wrapper[new_wrapper.index(start):new_wrapper.index(end)].replace('EPMETA', 'DXMETA').replace('EPRUN', 'DXRUN'), 'same metadata/envelope mechanics')
parser = types.ModuleType('ep_offline_parser')
exec(compile(new_parser, 'parse-result.py', 'exec'), parser.__dict__)
package = (B / 'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
need(len(package) == 5242880 and sha(package) == pins['selectedPackageSha256'], 'exact selected package')
samples = json.loads('[' + re.search(r'SampleHex=\{([^}]+)\}', (D / 'HostTests.cs').read_text()).group(1) + ']')
expected = [('root-getter', 0x460038fc, 12), ('root-save', 0x4600bd6c, 8), ('operating-mode-and-SB', 0x4600be0c, 44), ('four-unrolled-local-gates', 0x4600beb4, 228), ('gate-literal-pool', 0x4600c030, 32)]
need(parser.SPECS == expected and len(samples) == len(parser.FINGERPRINTS) == 5, 'exact five fixed specs')
need(sum(s[2] for s in expected) == 324, 'complete byte count')
for i, row in enumerate(pins['windows']):
    name, address, length = expected[i]
    need((name, address, length) == (row['name'], int(row['busAddress'], 16), row['bytes']), 'frozen EK mapping')
    need('new("' + name + '",' + hex(address) + ',' + str(length) + ')' in new, 'exact native mapping')
    need(parser.FINGERPRINTS[i] == row['expectedSha256'] and '"' + row['expectedSha256'] + '"' in new, 'exact hashes')
    sample = bytes.fromhex(samples[i])
    at = int(row['fileOffset'], 16)
    need(sample == package[at:at + length] and len(sample) == length and sha(sample) == row['expectedSha256'], 'bounded fake data matches selected bytes')
    need(address % 4 == 0 and 0 < address - 0x46000000 < 0x20000 and address + length <= 0x46020000, 'complete aligned alias interval')
    need(struct.pack('<III', 0x101, address, length).hex() == row['readHeaderLittleEndianHex'], 'exact independently encoded read header')
need('value.Length>128' in new and 'JsonSerializer.Serialize(value))>128' in new and 'public BoundedErrors Errors' in new, 'only bounded error rendering added outside controller')
receipt = (D / 'ReceiptMain.cs').read_text()
for forbidden in ['"--address"', '"--execute-set"', '"--execute-restore"', '"--mode"']:
    need(forbidden not in receipt, 'no arbitrary memory/write CLI')
need('fixedReadPairs\\\":5' in receipt and 'native.receipt.json' in receipt and '24576' in receipt, 'exclusive bounded receipt contract')
need('Native.Alarm' not in new and 'alarm(' not in (D / 'NativeBinding.cs').read_text(), 'no imported hard-alarm claim')
print(json.dumps({'sourceChecksPassed': checks, 'fixedReadPairs': 5, 'inputBytes': 324, 'targetOperations': 0, 'networkOperations': 0}))
