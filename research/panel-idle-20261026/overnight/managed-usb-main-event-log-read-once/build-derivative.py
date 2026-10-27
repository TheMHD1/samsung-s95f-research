#!/usr/bin/env python3
"""Mechanically derive one fixed main-controller event-log reader."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE / 'managed-usb-current-callbacks-alias-read-once'
DOTNET = BASE.parents[1] / 'live-cast/sdk/runtime/dotnet'
PROGRAM_PARENT = '795bc39dd478146d6c947ecb4b0d604f18851d2655b9500182af1baf02e6b8c5'
WRAPPER_PARENT = 'b80c5a4553e351b23a842a96c5dc6bdf5275e811543cf19be8f0c53ca6ca43e8'
EVIDENCE_SHA = 'f5237ffb62bb0c6ef4fdad553d234ec71e50095754a259e6abb9861caf92ca58'
ADDRESS = 0x20205000
LENGTH = 0xc00
PACKET = 512
HEADER = struct.pack('<III', 0x101, ADDRESS, LENGTH).hex()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def replace_exact(text, old, new, count):
    need(text.count(old) == count, 'occurrence count ' + old)
    return text.replace(old, new)


def main():
    need(HEADER == '0101000000502020000c0000', 'derived header')
    need(LENGTH == 3072 and LENGTH // PACKET == 6 and LENGTH % PACKET == 0,
         'fixed transfer geometry')
    need(sha((SOURCE / 'Program.cs').read_bytes()) == PROGRAM_PARENT,
         'program parent pin')
    need(sha((SOURCE / 'run-once.py').read_bytes()) == WRAPPER_PARENT,
         'wrapper parent pin')
    evidence_raw = (HERE / 'evidence-input.json').read_bytes()
    need(sha(evidence_raw) == EVIDENCE_SHA, 'evidence snapshot pin')
    evidence = json.loads(evidence_raw)
    need(evidence['request_candidate'] == {
        'target': '0x101', 'address': '0x20205000', 'length': LENGTH,
        'header_hex': HEADER, 'usb_max_packet': PACKET,
        'expected_packets_if_full': 6,
        'mapper_range': '[0x20000000,0x20200000)',
        'mapper_changes_candidate': False}, 'evidence request')
    need(evidence['no_live_io'] is True, 'evidence I/O boundary')

    program = (SOURCE / 'Program.cs').read_text()
    program = replace_exact(program, 'const int Length = 64, TimeoutMs = 2000;',
                            'const int Length = 3072, TimeoutMs = 2000;', 1)
    program = replace_exact(program, '010100008005004540000000', HEADER.upper(), 2)
    geometry_anchor = (
        f'        Need(Convert.ToHexString(Header) == "{HEADER.upper()}", '
        '"fixed LE header");')
    program = replace_exact(
        program, geometry_anchor,
        geometry_anchor + '\n'
        '        Need(Length == 3072 && Length / 512 == 6 && Length % 512 == 0, '
        '"fixed six-packet response geometry");', 1)
    program = replace_exact(program, 'address = "0x45000580"',
                            'address = "0x20205000"', 1)
    program = replace_exact(program,
                            'opaque-current-callback-table-DMA-alias-IN',
                            'opaque-main-event-log-DMA-IN', 1)
    (HERE / 'Program.cs').write_text(program)

    project = 'ManagedUsbRtBlockReadOnce.csproj'
    (HERE / project).write_bytes((SOURCE / project).read_bytes())

    wrapper = (SOURCE / 'run-once.py').read_text()
    wrapper = replace_exact(
        wrapper,
        '"010100008005004540000000", "input_length": 64',
        f'"{HEADER}", "input_length": {LENGTH}', 1)
    wrapper = replace_exact(
        wrapper, 'usb-fixed-current-callbacks-alias-read-build-v1',
        'usb-fixed-main-event-log-read-build-v1', 1)
    wrapper = replace_exact(wrapper,
                            '"address": "0x45000580", "length": 64',
                            f'"address": "0x20205000", "length": {LENGTH}', 1)
    (HERE / 'run-once.py').write_text(wrapper)

    built = subprocess.run(
        [str(DOTNET), 'build', '-c', 'Release', '--nologo', str(HERE / project)],
        capture_output=True, text=True)
    (HERE / 'build.log').write_text(built.stdout + built.stderr)
    need(built.returncode == 0, 'build failed')

    dll = HERE / 'bin/Release/net6.0/ManagedUsbRtBlockReadOnce.dll'
    checks = []
    for args, expected in (([], 0), (['--self-test'], 0),
                           (['--execute'], 64), (['--unknown'], 63)):
        done = subprocess.run([str(DOTNET), str(dll), *args],
                              capture_output=True, text=True)
        need(done.returncode == expected, 'host check ' + str(args))
        checks.append(dict(args=args, exit_code=done.returncode,
                           stdout=done.stdout, stderr=done.stderr))

    names = ['Program.cs', project] + [
        'bin/Release/net6.0/ManagedUsbRtBlockReadOnce.' + suffix
        for suffix in ('dll', 'deps.json', 'runtimeconfig.json')]
    manifest = dict(
        schema='usb-fixed-main-event-log-read-build-v1',
        source_parent_sha256=PROGRAM_PARENT,
        wrapper_parent_sha256=WRAPPER_PARENT,
        evidence_input_sha256=EVIDENCE_SHA,
        fixed_target='0x101', fixed_address=hex(ADDRESS), fixed_length=LENGTH,
        header_hex=HEADER, usb_max_packet=PACKET,
        expected_packets_if_full=6, out_transfers=1, in_transfers=1,
        retries=0,
        files={name: dict(size=len((HERE / name).read_bytes()),
                          sha256=sha((HERE / name).read_bytes()))
               for name in names},
        checks=checks,
        acceptance_scope=(
            'Exact one-OUT and one-IN counts plus cleanup only; opaque fixed '
            '3072-byte snapshot at the candidate direct main-event-log '
            'buffer. Acceptance does not prove DMA visibility, log validity, '
            'formatter activity, fault causality, or running-image identity.'))
    raw = (json.dumps(manifest, indent=2) + '\n').encode()
    (HERE / 'build-manifest.json').write_bytes(raw)
    print(json.dumps(dict(
        program_sha256=sha((HERE / 'Program.cs').read_bytes()),
        wrapper_sha256=sha((HERE / 'run-once.py').read_bytes()),
        manifest_sha256=sha(raw), dll_sha256=sha(dll.read_bytes()),
        checks=len(checks)), indent=2))


if __name__ == '__main__':
    main()
