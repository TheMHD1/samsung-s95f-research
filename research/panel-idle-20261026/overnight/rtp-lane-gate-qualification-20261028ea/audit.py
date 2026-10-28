#!/usr/bin/env python3
"""Host-only source qualification of the existing unpacker lane eligibility gates."""
from pathlib import Path
import hashlib
import json
import struct
import sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN, CS_MODE_MCLASS

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
B = HERE.parent
ASSET = B / 'firmware-rtp-producer-20261028df/private/official-selected-package.bin'
PRED = B / 'volatile-limit-trial-20261028dk/dv-final-clean-01'
checks = 0
def need(value, why):
    global checks
    if not value:
        raise ValueError(why)
    checks += 1
def sha(raw):
    return hashlib.sha256(raw).hexdigest()

raw = ASSET.read_bytes()
need(len(raw) == 5242880 and sha(raw) == 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0', 'selected package')
def data(va, length):
    return raw[0x40200 + va:0x40200 + va + length]
def word(va):
    return struct.unpack('<I', data(va, 4))[0]
decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
anchors = []
def ins(va, mnemonic, operands):
    decoded = list(decoder.disasm(data(va, 4), va, count=1))
    need(len(decoded) == 1 and decoded[0].mnemonic == mnemonic and decoded[0].op_str == operands,
         'instruction ' + hex(va))
    row = decoded[0]
    anchors.append({'va': hex(va), 'mnemonic': mnemonic, 'operands': operands,
                    'bytes': row.size, 'sha256': sha(data(va, row.size))})

for args in [
    (0xbd6c, 'bl', '#0x38fc'), (0xbd70, 'mov', 'r5, r0'),
    (0x38fc, 'ldr', 'r0, [pc, #4]'), (0x38fe, 'ldr', 'r0, [r0]'),
    (0x3900, 'bx', 'lr'),
    (0xbe0c, 'movw', 'r0, #0x2410'), (0xbe10, 'ldrh', 'r0, [r0, r5]'),
    (0xbe12, 'cmp', 'r0, #6'), (0xbe14, 'bge', '#0xbf14'),
    (0xbe16, 'ldr', 'r0, [pc, #0x228]'), (0xbe18, 'ldrh', 'r0, [r0]'),
    (0xbe1a, 'cmp', 'r0, #1'), (0xbe1c, 'beq', '#0xbe26'),
    (0xbe1e, 'ldr', 'r0, [pc, #0x210]'), (0xbe20, 'ldrh', 'r0, [r0]'),
    (0xbe22, 'cmp', 'r0, #1'), (0xbe24, 'bne', '#0xbe30'),
    (0xbe26, 'ldr', 'r0, [pc, #0x21c]'), (0xbe28, 'ldrb', 'r0, [r0]'),
    (0xbe2a, 'cbz', 'r0, #0xbe30'), (0xbe2c, 'movs', 'r0, #1'),
    (0xbe2e, 'b', '#0xbe32'), (0xbe30, 'movs', 'r0, #0'),
    (0xbe32, 'mov', 'sb, r0'),
    (0xbeb4, 'ldrb.w', 'r0, [r5, r4, lsl #1]'),
    (0xbeb8, 'and', 'r0, r0, #1'), (0xbebc, 'cbnz', 'r0, #0xbee4'),
    (0xbebe, 'ldr', 'r0, [pc, #0x188]'), (0xbec0, 'ldrb', 'r0, [r0, r4]'),
    (0xbec2, 'cbz', 'r0, #0xbeca'), (0xbec4, 'cmp.w', 'sb, #0'),
    (0xbec8, 'beq', '#0xbee4'), (0xbedc, 'bl', '#0xbbbc'),
    (0xbee4, 'adds', 'r0, r4, #1'), (0xbee6, 'ldrb.w', 'r0, [r5, r0, lsl #1]'),
    (0xbeea, 'and', 'r0, r0, #1'), (0xbeee, 'cbnz', 'r0, #0xbf20'),
    (0xbef0, 'ldr', 'r1, [pc, #0x154]'), (0xbef2, 'adds', 'r0, r4, #1'),
    (0xbef4, 'ldrb', 'r0, [r1, r0]'), (0xbef6, 'cbz', 'r0, #0xbefe'),
    (0xbef8, 'cmp.w', 'sb, #0'), (0xbefc, 'beq', '#0xbf20'),
    (0xbf18, 'bl', '#0xbbbc'),
    (0xbf20, 'adds', 'r0, r4, #2'), (0xbf22, 'ldrb.w', 'r0, [r5, r0, lsl #1]'),
    (0xbf26, 'and', 'r0, r0, #1'), (0xbf2a, 'cbnz', 'r0, #0xbf62'),
    (0xbf2c, 'ldr', 'r1, [pc, #0x118]'), (0xbf2e, 'adds', 'r0, r4, #2'),
    (0xbf30, 'ldrb', 'r0, [r1, r0]'), (0xbf32, 'cbz', 'r0, #0xbf3a'),
    (0xbf34, 'cmp.w', 'sb, #0'), (0xbf38, 'beq', '#0xbf62'),
    (0xbf5a, 'bl', '#0xbbbc'),
    (0xbf62, 'adds', 'r0, r4, #3'), (0xbf64, 'ldrb.w', 'r0, [r5, r0, lsl #1]'),
    (0xbf68, 'and', 'r0, r0, #1'), (0xbf6c, 'cbnz', 'r0, #0xbf98'),
    (0xbf6e, 'ldr', 'r1, [pc, #0xd8]'), (0xbf70, 'adds', 'r0, r4, #3'),
    (0xbf72, 'ldrb', 'r0, [r1, r0]'), (0xbf74, 'cbz', 'r0, #0xbf7c'),
    (0xbf76, 'cmp.w', 'sb, #0'), (0xbf7a, 'beq', '#0xbf98'),
    (0xbf90, 'bl', '#0xbbbc'), (0xbf98, 'adds', 'r4, r4, #4'),
    (0xbf9a, 'add.w', 'r0, fp, #6'), (0xbf9e, 'uxth.w', 'fp, r0'),
    (0xbfa2, 'ldr', 'r0, [pc, #0xa8]'), (0xbfa4, 'ldrh', 'r0, [r0]'),
    (0xbfa6, 'cmp', 'fp, r0'), (0xbfa8, 'blt.w', '#0xbe3a')]:
    ins(*args)

for va, expected in [(0x3904, 0x200004e0), (0xc030, 0x200004aa),
                     (0xc040, 0x200004ac), (0xc044, 0x200004cc),
                     (0xc048, 0x2000c95c), (0xc04c, 0x200004a6)]:
    need(word(va) == expected, 'literal ' + hex(va))

saved = json.loads((PRED / 'result.json').read_text())
need(saved['accepted'] is True and saved['cleanup'] == 'STAGE_ABSENT', 'previous completed capture')
m, r = (PRED / 'M.bin').read_bytes(), (PRED / 'end-R.bin').read_bytes()
need(sha(m) == next(row['sha256'] for row in saved['rawFiles'] if row['name'] == 'M.bin'), 'retained M hash')
need(sha(r) == next(row['sha256'] for row in saved['rawFiles'] if row['name'] == 'end-R.bin'), 'retained R hash')
need(len(m) == 68 and len(r) == 256, 'retained context extents')
root = struct.unpack_from('<I', m, 0x40)[0]
aa, ac = struct.unpack_from('<H', m, 10)[0], struct.unpack_from('<H', m, 12)[0]
operating_mode = struct.unpack_from('<H', r, 16)[0]
need(root == 0x20010000 and aa == 0 and ac == 2 and operating_mode == 4,
     'observed prior ordinary root context')
need(struct.unpack_from('<2H', m, 6) == (2880, 1920) and
     struct.unpack_from('<H', m, 32)[0] == 0, 'captured packed geometry and zero x base')
sb = int((aa == 1 or ac == 1) and m[0x2c] != 0)
need(sb == 0, 'observed aa0/ac2 implies secondary override false')

first, last = 568, 635
windows = [
    {'name': 'root-lane-lowbit-table', 'cpuAddress': hex(root + 2*first),
     'busAddress': hex(root + 2*first + 0x27000000), 'bytes': 2*(last-first+1),
     'decode': '68 little-endian halfwords; only low-byte bit0 is tested by this gate'},
    {'name': 'secondary-lane-byte-table', 'cpuAddress': hex(0x2000c95c + first),
     'busAddress': hex(0x2000c95c + first + 0x27000000), 'bytes': last-first+1,
     'decode': '68 bytes; a nonzero value skips unless the source-derived SB override is true'}]
for w in windows:
    address = int(w['cpuAddress'], 16)
    need(0x20000000 <= address and address + w['bytes'] <= 0x20020000, 'complete source SRAM range')
    need(address % 4 == 0, 'fixed read alignment')
    w['target'] = '0x101'
    w['headerLittleEndianHex'] = struct.pack('<III', 0x101, int(w['busAddress'], 16), w['bytes']).hex()

ranges = [(0x38fc, 12), (0xbd6c, 8), (0xbe0c, 0x2c),
          (0xbeb4, 0xe8), (0xc030, 0x24)]
report = {'schema': 'ea-lane-eligibility-source-qualification-v1', 'accepted': True,
          'checks': checks, 'targetOperations': 0, 'assetSha256': sha(raw),
          'sourceRanges': [{'image': 1, 'va': hex(va), 'fileOffset': hex(0x40200+va),
                            'bytes': n, 'sha256': sha(data(va, n))} for va, n in ranges],
          'anchors': anchors, 'sourcePredicate': 'eligible = not(primaryLowByte & 1) and (secondaryByte == 0 or SB != 0)',
          'secondaryOverride': 'SB = ((u16CPU4aa == 1 or u16CPU4ac == 1) and u8CPU4cc != 0)',
          'previousCapturedRoot': hex(root), 'previousCapturedAaAc': [aa, ac],
          'previousCapturedOperatingMode': operating_mode,
          'previousCapturedXBase': 0, 'previousCapturedPackedBytes': 2880,
          'previousCapturedLaneCount': 1920,
          'previousCapturedOverride': sb,
          'liveEligibilityTableRead': False, 'gateBodyLiveFingerprintMatched': False,
          'tableWriteOrFixQualified': False, 'physicalLaneMappingProven': False}
plan = {'schema': 'ea-fixed-lane-table-read-proposal-v1', 'targetOperations': 0,
        'helperImplemented': False, 'firstLane': first, 'lastLaneInclusive': last,
        'windows': windows, 'newHeaders': 2, 'newBulks': 4,
        'newInputBytes': sum(w['bytes'] for w in windows), 'write': False,
        'guards': ['fresh current M root equals0x20010000', 'source geometry and row/channel context retained',
                   'existing reviewed USB ownership/phase/private receipt/cleanup contract',
                   'no dynamic addresses, retry, fallback or target-memory write'],
        'limitations': ['Earlier code fingerprint did not sample the gate body atbeb4..bf98.',
                        'Source path and later record consistency do not attest past gate execution.',
                        'Table writers, units, physical mapping and reset restoration remain to be traced.',
                        'No helper, read, modification or prevention result is established here.']}
pins = {'schema': 'ea-input-pins-v1', 'files': [
    {'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
    for p in [ASSET, PRED/'result.json', PRED/'M.bin', PRED/'end-R.bin']]}
generated = {'source-qualification.json': report, 'fixed-read-plan.json': plan, 'input-pins.json': pins}
for name, value in generated.items():
    payload = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
    if '--check' in sys.argv:
        need((HERE/name).read_bytes() == payload, 'frozen output ' + name)
    else:
        with (HERE/name).open('xb') as f:
            f.write(payload)
print(json.dumps({'accepted': True, 'sourceChecks': report['checks'], 'targetOperations': 0,
                  'plannedInputBytes': plan['newInputBytes'], 'sourceSha256': sha((HERE/'source-qualification.json').read_bytes())}))
