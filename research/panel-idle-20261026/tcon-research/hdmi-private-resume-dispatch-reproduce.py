#!/usr/bin/env python3
"""Reproduce the bounded static HDMI private-resume dispatch evidence.

Offline only.  This reads exact saved module/kernel bytes; it does not contact
or modify the television.  The checks are deliberately instruction/relocation
landmarks plus manual CFG review, not a live-registration assertion.
"""
from pathlib import Path
import argparse
import hashlib
import struct


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
HDMI = BASE / 'binaries/sdp_hdmi.ko'
IMAGE = BASE / 'overnight/kernel-Image.bin'
HDMI_SHA = 'f7cffd19934ef459b0263ceddddf003306b399e01d0ddee48df3f64a86667994'
IMAGE_SHA = '77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def pinned(path, digest):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'hash ' + str(path))
    return raw


class Elf64:
    """Small, read-only ELF64-LE reader for sections, symbols and RELA rows."""

    def __init__(self, raw):
        self.raw = raw
        require(raw[:6] == b'\x7fELF\x02\x01', 'ELF64 little-endian identity')
        require(struct.unpack_from('<H', raw, 18)[0] == 183, 'AArch64 ELF')
        shoff = struct.unpack_from('<Q', raw, 40)[0]
        shentsize, shnum, shstrndx = struct.unpack_from('<HHH', raw, 58)
        require(shentsize == 64 and shnum > 0 and shstrndx < shnum, 'section header table')
        raw_sections = [struct.unpack_from('<IIQQQQIIQQ', raw, shoff + i*64)
                        for i in range(shnum)]
        shstr = raw_sections[shstrndx]
        names = raw[shstr[4]:shstr[4]+shstr[5]]
        self.sections = []
        for i, row in enumerate(raw_sections):
            noff = row[0]
            end = names.find(b'\0', noff)
            require(end >= noff, 'section name termination')
            name = names[noff:end].decode()
            self.sections.append({
                'index': i, 'name': name, 'type': row[1], 'flags': row[2],
                'addr': row[3], 'offset': row[4], 'size': row[5],
                'link': row[6], 'info': row[7], 'align': row[8], 'entsize': row[9],
            })
        self.by_name = {}
        for section in self.sections:
            if section['name'] in self.by_name:
                require(section['name'] == '.note.GNU-stack',
                        'unexpected duplicate section ' + section['name'])
            else:
                self.by_name[section['name']] = section
        symtab = self.by_name['.symtab']
        require(symtab['entsize'] == 24 and symtab['size'] % 24 == 0, 'symbol table shape')
        strtab = self.sections[symtab['link']]
        strings = self.bytes(strtab['name'])
        self.symbols = []
        for at in range(symtab['offset'], symtab['offset'] + symtab['size'], 24):
            nameoff, info, other, shndx, value, size = struct.unpack_from('<IBBHQQ', raw, at)
            end = strings.find(b'\0', nameoff)
            require(end >= nameoff, 'symbol name termination')
            self.symbols.append({
                'name': strings[nameoff:end].decode(), 'info': info, 'other': other,
                'shndx': shndx, 'value': value, 'size': size,
            })

    def bytes(self, name):
        s = self.by_name[name]
        require(s['type'] != 8, 'attempted file read of NOBITS ' + name)
        out = self.raw[s['offset']:s['offset']+s['size']]
        require(len(out) == s['size'], 'section file bounds ' + name)
        return out

    def word(self, section, address):
        raw = self.bytes(section)
        require(address % 4 == 0 and address + 4 <= len(raw), 'instruction bounds')
        return struct.unpack_from('<I', raw, address)[0]

    def symbol(self, name, section, value, size):
        found = [s for s in self.symbols if s['name'] == name]
        require(len(found) == 1, 'symbol cardinality ' + name)
        s = found[0]
        actual = self.sections[s['shndx']]['name'] if s['shndx'] < len(self.sections) else None
        require((actual, s['value'], s['size']) == (section, value, size), 'symbol ' + name)

    def relocs(self, name):
        sec = self.by_name[name]
        require(sec['type'] == 4 and sec['entsize'] == 24 and sec['size'] % 24 == 0,
                'RELA shape ' + name)
        out = []
        for at in range(sec['offset'], sec['offset'] + sec['size'], 24):
            offset, info, addend = struct.unpack_from('<QQq', self.raw, at)
            sym = self.symbols[info >> 32]
            if sym['name']:
                target = sym['name']
            else:
                require(sym['shndx'] < len(self.sections), 'section symbol index')
                target = self.sections[sym['shndx']]['name']
            out.append((offset, info & 0xffffffff, target, addend))
        return out

    def relocation(self, section, offset, target, addend, rtype=None):
        rows = [r for r in self.relocs('.rela' + section) if r[0] == offset]
        require(len(rows) == 1, f'relocation cardinality {section}+{offset:x}')
        row = rows[0]
        require((row[2], row[3]) == (target, addend), f'relocation target {section}+{offset:x}')
        if rtype is not None:
            require(row[1] == rtype, f'relocation type {section}+{offset:x}')

    def all_relocations(self):
        for s in self.sections:
            if s['name'].startswith('.rela') and s['type'] == 4:
                for row in self.relocs(s['name']):
                    yield (s['name'],) + row


