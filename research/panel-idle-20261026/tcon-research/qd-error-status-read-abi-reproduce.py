#!/usr/bin/env python3
"""Offline, hash-gated reproducer for qd-error-status-read-abi.md.

This script reads only the four copied ELF files named below.  It has no
network, device, /proc, root-agent, ioctl, or TV access.
"""
from __future__ import annotations

import hashlib
import importlib.util
import struct
from pathlib import Path

try:
    from capstone import CS_ARCH_ARM, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile
except ModuleNotFoundError as exc:
    raise SystemExit(
        f"missing offline prerequisite {exc.name}; "
        "validated with PYTHONPATH=/tmp/tcon-capstone"
    ) from exc


BASE = Path(__file__).resolve().parents[1]
FILES = {
    "libave": (
        BASE / "binaries/libave.so.0.1",
        "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777",
    ),
    "driver": (
        BASE / "binaries/tztv_frc_tcon.ko",
        "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd",
    ),
    "api": (
        BASE / "binaries/tztv_frc_tcon_api.ko",
        "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6",
    ),
    "qdf": (
        BASE / "binaries/qdf_tcon.ko",
        "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63",
    ),
}


def require_prerequisites() -> None:
    missing = [name for name in ("capstone", "elftools") if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit(
            "missing offline prerequisites: "
            + ", ".join(missing)
            + "; validated with PYTHONPATH=/tmp/tcon-capstone"
        )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbol(elf: ELFFile, name: str):
    table = elf.get_section_by_name(".symtab")
    matches = table.get_symbol_by_name(name)
    assert matches and len(matches) == 1, (name, matches)
    return matches[0]


def section_bytes(path: Path, section_name: str) -> tuple[bytes, int]:
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        section = elf.get_section_by_name(section_name)
        assert section is not None, section_name
        return section.data(), int(section["sh_addr"])


def decode(path: Path, section_name: str, start: int, stop: int, arch: int, mode: int) -> list[str]:
    blob, base = section_bytes(path, section_name)
    assert base <= start < stop <= base + len(blob), (section_name, hex(start), hex(stop))
    decoder = Cs(arch, mode)
    rows = []
    for insn in decoder.disasm(blob[start - base : stop - base], start):
        rows.append(f"{insn.address:08x} {insn.bytes.hex():<10} {insn.mnemonic:<8} {insn.op_str}")
    return rows


def assert_hashes() -> None:
    for label, (path, expected) in FILES.items():
        actual = sha256(path)
        assert actual == expected, (label, actual, expected)
        print(f"HASH {label:7} {actual}")


def ioctl_shape() -> None:
    request = 0xC010749F
    direction = (request >> 30) & 3
    size = (request >> 16) & 0x3FFF
    kind = (request >> 8) & 0xFF
    number = request & 0xFF
    assert (direction, size, kind, number) == (3, 16, 0x74, 0x9F)
    print(f"IOCTL request=0x{request:08x} dir={direction} size={size} type=0x{kind:02x} nr=0x{number:02x}")


def libave_contract() -> None:
    path = FILES["libave"][0]
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        get_status = symbol(elf, "_Z27ave_tcon_get_err_det_statusPi")
        wrapper = symbol(elf, "_Z10tcon_ioctlmPv")
        assert (int(get_status["st_value"]), int(get_status["st_size"])) == (0x25D165, 164)
        assert (int(wrapper["st_value"]), int(wrapper["st_size"])) == (0x2AD831, 336)

        text = elf.get_section_by_name(".text")
        text_blob, text_base = text.data(), int(text["sh_addr"])
        at = lambda address, count: text_blob[address - text_base : address - text_base + count]
        assert at(0x25D174, 8) == bytes.fromhex("47f29f40ccf21000")
        assert at(0x25D188, 10) == bytes.fromhex("1f23c7e9013530f6e6ee")
        assert at(0x25D192, 8) == bytes.fromhex("bb682360041e0bdb")
        assert at(0x2AD8A0, 16) == bytes.fromhex("dff8c8800221f8444046e2f5e6ef0028")

        plt = elf.get_section_by_name(".plt")
        rel = elf.get_section_by_name(".rel.plt")
        dynsym = elf.get_section(rel["sh_link"])
        wanted = {}
        for index, relocation in enumerate(rel.iter_relocations()):
            address = int(plt["sh_addr"]) + 20 + 12 * index
            if address in (0x8D77C, 0x8DF5C, 0x90878):
                wanted[address] = dynsym.get_symbol(relocation["r_info_sym"]).name
        assert wanted == {
            0x8D77C: "ioctl",
            0x8DF5C: "_Z10tcon_ioctlmPv",
            0x90878: "_Z8ave_openPKci",
        }

        rodata = elf.get_section_by_name(".rodata")
        ro_blob, ro_base = rodata.data(), int(rodata["sh_addr"])
        device = b"/dev/tztv_tcon\0"
        device_address = ro_base + ro_blob.index(device)
        assert device_address == 0x5763BC

    print("LIBAVE getter=0x25d164 Thumb request-word0=31 output-word1=+4")
    print("LIBAVE wrapper=tcon_ioctl; opens /dev/tztv_tcon with flags=2 when cached fd<0; then ioctl")
    print("-- libave getter")
    print("\n".join(decode(path, ".text", 0x25D164, 0x25D19A, CS_ARCH_ARM, CS_MODE_THUMB)))
    print("-- libave fd/ioctl wrapper")
    print("\n".join(decode(path, ".text", 0x2AD850, 0x2AD8B4, CS_ARCH_ARM, CS_MODE_THUMB)))


def driver_contract() -> None:
    path = FILES["driver"][0]
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        open_symbol = symbol(elf, "fop_tcon_open")
        native = symbol(elf, "fop_tcon_ioctl")
        compat = symbol(elf, "fop_tcon_compat_ioctl")
        fops = symbol(elf, "tcon_drv_fops")
        callback = symbol(elf, "tztv_tcon_ioctl")
        assert (int(open_symbol["st_value"]), int(open_symbol["st_size"])) == (0x26A8, 8)
        assert (int(native["st_value"]), int(native["st_size"])) == (0x28E8, 400)
        assert (int(compat["st_value"]), int(compat["st_size"])) == (0x2758, 400)
        assert (int(fops["st_value"]), int(fops["st_size"])) == (0x890, 264)
        assert int(callback["st_value"]) == 0x40 and callback["st_shndx"] == 23

        text = elf.get_section_by_name(".text")
        assert text.data()[0x26A8:0x26B0] == bytes.fromhex("00008052c0035fd6")

        rodata = elf.get_section_by_name(".rodata")
        assert rodata.data()[0x890 : 0x890 + 264] == bytes(264)
        rela = elf.get_section_by_name(".rela.rodata")
        symtab = elf.get_section(rela["sh_link"])
        rows = {}
        for relocation in rela.iter_relocations():
            off = int(relocation["r_offset"])
            if 0x890 <= off < 0x890 + 264:
                rows[off] = symtab.get_symbol(relocation["r_info_sym"]).name
        assert rows == {
            0x890: "__this_module",
            0x8E0: "fop_tcon_ioctl",
            0x8E8: "fop_tcon_compat_ioctl",
            0x900: "fop_tcon_open",
        }

        # The platform probe calls get_fn_ad, which resolves the exported API
        # callback name and stores its result in BSS+0x40.
        strings = elf.get_section_by_name(".rodata.str1.8").data()
        assert strings[0x4DC8 : 0x4DC8 + 22] == b"fop_tcon_ioctl_export\0"
        text_blob = text.data()
        unlikely = elf.get_section_by_name(".text.unlikely").data()
        assert struct.unpack_from("<I", unlikely, 0x2F30)[0] == 0x94000000
        assert struct.unpack_from("<I", text_blob, 0x5488)[0] == 0xF9002261

        # Bind the call/store arithmetic rather than treating those raw words
        # as self-describing: x19 is the .bss base, the literal is exact, and
        # the preceding call really is resolve_symbol.
        def relocations(section_name: str, wanted_offsets: set[int]):
            relocation_section = elf.get_section_by_name(section_name)
            relocation_symbols = elf.get_section(relocation_section["sh_link"])
            found = {}
            for relocation in relocation_section.iter_relocations():
                off = int(relocation["r_offset"])
                if off in wanted_offsets:
                    target = relocation_symbols.get_symbol(relocation["r_info_sym"])
                    found[off] = (
                        target.name,
                        target["st_shndx"],
                        int(relocation["r_addend"]),
                        int(relocation.entry["r_info_type"]),
                    )
            return found

        assert relocations(".rela.text.unlikely", {0x2F30}) == {
            0x2F30: ("get_fn_ad", 3, 0, 283),
        }
        assert relocations(".rela.text", {0x5160, 0x5188, 0x546C, 0x5470, 0x5478}) == {
            0x5160: ("", 23, 0, 275),       # ADRP .bss
            0x5188: ("", 23, 0, 277),       # ADD .bss
            0x546C: ("", 13, 0x4DC8, 275),  # ADRP exact resolver string
            0x5470: ("", 13, 0x4DC8, 277),  # ADD exact resolver string
            0x5478: ("resolve_symbol", 3, 0, 283),
        }

    print("DRIVER fops relocations " + ", ".join(f"+0x{o-0x890:x}={n}" for o, n in rows.items()))
    print("DRIVER all other 264-byte fops slots are zero; no driver read/write/release callback")
    print("-- driver open")
    print("\n".join(decode(path, ".text", 0x26A8, 0x26B0, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)))
    print("-- driver compat ioctl dispatch")
    print("\n".join(decode(path, ".text", 0x2790, 0x27D0, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)))
    print("-- driver native ioctl dispatch")
    print("\n".join(decode(path, ".text", 0x2920, 0x2960, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)))


def api_contract() -> None:
    path = FILES["api"][0]
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        request = symbol(elf, "TCON_Request")
        export = symbol(elf, "fop_tcon_ioctl_export")
        assert (int(request["st_value"]), int(request["st_size"])) == (0xE7B0, 3288)
        assert (int(export["st_value"]), int(export["st_size"])) == (0x3048, 15912)

        rodata = elf.get_section_by_name(".rodata").data()
        index = 31 - 1
        displacement = struct.unpack_from("<h", rodata, 0x6A0 + 2 * index)[0]
        target = 0xE804 + 4 * displacement
        assert displacement == 0x107 and target == 0xEC20

        # Compat operation 0x9f takes the fallback at 0x37c8, preserving the
        # original 0xc010749f command for the common native dispatcher.
        compat_disp = struct.unpack_from("<h", rodata, 0x424 + 2 * (0x9F - 1))[0]
        assert compat_disp == -8 and 0x37E8 + 4 * compat_disp == 0x37C8

        text = elf.get_section_by_name(".text").data()
        words = lambda address, count: struct.unpack_from("<" + "I" * count, text, address)
        assert words(0x3BE4, 7) == (
            0xD2800202,  # size 16
            0xAA1503E0,
            0x94000000,  # __arch_copy_from_user relocation
            0xD503201F,
            0xB5000260,
            0xAA1503E0,
            0x94000000,  # TCON_Request relocation
        )
        assert words(0x67A4, 4) == (
            0xD2800202,  # size 16
            0xAA1503E1,
            0x94000000,  # __arch_copy_to_user relocation
            0xD503201F,
        )
        assert words(0xEC20, 8) == (
            0x90000000,
            0xF9400000,
            0xB4003C60,
            0xF941F401,  # callback at interface+1000 (0x3e8)
            0xB4003C21,
            0x91001260,  # request+4 output address
            0xD63F0020,
            0x17FFFEE9,
        )

    print("API compat nr0x9f falls through unchanged; copy-in=16 and copy-out=16")
    print("API operation31 target=0xec20; interface slot=+0x3e8; callback argument=request+4")
    print("-- API common ioctl copy path")
    print("\n".join(decode(path, ".text", 0x3B78, 0x3C50, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)))
    print("-- API operation31")
    print("\n".join(decode(path, ".text", 0xEC20, 0xEC40, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)))
    print("-- API 16-byte copy-out")
    print("\n".join(decode(path, ".text", 0x678C, 0x67C4, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)))


def qdf_contract() -> None:
    path = FILES["qdf"][0]
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        status = symbol(elf, "QDFTcon_GetErrDetStatus")
        assert (int(status["st_value"]), int(status["st_size"])) == (0xA000, 316)
        expected_bss = {
            "m_suspend_status": 0x0,
            "m_tcon_state": 0x10,
            "m_err_debug": 0x28,
            "tcon_flash_update": 0x6C,
            "m_command_skip": 0x10C,
            "m_err_det_status_debug_status": 0x120,
        }
        for name, expected in expected_bss.items():
            assert int(symbol(elf, name)["st_value"]) == expected, name

        text = elf.get_section_by_name(".text").data()
        words = lambda address, count: struct.unpack_from("<" + "I" * count, text, address)
        assert words(0xA030, 5) == (
            0xD2800100,  # low command word 8
            0xAA1303E1,
            0xF2DE7000,  # high 0xf380 => 0xf38000000008
            0x90000014,
            0x97FFFED2,  # m_read_cmd
        )
        assert words(0x9C48, 5) == (
            0x91016BE2,
            0x528000C3,  # tx length6
            0x52800EC1,  # address0x76
            0x528000A0,  # adapter5
            0xD63F0080,  # raw write callback
        )
        assert words(0x9C6C, 5) == (
            0x91015BE2,
            0x52800083,  # rx length4
            0x52800EC1,
            0x528000A0,
            0xD63F0080,  # raw read callback
        )
        assert words(0x9CF0, 7) == (
            0x91015BE4,
            0x91016BE2,
            0x52800085,  # rx length4
            0x528000C3,  # tx length6
            0x52800EC1,
            0x528000A0,
            0xD63F00C0,  # combined read callback
        )

        init_rela = elf.get_section_by_name(".rela.init.text")
        init_symtab = elf.get_section(init_rela["sh_link"])
        init_text = elf.get_section_by_name(".init.text").data()
        assert struct.unpack_from("<I", init_text, 0x1B0)[0] == 0x910F8274  # x20=x19+0x3e0
        assert struct.unpack_from("<I", init_text, 0x2E8)[0] == 0xA9000683  # slots+0x3e0/+0x3e8
        registration = {}
        for relocation in init_rela.iter_relocations():
            off = int(relocation["r_offset"])
            if off in (0x2E0, 0x2E4):
                registration[off] = init_symtab.get_symbol(relocation["r_info_sym"]).name
        assert registration == {0x2E0: "QDFTcon_GetErrDetStatus", 0x2E4: "QDFTcon_GetErrDetStatus"}

    print("QDF registers GetErrDetStatus at interface+0x3e8")
    print("QDF fixed command=0xf38000000008; transport adapter5 address0x76 tx6/rx4")
    print("QDF gates include flash-update, suspend, command-skip, and TCON-state; skipped paths can leave output unchanged")
    print("QDF debug enable=BSS+0x28; override value=BSS+0x120")
    print("-- QDF status getter")
    print("\n".join(decode(path, ".text", 0xA000, 0xA13C, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)))
    print("-- QDF locking read helper")
    print("\n".join(decode(path, ".text", 0x9B88, 0x9E74, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)))


def main() -> None:
    require_prerequisites()
    assert_hashes()
    ioctl_shape()
    libave_contract()
    driver_contract()
    api_contract()
    qdf_contract()
    print("PASS: exact local ABI/call-path assertions satisfied; no target access performed")


if __name__ == "__main__":
    main()
