#!/usr/bin/env python3
"""One detached finite logger; dry by default, no automatic UI or retry."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import time
import uuid

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / 'managed-usb-secondary-logger-smoke'
PARENT_WRAPPER_SHA = 'eeb852c8e1b9a0d2611abc17e853ad2ee834f4e42712b2810bf8309eda5e59ca'
ADAPTER_SHA = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
BOOT = '00000000-0000-4000-8000-000000000000'
DOTNET_SHA = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
ASSEMBLY = 'ManagedUsbSecondaryLoggerOnset'
NAMES = [ASSEMBLY + '.' + s for s in ('dll', 'deps.json', 'runtimeconfig.json')]
INPUTS = NAMES + ['supervisor.sh']
OUTPUTS = ['supervisor.pid', 'supervisor.stat', 'native.pid', 'native.stdout',
           'native.stderr', 'native.exit', 'logger.ready']
MAX_STDOUT, MAX_STDERR = 50000, 2048
SCHEMA = 'usb-fixed-secondary-logger-onset-build-v1'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(raw):
    def bad(value):
        raise ValueError('Non-JSON constant ' + value)
    return json.loads(raw, parse_constant=bad)


def module(name, path, expected):
    need(sha(path.read_bytes()) == expected, 'module pin ' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def proc_stat(raw):
    match = re.fullmatch(r'(\d+) \((.*)\) (\S) (.*)\n?', raw.strip())
    need(match is not None, 'proc stat framing')
    fields = match[4].split()
    need(len(fields) >= 19, 'proc stat extent')
    return dict(pid=int(match[1]), state=match[3], pgrp=int(fields[1]),
                session=int(fields[2]), start_ticks=int(fields[18]))


def framed_bytes(lines, name):
    begin, end = name + '_BEGIN', name + '_END'
    need(lines.count(begin) == lines.count(end) == 1, 'unique framed block ' + name)
    a, b = lines.index(begin), lines.index(end)
    need(0 <= a < b and b-a <= 40, 'bounded framed block ' + name)
    return base64.b64decode(''.join(lines[a+1:b]), validate=True)


def supervisor(remote):
    q = shlex.quote(remote)
    dll = shlex.quote(remote + '/' + NAMES[0])
    return f'''#!/bin/sh
set -u
umask 077
cd {q} || exit 91
printf '%s\\n' "$$" > supervisor.pid.tmp
mv supervisor.pid.tmp supervisor.pid
cat /proc/$$/stat > supervisor.stat.tmp
mv supervisor.stat.tmp supervisor.stat
rc=0
/usr/bin/dotnet {dll} --execute > native.stdout 2> native.stderr </dev/null &
child=$!
printf '%s\\n' "$child" > native.pid.tmp
mv native.pid.tmp native.pid
wait "$child" || rc=$?
out_bytes=$(wc -c < native.stdout)
err_bytes=$(wc -c < native.stderr)
out_sha=$(sha256sum native.stdout | cut -d ' ' -f1)
err_sha=$(sha256sum native.stderr | cut -d ' ' -f1)
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf '{{"schema":"secondary-logger-onset-exit-v1","supervisor_pid":%s,"child_pid":%s,"child_exit":%s,"stdout_bytes":%s,"stderr_bytes":%s,"stdout_sha256":"%s","stderr_sha256":"%s","boot_id":"%s","uptime":"%s"}}\\n' "$$" "$child" "$rc" "$out_bytes" "$err_bytes" "$out_sha" "$err_sha" "$boot" "$up" > native.exit.tmp
mv native.exit.tmp native.exit
'''.encode()


def parse_selftest(stdout, expected):
    values = []
    for line in stdout.splitlines():
        if line.startswith('{'):
            values.append(strict_json(line))
        else:
            need(line.startswith('[GC_INFO] '), 'unclassified selftest output')
    need(len(values) == 1 and isinstance(values[0], dict), 'one target selftest summary')
    actual = values[0]
    # The fake-run JSON includes this process's PID in readiness. Its measured
    # serialized size can differ between host and TV; the count/budget proof
    # must hold, rather than requiring byte-for-byte equality of that metric.
    fixed = lambda row: {k: v for k, v in row.items() if k != 'successOutputBytes'}
    need(set(actual) == set(expected) and
         all(type(actual[k]) is type(expected[k]) for k in expected) and
         fixed(actual) == fixed(expected),
         'target selftest fixed fields match offline build')
    need(type(actual['successOutputBytes']) is int and
         0 < actual['successOutputBytes'] <= MAX_STDOUT, 'target selftest output budget')


def parse_native(stdout):
    values = []
    for line in stdout.splitlines():
        if line.startswith('{'):
            values.append(strict_json(line))
        else:
            need(line.startswith('[GC_INFO] '), 'unclassified native output')
    need(len(values) == 1, 'one native outcome')
    return values[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(target_operations=0, hold_ms=20000,
                              variant='detached-ready', automatic_ui=False)))
        return
    need(args.output is not None and args.output.is_absolute(), 'absolute new output')
    manifest_raw = (HERE / 'build-manifest.json').read_bytes()
    need(sha(manifest_raw) == args.manifest_sha256, 'reviewed aggregate manifest')
    manifest = strict_json(manifest_raw)
    need(manifest['schema'] == SCHEMA, 'manifest schema')
    native_raw = (HERE / 'native-build-manifest.json').read_bytes()
    need(sha(native_raw) == manifest['native_manifest_sha256'], 'native manifest pin')
    native = strict_json(native_raw)
    for collection in (native['files'], native['offline_files'], manifest['local_files']):
        for name, row in collection.items():
            raw = (HERE / name).read_bytes()
            need(row == dict(size=len(raw), sha256=sha(raw)), 'local build ' + name)
    need(native['fixed_protocol']['hold_ms'] == 20000 and
         native['fixed_protocol']['retries'] == 0, 'finite fixed protocol')
    parent = module('onset_parent_wrapper', PARENT / 'run-once.py', PARENT_WRAPPER_SHA)
    root = module('onset_root_transport', HERE / 'root-with-margin.py', ADAPTER_SHA)
    expected_tests = strict_json(next(x['stdout'] for x in native['checks']
                                     if x['args'] == ['--self-test']))
    args.output.mkdir(parents=True, exist_ok=False)
    remote = '/tmp/researcher-usb-onset-' + uuid.uuid4().hex
    record_path = args.output / 'record.json'
    record = dict(manifest_sha256=sha(manifest_raw), native_manifest_sha256=sha(native_raw),
                  deployment_script_sha256=sha(Path(__file__).read_bytes()),
                  root_adapter_sha256=ADAPTER_SHA, parent_wrapper_sha256=PARENT_WRAPPER_SHA,
                  remote_stage=remote, calls=[], cleanup_deferred=True,
                  no_retry=True, automatic_ui=False)
    root.save(record_path, record)

    def call(command):
        return root.root(command, record, record_path)

    def save():
        root.save(record_path, record)

    def put(name, data):
        target = remote + '/' + name
        temp = target + '.b64'
        encoded = base64.b64encode(data).decode()
        for start in range(0, len(encoded), 5000):
            chunk = encoded[start:start+5000]
            init = (f'test ! -e {shlex.quote(temp)}\ntest ! -L {shlex.quote(temp)}\n'
                    f': > {shlex.quote(temp)}\nchmod 600 {shlex.quote(temp)}\n') if start == 0 else ''
            call('set -eu\numask 077\n' + parent.dir_guard(remote) + init +
                 parent.file_guard(temp, start) +
                 f'printf %s {shlex.quote(chunk)} >> {shlex.quote(temp)}\n' +
                 parent.file_guard(temp, start+len(chunk)) + 'echo STAGED_CHUNK\n')
        call('set -eu\numask 077\n' + parent.dir_guard(remote) +
             parent.file_guard(temp, len(encoded)) +
             f'test ! -e {shlex.quote(target)}\ntest ! -L {shlex.quote(target)}\n' +
             f'base64 -d {shlex.quote(temp)} > {shlex.quote(target)}\n'
             f'chmod 600 {shlex.quote(target)}\n' + parent.file_guard(target, len(data)) +
             f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {sha(data)}\n'
             f'rm {shlex.quote(temp)}\necho STAGED_FILE\n')

    def status():
        command = ('set -eu\n' + parent.dir_guard(remote) +
                   'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n')
        path = remote + '/supervisor.stat'
        command += ('echo SUPERVISOR_STAT_BEGIN\n' +
                    f'if test -e {shlex.quote(path)}; then\n' + parent.file_guard(path) +
                    f'  test "$(wc -c < {shlex.quote(path)})" -le 2048\n'
                    f'  base64 {shlex.quote(path)}\nfi\necho SUPERVISOR_STAT_END\n')
        for filename, kind in [('native.exit', 'DONE'), ('logger.ready', 'READY')]:
            path = remote + '/' + filename
            command += (f'if test -e {shlex.quote(path)}; then\n' + parent.file_guard(path) +
                        f'  test "$(wc -c < {shlex.quote(path)})" -le 2048\n'
                        f'  echo {kind}\n  cat {shlex.quote(path)}\n'
                        '  echo POLL_END_UPTIME\n  cat /proc/uptime\n  exit 0\nfi\n')
        command += 'echo WAIT\necho POLL_END_UPTIME\ncat /proc/uptime\n'
        stdout = call(command)
        lines = stdout.splitlines()
        need(len(lines) >= 7 and lines[0] == BOOT, 'poll framing/boot')
        need(re.fullmatch(r'[0-9.]+ [0-9.]+', lines[1]) is not None, 'poll uptime')
        need(lines[2] == 'SUPERVISOR_STAT_BEGIN' and lines[-2] == 'POLL_END_UPTIME',
             'supervisor/end uptime framing')
        need(re.fullmatch(r'[0-9.]+ [0-9.]+', lines[-1]) is not None and
             float(lines[-1].split()[0]) >= float(lines[1].split()[0]), 'poll final uptime')
        supervisor_stat = None
        stat_bytes = framed_bytes(lines, 'SUPERVISOR_STAT')
        if stat_bytes:
            supervisor_stat = proc_stat(stat_bytes.decode())
            need(supervisor_stat['pid'] == supervisor_stat['pgrp'] == supervisor_stat['session'],
                 'detached supervisor group/session')
            need(supervisor_stat['pid'] == record['launcher_pid'], 'launcher binds supervisor PID')
        tail = lines[lines.index('SUPERVISOR_STAT_END')+1:-2]
        need((tail == ['WAIT']) or
             (len(tail) == 2 and tail[0] in ('READY', 'DONE')), 'poll status structure')
        return tail[0], strict_json(tail[1]) if len(tail) == 2 else None, supervisor_stat, lines[-1]

    # The only mutation before native execution is this unique private /tmp stage.
    call('set -eu\numask 077\n' +
         f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
         f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n' +
         'test -x /usr/bin/setsid\n' +
         f'test ! -e {shlex.quote(remote)}\ntest ! -L {shlex.quote(remote)}\n'
         f'mkdir -m 700 {shlex.quote(remote)}\n' + parent.dir_guard(remote) + 'echo STAGE_CREATED\n')
    for name in NAMES:
        put(name, (HERE / 'bin/Release/net6.0' / name).read_bytes())
    script = supervisor(remote)
    record['supervisor_script_sha256'] = sha(script)
    save()
    put('supervisor.sh', script)
    integrity = parent.dir_guard(remote) + parent.exact_inventory(remote, INPUTS)
    for name in INPUTS:
        data = script if name == 'supervisor.sh' else (HERE / 'bin/Release/net6.0' / name).read_bytes()
        target = remote + '/' + name
        integrity += parent.file_guard(target, len(data))
        integrity += f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {sha(data)}\n'
    dll = shlex.quote(remote + '/' + NAMES[0])
    stdout = call('set -eu\numask 077\n' + integrity + f'/usr/bin/dotnet {dll} --self-test\n')
    (args.output / 'selftest.stdout.txt').write_text(stdout)
    parse_selftest(stdout, expected_tests)
    launch = ('set -eu\numask 077\n' + integrity +
              f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
              f'/usr/bin/setsid /bin/sh {shlex.quote(remote + "/supervisor.sh")} </dev/null >/dev/null 2>&1 3>&- &\n'
              'echo LAUNCHER_PID=$!\n')
    launched = call(launch)
    need(re.fullmatch(r'LAUNCHER_PID=[1-9][0-9]*\n', launched) is not None, 'launcher receipt')
    record['launcher_pid'] = int(launched.split('=')[1])
    save()
    start = time.monotonic()
    ready = None
    completion = None
    supervisor_stat = None
    while time.monotonic() - start <= 8:
        kind, value, stat, up = status()
        if stat is not None:
            if supervisor_stat is not None:
                need(stat == supervisor_stat, 'stable saved supervisor identity')
            supervisor_stat = stat
        if kind == 'DONE':
            completion = value
            break
        if kind == 'READY':
            need(supervisor_stat is not None, 'ready has supervisor identity')
            need(set(value) == {'schema', 'stage_token', 'boot_id', 'pid', 'at_ms',
                                'uptime', 'gate', 'protocol_phase'}, 'ready schema keys')
            need(value['schema'] == 'secondary-logger-onset-ready-v1' and
                 value['stage_token'] == Path(remote).name and value['boot_id'] == BOOT and
                 value['gate'] == 1 and value['protocol_phase'] == 'ReadyForHeader', 'ready identity')
            need(type(value['pid']) is int and value['pid'] > 1 and
                 type(value['at_ms']) is int and 0 <= value['at_ms'] <= 12000, 'ready process/time')
            need(0 <= float(up.split()[0])-float(value['uptime'].split()[0]) <= 2,
                 'fresh ready observation')
            child, sup = value['pid'], supervisor_stat['pid']
            probe_started = time.monotonic()
            probe = call('set -eu\n' + parent.dir_guard(remote) +
                         f'test ! -e {shlex.quote(remote + "/native.exit")}\n' +
                         parent.file_guard(remote + '/native.pid') +
                         f'test "$(cat {shlex.quote(remote + "/native.pid")})" = {child}\n' +
                         'cat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n' +
                         f'echo LIVE_SUP_BEGIN\nbase64 /proc/{sup}/stat\necho LIVE_SUP_END\n'
                         f'echo LIVE_CHILD_BEGIN\nbase64 /proc/{child}/stat\necho LIVE_CHILD_END\n'
                         f'echo LIVE_CMDLINE_BEGIN\nbase64 /proc/{child}/cmdline\necho LIVE_CMDLINE_END\n'
                         'echo PROBE_END_UPTIME\ncat /proc/uptime\n')
            need(time.monotonic() - probe_started <= 1, 'bounded ready liveness probe')
            rows = probe.splitlines()
            need(len(rows) >= 13 and rows[0] == BOOT and rows[-2] == 'PROBE_END_UPTIME',
                 'live process probe')
            need(0 <= float(rows[-1].split()[0])-float(value['uptime'].split()[0]) <= 2,
                 'ready still fresh at live probe')
            live_sup = proc_stat(framed_bytes(rows, 'LIVE_SUP').decode())
            live_child = proc_stat(framed_bytes(rows, 'LIVE_CHILD').decode())
            need(all(live_sup[k] == supervisor_stat[k] for k in ('pid', 'start_ticks', 'pgrp', 'session')) and
                 live_sup['state'] not in ('Z', 'X') and live_child['state'] not in ('Z', 'X'),
                 'same live supervisor')
            need(live_child['pid'] == child and live_child['pgrp'] == live_child['session'] == sup,
                 'native belongs to detached supervisor')
            argv = framed_bytes(rows, 'LIVE_CMDLINE').decode().split('\0')
            need(argv == ['/usr/bin/dotnet', remote + '/' + NAMES[0], '--execute', ''], 'exact live native command')
            ready = value
            record['ready'] = ready
            record['supervisor_identity'] = supervisor_stat
            record['native_identity'] = live_child
            record['ready_probe_uptime'] = rows[-1]
            save()
            (args.output / 'ready.json').write_text(json.dumps(ready, separators=(',', ':')) + '\n')
            print(json.dumps(dict(event='LOGGER_READY', output=str(args.output),
                                  stage=remote, ready=ready)), flush=True)
            # Deliberately release both root command locks for a separate UI action.
            time.sleep(22)
            break
        time.sleep(0.25)
    while completion is None and time.monotonic() - start <= 65:
        kind, value, stat, _ = status()
        if kind == 'DONE':
            completion = value
            break
        time.sleep(1)
    need(completion is not None, 'completion unobserved: no kill, retry or cleanup permitted')
    record['completion'] = completion
    save()
    (args.output / 'completion.json').write_text(json.dumps(completion, indent=2) + '\n')
    need(completion['schema'] == 'secondary-logger-onset-exit-v1' and completion['boot_id'] == BOOT,
         'completion identity')
    need(supervisor_stat is not None and completion['supervisor_pid'] == supervisor_stat['pid'],
         'completed known supervisor')
    need(type(completion['child_exit']) is int and type(completion['child_pid']) is int,
         'completion exit/pid types')
    fetched = {}
    for name, key, limit in [('native.stdout', 'stdout', MAX_STDOUT), ('native.stderr', 'stderr', MAX_STDERR)]:
        count = completion[key + '_bytes']
        digest = completion[key + '_sha256']
        need(type(count) is int and 0 <= count <= limit and re.fullmatch('[0-9a-f]{64}', digest), 'bounded output')
        target = remote + '/' + name
        text = call('set -eu\n' + parent.dir_guard(remote) + parent.file_guard(target, count) +
                    f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {digest}\n'
                    f'cat {shlex.quote(target)}\n')
        raw = text.encode()
        need(len(raw) == count and sha(raw) == digest, 'fetched exact output ' + name)
        (args.output / name).write_bytes(raw)
        fetched[key] = text
    outcome = parse_native(fetched['stdout'])
    (args.output / 'native-outcome.json').write_text(json.dumps(outcome, separators=(',', ':')) + '\n')
    parent.validate_outcome(outcome, completion['child_exit'])
    if outcome['Accepted']:
        need(ready is not None and completion['child_pid'] == ready['pid'] and
             outcome['ReadyPublished'] is True and outcome['PreArmFault'] == 0, 'accepted ready/precondition')
        ready_raw = (outcome['ReadyJson'] + '\n').encode()
        need(sha(ready_raw) == outcome['ReadySha256'] and strict_json(ready_raw) == ready,
             'final outcome binds exact published readiness')
        need(fetched['stderr'] == '', 'accepted native stderr empty')
    artifacts = {}
    for field, name, extent, digest in (
        ('CallbackBase64', 'callbacks.bin', 64, 'CallbackSha256'),
        ('BaselineRingBase64', 'baseline-ring.bin', 15372, 'BaselineRingSha256'),
        ('PreArmRtBase64', 'prearm-rt.bin', 64, None),
        ('ArmedRtBase64', 'armed-rt.bin', 64, None),
        ('RestoredRtBase64', 'restored-rt.bin', 64, None),
        ('PostRingBase64', 'post-ring.bin', 15372, 'PostRingSha256')):
        row = parent.decode_artifact(outcome, field, name, args.output, extent, digest)
        if row is not None:
            artifacts[field] = row
    result = dict(accepted=outcome['Accepted'], ready_observed=ready is not None,
                  restore_verified=outcome['RestoreVerified'],
                  restore_unverified=outcome['RestoreUnverified'],
                  log_flag_may_remain_changed=outcome['LogFlagMayRemainChanged'],
                  protocol_phase=outcome['ProtocolPhase'], artifacts=artifacts,
                  physical_picture_observed=False, ui_action_included=False, repair_established=False)
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    record['native_accepted'] = outcome['Accepted']
    save()
    if outcome['Accepted']:
        # Terminal, parsed and retained output is required before any deletion.
        all_names = INPUTS + OUTPUTS
        clean = 'set -eu\n' + parent.dir_guard(remote) + parent.exact_inventory(remote, all_names)
        for name in all_names:
            clean += parent.file_guard(remote + '/' + name)
        clean += 'rm ' + ' '.join(shlex.quote(remote + '/' + n) for n in all_names) + '\n'
        clean += f'rmdir {shlex.quote(remote)}\ntest ! -e {shlex.quote(remote)}\necho STAGE_ABSENT\n'
        record['cleanup_stdout'] = call(clean)
        need(record['cleanup_stdout'] == 'STAGE_ABSENT\n', 'exact private-stage cleanup receipt')
        record['cleanup_deferred'] = False
        save()
    print(json.dumps(dict(event='LOGGER_FINISHED', output=str(args.output),
                          accepted=outcome['Accepted'], cleanup_deferred=record['cleanup_deferred'])))


if __name__ == '__main__':
    main()
