#!/usr/bin/env python3
"""Hash-gated local reproduction of the QD Weber-input producer; no TV calls."""
from pathlib import Path
import hashlib
import io
import json
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / 'binaries/libave.so.0.1'
EXPECTED = 'a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777'
BASELINE = BASE / 'overnight/pqe-policy-baseline-20261026T174544Z.json'
BASELINE_SHA = '5c36124d0d510fff8ac5ff282cfc43c1a70854d065b76da68ad760ceb56482a4'
FUNCTIONS = {
    '_ZN9QDDimming15m_CalcWeberGainEv': (0x1793d1, 236, 0x1794b0),
    '_ZN21DimmingBackendRoseMQD15t_GetWeberValueEP14BackendWeber_t':
        (0x1c78d5, 844, 0x1c7bd0),
    '_Z17sdp_read_registerjPj': (0x2b061d, 168, 0x2b06b4),
}
LANDMARKS = {
    0x179408: ('ldr', 'r0, [r4, #0x10]'),
    0x17940a: ('ldr.w', 'r2, [r3, #0x45c]'),
    0x179416: ('ldr.w', 'r3, [r3, #0x1c4]'),
    0x179420: ('bne', '#0x1794a2'),
    0x1794a2: ('movw', 'r2, #0x3ff'),
    0x1794a6: ('str.w', 'r2, [r3, #0x458]'),
    0x1c78d8: ('movs', 'r2, #0x8c'),
    0x1c78e8: ('add.w', 'r0, r7, #8'),
    0x1c78f2: ('add.w', 'sb, r7, #0x94'),
    0x1c7906: ('rsb.w', 'r6, r4, #0x760000'),
    0x1c790c: ('add.w', 'r6, r6, #0x800'),
    0x1c7924: ('blx', '#0x904ac'),
    0x1c7928: ('ldr', 'r2, [r4], #4'),
    0x1c792c: ('cmp', 'r2, #0xe'),
    0x1c792e: ('bls', '#0x1c791c'),
    0x1c7934: ('str', 'r3, [r5, #8]'),
    0x1c79a0: ('adds', 'r1, r5, #4'),
    0x1c79a2: ('movw', 'r0, #0x5238'),
    0x1c79a6: ('movt', 'r0, #4'),
    0x1c79aa: ('blx', '#0x8fdec'),
    0x1c79ae: ('ldr', 'r2, [r5]'),
    0x1c79b4: ('vldr', 'd17, [pc, #0x218]'),
    0x1c79b8: ('mov', 'r4, r0'),
    0x1c79ba: ('vcvt.f64.s32', 'd16, s15'),
    0x1c79be: ('vmul.f64', 'd16, d16, d17'),
    0x1c79c2: ('vcvt.s32.f64', 's15, d16'),
    0x1c79c6: ('vstr', 's15, [r5, #0xc]'),
    0x1c79ea: ('mov', 'r0, r4'),
    0x2b062e: ('ldr.w', 'r3, [r0, #0x2f8]'),
    0x2b0634: ('beq', '#0x2b0688'),
    0x2b0648: ('cbz', 'r3, #0x2b067a'),
    0x2b064a: ('movs', 'r0, #0'),
    0x2b067e: ('blx', '#0x8b058'),
    0x2b0682: ('movs', 'r0, #0'),
    0x2b06ae: ('movs', 'r0, #0'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def va_bytes(elf, raw, address, size):
    for segment in elf.iter_segments():
        lo = int(segment['p_vaddr'])
        hi = lo + int(segment['p_filesz'])
        if segment['p_type'] == 'PT_LOAD' and lo <= address and address + size <= hi:
            offset = int(segment['p_offset']) + address - lo
            return raw[offset:offset + size]
    raise ValueError(f'Not file-backed: {address:x}+{size:x}')


def main():
    raw = SOURCE.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPECTED, 'ELF hash mismatch')
    elf = ELFFile(io.BytesIO(raw))
    require(elf['e_machine'] == 'EM_ARM' and elf.elfclass == 32, 'ELF identity')
    plt = elf.get_section_by_name('.plt')
    relplt = elf.get_section_by_name('.rel.plt')
    require(int(plt['sh_addr']) == 0x8a468 and relplt.num_relocations() == 2491,
            'Unexpected ARM PLT layout')
    dynsym = elf.get_section(relplt['sh_link'])
    plt_targets = {int(plt['sh_addr']) + 20 + 12 * index:
                   dynsym.get_symbol(relocation['r_info_sym']).name
                   for index, relocation in enumerate(relplt.iter_relocations())}
    for address, name in {
        0x904ac: '_Z17sdp_read_registerjPj',
        0x8fdec: '_Z16ave_frc_read_i2cjPj',
        0x8b058: 'sdp_dpreg_read',
        0x8c9a8: 'memset',
    }.items():
        require(plt_targets.get(address) == name, f'PLT drift {address:x}')
    symbols = {s.name: (int(s['st_value']), int(s['st_size']))
               for s in elf.get_section_by_name('.symtab').iter_symbols()}
    relocations = {}
    for section in elf.iter_sections():
        if isinstance(section, RelocationSection):
            table = elf.get_section(section['sh_link'])
            for relocation in section.iter_relocations():
                relocations[int(relocation['r_offset'])] = table.get_symbol(
                    relocation['r_info_sym']).name
    require(relocations[0x5a16f0] ==
            '_ZN21DimmingBackendRoseMQD15t_GetWeberValueEP14BackendWeber_t',
            'Base backend vptr+1c4 relocation')
    require(relocations[0x5a1948] ==
            '_ZN24DimmingBackendRoseMQDMNT15t_GetWeberValueEP14BackendWeber_t',
            'MNT backend vptr+1c4 relocation')
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    decoded = {}
    lines = [f'Source {SOURCE}', f'SHA256 {EXPECTED}',
             'ELF VAs, not reusable runtime addresses. Literal pools are printed as data.']
    for name, (symbol, size, code_end) in FUNCTIONS.items():
        require(symbols.get(name) == (symbol, size), f'Symbol drift {name}')
        start = symbol & ~1
        require(start <= code_end <= start + size, 'Invalid code span')
        code = va_bytes(elf, raw, start, code_end - start)
        instructions = list(decoder.disasm(code, start))
        require(sum(i.size for i in instructions) == len(code), 'Incomplete decode')
        lines.append(f'\n{name}: symbol0x{symbol:x}, size{size}, code_end0x{code_end:x}')
        for instruction in instructions:
            decoded[instruction.address] = (instruction.mnemonic, instruction.op_str)
            lines.append(f'{instruction.address:08x} {instruction.bytes.hex():8} '
                         f'{instruction.mnemonic:14} {instruction.op_str}')
        pool = va_bytes(elf, raw, code_end, start + size - code_end)
        for offset in range(0, len(pool), 4):
            word = struct.unpack('<I', pool[offset:offset+4])[0]
            lines.append(f'{code_end+offset:08x} .word 0x{word:08x}')
    for address, expected in LANDMARKS.items():
        require(decoded.get(address) == expected, f'Instruction drift {address:x}')
    scale = struct.unpack('<d', va_bytes(elf, raw, 0x1c7bd0, 8))[0]
    require(scale == 0.05750475823879242, 'Scale literal changed')
    # Bind the already captured backend, without re-running or claiming atomicity.
    captured = BASELINE.read_bytes()
    require(hashlib.sha256(captured).hexdigest() == BASELINE_SHA, 'Baseline hash mismatch')
    record = json.loads(captured)
    require(record['accepted'] is True and record['physical_state'] == 'unobserved',
            'Baseline qualification changed')
    summary = record['summary']
    bias = int(summary['ave_bias'], 16)
    backend = summary['backend']
    require(backend['typed'] is True and backend['class'] == 'DimmingBackendRoseMQD',
            'Unsupported live backend')
    require(int(backend['vptr'], 16) == bias + 0x5a152c, 'Live backend vptr mismatch')
    require(summary['decoded']['qd_outer_header']['words'][4] ==
            int(backend['object'], 16), 'Q+0x10/backend object mismatch')
    result = {
        'source_sha256': EXPECTED, 'symbols': len(FUNCTIONS),
        'instruction_landmarks': len(LANDMARKS), 'vtable_relocations': 2,
        'plt_targets': 4,
        'register_range': ['0x760800', '0x760888'], 'register_words': 35,
        'unsigned_threshold': 14, 'frc_read_selector': '0x45238',
        'signed_object_scale': scale, 'scale_exact_ratio': scale.as_integer_ratio(),
        'baseline_sha256': BASELINE_SHA,
        'static_expected_slot_target_at_captured_bias': hex(bias + 0x1c78d5),
        'qualification': 'Local landmarks and captured bindings; loop/formula/error CFG interpretation is manual. No physical/fault inference.',
    }
    print('\n'.join(lines))
    print('\nRESULT ' + json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
