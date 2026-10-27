#!/usr/bin/env python3
"""Verify the fixed logger-smoke build and local evidence without target I/O."""
from pathlib import Path
import hashlib
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
        'run-once.py': 'd488ac74d5999f1633fd64600dab3b39bed1164d3ba2da2f158127a1a1f48e4a',
        'build-manifest.json': '6293e99052cac89be90b7d90a5654673106bcf5f16a853d0fd6ee3d02ba6f21b',
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
