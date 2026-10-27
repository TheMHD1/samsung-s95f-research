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
OUTPUTS = ['supervisor.launch.stdout', 'supervisor.launch.stderr',
           'supervisor.pid', 'supervisor.stat', 'supervisor.start',
           'native.pid', 'native.stdout', 'native.stderr', 'native.exit',
           'logger.ready']
MAX_STDOUT, MAX_STDERR = 50000, 2048
SCHEMA = 'usb-fixed-secondary-logger-onset-qualified-build-v1'


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
set -eu
umask 077
cd {q}
test "$(pwd)" = {q}
test ! -e supervisor.pid.tmp; test ! -e supervisor.pid
printf '%s\\n' "$$" > supervisor.pid.tmp
chmod 600 supervisor.pid.tmp
mv supervisor.pid.tmp supervisor.pid
test ! -e supervisor.stat.tmp; test ! -e supervisor.stat
cat /proc/$$/stat > supervisor.stat.tmp
chmod 600 supervisor.stat.tmp
mv supervisor.stat.tmp supervisor.stat
test ! -e supervisor.start.tmp; test ! -e supervisor.start
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf 'BOOT=%s\\nUPTIME=%s\\n' "$boot" "$up" > supervisor.start.tmp
chmod 600 supervisor.start.tmp
mv supervisor.start.tmp supervisor.start
test ! -e native.pid.tmp; test ! -e native.pid
test ! -e native.stdout; test ! -e native.stderr
test ! -e native.exit.tmp; test ! -e native.exit
rc=0
/usr/bin/dotnet {dll} --execute > native.stdout 2> native.stderr </dev/null &
child=$!
printf '%s\\n' "$child" > native.pid.tmp
chmod 600 native.pid.tmp
mv native.pid.tmp native.pid
if wait "$child"; then rc=0; else rc=$?; fi
out_bytes=$(wc -c < native.stdout)
err_bytes=$(wc -c < native.stderr)
out_sha=$(sha256sum native.stdout | cut -d ' ' -f1)
err_sha=$(sha256sum native.stderr | cut -d ' ' -f1)
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf '{{"schema":"secondary-logger-onset-exit-v1","supervisor_pid":%s,"child_pid":%s,"child_exit":%s,"stdout_bytes":%s,"stderr_bytes":%s,"stdout_sha256":"%s","stderr_sha256":"%s","boot_id":"%s","uptime":"%s"}}\\n' "$$" "$child" "$rc" "$out_bytes" "$err_bytes" "$out_sha" "$err_sha" "$boot" "$up" > native.exit.tmp
chmod 600 native.exit.tmp
mv native.exit.tmp native.exit
'''.encode()


def parse_start(raw):
    rows = raw.decode('ascii').splitlines()
    need(len(rows) == 2 and rows[0].startswith('BOOT=') and
         rows[1].startswith('UPTIME='), 'supervisor start framing')
    boot, uptime = rows[0][5:], rows[1][7:]
    need(re.fullmatch(r'[0-9a-f-]{36}', boot) is not None and
         re.fullmatch(r'[0-9.]+ [0-9.]+', uptime) is not None,
         'supervisor start fields')
    return boot, uptime


def parse_launch(stdout):
    lines = stdout.splitlines()
    need(len(lines) >= 8 and
         re.fullmatch(r'LAUNCH_ACK [1-9][0-9]* [1-9][0-9]* [1-9][0-9]*',
                      lines[0]) is not None and
         lines[-2] == 'ACK_END_UPTIME' and
         re.fullmatch(r'[0-9.]+ [0-9.]+', lines[-1]) is not None,
         'launch receipt framing')
    _, dispatch, supervisor_pid, start_ticks = lines[0].split()
    saved = proc_stat(framed_bytes(lines, 'HANDSHAKE_STAT').decode())
    boot, uptime = parse_start(framed_bytes(lines, 'HANDSHAKE_START'))
    need(boot == BOOT and saved['pid'] == saved['pgrp'] == saved['session'] ==
         int(supervisor_pid) and saved['start_ticks'] == int(start_ticks) and
         saved['state'] not in ('Z', 'X'), 'launch actual supervisor identity')
    need(0 <= float(lines[-1].split()[0]) - float(uptime.split()[0]) <= 2,
         'fresh supervisor handshake')
    return int(dispatch), saved, uptime


def launch_command(remote, integrity, parent):
    script = shlex.quote(remote + '/supervisor.sh')
    out = shlex.quote(remote + '/supervisor.launch.stdout')
    err = shlex.quote(remote + '/supervisor.launch.stderr')
    pid = shlex.quote(remote + '/supervisor.pid')
    stat = shlex.quote(remote + '/supervisor.stat')
    start = shlex.quote(remote + '/supervisor.start')
    return ('set -eu\numask 077\n' + integrity +
            'test -x /usr/bin/nohup\ntest -x /usr/bin/setsid\ntest -x /bin/sh\n' +
            f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
            f'test ! -e {out}; test ! -L {out}; : > {out}; chmod 600 {out}\n'
            f'test ! -e {err}; test ! -L {err}; : > {err}; chmod 600 {err}\n' +
            '''closefds() {
  for f in /proc/self/fd/*; do
    n=${f##*/}
    case "$n" in ''|*[!0-9]*|0|1|2) continue;; esac
    test "$n" -gt 2 || continue
    eval "exec $n>&-" 2>/dev/null || true
  done
}
''' + f'''(closefds; exec /usr/bin/nohup /usr/bin/setsid -f /bin/sh -c "$(cat {script})") >{out} 2>{err} </dev/null &
dispatch=$!
ready=0
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if test -f {pid} && test -f {stat} && test -f {start}; then ready=1; break; fi
  sleep .05
