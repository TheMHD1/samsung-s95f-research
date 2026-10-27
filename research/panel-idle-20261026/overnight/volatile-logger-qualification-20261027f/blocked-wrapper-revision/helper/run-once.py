#!/usr/bin/env python3
"""Deploy one reviewed fixed volatile logger qualification; no I/O by default."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import uuid

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
RUNNER = BASE / 'managed-tcon-status-read/run-status-read.py'
RUNNER_SHA = '7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a'
BOOT = '00000000-0000-4000-8000-000000000000'
DOTNET_SHA = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
ASSEMBLY = 'ManagedUsbSecondaryLoggerSmoke'
NAMES = [ASSEMBLY + '.' + suffix for suffix in
         ('dll', 'deps.json', 'runtimeconfig.json')]
MAX_NATIVE_JSON = 55000
RING_LENGTH = 15372
SCHEMA = 'usb-fixed-secondary-logger-smoke-build-v1'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def bad(value):
        raise ValueError('non-JSON constant ' + value)
    return json.loads(raw, parse_constant=bad)


def dir_guard(path):
    q = shlex.quote(path)
    return (f'test ! -L {q}\n' + f'test -d {q}\n' +
            f'test "$(stat -c "%u:%g:%a" {q})" = "0:0:700"\n')


def file_guard(path, size=None):
    q = shlex.quote(path)
    text = (f'test ! -L {q}\n' + f'test -f {q}\n' +
            f'test "$(stat -c "%u:%g:%a" {q})" = "0:0:600"\n')
    if size is not None:
        text += f'test "$(wc -c < {q})" = {size}\n'
    return text


def exact_inventory(path, names):
    q = shlex.quote(path)
    cases = '|'.join(shlex.quote(name) for name in sorted(names))
    return (f'count=0\nfor item in {q}/* {q}/.[!.]* {q}/..?*; do\n' +
            '  test -e "$item" || test -L "$item" || continue\n' +
            '  name=${item##*/}\n' +
            f'  case "$name" in {cases}) ;; *) exit 91 ;; esac\n' +
            '  count=$((count+1))\ndone\n' + f'test "$count" = {len(names)}\n')


def parse_stdout(stdout):
    lines = stdout.splitlines()
    uptime = re.compile(r'[0-9]+(?:\.[0-9]+)? [0-9]+(?:\.[0-9]+)?')
    need(len(lines) >= 8 and lines[0] == BOOT, 'helper boot framing')
    need(uptime.fullmatch(lines[1]) is not None and
         uptime.fullmatch(lines[-1]) is not None, 'helper uptime framing')
    need(lines.count('ACTIVE_LOGGER_SMOKE_BEGIN') == 1 and
         lines.count('WORKER_WAIT_COMPLETED') == 1, 'execution markers')
    phase = 'before'
    selftests = []
    outcomes = []
    exit_codes = []
    gc_rows = []
    for line in lines[2:-1]:
        if line == 'ACTIVE_LOGGER_SMOKE_BEGIN':
            need(phase == 'before', 'active marker order')
            phase = 'active'
        elif line.startswith('HELPER_EXIT='):
            need(phase == 'active' and re.fullmatch(r'HELPER_EXIT=[012]', line),
                 'helper exit marker')
            exit_codes.append(int(line.split('=', 1)[1]))
            phase = 'exited'
        elif line == 'WORKER_WAIT_COMPLETED':
            need(phase == 'exited', 'wait marker order')
            phase = 'waited'
        elif line.startswith('{'):
            value = strict_json(line)
            need(isinstance(value, dict), 'helper JSON object')
            (selftests if phase == 'before' else outcomes).append(value)
        elif line.startswith('[GC_INFO] '):
            gc_rows.append(line)
        else:
            raise ValueError('unclassified helper output')
    need(phase == 'waited' and len(exit_codes) == len(outcomes) == 1,
         'single native execution')
    need(selftests == [{'selfTestsPassed': 74, 'baselineTestsPassed': 26,
                        'stateMachineTestsPassed': 48,
                        'successOutputBytes': 45119,
                        'targetOperations': 0}], 'self-test summary')
    return outcomes[0], exit_codes[0], len(gc_rows)


def decode_artifact(outcome, field, name, output, expected=None, digest_field=None):
    value = outcome.get(field)
    if value is None:
        return None
    need(type(value) is str and len(value) <= 22000, field + ' bound')
    raw = base64.b64decode(value, validate=True)
    if expected is not None:
        need(len(raw) == expected, field + ' extent')
    if digest_field is not None:
        need(outcome.get(digest_field) == sha(raw), field + ' hash')
    path = output / name
    with path.open('xb') as stream:
        stream.write(raw)
    return {'file': name, 'size': len(raw), 'sha256': sha(raw)}


def validate_outcome(outcome, helper_exit):
    required = {'Stage', 'ProtocolPhase', 'Steps', 'Markers', 'Errors',
                'Opened', 'Claimed', 'Released', 'Closed', 'ArmAttempted',
                'ArmTransportComplete', 'ArmVerified', 'ObservationCompleted',
                'RestoreAttempted', 'RestoreTransportComplete',
                'RestoreVerified', 'RestoreUnverified',
                'LogFlagMayRemainChanged', 'DeadlineViolation', 'Accepted',
                'PhysicalPictureObserved', 'RepairEstablished'}
    need(isinstance(outcome, dict) and required <= set(outcome), 'outcome schema')
    need(type(outcome['Steps']) is list and type(outcome['Markers']) is list and
         type(outcome['Errors']) is list, 'outcome collections')
    need(len(outcome['Steps']) <= 16, 'bounded bulk-step count')
    allowed = {'callbacks-header', 'callbacks-data', 'baseline-ring-header',
               'baseline-ring-data', 'prearm-rt-header', 'prearm-rt-data',
               'arm-header', 'arm-payload', 'armed-rt-header', 'armed-rt-data',
               'restore-header', 'restore-payload', 'restored-rt-header',
               'restored-rt-data', 'post-ring-header', 'post-ring-data'}
    previous = -1
    for row in outcome['Steps']:
        need(isinstance(row, dict) and
             {'Name', 'AtMs', 'Direction', 'Expected', 'Before', 'After'} <= set(row),
             'step schema')
        need(row['Name'] in allowed and type(row['AtMs']) is int and
             row['AtMs'] >= previous, 'step order/name')
        need(row['Direction'] in ('IN', 'OUT') and type(row['Expected']) is int,
             'step direction/count')
        previous = row['AtMs']
    need(outcome['PhysicalPictureObserved'] is False and
         outcome['RepairEstablished'] is False, 'diagnostic-only classification')
    need(outcome['ProtocolPhase'] in
         ('ReadyForHeader', 'ExpectingWritePayload', 'ExpectingReadIn', 'Unknown'),
         'protocol phase')
    if outcome['Accepted']:
        need(helper_exit == 0 and outcome['Stage'] == 'complete' and
             outcome['ProtocolPhase'] == 'ReadyForHeader', 'accepted completion')
        need(len(outcome['Steps']) == 16 and all(row.get('Count') == row['Expected']
                                                for row in outcome['Steps']),
             'accepted exact transfers')
        need(all(outcome[name] is True for name in
                 ('Opened', 'Claimed', 'Released', 'Closed', 'ArmTransportComplete',
                  'ArmVerified', 'ObservationCompleted', 'RestoreAttempted',
                  'RestoreTransportComplete', 'RestoreVerified')),
             'accepted lifecycle')
        need(outcome['RestoreUnverified'] is False and
             outcome['LogFlagMayRemainChanged'] is False and
             outcome['DeadlineViolation'] is False and
             outcome.get('PreArmGate') == 0 and outcome.get('ArmedGate') == 1 and
             outcome.get('RestoredGate') == 0, 'accepted gate transition')
    else:
        need(helper_exit in (1, 2), 'rejected helper exit')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'target_operations': 0, 'variant': 'arm-verified',
                          'fixed_write_header': '020100000624014702000000',
                          'arm_payload': '0100', 'restore_payload': '0000',
                          'hold_ms': 3000, 'hard_arm_deadline_ms': 10000}))
        return
    need(args.output is not None and args.output.is_absolute() and
         args.manifest_sha256 is not None, 'absolute new output and manifest required')
    manifest_raw = (HERE / 'build-manifest.json').read_bytes()
    need(sha(manifest_raw) == args.manifest_sha256, 'reviewed manifest hash')
    manifest = strict_json(manifest_raw)
    need(manifest.get('schema') == SCHEMA, 'manifest schema')
    protocol = manifest.get('fixed_protocol')
    need(protocol == {
        'callback_read': {'target': '0x101', 'address': '0x45000580', 'length': 64,
                          'header_hex': '010100008005004540000000'},
        'ring_read': {'target': '0x101', 'address': '0x20200000', 'length': 15372,
                      'header_hex': '01010000000020200c3c0000'},
        'rt_read': {'target': '0x101', 'address': '0x47012400', 'length': 64,
                    'header_hex': '010100000024014740000000'},
        'gate_write': {'target': '0x102', 'address': '0x47012406', 'length': 2,
                       'header_hex': '020100000624014702000000',
                       'arm_payload_hex': '0100', 'restore_payload_hex': '0000'},
        'hold_ms': 3000, 'hard_arm_deadline_ms': 10000,
        'whole_deadline_ms': 20000, 'bulk_timeout_ms': 2000,
        'retries': 0}, 'fixed protocol manifest')
    expected = {'Program.cs', 'ManagedUsbSecondaryLoggerSmoke.csproj',
                *('bin/Release/net6.0/' + name for name in NAMES)}
    need(set(manifest.get('files', {})) == expected, 'manifest inventory')
    for name, row in manifest['files'].items():
        raw = (HERE / name).read_bytes()
        need(row == {'size': len(raw), 'sha256': sha(raw)}, 'build identity ' + name)
    need(sha(RUNNER.read_bytes()) == RUNNER_SHA, 'root runner identity')
    spec = importlib.util.spec_from_file_location('pinned_root_runner', RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args.output.mkdir(parents=True, exist_ok=False)
    record_path = args.output / 'record.json'
    remote = '/tmp/researcher-usb-logger-' + uuid.uuid4().hex
    record = {
        'manifest_sha256': sha(manifest_raw),
        'deployment_script_sha256': sha(Path(__file__).read_bytes()),
        'root_runner_sha256': RUNNER_SHA,
        'remote_stage': remote,
        'calls': [],
        'cleanup_deferred': True,
        'fixed_variant': 'arm-verified',
        'partial_policy': ('Unknown protocol phase forbids retry, restore, new header, '
                           'reset, or second native invocation.')
    }
    module.save(record_path, record)

    def call(command):
        return module.root(command, record, record_path)

    completion_seen = False
    try:
        call('set -eu\numask 077\n' +
             f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
             f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n' +
             f'test ! -e {shlex.quote(remote)}\ntest ! -L {shlex.quote(remote)}\n' +
             f'mkdir -m 700 {shlex.quote(remote)}\n' + dir_guard(remote) +
             'echo STAGE_CREATED\n')
        for name in NAMES:
            data = (HERE / 'bin/Release/net6.0' / name).read_bytes()
            encoded = base64.b64encode(data).decode('ascii')
            target = remote + '/' + name
            temp = target + '.b64'
            for start in range(0, len(encoded), 5000):
                chunk = encoded[start:start + 5000]
                initialize = (f'test ! -e {shlex.quote(temp)}\n'
                              f'test ! -L {shlex.quote(temp)}\n'
                              f': > {shlex.quote(temp)}\nchmod 600 {shlex.quote(temp)}\n') if start == 0 else ''
                call('set -eu\numask 077\n' + dir_guard(remote) + initialize +
                     file_guard(temp, start) +
                     f'printf %s {shlex.quote(chunk)} >> {shlex.quote(temp)}\n' +
                     file_guard(temp, start + len(chunk)) +
                     'echo STAGE_CHUNK_COMPLETE\n')
            call('set -eu\numask 077\n' + dir_guard(remote) +
                 file_guard(temp, len(encoded)) +
                 f'test ! -e {shlex.quote(target)}\ntest ! -L {shlex.quote(target)}\n' +
                 f'base64 -d {shlex.quote(temp)} > {shlex.quote(target)}\n'
                 f'chmod 600 {shlex.quote(target)}\n' + file_guard(target, len(data)) +
                 f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {sha(data)}\n' +
                 f'rm {shlex.quote(temp)}\ntest ! -e {shlex.quote(temp)}\n'
                 'echo FILE_VERIFIED\n')
        integrity = dir_guard(remote) + exact_inventory(remote, NAMES)
        for name in NAMES:
            target = remote + '/' + name
            data = (HERE / 'bin/Release/net6.0' / name).read_bytes()
            integrity += (file_guard(target, len(data)) +
                          f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {sha(data)}\n')
        dll = shlex.quote(remote + '/' + NAMES[0])
        command = ('set -eu\numask 077\n' +
                   f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
                   integrity +
                   'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n' +
                   f'/usr/bin/dotnet {dll} --self-test\n' +
                   'echo ACTIVE_LOGGER_SMOKE_BEGIN\nrc=0\n' +
                   f'/usr/bin/dotnet {dll} --execute || rc=$?\n' +
                   'echo HELPER_EXIT=$rc\necho WORKER_WAIT_COMPLETED\ncat /proc/uptime\n')
        stdout = call(command)
        completion_seen = 'WORKER_WAIT_COMPLETED\n' in stdout
        with (args.output / 'stdout.txt').open('x') as stream:
            stream.write(stdout)
        record['helper_stdout_sha256'] = sha(stdout.encode())
        outcome, helper_exit, gc_rows = parse_stdout(stdout)
        native_raw = (json.dumps(outcome, separators=(',', ':')) + '\n').encode()
        with (args.output / 'native-outcome.json').open('xb') as stream:
            stream.write(native_raw)
        need(len(native_raw) <= MAX_NATIVE_JSON, 'native JSON size budget')
        validate_outcome(outcome, helper_exit)
        artifacts = {}
        for field, name, extent, digest_field in (
            ('CallbackBase64', 'callbacks.bin', 64, 'CallbackSha256'),
            ('BaselineRingBase64', 'baseline-ring.bin', RING_LENGTH, 'BaselineRingSha256'),
            ('PreArmRtBase64', 'prearm-rt.bin', 64, None),
            ('ArmedRtBase64', 'armed-rt.bin', 64, None),
            ('RestoredRtBase64', 'restored-rt.bin', 64, None),
            ('PostRingBase64', 'post-ring.bin', RING_LENGTH, 'PostRingSha256')):
            row = decode_artifact(outcome, field, name, args.output, extent, digest_field)
            if row is not None:
                artifacts[field] = row
        summary = {
            'schema': 'secondary-logger-smoke-host-result-v1',
            'accepted': outcome['Accepted'],
            'helper_exit': helper_exit,
            'protocol_phase': outcome['ProtocolPhase'],
            'arm_verified': outcome['ArmVerified'],
            'restore_verified': outcome['RestoreVerified'],
            'restore_unverified': outcome['RestoreUnverified'],
            'log_flag_may_remain_changed': outcome['LogFlagMayRemainChanged'],
            'deadline_violation': outcome['DeadlineViolation'],
            'physical_picture_observed': False,
            'repair_established': False,
            'native_outcome_sha256': sha(native_raw),
            'artifacts': artifacts,
            'gc_rows': gc_rows
        }
        with (args.output / 'result.json').open('x') as stream:
            json.dump(summary, stream, indent=2, sort_keys=True)
            stream.write('\n')
        record['helper_exit'] = helper_exit
        record['native_accepted'] = outcome['Accepted']
        record['protocol_phase'] = outcome['ProtocolPhase']
        record['result_sha256'] = sha((args.output / 'result.json').read_bytes())
        module.save(record_path, record)
    finally:
        if completion_seen:
            files = [remote + '/' + name for name in NAMES]
            clean = ('set -eu\numask 077\n' + dir_guard(remote) +
                     exact_inventory(remote, NAMES))
            for name in NAMES:
                target = remote + '/' + name
                data = (HERE / 'bin/Release/net6.0' / name).read_bytes()
                clean += file_guard(target, len(data))
            clean += ('rm ' + ' '.join(map(shlex.quote, files)) + '\n' +
                      f'rmdir {shlex.quote(remote)}\n'
                      f'test ! -e {shlex.quote(remote)}\n'
                      'echo STAGE_ABSENT\n')
            record['cleanup_stdout'] = call(clean)
            record['cleanup_deferred'] = False
            module.save(record_path, record)
    print(json.dumps({'record': str(record_path),
                      'result': str(args.output / 'result.json'),
                      'cleanup_deferred': record['cleanup_deferred'],
                      'accepted': record.get('native_accepted')}))


if __name__ == '__main__':
    main()
