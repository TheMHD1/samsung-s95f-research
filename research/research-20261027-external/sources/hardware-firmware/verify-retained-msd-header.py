#!/usr/bin/env python3
"""Bounded local-only structural interpretation; no decryption or target I/O."""
import hashlib
import json
from pathlib import Path
import struct

BASE = Path('${S95F_EVIDENCE_ROOT}')
PREFIX = BASE / 'panel-idle-20261026/overnight/samsung-official-T-RSMFAKUC-0090-msd-prefix.bin'
EXPECTED_HASH = '01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d'
MEMBER_SIZE = 1493538434  # previously recorded ZIP central-directory member size

def require(condition, message):
    if not condition:
        raise ValueError(message)

def parse(data):
    require(len(data) >= 26 and data[:6] == b'MSDU11', 'magic/minimum length')
    raw_crc, unknown_or_size, count = struct.unpack_from('<IQI', data, 6)
    require(0 < count <= 64 and 22 + count * 20 + 4 <= len(data), 'section count/bounds')
    rows = []
    pos = 22
    for _ in range(count):
        item, offset, size = struct.unpack_from('<IQQ', data, pos)
        pos += 20
        require(size > 0 and offset <= MEMBER_SIZE and size <= MEMBER_SIZE - offset, 'section range')
        rows.append({'id': item, 'offset': offset, 'size': size, 'end': offset + size})
    nh, = struct.unpack_from('<I', data, pos)
    pos += 4
    require(0 < nh <= 16, 'encrypted header count')
    headers = []
    for _ in range(nh):
        require(pos + 13 <= len(data), 'descriptor bounds')
        offset, size, name_len = struct.unpack_from('<QIB', data, pos)
        pos += 13
        require(name_len > 0 and pos + name_len <= len(data), 'name bounds')
        name = data[pos:pos+name_len].decode('ascii')
        pos += name_len
        require(size >= 24 and offset + size <= len(data), 'complete header not retained')
        require(data[offset+8:offset+16] == b'Salted__', 'salt marker')
        headers.append({'name': name, 'offset': offset, 'size': size, 'end': offset + size,
                        'salted_marker_offset': offset + 8, 'complete_in_prefix': True})
    require(headers[0]['offset'] == pos, 'clear table/header adjacency')
    require(headers[-1]['end'] == rows[0]['offset'], 'header/payload adjacency')
    require(all(a['end'] == b['offset'] for a,b in zip(rows,rows[1:])), 'payload contiguity')
    require(rows[-1]['end'] == MEMBER_SIZE, 'member end')
    return {'raw_crc_word_unverified': hex(raw_crc), 'raw_u64_at_10_semantics_unverified': unknown_or_size,
            'section_count': count, 'sections': rows, 'encrypted_headers': headers,
            'clear_descriptor_end': pos, 'member_size_from_prior_metadata': MEMBER_SIZE,
            'signature_verified': False, 'payloads_decrypted': False,
            'names_salts_crcs_for_payloads_recovered': False}

def main():
    data = PREFIX.read_bytes()
    require(hashlib.sha256(data).hexdigest() == EXPECTED_HASH, 'retained prefix hash')
    result = parse(data)
    mutations = []
    variants = [('truncated', data[:219]), ('bad_magic', b'X'+data[1:])]
    altered = bytearray(data); struct.pack_into('<I', altered, 18, 0xffffffff)
    variants.append(('excess_count', altered))
    altered = bytearray(data); struct.pack_into('<Q', altered, 22+20+4, result['sections'][1]['offset']+1)
    variants.append(('payload_gap', altered))
    altered = bytearray(data); altered[242] ^= 1
    variants.append(('bad_header_salt_marker', altered))
    for name, variant in variants:
        try:
            parse(variant)
        except (ValueError, UnicodeDecodeError, struct.error):
            mutations.append(name)
        else:
            raise ValueError('mutation accepted: ' + name)
    result.update({'source': str(PREFIX), 'sha256': EXPECTED_HASH, 'prefix_bytes': len(data),
                   'rejected_mutations': mutations, 'target_operations': 0})
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
