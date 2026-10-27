#!/usr/bin/env python3
"""Build and attest the fixed secondary logger qualification without target I/O."""
import hashlib
import importlib.util
import json
from pathlib import Path
import py_compile
import subprocess
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
D5 = BASE / 'executing-image-identity-20261027e'
DOTNET = BASE.parents[1] / 'live-cast/sdk/runtime/dotnet'
PROJECT = 'ManagedUsbSecondaryLoggerSmoke.csproj'
ASSEMBLY = 'ManagedUsbSecondaryLoggerSmoke'
PROGRAM_SHA = 'abbfd7bbfafe11c4204934187600983379db1a93de9fde4fe9ac1fe3736a6991'
WRAPPER_SHA = 'eeb852c8e1b9a0d2611abc17e853ad2ee834f4e42712b2810bf8309eda5e59ca'
ROOT_ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
PROJECT_SHA = '05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187'
EVIDENCE_SHA = '7fd4a6fb53381af0bea1902aa54c7ec6bab33073d4a9ec08010594208e26c989'
SOURCE_EVIDENCE = {
    'secondary-logger-arm-protocol.md': '859190a1ff5d3b2817723221a1c88b01e0377f5f2f6a4a374eedc1dfbb547003',
    'volatile-logger-review.md': '16c9a6198317c5e144db274a94d7ba983190e07abd49b797f9aa9cee9afd28fe',
    'verify-secondary-logger-arm-protocol.py': '4858efeaaa6fbf3185b9eed9c7741e3e2ab5f9cd656b18b4c7a87d5075fd87e7',
    'secondary-event-log-buffer.md': '83d499bd9a44fd602b0211491521774f4fc53c86765fc3bb437386cd7fedcc6f',
    'verify-secondary-event-log-buffer.py': 'a82bdb61e7ff94e412a9c0304fef61f0819c157bcdca37503243c5fd98eb5ded',
    'callback-runtime-audit.json': 'd5e8abecd865b81deb18904127a13179117ebfe323b415be4ecba74d2c6e822c'
}
RAW_EVIDENCE = {
    'qualified-callbacks.bin': (D5 / 'callback-alias-read-once/returned-block.bin',
                                '55e0afcfdba1aa1fa14985f63d02aebaa60b77bf535afe955ce92745e967895f'),
    'qualified-secondary-ring-header.bin': (D5 / 'secondary-log-header-read-once/returned-block.bin',
                                            'c3adf13d0ea6ae4678758c97de3639dfcb068eca1e92fdb089d9212f3be020b4')
}
FIXED_PROTOCOL = {
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
    'whole_deadline_ms': 20000, 'bulk_timeout_ms': 2000, 'retries': 0
}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def copy_pinned(source, target, expected):
    raw = source.read_bytes()
    need(sha(raw) == expected, 'source evidence pin ' + source.name)
    target.write_bytes(raw)
    need(sha(target.read_bytes()) == expected, 'local evidence copy ' + target.name)


def run_dll(dll, args, expected):
    done = subprocess.run([str(DOTNET), str(dll), *args],
                          capture_output=True, text=True)
    need(done.returncode == expected, 'host check ' + str(args))
    return {'args': args, 'exit_code': done.returncode,
            'stdout': done.stdout, 'stderr': done.stderr}


