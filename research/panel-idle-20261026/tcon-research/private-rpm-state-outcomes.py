#!/usr/bin/env python3
"""Offline exact-build check of private PM state/return handling; no TV access."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import struct

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
READER = HERE/'hdmi-private-resume-dispatch-reproduce.py'
READER_SHA = 'b4430d1b2b3a2ff1bcb34318f75db513ed7557546a2cbf07b03c9db466d01411'
IMAGE_SHA = '77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d'
HDMI_SHA = 'f7cffd19934ef459b0263ceddddf003306b399e01d0ddee48df3f64a86667994'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pinned(path, digest):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'source hash '+str(path))
    return raw


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write-disassembly', action='store_true')
    args = ap.parse_args()
    pinned(READER, READER_SHA)
    spec = importlib.util.spec_from_file_location('private_rpm_elf_reader', READER)
    require(spec is not None and spec.loader is not None, 'reader loader')
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    image = pinned(BASE/'overnight/kernel-Image.bin', IMAGE_SHA)
    module = reader.Elf64(pinned(BASE/'binaries/sdp_hdmi.ko', HDMI_SHA))
    require(struct.unpack_from('<Q', image, 16)[0] == 0xd99000,
            'declared kernel memory extent')
    require(len(image) < 0xc249c8 < 0xd99000,
            'private bypass byte has no saved file payload')
    for entry, target, name in (
        (0x9a3a1c, 0x3fbbd0, 'sdp_runtime_pm_disable'),
        (0x9a3a40, 0x3fbee8, 'sdp_runtime_pm_getdev'),
        (0x9a3a34, 0x3fc040, 'sdp_runtime_pm_get'),
        (0x9a3a64, 0x3fc1c0, 'sdp_runtime_pm_put'),
        (0x9a3a4c, 0x3fbf10, 'sdp_runtime_pm_init_and_get'),
    ):
        reader.export(image, entry, target, name)

    # Full bodies are retained below for manual CFG review. These landmarks
    # check the decisive branch/store/call identities, not runtime execution.
    words = {
        0x3fbbd0: 0xb0004141, 0x3fbbd4: 0x52800022,
        0x3fbbd8: 0x52800000, 0x3fbbdc: 0x39272022,
        0x3fbbe0: 0xd65f03c0,
        0x3fbe5c: 0x91004260, 0x3fbe60: 0xd28001e2,
        0x3fbe64: 0x940eea48, 0x3fbe68: 0x35ffff20,
        0x3fbe90: 0x5281b801, 0x3fbe98: 0x97f5ec3e,
        0x3fbe9c: 0xaa0003f3, 0x3fbea0: 0xb4fffe60,
        0x3fbea8: 0x91004000, 0x3fbeac: 0xd28001e2,
        0x3fbeb0: 0x940f1cee, 0x3fbec0: 0xf90016d3,
        0x3fbec4: 0xf9000433, 0x3fbec8: 0xa9000261,
        0x3fbee8: 0xb0004141, 0x3fbeec: 0x39672021,
        0x3fbef0: 0x350000c1, 0x3fbefc: 0x97ffffc5,
        0x3fbf08: 0xd2800000,
        0x3fc104: 0xb9403ec0, 0x3fc108: 0x7100001f,
        0x3fc10c: 0x5400016d, 0x3fc110: 0x11000400,
        0x3fc114: 0xb9003ec0, 0x3fc128: 0x52800000,
        0x3fc138: 0xf94012c1, 0x3fc13c: 0xb4fffea1,
        0x3fc140: 0xf9401ac1, 0x3fc144: 0xb4fffe61,
        0x3fc148: 0x52800020, 0x3fc14c: 0xb90046c0,
        0x3fc15c: 0xf94012c0, 0x3fc160: 0xf9401ac1,
        0x3fc164: 0xd63f0020, 0x3fc168: 0xaa1503e0,
        0x3fc16c: 0x940fa3ef, 0x3fc170: 0xb90046df,
        0x3fc180: 0x91154000, 0x3fc184: 0x940f46b1,
        0x3fc188: 0xb9403ec0, 0x3fc18c: 0x17ffffe1,
        0x3fc190: 0x52800000,
        0x3fc278: 0xb9403ec0, 0x3fc27c: 0x71000400,
        0x3fc280: 0xb9003ec0, 0x3fc284: 0x54000204,
        0x3fc288: 0x540000a1, 0x3fc28c: 0xf94012c0,
        0x3fc290: 0xb4000060, 0x3fc294: 0xf94016c0,
        0x3fc298: 0xb5000260, 0x3fc2ac: 0x52800000,
        0x3fc2c4: 0xf94016c0, 0x3fc2c8: 0xb5000840,
        0x3fc2cc: 0xb9003edf, 0x3fc2e8: 0x52800041,
        0x3fc2f0: 0xb90046c1, 0x3fc308: 0xb94042c0,
        0x3fc310: 0x540003ad, 0x3fc37c: 0x91186000,
        0x3fc380: 0x940f4632, 0x3fc384: 0xa94206c0,
        0x3fc388: 0xd63f0020, 0x3fc38c: 0xaa1503e0,
        0x3fc390: 0x940fa366, 0x3fc398: 0x52800060,
        0x3fc39c: 0xb90046c0, 0x3fc3a8: 0x9117c000,
        0x3fc3ac: 0x940f4627, 0x3fc3b4: 0x17ffffba,
    }
    for at, expected in words.items():
        require(struct.unpack_from('<I', image, at)[0] == expected,
                f'Image instruction {at:x}')
    strings = {
        0x8fe550: b'\x016[sdp_runtime_pm] %s resumed.\n\0',
        0x8fe5f0: b'\x016[sdp_runtime_pm] %s suspended.\n\0',
        0x8fe618: b'\x013[sdp_runtime_pm] %s suspend timeout. device is still busy.\n\0',
    }
    for at, expected in strings.items():
        require(image[at:at+len(expected)] == expected, f'Image literal {at:x}')
    for name, value, size in (
        ('sdp_hdmi_pm_resume', 0x4e60, 700),
        ('sdp_hdmi_resume_ext', 0x5120, 132),
        ('sdp_hdmi_resume_fxn', 0x48f8, 1380),
    ):
        module.symbol(name, '.text', value, size)
    for at, expected in {
        0x4ea0: 0xf9403c16, 0x4ea8: 0x52800015,
        0x4eac: 0xf9400ec0, 0x4eb0: 0xf9400000,
        0x4eb4: 0x9140a000, 0x4eb8: 0xb95f4000,
        0x4ebc: 0x71000c1f, 0x4ec0: 0x540004e0,
        0x4ec4: 0x2a1503e0, 0x4ed8: 0xd65f03c0,
        0x4f84: 0x94000000, 0x4f8c: 0x2a0003f5,
        0x50c4: 0x17ffff80,
        0x5144: 0x97ffff47, 0x5150: 0xd65f03c0,
        0x4944: 0x910243e0, 0x494c: 0x94000000,
        0x50ac: 0x91000042, 0x50b0: 0xd2801001,
        0x50b4: 0x910103e0, 0x50b8: 0x94000000,
        0x50bc: 0x910103e0, 0x50c0: 0x94000000,
    }.items():
        require(module.word('.text', at) == expected, f'HDMI instruction {at:x}')
    module.relocation('.text', 0x4f84, 'sdp_hdmi_resume_fxn', 0, 283)
    for at, target, addend, kind in (
        (0x48f8, '.rodata.str1.8', 0x2910, 275),
        (0x48fc, '.rodata.str1.8', 0x2910, 277),
        (0x494c, 'trace_early_message', 0, 283),
        (0x50a4, '.rodata.str1.8', 0x2b60, 275),
        (0x50ac, '.rodata.str1.8', 0x2b60, 277),
        (0x50b8, 'snprintf', 0, 283),
        (0x50c0, 'trace_early_message', 0, 283),
    ):
        module.relocation('.text', at, target, addend, kind)
    module_strings = {
        0x2910: b'[HDMIRX] resuming ...\n\0',
        0x2b60: b'@PM Resume_time [sdp_hdmi_pm_resume] /HDMIRX_MODULE/%d/msec\n\0',
    }
    for at, expected in module_strings.items():
        require(module.bytes('.rodata.str1.8')[at:at+len(expected)] == expected,
                f'HDMI trace literal {at:x}')

    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    lines = ['# Exact-build private PM return/state excerpts',
             '# Image offsets are saved file offsets, never live addresses.',
             '# Module offsets are section-relative. Full bodies require CFG review.', '']
    for label, raw, start, end in (
        ('Image disable', image, 0x3fbbd0, 0x3fbbe4),
        ('Image named lookup/create helper', image, 0x3fbe10, 0x3fbee4),
        ('Image getdev', image, 0x3fbee8, 0x3fbf10),
        ('Image private get', image, 0x3fc040, 0x3fc1c0),
        ('Image private put', image, 0x3fc1c0, 0x3fc3e8),
        ('HDMI .text pm_resume', module.bytes('.text'), 0x4e60, 0x511c),
        ('HDMI .text resume_ext', module.bytes('.text'), 0x5120, 0x51a4),
        ('HDMI .text resume_fxn entry', module.bytes('.text'), 0x48f8, 0x4950),
    ):
        rows = list(md.disasm(raw[start:end], start))
        require(len(rows)*4 == end-start, 'complete fixed-word excerpt '+label)
        lines.extend(['## '+label])
        for ins in rows:
            lines.append(f'{ins.address:08x}  {ins.bytes.hex()}  {ins.mnemonic} {ins.op_str}')
        lines.append('')
    for at, literal in strings.items():
        lines.append(f'Image+0x{at:x} {literal!r}')
    for at, literal in module_strings.items():
        lines.append(f'HDMI .rodata.str1.8+0x{at:x} {literal!r}')
    listing = '\n'.join(lines)+'\n'
    output = HERE/'private-rpm-state-outcomes.disasm'
    if args.write_disassembly:
        require(not output.exists(), 'refuse to overwrite saved listing')
        output.write_text(listing)
    else:
        require(output.read_text() == listing, 'saved disassembly changed')
    print('PASS: private get/put state, ignored returns, disable and allocating getdev; static only')


if __name__ == '__main__':
    main()
