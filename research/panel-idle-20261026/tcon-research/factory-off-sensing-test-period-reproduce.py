#!/usr/bin/env python3
"""Offline verification for the factory off-sensing disable predicate."""
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/tcon-capstone")
from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "binaries" / "deviced"
SHA256 = "2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2"
TIFS = ROOT / "binaries" / "TIFSDaemon"
TIFS_SHA256 = "d2ebc1d11be46b4a189ec87666b68b73ae58d6f5a3c10da901c80e1125620c11"

def main():
    index_path = ROOT / "binaries/factory-data/FactoryIndexFile_Part1.dat"
    part_path = ROOT / "binaries/factory-data/Factory_Part1.dat"
    index_data, part_data = index_path.read_bytes(), part_path.read_bytes()
    assert hashlib.sha256(index_data).hexdigest() == "fd6588baf4e57c5b2b8b3c636e55888f9f6e49cf3b2e7dc80302733066993602"
    assert hashlib.sha256(part_data).hexdigest() == "687b6b019cb1b1fd5f3ae826949cfbe4dd38027cb8d0e2d8f321fd055e2ce417"
    assert struct.unpack_from("<8I", index_data, 0x8bc0) == (20590, 0, 6, 0, 5, 2, 1, 6240)
    assert struct.unpack_from("<I", part_data, 0x691dc)[0] == 20590
    assert part_data[0x691e8:].split(b"\0", 1)[0] == b"Offsensing TEST Period"
    assert part_data[0x69238:].split(b"\0", 1)[0] == b"db/factory/FC_STORE_LEVEL_EER_B/OFFSENSING_TEST_PERIOD"
    assert hashlib.sha256(IMAGE.read_bytes()).hexdigest() == SHA256, "unexpected deviced image"
    with IMAGE.open("rb") as f:
        elf = ELFFile(f); text = elf.get_section_by_name(".text"); base = text["sh_addr"]; blob = text.data()
        cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        def code(a, n): return {i.address: (i.mnemonic, i.op_str) for i in cs.disasm(blob[a-base:a-base+n], a)}
        p = code(0x7ad00, 340)
        for a, m, fragment in ((0x7ad04,"movw","#0x506e"),(0x7ad34,"bl","0x3e548"),(0x7ad38,"cmp","#1"),(0x7adb4,"mov","#0xff"),(0x7adc4,"sub","#6"),(0x7adcc,"clz","r4"),(0x7addc,"lsr","#5")):
            got=p.get(a); assert got and got[0] == m and fragment in got[1], (hex(a),got)
        sym = elf.get_section_by_name(".symtab")
        mapping = sorted((s["st_value"],s.name[:2]) for s in sym.iter_symbols() if s["st_shndx"] == 14 and s.name.startswith(("$a","$d","$t")))
        callers=[]
        for (lo, mode), (hi, _) in zip(mapping, mapping[1:]):
            if mode != "$a": continue
            for i in cs.disasm(blob[lo-base:hi-base],lo):
                if "0x769cc" in i.op_str: callers.append((i.address,i.mnemonic,i.op_str))
        assert callers == [(0x71688,"bl","#0x769cc")], callers
    assert hashlib.sha256(TIFS.read_bytes()).hexdigest() == TIFS_SHA256, "unexpected TIFSDaemon image"
    with TIFS.open("rb") as f:
        elf=ELFFile(f); text=elf.get_section_by_name(".text"); base=text["sh_addr"]; blob=text.data(); cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
        setter={i.address:(i.mnemonic,i.op_str) for i in cs.disasm(blob[0x1077d8-base:0x1077d8-base+260],0x1077d8)}
        assert setter[0x107838] == ("bl", "#0xc5e8c"), setter.get(0x107838)
        assert setter[0x107840] == ("cmp", "r0, #0")
        assert setter[0x107842] == ("eor", "r3, r3, #1")
        assert setter[0x107846] == ("and", "r3, r3, #1")
        assert setter[0x10784a] == ("it", "ne")
        assert setter[0x10784c] == ("movne", "r3, #0")
        assert setter[0x10784e] == ("cbnz", "r3, #0x107890")
        assert setter[0x10789a] == ("blx", "#0x5fd94"), setter.get(0x10789a)
        # The storage call is a PLT veneer; relocation is the stable identity.
        rel=elf.get_section_by_name(".rel.plt"); dyn=elf.get_section(rel["sh_link"])
        got={dyn.get_symbol(x["r_info_sym"]).name:x["r_offset"] for x in rel.iter_relocations()}
        assert got["_ZN19FCStorageBaseCommon13SetFactoryUIDEjii"] == 0x165ad0
    print("PASS: four source hashes; factory UID/label/key; predicate; wrapper caller; conditional transmit/storage sites")
if __name__ == "__main__": main()
