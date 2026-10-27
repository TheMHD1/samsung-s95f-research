#!/usr/bin/env python3
"""Disassemble exact acquired Home-exit consumers locally; no TV operations."""
from pathlib import Path
import hashlib
import io
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / 'binaries/rosem_frc.ko'
EXPECTED = 'c646b45d8ab5028defca91b5f8188bf905b8d29f8927fae292be591c94cdbd34'
FUNCTIONS = {'m_rosem_set_newhome_mode': (0x37b8, 624),
             'RosemFrc_SetNewhomeMode': (0x7bd8, 328),
             'RosemFrc_SetResolutionInfo': (0xb280, 1804),
             'm_rosem_set_tcon_frame_rate': (0x290, 500)}


def main():
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('Exact Rosem module hash mismatch')
    elf = ELFFile(io.BytesIO(raw))
    symbols = list(elf.get_section_by_name('.symtab').iter_symbols())
    table = elf.get_section_by_name('.symtab')
    text = elf.get_section_by_name('.text')
    text_index = next(i for i, section in enumerate(elf.iter_sections())
                      if section.name == '.text')
    relocations = {}
    for section in elf.iter_sections():
        if isinstance(section, RelocationSection) and section['sh_info'] == text_index:
            for relocation in section.iter_relocations():
                symbol = table.get_symbol(relocation['r_info_sym'])
                index = symbol['st_shndx']
                name = symbol.name or (elf.get_section(index).name
                                       if isinstance(index, int) else str(index))
                relocations[relocation['r_offset']] = (
                    f"{name}+0x{relocation.entry.get('r_addend', 0):x}")
    lines = [f'Source {SOURCE}', f'SHA256 {EXPECTED}',
             'Addresses are section-relative, not live addresses.',
             'BSS symbol offsets:']
    for symbol in symbols:
        index = symbol['st_shndx']
        if isinstance(index, int) and elf.get_section(index).name == '.bss':
            if symbol['st_size'] and symbol['st_value'] <= 0x380:
                lines.append(f"{symbol.name}: +0x{symbol['st_value']:x}, {symbol['st_size']} bytes")
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    for name, expected in FUNCTIONS.items():
        matches = [s for s in symbols if s.name == name]
        if len(matches) != 1:
            raise ValueError(f'Missing or ambiguous symbol {name}')
        symbol = matches[0]
        offset, size = symbol['st_value'], symbol['st_size']
        if (offset, size) != expected or symbol['st_shndx'] != text_index:
            raise ValueError(f'Unexpected symbol bounds for {name}')
        code = text.data()[offset:offset + size]
        instructions = list(decoder.disasm(code, offset))
        if sum(i.size for i in instructions) != size:
            raise ValueError(f'Incomplete decode for {name}')
        lines.append(f'\n{name}: 0x{offset:x}, {size} bytes, SHA256 {hashlib.sha256(code).hexdigest()}')
        for instruction in instructions:
            lines.append(f'{instruction.address:08x} {instruction.bytes.hex():8} '
                         f'{instruction.mnemonic:8} {instruction.op_str:40} '
                         f'{relocations.get(instruction.address, "")}')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
