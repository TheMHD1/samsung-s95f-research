#!/usr/bin/env python3
"""Offline behavioral tests for the detached onset-wrapper orchestration."""
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
WRAPPER = HERE / 'run-once.py'
PARENT = HERE.parent / 'managed-usb-secondary-logger-smoke/run-once.py'
BOOT = '00000000-0000-4000-8000-000000000000'
STAGE_TOKEN = 'researcher-usb-onset-' + '1' * 32
REMOTE = '/tmp/' + STAGE_TOKEN


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def proc_line(pid, parent, group, session, start, name):
    # Fields after state: ppid, pgrp, session, then enough fixed fields to starttime.
    fields = [parent, group, session] + [0] * 12 + [1, 0, 1, start]
    return f"{pid} ({name}) S " + ' '.join(map(str, fields)) + '\n'


def wrapped64(raw):
    value = base64.b64encode(raw).decode()
    return '\n'.join(value[i:i+76] for i in range(0, len(value), 76))


class Clock:
    def __init__(self):
        self.value = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        self.sleeps.append((self.value, seconds))
        self.value += seconds


def ready(phase='ReadyForHeader'):
    return {'schema': 'secondary-logger-onset-ready-v1',
            'stage_token': STAGE_TOKEN, 'boot_id': BOOT, 'pid': 701,
            'at_ms': 100, 'uptime': '100.00 200.00', 'gate': 1,
            'protocol_phase': phase}


def steps():
    names = [('callbacks-header', 'OUT', 12), ('callbacks-data', 'IN', 64),
             ('baseline-ring-header', 'OUT', 12), ('baseline-ring-data', 'IN', 15372),
             ('prearm-rt-header', 'OUT', 12), ('prearm-rt-data', 'IN', 64),
             ('arm-header', 'OUT', 12), ('arm-payload', 'OUT', 2),
             ('armed-rt-header', 'OUT', 12), ('armed-rt-data', 'IN', 64),
             ('restore-header', 'OUT', 12), ('restore-payload', 'OUT', 2),
             ('restored-rt-header', 'OUT', 12), ('restored-rt-data', 'IN', 64),
             ('post-ring-header', 'OUT', 12), ('post-ring-data', 'IN', 15372)]
    result = []
    phase = 'ReadyForHeader'
    for index, (name, direction, count) in enumerate(names):
        after = ('ExpectingWritePayload' if name.endswith('header') and
                 name.split('-')[0] in ('arm', 'restore') else
                 'ExpectingReadIn' if name.endswith('header') else 'ReadyForHeader')
        result.append({'Name': name, 'AtMs': 20000 if index >= 10 else 0,
                       'Direction': direction, 'Expected': count, 'Count': count,
                       'Errno': 0, 'Before': phase, 'After': after})
        phase = after
    return result


def outcome(accepted=True, ready_value=None):
    ring0 = bytes(15372)
    ring1 = bytearray(15372)
    ring1[:8] = (1).to_bytes(4, 'little') * 2
    callback = bytes(64)
    rt0 = bytes(64)
    rt1 = bytearray(64)
    rt1[6] = 1
    value = ready_value or ready()
    ready_json = json.dumps(value, separators=(',', ':'))
    result = {
        'Stage': 'complete' if accepted else 'rejected',
        'ProtocolPhase': 'ReadyForHeader', 'Steps': steps() if accepted else [],
        'Markers': [], 'Errors': [] if accepted else ['fresh-prearm-rt: rejected'],
        'Opened': True, 'Claimed': True, 'Released': True, 'Closed': True,
        'ArmAttempted': accepted, 'ArmTransportComplete': accepted,
        'ArmVerified': accepted, 'ReadyPublished': accepted,
        'ObservationCompleted': accepted, 'RestoreAttempted': accepted,
        'RestoreTransportComplete': accepted, 'RestoreVerified': accepted,
        'RestoreUnverified': False, 'LogFlagMayRemainChanged': False,
        'DeadlineViolation': False, 'Accepted': accepted,
        'PhysicalPictureObserved': False, 'RepairEstablished': False,
        'PreArmGate': 0, 'ArmedGate': 1 if accepted else None,
        'RestoredGate': 0 if accepted else None, 'PreArmFault': 0,
    }
    if accepted:
        result.update(
            ReadyJson=ready_json,
            ReadySha256=sha((ready_json + '\n').encode()),
            CallbackBase64=base64.b64encode(callback).decode(),
            CallbackSha256=sha(callback),
            BaselineRingBase64=base64.b64encode(ring0).decode(),
            BaselineRingSha256=sha(ring0),
            PreArmRtBase64=base64.b64encode(rt0).decode(),
            ArmedRtBase64=base64.b64encode(rt1).decode(),
            RestoredRtBase64=base64.b64encode(rt0).decode(),
            PostRingBase64=base64.b64encode(ring1).decode(),
            PostRingSha256=sha(ring1))
    return result


