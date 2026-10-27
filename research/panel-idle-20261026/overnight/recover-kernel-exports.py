#!/usr/bin/env python3
"""Recover one verified PREL32 export-table run from the acquired ARM64 Image.

No TV access. This is not kallsyms or full ELF reconstruction. Every address
emitted is a raw Image file offset. Namespace-zero records only are supported.
"""
from pathlib import Path
import hashlib
import json
import re
import struct

BASE = Path(__file__).resolve().parent
data = (BASE / 'kernel-Image.bin').read_bytes()
image_size = struct.unpack_from('<Q', data, 16)[0]
expected = '77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d'
assert hashlib.sha256(data).hexdigest() == expected, 'Different kernel image'

def entry(pos):
    if pos < 0 or pos + 12 > len(data):
        return None
    value, name, namespace = struct.unpack_from('<iii', data, pos)
    target, name_pos = pos + value, pos + 4 + name
    if not (0 <= target < image_size and 0 <= name_pos < len(data)) or namespace:
        return None
    end = data.find(b'\0', name_pos, name_pos + 160)
    if end < 0:
        return None
    text = data[name_pos:end]
    if not re.fullmatch(rb'[A-Za-z_][A-Za-z_0-9.$]{0,159}', text):
        return None
    return {'entry_file_offset': hex(pos), 'target_image_offset': hex(target),
            'target_file_offset': hex(target) if target < len(data) else None,
            'name_file_offset': hex(name_pos), 'name': text.decode('ascii')}

seed_name = b'sdp_runtime_pm_tryuse\0'
seed_string = data.index(seed_name)
hits = []
for pos in range(4, len(data) - 8, 4):
    if pos + struct.unpack_from('<i', data, pos)[0] == seed_string:
        candidate = entry(pos - 4)
        if candidate and candidate['name'] == 'sdp_runtime_pm_tryuse':
            hits.append(pos - 4)
assert len(hits) == 1, 'Ambiguous export seed'
start = end = hits[0]
while entry(start - 12):
    start -= 12
while entry(end + 12):
    end += 12
rows = [entry(pos) for pos in range(start, end + 1, 12)]
assert start == 0x997ef0 and len(rows) > 4885
result = {'qualification': 'Reconstructed contiguous namespace-zero PREL32 export table around verified runtime-PM exports. Image offsets, not runtime VAs; BSS targets beyond saved payload have no file offset. Not full kallsyms or original ELF.',
          'source_sha256': expected, 'start': hex(start), 'end_inclusive': hex(end),
          'record_size': 12, 'exports': rows}
(BASE / 'kernel-export-index.json').write_text(json.dumps(result, indent=2) + '\n')
print(f'Recovered {len(rows)} export records from {start:#x} through {end:#x}')
