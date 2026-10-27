#!/usr/bin/env python3
"""Offline exact-reference census for the selected package's image-1 window."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

try:
    import capstone
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB
    from capstone.arm import ARM_OP_IMM
except ImportError as exc:  # pragma: no cover - explicit invocation contract
    raise SystemExit("capstone is required; use PYTHONPATH=/tmp/tcon-re-capstone") from exc


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
BASE = OVERNIGHT.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
N_REPORT = OVERNIGHT / "code-map-qualified-followup-20261027n/code-map-qualified-followup.md"
IMAGE1_REPORT = BASE / "tcon-research/qd-profile-rtp-image1.md"
Y_REPORT = OVERNIGHT / "ap-table-source-20261027y/table-source-trace.md"
AB_REPORT = OVERNIGHT / "pre-pd-stored-values-20261027ab/stored-values.md"

PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
SOURCE_START = 0x58410000
SOURCE_END = 0x58410AB0
TARGETS = (0x584109A4, 0x58410A64, 0x58410178, 0x58410000)
FILE_START = 0x40200
LINKED_LENGTH = 0x20000
FILE_END = FILE_START + LINKED_LENGTH


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_pinned(path: Path, digest: str) -> bytes:
    raw = path.read_bytes()
    need(sha256(raw) == digest, f"SHA-256 mismatch: {path}")
    return raw


def u16(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def all_u32_range_hits(raw: bytes, start: int, end: int) -> list[dict[str, int]]:
    """Byte-granular four-byte candidates, deliberately including unaligned data."""
    result = []
    for offset in range(0, len(raw) - 3):
        value = u32(raw, offset)
        if start <= value < end:
            result.append({"linked_offset": offset, "value": value})
    return result


def literal_loads(instructions: bytes, backing: bytes) -> list[dict[str, int | str]]:
    """Raw nominal-instruction census with a separately pinned literal backing."""
    result: list[dict[str, int | str]] = []
    need(len(instructions) % 2 == 0, "instruction-window halfword alignment")
    need(len(backing) >= len(instructions), "literal backing extent")
    for address in range(0, len(instructions) - 1, 2):
        first = u16(instructions, address)
        if first & 0xF800 == 0x4800:
            literal = ((address + 4) & ~3) + (first & 0xFF) * 4
            kind = "ldr16"
            register = (first >> 8) & 7
        elif first == 0xF8DF and address + 4 <= len(instructions):
            second = u16(instructions, address + 2)
            literal = ((address + 4) & ~3) + (second & 0xFFF)
            kind = "ldr32-positive"
            register = (second >> 12) & 15
        elif first == 0xF85F and address + 4 <= len(instructions):
            second = u16(instructions, address + 2)
            literal = ((address + 4) & ~3) - (second & 0xFFF)
            kind = "ldr32-negative"
            register = (second >> 12) & 15
        else:
            continue
        if not 0 <= literal <= len(backing) - 4:
            continue
        result.append({
            "load_va": address,
            "kind": kind,
            "register": register,
            "literal_va": literal,
            "value": u32(backing, literal),
        })
    return result


def source_literal_loads(instructions: bytes, backing: bytes) -> list[dict[str, int | str]]:
    return [item for item in literal_loads(instructions, backing)
            if SOURCE_START <= item["value"] < SOURCE_END]


def decode_mov_half(raw: bytes, address: int) -> tuple[str, int, int] | None:
    first, second = struct.unpack_from("<HH", raw, address)
    if first & 0xFBF0 == 0xF240:
        kind = "movw"
    elif first & 0xFBF0 == 0xF2C0:
        kind = "movt"
    else:
        return None
    immediate = ((first & 0xF) << 12) | (((first >> 10) & 1) << 11)
    immediate |= (((second >> 12) & 7) << 8) | (second & 0xFF)
    register = (second >> 8) & 15
    return kind, register, immediate


def mov_half_candidates(raw: bytes) -> list[dict[str, int | str]]:
    result: list[dict[str, int | str]] = []
    for address in range(0, len(raw) - 3, 2):
        decoded = decode_mov_half(raw, address)
        if decoded is None:
            continue
        kind, register, immediate = decoded
        result.append({
            "va": address,
            "kind": kind,
            "register": register,
            "immediate": immediate,
        })
    return result


def capstone_exact_mov_immediates(raw: bytes) -> list[dict[str, int | str]]:
    """Decode at every halfword; data false positives are allowed, not hidden."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    result: list[dict[str, int | str]] = []
    for address in range(0, len(raw) - 3, 2):
        insn = next(md.disasm(raw[address:address + 4], address, count=1), None)
        if insn is None or not insn.mnemonic.startswith("mov"):
            continue
        for operand in insn.operands:
            if operand.type == ARM_OP_IMM and SOURCE_START <= operand.imm < SOURCE_END:
                result.append({
                    "va": address,
                    "bytes": insn.bytes.hex(),
                    "mnemonic": insn.mnemonic,
                    "op_str": insn.op_str,
                    "immediate": operand.imm,
                })
    return result


