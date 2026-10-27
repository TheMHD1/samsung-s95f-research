#!/usr/bin/env python3
"""Offline, hash-gated cache-lifecycle evidence for active RoseMQD only."""
import hashlib
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile

BASE = Path(__file__).resolve().parents[1]
IMAGE = BASE / "binaries/libave.so.0.1"
EXPECTED = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"
CACHE = 0x5AB958
ANCHOR = 0x5AB948

def main():
    blob = IMAGE.read_bytes()
    actual = hashlib.sha256(blob).hexdigest()
    assert actual == EXPECTED, actual
    print("SHA256", IMAGE.name, actual)
    with IMAGE.open("rb") as handle:
        elf = ELFFile(handle)
        loads = [s for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"]
        def data_at(vaddr, size):
            for segment in loads:
                start, end = segment["p_vaddr"], segment["p_vaddr"] + segment["p_filesz"]
                if start <= vaddr and vaddr + size <= end:
                    offset = segment["p_offset"] + vaddr - start
                    return blob[offset:offset + size], offset
            raise AssertionError(hex(vaddr))
        symbols = {s.name: s for s in elf.get_section_by_name(".symtab").iter_symbols()}
        name = "_ZZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_tE8siDimLvl"
        symbol = symbols[name]
        assert symbol["st_value"] == CACHE and symbol["st_size"] == 4
        initial, _ = data_at(CACHE, 4)
        assert struct.unpack("<i", initial)[0] == -1
        print(f"CACHE symbol VA=0x{CACHE:x} initial={struct.unpack('<i', initial)[0]}")
        literal, literal_off = data_at(0x1C6354, 4)
        assert struct.unpack("<I", literal)[0] == 0x3E56BE
        assert blob.count(literal) == 1
        assert 0x1C628A + struct.unpack("<I", literal)[0] == ANCHOR
        assert ANCHOR + 0x10 == CACHE
        print("UNIQUE_LITERAL file_offset=0x%x VA=0x1c6354 value=0x3e56be "
              "add-PC@0x1c6286(PC=0x1c628a)=>0x5ab948 +0x10=>0x5ab958" % literal_off)
        text = elf.get_section_by_name(".text")
        raw, start = text.data(), 0x1C6274
        insns = {(x.address, x.mnemonic, x.op_str) for x in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(
            raw[start-text["sh_addr"]:start-text["sh_addr"]+0xFC], start)}
        required = {(0x1C6282,"ldr","r3, [pc, #0xd0]"),(0x1C6286,"add","r3, pc"),
                    (0x1C629A,"ldr","r2, [r3, #0x10]"),(0x1C629E,"cmp","r2, r8"),
                    (0x1C62A0,"beq","#0x1c62ca"),(0x1C62AC,"str.w","r8, [r3, #0x10]"),
                    (0x1C62B4,"blx","#0x8db9c"),(0x1C62B8,"ldr","r1, [r7]"),
                    (0x1C62C4,"blx","#0x9023c"),(0x1C62C8,"orrs","r5, r0")}
        assert required <= insns
        print("SET2D: read/compare/equal-skip; pre-I/O store; both calls; OR result")
        # The constructor/destructor and these vtable-selected methods are the
        # bounded lifecycle set below. This only tests for this same recovered
        # PC-relative materialization, not every possible address construction.
        lifecycle = {
            "destructor": ("_ZN21DimmingBackendRoseMQDD1Ev", 0x1C5C54, 0x24),
            "dimming-condition": ("_ZN21DimmingBackendRoseMQD21t_SetDimmingConditionEv", 0x1C5C8C, 0x204),
            "init-qd-dimming": ("_ZN21DimmingBackendRoseMQD15t_InitQDDimmingEv", 0x1C5EB8, 0x90),
            "resume-data": ("_ZN21DimmingBackendRoseMQD17t_SetQdResumeDataEv", 0x1C5F48, 0x3E),
            "constructor": ("_ZN21DimmingBackendRoseMQDC2Ev", 0x1C85A0, 0x124),
        }
        for label, (name, where, size) in lifecycle.items():
            lifecycle_symbol = symbols[name]
            assert lifecycle_symbol["st_value"] & ~1 == where
            assert lifecycle_symbol["st_size"] == size
            code = raw[where-text["sh_addr"]:where-text["sh_addr"]+size]
            assert literal not in code
            calls = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, where))
            assert not any(x.mnemonic in ("bl", "blx") and x.op_str == "#0x1c6274"
                           for x in calls), label
        print("LIFECYCLE: ctor/dtor/init/resume/condition bodies contain no cache literal")
        final = symbols["_ZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_t"]
        assert final["st_value"] & ~1 == 0x1C6274 and final["st_size"] == 0xFC
        base = 0x17B564
        caller = {(x.address, x.mnemonic, x.op_str) for x in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(
            raw[base-text["sh_addr"]:base-text["sh_addr"]+10], base)}
        assert (0x17B566,"blx","#0x8e304") in caller and (0x17B56A,"b","#0x17b3e4") in caller
        print("CALLER: QDDimming vsync calls final-duty then branches without consuming r0")
    print("PASS: static cache anchor/reference/update path only; no runtime or emission proof.")

if __name__ == "__main__":
    main()
