#!/usr/bin/env python3
"""Offline, hash-gated caller inventory for AVE QD-monitor restart bookkeeping."""
from pathlib import Path
import hashlib

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "binaries/libave.so.0.1"
EXPECTED = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"
ONOFF = 0x26B17C
PLT = 0x8D0C8


def symbols(elf):
    answer = {}
    for section in elf.iter_sections():
        if section["sh_type"] in ("SHT_SYMTAB", "SHT_DYNSYM"):
            for symbol in section.iter_symbols():
                if symbol.name:
                    answer[symbol.name] = (symbol["st_value"], symbol["st_size"])
    return answer


def listing(elf, address, size):
    text = elf.get_section_by_name(".text")
    offset = address - text["sh_addr"]
    return [(item.address, item.mnemonic, item.op_str)
            for item in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(text.data()[offset:offset + size], address)]


def mapping_calls(elf, targets):
    """Decode every mapping-symbol code interval; return coverage and calls."""
    text = elf.get_section_by_name(".text")
    start, end, raw = text["sh_addr"], text["sh_addr"] + text["sh_size"], text.data()
    symbols = elf.get_section_by_name(".symtab")
    markers = {}
    for symbol in symbols.iter_symbols():
        if symbol.name in ("$a", "$t", "$d") and start <= symbol["st_value"] < end:
            markers[symbol["st_value"]] = symbol.name
    points = sorted(markers)
    assert points and points[0] == start
    coverage = {"thumb": 0, "arm": 0, "data": 0, "undecodable": []}
    calls = []
    for index, address in enumerate(points):
        following = points[index + 1] if index + 1 < len(points) else end
        kind = markers[address]
        if kind == "$d":
            coverage["data"] += following - address
            continue
        mode, label = (CS_MODE_THUMB, "thumb") if kind == "$t" else (CS_MODE_ARM, "arm")
        decoded = list(Cs(CS_ARCH_ARM, mode).disasm(raw[address - start:following - start], address))
        size = sum(item.size for item in decoded)
        coverage[label] += size
        if size != following - address:
            coverage["undecodable"].append((address, following, kind, size))
        for item in decoded:
            if item.mnemonic in ("bl", "blx") and item.op_str in {f"#{value:#x}" for value in targets.values()}:
                calls.append((item.address, item.mnemonic, int(item.op_str[1:], 16)))
    assert coverage["thumb"] + coverage["arm"] + coverage["data"] == text["sh_size"]
    return coverage, calls


