#!/usr/bin/env python3
"""Hash-gated, offline landmarks for DRM histogram console output.

This opens only the copied sdp_drm.ko.  It does not access a TV, kernel,
device node, network, or process state.  The checks are static landmarks, not
an execution trace or a definition of the histogram units.
"""
from pathlib import Path
import hashlib

try:
    from elftools.elf.elffile import ELFFile
except ModuleNotFoundError as exc:
    raise SystemExit(f"missing {exc.name}; use PYTHONPATH=/tmp/tcon-capstone") from exc


HERE = Path(__file__).resolve().parent
MODULE = HERE.parent / "binaries" / "sdp_drm.ko"
MODULE_SHA256 = "d1016cf5b72f86a1623b231d96dc944082263a70d3602d859f993d751bfdf881"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    require(MODULE.is_file(), f"missing {MODULE}")
    require(hashlib.sha256(MODULE.read_bytes()).hexdigest() == MODULE_SHA256,
            "sdp_drm.ko hash")
    with MODULE.open("rb") as handle:
        elf = ELFFile(handle)
        symtab = elf.get_section_by_name(".symtab")
        symbols = {symbol.name: symbol for symbol in symtab.iter_symbols()
                   if symbol.name}
        expected_symbols = {
            "__dp_isr_queue_work_thrd": (0x1B008, 4128),
            "__get_hist_val": (0x204D8, 108),
            "sdp_dp_input_print_hist_analyze": (0x22E40, 432),
            "dp_capture_get_capt_frame_crop": (0x2D600, 1568),
            "sdp_dp_post_print_hist": (0x48BD0, 820),
            "sdp_dp_post_print_hist_de_ve": (0x48F08, 696),
        }
        for name, expected in expected_symbols.items():
            symbol = symbols.get(name)
            require(symbol is not None, f"missing symbol {name}")
            got = (int(symbol["st_value"]), int(symbol["st_size"]))
            require(got == expected, f"symbol {name}: {got!r}")

        relocations = {}
        for section in elf.iter_sections():
            if section["sh_type"] != "SHT_RELA":
                continue
            target = elf.get_section(section["sh_info"]).name
            linked = elf.get_section(section["sh_link"])
            for relocation in section.iter_relocations():
                symbol = linked.get_symbol(relocation["r_info_sym"])
                relocations[(target, int(relocation["r_offset"]))] = symbol.name

        expected_calls = {
            (".text", 0x1B930): "sdp_dp_input_print_hist_analyze",
            (".text", 0x1B934): "sdp_dp_post_print_hist_de_ve",
            (".text", 0x2D898): "dp_drv_get_mute_status_with_auto_mute_cnt",
            (".text", 0x2D8A4): "sdp_dp_post_print_hist",
        }
        for location, name in expected_calls.items():
            require(relocations.get(location) == name,
                    f"relocation {location!r}: {relocations.get(location)!r}")

        # `__get_hist_val` encodes eight four-register groups: base+0..0x7c.
        text = elf.get_section_by_name(".text").data()
        def word(offset):
            return int.from_bytes(text[offset:offset + 4], "little")
        require([word(offset) for offset in (0x204EC, 0x204F0)] ==
                [0x11004015, 0x11024016], "histogram helper bounds")
        require([word(offset) for offset in (0x2050C, 0x20520, 0x2052C, 0x20530)] ==
                [0x12005800, 0x54FFFF01, 0x6B1602BF, 0x54FFFE41],
                "histogram helper mask/loops")

        # Register-base constructions in the formatter bodies, all statically
        # sourced from the copied module.
        expected_words = {
            0x22E44: 0x5284A480, 0x22E4C: 0x72A01920,  # 0xc9002524 (Y)
            0x22EC4: 0x5284B480, 0x22EC8: 0x72A01920,  # 0xc90025a4 (R)
            0x22F24: 0x5284C480, 0x22F28: 0x72A01920,  # 0xc9002624 (G)
            0x22F84: 0x5284D480, 0x22F88: 0x72A01920,  # 0xc90026a4 (B)
            0x48F20: 0x5281EF15, 0x48F24: 0x5281FF16,
            0x48F28: 0x72A00F55, 0x48F2C: 0x72A00F56,
            0x48F80: 0x52815380, 0x48F84: 0x72A00E00,
        }
        for offset, expected in expected_words.items():
            require(word(offset) == expected,
                    f"register construction {offset:#x}: {word(offset):#x}")

        strings = elf.get_section_by_name(".rodata.str1.8").data()
        for literal in (
            b"[HISTOGRAM INP(Y) : 08 level, low <-> high]",
            b"[HISTOGRAM INP(R) : 08 level, low <-> high]",
            b"[HISTOGRAM INP(G) : 08 level, low <-> high]",
            b"[HISTOGRAM INP(B) : 08 level, low <-> high]",
            b"[HISTOGRAM DE(SAC): 10 level, low <-> high]",
            b"[HISTOGRAM VE(CE_): 08 level, low <-> high]",
        ):
            require(literal in strings, f"format literal {literal!r}")

    print("PASS: exact sdp_drm.ko hash; named histogram functions and producer calls")
    print("PASS: helper 8x4 masked aggregate, formatter register constructions, log literals")
    print("BOUNDARY: static code only; no live call, unit, panel-output, cache, or cadence proof")


if __name__ == "__main__":
    main()
