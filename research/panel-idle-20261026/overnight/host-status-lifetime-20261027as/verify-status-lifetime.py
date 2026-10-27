#!/usr/bin/env python3
"""Offline verifier for the selected image-0 common status lifetime trace."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / "selected-qd-profile-copy-20261027b" / "F_RSM1_BN9659934B_COMMON.bin"
PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
IMAGE0_FILE = 0x200
IMAGE0_SIZE = 0x40000
COMMON_BASE = 0x2000F0E0

for candidate in (Path("/tmp/tcon-re-capstone"), Path("/tmp/tcon-capstone")):
    if (candidate / "capstone").is_dir():
        sys.path.insert(0, str(candidate))
        break

from capstone import Cs, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB  # noqa: E402
from capstone.arm import (  # noqa: E402
    ARM_OP_IMM,
    ARM_OP_MEM,
    ARM_OP_REG,
    ARM_REG_PC,
    ARM_REG_R0,
    ARM_REG_R1,
    ARM_REG_R2,
    ARM_REG_R3,
    ARM_REG_R12,
    ARM_REG_SP,
)


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def text(data: bytes, offset: int) -> str:
    end = data.index(b"\0", offset)
    return data[offset:end].decode("ascii")


def thumb_bl_target(image: bytes, va: int) -> int | None:
    if va < 0 or va + 4 > len(image) or va & 1:
        return None
    first, second = struct.unpack_from("<HH", image, va)
    if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
        return None
    sign = (first >> 10) & 1
    imm10 = first & 0x03FF
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    imm11 = second & 0x07FF
    i1 = 1 ^ (j1 ^ sign)
    i2 = 1 ^ (j2 ^ sign)
    displacement = (sign << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
    if sign:
        displacement -= 1 << 25
    return (va + 4 + displacement) & 0xFFFFFFFF


def direct_bl_callers(image: bytes, target: int) -> list[int]:
    return [va for va in range(0, len(image) - 3, 2) if thumb_bl_target(image, va) == target]


def capstone_image(image: bytes):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    md.skipdata = True
    return md, [insn for insn in md.disasm(image, 0) if insn.id]


def accessor_taint_census(image: bytes) -> tuple[list[tuple[int, str, str]], list[dict[str, object]], int]:
    """Bounded linear register-use heuristic, not CFG or whole-program analysis."""
    md, instructions = capstone_image(image)
    positions = {insn.address: index for index, insn in enumerate(instructions)}
    getter_calls = [
        insn for insn in instructions
        if insn.mnemonic in ("bl", "blx") and insn.op_str == "#0xe670"
    ]
    accesses: set[tuple[int, str, str]] = set()
    escapes: set[tuple[int, str, tuple[tuple[str, int], ...]]] = set()

    for call in getter_calls:
        taint = {ARM_REG_R0: 0}
        # Every inspected use terminates at a return or after 250 decoded
        # instructions. This linear walk ignores control-flow edges and can
        # both miss feasible uses and overapproximate infeasible sequences.
        for insn in instructions[positions[call.address] + 1:positions[call.address] + 251]:
            for operand in insn.operands:
                if operand.type == ARM_OP_MEM and operand.mem.base in taint:
                    effective = taint[operand.mem.base] + operand.mem.disp
                    if effective == 0x10:
                        accesses.add((insn.address, insn.mnemonic, insn.op_str))

            if insn.mnemonic in ("bl", "blx"):
                args = tuple(sorted(
                    (md.reg_name(register), offset)
                    for register, offset in taint.items()
                    if register in (ARM_REG_R0, ARM_REG_R1, ARM_REG_R2, ARM_REG_R3)
                ))
                if args:
                    escapes.add((insn.address, insn.op_str, args))
                for register in (ARM_REG_R0, ARM_REG_R1, ARM_REG_R2, ARM_REG_R3, ARM_REG_R12):
                    taint.pop(register, None)
            else:
                propagated = None
                operands = insn.operands
                if (insn.mnemonic.startswith("mov") and len(operands) >= 2 and
                        operands[0].type == ARM_OP_REG and operands[1].type == ARM_OP_REG and
                        operands[1].reg in taint):
                    propagated = (operands[0].reg, taint[operands[1].reg])
                elif ((insn.mnemonic.startswith("add") or insn.mnemonic.startswith("sub")) and
                      len(operands) >= 3 and operands[0].type == ARM_OP_REG and
                      operands[1].type == ARM_OP_REG and operands[1].reg in taint and
                      operands[2].type == ARM_OP_IMM):
                    delta = operands[2].imm if insn.mnemonic.startswith("add") else -operands[2].imm
                    propagated = (operands[0].reg, taint[operands[1].reg] + delta)
                _, written = insn.regs_access()
                for register in written:
                    taint.pop(register, None)
                if propagated:
                    taint[propagated[0]] = propagated[1]

            if ((insn.mnemonic == "bx" and insn.op_str == "lr") or
                    (insn.mnemonic.startswith("pop") and "pc" in insn.op_str)):
                break

    escape_rows = [
        {"va": address, "target": target, "args": [[register, value] for register, value in args]}
        for address, target, args in sorted(escapes)
    ]
    return sorted(accesses), escape_rows, len(getter_calls)


EXPECTED_COMMON_CALLS = [
    0x391C, 0x3C2A, 0x5C52, 0x5E9E, 0x60D2, 0x6288, 0x6358,
    0x6EB8, 0x6EC4, 0x6ED0, 0x6F48, 0x7450, 0x93F0, 0x96B2,
    0x9834, 0x9862, 0xD6E2, 0xDBE2, 0x12FBC, 0x130EA, 0x13226,
    0x1C740, 0x1C970, 0x1CAA0, 0x1DDCA, 0x1DF38, 0x1DF86,
    0x1DFD4, 0x214F2, 0x2236E, 0x22420, 0x22486, 0x24CEE,
    0x2E60A, 0x39A54,
]

EXPECTED_SELECTORS = {
    0x391C: 0x40, 0x3C2A: 0xC00, 0x5C52: 0x400, 0x5E9E: 0x400,
    0x60D2: 0x400, 0x6288: 0x400, 0x6358: 0x400, 0x6EB8: 0xA00,
    0x6EC4: 0xA00, 0x6ED0: 0xA00, 0x6F48: 0x400, 0x7450: 0x400,
    0x93F0: 0x20, 0x96B2: 2, 0x9834: 0x10, 0x9862: 0x10,
    0xD6E2: 0x80, 0xDBE2: 0x800, 0x12FBC: 0, 0x130EA: 0,
    0x13226: 0, 0x1C740: 0xB00, 0x1C970: 0, 0x1CAA0: 0xB00,
    0x1DDCA: 8, 0x1DF38: 8, 0x1DF86: 8, 0x1DFD4: 8,
    0x214F2: 0x10, 0x2236E: 4, 0x22420: 2, 0x22486: 1,
    0x24CEE: 0x2000, 0x2E60A: 0x80, 0x39A54: 0x900,
}

EXPECTED_FIELD_ACCESSES = [
    (0x1ECA2, "ldrh", "r0, [r4, #0x10]"),
    (0x1F324, "ldrh", "r0, [r4, #0x10]"),
    (0x1F33A, "ldrh", "r0, [r4, #0x10]"),
    (0x1F34A, "ldrh", "r0, [r4, #0x10]"),
    (0x1F35A, "ldrh", "r0, [r4, #0x10]"),
    (0x1F36A, "ldrh", "r0, [r4, #0x10]"),
    (0x1FBFC, "ldrh", "r0, [r4, #0x10]"),
    (0x21E6A, "ldrh", "r0, [r0, #0x10]"),
    (0x2B770, "ldrh", "r0, [r0, #0x10]"),
    (0x2B776, "strh", "r0, [r5]"),
]


def verify(data: bytes, require_identity: bool = True) -> dict[str, object]:
    need(len(data) == 0x500000, "package size")
    if require_identity:
        need(sha(data) == PACKAGE_SHA256, "package identity")
    image = data[IMAGE0_FILE:IMAGE0_FILE + IMAGE0_SIZE]

    # Fixed object accessor and reset zero-fill allocation.
    need(image[0xE670:0xE678].hex() == "00487047e0f00020", "common accessor")
    need(u32(image, 0xE674) == COMMON_BASE, "common base literal")
    scatter = data[0x3E340:0x3E400]
    need(sha(scatter) == "3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d",
         "scatter table")
    rows = [struct.unpack_from("<4I", scatter, index * 16) for index in range(12)]
    need(rows[11] == (0x3E764, 0x20000F4C, 0x16438, 0x1D8), "zero-fill row")
    zero_start, zero_length = rows[11][1], rows[11][2]
    need(zero_start <= COMMON_BASE + 0x10 < zero_start + zero_length, "field outside reset zero-fill")
    need(image[0x1D8:0x1F4].hex() ==
         "0023002400250026103a28bf78c1fbd8520728bf30c148bf0b607047", "zero-fill body")

    # Positive AP registry and packaged type-4 initialization of +0x10 to 0.
    row = struct.unpack_from("<7I", data, 0x3CCD8)
    need(text(data, row[0] + IMAGE0_FILE) == "AP", "AP row name")
    need(row == (0x3DE88, 0x2000F0E0, 0x40C, 0, 0, 0x130000, 0), "AP row")
    metadata = 0x84C00
    fields = {offset: u32(data, metadata + offset) for offset in (0x20, 0x24, 0x28, 0x2C, 0x6C, 0xAC)}
    need(text(data, metadata) == "AP", "AP metadata name")
    need(fields == {0x20: 4, 0x24: 0x130000, 0x28: 1, 0x2C: 0xF2000,
                    0x6C: 0, 0xAC: 0x40A}, "AP metadata")
    payload = 0x80000 + fields[0x2C]
    need(payload == 0x172000, "AP payload arithmetic")
    need(struct.unpack_from("<H", data, payload + 0x10)[0] == 0, "AP packaged status default")
    need(sha(data[payload:payload + 0x40A]) ==
         "936bf564162421ffca508509e7aba21e360f4556d9eaafc16230676aa53ca858",
         "AP payload")

    # Pin the ordinary type-4 dispatch and the relevant successful first-copy
    # semantics rather than relying on metadata shape alone. The loader takes
    # min(table first limit, record first length), requires a zero lower-read
    # result before the copy arm, caps each copy chunk, resolves table+4 plus
    # record destination offset, and calls the ordinary copy helper.
    need(sha(image[0x7568:0x7584]) ==
         "4f3d700e87559f93cc617cdfe45fa5ce160a425d5384255e05001d9339acb0d4",
         "type4 dispatch slice")
    need(image[0x756A:0x756E].hex() == "04280bd1", "type4 compare and branch")
    need(thumb_bl_target(image, 0x7580) == 0x6190, "type4 loader call")
    need(sha(image[0x61D0:0x61F4]) ==
         "7f5e058f1a33439081ec9ff68ad76e345f06732167c8d9d6059bc088e03e91c1",
         "loader first-length minimum slice")
    need(sha(image[0x6214:0x625C]) ==
         "f29b2ba877260a0161170b61c17cb79e7048ba236a2d51eb27ae35804eb5bd6a",
         "loader successful first-copy slice")
    need(image[0x6224:0x6228].hex() == "049808bb", "loader read-result gate")
    need(thumb_bl_target(image, 0x621E) == 0x9BD4, "loader lower read call")
    need(thumb_bl_target(image, 0x6258) == 0xA72, "loader copy call")
    need(direct_bl_callers(image, 0x6190) == [0x7580, 0x75F4], "type4 loader callers")
    need(direct_bl_callers(image, 0x7474) == [0x39A5E], "config wrapper caller")
    need(thumb_bl_target(image, 0x7492) == 0x7544, "config wrapper to type4 enumerator")
    need(direct_bl_callers(image, 0x97E8) == [0x39B26], "pre-loop history caller")
    need(0x39A5E < 0x39B26, "startup config/history order")

    # Exact overwrite setter, sole direct caller, and all direct common-entry selectors.
    setter = image[0x2B764:0x2B77A]
    need(setter.hex() == "70b50446e2f782ff00f11005008a64f30f00288070bd", "selector setter")
    need(direct_bl_callers(image, 0x2B764) == [0xB6A6], "selector setter direct caller")
    common_callers = direct_bl_callers(image, 0xB660)
    need(common_callers == EXPECTED_COMMON_CALLS, "common-entry direct caller census")
    md, instructions = capstone_image(image)
    by_address = {insn.address: index for index, insn in enumerate(instructions)}
    actual_selectors: dict[int, int] = {}
    for call in common_callers:
        index = by_address[call]
        previous = instructions[index - 1]
        need(previous.mnemonic in ("mov", "movs", "mov.w"), f"selector setup mnemonic {call:x}")
        need(len(previous.operands) >= 2 and previous.operands[0].type == ARM_OP_REG and
             previous.operands[0].reg == ARM_REG_R0 and previous.operands[1].type == ARM_OP_IMM,
             f"selector setup operands {call:x}")
        actual_selectors[call] = previous.operands[1].imm
    need(actual_selectors == EXPECTED_SELECTORS, "common-entry selector map")

    # Four explicit selector-zero sites and the one positively ordered startup site.
    zero_sites = [address for address, selector in actual_selectors.items() if selector == 0]
    need(zero_sites == [0x12FBC, 0x130EA, 0x13226, 0x1C970], "selector-zero sites")
    need(direct_bl_callers(image, 0x1C8C4) == [0x39B4A], "PMIC startup helper caller")
    need(0x39B26 < 0x39B4A, "history/PMIC startup order")
    labels = {}
    for load_va in (0x12FB8, 0x130E6, 0x13222, 0x1C96C):
        insn = instructions[by_address[load_va]]
        need(insn.mnemonic == "ldr" and insn.operands[-1].type == ARM_OP_MEM and
             insn.operands[-1].mem.base == ARM_REG_PC, f"label literal load {load_va:x}")
        literal_va = ((load_va + 4) & ~3) + insn.operands[-1].mem.disp
        label_va = u32(image, literal_va)
        labels[load_va + 4] = text(data, label_va + IMAGE0_FILE)
    need(labels == {0x12FBC: "INA226_GetCurReg", 0x130EA: "INA238_GetReg",
                    0x13226: "INA238_SetReg", 0x1C970: "PMIC_Init"}, "selector-zero labels")

    # Bounded accessor-derived explicit access census. Escapes are retained as
    # a proof limit rather than recursively treated as nonwriters.
    accesses, escapes, getter_call_count = accessor_taint_census(image)
    need(accesses == EXPECTED_FIELD_ACCESSES, "direct effective +0x10 census")
    need(getter_call_count == 223, "accessor call count")
    need(len(escapes) == 62, "pointer escape count")
    escape_digest = sha(json.dumps(escapes, sort_keys=True, separators=(",", ":")).encode())
    need(escape_digest == "3c742bd201ed4aa9120acebc9f6397282278875af14415b21f51b53deecde8e8",
         "pointer escape census")
    raw_base_hits = [index for index in range(len(image) - 3)
                     if image[index:index + 4] == struct.pack("<I", COMMON_BASE)]
    need(raw_base_hits == [0x70F0, 0xE674, 0x3CADC], "raw common-base word census")

    return {
        "schema": "host-status-lifetime-offline-v1",
        "package_sha256": sha(data),
        "common_base": f"0x{COMMON_BASE:08x}",
        "reset_default": 0,
        "packaged_type4_default": 0,
        "setter_va": "0x2b764",
        "setter_direct_callers": [f"0x{value:x}" for value in direct_bl_callers(image, 0x2B764)],
        "common_entry_direct_call_count": len(common_callers),
        "selector_zero_sites": [f"0x{value:x}" for value in zero_sites],
        "selector_ten_sites": [f"0x{address:x}" for address, value in actual_selectors.items() if value == 0x10],
        "startup_order": ["config-load@0x39a5e", "history-check@0x39b26", "pmic-helper@0x39b4a"],
        "direct_effective_field_accesses": [f"0x{value[0]:x}:{value[1]}" for value in accesses],
        "accessor_recognized_decoded_calls": getter_call_count,
        "pointer_escape_count": len(escapes),
        "pointer_escape_sha256": escape_digest,
        "scope": "selected-image linear register-use heuristic; not CFG, exhaustive direct-call, alias, or copy proof",
        "target_operations": 0,
    }


def mutation_tests(original: bytes) -> list[str]:
    cases = []

    def rejected(name: str, offset: int, replacement: bytes) -> None:
        mutated = bytearray(original)
        mutated[offset:offset + len(replacement)] = replacement
        try:
            verify(bytes(mutated), require_identity=False)
        except ValueError:
            cases.append(name)
            return
        raise ValueError(f"mutation accepted: {name}")

    rejected("common-base-literal", IMAGE0_FILE + 0xE674, struct.pack("<I", COMMON_BASE + 2))
    rejected("packaged-status-default", 0x172010, b"\x01\x00")
    rejected("setter-store", IMAGE0_FILE + 0x2B776, b"\x00\xbf")
    rejected("startup-selector-zero", IMAGE0_FILE + 0x1C96E, b"\x01\x20")
    rejected("startup-config-call", IMAGE0_FILE + 0x39A5E, b"\x00\xbf\x00\xbf")
    rejected("config-wrapper-enumerator-call", IMAGE0_FILE + 0x7492, b"\x00\xbf\x00\xbf")
    rejected("type4-dispatch-gate", IMAGE0_FILE + 0x756A, b"\x00\xbf\x00\xbf")
    rejected("loader-minimum-branch", IMAGE0_FILE + 0x61E0, b"\x00\xbf")
    rejected("loader-success-gate", IMAGE0_FILE + 0x6226, b"\x00\xbf")
    rejected("loader-copy-call", IMAGE0_FILE + 0x6258, b"\x00\xbf\x00\xbf")
    return cases


def main() -> None:
    package = PACKAGE.read_bytes()
    result = verify(package)
    result["mutation_tests"] = mutation_tests(package)
    result["mutation_test_count"] = len(result["mutation_tests"])
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
