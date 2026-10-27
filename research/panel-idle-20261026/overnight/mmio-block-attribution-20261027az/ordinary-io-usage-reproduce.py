#!/usr/bin/env python3
"""Offline byte checks for selected-image-0 ordinary MMIO-block usage."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
BASE = OVERNIGHT.parent
PACKAGE = OVERNIGHT / 'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pinned(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    need(sha(raw) == expected, 'identity: ' + str(path))
    return raw


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def thumb_bl_target(image: bytes, address: int) -> int | None:
    if address < 0 or address + 4 > len(image) or address & 1:
        return None
    first, second = struct.unpack_from('<HH', image, address)
    if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
        return None
    s = (first >> 10) & 1
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    i1 = 1 ^ (j1 ^ s)
    i2 = 1 ^ (j2 ^ s)
    encoded = ((s << 24) | (i1 << 23) | (i2 << 22) |
               ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    return address + 4 + sign_extend(encoded, 25)


def callers(image: bytes, target: int) -> list[int]:
    return [address for address in range(0, len(image) - 3, 2)
            if thumb_bl_target(image, address) == target]


def exact(image: bytes, start: int, end: int, expected: str) -> None:
    need(sha(image[start:end]) == expected, f'image-0 range {start:x}..{end:x}')


def u32(image: bytes, offset: int) -> int:
    return struct.unpack_from('<I', image, offset)[0]


def main() -> None:
    # These three reports are inputs only for prior results and scope boundaries.
    pinned(OVERNIGHT / 'rtp-action-causality-20261027t/rtp-action-causality.md',
           '4465ca1a50b9c4a851cf0233a4172e930987b1b1dec7f1b7d3972e264755dbb5')
    pinned(BASE / 'tcon-research/owner-photo-board-map.md',
           '93ede258bbb6f5b163466205c0ed828cf0b912ec0a1dacdc9ec7371d07f0f0a3')
    pinned(BASE / 'tcon-research/qd-emergency-loop-output-sequence.md',
           '02fe780962a6c4894351aea6b547aa03628c92d64b95a56f69f1d3b717230a6d')

    package = pinned(PACKAGE,
                     'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0')
    need(len(package) == 5_242_880, 'package extent')
    image = package[0x200:0x40200]
    need(len(image) == 0x40000, 'selected image-0 extent')

    # Corrected image-0 coordinates and finite positive bodies.
    for start, end, digest in [
        (0x3DFC, 0x3E14, 'fcb86b1b0ae40b9bc1028553195339714f4093f392c17ab6379d05c71d292583'),
        (0x3E14, 0x3E2C, '6dcca660a03c895a2a4f098dbe79d8d35485dbd55acefb4b083161613e9763b1'),
        (0x25B24, 0x25B60, '94f4a4f1407e57b0e80f80fa4b16b353b6c41dd7f98d566203b916f1f1387b48'),
        (0x40F4, 0x41D0, 'e3ffa3b78352ea9121badf6c6bd5024b514e319c5ab29af6700bc19e9ae65aec'),
        (0x41D0, 0x423C, 'ff2fdbe01813c49a772f4a0bb9f2462ae8d51b65e22e7ffc0d7537d179d807d9'),
        (0xD810, 0xD834, '523a6774a8636b6db91e4faad9b49dc4b5eec329191c2136b7c9e73cf9942484'),
        (0x14910, 0x149BC, '5fcc7bea9301c9aa6b815a92fff05ac97769daf64e9eccbe1bac23f5667e3d18'),
        (0x1E02C, 0x1E32E, '310b70a2bda4673776316802a58fb30fbc031ec91f0b7776450d0fd1ec434bbe'),
        (0x39998, 0x39BD8, 'bb0f071510538b63f5fabadaf5e9e90ef4a6ae547c51e85e0bfc48b014e34f0a'),
        (0x39BDA, 0x39C4E, 'e2d3cc629921b0cdccdd3151a4b545dbb594c5b214ff87faf9e7c81c03bd8936'),
    ]:
        exact(image, start, end, digest)

    # Exact small helpers: clear a RAM byte, then issue a fixed full-word store.
    need(image[0x3DFC:0x3E14] == bytes.fromhex(
        '00200349087008200249086170470000b00c002000001340'), '0x3dfc body')
    need(image[0x3E14:0x3E2C] == bytes.fromhex(
        '0020034908704ff40070024908617047b10c002000201340'), '0x3e14 body')
    need(u32(image, 0x3E0C) == 0x20000CB0 and u32(image, 0x3E10) == 0x40130000,
         '0x3dfc literals')
    need(u32(image, 0x3E24) == 0x20000CB1 and u32(image, 0x3E28) == 0x40132000,
         '0x3e14 literals')

    # 0x25b24 always calls 0x3dfc; conditionally calls 0x3e14; argument!=0
    # reaches the two final stores. These checks bind calls, literals and opcodes.
    need(thumb_bl_target(image, 0x25B2E) == 0x3DFC, '0x25b24 first helper')
    need(thumb_bl_target(image, 0x25B3C) == 0x3E14, '0x25b24 conditional helper')
    need(u32(image, 0x25B58) == 0x40132000 and
         u32(image, 0x25B5C) == 0x40131000, '0x25b24 literals')
    need(image[0x25B48:0x25B56] == bytes.fromhex(
        '2db1802002490861042002490861'), '0x25b24 nonzero stores')

    # The generic indexed pair selects six 0x1000-spaced blocks. The first
    # helper RMWs a selected nibble in +0/+4; the second reads a selected bit
    # from +0x18. Names/physical roles are deliberately not assigned.
    block_bases = [u32(image, offset) for offset in
                   (0x41B8, 0x41BC, 0x41C0, 0x41C4, 0x41C8, 0x41CC)]
    read_bases = [u32(image, offset) for offset in
                  (0x4224, 0x4228, 0x422C, 0x4230, 0x4234, 0x4238)]
    expected_bases = [0x40130000, 0x40131000, 0x40132000,
                      0x40133000, 0x40134000, 0x40135000]
    need(block_bases == expected_bases and read_bases == expected_bases,
         'six-block generic helper pools')
    need(callers(image, 0x40F4) == [0xD81A] and callers(image, 0x41D0) == [0xD82A],
         'generic helper wrappers')

    # 0x1e02c is called twice in the broad pre-loop initialization sequence.
    # It invokes both fixed helpers, then directly writes the same four exact
    # addresses later used by the selector action.
    need(callers(image, 0x1E02C) == [0x39A3E, 0x39B3A], 'pre-loop init callers')
    need(thumb_bl_target(image, 0x1E258) == 0x3E14 and
         thumb_bl_target(image, 0x1E272) == 0x3DFC, 'init helper calls')
    startup_stores = [
        # value instruction, literal-load, pool, base, store, offset, value
        (0x1E264, 0x1E266, 0x1E33C, 0x40134000, 0x1E268, 0x0C, 0x08),
        (0x1E27E, 0x1E280, 0x1E338, 0x40130000, 0x1E282, 0x10, 0x10),
        (0x1E28C, 0x1E28E, 0x1E340, 0x40131000, 0x1E290, 0x10, 0x04),
        (0x1E29A, 0x1E29C, 0x1E344, 0x40132000, 0x1E29E, 0x10, 0x80),
    ]
    expected_code = {
        0x1E264: '0820', 0x1E266: '3549', 0x1E268: 'c860',
        0x1E27E: '1020', 0x1E280: '2d49', 0x1E282: '0861',
        0x1E28C: '0420', 0x1E28E: '2c49', 0x1E290: '0861',
        0x1E29A: '8020', 0x1E29C: '2949', 0x1E29E: '0861',
    }
    for value_at, load_at, pool, base, store_at, _offset, _value in startup_stores:
        need(image[value_at:value_at + 2].hex() == expected_code[value_at], 'startup value')
        need(image[load_at:load_at + 2].hex() == expected_code[load_at], 'startup literal load')
        need(image[store_at:store_at + 2].hex() == expected_code[store_at], 'startup store')
        need(u32(image, pool) == base, 'startup literal value')

    # The selector-0x10 arm supplies the fourth emergency store exactly.
    need(thumb_bl_target(image, 0x14976) == 0x25B24 and
         u32(image, 0x149C0) == 0x40134000 and
         image[0x1497A:0x14980] == bytes.fromhex('10201049c860'),
         'selector-0x10 0x4013400c store')

    direct = {
        '0x3dfc': callers(image, 0x3DFC),
        '0x3e14': callers(image, 0x3E14),
        '0x25b24': callers(image, 0x25B24),
    }
    need(direct == {
        '0x3dfc': [0x1DCE6, 0x1DD02, 0x1DD4C, 0x1DD80, 0x1E272, 0x25B2E],
        '0x3e14': [0x1DCE2, 0x1DD06, 0x1DD48, 0x1DE90, 0x1E258, 0x25B3C],
        '0x25b24': [0x14976, 0x14998, 0x149A6, 0x149B0],
    }, 'bounded direct-call census')

    print(json.dumps({
        'target_operations': 0,
        'package_sha256': sha(package),
        'corrected_image0_functions': ['0x3dfc', '0x3e14', '0x25b24'],
        'fixed_helper_effects': {
            '0x3dfc': {'ram_byte': '0x20000cb0 <- 0',
                       'mmio': '0x40130010 <- 0x00000008'},
            '0x3e14': {'ram_byte': '0x20000cb1 <- 0',
                       'mmio': '0x40132010 <- 0x00000200'},
            '0x25b24_nonzero_final': ['0x40132010 <- 0x00000080',
                                      '0x40131010 <- 0x00000004'],
        },
        'direct_callers': {key: [f'0x{x:x}' for x in value]
                           for key, value in direct.items()},
        'generic_six_block_helpers': {
            'bases': [f'0x{x:08x}' for x in block_bases],
            'configuration_body': '0x40f4',
            'status_body': '0x41d0',
            'wrappers': ['0xd810', '0xd822'],
            'hardware_role_named': False,
        },
        'pre_loop_initialization': {
            'body': '0x1e02c..0x1e32d',
            'callers': ['0x39a3e', '0x39b3a'],
            'same_exact_addresses': {
                '0x40130010': ['0x00000008 via 0x3dfc', '0x00000010 direct'],
                '0x40131010': ['0x00000004 direct'],
                '0x40132010': ['0x00000200 via 0x3e14', '0x00000080 direct'],
                '0x4013400c': ['0x00000008 direct'],
            },
            'precedes_ordinary_recurring_loop': True,
        },
        'conclusions': {
            'four_addresses_emergency_unique': False,
            'four_addresses_part_of_broader_indexed_block_family': True,
            'register_roles_or_physical_effects_identified': False,
            'executing_image_or_runtime_write_proved': False,
            'whole_program_reference_absence_claimed': False,
        },
    }, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
