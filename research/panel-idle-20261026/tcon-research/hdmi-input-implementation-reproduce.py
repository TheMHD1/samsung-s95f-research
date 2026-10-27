#!/usr/bin/env python3
"""Hash-gated offline landmarks for the Samsung HDMI input implementation."""

from pathlib import Path
import argparse
import hashlib
import re
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LIB = (ROOT / "overnight/serdes-hdmi-input-impl-copy-20261026/"
       "libhdmi-input-control-impl-sec.so.0.1")
LIB_SHA256 = "5f822a6f297e1d24a65ad8dd4363a1dcf43b7d15f405fa7799ddf20f01410126"
OUT = HERE / "hdmi-input-implementation.disasm"


def require(condition, message):
    if not condition:
        raise ValueError(message)


SYMBOLS = {
    "hdmi_input_control_inject": (0x11BD, 96),
    "ppi_hdmi_input_control_set_background_impl": (0x211D, 264),
    "ppi_hdmi_input_control_set_foreground_impl": (0x2225, 264),
    "ppi_hdmi_input_control_get_power_status_impl": (0x243D, 228),
    "ppi_hdmi_input_control_stop_impl": (0x260D, 216),
    "ppi_hdmi_input_control_start_impl": (0x26E5, 216),
    "hdmisw_convert_switchport": (0x357D, 110),
    "ppi_hdmi_input_control_set_source_impl": (0x35ED, 276),
    "hdmi_input_control_impl_set_funcs": (0x3955, 348),
    "hdmi_input_control_backend_data_inject": (0x3AB1, 224),
}

# Exact callback table produced by hdmi_input_control_impl_set_funcs.  This is
# an ELF table mapping, not proof that a live process installed or called it.
SLOTS = {
    0x00: "ppi_hdmi_input_control_create_handle_impl",
    0x04: "ppi_hdmi_input_control_destroy_handle_impl",
    0x08: "ppi_hdmi_input_control_start_impl",
    0x0C: "ppi_hdmi_input_control_stop_impl",
    0x10: "ppi_hdmi_input_control_get_infopacket_impl",
    0x14: "ppi_hdmi_input_control_get_resolution_impl",
    0x18: "ppi_hdmi_input_control_get_signal_information_impl",
    0x1C: "ppi_hdmi_input_control_get_signal_status_impl",
    0x20: "ppi_hdmi_input_control_get_signal_format_impl",
    0x24: "ppi_hdmi_input_control_get_lock_impl",
    0x28: "ppi_hdmi_input_control_get_vrr_mode_impl",
    0x2C: "ppi_hdmi_input_control_get_hdcp_version_impl",
    0x30: "ppi_hdmi_input_control_get_err_count_impl",
    0x34: "ppi_hdmi_input_control_get_power_status_impl",
    0x38: "ppi_hdmi_input_control_is_mhl_connection_impl",
    0x3C: "ppi_hdmi_input_control_set_source_impl",
    0x40: "ppi_hdmi_input_control_set_resolution_impl",
    0x44: "ppi_hdmi_input_control_set_foreground_impl",
    0x48: "ppi_hdmi_input_control_set_background_impl",
    0x4C: "ppi_hdmi_input_control_set_pc_mode_impl",
    0x50: "ppi_hdmi_input_control_set_hot_plug_impl",
    0x54: "ppi_hdmi_input_control_set_err_count_impl",
    0x58: "ppi_hdmi_input_control_set_latency_level_impl",
    0x5C: "ppi_hdmi_input_control_set_dvi_signal_impl",
    0x60: "ppi_hdmi_input_control_set_signal_format_impl",
    0x64: "ppi_hdmi_input_control_connect_decoder_impl",
    0x68: "ppi_hdmi_input_control_update_dma_buffer_impl",
    0x6C: "ppi_hdmi_input_control_get_dma_buffer_handle_impl",
    0x70: "ppi_hdmi_input_control_request_dma_buffer_impl",
    0x74: "ppi_hdmi_input_control_set_multi_hdmi_config_impl",
    0x78: "ppi_hdmi_input_control_set_multi_hdmi_ir_position_impl",
    0x7C: "ppi_hdmi_input_control_set_fake_resolution_impl",
    0x80: "ppi_hdmi_input_control_get_hdcp_status_impl",
}

