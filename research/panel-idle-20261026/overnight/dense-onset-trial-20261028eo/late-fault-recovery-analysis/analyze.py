#!/usr/bin/env python3
"""Pinned EO retained-file analysis; no target adapter import or command replay."""
import base64
import copy
import hashlib
import json
import re
import struct
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
EO = HERE.parent
B = EO.parent
EB = B / 'rtp-lane-gate-capture-20261028eb'
DR = B / 'rtp-fixed-reference-qualification-20261028dr'
checks = 0
negative_cases = 0

def need(ok, why):
    global checks
    checks += 1
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def strict(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'duplicate JSON field')
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))

def j(path):
    # Duplicate/nonfinite checks come from the frozen strict parser below for
    # capture inputs. This helper is also used before any module is loaded.
    return strict(path.read_bytes())

def module(path, digest, name):
    raw = path.read_bytes()
    need(sha(raw) == digest, 'frozen module pin')
    value = types.ModuleType(name)
    value.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), value.__dict__)
    return value

def inventory(root, digest):
    raw = (root / 'source-inventory.json').read_bytes()
    need(sha(raw) == digest, 'frozen source inventory')
    rows = j(root / 'source-inventory.json')['files']
    for row in rows:
        data = (root / row['path']).read_bytes()
        need(len(data) == row['bytes'] and sha(data) == row['sha256'], 'inventoried source bytes')
    return len(rows)

def rejected(fn):
    global negative_cases
    try:
        fn()
    except (ValueError, KeyError, TypeError):
        negative_cases += 1
        need(True, 'malformed input refused')
        return
    raise ValueError('malformed input unexpectedly accepted')

def u16(raw, at):
    return struct.unpack_from('<H', raw, at)[0]

def decode68(raw, xbase=0):
    need(type(raw) is bytes and len(raw) == 104 and type(xbase) is int and xbase == 0, 'qualified fixed extent and xbase')
    values = []
    for at in range(0, 102, 6):
        word, tail = struct.unpack_from('<IH', raw, at)
        values.extend((word & 0xfff, (word >> 12) & 0xfff,
                       (word >> 24) | ((tail & 15) << 8), tail >> 4))
    need(len(values) == 68, 'all seventeen complete packed groups')
    return {str(568 + i): value for i, value in enumerate(values)}

def candidates(b, difference):
    need(type(b) is int and type(difference) is int and 0 <= b <= 4095 and 0 <= difference <= 4095, 'conditional twelve-bit premise')
    return sorted({value for value in (b - difference, b + difference) if 0 <= value <= 4095})

def result_contract(result, raw_rows, manifest_raw, ready_raw):
    need(type(result) is dict and result['schema'] == 'eb-rtp-lane-gate-wrapper-result-v1' and result['accepted'] is True, 'original accepted wrapper result')
    for field, expected in [('headersSent', 16), ('bulkTransfers', 32), ('nativeInvocations', 1), ('retries', 0), ('wrapperUiOperations', 0)]:
        need(type(result[field]) is int and result[field] == expected, 'exact wrapper count ' + field)
    need(result['operation'] == 'fixed_read_only_record_capture' and result['cleanup'] == 'STAGE_ABSENT', 'read-only operation and exact cleanup')
    for field in ['endpointQueueProof', 'identitySnapshotsAtomic', 'physicalPictureObserved', 'rootCauseFixEstablished', 'automaticRestore', 'diagnosticStdoutIsSemanticReceipt']:
        need(result[field] is False, 'limited claim ' + field)
    need(result['structuredReceipt'] == 'exclusive_private_file', 'structured receipt source')
    need(result['manifestSha256'] == sha(manifest_raw) and result['readinessSha256'] == sha(ready_raw), 'wrapper input binding')
    need(type(result['rawFiles']) is list and len(result['rawFiles']) == 16, 'sixteen raw inventory rows')
    for actual, (name, raw, digest) in zip(result['rawFiles'], raw_rows):
        need(type(actual) is dict and set(actual) == {'name', 'bytes', 'sha256'} and type(actual['bytes']) is int, 'typed raw inventory row')
        need(actual == {'name': name, 'bytes': len(raw), 'sha256': digest}, 'canonical ordered raw inventory')