done
if test "$ready" != 1; then
  echo LAUNCH_HANDSHAKE_MISSING
  test "$(wc -c < {err})" -le 2048 && base64 {err} || true
  exit 41
fi
''' + parent.file_guard(remote + '/supervisor.pid') +
            parent.file_guard(remote + '/supervisor.stat') +
            parent.file_guard(remote + '/supervisor.start') +
            f'''test "$(wc -c < {stat})" -le 2048
test "$(wc -c < {start})" -le 256
p=$(cat {pid}); case "$p" in ''|*[!0-9]*) exit 42;; esac; test "$p" -gt 1
saved=$(cat {stat}); rest=${{saved##*) }}; set -- $rest
test "$#" -ge 20; test "$1" != Z; test "$1" != X
test "${{saved%% *}}" = "$p"; test "$3" = "$p"; test "$4" = "$p"
ticks=${{20}}; case "$ticks" in ''|*[!0-9]*) exit 43;; esac
test "$(sed -n '1s/^BOOT=//p' {start})" = {BOOT}
su=$(sed -n '2s/^UPTIME=//p' {start}); test -n "$su"
live=$(cat "/proc/$p/stat"); rest=${{live##*) }}; set -- $rest
test "$#" -ge 20; test "$1" != Z; test "$1" != X
test "${{live%% *}}" = "$p"; test "$3" = "$p"; test "$4" = "$p"; test "${{20}}" = "$ticks"
sleep .2
live=$(cat "/proc/$p/stat"); rest=${{live##*) }}; set -- $rest
test "$#" -ge 20; test "$1" != Z; test "$1" != X
test "${{live%% *}}" = "$p"; test "$3" = "$p"; test "$4" = "$p"; test "${{20}}" = "$ticks"
eu=$(cut -d ' ' -f1 /proc/uptime)
awk -v s="${{su%% *}}" -v e="$eu" 'BEGIN {{ exit !(e >= s && e-s <= 2) }}'
printf 'LAUNCH_ACK %s %s %s\\n' "$dispatch" "$p" "$ticks"
echo HANDSHAKE_STAT_BEGIN; base64 {stat}; echo HANDSHAKE_STAT_END
echo HANDSHAKE_START_BEGIN; base64 {start}; echo HANDSHAKE_START_END
echo ACK_END_UPTIME; cat /proc/uptime
''')


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
                              variant='qualified-detached-ready', automatic_ui=False)))
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
            need(all(supervisor_stat[k] == record['supervisor_identity'][k]
                     for k in ('pid', 'pgrp', 'session', 'start_ticks')),
                 'status binds actual supervisor PID')
        tail = lines[lines.index('SUPERVISOR_STAT_END')+1:-2]
        need((tail == ['WAIT']) or
             (len(tail) == 2 and tail[0] in ('READY', 'DONE')), 'poll status structure')
        return tail[0], strict_json(tail[1]) if len(tail) == 2 else None, supervisor_stat, lines[-1]

    # The only mutation before native execution is this unique private /tmp stage.
    call('set -eu\numask 077\n' +
         f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
         f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n' +
         'test -x /usr/bin/nohup\ntest -x /usr/bin/setsid\ntest -x /bin/sh\n' +
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
    launched = call(launch_command(remote, integrity, parent))
    dispatch, supervisor_identity, supervisor_start_uptime = parse_launch(launched)
    record['dispatch_pid'] = dispatch
    record['supervisor_identity'] = supervisor_identity
    record['supervisor_start_uptime'] = supervisor_start_uptime
    save()
    start = time.monotonic()
    ready = None
    completion = None
    supervisor_stat = supervisor_identity
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
    launch_diagnostics = {}
    for name in ('supervisor.launch.stdout', 'supervisor.launch.stderr'):
        target = remote + '/' + name
        reply = call('set -eu\n' + parent.dir_guard(remote) +
                     parent.file_guard(target) +
                     f'test "$(wc -c < {shlex.quote(target)})" -le 2048\n'
                     'echo DIAGNOSTIC_BEGIN\n' +
                     f'base64 {shlex.quote(target)}\n' +
                     'echo DIAGNOSTIC_END\n')
        raw = framed_bytes(reply.splitlines(), 'DIAGNOSTIC')
        need(len(raw) <= 2048, 'bounded launch diagnostic')
        (args.output / name).write_bytes(raw)
        launch_diagnostics[name] = dict(size=len(raw), sha256=sha(raw))
    outcome = parse_native(fetched['stdout'])
    (args.output / 'native-outcome.json').write_text(json.dumps(outcome, separators=(',', ':')) + '\n')
    parent.validate_outcome(outcome, completion['child_exit'])
    if outcome['Accepted']:
        need(ready is not None and completion['child_pid'] == ready['pid'] and
             outcome['ReadyPublished'] is True and outcome['PreArmFault'] == 0, 'accepted ready/precondition')
        ready_raw = (outcome['ReadyJson'] + '\n').encode()
        need(sha(ready_raw) == outcome['ReadySha256'] and strict_json(ready_raw) == ready,
             'final outcome binds exact published readiness')
        need(fetched['stderr'] == '' and
             all(row['size'] == 0 for row in launch_diagnostics.values()),
             'accepted native/launcher stderr and launcher stdout empty')
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
                  launch_diagnostics=launch_diagnostics,
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