class FakeRoot:
    def __init__(self, scenario, clock):
        self.scenario = scenario
        self.clock = clock
        self.commands = []
        self.status_count = 0
        self.ready = ready('Unknown' if scenario == 'invalid-ready' else 'ReadyForHeader')
        accepted = scenario in ('accepted', 'selftest-size-variation',
                                'binding-mismatch', 'cleanup-residue',
                                'completion-absent')
        self.selftest = {
            'selfTestsPassed': 85, 'baselineTestsPassed': 26,
            'stateMachineTestsPassed': 59, 'successOutputBytes': 45851,
            'targetOperations': 0}
        if scenario == 'selftest-size-variation':
            self.selftest['successOutputBytes'] = 45848
        elif scenario == 'selftest-oversize':
            self.selftest['successOutputBytes'] = 50001
        elif scenario == 'selftest-bad-total':
            self.selftest['selfTestsPassed'] = 84
        elif scenario == 'selftest-bad-baseline':
            self.selftest['baselineTestsPassed'] = 25
        elif scenario == 'selftest-bad-state':
            self.selftest['stateMachineTestsPassed'] = 58
        elif scenario == 'selftest-bad-ops':
            self.selftest['targetOperations'] = 1
        native_ready = dict(self.ready)
        if scenario == 'binding-mismatch':
            native_ready['at_ms'] += 1
        self.native = outcome(accepted, native_ready)
        self.stdout = json.dumps(self.native, separators=(',', ':')) + '\n'
        self.stderr = ''
        self.completion = {
            'schema': 'secondary-logger-onset-exit-v1', 'supervisor_pid': 700,
            'child_pid': 701, 'child_exit': 0 if accepted else 1,
            'stdout_bytes': len(self.stdout.encode()), 'stderr_bytes': 0,
            'stdout_sha256': sha(self.stdout.encode()), 'stderr_sha256': sha(b''),
            'boot_id': BOOT, 'uptime': '122.50 250.00'}
        if scenario == 'oversized':
            self.completion['stdout_bytes'] = 50001

    def save(self, path, record):
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')

    def root(self, command, record, path):
        self.commands.append((self.clock.value, command))
        record['calls'].append({'command': command, 'fake_at': self.clock.value})
        self.save(path, record)
        if '/usr/bin/setsid ' in command:
            if self.scenario == 'ambiguous-launch':
                raise TimeoutError('injected ambiguous launch')
            return 'LAUNCHER_PID=700\n'
        if '--self-test' in command:
            return json.dumps(self.selftest, separators=(',', ':')) + '\n'
        if 'SUPERVISOR_STAT_BEGIN' in command:
            supervisor_pid = 702 if self.scenario == 'launcher-mismatch' else 700
            stat = wrapped64(proc_line(supervisor_pid, 1, supervisor_pid,
                                       supervisor_pid, 12345, 'supervisor').encode())
            self.status_count += 1
            ready_scenarios = ('accepted', 'selftest-size-variation',
                               'invalid-ready', 'stale-ready', 'child-mismatch',
                               'stale-probe', 'cmdline-mismatch', 'binding-mismatch',
                               'cleanup-residue', 'completion-absent',
                               'launcher-mismatch')
            prefix = (f'{BOOT}\n100.20 200.20\nSUPERVISOR_STAT_BEGIN\n{stat}\n'
                      'SUPERVISOR_STAT_END\n')
            if self.scenario in ready_scenarios and self.status_count == 1:
                end_up = '103.20 203.20' if self.scenario == 'stale-ready' else '100.20 200.20'
                return prefix + 'READY\n' + json.dumps(self.ready) + f'\nPOLL_END_UPTIME\n{end_up}\n'
            if self.scenario == 'completion-absent':
                return prefix + 'WAIT\nPOLL_END_UPTIME\n122.50 250.00\n'
            return prefix + 'DONE\n' + json.dumps(self.completion) + '\nPOLL_END_UPTIME\n122.50 250.00\n'
        if 'LIVE_SUP_BEGIN' in command:
            child_group = 702 if self.scenario == 'child-mismatch' else 700
            argv_raw = (f'/usr/bin/dotnet\0{REMOTE}/ManagedUsbSecondaryLoggerOnset.dll\0'
                        + ('--wrong\0' if self.scenario == 'cmdline-mismatch' else '--execute\0')).encode()
            probe_end = '103.26 203.26' if self.scenario == 'stale-probe' else '100.26 200.26'
            return (f'{BOOT}\n100.25 200.25\nLIVE_SUP_BEGIN\n' +
                    wrapped64(proc_line(700, 1, 700, 700, 12345, 'supervisor').encode()) +
                    '\nLIVE_SUP_END\nLIVE_CHILD_BEGIN\n' +
                    wrapped64(proc_line(701, 700, child_group, child_group, 12346, 'dotnet').encode()) +
                    '\nLIVE_CHILD_END\nLIVE_CMDLINE_BEGIN\n' + wrapped64(argv_raw) +
                    f'\nLIVE_CMDLINE_END\nPROBE_END_UPTIME\n{probe_end}\n')
        if 'cat ' + REMOTE + '/native.stdout' in command:
            return self.stdout
        if 'cat ' + REMOTE + '/native.stderr' in command:
            return self.stderr
        if 'rmdir ' in command:
            if self.scenario == 'cleanup-residue':
                raise ValueError('injected cleanup inventory residue')
            return 'STAGE_ABSENT\n'
        return 'OK\n'


