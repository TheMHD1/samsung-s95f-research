#!/usr/bin/env python3
"""Prepare, send one fixed normal-UI AppControl request, or clean the private stage.

Dry by default. Preparation performs uploads only. Every --send performs exactly
one managed invocation and never retries. Cleanup is a separate explicit phase.
"""
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
ROOT_ADAPTER = HERE / 'root-with-margin.py'
ROOT_ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT = '00000000-0000-4000-8000-000000000000'
DOTNET_SHA = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
SCHEMA = 'managed-ui-tab-launch-build-v1'
ASSEMBLY = 'ManagedUiTabLaunch'
REMOTE_NAMES = [ASSEMBLY + suffix for suffix in
                ('.dll', '.deps.json', '.runtimeconfig.json')]
REMOTE_NAMES += ['Tizen.Applications.Common.dll', 'Tizen.dll', 'Tizen.Log.dll']
MODES = {'apps': ('--apps', 'd/apps.tab'),
         'for-you': ('--for-you', 'd/ug.tab@ForYou')}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def bad(value):
        raise ValueError('non-JSON constant ' + value)
    return json.loads(raw, parse_constant=bad)


def load_module():
    need(sha(ROOT_ADAPTER.read_bytes()) == ROOT_ADAPTER_SHA, 'root adapter pin')
    spec = importlib.util.spec_from_file_location('ui_tab_root_transport', ROOT_ADAPTER)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def dir_guard(path):
    q = shlex.quote(path)
    return (f'test ! -L {q}\n' + f'test -d {q}\n' +
            f'test "$(stat -c "%u:%g:%a" {q})" = "0:0:700"\n')


def file_guard(path, size=None):
    q = shlex.quote(path)
    out = (f'test ! -L {q}\n' + f'test -f {q}\n' +
           f'test "$(stat -c "%u:%g:%a" {q})" = "0:0:600"\n')
    if size is not None:
        out += f'test "$(wc -c < {q})" = {size}\n'
    return out


def exact_inventory(path, names):
    q = shlex.quote(path)
    cases = '|'.join(shlex.quote(name) for name in sorted(names))
    return (f'count=0\nfor item in {q}/* {q}/.[!.]* {q}/..?*; do\n' +
            '  test -e "$item" || test -L "$item" || continue\n' +
            '  name=${item##*/}\n' +
            f'  case "$name" in {cases}) ;; *) exit 91 ;; esac\n' +
            '  count=$((count+1))\ndone\n' + f'test "$count" = {len(names)}\n')


def load_contract(expected_manifest_sha):
    manifest_raw = (HERE / 'build-manifest.json').read_bytes()
    need(re.fullmatch(r'[0-9a-f]{64}', expected_manifest_sha or '') is not None,
         'manifest SHA required')
    need(sha(manifest_raw) == expected_manifest_sha, 'reviewed aggregate manifest')
    manifest = strict_json(manifest_raw)
    need(manifest.get('schema') == SCHEMA, 'manifest schema')
    files = manifest.get('files')
    expected = {'Program.cs', 'ManagedUiTabLaunch.csproj', 'run-once.py',
                'root-with-margin.py'}
    expected.update('bin/Release/net6.0/' + name for name in REMOTE_NAMES)
    need(isinstance(files, dict) and set(files) == expected, 'manifest inventory')
    for name, row in files.items():
        raw = (HERE / name).read_bytes()
        need(row == {'size': len(raw), 'sha256': sha(raw)}, 'local pin ' + name)
    staged = {name: (HERE / 'bin/Release/net6.0' / name).read_bytes()
              for name in REMOTE_NAMES}
    return manifest_raw, manifest, staged


def integrity(stage, staged):
    text = dir_guard(stage) + exact_inventory(stage, REMOTE_NAMES)
    for name in REMOTE_NAMES:
        target = stage + '/' + name
        raw = staged[name]
        text += file_guard(target, len(raw))
        text += (f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" '
                 f'= {sha(raw)}\n')
    return text


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def new_output(path):
    need(path is not None and path.is_absolute(), 'absolute output required')
    path.mkdir(parents=True, exist_ok=False)