def encode_mov_half(kind: str, register: int, immediate: int) -> bytes:
    need(kind in ("movw", "movt"), "fixture kind")
    need(0 <= register < 16 and 0 <= immediate < 0x10000, "fixture operand")
    first = (0xF240 if kind == "movw" else 0xF2C0)
    first |= ((immediate >> 12) & 0xF) | (((immediate >> 11) & 1) << 10)
    second = (((immediate >> 8) & 7) << 12) | (register << 8) | (immediate & 0xFF)
    return struct.pack("<HH", first, second)


def verify_positive_fixtures() -> None:
    # Byte-granular word scanning must find both aligned and unaligned inputs.
    fixture = b"\x00" + struct.pack("<I", TARGETS[0]) + b"\x00" * 8
    need(all_u32_range_hits(fixture, SOURCE_START, SOURCE_END) == [
        {"linked_offset": 1, "value": TARGETS[0]}
    ], "word-scan positive fixture")

    # ldr r0,[pc,#0] at 0 resolves the word at offset 4.
    literal_fixture = struct.pack("<HHI", 0x4800, 0xBF00, TARGETS[1])
    need(source_literal_loads(literal_fixture, literal_fixture) == [{
        "load_va": 0,
        "kind": "ldr16",
        "register": 0,
        "literal_va": 4,
        "value": TARGETS[1],
    }], "literal-load positive fixture")

    # A final 16-bit instruction may legally reach a pool outside the nominal
    # instruction window. It must not be dropped by a four-byte loop bound.
    final16_instructions = struct.pack("<H", 0x4800)
    final16_backing = final16_instructions + b"\x00\x00" + struct.pack("<I", TARGETS[0])
    need(source_literal_loads(final16_instructions, final16_backing) == [{
        "load_va": 0,
        "kind": "ldr16",
        "register": 0,
        "literal_va": 4,
        "value": TARGETS[0],
    }], "final-halfword external-pool fixture")

    ldr32_positive_instructions = struct.pack("<HH", 0xF8DF, 0x0004)
    ldr32_positive_backing = ldr32_positive_instructions + bytes(4) + struct.pack("<I", TARGETS[2])
    need(source_literal_loads(ldr32_positive_instructions, ldr32_positive_backing) == [{
        "load_va": 0,
        "kind": "ldr32-positive",
        "register": 0,
        "literal_va": 8,
        "value": TARGETS[2],
    }], "LDR.W positive fixture")

    ldr32_negative_instructions = bytes(4) + struct.pack("<I", TARGETS[3])
    ldr32_negative_instructions += struct.pack("<HH", 0xF85F, 0x0008)
    need(source_literal_loads(ldr32_negative_instructions,
                              ldr32_negative_instructions) == [{
        "load_va": 8,
        "kind": "ldr32-negative",
        "register": 0,
        "literal_va": 4,
        "value": TARGETS[3],
    }], "LDR.W negative fixture")

    # A truncated final Thumb-2 first half must be ignored rather than reading
    # a nonexistent second halfword from outside the instruction window.
    need(source_literal_loads(struct.pack("<H", 0xF8DF),
                              struct.pack("<H", 0xF8DF) + bytes(6)) == [],
         "truncated LDR.W fixture")

    mov_fixture = encode_mov_half("movw", 3, TARGETS[2] & 0xFFFF)
    mov_fixture += encode_mov_half("movt", 3, TARGETS[2] >> 16)
    need(mov_half_candidates(mov_fixture) == [
        {"va": 0, "kind": "movw", "register": 3,
         "immediate": TARGETS[2] & 0xFFFF},
        {"va": 4, "kind": "movt", "register": 3,
         "immediate": TARGETS[2] >> 16},
    ], "MOVW/MOVT positive fixture")
    need(capstone_exact_mov_immediates(encode_mov_half("movw", 0, 0) +
                                       encode_mov_half("movt", 0, 0)) == [],
         "Capstone negative fixture")


