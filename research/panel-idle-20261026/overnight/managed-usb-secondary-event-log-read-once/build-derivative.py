#!/usr/bin/env python3
"""Mechanically derive one fixed full secondary-controller event-log reader."""
import difflib
import hashlib
import json
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE / 'managed-usb-main-event-log-read-once'
D5 = BASE / 'executing-image-identity-20261027e'
HEADER_ACTUAL = D5 / 'secondary-log-header-read-once'
DOTNET = BASE.parents[1] / 'live-cast/sdk/runtime/dotnet'
PROGRAM_PARENT = '6bb6d6313beeea6ef464ce09e3d4c3a98e39d3d53ed78f53d19ccd7074e02c4f'
WRAPPER_PARENT = '245323c709dc098d343a1ee470c505ba909249126d4fe5645b12b20709ff7031'
EVIDENCE_SHA = '6eb6237ca5ffef037ff99f653aec20271217cf525872f94093b69e95cfdd2d68'
REPORT_SHA = '83d499bd9a44fd602b0211491521774f4fc53c86765fc3bb437386cd7fedcc6f'
VERIFIER_SHA = 'a82bdb61e7ff94e412a9c0304fef61f0819c157bcdca37503243c5fd98eb5ded'
ACTUAL_RECORD_SHA = '6bdf6ef5ae71915763f4aa38022184fd80c95c9795a5d89a878aa61e5133be59'
ACTUAL_PAYLOAD_SHA = 'c3adf13d0ea6ae4678758c97de3639dfcb068eca1e92fdb089d9212f3be020b4'
ACTUAL_STDOUT_SHA = 'fe08a1079175b24a6a1a2effc205ee53aeea572f5cabc0579de9c1ab707b11a3'
ADDRESS = 0x20200000
LENGTH = 0x3c0c
METADATA_LENGTH = 12
RING_LENGTH = 0x3c00
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


def copy_pinned(source, target, expected):
    raw = source.read_bytes()
    need(sha(raw) == expected, 'source pin ' + source.name)
    target.write_bytes(raw)
    need(sha(target.read_bytes()) == expected, 'local copy ' + target.name)


