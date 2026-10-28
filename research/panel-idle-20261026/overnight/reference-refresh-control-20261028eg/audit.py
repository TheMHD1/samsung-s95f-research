#!/usr/bin/env python3
"""Bounded source audit and retained-data decoder; no target or network calls."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS

sys.dont_write_bytecode = True
D = Path(__file__).resolve().parent
B = D.parent
sha = lambda data: hashlib.sha256(data).hexdigest()
checks = 0

def need(condition, message):
    global checks
    checks += 1
    if not condition:
        raise ValueError(message)

asset = B / 'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
raw = asset.read_bytes()
need(len(raw) == 5242880 and sha(raw) == 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0', 'selected asset')
data = raw[0x40200:0x60200]
word = lambda va: struct.unpack_from('<I', data, va)[0]
cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
anchors = []

def ins(va, mnemonic, operands):
    decoded = list(cs.disasm(data[va:va + 4], va, count=1))
    need(len(decoded) == 1 and decoded[0].mnemonic == mnemonic and decoded[0].op_str == operands, 'instruction ' + hex(va))
    item = decoded[0]
    anchors.append({'va': hex(va), 'mnemonic': mnemonic, 'operands': operands,
                    'bytes': item.size, 'sha256': sha(data[va:va + item.size])})

for row in [
    (0x38f4, 'ldr', 'r0, [pc, #0]'), (0x38f6, 'bx', 'lr'),
    (0xb812, 'ldr', 'r1, [pc, #0x80]'), (0xb814, 'str', 'r0, [r1]'),
    (0xb818, 'bl', '#0x18ce0'), (0xb81c, 'ldr', 'r1, [pc, #0x78]'), (0xb81e, 'str', 'r0, [r1]'),
    (0xb824, 'ldrb', 'r0, [r0, #1]'), (0xb826, 'cbz', 'r0, #0xb82c'), (0xb828, 'bl', '#0x1c12c'),
    (0xb82e, 'ldrh', 'r0, [r0]'), (0xb830, 'cbnz', 'r0, #0xb878'),
    (0xc252, 'bl', '#0x38f4'), (0xc256, 'mov', 'r5, r0'),
    (0xc27c, 'ldrb.w', 'r0, [r5, #0x6c7]'), (0xc280, 'ldr', 'r1, [pc, #0x6c]'),
    (0xc282, 'ldrh', 'r1, [r1]'), (0xc284, 'cmp', 'r0, r1'), (0xc286, 'beq', '#0xc2a4'),
    (0xc288, 'ldrb.w', 'r0, [r5, #0x6c7]'), (0xc28e, 'strh', 'r0, [r1]'),
    (0xc292, 'ldrh', 'r0, [r0]'), (0xc294, 'cbz', 'r0, #0xc29e'),
    (0xc296, 'movs', 'r0, #1'), (0xc29a, 'strh', 'r0, [r1]'),
    (0xc29e, 'movs', 'r0, #0'), (0xc2a2, 'strh', 'r0, [r1]'),
    (0x4440, 'ldrb.w', 'r0, [r7, #0x48]'), (0x4444, 'cbz', 'r0, #0x4460'), (0x4446, 'bl', '#0xc250'),
    (0x1c12e, 'bl', '#0x38f4'), (0x1c136, 'ldrh', 'r0, [r0]'), (0x1c138, 'cbz', 'r0, #0x1c19c'),
    (0x1c13a, 'ldrb.w', 'r0, [r4, #0x6c7]'), (0x1c13e, 'cbz', 'r0, #0x1c19c'),
    (0x1c144, 'ldrh', 'r0, [r0, #6]'), (0x1c146, 'cbnz', 'r0, #0x1c164'),
    (0x1c14c, 'adds', 'r0, r0, #1'), (0x1c150, 'strh', 'r0, [r1]'),
    (0x1c152, 'mov.w', 'r2, #0xb60'), (0x1c15a, 'adds', 'r1, #8'), (0x1c15e, 'bl', '#0x70c'),
    (0x1c168, 'ldrh', 'r1, [r0, #6]'), (0x1c16a, 'ldrh.w', 'r0, [r4, #0x6c0]'),
    (0x1c16e, 'subs', 'r0, r0, #1'), (0x1c170, 'cmp', 'r1, r0'), (0x1c172, 'bne', '#0x1c18e'),
    (0x1c178, 'adds', 'r0, r0, #1'), (0x1c17c, 'strh', 'r0, [r1]'),
    (0x1c17e, 'mov.w', 'r2, #0xb60'), (0x1c186, 'adds', 'r1, #8'), (0x1c18a, 'bl', '#0x70c'),
    (0x1c192, 'cmp', 'r0, #2'), (0x1c194, 'ble', '#0x1c19c'),
    (0x1c196, 'movs', 'r0, #0'), (0x1c19a, 'strh', 'r0, [r1]')]:
    ins(*row)

literals = {0x38f8: 0x20000500, 0xb894: 0x20000494, 0xb898: 0x20000498,
            0xb89c: 0x200004c4, 0xc2f0: 0x200004c2, 0xc2f4: 0x200004c4,
            0x1c1a0: 0x200004c4, 0x1c1a4: 0x20000498,
            0x1c1a8: 0x20015000, 0x1c1ac: 0x20015f10}
for va, value in literals.items():
    need(word(va) == value, 'literal ' + hex(va))
need(word(0x38f8) + 0x6c7 == 0x20000bc7, 'context selector address')
need(0x200004c2 - 0x200004a0 == 34 and 0x200004c4 - 0x200004a0 == 36, 'M field offsets')
need(0x20000494 - 0x20000490 == 4 and 0x20000498 - 0x20000490 == 8, 'P pointer offsets')

# This overlapping halfword syntactic scan includes possible data decodes. It is
# not a CFG, complete writer census, or exclusion of computed/other-CPU writes.
refs = []
for va in range(0, 0x1d6a4, 2):
    item = next(cs.disasm(data[va:va + 4], va, count=1), None)
    if item is None:
        continue
    match = re.fullmatch(r'(r\d+), \[pc(?:, #(0x[0-9a-f]+|[0-9]+))?\]', item.op_str)
    if item.mnemonic not in ('ldr', 'ldr.w') or not match:
        continue
    literal = ((va + 4) & ~3) + int(match[2] or '0', 0)
    if literal + 4 <= len(data) and word(literal) == 0x200004c4:
        refs.append({'va': hex(va), 'literalVa': hex(literal)})
need([int(row['va'], 16) for row in refs] == [0xb82c, 0xc298, 0xc2a0, 0x1c134, 0x1c148, 0x1c14e, 0x1c174, 0x1c17a, 0x1c18e, 0x1c198], 'bounded reference census')

captures = []
for relative in ['volatile-limit-trial-20261028dk/score-baseline-01',
                 'volatile-limit-trial-20261028dk/reference-onset-01',
                 'volatile-limit-trial-20261028dk/dv-observation-01',
                 'volatile-limit-trial-20261028dk/dv-rechallenge-01',
                 'lane-gate-onset-20261028ee/onset-01']:
    directory = B / relative
    result = json.loads((directory / 'result.json').read_bytes())
    need(result['accepted'] is True and result['cleanup'] == 'STAGE_ABSENT', 'accepted saved result')
    pinned = {row['name']: row for row in result['rawFiles']}
    for mf in sorted(directory.glob('retained-*-01-M.bin')):
        prefix = mf.name[:-len('01-M.bin')]
        paths = [mf, directory / (prefix + '02-C.bin'), directory / (prefix + '03-P.bin')]
        values = []
        for path, size in zip(paths, (68, 16, 16)):
            content = path.read_bytes()
            need(len(content) == size and sha(content) == pinned[path.name]['sha256'], 'saved window ' + path.name)
            values.append(content)
        m, c, p = values
        captures.append({'capture': relative, 'prefix': prefix,
                         'files': [{'name': path.name, 'sha256': sha(value)} for path, value in zip(paths, values)],
                         'selectorC7': c[7], 'trainer4a2': struct.unpack_from('<H', m, 2)[0],
                         'trainerAggregate4a4': struct.unpack_from('<H', m, 4)[0],
                         'selectorMirror4c2': struct.unpack_from('<H', m, 34)[0],
                         'referenceRefreshCounter4c4': struct.unpack_from('<H', m, 36)[0],
                         'capturedDynamicAPointer': hex(struct.unpack_from('<I', p, 4)[0]),
                         'capturedDynamicBPointer': hex(struct.unpack_from('<I', p, 8)[0])})

ranges = [(0x38f4, 12), (0x4440, 10), (0xb810, 0x98), (0xc250, 0xa8), (0x1c12c, 0x84)]
report = {'schema': 'eg-reference-refresh-source-v1', 'selectedAssetSha256': sha(raw),
          'targetOperations': 0, 'instructionHooksInstalled': False, 'anchors': anchors,
          'literals': {hex(va): hex(value) for va, value in literals.items()},
          'sourceRanges': [{'va': hex(va), 'bytes': size, 'sha256': sha(data[va:va + size])} for va, size in ranges],
          'syntactic4c4References': refs, 'completeWriterCensus': False,
          'retainedBoundarySamples': captures, 'intermediateCounterHistoryRecovered': False,
          'historicalActualBHeaderProven': False, 'rootCauseOrPreventionEstablished': False}
out = (json.dumps(report, indent=2) + '\n').encode()
if sys.argv[1:] == ['--record']:
    with (D / 'source-audit.json').open('xb') as stream:
        stream.write(out)
else:
    need((D / 'source-audit.json').read_bytes() == out, 'frozen source report')
print(json.dumps({'accepted': True, 'checks': checks, 'boundarySamples': len(captures), 'sourceAuditSha256': sha(out), 'targetOperations': 0}))
