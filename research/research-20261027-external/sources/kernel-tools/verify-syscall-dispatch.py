#!/usr/bin/env python3
"""Offline only: qualify two normal ABI dispatch tables in the retained Image.

No network, target communication, subprocess execution, or target mutation.
Raw offsets are file coordinates; LINK_BASE is a stored link coordinate, never
a recovered runtime address. This does not hash the executing kernel.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

IMAGE = Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight/kernel-Image.bin')
SHA = '77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d'
LINK_BASE = 0xffffffc010080000

def require(ok, message):
    if not ok:
        raise ValueError(message)

def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def adrp_add(data, offset):
    a, b = word(data, offset), word(data, offset + 4)
    require(a & 0x9f000000 == 0x90000000, 'Expected ADRP')
    require(b & 0xffc00000 == 0x91000000, 'Expected unshifted ADD immediate')
    reg = a & 31
    require(reg == 2 and (b >> 5) & 31 == reg and b & 31 == reg, 'Expected x2 table construction')
    immediate = ((a >> 29) & 3) | (((a >> 5) & 0x7ffff) << 2)
    if immediate & (1 << 20):
        immediate -= 1 << 21
    return (offset & ~4095) + (immediate << 12) + ((b >> 10) & 4095)

def bl_target(data, offset):
    w = word(data, offset)
    require(w & 0xfc000000 == 0x94000000, 'Expected BL')
    imm = w & 0x3ffffff
    if imm & (1 << 25):
        imm -= 1 << 26
    return offset + 4 * imm

def verify(data):
    require(hashlib.sha256(data).hexdigest() == SHA, 'Different saved Image')
    require(data[56:60] == b'ARMd', 'Expected ARM64 Image magic')
    sites = [(0x19054, 0x7f07e0, 0x1905c), (0x190a0, 0x7f07e0, 0x190a8),
             (0x190d4, 0x7f5028, 0x190e4)]
    for site, table, branch in sites:
        require(adrp_add(data, site) == table, 'Wrong constructed table')
        require(bl_target(data, branch) == 0x18ec8, 'Wrong common dispatch target')
    # Register frame syscall inputs x8 for AArch64, x7 for AArch32.
    instructions = {0x19050: 0xb9404001, 0x1909c: 0xb9404001, 0x190e0: 0xb9403801,
                    0x18ee0: 0xaa0203f5,  # mov x21,x2: retain table
                    0x18f08: 0x7106d43f,  # cmp w1,#437: inclusive table bound
                    0x18f28: 0xf8617aa1,  # ldr x1,[x21,x1,lsl #3]
                    0x18f2c: 0xd63f0020}  # blr x1
    for offset, expected in instructions.items():
        require(word(data, offset) == expected, f'Changed dispatch at {offset:#x}')
    tables = {'aarch64': 0x7f07e0, 'aarch32_compat': 0x7f5028}
    results = []
    for abi, table in tables.items():
        entries = struct.unpack_from('<438Q', data, table)
        require(all(LINK_BASE <= p < LINK_BASE + len(data) and p % 4 == 0 for p in entries),
                'A table target leaves the saved Image')
        checks = [('perf_event_open', 241 if abi == 'aarch64' else 364, 0x52388),
                  ('bpf', 280 if abi == 'aarch64' else 386, 0x52430)]
        for name, nr, target in checks:
            require(entries[nr] == LINK_BASE + target, 'Unexpected handler pointer')
            require(data[target:target + 8] == bytes.fromhex('a0048092c0035fd6'),
                    'Expected MOVN x0,#37 (x0=-38), RET only')
            results.append({'abi': abi, 'name': name, 'number': nr,
                            'table_file_offset': hex(table),
                            'entry_file_offset': hex(table + nr * 8),
                            'handler_image_offset': hex(target),
                            'handler_bytes': data[target:target + 8].hex(), 'return': -38})
    # Independent ABI consistency anchors, beyond the two queried entries.
    get = lambda t, n: struct.unpack_from('<Q', data, t + n * 8)[0]
    for native, compat in [(172, 20), (93, 1), (64, 4)]:
        require(get(tables['aarch64'], native) == get(tables['aarch32_compat'], compat),
                'getpid/exit/write cross-ABI anchor mismatch')
    return {'image_sha256': SHA, 'status': 'stored_image_both_abis_ENOSYS_stubs',
            'target_operations': 0, 'executing_text_identity_proved': False,
            'link_coordinate_base_not_runtime_address': hex(LINK_BASE),
            'embedded_IKCFG_ST_marker_offset': data.find(b'IKCFG_ST'),
            'dispatcher_file_range': ['0x18ec8', '0x190f0'],
            'dispatcher_sha256': hashlib.sha256(data[0x18ec8:0x190f0]).hexdigest(),
            'syscalls': results}

if __name__ == '__main__':
    print(json.dumps(verify(IMAGE.read_bytes()), indent=2))