def fixture(root):
    (root / 'bin/Release/net6.0').mkdir(parents=True)
    names = ['ManagedUsbSecondaryLoggerOnset.' + x for x in
             ('dll', 'deps.json', 'runtimeconfig.json')]
    rows = {}
    for index, name in enumerate(names):
        raw = (name + ':' + str(index)).encode()
        path = root / 'bin/Release/net6.0' / name
        path.write_bytes(raw)
        rows['bin/Release/net6.0/' + name] = {'size': len(raw), 'sha256': sha(raw)}
    native = {'files': rows, 'offline_files': {},
              'fixed_protocol': {'hold_ms': 20000, 'retries': 0},
              'checks': [{'args': ['--self-test'],
                          'stdout': ('{"selfTestsPassed":85,"baselineTestsPassed":26,'
                                     '"stateMachineTestsPassed":59,"successOutputBytes":45851,'
                                     '"targetOperations":0}\n')}]}
    native_raw = (json.dumps(native) + '\n').encode()
    (root / 'native-build-manifest.json').write_bytes(native_raw)
    wrapper_raw = WRAPPER.read_bytes()
    (root / 'run-once.py').write_bytes(wrapper_raw)
    manifest = {'schema': 'usb-fixed-secondary-logger-onset-build-v1',
                'native_manifest_sha256': sha(native_raw), 'local_files': {}}
    manifest_raw = (json.dumps(manifest) + '\n').encode()
    (root / 'build-manifest.json').write_bytes(manifest_raw)
    return sha(manifest_raw)


