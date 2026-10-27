#!/usr/bin/env python3
"""Local exact-build send/read wrapper dataflow evidence; no TV operations."""
from pathlib import Path
import hashlib
import io
import json
from capstone import Cs, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / 'binaries/libave.so.0.1'
SHA = 'a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777'
FUNCTIONS = {
    '_Z28ave_tcon_api_send_onecommandyPj': (0x2519d9, 224, 0x251a8c),
    '_Z28ave_tcon_api_read_onecommandyPj': (0x251ab9, 232, 0x251b74),
    '_ZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_t':
        (0x1c6275, 252, 0x1c634c),
}
LANDMARKS = {
    0x2519f2: ('cbz', 'r2, #0x251a2c'),
    0x2519f4: ('ldr', 'r2, [r2]'),
    0x2519f6: ('adds', 'r1, r7, #4'),
    0x2519f8: ('movw', 'r0, #0x749f'),
    0x2519fc: ('movt', 'r0, #0xc010'),
    0x251a00: ('uxth', 'r3, r3'),
    0x251a02: ('str', 'r2, [r7, #8]'),
    0x251a04: ('str', 'r4, [r7, #0x10]'),
    0x251a06: ('movs', 'r2, #0x12'),
    0x251a08: ('str', 'r3, [r7, #0xc]'),
    0x251a0a: ('str', 'r2, [r7, #4]'),
    0x251a0c: ('blx', '#0x8df5c'),
    0x251a24: ('mov', 'r0, r4'),
    0x251ac8: ('mov', 'r4, r2'),
    0x251ad6: ('ldr', 'r2, [r2]'),
    0x251ae8: ('movs', 'r3, #0x13'),
    0x251aee: ('blx', '#0x8df5c'),
    0x251af4: ('blt', '#0x251b3a'),
    0x251af6: ('ldr', 'r3, [r7, #8]'),
    0x251af8: ('str', 'r3, [r4]'),
    0x1c62b4: ('blx', '#0x8db9c'),
    0x1c62b8: ('ldr', 'r1, [r7]'),
    0x1c62c4: ('blx', '#0x9023c'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    raw = SOURCE.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SHA, 'ELF hash mismatch')
    elf = ELFFile(io.BytesIO(raw))
    require(elf.elfclass == 32 and elf['e_machine'] == 'EM_ARM', 'ELF identity')
    symbols = {s.name: (int(s['st_value']), int(s['st_size']))
               for s in elf.get_section_by_name('.symtab').iter_symbols()}
    def read_va(address, size):
        for segment in elf.iter_segments():
            lo = int(segment['p_vaddr'])
            if segment['p_type'] == 'PT_LOAD' and lo <= address and address+size <= lo+int(segment['p_filesz']):
                start = int(segment['p_offset']) + address-lo
                return raw[start:start+size]
        raise ValueError(f'VA not file-backed: {address:x}+{size:x}')
    plt = elf.get_section_by_name('.plt')
    rel = elf.get_section_by_name('.rel.plt')
    require(int(plt['sh_addr']) == 0x8a468 and rel.num_relocations() == 2491, 'PLT layout')
    dynsym = elf.get_section(rel['sh_link'])
    targets = {int(plt['sh_addr'])+20+12*i: dynsym.get_symbol(r['r_info_sym']).name
               for i, r in enumerate(rel.iter_relocations())}
    for address, name in {
        0x8df5c: '_Z10tcon_ioctlmPv',
        0x8db9c: '_Z28ave_tcon_api_send_onecommandyPj',
        0x9023c: '_Z17ave_frc_write_i2cjj',
    }.items():
        require(targets.get(address) == name, f'PLT mismatch {address:x}')
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    found = {}
    lines = [f'Source {SOURCE}', f'SHA256 {SHA}',
             'ELF virtual addresses; code and literal pools separated.']
    for name, (symbol, size, code_end) in FUNCTIONS.items():
        require(symbols.get(name) == (symbol, size), f'Symbol mismatch {name}')
        start = symbol & ~1
        code = read_va(start, code_end-start)
        decoded = list(decoder.disasm(code, start))
        require(sum(i.size for i in decoded) == len(code), 'Incomplete code decode')
        lines.append(f'\n{name}: 0x{symbol:x}, size{size}, code_end0x{code_end:x}')
        for instruction in decoded:
            found[instruction.address] = (instruction.mnemonic, instruction.op_str)
            lines.append(f'{instruction.address:08x} {instruction.bytes.hex():8} '
                         f'{instruction.mnemonic:12} {instruction.op_str}')
        pool = read_va(code_end, start+size-code_end)
        lines.append(f'{code_end:08x} literal_pool {pool.hex()}')
    for address, expected in LANDMARKS.items():
        require(found.get(address) == expected, f'Instruction mismatch {address:x}')
    print('\n'.join(lines))
    print('\nRESULT ' + json.dumps({
        'source_sha256': SHA, 'symbols': len(FUNCTIONS),
        'instruction_landmarks': len(LANDMARKS), 'plt_targets': 3,
        'ioctl_request': '0xc010749f', 'envelope_bytes': 16,
        'send_selector': 18, 'read_selector': 19,
        'send_envelope_words': ['18', 'caller_value', 'command_high16', 'command_low32'],
        'qualification': 'Landmarks pin code; caller-pointer lifetime and absence of copyback are manually reviewed CFG/dataflow. Defined stock execution only; no wire/application/physical claim.',
    }, sort_keys=True))


if __name__ == '__main__':
    main()
