#!/usr/bin/env python3
"""Hash-gated instruction landmarks, not full CFG or live delivery proof."""
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, '/tmp/tcon-capstone')
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile

BASE = Path(__file__).resolve().parents[1]
EXPECTED = {
    'data-provider-master': 'ce0b2c76f625d66b6967a05e9c743c294661c0f7964227629289e1495fcb7337',
    'libnotification.so.0': '16d1aaa56fde2506e80291d7aa39f73db2e4d3b446339fbd439a3d1f23ce7f91',
    'libnotification-ex.so.1': '948df9c8be3045111a40851d4c8e44824a78522bcbeb40d3b963b8fc13a6d8c7',
    'tv-viewer': 'd32fbb420d26a27845cbb23ab216de23706c6aeb6376e4107849f74ec5a1883f',
}


def instructions(name, start, length):
    with (BASE / 'binaries' / name).open('rb') as handle:
        elf = ELFFile(handle)
        assert elf.elfclass == 32 and elf['e_machine'] == 'EM_ARM'
        text = elf.get_section_by_name('.text')
        offset = start - text['sh_addr']
        assert 0 <= offset and offset + length <= text['sh_size']
        code = text.data()[offset:offset + length]
    return {ins.address: (ins.mnemonic, ins.op_str)
            for ins in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, start)}


def main():
    for name, digest in EXPECTED.items():
        assert hashlib.sha256((BASE / 'binaries' / name).read_bytes()).hexdigest() == digest, name
    provider = instructions('data-provider-master', 0x143f8, 52)
    assert provider[0x143fa] == ('cmp', 'r3, #0')
    assert provider[0x143fc] == ('ble', '#0x14468')
    assert provider[0x14404] == ('movs', 'r1, #1')
    assert provider[0x14408] == ('blx', '#0xa05c')
    assert provider[0x14424] == ('bl', '#0x1a688')
    client = instructions('libnotification.so.0', 0x46c5cfa8, 20)
    assert client[0x46c5cfb4] == ('movs', 'r1, #1')
    assert client[0x46c5cfb6] == ('bl', '#0x46c5ec8c')
    callback = instructions('libnotification.so.0', 0x46c5ecfe, 12)
    assert callback[0x46c5ed00] == ('mov', 'r3, r7')
    assert callback[0x46c5ed06] == ('blx', 'r8')
    for name in ('data-provider-master', 'libnotification.so.0'):
        assert b'delete_single_notify\0' in (BASE / 'binaries' / name).read_bytes()
    print('PASS: source hashes and legacy event-1 landmarks; full route/identity/CFG require manual report review; no live action')


if __name__ == '__main__':
    main()