def prepare(args, root):
    manifest_raw, _, staged = load_contract(args.manifest_sha256)
    new_output(args.output)
    record_path = args.output / 'prepare-record.json'
    stage = '/tmp/researcher-ui-tab-' + uuid.uuid4().hex
    record = {'schema': 'managed-ui-tab-prepare-record-v1', 'phase': 'prepare',
              'manifest_sha256': sha(manifest_raw),
              'wrapper_sha256': sha(Path(__file__).read_bytes()),
              'root_adapter_sha256': ROOT_ADAPTER_SHA, 'expected_boot_id': BOOT,
              'remote_stage': stage, 'calls': [], 'cleanup_required': True,
              'target_operations': 0, 'no_retry': True}
    root.save(record_path, record)

    def call(command):
        return root.root(command, record, record_path)

    call('set -eu\numask 077\n' +
         f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
         f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n' +
         f'test ! -e {shlex.quote(stage)}\ntest ! -L {shlex.quote(stage)}\n' +
         f'mkdir -m 700 {shlex.quote(stage)}\n' + dir_guard(stage) +
         'cat /proc/uptime\necho PRIVATE_STAGE_CREATED\n')

    for name in REMOTE_NAMES:
        raw = staged[name]
        target = stage + '/' + name
        encoded = base64.b64encode(raw).decode()
        raw_offset = 0
        for offset in range(0, len(encoded), 5000):
            chunk = encoded[offset:offset + 5000]
            decoded = base64.b64decode(chunk, validate=True)
            initialize = (f'test ! -e {shlex.quote(target)}\n'
                          f'test ! -L {shlex.quote(target)}\n'
                          f': > {shlex.quote(target)}\n'
                          f'chmod 600 {shlex.quote(target)}\n') if offset == 0 else ''
            call('set -eu\numask 077\n' +
                 f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
                 dir_guard(stage) + initialize + file_guard(target, raw_offset) +
                 f'printf %s {shlex.quote(chunk)} | base64 -d >> {shlex.quote(target)}\n' +
                 file_guard(target, raw_offset + len(decoded)) +
                 'echo STAGED_CHUNK\n')
            raw_offset += len(decoded)
        need(raw_offset == len(raw), 'local upload extent ' + name)
        call('set -eu\numask 077\n' +
             f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
             dir_guard(stage) + file_guard(target, len(raw)) +
             f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {sha(raw)}\n' +
             'echo STAGED_FILE\n')

    final = call('set -eu\numask 077\n' +
                 f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
                 integrity(stage, staged) +
                 'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n'
                 'echo PRIVATE_STAGE_READY\n')
    lines = final.splitlines()
    need(len(lines) == 3 and lines[0] == BOOT and lines[2] == 'PRIVATE_STAGE_READY' and
         re.fullmatch(r'[0-9.]+ [0-9.]+', lines[1]) is not None, 'prepare receipt')
    prepared = {'schema': 'managed-ui-tab-prepared-v1',
                'manifest_sha256': sha(manifest_raw),
                'wrapper_sha256': sha(Path(__file__).read_bytes()),
                'root_adapter_sha256': ROOT_ADAPTER_SHA,
                'expected_boot_id': BOOT, 'remote_stage': stage,
                'files': {name: {'size': len(staged[name]), 'sha256': sha(staged[name])}
                          for name in REMOTE_NAMES},
                'prepared_boot_id': lines[0], 'prepared_uptime': lines[1],
                'cleanup_required': True, 'target_operations': 0}
    save_json(args.output / 'prepared.json', prepared)
    print(json.dumps({'schema': 'managed-ui-tab-prepare-result-v1',
                      'prepared': str(args.output / 'prepared.json'),
                      'remote_stage': stage, 'cleanup_required': True,
                      'target_operations': 0}, separators=(',', ':')))


