#!/usr/bin/env python3
"""Offline, hash-gated checks for the libave PQE event consumer report.

This script reads only the acquired local ELF and capture artifacts.  It does
not open a device, contact the TV, or execute target code.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from capstone import CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB, Cs
    from elftools.elf.elffile import ELFFile
except ImportError as exc:
    raise SystemExit(
        "requires Capstone and pyelftools; use PYTHONPATH=/tmp/tcon-capstone"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
ELF_PATH = ROOT / "binaries/libave.so.0.1"
META_PATH = ROOT / "overnight/capacity-20261026t1648.onset/meta.txt"
VLOG_PATH = ROOT / "overnight/capacity-20261026t1648.onset/vlog-after.txt"
EXPECTED_SHA256 = "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777"

SYMBOLS = {
    "_ZL10poInstance": (0x005ADB5C, 4),
    "_ZN18RoseMVideoEnhancer6m_pShmE": (0x005B24E0, 4),
    "_ZTV18RoseMVideoEnhancer": (0x0059CBF0, 1364),
    "_ZTV21RoseMVideoEnhancerMNT": (0x0059D514, 1364),
    "_ZTV22RoseMVideoEnhancerWALL": (0x0059DA74, 1448),
    "_ZTV20RoseMVideoEnhancerEP": (0x0059E028, 1448),
    "_ZZN18RoseMVideoEnhancer11GetInstanceEvE8instance": (0x005B21A0, 824),
    "_ZZN21RoseMVideoEnhancerMNT11GetInstanceEvE8instance": (0x005BD6F4, 824),
    "_ZZN20RoseMVideoEnhancerEP11GetInstanceEvE8instance": (0x005BDEAC, 824),
    "_ZN20VideoEnhancerBuilder19GetInstanceEnhancerEv": (0x00093A29, 60),
    "_ZN18RoseMVideoEnhancer13CheckNeedDlsrEv": (0x000A1E55, 14),
    "_Z16pthd_ave_dlsr_pqPv": (0x002BCFD5, 660),
    "_Z23ave_pqe_dlsr_genre_infoiPjS_": (0x002B1259, 116),
    "_ZN18RoseMVideoEnhancer12SetDlsrClassEj": (0x000A3245, 128),
    "_ZN18RoseMVideoEnhancer25SetHDRBrightnessOptimizerEj": (0x000A32C5, 84),
    "_ZN18RoseMVideoEnhancer15AIGenreAddGenreEi": (0x000B782D, 26),
    "_ZN18RoseMVideoEnhancer22AIColorBoosterAddLevelEi": (0x000B9B3D, 120),
    "_ZN18RoseMVideoEnhancer13SetGSRFromNPUEi": (0x000A3AAD, 144),
    "_ZN11ave_dimming15SetObjectNumberEi": (0x00152509, 320),
    "_ZN9QDDimming15SetObjectNumberEi": (0x00172D2D, 84),
    "_ZN9QDDimming15m_CalcWeberGainEv": (0x001793D1, 236),
    "_ZN9QDDimming16m_SetFinalDuty2DEv": (0x00174261, 876),
    "_ZN9QDDimming15t_vSyncCallBackEv": (0x0017B35D, 864),
    "_ZN12QDDimmingMNT15t_vSyncCallBackEv": (0x0019B1C9, 868),
    "_ZN18RoseMVideoEnhancer14m_SetDlsrClassEv": (0x000AD199, 2100),
    "_ZN21RoseMVideoEnhancerMNT14m_SetDlsrClassEv": (0x0010B4B5, 1920),
    "_ZN17SamPictureMonitor27m_SetHDRBrightnessOptimizerEv": (0x000DFFF1, 308),
    "_ZN12DimmingShare31t_DimmingShare_GetWebberDimmingEPjP12ShareWeber_t": (
        0x00237661,
        528,
    ),
    "_ZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_t": (
        0x001C6275,
        252,
    ),
    "_ZZN12DimmingShare31t_DimmingShare_GetWebberDimmingEPjP12ShareWeber_tE11siWeberGain": (
        0x005AD94C,
        4,
    ),
    "_ZZN12DimmingShare31t_DimmingShare_GetWebberDimmingEPjP12ShareWeber_tE20siPreTargetWeberGain": (
        0x005BF6D0,
        4,
    ),
    "_ZZN12DimmingShare31t_DimmingShare_GetWebberDimmingEPjP12ShareWeber_tE10siWeberCnt": (
        0x005BF6D4,
        4,
    ),
}

PLT_EXPECTED = {
    0x0009089C: "_Z16get_product_typei",
    0x0008C024: "_ZN21RoseMVideoEnhancerMNT11GetInstanceEv",
    0x0008C108: "_ZN18RoseMVideoEnhancer11GetInstanceEv",
    0x0008EB08: "_ZN20RoseMVideoEnhancerEP11GetInstanceEv",
    0x0008C708: "prctl",
    0x0008D20C: "poll",
    0x0008D77C: "ioctl",
    0x0008D9E0: "open64",
    0x0008FD50: "usleep",
    0x0008B67C: "_Z23ave_pqe_dlsr_genre_infoiPjS_",
    0x0008BC58: "_Z20get_dimming_instancev",
    0x0008EF1C: "_ZN20VideoEnhancerBuilder19GetInstanceEnhancerEv",
}

RELOC_EXPECTED = {
    0x005A6A28: "_ZN18RoseMVideoEnhancer6m_pShmE",
    0x0059CDC4: "_ZN18RoseMVideoEnhancer13CheckNeedDlsrEv",
    0x0059CDC8: "_ZN18RoseMVideoEnhancer12SetDlsrClassEj",
    0x0059CDCC: "_ZN18RoseMVideoEnhancer15AIGenreAddGenreEi",
    0x0059CDD0: "_ZN18RoseMVideoEnhancer25SetHDRBrightnessOptimizerEj",
    0x0059CE54: "_ZN18RoseMVideoEnhancer22AIColorBoosterAddLevelEi",
    0x0059CE60: "_ZN18RoseMVideoEnhancer13SetGSRFromNPUEi",
    0x0059D6E8: "_ZN18RoseMVideoEnhancer13CheckNeedDlsrEv",
    0x0059D6EC: "_ZN18RoseMVideoEnhancer12SetDlsrClassEj",
    0x0059D6F0: "_ZN18RoseMVideoEnhancer15AIGenreAddGenreEi",
    0x0059D6F4: "_ZN18RoseMVideoEnhancer25SetHDRBrightnessOptimizerEj",
    0x0059D778: "_ZN18RoseMVideoEnhancer22AIColorBoosterAddLevelEi",
    0x0059D784: "_ZN18RoseMVideoEnhancer13SetGSRFromNPUEi",
    0x0059DC48: "_ZN18RoseMVideoEnhancer13CheckNeedDlsrEv",
    0x0059DC4C: "_ZN18RoseMVideoEnhancer12SetDlsrClassEj",
    0x0059DC50: "_ZN18RoseMVideoEnhancer15AIGenreAddGenreEi",
    0x0059DC54: "_ZN18RoseMVideoEnhancer25SetHDRBrightnessOptimizerEj",
    0x0059DCD8: "_ZN18RoseMVideoEnhancer22AIColorBoosterAddLevelEi",
    0x0059DCE4: "_ZN18RoseMVideoEnhancer13SetGSRFromNPUEi",
    0x0059E1FC: "_ZN18RoseMVideoEnhancer13CheckNeedDlsrEv",
    0x0059E200: "_ZN18RoseMVideoEnhancer12SetDlsrClassEj",
    0x0059E204: "_ZN18RoseMVideoEnhancer15AIGenreAddGenreEi",
    0x0059E208: "_ZN18RoseMVideoEnhancer25SetHDRBrightnessOptimizerEj",
    0x0059E28C: "_ZN18RoseMVideoEnhancer22AIColorBoosterAddLevelEi",
    0x0059E298: "_ZN18RoseMVideoEnhancer13SetGSRFromNPUEi",
    0x0059D020: "_ZN18RoseMVideoEnhancer14m_SetDlsrClassEv",
    0x0059D944: "_ZN21RoseMVideoEnhancerMNT14m_SetDlsrClassEv",
    0x0059EB04: "_ZN11ave_dimming15SetObjectNumberEi",
    0x0059F4A4: "_ZN9QDDimming15SetObjectNumberEi",
    0x005A0B08: "_ZN9QDDimming15SetObjectNumberEi",
    0x005A2E2C: "_ZN12DimmingShare31t_DimmingShare_GetWebberDimmingEPjP12ShareWeber_t",
}

# Address -> (mnemonic, exact Capstone 5.0.7 operand text).  These checks pin
# the ioctl ABI, return gate, queue drain, dispatch slots, and dimming handoff.
INSN_EXPECTED = {
    0x00093A36: ("movs", "r0, #1"),
    0x00093A38: ("blx", "#0x9089c"),
    0x00093A3E: ("blx", "#0x8c024"),
    0x00093A46: ("blx", "#0x9089c"),
    0x00093A4A: ("cmp", "r0, #4"),
    0x00093A4E: ("blx", "#0x8c108"),
    0x00093A56: ("blx", "#0x8eb08"),
    0x002B126A: ("movw", "r1, #0x510a"),
    0x002B126E: ("movt", "r1, #0xc004"),
    0x002B1280: ("blx", "#0x8d77c"),
    0x002B1284: ("ldr", "r3, [r7]"),
    0x002B129C: ("ldr", "r3, [r7, #4]"),
    0x002BD0CA: ("mov", "r2, r6"),
    0x002BD0D0: ("blx", "#0x8b67c"),
    0x002BD0D4: ("cmp", "r0, #0"),
    0x002BD0D6: ("bne", "#0x2bd08e"),
    0x002BD0EA: ("ldr.w", "r3, [r3, #0x1d0]"),
    0x002BD0F6: ("blx", "#0x8b67c"),
    0x002BD116: ("ldr.w", "r3, [r3, #0x1d4]"),
    0x002BD132: ("ldr.w", "r3, [r3, #0x268]"),
    0x002BD168: ("ldr.w", "r3, [r3, #0x1d8]"),
    0x002BD170: ("blx", "#0x8bc58"),
    0x002BD180: ("ldr.w", "r3, [r3, #0x1c8]"),
    0x002BD194: ("ldr.w", "r3, [r3, #0x25c]"),
    0x000A3292: ("str", "r4, [r6]"),
    0x000A324C: ("ldr.w", "r8, [pc, #0x5c]"),
    0x000A3252: ("add", "r8, pc"),
    0x000A328E: ("ldr.w", "r3, [r8, r3]"),
    0x000A3294: ("ldr", "r3, [r3]"),
    0x000A3296: ("str.w", "r4, [r3, #0xb0]"),
    0x000A329C: ("ldr.w", "r3, [r3, #0x428]"),
    0x000A32DE: ("str.w", "r3, [r0, #0xec]"),
    0x00172D34: ("str.w", "r1, [r3, #0x45c]"),
    0x0017940A: ("ldr.w", "r2, [r3, #0x45c]"),
    0x0017947C: ("strd", "r4, r5, [r7, #0x18]"),
    0x00179484: ("ldr.w", "r3, [r3, #0x90]"),
    0x00237668: ("ldr", "r3, [r2, #4]"),
    0x0023766C: ("ldr.w", "r8, [r2, #0x38]"),
    0x002376CE: ("str.w", "ip, [r1]"),
    0x002376EA: ("mul", "lr, lr, ip"),
    0x002376EE: ("sdiv", "lr, lr, r2"),
    0x00237724: ("ldr", "r6, [r2]"),
    0x00237742: ("ldr", "r3, [r4, #0x14]"),
    0x0023776E: ("ldr", "r5, [r4, #0x10]"),
    0x00237830: ("ldr", "r5, [r4, #0xc]"),
    0x001743F2: ("ldr.w", "r1, [r2, #0x458]"),
    0x00174438: ("str.w", "r3, [r2, #0xac]"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def vaddr_bytes(elf: ELFFile, stream, address: int, size: int) -> bytes:
    for segment in elf.iter_segments():
        if segment["p_type"] != "PT_LOAD":
            continue
        lo = int(segment["p_vaddr"])
        hi = lo + int(segment["p_filesz"])
        if lo <= address and address + size <= hi:
            stream.seek(int(segment["p_offset"]) + address - lo)
            return stream.read(size)
    raise AssertionError(f"VA range not file-backed: 0x{address:x}+0x{size:x}")


def symbol_map(elf: ELFFile) -> dict[str, tuple[int, int]]:
    symtab = elf.get_section_by_name(".symtab")
    require(symtab is not None, "missing .symtab")
    return {
        symbol.name: (int(symbol["st_value"]), int(symbol["st_size"]))
        for symbol in symtab.iter_symbols()
    }


def plt_map(elf: ELFFile) -> dict[int, str]:
    plt = elf.get_section_by_name(".plt")
    rel = elf.get_section_by_name(".rel.plt")
    require(plt is not None and rel is not None, "missing ARM .plt/.rel.plt")
    dynsym = elf.get_section(rel["sh_link"])
    # This ARM ELF has the standard 20-byte PLT header and 12-byte entries.
    require(int(plt["sh_addr"]) == 0x8A468, "unexpected .plt base")
    require(rel.num_relocations() == 2491, "unexpected PLT relocation count")
    return {
        int(plt["sh_addr"]) + 20 + index * 12: dynsym.get_symbol(
            reloc["r_info_sym"]
        ).name
        for index, reloc in enumerate(rel.iter_relocations())
    }


def relocation_map(elf: ELFFile) -> dict[int, str]:
    result: dict[int, str] = {}
    for section in elf.iter_sections():
        if not hasattr(section, "iter_relocations") or not section["sh_link"]:
            continue
        symbols = elf.get_section(section["sh_link"])
        for reloc in section.iter_relocations():
            if reloc["r_info_sym"]:
                result[int(reloc["r_offset"])] = symbols.get_symbol(
                    reloc["r_info_sym"]
                ).name
    return result


def disassembly_map(elf: ELFFile, stream) -> dict[int, tuple[str, str]]:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    ranges = (
        (0x00093A28, 0x38),
        (0x002B1258, 0x74),
        (0x002BCFD4, 0x234),
        (0x000A3244, 0x64),
        (0x000A32C4, 0x42),
        (0x00172D2C, 0x44),
        (0x001793D0, 0xDC),
        (0x00174260, 0x1E0),
        (0x00237660, 0x1D8),
    )
    result: dict[int, tuple[str, str]] = {}
    for start, size in ranges:
        for insn in md.disasm(vaddr_bytes(elf, stream, start, size), start):
            result[insn.address] = (insn.mnemonic, insn.op_str)
    return result


def main() -> int:
    raw = ELF_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == EXPECTED_SHA256, f"libave hash mismatch: {digest}")

    with ELF_PATH.open("rb") as stream:
        elf = ELFFile(stream)
        require(elf.elfclass == 32, "libave is not ELF32")
        require(elf["e_machine"] == "EM_ARM", "libave is not ARM")

        symbols = symbol_map(elf)
        for name, expected in SYMBOLS.items():
            require(symbols.get(name) == expected, f"symbol mismatch: {name}")

        plts = plt_map(elf)
        for address, name in PLT_EXPECTED.items():
            require(plts.get(address) == name, f"PLT mismatch at 0x{address:x}")

        relocs = relocation_map(elf)
        for address, name in RELOC_EXPECTED.items():
            require(
                relocs.get(address) == name,
                f"relocation mismatch at 0x{address:x}",
            )

        instructions = disassembly_map(elf, stream)
        for address, expected in INSN_EXPECTED.items():
            require(
                instructions.get(address) == expected,
                f"instruction mismatch at 0x{address:x}: {instructions.get(address)!r}",
            )

        require(
            vaddr_bytes(elf, stream, 0x002B1290, 11)
            == bytes([6, 6, 6, 6, 6, 19, 19, 19, 19, 19, 6]),
            "wrapper type jump table changed",
        )
        # At 0x093a2e `add r4,pc` observes Thumb PC 0x093a32.  The literal
        # loaded at 0x093a60 therefore identifies the cached VE pointer.
        builder_literal = int.from_bytes(
            vaddr_bytes(elf, stream, 0x00093A60, 4), "little"
        )
        require(
            0x00093A32 + builder_literal == 0x005ADB5C,
            "VideoEnhancerBuilder cached-pointer address changed",
        )
        require(
            vaddr_bytes(elf, stream, 0x005774D0, 16).split(b"\0", 1)[0]
            == b"/dev/sdp_pqe_dp",
            "device path literal mismatch",
        )
        require(
            vaddr_bytes(elf, stream, 0x00578EFC, 12).split(b"\0", 1)[0]
            == b"AVEMonDLSR",
            "thread-name literal mismatch",
        )

    meta = META_PATH.read_text(errors="strict")
    mapping = re.search(
        r"^([0-9a-f]+)-([0-9a-f]+) r-xp 00000000 .*"
        r"/prd/usr/lib/libave\.so\.0\.1$",
        meta,
        re.MULTILINE,
    )
    require(mapping is not None, "AVOC libave executable mapping not found")
    base, executable_end = (int(value, 16) for value in mapping.groups())
    require((base, executable_end) == (0xF6B77000, 0xF7103000), "map changed")
    require(
        f"{EXPECTED_SHA256}  /prd/usr/lib/libave.so.0.1" in meta,
        "installed libave identity missing",
    )

    vlog = VLOG_PATH.read_text(errors="replace")
    lines = [
        line
        for line in vlog.splitlines()
        if "AVEMonDLSR" in line and "SetHDRBrightnessOptimizer" in line
    ]
    require(len(lines) == 44, f"unexpected captured HDR-change line count: {len(lines)}")
    values = [int(value) for value in re.findall(r"brightClass\[(\d+)\]", "\n".join(lines))]
    require(set(values) == {1, 2, 3}, f"unexpected captured HDR classes: {values}")

    report = {
        "elf": str(ELF_PATH.relative_to(ROOT)),
        "sha256": digest,
        "elf_class": 32,
        "machine": "ARM",
        "runtime_text_mapping": [f"0x{base:08x}", f"0x{executable_end:08x}"],
        "load_bias": f"0x{base:08x}",
        "consumer_symbol": ["0x002bcfd5", 660],
        "wrapper_symbol": ["0x002b1259", 116],
        "ioctl_request": "0xc004510a",
        "record_bytes": 52,
        "captured_hdr_change_logs": len(lines),
        "captured_hdr_classes": sorted(set(values)),
        "checks": {
            "symbols": len(SYMBOLS),
            "plt": len(PLT_EXPECTED),
            "relocations": len(RELOC_EXPECTED),
            "instructions": len(INSN_EXPECTED),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
