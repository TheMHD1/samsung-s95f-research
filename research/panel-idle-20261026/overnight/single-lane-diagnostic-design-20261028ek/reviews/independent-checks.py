#!/usr/bin/env python3
"""Offline independent EK review. No native/USB/network imports or target execution."""
import hashlib
import json
import struct
import sys
from dataclasses import replace
from pathlib import Path

sys.dont_write_bytecode = True
D = Path(__file__).resolve().parent.parent
B = D.parent
sys.path.insert(0, str(D))
import state_model as model
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS

checks = 0


def need(value, label):
    global checks
    checks += 1
    if not value:
        raise ValueError(label)


def rejected(fn, label):
    try:
        fn()
    except ValueError:
        need(True, label)
        return
    raise ValueError('unexpected model admission: ' + label)


def sha(data):
    return hashlib.sha256(data).hexdigest()


inventory_raw = (D / 'source-inventory.json').read_bytes()
need(sha(inventory_raw) == 'caca76ba6a9dfe3bee8df33d198e38c836710abff7e65470393840ab063ef0f8', 'frozen EK inventory')
for row in json.loads(inventory_raw)['files']:
    data = (D / row['path']).read_bytes()
    need(len(data) == row['bytes'] and sha(data) == row['sha256'], 'EK source bytes')
pins = json.loads((D / 'input-pins.json').read_text())['files']
for row in pins:
    data = Path(row['path']).read_bytes()
    need(len(data) == row['bytes'] and sha(data) == row['sha256'], 'retained input pin')

plan = json.loads((D / 'design.json').read_text())
source = json.loads((D / 'source-qualification.json').read_text())
need(struct.unpack('<III', bytes.fromhex(plan['setHeaderLittleEndianHex'])) == (0x102, 0x47010474, 2), 'independent set header fields')
need(plan['restoreHeaderLittleEndianHex'] == plan['setHeaderLittleEndianHex'], 'fixed restore address and length')
need(bytes.fromhex(plan['setPayloadHex']) == b'\x01\x00' and bytes.fromhex(plan['restorePayloadHex']) == b'\x00\x00', 'little endian fixed word payloads')
need(0x20010000 + 570 * 2 == 0x20010474 and 0x20010474 + 0x27000000 == 0x47010474, 'CPU to bus and index')
need(0x47010474 % 2 == 0 and 0x47010474 + 2 <= 0x47020000, 'aligned complete SRAM interval')
need((0x47010474 - 0x47010470, (0x2000c95c + 570) - (0x4700cb94 - 0x27000000)) == (4, 2), 'two window offsets')
expected_names = ['Rpre', 'Mpre', 'Cpre', 'Secondarypre', 'Primarypre', 'Rfresh', 'Mfresh', 'Cfresh', 'Secondaryfresh', 'Primaryfresh', 'Primaryreadback', 'Rpost', 'Mpost', 'Cpost', 'Secondarypost', 'Primarypost']
need([r['name'] for r in plan['readSchedule']] == expected_names and plan['writeHeaderIndexAfterReadPair'] == 10, 'exact fixed action schedule')
allowed = {(0x47012400, 256), (0x470004a0, 68), (0x47000bc0, 16), (0x4700cb94, 68), (0x47010470, 136)}
for row in plan['readSchedule']:
    fields = struct.unpack('<III', bytes.fromhex(row['headerLittleEndianHex']))
    need(fields == (0x101, int(row['busAddress'], 16), row['bytes']) and fields[1:] in allowed, 'read-only fixed packet')
need(sum(r['bytes'] for r in plan['readSchedule']) == 1768 and len(plan['readSchedule']) == 16, 'input byte count')
need(plan['perSeparateAction']['headers'] == 17 and plan['perSeparateAction']['bulkTransfers'] == 34, 'pair totals')
need(plan['deadlineProposal']['minimumBeforeWriteReserveSeconds'] == 2 * 2 + 6 * 2 * 2 + 4, 'conditional write reserve arithmetic')
need(plan['deadlineProposal']['hardNativeProcessAlarmImplemented'] is False and plan['helperImplemented'] is False, 'design has no alarm or helper')

