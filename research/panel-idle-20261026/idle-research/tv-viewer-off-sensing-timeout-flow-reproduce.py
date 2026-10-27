#!/usr/bin/env python3
"""Offline, hash-gated checks for the forced off-sensing countdown trace.

This validates instruction locations in the saved executable; it neither opens
a device connection nor executes target code.  It cannot prove runtime timer
units, callback delivery/order, or a request/reply on the television.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# Analysis dependencies were staged locally for this audit, not installed or
# fetched by this verifier.
sys.path.insert(0, "/tmp/tcon-capstone")
from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs  # noqa: E402
from elftools.elf.elffile import ELFFile  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
TV_VIEWER = ROOT / "binaries" / "tv-viewer"
EXPECTED_SHA256 = "d32fbb420d26a27845cbb23ab216de23706c6aeb6376e4107849f74ec5a1883f"


def fail(message: str) -> None:
    raise AssertionError(message)


def decode(elf: ELFFile, address: int, size: int) -> dict[int, tuple[str, str]]:
    text = elf.get_section_by_name(".text")
    assert text is not None
    start = address - text["sh_addr"]
    if start < 0 or start + size > text.data_size:
        fail(f"range outside .text: {address:#x}+{size:#x}")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    return {i.address: (i.mnemonic, i.op_str) for i in md.disasm(text.data()[start:start + size], address)}


def expect(code: dict[int, tuple[str, str]], address: int, mnemonic: str,
           operand_fragment: str) -> None:
    actual = code.get(address)
    if actual is None or actual[0] != mnemonic or operand_fragment not in actual[1]:
        fail(f"{address:#x}: expected {mnemonic} containing {operand_fragment!r}; got {actual!r}")


def main() -> None:
    digest = hashlib.sha256(TV_VIEWER.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        fail(f"wrong tv-viewer hash: {digest}")

    with TV_VIEWER.open("rb") as stream:
        elf = ELFFile(stream)
        symbols = elf.get_section_by_name(".dynsym")
        assert symbols is not None
        exported = {s.name: (s["st_value"], s["st_size"]) for s in symbols.iter_symbols()}
        relplt = elf.get_section_by_name(".rel.plt")
        assert relplt is not None
        rel_dynsym = elf.get_section(relplt["sh_link"])
        imported = {rel_dynsym.get_symbol(r["r_info_sym"]).name for r in relplt.iter_relocations()}
        for name in (
            "_ZN5Lotus7TCAlarm6CreateEPNS_9TCEventIOEmm",
            "_ZN5Lotus7TCAlarm5ResetEmm",
            "qd_display_request_off_sensing",
        ):
            if name not in imported:
                fail(f"missing expected PLT relocation: {name}")
        # These odd symbol values name Thumb entry points; code starts one byte lower.
        for name, value in {
            "_ZN20CNotificationManager27m_OnUpdateNotiProgressBarCbEPv": (0x27217D, 12),
            "_ZN20CNotificationManager25m_OnUpdateNotiProgressBarEv": (0x26D219, 1520),
            "_ZN17CNotificationUtil26RequestQdDisplayOffSensingEv": (0x273BD9, 2476),
        }.items():
            if exported.get(name) != value:
                fail(f"symbol mismatch for {name}: {exported.get(name)!r}")

        # Thunk -> tick handler, then counter increment, display formatting and tick-60 test.
        thunk = decode(elf, 0x27217C, 12)
        expect(thunk, 0x272180, "bl", "0x26d218")
        create = decode(elf, 0x26CC44, 1492)
        expect(create, 0x26CD54, "movs", "#0x3c")
        expect(create, 0x26CD56, "mov.w", "#0x3e8")
        expect(create, 0x26CD60, "blx", "0x12696c")
        update = decode(elf, 0x26D218, 1520)
        expect(update, 0x26D2F8, "ldr.w", "#0xd4")
        expect(update, 0x26D306, "adds", "#1")
        expect(update, 0x26D308, "str.w", "#0xd4")
        expect(update, 0x26D348, "movs", "#0x3c")
        expect(update, 0x26D3B8, "cmp", "#0x3c")
        expect(update, 0x26D3BA, "beq.w", "0x26d540")
        expect(update, 0x26D5B2, "bl", "0x273bd8")

        # The formatter is actual 60-counter / quotient / remainder code.
        formatter = decode(elf, 0x2727F8, 344)
        expect(formatter, 0x27286C, "sub.w", "r1, r6, sb")
        expect(formatter, 0x27287C, "movs", "#0x3c")
        expect(formatter, 0x2728A6, "mls", "r1, r6, r2, r1")

        # Explicit Start Now shares the same wrapper and immediately destroys the timer.
        events = decode(elf, 0x26E988, 6056)
        expect(events, 0x26F724, "bl", "0x273bd8")
        expect(events, 0x26F72A, "bl", "0x26c834")

        # Wrapper makes an imported off-sensing request and branches on its return.
        wrapper = decode(elf, 0x273BD8, 2476)
        expect(wrapper, 0x273CC6, "blx", "0x125d44")
        expect(wrapper, 0x273CCA, "cmp", "r0, #0")
        expect(wrapper, 0x273CCC, "bne.w", "0x27412e")

    print("PASS: hash, symbols, 60-tick CFG, expiry/button calls, and return branch verified offline")


if __name__ == "__main__":
    main()
