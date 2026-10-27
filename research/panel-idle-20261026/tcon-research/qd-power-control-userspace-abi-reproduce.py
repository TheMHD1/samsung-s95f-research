#!/usr/bin/env python3
"""Offline exact-build power-control ABI checks; never accesses a device."""
from pathlib import Path
import importlib.util
import struct

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("read_abi", HERE / "qd-current-fault-gpio-read-abi-reproduce.py")
abi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(abi)
Source, require, has = abi.Source, abi.require, abi.has


def main():
    ave, api, qdf = (Source(k) for k in ("ave", "api", "qdf"))
    ave.symbol("_Z29ave_tcon_qd_set_power_controli", 0x25c2e1, 156)
    ave.symbol("ave_api_set_qd_tcon_power_control", 0x291e19, 1024)
    rows = ave.rows(".text", 0x25c2e0, 0x25c320, True)
    for insn in [(0x25c2e2, "mov", "r3, r0"),
                 (0x25c2ec, "adds", "r1, r7, #4"),
                 (0x25c2ee, "movw", "r0, #0x749f"),
                 (0x25c2f2, "movt", "r0, #0xc010"),
                 (0x25c2f6, "str", "r3, [r7, #8]"),
                 (0x25c304, "movs", "r3, #0x29"),
                 (0x25c306, "str", "r3, [r7, #4]"),
                 (0x25c308, "blx", "#0x8df5c")]:
        has(rows, *insn)
    require(ave.plt[0x8df5c] == "_Z10tcon_ioctlmPv", "ioctl PLT")
    require(ave.plt[0x8c5f4] == "_Z29ave_tcon_qd_set_power_controli", "public PLT")
    has(ave.rows(".text", 0x291e78, 0x291e80, True), 0x291e7c, "blx", "#0x8c5f4")
    rodata = api.elf.get_section_by_name(".rodata").data()
    targets = []
    for table, origin in [(0x6a0, 0xe804), (0x768, 0xf474)]:
        entry = struct.unpack_from("<h", rodata, table + 40 * 2)[0]
        target = origin + 4 * entry
        require(target == 0xed80, "operation41 table target")
        targets.append(hex(target))
    rows = api.rows(".text", 0xed80, 0xeda0)
    for insn in [(0xed88, "cbz", "x0, #0xf35c"),
                 (0xed8c, "ldr", "x1, [x0, #0x458]"),
                 (0xed90, "cbz", "x1, #0xf35c"),
                 (0xed94, "ldr", "w0, [x19, #4]"),
                 (0xed98, "blr", "x1")]:
        has(rows, *insn)
    require(api.relocations[(".text", 0xed80)] == ("", 0x620), "API BSS reference")
    has(api.rows(".text", 0xf35c, 0xf364), 0xf35c, "mov", "w0, #0")
    has(api.rows(".text", 0x3160, 0x3170), 0x3160, "mov", "x0, x20")
    has(api.rows(".text", 0x3c08, 0x3c0c), 0x3c08, "sxtw", "x20, w0")
    has(api.rows(".text", 0x67c0, 0x67c4), 0x67c0, "b", "#0x3160")
    require(api.relocations[(".text", 0x3bfc)][0] == "TCON_Request", "request call")
    require(api.relocations[(".text", 0x67ac)][0] == "__arch_copy_to_user", "copy back")
    require(api.relocations[(".text", 0x7c5c)] == ("", 0x620), "binding BSS reference")
    require(qdf.relocations[(".init.text", 0x454)][0] == "QDFTcon_SetQdTconPowerControl", "power callback")
    has(qdf.rows(".init.text", 0x484, 0x488), 0x484, "str", "x8, [x19, #0x458]")
    require(qdf.relocations[(".init.text", 0x5c0)][0] == "map_tcon_functions", "table registration")
    qdf.symbol("QDFTcon_SetQdTconPowerControl", 0x11c48, 304)
    rows = qdf.rows(".text", 0x11cdc, 0x11cf4)
    for insn in [(0x11cdc, "mov", "w0, #0"), (0x11ce0, "bl", "#0x11848"),
                 (0x11ce4, "mov", "w19, w0"), (0x11ce8, "mov", "w0, #1"),
                 (0x11cec, "bl", "#0x11848"), (0x11cf0, "orr", "w0, w19, w0")]:
        has(rows, *insn)
    print("PASS: exact source hashes, ARM wrapper, both dispatch tables, callback binding,")
    print("      callback result propagation, missing-callback zero, off/on sequence.")
    print("No target action; static landmarks are not runtime binding or physical recovery.")


if __name__ == "__main__":
    main()
