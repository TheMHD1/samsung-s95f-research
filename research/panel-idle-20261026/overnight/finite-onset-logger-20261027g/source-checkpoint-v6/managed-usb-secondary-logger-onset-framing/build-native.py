#!/usr/bin/env python3
"""Build and attest the finite onset logger native helper without target I/O."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DOTNET = BASE.parents[1] / 'live-cast/sdk/runtime/dotnet'
PROJECT = 'ManagedUsbSecondaryLoggerOnset.csproj'
ASSEMBLY = 'ManagedUsbSecondaryLoggerOnset'
PROGRAM_SHA = 'db45feac5d5bda5e670da51be296cdb39769f898b4d7c8d9224a36cc65e13cdd'
PROJECT_SHA = '05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187'
PARENT_SOURCE_SHA = 'abbfd7bbfafe11c4204934187600983379db1a93de9fde4fe9ac1fe3736a6991'
PARENT_DLL_SHA = '03296496c42c01453d05a02678ef7a79d121e5822ff17097f7f6ae8b34eea3b5'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run_dll(dll, args, expected):
    done = subprocess.run([str(DOTNET), str(dll), *args],
                          capture_output=True, text=True)
    need(done.returncode == expected, 'host check ' + str(args))
    return {'args': args, 'exit_code': done.returncode,
            'stdout': done.stdout, 'stderr': done.stderr}


def build(project):
    return subprocess.run([str(DOTNET), 'build', '-c', 'Release', '--nologo',
                           str(project)], capture_output=True, text=True)


def main():
    need(sha((HERE / 'Program.cs').read_bytes()) == PROGRAM_SHA, 'Program pin')
    need(sha((HERE / PROJECT).read_bytes()) == PROJECT_SHA, 'project pin')
    parent = BASE / 'managed-usb-secondary-logger-smoke'
    need(sha((parent / 'Program.cs').read_bytes()) == PARENT_SOURCE_SHA,
         'qualified parent source pin')
    need(sha((parent / 'bin/Release/net6.0/ManagedUsbSecondaryLoggerSmoke.dll').read_bytes()) ==
         PARENT_DLL_SHA, 'qualified parent DLL pin')

    built = build(HERE / PROJECT)
    (HERE / 'build.log').write_text(built.stdout + built.stderr)
    need(built.returncode == 0 and '0 Warning(s)' in built.stdout and
         '0 Error(s)' in built.stdout, 'clean build')
    dll = HERE / f'bin/Release/net6.0/{ASSEMBLY}.dll'
    checks = [run_dll(dll, [], 0), run_dll(dll, ['--self-test'], 0),
              run_dll(dll, ['--execute'], 64), run_dll(dll, ['--unknown'], 63)]
    selftest = json.loads(checks[1]['stdout'])
    need(selftest == {'selfTestsPassed': 85, 'baselineTestsPassed': 26,
                      'stateMachineTestsPassed': 59,
                      'successOutputBytes': 45851, 'targetOperations': 0},
         'self-test result')
    dry = json.loads(checks[0]['stdout'])
    need(dry == {'dryRun': True, 'targetOperations': 0, 'variant': 'arm-verified',
                 'fixedSequence': ('callbacks64,baseline15372,preRT64-zero-gate-fault,'
                                   'arm2,armedRT64,ready,hold20s,restore2,'
                                   'restoredRT64,post15372'),
                 'writeHeaderHex': '020100000624014702000000',
                 'armPayloadHex': '0100', 'restorePayloadHex': '0000',
                 'timeoutMs': 2000, 'hardArmDeadlineMs': 30000,
                 'wholeDeadlineMs': 45000, 'interfaceNumber': 2}, 'dry contract')

    deploy = [f'{ASSEMBLY}.{suffix}' for suffix in
              ('dll', 'deps.json', 'runtimeconfig.json')]
    with tempfile.TemporaryDirectory(prefix='onset-repro-') as temporary:
        root = Path(temporary)
        shutil.copy2(HERE / 'Program.cs', root / 'Program.cs')
        shutil.copy2(HERE / PROJECT, root / PROJECT)
        repeated = build(root / PROJECT)
        need(repeated.returncode == 0 and '0 Warning(s)' in repeated.stdout and
             '0 Error(s)' in repeated.stdout, 'reproducible clean build')
        for name in deploy:
            need((root / 'bin/Release/net6.0' / name).read_bytes() ==
                 (HERE / 'bin/Release/net6.0' / name).read_bytes(),
                 'reproducible artifact ' + name)

    files = ['Program.cs', PROJECT] + [f'bin/Release/net6.0/{name}' for name in deploy]
    manifest = {
        'schema': 'usb-fixed-secondary-logger-onset-native-build-v1',
        'qualified_parent': {'program_sha256': PARENT_SOURCE_SHA,
                             'dll_sha256': PARENT_DLL_SHA},
        'fixed_protocol': {
            'callback_read': {'target': '0x101', 'address': '0x45000580', 'length': 64,
                              'header_hex': '010100008005004540000000'},
            'ring_read': {'target': '0x101', 'address': '0x20200000', 'length': 15372,
                          'header_hex': '01010000000020200c3c0000'},
            'rt_read': {'target': '0x101', 'address': '0x47012400', 'length': 64,
                        'header_hex': '010100000024014740000000'},
            'gate_write': {'target': '0x102', 'address': '0x47012406', 'length': 2,
                           'header_hex': '020100000624014702000000',
                           'arm_payload_hex': '0100', 'restore_payload_hex': '0000'},
            'hold_ms': 20000, 'hard_arm_deadline_ms': 30000,
            'whole_deadline_ms': 45000, 'minimum_prearm_budget_ms': 43000,
            'publication_budget_ms': 2000, 'bulk_timeout_ms': 2000, 'retries': 0},
        'fresh_precondition': {'gate_halfword_offset': 6, 'gate_value': 0,
                               'fault_halfword_offset': 10, 'fault_value': 0},
        'ready_file': {'temporary': 'logger.ready.tmp', 'final': 'logger.ready',
                       'create_new': True, 'durable_flush': True,
                       'non_overwrite_rename': True,
                       'schema': 'secondary-logger-onset-ready-v1',
                       'fields': ['schema', 'stage_token', 'boot_id', 'pid', 'at_ms',
                                  'uptime', 'gate', 'protocol_phase'],
                       'final_binding': ['ReadyJson', 'ReadySha256']},
        'phase_model': ['ReadyForHeader', 'ExpectingWritePayload',
                        'ExpectingReadIn', 'Unknown'],
        'max_native_json_bytes': 55000,
        'files': {name: {'size': len((HERE / name).read_bytes()),
                         'sha256': sha((HERE / name).read_bytes())} for name in files},
        'offline_files': {
            name: {'size': len((HERE / name).read_bytes()),
                   'sha256': sha((HERE / name).read_bytes())}
            for name in ('build-native.py', 'README-native.md')},
        'checks': checks,
        'reproducible_build': True,
        'target_operations_during_build': 0,
        'scope': ('Finite volatile onset logger only. It publishes readiness after exact '
                  'arm readback, holds without USB traffic, restores from a known ready '
                  'boundary, and collects fixed post-state. It does not trigger UI, flash, '
                  'change protection policy, or establish physical output or repair.')
    }
    raw = (json.dumps(manifest, indent=2) + '\n').encode()
    (HERE / 'native-build-manifest.json').write_bytes(raw)
    print(json.dumps({'program_sha256': PROGRAM_SHA,
                      'manifest_sha256': sha(raw),
                      'dll_sha256': sha(dll.read_bytes()),
                      'self_tests': selftest}, indent=2))


if __name__ == '__main__':
    main()
