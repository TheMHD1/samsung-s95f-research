#!/usr/bin/env python3
"""Bind the two ordinary cap-helper arrays to packaged NPC record ranges."""
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


def main():
    package = (BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    need(sha(package) == 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0', 'package')
    image = package[0x200:0x40200]
    need(sha(image[0x19338:0x19364]) == sha(image[0x23510:0x2353c]) ==
         '1c1ef2774d5f516ebade2b709a8e341545a49b87306f9b3afbd92b2dabe1abd1', 'two cap helpers')
    need(sha(image[0x5c74:0x5e24]) == 'b77188019bd4de2e61579bd81174842a1ac97a468c8a8901839fc3e2f0e23d05',
         'reviewed type7 first-group loader slices')
    record = package[0x81400:0x81600]
    need(sha(record) == '7d567ebfc11be5c4d71984e9ff593d1575183c704436b12b35403ccce6af943c', 'NPC record')
    value = lambda off: struct.unpack_from('<I',record,off)[0]
    need(record[:32] == b'NPC'+bytes(29) and
         [value(off) for off in (0x20,0x24,0x28)] == [7,0x58430000,2], 'NPC header')
    rows=[]
    for index,address in enumerate([0x584301f0,0x584311f0]):
        source_offset=value(0x2c+4*index)
        destination_offset=value(0x6c+4*index)
        length=value(0xac+4*index)
        need((source_offset,destination_offset,length) ==
             [(0x11600,0,0x8e0),(0x11ee0,0x1000,0x8e0)][index], 'first-group entry')
        start=value(0x24)+destination_offset
        end=start+length
        need(start <= address and address+12 <= end, 'whole three-word array contained')
        source=0x80000+source_offset+address-start
        raw=package[source:source+12]
        need(source == [0x917f0,0x920d0][index] and raw==bytes(12), 'stored cap bytes')
        need(struct.unpack_from('<I',image,0x1935c+index*4)[0] == address and
             struct.unpack_from('<I',image,0x23534+index*4)[0] == address, 'helper literals')
        rows.append({'entry':index,'source_offset':hex(source_offset),
                     'destination_offset':hex(destination_offset),
                     'described_address_range':[hex(start),hex(end)],
                     'array_address':hex(address), 'stored_array_file_range':[hex(source),hex(source+12)],
                     'stored_words':[0,0,0]})
    print(json.dumps({'schema':'npc-enclosing-cap-record-v1','target_operations':0,
                      'package_record':'NPC','record_file_range':['0x81400','0x81600'],
                      'metadata_type':7,'first_group_entries':rows,
                      'individual_field_names_or_units_identified':False,
                      'live_array_values_or_boot_load_sampled':False,
                      'runtime_producer_identified':False,
                      'NPC_record_equated_with_NPC_AP_RAM_record':False,
                      'blackout_cause_or_fix_proved':False},sort_keys=True))


if __name__ == '__main__':
    main()