def main():
    need(sha((HERE / 'Program.cs').read_bytes()) == PROGRAM_SHA, 'Program pin')
    need(sha((HERE / 'run-once.py').read_bytes()) == WRAPPER_SHA, 'wrapper pin')
    need(sha((HERE / 'root-with-margin.py').read_bytes()) == ROOT_ADAPTER_SHA,
         'root margin adapter pin')
    need(sha((HERE / PROJECT).read_bytes()) == PROJECT_SHA, 'project pin')
    evidence_raw = (HERE / 'evidence-input.json').read_bytes()
    need(sha(evidence_raw) == EVIDENCE_SHA, 'evidence-input pin')
    evidence = json.loads(evidence_raw)
    need(evidence['fixed_protocol'] == FIXED_PROTOCOL, 'fixed evidence protocol')
    need(evidence['no_live_io'] is True, 'offline evidence boundary')
    for name, expected in SOURCE_EVIDENCE.items():
        copy_pinned(D5 / name, HERE / name, expected)
    for name, (source, expected) in RAW_EVIDENCE.items():
        copy_pinned(source, HERE / name, expected)

    py_compile.compile(str(HERE / 'run-once.py'), doraise=True)
    py_compile.compile(str(HERE / 'root-with-margin.py'), doraise=True)
    py_compile.compile(str(HERE / 'verify-secondary-logger-arm-protocol.py'), doraise=True)
    build = subprocess.run([str(DOTNET), 'build', '-c', 'Release', '--nologo',
                            str(HERE / PROJECT)], capture_output=True, text=True)
    (HERE / 'build.log').write_text(build.stdout + build.stderr)
    need(build.returncode == 0 and '0 Warning(s)' in build.stdout and
         '0 Error(s)' in build.stdout, 'clean build')
    dll = HERE / f'bin/Release/net6.0/{ASSEMBLY}.dll'
    checks = [run_dll(dll, [], 0), run_dll(dll, ['--self-test'], 0),
              run_dll(dll, ['--execute'], 64), run_dll(dll, ['--unknown'], 63)]
    selftest = json.loads(checks[1]['stdout'])
    need(selftest == {'selfTestsPassed': 74, 'baselineTestsPassed': 26,
                      'stateMachineTestsPassed': 48,
                      'successOutputBytes': 45119, 'targetOperations': 0},
         'self-test result')
    dry = json.loads(checks[0]['stdout'])
    need(dry['targetOperations'] == 0 and dry['variant'] == 'arm-verified' and
         dry['writeHeaderHex'].lower() == FIXED_PROTOCOL['gate_write']['header_hex'],
         'dry-run fixed scope')
    wrapper_dry = subprocess.run(['python3', str(HERE / 'run-once.py')],
                                 capture_output=True, text=True)
    need(wrapper_dry.returncode == 0 and
         json.loads(wrapper_dry.stdout)['target_operations'] == 0,
         'wrapper dry run')
    with tempfile.TemporaryDirectory(prefix='logger-smoke-refusal-') as temp:
        refused = subprocess.run(['python3', str(HERE / 'run-once.py'), '--execute',
                                  '--manifest-sha256', '0' * 64,
                                  '--output', str(Path(temp) / 'unused')],
                                 capture_output=True, text=True)
        need(refused.returncode != 0 and not (Path(temp) / 'unused').exists(),
             'wrapper wrong-manifest refusal before root call')

    adapter_spec = importlib.util.spec_from_file_location(
        'offline_margin_adapter', HERE / 'root-with-margin.py')
    adapter = importlib.util.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter)
    command = 'echo ADAPTER_FAKE_ONLY'
    response = {'model': 'QN77S95FAFXZC', 'authenticated': True,
                'uid': 0, 'euid': 0, 'root_persistence': 'host-assisted',
                'global_system_files_unchanged_at_acquisition': True,
                'commands': [{'command': command, 'exit_code': 0,
                              'timed_out': False, 'stderr': '',
                              'stdout': 'ADAPTER_FAKE_ONLY\n'}]}
    encoded = json.dumps(response).encode()
    with tempfile.TemporaryDirectory(prefix='logger-margin-adapter-') as temp:
        record_path = Path(temp) / 'record.json'
        record = {'calls': []}
        completed = subprocess.CompletedProcess([], 0, encoded, b'')
        with patch.object(adapter.subprocess, 'run', return_value=completed) as mocked:
            returned = adapter.root(command, record, record_path)
        need(returned == 'ADAPTER_FAKE_ONLY\n' and mocked.call_count == 1,
             'adapter one-call success')
        argv = mocked.call_args.args[0]
        need(argv == ['python3', str(adapter.ACCESS), 'root', '--persistent-only',
                      '--timeout', '45', '--command', command],
             'adapter authenticated argv')
        need(mocked.call_args.kwargs == {'capture_output': True, 'timeout': 75},
             'adapter host margin')
        need(record['calls'][0]['remote_timeout_seconds'] == 45 and
             record['calls'][0]['host_timeout_limit_seconds'] == 75 and
             record['calls'][0]['host_timeout'] is False,
             'adapter success record')
        timeout_record = {'calls': []}
        timeout_path = Path(temp) / 'timeout-record.json'
        expired = subprocess.TimeoutExpired([], 75, output=b'', stderr=b'')
        with patch.object(adapter.subprocess, 'run', side_effect=expired) as mocked:
            try:
                adapter.root(command, timeout_record, timeout_path)
                need(False, 'adapter timeout must raise')
            except subprocess.TimeoutExpired:
                pass
        need(mocked.call_count == 1 and len(timeout_record['calls']) == 1 and
             timeout_record['calls'][0]['host_timeout'] is True,
             'adapter timeout no retry/fallback')

    names = ['Program.cs', PROJECT] + [
        f'bin/Release/net6.0/{ASSEMBLY}.{suffix}'
        for suffix in ('dll', 'deps.json', 'runtimeconfig.json')]
    local_evidence = {
        name: sha((HERE / name).read_bytes()) for name in
        [*SOURCE_EVIDENCE, *RAW_EVIDENCE, 'evidence-input.json']
    }
    manifest = {
        'schema': 'usb-fixed-secondary-logger-smoke-build-v1',
        'program_sha256': PROGRAM_SHA,
        'wrapper_sha256': WRAPPER_SHA,
        'project_sha256': PROJECT_SHA,
        'evidence_input_sha256': EVIDENCE_SHA,
        'fixed_protocol': FIXED_PROTOCOL,
        'phase_model': ['ReadyForHeader', 'ExpectingWritePayload',
                        'ExpectingReadIn', 'Unknown'],
        'max_native_json_bytes': 55000,
        'root_adapter': {
            'path': 'root-with-margin.py', 'sha256': ROOT_ADAPTER_SHA,
            'base_runner_path': '../managed-tcon-status-read/run-status-read.py',
            'base_runner_sha256': '7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a',
            'access_sha256': '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5',
            'remote_timeout_seconds': 45, 'host_timeout_seconds': 75,
            'max_command_bytes': 8192, 'max_response_bytes': 65536,
            'retry_count': 0
        },
        'files': {name: {'size': len((HERE / name).read_bytes()),
                         'sha256': sha((HERE / name).read_bytes())}
                  for name in names},
        'local_evidence': local_evidence,
        'local_files': {
            'run-once.py': {'size': len((HERE / 'run-once.py').read_bytes()),
                            'sha256': WRAPPER_SHA},
            'root-with-margin.py': {
                'size': len((HERE / 'root-with-margin.py').read_bytes()),
                'sha256': ROOT_ADAPTER_SHA}
        },
        'checks': checks,
        'wrapper_checks': {
            'dry_run_exit': wrapper_dry.returncode,
            'dry_run_stdout': wrapper_dry.stdout,
            'wrong_manifest_refused_before_output': True,
            'adapter_fake_success_calls': 1,
            'adapter_fake_timeout_calls': 1,
            'adapter_retry_or_fallback': False
        },
        'acceptance_scope': (
            'One finite volatile diagnostic gate qualification only. Exact '
            'callbacks, baseline ring, fresh-zero RT precondition, arm-one '
            'readback, no-USB three-second hold, restore-zero readback, and '
            'post-ring collection are required. Any ambiguous transfer enters '
            'Unknown and forbids later traffic. This does not establish a panel '
            'repair, physical picture state, causality, or persisted change.')
    }
    raw = (json.dumps(manifest, indent=2) + '\n').encode()
    (HERE / 'build-manifest.json').write_bytes(raw)
    print(json.dumps({
        'program_sha256': PROGRAM_SHA,
        'wrapper_sha256': WRAPPER_SHA,
        'manifest_sha256': sha(raw),
        'dll_sha256': sha(dll.read_bytes()),
        'self_tests': selftest,
        'local_evidence_files': len(local_evidence)
    }, indent=2))


if __name__ == '__main__':
    main()
