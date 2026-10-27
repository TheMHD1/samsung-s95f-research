#!/usr/bin/env python3
"""Mechanically derive one fixed main-log index and flag reader."""
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
EVIDENCE_SHA = '39b01623db3b568eaded4efd30f8102899198c4ae0449bdf5740327e84ca010b'
ADDRESS = 0x45000e20
LENGTH = 64
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
    need(HEADER == '01010000200e004540000000', 'derived header')
    need(sha((SOURCE / 'Program.cs').read_bytes()) == PROGRAM_PARENT,
         'program parent pin')
    need(sha((SOURCE / 'run-once.py').read_bytes()) == WRAPPER_PARENT,
         'wrapper parent pin')
    evidence_raw = (HERE / 'evidence-input.json').read_bytes()
    need(sha(evidence_raw) == EVIDENCE_SHA, 'evidence snapshot pin')
    evidence = json.loads(evidence_raw)
    need(evidence['request_candidate'] == {
        'target': '0x101', 'cpu_start': '0x20000e20',
        'dma_address': '0x45000e20', 'length': LENGTH,
        'header_hex': HEADER, 'flag_snapshot_offset': 16,
        'index_snapshot_offset': 60}, 'evidence request')
    need(evidence['mapping']['addend'] == '0x25000000' and
         evidence['mapping']['core_tag'] == '0xa' and
         evidence['mapping']['live_alias_path_previously_qualified'] is True,
         'evidence mapping')
    need(evidence['no_live_io'] is True, 'evidence I/O boundary')

    program = (SOURCE / 'Program.cs').read_text()
    program = replace_exact(program, '010100008005004540000000', HEADER.upper(), 2)
    program = replace_exact(program, 'address = "0x45000580"',
                            'address = "0x45000e20"', 1)
    program = replace_exact(program,
                            'opaque-current-callback-table-DMA-alias-IN',
                            'opaque-main-log-index-and-flag-DMA-IN', 1)
    (HERE / 'Program.cs').write_text(program)

    project = 'ManagedUsbRtBlockReadOnce.csproj'
    (HERE / project).write_bytes((SOURCE / project).read_bytes())

    wrapper = (SOURCE / 'run-once.py').read_text()
    wrapper = replace_exact(wrapper, '010100008005004540000000', HEADER, 1)
    wrapper = replace_exact(
        wrapper, 'usb-fixed-current-callbacks-alias-read-build-v1',
        'usb-fixed-main-log-index-read-build-v1', 1)
    wrapper = replace_exact(wrapper,
                            '"address": "0x45000580", "length": 64',
                            '"address": "0x45000e20", "length": 64', 1)
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
        schema='usb-fixed-main-log-index-read-build-v1',
        source_parent_sha256=PROGRAM_PARENT,
        wrapper_parent_sha256=WRAPPER_PARENT,
        evidence_input_sha256=EVIDENCE_SHA,
        fixed_target='0x101', fixed_address=hex(ADDRESS), fixed_length=LENGTH,
        header_hex=HEADER, flag_snapshot_offset=16, index_snapshot_offset=60,
        files={name: dict(size=len((HERE / name).read_bytes()),
                          sha256=sha((HERE / name).read_bytes()))
               for name in names},
        checks=checks,
        acceptance_scope=(
            'Exact counts and cleanup only; opaque fixed 64-byte snapshot '
            'covering the candidate main status flag and log index. '
            'Acceptance does not assign byte semantics, prove fault '
            'causality, or establish running-image identity.'))
    raw = (json.dumps(manifest, indent=2) + '\n').encode()
    (HERE / 'build-manifest.json').write_bytes(raw)
    print(json.dumps(dict(
        program_sha256=sha((HERE / 'Program.cs').read_bytes()),
        wrapper_sha256=sha((HERE / 'run-once.py').read_bytes()),
        manifest_sha256=sha(raw), dll_sha256=sha(dll.read_bytes()),
        checks=len(checks)), indent=2))


if __name__ == '__main__':
    main()
