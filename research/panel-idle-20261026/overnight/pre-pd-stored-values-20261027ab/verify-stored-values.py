#!/usr/bin/env python3
"""Check only the retained Pre-PD payload and earlier W arithmetic inputs."""
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
    package = (BASE / 'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    need(sha(package) == 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0', 'package')
    record = package[0x80600:0x80800]
    need(sha(record) == '11696518d668a8c2ac409a0cf2d7a7e462f2e410bba6e5a0747007618e2ec87f', 'Pre-PD record')
    field = lambda off: struct.unpack_from('<I', record, off)[0]
    need(record[:32] == b'Pre-PD' + bytes(26) and
         [field(off) for off in (0x20,0x24,0x28,0x2c,0x6c,0xac)] ==
         [7,0x58410000,1,0x8000,0,0xab0], 'first group metadata')
    source = 0x80000 + field(0x2c)
    table_offset = 0x584109a4 - field(0x24)
    companion_offset = 0x58410178 - field(0x24)
    need(table_offset + 256 <= field(0xac) and companion_offset + 64 <= field(0xac), 'containment')
    table = package[source + table_offset:source + table_offset + 256]
    companion = package[source + companion_offset:source + companion_offset + 64]
    need(sha(table) == '5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1' and
         table == bytes(256), 'stored table is zero')
    need(sha(companion) == '87665b6d2c1cd41ead5bc1d2ff4eb693e9b8350d77c053249151a0eed53b0542', 'stored companion')
    levels = list(struct.unpack('<16I', companion))
    need(levels == [960,768,640,512,448,384,320,256,192,160,128,96,64,36,1,0], 'stored constants')
    ordinary = (BASE/'ap-exco-input-snapshot-20261027w/capture-once/ordinary-ap-exco-prefix.bin').read_bytes()
    need(sha(ordinary) == '0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271', 'W bytes')
    # Consecutive little-endian halfword pairs mirror u32 sums. All-zero
    # source words produce zero for both selected inclusive index ranges.
    mirrors = [struct.unpack_from('<I', ordinary, off)[0] for off in (0xf8,0xfc,0x100,0x10a,0x10e,0x112)]
    need(mirrors == [8252833,8248159,8248218,8254590,8251261,8250967], 'W sum mirrors')
    print(json.dumps({
        'schema':'pre-pd-stored-values-v1', 'target_operations':0,
        'table_file_range':[hex(source+table_offset),hex(source+table_offset+256)],
        'table_stored_u32_words':64, 'table_stored_all_zero':True,
        'companion_file_range':[hex(source+companion_offset),hex(source+companion_offset+64)],
        'companion_stored_words':levels, 'companion_strictly_descending':True,
        'W_nonzero_sum_mirrors':mirrors,
        'stored_zero_table_alone_reproduces_W_sums':False,
        'current_table_contents_sampled':False, 'runtime_writer_identified':False,
        'stored_payload_loaded_on_observed_boot_proved':False,
        'pixel_or_luma_units_proved':False, 'blackout_cause_or_fix_proved':False,
    },sort_keys=True))


if __name__ == '__main__':
    main()
