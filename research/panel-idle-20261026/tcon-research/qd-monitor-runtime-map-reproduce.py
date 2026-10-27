#!/usr/bin/env python3
"""Offline, hash-gated checks for the QD monitor runtime-state map."""
from pathlib import Path
import hashlib
import struct

from capstone import CS_ARCH_ARM, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "binaries/libave.so.0.1"
EXPECTED = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"
STATE = 0x005BFC20


def symbols(elf):
    result = {}
    for section in elf.iter_sections():
        if section["sh_type"] in ("SHT_SYMTAB", "SHT_DYNSYM"):
            for symbol in section.iter_symbols():
                if symbol.name:
                    result[symbol.name] = symbol["st_value"]
    return result


def main():
    data = SOURCE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED
    with SOURCE.open("rb") as handle:
        elf = ELFFile(handle)
        named = symbols(elf)
        required = {
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE11err_det_cnt": STATE + 0x3C,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE11vdd_det_cnt": STATE + 0x40,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE19elvdd_i2c_error_cnt": STATE + 0x44,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE18err_det_reboot_try": STATE + 0x48,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE18vdd_det_reboot_try": STATE + 0x4C,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE20elvdd_i2c_reboot_try": STATE + 0x50,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE11si_ok_count": STATE + 0x54,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE11qd_tcon_off": STATE + 0x58,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE17onetime_execution": STATE + 0x5C,
            "_ZZ39ave_tcon_monitor_ddr_pmic_check_qd_oledvE14fault_occurred": STATE + 0x68,
            "_ZZ22ave_tcon_monitor_onoffiE14pre_monitor_on": 0x005BFCD0,
            "g_tcon_monitor_restart": 0x005BFCE8,
            "g_tcon_monitor_on": 0x005BFCEC,
        }
        for name, address in required.items():
            assert named.get(name) == address, (name, hex(named.get(name, -1)), hex(address))
        got_relocations = {}
        for section in elf.iter_sections():
            if section["sh_type"] == "SHT_REL":
                linked = elf.get_section(section["sh_link"])
                for relocation in section.iter_relocations():
                    symbol = linked.get_symbol(relocation["r_info_sym"])
                    got_relocations[relocation["r_offset"]] = (
                        relocation["r_info_type"], symbol.name, symbol["st_value"])
        assert got_relocations.get(0x005A7370) == (
            21, "g_tcon_monitor_restart", 0x005BFCE8)
        # The initial restart gate constructs the libave GOT base in r4.
        assert struct.unpack_from("<I", data, 0x269C40)[0] == 0x0033A9D8
        assert 0x269628 + struct.unpack_from("<I", data, 0x269C40)[0] == 0x005A4000
        assert struct.unpack_from("<I", data, 0x269C44)[0] == 0x00003370
        assert 0x005A4000 + struct.unpack_from("<I", data, 0x269C44)[0] == 0x005A7370
        assert struct.unpack_from("<I", data, 0x269C48)[0] == 0x003565DE
        assert 0x269642 + struct.unpack_from("<I", data, 0x269C48)[0] == STATE
        text = elf.get_section_by_name(".text")
        decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        def listing(address, length):
            start = address - text["sh_addr"]
            return [(i.address, i.mnemonic, i.op_str) for i in decoder.disasm(text.data()[start:start + length], address)]
        qd = listing(0x26963A, 0x50)
        assert (0x26963E, "add", "r3, pc") in qd
        assert (0x269640, "ldr", "r2, [r3, #0x58]") in qd
        assert (0x269786, "str", "r2, [r3, #0x58]") in listing(0x269776, 0x24)
        initial_gate = listing(0x269616, 0x28)
        assert (0x269616, "ldr.w", "r4, [pc, #0x628]") in initial_gate
        assert (0x269624, "add", "r4, pc") in initial_gate
        assert (0x26962C, "ldr.w", "r3, [pc, #0x614]") in initial_gate
        assert (0x269630, "ldr", "r5, [r4, r3]") in initial_gate
        assert (0x269632, "ldr", "r3, [r5]") in initial_gate
        assert (0x269634, "cmp", "r3, #1") in initial_gate
        assert (0x269636, "beq.w", "#0x269a54") in initial_gate
        clear_gate = listing(0x269A48, 0x0C)
        assert (0x269A48, "ldr", "r3, [pc, #0x1f8]") in clear_gate
        assert (0x269A4A, "ldr", "r5, [r4, r3]") in clear_gate
        assert (0x269A4C, "ldr", "r3, [r5]") in clear_gate
        assert (0x269A4E, "cmp", "r3, #1") in clear_gate
        assert (0x269A50, "bne.w", "#0x26963a") in clear_gate
        clear = listing(0x269A70, 0x20)
        assert (0x269A76, "str", "r0, [r4, #0x3c]") in clear
        assert (0x269A7A, "str", "r0, [r5]") in clear
        assert (0x269A88, "strd", "r0, r0, [r4, #0x58]") in clear
        onoff = listing(0x26B17C, 0x2A)
        assert (0x26B190, "str", "r0, [r4]") in onoff
        assert (0x26B19A, "str.w", "r0, [r1, #0xb0]") in onoff
        assert (0x26B1A0, "str", "r4, [r3]") in onoff
    print("PASS: libave QD monitor state/counter/latch and monitor-control addresses")


if __name__ == "__main__":
    main()