def parse_prepared(path):
    need(path is not None and path.is_absolute() and path.is_file(),
         'absolute prepared record required')
    raw = path.read_bytes()
    value = strict_json(raw)
    expected_keys = {'schema', 'manifest_sha256', 'wrapper_sha256',
                     'root_adapter_sha256', 'expected_boot_id', 'remote_stage',
                     'files', 'prepared_boot_id', 'prepared_uptime',
                     'cleanup_required', 'target_operations'}
    need(isinstance(value, dict) and set(value) == expected_keys, 'prepared schema keys')
    need(value['schema'] == 'managed-ui-tab-prepared-v1' and
         value['expected_boot_id'] == BOOT and value['prepared_boot_id'] == BOOT and
         value['root_adapter_sha256'] == ROOT_ADAPTER_SHA and
         value['cleanup_required'] is True and value['target_operations'] == 0,
         'prepared identity')
    need(re.fullmatch(r'/tmp/researcher-ui-tab-[0-9a-f]{32}', value['remote_stage']) is not None,
         'prepared private path')
    return raw, value


def parse_native(stdout, mode, page):
    rows = []
    for line in stdout.splitlines():
        if line.startswith('{'):
            rows.append(strict_json(line))
        else:
            need(line.startswith('[GC_INFO] '), 'unclassified native output')
    need(len(rows) == 1 and isinstance(rows[0], dict), 'one native outcome')
    value = rows[0]
    request = value.get('request')
    need(value.get('schema') == 'managed-ui-tab-launch-v1' and
         value.get('mode') == mode and isinstance(request, dict), 'native identity')
    need(request == {'application_id': 'com.samsung.tv.csfs',
                     'extra_key': 'switch_page', 'extra_value': page,
                     'operation_set': False, 'no_raise_window_set': False},
         'fixed request contract')
    need(value.get('expected_boot_id') == BOOT and
         value.get('boot_id_before') == BOOT and value.get('boot_id_after') == BOOT and
         value.get('boot_matched_before') is True and
         value.get('boot_matched_after') is True, 'native boot contract')
    need(value.get('architecture') == 'Arm' and value.get('pointer_bytes') == 4 and
         value.get('little_endian') is True and value.get('abi_accepted') is True,
         'native ARM32 contract')
    need(value.get('physical_picture_observed') is False and
         value.get('execution_confirmed') is False and
         value.get('target_operations') in (0, 1), 'claim/operation contract')
    need(isinstance(value.get('uptime_before'), str) and
         isinstance(value.get('uptime_after'), str), 'native uptime contract')
    return value


def send(args, root):
    prepared_raw, prepared = parse_prepared(args.prepared)
    _, _, staged = load_contract(prepared['manifest_sha256'])
    need(prepared['wrapper_sha256'] == sha(Path(__file__).read_bytes()), 'prepared wrapper pin')
    need(prepared['files'] == {name: {'size': len(staged[name]), 'sha256': sha(staged[name])}
                                for name in REMOTE_NAMES}, 'prepared file pins')
    mode = 'apps' if args.apps else 'for-you'
    option, page = MODES[mode]
    new_output(args.output)
    record_path = args.output / 'action-record.json'
    record = {'schema': 'managed-ui-tab-action-record-v1', 'phase': 'send',
              'mode': mode, 'page': page, 'prepared_sha256': sha(prepared_raw),
              'remote_stage': prepared['remote_stage'], 'calls': [],
              'no_retry': True, 'expected_invocations': 1,
              'physical_picture_observed': False, 'execution_confirmed': False}
    root.save(record_path, record)
    stage = prepared['remote_stage']
    dll = stage + '/' + ASSEMBLY + '.dll'
    command = ('set -eu\numask 077\n' +
               f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
               f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n' +
               integrity(stage, staged) +
               f'/usr/bin/dotnet {shlex.quote(dll)} {option}\n')
    stdout = root.root(command, record, record_path)
    (args.output / 'native.stdout.txt').write_text(stdout)
    outcome = parse_native(stdout, mode, page)
    save_json(args.output / 'native-outcome.json', outcome)
    result = {'schema': 'managed-ui-tab-action-result-v1', 'mode': mode, 'page': page,
              'send_attempted': outcome['send_attempted'],
              'send_returned': outcome['send_returned'],
              'exception': outcome['exception'], 'target_operations': outcome['target_operations'],
              'physical_picture_observed': False, 'execution_confirmed': False,
              'cleanup_required': True}
    save_json(args.output / 'result.json', result)
    print(json.dumps(result, separators=(',', ':')))


