#!/usr/bin/env python3
"""Compare two saved W input snapshots using a bounded selected-source case.

Host files only. No TV, network, native helper or controller operation.
This checks numerical consistency, not execution, timing or physical cause.
"""
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
B = HERE.parent


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(path, digest):
    raw = path.read_bytes()
    need(sha(raw) == digest, 'identity: ' + str(path))
    return raw


def decode(ordinary, derived):
    need((len(ordinary), len(derived)) == (824, 1004), 'snapshot extents')
    u16 = lambda offset: struct.unpack_from('<H', ordinary, offset)[0]
    u32 = lambda offset: struct.unpack_from('<I', ordinary, offset)[0]
    need([u16(x) for x in (0xCA, 0xCC, 0xCE, 0x116)] == [1, 1, 0, 1],
         'outside the deliberately bounded captured branch')
    p = [u32(x) for x in (0xD0, 0xD4, 0xD8, 0xDC)]
    x = [u32(x) for x in (0x10A, 0x10E, 0x112)]
    condition = any(p[i] < x[i] for i in range(3))
    # For ca=cc=1, ce=0, selected helper F0 uses this strict condition;
    # F1 is bypassed. A false condition clears e2. A mature true condition
    # has already reached e0 and yields F0=1. These snapshots are not an
    # input/output invocation pair, so only fixed-point consistency is tested.
    expected_e6 = int(condition and u16(0xE2) >= u16(0xE0))
    need(u16(0xE6) == expected_e6, 'first-helper output consistency')
    if not condition:
        need(u16(0xE2) == 0, 'false-condition counter consistency')
    composite = bool((u16(0xE6) & 1) or u16(0x2FC))
    need(derived[0x3D8] == int(composite), 'ordinary/derived composite consistency')
    return {
        'P': p, 'initial_sum_mirrors': [u32(x) for x in (0xF8, 0xFC, 0x100)],
        'recomputed_sum_mirrors': x, 'strict_P_lt_X': [p[i] < x[i] for i in range(3)],
        'candidate_condition': condition, 'debounce_threshold': u16(0xE0),
        'debounce_counter': u16(0xE2), 'output_e6': u16(0xE6),
        'other_output_2fc': u16(0x2FC),
        'initial_indexes': [u16(x) for x in (0xEA, 0xEC, 0xEE)],
        'recomputed_indexes': [u16(x) for x in (0x104, 0x106, 0x108)],
        'index_caps': [u16(x) for x in (0xF2, 0xF4, 0xF6)],
        'common_multiplier': u16(0xF0), 'upper_bound_flag': u16(0xE8),
        'derived_bytes_0_1_3d8': [derived[i] for i in (0, 1, 0x3D8)],
        'composite': composite,
    }


def main():
    package = pinned(B / 'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin',
                     'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0')
    need(len(package) == 0x500000, 'package extent')
    image = package[0x200:0x40200]
    for start, end, digest in [
        (0x2F5D8, 0x2F970, '428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45'),
        (0x2F804, 0x2F964, '1edc35ef9c97b5836cbf6be9c671d948f247b31375c70d1fe9cff1f57941566a'),
        (0x2FB44, 0x2FB7C, 'f9b94ce545ffc142ac8cbff9d0c4f2c6bcf7146316a59dd32d49814ffb8443a7'),
    ]:
        need(sha(image[start:end]) == digest, f'selected-source body {start:x}')
    rows = {}
    for name, path, odigest, ddigest in [
        ('older_post_fault_AK', B / 'npc-ap-divisor-snapshot-20261027ak/capture-ordinary-after',
         '0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271',
         'de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0'),
        ('later_post_lifecycle_AW', HERE / 'post-lifecycle-inputs',
         '94839af14f71937d0defd81b380d277f092d8a9add3f782731da835a66dee2cf',
         'eb15688aac78bcaf6ca12d34249898b355df5d4f7332b97e9d9b325852be4694'),
    ]:
        ordinary = pinned(path / 'ordinary-ap-exco-prefix.bin', odigest)
        derived = pinned(path / 'derived-ap-exco.bin', ddigest)
        result = json.loads((path / 'result.json').read_text())
        need(result['transport_accepted'] and result['interpretation_accepted'] and
             result['cleanup'] == 'STAGE_ABSENT' and
             result['ordinary_raw_sha256'] == odigest and result['derived_raw_sha256'] == ddigest,
             'accepted snapshot/raw identity binding')
        rows[name] = decode(ordinary, derived)
    old, new = rows.values()
    stable = ['P', 'debounce_threshold', 'initial_indexes', 'recomputed_indexes',
              'index_caps', 'common_multiplier', 'upper_bound_flag']
    need(all(old[k] == new[k] for k in stable), 'claimed stable setup changed')
    need(old['candidate_condition'] is True and new['candidate_condition'] is False,
         'claimed comparison difference')
    print(json.dumps({
        'target_operations': 0, 'scope': 'late sequential numeric consistency only',
        'image0_interpretation': 'conditional selected-source model, not executing-code proof',
        'timing': 'AK older post-fault snapshot; AW later than AV post-X, not coincident',
        'stable_fields': stable, 'snapshots': rows,
        'table_words_observed': False, 'physical_units_identified': False,
        'physical_picture_observed': False, 'exclusive_reset_cause_proved': False,
    }, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
