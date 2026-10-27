#!/usr/bin/env python3
"""Reproduce the bounded qdf_tcon F3:0x128 cache/replay analysis offline.

This program reads only the pinned local kernel module.  It performs no root,
network, process-memory, device, ioctl, getter, setter, or TV operation.

Run with:
    PYTHONPATH=/tmp/tcon-capstone python3 \
      tcon-research/qd-kernel-output-replay-reproduce.py

Use ``--write-output`` only to regenerate the deterministic companion excerpt.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct

from capstone import CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN, Cs
from elftools.elf.elffile import ELFFile


BASE = Path(__file__).resolve().parents[1]
MODULE = BASE / "binaries/qdf_tcon.ko"
OUTPUT = BASE / "tcon-research/qd-kernel-output-replay.disasm"
MODULE_SHA256 = "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"
TABLE_OFFSET = 0x15F0
TABLE_COUNT = 226
TABLE_SHA256 = "1ca59d38d74dda0bbaf0d40453c57c6b53d0d3c692cee627d1856c9fd73bebb4"
F3_128 = 0x0000F30000000128


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-output", action="store_true")
    args = parser.parse_args()

    module_bytes = MODULE.read_bytes()
    actual_hash = hashlib.sha256(module_bytes).hexdigest()
    require(actual_hash == MODULE_SHA256, f"unexpected qdf_tcon hash: {actual_hash}")

    with MODULE.open("rb") as stream:
        elf = ELFFile(stream)
        require(elf.elfclass == 64 and elf.little_endian, "expected ELF64 little-endian module")
        require(elf.header["e_machine"] == "EM_AARCH64", "expected AArch64 module")
        text = elf.get_section_by_name(".text")
        init = elf.get_section_by_name(".init.text")
        rodata = elf.get_section_by_name(".rodata")
        symtab = elf.get_section_by_name(".symtab")
        require(all(section is not None for section in (text, init, rodata, symtab)),
                "required ELF section missing")
        text_bytes = text.data()
        init_bytes = init.data()
        rodata_bytes = rodata.data()
        symbols = {symbol.name: symbol for symbol in symtab.iter_symbols()}

        expected_symbols = {
            "QDFTcon_InitVariable": (0x0F98, 1100, 3),
            "QDFTcon_Tcon_InitDevice": (0x0F910, 3064, 3),
            "QDFTcon_SendOneCommand": (0x0D120, 304, 3),
            "m_send_cmd_with_lock.constprop.0": (0x0BBA0, 1632, 3),
            "m_set_npc_lumi_global_gain": (0x0DBA8, 236, 3),
            "m_set_npc_dim_lvl2": (0x0E2F8, 160, 3),
            "m_set_ss_brightness": (0x0EB60, 160, 3),
            "m_register_recovery_noFramerate": (0x0F6D8, 568, 3),
            "m_tcon_recovery_frame_mode": (0x107E8, 320, 3),
            "QDFTcon_MonitorTemperatureSensor": (0x10928, 1472, 3),
            "QDFTcon_Resume": (0x10EE8, 364, 3),
            "QDFTcon_EW_QdNpcTest": (0x115E0, 616, 3),
            "m_set_power_control": (0x11848, 832, 3),
            "QDFTcon_SetQdTconPowerControl": (0x11C48, 304, 3),
            "QDFTcon_SetElSensing": (0x11D78, 1184, 3),
            "QDFTcon_SetOffSensing": (0x13690, 1436, 3),
            "m_npc_lut_register_data": (0x160, 8, 21),
            "m_npc_lut_register_info": (0x300, 24, 21),
        }
        for name, expected in expected_symbols.items():
            symbol = symbols.get(name)
            require(symbol is not None, f"missing symbol: {name}")
            actual = (int(symbol["st_value"]), int(symbol["st_size"]),
                      int(symbol["st_shndx"]))
            require(actual == expected, f"symbol mismatch for {name}: {actual!r}")

        table_bytes = rodata_bytes[TABLE_OFFSET:TABLE_OFFSET + TABLE_COUNT * 8]
        require(len(table_bytes) == TABLE_COUNT * 8, "short command table")
        require(hashlib.sha256(table_bytes).hexdigest() == TABLE_SHA256,
                "command table hash mismatch")
        commands = list(struct.unpack(f"<{TABLE_COUNT}Q", table_bytes))
        require(commands[0] == 0x0000F300000001D0, "unexpected first command")
        require([index for index, value in enumerate(commands) if value == F3_128] == [218],
                "F3:0x128 is not unique at index 218")
        require(commands[217:224] == [
            0x0000F3000000012C,
            0x0000F30000000128,
            0x0000F30000000144,
            0x0000F30000000148,
            0x0000F30000000100,
            0x0000F30000000120,
            0x0000F30000000124,
        ], "unexpected table neighborhood")

        decoder = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
        decoded_text = list(decoder.disasm(text_bytes, 0))
        by_address = {instruction.address: instruction for instruction in decoded_text}

        def has(address: int, mnemonic: str, operands: str) -> bool:
            instruction = by_address.get(address)
            return bool(instruction and instruction.mnemonic == mnemonic and
                        instruction.op_str == operands)

        # Descriptor clearing and table construction.
        init_landmarks = {
            (0x10B8, "str", "xzr, [x19, #0x160]"),
            (0x1284, "add", "x0, x19, #0x300"),
            (0x1288, "mov", "x2, #0x18"),
            (0xFB28, "mov", "w1, #0xe2"),
            (0xFB30, "str", "w1, [x19, #0x300]"),
            (0x1021C, "ldr", "w0, [x19, #0x300]"),
            (0x10220, "lsl", "x0, x0, #2"),
            (0x10228, "str", "x0, [x19, #0x160]"),
            (0x1026C, "ldr", "w0, [x19, #0x300]"),
            (0x10270, "lsl", "x0, x0, #3"),
            (0x1027C, "str", "x0, [x19, #0x310]"),
            (0x10280, "lsl", "x0, x1, #2"),
            (0x10288, "str", "x0, [x19, #0x308]"),
            (0x102B0, "mov", "x0, #0x1d0"),
            (0x102B8, "movk", "x0, #0xf300, lsl #32"),
            (0x102C0, "add", "x26, x20, #0x3c8"),
            (0x102C8, "ldr", "x0, [x26, x22, lsl #3]"),
            (0x102D0, "str", "x0, [x1, x22, lsl #3]"),
            (0x102DC, "ldr", "x1, [x19, #0x308]"),
            (0x102E0, "str", "wzr, [x1, x22, lsl #2]"),
            (0x102F4, "b.hi", "#0x102c8"),
        }
        require(all(has(*landmark) for landmark in init_landmarks),
                "descriptor/table construction landmark mismatch")

        # Generic one-command pre-send cache and lower send.
        send_landmarks = {
            (0xD178, "ldr", "x3, [x20, #0x160]"),
            (0xD180, "ldr", "x1, [x20, #0x310]"),
            (0xD188, "ldr", "w2, [x20, #0x300]"),
            (0xD1AC, "ldr", "x0, [x1, x26, lsl #3]"),
            (0xD1B4, "cmp", "x0, x19"),
            (0xD1BC, "ldr", "w0, [x21]"),
            (0xD1C0, "mov", "w2, #1"),
            (0xD1C4, "str", "w0, [x3, x26, lsl #2]"),
            (0xD1D0, "ldr", "x1, [x20, #0x308]"),
            (0xD1D4, "str", "w2, [x1, x26, lsl #2]"),
            (0xD1E4, "mov", "x0, x19"),
            (0xD1E8, "ldr", "w1, [x21]"),
            (0xD1EC, "mov", "w2, #1"),
            (0xD1F0, "bl", "#0xbba0"),
            (0xD200, "ret", ""),
        }
        require(all(has(*landmark) for landmark in send_landmarks),
                "generic send/cache landmark mismatch")

        named_recovery = [
            (0xF6F8, 0xB4, 0xF708, 0xDBA8),
            (0xF70C, 0xB0, 0xF710, 0xF1C0),
            (0xF714, 0xC0, 0xF718, 0xEF98),
            (0xF71C, 0xC4, 0xF720, 0xEEF8),
            (0xF724, 0xC8, 0xF728, 0xEE58),
            (0xF72C, 0xCC, 0xF730, 0xECE0),
            (0xF734, 0xD0, 0xF738, 0xEB60),
            (0xF73C, 0xD8, 0xF740, 0xE9E8),
            (0xF744, 0xDC, 0xF748, 0xE870),
            (0xF74C, 0x174, 0xF750, 0xE740),
            (0xF754, 0xE4, 0xF758, 0xE6A0),
            (0xF75C, 0xE8, 0xF760, 0xE600),
            (0xF764, 0xEC, 0xF768, 0xE560),
            (0xF76C, 0xF4, 0xF770, 0xE4C0),
            (0xF774, 0xFC, 0xF778, 0xE420),
            (0xF77C, 0x124, 0xF780, 0xE2F8),
            (0xF784, 0x320, 0xF788, 0xDA80),
            (0xF78C, 0x148, 0xF790, 0xE1B8),
            (0xF794, 0x14C, 0xF798, 0xE098),
            (0xF79C, 0x150, 0xF7A0, 0xDF78),
            (0xF7A4, 0x170, 0xF7A8, 0xD8F8),
            (0xF7AC, 0x130, 0xF7B0, 0xD7C8),
            (0xF7B4, 0x130, 0xF7B8, 0xD728),
            (0xF7BC, 0x17C, 0xF7C0, 0xDE50),
            (0xF7C4, 0x180, 0xF7C8, 0xDD28),
            (0xF7CC, 0x184, 0xF7D0, 0xD600),
            (0xF7D4, 0x188, 0xF7D8, 0xD428),
            (0xF7DC, 0x18C, 0xF7E0, 0xD250),
        ]
        for load_at, field, call_at, target in named_recovery:
            require(has(load_at, "ldr", f"w0, [x19, #{field:#x}]") and
                    has(call_at, "bl", f"#{target:#x}"),
                    f"named recovery pair mismatch at {load_at:#x}")

        replay_landmarks = {
            (0xF808, "ldr", "x0, [x19, #0x160]"),
            (0xF810, "ldr", "x1, [x19, #0x310]"),
            (0xF818, "ldr", "x0, [x19, #0x308]"),
            (0xF820, "ldr", "w1, [x19, #0x300]"),
            (0xF85C, "ldr", "w2, [x0, x3, lsl #2]"),
            (0xF860, "cmp", "w2, #1"),
            (0xF868, "ldr", "x1, [x19, #0x160]"),
            (0xF878, "ldr", "w1, [x1, x3, lsl #2]"),
            (0xF87C, "ldr", "x0, [x0, x3, lsl #3]"),
            (0xF880, "bl", "#0xbba0"),
            (0xF8F8, "mov", "w0, #0"),
            (0xF90C, "ret", ""),
        }
        require(all(has(*landmark) for landmark in replay_landmarks),
                "generic replay landmark mismatch")

        # Separate frame recovery, Resume, and power-on recovery ordering.
        control_landmarks = {
            (0x107EC, "mov", "x0, #0x160"),
            (0x107F0, "movk", "x0, #0xf300, lsl #32"),
            (0x10854, "ldr", "w0, [x20, #0x13c]"),
            (0x10890, "bl", "#0x10508"),
            (0x10F2C, "cmp", "w19, #0xa"),
            (0x10FE8, "ldr", "w0, [x19, #8]"),
            (0x11038, "bl", "#0xb250"),
            (0x1103C, "bl", "#0x107e8"),
            (0x11040, "bl", "#0xf6d8"),
            (0x11044, "str", "wzr, [x19, #8]"),
            (0x11858, "cbz", "w0, #0x11a28"),
            (0x118F4, "cbnz", "w1, #0x11994"),
            (0x11928, "mov", "w0, #2"),
            (0x1192C, "bl", "#0xb250"),
            (0x11930, "bl", "#0x107e8"),
            (0x11934, "bl", "#0xf6d8"),
            (0x11940, "mov", "w0, w19"),
        }
        require(all(has(*landmark) for landmark in control_landmarks),
                "recovery caller/control landmark mismatch")

        # Screen-saver brightness is a separate named cached policy restore.
        brightness_landmarks = {
            (0xEB64, "cmp", "w0, #7"),
            (0xEBA8, "mov", "x0, #0xc4"),
            (0xEBB0, "movk", "x0, #0xf300, lsl #32"),
            (0xEBB8, "bl", "#0xbba0"),
        }
        require(all(has(*landmark) for landmark in brightness_landmarks),
                "screen-saver brightness restore mismatch")

        # The engineering-test routine's direct 0x128 sends bypass the generic
        # QDFTcon_SendOneCommand cache entry and call the lower sender directly.
        ew_landmarks = {
            (0x11694, "mov", "x21, #0x128"),
            (0x116B0, "movk", "x21, #0xf300, lsl #32"),
            (0x116C8, "mov", "x0, x21"),
            (0x116CC, "bl", "#0xbba0"),
            (0x116F0, "mov", "x0, #0x128"),
            (0x116F4, "movk", "x0, #0xf300, lsl #32"),
            (0x116F8, "bl", "#0xbba0"),
        }
        require(all(has(*landmark) for landmark in ew_landmarks),
                "engineering-test F3:0x128 route mismatch")

        # Full direct call inventory for this local recovery helper.
        intervals = []
        for name, symbol in symbols.items():
            if symbol["st_info"]["type"] != "STT_FUNC" or int(symbol["st_shndx"]) != 3:
                continue
            start, size = int(symbol["st_value"]), int(symbol["st_size"])
            if size:
                intervals.append((start, start + size, name))
        intervals.sort()

        def owner(address: int) -> str:
            matches = [name for start, end, name in intervals if start <= address < end]
            require(len(matches) == 1, f"ambiguous function owner at {address:#x}: {matches}")
            return matches[0]

        replay_calls = [instruction.address for instruction in decoded_text
                        if instruction.mnemonic == "bl" and instruction.op_str == "#0xf6d8"]
        expected_calls = [0x10CD8, 0x10DE0, 0x11040, 0x11934, 0x121D8, 0x13BEC]
        require(replay_calls == expected_calls, f"replay call-site set changed: {replay_calls!r}")
        for address in replay_calls:
            require(has(address - 4, "bl", "#0x107e8"),
                    f"frame recovery is not adjacent before replay at {address:#x}")
        call_owners = [(address, owner(address)) for address in replay_calls]
        require(call_owners == [
            (0x10CD8, "QDFTcon_MonitorTemperatureSensor"),
            (0x10DE0, "QDFTcon_MonitorTemperatureSensor"),
            (0x11040, "QDFTcon_Resume"),
            (0x11934, "m_set_power_control"),
            (0x121D8, "QDFTcon_SetElSensing"),
            (0x13BEC, "QDFTcon_SetOffSensing"),
        ], "replay call ownership changed")

        # Resolve only the relocations needed to bind initialization and the
        # public ops-table entry; internal BL operands above are direct.
        def relocations(section_name: str) -> dict[int, tuple[str, int, int]]:
            section = elf.get_section_by_name(section_name)
            require(section is not None, f"missing {section_name}")
            linked = elf.get_section(section["sh_link"])
            return {
                int(relocation["r_offset"]): (
                    linked.get_symbol(relocation["r_info_sym"]).name,
                    int(relocation["r_addend"]),
                    int(relocation["r_info_type"]),
                )
                for relocation in section.iter_relocations()
            }

        text_reloc = relocations(".rela.text")
        init_reloc = relocations(".rela.init.text")
        require(text_reloc[0xF9B8][:2] == ("", 0x1228), "table rodata page relocation mismatch")
        require(text_reloc[0xF9C0][:2] == ("", 0x1228), "table rodata low relocation mismatch")
        require(text_reloc[0x10224][0] == "ft_vmalloc" and
                text_reloc[0x10274][0] == "ft_vmalloc" and
                text_reloc[0x10284][0] == "ft_vmalloc", "allocator relocation mismatch")
        require(init_reloc[0x2AC][0] == "QDFTcon_SendOneCommand" and
                init_reloc[0x2B4][0] == "QDFTcon_SendOneCommand",
                "ops-table SendOneCommand relocation mismatch")

        lines = [
            "qdf_tcon.ko SHA256 " + actual_hash,
            "ELF64 little-endian AArch64 relocatable; addresses are .text offsets",
            "",
            "BSS replay descriptor symbols:",
            "  m_npc_lut_register_data  .bss+0x160 size 8",
            "  m_npc_lut_register_info  .bss+0x300 size 24",
            "  fields used here: values*=+0x160 count=+0x300 valid*=+0x308 commands*=+0x310",
            "",
            f"command table .rodata+0x{TABLE_OFFSET:x}, {TABLE_COUNT} u64 entries, SHA256 {TABLE_SHA256}",
        ]
        for index in range(213, 226):
            marker = "  <F3:0x128>" if index == 218 else ""
            lines.append(f"  [{index:3d}] 0x{commands[index]:016x}{marker}")
        lines.extend(["", "direct m_register_recovery_noFramerate call sites:"])
        for address, name in call_owners:
            lines.append(f"  0x{address:05x} {name}; preceding 0x{address-4:05x} m_tcon_recovery_frame_mode")

        def dump_range(title: str, section_name: str, data: bytes, start: int, size: int,
                       reloc: dict[int, tuple[str, int, int]]) -> None:
            lines.extend(["", f"[{title}] 0x{start:x}..0x{start+size:x}"])
            for instruction in decoder.disasm(data[start:start + size], start):
                suffix = ""
                if instruction.address in reloc:
                    symbol, addend, kind = reloc[instruction.address]
                    label = symbol or f"section-addend:{addend:#x}"
                    suffix = f" ; RELOC type={kind} {label} addend={addend:#x}"
                lines.append(f"{instruction.address:06x}: {instruction.mnemonic:<8} {instruction.op_str}{suffix}".rstrip())

        dump_range("QDFTcon_InitVariable replay-descriptor clear", ".text", text_bytes,
                   0x10A4, 0x20, text_reloc)
        dump_range("QDFTcon_InitVariable info-struct zero", ".text", text_bytes,
                   0x1274, 0x24, text_reloc)
        dump_range("QDFTcon_Tcon_InitDevice table count", ".text", text_bytes,
                   0xFB20, 0x20, text_reloc)
        dump_range("QDFTcon_Tcon_InitDevice values allocation", ".text", text_bytes,
                   0x101E8, 0x48, text_reloc)
        dump_range("QDFTcon_Tcon_InitDevice command/valid allocation and population", ".text",
                   text_bytes, 0x1026C, 0x98, text_reloc)
        for name in [
            "QDFTcon_SendOneCommand",
            "m_register_recovery_noFramerate",
            "m_tcon_recovery_frame_mode",
            "QDFTcon_Resume",
            "m_set_power_control",
            "m_set_ss_brightness",
        ]:
            symbol = symbols[name]
            dump_range(name, ".text", text_bytes, int(symbol["st_value"]),
                       int(symbol["st_size"]), text_reloc)
        dump_range("QDFTcon_EW_QdNpcTest direct F3:0x128 excerpt", ".text", text_bytes,
                   0x11694, 0x68, text_reloc)
        dump_range("init_module ops-table SendOneCommand binding", ".init.text", init_bytes,
                   0x2AC, 0x14, init_reloc)

    generated = "\n".join(lines) + "\n"
    if args.write_output:
        OUTPUT.write_text(generated)
    else:
        require(OUTPUT.is_file(), "generated disassembly is missing; use --write-output")
        require(OUTPUT.read_text() == generated, "generated disassembly differs")

    print("PASS: pinned F3:0x128 table index, pre-send cache, six recovery callers, and named brightness replay")
    print("LIMIT: static request replay is not live execution, lower success, controller acceptance, or physical output")


if __name__ == "__main__":
    main()