EXPECTED_CIDS = {
    ("ppi_hdmi_input_control_get_hdcp_status_impl", 0x1312, 0x00A00973),
    ("ppi_hdmi_input_control_set_fake_resolution_impl", 0x140E, 0x00A009A4),
    ("ppi_hdmi_input_control_set_multi_hdmi_ir_position_impl", 0x1580, 0x00A009A3),
    ("ppi_hdmi_input_control_set_multi_hdmi_config_impl", 0x16C0, 0x00A009A3),
    ("ppi_hdmi_input_control_set_hot_plug_impl", 0x1E50, 0x00A00999),
    ("ppi_hdmi_input_control_set_pc_mode_impl", 0x204C, 0x00A0096C),
    ("ppi_hdmi_input_control_set_background_impl", 0x214C, 0x00A009BC),
    ("ppi_hdmi_input_control_set_foreground_impl", 0x2254, 0x00A009BD),
    ("ppi_hdmi_input_control_is_mhl_connection_impl", 0x2364, 0x00A0099A),
    ("ppi_hdmi_input_control_get_infopacket_impl", 0x27FA, 0x00A009AB),
    ("ppi_hdmi_input_control_set_err_count_impl", 0x2A9E, 0x00A009B5),
    ("ppi_hdmi_input_control_set_resolution_impl", 0x2BD4, 0x00A0096A),
    ("ppi_hdmi_input_control_get_err_count_impl", 0x2D52, 0x00A009B2),
    ("ppi_hdmi_input_control_get_signal_status_impl", 0x2FF8, 0x00A00967),
    ("ppi_hdmi_input_control_get_signal_information_impl", 0x314C, 0x00A00968),
    ("ppi_hdmi_input_control_get_resolution_impl", 0x32C0, 0x00A00966),
    ("ppi_hdmi_input_control_get_hdcp_version_impl", 0x375A, 0x00A009C1),
    ("ppi_hdmi_input_control_get_vrr_mode_impl", 0x3888, 0x00A009C0),
    ("ppi_hdmi_input_control_set_latency_level_impl", 0x1D54, 0x00A009C3),
}


def code_spans(elf, start, size):
    """Return mapping-symbol-delimited executable spans inside one symbol."""
    symtab = elf.get_section_by_name(".symtab")
    marks = sorted((int(s["st_value"]), s.name) for s in symtab.iter_symbols()
                   if s.name in {"$t", "$a", "$d"})
    end = start + size
    prior = [(address, kind) for address, kind in marks if address <= start]
    require(prior and prior[-1][1] == "$t", f"missing Thumb mapping at {start:x}")
    inside = [(start, "$t")] + [(address, kind) for address, kind in marks
                                if start < address < end]
    result = []
    for index, (address, kind) in enumerate(inside):
        limit = inside[index + 1][0] if index + 1 < len(inside) else end
        if kind in {"$t", "$a"}:
            result.append((address, limit, kind))
    return result


def decode_functions(elf, wanted=None):
    text = elf.get_section_by_name(".text")
    raw, base = text.data(), int(text["sh_addr"])
    text_index = elf.get_section_index(".text")
    dyn = {s.name: s for s in elf.get_section_by_name(".dynsym").iter_symbols()
           if s.name}
    thumb = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    decoded = {}
    names = sorted(wanted if wanted is not None else
                   [name for name, sym in dyn.items()
                    if sym["st_shndx"] == text_index])
    for name in names:
        sym = dyn[name]
        start, size = int(sym["st_value"]) & ~1, int(sym["st_size"])
        spans = []
        for lo, hi, kind in code_spans(elf, start, size):
            require(kind == "$t", f"unexpected ARM code in {name}")
            ins = list(thumb.disasm(raw[lo - base:hi - base], lo))
            require(sum(item.size for item in ins) == hi - lo,
                    f"short Thumb decode in {name} {lo:x}-{hi:x}")
            spans.append((lo, hi, ins))
        decoded[name] = spans
    return decoded


def row_map(spans):
    return {item.address: (item.mnemonic, item.op_str)
            for _, _, instructions in spans for item in instructions}