def run_case(scenario):
    wrapper = load('onset_wrapper_' + scenario.replace('-', '_'), WRAPPER)
    parent = load('onset_parent_for_tests', PARENT)
    clock = Clock()
    fake = FakeRoot(scenario, clock)
    with tempfile.TemporaryDirectory(prefix='onset-wrapper-test-') as temporary:
        root = Path(temporary) / 'build'
        root.mkdir()
        manifest_sha = fixture(root)
        output = Path(temporary) / 'output'
        wrapper.HERE = root
        wrapper.PARENT = Path(temporary) / 'unused-parent'

        def modules(name, path, expected):
            return parent if name == 'onset_parent_wrapper' else fake

        argv = ['run-once.py', '--execute', '--manifest-sha256', manifest_sha,
                '--output', str(output)]
        caught = None
        stream = io.StringIO()
        try:
            with patch.object(wrapper, 'module', side_effect=modules), \
                 patch.object(wrapper.uuid, 'uuid4', return_value=SimpleNamespace(hex='1' * 32)), \
                 patch.object(wrapper.time, 'monotonic', side_effect=clock.monotonic), \
                 patch.object(wrapper.time, 'sleep', side_effect=clock.sleep), \
                 patch.object(sys, 'argv', argv), contextlib.redirect_stdout(stream):
                wrapper.main()
        except Exception as error:
            caught = error
        if not (output / 'record.json').exists():
            raise RuntimeError('wrapper failed before record creation') from caught
        record = json.loads((output / 'record.json').read_text())
        return SimpleNamespace(error=caught, record=record, output=output,
                               stdout=stream.getvalue(), commands=fake.commands,
                               sleeps=clock.sleeps, snapshot={p.name: p.read_bytes()
                                                             for p in output.iterdir()})


