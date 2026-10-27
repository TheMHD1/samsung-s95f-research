#!/usr/bin/env python3
"""Verify the fixed logger-smoke build and local evidence without target I/O."""
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
BUILD = BASE / 'managed-usb-secondary-logger-smoke'
DOTNET = BASE.parents[1] / 'live-cast/sdk/runtime/dotnet'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def header(target, address, length):
    return struct.pack('<III', target, address, length).hex()


def main():
    pins = {
        'Program.cs': 'abbfd7bbfafe11c4204934187600983379db1a93de9fde4fe9ac1fe3736a6991',
        'run-once.py': 'eeb852c8e1b9a0d2611abc17e853ad2ee834f4e42712b2810bf8309eda5e59ca',
        'root-with-margin.py': 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a',
        'build-manifest.json': '150189300d1fb78507e8dcad330cc1ca2ebbef05617d5741506a062986445b8b',
        'bin/Release/net6.0/ManagedUsbSecondaryLoggerSmoke.dll': '03296496c42c01453d05a02678ef7a79d121e5822ff17097f7f6ae8b34eea3b5'
    }
    for name, expected in pins.items():
        need(sha((BUILD / name).read_bytes()) == expected, 'build pin ' + name)
    manifest = json.loads((BUILD / 'build-manifest.json').read_text())
    need(manifest['schema'] == 'usb-fixed-secondary-logger-smoke-build-v1', 'schema')
    protocol = manifest['fixed_protocol']
    expected = {
        'callback_read': ('0x101', '0x45000580', 64,
                          header(0x101, 0x45000580, 64)),
        'ring_read': ('0x101', '0x20200000', 0x3c0c,
                      header(0x101, 0x20200000, 0x3c0c)),
        'rt_read': ('0x101', '0x47012400', 64,
                    header(0x101, 0x47012400, 64))
    }
    for name, (target, address, length, raw_header) in expected.items():
        need(protocol[name] == {'target': target, 'address': address,
                                'length': length, 'header_hex': raw_header},
             'fixed read ' + name)
    need(protocol['gate_write'] == {
        'target': '0x102', 'address': '0x47012406', 'length': 2,
        'header_hex': header(0x102, 0x47012406, 2),
        'arm_payload_hex': '0100', 'restore_payload_hex': '0000'},
        'fixed write')
    need(protocol['hold_ms'] == 3000 and
         protocol['hard_arm_deadline_ms'] == 10000 and
         protocol['whole_deadline_ms'] == 20000 and
         protocol['bulk_timeout_ms'] == 2000 and protocol['retries'] == 0,
         'timing and retry limits')
    need(manifest['phase_model'] == ['ReadyForHeader', 'ExpectingWritePayload',
                                     'ExpectingReadIn', 'Unknown'], 'phase model')
    need(manifest['max_native_json_bytes'] == 55000, 'output limit')
    need(manifest['wrapper_sha256'] == pins['run-once.py'], 'wrapper manifest pin')
    need(manifest['root_adapter'] == {
        'path': 'root-with-margin.py', 'sha256': pins['root-with-margin.py'],
        'base_runner_path': '../managed-tcon-status-read/run-status-read.py',
        'base_runner_sha256': '7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a',
        'access_sha256': '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5',
        'remote_timeout_seconds': 45, 'host_timeout_seconds': 75,
        'max_command_bytes': 8192, 'max_response_bytes': 65536,
        'retry_count': 0}, 'root adapter manifest')
    expected_files = {'Program.cs', 'ManagedUsbSecondaryLoggerSmoke.csproj',
                      *('bin/Release/net6.0/ManagedUsbSecondaryLoggerSmoke.' + suffix
                        for suffix in ('dll', 'deps.json', 'runtimeconfig.json'))}
    need(set(manifest['files']) == expected_files, 'deployment inventory')
    for name, row in manifest['files'].items():
        raw = (BUILD / name).read_bytes()
        need(row == {'size': len(raw), 'sha256': sha(raw)}, 'manifest file ' + name)
    for name, expected_sha in manifest['local_evidence'].items():
        need(sha((BUILD / name).read_bytes()) == expected_sha,
             'local evidence ' + name)
    for name, row in manifest['local_files'].items():
        raw = (BUILD / name).read_bytes()
        need(row == {'size': len(raw), 'sha256': sha(raw)},
             'local helper file ' + name)
    need(set(manifest['local_files']) == {'run-once.py', 'root-with-margin.py'},
         'local helper inventory')
    need(manifest['wrapper_checks'] == {
        'dry_run_exit': 0,
        'dry_run_stdout': ('{"target_operations": 0, "variant": "arm-verified", '
                           '"fixed_write_header": "020100000624014702000000", '
                           '"arm_payload": "0100", "restore_payload": "0000", '
                           '"hold_ms": 3000, "hard_arm_deadline_ms": 10000}\n'),
        'wrong_manifest_refused_before_output': True,
        'adapter_fake_success_calls': 1,
        'adapter_fake_timeout_calls': 1,
        'adapter_retry_or_fallback': False}, 'wrapper checks')
    selftest = manifest['checks'][1]
    need(selftest['args'] == ['--self-test'] and selftest['exit_code'] == 0,
         'self-test check row')
    need(json.loads(selftest['stdout']) == {
        'selfTestsPassed': 74, 'baselineTestsPassed': 26,
        'stateMachineTestsPassed': 48, 'successOutputBytes': 45119,
        'targetOperations': 0}, 'self-test result')
    need(manifest['checks'][2]['args'] == ['--execute'] and
         manifest['checks'][2]['exit_code'] == 64 and
         manifest['checks'][2]['stdout'] == 'REFUSED_ARM32_ABI\n',
         'host ABI refusal')
    dll = BUILD / 'bin/Release/net6.0/ManagedUsbSecondaryLoggerSmoke.dll'
    rerun = subprocess.run([str(DOTNET), str(dll), '--self-test'],
                           capture_output=True, text=True)
    need(rerun.returncode == 0 and rerun.stdout == selftest['stdout'],
         'fresh zero-I/O self-test replay')
    dry = subprocess.run(['python3', str(BUILD / 'run-once.py')],
                         capture_output=True, text=True)
    need(dry.returncode == 0 and json.loads(dry.stdout)['target_operations'] == 0,
         'wrapper zero-I/O default')
    wrapper_source = (BUILD / 'run-once.py').read_text()
    need(wrapper_source.count('selftest_stdout = call(selftest_command)') == 1 and
         wrapper_source.count('stdout = call(execute_command)') == 1 and
         '/usr/bin/dotnet {dll} --self-test' in wrapper_source and
         '/usr/bin/dotnet {dll} --execute' in wrapper_source,
         'separate one-selftest one-execute calls')
    adapter_spec = importlib.util.spec_from_file_location(
        'verified_margin_adapter', BUILD / 'root-with-margin.py')
    adapter = importlib.util.module_from_spec(adapter_spec)
    adapter_spec.loader.exec_module(adapter)
    need(adapter.REMOTE_TIMEOUT_SECONDS == 45 and
         adapter.HOST_TIMEOUT_SECONDS == 75 and adapter.MAX_COMMAND == 8192 and
         adapter.MAX_RESPONSE == 65536 and
         sha(adapter.ACCESS.read_bytes()) ==
         '3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5' and
         sha(adapter.RUNNER.read_bytes()) ==
         '7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a',
         'loaded margin adapter bounds and dependencies')
    blocked = HERE / 'blocked-wrapper-revision'
    blocked_pins = {
        'helper/Program.cs': 'abbfd7bbfafe11c4204934187600983379db1a93de9fde4fe9ac1fe3736a6991',
        'helper/run-once.py': 'd488ac74d5999f1633fd64600dab3b39bed1164d3ba2da2f158127a1a1f48e4a',
        'helper/build-manifest.json': '6293e99052cac89be90b7d90a5654673106bcf5f16a853d0fd6ee3d02ba6f21b',
        'helper/bin/Release/net6.0/ManagedUsbSecondaryLoggerSmoke.dll': '03296496c42c01453d05a02678ef7a79d121e5822ff17097f7f6ae8b34eea3b5',
        'd6/architecture-review.md': '26d2f6227b7ec5d960b9be6569bc85f23d0513b8233f3c3e8279e5dc26021062',
        'd6/verify-offline-build.py': '09ebeb6543995407817b287523897ef10cce8bfc33a2a31d7c21ef88c68e0405'
    }
    for name, expected_sha in blocked_pins.items():
        need(sha((blocked / name).read_bytes()) == expected_sha,
             'blocked revision pin ' + name)
    print(json.dumps({
        'status': 'PASS',
        'target_operations': 0,
        'manifest_sha256': pins['build-manifest.json'],
        'self_tests': 74,
        'success_output_bytes': 45119,
        'live_execution_approved': False,
        'physical_picture_observed': False,
        'repair_established': False
    }, sort_keys=True))


if __name__ == '__main__':
    main()
