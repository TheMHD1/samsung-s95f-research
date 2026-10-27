#!/usr/bin/env python3
"""Offline hash-gated invariants for pm-lock-expiry-notifier.md."""
import hashlib
from pathlib import Path
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from elftools.elf.elffile import ELFFile

p = Path(__file__).resolve().parents[1] / "binaries/deviced"
assert hashlib.sha256(p.read_bytes()).hexdigest() == "2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2"
with p.open("rb") as fp:
    e = ELFFile(fp)
    def read(a, n):
        for s in e.iter_segments():
            if s["p_type"] == "PT_LOAD" and s["p_vaddr"] <= a and a+n <= s["p_vaddr"]+s["p_filesz"]:
                fp.seek(s["p_offset"] + a-s["p_vaddr"]); return fp.read(n)
        raise AssertionError(hex(a))
    def ins(a, n): return list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(read(a, n), a))
    a = ins(0x66008, 12)
    assert [(x.mnemonic, x.op_str) for x in a] == [("mov", "r1, #0"), ("mov", "r0, #0x14"), ("bl", "#0x415ac")]
    assert any(x.mnemonic == "bl" and x.op_str == "#0x3e2a8" for x in ins(0x65fcc, 16))
    assert any(x.mnemonic == "bl" and x.op_str == "#0x412a4" for x in ins(0x73834, 16))
    h = ins(0x7366c, 84)
    assert any(x.op_str == "#0x752a0" for x in h) and any(x.op_str == "#0x7dd34" for x in h)
    def u32(a): return int.from_bytes(read(a, 4), "little")
    assert u32(0x128A20 + 8 + 0x0C) == 0x7A6F8
    assert u32(0x128AE0 + 8 + 0x0C) == 0x80F3C
print("PASS: static PM/notifier edges only; runtime list/object/output unknown.")
