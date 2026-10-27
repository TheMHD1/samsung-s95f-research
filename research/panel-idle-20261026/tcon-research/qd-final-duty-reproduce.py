#!/usr/bin/env python3
"""Offline checks for the pinned base-QDDimming final-duty branch.

This program only reads the local libave image and the already accepted passive
baseline JSON.  It performs no process-memory, device, root, or network access.

Run with:
    PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-final-duty-reproduce.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

from capstone import CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB, Cs
from elftools.elf.elffile import ELFFile


BASE = Path(__file__).resolve().parents[1]
LIB = BASE / "binaries/libave.so.0.1"
BASELINE = BASE / "overnight/pqe-policy-baseline-20261026T174544Z.json"
EXPECTED = {
    LIB: "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777",
    BASELINE: "5c36124d0d510fff8ac5ff282cfc43c1a70854d065b76da68ad760ceb56482a4",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def mul32(left: int, right: int) -> int:
    return u32(left * right)


def trunc_div(value: int, divisor: int) -> int:
    """C/ARM signed division toward zero, without using floating point."""
    require(divisor > 0, "positive divisor required")
    value = s32(value)
    return value // divisor if value >= 0 else -((-value) // divisor)


def magic_signed_div(value: int, multiplier: int) -> int:
    """The SMULL/high-ASR5/sign correction used for /100 and /300."""
    value = s32(value)
    high = (value * s32(multiplier)) >> 32
    return (high >> 5) - (value >> 31)


def weighted_formula(fc: int, f8: int, weight: int) -> int:
    """Exact 32-bit arithmetic of the +0x38/+0x450 formula."""
    base = magic_signed_div(mul32(fc, 1023), 0x51EB851F)
    delta_term = magic_signed_div(mul32(weight, s32(u32(f8 - fc))), 0x51EB851F)
    return s32(u32(base + delta_term))


def weber_formula(fc: int, f8: int, weight: int, weber: int, scale: int) -> int:
    """Exact instruction-level arithmetic of the ordinary Weber branch.

    The final reciprocal is retained as the literal fixed-point operation.  It
    is deliberately not relabelled as a physical unit or an exact division by
    an inferred decimal constant.
    """
    base = magic_signed_div(mul32(fc, 1023), 0x51EB851F)
    stage1 = mul32(weber, scale) >> 10
    stage2 = mul32(weight, stage1) >> 10
    stage3 = mul32(s32(u32(f8 - fc)), stage2)
    stage4 = mul32(stage3, 1023) >> 2
    correction = ((stage4 * 0x52000521) >> 32) >> 13
    return s32(u32(base + correction))


def auto_power_off(fc: int, working: int, auto_dim: int, count: int) -> tuple[int, int]:
    """Exact non-logging m_AutoPowerOff state transition."""
    floor = magic_signed_div(u32(fc << 10), 0x51EB851F)
    working = s32(working)
    count = s32(count)
    if s32(auto_dim) == 1:
        if count < 300 and working > floor:
            count = max(s32(u32(count + 1)), 0)
        else:
            return floor, 300
    else:
        count = min(max(s32(u32(count - 1)), 0), 300)
    remain = s32(u32(300 - count))
    delta = s32(u32(working - floor))
    interpolated = magic_signed_div(mul32(delta, remain), 0x1B4E81B5)
    return s32(u32(floor + interpolated)), count


def final_clamp(value: int, oled_model_gate: int) -> int:
    value = s32(value)
    value = max(value, 12 if s32(oled_model_gate) == 1 else 51)
    return min(value, 1023)


def main() -> None:
    for path, expected in EXPECTED.items():
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual == expected, f"unexpected SHA256 for {path.name}: {actual}")
        print(f"SHA256 {path.relative_to(BASE)} {actual}")

    with LIB.open("rb") as stream:
        elf = ELFFile(stream)

        def read_va(address: int, size: int) -> bytes:
            for segment in elf.iter_segments():
                if segment["p_type"] != "PT_LOAD":
                    continue
                low = int(segment["p_vaddr"])
                high = low + int(segment["p_filesz"])
                if low <= address and address + size <= high:
                    stream.seek(int(segment["p_offset"]) + address - low)
                    data = stream.read(size)
                    require(len(data) == size, "short ELF read")
                    return data
            raise AssertionError(f"VA not file-backed: 0x{address:x}+0x{size:x}")

        symbols = elf.get_section_by_name(".symtab")
        require(symbols is not None, "missing .symtab")
        by_name = {symbol.name: symbol for symbol in symbols.iter_symbols()}
        expected_symbols = {
            "_ZN9QDDimming16m_SetFinalDuty2DEv": (0x174261, 0x36C),
            "_ZN9QDDimming14m_AutoPowerOffEv": (0x1740F1, 0x170),
            "_ZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_t": (0x1C6275, 0xFC),
            "_ZN9QDDimming12SetConditionEii": (0x17030D, 0x130),
            "_ZN9QDDimming10SetAutoDimEi": (0x172A35, 0x98),
            "_ZN9QDDimming12SetInstantOnE14AVEInstantOn_k": (0x1707A9, 0xC0),
            "_ZN9QDDimming17SetDebugPrintFlagEiii": (0x170DED, 0x150),
            "_ZN9QDDimmingC2EP23DimmingBackendInterface13DimmingType_k": (0x17A9D9, 0x6D4),
            "_ZZN9QDDimming14m_AutoPowerOffEvE14siAutoDimCount": (0x5BE420, 4),
            "_ZZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_tE8siDimLvl": (0x5AB958, 4),
        }
        for name, expected in expected_symbols.items():
            symbol = by_name.get(name)
            require(symbol is not None, f"missing symbol {name}")
            actual = (int(symbol["st_value"]), int(symbol["st_size"]))
            require(actual == expected, f"symbol mismatch {name}: {actual!r}")

        decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)

        def instructions(start: int, size: int) -> set[tuple[int, str, str]]:
            return {
                (insn.address, insn.mnemonic, insn.op_str)
                for insn in decoder.disasm(read_va(start, size), start)
            }

        final = instructions(0x174260, 0x36C)
        final_landmarks = {
            # Ordered formula gates and their inputs.
            (0x17427C, "ldrb.w", "r3, [r2, #0x38]"),
            (0x174282, "beq.w", "#0x1743d2"),
            (0x174296, "ldr.w", "r1, [r2, #0x88]"),
            (0x1743D2, "ldr.w", "r3, [r2, #0x450]"),
            (0x1743D8, "beq.w", "#0x1744fa"),
            (0x1743DC, "ldr.w", "r3, [r2, #0x188]"),
            (0x1743E2, "beq.w", "#0x174510"),
            (0x1743F2, "ldr.w", "r1, [r2, #0x458]"),
            (0x1743F6, "ldr.w", "r5, [r2, #0x98]"),
            (0x1743FA, "movw", "r6, #0x521"),
            (0x1743FE, "movt", "r6, #0x5200"),
            (0x17442A, "rsb", "r1, r1, r1, lsl #10"),
            (0x174430, "umull", "r0, r1, r6, r1"),
            (0x174438, "str.w", "r3, [r2, #0xac]"),
            (0x17450A, "ldr.w", "r1, [r2, #0x98]"),
            (0x174510, "ldr.w", "r3, [r2, #0xac]"),
            (0x17451E, "asrs", "r3, r3, #2"),
            # Lower bound, mutating interface, AutoPowerOff, and final clamps.
            (0x1742C0, "ldr.w", "r3, [r2, #0x188]"),
            (0x1742CC, "ldr.w", "r1, [r2, #0xa4]"),
            (0x1742E8, "add.w", "r1, r2, #0xac"),
            (0x1742EE, "ldr", "r3, [r3, #0x54]"),
            (0x1742F0, "blx", "r3"),
            (0x1742FA, "str.w", "r2, [r3, #0xa8]"),
            (0x1742FE, "blx", "#0x8f75c"),
            (0x174312, "cmp", "r2, #0x33"),
            (0x17443E, "cmp", "r2, #0xc"),
            (0x17431C, "movw", "r1, #0x3ff"),
            # Backend and vendor result accumulation.
            (0x17433C, "ldr", "r0, [r4, #0x10]"),
            (0x174340, "cbz", "r0, #0x17438e"),
            (0x17434C, "ldr.w", "r5, [r3, #0xa8]"),
            (0x174384, "ldr.w", "r3, [r3, #0xd8]"),
            (0x174388, "blx", "r3"),
            (0x174390, "cmp", "r2, #1"),
            (0x1743B0, "ldr", "r3, [r3, #0x48]"),
            (0x1743B4, "orrs", "r5, r0"),
        }
        require(final_landmarks <= final, "m_SetFinalDuty2D landmark mismatch")

        auto = instructions(0x1740F0, 0x170)
        auto_landmarks = {
            (0x174106, "ldr.w", "r3, [r0, #0xfc]"),
            (0x17410C, "ldr.w", "r5, [r0, #0xa8]"),
            (0x174110, "ldr.w", "r6, [r0, #0x2a8]"),
            (0x174118, "cmp", "r6, #1"),
            (0x17417E, "cmp.w", "r2, #0x12c"),
            (0x174184, "cmp", "r5, r3"),
            (0x174188, "adds", "r2, #1"),
            (0x174132, "subs", "r2, #1"),
            (0x174140, "bic.w", "r2, r2, r2, asr #31"),
            (0x17414A, "subs", "r6, r6, r2"),
            (0x174152, "smull", "ip, r1, ip, r1"),
            (0x17415C, "str.w", "r3, [r0, #0xa8]"),
            (0x17416C, "str.w", "r2, [r8, #0x10]"),
        }
        require(auto_landmarks <= auto, "m_AutoPowerOff landmark mismatch")

        backend = instructions(0x1C6274, 0xFC)
        backend_landmarks = {
            (0x1C6288, "ldr.w", "r8, [r6, #8]"),
            (0x1C629A, "ldr", "r2, [r3, #0x10]"),
            (0x1C629E, "cmp", "r2, r8"),
            (0x1C62A0, "beq", "#0x1c62ca"),
            (0x1C62A4, "mov.w", "r1, #0xf300"),
            (0x1C62A8, "mov.w", "r0, #0x128"),
            (0x1C62AC, "str.w", "r8, [r3, #0x10]"),
            (0x1C62B0, "str.w", "r8, [r7]"),
            (0x1C62B4, "blx", "#0x8db9c"),
            (0x1C62B8, "ldr", "r1, [r7]"),
            (0x1C62BC, "movw", "r0, #0x2b48"),
            (0x1C62C0, "movt", "r0, #4"),
            (0x1C62C4, "blx", "#0x9023c"),
            (0x1C62C8, "orrs", "r5, r0"),
        }
        require(backend_landmarks <= backend, "RoseMQD backend landmark mismatch")

        # PC-relative static objects used by the two stateful routines.
        auto_literal = struct.unpack("<I", read_va(0x174244, 4))[0]
        cache_literal = struct.unpack("<I", read_va(0x1C6354, 4))[0]
        require(0x17410E + auto_literal + 0x10 == 0x5BE420, "AutoDim counter literal mismatch")
        require(0x1C628A + cache_literal + 0x10 == 0x5AB958, "backend cache literal mismatch")
        require(struct.unpack("<I", read_va(0x5AB958, 4))[0] == 0xFFFFFFFF, "backend cache initializer mismatch")

        # PLT call identity and the concrete runtime backend vtable slot.
        rel_plt = elf.get_section_by_name(".rel.plt")
        plt = elf.get_section_by_name(".plt")
        require(rel_plt is not None and plt is not None, "missing ARM PLT metadata")
        dynsym = elf.get_section(rel_plt["sh_link"])
        plt_names = {
            int(plt["sh_addr"]) + 20 + 12 * index: dynsym.get_symbol(reloc["r_info_sym"]).name
            for index, reloc in enumerate(rel_plt.iter_relocations())
        }
        require(plt_names[0x8DB9C] == "_Z28ave_tcon_api_send_onecommandyPj", "command sender PLT mismatch")
        require(plt_names[0x9023C] == "_Z17ave_frc_write_i2cjj", "FRC writer PLT mismatch")
        require(plt_names[0x8E304] == "_ZN9QDDimming16m_SetFinalDuty2DEv", "final-duty PLT mismatch")
        require(plt_names[0x8F75C] == "_ZN9QDDimming14m_AutoPowerOffEv", "AutoPowerOff PLT mismatch")
        require(plt_names[0x9089C] == "_Z16get_product_typei", "product-type PLT mismatch")
        require(plt_names[0x90D10] == "_Z23ave_get_oled_model_typeP16AVEOledModelType", "OLED-type PLT mismatch")

        relocations: dict[int, str] = {}
        for section in elf.iter_sections():
            if not hasattr(section, "iter_relocations") or not section["sh_link"]:
                continue
            linked = elf.get_section(section["sh_link"])
            for reloc in section.iter_relocations():
                if reloc["r_info_sym"]:
                    relocations[int(reloc["r_offset"])] = linked.get_symbol(reloc["r_info_sym"]).name
        backend_name = "_ZN21DimmingBackendRoseMQD16t_Set2DFinalDutyEP22BackendGd2DFinalDuty_t"
        require(relocations.get(0x5A1604) == backend_name, "RoseMQD vtable +0xd8 relocation mismatch")

        # Direct writer landmarks for the principal gates.
        writers = instructions(0x17030C, 0x130) | instructions(0x17A9D8, 0x6D4)
        writer_landmarks = {
            (0x170342, "it", "ne"),
            (0x170344, "movne", "r2, #1"),
            (0x170346, "strb.w", "r2, [r3, #0x38]"),
            (0x17AAC0, "strb.w", "r1, [r5, #0x38]"),
            (0x17AFCA, "movs", "r0, #1"),
            (0x17AFCC, "blx", "#0x9089c"),
            (0x17AFD2, "str.w", "r0, [r3, #0x450]"),
            (0x17AFC4, "mov", "r0, r7"),
            (0x17AFC6, "blx", "#0x90d10"),
            (0x17AFE2, "sub.w", "r2, r2, #2"),
            (0x17AFE6, "clz", "r2, r2"),
            (0x17AFEA, "lsrs", "r2, r2, #5"),
            (0x17AFEC, "str.w", "r2, [r3, #0x188]"),
            (0x17B080, "str.w", "r2, [r3, #0x188]"),
        }
        require(writer_landmarks <= writers, "principal gate writer mismatch")
        # SetCondition selector 1 is jump-table byte 0x0f: 0x170320 + 2*0x0f = 0x17033e.
        require(read_va(0x170320, 1) == b"\x0f", "SetCondition selector-1 jump mismatch")
        auto_writers = instructions(0x172A34, 0x98) | instructions(0x1707A8, 0xC0)
        require((0x172A4E, "str.w", "r3, [r0, #0x2a8]") in auto_writers, "SetAutoDim writer mismatch")
        require((0x1707C0, "str.w", "r6, [r2, #0x2a8]") in auto_writers, "SetInstantOn clear mismatch")
        debug_writer = instructions(0x170DEC, 0x150)
        require((0x170E88, "str.w", "r3, [r0, #0x138]") in debug_writer, "debug clear writer mismatch")
        require((0x170F00, "str.w", "r1, [r0, #0x138]") in debug_writer, "debug set writer mismatch")

        # The vsync caller invokes final-duty and branches without inspecting r0.
        vsync = instructions(0x17B55E, 0x12)
        require((0x17B566, "blx", "#0x8e304") in vsync, "vsync final-duty call mismatch")
        require((0x17B56A, "b", "#0x17b3e4") in vsync, "vsync return-discard branch mismatch")

    # Check the reciprocal sequences against signed truncation over a useful
    # exhaustive interval plus int32 boundaries.  This tests the model; the
    # instruction assertions above are the binary evidence.
    samples = list(range(-200_000, 200_001)) + [-(1 << 31), -(1 << 31) + 1, -1, 0, 1, (1 << 31) - 2, (1 << 31) - 1]
    for value in samples:
        require(magic_signed_div(value, 0x51EB851F) == trunc_div(value, 100), f"/100 mismatch at {value}")
        require(magic_signed_div(value, 0x1B4E81B5) == trunc_div(value, 300), f"/300 mismatch at {value}")

    # Zero is possible inside AutoPowerOff, but the immediately following final
    # clamp prevents a zero backend candidate on either +0x188 branch.
    require(auto_power_off(0, 0, 1, 299) == (0, 300), "AutoPowerOff zero case mismatch")
    require(final_clamp(0, 0) == 51 and final_clamp(0, 1) == 12, "final clamps mismatch")
    require(weighted_formula(0, 100, 50) == 50, "weighted formula check mismatch")
    require(weber_formula(0, 100, 1024, 1024, 1024) >= 0, "Weber model sanity failure")

    baseline = json.loads(BASELINE.read_text())
    summary = baseline["summary"]
    require(baseline["accepted"] is True and summary["physical_state"] == "unobserved", "baseline status mismatch")
    require(summary["qd"]["class"] == "QDDimming", "baseline QD type mismatch")
    require(summary["backend"]["class"] == "DimmingBackendRoseMQD", "baseline backend type mismatch")
    decoded = summary["decoded"]
    require(decoded["qd_working_duty"]["words"] == [236, 236], "baseline +a8/+ac mismatch")
    require(decoded["qd_weber_policy"]["words"][0] == 1023, "baseline +458 mismatch")
    require(decoded["backend_cache"]["words"] == [236], "baseline cache mismatch")

    print("PASS: pinned final-duty gates, arithmetic, clamps, static state, backend relocation/transport, and sampled-baseline anchors")
    print("LIMIT: CFG/dataflow classification is manual; indirect writers, runtime virtual mutation, transport application, and physical output are not proved")


if __name__ == "__main__":
    main()
