#!/usr/bin/env python3
"""Reproduce the bounded cross-time AK/W numeric comparison offline."""
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent

def need(ok, why):
    if not ok:
        raise ValueError(why)

def load(path, expected):
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, 'pin ' + str(path))
    return raw

def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]

def quotient(a, b, divisor, cap):
    need(1 <= divisor <= 65535, 'positive divisor domain only')
    product = f32(f32(float(a)) * f32(float(b)))
    rounded = int(f32(f32(product / f32(float(divisor))) + f32(0.5)))
    need(0 <= rounded <= 0xffffffff, 'in-range conversion only')
    return rounded, min(rounded & 0xffff, cap)

def main():
    npc = load(HERE/'capture-once/npc-ap-offset-14-through-1b.bin',
        '703e6dd703874a61cf296a379be701c53e5db31d7b51e5e1c868504fb380a86d')
    ordinary = load(HERE/'capture-ordinary-after/ordinary-ap-exco-prefix.bin',
        '0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271')
    derived = load(HERE/'capture-ordinary-after/derived-ap-exco.bin',
        'de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0')
    old = HERE.parent/'ap-exco-input-snapshot-20261027w/capture-once'
    need(ordinary == (old/'ordinary-ap-exco-prefix.bin').read_bytes(), 'original W prefix equality')
    need(derived == (old/'derived-ap-exco.bin').read_bytes(), 'original W derived equality')
    nr = json.loads(load(HERE/'capture-once/record.json',
        '9315749c956fbdaaaed84ac6092b13fded842182579e79f43bb170796341264a'))
    ar = json.loads(load(HERE/'capture-ordinary-after/record.json',
        '28a14ab86d85a30f77f78628c39646bbf9b1bc21c20522c3b4d0b1947efa8423'))
    for record, operations, calls in ((nr,1,19),(ar,3,20)):
        need(record['native_invocations'] == 1 and record['target_operations'] == operations,
             'accepted operation accounting')
        need(record['target_operations_status'] == 'accepted_exact' and
             not record['cleanup_required'] and record['cleanup_stdout'] == 'STAGE_ABSENT\n',
             'cleanup/accounting')
        need(len(record['calls']) == calls, 'retained call count')
        need(record['terminal']['boot_id'] == '00000000-0000-4000-8000-000000000000',
             'boot pin')
    # Terminal uptimes are retained decimal centiseconds, avoiding a float gap.
    def centiseconds(record):
        text = record['terminal']['uptime'].split()[0]
        whole, fraction = text.split('.')
        need(len(fraction) == 2, 'centisecond terminal format')
        return int(whole)*100 + int(fraction)
    gap = centiseconds(ar)-centiseconds(nr)
    need(gap == 17657, 'sequential terminal separation')
    need(len(npc) == 8 and len(ordinary) == 824 and len(derived) == 1004, 'extents')
    values = struct.unpack('<4H', npc)
    need(values == (100,118,118,118), 'observed raw halfwords')
    u16 = lambda offset: struct.unpack_from('<H', ordinary, offset)[0]
    caps = [u16(offset) for offset in (0xf2,0xf4,0xf6)]
    retained = [u16(offset) for offset in (0x104,0x106,0x108)]
    need((u16(0xea),u16(0xf0),u16(0x116)) == (3,900,1), 'ordinary inputs')
    need(caps == retained == [6,6,6], 'caps and retained outputs')
    computed = [quotient(3,900,value,cap) for value,cap in zip(values[1:],caps)]
    defaults = [quotient(3,900,1024,cap)[1] for cap in caps]
    need(computed == [(23,6)]*3 and defaults == [3]*3, 'cross-time substitution')
    need(quotient(65535,65535,1,6)[1] == 0, 'halfword before cap')
    need(u16(0xe6) == 1 and u16(0x2fc) == 0 and derived[0x3d8] == 1, 'selector compatibility')
    print(json.dumps({
        'target_operations_in_this_verifier':0,
        'conditional_divisors':list(values[1:]),
        'ordinary_numerator_fields':[3,900],
        'cross_time_unclamped_candidates':[v[0] for v in computed],
        'cross_time_capped_candidates':[v[1] for v in computed],
        'retained_indexes':retained,'stored_default_substitution':defaults,
        'terminal_separation_centiseconds':gap,
        'ordinary_and_derived_equal_original_W':True,
        'atomic_event_tuple':False,'npc_live_pointer_identity_proven':False,
        'runtime_producer_or_branch_proven':False,'physical_cause_proven':False,
    },sort_keys=True,separators=(',',':')))

if __name__ == '__main__':
    main()
