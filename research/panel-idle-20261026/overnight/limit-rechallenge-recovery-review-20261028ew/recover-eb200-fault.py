#!/usr/bin/env python3
"""Fixed200 EB fault admission and one existing Apps-selected stock recovery.

Dry by default. No USB read/write implementation, DV restore, reset retry,
new MODE2 payload, threshold-reset assumption or physical inference.
"""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

B = Path(__file__).resolve().parent.parent
PARSER_SHA = 'e44f4c96989f895ec8ce8d1f72c9a1d8c1423a28cc1ec5358a885bd9f38d4523'
WRAPPER_SHA = '886bdc05bb8eb5a255443f95a964f2bae947fc758b18ea0e4893f42c3e4ad9a8'
MANIFEST_SHA = 'e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11'
GATES_SHA = '4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f'
NAV_SHA = '74b60a9611f35a76d272b33677f773cc955838c2c6dda2c3565c371cc9d4d530'
HELPER_SHA = 'a838433923e0a6bce7a8c6b3ef810c2d4703d3a5a1061f436f93d4c7e63c5551'
RESULT_FIELDS = {'schema','accepted','operation','headersSent','bulkTransfers','rawFiles','manifestSha256','readinessSha256','endpointQueueProof','identitySnapshotsAtomic','physicalPictureObserved','rootCauseFixEstablished','automaticRestore','wrapperUiOperations','nativeInvocations','retries','cleanup','structuredReceipt','diagnosticStdoutIsSemanticReceipt'}

