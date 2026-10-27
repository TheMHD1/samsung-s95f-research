#!/usr/bin/env python3
"""Offline audit of selected-image SSB transfer mode RAM 0x20000571.

This checker reads retained local files only.  It emits no transport packet
and opens no USB, device, network, or target resource.
"""
from __future__ import annotations

import hashlib
import importlib.util
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_MCLASS
from capstone import CS_MODE_THUMB, Cs


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
DECODER = ROOT / "tcon-research/qd-rt-window-reset-output-reproduce.py"
PROFILE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
DECODER_SHA256 = "fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02"
BIAS = 0x200
MODE = 0x20000571


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, file_offset: int) -> int:
    return struct.unpack_from("<I", data, file_offset)[0]


def decode(data: bytes, va: int, size: int):
    md = Cs(CS_ARCH_ARM,
            CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
    rows = list(md.disasm(data[va + BIAS:va + BIAS + size], va))
    need(rows and rows[0].address == va, "instruction slice did not decode")
    return {i.address: (i.mnemonic, i.op_str, i.bytes.hex()) for i in rows}


def exact(rows, address: int, mnemonic: str, operands: str, raw: str) -> None:
    need(rows.get(address) == (mnemonic, operands, raw),
         f"instruction changed at 0x{address:x}: {rows.get(address)!r}")


def literal_hits(data: bytes, value: int) -> list[int]:
    needle = struct.pack("<I", value)
    # Image 0 occupies stored FILE 0x200..<0x40200.  This is a complete raw
    # exact-word census for that stored image, not an alias/dataflow proof.
    return [offset for offset in range(0x200, 0x40200 - 3)
            if data[offset:offset + 4] == needle]


def main() -> None:
    data = PROFILE.read_bytes()
    need(len(data) == 0x500000 and sha(data) == PROFILE_SHA256,
         "selected profile identity")
    need(sha(DECODER.read_bytes()) == DECODER_SHA256,
         "scatter decoder identity")

    spec = importlib.util.spec_from_file_location("pinned_scatter", DECODER)
    scatter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scatter)
    row0 = struct.unpack_from("<4I", data, 0x3E340)
    need(row0 == (0x3E32C, 0x20000000, 0xF4C, 0x17C),
         "reset scatter row0")
    ram, consumed = scatter.unpack(data, row0[0] + BIAS, row0[2])
    need(consumed == 0x3E961 and
         sha(ram) == "685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3",
         "reset scatter output")
    need(ram[MODE - row0[1]] == 0,
         "packaged reset value of mode byte")

    parser = decode(data, 0x28F24, 0x2CC)

    # Per-header sentinel: parsing begins with an unselected/invalid mode 2.
    exact(parser, 0x28F44, "movs", "r0, #2", "0220")
    exact(parser, 0x28F46, "ldr", "r1, [pc, #0x2a8]", "aa49")
    exact(parser, 0x28F48, "strb", "r0, [r1]", "0870")
    need(u32(data, 0x293F0) == MODE, "shared parser mode literal")

    # The validated target is reduced to its low-byte operation, with bit 4
    # separated, before the mode selection below.  0x203 therefore becomes 3.
    exact(parser, 0x28FB4, "ldrb", "r0, [r4, #0xc]", "207b")
    exact(parser, 0x28FB6, "ubfx", "r0, r0, #4, #1", "c0f30010")
    exact(parser, 0x28FC0, "and", "r0, r0, #0xef", "00f0ef00")
    exact(parser, 0x28FC4, "str", "r0, [r4, #0xc]", "e060")

    # Operations 1/2 select mode 0 (direct-address transfer family).
    exact(parser, 0x29046, "ldr", "r0, [r4, #0xc]", "e068")
    exact(parser, 0x29048, "cmp", "r0, #1", "0128")
    exact(parser, 0x2904A, "beq", "#0x29052", "02d0")
    exact(parser, 0x2904C, "ldr", "r0, [r4, #0xc]", "e068")
    exact(parser, 0x2904E, "cmp", "r0, #2", "0228")
    exact(parser, 0x29050, "bne", "#0x29062", "07d1")
    exact(parser, 0x2905A, "movs", "r0, #0", "0020")
    exact(parser, 0x2905C, "ldr", "r1, [pc, #0x190]", "6449")
    exact(parser, 0x2905E, "strb", "r0, [r1]", "0870")

    # Operations 3/4 select mode 1 (buffered eMMC transfer family).
    exact(parser, 0x29062, "ldr", "r0, [r4, #0xc]", "e068")
    exact(parser, 0x29064, "cmp", "r0, #3", "0328")
    exact(parser, 0x29066, "beq", "#0x2906e", "02d0")
    exact(parser, 0x29068, "ldr", "r0, [r4, #0xc]", "e068")
    exact(parser, 0x2906A, "cmp", "r0, #4", "0428")
    exact(parser, 0x2906C, "bne", "#0x2907c", "06d1")
    exact(parser, 0x29076, "movs", "r0, #1", "0120")
    exact(parser, 0x29078, "ldr", "r1, [pc, #0x174]", "5d49")
    exact(parser, 0x2907A, "strb", "r0, [r1]", "0870")

    # Both PC-relative stores above resolve to VA 0x291f0 / FILE 0x293f0.
    need(0x29060 + 0x190 == 0x291F0 and
         0x2907C + 0x174 == 0x291F0,
         "PC-relative mode producers do not share the expected literal")

    # For family 2 the remap flag is zero, so target 0x203 skips mapper efa4.
    validator = decode(data, 0x29258, 0x15C)
    exact(validator, 0x2927E, "movs", "r0, #0", "0020")
    exact(validator, 0x29280, "ldr", "r1, [pc, #0x130]", "4c49")
    exact(validator, 0x29282, "strb", "r0, [r1]", "0870")
    need(u32(data, 0x295B4) == 0x20000570,
         "family remap-byte literal")
    exact(validator, 0x29334, "adds", "r1, r1, #1", "491c")
    exact(validator, 0x29338, "cmp", "r0, r1", "8842")
    exact(validator, 0x2933A, "beq", "#0x29382", "22d0")

    exact(parser, 0x290C8, "ldr", "r0, [pc, #0x158]", "5648")
    exact(parser, 0x290CA, "ldrb", "r0, [r0]", "0078")
    exact(parser, 0x290CC, "cbz", "r0, #0x290d6", "18b1")
    need(u32(data, 0x29424) == 0x20000570,
         "remap consumer literal")

    # The mode-2 branch is reached only when no supported op selected 0/1.
    exact(parser, 0x290D6, "ldr", "r0, [pc, #0x118]", "4648")
    exact(parser, 0x290D8, "ldrb", "r0, [r0]", "0078")
    exact(parser, 0x290DA, "cmp", "r0, #2", "0228")
    exact(parser, 0x290DC, "bne", "#0x290e0", "00d1")
    exact(parser, 0x290DE, "b", "#0x28f70", "47e7")

    # With target 0x203 normalized to op 3, mode 1 passes that branch and
    # selects the already-established eMMC read leaf.
    exact(parser, 0x2914E, "ldr", "r0, [r4, #0xc]", "e068")
    exact(parser, 0x29150, "cmp", "r0, #3", "0328")
    exact(parser, 0x29176, "bl", "#0x9bd4", "e0f72dfd")

    # Continuations independently interpret 0 as direct-address and 1 as the
    # eMMC-buffer path.  This supports the mode semantics, not just values.
    continuation = decode(data, 0x28B84, 0x130)
    exact(continuation, 0x28BB4, "ldr", "r0, [r4, #8]", "a068")
    exact(continuation, 0x28BB6, "ldr.w", "r1, [sb, #0x18]", "d9f81810")
    exact(continuation, 0x28BBA, "subs", "r0, r0, r1", "401a")
    exact(continuation, 0x28BBC, "str", "r0, [r4, #8]", "a060")
    exact(continuation, 0x28BC8, "ldr", "r0, [r4, #8]", "a068")
    exact(continuation, 0x28BCA, "cbnz", "r0, #0x28c0a", "f0b9")
    exact(continuation, 0x28BE8, "movs", "r0, #6", "0620")
    exact(continuation, 0x28BEA, "str", "r0, [r4, #0xc]", "e060")
    exact(continuation, 0x28BF0, "bl", "#0x29500", "00f086fc")
    exact(continuation, 0x28C0A, "ldr", "r0, [pc, #0xd0]", "3448")
    exact(continuation, 0x28C0C, "ldrb", "r0, [r0]", "0078")
    exact(continuation, 0x28C2E, "mov", "r0, r7", "3846")
    exact(continuation, 0x28C30, "bl", "#0x8054", "dff710fa")
    exact(continuation, 0x28C52, "ldr", "r0, [pc, #0x88]", "2248")
    exact(continuation, 0x28C54, "ldrb", "r0, [r0]", "0078")
    exact(continuation, 0x28C56, "cmp", "r0, #1", "0128")
    exact(continuation, 0x28C80, "bl", "#0x9bd4", "e0f7a8ff")
    need(u32(data, 0x28EDC) == MODE,
         "continuation mode literal")

    # Complete exact-word census over stored image0.  Nearby direct pointer
    # literals are included to catch a future composite-word rewrite.  This
    # cannot prove absence of computed pointers or DMA/alias writers.
    expected = {
        0x2000056C: [0x28EC0, 0x29100, 0x29420],
        0x20000570: [0x29424, 0x295B4],
        0x20000571: [0x0F348, 0x28EDC, 0x290EC, 0x293F0],
        0x20000574: [0x29658],
    }
    for value, hits in expected.items():
        need(literal_hits(data, value) == hits,
             f"exact image0 pointer census changed for 0x{value:x}")

    slices = {
        (0x29124, 0x293F0):
            "101fe3f099e3d9b75ed873206120a8753486edeefe3019b55648e3758a8c2bc4",
        (0x29458, 0x295B4):
            "febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234",
        (0x28D84, 0x28EB4):
            "09c88596911a2ab85a7a415c0726384d82ab78acd8655968ff22cd8f275f3786",
        (0x0F1A4, 0x0F348):
            "6570caec871c718fec0f9adeca238eb57bdfed12e35b366364eb3e62e64d5ab8",
    }
    for (start, stop), digest in slices.items():
        need(sha(data[start:stop]) == digest,
             f"bounded source slice changed at FILE 0x{start:x}")

    # Pure local semantic model, deliberately not serialized as a packet.
    target = 0x203
    family = target >> 8
    operation = (target & 0xFF) & 0xEF
    mode = 0 if operation in (1, 2) else 1 if operation in (3, 4) else 2
    need(family == 2 and operation == 3 and mode == 1,
         "0x203 family/operation/mode model")

    print("PASS")
    print("target_0x203_normalized_operation=3 transfer_mode=1")
    print("mode_2_semantics=per_header_sentinel_or_unselected_operation")
    print("target_0x203_local_branch_reachable=true live_request_sent=false")


if __name__ == "__main__":
    main()
