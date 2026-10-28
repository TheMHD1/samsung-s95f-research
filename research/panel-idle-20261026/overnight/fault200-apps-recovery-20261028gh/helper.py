#!/usr/bin/env python3
"""One fixed stock MODE2 request; foreground, native deadline, separate receipt."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import uuid
import time

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent / 'autonomous-fault-harness-20261028dh/deadline-mode2'
BASE = HERE.parent
ADAPTER = BASE / 'managed-ui-tab-launch/root-with-margin.py'
ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
STOCK = BASE / 'managed-tcon-power-cycle-once/run-power-cycle-once.py'
STOCK_SHA = '5c7ec5d3581e349d7f91669977123497147777e573fbdefd8a9b6f96dcf3cb75'
MANIFEST_SHA = 'c2daff227e1f1bf8f9b23e9f4ae1fc389c39f4f4852bb53d8c472e452d7850f3'
BOOT = '00000000-0000-4000-8000-000000000000'
DOTNET_SHA = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
NAMES = ('DeadlineMode2.dll', 'DeadlineMode2.deps.json', 'DeadlineMode2.runtimeconfig.json')

POLICY_SHA = '0013cc4d6ef09237d33cdb0027baa25850432a7ef6011d7833dba305d6503df0'
BV_SHA = '4fddc3f6e933a19b15ba208e1ffc029ccd7df323c66cdb7ae24157f374e64a0f'

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load(path, pin, name):
    need(sha(path.read_bytes()) == pin, name + ' changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def contract():
    need(sha((BUILD / 'build-manifest.json').read_bytes()) == MANIFEST_SHA, 'manifest changed')
    manifest = json.loads((BUILD / 'build-manifest.json').read_text())
    need(manifest['schema'] == 'deadline-stock-mode2-build-v1', 'manifest schema')
    need(manifest['operation'] == 41 and manifest['mode'] == 2 and manifest['deadline_seconds'] == 12,
         'fixed operation/deadline changed')
    for path, pin in manifest['files'].items():
        need(sha((BUILD / path).read_bytes()) == pin, 'build file changed: ' + path)
    need(sha((BASE / 'managed-tcon-power-cycle-once/Program.cs').read_bytes()) ==
         manifest['original_stock_source_sha256'], 'stock source changed')
    return {name: (BUILD / 'bin/Release/net6.0' / name).read_bytes() for name in NAMES}

def guard():
    return ('set -eu\n'
            f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
            'test "$(id -u)" = 0\n'
            'test -c /dev/tztv_tcon\n'
            f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f 1)" = {DOTNET_SHA}\n')

def parse_receipt(text, stock):
    match = re.findall(r'^PID_LIBC=([1-9][0-9]*)$', text, re.M)
    need(len(match) == 1, 'missing/duplicate helper PID')
    return stock.parse_managed(text, int(match[0]))

def render_stage(remote, payloads):
    need(re.fullmatch('/tmp/s95f-mode2-[0-9a-f]{32}', remote) is not None, 'remote path')
    commands = [guard() + f'umask 077\nmkdir {remote}\n']
    for name, data in payloads.items():
        need(name in NAMES, 'unexpected payload')
        encoded = base64.b64encode(data).decode()
        for i in range(0, len(encoded), 4400):
            redirect = '>' if i == 0 else '>>'
            commands.append(guard() + f'printf %s {encoded[i:i+4400]} {redirect}{remote}/{name}.b64\n')
        commands.append(guard() + f'base64 -d {remote}/{name}.b64 >{remote}/{name}\n'
                        f'test "$(sha256sum {remote}/{name} | cut -d " " -f 1)" = {sha(data)}\n'
                        f'rm -- {remote}/{name}.b64\n')
    need(all(0 < len(c.encode()) <= 8192 for c in commands), 'root command limit')
    return commands

def execute(output, payloads, adapter, identity, clock=time.monotonic_ns):
    output.mkdir(mode=0o700)
    stock = load(STOCK, STOCK_SHA, 'deadline_stock_parser')
    stock.contract()
    policy = load(HERE / 'policy.py', POLICY_SHA, 'gh_fixed_policy')
    gates = load(BASE / 'recovery-quickpath-20261027bv/recover.py', BV_SHA, 'gh_public_gates')
    remote = '/tmp/s95f-mode2-' + uuid.uuid4().hex
    record = {'schema': 'gh-deadline-stock-mode2-run-v1', 'remote_private_directory': remote,
              'accepted': False, 'physical_state': 'unobserved', 'max_requests': 1,
              'automatic_retries': 0, 'calls': []}
    record.update(nativeInvocations=0, nativeInvocationStatus='not_submitted', wrapperUiOperations=0)
    root_path = output / 'root.json'
    for command in render_stage(remote, payloads):
        adapter.root(command, record, root_path)
    policy.identity_checkpoint(adapter, record, root_path, output, identity, 'GH_BEFORE_NATIVE')
    public = output / 'pre-native-public'; public.mkdir(mode=0o700)
    gates.public_gate(public, adapter_module=adapter)
    checkpoint = policy.snapshot(adapter, record, root_path, output, 'pre-native', clock)
    hashes = ''.join(f'test "$(sha256sum {remote}/{name} | cut -d " " -f 1)" = {sha(data)}\n'
                     for name, data in payloads.items())
    command = guard() + stock.lifecycle_module().stock_checks() + '\n' + hashes + f'''cd {remote}
test ! -e receipt.txt
ulimit -f 128
echo BEFORE
cat /proc/uptime
tv_mode2_rc=0
env TMPDIR={remote} DOTNET_CLI_HOME={remote} DOTNET_EnableDiagnostics=0 DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 /usr/bin/dotnet --clr-path /usr/share/dotnet/shared/Microsoft.NETCore.App/6.0.9 --globalizationinvariant ./DeadlineMode2.dll >native.stdout 2>native.stderr || tv_mode2_rc=$?
echo HELPER_EXIT
echo "$tv_mode2_rc"
echo RECEIPT_BASE64
if test -f receipt.txt; then head -c 8192 receipt.txt | base64; fi
echo NATIVE_STDERR_BASE64
head -c 4096 native.stderr | base64
echo AFTER
cat /proc/uptime
'''
    policy.dispatch(checkpoint, clock)
    policy.save(output / 'pre-native-checkpoint.json', checkpoint)
    record.update(nativeInvocations=1, nativeInvocationStatus='submitted_or_unknown')
    policy.save(root_path, record)
    framed = adapter.root(command, record, root_path)
    need(type(framed) is str and len(framed.encode()) <= 65536, 'bounded native root response')
    (output / 'framed.txt').write_text(framed)
    policy.validate_framed(framed)
    record['nativeInvocationStatus'] = 'terminal_framing_retained'
    policy.save(root_path, record)
    rc = int(framed.split('HELPER_EXIT\n', 1)[1].splitlines()[0])
    raw = framed.split('RECEIPT_BASE64\n', 1)[1].split('NATIVE_STDERR_BASE64\n', 1)[0]
    receipt = base64.b64decode(''.join(raw.split()), validate=True)
    (output / 'receipt.txt').write_bytes(receipt)
    stderr = framed.split('NATIVE_STDERR_BASE64\n', 1)[1].split('AFTER\n', 1)[0]
    err = base64.b64decode(''.join(stderr.split()), validate=True)
    (output / 'native.stderr').write_bytes(err)
    policy.save(output / 'helper-terminal.json', {'schema':'gh-helper-terminal-v1','helperExit':rc,'receiptSha256':sha(receipt),'stderrSha256':sha(err),'nativeInvocations':1,'nativeTerminalAccepted':False,'physicalPictureObserved':False})
    need(rc == 0, 'helper exit ' + str(rc) + '; no retry')
    need(err == b'', 'native stderr; no retry')
    parsed = parse_receipt(receipt.decode('utf-8'), stock)
    policy.save(output / 'helper-terminal.json', {'schema':'gh-helper-terminal-v1','helperExit':rc,'receiptSha256':sha(receipt),'stderrSha256':sha(err),'nativeInvocations':1,'nativeTerminalAccepted':True,'classification':parsed['classification'],'physicalPictureObserved':False})
    # Foreground invocation has returned: no racy /proc/PID/stat success premise.
    cleanup = guard() + f'cd {remote}\n' + hashes
    cleanup += 'rm -- ' + ' '.join(shlex.quote(name) for name in (*NAMES, 'receipt.txt', 'native.stdout', 'native.stderr')) + '\n'
    cleanup += f'cd /\nrmdir {remote}\ntest ! -e {remote}\n'
    adapter.root(cleanup, record, root_path)
    result = {'schema': 'gh-deadline-stock-mode2-result-v1', 'accepted': True,
              'helper_exit': rc, 'cleanup_confirmed': True, 'request_count': 1,
              'classification': parsed['classification'], 'physical_state': 'unobserved',
              'recovery_inferred': False, 'power_action_acknowledged': False,
              'native_deadline_seconds': 12, 'receipt_sha256': sha(receipt)}
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
