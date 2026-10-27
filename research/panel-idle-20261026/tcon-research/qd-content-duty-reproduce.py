#!/usr/bin/env python3
"""Offline, fingerprinted QDMNT brightness evidence; no device/network access.

Run with PYTHONPATH=/tmp/tcon-capstone on the investigation controller.
Requires pyelftools 0.33, capstone 5.0.7, c++filt and AArch64 objdump.
Addresses are link-time addresses or explicitly section-relative offsets.
ARM mapping symbols exclude literal pools from instruction decoding.
"""
from bisect import bisect_right
import hashlib
from pathlib import Path
import struct
import subprocess
import sys

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
from elftools.elf.elffile import ELFFile

BASE = Path(__file__).resolve().parents[1]
EXPECTED = {
    "libave.so.0.1": "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777",
    "qdf_tcon.ko": "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63",
    "tztv_frc_tcon_api.ko": "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6",
}


def demangle(name):
    return subprocess.run(["c++filt", name], check=True, text=True, capture_output=True).stdout.strip()


def main():
    for name, expected in EXPECTED.items():
        actual = hashlib.sha256((BASE / "binaries" / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"Unexpected input {name}: {actual}")
        print("SHA256", name, actual)
    with (BASE / "binaries/libave.so.0.1").open("rb") as fh:
        elf = ELFFile(fh)
        symbols = list(elf.get_section_by_name(".symtab").iter_symbols())
        text = elf.get_section_by_name(".text")
        blob, text_base = text.data(), text["sh_addr"]
        mappings = sorted({(symbol["st_value"], symbol.name[:2]) for symbol in symbols
                           if symbol.name.startswith(("$a", "$t", "$d"))
                           and symbol["st_shndx"] == elf.get_section_index(".text")})
        map_addresses = [address for address, _ in mappings]
        rel = elf.get_section_by_name(".rel.plt")
        dynsym = elf.get_section(rel["sh_link"])
        plt_base = elf.get_section_by_name(".plt")["sh_addr"]
        plt = {plt_base + 20 + 12 * index: (reloc["r_offset"], dynsym.get_symbol(reloc["r_info_sym"]).name)
               for index, reloc in enumerate(rel.iter_relocations())}

        def read(address, size=4):
            for section in elf.iter_sections():
                start = section["sh_addr"]
                if section["sh_type"] != "SHT_NOBITS" and start <= address and address + size <= start + section["sh_size"]:
                    return section.data()[address - start:address - start + size]
            raise ValueError(hex(address))

        print("\nQDMNT backend vtable relocations; address point = symbol +8:")
        rel = elf.get_section_by_name(".rel.dyn")
        dynsym = elf.get_section(rel["sh_link"])
        wanted = {0x5A177C + 8 + slot: slot for slot in (0xD8, 0x19C, 0x200, 0x210)}
        for reloc in rel.iter_relocations():
            address = reloc["r_offset"]
            if address in wanted:
                symbol = dynsym.get_symbol(reloc["r_info_sym"])
                addend = struct.unpack("<I", read(address))[0]
                assert reloc["r_info_type"] == 2  # R_ARM_ABS32
                print(f"slot+0x{wanted[address]:x} entry@0x{address:x} R_ARM_ABS32 "
                      f"S=0x{symbol['st_value']:x} A=0x{addend:x} {demangle(symbol.name)}")

        # Use verified exported symbol starts; print each actual symbol name.
        starts = (0x172A34, 0x1740F0, 0x19ABE8, 0x1C9E74, 0x1C8F78,
                  0x1C9704, 0x17B204, 0x1CB2D8, 0x25D2AC, 0x2519D8)
        for start in starts:
            candidates = [symbol for symbol in symbols if symbol["st_info"]["type"] == "STT_FUNC"
                          and symbol["st_value"] & ~1 == start and symbol["st_size"]]
            if not candidates:
                raise SystemExit(f"Missing function @0x{start:x}")
            symbol = candidates[0]
            end = start + symbol["st_size"]
            print(f"\nFUNCTION {demangle(symbol.name)} 0x{start:x}..0x{end:x}")
            boundaries = sorted({start, end, *(address for address, _ in mappings if start < address < end)})
            for lo, hi in zip(boundaries, boundaries[1:]):
                mode = mappings[bisect_right(map_addresses, lo) - 1][1]
                data = blob[lo - text_base:hi - text_base]
                if mode == "$d":
                    print(f"LITERAL POOL 0x{lo:x}..0x{hi:x}: {data.hex()}")
                    continue
                decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB if mode == "$t" else CS_MODE_ARM)
                for insn in decoder.disasm(data, lo):
                    annotation = ""
                    if insn.mnemonic in ("bl", "blx", "b.w") and insn.op_str.startswith("#0x"):
                        target = int(insn.op_str[1:], 16)
                        if target in plt:
                            got, name = plt[target]
                            annotation = f" ; PLT GOT0x{got:x} {demangle(name)}"
                    print(f"{insn.address:08x}: {insn.mnemonic:8} {insn.op_str}{annotation}")
        for literal, pc in ((0x174244, 0x17410E), (0x174248, 0x17416A), (0x1C9F38, 0x1C9E8A)):
            value = struct.unpack("<I", read(literal))[0]
            print(f"PC-relative literal@0x{literal:x}=0x{value:x}, PC0x{pc:x} => 0x{(value + pc) & 0xffffffff:x}")
    sys.stdout.flush()
    for start, stop in ((0xEB60, 0xECE0), (0xD120, 0xD250)):
        subprocess.run(["aarch64-linux-gnu-objdump", "-dr", "-j", ".text",
                        f"--start-address={start}", f"--stop-address={stop}",
                        str(BASE / "binaries/qdf_tcon.ko")], check=True)
    with (BASE / "binaries/tztv_frc_tcon_api.ko").open("rb") as fh:
        rodata = ELFFile(fh).get_section_by_name(".rodata").data()
        for op in (18, 32):
            displacement = struct.unpack_from("<h", rodata, 0x6A0 + (op - 1) * 2)[0]
            print(f"TCON_Request op{op} jump-table target = 0x{0xE804 + displacement * 4:x}")
    sys.stdout.flush()
    for start, stop in ((0xEC00, 0xEC20), (0xF170, 0xF198)):
        subprocess.run(["aarch64-linux-gnu-objdump", "-dr", "-j", ".text",
                        f"--start-address={start}", f"--stop-address={stop}",
                        str(BASE / "binaries/tztv_frc_tcon_api.ko")], check=True)
    subprocess.run(["aarch64-linux-gnu-objdump", "-dr", "-j", ".init.text",
                    str(BASE / "binaries/qdf_tcon.ko")], check=True)


if __name__ == "__main__":
    main()
