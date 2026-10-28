#!/usr/bin/env python3
"""Offline admission of a completed EM40 capture before a separate EB read."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
B = Path(__file__).resolve().parent.parent
PARSER = B / 'rtp-refresh-dense-checkpoints-20261028em/parse-result.py'
PARSER_SHA = 'cfa98869b725ce86d9bab876e7a59c554f690b75f77e17e22de035b214cdc49c'
MANIFEST_SHA = '83382d9a55271194480cb17d777a0d45737128f3dd849228b9517c3d2284c522'

def need(condition, reason):
    if not condition:
        raise ValueError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify(directory):
    need(directory.is_absolute() and not directory.is_symlink(), 'ordinary absolute capture')
    need(sha(PARSER.read_bytes()) == PARSER_SHA, 'frozen EM parser')
    spec = importlib.util.spec_from_file_location('eo_em_admission', PARSER)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    native_path = directory / 'native.receipt.json'
    n, summaries, files, gc, q = parser.parse_native(native_path.read_text())
    need(gc == [] and q.get('trialQualified') is True, 'strict synchronized workflow qualification')
    result_path = directory / 'result.json'
    r = parser.load_parent().strict_json(result_path.read_text())
    need(type(r) is dict, 'wrapper result object')
    for key in ('nativeInvocations', 'retries', 'headersSent', 'bulkTransfers', 'scoreCheckpointCount'):
        need(type(r.get(key)) is int, 'exact integer result field ' + key)
    need(type(r.get('rawFiles')) is list and all(type(row) is dict and type(row.get('bytes')) is int for row in r['rawFiles']), 'exact integer raw sizes')
    need(r.get('accepted') is True and r.get('trialQualified') is True
         and r.get('manifestSha256') == MANIFEST_SHA and r.get('cleanup') == 'STAGE_ABSENT'
         and r.get('nativeInvocations') == 1 and r.get('retries') == 0, 'accepted one-shot EM result')
    need(n['accepted'] is True and n['protocolPhase'] == 'ReadyForHeader'
         and n['released'] is True and n['closed'] is True, 'closed native boundary')
    need(r['headersSent'] == n['headersSent'] and r['bulkTransfers'] == n['bulkTransfers'], 'exact transfer counts')
    inventory = []
    for name, raw, digest in files:
        need((directory / name).read_bytes() == raw, 'saved raw ' + name)
        inventory.append({'name': name, 'bytes': len(raw), 'sha256': digest})
    need(r['rawFiles'] == inventory, 'complete saved raw inventory')
    rows = q['scoreCheckpoints']['rows']
    need(1 <= len(rows) <= 60 and r['scoreCheckpointCount'] == len(rows), 'complete compact row count')
    need(all(x['startAlternateThreshold'] == x['endAlternateThreshold'] == 40 for x in rows), 'all compact limits40')
    need(n['terminalReason'] in ('TimeLimit', 'CycleLimit', 'TransitionCaptured'), 'qualified terminal reason')
    expected = [1, 0x1001, 0] if n['terminalReason'] == 'TransitionCaptured' else [0, 0, 1]
    r_samples = []
    completed_ins = []
    for capture in n['retained']:
        transfers = capture['transfers']
        for index, window in enumerate(capture['windows']):
            if window['complete']:
                pair = transfers[2 * index:2 * index + 2]
                need(len(pair) == 2 and pair[1]['afterUs'] is not None, 'complete pair time')
                completed_ins.append(pair[1]['afterUs'])
                if window['name'] == 'R':
                    raw = base64.b64decode(window['rawBase64'], validate=True)
                    need(len(raw) == 256 and struct.unpack_from('<H', raw, 0xc4)[0] == 40, 'every retained R limit40')
                    r_samples.append((pair[1]['afterUs'], [struct.unpack_from('<H', raw, off)[0] for off in (0, 10, 14)]))
    need(r_samples and max(r_samples, key=lambda row: row[0])[1] == expected, 'last actual R agrees with terminal')
    return {'schema': 'eo-completed-em40-admission-v1', 'accepted': True,
            'headers': r['headersSent'], 'bulks': r['bulkTransfers'],
            'checkpoints': len(rows), 'maximumSampledA0': max(x['a0U32'] for x in rows),
            'terminal': n['terminalReason'], 'lastRtTuple': expected,
            'lastCompletedDataAfterUs': max(completed_ins), 'actualSampledLimit': 40,
            'phase': 'ReadyForHeader', 'released': True, 'closed': True,
            'cleanup': 'STAGE_ABSENT', 'targetOperations': 0,
            'physicalPictureObserved': False, 'endpointQueueProof': False,
            'inputs': [{'path': str(path), 'sha256': sha(path.read_bytes())}
                       for path in (PARSER, native_path, result_path)]}

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--capture', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    need(args.output.is_absolute() and not args.output.exists(), 'fresh absolute proof output')
    result = verify(args.capture)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'inputs'}))

if __name__ == '__main__':
    main()
