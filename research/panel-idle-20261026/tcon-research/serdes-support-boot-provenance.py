#!/usr/bin/env python3
"""Offline exact-binary checks for the board-identity gate's boot input.

No device action. Output is conditional static evaluation, not a live cache read.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import importlib.util
import json
import math
import re
import struct

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
B = BASE/'overnight'
IMAGE_SHA = '77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d'
SUPPORT_SHA = 'fbe4eaad57c66865e2cc50b575a878a690c06303905e666e75b9f08d139dd1f0'
PINS = {
    'client-result.json': '116a7f75683ee9a267defd608211979119a80969deb7cceaabd8c7a2d11117b5',
    'client-stderr.txt': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'client-stdout.json': '279ed400c67d30707b0bca39dec3f616df72163cb202787a4915a91dd60e4bd9',
    'intent.json': '4883c1f267cf8f9a27ce272bcbfdfe42ba3d9a8d3f521d2c9fc4dd88db3e13d7',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pinned(path, digest):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'hash '+str(path))
    return raw


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write-disassembly', action='store_true')
    args = ap.parse_args()
    reader = HERE/'sdp-hdmi-cell-gate-reproduce.py'
    pinned(reader, '8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67')
    spec = importlib.util.spec_from_file_location('exact_support_reader', reader)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.SOURCES['support'] = (B/'serdes-support-copy-20261026/system_drv.ko', SUPPORT_SHA)
    src = m.Source('support')
    spans = []
    rows = {}
    for name, off, size in (
        ('system_drv_probe', 0x858, 620),
        ('tztv_sys_is_oc_support', 0xdc0, 40),
        ('tztv_sys_get_formfactor_info', 0xdf8, 64),
    ):
        src.symbol(name, '.text', off, size)
        listing = src.listing('.text', off, off+size)
        spans.append(('system_drv '+name, listing))
        rows.update(listing)
    for at, mn, op in (
        (0xdcc, 'ldrb', 'w2, [x1, #3]'), (0xdd0, 'tst', 'w2, #0xf0'),
        (0xdd4, 'b.ne', '#0xde4'), (0xdd8, 'ldrb', 'w0, [x1, #1]'),
        (0xddc, 'cmp', 'w0, #4'), (0xde0, 'cset', 'w0, eq'),
        (0xe04, 'mov', 'w1, w0'), (0xe18, 'str', 'w1, [x0]'),
    ):
        require(rows.get(at) == (mn, op), f'module landmark {at:x}')
    for at, target, addend in (
        (0x918, 'tztv_sys_get_formfactor_info', 0),
        (0xe00, 'get_formfactor_info', 0),
        (0xe0c, '.bss', 0xa8), (0xe18, '.bss', 0xa8),
        (0xdc0, '.bss', 0xa8), (0xdc4, '.bss', 0xa8),
    ):
        src.relocation('.text', at, target, addend)
    src.symbol('ffinfo', '.bss', 0xa8, 4)

    image = pinned(B/'kernel-Image.bin', IMAGE_SHA)
    # Decode these two export records directly; do not depend on the old
    # assert-based export-index generator or its names as an authority.
    for entry, off, name in ((0x99e64c, 0x4c2490, b'get_formfactor_info'),
                             (0x9a03a4, 0x30f708, b'kstrtouint')):
        value, text, ns = struct.unpack_from('<iii', image, entry)
        require(ns == 0 and entry+value == off, 'PREL32 target')
        start = entry+4+text
        require(image[start:start+len(name)+1] == name+b'\0', 'PREL32 name')
    md = m.Cs(m.CS_ARCH_ARM64, m.CS_MODE_ARM)
    kernel_rows = {}
    for name, lo, hi in (
        ('kernel get_formfactor_info', 0x4c2490, 0x4c249c),
        ('kernel ffinfo setup-handler body', 0xa233a4, 0xa233e4),
    ):
        ins = list(md.disasm(image[lo:hi], lo))
        require(sum(i.size for i in ins) == hi-lo, 'kernel decode coverage')
        listing = {i.address: (i.mnemonic, i.op_str) for i in ins}
        spans.append((name, listing))
        kernel_rows.update(listing)
    for at, mn, op in (
        (0x4c2490, 'adrp', 'x0, #0xc31000'),
        (0x4c2494, 'ldr', 'w0, [x0, #0x714]'),
        (0x4c2498, 'ret', ''),
        (0xa233a4, 'cbz', 'x0, #0xa233dc'),
        (0xa233a8, 'ldrb', 'w1, [x0]'),
        (0xa233ac, 'cbz', 'w1, #0xa233dc'),
        (0xa233b4, 'adrp', 'x2, #0xc31000'),
        (0xa233b8, 'add', 'x2, x2, #0x710'),
        (0xa233c0, 'add', 'x2, x2, #4'),
        (0xa233c4, 'mov', 'w1, #0x10'),
        (0xa233c8, 'bl', '#0x30f708'),
        (0xa233cc, 'cmp', 'w0, #0'),
        (0xa233d0, 'cset', 'w0, eq'),
        (0xa233dc, 'mov', 'w0, #0'),
    ):
        require(kernel_rows.get(at) == (mn, op), f'kernel landmark {at:x}')
    nominal_base = 0xffffffc010080000
    require(image[0xa6751e:0xa67526] == b'ffinfo=\0', 'boot parameter literal')
    require(struct.unpack_from('<QQQ', image, 0xa6deb0) ==
            (nominal_base+0xa6751e, nominal_base+0xa233a4, 0), 'setup-shaped tuple')
    # c31714 is BSS outside the saved payload. Do not read file bytes there.
    declared_size = struct.unpack_from('<Q', image, 16)[0]
    require(len(image) < 0xc31714 and 0xc31718 <= declared_size, 'BSS range')

    capture = B/'formfactor-boot-metadata-20261026'
    raw = {n: pinned(capture/n, sha) for n, sha in PINS.items()}
    intent = json.loads(raw['intent.json'])
    host = json.loads(raw['client-result.json'])
    require(host['returncode'] == 0 and host['host_timeout'] is False, 'host result')
    require(raw['client-stderr.txt'] == b'', 'host stderr')
    result = json.loads(raw['client-stdout.json'])
    require(result['authenticated'] is True and result['uid'] == result['euid'] == 0,
            'root authentication')
    require(result['host'] == '198.51.100.20' and result['model'] == 'QN77S95FAFXZC', 'target')
    require(result['root_persistence'] == 'host-assisted' and
            result['global_system_files_unchanged_at_acquisition'] is True, 'access provenance')
    require(len(result['commands']) == 1, 'command cardinality')
    cmd = result['commands'][0]
    require(cmd['command'] == intent['command'] and
            hashlib.sha256(cmd['command'].encode()).hexdigest() == intent['command_sha256'], 'intent binding')
    require(cmd['exit_code'] == 0 and cmd['timed_out'] is False and cmd['stderr'] == '', 'remote result')
    num = r'(\d+\.\d+)'
    frame = re.fullmatch(
        r'@@ BOOT_START\n([0-9a-f-]{36})\n@@ TIME_START\n(\d+)\n'+num+' '+num+
        r'\n@@ KERNEL_RELEASE\n5\.4\.261\n@@ SYSTEM_MODULE_HASH\n'+SUPPORT_SHA+
        r'  /lib/modules/5\.4\.261/kernel/system_drv\.ko\n@@ CMDLINE_BASE64\n'
        r'([A-Za-z0-9+/=\n]+)@@ BOOT_END\n([0-9a-f-]{36})\n@@ TIME_END\n(\d+)\n'+num+' '+num+r'\n',
        cmd['stdout'])
    require(frame is not None, 'whole stdout framing')
    boot, epoch0, up0, idle0, payload, endboot, epoch1, up1, idle1 = frame.groups()
    require(boot == endboot == '00000000-0000-4000-8000-000000000000', 'boot identity')
    require(0 <= int(epoch1)-int(epoch0) <= 2 and
            all(math.isfinite(float(x)) for x in (up0, up1, idle0, idle1)) and
            0 <= float(up1)-float(up0) <= 2, 'finite monotonic capture bounds')
    compact = payload.replace('\n', '')
    line = base64.b64decode(compact, validate=True)
    require(base64.b64encode(line).decode() == compact and 0 < len(line) <= 8192,
            'canonical bounded base64')
    require(line.endswith(b'\n') and line.count(b'\n') == 1 and b'\0' not in line, 'cmdline shape')
    values = [x[7:] for x in line.split() if x.startswith(b'ffinfo=')]
    require(len(values) == 1 and re.fullmatch(rb'[0-9a-fA-F]{1,8}', values[0]) is not None, 'unique hex ffinfo')
    value = int(values[0], 16)
    octets = value.to_bytes(4, 'little')
    conditional = int((octets[3] & 0xf0) == 0 and octets[1] == 4)
    require(value == 0x401 and conditional == 1, 'expected conditional board-gate value')
    output = ''.join('\n## '+name+'\n'+''.join(f'{a:08x}  {mn:8} {op}\n'
                    for a, (mn, op) in listing.items()) for name, listing in spans)
    outpath = HERE/'serdes-support-boot-provenance.disasm'
    if args.write_disassembly:
        with outpath.open('x') as out:
            out.write(output)
    else:
        require(outpath.read_text() == output, 'saved disassembly equality')
    print(f'PASS: exact module/kernel boot-input path; captured ffinfo={value:08x}, conditional support={conditional}.')
    print(f'Capture boot={boot}, uptime={up0}..{up1}, physical=unobserved.')
    print('Not a live ffinfo/cache/binding read; no incident, hardware state, cause, recovery or prevention established.')


if __name__ == '__main__':
    main()