def main():
    need(HEADER == '01010000000020200c3c0000', 'derived header')
    need(LENGTH == METADATA_LENGTH + RING_LENGTH, 'exact header plus ring extent')
    need(LENGTH == 15372 and LENGTH // PACKET == 30 and LENGTH % PACKET == 12,
         'fixed non-packet-aligned transfer geometry')
    need(sha((SOURCE / 'Program.cs').read_bytes()) == PROGRAM_PARENT,
         'program parent pin')
    need(sha((SOURCE / 'run-once.py').read_bytes()) == WRAPPER_PARENT,
         'wrapper parent pin')
    evidence_raw = (HERE / 'evidence-input.json').read_bytes()
    need(sha(evidence_raw) == EVIDENCE_SHA, 'evidence snapshot pin')
    evidence = json.loads(evidence_raw)
    need(evidence['request_candidate'] == {
        'target': '0x101', 'address': '0x20200000', 'length': LENGTH,
        'header_hex': HEADER, 'usb_max_packet': PACKET,
        'response_geometry': '30*512+12',
        'extent': {'metadata_bytes': METADATA_LENGTH,
                   'ring_bytes': RING_LENGTH, 'total_bytes': LENGTH}},
        'evidence request')
    need(evidence['qualified_header_read']['record_sha256'] == ACTUAL_RECORD_SHA,
         'actual record pin')
    need(evidence['qualified_header_read']['payload_sha256'] == ACTUAL_PAYLOAD_SHA,
         'actual payload pin')
    need(evidence['qualified_header_read']['stdout_sha256'] == ACTUAL_STDOUT_SHA,
         'actual stdout pin')
    need(evidence['no_live_io'] is True, 'evidence I/O boundary')

    copy_pinned(D5 / 'secondary-event-log-buffer.md',
                HERE / 'secondary-event-log-buffer.md', REPORT_SHA)
    copy_pinned(D5 / 'verify-secondary-event-log-buffer.py',
                HERE / 'verify-secondary-event-log-buffer.py', VERIFIER_SHA)
    copy_pinned(HEADER_ACTUAL / 'record.json',
                HERE / 'qualified-header-record.json', ACTUAL_RECORD_SHA)
    copy_pinned(HEADER_ACTUAL / 'returned-block.bin',
                HERE / 'qualified-header-payload.bin', ACTUAL_PAYLOAD_SHA)
    copy_pinned(HEADER_ACTUAL / 'stdout.txt',
                HERE / 'qualified-header-stdout.txt', ACTUAL_STDOUT_SHA)

    parent_program = (SOURCE / 'Program.cs').read_text()
    program = replace_exact(parent_program,
                            'const int Length = 3072, TimeoutMs = 2000;',
                            'const int Length = 15372, TimeoutMs = 2000;', 1)
    program = replace_exact(program, '0101000000502020000C0000',
                            HEADER.upper(), 2)
    program = replace_exact(
        program,
        'Need(Length == 3072 && Length / 512 == 6 && Length % 512 == 0, '
        '"fixed six-packet response geometry");',
        'Need(Length == 15372 && Length / 512 == 30 && Length % 512 == 12, '
        '"fixed thirty-packet-plus-twelve response geometry");', 1)
    program = replace_exact(program, 'address = "0x20205000"',
                            'address = "0x20200000"', 1)
    program = replace_exact(program, 'opaque-main-event-log-DMA-IN',
                            'opaque-secondary-event-log-DMA-IN', 1)
    (HERE / 'Program.cs').write_text(program)

    project = 'ManagedUsbRtBlockReadOnce.csproj'
    (HERE / project).write_bytes((SOURCE / project).read_bytes())

    parent_wrapper = (SOURCE / 'run-once.py').read_text()
    wrapper = replace_exact(
        parent_wrapper,
        '"""Stage a hash-bound, fixed current-callback-table reader; no target work by default."""',
        '"""Stage a hash-bound, fixed secondary-event-log reader; no target work by default."""',
        1)
    wrapper = replace_exact(
        wrapper,
        '"0101000000502020000c0000", "input_length": 3072',
        f'"{HEADER}", "input_length": {LENGTH}', 1)
    wrapper = replace_exact(wrapper,
                            'usb-fixed-main-event-log-read-build-v1',
                            'usb-fixed-secondary-event-log-read-build-v1', 1)
    wrapper = replace_exact(wrapper,
                            '"address": "0x20205000", "length": 3072',
                            f'"address": "0x20200000", "length": {LENGTH}', 1)
    (HERE / 'run-once.py').write_text(wrapper)

    diff = ''.join(difflib.unified_diff(
        parent_program.splitlines(keepends=True), program.splitlines(keepends=True),
        fromfile='parent/Program.cs', tofile='derived/Program.cs'))
    diff += ''.join(difflib.unified_diff(
        parent_wrapper.splitlines(keepends=True), wrapper.splitlines(keepends=True),
        fromfile='parent/run-once.py', tofile='derived/run-once.py'))
    (HERE / 'derivation-diff.txt').write_text(diff)

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
    need(json.loads(checks[1]['stdout']) ==
         {'selfTestsPassed': 26, 'targetOperations': 0}, 'self-test summary')
    need(json.loads(checks[0]['stdout'])['inputLength'] == LENGTH,
         'dry-run fixed length')

    names = ['Program.cs', project] + [
        'bin/Release/net6.0/ManagedUsbRtBlockReadOnce.' + suffix
        for suffix in ('dll', 'deps.json', 'runtimeconfig.json')]
    manifest = dict(
        schema='usb-fixed-secondary-event-log-read-build-v1',
        source_parent_sha256=PROGRAM_PARENT,
        wrapper_parent_sha256=WRAPPER_PARENT,
        evidence_input_sha256=EVIDENCE_SHA,
        evidence_report_sha256=REPORT_SHA,
        evidence_verifier_sha256=VERIFIER_SHA,
        qualified_header_record_sha256=ACTUAL_RECORD_SHA,
        qualified_header_payload_sha256=ACTUAL_PAYLOAD_SHA,
        qualified_header_stdout_sha256=ACTUAL_STDOUT_SHA,
        fixed_target='0x101', fixed_address=hex(ADDRESS), fixed_length=LENGTH,
        header_hex=HEADER, usb_max_packet=PACKET,
        response_geometry='30*512+12',
        exact_extent=dict(metadata_bytes=METADATA_LENGTH,
                          ring_bytes=RING_LENGTH, total_bytes=LENGTH),
        out_transfers=1, in_transfers=1, retries=0,
        files={name: dict(size=len((HERE / name).read_bytes()),
                          sha256=sha((HERE / name).read_bytes()))
               for name in names},
        checks=checks,
        acceptance_scope=(
            'Exact one-OUT and one-IN counts plus cleanup only; opaque fixed '
            '15372-byte snapshot covering the 12-byte metadata header and '
            '0x3c00-byte secondary event-log ring. The prior 64-byte sample '
            'proves visibility only. Acceptance does not prove freshness, '
            'stability, running-image identity, formatter activity, record '
            'boundaries, log validity, or fault causality.'))
    raw = (json.dumps(manifest, indent=2) + '\n').encode()
    (HERE / 'build-manifest.json').write_bytes(raw)
    print(json.dumps(dict(
        program_sha256=sha((HERE / 'Program.cs').read_bytes()),
        wrapper_sha256=sha((HERE / 'run-once.py').read_bytes()),
        manifest_sha256=sha(raw), dll_sha256=sha(dll.read_bytes()),
        derivation_diff_sha256=sha((HERE / 'derivation-diff.txt').read_bytes()),
        evidence_report_sha256=sha((HERE / 'secondary-event-log-buffer.md').read_bytes()),
        evidence_verifier_sha256=sha((HERE / 'verify-secondary-event-log-buffer.py').read_bytes()),
        qualified_header_record_sha256=sha((HERE / 'qualified-header-record.json').read_bytes()),
        qualified_header_payload_sha256=sha((HERE / 'qualified-header-payload.bin').read_bytes()),
        qualified_header_stdout_sha256=sha((HERE / 'qualified-header-stdout.txt').read_bytes()),
        checks=len(checks)), indent=2))


if __name__ == '__main__':
    main()