def capture(label, wrapper, parser, manifest_raw):
    root = EO / 'trial-01' / label
    result = parser.strict_json((root / 'result.json').read_text())
    native, raws, interpretation = parser.parse_native((root / 'native.receipt.json').read_text())
    ready, ready_raw = wrapper.load_readiness(root / 'readiness-decision.json', result['readinessSha256'])
    need(str(native['device']) == ready['identity']['devnum'], 'native device matches exact admitted identity')
    need((root / 'reviewed-manifest.json').read_bytes() == manifest_raw, 'same exact frozen EB manifest')
    result_contract(result, raws, manifest_raw, ready_raw)
    need(interpretation == parser.strict_json((root / 'interpretation.json').read_text()), 'saved interpretation exactly reproduced')
    record = parser.strict_json((root / 'record.json').read_text())
    need(type(record['native_invocations']) is int and record['native_invocations'] == 1 and record['target_operations'] == 16 and record['no_retry'] is True, 'one original native invocation')
    need(record['manifestSha256'] == result['manifestSha256'] and record['readinessSha256'] == result['readinessSha256'], 'record input binding')
    need(record['cleanup_required'] is False and record['cleanup_stdout'] == 'STAGE_ABSENT\n', 'original cleanup receipt')
    need(record['retained_raw_files'] == result['rawFiles'], 'record and result raw inventory identical')
    for tag in ['selftest', 'native']:
        envelope = (root / (tag + '-envelope.txt')).read_text()
        if tag == 'native':
            need(envelope.startswith('IMMEDIATE_READY\n'), 'same-command immediate metadata marker')
            envelope = envelope[len('IMMEDIATE_READY\n'):]
        terminal, receipt, stdout, stderr = wrapper.receipt_envelope(envelope)
        need(terminal == record[tag + 'Terminal'] and terminal['exit_code'] == 0, 'saved original terminal')
        for suffix, raw in [('receipt.json', receipt), ('stdout', stdout), ('stderr', stderr)]:
            need((root / (tag + '.' + suffix)).read_bytes() == raw, 'envelope to saved blob binding')
        need(stderr == b'' and record[tag + 'DiagnosticStdout'] == {'bytes': len(stdout), 'sha256': sha(stdout), 'semanticReceipt': False}, 'opaque diagnostics preserved')
        if tag == 'selftest':
            need(parser.strict_json(receipt.decode()) == {'selfTestsPassed': 2071, 'targetOperations': 0}, 'accepted zero-I/O fake selftest')
    data = {}
    for name, raw, digest in raws:
        need((root / name).read_bytes() == raw and sha(raw) == digest, 'native receipt to retained raw file binding')
        data[name] = raw
    for row in ready['evidence']:
        need(sha(Path(row['path']).read_bytes()) == row['sha256'], 'saved readiness evidence unchanged')
    for label_marker, name, field in [('PRE_READY', 'metadata-pre.txt', 'preCensus'), ('BEFORE_INVOKE_READY', 'metadata-before-invoke.txt', 'beforeInvokeCensus'), ('POST_READY', 'metadata-post.txt', 'postCensus')]:
        need(wrapper.parse_metadata((root / name).read_text(), label_marker) == record[field], 'saved cached census binding')
    # No transport mock replay: inspect the already retained request/response
    # bindings directly, never load or call the root transport module.
    need(len(record['calls']) == 28, 'retained orchestration count')
    envelope_responses = []
    for call in record['calls']:
        need(type(call['command_bytes']) is int and call['command_bytes'] == len(call['command'].encode()) <= 8192, 'saved command length')
        need(call['transport_exit'] == 0 and call['host_timeout'] is False and call['remote_timeout_seconds'] == 45 and call['host_timeout_limit_seconds'] == 75, 'saved transport completion and bounds')
        def blob(value):
            need(type(value) is dict and set(value) == {'encoding', 'data'} and value['encoding'] == 'base64', 'saved blob schema')
            raw = base64.b64decode(value['data'], validate=True)
            need(base64.b64encode(raw).decode() == value['data'], 'saved blob canonical encoding')
            return raw
        need(blob(call['transport_stderr']) == b'', 'saved transport stderr')
        response_raw = blob(call['transport_stdout'])
        need(len(response_raw) <= 65536 and parser.strict_json(response_raw.decode()) == call['response'], 'saved response exact JSON')
        response = call['response']
        need(response['authenticated'] is True and response['uid'] == response['euid'] == 0 and len(response['commands']) == 1, 'saved authenticated root receipt')
        command = response['commands'][0]
        need(command['command'] == call['command'] and command['exit_code'] == 0 and command['timed_out'] is False and command['stderr'] == '', 'saved root command echo/status')
        if 'EPMETA_BEGIN' in command['stdout']:
            raise ValueError('unrelated EP data outside EO scope')
        if 'EBMETA_BEGIN\n' in command['stdout']:
            envelope_responses.append(command['stdout'])
    need(envelope_responses == [(root / 'selftest-envelope.txt').read_text(), (root / 'native-envelope.txt').read_text()], 'two original envelopes bound to retained root responses')
    fixed = {side: decode68(data['fixed-' + side + '-candidate.bin'], interpretation['sourceContext']['xBase']) for side in ['top', 'bottom']}
    for side in ['top', 'bottom']:
        need(all(fixed[side][key] == value for key, value in interpretation['fixedReferenceCandidates'][side].items()), 'legacy eight-lane output agrees with full decoder')
    columns = {name: list(struct.unpack('<48H', data[name + '.bin'])) for name in ['X', 'Y', 'RGB', 'B', 'Diff']}
    n_counts = lambda raw: {'ordinals': list(struct.unpack_from('<6I', raw)), 'sourceCounts': list(struct.unpack_from('<6H', raw, 24))}
    rt = lambda raw: {'rt': [u16(raw, 0), u16(raw, 10), u16(raw, 14)], 'alternateLimit': u16(raw, 0xc4), 'mode1RecordLatch': u16(raw, 0x90), 'operatingMode': u16(raw, 16)}
    m, r, c = data['M.bin'], data['start-R.bin'], data['C.bin']
    summary = {'label': label, 'strictParserAccepted': True, 'headers': 16, 'bulks': 32, 'stageAbsent': True,
               'startR': rt(r), 'endR': rt(data['end-R.bin']), 'startN': n_counts(data['start-N.bin']), 'endN': n_counts(data['end-N.bin']),
               'rBytesEqual': data['start-R.bin'] == data['end-R.bin'], 'nBytesEqual': data['start-N.bin'] == data['end-N.bin'],
               'sampledControls': {'trainer4a2': u16(m, 2), 'aggregate4a4': u16(m, 4), 'selectorMirror4c2': u16(m, 34), 'refreshCounter4c4': u16(m, 36), 'selectorC7': c[7], 'writer2460': u16(r, 0x60), 'publisher246e': u16(r, 0x6e), 'aa': u16(m, 10), 'ac': u16(m, 12), 'publicationBoundMirror': u16(m, 42)},
               'primaryNonzeroWords': sum(value != 0 for value in struct.unpack('<68H', data['primary-lane-gate.bin'])),
               'secondaryNonzeroBytes': sum(value != 0 for value in data['secondary-lane-gate.bin']),
               'all68LocallyAdmittedAtSample': all(row['locallyAdmittedByCapturedTables'] is True for row in interpretation['laneGateSamples']),
               'fixed68': fixed, 'columns48': columns,
               'nonzeroColumnHalfwords': {name: sum(value != 0 for value in values) for name, values in columns.items()},
               'fixed104AllZero': {side: not any(data['fixed-' + side + '-candidate.bin']) for side in ['top', 'bottom']},
               'readBrackets': interpretation['readBrackets'], 'snapshotFirstHeaderBeforeUs': native['steps'][0]['beforeUs'], 'snapshotLastDataAfterUs': native['steps'][-1]['afterUs'],
               'sourceContext': interpretation['sourceContext'], 'epochProven': False, 'physicalPictureObserved': False}
    return summary, data, native, result, ready

