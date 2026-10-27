#!/usr/bin/env python3
"""Qualify only the detached root-agent launcher; dry by default."""
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
OVERNIGHT = HERE.parent
ROOT_ADAPTER = OVERNIGHT / 'managed-usb-secondary-logger-onset/root-with-margin.py'
ROOT_ADAPTER_SHA256 = 'bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a'
PARENT = OVERNIGHT / 'managed-usb-secondary-logger-smoke/run-once.py'
PARENT_SHA256 = 'eeb852c8e1b9a0d2611abc17e853ad2ee834f4e42712b2810bf8309eda5e59ca'
STAGE_PREFIX = '/tmp/researcher-launch-qual-'
FILES = ('launcher.stderr', 'launcher.stdout', 'marker.done', 'marker.pid',
         'marker.sh', 'marker.start', 'marker.stat')
LIMITS = {'launcher.stderr': 4096, 'launcher.stdout': 4096,
          'marker.done': 256, 'marker.pid': 32, 'marker.sh': 2048,
          'marker.start': 256, 'marker.stat': 2048}
MAX_COMMAND = 8192
MAX_RESPONSE = 65536


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, path, expected):
    need(sha(path.read_bytes()) == expected, 'module pin ' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def marker_script(remote):
    q = shlex.quote(remote)
    return f'''#!/bin/sh
set -eu
umask 077
cd {q}
test "$(pwd)" = {q}
p=$$
test ! -e marker.pid.tmp; test ! -e marker.pid
printf '%s\n' "$p" > marker.pid.tmp
chmod 600 marker.pid.tmp
mv marker.pid.tmp marker.pid
test ! -e marker.stat.tmp; test ! -e marker.stat
cat "/proc/$p/stat" > marker.stat.tmp
chmod 600 marker.stat.tmp
mv marker.stat.tmp marker.stat
test ! -e marker.start.tmp; test ! -e marker.start
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf 'BOOT=%s\nUPTIME=%s\n' "$boot" "$up" > marker.start.tmp
chmod 600 marker.start.tmp
mv marker.start.tmp marker.start
sleep 3
test ! -e marker.done.tmp; test ! -e marker.done
boot=$(cat /proc/sys/kernel/random/boot_id)
up=$(cat /proc/uptime)
printf 'BOOT=%s\nUPTIME=%s\n' "$boot" "$up" > marker.done.tmp
chmod 600 marker.done.tmp
mv marker.done.tmp marker.done
'''.encode()


def parse_stat(raw):
    match = re.fullmatch(r'(\d+) \((.*)\) (\S) (.*)\n?', raw.decode().strip())
    need(match is not None, 'marker stat framing')
    fields = match[4].split()
    need(len(fields) >= 19, 'marker stat extent')
    return dict(pid=int(match[1]), state=match[3], pgrp=int(fields[1]),
                session=int(fields[2]), start_ticks=int(fields[18]))


def parse_stamp(raw, label):
    try:
        rows = raw.decode('ascii').splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError(label + ' ASCII') from exc
    need(len(rows) == 2 and rows[0].startswith('BOOT=') and
         rows[1].startswith('UPTIME='), label + ' framing')
    boot = rows[0][5:]
    uptime = rows[1][7:]
    need(re.fullmatch(r'[0-9a-f-]{36}', boot) is not None and
         re.fullmatch(r'[0-9.]+ [0-9.]+', uptime) is not None,
         label + ' values')
    return boot, float(uptime.split()[0]), uptime


def framed(stdout):
    lines = stdout.splitlines()
    artifacts = {}
    cursor = 0
    for name in FILES:
        begin, end = 'ART_' + name + '_BEGIN', 'ART_' + name + '_END'
        need(cursor < len(lines) and lines[cursor] == begin,
             'artifact start ' + name)
        try:
            finish = lines.index(end, cursor + 1)
        except ValueError as exc:
            raise ValueError('artifact end ' + name) from exc
        need(finish - cursor <= 40, 'artifact bounds ' + name)
        raw = base64.b64decode(''.join(lines[cursor + 1:finish]), validate=True)
        need(len(raw) <= LIMITS[name], 'artifact size ' + name)
        artifacts[name] = raw
        cursor = finish + 1
    need(lines[cursor:] == ['PID_MISSING'], 'terminal PID state')
    return artifacts


def launch_command(remote, parent):
    script = shlex.quote(remote + '/marker.sh')
    stdout = shlex.quote(remote + '/launcher.stdout')
    stderr = shlex.quote(remote + '/launcher.stderr')
    pidfile = shlex.quote(remote + '/marker.pid')
    statfile = shlex.quote(remote + '/marker.stat')
    startfile = shlex.quote(remote + '/marker.start')
    return ('''set -eu
umask 077
test -x /usr/bin/nohup
test -x /usr/bin/setsid
test -x /bin/sh
''' + parent.dir_guard(remote) + parent.file_guard(remote + '/marker.sh') +
            f'''test ! -e {stdout}; test ! -L {stdout}; : > {stdout}; chmod 600 {stdout}
test ! -e {stderr}; test ! -L {stderr}; : > {stderr}; chmod 600 {stderr}
closefds() {{
  for f in /proc/self/fd/*; do
    n=${{f##*/}}
    case "$n" in ''|*[!0-9]*|0|1|2) continue;; esac
    test "$n" -gt 2 || continue
    eval "exec $n>&-" 2>/dev/null || true
  done
}}
(closefds; exec /usr/bin/nohup /usr/bin/setsid -f /bin/sh -c "$(cat {script})") >{stdout} 2>{stderr} </dev/null &
dispatch=$!
ready=0
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if test -f {pidfile} && test -f {statfile} && test -f {startfile}; then ready=1; break; fi
  sleep .05
done
test "$ready" = 1
''' + parent.file_guard(remote + '/marker.pid') +
            parent.file_guard(remote + '/marker.stat') +
            parent.file_guard(remote + '/marker.start') +
            f'''p=$(cat {pidfile})
case "$p" in ''|*[!0-9]*) exit 40;; esac
test "$p" -gt 1
saved=$(cat {statfile}); saved_rest=${{saved##*) }}; set -- $saved_rest
test "$#" -ge 20; test "$1" != Z; test "$1" != X
test "${{saved%% *}}" = "$p"; test "$3" = "$p"; test "$4" = "$p"
start=${{20}}; case "$start" in ''|*[!0-9]*) exit 41;; esac
live=$(cat "/proc/$p/stat"); live_rest=${{live##*) }}; set -- $live_rest
test "$#" -ge 20; test "$1" != Z; test "$1" != X
test "${{live%% *}}" = "$p"; test "$3" = "$p"; test "$4" = "$p"; test "${{20}}" = "$start"
sleep .2
live=$(cat "/proc/$p/stat"); live_rest=${{live##*) }}; set -- $live_rest
test "$#" -ge 20; test "$1" != Z; test "$1" != X
test "${{live%% *}}" = "$p"; test "$3" = "$p"; test "$4" = "$p"; test "${{20}}" = "$start"
printf 'LAUNCH_ACK %s %s %s\n' "$dispatch" "$p" "$start"
''')


def fetch_command(remote, parent):
    text = 'set -eu\n' + parent.dir_guard(remote) + parent.exact_inventory(remote, FILES)
    for name in FILES:
        text += parent.file_guard(remote + '/' + name)
        text += (f'test "$(wc -c < {shlex.quote(remote + "/" + name)})" '
                 f'-le {LIMITS[name]}\n')
    text += f'''p=$(cat {shlex.quote(remote + '/marker.pid')})
case "$p" in ''|*[!0-9]*) exit 40;; esac
for name in {' '.join(shlex.quote(name) for name in FILES)}; do
  echo "ART_${{name}}_BEGIN"
  base64 {shlex.quote(remote)}/"$name"
  echo "ART_${{name}}_END"
done
gone=0
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if test ! -e "/proc/$p/stat"; then gone=1; break; fi
  sleep .05
done
test "$gone" = 1
echo PID_MISSING
'''
    return text


def cleanup_command(remote, parent, artifacts):
    text = 'set -eu\n' + parent.dir_guard(remote) + parent.exact_inventory(remote, FILES)
    for name in FILES:
        target = remote + '/' + name
        text += parent.file_guard(target, len(artifacts[name]))
        text += (f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = '
                 f'{sha(artifacts[name])}\n')
    text += 'rm ' + ' '.join(shlex.quote(remote + '/' + name) for name in FILES) + '\n'
    text += f'rmdir {shlex.quote(remote)}\ntest ! -e {shlex.quote(remote)}\necho STAGE_REMOVED\n'
    return text


def execute(args, script_sha):
    need(args.output is not None and args.output.is_absolute(), 'absolute output required')
    need(args.script_sha256 == script_sha, 'reviewed script SHA-256 pin')
    args.output.mkdir(parents=True, exist_ok=False)
    root = load('launcher_qual_root', ROOT_ADAPTER, ROOT_ADAPTER_SHA256)
    parent = load('launcher_qual_parent', PARENT, PARENT_SHA256)
    remote = STAGE_PREFIX + uuid.uuid4().hex
    record_path = args.output / 'record.json'
    record = dict(schema='launcher-qualification-record-v1', script_sha256=script_sha,
                  root_adapter_sha256=ROOT_ADAPTER_SHA256,
                  parent_wrapper_sha256=PARENT_SHA256, remote_stage=remote,
                  calls=[], cleanup_deferred=True, no_retry=True,
                  target_device_operations=0, physical_picture_observed=False)
    root.save(record_path, record)

    def call(command):
        need(0 < len(command.encode()) <= MAX_COMMAND, 'root command bound')
        result = root.root(command, record, record_path)
        need(len(result.encode()) <= MAX_RESPONSE, 'root response bound')
        return result

    script = marker_script(remote)
    encoded = base64.b64encode(script).decode()
    stage = ('set -eu\numask 077\n' +
             f'test ! -e {shlex.quote(remote)}; test ! -L {shlex.quote(remote)}\n'
             f'mkdir -m 700 {shlex.quote(remote)}\n' + parent.dir_guard(remote) +
             f'printf %s {shlex.quote(encoded)} | base64 -d > '
             f'{shlex.quote(remote + "/marker.sh")}\n'
             f'chmod 600 {shlex.quote(remote + "/marker.sh")}\n' +
             parent.file_guard(remote + '/marker.sh', len(script)) +
             f'test "$(sha256sum {shlex.quote(remote + "/marker.sh")} | cut -d " " -f1)" = {sha(script)}\n'
             'echo STAGE_READY\n')
    try:
        need(call(stage) == 'STAGE_READY\n', 'stage receipt')
        receipt = call(launch_command(remote, parent))
        match = re.fullmatch(r'LAUNCH_ACK ([1-9][0-9]*) ([1-9][0-9]*) ([1-9][0-9]*)\n',
                             receipt)
        need(match is not None, 'verified launch receipt')
        record['dispatch_pid'] = int(match[1])
        record['marker_pid'] = int(match[2])
        record['marker_start_ticks'] = int(match[3])
        root.save(record_path, record)

        time.sleep(3.4)
        artifacts = framed(call(fetch_command(remote, parent)))
        need(artifacts['marker.sh'] == script, 'exact marker script')
        need(artifacts['launcher.stdout'] == b'', 'launcher stdout empty')
        need(artifacts['launcher.stderr'] == b'', 'launcher stderr empty')
        pid_text = artifacts['marker.pid'].decode('ascii')
        need(re.fullmatch(r'[1-9][0-9]*\n', pid_text) is not None and
             int(pid_text) == record['marker_pid'], 'marker PID binding')
        identity = parse_stat(artifacts['marker.stat'])
        need(identity['pid'] == identity['pgrp'] == identity['session'] ==
             record['marker_pid'] and identity['start_ticks'] ==
             record['marker_start_ticks'] and identity['state'] not in ('Z', 'X'),
             'saved marker identity')
        boot0, up0, uptime0 = parse_stamp(artifacts['marker.start'], 'marker start')
        boot1, up1, uptime1 = parse_stamp(artifacts['marker.done'], 'marker done')
        need(boot0 == boot1 and 2.5 <= up1 - up0 <= 10.0,
             'same boot bounded marker lifetime')

        inventory = {}
        for name in FILES:
            raw = artifacts[name]
            (args.output / name).write_bytes(raw)
            inventory[name] = dict(size=len(raw), sha256=sha(raw))
        artifact_manifest = dict(schema='launcher-qualification-artifacts-v1',
                                 files=inventory)
        (args.output / 'artifact-manifest.json').write_text(
            json.dumps(artifact_manifest, indent=2, sort_keys=True) + '\n')
        result = dict(schema='launcher-qualification-result-v1', qualified=True,
                      terminal_valid=True, cleanup_verified=False,
                      marker_pid=record['marker_pid'],
                      marker_start_ticks=record['marker_start_ticks'],
                      boot_id=boot0, start_uptime=uptime0, done_uptime=uptime1,
                      elapsed_uptime=up1-up0, artifacts=inventory,
                      target_device_operations=0, physical_picture_observed=False)
        (args.output / 'result.json').write_text(
            json.dumps(result, indent=2, sort_keys=True) + '\n')
        record['terminal_valid'] = True
        root.save(record_path, record)

        need(call(cleanup_command(remote, parent, artifacts)) == 'STAGE_REMOVED\n',
             'cleanup receipt')
        result['cleanup_verified'] = True
        (args.output / 'result.json').write_text(
            json.dumps(result, indent=2, sort_keys=True) + '\n')
        record['cleanup_deferred'] = False
        record['cleanup_verified'] = True
        root.save(record_path, record)
        print(json.dumps(result, sort_keys=True))
    except BaseException as exc:
        record['failure_type'] = type(exc).__name__
        root.save(record_path, record)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--script-sha256')
    args = parser.parse_args()
    script_sha = sha(Path(__file__).read_bytes())
    if not args.execute:
        print(json.dumps(dict(schema='launcher-qualification-dry-v1',
                              script_sha256=script_sha, execute=False,
                              marker_sleep_seconds=3, automatic_ui=False,
                              target_device_operations=0,
                              physical_picture_observed=False), sort_keys=True))
        return
    execute(args, script_sha)


if __name__ == '__main__':
    main()
