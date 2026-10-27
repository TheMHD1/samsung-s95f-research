#!/usr/bin/env python3
"""Verify bounded ordinary-callback invocation facts; local retained bytes only."""
from pathlib import Path
import hashlib
import json
import struct

BASE = Path(__file__).resolve().parent.parent


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def word(image, address):
    return struct.unpack_from('<I', image, address)[0]


def bl(image, address):
    first, second = struct.unpack_from('<HH', image, address)
    need(first & 0xf800 == 0xf000 and second & 0xd000 == 0xd000, 'BL encoding')
    s = (first >> 10) & 1
    value = ((s << 24) | ((1 ^ ((second >> 13) & 1) ^ s) << 23) |
             ((1 ^ ((second >> 11) & 1) ^ s) << 22) |
             ((first & 0x3ff) << 12) | ((second & 0x7ff) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def main():
    package = (BASE / 'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    need(len(package) == 0x500000 and sha(package) ==
         'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0', 'package')
    image = package[0x200:0x40200]
    source_report = BASE / 'ap-exco-helper-inputs-20261027s/ap-exco-helper-inputs.md'
    need(sha(source_report.read_bytes()) ==
         '17068bd31de065a2720ca027498da41517e5d214e0dd633272ed144c29cabdb6',
         'corrected first-helper decision provenance')
    slices = {
        (0x38c24, 0x38c38): '287a309773f5f64fae4fac7d201097180674aa4480a6dd708fe5d84afc204df6',
        (0x1e7aa, 0x1e80a): '23033e4c06740f7c7278508278319719d1a8912e76579d01dabc7d948491e71c',
        (0x26988, 0x269a4): '042ab7f81cd64bbec5c43c7a05554c0bc11089b5db7c4e15093294b3f51c22ee',
        (0x13464, 0x1375a): 'ceb2219987046cb185913963cda6583abc9822e845ddbfdab30053f50c735d5f',
        (0x1b024, 0x1b03c): '91c14e2a69ee54b1a85f6ca9fba1b7004f0c9178c21cd2e2f363852488f9d02f',
        (0x2f840, 0x2f890): 'b8e1b07177ce89b890ba235e7ad43d01bada34fdd912d128fa5d9826bc2a03f9',
    }
    for (start, end), digest in slices.items():
        need(sha(image[start:end]) == digest, f'slice {start:#x}')
    need(word(image, 0x38c34) == word(image, 0x269a0) == 0x20000948, 'descriptor base')
    need(image[0x1e7aa:0x1e7ac] == bytes.fromhex('1c20') and
         bl(image, 0x1e7ac) == 0x38c24, 'lookup index 28')
    need(image[0x1e7f6:0x1e7fa] == bytes.fromhex('2c48a060') and
         word(image, 0x1e8a8) == 0x13465, 'callback registration')
    need(image[0x2698c:0x26990] == bytes.fromhex('d0f83802') and
         image[0x26994:0x2699e] == bytes.fromhex('d0f8381200f50c708847'), 'wrapper load/argument/call')
    descriptor = 0x20000948 + 28 * 20
    need(descriptor == 0x20000b78 and descriptor + 8 == 0x20000b80, 'descriptor arithmetic')
    need(word(image, 0x12c) == 0x26989 and 0x12c // 4 - 16 == 59, 'stored vector candidate')
    need(bl(image, 0x13710) == 0x2fb44 and bl(image, 0x2fb52) == 0x2f5d8, 'ordinary update chain')
    need(bl(image, 0x134e0) == bl(image, 0x13752) == 0x1b024 and
         word(image, 0x1b038) == 0xe000e280, 'pending-clear helper')
    need(image[0x134e4:0x134ee] == bytes.fromhex('0bb0bdec028bbde8f08f') and
         image[0x13758:0x1375a] == bytes.fromhex('c4e6'), 'return epilogue edge')
    # Counter is incremented while below 30; the mature decision precedes any
    # increment, so continuous qualification from zero first yields F0 at 31.
    count = 0
    outputs = []
    for _ in range(31):
        outputs.append(int(count >= 30))
        if count < 30:
            count += 1
    need(outputs == [0] * 30 + [1], 'bounded debounce arithmetic')
    print(json.dumps({
        'schema': 'ordinary-callback-invocation-v1', 'target_operations': 0,
        'package_sha256': sha(package), 'descriptor_index': 28,
        'descriptor_cpu_candidate': hex(descriptor), 'callback_field_cpu_candidate': hex(descriptor + 8),
        'callback_thumb_pointer': '0x13465', 'stored_vector_offset': '0x12c',
        'stored_vector_wrapper': '0x26989', 'external_irq_if_standard_vector_active': 59,
        'live_vector_base_or_callback_sampled': False, 'execution_proved': False,
        'cadence_seconds_or_frame_rate_proved': False,
        'continuous_true_calls_from_counter_zero_to_F0': 31,
        'helper_1b024_store_base': '0xe000e280',
        'helper_1b024_is_time_delay': False,
        'physical_cause_or_fix_proved': False,
    }, sort_keys=True))


if __name__ == '__main__':
    main()
