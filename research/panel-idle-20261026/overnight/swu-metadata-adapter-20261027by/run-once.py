#!/usr/bin/env python3
"""Central fixed metadata adapter runner. Dry default, no automatic retry."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ADAPTER = BASE / 'managed-ui-tab-launch/root-with-margin.py'
ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT = '00000000-0000-4000-8000-000000000000'
DOTNET_SHA = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
STAGE = '/tmp/swu-metadata-20261027by'
PAYLOAD = {name: HERE / 'bin/Release/net6.0' / name for name in
           ('SwuMetadataAdapter.dll', 'SwuMetadataAdapter.deps.json', 'SwuMetadataAdapter.runtimeconfig.json')}
PAYLOAD['header-envelope.bin'] = HERE / 'header-envelope.bin'
SOURCE_NAMES = ['Core.cs', 'Native.cs', 'Program.cs', 'SwuMetadataAdapter.csproj', 'run-once.py']


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def manifest():
    paths = [HERE / name for name in SOURCE_NAMES] + list(PAYLOAD.values())
    return {'schema': 'swu-metadata-adapter-deployment-v1', 'boot': BOOT,
            'root_adapter_sha256': ADAPTER_SHA, 'target_dotnet_sha256': DOTNET_SHA,
            'stage': STAGE, 'payload_names': sorted(PAYLOAD),
            'files': {str(p.relative_to(HERE)): {'bytes': p.stat().st_size,
                                                'sha256': sha(p.read_bytes())} for p in paths},
            'scope': 'Exactly one fixed metadata-only TEEC 0/1/2 sequence, no firmware writing; plaintext quarantined and wiped. Native 25s deadline; root timeout 45s. No automatic retry.'}


def load_root():
    spec = importlib.util.spec_from_file_location('swu_bx_central_root', ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def guard():
    return ('set -eu\n'
            f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
            f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n')


def stage_guard():
    return (f'test ! -L {STAGE}\ntest -d {STAGE}\n'
            f'test "$(stat -c "%u:%g:%a" {STAGE})" = 0:0:700\n')


def exact_guard(names):
    text = stage_guard()
    for name in names:
        path = f'{STAGE}/{name}'
        text += f'test ! -L {path}\ntest -f {path}\n'
        text += f'test "$(stat -c "%u:%g:%a" {path})" = 0:0:600\n'
        if name in PAYLOAD:
            raw = PAYLOAD[name].read_bytes()
            text += f'test "$(wc -c < {path})" = {len(raw)}\n'
            text += f'test "$(sha256sum {path} | cut -d " " -f1)" = {sha(raw)}\n'
    cases = '|'.join(sorted(names))
    text += f'count=0\nfor path in {STAGE}/* {STAGE}/.[!.]* {STAGE}/..?*; do\n'
    text += '[ -e "$path" ] || [ -L "$path" ] || continue\n'
    text += f'case "${{path##*/}}" in {cases}) count=$((count+1));; *) exit 91;; esac\ndone\n'
    return text + f'test "$count" = {len(names)}\n'


def execute(output, digest):
    mpath = HERE / 'deployment-manifest.json'
    need(mpath.is_file() and sha(mpath.read_bytes()) == digest, 'deployment manifest identity')
    need(json.loads(mpath.read_text()) == manifest(), 'source/payload drift')
    need(sha(ADAPTER.read_bytes()) == ADAPTER_SHA, 'root adapter drift')
    need(output.is_absolute() and not output.exists(), 'fresh absolute output directory')
    output.mkdir(parents=True, mode=0o700)
    (output / 'runner-at-run.py').write_bytes(Path(__file__).read_bytes())
    (output / 'deployment-manifest.json').write_bytes(mpath.read_bytes())
    mod = load_root()
    record = {'schema': 'swu-metadata-bounded-run-v1', 'calls': [],
              'invocations': 0, 'target_operation_state': 'not_dispatched', 'retries': 0}

    def call(command, label):
        save(output / 'record.json', record)
        return mod.root(command, record, output / (label + '.json'))

    call(guard() + f'test ! -e {STAGE}\ntest ! -L {STAGE}\numask 077\nmkdir {STAGE}\nchmod 700 {STAGE}\n', 'stage')
    for name, local in PAYLOAD.items():
        raw = local.read_bytes(); remote = f'{STAGE}/{name}'
        call(guard() + stage_guard() + f'test ! -e {remote}\ntest ! -L {remote}\numask 077\n: > {remote}\nchmod 600 {remote}\n', 'create-' + name)
        for offset in range(0, len(raw), 3072):
            chunk = base64.b64encode(raw[offset:offset + 3072]).decode('ascii')
            cmd = guard() + stage_guard() + f'test ! -L {remote}\ntest -f {remote}\n'
            cmd += f'test "$(wc -c < {remote})" = {offset}\n'
            cmd += f"printf '%s' '{chunk}' | base64 -d >> {remote}\n"
            call(cmd, f'upload-{name}-{offset:06d}')
    record.update(invocations=1, target_operation_state='inflight_or_unknown')
    save(output / 'record.json', record)
    cmd = guard() + exact_guard(PAYLOAD)
    cmd += f'umask 077\nset +e\n/usr/bin/dotnet {STAGE}/SwuMetadataAdapter.dll > {STAGE}/stdout.txt 2> {STAGE}/stderr.txt\nrun_exit=$?\nset -e\n'
    cmd += f'test "$(wc -c < {STAGE}/stdout.txt)" -le 4096\ntest "$(wc -c < {STAGE}/stderr.txt)" -le 2048\n'
    cmd += 'printf "RUN_EXIT=%s\\n" "$run_exit"\n'
    cmd += f'printf "STDOUT_BEGIN\\n"\ncat {STAGE}/stdout.txt\nprintf "STDOUT_END\\nSTDERR_BEGIN\\n"\ncat {STAGE}/stderr.txt\nprintf "STDERR_END\\n"\n'
    text = call(cmd, 'invoke-once')
    (output / 'diagnostic.txt').write_text(text)
    matched = re.fullmatch(r'RUN_EXIT=([0-9]+)\nSTDOUT_BEGIN\n(.*?)STDOUT_END\nSTDERR_BEGIN\n(.*?)STDERR_END\n', text, re.S)
    need(matched is not None, 'run framing unknown; stage retained, never retry')
    rc, stdout, stderr = int(matched[1]), matched[2], matched[3]
    rows = [line for line in stdout.splitlines() if not line.startswith('[GC_INFO]')]
    diagnostic = [line for line in rows if line.startswith('SWU_METADATA_DIAGNOSTIC ')]
    need(rc == 0 and stderr == '' and len(diagnostic) == 1 and
         rows.count('SELECTOR result=0 value=0') == 5 and len(rows) == 6 and
         all(line.startswith(('SELECTOR ', 'SWU_METADATA_DIAGNOSTIC ')) for line in rows),
         'native sequence not accepted; stage retained, never retry')
    need(re.fullmatch(r'SWU_METADATA_DIAGNOSTIC stage=quarantined result=0x00000000 origin=0x[0-9a-f]{8} local=0 calls=1,1,1 counts=[0-9]+,[0-9]+ observed=[0-9]+,[0-9]+ closed=1 released=3 finalized=1 metadata_published=0', diagnostic[0]) is not None,
         'native terminal cleanup/command contract')
    record.update(target_operation_state='terminal_native_cleanup_reported', native_exit=rc,
                  plaintext_saved=False, metadata_validated=False)
    save(output / 'record.json', record)
    names = list(PAYLOAD) + ['stdout.txt', 'stderr.txt']
    cleanup = guard() + exact_guard(names)
    # Remove only the reviewed fixed stage after the terminal native contract.
    cleanup += 'rm -- ' + ' '.join(shlex.quote(f'{STAGE}/{n}') for n in names) + '\n'
    cleanup += f'rmdir {STAGE}\ntest ! -e {STAGE}\nprintf "STAGE_REMOVED\\n"\n'
    need(call(cleanup, 'cleanup') == 'STAGE_REMOVED\n', 'cleanup contract')
    save(output / 'result.json', {'sequence_completed': True, 'invocations': 1,
                                 'native_diagnostic': diagnostic[0], 'stage_removed': True,
                                 'metadata_validated': False, 'plaintext_saved': False,
                                 'permanent_prevention': False})
    print(json.dumps({'sequence_completed': True, 'invocations': 1, 'stage_removed': True,
                      'metadata_validated': False, 'plaintext_saved': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze-manifest', action='store_true')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    need(not (args.execute and args.freeze_manifest), 'choose one mode')
    if args.freeze_manifest:
        need(args.output is None and args.manifest_sha256 is None, 'freeze arguments')
        save(HERE / 'deployment-manifest.json', manifest())
        print(sha((HERE / 'deployment-manifest.json').read_bytes()))
    elif args.execute:
        need(args.output is not None and re.fullmatch('[0-9a-f]{64}', args.manifest_sha256 or '') is not None, 'execution arguments')
        execute(args.output, args.manifest_sha256)
    else:
        need(args.output is None and args.manifest_sha256 is None, 'dry arguments')
        print(json.dumps({'target_operations': 0, 'execute_required': True,
                          'payload_names': sorted(PAYLOAD), 'metadata_published': False,
                          'retries': 0, 'stage': STAGE}))