def cleanup(args, root):
    prepared_raw, prepared = parse_prepared(args.prepared)
    _, _, staged = load_contract(prepared['manifest_sha256'])
    need(prepared['wrapper_sha256'] == sha(Path(__file__).read_bytes()), 'prepared wrapper pin')
    need(prepared['files'] == {name: {'size': len(staged[name]), 'sha256': sha(staged[name])}
                                for name in REMOTE_NAMES}, 'prepared file pins')
    new_output(args.output)
    record_path = args.output / 'cleanup-record.json'
    stage = prepared['remote_stage']
    record = {'schema': 'managed-ui-tab-cleanup-record-v1', 'phase': 'cleanup',
              'prepared_sha256': sha(prepared_raw), 'remote_stage': stage,
              'calls': [], 'target_operations': 0}
    root.save(record_path, record)
    command = ('set -eu\numask 077\n' +
               f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
               integrity(stage, staged) +
               'rm ' + ' '.join(shlex.quote(stage + '/' + name) for name in REMOTE_NAMES) + '\n' +
               f'rmdir {shlex.quote(stage)}\n' +
               f'test ! -e {shlex.quote(stage)}\necho PRIVATE_STAGE_ABSENT\n')
    stdout = root.root(command, record, record_path)
    need(stdout == 'PRIVATE_STAGE_ABSENT\n', 'cleanup receipt')
    result = {'schema': 'managed-ui-tab-cleanup-result-v1', 'stage_absent': True,
              'target_operations': 0}
    save_json(args.output / 'result.json', result)
    print(json.dumps(result, separators=(',', ':')))


def main():
    parser = argparse.ArgumentParser()
    phase = parser.add_mutually_exclusive_group()
    phase.add_argument('--prepare', action='store_true')
    phase.add_argument('--send', action='store_true')
    phase.add_argument('--cleanup', action='store_true')
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument('--apps', action='store_true')
    destination.add_argument('--for-you', action='store_true')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--prepared', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not (args.prepare or args.send or args.cleanup):
        need(not any((args.apps, args.for_you, args.manifest_sha256, args.prepared, args.output)),
             'phase required for options')
        print(json.dumps({'dry_run': True, 'target_operations': 0,
                          'phases': ['prepare', 'send', 'cleanup'],
                          'destinations': MODES, 'automatic_retry': False,
                          'automatic_cleanup': False}, separators=(',', ':')))
        return
    if args.prepare:
        need(not any((args.apps, args.for_you, args.prepared)) and args.output is not None and
             args.manifest_sha256 is not None, 'prepare arguments')
    elif args.send:
        need((args.apps ^ args.for_you) and args.prepared is not None and args.output is not None and
             args.manifest_sha256 is None, 'send arguments')
    else:
        need(not any((args.apps, args.for_you, args.manifest_sha256)) and
             args.prepared is not None and args.output is not None, 'cleanup arguments')
    root = load_module()
    if args.prepare:
        prepare(args, root)
    elif args.send:
        send(args, root)
    else:
        cleanup(args, root)


if __name__ == '__main__':
    main()