MODULE_WORDS = {
    ('.text.unlikely', 0x574): (0xaa0003f5, 'mov x21, x0'),
    ('.text.unlikely', 0x584): (0x910042b4, 'add x20, x21, #0x10'),
    ('.text.unlikely', 0x1784): (0xaa1403e0, 'mov x0, x20'),
    ('.text.unlikely', 0x1798): (0x94000000, 'bl hdmi_rpm_init'),
    ('.text.unlikely', 0x17a4): (0x94000000, 'bl hdmi_rpm_dev_init'),
    ('.text', 0xaa7b4): (0xaa0003e4, 'mov x4, x0'),
    ('.text', 0xaa7b8): (0xaa0103e3, 'mov x3, x1'),
    ('.text', 0xaa7c0): (0x910043e0, 'add x0, sp, #0x10'),
    ('.text', 0xaa7cc): (0xa9020fe4, 'stp x4, x3, [sp, #0x20]'),
    ('.text', 0xaa7d0): (0xf9001be2, 'str x2, [sp, #0x30]'),
    ('.text', 0xaa7d4): (0x94000000, 'bl sdp_runtime_pm_init_and_get'),
    ('.text', 0xaa7f0): (0x94000000, 'bl sdp_runtime_pm_getdev'),
    ('.text', 0xaa7fc): (0xf9000020, 'str x0, [x1]'),
    ('.text', 0x5140): (0xaa1303e0, 'mov x0, x19'),
    ('.text', 0x5144): (0x97ffff47, 'bl sdp_hdmi_pm_resume'),
    ('.text', 0x4f78): (0xd1004261, 'sub x1, x19, #0x10'),
    ('.text', 0x4f7c): (0xaa1603e0, 'mov x0, x22'),
    ('.text', 0x4f84): (0x94000000, 'bl sdp_hdmi_resume_fxn'),
    ('.text', 0x543c): (0xaa1303e1, 'mov x1, x19'),
    ('.text', 0x5440): (0xaa1603e0, 'mov x0, x22'),
    ('.text', 0x5444): (0x94000000, 'bl sdp_hdmi_resume_fxn'),
    ('.init.text', 0x10): (0x910fc000, 'add x0, x0, #0x3f0'),
    ('.init.text', 0x1c): (0x94000000, 'bl __platform_driver_register'),
}

IMAGE_WORDS = {
    0x3fbf58: (0xf9400a81, 'ldr x1, [x20, #0x10]'),
    0x3fbf5c: (0xf9001261, 'str x1, [x19, #0x20]'),
    0x3fbf68: (0xf9400e80, 'ldr x0, [x20, #0x18]'),
    0x3fbf6c: (0xf9001660, 'str x0, [x19, #0x28]'),
    0x3fbf78: (0xf9401283, 'ldr x3, [x20, #0x20]'),
    0x3fbf7c: (0xf9001a63, 'str x3, [x19, #0x30]'),
    0x3fbf80: (0xb9003e62, 'str w2, [x19, #0x3c]'),
    0x3fbf84: (0xb900467f, 'str wzr, [x19, #0x44]'),
    0x3fc104: (0xb9403ec0, 'ldr w0, [x22, #0x3c]'),
    0x3fc10c: (0x5400016d, 'b.le 0x3fc138'),
    0x3fc138: (0xf94012c1, 'ldr x1, [x22, #0x20]'),
    0x3fc140: (0xf9401ac1, 'ldr x1, [x22, #0x30]'),
    0x3fc148: (0x52800020, 'mov w0, #1'),
    0x3fc14c: (0xb90046c0, 'str w0, [x22, #0x44]'),
    0x3fc15c: (0xf94012c0, 'ldr x0, [x22, #0x20]'),
    0x3fc160: (0xf9401ac1, 'ldr x1, [x22, #0x30]'),
    0x3fc164: (0xd63f0020, 'blr x1'),
    0x3fc170: (0xb90046df, 'str wzr, [x22, #0x44]'),
    0x3fc384: (0xa94206c0, 'ldp x0, x1, [x22, #0x20]'),
    0x3fc388: (0xd63f0020, 'blr x1'),
}


