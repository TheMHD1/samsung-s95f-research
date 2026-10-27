#!/usr/bin/env python3
"""Offline exact-build PLT/caller recovery. Requires Capstone and pyelftools.

Run with PYTHONPATH=/tmp/tcon-capstone on this controller. Disassembly windows
may include literal pools; only identified branch/call instructions are used
as evidence. No live process instrumentation or TV access occurs.
"""
from pathlib import Path
import hashlib
import json
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BASE = Path(__file__).resolve().parent
binary = BASE.parent / 'binaries/avocd'
assert hashlib.sha256(binary.read_bytes()).hexdigest() == 'ab450eaf99c793f3c7a9360629b1a1677e9d86dcd74a1f93796b56ba07401de9'
with binary.open('rb') as stream:
    elf = ELFFile(stream)
    text = elf.get_section_by_name('.text')
    plt = elf.get_section_by_name('.plt')
    reloc = elf.get_section_by_name('.rel.plt')
    syms = elf.get_section(reloc['sh_link'])
    targets = {}
    for index, item in enumerate(reloc.iter_relocations()):
        name = syms.get_symbol(item['r_info_sym']).name
        if 'panel_mute' in name:
            targets[plt['sh_addr'] + 20 + 12 * index] = name
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.skipdata = True
    instructions = list(md.disasm(text.data(), text['sh_addr']))

    def calls(target):
        found = []
        for instruction in instructions:
            if instruction.mnemonic not in ('bl', 'blx', 'b.w'):
                continue
            try:
                dest = int(instruction.op_str.lstrip('#'), 0)
            except ValueError:
                continue
            if dest == target:
                found.append(instruction.address)
        return found

    def window(start, end):
        block = text.data()[start - text['sh_addr']:end - text['sh_addr']]
        return '\n'.join(f'{i.address:08x}: {i.mnemonic:9s} {i.op_str}'
                         for i in md.disasm(block, start))

    rows = []
    for target, name in targets.items():
        for site in calls(target):
            rows.append({'name': name, 'plt_va': hex(target), 'call_va': hex(site)})
    wrapper_sites = calls(0xac2c8)
    assert wrapper_sites == [0xaff70, 0xb13cc, 0xb1404, 0xb1550]
    assert [row['call_va'] for row in rows if row['name'] == 'ppi_ve_set_panel_mute'] == ['0xac2f6']
    (BASE / 'avocd-panel-mute-index.json').write_text(json.dumps({
        'qualification': 'ELF link VAs; Thumb code starts are even. Not runtime addresses.',
        'ppi_calls': rows, 'wrapper_va': '0xac2c8',
        'wrapper_callers': [hex(site) for site in wrapper_sites],
        'controller_global_va': '0x179434', 'reset_function_va': '0xb152c',
        'eligibility_function_va': '0xafe18',
    }, indent=2) + '\n')
    (BASE / 'avocd-panel-mute-calls.txt').write_text('\n\n'.join(
        row['name'] + ' call ' + row['call_va'] + '\n' +
        window(int(row['call_va'], 16) - 160, int(row['call_va'], 16) + 100)
        for row in rows) + '\n')
    (BASE / 'avocd-panel-mute-controller-calls.txt').write_text('\n\n'.join(
        f'CALLSITE {site:#x}\n' + window(site - 200, site + 120)
        for site in wrapper_sites) + '\n')
    (BASE / 'avocd-panel-mute-reset.txt').write_text('\n\n'.join(
        window(start, end) for start, end in
        [(0xafe18, 0xaff00), (0xb152c, 0xb15c4), (0xb13b4, 0xb1410)]) + '\n')
    print('Verified one panel-mute PPI call and four controller wrapper calls')
