#!/usr/bin/env python3
"""Plan the retained target MSD metadata input only. No crypto, loader or TV I/O."""
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path('${S95F_EVIDENCE_ROOT}')
PREFIX = ROOT / 'panel-idle-20261026/overnight/samsung-official-T-RSMFAKUC-0090-msd-prefix.bin'
PREFIX_SHA256 = '01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d'
MEMBER_BYTES = 1493538434


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def parse(data):
    require(len(data) >= 26 and data[:6] == b'MSDU11', 'magic/minimum')
    count = struct.unpack_from('<I', data, 18)[0]
    require(count == 9 and 22 + count * 20 + 4 <= len(data), 'target section count')
    rows = []
    pos = 22
    for index in range(count):
        item, offset, size = struct.unpack_from('<IQQ', data, pos)
        pos += 20
        require(item == 1001 + index, 'target section identity')
        require(0 < size <= MEMBER_BYTES and offset <= MEMBER_BYTES - size, 'section range')
        rows.append({'id': item, 'offset': offset, 'size': size})
    require(all(a['offset'] + a['size'] == b['offset'] for a, b in zip(rows, rows[1:])), 'section adjacency')
    require(rows[-1]['offset'] + rows[-1]['size'] == MEMBER_BYTES, 'member length')
    headers = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    require(headers == 1 and pos + 13 <= len(data), 'target header count/descriptor bounds')
    offset, size, name_bytes = struct.unpack_from('<QIB', data, pos)
    pos += 13
    require(pos + name_bytes <= len(data), 'label bounds')
    label = data[pos:pos + name_bytes].decode('ascii')
    pos += name_bytes
    require(label == 'T-RSMFAKUC-0090', 'target label')
    require(offset == pos and offset == 234, 'descriptor/header adjacency')
    require(size == 4056 and offset + size <= len(data), 'complete target header')
    require(offset + size == rows[0]['offset'], 'header/payload adjacency')
    marker_start = offset + 8
    require(data[marker_start:marker_start + 8] == b'Salted__', 'salted marker')
    salt_start = marker_start + 8
    ciphertext_start = salt_start + 8
    ciphertext_end = offset + size
    ciphertext_size = ciphertext_end - ciphertext_start
    require(ciphertext_size > 0 and ciphertext_size % 16 == 0, 'ciphertext alignment')
    first_wrapper_word, expected_crc = struct.unpack_from('<II', data, offset)
    computed_crc = zlib.crc32(data[ciphertext_start:ciphertext_end]) & 0xffffffff
    require(computed_crc == expected_crc, 'encrypted metadata CRC32')
    return {
        'container': label,
        'sections': rows,
        'metadata_envelope': {'offset': offset, 'size': size, 'end_exclusive': offset + size},
        'wrapper': {'offset': offset, 'size': 8,
                    'first_word_semantics_not_yet_qualified': f'0x{first_wrapper_word:08x}',
                    'ciphertext_crc32_offset': offset + 4,
                    'ciphertext_crc32_expected': f'0x{expected_crc:08x}',
                    'ciphertext_crc32_computed': f'0x{computed_crc:08x}',
                    'ciphertext_crc32_matches': True},
        'salted_marker': {'offset': marker_start, 'size': 8},
        'salt': {'offset': salt_start, 'size': 8, 'value_omitted': True},
        'ciphertext': {'offset': ciphertext_start, 'size': ciphertext_size,
                       'end_exclusive': ciphertext_end, 'aes_blocks': ciphertext_size // 16,
                       'sha256': hashlib.sha256(data[ciphertext_start:ciphertext_end]).hexdigest()},
        'hypothetical_call_budget_after_execution_review': {'cmd0': 1, 'cmd1': 1, 'cmd2': 1, 'cmd3': 0},
        'normal_world_command_abi_statically_mapped': True,
        'operation_minimum_storage_bytes': 60,
        'target_execution_qualified': False,
        'target_calls_executed': 0,
        'decryption_attempted': False,
        'signature_verified': False,
        'ciphertext_crc_semantics_target_static_and_bytes_matched': True,
        'plaintext_crc_and_rsa_semantics_verified': False,
        'payload_names_salts_crcs_recovered': False,
    }


def self_test(data):
    cases = [('truncated_header', data[:4289]), ('bad_magic', b'X' + data[1:])]
    for name, offset, fmt, value in (
        ('wrong_count', 18, '<I', 10),
        ('section_gap', 46, '<Q', 1455427795),
        ('wrong_header_count', 202, '<I', 2),
        ('wrong_header_offset', 206, '<Q', 235),
        ('wrong_header_size', 214, '<I', 4055),
        ('wrong_label_length', 218, '<B', 255),
    ):
        altered = bytearray(data)
        struct.pack_into(fmt, altered, offset, value)
        cases.append((name, altered))
    altered = bytearray(data)
    altered[242] ^= 1
    cases.append(('bad_marker', altered))
    altered = bytearray(data)
    altered[258] ^= 1
    cases.append(('ciphertext_crc_mismatch', altered))
    rejected = []
    for name, variant in cases:
        try:
            parse(variant)
        except (ValueError, UnicodeDecodeError, struct.error):
            rejected.append(name)
        else:
            raise ValueError('accepted malformed input: ' + name)
    return rejected


def main():
    data = PREFIX.read_bytes()
    require(hashlib.sha256(data).hexdigest() == PREFIX_SHA256, 'retained source hash')
    result = parse(data)
    result.update({'source': str(PREFIX), 'prefix_sha256': PREFIX_SHA256,
                   'prefix_bytes': len(data), 'member_bytes_from_prior_zip_metadata': MEMBER_BYTES,
                   'rejected_mutations': self_test(data)})
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
