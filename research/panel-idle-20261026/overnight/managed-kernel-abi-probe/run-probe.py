#!/usr/bin/env python3
"""One ARM32 invalid-syscall probe through the installed CLR; dry by default.

Stages data files in a private /tmp directory, launches the stock runtime,
retains every transport response, and removes its exact private files.
No execution policy, installed file, driver state, tracing hook or map change.
"""
import argparse
import base64
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ACCESS = BASE.parent / 'root-access/s95f-access.py'
CLR = '/usr/share/dotnet/shared/Microsoft.NETCore.App/6.0.9'
BOOT = '00000000-0000-4000-8000-000000000000'
STOCK = {
    '/usr/bin/dotnet': 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310',
    CLR + '/libcoreclr.so': '5e5b5f160204058284d7fcced47fc57e65111e8203b53be5104350a63efd46ff',
    CLR + '/System.Private.CoreLib.dll': '5cfe69fbb72ba75a78b1b993c46a0d7983b2674d0affcee161ecdf4b08fb17f8',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((HERE / 'build-manifest.json').read_text())
    files = {}
    for name, digest in manifest['files'].items():
        data = (HERE / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Build/source integrity mismatch: ' + name)
        if name.startswith('bin/'):
            files[Path(name).name] = data
    assert set(files) == {'ArmKernelProbe.dll', 'ArmKernelProbe.runtimeconfig.json', 'ArmKernelProbe.deps.json'}
    if not args.run:
        print(json.dumps({'dry_run': True, 'stock_runtime': '/usr/bin/dotnet',
            'clr_path': CLR, 'private_data_files': {k: len(v) for k, v in files.items()},
            'probe': 'ARM32 getpid20, invalid bpf386(-1,NULL,0), perf364(NULL,0,-1,-1,0)',
            'temporary_files_only': True, 'physical_state': 'unobserved'}, indent=2))
        return
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = HERE / ('result-' + stamp + '.json')
    private = '/tmp/researcher-managed-abi-' + uuid.uuid4().hex
    assert re.fullmatch('/tmp/researcher-managed-abi-[0-9a-f]{32}', private)
    record = {'accepted': False, 'physical_state': 'unobserved', 'private_directory': private,
              'temporary_managed_data_staging': True, 'calls': []}
    destination.write_text(json.dumps(record, indent=2) + '\n')

    def root(command):
        if not 0 < len(command.encode()) <= 8192:
            raise ValueError('Root command size')
        p = subprocess.run(['python3', str(ACCESS), 'root', '--persistent-only', '--timeout', '25',
                            '--command', command], capture_output=True, text=True, timeout=55)
        item = {'command': command, 'transport_exit': p.returncode, 'transport_stderr': p.stderr}
        record['calls'].append(item)
        try:
            d = json.loads(p.stdout)
            item['response'] = d
        except ValueError:
            item['unparsed_stdout'] = p.stdout
            raise
        finally:
            destination.write_text(json.dumps(record, indent=2) + '\n')
        if p.returncode or p.stderr or d.get('model') != 'QN77S95FAFXZC' or not d.get('authenticated'):
            raise ValueError('Root transport/model')
        if d.get('uid') != 0 or d.get('euid') != 0 or d.get('root_persistence') != 'host-assisted':
            raise ValueError('Root identity/path')
        if d.get('global_system_files_unchanged_at_acquisition') is not True:
            raise ValueError('Acquisition source invariant')
        c = d['commands'][0]
        if c['exit_code'] or c['timed_out'] or c['stderr']:
            raise ValueError('Remote command failed; retain raw result')
        return c['stdout']

    created = False
    try:
        preflight = f'set -eu\ndate -u\ntest "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
        for name, digest in STOCK.items():
            preflight += f'test "$(sha256sum {name} | cut -d " " -f1)" = {digest}\n'
        preflight += 'cat /proc/uptime\necho STOCK_IDENTITY_MATCH\n'
        assert root(preflight).rstrip().endswith('STOCK_IDENTITY_MATCH')
        assert root(f'set -eu\nmkdir -m 700 {private}\necho PRIVATE_CREATED\n').strip() == 'PRIVATE_CREATED'
        created = True
        for name, data in files.items():
            for offset in range(0, len(data), 3072):
                encoded = base64.b64encode(data[offset:offset + 3072]).decode()
                root(f"set -eu\numask 077\nprintf %s '{encoded}' | base64 -d >> {private}/{name}\n")
        execute = 'set -eu\n'
        for name, data in files.items():
            digest = hashlib.sha256(data).hexdigest()
            execute += f'test "$(sha256sum {private}/{name} | cut -d " " -f1)" = {digest}\n'
        execute += f'''date -u
cat /proc/uptime
TMPDIR={private} DOTNET_CLI_HOME={private} DOTNET_EnableDiagnostics=0 DOTNET_CLI_TELEMETRY_OPTOUT=1 /usr/bin/dotnet --clr-path {CLR} --globalizationinvariant {private}/ArmKernelProbe.dll > {private}/stdout 2> {private}/stderr &
probe_pid=$!
( sleep 10
  kill -TERM "$probe_pid" 2>/dev/null || true
  sleep 2
  kill -KILL "$probe_pid" 2>/dev/null || true
) &
watchdog_pid=$!
probe_status=0
wait "$probe_pid" || probe_status=$?
kill "$watchdog_pid" 2>/dev/null || true
wait "$watchdog_pid" 2>/dev/null || true
echo "PROBE_EXIT=$probe_status"
echo MANAGED_STDOUT_BEGIN
cat {private}/stdout
echo MANAGED_STDOUT_END
echo MANAGED_STDERR_BEGIN
cat {private}/stderr
echo MANAGED_STDERR_END
cat /proc/uptime
date -u
'''
        stdout = root(execute)
        record['probe_output'] = stdout
        if 'PROBE_EXIT=0\n' not in stdout or 'PROBE_COMPLETE\n' not in stdout:
            raise ValueError('Probe not completed; interface presence unclassified')
        body = stdout.split('MANAGED_STDOUT_BEGIN\n', 1)[1].split('MANAGED_STDOUT_END\n', 1)[0]
        fields = dict(line.split('=', 1) for line in body.splitlines() if '=' in line)
        if fields.get('ARCH') != 'Arm' or fields.get('PTR_BYTES') != '4':
            raise ValueError('Probe architecture mismatch')
        if int(fields['PID_LIBC']) <= 0 or fields['PID_LIBC'] != fields['PID_SYSCALL']:
            raise ValueError('Probe PID mismatch')
        if fields['BPF_RETURN'] != '-1' or fields['PERF_RETURN'] != '-1':
            raise ValueError('Unexpected syscall result')
        if not all(0 < int(fields[x]) <= 4095 for x in ('BPF_ERRNO', 'PERF_ERRNO')):
            raise ValueError('Unexpected errno')
        record['decoded'] = fields
        record['accepted'] = True
    except Exception as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        if created:
            try:
                names = list(files) + ['stdout', 'stderr']
                cleanup = 'set -eu\nrm -f ' + ' '.join(private + '/' + x for x in names)
                cleanup += f'\nrmdir {private}\ntest ! -e {private}\necho PRIVATE_REMOVED\n'
                record['cleanup_confirmed'] = root(cleanup).strip() == 'PRIVATE_REMOVED'
            except Exception as error:
                record['cleanup_error'] = type(error).__name__ + ': ' + str(error)
                record['accepted'] = False
        destination.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'result': str(destination), 'accepted': record['accepted'],
                      'decoded': record.get('decoded'), 'error': record.get('error'),
                      'cleanup_confirmed': record.get('cleanup_confirmed')}, indent=2))
    if not record['accepted'] or not record.get('cleanup_confirmed'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
