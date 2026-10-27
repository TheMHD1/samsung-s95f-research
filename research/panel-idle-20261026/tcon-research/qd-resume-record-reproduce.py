#!/usr/bin/env python3
"""Offline hash-gated checks for RoseMQD QD resume record/replay."""
import hashlib
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile

BASE = Path(__file__).resolve().parents[1]
LIB = BASE / "binaries/libave.so.0.1"
SHA = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"


def need(ok, text):
    if not ok:
        raise AssertionError(text)


def main():
    actual = hashlib.sha256(LIB.read_bytes()).hexdigest()
    need(actual == SHA, f"unexpected libave SHA256: {actual}")
    print(f"SHA256 binaries/libave.so.0.1 {actual}")
    with LIB.open("rb") as f:
        elf = ELFFile(f)
        syms = elf.get_section_by_name(".symtab")
        need(syms is not None, "missing symtab")
        by_name = {x.name: x for x in syms.iter_symbols()}
        expected = {
            "_ZN21DimmingBackendRoseMQD17t_SetQdResumeDataEv": (0x1C5F49, 62),
            "_ZN21DimmingBackendRoseMQD21t_DevQdDrv_Write_DataEyiji": (0x1C7D6D, 188),
            "_ZN9QDDimming15m_SetResumeDataEv": (0x1738A9, 44),
            "_ZN21DimmingBackendRoseMQDC1Ev": (0x1C85A1, 292),
        }
        for n, wanted in expected.items():
            s = by_name.get(n)
            need(s is not None and (int(s["st_value"]), int(s["st_size"])) == wanted, f"symbol mismatch {n}")

        def data(va, size):
            for seg in elf.iter_segments():
                if seg["p_type"] == "PT_LOAD" and int(seg["p_vaddr"]) <= va and va + size <= int(seg["p_vaddr"]) + int(seg["p_filesz"]):
                    f.seek(int(seg["p_offset"]) + va - int(seg["p_vaddr"]))
                    b = f.read(size)
                    need(len(b) == size, "short read")
                    return b
            raise AssertionError(f"unmapped VA {va:x}")

        cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
        def code(va, size):
            return {(i.address, i.mnemonic, i.op_str) for i in cs.disasm(data(va, size), va)}

        replay = code(0x1C5F48, 62)
        need(0x115 * 8 == 0x8A8, "resume command-base arithmetic")
        need({
            (0x1C5F54, "cmp", "r4, #0x10"), (0x1C5F5C, "ldrb.w", "r2, [r2, #0x330]"),
            (0x1C5F60, "cmp", "r2, #1"), (0x1C5F64, "addw", "r1, r4, #0x115"),
            (0x1C5F6C, "addw", "r2, r2, #0xee8"), (0x1C5F72, "add.w", "r3, r3, r1, lsl #3"),
            (0x1C5F76, "ldrd", "r0, r1, [r3]"), (0x1C5F7A, "blx", "#0x8db9c"),
            (0x1C5F82, "movs", "r0, #0"),
        } <= replay, "resume replay landmarks")
        need(not any(m in {"bl", "blx"} and "0x1c6274" in o for _, m, o in replay), "unexpected direct final-duty call")

        writer = code(0x1C7D6C, 188)
        need({
            (0x1C7D90, "cmp", "r6, #0xf"), (0x1C7D94, "bgt", "#0x1c7dda"),
            (0x1C7D98, "addw", "r2, r6, #0x115"), (0x1C7DA4, "add.w", "r3, r3, r2, lsl #3"),
            (0x1C7DAA, "strd", "r0, r1, [r3]"), (0x1C7DB0, "str.w", "ip, [r3, lr, lsl #2]"),
            (0x1C7DBA, "strb.w", "r3, [r6, #0x330]"), (0x1C7DBE, "blx", "#0x8db9c"),
            (0x1C7E00, "mov.w", "r0, #-1"),
        } <= writer, "record producer landmarks")

        gate = code(0x1738A8, 44)
        need({
            (0x1738AE, "ldr.w", "r2, [r3, #0x398]"), (0x1738B2, "cmp", "r2, #1"),
            (0x1738C0, "cbz", "r0, #0x1738cc"), (0x1738C4, "ldr.w", "r3, [r3, #0x18c]"),
            (0x1738C8, "blx", "r3"), (0x1738CE, "str.w", "r2, [r3, #0x398]"),
        } <= gate, "QDDimming resume gate landmarks")

        ctor = code(0x1C85A0, 292)
        need({
            (0x1C8620, "addw", "r0, r0, #0x8a8"), (0x1C8624, "blx", "#0x8cbdc"),
            (0x1C8630, "addw", "r0, r0, #0xee8"), (0x1C8634, "blx", "#0x8cbdc"),
            (0x1C863E, "add.w", "r0, r0, #0x330"), (0x1C8642, "blx", "#0x8cbdc"),
        } <= ctor, "constructor clear landmarks")

        relocs = {}
        for sec in elf.iter_sections():
            if not hasattr(sec, "iter_relocations") or not sec["sh_link"]:
                continue
            linked = elf.get_section(sec["sh_link"])
            for r in sec.iter_relocations():
                if r["r_info_sym"]:
                    relocs[int(r["r_offset"])] = linked.get_symbol(r["r_info_sym"]).name
        need(relocs.get(0x5A16B8) == "_ZN21DimmingBackendRoseMQD17t_SetQdResumeDataEv", "resume vtable binding")
        need(relocs.get(0x5A16BC) == "_ZN21DimmingBackendRoseMQD21t_DevQdDrv_Write_DataEyiji", "producer vtable binding")
    print("PASS: hash-gated RoseMQD 16-slot resume record/replay landmarks")
    print("LIMIT: manual CFG/ABI; record contents, live calls, sender acceptance, and physical output unproved")


if __name__ == "__main__":
    main()
