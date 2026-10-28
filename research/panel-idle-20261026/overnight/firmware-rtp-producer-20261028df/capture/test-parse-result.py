#!/usr/bin/env python3
"""Host-only pinned-fixture parser tests. Never root, network, or target I/O."""
import copy
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
from fixture_upgrade import upgrade
module = types.ModuleType('bx_parser_under_test')
module.__file__ = str(HERE / 'parse-result.py')
exec(compile((HERE / 'parse-result.py').read_bytes(), module.__file__, 'exec'), module.__dict__)
FIXTURES = HERE.parents[1] / 'managed-usb-rt-passive-observer/fixtures'
PINS = {
 'accepted-already-faulted.json': '23e1b61b576079bae8283b9a4f5a8fa0af279b7f534dc3d468e04211d6f4fb04',
 'accepted-time-limit.json': 'ad2a5ab505cafeeb7d06eb3b3879c1fb1e1ca6fd418ae5f137a32271eb82dea8',
 'accepted-transition-rend.json': '82d0a786388b459dacdff4e8f41c0fb28e48f27e7d31e36408e2a92039ff27cd',
 'accepted-transition-rstart.json': '4a0df14090e29d0c4e90f63571edf7631ac42f595eac965eca16efcdd5a00309',
}
fixtures = {}
for name, pin in PINS.items():
    raw = (FIXTURES / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError('frozen fixture changed ' + name)
    fixtures[name] = upgrade(json.loads(raw))
checks = 0
rejections = 0


def need(value, why):
    global checks
    if not value:
        raise ValueError(why)
    checks += 1


def encode(value):
    return json.dumps(value, separators=(',', ':')) + '\n'


def state(attempted=True, down=(1300, 1400), up=(1500, 1600)):
    result = {'key': 'Left', 'trigger': 'first-full-clean-cycle', 'attempted': attempted,
              'completed': attempted, 'uiReceiptObserved': False,
              'physicalPictureObserved': False, 'calls': []}
    if attempted:
        result.update(armedUs=1200, endUs=up[1] + 100)
    for phase, times in [('down', down), ('up', up)]:
        call = {'phase': phase, 'started': attempted, 'reaped': attempted,
                'timedOut': False, 'stdoutBytes': 0, 'stderrBytes': 0}
        if attempted:
            call.update(beforeUs=times[0], afterUs=times[1], exitCode=0)
        result['calls'].append(call)
    return result


def wrap(original, attempted=True):
    value = copy.deepcopy(original)
    value.update(schema=module.SCHEMA, observationAccepted=True, accepted=attempted,
                 intervention=state(attempted))
    if attempted:
        base = copy.deepcopy(fixtures['accepted-transition-rstart.json']['retained'][0])
        base['role'] = 'trigger-baseline'
        value['retained'].insert(0, base)
    return value


def transition_rend_cycle_two():
    # Clone frozen captures, with synthetic second-cycle times and matching
    # global counters. No new fixture file or native call is generated.
    old = copy.deepcopy(fixtures['accepted-transition-rend.json'])
    clean = copy.deepcopy(fixtures['accepted-transition-rstart.json']['retained'][0])
    for cap in old['retained']:
        cap['cycleIndex'] = 2
        for t in cap['transfers']:
            t['beforeUs'] += 250000; t['afterUs'] += 250000
    old['retained'].insert(0, clean)
    old.update(cyclesStarted=2, cleanCyclesCompleted=1, cleanCyclesDiscarded=0,
               headersSent=23, bulkTransfers=46, inputsCompleted=23, endUs=252200)
    return wrap(old)


def reject(value, mutation, why):
    global rejections
    bad = copy.deepcopy(value)
    mutation(bad)
    failed = False
    try:
        module.parse_result(encode(bad))
    except (ValueError, KeyError, StopIteration, TypeError):
        failed = True
    need(failed, 'mutation accepted: ' + why)
    rejections += 1


rstart = wrap(fixtures['accepted-transition-rstart.json'])
rend = transition_rend_cycle_two()
time = wrap(fixtures['accepted-time-limit.json'])
for source in (rstart, rend, time):
    before = copy.deepcopy(source)
    value, captures, raw_files, gc, q = module.parse_native(encode(source))
    need(q['transportAccepted'] and q['trialQualified'], 'qualified triggered fixture')
    need(not q['uiReceiptObserved'] and not q['physicalPictureObserved'] and not q['keyCausalityEstablished'], 'no unsupported observation')
    need(captures[0]['role'] == 'trigger-baseline' and captures[0]['cycle'] == 1, 'baseline summary')
    need(captures[0]['rt_states'] == ['Clean', 'Clean'], 'baseline raw-state checks')
    need(len(raw_files) == sum(len(c['windows']) for c in source['retained']), 'raw retention includes duplicate only')
    need(len(set(n for n, _, _ in raw_files)) == len(raw_files), 'unique raw filenames')
    result = module.parse_result(encode(source))
    need(result['globalCounters']['headersSent'] == source['headersSent'] and result['globalCounters']['bulkTransfers'] == source['bulkTransfers'], 'global counters preserved')
    need(source == before, 'caller fixture unmodified')
need(module.parse_result(encode(rstart))['ordering']['classification'] ==
     'first_fault_read_after_down_but_transition_bracket_spans_down', 'after-read alone not causal ordering')
need(module.parse_result(encode(rend))['ordering']['classification'] ==
     'retained_clean_and_fault_reads_after_down_return', 'strictly later clean and fault ordering')
need(module.parse_result(encode(time))['ordering']['classification'] ==
     'no_software_transition_observed', 'clean time-limit classification')

before_down = copy.deepcopy(rstart)
before_down['intervention'] = state(True, (250300, 250400), (250500, 250600))
q = module.parse_result(encode(before_down))
need(q['softwareOnsetObserved'] and q['ordering']['classification'] == 'fault_observed_before_down_dispatch', 'fault before scheduled worker dispatch')
need(q['trialQualified'] and q['keyCausalityEstablished'] is False, 'valid instrument trial is not causal attribution')
overlap = copy.deepcopy(rstart)
overlap['intervention'] = state(True, (250050, 250250), (250300, 250400))
need(module.parse_result(encode(overlap))['ordering']['classification'] == 'first_fault_read_overlaps_down_call', 'overlap classification')
touch = copy.deepcopy(rstart)
touch['intervention'] = state(True, (250200, 250250), (250300, 250400))
need(module.parse_result(encode(touch))['ordering']['firstFaultReadVsDown'] == 'overlaps_or_touches', 'equal boundary not strict ordering')

late_key = copy.deepcopy(rstart)
late_key['endUs'] = 500000
late_key['intervention'] = state(True, (300000,300100), (300200,300300))
result = module.parse_result(encode(late_key))
need(result['transportAccepted'] and result['nativeAccepted'] and not result['trialQualified'], 'late worker EndUs cannot qualify key after USB ends')
need(result['trialRejectionReasons'] == ['keyOutsideObservedWindow'] and
     result['ordering']['classification'] == 'fault_observed_before_down_dispatch', 'late key explicitly qualified negative')
up_after_usb = copy.deepcopy(rstart)
up_after_usb['endUs'] = 300000
up_after_usb['intervention'] = state(True, (250050,250100), (260000,260100))
need(module.parse_result(encode(up_after_usb))['trialQualified'], 'Up cleanup may complete after USB recording stops')
# A later completed M does not replace missing RT coverage after Down.
no_later_r = copy.deepcopy(time)
rolling = no_later_r['retained'][1]
rolling['cycleIndex'] = 79
for transfer in rolling['transfers']:
    transfer['beforeUs'] -= 250000; transfer['afterUs'] -= 250000
part = copy.deepcopy(fixtures['accepted-transition-rstart.json']['retained'][0])
part.update(role='current-partial', cycleIndex=80, windows=part['windows'][:2], transfers=part['transfers'][:4])
for transfer in part['transfers']:
    transfer['beforeUs'] += 19750000; transfer['afterUs'] += 19750000
no_later_r['retained'].append(part)
no_later_r.update(cyclesStarted=80, cleanCyclesCompleted=79, cleanCyclesDiscarded=78,
                 headersSent=634, bulkTransfers=1268, inputsCompleted=634,
                 intervention=state(True, (19750300,19750320), (19750330,19750340)))
result = module.parse_result(encode(no_later_r))
need(result['observationWindow']['downBeginsBeforeOrAtLastReadCompletion'] and
     not result['observationWindow']['completedRPairOverlappingOrAfterDownBegins'] and
     not result['trialQualified'], 'non-R read after Down does not qualify RT observation window')

for name in ('accepted-already-faulted.json', 'accepted-transition-rend.json'):
    value = wrap(fixtures[name], False)
    result = module.parse_result(encode(value))
    need(result['transportAccepted'] and not result['trialQualified'] and not result['nativeAccepted'], 'unarmed transport-only retained')
    need(result['workflowAttempts'] == 0 and not result['baselineDuplicatesCountedCycle'], 'no phantom workflow or baseline')
zero = wrap(fixtures['accepted-time-limit.json'], False)
zero.update(cyclesStarted=0, cleanCyclesCompleted=0, cleanCyclesDiscarded=0,
            headersSent=0, bulkTransfers=0, inputsCompleted=0, retained=[])
need(module.parse_result(encode(zero))['transportAccepted'], 'zero-cycle native-valid unarmed timeout')
partial = copy.deepcopy(zero)
cap = copy.deepcopy(fixtures['accepted-transition-rstart.json']['retained'][0])
cap.update(role='current-partial', windows=cap['windows'][:3], transfers=cap['transfers'][:6])
partial.update(cyclesStarted=1, headersSent=3, bulkTransfers=6, inputsCompleted=3, retained=[cap])
need(module.parse_result(encode(partial))['transportAccepted'], 'unarmed partial first cycle preserved')

# Extension and baseline mutations.
reject(rstart, lambda x: x['retained'].pop(0), 'missing baseline')
reject(rstart, lambda x: x['retained'].insert(0, copy.deepcopy(x['retained'][0])), 'duplicate baseline')
reject(rstart, lambda x: x['retained'].reverse(), 'baseline/retained order')
reject(rstart, lambda x: x['retained'][0].update(cycleIndex=2), 'baseline cycle two')
reject(rstart, lambda x: x['retained'][0]['windows'].pop(), 'partial baseline')
reject(rstart, lambda x: x['retained'][0]['windows'][0].update(sha256='0'*64), 'baseline raw hash')
reject(rstart, lambda x: x['retained'][0]['windows'][0]['observedRtState'].update(classification='Faulted'), 'baseline not clean')
reject(rstart, lambda x: x['retained'][0]['transfers'][1].update(count=255), 'baseline short read')
reject(rstart, lambda x: x['retained'][0]['transfers'][1].update(errno=5), 'baseline errno')
reject(rstart, lambda x: x['retained'][0]['transfers'][0].update(beforeUs=-1), 'baseline before start')
reject(rstart, lambda x: x['retained'][0]['transfers'][0].update(beforeUs=True), 'baseline boolean time')
reject(rstart, lambda x: x['retained'][0]['transfers'][0].update(afterUs=99), 'baseline reverse time')
reject(rstart, lambda x: x['retained'][0]['transfers'][-1].update(afterUs=1300), 'baseline duplicate time mismatch')
reject(rstart, lambda x: x['retained'][0]['windows'][1].update(rawBase64='!'), 'baseline malformed base64')
def mismatch_baseline_raw(value):
    window = value['retained'][0]['windows'][1]
    raw = bytearray(base64.b64decode(window['rawBase64']));raw[0] ^= 1
    window.update(rawBase64=base64.b64encode(raw).decode(), sha256=hashlib.sha256(raw).hexdigest())
reject(rstart, mismatch_baseline_raw, 'valid baseline bytes differ from retained first clean')
reject(time, lambda x: x['retained'][0]['transfers'][-1].update(afterUs=19800000), 'old baseline overlaps rolling clean')
reject(rstart, lambda x: x.update(headersSent=x['headersSent']+6, bulkTransfers=x['bulkTransfers']+12, inputsCompleted=x['inputsCompleted']+6), 'baseline counter double count')
reject(rstart, lambda x: x.update(observationAccepted=False), 'transport acceptance false')
reject(rstart, lambda x: x.update(observationAccepted=1), 'transport acceptance integer')
reject(rstart, lambda x: x.update(accepted=False), 'success native accepted false')
reject(rstart, lambda x: x.update(accepted=1), 'native accepted integer')
reject(rstart, lambda x: x.update(schema='other'), 'wrong native schema')
reject(rstart, lambda x: x.update(extra=True), 'unknown top-level field')
reject(rstart, lambda x: x.update(error='failure'), 'top-level error')
reject(rstart, lambda x: x.update(physicalPictureObserved=True), 'unsupported top-level light')
reject(rstart, lambda x: x['intervention'].update(physicalPictureObserved=True), 'unsupported key light')
reject(rstart, lambda x: x['intervention'].update(uiReceiptObserved=True), 'unsupported UI receipt')
reject(rstart, lambda x: x['intervention'].update(key='Right'), 'wrong key')
reject(rstart, lambda x: x['intervention'].update(trigger='second-cycle'), 'wrong trigger')
reject(rstart, lambda x: x['intervention'].update(attempted=1), 'attempted not bool')
reject(rstart, lambda x: x['intervention'].update(completed=False), 'unfinished key workflow')
reject(rstart, lambda x: x['intervention'].update(error='key failure'), 'workflow error')
reject(rstart, lambda x: x['intervention'].update(armedUs=1199), 'armed before baseline R-end')
reject(rstart, lambda x: x['intervention'].update(armedUs=True), 'armed boolean')
reject(rstart, lambda x: x['intervention'].update(armedUs=250001), 'armed after next-cycle USB')
def arm_after_next_cycle(value):
    value['intervention'] = state(True, (250050,250150), (250200,250300))
    value['intervention']['armedUs'] = 250001
reject(rstart, arm_after_next_cycle, 'otherwise valid key armed after next-cycle USB starts')
reject(rstart, lambda x: x['intervention'].update(endUs=1599), 'workflow end before up return')
reject(rstart, lambda x: x['intervention'].update(endUs=x['endUs']+1), 'workflow end after run')
reject(rstart, lambda x: x['intervention']['calls'].pop(), 'missing up')
reject(rstart, lambda x: x['intervention']['calls'].append(copy.deepcopy(x['intervention']['calls'][1])), 'extra attempt')
for field, bad in [('started', False), ('reaped', False), ('timedOut', True), ('exitCode', 1), ('exitCode', False), ('stdoutBytes', 4097), ('stderrBytes', -1), ('beforeUs', 1199), ('beforeUs', 1300.0), ('afterUs', 1299), ('afterUs', 251201), ('phase', 'up'), ('error', 'failure'), ('extra', 1)]:
    reject(rstart, lambda x, f=field, b=bad: x['intervention']['calls'][0].update({f:b}), 'bad down '+field)
reject(rstart, lambda x: x['intervention']['calls'][1].update(beforeUs=1399), 'up before down completion')
reject(rstart, lambda x: x['retained'][-1]['transfers'][-1].update(afterUs=x['endUs']+1), 'transfer after overall end')
unarmed = wrap(fixtures['accepted-already-faulted.json'], False)
reject(unarmed, lambda x: x['intervention'].update(completed=True), 'phantom completion')
reject(unarmed, lambda x: x.update(accepted=True), 'phantom native success')
reject(unarmed, lambda x: x['intervention']['calls'][0].update(started=True), 'unarmed child started')
reject(unarmed, lambda x: x['intervention']['calls'][0].update(beforeUs=0), 'unarmed timestamp')
reject(unarmed, lambda x: x['retained'].insert(0, copy.deepcopy(rstart['retained'][0])), 'unarmed baseline')

# P/N-specific malformed/cleanup checks on the actual eight-window schema.
for new_name in ('P', 'N'):
    idx = next(i for i,w in enumerate(rstart['retained'][0]['windows']) if w['name'] == new_name)
    reject(rstart, lambda x, i=idx: x['retained'][0]['windows'][i].update(address='0x60000000'), new_name+' arbitrary address')
    reject(rstart, lambda x, i=idx: x['retained'][0]['windows'][i].update(count=0), new_name+' truncated raw count')
    reject(rstart, lambda x, i=idx: x['retained'][0]['windows'][i].update(sha256='0'*64), new_name+' bad hash')
    reject(rstart, lambda x, i=idx: x['retained'][0]['transfers'][2*i+1].update(count=0), new_name+' short IN')
    reject(rstart, lambda x, i=idx: x['retained'][0]['transfers'][2*i].update(name='R-header'), new_name+' wrong header step')
for field in ('released', 'closed', 'claimed', 'opened'):
    reject(rstart, lambda x, f=field: x.update(**{f:False}), 'cleanup/ownership '+field)
reject(rstart, lambda x: x.update(physicalPictureObserved=True), 'forged physical observation')
reject(rstart, lambda x: x['retained'][0]['windows'].reverse(), 'eight-window wrong order')

actual_native = (HERE/'host-native-fixture.json').read_text()
actual_result = module.parse_result(actual_native)
need(actual_result['trialQualified'] and actual_result['globalCounters']['headersSent']==23, 'actual eight-window native engine fixture')
need(all(not actual_result[x] for x in ['physicalPictureObserved','uiReceiptObserved','keyCausalityEstablished']), 'actual fixture preserves no physical/causal observations')
reject(json.loads(actual_native),lambda x:x.update(closed=False),'actual native cleanup failure')

valid_text = encode(rstart)
need(module.parse_result('[GC_INFO] bounded host fixture\n'+valid_text)['gcDiagnosticLines'] == 1, 'bounded GC line permitted')
for text in [valid_text.replace('"accepted":true', '"accepted":false,"accepted":true', 1),
             valid_text.replace('"armedUs":1200', '"armedUs":NaN', 1),
             'unknown line\n'+valid_text, ' '*(module.MAX_BYTES+1), valid_text+valid_text]:
    failed = False
    try:module.parse_result(text)
    except ValueError:failed=True
    need(failed, 'invalid native text accepted');rejections += 1
saved = module.PARENT_SHA
module.PARENT_SHA = '0'*64
try:
    failed = False
    try:module.parse_result(valid_text)
    except ValueError:failed=True
    need(failed, 'parent parser drift accepted');rejections += 1
finally:module.PARENT_SHA = saved
for text, expected in [(valid_text, 0), ('{}\n', 2)]:
    process = subprocess.run([sys.executable, '-B', str(HERE/'parse-result.py')], input=text,
                             capture_output=True, text=True, timeout=10)
    need(process.returncode == expected, 'CLI status')
    data = json.loads(process.stdout if expected == 0 else process.stderr)
    need(data.get('transportAccepted') is (True if expected == 0 else None), 'CLI narrow acceptance')
print(json.dumps({'schema':'synchronized-key-parser-tests-v1','checks':checks,'rejected_mutations':rejections,
                  'frozen_fixtures':len(fixtures),'parent_parser_sha256':saved,
                  'target_operations':0,'network_calls':0,'root_calls':0}))
