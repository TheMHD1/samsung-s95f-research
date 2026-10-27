#!/usr/bin/env python3
"""Offline, bounded disassembly reproducer for the NewHome QD frame-mode path.

It only opens the copied qdf_tcon.ko and writes disassembly to stdout.  Run:
  PYTHONPATH=/tmp/tcon-capstone python3 newhome-tcon-vfreq-reproduce.py
"""
from pathlib import Path
import hashlib
from elftools.elf.elffile import ELFFile
from capstone import CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN, Cs

MODULE = Path(__file__).parent.parent / "binaries" / "qdf_tcon.ko"
assert hashlib.sha256(MODULE.read_bytes()).hexdigest() == "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"
with MODULE.open("rb") as source:
    TEXT_FILE_OFFSET = ELFFile(source).get_section_by_name(".text")["sh_offset"]
FUNCTIONS = (
    (0x10508, 0x2E0, "m_tcon_set_frame_mode"),
    (0x11058, 0x268, "m_tcon_set_frame_control"),
    (0x112C0, 0x74, "QDFTcon_SetVRRFrameRate"),
    (0x0CE00, 0x290, "QDFTcon_t_Tcon_SetMute"),
    (0x0D728, 0xA0, "m_tcon_set_vrr_control"),
    (0x0D7C8, 0xA0, "m_tcon_set_vrr_dia_en"),
)

with MODULE.open("rb") as binary:
    for address, size, label in FUNCTIONS:
        binary.seek(TEXT_FILE_OFFSET + address)
        print(f"# {label} @ .text+0x{address:x}")
        for instruction in Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN).disasm(
            binary.read(size), address
        ):
            print(f"{instruction.address:06x}: {instruction.mnemonic:7} {instruction.op_str}")
        print()
