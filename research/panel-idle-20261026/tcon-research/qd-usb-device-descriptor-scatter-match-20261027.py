#!/usr/bin/env python3
"""Reconstruct the packaged USB device descriptor; compare retained metadata.

Offline only. No device, network, target process or firmware operation.
"""
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PROFILE = BASE / 'overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin'
METADATA = BASE / 'overnight/qd-usb-interface-metadata-20261027a/client.stdout'
DECODER = BASE / 'tcon-research/qd-rt-window-reset-output-reproduce.py'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    blob = PROFILE.read_bytes()
    need(len(blob) == 0x500000 and sha(blob) ==
         'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0',
         'profile identity')
    metadata = METADATA.read_bytes()
    need(sha(metadata) == '065113d8f9d133570a72a4c086e2fdbff26567c9f8c082612f794f7414430530',
         'retained metadata identity')
    need(sha(DECODER.read_bytes()) ==
         'fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02',
         'decoder implementation identity')
    spec = importlib.util.spec_from_file_location('pinned_scatter_decoder', DECODER)
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    known, end = decoder.unpack(blob, 0x5DA60, 0x4F8)
    need(end == 0x5DB5B and sha(known) ==
         '76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8',
         'decoder known answer')
    row6 = struct.unpack_from('<4I', blob, 0x3E3A0)
    need(row6 == (0x3E89C, 0x20261000, 0x4D4, 0x17C), 'scatter row6')
    ram, end = decoder.unpack(blob, row6[0] + 0x200, row6[2])
    need(end == 0x3EAC6 and sha(ram) ==
         'b7017446eabb7487bd28e612aa20df018b7b5442528664ca5990d3db80397fe0',
         'USB reset data')
    descriptor = ram[0x200:0x212]
    need(descriptor.hex() == '12010002ef020140e8040120500201020301',
         'packaged descriptor')
    reply = json.loads(metadata)
    need(reply['authenticated'] is True and reply['uid'] == reply['euid'] == 0,
         'retained authentication')
    command, = reply['commands']
    need(command['exit_code'] == 0 and command['timed_out'] is False and
         command['stderr'] == '', 'retained command result')
    raw = command['stdout'].split('CACHED_DESCRIPTORS\n', 1)[1].split('INTERFACE=', 1)[0]
    cached = bytes.fromhex(raw)
    need(len(cached) == 116 and cached[:18] == descriptor, 'device descriptor equality')
    need(int.from_bytes(cached[20:22], 'little') == 98, 'cached config total length')
    slices = {
        'descriptor_callback': (0x2A3EC, 0x2A3FC, 'a7de8503cc811287534f0c016d11def4be56b1e607c33ab88cefb52e0a6e8995'),
        'callback_table_accessor': (0xF978, 0xF980, '5b34918a5fd546620067062330446e2cec32d849f5da1d611c23a36666f0516b'),
        'usb_init': (0x24B0C, 0x24B62, 'e9ac54a051c27aafecff378362b097fc7b9c8fc67eb99ebb0ea986bc3b860062'),
    }
    for name, (start, stop, expected) in slices.items():
        need(sha(blob[start:stop]) == expected, 'code slice: ' + name)
    row0 = struct.unpack_from('<4I', blob, 0x3E340)
    need(row0 == (0x3E32C, 0x20000000, 0xF4C, 0x17C), 'scatter row0')
    context, end = decoder.unpack(blob, row0[0] + 0x200, row0[2])
    need(end == 0x3E961 and sha(context) ==
         '685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3',
         'main reset context')
    need(struct.unpack_from('<I', context, 0x500)[0] == 0x2A1ED,
         'descriptor callback Thumb pointer')
    need(struct.unpack_from('<I', blob, 0x2A3F8)[0] == 0x20261200,
         'descriptor callback source')
    print(json.dumps({
        'device_descriptor_18_bytes_equal': True,
        'device_descriptor_hex': descriptor.hex(),
        'cached_116_bytes_sha256': sha(cached),
        'reset_descriptor_ram': '0x20261200',
        'descriptor_callback_va': '0x2a1ec',
        'descriptor_callback_file': '0x2a3ec',
        'callback_table_ram': '0x20000500',
        'full_configuration_reconstruction_completed': False,
        'current_executable_equality_proved': False,
        'target_operations': 0,
    }, indent=2))


if __name__ == '__main__':
    main()