def main():
    passed = []
    wrapped = wrapped64(proc_line(700, 1, 700, 700, 12345, 'supervisor').encode())
    need('\n' in wrapped and 'n' in wrapped and "tr -d" not in WRAPPER.read_text(),
         'multiline base64 including literal n reaches real framed parser without tr deletion')

    accepted = run_case('accepted')
    need(accepted.error is None and accepted.record['native_accepted'] is True and
         accepted.record['cleanup_deferred'] is False, 'accepted completion')
    launch = [x for x in accepted.commands if '/usr/bin/setsid ' in x[1]]
    need(len(launch) == 1, 'exactly one detached launch')
    need(accepted.record['supervisor_identity']['pid'] == 700 and
         accepted.record['native_identity']['pid'] == 701 and
         accepted.record['native_identity']['pgrp'] ==
         accepted.record['native_identity']['session'] == 700,
         'verified supervisor/child relationship')
    grace = [x for x in accepted.sleeps if x[1] == 22]
    need(grace == [(0.0, 22)], 'one local trigger grace')
    probe_index = next(i for i, (_, command) in enumerate(accepted.commands)
                       if 'LIVE_SUP_BEGIN' in command)
    need(probe_index + 1 < len(accepted.commands) and
         accepted.commands[probe_index + 1][0] >= 22,
         'no root invocation between liveness probe and local grace end')
    need('LOGGER_READY' in accepted.stdout and 'LOGGER_FINISHED' in accepted.stdout,
         'accepted ready and finish events')
    passed.append('accepted-detached-ready-grace')

    variable_size = run_case('selftest-size-variation')
    need(variable_size.error is None and
         variable_size.record['native_accepted'] is True and
         variable_size.record['cleanup_deferred'] is False and
         len([x for x in variable_size.commands if '/usr/bin/setsid ' in x[1]]) == 1 and
         'LOGGER_READY' in variable_size.stdout and
         'LOGGER_FINISHED' in variable_size.stdout,
         'bounded platform-dependent selftest output size accepted through completion')
    passed.append('selftest-size-variation-accepted')

    for scenario in ('selftest-oversize', 'selftest-bad-total',
                     'selftest-bad-baseline', 'selftest-bad-state',
                     'selftest-bad-ops'):
        rejected = run_case(scenario)
        need(isinstance(rejected.error, ValueError) and
             rejected.record['cleanup_deferred'] is True and
             not any('/usr/bin/setsid ' in command for _, command in rejected.commands) and
             'LOGGER_READY' not in rejected.stdout and
             not any(seconds == 22 for _, seconds in rejected.sleeps),
             scenario + ' refused before detached launch')
    passed.append('selftest-oversize-and-fixed-fields-refused')

    ambiguous = run_case('ambiguous-launch')
    need(isinstance(ambiguous.error, TimeoutError), 'ambiguous launch retained')
    need(len([x for x in ambiguous.commands if '/usr/bin/setsid ' in x[1]]) == 1,
         'ambiguous launch never retried')
    need(ambiguous.record['cleanup_deferred'] is True and
         not any('rmdir ' in x[1] or 'kill ' in x[1] for x in ambiguous.commands),
         'ambiguous launch no kill/cleanup')
    passed.append('ambiguous-launch-safe-stop')

    early = run_case('early-reject')
    need(early.error is None and early.record['native_accepted'] is False and
         early.record['cleanup_deferred'] is True and 'LOGGER_READY' not in early.stdout,
         'early prearm reject retained without ready')
    need(not any(seconds == 22 for _, seconds in early.sleeps), 'early reject no UI grace')
    passed.append('early-prearm-reject-retained')

    invalid = run_case('invalid-ready')
    need(isinstance(invalid.error, ValueError) and
         invalid.record['cleanup_deferred'] is True and 'LOGGER_READY' not in invalid.stdout,
         'invalid readiness refused before broadcast')
    need(not any(seconds == 22 for _, seconds in invalid.sleeps), 'invalid ready no UI grace')
    passed.append('invalid-ready-refused')

    oversized = run_case('oversized')
    need(isinstance(oversized.error, ValueError) and oversized.record['cleanup_deferred'] is True,
         'oversized completion retained')
    need(not any('cat ' + REMOTE + '/native.stdout' in x[1] or 'rmdir ' in x[1]
                 for x in oversized.commands), 'oversized refuses fetch and cleanup')
    passed.append('oversized-output-refused')

    for scenario in ('launcher-mismatch', 'stale-ready', 'stale-probe',
                     'child-mismatch', 'cmdline-mismatch'):
        rejected = run_case(scenario)
        need(isinstance(rejected.error, ValueError) and
             rejected.record['cleanup_deferred'] is True and
             'LOGGER_READY' not in rejected.stdout and
             not any(seconds == 22 for _, seconds in rejected.sleeps),
             scenario + ' refused before broadcast')
        passed.append(scenario + '-refused')

    absent = run_case('completion-absent')
    need(isinstance(absent.error, ValueError) and absent.record['cleanup_deferred'] is True and
         'LOGGER_READY' in absent.stdout and
         not any('rmdir ' in command or 'kill ' in command for _, command in absent.commands),
         'completion absent retained without kill/cleanup')
    passed.append('completion-absent-retained')

    binding = run_case('binding-mismatch')
    need(isinstance(binding.error, ValueError) and binding.record['cleanup_deferred'] is True and
         not any('rmdir ' in command for _, command in binding.commands),
         'ready binding mismatch retained')
    passed.append('ready-binding-mismatch-retained')

    residue = run_case('cleanup-residue')
    need(isinstance(residue.error, ValueError) and residue.record['native_accepted'] is True and
         residue.record['cleanup_deferred'] is True,
         'cleanup inventory residue retained')
    passed.append('cleanup-residue-retained')

    print(json.dumps({'status': 'PASS', 'tests': passed, 'count': len(passed),
                      'target_operations': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
