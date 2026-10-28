#!/usr/bin/env python3
"""Offline admission plus independent compact/full-window FE decoding."""
import base64
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import struct

HERE = Path(__file__).resolve().parent
FE = HERE.parent
BASE = FE.parent
FC = BASE/'reader-wake-checkpoints-20261028fc'
CAP = FE/'capture-01'
MANIFEST = '16c05204703a377a2f5ce8ec4aeda4028da8fcab85a633a6e488a07f536829c2'
checks = 0


def need(ok, message):
    global checks
    if not ok:
        raise ValueError(message)
    checks += 1


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def u16(raw, at):
    return struct.unpack_from('<H', raw, at)[0]


def u32(raw, at):
    return struct.unpack_from('<I', raw, at)[0]


def main():
    pins = json.loads((HERE/'input-pins.json').read_text())
    for row in pins['files']:
        p = Path(row['path'])
        need(p.is_file() and not p.is_symlink(), 'ordinary frozen input')
        raw = p.read_bytes()
        need(len(raw) == row['bytes'] and digest(raw) == row['sha256'], 'frozen input bytes')
    spec = importlib.util.spec_from_file_location('fe_frozen_admission', FC/'verify-observation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    proof = module.verify(CAP, MANIFEST)
    need(proof == json.loads((FE/'capture-admission.json').read_text()), 'recomputed exact completed admission')
    n = json.loads((CAP/'native.receipt.json').read_text())
    s = n['scoreCheckpoints']
    raw = base64.b64decode(s['rawBase64'], validate=True)
    need(s['recordBytes'] == 58 and s['count'] == 45 and len(raw) == 58*45 and digest(raw) == s['sha256'], 'compact extent/integrity')
    rows = []
    previous = 0
    for i in range(45):
        r = raw[58*i:58*(i+1)]
        need(r[0] in (0, 0x33), 'only complete Clean/Clean or Quiescent/Quiescent rows')
        need(u16(r, 2) == u16(r, 4) == 40, 'both sampled limits40')
        before, after = n['startUs']+u32(r, 24), n['startUs']+u32(r, 28)
        need(previous <= before <= after <= n['endUs'], 'native H read time order')
        previous = after
        rows.append({'cycle':i+1, 'state':'Clean' if r[0] == 0 else 'Quiescent',
                     'c7':r[1], 'h0Low16':u32(r, 6)&65535, 'history':list(struct.unpack_from('<4H', r, 12)),
                     'ordinal0':u32(r, 20), 'hBeforeUs':before, 'hAfterUs':after,
                     'publicationMirror':u16(r, 32), 'trainer':u16(r, 34),
                     'aggregate':u16(r, 36), 'selectorMirror':u16(r, 38),
                     'refreshCounter':u16(r, 40), 'endR60':u16(r, 42),
                     'endR6e':u16(r, 44), 'endRca':u16(r, 54), 'endR68':u16(r, 56)})
    counts = Counter(r['state'] for r in rows)
    need((counts['Clean'], counts['Quiescent']) == (n['cleanCyclesCompleted'], n['quiescentCyclesCompleted']) == (43, 2), 'independent state counters')
    need(n['cyclesStarted'] == 46 and n['headersSent'] == 368 and n['bulkTransfers'] == 736, 'actual cycles and pair counts')
    need(n['terminalReason'] == 'TransitionCaptured' and n['onsetObserved'] is True, 'actual software onset')
    retained = []
    rt = []
    for c in n['retained']:
        entry = {'role':c['role'], 'cycle':c['cycleIndex'], 'windows':[]}
        for i, w in enumerate(c['windows']):
            need(w['complete'] is True, 'retained complete window')
            data = base64.b64decode(w['rawBase64'], validate=True)
            need(len(data) == w['expected'] == w['count'] and digest(data) == w['sha256'], 'retained raw integrity')
            pair = c['transfers'][2*i:2*i+2]
            need(len(pair) == 2 and pair[0]['beforeUs'] <= pair[1]['afterUs'], 'retained pair')
            v = {'name':w['name'], 'beforeUs':pair[0]['beforeUs'], 'afterUs':pair[1]['afterUs']}
            if w['name'] == 'R':
                v['rtTuple'] = [u16(data, x) for x in (0, 10, 14)]
                v['limit'] = u16(data, 196)
                v['loggerHalfword'] = u16(data, 6)
                need(v['limit'] == 40 and v['loggerHalfword'] == 0, 'original threshold and no event logger armed')
                rt.append(dict(v, role=c['role'], cycle=c['cycleIndex']))
            elif w['name'] == 'H':
                v.update(h0Low16=u32(data, 4)&65535, history=list(struct.unpack_from('<4H', data, 40)))
                if c['role'] in ('trigger-baseline', 'last-clean'):
                    row = rows[c['cycleIndex']-1]
                    need(v['h0Low16'] == row['h0Low16'] and v['history'] == row['history'] and v['beforeUs'] == row['hBeforeUs'] and v['afterUs'] == row['hAfterUs'], 'full H/compact agreement')
            elif w['name'] == 'M':
                v.update(aa=u16(data, 10), ac=u16(data, 12), scan=data[56], root=u32(data, 64), publicationMirror=u16(data, 42))
            elif w['name'] == 'C':
                v['c7'] = data[7]
            entry['windows'].append(v)
        retained.append(entry)
    clean = [r for r in rt if r['rtTuple'] == [0, 0, 1]][-1]
    fault = [r for r in rt if r['rtTuple'] == [1, 4097, 0]][0]
    need(clean['cycle'] == 45 and fault['cycle'] == 46 and clean['afterUs'] < fault['beforeUs'], 'ordered clean/fault samples')
    timing = {'lastCleanRHeaderBeforeUs':clean['beforeUs'], 'lastCleanRDataAfterUs':clean['afterUs'],
              'firstFaultRHeaderBeforeUs':fault['beforeUs'], 'firstFaultRDataAfterUs':fault['afterUs'],
              'conservativeSoftwareReadBracketUs':fault['afterUs']-clean['beforeUs'],
              'nativeObservationSpanUs':n['endUs']-n['startUs'],
              'medianHStartSpacingUs':statistics.median(rows[i]['hBeforeUs']-rows[i-1]['hBeforeUs'] for i in range(1,len(rows))),
              'scope':'Sequential software read brackets, not controller instruction or physical blackout timestamps.'}
    cp = json.loads((CAP/'wake-checkpoint.json').read_text())
    ui = json.loads((FE/'after-capture-ui/result.json').read_text())['after']
    need(ui['cached_current_tab'] == 'd/ug.tab@Live', 'separate later cached Live')
    transitions = []
    for row in rows:
        key = [row[k] for k in ('state','c7','refreshCounter','aggregate','endRca')]
        if not transitions or transitions[-1]['stateVector'] != key:
            transitions.append({'cycle':row['cycle'], 'stateVector':key})
    out = {'schema':'fe-independent-scientific-decode-v1', 'checks':checks,
           'admissionAccepted':True, 'headers':368, 'bulks':736, 'compactRows':45,
           'cleanRows':43, 'quiescentRows':2, 'quiescentCycles':[r['cycle'] for r in rows if r['state']=='Quiescent'],
           'maximumCompactH0Low16':max(r['h0Low16'] for r in rows), 'rows':rows,
           'retained':retained, 'observedStateChanges':transitions, 'timing':timing,
           'hostQueryReturnToRootDispatchAttemptNs':cp['hostSubmissionAgeNs'],
           'laterCachedTab':ui['cached_current_tab'], 'actualFPObserved':False,
           'actualSelectedAOrCallerObserved':False, 'physicalPictureObserved':False,
           'targetOperations':0, 'limitations':['Full context exists only in retained windows; compact fields are sequential.',
               'Event logging was off in retained R samples. No event argument or caller LR was captured.',
               'No subtraction across host monotonic, native Stopwatch and remote uptime clocks.',
               'No claim of equal rendered scene, key consumption, comparator execution time or physical prevention.']}
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