def main():
    data = SOURCE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED
    with SOURCE.open("rb") as handle:
        elf = ELFFile(handle)
        text = elf.get_section_by_name(".text")
        def file_at(address):
            assert text["sh_addr"] <= address < text["sh_addr"] + text["sh_size"]
            return text["sh_offset"] + address - text["sh_addr"]
        named = symbols(elf)
        assert named["_Z22ave_tcon_monitor_onoffi"] == (ONOFF + 1, 60)
        assert named["_Z22ave_tcon_monitor_startv"] == (0x26AAED, 1680)
        assert named["_Z33ave_tcon_monitor_set_system_poweri"] == (0x268A59, 244)
        assert named["g_tcon_monitor_restart"] == (0x5BFCE8, 4)

        rel = elf.get_section_by_name(".rel.plt")
        dyn = elf.get_section(rel["sh_link"])
        plt = elf.get_section_by_name(".plt")
        found = [(index, item, dyn.get_symbol(item["r_info_sym"]).name)
                 for index, item in enumerate(rel.iter_relocations())
                 if dyn.get_symbol(item["r_info_sym"]).name == "_Z22ave_tcon_monitor_onoffi"]
        assert len(found) == 1
        index, item, name = found[0]
        assert (index, item["r_offset"], name) == (945, 0x5A4ED0, "_Z22ave_tcon_monitor_onoffi")
        # Resolver header has 20 bytes; ARM PLT entries are 12 bytes each.
        assert plt["sh_addr"] + 0x14 + index * 12 == PLT

        start_reloc = [(number, entry, dyn.get_symbol(entry["r_info_sym"]).name)
                       for number, entry in enumerate(rel.iter_relocations())
                       if dyn.get_symbol(entry["r_info_sym"]).name == "_Z22ave_tcon_monitor_startv"]
        instant_reloc = [(number, entry, dyn.get_symbol(entry["r_info_sym"]).name)
                         for number, entry in enumerate(rel.iter_relocations())
                         if dyn.get_symbol(entry["r_info_sym"]).name == "_Z27ave_tcon_api_set_instant_on14AVEInstantOn_k"]
        api_start_reloc = [(number, entry, dyn.get_symbol(entry["r_info_sym"]).name)
                           for number, entry in enumerate(rel.iter_relocations())
                           if dyn.get_symbol(entry["r_info_sym"]).name == "_Z26ave_tcon_api_start_monitorv"]
        assert [(n, x["r_offset"]) for n, x, _ in start_reloc] == [(644, 0x5A4A1C)]
        assert [(n, x["r_offset"]) for n, x, _ in instant_reloc] == [(867, 0x5A4D98)]
        assert [(n, x["r_offset"]) for n, x, _ in api_start_reloc] == [(1154, 0x5A5214)]
        targets = {"onoff_plt": PLT, "onoff_body": ONOFF,
                   "start_plt": plt["sh_addr"] + 0x14 + 644 * 12, "start_body": 0x26AAEC,
                   "instant_plt": plt["sh_addr"] + 0x14 + 867 * 12, "instant_body": 0x251228,
                   "api_start_plt": plt["sh_addr"] + 0x14 + 1154 * 12, "api_start_body": 0x24F0EC}
        assert targets == {"onoff_plt": 0x8D0C8, "onoff_body": ONOFF,
                           "start_plt": 0x8C2AC, "start_body": 0x26AAEC,
                           "instant_plt": 0x8CD20, "instant_body": 0x251228,
                           "api_start_plt": 0x8DA94, "api_start_body": 0x24F0EC}

        expected_onoff = {
            (0x26B182, "add", "r2, pc"),
            (0x26B188, "ldr", "r4, [r2, r3]"),
            (0x26B190, "str", "r0, [r4]"),
            (0x26B192, "cmp", "r3, r0"),
            (0x26B194, "beq", "#0x26b1a2"),
            (0x26B19A, "str.w", "r0, [r1, #0xb0]"),
            (0x26B1A0, "str", "r4, [r3]"),
        }
        assert expected_onoff <= set(listing(elf, ONOFF, 60))

        # Start takes the same PIC base then uses GOT offsets 0x2e18 and
        # 0x3370. r6 becomes one before the two stores. The relocations turn
        # those slots into g_tcon_monitor_on and g_tcon_monitor_restart.
        start = listing(elf, 0x26AAEC, 1680)
        expected_start = {
            (0x26AB04, "ldr.w", "r3, [pc, #0x524]"),
            (0x26AB08, "add", "r5, pc"),
            (0x26AB16, "movs", "r6, #1"),
            (0x26AB24, "ldr.w", "r2, [pc, #0x508]"),
            (0x26AB28, "ldr", "r0, [r5, r3]"),
            (0x26AB2E, "str", "r6, [r0]"),
            (0x26AB36, "ldr", "r2, [r5, r2]"),
            (0x26AB3E, "str", "r6, [r2]"),
        }
        assert expected_start <= set(start)
        import struct
        assert struct.unpack_from("<I", data, file_at(0x26B028))[0] == 0x003394F4
        assert struct.unpack_from("<I", data, file_at(0x26B02C))[0] == 0x00002E18
        assert struct.unpack_from("<I", data, file_at(0x26B030))[0] == 0x00003370
        # PC at 0x26ab0c makes the first literal a 0x5a4000 GOT base.
        assert 0x26AB0C + 0x003394F4 == 0x005A4000
        rel_dyn = elf.get_section(elf.get_section_by_name(".rel.dyn")["sh_link"])
        relocations = {entry["r_offset"]: (entry["r_info_type"],
                                              rel_dyn.get_symbol(entry["r_info_sym"]).name)
                       for entry in elf.get_section_by_name(".rel.dyn").iter_relocations()}
        assert relocations[0x005A6E18] == (21, "g_tcon_monitor_on")
        assert relocations[0x005A7370] == (21, "g_tcon_monitor_restart")
        needle = (0x00003370).to_bytes(4, "little")
        offsets, position = [], 0
        while True:
            position = data.find(needle, position)
            if position < 0:
                break
            offsets.append(position)
            position += 1
        # These are the five known literal-pool materializations: ULED/QD/
        # WOLED monitor code, monitor start, and monitor_onoff. It does not
        # exclude another addressing form, alias, external writer or firmware.
        offsets = [text["sh_addr"] + value - text["sh_offset"] for value in offsets
                   if text["sh_offset"] <= value < text["sh_offset"] + text["sh_size"]]
        assert offsets == [0x2694A4, 0x269C44, 0x26A6D8, 0x26B030, 0x26B1B4]

        # These are targeted whole-body checks. They exclude the known PIC
        # materializations and direct branch edge, not another form/indirection.
        for name in ["_Z33ave_tcon_monitor_set_system_poweri"]:
            address, size = named[name]
            assert all(not (mnemonic in ("bl", "blx") and operand == f"#{PLT:#x}")
                       for _, mnemonic, operand in listing(elf, address & ~1, size))
            body = data[file_at(address & ~1):file_at(address & ~1) + size]
            assert (0x00002E18).to_bytes(4, "little") not in body
            assert (0x00003370).to_bytes(4, "little") not in body

        # This scans every $a/$t code range, skips every $d data range, and
        # fails on a partially decoded range. It finds the real lifecycle
        # edges rather than claiming absence from a decoder that stopped early.
        coverage, calls = mapping_calls(elf, targets)
        assert coverage == {"thumb": 2045156, "arm": 28, "data": 298268, "undecodable": []}
        assert calls == [(0x24F102, "blx", 0x8C2AC), (0x24F15A, "blx", 0x8C2AC),
                         (0x251244, "blx", 0x8D0C8), (0x251250, "blx", 0x8D0C8),
                         (0x2708A4, "blx", 0x8DA94), (0x27A0DC, "blx", 0x8CD20)]
        instant = listing(elf, 0x251228, 144)
        # Input is saved in r4.  Both nonzero object-word report paths branch
        # back to 0x251240, where that saved input selects exact 0 or 1.
        assert {(0x25122A, "mov", "r4, r0"),
                (0x251234, "ldr", "r3, [r0, #0x28]"),
                (0x251236, "cbnz", "r3, #0x251274"),
                (0x25123C, "ldr", "r3, [r0, #0x7c]"),
                (0x25123E, "cbnz", "r3, #0x25125a"),
                (0x251240, "cbnz", "r4, #0x25124e"), (0x251242, "mov", "r0, r4"),
                (0x251244, "blx", "#0x8d0c8"), (0x25124E, "movs", "r0, #1"),
                (0x251250, "blx", "#0x8d0c8"),
                (0x251272, "b", "#0x251240"), (0x25129E, "b", "#0x251238")} <= set(instant)
        public_instant = listing(elf, 0x27A024, 448)
        # The public wrapper's lookup result is null-checked before the
        # eventually forwarded saved input can reach the TCON API.
        assert {(0x27A04C, "mov", "r4, r0"), (0x27A064, "blx", "#0x8fef4"),
                (0x27A068, "mov", "r5, r0"), (0x27A06A, "cmp", "r0, #0"),
                (0x27A06C, "beq.w", "#0x27a17a"),
                (0x27A0DA, "mov", "r0, r4"), (0x27A0DC, "blx", "#0x8cd20")} <= set(public_instant)
        tcon_start = listing(elf, 0x24F0EC, 148)
        # The two report paths converge on one of the two monitor-start calls.
        assert {(0x24F0F6, "ldr", "r3, [r0, #0x28]"),
                (0x24F0F8, "cbnz", "r3, #0x24f10e"),
                (0x24F0FE, "ldr", "r3, [r0, #0x7c]"),
                (0x24F100, "cbnz", "r3, #0x24f142"),
                (0x24F102, "blx", "#0x8c2ac"),
                (0x24F13C, "ldr", "r3, [r0, #0x7c]"),
                (0x24F140, "beq", "#0x24f102"),
                (0x24F15A, "blx", "#0x8c2ac")} <= set(tcon_start)
        public_start = listing(elf, 0x270660, 796)
        assert (0x2708A4, "blx", "#0x8da94") in public_start
    print("PASS: complete mapping-symbol call scan; start and instant-on lifecycle edges plus monitor GOT stores")


if __name__ == "__main__":
    main()
