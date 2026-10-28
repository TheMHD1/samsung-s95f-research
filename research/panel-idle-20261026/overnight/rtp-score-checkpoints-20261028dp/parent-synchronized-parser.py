#!/usr/bin/env python3
"""Strict offline synchronized-key result parser; no root/network/TV execution.

parse_native(text) returns (native, captures, raw_files, gc_rows, qualification).
The old pinned parser remains responsible for its unchanged transport contract.
Trial qualification means a clean trigger, one completed key workflow and
completed R coverage at/after Down begins. It never establishes UI receipt, emitted light, or key causation. Unarmed valid
transport records are preserved with trialQualified=False. Attempted key
failures/malformed states are rejected and their original bytes must be retained.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
PARENT = HERE / 'transport-parser.py'
PARENT_SHA = 'acc9f37f3586dc1066a31ec853d739da127fc2afb704fe7202f14a1cc170f0af'
SCHEMA = 'managed-usb-rt-synchronized-key-df-v1'
MAX_BYTES = 24576
FULL = ['R', 'M', 'C', 'P', 'N', 'H', 'L', 'R']


def need(ok, why):
    if not ok:
        raise ValueError(why)


def integer(value, why, low=0, high=None):
    if high is None:
        high = (1 << 63) - 1
    need(type(value) is int and value >= low and value <= high, why)
    return value


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON field ' + key)
            result[key] = value
        return result

    def bad(value):
        raise ValueError('non-JSON constant ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=bad)


def load_parent():
    # Compile the exact bytes just hashed; do not import a later reread or root
    # adapter, write pycache, or execute the original script's CLI.
    raw = PARENT.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == PARENT_SHA, 'pinned transport parser identity')
    module = types.ModuleType('bx_frozen_passive_parser')
    module.__file__ = str(PARENT)
    exec(compile(raw, str(PARENT), 'exec'), module.__dict__)
    return module


def parse_lines(text, parent):
    need(type(text) is str and len(text.encode('utf-8')) <= MAX_BYTES, 'native output byte bound')
    # Use stricter duplicate-key decoding before the inherited line contract.
    for line in text.splitlines():
        if line.startswith('{'):
            strict_json(line)
    rows, gc = parent.parse_lines_with_gc(text)
    need(len(rows) == 1 and type(rows[0]) is dict, 'one native outcome')
    return rows[0], gc


def same_cycle(left, right):
    a, b = copy.deepcopy(left), copy.deepcopy(right)
    a.pop('role', None); b.pop('role', None)
    return a == b


def check_times(value, captures):
    start = integer(value.get('startUs'), 'startUs')
    end = integer(value.get('endUs'), 'endUs', start)
    for capture in captures:
        for transfer in capture['transfers']:
            before = integer(transfer.get('beforeUs'), 'transfer beforeUs', start, end)
            integer(transfer.get('afterUs'), 'transfer afterUs', before, end)
    return start, end


def key_success(state, baseline_end, end):
    need(set(state) == {'key', 'trigger', 'attempted', 'completed', 'armedUs', 'endUs',
                        'uiReceiptObserved', 'physicalPictureObserved', 'calls'}, 'successful intervention fields/no errors')
    need(state['attempted'] is True and state['completed'] is True, 'key workflow attempted/completed')
    armed = integer(state['armedUs'], 'armedUs after baseline R-end', baseline_end, end)
    calls = state['calls']
    need(type(calls) is list and len(calls) == 2, 'exactly one down/up attempt')
    last = armed
    for phase, call in zip(('down', 'up'), calls):
        need(type(call) is dict and set(call) == {'phase', 'beforeUs', 'afterUs', 'exitCode', 'started',
             'reaped', 'timedOut', 'stdoutBytes', 'stderrBytes'}, 'key call fields/no errors')
        need(call['phase'] == phase and call['started'] is True and call['reaped'] is True and
             call['timedOut'] is False, 'key child success ' + phase)
        need(type(call['exitCode']) is int and call['exitCode'] == 0, 'key child exit ' + phase)
        integer(call['stdoutBytes'], 'key stdout bound', 0, 4096)
        integer(call['stderrBytes'], 'key stderr bound', 0, 4096)
        before = integer(call['beforeUs'], 'key ' + phase + ' beforeUs order', last, end)
        last = integer(call['afterUs'], 'key ' + phase + ' afterUs order', before, end)
    integer(state['endUs'], 'intervention endUs order', last, end)


def key_unarmed(state):
    need(set(state) == {'key', 'trigger', 'attempted', 'completed', 'uiReceiptObserved',
                        'physicalPictureObserved', 'calls'}, 'unarmed intervention fields')
    need(state['attempted'] is False and state['completed'] is False, 'unarmed workflow state')
    calls = state['calls']
    need(type(calls) is list and len(calls) == 2, 'unarmed call extent')
    for phase, call in zip(('down', 'up'), calls):
        need(type(call) is dict and set(call) == {'phase', 'started', 'reaped', 'timedOut',
                                                'stdoutBytes', 'stderrBytes'}, 'unarmed call fields')
        need(call['phase'] == phase and call['started'] is False and call['reaped'] is False and
             call['timedOut'] is False, 'unarmed child state')
        need(integer(call['stdoutBytes'], 'unarmed stdout') == 0 and
             integer(call['stderrBytes'], 'unarmed stderr') == 0, 'unarmed output count')


def r_intervals(capture):
    intervals = []
    for i, window in enumerate(capture['windows']):
        if window['name'] == 'R':
            intervals.append({'classification': window['observedRtState']['classification'],
                              'beforeUs': capture['transfers'][2*i]['beforeUs'],
                              'afterUs': capture['transfers'][2*i+1]['afterUs'],
                              'role': capture['role'], 'cycleIndex': capture['cycleIndex']})
    return intervals


def relation(left, right):
    if left['afterUs'] < right['beforeUs']:
        return 'strictly_before'
    if left['beforeUs'] > right['afterUs']:
        return 'strictly_after'
    return 'overlaps_or_touches'


def ordering(native, retained, state):
    result = {'classification': 'unarmed_no_key_comparison', 'firstFaultRead': None,
              'latestCleanRead': None, 'softwareTransitionBracket': None,
              'firstFaultReadVsDown': None, 'transitionBracketVsDown': None,
              'keyCausalityEstablished': False,
              'scope': 'full OUT-before/IN-after USB brackets, conditional on reply freshness; key call/return is not UI consumption; no physical-light timestamp'}
    if not state['attempted']:
        return result
    if not native['onsetObserved']:
        result['classification'] = 'no_software_transition_observed'
        return result
    transitions = [capture for capture in retained if capture['role'] == 'transition']
    need(len(transitions) == 1, 'one transition for ordering')
    first_fault = next(x for x in r_intervals(transitions[0]) if x['classification'] == 'Faulted')
    clean = [x for capture in retained if capture['role'] in ('last-clean', 'transition')
             for x in r_intervals(capture) if x['classification'] == 'Clean' and x['afterUs'] <= first_fault['beforeUs']]
    need(clean, 'clean read before first fault read')
    latest = max(clean, key=lambda x: x['afterUs'])
    bracket = {'beforeUs': latest['beforeUs'], 'afterUs': first_fault['afterUs']}
    down = state['calls'][0]
    fault_relation, onset_relation = relation(first_fault, down), relation(bracket, down)
    if fault_relation == 'strictly_before':
        classification = 'fault_observed_before_down_dispatch'
    elif onset_relation == 'strictly_after':
        classification = 'retained_clean_and_fault_reads_after_down_return'
    elif fault_relation == 'overlaps_or_touches':
        classification = 'first_fault_read_overlaps_down_call'
    else:
        classification = 'first_fault_read_after_down_but_transition_bracket_spans_down'
    result.update(classification=classification, firstFaultRead=first_fault, latestCleanRead=latest,
                  softwareTransitionBracket=bracket, firstFaultReadVsDown=fault_relation,
                  transitionBracketVsDown=onset_relation)
    return result


def parse_native(text):
    parent = load_parent()
    value, gc = parse_lines(text, parent)
    need(value.get('schema') == SCHEMA, 'synchronized native schema')
    need('observationAccepted' in value and type(value['observationAccepted']) is bool and
         type(value.get('accepted')) is bool, 'native acceptance booleans')
    need(value['observationAccepted'] is True, 'transport observation not accepted')
    state = value.get('intervention')
    need(type(state) is dict and state.get('key') == 'Left' and state.get('trigger') == 'first-full-clean-cycle',
         'fixed key/trigger')
    need(state.get('uiReceiptObserved') is False and state.get('physicalPictureObserved') is False,
         'no unsupported UI/physical observation')
    need(type(state.get('attempted')) is bool, 'attempted boolean')
    captures = value.get('retained')
    need(type(captures) is list and all(type(x) is dict for x in captures), 'retained captures')
    baselines = [x for x in captures if x.get('role') == 'trigger-baseline']
    baseline, baseline_summary, baseline_raw = None, None, []
    if state['attempted']:
        need(len(baselines) == 1 and captures[0] is baselines[0], 'one first trigger baseline')
        baseline = baselines[0]
        baseline_summary, baseline_raw = parent.parse_capture(baseline, 'trigger-baseline', FULL, 0)
        need(baseline_summary['cycle'] == 1 and baseline_summary['rt_states'] == ['Clean', 'Clean'],
             'full clean cycle-one trigger baseline')
    else:
        need(not baselines, 'unarmed must not retain trigger baseline')
    projected = copy.deepcopy(value)
    projected['schema'] = 'managed-usb-rt-passive-observer-v1'
    projected['accepted'] = projected.pop('observationAccepted')
    projected.pop('intervention')
    if baseline is not None:
        projected['retained'] = projected['retained'][1:]
    # No counters are adjusted: the baseline is a retained duplicate, not new I/O.
    transport, summaries, raw_files, _ = parent.parse_native(json.dumps(projected, separators=(',', ':')))
    start, end = check_times(value, captures)
    if baseline is not None:
        need(integer(value['cleanCyclesCompleted'], 'clean cycle count') >= 1, 'baseline requires a completed clean cycle')
        last_clean = next(x for x in projected['retained'] if x['role'] == 'last-clean')
        if last_clean['cycleIndex'] == 1:
            need(same_cycle(baseline, last_clean), 'cycle-one baseline raw/timestamps differ from first clean cycle')
        else:
            need(baseline_summary['last_us'] <= last_clean['transfers'][0]['beforeUs'],
                 'cycle-one baseline precedes later rolling clean')
        key_success(state, baseline_summary['last_us'], end)
        later = [c['transfers'][0]['beforeUs'] for c in projected['retained']
                 if c['cycleIndex'] > 1 and c['transfers']]
        if later:
            need(state['armedUs'] <= min(later), 'key must arm before later-cycle USB requests')
        need(value['accepted'] is True, 'completed successful trial native acceptance')
    else:
        key_unarmed(state)
        need(value['cleanCyclesCompleted'] == 0 and value['accepted'] is False,
             'unarmed transport-only native acceptance')
    # EndUs includes the worker join, so it is not the USB observation edge.
    # A key starting after the retained completed reads recreates the missed
    # interval this instrument is intended to prevent. Up may finish later.
    completions = [t['afterUs'] for capture in projected['retained'] for t in capture['transfers']
                   if t['direction'] == 'IN']
    last_read = max(completions) if completions else None
    r_pairs = [pair for capture in projected['retained'] for pair in r_intervals(capture)]
    down_before = state['calls'][0]['beforeUs'] if baseline is not None else None
    within_reads = down_before is not None and last_read is not None and down_before <= last_read
    r_covered = down_before is not None and any(pair['afterUs'] >= down_before for pair in r_pairs)
    key_within_window = within_reads and r_covered
    rejection = (['intervention_not_armed'] if baseline is None else
                 [] if key_within_window else ['keyOutsideObservedWindow'])
    qualification = {'transportAccepted': True, 'observationAccepted': True,
                     'nativeAccepted': value['accepted'], 'trialQualified': baseline is not None and key_within_window,
                     'trialQualificationScope': 'clean cycle-one trigger, successful down/up workflow and completed R coverage at/after Down begins; causality not established',
                     'trialRejectionReasons': rejection,
                     'observationWindow': {'lastCompletedReadDataAfterUs': last_read,
                         'downBeginsBeforeOrAtLastReadCompletion': within_reads,
                         'completedRPairOverlappingOrAfterDownBegins': r_covered,
                         'keyWithinObservedWindow': key_within_window},
                     'workflowAttempts': 1 if baseline is not None else 0,
                     'baselineDuplicatesCountedCycle': baseline is not None,
                     'globalCountersAdjusted': False, 'softwareOnsetObserved': value['onsetObserved'],
                     'uiReceiptObserved': False, 'physicalPictureObserved': False,
                     'keyCausalityEstablished': False, 'ordering': ordering(value, projected['retained'], state)}
    if baseline_summary is not None:
        summaries = [baseline_summary] + summaries
    raw_files = baseline_raw + raw_files
    need(len({name for name, _, _ in raw_files}) == len(raw_files), 'unique retained raw filenames')
    return value, summaries, raw_files, gc, qualification


def parse_result(text):
    native, captures, raw_files, gc, qualification = parse_native(text)
    return {'schema': 'synchronized-key-parsed-result-v1', 'parentParserSha256': PARENT_SHA,
            **qualification, 'globalCounters': {key: native[key] for key in
            ('cyclesStarted', 'cleanCyclesCompleted', 'cleanCyclesDiscarded', 'headersSent', 'bulkTransfers', 'inputsCompleted')},
            'captures': captures, 'rawFiles': [{'name': name, 'bytes': len(raw), 'sha256': digest}
                                              for name, raw, digest in raw_files],
            'gcDiagnosticLines': len(gc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path, help='retained native stdout; stdin when omitted')
    args = parser.parse_args()
    if args.input is not None:
        with args.input.open('rb') as source:
            raw = source.read(MAX_BYTES + 1)
    else:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    need(len(raw) <= MAX_BYTES, 'native input byte bound')
    print(json.dumps(parse_result(raw.decode('utf-8', errors='strict')), indent=2, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError, KeyError, StopIteration, TypeError) as error:
        print(json.dumps({'schema': 'synchronized-key-parser-rejection-v1', 'parserAccepted': False,
                          'transportAccepted': None, 'trialQualified': False,
                          'error': str(error)[:240]}), file=sys.stderr)
        raise SystemExit(2)
