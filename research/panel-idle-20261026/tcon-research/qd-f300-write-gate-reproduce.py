#!/usr/bin/env python3
"""Inspect exact selected-profile F300 gates offline; never contacts a device."""
import hashlib
import json
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
EXPECTED = 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0'
b = SOURCE.read_bytes()


def need(condition, message):
    if not condition:
        raise ValueError(message)


need(len(b) == 5242880 and hashlib.sha256(b).hexdigest() == EXPECTED,
     'selected-profile identity mismatch')
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)


def word(va):
    return struct.unpack_from('<I', b, va + 0x200)[0]


def ins(va):
    i = next(md.disasm(b[va + 0x200:va + 0x204], va, count=1), None)
    need(i is not None, f'no instruction at {va:#x}')
    return i.mnemonic, i.op_str


# Instruction guards cover the actual gate, its decoded stores, and callers.
checks = {
    0x2c750: ('ldr', 'r0, [pc, #0x50]'),
    0x2c752: ('ldrb', 'r0, [r0]'),
    0x2c754: ('cmp', 'r0, #1'),
    0x2c756: ('beq', '#0x2c75e'),
    0x2c758: ('cmp', 'r0, #2'),
    0x2c75a: ('bne', '#0x2c77a'),
    0x2c762: ('ldrh.w', 'r0, [sb, #6]'),
    0x2c766: ('cbnz', 'r0, #0x2c770'),
    0x2c768: ('movs', 'r0, #0'),
    0x2c76c: ('strb', 'r0, [r1]'),
    0x2c770: ('cmp.w', 'r6, #0x180'),
    0x2c776: ('b', '#0x2c75e'),
    0x96cc: ('movs', 'r0, #1'),
    0x96d0: ('strb', 'r0, [r1]'),
    0xb654: ('movs', 'r0, #0'),
    0xb658: ('strb', 'r0, [r1]'),
    0x57ba: ('bl', '#0x96cc'),
    0x4fcc: ('bl', '#0xb654'),
    0x2e56e: ('bl', '#0xb654'),
    0x2558e: ('movs', 'r0, #1'),
    0x25592: ('strb', 'r0, [r1]'),
    0x2ce04: ('bl', '#0x2555c'),
    0x2ce38: ('strh.w', 'r0, [sb, #6]'),
    0x2ce40: ('movs', 'r0, #2'),
    0x2ce44: ('strb', 'r0, [r1]'),
    0x2ce4c: ('strh.w', 'r0, [sb, #6]'),
    0x2ce52: ('strb', 'r0, [r1]'),
    0x21c30: ('ldrh.w', 'r0, [r4, #0xa6]'),
    0x21c34: ('ubfx', 'r0, r0, #0, #0xa'),
    0x21c38: ('b', '#0x2178e'),
    0x2cc96: ('ubfx', 'r0, r4, #0, #0xa'),
    0x2cc9a: ('strh.w', 'r0, [r5, #0xa6]'),
}
for va, expected in checks.items():
    need(ins(va) == expected, f'instruction mismatch at {va:#x}: {ins(va)!r}')

gate_literals = (0x96d4, 0xb65c, 0x2559c, 0x2c7a4, 0x2cf54)
need(all(word(va) == 0x200008e8 for va in gate_literals), 'gate literal mismatch')
need(word(0xefa0) == 0x2000d71c, 'staged-object getter changed')
need(word(0xe67c) == 0x2000ff14, 'special-gate object getter changed')
need(word(0x4fe0) == word(0x57d8) == 0x20000c98, 'PTM state root mismatch')
need(b[0x57cc + 0x200:0x57cc + 0x200 + 11] == b'Start PTM\n\0', 'start string mismatch')
need(b[0x4fe4 + 0x200:0x4fe4 + 0x200 + 9] == b'End PTM\n\0', 'end string mismatch')
selectors = {}
for selector in (0x128, 0x160, 0x180):
    target = 0x2c7b4 + word(0x2c7b4 + ((selector >> 2) - 9) * 4)
    selectors[hex(selector)] = hex(target)
need(selectors == {'0x128': '0x2cc96', '0x160': '0x2cdfc', '0x180': '0x2ce2a'},
     'write table mapping mismatch')

def slice_record(start, end):
    data = b[start + 0x200:end + 0x200]
    return {'va_start': hex(start), 'va_end_exclusive': hex(end),
            'file_start': hex(start + 0x200), 'size': len(data),
            'sha256': hashlib.sha256(data).hexdigest(),
            'instructions': [{'va': hex(i.address), 'mnemonic': i.mnemonic,
                              'operands': i.op_str}
                             for i in md.disasm(data, start)]}

print(json.dumps({
    'source_sha256': EXPECTED,
    'address_convention': 'image0 linked VA = file offset - 0x200; RAM addresses unchanged',
    'gate_ram': '0x200008e8',
    'special_gate_halfword': '0x2000ff1a',
    'staged_scalar_halfword': '0x2000d7c2',
    'write_table_targets': selectors,
    'gate_literal_vas': [hex(x) for x in gate_literals],
    'verified_instructions': len(checks),
    'slices': [slice_record(a, z) for a, z in (
        (0x2c71c, 0x2c7a4), (0x96cc, 0x96d4), (0xb654, 0xb65c),
        (0x5798, 0x57c6), (0x4f80, 0x4fde), (0x2555c, 0x2559a),
        (0x2cdfc, 0x2ce0a), (0x2ce2a, 0x2ce56), (0x2e4ec, 0x2e57a),
        (0x21c30, 0x21c3a), (0x2cc96, 0x2cca0))],
    'limits': [
        'Offline selected-package analysis only; no current-controller flash equality.',
        'No gate value was measured on the TV.',
        'Explicit literal-backed references were traced; computed/indirect writers are not excluded.',
        'No protection or recovery semantics inferred from a RAM gate.',
        'No target calls, helper deployment, command transmission, or device changes.'
    ]
}, indent=2))
