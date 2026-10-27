#!/usr/bin/env python3
"""Offline hash-gated checks for qd-current-fault-gpio-read-abi.md.

Reads only four already-copied ELF files. It has no target, network, root,
device, ioctl, GPIO, or /proc access. Landmark checks are not emulation.
"""
from pathlib import Path
import hashlib
import importlib.util
import struct

try:
    from capstone import Cs, CS_ARCH_ARM, CS_ARCH_ARM64, CS_MODE_THUMB, CS_MODE_LITTLE_ENDIAN
    from elftools.elf.elffile import ELFFile
except ModuleNotFoundError as exc:
    raise SystemExit(f"missing {exc.name}; use PYTHONPATH=/tmp/tcon-capstone") from exc

BASE = Path(__file__).resolve().parents[1]
FILES = {
    "ave": (BASE / "binaries/libave.so.0.1",
            "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"),
    "driver": (BASE / "binaries/tztv_frc_tcon.ko",
               "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd"),
    "api": (BASE / "binaries/tztv_frc_tcon_api.ko",
            "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6"),
    "qdf": (BASE / "binaries/qdf_tcon.ko",
            "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"),
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


class Source:
    def __init__(self, key):
        self.key = key
        self.path, expected = FILES[key]
        require(hashlib.sha256(self.path.read_bytes()).hexdigest() == expected,
                key + " hash")
        self.handle = self.path.open("rb")
        self.elf = ELFFile(self.handle)
        self.symbols = {s.name: s for sec in self.elf.iter_sections()
                        if sec["sh_type"] == "SHT_SYMTAB"
                        for s in sec.iter_symbols() if s.name}
        self.relocations = {}
        for sec in self.elf.iter_sections():
            if sec["sh_type"] not in ("SHT_REL", "SHT_RELA"):
                continue
            syms = self.elf.get_section(sec["sh_link"])
            target = self.elf.get_section(sec["sh_info"]).name
            for rel in sec.iter_relocations():
                sym = syms.get_symbol(rel["r_info_sym"])
                addend = int(rel["r_addend"]) if sec["sh_type"] == "SHT_RELA" else 0
                self.relocations[(target, int(rel["r_offset"]))] = (sym.name, addend)
        self.plt = {}
        rel = self.elf.get_section_by_name(".rel.plt")
        if rel:
            syms = self.elf.get_section(rel["sh_link"])
            base = int(self.elf.get_section_by_name(".plt")["sh_addr"]) + 20
            self.plt = {base + 12 * index: syms.get_symbol(row["r_info_sym"]).name
                        for index, row in enumerate(rel.iter_relocations())}

    def symbol(self, name, value, size):
        row = self.symbols[name]
        require((int(row["st_value"]), int(row["st_size"])) == (value, size), name)

    def rows(self, section, start, stop, thumb=False):
        sec = self.elf.get_section_by_name(section)
        base = int(sec["sh_addr"])
        blob = sec.data()[start - base:stop - base]
        decoder = Cs(CS_ARCH_ARM if thumb else CS_ARCH_ARM64,
                     CS_MODE_THUMB if thumb else CS_MODE_LITTLE_ENDIAN)
        rows = {i.address: (i.mnemonic, i.op_str) for i in decoder.disasm(blob, start)}
        require(rows, f"empty decode {self.key} {section}")
        return rows


def has(rows, address, mnemonic, operands):
    require(rows.get(address) == (mnemonic, operands),
            (hex(address), rows.get(address), (mnemonic, operands)))


def main():
    require(importlib.util.find_spec("capstone") is not None, "capstone")
    sources = {key: Source(key) for key in FILES}
    ave, driver, api, qdf = (sources[k] for k in ("ave", "driver", "api", "qdf"))

    request = 0xC010749F
    require(((request >> 30) & 3, (request >> 16) & 0x3FFF,
             (request >> 8) & 0xFF, request & 0xFF) == (3, 16, 0x74, 0x9F),
            "ioctl shape")

    # ARM32 public wrapper: word0=0x1d, word1=0, call, then copy word1 out
    # before inspecting the signed ioctl result.
    ave.symbol("_Z26ave_tcon_get_err_det_faultPi", 0x25D01D, 164)
    ar = ave.rows(".text", 0x25D01C, 0x25D0A4, True)
    for expected in ((0x25D02C, "movw", "r0, #0x749f"),
                     (0x25D030, "movt", "r0, #0xc010"),
                     (0x25D040, "movs", "r3, #0x1d"),
                     (0x25D042, "strd", "r3, r5, [r7, #4]"),
                     (0x25D046, "blx", "#0x8df5c"),
                     (0x25D04A, "ldr", "r3, [r7, #8]"),
                     (0x25D04C, "str", "r3, [r4]"),
                     (0x25D04E, "subs", "r4, r0, #0")):
        has(ar, *expected)
    require(ave.plt[0x8DF5C] == "_Z10tcon_ioctlmPv", "AVE ioctl PLT")

    # Character device: open is a no-op success; fops has no release/read/write.
    driver.symbol("fop_tcon_open", 0x26A8, 8)
    dr = driver.rows(".text", 0x26A8, 0x26B0)
    has(dr, 0x26A8, "mov", "w0, #0")
    has(dr, 0x26AC, "ret", "")
    fops = driver.elf.get_section_by_name(".rodata").data()[0x890:0x998]
    require(fops == bytes(264), "fops raw body")
    fops_reloc = {off: name for (sec, off), (name, _) in driver.relocations.items()
                  if sec == ".rodata" and 0x890 <= off < 0x998}
    require(fops_reloc == {0x890: "__this_module", 0x8E0: "fop_tcon_ioctl",
                           0x8E8: "fop_tcon_compat_ioctl", 0x900: "fop_tcon_open"},
            "fops relocation inventory")
    compat = driver.rows(".text", 0x2790, 0x27C0)
    has(compat, 0x27AC, "mov", "w0, w20")
    has(compat, 0x27B0, "mov", "x1, x21")
    has(compat, 0x27B4, "mov", "w2, #1")
    has(compat, 0x27B8, "blr", "x3")

    # API 16-byte copy path and operation-0x1d dispatch to interface+0x3d0.
    api.symbol("TCON_Request", 0xE7B0, 3288)
    api.symbol("fop_tcon_ioctl_export", 0x3048, 15912)
    req = api.rows(".text", 0x3BE0, 0x3C10)
    has(req, 0x3BE4, "mov", "x2, #0x10")
    has(req, 0x3BFC, "bl", "#0x3bfc")
    copyout = api.rows(".text", 0x6790, 0x67B4)
    has(copyout, 0x67A4, "mov", "x2, #0x10")
    ro = api.elf.get_section_by_name(".rodata").data()
    target = 0xE804 + 4 * struct.unpack_from("<h", ro, 0x6A0 + 2 * (0x1D - 1))[0]
    require(target == 0xF198, "operation 0x1d jump target")
    op = api.rows(".text", 0xF198, 0xF1B8)
    has(op, 0xF1A4, "ldr", "x1, [x0, #0x3d0]")
    has(op, 0xF1AC, "add", "x0, x19, #4")
    has(op, 0xF1B0, "blr", "x1")
    missing = api.rows(".text", 0xF35C, 0xF36C)
    has(missing, 0xF364, "mov", "w0, #0")

    # QDF gate/provider/debug/output dataflow and exact init registration.
    qdf.symbol("QDFTcon_GetErrDetFault", 0x5608, 284)
    qr = qdf.rows(".text", 0x5608, 0x5724)
    for expected in ((0x5624, "ldr", "w19, [x20, #4]"),
                     (0x562C, "cbz", "w19, #0x56ec"),
                     (0x5638, "cbz", "x1, #0x5680"),
                     (0x563C, "add", "x0, sp, #0x3c"),
                     (0x5640, "blr", "x1"),
                     (0x5644, "mov", "w19, w0"),
                     (0x5648, "cbnz", "w0, #0x5684"),
                     (0x564C, "ldr", "w1, [sp, #0x3c]"),
                     (0x5658, "ldr", "w0, [x20, #0x28]"),
                     (0x565C, "cmp", "w0, #1"),
                     (0x5664, "ldr", "w1, [x20, #0x11c]"),
                     (0x5668, "str", "w1, [x21]"),
                     (0x566C, "mov", "w0, w19"),
                     (0x56B0, "mov", "w1, #0"),
                     (0x571C, "mov", "w1, #0"),
                     (0x5720, "b", "#0x5668")):
        has(qr, *expected)
    require(qdf.relocations[(".text", 0x5630)][0] ==
            qdf.relocations[(".text", 0x5634)][0] ==
            "tztv_frc_tcon_read_err_det_status", "provider import")
    require(qdf.relocations[(".init.text", 0x2C8)] == ("QDFTcon_GetErrDetFault", 0),
            "QDF init relocation")
    init = qdf.rows(".init.text", 0x2C8, 0x330)
    has(init, 0x328, "str", "x5, [x19, #0x3d0]")

    # Provider: DT lookup/cache, temporary ownership, direction-input, raw read,
    # caller store, and free. Direction/get return does not replace saved request status.
    driver.symbol("_tztv_frc_tcon_read_err_det_status", 0x1AF0, 316)
    pr = driver.rows(".text", 0x1AF0, 0x1C30)
    for expected in ((0x1B0C, "ldr", "w0, [x19, #0xa0]"),
                     (0x1B34, "bl", "#0x1b34"),
                     (0x1B38, "str", "w0, [x19, #0xa0]"),
                     (0x1B90, "bl", "#0x1b90"),
                     (0x1B94, "mov", "w20, w0"),
                     (0x1B98, "cbnz", "w0, #0x1bd8"),
                     (0x1BA4, "bl", "#0x1ba4"),
                     (0x1BB0, "bl", "#0x1bb0"),
                     (0x1BB4, "mov", "w1, w0"),
                     (0x1BBC, "str", "w1, [x21]"),
                     (0x1BC0, "bl", "#0x1bc0"),
                     (0x1BC4, "mov", "w0, w20")):
        has(pr, *expected)
    expected_calls = {0x1B34: "of_get_named_gpio_flags", 0x1B5C: "printk",
                      0x1B7C: "printk", 0x1B90: "gpio_request",
                      0x1BA0: "gpio_to_desc", 0x1BA4: "gpiod_direction_input",
                      0x1BAC: "gpio_to_desc", 0x1BB0: "gpiod_get_raw_value_cansleep",
                      0x1BC0: "gpio_free", 0x1BFC: "printk",
                      0x1C10: "printk", 0x1C24: "printk"}
    actual_calls = {off: name for (sec, off), (name, _) in driver.relocations.items()
                    if sec == ".text" and 0x1AF0 <= off < 0x1C30 and name}
    require(actual_calls == expected_calls, (actual_calls, expected_calls))
    strings = driver.elf.get_section_by_name(".rodata.str1.8").data()
    require(strings[0x18C8:0x18D8] == b"samsung,err_det\0", "DT property")
    require(strings[0x1930:0x1938] == b"err_det\0", "request label")

    # Manual boundary checks make explicit the two most important ambiguities.
    def qdf_model(power, callback_status, raw, debug=False, debug_word=0):
        if not power:
            return 0, 0, False
        if callback_status != 0:
            return callback_status, (debug_word if debug else 0), True
        return 0, (debug_word if debug else raw), True
    require(qdf_model(0, 0, 1) == (0, 0, False), "power-zero skip")
    require(qdf_model(1, 0, -22) == (0, -22, True), "signed raw preservation")
    require(qdf_model(1, 0, 0, True, 1) == (0, 1, True), "debug override")

    print("PASS exact four ELFs; ARM32 op0x1d ABI; compat/API/QDF/provider chain")
    print("PASS provider calls limited to DT/cache, GPIO request/direction/raw-read/free, and logs")
    print("BOUNDARY zero=power-skip-or-low; nonzero=raw-or-debug; preserve signed word and logs")
    print("NO TARGET ACCESS; landmark assertions plus manual model, not execution/emulation")


if __name__ == "__main__":
    main()