def need(ok, why):
    if not ok:
        raise ValueError(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load(path, pin, name):
    need(not path.is_symlink() and sha(path.read_bytes()) == pin, name + ' frozen source')
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def read(path, cap):
    need(not path.is_symlink() and path.is_file(), 'regular local artifact required')
    with path.open('rb') as stream:
        raw = stream.read(cap + 1)
    need(len(raw) <= cap, 'artifact extent')
    return raw

def validate_capture(capture, result_pin, record_pin):
    """Offline only. Caller separately seals actual result and original root record."""
    need(capture.is_absolute() and capture.is_dir() and not capture.is_symlink(), 'absolute capture directory')
    need(all(type(x) is str and re.fullmatch('[0-9a-f]{64}', x) for x in (result_pin, record_pin)), 'two exact capture digests')
    wrapper = load(B/'rtp-lane-gate-capture-20261028eb/run-once.py', WRAPPER_SHA, 'ew_eb_wrapper')
    parser = load(B/'rtp-lane-gate-capture-20261028eb/parse-result.py', PARSER_SHA, 'ew_eb_parser')
    result_raw, record_raw = read(capture/'result.json', 16384), read(capture/'record.json', 2000000)
    need(sha(result_raw) == result_pin and sha(record_raw) == record_pin, 'sealed actual capture binding')
    result, record = wrapper.strict_json(result_raw), wrapper.strict_json(record_raw)
    need(type(result) is dict and set(result) == RESULT_FIELDS, 'exact EB wrapper result fields')
    need(result['schema'] == 'eb-rtp-lane-gate-wrapper-result-v1' and result['accepted'] is True
         and result['operation'] == 'fixed_read_only_record_capture', 'accepted fixed EB operation')
    for key, expected in [('headersSent',16),('bulkTransfers',32),('wrapperUiOperations',0),('nativeInvocations',1),('retries',0)]:
        need(type(result[key]) is int and result[key] == expected, 'exact EB result count')
    for key in ('endpointQueueProof','identitySnapshotsAtomic','physicalPictureObserved','rootCauseFixEstablished','automaticRestore','diagnosticStdoutIsSemanticReceipt'):
        need(result[key] is False, 'EB claim boundary')
    need(result['manifestSha256'] == MANIFEST_SHA and result['cleanup'] == 'STAGE_ABSENT'
         and result['structuredReceipt'] == 'exclusive_private_file', 'completed exact EB capture')
    manifest = read(capture/'reviewed-manifest.json', 65536)
    need(sha(manifest) == MANIFEST_SHA, 'captured frozen EB manifest')
    regenerated, _ = wrapper.build_manifest()
    need(wrapper.manifest_bytes(regenerated) == manifest, 'original EB source/payload contract')
    ready, ready_raw = wrapper.load_readiness(capture/'readiness-decision.json', result['readinessSha256'])
    for evidence in ready['evidence']:
        need(sha(read(Path(evidence['path']), 4000000)) == evidence['sha256'], 'readiness evidence binding')
    native_raw = read(capture/'native.receipt.json', 24576)
    native, raws, _ = parser.parse_native(native_raw.decode('utf8'))
    need(str(native['device']) == ready['identity']['devnum'], 'same native/readiness device')
    expected = []
    for name, raw, digest in raws:
        need(read(capture/name, len(raw)) == raw, 'EB capture raw binding')
        expected.append({'name':name,'bytes':len(raw),'sha256':digest})
    need(result['rawFiles'] == expected == record['retained_raw_files'], 'complete raw inventory binding')
    need(record['schema'] == 'eb-rtp-lane-gate-wrapper-record-v1' and record['manifestSha256'] == MANIFEST_SHA
         and record['readinessSha256'] == result['readinessSha256'] and record['no_retry'] is True,
         'original record contract')
    need(type(record['native_invocations']) is int and record['native_invocations'] == 1
         and type(record['target_operations']) is int and record['target_operations'] == 16
         and record['native_invocations_status'] == 'one_completed'
         and record['target_operations_status'] == 'accepted_fixed_read_only_record_capture'
         and record['cleanup_required'] is False and record['cleanup_stdout'] == 'STAGE_ABSENT\n', 'record lifecycle/cleanup')
    saved_envelopes = []
    for tag in ('selftest','native'):
        envelope = read(capture/(tag+'-envelope.txt'), 65536).decode('utf8')
        saved_envelopes.append(envelope)
        if tag == 'native':
            need(envelope.startswith('IMMEDIATE_READY\n'), 'native immediate identity guard')
            envelope = envelope[len('IMMEDIATE_READY\n'):]
        terminal, receipt, stdout, stderr = wrapper.receipt_envelope(envelope)
        need(terminal == record[tag+'Terminal'] and terminal['exit_code'] == 0, 'original terminal binding')
        need(receipt == read(capture/(tag+'.receipt.json'),24576)
             and stdout == read(capture/(tag+'.stdout'),16384)
             and stderr == read(capture/(tag+'.stderr'),2048) == b'', 'envelope saved-byte binding')
        if tag == 'selftest':
            need(wrapper.strict_json(receipt) == {'selfTestsPassed':2071,'targetOperations':0}, 'zero-I/O selftest')
    # Inspect original completed envelopes; do not import or invoke a root adapter.
    need(type(record['calls']) is list and len(record['calls']) == 28, '28 completed original root calls')
    for call in record['calls']:
        need(type(call['command_bytes']) is int and call['command_bytes'] == len(call['command'].encode()) <= 8192,
             'original command bound')
        need(type(call['transport_exit']) is int and call['transport_exit'] == 0 and call['host_timeout'] is False
             and call['remote_timeout_seconds'] == 45 and call['host_timeout_limit_seconds'] == 75, 'root transport completion')
        def blob(obj):
            need(type(obj) is dict and set(obj) == {'encoding','data'} and obj['encoding'] == 'base64', 'transport blob')
            raw = base64.b64decode(obj['data'], validate=True)
            need(base64.b64encode(raw).decode() == obj['data'], 'canonical transport encoding')
            return raw
        need(blob(call['transport_stderr']) == b'', 'empty original transport stderr')
        response = wrapper.strict_json(blob(call['transport_stdout']))
        need(response == call['response'] and response['authenticated'] is True
             and type(response['uid']) is int and response['uid'] == 0
             and type(response['euid']) is int and response['euid'] == 0, 'original root response')
        need(type(response['commands']) is list and len(response['commands']) == 1, 'one original root command')
        command = response['commands'][0]
        need(command['command'] == call['command'] and type(command['exit_code']) is int and command['exit_code'] == 0
             and command['timed_out'] is False and command['stderr'] == '', 'original command completion')
    outputs = [call['response']['commands'][0]['stdout'] for call in record['calls']]
    need(all(type(value) is str and len(value.encode()) <= 65536 for value in outputs), 'original output bounds')
    need(all(outputs.count(value) == 1 for value in saved_envelopes), 'saved envelopes bound to original completed calls')
    need(outputs[-1] == 'STAGE_ABSENT\n', 'last original call exact cleanup')
    for label,key,name in [('PRE_READY','preCensus','metadata-pre.txt'),('BEFORE_INVOKE_READY','beforeInvokeCensus','metadata-before-invoke.txt'),('POST_READY','postCensus','metadata-post.txt')]:
        need(wrapper.parse_metadata(read(capture/name,65536).decode(),label) == record[key], 'original cached census')
    start, end = read(capture/'start-R.bin',256), read(capture/'end-R.bin',256)
    need(start == end and [struct.unpack_from('<H', start, i)[0] for i in (0,10,14,0xc4)] == [1,0x1001,0,200],
         'stable captured fixed200 fault required')
    return {'schema':'ew-eb200-recovery-admission-v1','accepted':True,'captureResultSha256':result_pin,
            'captureRecordSha256':record_pin,'captureReadinessSha256':sha(ready_raw),'captureManifestSha256':MANIFEST_SHA,
            'nativeDevice':native['device'],'samePhase':'ReadyForHeader','headers':16,'bulks':32,
            'released':True,'closed':True,'cleanup':'STAGE_ABSENT','faultTuple':[1,0x1001,0,200],
            'freshCurrentIdentityStillRequired':True,'coordinatorNoInterveningVendorOutRequired':True,'endpointQueueProof':False}

def perform_recovery(output, admission, modules=None):
    """EI's existing navigation/public-gate/stock-helper sequence; no DV restore."""
    need(output.is_absolute() and not output.exists(), 'fresh absolute output')
    if modules is None:
        modules = (load(B/'recovery-quickpath-20261027bv/recover.py',GATES_SHA,'ew_recovery_gates'),
                   load(B/'ui-navigation-20261027br/navigate.py',NAV_SHA,'ew_recovery_nav'),
                   load(B/'autonomous-fault-harness-20261028dh/run-deadline-mode2.py',HELPER_SHA,'ew_stock_recovery'))
    gates, nav, helper = modules
    output.mkdir(mode=0o700)
    record = {'schema':'ew-fixed200-stock-recovery-v1','accepted':False,'admission':admission,'mode2_attempts':0,
              'mode2_invocations':0,'threshold_writes':0,'automatic_retries':0,'physical_picture_observed':False,
              'c4_after_mode2_assumed':False,'automatic_dv_restore':False}
    try:
        root = gates.load_adapter()
        current = nav.command_snapshot(root,output,'before');record['before'] = current
        if current['cached_current_tab'] == 'd/ug.tab@Live':
            nav.one_key('right','local',output,root,'live-right')
            record['after_right'] = nav.command_snapshot(root,output,'after-right')
        gate_dir = output/'recovery-gates';gate_dir.mkdir(mode=0o700)
        record['apps_preparation'] = gates.apps_gate(gate_dir)
        gates.public_gate(gate_dir)
        payload = helper.contract()
        record['mode2_attempts'] = 1;record['mode2_invocations'] = None
        record['recovery'] = helper.execute(output/'mode2',payload)
        need(record['recovery']['accepted'] is True and record['recovery']['request_count'] == 1
             and record['recovery']['cleanup_confirmed'] is True, 'one accepted stock request')
        record['mode2_invocations'] = 1
        record['final'] = nav.command_snapshot(root,output,'final')
        record['accepted'] = record['final']['cached_current_tab'] == 'd/apps.tab'
        record['next_step'] = 'Separate fresh USB identity/phase readiness and EB capture; observe actual c4 before any restore decision.'
    except Exception as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        (output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--execute',action='store_true')
    cli.add_argument('--capture',type=Path)
    cli.add_argument('--capture-result-sha256')
    cli.add_argument('--capture-record-sha256')
    cli.add_argument('--output',type=Path)
    args = cli.parse_args()
    if not args.execute:
        need(all(x is None for x in (args.capture,args.capture_result_sha256,args.capture_record_sha256,args.output)), 'live arguments require execute')
        print(json.dumps({'schema':'ew-fixed200-recovery-dry-v1','targetOperations':0,'maxMode2Attempts':1,
                          'requiredStableFault':[1,0x1001,0,200],'thresholdWrites':0,'automaticRestore':False}))
        return
    need(args.capture is not None and args.output is not None, 'capture/output required')
    admission = validate_capture(args.capture,args.capture_result_sha256,args.capture_record_sha256)
    record = perform_recovery(args.output,admission)
    print(json.dumps({'accepted':record['accepted'],'mode2_invocations':record['mode2_invocations'],
                      'threshold_writes':0,'automatic_dv_restore':False,'physical_picture_observed':False}))

if __name__ == '__main__':
    main()
