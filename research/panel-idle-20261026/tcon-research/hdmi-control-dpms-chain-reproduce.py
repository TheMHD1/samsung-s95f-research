#!/usr/bin/env python3
"""Offline userspace-to-kernel HDMI DPMS notification chain; no target access."""
from pathlib import Path
import argparse
import bisect
import hashlib
import importlib.util
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
from capstone.arm import ARM_OP_MEM, ARM_REG_PC, ARM_REG_INVALID
from elftools.elf.elffile import ELFFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LIB = ROOT/'overnight/serdes-hdmi-control-impl-copy-20261026/libhdmi-control-impl-sec.so.0.1'
LIB_SHA = '5eaef7e92eac9468bf41073ccece56a64a70339c3056c3ca2b62391171f4d2a1'
READER = HERE/'sdp-hdmi-cell-gate-reproduce.py'
READER_SHA = '8c97cb7cfed4b0e8694725e7017625b363b772f132ad3aaae32ccd699de28c67'

def require(ok, msg):
    if not ok:
        raise ValueError(msg)

def ror32(value, count):
    return ((value >> count) | (value << ((32-count) % 32))) & 0xffffffff

def arm_immediate(word):
    return ror32(word & 255, ((word >> 8) & 15)*2)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write-disassembly', action='store_true')
    args = ap.parse_args()
    require(hashlib.sha256(LIB.read_bytes()).hexdigest() == LIB_SHA, 'implementation hash')
    require(hashlib.sha256(READER.read_bytes()).hexdigest() == READER_SHA, 'kernel reader hash')
    spec = importlib.util.spec_from_file_location('dpms_kernel_reader', READER)
    kr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kr)
    kr.SOURCES.update({
        'switch': (ROOT/'binaries/tztv_hdmi_switch.ko', '11d9c53a0e08300bb12b1cafd513e3fc6ee84ba1bcd434007e459dce70fa82b6'),
        'api': (ROOT/'binaries/tztv_hdmi_switch_api.ko', 'c586a2601665a778a1e7401cd6b7553e03684f2e4536a282047b17059b7eec97'),
    })
    sw, api = kr.Source('switch'), kr.Source('api')
    output = ['# Exact HDMI control DPMS notification chain\n', f'Implementation SHA-256: {LIB_SHA}\n']
    with LIB.open('rb') as handle:
        elf = ELFFile(handle)
        require(elf['e_machine'] == 'EM_ARM' and elf['e_type'] == 'ET_DYN', 'ARM DSO')
        syms = elf.get_section_by_name('.dynsym')
        tx = elf.get_section_by_name('.text')
        mapping = sorted((s['st_value'], s.name[1]) for s in elf.get_section_by_name('.symtab').iter_symbols()
                         if s.name.startswith(('$a', '$t', '$d')))
        addresses = [a for a, _ in mapping]
        def read_va(addr, size):
            matches = [s for s in elf.iter_sections() if s['sh_type'] != 'SHT_NOBITS'
                       and s['sh_flags'] & 2 and s['sh_addr'] <= addr
                       and addr+size <= s['sh_addr']+s['sh_size']]
            require(len(matches) == 1, f'file VA bounds {addr:x}')
            sec = matches[0]
            return sec.data()[addr-sec['sh_addr']:addr-sec['sh_addr']+size]
        def u32(addr):
            return struct.unpack('<I', read_va(addr, 4))[0]
        # Mixed Thumb veneers make relocation ordinal * stub-size invalid.
        # Resolve actual ARM stub encodings, including rotated immediates,
        # to exact GOT relocation addresses instead.
        relplt = {r['r_offset']: syms.get_symbol(r['r_info_sym']).name
                  for r in elf.get_section_by_name('.rel.plt').iter_relocations()}
        plt = elf.get_section_by_name('.plt')
        resolved = {}
        for off in range(20, plt['sh_size']-11, 4):
            a = plt['sh_addr']+off
            x, y, z = struct.unpack_from('<III', plt.data(), off)
            if x & 0xfffff000 == 0xe28fc000 and y & 0xfffff000 == 0xe28cc000 and z & 0xfffff000 == 0xe5bcf000:
                got = (a+8+arm_immediate(x)+arm_immediate(y)+(z & 0xfff)) & 0xffffffff
                if got in relplt:
                    resolved[a] = (got, relplt[got])
        require(len(resolved) == len(relplt) == 77, 'all 77 PLT entries resolved')
        require({g for g, _ in resolved.values()} == set(relplt), 'PLT/GOT bijection')
        for a, name in [(0x1f48, 'hdmisw_set_ext_ctrls'), (0x203c, '__dlog_print'),
                        (0x2048, 'hdmi_control_impl_set_funcs'), (0x206c, 'hdmi_control_backend_data_inject'),
                        (0x2104, 'ioctl'), (0x218c, 'open64'), (0x21c8, 'close'),
                        (0x21ec, 'ppi_hdmi_control_get_backend_data_address')]:
            require(resolved[a][1] == name, 'PLT identity '+name)
        output.append('\n## All instruction/GOT-resolved PLT entries\n')
        output.extend(f'{a:08x} GOT {g:08x} {name}\n' for a, (g, name) in sorted(resolved.items()))
        functions = [
            ('ppi_hdmi_control_set_notify_dpms_type_impl', 0x8575, 164),
            ('hdmisw_set_ext_ctrls', 0x816d, 336),
            ('hdmi_control_impl_set_funcs', 0x8e79, 336),
            ('hdmi_control_backend_data_inject', 0x8fc9, 312),
            ('hdmicontrol_inject', 0x22dd, 100),
        ]
        decoded = {}
        for name, value, size in functions:
            sym = syms.get_symbol_by_name(name)[0]
            require((sym['st_value'], sym['st_size']) == (value, size), 'symbol '+name)
            start, end = value & ~1, (value & ~1)+size
            bounds = [start]+[a for a, _ in mapping if start < a < end]+[end]
            output.append(f'\n## {name} VA {start:x}..{end:x}\n')
            for lo, hi in zip(bounds, bounds[1:]):
                mode = mapping[bisect.bisect_right(addresses, lo)-1][1]
                raw = read_va(lo, hi-lo)
                if mode == 'd':
                    output.extend(f'{lo+o:08x} DATA {raw[o:o+4].hex()}\n' for o in range(0, len(raw), 4))
                    continue
                cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB if mode == 't' else CS_MODE_ARM)
                cs.detail = True
                ins = list(cs.disasm(raw, lo))
                require(sum(i.size for i in ins) == hi-lo, 'mapping-aware complete decode '+name)
                for i in ins:
                    decoded[i.address] = i
                    annotation = ''
                    if i.mnemonic in ('bl', 'blx') and i.op_str.startswith('#'):
                        target = int(i.op_str[1:], 16)
                        if target in resolved:
                            annotation = ' ; '+resolved[target][1]
                    output.append(f'{i.address:08x} {i.bytes.hex():10} {i.mnemonic:8} {i.op_str}{annotation}\n')
        def check(addr, mnemonic, operands):
            i = decoded[addr]
            require((i.mnemonic, i.op_str) == (mnemonic, operands), f'userspace landmark {addr:x}')
        for row in [(0x8598, 'movw', 'r3, #0x9d5'), (0x859c, 'movt', 'r3, #0xa0'),
                    (0x85aa, 'blx', '#0x1f48'), (0x81a2, 'mov.w', 'r3, #0xa00000'),
                    (0x819a, 'movw', 'r1, #0x5648'), (0x819e, 'movt', 'r1, #0xc018'),
                    (0x81b6, 'blx', '#0x2104'), (0x81aa, 'movs', 'r3, #1'),
                    (0x81a6, 'str', 'r4, [sp, #0x28]'), (0x85a8, 'str', 'r3, [sp, #0x2c]'),
                    (0x8596, 'str', 'r4, [sp, #0x24]'), (0x85f2, 'mov', 'r0, r5')]:
            check(*row)
        cid = (0xa0 << 16) | 0x9d5
        require(cid == 0x00a009d5, 'CID arithmetic')
        fd_path = (u32(0x8280)+0x8184) & 0xffffffff
        require(read_va(fd_path, 13) == b'/dev/video28\0', 'open path literal plus PC')
        # Decode the straight-line table builder: only literal loads, PC add,
        # GOT loads and table stores affect values used here. No execution.
        dynrel = {r['r_offset']: syms.get_symbol(r['r_info_sym']).name
                  for r in elf.get_section_by_name('.rel.dyn').iter_relocations() if r['r_info_sym']}
        values, slots = {}, {}
        for addr in sorted(a for a in decoded if 0x8e78 <= a < 0x8f42):
            i = decoded[addr]
            ops = i.operands
            if i.mnemonic == 'ldr' and len(ops) == 2 and ops[1].type == ARM_OP_MEM:
                mem = ops[1].mem
                if mem.base == ARM_REG_PC:
                    values[ops[0].reg] = u32(((addr+4)&~3)+mem.disp)
                elif mem.base in values and mem.index in values:
                    got = values[mem.base]+values[mem.index]+mem.disp
                    require(got in dynrel, 'builder GOT identity')
                    values[ops[0].reg] = dynrel[got]
                else:
                    raise ValueError('unexpected table-builder load')
            elif i.mnemonic == 'add' and i.op_str == 'r3, pc':
                values[ops[0].reg] += addr+4
            elif i.mnemonic == 'str' and len(ops) == 2:
                require(i.reg_name(ops[1].mem.base) == 'r0' and ops[1].mem.index == ARM_REG_INVALID, 'table destination')
                require(isinstance(values[ops[0].reg], str), 'table symbol source')
                require(ops[1].mem.disp not in slots, 'duplicate table slot')
                slots[ops[1].mem.disp] = values[ops[0].reg]
            elif i.mnemonic not in ('push', 'pop', 'bx', 'nop'):
                raise ValueError('unexpected table-builder instruction '+i.mnemonic)
        require(set(slots) == set(range(0, 128, 4)), 'complete 32-slot table')
        require(slots[0x38] == 'ppi_hdmi_control_set_notify_dpms_type_impl', 'DPMS slot publication')
        output.append('\n## Statically constructed implementation table\n')
        output.extend(f'+{o:02x} {name}\n' for o, name in sorted(slots.items()))
    rt = sw.elf.get_section_by_name('.rodata').data()
    idx = cid-((0xa00 << 12)+0x998)
    require(idx == 0x3d and 0x1628+int.from_bytes(rt[idx*2:idx*2+2], 'little', signed=True)*4 == 0x1da0, 'kernel CID dispatch')
    for obj, label, lo, hi in [(sw, 'DPMS switch case', 0x1da0, 0x1e14),
                               (sw, 'copy helper including zero-tail failure', 0x8a8, 0x998),
                               (api, 'API DPMS callback wrapper', 0x3280, 0x32c0),
                               (api, 'driver operation publication', 0x1d10, 0x1d94),
                               (api, 'operation table address', 0x1cfd0, 0x1cfe0),
                               (api, 'NotifyDpmsType', 0xc958, 0xc9dc)]:
        rows = obj.listing('.text', lo, hi)
        output.append(f'\n## {obj.name}: {label} .text+{lo:x}..{hi:x}\n')
        output.extend(f'{a:08x} {mn:8} {op}\n' for a, (mn, op) in rows.items())
    sw.relocation('.text', 0x1dbc, 'tztv_hdmi_switch_notify_dpms_type')
    sw.symbol('_copy_from_user', '.text', 0x8a8, 240)
    sw.relocation('.text', 0x924, '__arch_copy_from_user')
    sw.relocation('.text', 0x980, 'memset')
    case = sw.listing('.text', 0x1da8, 0x1dc0)
    require(list(case.values()) == [
        ('mov', 'x2, #1'), ('add', 'x0, sp, #0x210'),
        ('strb', 'wzr, [sp, #0x210]'), ('bl', '#0x8a8'),
        ('ldrb', 'w0, [sp, #0x210]'), ('bl', '#0x1dbc')],
        'notification proceeds without testing copy result')
    api.relocation('.text', 0x3284, 'sgHdmi_ops')
    api.relocation('.text', 0x328c, 'sgHdmi_ops')
    api.relocation('.text', 0x1d58, 'hdmiswitch_get_ops')
    api.relocation('.text', 0x1d60, 'sgHdmi_ops')
    api.relocation('.text', 0x1cfd0, '.data', 0xa30)
    api.relocation('.text', 0x1cfd4, '.data', 0xa30)
    api.relocation('.data', 0xa30+0x180+0x240, '.text', 0xc958)
    api.symbol('NotifyDpmsType', '.text', 0xc958, 132)
    api.relocation('.text', 0xc964, '.data', 0xa30)
    api.relocation('.text', 0xc968, '.data', 0xa30)
    notify = api.listing('.text', 0xc958, 0xc9dc)
    require(notify[0xc974] == ('strb', 'w20, [x19, #8]'), 'cached notification byte')
    require(notify[0xc9c8] == ('mov', 'w0, #0'), 'notification success return')
    for ad, name in [(0xc978, 'hdmisw_current_pid'), (0xc980, 'hdmisw_current_comm'),
                     (0xc99c, 'printk'), (0xc9b0, 'printk'), (0xc9c4, 'hdmisw_vlog')]:
        api.relocation('.text', ad, name)
    require([a for a, (mn, _) in notify.items() if mn in ('bl', 'blr')] ==
            [0xc978, 0xc980, 0xc99c, 0xc9b0, 0xc9c4], 'bounded notification calls are identity/log only')
    result = ''.join(output)
    dest = HERE/'hdmi-control-dpms-chain-v2.disasm'
    if args.write_disassembly:
        with dest.open('x') as out:
            out.write(result)
    else:
        require(dest.read_text() == result, 'saved disassembly equality')
    print('PASS: exact backend table +38, DPMS CID 00a009d5, ioctl route and cache/log handler.')
    print('Bounded static path only; downstream consumers, live invocation and panel causality remain unproved.')

if __name__ == '__main__':
    main()
