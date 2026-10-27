#!/usr/bin/env python3
"""Reproduce the retained host DRM histogram comparison around AV MODE2.

Host files only: this performs no TV, network, root, USB, native-helper,
controller, power, reset, or MMIO operation.
"""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
OVERNIGHT = BASE / 'overnight'


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(path, expected):
    raw = path.read_bytes()
    need(digest(raw) == expected, 'identity: ' + str(path))
    return raw


def extract_gzip_section(raw, name):
    text = raw.decode('ascii')
    begin = '@@ ' + name
    end = begin + '_END'
    lines = text.splitlines()
    need(lines.count(begin) == 1 and lines.count(end) == 1, name + ' markers')
    first, last = lines.index(begin), lines.index(end)
    need(last > first + 3, name + ' shape')
    boot_id, uptime = lines[first + 1:first + 3]
    need(re.fullmatch(r'[0-9a-f-]{36}', boot_id) is not None, name + ' boot id')
    need(re.fullmatch(r'[0-9]+\.[0-9]+ [0-9]+\.[0-9]+', uptime) is not None,
         name + ' uptime')
    compressed = base64.b64decode(''.join(lines[first + 3:last]), validate=True)
    return boot_id, uptime, gzip.decompress(compressed)


ROW = re.compile(
    r'^\[([0-9]+\.[0-9]+)\] \[DRM-DP\] '
    r'\[HISTOGRAM (INP\([YRGB]\)|DE\(SAC\)|VE\(CE_\))[^]]*\] '
    r'0x\|((?:[0-9a-f]{6}\|)+)$')
LABELS = ['INP(Y)', 'INP(R)', 'INP(G)', 'INP(B)', 'DE(SAC)', 'VE(CE_)']


def histogram_groups(raw):
    rows = []
    for line in raw.decode('utf-8', errors='strict').splitlines():
        match = ROW.fullmatch(line)
        if match:
            rows.append({
                'time': float(match.group(1)),
                'label': match.group(2),
                'values': [int(value, 16) for value in match.group(3).split('|') if value],
            })
    need(rows and len(rows) % 6 == 0, 'complete histogram row count')
    groups = []
    for offset in range(0, len(rows), 6):
        group = rows[offset:offset + 6]
        need([row['label'] for row in group] == LABELS, 'histogram group order')
        need(group[-1]['time'] - group[0]['time'] < 0.001, 'histogram group span')
        need([len(row['values']) for row in group] == [8, 8, 8, 8, 10, 8],
             'histogram field widths')
        groups.append({
            'time': group[0]['time'],
            'end_time': group[-1]['time'],
            'values': {row['label']: row['values'] for row in group},
        })
    return groups


def accepted_snapshot(directory, record_hash, result_hash, ordinary_hash, derived_hash):
    record = json.loads(pinned(directory / 'record.json', record_hash))
    result = json.loads(pinned(directory / 'result.json', result_hash))
    ordinary = pinned(directory / 'ordinary-ap-exco-prefix.bin', ordinary_hash)
    derived = pinned(directory / 'derived-ap-exco.bin', derived_hash)
    need((len(ordinary), len(derived)) == (824, 1004), 'snapshot extents')
    need(result['transport_accepted'] is True and
         result['interpretation_accepted'] is True and
         result['cleanup'] == 'STAGE_ABSENT', 'snapshot acceptance')
    need(result['ordinary_raw_sha256'] == ordinary_hash and
         result['derived_raw_sha256'] == derived_hash, 'snapshot result hashes')
    uptime = float(record['terminal']['uptime'].split()[0])
    x_values = [struct.unpack_from('<I', ordinary, offset)[0]
                for offset in (0x10A, 0x10E, 0x112)]
    return {
        'boot_id': record['terminal']['boot_id'],
        'terminal_uptime': uptime,
        'ordinary_sha256': ordinary_hash,
        'derived_sha256': derived_hash,
        'X0_X1_X2': x_values,
    }


