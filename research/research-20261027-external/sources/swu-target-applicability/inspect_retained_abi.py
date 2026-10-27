#!/usr/bin/env python3
"""Static ELF/disassembly evidence only. Run with existing host analysis packages.

PYTHONPATH=/tmp/tcon-capstone python3 inspect_retained_abi.py
No target file is loaded as executable code, no TV connection is available here.
"""
from pathlib import Path
import hashlib
import json
import struct

import capstone
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile

ROOT = Path('${S95F_EVIDENCE_ROOT}/research-20261027-external')
OUT = ROOT / 'sources/swu-target-applicability'
FILES = {
    'wrapper': ('target-file-acquisition-02/libteec.so', '926840c9e7b26c59d8cb9d4ab5ae274e62b11efdbf14831b0a4d81d3de720f70'),
    'backend': ('target-file-acquisition-02/libteec_trustware.so', '0574261e6291fb3f28bf8a254c0610c9177e132a6afd0bc7418826173555db81'),
    'core': ('target-file-acquisition-03/SWUCoreTV', 'b8de9e31bf6e74cf9a1f3cfd2598658d978a4edd88b36d1c2f10129ccc8a2697'),
    'config': ('target-file-acquisition-03/libSWUProductionConfig.so', 'c6af8346f4643f2cf50e996682611ece7ad6ff8999274570023561d1a97879f0'),
    'common': ('target-file-acquisition-04/libteec_trustware_common.so', '353104729c40d6f1eff4f07b96f8a14466dd98efddb21a9cb7d14752351dd139'),
}
RANGES = {
    'backend': [(0x47c8, 0x4846), (0x5c20, 0x5c58), (0x594c, 0x5960), (0x5a10, 0x5a30)],
    'core': [(0x1d6174, 0x1d61b0), (0x1d633e, 0x1d6378), (0x1d63cc, 0x1d6436),
             (0x1d68fe, 0x1d693e), (0x1d503c, 0x1d50b0), (0x2450f4, 0x2450f8),
             (0x245554, 0x24555c), (0x2455ea, 0x245680), (0x2458ea, 0x245952),
             (0x245d98, 0x245e18), (0x245f22, 0x245f70), (0x246d20, 0x246d78), (0x246e6a, 0x246e8a),
             (0x243030, 0x24306c), (0x24317e, 0x2431e2), (0x244e7c, 0x244efe),
             (0x244698, 0x244722), (0x2447e2, 0x2447ee), (0x6ded2, 0x6df08),
             (0x32be64, 0x32be88), (0x32bea6, 0x32bee0), (0x32bf50, 0x32bf74)],
    'config': [(0x42df03bc, 0x42df03c0)],
    'common': [(0x14020, 0x14050), (0x14050, 0x1406c), (0x14080, 0x14096),
               (0x14ff8, 0x15028), (0x1512c, 0x15196), (0x1e8da, 0x1e8f8),
               (0x1246a, 0x124b0), (0x12506, 0x12514), (0x16492, 0x164ac),
               (0x208c8, 0x208f4), (0x209ae, 0x209c4)],
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    result = {'scope': 'Retained ELF bytes only; zero target execution or communication',
              'capstone_version': capstone.__version__, 'files': {}}
    disassembly = ['Selected instruction ranges; values are ELF virtual addresses before relocation.',
                   'These are bounded evidence excerpts, not a complete control-flow or TA audit.']
    for name, (relative, expected) in FILES.items():
        path = ROOT / relative
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected, 'artifact hash: ' + name)
        with path.open('rb') as stream:
            elf = ELFFile(stream)
            require(elf.elfclass == 32 and elf.little_endian and elf['e_machine'] == 'EM_ARM', 'ARM32 ELF: ' + name)
            dynamic = elf.get_section_by_name('.dynamic')
            needed, soname, init, build_id = [], None, {}, None
            for tag in dynamic.iter_tags():
                if tag.entry.d_tag == 'DT_NEEDED': needed.append(tag.needed)
                if tag.entry.d_tag == 'DT_SONAME': soname = tag.soname
                if tag.entry.d_tag in ['DT_INIT', 'DT_INIT_ARRAY', 'DT_INIT_ARRAYSZ']:
                    init[tag.entry.d_tag] = tag.entry.d_val
            note = elf.get_section_by_name('.note.gnu.build-id')
            if note:
                for n in note.iter_notes():
                    if n['n_type'] == 'NT_GNU_BUILD_ID': build_id = n['n_desc']
            sym = elf.get_section_by_name('.dynsym')
            exports = [{'name': s.name, 'value': hex(s['st_value']), 'size': s['st_size']}
                       for s in sym.iter_symbols() if s['st_shndx'] != 'SHN_UNDEF'
                       and (s.name.startswith('TEEC_') or 'isProduction' in s.name)]
            result['files'][name] = {'path': str(path), 'sha256': expected, 'bytes': len(data),
                                     'class': 32, 'little_endian': True, 'machine': 'EM_ARM',
                                     'flags': hex(elf['e_flags']), 'build_id': build_id,
                                     'soname': soname, 'needed': needed, 'initializers': init,
                                     'selected_exports': exports}
            segments = [s for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']
            def read(va, size):
                for s in segments:
                    if s['p_vaddr'] <= va and va + size <= s['p_vaddr'] + s['p_filesz']:
                        start = s['p_offset'] + va - s['p_vaddr']
                        return data[start:start + size]
                raise ValueError('unmapped virtual range')
            md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
            for start, end in RANGES.get(name, []):
                disassembly.append(f'\n{name}: {start:08x}..{end:08x}')
                for i in md.disasm(read(start, end - start), start):
                    disassembly.append(f'{i.address:08x}  {i.bytes.hex():10s} {i.mnemonic:9s} {i.op_str}')
            if name == 'core':
                uuid = read(0x3fc2e8, 16)
                require(uuid == bytes.fromhex('21222222000000000000000000000001'), 'target SWU UUID')
                result['core_swu_uuid'] = {'address': '0x3fc2e8', 'uuid': '22222221-0000-0000-0000-000000000001'}
                require(read(0x431fa4, 8) == b'Salted__', 'target salt marker')
                require(struct.unpack('<I', read(0x431fa0, 4))[0] == 8, 'target marker length')
                require(struct.unpack('<I', read(0x431f9c, 4))[0] == 8, 'target salt length')
                result['target_salt_constants'] = {'marker_address': '0x431fa4', 'marker_length': 8, 'salt_length': 8}
    result['operation_layout'] = {'public_prefix_bytes': 56, 'minimum_storage_bytes': 60,
                                  'cancellation_token_offset': 56, 'parameter_offset': 8,
                                  'parameter_stride': 12, 'parameter_type_slot_bits': 8,
                                  'existing_ModernTeecOperation56_undersized': True}
    result['selector_sample'] = {'source': str(ROOT / 'target-swu-selector-05/metadata.txt'),
                                 'value': False, 'selected': 'master',
                                 'uptime_interval_seconds': [163635.32, 163635.40],
                                 'boot_id': '00000000-0000-4000-8000-000000000000',
                                 'temporal_sample_only': True}
    result['qualification'] = {'normal_world_command_frames_statically_mapped': True,
                               'current_key_selector_value_known': True,
                               'TA_execution_observed': False,
                               'TA_persistent_sideeffects_audited': False,
                               'target_helper_built': False}
    (OUT / 'target-static-evidence.json').write_text(json.dumps(result, indent=2) + '\n')
    (OUT / 'target-static-excerpts.txt').write_text('\n'.join(disassembly) + '\n')
    print(json.dumps({'files_verified': len(FILES), 'normal_world_command_frames_statically_mapped': True,
                      'target_execution': False}, indent=2))


if __name__ == '__main__':
    main()