def analyze():
    pins = j(HERE / 'input-pins.json')['files']
    need(len({row['path'] for row in pins}) == len(pins), 'unique fixed input selection')
    for row in pins:
        raw = (B / row['path']).read_bytes()
        need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'immutable selected input pin')
    source_files = inventory(EB, '271061f8c60ee75f219b56217ac6dfcf3aa13616d67c3d4f54e46f655c13bdec')
    inventory(DR, '75aa8520f9a0de3da3e05a42434f00215b892e1de482dcb2b25017a0fcd5c22c')
    inventory(EO / 'refusal-analysis', '62c2b6e013f67685b3de644816866afc3671c34a0ad0194f7cdcb43066bf9dd1')
    wrapper = module(EB / 'run-once.py', '886bdc05bb8eb5a255443f95a964f2bae947fc758b18ea0e4893f42c3e4ad9a8', 'eo_late_offline_wrapper')
    parser = module(EB / 'parse-result.py', 'e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523', 'eo_late_offline_parser')
    manifest, _ = wrapper.build_manifest()
    manifest_raw = wrapper.manifest_bytes(manifest)
    need(manifest_raw == (EB / 'deployment-manifest.json').read_bytes() and sha(manifest_raw) == 'e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11', 'regenerated frozen manifest')
    parsed = {name: capture(name, wrapper, parser, manifest_raw) for name in ['baseline', 'after-refusal-tables', 'recovery-validation']}
    baseline, fault, clean = [parsed[name][0] for name in ['baseline', 'after-refusal-tables', 'recovery-validation']]
    need(all(s['startR']['alternateLimit'] == s['endR']['alternateLimit'] == 40 for s in [baseline, fault, clean]), 'original alternate limit40 throughout')
    need(baseline['startR']['rt'] == clean['startR']['rt'] == [0, 0, 1] and fault['startR']['rt'] == [1, 0x1001, 0], 'separate clean/fault/clean classification')
    need(fault['startR']['mode1RecordLatch'] == fault['endR']['mode1RecordLatch'] == 41, 'fault root latch41 is not an H score')
    need(all(s['startN']['sourceCounts'] == s['endN']['sourceCounts'] == [0] * 6 for s in [baseline, fault, clean]), 'all sampled source counts zero')
    need(fault['startN']['ordinals'] == fault['endN']['ordinals'] == [41, 0, 0, 0, 0, 0], 'fault ordinal41 retained separately from zero current counts')
    need(all(s['primaryNonzeroWords'] == s['secondaryNonzeroBytes'] == 0 for s in [baseline, fault, clean]), 'all three tables zero at their samples')
    records, groups = [], {}
    columns = fault['columns48']
    for i in range(48):
        row = {name.lower(): columns[name][i] for name in columns}
        row['index'] = i
        row['conditional12bitA'] = None
        if row['x'] != 0:
            need(row['y'] == 2159 and row['rgb'] == 0 and 568 <= row['x'] < 636 and row['diff'] > 0, 'bounded terminal-row RGB0 candidate')
            possible = candidates(row['b'], row['diff'])
            need(len(possible) == 1, 'unique conditional signed absolute-difference solution')
            value = possible[0]
            row.update(conditional12bitA=value, sign='B+Diff' if value == row['b'] + row['diff'] else 'B-Diff', bottomMatches=value == fault['fixed68']['bottom'][str(row['x'])], topMatches=value == fault['fixed68']['top'][str(row['x'])])
            need(row['bottomMatches'] is True and row['topMatches'] is False, 'all conditional candidates match bottom and differ from top')
            key = str(row['x'])
            groups.setdefault(key, {'indices': [], 'conditionalA': value, 'top': fault['fixed68']['top'][key], 'bottom': fault['fixed68']['bottom'][key], 'signs': [], 'bValues': [], 'diffValues': []})
            group = groups[key]
            need(group['conditionalA'] == value, 'same x gives stable conditional A')
            for key2, value2 in [('indices', i), ('bValues', row['b']), ('diffValues', row['diff'])]:
                group[key2].append(value2)
            if row['sign'] not in group['signs']:
                group['signs'].append(row['sign'])
        records.append(row)
    need([row['index'] for row in records if row['conditional12bitA'] is not None] == list(range(41)), '41 candidate-coordinate rows, not a proved current prefix')
    need(sorted(map(int, groups)) == [570, 571, 620, 621, 624, 625, 630, 631], 'changed coordinates use full68 decoder')
    need(groups['630']['signs'] == groups['631']['signs'] == ['B-Diff'] and groups['630']['conditionalA'] == 2990, 'high-rail B4095 subtraction case')
    need(all(clean['fixed104AllZero'].values()) and all(baseline['fixed104AllZero'].values()), 'both complete104-byte fixed windows zero in the two Apps samples')
    need(clean['nonzeroColumnHalfwords']['X'] == clean['nonzeroColumnHalfwords']['Y'] == 48 and clean['nonzeroColumnHalfwords']['RGB'] == 26 and clean['nonzeroColumnHalfwords']['B'] == 24 and clean['nonzeroColumnHalfwords']['Diff'] == 0, 'clean recovery is not all-record-RAM clear')
    original = j(EO / 'trial-01/result.json')
    em = j(EO / 'trial-01/onset/native.receipt.json')
    classifier = j(EO / 'refusal-analysis/decoded.json')
    need(sha((EO / 'refusal-analysis/decoded.json').read_bytes()) == '721df4c000c863eb9b5295eeb5a5748c2933e32cb8ea9008b8811e5e13e06f7b', 'earlier frozen refusal classification')
    need(original['accepted_pair'] is False and original['phase'] == 'stopped' and em['accepted'] is False and em['terminalReason'] == 'UnexpectedRt', 'original EM/wrapper refusal preserved')
    need(classifier['latestUnexpectedR']['rt'] == [0, 0, 0] and classifier['nativeTiming']['physicalOrFaultOnsetTimestampProven'] is False, 'earlier invalid RT is not later 0x1001 onset')
    need(em['headersSent'] == 145 and em['bulkTransfers'] == 290 and em['protocolPhase'] == 'ReadyForHeader' and em['released'] is True and em['closed'] is True, 'earlier exact completed read phase')
    em_ready = j(EO / 'trial-01/onset/readiness-decision.json')
    need(em_ready['identity'] == parsed['after-refusal-tables'][4]['identity'] == parsed['baseline'][4]['identity'], 'earlier EM and later fault EB share the exact saved instance identity')
    last_em_in = max(t['afterUs'] for cap in em['retained'] for t in cap['transfers'] if t['direction'] == 'IN')
    gap = fault['snapshotFirstHeaderBeforeUs'] - last_em_in
    need(gap > 0, 'positive later native-clock gap')
    cleanup = j(EO / 'trial-01/onset-cleanup/result.json')
    need(cleanup['accepted'] is True and cleanup['exactStageRemoved'] is True and cleanup['removedFiles'] == 9 and cleanup['originalWrapperRejectionPreserved'] is True and cleanup['proofSha256'] == sha((EO / 'refusal-analysis/decoded.json').read_bytes()), 'separate exact cleanup proof')
    need(all(type(cleanup[k]) is int and cleanup[k] == 0 for k in ['additionalVendorTransfers', 'writes', 'uiCalls', 'resets', 'retries']), 'cleanup added no vendor/UI/reset action')
    withheld = j(EO / 'trial-01/fault-recovery/result.json')
    prep = j(EO / 'trial-01/recovery-apps-preparation/result.json')
    recovery = j(EO / 'trial-01/fault-recovery-02/result.json')
    mode2 = j(EO / 'trial-01/fault-recovery-02/mode2/result.json')
    need(withheld['accepted'] is False and type(withheld['mode2_invocations']) is int and withheld['mode2_invocations'] == 0, 'first recovery withheld MODE2')
    need(withheld['before']['screensaver_windows_present'] is True and withheld['after_right']['screensaver_windows_present'] is False and withheld['before']['cached_current_tab'] == withheld['after_right']['cached_current_tab'] == 'd/ug.tab@Live', 'Right dismissed saver without reaching Apps')
    need(prep['accepted'] is True and prep['vendor_operations'] == 0 and prep['threshold_writes'] == 0 and prep['key_retries'] == 0, 'separate ordinary Apps preparation')
    need(recovery['accepted'] is True and type(recovery['mode2_invocations']) is int and recovery['mode2_invocations'] == 1 and recovery['automatic_retries'] == recovery['threshold_writes'] == 0, 'second guarded workflow exactly one unchanged MODE2')
    need(mode2 == recovery['recovery'] and mode2['accepted'] is True and mode2['request_count'] == 1 and mode2['helper_exit'] == 0 and mode2['cleanup_confirmed'] is True, 'accepted MODE2 child result')
    receipt = (EO / 'trial-01/fault-recovery-02/mode2/receipt.txt').read_bytes()
    need(sha(receipt) == mode2['receipt_sha256'], 'stock request receipt hash')
    for line in ['OPERATION_DECIMAL=41', 'MODE_DECIMAL=2', 'IOCTL_RETURN=0', 'CLOSE_RETURN=0', 'CLASSIFICATION=kernel_return_zero_only', 'POWER_ACTION_ACKNOWLEDGED=0', 'RECOVERY_INFERRED=0', 'PHYSICAL_STATE_INFERRED=0']:
        need(receipt.decode().splitlines().count(line) == 1, 'stock request limited receipt ' + line)
    identity = j(EO / 'trial-01/after-recovery-identity/instance-check.json')
    need(identity['accepted'] is True and identity['old_device'] == 61 and identity['new_device'] == 62 and identity['same_boot'] is True and identity['same_descriptors'] is True and identity['positive_disconnect_then_enumeration'] is True and identity['vendor_operations'] == 0, 'retained positive new-instance proof')
    for row in identity['inputs']:
        need(sha(Path(row['path']).read_bytes()) == row['sha256'], 'new-instance proof input')
    before_id, after_id = parsed['after-refusal-tables'][4]['identity'], parsed['recovery-validation'][4]['identity']
    need(before_id['boot'] == after_id['boot'] and before_id['descriptorsSha256'] == after_id['descriptorsSha256'] and before_id['devnum'] == '61' and after_id['devnum'] == '62', 'actual capture identities same boot/descriptors, new device')
    text = (EO / 'trial-01/after-recovery-identity/metadata.txt').read_text()
    disconnect = re.search(r'\[([0-9.]+)\].*USB disconnect,.*device number 61>', text)
    enumeration = re.search(r'\[([0-9.]+)\].*new high-speed USB device number 62', text)
    need(disconnect is not None and enumeration is not None and float(disconnect.group(1)) < float(enumeration.group(1)), 'positive ordered kernel disconnect/enumeration lines')
    # Independent bitstream decoder and all816 meaningful bit positions. The
    # final two alignment bytes are intentionally never interpreted as lanes.
    for summary, data, *_ in parsed.values():
        for side in ['top', 'bottom']:
            raw = data['fixed-' + side + '-candidate.bin']
            stream = int.from_bytes(raw[:102], 'little')
            expected = {str(568 + i): (stream >> (12 * i)) & 4095 for i in range(68)}
            need(summary['fixed68'][side] == expected, 'independent all68 contiguous bitstream decoder')
            for tail in [b'\x00\x00', b'\xff\xff', b'\x55\xaa']:
                need(decode68(raw[:102] + tail) == expected, 'two ignored tail bytes cannot change a lane')
    for bit in range(816):
        raw = (1 << bit).to_bytes(102, 'little') + b'\xff\xff'
        values = decode68(raw)
        need(values == {str(568 + i): (1 << (bit % 12)) if i == bit // 12 else 0 for i in range(68)}, 'every meaningful packed bit maps to the exact lane')
    for raw in [bytes(102), bytes(103), bytes(105), bytes(106)]:
        rejected(lambda raw=raw: decode68(raw))
    for xbase in [True, 1, -1, None]:
        rejected(lambda xbase=xbase: decode68(bytes(104), xbase))
    bad_native = parsed['after-refusal-tables'][2]
    for index in range(16):
        bad = copy.deepcopy(bad_native)
        bad['windows'][index]['sha256'] = '0' * 64
        rejected(lambda bad=bad: parser.parse_native(json.dumps(bad)))
    for index in range(32):
        bad = copy.deepcopy(bad_native)
        bad['steps'][index]['count'] = -1
        rejected(lambda bad=bad: parser.parse_native(json.dumps(bad)))
    for field, value in [('accepted', False), ('headersSent', True), ('bulkTransfers', 31), ('released', False), ('closed', False)]:
        bad = copy.deepcopy(bad_native)
        bad[field] = value
        rejected(lambda bad=bad: parser.parse_native(json.dumps(bad)))
    original_result = parsed['after-refusal-tables'][3]
    originals_raw = parser.parse_native((EO / 'trial-01/after-refusal-tables/native.receipt.json').read_text())[1]
    ready_raw = (EO / 'trial-01/after-refusal-tables/readiness-decision.json').read_bytes()
    for field, value in [('accepted', 1), ('headersSent', True), ('bulkTransfers', 31), ('nativeInvocations', 2), ('cleanup', 'UNKNOWN')]:
        bad = copy.deepcopy(original_result)
        bad[field] = value
        rejected(lambda bad=bad: result_contract(bad, originals_raw, manifest_raw, ready_raw))
    for index in range(16):
        bad = copy.deepcopy(original_result)
        bad['rawFiles'][index]['sha256'] = '0' * 64
        rejected(lambda bad=bad: result_contract(bad, originals_raw, manifest_raw, ready_raw))
    for invalid in ['{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}']:
        rejected(lambda invalid=invalid: parser.strict_json(invalid))
    need(not any(str(getattr(value, '__file__', '')).endswith('managed-ui-tab-launch/root-with-margin.py') for value in sys.modules.values()), 'no real root adapter imported')
    return {'schema': 'eo-independent-late-fault-recovery-v1', 'checks': checks, 'inputFiles': len(pins), 'negativeCasesRejected': negative_cases,
            'sourceProvenance': {'ebInventorySha256': sha((EB / 'source-inventory.json').read_bytes()), 'ebSourceFilesVerified': source_files, 'packedModelInventorySha256': sha((DR / 'source-inventory.json').read_bytes()), 'fixedWindowBytes': 104, 'completeDecodeBytes': 102, 'ignoredTailBytes': 2, 'firstLane': 568, 'completeLanes': 68, 'sourceFormula': 'u32+u16 little endian: w&fff,(w>>12)&fff,(w>>24)|((t&f)<<8),t>>4'},
            'captures': {name: value[0] for name, value in parsed.items()}, 'faultCandidateRows': records, 'conditionalGroups': groups,
            'conditionalPremises': ['same epoch across sequential X/Y/RGB/B/Diff', 'record type1 absolute difference', 'both amplitudes are unsigned12bit', 'captured fixed references comparable to historical A'],
            'candidateBottomMatches': 41, 'candidateTopMismatches': 41, 'candidateCurrentPrefixProven': False,
            'earlierRejectedEm': {'originalWrapperAccepted': False, 'nativeAccepted': False, 'terminal': 'UnexpectedRt', 'rt': [0, 0, 0], 'headers': 145, 'bulks': 290, 'lastCompletedInUs': last_em_in, 'cleanCycles': 18, 'laterEbIsNotAcceptancePromotion': True, 'separateNineFileCleanupAccepted': True, 'cleanupAdditionalVendorTransfers': 0},
            'timing': {'laterEbFirstHeaderUs': fault['snapshotFirstHeaderBeforeUs'], 'gapFromLastRejectedEmInUs': gap, 'gapIsNotFaultOnsetBracket': True, 'sameSavedBootAndNativeTimebase': True, 'faultAndRecoverySnapshotsSequentialNotAtomic': True},
            'recovery': {'firstGuardAccepted': False, 'firstGuardMode2Requests': 0, 'rightOnlyDismissedSaverCachedLiveRemained': True, 'separateOrdinaryAppsPreparationAccepted': True, 'secondGuardAccepted': True, 'secondGuardMode2Requests': 1, 'stockIoctlReturnZeroOnly': True, 'sameBootNewUsbInstancePositivelyObserved': True, 'newInstanceOldNumber': 61, 'newInstanceNewNumber': 62, 'validationAccepted': True, 'validationCleanRt': [0, 0, 1], 'alternateLimit': 40, 'validationMode1Latch': 0, 'recordArraysAllZero': False, 'fixed104WindowsAllZero': True, 'thresholdWrites': 0, 'physicalPictureObserved': False},
            'validationScope': 'Strict frozen EB/parser/envelope/result/raw-file/inventory bindings plus retained root-response inspection. No old transport command regeneration/mock replay and no native or target execution.',
            'claims': {'recordEpochProven': False, 'historicalSelectedABranchProven': False, 'historicalGateExecutionProven': False, 'actualComparatorCallProven': False, 'opticalStateProven': False, 'allRamResetProven': False, 'instructionReloadProven': False, 'rootCauseOrFixEstablished': False, 'endpointQueueProof': False},
            'targetOperations': 0, 'networkOperations': 0}

if __name__ == '__main__':
    result = analyze()
    raw = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
    if sys.argv[1:] == ['--record']:
        with (HERE / 'decoded.json').open('xb') as out:
            out.write(raw)
        (HERE / 'decoded.json').chmod(0o600)
    elif sys.argv[1:] == ['--check']:
        need((HERE / 'decoded.json').read_bytes() == raw, 'exact frozen analysis reproduction')
    else:
        raise SystemExit('usage: analyze.py --record|--check')
    print(json.dumps({'accepted': True, 'checks': checks, 'negativeCasesRejected': negative_cases, 'inputFiles': result['inputFiles'], 'conditionalBottomMatches': 41, 'decodedSha256': sha(raw), 'targetOperations': 0, 'networkOperations': 0}, sort_keys=True))