def main() -> None:
    package = load_pinned(PACKAGE, PACKAGE_SHA256)
    need(len(package) == 0x500000, "selected package size")
    load_pinned(N_REPORT,
                "d14282ce16dac0b6a594bfdcce078170d28264c54c515f3b02ad670477901c2a")
    load_pinned(IMAGE1_REPORT,
                "90230a772b149d3f56c5beecf9ebfd3546a5e488d684d6ebcd3fa97e2b502c87")
    load_pinned(Y_REPORT,
                "52774f5a67d1f927a05c71dd7788da2b4601091472ac9e3230b53692c89aacdb")
    load_pinned(AB_REPORT,
                "31312fd987633bba78f4d9edc87c149d766181a50a5c99c01ba6be1632c7ac3f")

    need(sha256(package[0x40000:0x80000]) ==
         "56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf",
         "N full image-1 slot")
    need(sha256(package[0x40000:0x60000]) ==
         "c97865a60fcf0112b0547d41dca99bcad79d5411f90d26f4048cab926a9c4a5f",
         "legacy component range")
    image = package[FILE_START:FILE_END]
    literal_backing = package[FILE_START:0x80000]
    need(len(image) == LINKED_LENGTH and sha256(image) ==
         "d16d0a293fc889b891b15904edc22cbba1f8173012ea07eac691041a649fb675",
         "requested nominal linked image-1 window")
    need(len(literal_backing) == 0x3FE00 and sha256(literal_backing) ==
         "6fb6c9ae101fbe7c6c1fd7f46df6ef2fd9f2fbb8bc28ce23ddc38795b68c1288",
         "positive-VA image-1 slot backing")

    verify_positive_fixtures()

    word_hits = all_u32_range_hits(image, SOURCE_START, SOURCE_END)
    all_literal_hits = literal_loads(image, literal_backing)
    literal_hits = [item for item in all_literal_hits
                    if SOURCE_START <= item["value"] < SOURCE_END]
    external_pool_hits = [item for item in all_literal_hits
                          if item["literal_va"] >= len(image)]
    mov_halves = mov_half_candidates(image)
    movt_high_hits = [item for item in mov_halves
                      if item["kind"] == "movt" and item["immediate"] == 0x5841]
    target_lows = sorted({target & 0xFFFF for target in TARGETS})
    target_low_hits = [item for item in mov_halves
                       if item["kind"] == "movw" and item["immediate"] in target_lows]
    source_low_hits = [item for item in mov_halves
                       if item["kind"] == "movw" and 0 <= item["immediate"] < 0xAB0]
    capstone_hits = capstone_exact_mov_immediates(image)

    need(word_hits == [], "unexpected source-range word")
    need(literal_hits == [], "unexpected source-range literal load")
    need(movt_high_hits == [], "unexpected MOVT #0x5841")
    need(target_low_hits == [], "unexpected target-low MOVW")
    need(capstone_hits == [], "unexpected exact MOV immediate")

    result = {
        "schema": "pre-pd-cross-image-exact-reference-census-v1",
        "target_operations": 0,
        "package_sha256": PACKAGE_SHA256,
        "package_bytes": len(package),
        "source_range": [hex(SOURCE_START), hex(SOURCE_END)],
        "targets": [hex(target) for target in TARGETS],
        "bounds": {
            "n_full_slot_file_range": ["0x40000", "0x80000"],
            "n_full_slot_sha256": sha256(package[0x40000:0x80000]),
            "legacy_component_file_range": ["0x40000", "0x60000"],
            "legacy_component_sha256": sha256(package[0x40000:0x60000]),
            "scan_file_range": [hex(FILE_START), hex(FILE_END)],
            "scan_linked_va_range": ["0x0", hex(LINKED_LENGTH)],
            "scan_sha256": sha256(image),
            "coordinate": "FILE=0x40200+linked_VA",
            "literal_backing_file_range": [hex(FILE_START), "0x80000"],
            "literal_backing_positive_va_range": ["0x0", "0x3fe00"],
            "literal_backing_sha256": sha256(literal_backing),
        },
        "byte_granular_source_range_words": word_hits,
        "thumb_literal_loads_of_source_range_words": literal_hits,
        "thumb_literal_load_candidates_total": len(all_literal_hits),
        "thumb_literal_pools_outside_nominal_window": external_pool_hits,
        "final_nominal_halfword_va": hex(len(image) - 2),
        "final_nominal_halfword_value": hex(u16(image, len(image) - 2)),
        "final_nominal_halfword_examined_as_instruction_start": True,
        "movt_0x5841_candidates": movt_high_hits,
        "movw_exact_target_low_candidates": target_low_hits,
        "movw_low_in_0x0000_0x0aaf_candidate_count": len(source_low_hits),
        "capstone_exact_mov_immediate_candidates": capstone_hits,
        "direct_exact_source_reference_found": False,
        "direct_image1_producer_or_consumer_found": False,
        "mapped_aliases_included": [],
        "mapped_alias_limit": (
            "Existing positive image-1 mapper covers low linked and 0x20000000 RAM "
            "domains, not 0x58410000..0x58410aaf; no alias was invented."
        ),
        "code_data_limit": (
            "Raw scans cover every byte/halfword in the nominal window and may admit "
            "data as instruction candidates; a negative result is bounded to exact words, "
            "PC-relative literal loads, MOVW/MOVT halves, and exact MOV immediates."
        ),
        "capstone_version": capstone.__version__,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