def relocation_maps(elf):
    result = {}
    for section_name in (".rel.dyn", ".rel.plt"):
        section = elf.get_section_by_name(section_name)
        symtab = elf.get_section(section["sh_link"])
        result[section_name] = {
            int(reloc["r_offset"]): symtab.get_symbol(reloc["r_info_sym"]).name
            for reloc in section.iter_relocations() if reloc["r_info_sym"]}
    return result


def derive_plt(elf):
    """Decode every ARM PLT veneer and bind its computed GOT slot to relocation."""
    section = elf.get_section_by_name(".plt")
    require((int(section["sh_addr"]), int(section["sh_size"])) == (0x10F4, 0xC8),
            "PLT bounds")
    relocations = relocation_maps(elf)[".rel.plt"]
    got_slots = sorted(relocations)
    require(got_slots == list(range(0x1500C, 0x15048, 4)),
            "PLT GOT relocation slots")
    arm = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    raw, base = section.data(), int(section["sh_addr"])
    result = {}
    load = re.compile(r"pc, \[ip, #(0x[0-9a-f]+|[0-9]+)\]!$")
    for index, got in enumerate(got_slots):
        start = 0x1108 + index * 12
        instructions = list(arm.disasm(raw[start - base:start - base + 12], start))
        require(len(instructions) == 3 and
                sum(item.size for item in instructions) == 12 and
                (instructions[0].mnemonic, instructions[0].op_str) ==
                ("add", "ip, pc, #0, #12") and
                (instructions[1].mnemonic, instructions[1].op_str) ==
                ("add", "ip, ip, #0x13000") and
                instructions[2].mnemonic == "ldr",
                f"PLT veneer decode {start:x}")
        match = load.fullmatch(instructions[2].op_str)
        require(match is not None and
                start + 8 + 0x13000 + int(match.group(1), 0) == got,
                f"PLT veneer GOT target {start:x}")
        name = relocations[got]
        require(name not in result, "duplicate PLT symbol")
        result[name] = start
    require(0x1108 + len(got_slots) * 12 == 0x11BC,
            "PLT veneers do not end at text")
    return result


def derive_slots(elf, initializer):
    """Symbolically follow initializer PC literals, GOT loads, and table stores."""
    text = elf.get_section_by_name(".text")
    raw, base = text.data(), int(text["sh_addr"])
    relocs = relocation_maps(elf)[".rel.dyn"]
    registers = {}
    slots = {}
    literal = re.compile(r"(r[0-9]+), \[pc, #(0x[0-9a-f]+|[0-9]+)\]")
    indexed = re.compile(r"(r[0-9]+), \[r3, (r[0-9]+)\]")
    store = re.compile(r"(r[0-9]+), \[r0(?:, #(0x[0-9a-f]+|[0-9]+))?\]")
    for item in initializer:
        match = literal.fullmatch(item.op_str)
        if item.mnemonic.startswith("ldr") and match:
            address = ((item.address + 4) & ~3) + int(match.group(2), 0)
            require(base <= address <= base + len(raw) - 4, "literal outside text")
            registers[match.group(1)] = struct.unpack_from("<I", raw, address - base)[0]
            continue
        if item.mnemonic == "add" and item.op_str == "r3, pc":
            registers["r3"] += (item.address + 4) & ~3
            require(registers["r3"] == 0x15000, "unexpected GOT base")
            continue
        match = indexed.fullmatch(item.op_str)
        if item.mnemonic.startswith("ldr") and match:
            require(registers.get("r3") == 0x15000, "initializer lost GOT base")
            got = 0x15000 + registers[match.group(2)]
            require(got in relocs, f"unrelocated GOT slot {got:x}")
            registers[match.group(1)] = relocs[got]
            continue
        match = store.fullmatch(item.op_str)
        if item.mnemonic.startswith("str") and match:
            offset = int(match.group(2), 0) if match.group(2) else 0
            value = registers.get(match.group(1))
            require(isinstance(value, str), f"non-symbolic table value at {item.address:x}")
            require(offset not in slots, f"duplicate table slot {offset:x}")
            slots[offset] = value
    return slots


