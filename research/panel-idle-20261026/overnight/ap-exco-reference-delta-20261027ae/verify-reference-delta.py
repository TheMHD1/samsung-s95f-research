#!/usr/bin/env python3
"""Compare the retained W prefix with two pinned ordinary-object references."""
from pathlib import Path
import hashlib
import json
import struct

BASE = Path(__file__).resolve().parent.parent


def need(ok, message):
    if not ok:
        raise ValueError(message)


def load(relative, expected):
    raw = (BASE / relative).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, 'SHA-256 ' + relative)
    return raw


def u16(raw, offset):
    return struct.unpack_from('<H', raw, offset)[0]


def main():
    package = load('selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin',
                   'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0')
    backup = load('firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin',
                  'f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562')
    captured = load('ap-exco-input-snapshot-20261027w/capture-once/ordinary-ap-exco-prefix.bin',
                    '0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271')
    # Bind the already reviewed ordinary-object initializer provenance.
    load('ap-exco-helper-inputs-20261027s/ap-exco-helper-inputs.md',
         '17068bd31de065a2720ca027498da41517e5d214e0dd633272ed144c29cabdb6')
    initial = package[0x182200:0x18253a]
    need(initial == backup[0x182200:0x18253a] and
         hashlib.sha256(initial).hexdigest() ==
         'c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf', 'two reference payloads')
    need((len(initial), len(captured)) == (826, 824), 'object versus sampled prefix')
    stable_fields = [0xca,0xcc,0xce,0xd0,0xd2,0xd4,0xd6,0xd8,0xda,0xdc,0xde,
                     0xe0,0xe4,0xe8,0xea,0xec,0xee,0xf0,0xf2,0xf4,0xf6,0x116,
                     0x2cc,0x2ce,0x2fc,0x300,0x302]
    need(all(u16(initial, off) == u16(captured, off) for off in stable_fields), 'selected equal fields')
    changes = [{'offset':hex(off), 'reference_u16':u16(initial,off),
                'captured_u16':u16(captured,off)}
               for off in range(0,len(captured),2) if initial[off:off+2] != captured[off:off+2]]
    expected_offsets = [0x8,0x78,0xe2,0xe6,0xf8,0xfa,0xfc,0xfe,0x100,0x102,
                        0x104,0x106,0x108,0x10a,0x10c,0x10e,0x110,0x112,0x114,
                        0x126,0x128,0x12a,0x12c,0x12e,0x132,0x142,0x144,0x146,
                        0x148,0x14e,0x150,0x152,0x154,0x15c,0x17e,0x180,0x182,
                        0x2a6,0x2a8,0x2aa,0x2b2,0x2b6,0x2b8,0x2da,0x2de,0x2e2]
    need([int(row['offset'],16) for row in changes] == expected_offsets, 'exact differing halfwords')
    need((u16(initial,0xe2),u16(captured,0xe2),u16(initial,0xe6),u16(captured,0xe6)) ==
         (0,30,0,1), 'counter and output differences')
    thresholds = [struct.unpack_from('<I',captured,off)[0] for off in (0xd0,0xd4,0xd8,0xdc)]
    need(thresholds == [7464960,7464960,7464960,8128512], 'threshold values')
    print(json.dumps({
        'schema':'ap-exco-two-reference-prefix-delta-v1', 'target_operations':0,
        'reference_payload_bytes':826, 'captured_prefix_bytes':824,
        'reference_payloads_identical':True, 'halfwords_compared':412,
        'different_halfwords':len(changes), 'equal_halfwords':412-len(changes),
        'known_equal_offsets':[hex(off) for off in stable_fields],
        'captured_thresholds_equal_two_stored_references':thresholds,
        'differences':changes,
        'final_two_object_bytes_sampled':False,
        'references_proved_active_at_onset':False,
        'continuous_change_history_or_writer_proved':False,
        'captured_object_atomic':False, 'blackout_cause_or_fix_proved':False,
    },sort_keys=True))


if __name__ == '__main__':
    main()