def main():
    provenance = pinned(
        BASE / 'tcon-research/drm-histogram-logging-provenance.md',
        'a0153f56add3290c27e2d0e4d1816409253e6190f53b1ea6a71bee375404b220')
    need(b'`dp_reg_readl`' in provenance and b'QD-protection input' in provenance,
         'source provenance boundary')

    av = OVERNIGHT / 'stock-rt-lifecycle-trial-20261027av'
    source = OVERNIGHT / 'stock-rt-av-20261027.onset'
    manifest_raw = pinned(av / 'evidence-manifest.json',
                          '1c0dbaaa92b6167aa23e2ca2bd04cadbabe90f422535fbe935cbcfb5ddccca75')
    manifest = json.loads(manifest_raw)
    expected = {
        'panel-idle-20261026/overnight/stock-rt-av-20261027.onset/artifacts.txt':
            'a5cb2171a4faf92f7128d15d8adcda5f30449d83daff0aa31fceb4e6b539f95d',
        'panel-idle-20261026/overnight/stock-rt-av-20261027.onset/trace':
            'ea9f0a57ae34faaae714c11230194d32819cf28c5debcbe8ec1e381706d686ed',
        'panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/kernel-start.txt':
            'e5eac973ce8ca603e5bfc1e1749eea3897e87eec14f17b4943720da9bbc82e68',
        'panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/kernel-end.txt':
            'c00c2efd6ba743283c38113dc4513d04c9e01488e84c7a27b7536e97d2ece8e8',
        'panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/trace-decoded.json':
            'a6835690ca62fb68ca563ba132171549161876f96c4c964f1a8928ccbd59978b',
        'panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/baseline-and-lifecycle-audit.md':
            'f3756c82257e8b0afcb327c4fc9a5436990cb55ea959a999859d00d9cdbb1088',
    }
    for name, expected_hash in expected.items():
        need(manifest['files'][name]['sha256'] == expected_hash, 'AV manifest pin: ' + name)

    artifacts = pinned(source / 'artifacts.txt', expected[next(iter(expected))])
    start_boot, start_uptime, start_from_artifact = extract_gzip_section(artifacts, 'KERNEL_START')
    end_boot, end_uptime, end_from_artifact = extract_gzip_section(artifacts, 'KERNEL_END')
    start_saved = pinned(av / 'kernel-start.txt', expected[
        'panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/kernel-start.txt'])
    end_saved = pinned(av / 'kernel-end.txt', expected[
        'panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/kernel-end.txt'])
    need(start_from_artifact == start_saved and end_from_artifact == end_saved,
         'gzip artifact reconstruction')
    need(start_boot == end_boot == '00000000-0000-4000-8000-000000000000',
         'one retained Linux boot')

    trace_raw = pinned(source / 'trace', expected[
        'panel-idle-20261026/overnight/stock-rt-av-20261027.onset/trace'])
    trace_decoded = json.loads(pinned(av / 'trace-decoded.json', expected[
        'panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/trace-decoded.json']))
    need(trace_decoded['source_sha256'] == digest(trace_raw), 'decoded/raw trace binding')
    audit = pinned(av / 'baseline-and-lifecycle-audit.md', expected[
        'panel-idle-20261026/overnight/stock-rt-lifecycle-trial-20261027av/baseline-and-lifecycle-audit.md'])
    need(b'136363.892943..951' in audit and b'136365.920098' in audit and
         b'136366.222190' in audit, 'audit action bounds')
    action_match = re.search(
        rb'^\[([0-9]+\.[0-9]+)\].*QDFTcon_SetQdTconPowerControl\[17157:[^]]+\]: Reset\(2\)$',
        end_saved, re.MULTILINE)
    need(action_match is not None, 'PID-tagged MODE2 start')
    action_start = float(action_match.group(1))
    action_transfers = [row for row in trace_decoded['transfers'] if row['pid'] == 17157]
    need(len(action_transfers) == 346, 'MODE2 transfer count')
    action_end = max(row['end_time'] for row in action_transfers)
    need((action_start, action_end) == (136363.892943, 136366.222190),
         'MODE2 action bounds')

    start_groups = histogram_groups(start_from_artifact)
    end_groups = histogram_groups(end_from_artifact)
    need((len(start_groups), len(end_groups)) == (51, 50), 'histogram group counts')
    start_times = {group['time'] for group in start_groups}
    end_times = {group['time'] for group in end_groups}
    signatures = {
        json.dumps(group['values'], sort_keys=True)
        for group in start_groups + end_groups
    }
    need(len(signatures) == 1, 'all retained histogram values stable')
    before = [group for group in end_groups if group['end_time'] < action_start][-1]
    after = [group for group in end_groups if group['time'] > action_end][0]
    need((before['time'], after['time']) == (136361.560322, 136371.577002),
         'nearest bracketing histogram groups')
    need(before['values'] == after['values'], 'bracketing values stable')
    need(not [group for group in end_groups
              if group['time'] <= action_end and group['end_time'] >= action_start],
         'no retained histogram group inside action interval')

    old = accepted_snapshot(
        OVERNIGHT / 'ap-exco-input-snapshot-20261027w/capture-once',
        '0a9a35106d6d2ce35d3212d51775fe2fd2a8e68ccf4d2c08c150677e6b7cf1c9',
        '83cd349d84ef397074f36c5b80e2cc72ad8b00bbeebae5dae978a21f11935171',
        '0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271',
        'de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0')
    ak = accepted_snapshot(
        OVERNIGHT / 'npc-ap-divisor-snapshot-20261027ak/capture-ordinary-after',
        '28a14ab86d85a30f77f78628c39646bbf9b1bc21c20522c3b4d0b1947efa8423',
        'e1480df76124fa3ea07a62bfc88c68d3f1eaa718bee60d3dc86df424ca1c2541',
        '0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271',
        'de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0')
    aw = accepted_snapshot(
        OVERNIGHT / 'stock-rt-state-delta-20261027aw/post-lifecycle-inputs',
        'f4722be28e23b953c1befbd60482f592741b90b231bc43dd415f66ae04946cd9',
        '778cb7e9ab4f3950c6a466f799e41b13115e0b9e4cef8f8ac412466041d90e57',
        '94839af14f71937d0defd81b380d277f092d8a9add3f782731da835a66dee2cf',
        'eb15688aac78bcaf6ca12d34249898b355df5d4f7332b97e9d9b325852be4694')
    need(old['ordinary_sha256'] == ak['ordinary_sha256'] and
         old['derived_sha256'] == ak['derived_sha256'], 'old W/AK byte identity')
    need(aw['ordinary_sha256'] != ak['ordinary_sha256'], 'later AW input difference')
    need({old['boot_id'], ak['boot_id'], aw['boot_id'], start_boot} ==
         {'00000000-0000-4000-8000-000000000000'}, 'snapshot boot lineage')

    result = {
        'target_operations': 0,
        'artifact_reconstruction': {
            'manifest_sha256': digest(manifest_raw),
            'artifacts_sha256': digest(artifacts),
            'start': {'boot_id': start_boot, 'uptime': start_uptime,
                      'sha256': digest(start_from_artifact)},
            'end': {'boot_id': end_boot, 'uptime': end_uptime,
                    'sha256': digest(end_from_artifact)},
            'saved_extracts_byte_equal': True,
        },
        'mode2': {'start': action_start, 'i2c_tail_end': action_end},
        'histograms': {
            'start_extract_groups': len(start_groups),
            'end_extract_groups': len(end_groups),
            'overlapping_group_times': len(start_times & end_times),
            'unique_group_times': len(start_times | end_times),
            'unique_value_sets_across_both_extracts': len(signatures),
            'nearest_pre': before,
            'nearest_post': after,
            'per_field_changed': {label: before['values'][label] != after['values'][label]
                                  for label in LABELS},
            'group_during_action_interval': False,
            'pre_first_row_to_action_start_seconds': round(action_start - before['time'], 6),
            'action_tail_to_post_first_row_seconds': round(after['time'] - action_end, 6),
        },
        'controller_snapshot_timeline': {
            'old_W_AP_EXCO': old,
            'AK_repeat': ak,
            'AV_action': {'start': action_start, 'end': action_end},
            'later_AW': aw,
            'AK_to_AV_start_seconds': round(action_start - ak['terminal_uptime'], 6),
            'AV_tail_to_AW_seconds': round(aw['terminal_uptime'] - action_end, 6),
        },
        'claims': {
            'host_reported_register_values_stable_across_bracket': True,
            'constant_content_proved': False,
            'histogram_cadence_or_frame_association_proved': False,
            'host_histogram_bound_to_pre_pd_or_controller_X': False,
            'controller_snapshots_are_event_time_for_AV': False,
            'samples_atomic': False,
            'physical_light_or_picture_observed': False,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
