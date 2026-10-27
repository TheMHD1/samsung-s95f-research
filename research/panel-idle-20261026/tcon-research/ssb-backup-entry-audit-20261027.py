#!/usr/bin/env python3
"""Hash-gated landmarks for the bounded SSB backup-entry audit.

The companion Markdown's data-flow interpretation is manual review; this
checker deliberately verifies only source identity, instruction landmarks,
and relocation/symbol evidence.
"""
import hashlib
import struct
import subprocess
from pathlib import Path

MODULE = Path('${S95F_EVIDENCE_ROOT}/panel-idle-20261026/'
              'overnight/sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko')
SHA256 = '1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4'
TEXT_FILE_OFFSET = 0x80

def require(ok, what):
    if not ok:
        raise ValueError(what)

def word(data, va):
    return struct.unpack_from('<I', data, TEXT_FILE_OFFSET + va)[0]

def main():
    data = MODULE.read_bytes()
    require(hashlib.sha256(data).hexdigest() == SHA256, 'exact module hash')
    expected = {
        # initializer: state fields, dimming bits, resolver, register/store
        0x573f8: 0xf9400014, 0x573fc: 0x39401280, 0x57404: 0xb9400a93,
        0x57424: 0x370802c0, 0x5742c: 0x37100280,
        0x57458: 0x35000340, 0x574d8: 0x7100041f, 0x574ec: 0xb9000a80,
        # exported PQE root invokes init before selector dispatch.
        0x58080: 0x97fffcda, 0x58084: 0x35000b60, 0x58094: 0x12003e73,
        0x580b8: 0x7100927f, 0x580cc: 0x94000000,
        0x5811c: 0x7100867f, 0x58368: 0x94000000,
        # ioctl: private check, commands 0x0a/0x0b, raw x2 -> read call.
        0x591d4: 0xf9406680, 0x591dc: 0x71002a7f, 0x591e4: 0x71002e7f,
        0x5921c: 0xaa1503e0, 0x59220: 0xd2800013, 0x59224: 0x94000000,
        # read target: init, copy length, file open, transfer literals.
        0x58a78: 0x97fffa5c, 0x58a7c: 0x35000e00,
        0x58ae0: 0xd2801f42, 0x58ae8: 0x94000000,
        0x58b54: 0x528036c2, 0x58b58: 0x52804821, 0x58b74: 0xd2840000,
        0x58b90: 0x52804065, 0x58b94: 0x52840004, 0x58bb8: 0xd2a00a03,
        # dynamic driver registration: lookup, indirect call, request/retry.
        0x5ba10: 0x94000000, 0x5ba34: 0xd63f0060,
        0x5ba54: 0x94000000, 0x5ba5c: 0x94000000,
    }
    for va, value in expected.items():
        require(word(data, va) == value, f'word {va:#x}')
    relocs = subprocess.check_output(['readelf', '-rW', str(MODULE)], text=True)
    for needle in (
        '0000000000057420', 'frc_pqe_sys_get_dimming_info',
        '0000000000057454', 'resolve_usb_symbols',
        '00000000000574d4', 'ssb_usb_register_driver',
        '0000000000059224', 'tcon_read_backup_data',
        '0000000000059214', 'tcon_restore_backup_data',
        '0000000000001e68', '00000000000591a8',
        '000000000000000c', '0000000000058048',
    ):
        require(needle in relocs, f'relocation/symbol text: {needle}')
    print('PASS hash-gated SSB init, PQE root, fops ioctl, and backup landmarks')

if __name__ == '__main__':
    main()
