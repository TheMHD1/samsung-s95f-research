#!/usr/bin/env python3
"""Reconcile retained root envelopes, fixed builds, uploads and sector replies."""
import base64
import importlib.util
import json
from pathlib import Path
import struct
import shlex
from datetime import datetime

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
spec = importlib.util.spec_from_file_location('previous_audit', BASE / 'rt-onset-memory-20261027c/audit-runtime.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
need, sha = audit.need, audit.sha

def exact_plan(record, build):
    remote = record['remote_stage']
    import re
    need(re.fullmatch('/tmp/researcher-usb-emmcsector-[0-9a-f]{32}', remote) is not None, 'private stage shape')
    boot = audit.BOOT
    dotnet_sha = 'e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310'
    names = ['ManagedUsbEmmcSectorReadOnce.'+s for s in ('dll','deps.json','runtimeconfig.json')]
    commands = ['set -eu\numask 077\n'+f'test "$(cat /proc/sys/kernel/random/boot_id)" = {boot}\n'+f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {dotnet_sha}\n'+f'mkdir {shlex.quote(remote)}\necho STAGE_CREATED\n']
    for name in names:
        raw = (build/'bin/Release/net6.0'/name).read_bytes()
        encoded = base64.b64encode(raw).decode('ascii')
        target = remote+'/'+name
        temp = target+'.b64'
        for start in range(0,len(encoded),5000):
            commands.append(f'set -eu\nprintf %s {shlex.quote(encoded[start:start+5000])} >> {shlex.quote(temp)}\n')
        commands.append('set -eu\n'+f'base64 -d {shlex.quote(temp)} > {shlex.quote(target)}\n'+f'test "$(wc -c < {shlex.quote(target)})" = {len(raw)}\n'+f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {sha(raw)}\n'+f'rm {shlex.quote(temp)}\necho FILE_VERIFIED\n')
    dll = shlex.quote(remote+'/'+names[0])
    commands.append('set -eu\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n'+f'/usr/bin/dotnet {dll} --self-test\n'+'echo ACTIVE_READ_BEGIN\nrc=0\n'+f'/usr/bin/dotnet {dll} --execute || rc=$?\n'+'echo HELPER_EXIT=$rc\ncat /proc/uptime\n')
    files = [remote+'/'+n+suffix for n in names for suffix in ('','.b64')]
    commands.append('set -eu\n'+f'test ! -L {shlex.quote(remote)}\n'+f'if test -d {shlex.quote(remote)}; then\n'+'rm -f '+' '.join(map(shlex.quote,files))+'\n'+f'rmdir {shlex.quote(remote)}\nfi\n'+f'test ! -e {shlex.quote(remote)}\necho STAGE_ABSENT\n')
    need([c['command'] for c in record['calls']] == commands, 'complete exact command plan')
    last = None
    for call in record['calls']:
        start,end = (datetime.fromisoformat(call[key]) for key in ('started_utc','finished_utc'))
        need(start <= end and (last is None or last <= start), 'ordered call timestamps')
        need(call['command_bytes'] == len(call['command'].encode()), 'command byte count')
        last = end

def check(row):
    address = int(row['address'], 16)
    length = row.get('length',512)
    need(length in (512,8192), 'qualified fixed extents')
    build = Path(row['build'])
    directory = HERE / ('prefix-8192' if length == 8192 else 'sector-' + format(address, '06x'))
    record_raw = (directory/'record.json').read_bytes()
    record = json.loads(record_raw)
    exact_plan(record, build)
    uploaded = audit.root_calls(record)
    manifest_raw = (build/'build-manifest.json').read_bytes()
    need(sha(manifest_raw) == row['manifest_sha256'] == record['manifest_sha256'], 'manifest identity')
    manifest = json.loads(manifest_raw)
    header = struct.pack('<III', 0x203, address, length).hex()
    need(manifest['fixed_target'] == '0x203' and manifest['fixed_address'] == hex(address) and manifest['fixed_length'] == length and manifest['header_hex'] == row['header_hex'] == header, 'fixed request')
    original = BASE/'managed-usb-emmc-sector-read-once'
    expected_source = (original/'Program.cs').read_text().replace('030200000000000000020000', header.upper()).replace('address = "0x0"', f'address = "{address:#x}"')
    if length == 8192:
        expected_source = expected_source.replace('const int Length = 512,','const int Length = 8192,')
    need((build/'Program.cs').read_text() == expected_source, 'only fixed header and displayed address changed')
    expected_wrapper = (original/'run-once.py').read_text().replace('030200000000000000020000', header).replace('"address": "0x0"', f'"address": "{address:#x}"')
    if length == 8192:
        expected_wrapper = expected_wrapper.replace('"input_length": 512','"input_length": 8192').replace('"length": 512','"length": 8192')
    need((build/'run-once.py').read_text() == expected_wrapper, 'only wrapper request fields changed')
    need(sha((build/'run-once.py').read_bytes()) == row['wrapper_sha256'] == record['deployment_script_sha256'], 'wrapper hash')
    need(record['root_runner_sha256'] == '7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a', 'runner pin')
    expected_files = {'Program.cs', 'ManagedUsbEmmcSectorReadOnce.csproj', *('bin/Release/net6.0/ManagedUsbEmmcSectorReadOnce.' + s for s in ('dll','deps.json','runtimeconfig.json'))}
    need(set(manifest['files']) == expected_files, 'build inventory')
    need(set(uploaded) == {'ManagedUsbEmmcSectorReadOnce.' + s for s in ('dll','deps.json','runtimeconfig.json')}, 'upload inventory')
    for name, info in manifest['files'].items():
        raw = (build/name).read_bytes()
        need(len(raw) == info['size'] and sha(raw) == info['sha256'], 'build hash '+name)
        if name.startswith('bin/'):
            need(base64.b64decode(uploaded[Path(name).name], validate=True) == raw, 'upload exact '+name)
    need(record['request'] == dict(target='0x203', address=hex(address), length=length), 'record request')
    active = [c for c in record['calls'] if 'ACTIVE_READ_BEGIN' in c['command']]
    need(len(active) == 1 and active[0]['command'].count(' --execute') == 1, 'single invocation')
    stdout = (directory/'stdout.txt').read_text()
    need(stdout == active[0]['response']['commands'][0]['stdout'] and sha(stdout.encode()) == record['helper_stdout_sha256'], 'stdout identity')
    before, after, outcomes, gc = audit.parse_stdout(stdout, 26)
    need(len(outcomes) == 1, 'one result')
    payload = audit.transport(outcomes[0], length)
    need(record['cleanup_stdout'] == 'STAGE_ABSENT\n' == record['calls'][-1]['response']['commands'][0]['stdout'], 'cleanup')
    profile = (BASE/'selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin').read_bytes()
    need(sha(profile) == 'bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0', 'profile')
    packaged = profile[address:address+length]
    if length == 8192:
        need(address == 0, 'fixed prefix address')
        need(payload[:512] == (BASE/'rt-onset-memory-20261027c/emmc-sector-read-once/returned-sector.bin').read_bytes(), 'repeated header sector')
        need(payload[512:1024] == (HERE/'sector-000200/returned-sector.bin').read_bytes(), 'repeated vector sector')
    output = directory/'returned-sector.bin'
    if output.exists():
        need(output.read_bytes() == payload, 'preserved extraction')
    else:
        output.write_bytes(payload)
    return dict(address=hex(address), length=length, header_hex=header, record_sha256=sha(record_raw), manifest_sha256=sha(manifest_raw), stdout_sha256=sha(stdout.encode()), root_calls=len(record['calls']), uptime_before=before, uptime_after=after,
                payload_sha256=sha(payload), package_sha256=sha(packaged), package_equal=payload == packaged,
                changed_byte_offsets=[i for i,(a,b) in enumerate(zip(packaged,payload)) if a != b], first32_hex=payload[:32].hex(), gc_rows=len(gc), cleanup_verified=True)

def main():
    rows = [check(row) for row in json.loads((HERE/'builds.json').read_text()) if (HERE/('sector-'+format(int(row['address'],16),'06x'))/'stdout.txt').exists()]
    if (HERE/'prefix-8192/stdout.txt').exists():
        rows.append(check(json.loads((HERE/'prefix-build.json').read_text())))
    need(rows, 'no completed captures')
    need(len({r['payload_sha256'] for r in rows}) == len(rows), 'distinct fingerprint sectors')
    result = dict(schema='fixed-emmc-sector-fingerprints-v1', boot_id=audit.BOOT, runs=rows, all_payloads_distinct=True, storage_success_or_freshness_proved=False,
                  physical_state='unobserved', current_executing_image_identity_proved=False, repair_established=False)
    (HERE/'runtime-audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
