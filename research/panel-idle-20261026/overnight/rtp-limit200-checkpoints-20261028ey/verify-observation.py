#!/usr/bin/env python3
"""Offline admission of a completed EY200 capture before a separate EB read."""
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
PARSER = B / 'rtp-limit200-checkpoints-20261028ey/parse-result.py'
PARSER_SHA = 'c3175bb5fa190dc517f0450c0e726089b451decaeeb0da83f262a477836551ba'
MANIFEST_SHA = 'd5147751a8ec387cf6d85b06eb197c0f08075a1cb2e2157b7fef152fcd6a878b'

def need(condition, reason):
    if not condition:
        raise ValueError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def verify(directory):
    need(directory.is_absolute() and not directory.is_symlink(), 'ordinary absolute capture')
    need(sha(PARSER.read_bytes()) == PARSER_SHA, 'frozen EY parser')
    spec = importlib.util.spec_from_file_location('es_er_admission', PARSER)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    native_path = directory / 'native.receipt.json'
    n, summaries, files, gc, q = parser.parse_native(native_path.read_text())
    need(gc == [] and q.get('trialQualified') is True, 'strict synchronized workflow qualification')
    result_path = directory / 'result.json'
    r = parser.load_parent().strict_json(result_path.read_text())
    need(type(r) is dict and r.get('schema') == 'ey-limit200-checkpoint-wrapper-result-v1', 'fixed200 wrapper result schema')
    for key in ('nativeInvocations', 'retries', 'headersSent', 'bulkTransfers', 'scoreCheckpointCount'):
        need(type(r.get(key)) is int, 'exact integer result field ' + key)
    need(type(r.get('rawFiles')) is list and all(type(row) is dict and type(row.get('bytes')) is int for row in r['rawFiles']), 'exact integer raw sizes')
    need(r.get('accepted') is True and r.get('trialQualified') is True
         and r.get('manifestSha256') == MANIFEST_SHA and r.get('cleanup') == 'STAGE_ABSENT'
         and r.get('nativeInvocations') == 1 and r.get('retries') == 0, 'accepted one-shot EY result')
    need(n['accepted'] is True and n['protocolPhase'] == 'ReadyForHeader'
         and n['released'] is True and n['closed'] is True, 'closed native boundary')
    need(r['headersSent'] == n['headersSent'] and r['bulkTransfers'] == n['bulkTransfers'], 'exact transfer counts')
    inventory = []
    for name, raw, digest in files:
        need((directory / name).read_bytes() == raw, 'saved raw ' + name)
        inventory.append({'name': name, 'bytes': len(raw), 'sha256': digest})
    need(r['rawFiles'] == inventory, 'complete saved raw inventory')
    rows = q['scoreCheckpoints']['rows']
    need(1 <= len(rows) <= 56 and r['scoreCheckpointCount'] == len(rows), 'complete compact row count')
    need(all(x['startAlternateThreshold'] == x['endAlternateThreshold'] == 200 for x in rows), 'all compact limits200')
    need(n['terminalReason'] in ('TimeLimit', 'CycleLimit', 'TransitionCaptured'), 'qualified terminal reason')
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
                    need(len(raw) == 256 and struct.unpack_from('<H', raw, 0xc4)[0] == 200, 'every retained R limit200')
                    r_samples.append((pair[1]['afterUs'], [struct.unpack_from('<H', raw, off)[0] for off in (0, 10, 14)]))
    need(bool(r_samples), 'actual retained R samples')
    expected = max(r_samples, key=lambda row: row[0])[1]
    if n['terminalReason'] == 'TransitionCaptured':
        need(expected == [1, 0x1001, 0], 'fault terminal has latest fault R')
    else:
        need(expected in ([0, 0, 1], [0, 0, 0]), 'bounded nonfault terminal has clean or quiescent latest R')
    all_sampled_clean = all(x['cleanRBrackets'] for x in rows) and all(t == [0, 0, 1] for _, t in r_samples)
    return {'schema': 'ey-completed-fixed200-admission-v1', 'accepted': True,
            'headers': r['headersSent'], 'bulks': r['bulkTransfers'],
            'checkpoints': len(rows), 'maximumSampledA0': max(x['a0U32'] for x in rows),
            'terminal': n['terminalReason'], 'lastRtTuple': expected,
            'quiescentCyclesCompleted': n['quiescentCyclesCompleted'],
            'allSampledClean': all_sampled_clean, 'rtObservationOutcome': q['rtObservationOutcome'],
            'fixed200Evidence': q['fixed200Evidence'], 'lastCompletedDataAfterUs': max(completed_ins), 'actualSampledLimit': 200,
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
