#!/usr/bin/env python3
"""Offline reproducible build and manifest for the fixed UI-tab sender."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
DOTNET = HERE.parents[2] / 'live-cast/sdk/runtime/dotnet'
PROJECT = 'ManagedUiTabLaunch.csproj'
ASSEMBLY = 'ManagedUiTabLaunch'
PROGRAM_SHA = '43aa6067d1012c318d84b4204a6708da0df8a77bfb8a1f3d45f538090faf32c0'
PROJECT_SHA = 'db98549468c2cc3c57d9540323110e16657b50c0e1d54c7cbb85f54ec574bdbb'
DOTNET_SHA = '6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36'
ROOT_ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
FRAMEWORK = HERE.parents[2] / 'live-cast/framework'
FRAMEWORK_PINS = {
    'Tizen.Applications.Common.dll': 'f9d17e5e10632d4001a5381331661104302cc95d12f61567cc61c6cb74ea737c',
    'Tizen.dll': 'a4f743fd522517584641eb86afe2403ce4134e6e40768da9998242cb095ca93e',
}
REMOTE_NAMES = [ASSEMBLY + suffix for suffix in
                ('.dll', '.deps.json', '.runtimeconfig.json')]
REMOTE_NAMES += list(FRAMEWORK_PINS)


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(argv, expected=0):
    done = subprocess.run(argv, capture_output=True, text=True)
    need(done.returncode == expected, 'command exit ' + repr(argv))
    return {'argv': [str(x) for x in argv], 'exit_code': done.returncode,
            'stdout': done.stdout, 'stderr': done.stderr}


def build(project):
    restore = run([str(DOTNET), 'restore', '--ignore-failed-sources',
                   '-p:RestoreSources=', str(project)])
    built = run([str(DOTNET), 'build', '-c', 'Release', '--no-restore',
                 '--nologo', str(project)])
    need('0 Warning(s)' in built['stdout'] and '0 Error(s)' in built['stdout'],
         'clean build')
    return restore, built


def main():
    need(sha(DOTNET.read_bytes()) == DOTNET_SHA, 'offline SDK host pin')
    need(sha((HERE / 'Program.cs').read_bytes()) == PROGRAM_SHA, 'Program pin')
    need(sha((HERE / PROJECT).read_bytes()) == PROJECT_SHA, 'project pin')
    need(sha((HERE / 'root-with-margin.py').read_bytes()) == ROOT_ADAPTER_SHA,
         'root adapter pin')
    for name, expected in FRAMEWORK_PINS.items():
        need(sha((FRAMEWORK / name).read_bytes()) == expected, 'framework input pin ' + name)

    restore, built = build(HERE / PROJECT)
    (HERE / 'build.log').write_text(restore['stdout'] + restore['stderr'] +
                                    built['stdout'] + built['stderr'])
    output = HERE / 'bin/Release/net6.0'
    for name, expected in FRAMEWORK_PINS.items():
        need(sha((output / name).read_bytes()) == expected, 'copied framework pin ' + name)

    dll = output / (ASSEMBLY + '.dll')
    dry = run([str(DOTNET), str(dll)])
    invalid = run([str(DOTNET), str(dll), '--invalid'], 63)
    abi = run([str(DOTNET), str(dll), '--apps'], 64)
    dry_json = json.loads(dry['stdout'])
    abi_json = json.loads(abi['stdout'])
    need(dry_json == {
        'schema': 'managed-ui-tab-launch-dry-v1', 'dry_run': True,
        'target_operations': 0, 'application_id': 'com.samsung.tv.csfs',
        'extra_key': 'switch_page',
        'fixed_modes': {'--apps': 'd/apps.tab', '--for-you': 'd/ug.tab@ForYou'},
        'operation_set': False, 'no_raise_window_set': False, 'retries': 0,
        'physical_picture_observed': False, 'execution_confirmed': False}, 'dry contract')
    need(invalid['stdout'] == invalid['stderr'] == '', 'invalid CLI silent refusal')
    need(abi_json['abi_accepted'] is False and abi_json['request_constructed'] is False and
         abi_json['send_attempted'] is False and abi_json['target_operations'] == 0,
         'host ABI refusal before request')
    wrapper_dry = run(['python3', str(HERE / 'run-once.py')])
    need(json.loads(wrapper_dry['stdout'])['target_operations'] == 0,
         'wrapper dry contract')
    wrapper_fake = run(['python3', str(HERE / 'test-wrapper.py')])
    fake_summary = json.loads(wrapper_fake['stdout'].splitlines()[-1])
    need(fake_summary == {'fakeRootTestsPassed': 8, 'prepareUiInvocations': 0,
                          'sendRootCalls': {'apps': 1, 'for-you': 1},
                          'cleanupManagedInvocations': 0, 'targetOperations': 0},
         'wrapper fake-root checks')

    with tempfile.TemporaryDirectory(prefix='ui-tab-repro-') as temporary:
        root = Path(temporary)
        shutil.copy2(HERE / 'Program.cs', root / 'Program.cs')
        shutil.copy2(HERE / PROJECT, root / PROJECT)
        build(root / PROJECT)
        repeated = root / 'bin/Release/net6.0'
        for name in REMOTE_NAMES:
            need((repeated / name).read_bytes() == (output / name).read_bytes(),
                 'reproducible artifact ' + name)

    files = ['Program.cs', PROJECT, 'run-once.py', 'root-with-margin.py']
    files += ['bin/Release/net6.0/' + name for name in REMOTE_NAMES]
    manifest = {
        'schema': 'managed-ui-tab-launch-build-v1',
        'expected_boot_id': '00000000-0000-4000-8000-000000000000',
        'fixed_request': {
            'application_id': 'com.samsung.tv.csfs', 'extra_key': 'switch_page',
            'modes': {'apps': 'd/apps.tab', 'for-you': 'd/ug.tab@ForYou'},
            'operation_set': False, 'no_raise_window_set': False,
            'send_calls_per_invocation': 1, 'retries': 0},
        'phases': {
            'prepare': 'private-stage-only-no-AppControl',
            'send': 'one-fixed-managed-invocation-no-retry',
            'cleanup': 'explicit-after-all-actions'},
        'target_runtime': {'architecture': 'Arm', 'pointer_bytes': 4,
                           'little_endian': True, 'dotnet_sha256':
                           'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'},
        'root_adapter': {'sha256': ROOT_ADAPTER_SHA, 'remote_timeout_seconds': 45,
                         'host_timeout_seconds': 75, 'max_response_bytes': 65536},
        'framework_inputs': FRAMEWORK_PINS,
        'files': {name: {'size': len((HERE / name).read_bytes()),
                         'sha256': sha((HERE / name).read_bytes())} for name in files},
        'offline_files': {
            name: {'size': len((HERE / name).read_bytes()),
                   'sha256': sha((HERE / name).read_bytes())}
            for name in ('build.py', 'README.md', 'test-wrapper.py')},
        'checks': {'dry': dry, 'invalid_cli': invalid,
                   'host_abi_refusal': abi, 'wrapper_dry': wrapper_dry,
                   'wrapper_fake_root': wrapper_fake},
        'reproducible_build': True,
        'network_dependencies': 0,
        'target_operations_during_build': 0,
        'claims': {'physical_picture_observed': False, 'execution_confirmed': False}
    }
    raw = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    (HERE / 'build-manifest.json').write_bytes(raw)
    print(json.dumps({'manifest_sha256': sha(raw),
                      'program_sha256': PROGRAM_SHA,
                      'wrapper_sha256': sha((HERE / 'run-once.py').read_bytes()),
                      'dll_sha256': sha(dll.read_bytes()),
                      'checks': ['dry', 'invalid-cli', 'host-ABI-refusal',
                                 'wrapper-dry', 'wrapper-fake-root',
                                 'reproducible-build']}, indent=2))


if __name__ == '__main__':
    main()
