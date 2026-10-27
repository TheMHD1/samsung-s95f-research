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
ASSEMBLY = 'ManagedAppsKeyLaunch'
INSPECTION_PROJECT = 'inspection/AssemblyRefs.csproj'
PROGRAM_SHA = '9bc3f862015c52640fc53d2ecbe46a412821d367988dba3a97f3d0d37c9a4d54'
PROJECT_SHA = 'f0cf1428b53e85a95f31b451b2704da184c8047ca84c1451fd1577ef0bce976b'
DOTNET_SHA = '6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36'
ROOT_ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
FRAMEWORK = HERE.parents[2] / 'live-cast/framework'
FRAMEWORK_PINS = {
    'Tizen.Applications.Common.dll': 'f9d17e5e10632d4001a5381331661104302cc95d12f61567cc61c6cb74ea737c',
    'Tizen.dll': 'a4f743fd522517584641eb86afe2403ce4134e6e40768da9998242cb095ca93e',
    'Tizen.Log.dll': 'a2b27f2033177328d0d609f8fab47f3c45bc20a0a30b5f29992b142b02fdf66b',
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
    inspect_restore, inspect_build = build(HERE / INSPECTION_PROJECT)
    closure_run = run([
        str(DOTNET), str(HERE / 'inspection/bin/Release/net6.0/AssemblyRefs.dll'),
        *(str(FRAMEWORK / name) for name in FRAMEWORK_PINS)])
    closure = json.loads(closure_run['stdout'])
    need(closure.get('schema') == 'managed-ui-tab-dependency-closure-v1',
         'closure schema')
    rows = {row['file']: row for row in closure['files']}
    need(set(rows) == set(FRAMEWORK_PINS), 'closure file inventory')
    managed = {
        name: {item['name'] for item in row['assembly_references']
               if not item['name'].startswith('System.')}
        for name, row in rows.items()}
    need(managed == {
        'Tizen.Applications.Common.dll': {'Tizen', 'Tizen.Log'},
        'Tizen.dll': {'Tizen.Log'}, 'Tizen.Log.dll': set()},
        'closed nonframework managed references')
    native = {name: row['native_module_references'] for name, row in rows.items()}
    need(native == {
        'Tizen.Applications.Common.dll': [
            'libapp-core-ui-cpp.so.1', 'libbase-utils-i18n.so.0', 'libbundle.so.0',
            'libc.so.6', 'libcapi-appfw-app-common.so.0',
            'libcapi-appfw-app-control.so.0', 'libcapi-appfw-app-manager.so.0',
            'libcapi-appfw-application.so.0', 'libglib-2.0.so.0',
            'libiniparser.so.1', 'librpc-port.so.1', 'librua.so.0'],
        'Tizen.dll': ['libcapi-base-common.so.0', 'libdlog.so.0', 'libvconf.so.0'],
        'Tizen.Log.dll': ['libdlog.so.0']}, 'native module reference inventory')
    closure_raw = (json.dumps(closure, indent=2) + '\n').encode()
    (HERE / 'managed-dependency-closure.json').write_bytes(closure_raw)
    (HERE / 'build.log').write_text(
        restore['stdout'] + restore['stderr'] + built['stdout'] + built['stderr'] +
        inspect_restore['stdout'] + inspect_restore['stderr'] +
        inspect_build['stdout'] + inspect_build['stderr'])
    output = HERE / 'bin/Release/net6.0'
    for name, expected in FRAMEWORK_PINS.items():
        need(sha((output / name).read_bytes()) == expected, 'copied framework pin ' + name)

    dll = output / (ASSEMBLY + '.dll')
    dry = run([str(DOTNET), str(dll)])
    invalid = run([str(DOTNET), str(dll), '--invalid'], 63)
    abi = run([str(DOTNET), str(dll), '--apps-key'], 64)
    dry_json = json.loads(dry['stdout'])
    abi_json = json.loads(abi['stdout'])
    need(dry_json == {
        'schema': 'managed-apps-key-launch-dry-v1', 'dry_run': True,
        'target_operations': 0, 'application_id': 'com.samsung.tv.csfs',
        'request': {'application_id': 'com.samsung.tv.csfs', 'switch_page': 'd/apps.tab',
                    'entry_point': 'apps_key'},
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
    need(fake_summary == {'fakeRootTestsPassed': 7, 'prepareUiInvocations': 0,
                          'sendRootCalls': {'apps-key': 1},
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
        'schema': 'managed-apps-key-launch-build-v1',
        'expected_boot_id': '00000000-0000-4000-8000-000000000000',
        'fixed_request': {
            'application_id': 'com.samsung.tv.csfs',
            'extras': {'switch_page': 'd/apps.tab', 'entry_point': 'apps_key'},
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
        'managed_dependency_closure': {
            'report': 'managed-dependency-closure.json',
            'sha256': sha(closure_raw),
            'nonframework_references_closed_by_staged_files': True,
            'native_references_are_target_stock_not_staged': True},
        'files': {name: {'size': len((HERE / name).read_bytes()),
                         'sha256': sha((HERE / name).read_bytes())} for name in files},
        'offline_files': {
            name: {'size': len((HERE / name).read_bytes()),
                   'sha256': sha((HERE / name).read_bytes())}
            for name in ('build.py', 'README.md', 'test-wrapper.py',
                         'inspection/Program.cs', 'inspection/AssemblyRefs.csproj',
                         'managed-dependency-closure.json')},
        'checks': {'dry': dry, 'invalid_cli': invalid,
                   'host_abi_refusal': abi, 'wrapper_dry': wrapper_dry,
                   'wrapper_fake_root': wrapper_fake,
                   'dependency_closure': {
                       'managed_nonframework_refs': {
                           name: sorted(values) for name, values in managed.items()},
                       'native_module_refs': native}},
        'reproducible_build': True,
        'network_dependencies': 0,
        'target_operations_during_build': 0,
        'claims': {'physical_picture_observed': False, 'execution_confirmed': False}
    }
    raw = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    (HERE / 'build-manifest.json').write_bytes(raw)
    # Exercise the unmodified production loader against the exact manifest just
    # written. This is deliberately after serialization: the check result is
    # retained separately and never changes the manifest or its file pins.
    loader_spec = __import__('importlib.util').util.spec_from_file_location(
        'apps_key_contract_loader', HERE / 'run-once.py')
    loader = __import__('importlib.util').util.module_from_spec(loader_spec)
    loader_spec.loader.exec_module(loader)
    loaded_raw, loaded_manifest, loaded_staged = loader.load_contract(sha(raw))
    need(loaded_raw == raw and loaded_manifest == manifest and
         set(loaded_staged) == set(REMOTE_NAMES), 'post-build production contract load')
    post_build = {'schema': 'managed-apps-key-post-build-contract-check-v1',
                  'manifest_sha256': sha(raw), 'loader_schema': loader.SCHEMA,
                  'loaded_file_count': len(loaded_staged), 'passed': True,
                  'target_operations': 0}
    (HERE / 'post-build-contract-check.json').write_text(
        json.dumps(post_build, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'manifest_sha256': sha(raw),
                      'program_sha256': PROGRAM_SHA,
                      'wrapper_sha256': sha((HERE / 'run-once.py').read_bytes()),
                      'dll_sha256': sha(dll.read_bytes()),
                      'checks': ['dry', 'invalid-cli', 'host-ABI-refusal',
                                 'wrapper-dry', 'wrapper-fake-root',
                                 'managed-dependency-closure',
                                 'reproducible-build']}, indent=2))


if __name__ == '__main__':
    main()
