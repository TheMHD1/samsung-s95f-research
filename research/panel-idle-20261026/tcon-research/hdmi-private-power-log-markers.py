#!/usr/bin/env python3
"""Offline stock-log lineage for a private Samsung HDMI PM caller.

Positive emission candidates only; no trace silence or causal inference.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
READER_SHA = '8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67'
API_SHA = 'c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write-artifacts', action='store_true')
    args = ap.parse_args()
    reader = HERE/'sdp-hdmi-cell-gate-reproduce.py'
    require(hashlib.sha256(reader.read_bytes()).hexdigest() == READER_SHA, 'reader hash')
    spec = importlib.util.spec_from_file_location('private_pm_log_reader', reader)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SOURCES['switch_api'] = (BASE/'binaries/tztv_hdmi_switch_api.ko', API_SHA)
    src = mod.Source('switch_api')
    spans = []
    rows = {}
    for name, lo, size in (('hdmi_hwc_log', 0x320, 152),
                           ('suspend_hdmi_suspend', 0x1bb8, 152),
                           ('suspend_hdmi_resume', 0x1c50, 188)):
        src.symbol(name, '.text', lo, size)
        listing = src.listing('.text', lo, lo+size)
        spans.append((name, listing))
        rows.update(listing)
    for at, mn, op in (
        (0x1bcc, 'ldrb', 'w0, [x19, #5]'), (0x1bd0, 'cbz', 'w0, #0x1be4'),
        (0x1c1c, 'strb', 'w1, [x19, #5]'),
        (0x1c64, 'ldrb', 'w0, [x19, #5]'), (0x1c68, 'cmp', 'w0, #1'),
        (0x1c6c, 'b.eq', '#0x1c80'), (0x1cf4, 'strb', 'wzr, [x19, #5]'),
        (0x330, 'add', 'x0, sp, #0x70'), (0x390, 'add', 'x0, sp, #0x60'),
        (0x398, 'add', 'x0, sp, #0x60'), (0x3a4, 'blr', 'x1'),
    ):
        require(rows.get(at) == (mn, op), f'landmark {at:x}')
    for at, target, addend in (
        (0x1bc4, '.bss', 0x1e8), (0x1bc8, '.bss', 0x1e8),
        (0x1c5c, '.bss', 0x1e8), (0x1c60, '.bss', 0x1e8),
        (0x38c, 'vsnprintf', 0), (0x394, 'trace_early_message', 0),
        (0x39c, '.bss', 0), (0x3a0, '.bss', 0),
        (0x1c04, 'sdp_runtime_pm_put', 0), (0x1ca0, 'sdp_runtime_pm_get', 0),
        (0x1bfc, '.rodata.str1.8', 0xab8), (0x1c00, '.rodata.str1.8', 0xab8),
        (0x1c98, '.rodata.str1.8', 0xab8), (0x1c9c, '.rodata.str1.8', 0xab8),
    ):
        src.relocation('.text', at, target, addend)
    ro = src.elf.get_section_by_name('.rodata.str1.8').data()
    require(ro[0xab8:].split(b'\0', 1)[0] == b'sdp-hdmi', 'private record name')
    markers = []
    for operation, position, literal, load, call, message in (
        ('put', 'before', 0xa70, 0x1bf0, 0x1bf8,
         '[HDMISW] suspend_hdmi_suspend : sdp_runtime_pm_put(sdp-hdmi) [IN]'),
        ('put', 'after', 0xac8, 0x1c08, 0x1c10,
         '[HDMISW] suspend_hdmi_suspend : sdp_runtime_pm_put(sdp-hdmi) [OUT]'),
        ('get', 'before', 0xb88, 0x1c8c, 0x1c94,
         '[HDMISW] suspend_hdmi_resume : sdp_runtime_pm_get(sdp_hdmi) [IN]'),
        ('get', 'after', 0xbd0, 0x1ca4, 0x1cac,
         '[HDMISW] suspend_hdmi_resume : sdp_runtime_pm_get(sdp_hdmi) [OUT]'),
    ):
        require(ro[literal:].split(b'\0', 1)[0].decode() == message, 'literal text')
        src.relocation('.text', load, '.rodata.str1.8', literal)
        src.relocation('.text', load+4, '.rodata.str1.8', literal)
        src.relocation('.text', call, 'hdmi_hwc_log', 0)
        markers.append({'operation': operation, 'position_relative_to_private_call': position,
                        'exact_message': message, 'literal_section': '.rodata.str1.8',
                        'literal_offset': hex(literal), 'log_call_text_offset': hex(call)})
    ex = src.elf.get_section_by_name('.rela__ksymtab')
    sy = src.elf.get_section(ex['sh_link'])
    exported = [sy.get_symbol(r['r_info_sym']).name for r in ex.iter_relocations()]
    for name in ('suspend_hdmi_suspend', 'suspend_hdmi_resume'):
        require(exported.count(name) == 1, 'export '+name)

    contract = {'module_sha256': API_SHA, 'private_record': 'sdp-hdmi', 'markers': markers,
                'physical_state': 'unobserved', 'absence_claim_supported': False,
                'limits': ['caller-specific stock messages, not universal callback instrumentation',
                           'an OUT row proves return to this caller, not callback or hardware success',
                           'record lookup/bypass/count gates can skip a hardware callback',
                           'raw message identity does not uniquely prove which binary emitted it',
                           'no physical onset, recovery, prevention, or cause established']}
    listing = ''.join('\n## '+name+'\n'+''.join(f'{a:08x}  {mn:8} {op}\n'
                      for a, (mn, op) in ins.items()) for name, ins in spans)
    outputs = {HERE/'hdmi-private-power-log-markers.disasm': listing,
               HERE/'hdmi-private-power-log-markers.json': json.dumps(contract, indent=2)+'\n'}
    for path, text in outputs.items():
        if args.write_artifacts:
            with path.open('x') as out:
                out.write(text)
        else:
            require(path.read_text() == text, 'saved artifact equality '+path.name)
    print('PASS: exact stock IN/OUT literals surround private sdp-hdmi get/put; logger calls trace_early_message.')
    print('Positive correlation candidates only; no universal coverage, live binding, physical state, or causation.')


if __name__ == '__main__':
    main()