def export(image, entry, target, name):
    value, text, namespace = struct.unpack_from('<iii', image, entry)
    require(entry + value == target and namespace == 0, 'kernel export target ' + name)
    start = entry + 4 + text
    require(image[start:start+len(name)+1] == name.encode() + b'\0', 'kernel export name ' + name)


def render_listing():
    lines = [
        '# Exact checked instruction landmarks',
        '# Module offsets are section-relative; Image offsets are file/image-relative.',
        '',
        '## sdp_hdmi.ko',
    ]
    for (section, at), (word, asm) in MODULE_WORDS.items():
        lines.append(f'{section}+0x{at:06x}  {word:08x}  {asm}')
    lines += ['', '## kernel Image']
    for at, (word, asm) in IMAGE_WORDS.items():
        lines.append(f'Image+0x{at:06x}  {word:08x}  {asm}')
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write-disassembly', action='store_true')
    args = ap.parse_args()
    module = Elf64(pinned(HDMI, HDMI_SHA))
    image = pinned(IMAGE, IMAGE_SHA)

    for identity in (
        ('sdp_hdmi_probe', '.text.unlikely', 0x53c, 4948),
        ('sdp_hdmi_pm_suspend', '.text', 0x46c8, 416),
        ('sdp_hdmi_pm_resume', '.text', 0x4e60, 700),
        ('sdp_hdmi_resume_ext', '.text', 0x5120, 132),
        ('sdp_hdmi_suspend_ext', '.text', 0x4868, 140),
        ('sdp_hdmi_resume', '.text', 0x5348, 492),
        ('sdp_hdmi_resume_fxn', '.text', 0x48f8, 1380),
        ('hdmi_rpm_init', '.text', 0xaa7b0, 48),
        ('hdmi_rpm_dev_init', '.text', 0xaa7e0, 36),
        ('sdp_hdmi_pm', '.rodata', 0x470, 184),
        ('sdp_hdmi_driver', '.data', 0x3f0, 192),
        ('rpm_dev', '.bss', 0x164c8, 8),
    ):
        module.symbol(*identity)

    for key, (word, _asm) in MODULE_WORDS.items():
        require(module.word(*key) == word, f'module instruction {key[0]}+{key[1]:x}')
    for at, (word, _asm) in IMAGE_WORDS.items():
        require(struct.unpack_from('<I', image, at)[0] == word, f'Image instruction {at:x}')

    # The dev_pm_ops-shaped table has only suspend/resume callback relocations.
    module.relocation('.rodata', 0x480, 'sdp_hdmi_pm_suspend', 0, 257)
    module.relocation('.rodata', 0x488, '.text', 0x4e60, 257)
    require(all(b == 0 for b in module.bytes('.rodata')[0x470:0x470+184]), 'pre-relocation PM table bytes')

    # The platform_driver actually registered by init_module has no relocation
    # to that PM table and no legacy suspend/resume callback at +0x18/+0x20.
    driver_rows = [(o, t, n, a) for o, t, n, a in module.relocs('.rela.data')
                   if 0x3f0 <= o < 0x3f0 + 192]
    require(driver_rows == [
        (0x3f0, 257, '.text.unlikely', 0x53c),
        (0x418, 257, '.rodata.str1.8', 0xa88),
        (0x428, 257, '__this_module', 0),
        (0x440, 257, '.rodata', 0x528),
    ], 'platform_driver relocation layout')
    require(module.bytes('.data')[0x408:0x418] == bytes(16), 'legacy suspend/resume slots')
    module.relocation('.init.text', 0x4, '.data', 0, 275)
    module.relocation('.init.text', 0x8, '.data', 0, 277)
    module.relocation('.init.text', 0x1c, '__platform_driver_register', 0, 283)

    # No static relocation in the exact module consumes sdp_hdmi_pm.  The one
    # static reference to legacy sdp_hdmi_resume is unwind metadata only.
    all_rows = list(module.all_relocations())
    pm_refs = [r for r in all_rows if r[3] == 'sdp_hdmi_pm' or
               (r[3] == '.rodata' and r[4] == 0x470)]
    require(pm_refs == [], 'unexpected static sdp_hdmi_pm consumer')
    legacy_refs = [(sec, off) for sec, off, _typ, target, addend in all_rows
                   if ((target == '.text' and addend == 0x5348) or
                       (target == 'sdp_hdmi_resume' and addend == 0))]
    require(legacy_refs == [('.rela.eh_frame', 0xac4)], 'legacy resume references')
    export_names = {r[2] for r in module.relocs('.rela__ksymtab')}
    require('sdp_hdmi_pm' not in export_names and 'sdp_hdmi_resume' not in export_names,
            'unexpected exported table/legacy resume')

    # Relocations do not describe fixed same-section B/BL instructions. Scan
    # every aligned word in every executable PROGBITS section, while treating
    # only a branch originating in .text as capable of naming .text+0x5348.
    branch_hits = []
    executable_words = 0
    for section in module.sections:
        if section['type'] != 1 or not (section['flags'] & 0x4):
            continue
        raw = module.bytes(section['name'])
        require(len(raw) % 4 == 0, 'fixed-width executable section ' + section['name'])
        executable_words += len(raw) // 4
        for at in range(0, len(raw), 4):
            word = struct.unpack_from('<I', raw, at)[0]
            if word & 0x7c000000 != 0x14000000:  # AArch64 B or BL immediate
                continue
            imm26 = word & 0x03ffffff
            if imm26 & 0x02000000:
                imm26 -= 1 << 26
            target = at + (imm26 << 2)
            if section['name'] == '.text' and target == 0x5348:
                branch_hits.append((section['name'], at, word))
    require(executable_words == 187259, 'executable fixed-word census changed')
    require(branch_hits == [], 'direct fixed B/BL to legacy resume body')

    # Positive proprietary registration path in probe and its saved record.
    for sec, off, target, addend, typ in (
        ('.text.unlikely', 0x1788, '.text', 0x5120, 275),
        ('.text.unlikely', 0x178c, '.text', 0x4868, 275),
        ('.text.unlikely', 0x1790, '.text', 0x5120, 277),
        ('.text.unlikely', 0x1794, '.text', 0x4868, 277),
        ('.text.unlikely', 0x1798, 'hdmi_rpm_init', 0, 283),
        ('.text.unlikely', 0x17a4, 'hdmi_rpm_dev_init', 0, 283),
        ('.text', 0xaa7c4, '.rodata.str1.8', 0x4bad0, 275),
        ('.text', 0xaa7c8, '.rodata.str1.8', 0x4bad0, 277),
        ('.text', 0xaa7d4, 'sdp_runtime_pm_init_and_get', 0, 283),
        ('.text', 0xaa7e4, '.rodata.str1.8', 0x4bad0, 275),
        ('.text', 0xaa7e8, '.rodata.str1.8', 0x4bad0, 277),
        ('.text', 0xaa7f0, 'sdp_runtime_pm_getdev', 0, 283),
        ('.text', 0xaa7f4, '.bss', 0x164c8, 275),
        ('.text', 0xaa7fc, '.bss', 0x164c8, 286),
        ('.text', 0x4f84, 'sdp_hdmi_resume_fxn', 0, 283),
        ('.text', 0x5444, 'sdp_hdmi_resume_fxn', 0, 283),
    ):
        module.relocation(sec, off, target, addend, typ)
    strings = module.bytes('.rodata.str1.8')
    require(strings[0x4bad0:].split(b'\0', 1)[0] == b'sdp-hdmi', 'private record name')

    # Directly authenticate the three relevant exported kernel entry points.
    export(image, 0x9a3a34, 0x3fc040, 'sdp_runtime_pm_get')
    export(image, 0x9a3a4c, 0x3fbf10, 'sdp_runtime_pm_init_and_get')
    export(image, 0x9a3a64, 0x3fc1c0, 'sdp_runtime_pm_put')

    listing = render_listing()
    out = HERE / 'hdmi-private-resume-dispatch.disasm'
    if args.write_disassembly:
        with out.open('x') as handle:
            handle.write(listing)
    else:
        require(out.read_text() == listing, 'saved listing equality')

    print('PASS: exact module/Image private HDMI resume registration and callback landmarks.')
    print('No relocation-backed standard-PM attachment or legacy-resume consumer was found in this exact ELF.')
    print('Static/manual CFG only: live registration, invocation, runtime patch state and incident timing remain unobserved.')


if __name__ == '__main__':
    main()
