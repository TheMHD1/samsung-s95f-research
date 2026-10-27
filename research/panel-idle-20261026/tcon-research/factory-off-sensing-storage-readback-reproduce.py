#!/usr/bin/env python3
"""Offline landmark verifier for factory UID 0x506e readback/storage audit."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

try:
    from elftools.elf.elffile import ELFFile
    from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
except ModuleNotFoundError:
    sys.path.insert(0, "/tmp/tcon-capstone")
    from elftools.elf.elffile import ELFFile
    from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "binaries/libfactory.so.0.1": "31dc9c0705ae864105cb60bd952e2f06f9bb5524f38612b611906343d11d418d",
    "binaries/libfactory-interface-ATSC.so": "1fc40fa93b3bf81ee79b610d8c699ba94e3f4ee49e3a737d4dfe1e2e803425dd",
    "binaries/libfactory-api-impl-sec.so": "671575f611a69fdbac1c43d27597db640bd963ed9bbce9ecb2f6f5eb1300d12c",
    "binaries/libppi-factory-api.so": "5c7026ae05f5d0ecbd2460245ac604ab718f0af97f6c7a2df717c7a224a8f517",
    "binaries/libprd-factory-interface-ATSC.so": "ef872d9d90135ffcf4bea4470df4f37f4b06b51cd53a9a482568113a3970d0a5",
    "binaries/libnvram.so.0.1": "3f4477b347980727fd1de7ec7709e76a8946a047514d4eeee5e8113f9c80dd95",
    "binaries/libnvram-impl-sec.so.0.1": "8b7b8adf55415aa19b0c55a8f562a3c428620ebf823e1b48c3412f142d5e62fc",
    "binaries/libeeprom-map.so.0.1": "2a7df2af3997c810066585b0186fe3c8455a6a8eb97a47213ef11a8342c5478c",
    "binaries/TIFSDaemon": "d2ebc1d11be46b4a189ec87666b68b73ae58d6f5a3c10da901c80e1125620c11",
    "binaries/factory-data/FactoryIndexFile_Part1.dat": "fd6588baf4e57c5b2b8b3c636e55888f9f6e49cf3b2e7dc80302733066993602",
}


def fail(message: str) -> None:
    raise AssertionError(message)


def dyn_symbols(path: Path):
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        section = elf.get_section_by_name(".dynsym")
        return {symbol.name: (symbol["st_value"], symbol["st_size"])
                for symbol in section.iter_symbols()}


def relocs(path: Path):
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        answer = {}
        for section_name in (".rel.plt", ".rel.dyn"):
            section = elf.get_section_by_name(section_name)
            if not section:
                continue
            symbols = elf.get_section(section["sh_link"])
            for relocation in section.iter_relocations():
                answer[relocation["r_offset"]] = symbols.get_symbol(
                    relocation["r_info_sym"]
                ).name
        return answer


def needed(path: Path):
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        dynamic = elf.get_section_by_name(".dynamic")
        strings = elf.get_section(dynamic["sh_link"])
        return {strings.get_string(tag["d_val"])
                for tag in dynamic.iter_tags() if tag["d_tag"] == "DT_NEEDED"}


def thumb_text(path: Path, address: int, length: int):
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        text = elf.get_section_by_name(".text")
        start = address - text["sh_addr"]
        disassembler = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        return [(item.address, item.mnemonic, item.op_str) for item in
                disassembler.disasm(text.data()[start:start + length], address)]


def contains(instructions, address: int, mnemonic: str, fragment: str = ""):
    if not any(a == address and m == mnemonic and fragment in o
               for a, m, o in instructions):
        fail(f"missing {address:#x}: {mnemonic} {fragment}")


def main() -> None:
    for relative, expected in FILES.items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            fail(f"hash mismatch {relative}: {actual}")

    interface = ROOT / "binaries/libfactory-interface-ATSC.so"
    api = ROOT / "binaries/libfactory-api-impl-sec.so"
    loader = ROOT / "binaries/libfactory.so.0.1"
    ppi = ROOT / "binaries/libppi-factory-api.so"
    prd = ROOT / "binaries/libprd-factory-interface-ATSC.so"
    nvram = ROOT / "binaries/libnvram.so.0.1"
    nvram_impl = ROOT / "binaries/libnvram-impl-sec.so.0.1"
    eeprom = ROOT / "binaries/libeeprom-map.so.0.1"
    tifs = ROOT / "binaries/TIFSDaemon"
    index1 = ROOT / "binaries/factory-data/FactoryIndexFile_Part1.dat"
    interface_symbols = dyn_symbols(interface)
    api_symbols = dyn_symbols(api)
    loader_symbols = dyn_symbols(loader)
    ppi_symbols = dyn_symbols(ppi)
    prd_symbols = dyn_symbols(prd)
    nvram_symbols = dyn_symbols(nvram)
    nvram_impl_symbols = dyn_symbols(nvram_impl)
    eeprom_symbols = dyn_symbols(eeprom)

    if interface_symbols.get("factory_get_data") != (0x439A4B0D, 176):
        fail("unexpected public factory_get_data symbol")
    if api_symbols.get("factory_get_data_impl") != (0x1DC5, 168):
        fail("unexpected factory_get_data_impl symbol")
    if "factory_get_data" in loader_symbols:
        fail("libfactory.so unexpectedly exports factory_get_data")
    if "ppi_factory_get_backend" not in loader_symbols:
        fail("missing libfactory backend loader export")
    if ppi_symbols.get("ppi_factory_get_data") != (0x43AB2021, 232):
        fail("unexpected PPI factory_get_data symbol")
    if prd_symbols.get("prd_factory_get_data") != (0x12E9D, 100):
        fail("unexpected PRD factory_get_data symbol")
    if interface_symbols.get("_ZN19FCStorageBaseCommon13SetFactoryUIDEji17fac_source_info_s") != (0x43999999, 400):
        fail("unexpected FC SetFactoryUID symbol")
    if interface_symbols.get("_ZN10FCNvramMap16WriteFactoryAreaEjjPKh") != (0x439B0781, 96):
        fail("unexpected FC byte WriteFactoryArea symbol")
    if prd_symbols.get("_ZN11PrdNvramMap15ReadFactoryAreaEjjPh") != (0x15699, 96):
        fail("unexpected PRD byte ReadFactoryArea symbol")
    if prd_symbols.get("_ZN11PrdNvramMap16WriteFactoryAreaEjjPKh") != (0x1557D, 96):
        fail("unexpected PRD byte WriteFactoryArea symbol")
    if nvram_symbols.get("ppi_nvram_write") != (0x43A7074D, 124):
        fail("unexpected PPI NVRAM write symbol")
    if nvram_impl_symbols.get("_ZN12NvramSecImpl5writeEjjPKc") != (0xA65, 84):
        fail("unexpected NVRAM implementation write symbol")
    if eeprom_symbols.get("eeprom_write") != (0xA41, 364):
        fail("unexpected EEPROM write symbol")
    if "libeeprom-map.so.0" not in needed(nvram_impl):
        fail("NVRAM implementation no longer needs libeeprom-map.so.0")

    interface_relocs = relocs(interface)
    api_relocs = relocs(api)
    prd_relocs = relocs(prd)
    tifs_relocs = relocs(tifs)
    nvram_impl_relocs = relocs(nvram_impl)
    if interface_relocs.get(0x439D5D0C) != "ppi_factory_get_data":
        fail("public getter PPI relocation changed")
    if api_relocs.get(0x1305C) != "prd_factory_get_data":
        fail("implementation getter PRD relocation changed")
    expected_prd = {
        0x2E07C: "_ZN20PrdStorageBaseCommon13GetFactoryUIDEjPi22_ppi_fac_source_info_s",
        0x2E0D0: "_ZN11PrdNvramMap15ReadFactoryAreaEjjPi",
        0x2E0F0: "_ZN20PrdStorageBaseCommon17t_GetFileItemNodeEP13FacFileItem_s",
        0x2E1FC: "_ZN11PrdNvramMap16WriteFactoryAreaEjji",
    }
    for address, symbol in expected_prd.items():
        if prd_relocs.get(address) != symbol:
            fail(f"PRD relocation changed at {address:#x}")
    if interface_relocs.get(0x439D5CE4) != "_ZN19FCStorageBaseCommon17t_GetFileItemNodeEP13FacFileItem_s":
        fail("FC file-item lookup relocation changed")
    if interface_relocs.get(0x439D5B10) != "_ZN10FCNvramMap16WriteFactoryAreaEjji":
        fail("FC integer NVRAM write relocation changed")
    if interface_relocs.get(0x439D6018) != "ppi_nvram_write":
        fail("FC NVRAM PPI write relocation changed")
    if nvram_impl_relocs.get(0x12020) != "eeprom_write":
        fail("NVRAM implementation EEPROM write relocation changed")
    if tifs_relocs.get(0x165AD0) != "_ZN19FCStorageBaseCommon13SetFactoryUIDEjii":
        fail("TIFSDaemon simple FC SetFactoryUID relocation changed")
    if interface_relocs.get(0x439D5FF4) != "_ZN19FCStorageBaseCommon13SetFactoryUIDEji17fac_source_info_s":
        fail("FC detailed SetFactoryUID relocation changed")
    if prd_relocs.get(0x2DED0) != "_ZN11PrdNvramMap6t_ReadEjjPhPi":
        fail("PRD NVRAM read vtable slot changed")
    if prd_relocs.get(0x2DED4) != "_ZN11PrdNvramMap7t_WriteEjjPKhPi":
        fail("PRD NVRAM write vtable slot changed")
    if interface_relocs.get(0x439D5760) != "_ZN10FCNvramMap6t_ReadEjjPhPi":
        fail("FC NVRAM read vtable slot changed")
    if interface_relocs.get(0x439D5764) != "_ZN10FCNvramMap7t_WriteEjjPKhPi":
        fail("FC NVRAM write vtable slot changed")

    public = thumb_text(interface, 0x439A4B0C, 0x8C)
    contains(public, 0x439A4B14, "blx", "0x4398a730")
    contains(public, 0x439A4B28, "blx", "0x4398a730")
    contains(public, 0x439A4B20, "cmp", "r0, r3")
    contains(public, 0x439A4B2C, "movw", "r3, #0xf447")
    contains(public, 0x439A4B38, "movne", "r0, #1")

    implementation = thumb_text(api, 0x1DC4, 0x88)
    contains(implementation, 0x1DCC, "blx", "0x1050")
    contains(implementation, 0x1DD8, "blx", "0x1050")
    contains(implementation, 0x1DD0, "adds", "r0, #1")
    contains(implementation, 0x1DDC, "cbz", "r0, #0x1e18")

    ppi_get = thumb_text(ppi, 0x43AB2020, 0xB8)
    contains(ppi_get, 0x43AB2040, "ldr", "r0, [r3]")
    contains(ppi_get, 0x43AB2050, "ldr", "r3, [r3]")
    contains(ppi_get, 0x43AB2058, "bx", "r3")
    api_table = thumb_text(api, 0x1F10, 0x30)
    contains(api_table, 0x1F1C, "ldr", "r1, [r3, r1]")
    contains(api_table, 0x1F1E, "str", "r1, [r0]")

    prd_normal = thumb_text(prd, 0x10B24, 0xE0)
    contains(prd_normal, 0x10B9C, "cmp.w", "r1, #0x1fa")
    contains(prd_normal, 0x10BA0, "bne", "#0x10bde")
    contains(prd_normal, 0x10BFA, "blx", "#0xa690")
    prd_store = thumb_text(prd, 0x10A08, 0xB8)
    contains(prd_store, 0x10A2C, "blx", "#0xa7f0")
    contains(prd_store, 0x10A36, "ldr", "r0, [r0, #0x14]")
    contains(prd_store, 0x10A5A, "cmp", "r0, #2")
    contains(prd_store, 0x10A5C, "beq", "#0x10aa0")
    contains(prd_store, 0x10AA4, "ldrd", "r2, r1, [r4, #0x18]")
    contains(prd_store, 0x10AA8, "blx", "#0xa78c")

    setter_prd = thumb_text(prd, 0x137E4, 0x170)
    contains(setter_prd, 0x1382A, "subs", "r2, r3, #2")
    contains(setter_prd, 0x1382E, "bls", "#0x138c6")
    contains(setter_prd, 0x138FA, "ldr", "r2, [r4, #0x18]")
    contains(setter_prd, 0x13900, "ldr", "r0, [r7, #4]")
    contains(setter_prd, 0x13906, "blx", "#0xab24")

    prd_read_byte = thumb_text(prd, 0x15698, 0x50)
    contains(prd_read_byte, 0x1569A, "adds", "r6, r1, r2")
    contains(prd_read_byte, 0x156A0, "cmp.w", "r6, #0x4000")
    contains(prd_read_byte, 0x156AC, "add.w", "r1, r4, #0x3e00")
    contains(prd_read_byte, 0x156B2, "blx", "r4")
    prd_write_byte = thumb_text(prd, 0x1557C, 0x50)
    contains(prd_write_byte, 0x1557E, "adds", "r6, r1, r2")
    contains(prd_write_byte, 0x15584, "cmp.w", "r6, #0x4000")
    contains(prd_write_byte, 0x15590, "add.w", "r1, r4, #0x3e00")
    contains(prd_write_byte, 0x15596, "blx", "r4")
    prd_read_int = thumb_text(prd, 0x156F8, 0x80)
    contains(prd_read_int, 0x15732, "blx", "#0xab30")
    contains(prd_read_int, 0x15736, "ldrsb.w", "r3, [sp, #0x25]")
    prd_write_int = thumb_text(prd, 0x155DC, 0x70)
    contains(prd_write_int, 0x15612, "strb.w", "r6, [sp, #0x1d]")
    contains(prd_write_int, 0x15616, "blx", "#0xa714")
    prd_read_e = thumb_text(prd, 0x14BF0, 0x120)
    contains(prd_read_e, 0x14C30, "add", "r2, sp, #0x24")
    contains(prd_read_e, 0x14C32, "movw", "r1, #0x4906")
    contains(prd_read_e, 0x14C36, "movt", "r1, #0x8004")
    contains(prd_read_e, 0x14C48, "blx", "#0xa980")
    contains(prd_read_e, 0x14C8A, "blx", "#0xa9d8")
    prd_write_e = thumb_text(prd, 0x14DB4, 0x120)
    contains(prd_write_e, 0x14DF4, "movw", "r1, #0x4905")
    contains(prd_write_e, 0x14DF8, "movt", "r1, #0x4004")
    contains(prd_write_e, 0x14E08, "blx", "#0xa980")
    contains(prd_write_e, 0x14E4A, "blx", "#0xa9d8")
    raw = index1.read_bytes()
    expected_tuple = (0x506E, 0, 6, 0, 5, 2, 1, 0x1860)
    found_tuple = tuple(int.from_bytes(raw[0x8BC0 + i:0x8BC4 + i], "little")
                        for i in range(0, 32, 4))
    if found_tuple != expected_tuple:
        fail(f"UID 0x506e FactoryIndex tuple changed: {found_tuple}")

    setter = thumb_text(interface, 0x43999998, 0x190)
    revision = thumb_text(interface, 0x43999928, 0x60)
    contains(setter, 0x43999A2E, "ldr.w", "r8, [ip, #0x30]")
    contains(setter, 0x43999A32, "blx", "r8")
    contains(revision, 0x43999952, "ldr", "r1, [r5, #0x30]")
    contains(revision, 0x43999958, "blx", "0x4398a110")

    fc_setter = thumb_text(interface, 0x43999998, 0x140)
    contains(fc_setter, 0x439999BC, "blx", "#0x4398a6b0")
    contains(fc_setter, 0x439999DA, "ldr", "r3, [r4, #0x14]")
    contains(fc_setter, 0x439999DC, "subs", "r2, r3, #2")
    contains(fc_setter, 0x439999E0, "bls", "#0x43999a76")
    contains(fc_setter, 0x43999AA6, "ldr", "r2, [r4, #0x18]")
    contains(fc_setter, 0x43999AAA, "ldr", "r1, [r4, #0x1c]")
    contains(fc_setter, 0x43999AAE, "mla", "r1, r6, r2, r1")
    contains(fc_setter, 0x43999AB2, "blx", "#0x4398a104")
    fc_write_byte = thumb_text(interface, 0x439B0780, 0x40)
    contains(fc_write_byte, 0x439B0782, "adds", "r6, r1, r2")
    contains(fc_write_byte, 0x439B0788, "cmp.w", "r6, #0x4000")
    contains(fc_write_byte, 0x439B0794, "add.w", "r1, r4, #0x3e00")
    contains(fc_write_byte, 0x439B079A, "blx", "r4")
    fc_write_e = thumb_text(interface, 0x439AFB68, 0xB0)
    contains(fc_write_e, 0x439AFC04, "blx", "#0x4398b07c")
    fc_simple_setter = thumb_text(interface, 0x43999B28, 0x50)
    contains(fc_simple_setter, 0x43999B6A, "blx", "#0x4398b010")
    tifs_setter = thumb_text(tifs, 0x1077D8, 0xD0)
    contains(tifs_setter, 0x10789A, "blx", "#0x5fd94")

    nvram_write = thumb_text(nvram, 0x43A7074C, 0x40)
    contains(nvram_write, 0x43A70762, "bl", "#0x43a705f4")
    contains(nvram_write, 0x43A7076A, "ldr", "r3, [r3, #4]")
    contains(nvram_write, 0x43A7076E, "ldr", "r3, [r3, #4]")
    contains(nvram_write, 0x43A7077E, "bx", "r3")
    nvram_impl_write = thumb_text(nvram_impl, 0xB3C, 0x30)
    contains(nvram_impl_write, 0xB62, "b.w", "#0x830")
    nvram_method_write = thumb_text(nvram_impl, 0xA64, 0x20)
    contains(nvram_method_write, 0xA6E, "blx", "#0x7b4")
    eeprom_write = thumb_text(eeprom, 0xA40, 0x60)
    contains(eeprom_write, 0xA78, "movw", "r1, #0x4905")
    contains(eeprom_write, 0xA7C, "movt", "r1, #0x4004")
    contains(eeprom_write, 0xA8E, "blx", "#0x670")

    print("PASS: hash-gated PRD/FC type-2 NVRAM and PPI-to-EEPROM landmarks")
    print("LIMIT: no live PPI table binding, EEPROM persistence/notify, reload, or deletion proof")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, KeyError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