package = (B / 'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
need(len(package) == 5242880 and sha(package) == source['selectedPackageSha256'], 'selected package')
image0 = package[0x200:0x40200]
image1 = package[0x40200:0x60200]
cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
for row in source['positiveFingerprintProposal']:
    va = int(row['linkedVa'], 16)
    size = row['bytes']
    need(int(row['busAddress'], 16) == 0x46000000 + va and va + size <= 0x20000, 'complete code/resource alias interval')
    need(sha(image1[va:va + size]) == row['expectedSha256'], 'fingerprint source hash')
    need(struct.unpack('<III', bytes.fromhex(row['readHeaderLittleEndianHex'])) == (0x101, 0x46000000 + va, size), 'fingerprint read header')
need(sum(row['bytes'] for row in source['positiveFingerprintProposal']) == 324, 'complete five-region bytes')

# These are source instruction assertions, never code execution or raw output.
anchors = {
    0xbf20: ('adds', 'r0, r4, #2'),
    0xbf22: ('ldrb.w', 'r0, [r5, r0, lsl #1]'),
    0xbf26: ('and', 'r0, r0, #1'),
    0xbf2a: ('cbnz', 'r0, #0xbf62'),
    0xbf30: ('ldrb', 'r0, [r1, r0]'),
    0xbf34: ('cmp.w', 'sb, #0'),
    0xbf38: ('beq', '#0xbf62'),
}
for va, expected in anchors.items():
    ins = next(cs.disasm(image1[va:va + 4], va, count=1))
    need((ins.mnemonic, ins.op_str) == expected, 'selected third-lane gate anchor')

# Bounded independent protocol-risk source anchors from image0.
protocol_anchors = {
    0x28f68: ('bl', '#0x29258'),
    0x28f6c: ('cmp', 'r0, #2'),
    0x28f6e: ('bne', '#0x28f74'),
    0x28fc0: ('and', 'r0, r0, #0xef'),
    0x29284: ('cmp', 'r6, #0xc'),
    0x29286: ('bhs', '#0x2929a'),
    0x29294: ('movs', 'r0, #2'),
    0x292ea: ('cmp.w', 'r0, #0x102'),
    0x292ee: ('beq', '#0x29382'),
    0x2912c: ('cmp', 'r0, #2'),
    0x29146: ('ldr', 'r2, [r4, #4]'),
    0x29148: ('bl', '#0x7fce'),
    0x7fea: ('str', 'r6, [r4, #0x10]'),
    0x7fec: ('str.w', 'r8, [r4, #0x18]'),
    0x8002: ('bl', '#0x2ac10'),
    0x2ac90: ('ldr', 'r0, [r4, #8]'),
    0x2ac92: ('subs', 'r0, r0, #1'),
    0x2ac94: ('ldr', 'r1, [r4, #0x18]'),
    0x2ac96: ('add', 'r0, r1'),
    0x2ac98: ('ldr', 'r1, [r4, #8]'),
    0x2ac9a: ('udiv', 'r0, r0, r1'),
    0x2ac9e: ('mul', 'r8, r0, r1'),
    0x2aca8: ('bl', '#0x280c'),
    0x296e: ('adds', 'r0, r6, r4'),
    0x2970: ('str', 'r0, [r1, #4]'),
}
for va, expected in protocol_anchors.items():
    ins = next(cs.disasm(image0[va:va + 4], va, count=1))
    need((ins.mnemonic, ins.op_str) == expected, 'image0 protocol source anchor')
for maxpacket in (64, 512, 1024):
    capacity = ((maxpacket - 1 + 2) // maxpacket) * maxpacket
    need(capacity == maxpacket and capacity > 2, 'OUT descriptor capacity is not requested two-byte payload')

a = model.Context(fingerprints_verified=True)
pending = model.admit_set(a, a)
for field in ['root', 'rows', 'lanes', 'packed_bytes', 'x_base', 'aa', 'ac', 'operating_mode', 'trainer', 'writer_2460', 'publisher_246e', 'refresh_counter', 'selector_mirror', 'primary', 'selector', 'secondary']:
    for bad in [True, False, -1, 65536, None, 0.0, '0']:
        rejected(lambda field=field, bad=bad: model.admit_set(replace(a, **{field: bad}), replace(a, **{field: bad})), 'exact unsigned context types/width/fixed values')
for count in range(-2, 32):
    t = model.Transfer()
    t.header(count)
    if count != 12:
        need(t.phase == 'Unknown' and t.write_may_have_changed, 'unknown header failclosed')
        rejected(lambda: t.header(12), 'no header after ambiguity')
        rejected(lambda: t.payload(2), 'no speculative pending payload')
for count in range(-2, 16):
    t = model.Transfer()
    t.header(12)
    t.payload(count)
    if count != 2:
        need(t.phase == 'Unknown' and t.write_may_have_changed, 'unknown payload failclosed')
        rejected(lambda: t.header(12), 'no restore/read header after ambiguity')
t = model.Transfer()
t.header(12)
t.payload(2)
t.readback(1, 1)
one = replace(a, primary=1)
owner = model.confirm_set(pending, t, one, one)
need(model.admit_restore(owner, one, one) == 0, 'normal guarded restore admission')
fault = replace(one, rt=(1, 0x1001, 0), selector=1, selector_mirror=1)
need(model.admit_restore(owner, fault, fault) == 0, 'coherent fault does not prevent restore')
for index in range(67):
    words = list(a.other_primary_words)
    words[index] = 1
    changed = replace(one, other_primary_words=tuple(words))
    rejected(lambda: model.admit_restore(owner, changed, changed), 'every neighboring primary word guarded')
    flags = list(a.other_secondary_bytes)
    flags[index] = 1
    changed = replace(one, other_secondary_bytes=tuple(flags))
    rejected(lambda: model.admit_restore(owner, changed, changed), 'every neighboring secondary byte guarded')

# Explicitly prove what this small model DOES NOT enforce. Not helper defects:
# there is no helper, and these omissions must not become implementation claims.
same_value_stock_context = replace(one)
need(model.admit_restore(owner, same_value_stock_context, same_value_stock_context) == 0, 'indistinguishable same-value stock publication cannot be detected')
t.header(12)
need(t.phase == 'ExpectingWritePayload', 'pure transfer object does not enforce one-write-per-process budget')
loose = model.Transfer()
loose.header(12)
loose.payload(2)
loose.readback(0, 0)
need(model.confirm_set(pending, loose, one, one).set_readback_verified, 'pure transfer model does not bind generic readback expected value; full post-context still required')

print(json.dumps({
    'schema': 'ek-independent-host-review-checks-v1',
    'accepted': True,
    'checks': checks,
    'frozenInventorySha256': sha(inventory_raw),
    'inputPinsVerified': len(pins),
    'instructionAnchorsVerified': len(anchors) + len(protocol_anchors),
    'protocolSourceImage': 'selected image0, file=VA+0x200',
    'protocolSourceSpans': [{'va': hex(a), 'bytes': z - a, 'sha256': sha(image0[a:z])} for a, z in [(0x29284, 0x2929a), (0x2912a, 0x2914e), (0x7fce, 0x800c), (0x2ac86, 0x2acac), (0x296e, 0x2972)]],
    'sourcePacketAndModelConsistent': True,
    'helperOrDeploymentQualified': False,
    'completeWriterExclusionProven': False,
    'unknownPhaseReentryQualified': False,
    'modelLimitationsExercised': ['indistinguishable-ABA', 'one-write-budget-not-modeled', 'generic-readback-value-not-bound'],
    'targetOperations': 0,
    'networkOperations': 0,
}, sort_keys=True))
