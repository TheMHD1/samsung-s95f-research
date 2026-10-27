#!/usr/bin/env python3
"""Create a host-only flat ELF analysis view, with recovered export names.

This is not original vmlinux, a runnable image, or a firmware update. It uses
Image offsets as artificial VAs starting at zero, unknown symbol types/sizes,
and one mixed-permission section. Original permissions, internal symbols,
relocations, source lines and unwind metadata are not reconstructed.
"""
from pathlib import Path
import hashlib
import json
import struct

B = Path(__file__).resolve().parent
data = (B / 'kernel-Image.bin').read_bytes()
index = json.loads((B / 'kernel-export-index.json').read_text())
assert hashlib.sha256(data).hexdigest() == index['source_sha256']
memory_size = struct.unpack_from('<Q', data, 16)[0]
strings = bytearray(b'\0')
symbols = bytearray(24)
for row in index['exports']:
    name_offset = len(strings)
    strings.extend(row['name'].encode('ascii') + b'\0')
    value = int(row['target_image_offset'], 16)
    section = 1 if value < len(data) else 2
    symbols.extend(struct.pack('<IBBHQQ', name_offset, 0x10, 0, section, value, 0))

def align(number, boundary=8):
    return (number + boundary - 1) & -boundary

image_offset = 0x1000
str_offset = align(image_offset + len(data))
sym_offset = align(str_offset + len(strings))
shstr = b'\0.image\0.bss\0.strtab\0.symtab\0.shstrtab\0'
shstr_offset = sym_offset + len(symbols)
section_offset = align(shstr_offset + len(shstr))
output = bytearray(section_offset + 6 * 64)
ident = b'\x7fELF\x02\x01\x01' + bytes(9)
output[:64] = struct.pack('<16sHHIQQQIHHHHHH', ident, 2, 183, 1, 0, 64,
                         section_offset, 0, 64, 56, 1, 64, 6, 5)
output[64:120] = struct.pack('<IIQQQQQQ', 1, 7, image_offset, 0, 0,
                            len(data), memory_size, 0x1000)
output[image_offset:image_offset + len(data)] = data
output[str_offset:str_offset + len(strings)] = strings
output[sym_offset:sym_offset + len(symbols)] = symbols
output[shstr_offset:shstr_offset + len(shstr)] = shstr

def section(slot, name, kind, flags, address, offset, size, link=0, info=0,
            alignment=1, entry_size=0):
    name_index = shstr.index(name.encode() + b'\0')
    start = section_offset + slot * 64
    output[start:start + 64] = struct.pack('<IIQQQQIIQQ', name_index, kind,
        flags, address, offset, size, link, info, alignment, entry_size)

section(1, '.image', 1, 7, 0, image_offset, len(data), alignment=0x1000)
section(2, '.bss', 8, 3, len(data), image_offset + len(data),
        memory_size - len(data), alignment=8)
section(3, '.strtab', 3, 0, 0, str_offset, len(strings))
section(4, '.symtab', 2, 0, 0, sym_offset, len(symbols), 3, 1, 8, 24)
section(5, '.shstrtab', 3, 0, 0, shstr_offset, len(shstr))
destination = B / 'kernel-export-view.elf'
destination.write_bytes(output)
manifest = {
    'qualification': __doc__, 'input_sha256': index['source_sha256'],
    'output_sha256': hashlib.sha256(output).hexdigest(),
    'export_symbols': len(index['exports']), 'artificial_base': 0,
    'original_payload_preserved': output[image_offset:image_offset + len(data)] == data,
}
(B / 'kernel-export-view-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Built host-only analysis ELF with', len(index['exports']), 'export names')