def private_cids(decoded):
    result = set()
    operand = re.compile(r"(r[0-9]+|ip|lr), #(0x[0-9a-f]+|[0-9]+)")
    for name, spans in decoded.items():
        for _, _, instructions in spans:
            lows = {}
            for index, item in enumerate(instructions):
                match = operand.fullmatch(item.op_str)
                if item.mnemonic in {"movw", "mov.w"} and match:
                    lows[match.group(1)] = (index, int(match.group(2), 0), item.address)
                elif item.mnemonic == "movt" and match and match.group(1) in lows:
                    prior, low, address = lows[match.group(1)]
                    value = (int(match.group(2), 0) << 16) | low
                    if index - prior <= 16 and 0x00A00000 <= value <= 0x00A0FFFF:
                        result.add((name, address, value))
    return result


def require_landmarks(decoded, plt):
    rows = {name: row_map(spans) for name, spans in decoded.items()}
    expected = {
        "ppi_hdmi_input_control_set_background_impl": {
            0x2132: ("ldr", "r0, [r0, #0xc]"),
            0x213E: ("movw", "r1, #0x5648"),
            0x2142: ("movt", "r1, #0xc018"),
            0x214C: ("movw", "r3, #0x9bc"),
            0x2150: ("movt", "r3, #0xa0"),
            0x2158: ("str", "r3, [sp, #0x10]"),
            0x2160: ("str", "r3, [sp, #0x38]"),
            0x2166: ("strd", "r4, r3, [sp, #0x24]"),
            0x2172: ("blx", "#0x1150"),
            0x217A: ("movge", "r0, #0"),
        },
        "ppi_hdmi_input_control_set_foreground_impl": {
            0x223A: ("ldr", "r0, [r0, #0xc]"),
            0x2246: ("movw", "r1, #0x5648"),
            0x224A: ("movt", "r1, #0xc018"),
            0x2254: ("movw", "r3, #0x9bd"),
            0x2258: ("movt", "r3, #0xa0"),
            0x2260: ("str", "r3, [sp, #0x10]"),
            0x2268: ("str", "r3, [sp, #0x38]"),
            0x226E: ("strd", "r4, r3, [sp, #0x24]"),
            0x227A: ("blx", "#0x1150"),
            0x2282: ("movge", "r0, #0"),
        },
        "ppi_hdmi_input_control_set_source_impl": {
            0x3602: ("ldr", "r3, [r0, #8]"),
            0x3608: ("str", "r1, [r0]"),
            0x360C: ("ldr", "r0, [r0, #4]"),
            0x3610: ("blx", "#0x11a4"),
            0x3656: ("movw", "r1, #0x5627"),
            0x365A: ("movt", "r1, #0xc004"),
            0x365E: ("blx", "#0x1150"),
            0x3666: ("movge", "r0, #0"),
        },
        "ppi_hdmi_input_control_get_power_status_impl": {
            0x2448: ("ldr", "r6, [r0, #8]"),
            0x2458: ("mov", "r4, r1"),
            0x2468: ("movw", "r1, #0x561a"),
            0x246C: ("movt", "r1, #0xc050"),
            0x2470: ("str", "r4, [sp, #0x10]"),
            0x2472: ("blx", "#0x1150"),
            0x247A: ("ldr", "r3, [sp, #0x48]"),
            0x247E: ("str", "r3, [r5]"),
        },
        "ppi_hdmi_input_control_start_impl": {
            0x26FC: ("ldr", "r0, [r0, #0xc]"),
            0x26FE: ("str", "r2, [sp, #0x10]"),
            0x2706: ("movw", "r1, #0x5612"),
            0x270A: ("movt", "r1, #0x4004"),
            0x270E: ("blx", "#0x1150"),
        },
        "ppi_hdmi_input_control_stop_impl": {
            0x2624: ("ldr", "r0, [r0, #0xc]"),
            0x2626: ("str", "r2, [sp, #0x10]"),
            0x262E: ("movw", "r1, #0x5613"),
            0x2632: ("movt", "r1, #0x4004"),
            0x2636: ("blx", "#0x1150"),
        },
        "hdmi_input_control_inject": {
            0x11E8: ("blx", "#0x1138"),
        },
        "hdmi_input_control_backend_data_inject": {
            0x3AF0: ("add", "r0, sp, #0x10"),
            0x3AF2: ("blx", "#0x1114"),
            0x3AFC: ("ldr", "r0, [r3, #4]"),
            0x3AFE: ("blx", "#0x1198"),
            0x3B24: ("str", "r5, [r1]"),
        },
    }
    for name, landmarks in expected.items():
        for address, instruction in landmarks.items():
            require(rows[name].get(address) == instruction,
                    f"landmark {name} {address:x}")
    require(plt["ioctl"] == 0x1150 and
            plt["hdmi_input_control_backend_data_inject"] == 0x1138 and
            plt["ppi_hdmi_input_control_get_backend_data_address"] == 0x1114 and
            plt["hdmi_input_control_impl_set_funcs"] == 0x1198 and
            plt["hdmisw_convert_switchport"] == 0x11A4,
            "PLT identity landmarks")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-disassembly", action="store_true")
    args = parser.parse_args()
    raw = LIB.read_bytes()
    require(len(raw) == 29650, "library size")
    require(hashlib.sha256(raw).hexdigest() == LIB_SHA256, "library hash")
    require(b"mute" not in raw.lower(), "unexpected mute-named string")

    with LIB.open("rb") as handle:
        elf = ELFFile(handle)
        require(elf["e_type"] == "ET_DYN" and elf["e_machine"] == "EM_ARM" and
                elf.elfclass == 32 and elf.little_endian, "ELF identity")
        require((int(elf.get_section_by_name(".text")["sh_addr"]),
                 int(elf.get_section_by_name(".text")["sh_size"])) ==
                (0x11BC, 0x29D4), "text bounds")
        dyn = {s.name: s for s in elf.get_section_by_name(".dynsym").iter_symbols()
               if s.name}
        for name, identity in SYMBOLS.items():
            require(name in dyn and
                    (int(dyn[name]["st_value"]), int(dyn[name]["st_size"])) == identity,
                    f"symbol identity {name}")
        require(not any("mute" in name.lower() for name in dyn), "mute-named export")

        decoded = decode_functions(elf)
        relocs = relocation_maps(elf)
        plt = derive_plt(elf)
        require_landmarks(decoded, plt)
        initializer = decoded["hdmi_input_control_impl_set_funcs"][0][2]
        require(derive_slots(elf, initializer) == SLOTS, "callback table mapping")
        require(private_cids(decoded) == EXPECTED_CIDS, "private CID census")
        init = elf.get_section_by_name(".init_array").data()
        require(struct.unpack_from("<II", init) == (0x12E1, 0), "init-array pre-relocation")
        require(relocs[".rel.dyn"].get(0x14EE8) == "hdmi_input_control_inject",
                "inject init-array relocation")

        selected = ("hdmi_input_control_inject",
                    "hdmi_input_control_backend_data_inject",
                    "hdmi_input_control_impl_set_funcs",
                    "ppi_hdmi_input_control_set_source_impl",
                    "ppi_hdmi_input_control_set_background_impl",
                    "ppi_hdmi_input_control_set_foreground_impl",
                    "ppi_hdmi_input_control_get_power_status_impl",
                    "ppi_hdmi_input_control_start_impl",
                    "ppi_hdmi_input_control_stop_impl",
                    "hdmisw_convert_switchport")
        listing = [f"ELF sha256 {LIB_SHA256}\n",
                   "ELF32 little-endian ARM EABI5; Thumb symbols use odd st_value.\n",
                   "\n## callback table\n"]
        listing.extend(f"+0x{offset:02x} {name}\n" for offset, name in SLOTS.items())
        listing.append("\n## straightforward private-CID constructions\n")
        listing.extend(f"0x{value:08x} {name} @0x{address:08x}\n"
                       for name, address, value in sorted(EXPECTED_CIDS,
                                                          key=lambda row: (row[2], row[0])))
        for name in selected:
            for lo, hi, instructions in decoded[name]:
                listing.append(f"\n## {name} Thumb 0x{lo:08x}..0x{hi:08x}\n")
                listing.extend(f"{item.address:08x} {item.mnemonic:8} {item.op_str}\n"
                               for item in instructions)
        output = "".join(listing)

    if args.write_disassembly:
        with OUT.open("x") as target:
            target.write(output)
    else:
        require(OUT.read_text() == output, "saved disassembly equality")
    print("PASS: exact HDMI input implementation table and bounded callback paths.")
    print("Static acquired-ELF evidence only; no live binding, callback, ioctl, power, mute, or physical effect proved.")


if __name__ == "__main__":
    main()
