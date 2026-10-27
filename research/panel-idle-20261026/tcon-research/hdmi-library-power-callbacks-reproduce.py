#!/usr/bin/env python3
"""Verify bounded, offline HDMI-control power callback landmarks.

This proves only static code/data-flow landmarks in the hash-pinned library.
It neither invokes the library nor establishes event delivery or a display effect.
"""
from pathlib import Path
import argparse
import hashlib
import struct

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / "overnight/serdes-hdmi-control-copy-20261026/libhdmi-control.so.0.1"
SHA256 = "067ddb8f639f8e91d02524f0820fb3a56e2d9f174d0f3f75a5dec963f7339410"
LISTING = HERE / "hdmi-library-power-callbacks-v2.disasm"


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def signed_word(section, address):
    return struct.unpack_from("<i", section.data(), address - section["sh_addr"])[0]


def ror32(value, count):
    return ((value >> count) | (value << ((32 - count) % 32))) & 0xFFFFFFFF


def arm_immediate(word):
    return ror32(word & 0xFF, ((word >> 8) & 0xF) * 2)


def thumb_slice(section, decoder, name, lo, hi):
    raw = section.data()[lo - section["sh_addr"] : hi - section["sh_addr"]]
    decoded = list(decoder.disasm(raw, lo))
    require(sum(item.size for item in decoded) == len(raw), f"undecoded {name}")
    return name, decoded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-disassembly", action="store_true")
    args = parser.parse_args()
    require(hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SHA256, "source SHA-256")

    with SOURCE.open("rb") as stream:
        elf = ELFFile(stream)
        text = elf.get_section_by_name(".text")
        require(text is not None, ".text")
        decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        spans = [
            thumb_slice(text, decoder, "poweroff_callback", 0x47E34594, 0x47E345C8),
            thumb_slice(text, decoder, "wake_callback", 0x47E345DC, 0x47E346DC),
            thumb_slice(text, decoder, "registration_thread", 0x47E34714, 0x47E347B8),
            thumb_slice(text, decoder, "rpc_dpms", 0x47E38A5C, 0x47E38B28),
            thumb_slice(text, decoder, "ppi_dpms", 0x47E624C4, 0x47E62568),
        ]
        decoded = {item.address: (item.mnemonic, item.op_str)
                   for _, items in spans for item in items}
        expected = [
            (0x47E345C2, "str", "r2, [r3]"),
            (0x47E34620, "cmp", "r0, #0"),
            (0x47E3462A, "str", "r2, [r3]"),
            (0x47E34772, "blx", "#0x47e32eec"),
            (0x47E3477C, "blx", "#0x47e33180"),
            (0x47E38AAA, "ldr", "r0, [r3, #4]"),
            (0x47E38AAC, "cbz", "r0, #0x47e38afe"),
            (0x47E38AB0, "cmp", "r3, #1"),
            (0x47E624E6, "ldr", "r3, [r3, #0x38]"),
            (0x47E624EE, "ldrb", "r4, [r3, #0x10]"),
            (0x47E624F0, "cbnz", "r4, #0x47e62530"),
            (0x47E624FE, "blx", "r3"),
            (0x47E62500, "orrs", "r0, r4"),
        ]
        for address, mnemonic, operands in expected:
            require(decoded.get(address) == (mnemonic, operands), f"instruction {address:#x}")

        # For Thumb ADD, architectural PC is instruction-address + 4.
        additions = [
            (0x47E345D8, 0x47E345C0, 0x47E83150, "poweroff-state"),
            (0x47E346F8, 0x47E3461C, 0x47E83150, "wake-state"),
            (0x47E347D4, 0x47E34770, 0x47E34595, "poweroff-callback"),
            (0x47E347D8, 0x47E3477A, 0x47E345DD, "wake-callback"),
            (0x47E38B40, 0x47E38AA8, 0x47E83150, "rpc-state"),
            (0x47E62568, 0x47E624EC, 0x47E834F4, "wrapper-global"),
        ]
        for literal, instruction, target, name in additions:
            require((instruction + 4 + signed_word(text, literal)) & 0xFFFFFFFF == target,
                    f"literal target {name}")

        # Resolve all mixed ARM/Thumb PLT veneers from their actual ARM
        # instruction words and GOT relocations; PLT ordinal/entry-size is not
        # used.  This makes the three names used by the callback analysis
        # independently checked rather than a companion-report assumption.
        dynsym = elf.get_section_by_name(".dynsym")
        relplt = {rel["r_offset"]: dynsym.get_symbol(rel["r_info_sym"]).name
                  for rel in elf.get_section_by_name(".rel.plt").iter_relocations()}
        plt = elf.get_section_by_name(".plt")
        resolved = {}
        for offset in range(20, plt["sh_size"] - 11, 4):
            address = plt["sh_addr"] + offset
            one, two, three = struct.unpack_from("<III", plt.data(), offset)
            if (one & 0xFFFFF000 == 0xE28FC000 and
                    two & 0xFFFFF000 == 0xE28CC000 and
                    three & 0xFFFFF000 == 0xE5BCF000):
                got = (address + 8 + arm_immediate(one) + arm_immediate(two) +
                       (three & 0xFFF)) & 0xFFFFFFFF
                if got in relplt:
                    resolved[address] = (got, relplt[got])
        require(len(relplt) == len(resolved) == 409, "complete PLT resolver")
        require({got for got, _ in resolved.values()} == set(relplt), "PLT/GOT bijection")
        for address, name in [(0x47E32EEC, "device_power_subscribe_poweroff"),
                              (0x47E33180, "device_power_subscribe_early_wakeup"),
                              (0x47E333B8, "__dlog_print")]:
            require(resolved.get(address, (None, None))[1] == name, "PLT name " + name)
        arm = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        plt_rows = []
        for address in (0x47E32EEC, 0x47E33180, 0x47E333B8):
            raw = plt.data()[address - plt["sh_addr"]:address - plt["sh_addr"] + 12]
            ins = list(arm.disasm(raw, address))
            require(sum(item.size for item in ins) == 12, "PLT veneer decode")
            plt_rows.append((resolved[address][1] + "_plt_arm", ins, resolved[address][0]))

    output = "".join(
        "\n## " + name + "\n" + "".join(
            f"{item.address:08x} {item.mnemonic:8} {item.op_str}\n" for item in items
        ) for name, items in spans
    )
    output += "\n## resolved_plt_veneer_summary\n"
    for name, items, got in plt_rows:
        output += f"{name} GOT {got:08x}\n"
        output += "".join(f"{item.address:08x} {item.mnemonic:8} {item.op_str}\n" for item in items)
    if args.write_disassembly:
        with LISTING.open("x") as stream:
            stream.write(output)
    else:
        require(LISTING.read_text() == output, "saved listing differs")
    print("PASS: hash-gated static callback-state, registration, RPC, and wrapper landmarks.")
    print("No callback delivery, RPC connection, physical display transition, or causality is established.")


if __name__ == "__main__":
    main()
