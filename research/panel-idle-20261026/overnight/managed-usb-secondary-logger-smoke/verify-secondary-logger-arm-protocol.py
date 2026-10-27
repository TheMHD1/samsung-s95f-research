#!/usr/bin/env python3
"""Offline proof of the fixed target-0x102 two-OUT volatile-write path.

This checker reads retained local evidence only.  It does not serialize a live
request, open USB, or access a target, device, network endpoint, or writer.
All checks remain active under ``python -O``.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_MCLASS
from capstone import CS_MODE_THUMB, Cs


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parent
PROFILE = BASE / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CURRENT = BASE / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
DECODER = ROOT / "tcon-research/qd-rt-window-reset-output-reproduce.py"
READ_REPORT = ROOT / "tcon-research/ssb-device-read-protocol-20261027.md"
MODE_REPORT = ROOT / "tcon-research/ssb-mode-gate-followup-20261027.md"
D3_BLOCK = BASE / "rt-onset-memory-20261027c/rt-block-read-once/returned-block.bin"
D3_RECORD = BASE / "rt-onset-memory-20261027c/rt-block-read-once/record.json"

PROFILE_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
CURRENT_SHA = "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"
DECODER_SHA = "fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02"
READ_REPORT_SHA = "6bafcfb45e95b18a3646b71e5da37a43df4a863e6368e57dfb808e139da7021c"
MODE_REPORT_SHA = "1d0539352a82a6c51a5b084de5d42fc8c272f1a3ca6b821b217bb75add680c9c"
D3_BLOCK_SHA = "7044ed744404edf22eff6d90a7cc9cdcd5704cbbad5e0e2f85de03acfa23217d"
D3_RECORD_SHA = "f81e8878ce10cd3d4c8e3c67efdaf68f22b73bf6db6f540038dad295305f4bdd"
I0 = 0x200
I1 = 0x40200


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def decode(data: bytes, bias: int, va: int, size: int):
    md = Cs(CS_ARCH_ARM,
            CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
    rows = list(md.disasm(data[bias + va:bias + va + size], va))
    need(rows and rows[0].address == va,
         f"instruction slice did not decode at VA 0x{va:x}")
    return {i.address: (i.mnemonic, i.op_str, i.bytes.hex()) for i in rows}


def exact(rows, address: int, mnemonic: str, operands: str, raw: str) -> None:
    need(rows.get(address) == (mnemonic, operands, raw),
         f"instruction changed at VA 0x{address:x}: {rows.get(address)!r}")


def movw_2406_hits(data: bytes, bias: int, size: int) -> list[int]:
    md = Cs(CS_ARCH_ARM,
            CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
    hits = []
    for va in range(0, size - 3, 2):
        rows = list(md.disasm(data[bias + va:bias + va + 4], va, count=1))
        if (rows and rows[0].size == 4 and rows[0].mnemonic == "movw" and
                rows[0].op_str.endswith(", #0x2406")):
            hits.append(va)
    return hits


def main() -> None:
    profile = PROFILE.read_bytes()
    current = CURRENT.read_bytes()
    need(len(profile) == 0x500000 and sha(profile) == PROFILE_SHA,
         "selected package identity")
    need(len(current) == 0x500000 and sha(current) == CURRENT_SHA,
         "current acquired image identity")
    need(sha(DECODER.read_bytes()) == DECODER_SHA, "scatter decoder identity")
    need(sha(READ_REPORT.read_bytes()) == READ_REPORT_SHA,
         "device-read source report identity")
    need(sha(MODE_REPORT.read_bytes()) == MODE_REPORT_SHA,
         "mode-gate source report identity")

    # The proposed bytes are modeled locally but never sent.
    header = struct.pack("<III", 0x102, 0x47012406, 2)
    payload = bytes.fromhex("0100")
    need(header.hex() == "020100000624014702000000", "fixed header encoding")
    need(payload == b"\x01\x00", "fixed payload encoding")

    # FILE = VA + 0x200 for image 0.  Header parsing accepts target 0x102,
    # requires a complete 12-byte header and nonzero length, and applies the
    # 16 MiB range test only when the high family is exactly 2.
    validator = decode(profile, I0, 0x29258, 0x15C)
    exact(validator, 0x29264, "ldr", "r0, [r4, #0xc]", "e068")
    exact(validator, 0x29266, "ubfx", "r8, r0, #8, #0x10", "c0f30f28")
    exact(validator, 0x29270, "cmp.w", "r8, #0", "b8f1000f")
    exact(validator, 0x2927E, "movs", "r0, #0", "0020")
    exact(validator, 0x29282, "strb", "r0, [r1]", "0870")
    exact(validator, 0x29284, "cmp", "r6, #0xc", "0c2e")
    exact(validator, 0x29286, "bhs", "#0x2929a", "08d2")
    exact(validator, 0x2929A, "ldr", "r0, [r4, #8]", "a068")
    exact(validator, 0x2929C, "cbnz", "r0, #0x292a2", "08b9")
    exact(validator, 0x292E8, "ldr", "r0, [r4, #0xc]", "e068")
    exact(validator, 0x292EA, "cmp.w", "r0, #0x102", "b0f5817f")
    exact(validator, 0x292EE, "beq", "#0x29382", "48d0")
    exact(validator, 0x29382, "cmp.w", "r8, #2", "b8f1020f")
    exact(validator, 0x29386, "bne", "#0x293b0", "13d1")
    exact(validator, 0x293B0, "movs", "r0, #0", "0020")
    need(u32(profile, I0 + 0x293B4) == 0x20000570,
         "family-remap flag literal")

    # The parser normalizes 0x102 to operation 2, selects direct mode 0,
    # leaves the family-1 address unchanged, bounds the current chunk, and
    # schedules an OUT receive directly into that address via VA 0x7fce.
    parser = decode(profile, I0, 0x28F24, 0x2CC)
    exact(parser, 0x28F50, "ldr", "r0, [r4, #0x10]", "2069")
    exact(parser, 0x28F52, "ldr", "r0, [r0, #8]", "8068")
    exact(parser, 0x28F54, "str", "r0, [r4, #8]", "a060")
    exact(parser, 0x28F58, "ldr", "r0, [r0]", "0068")
    exact(parser, 0x28F5A, "str", "r0, [r4, #0xc]", "e060")
    exact(parser, 0x28F5E, "ldr", "r0, [r0, #4]", "4068")
    exact(parser, 0x28F60, "str", "r0, [r4, #4]", "6060")
    exact(parser, 0x28F68, "bl", "#0x29258", "00f076f9")
    exact(parser, 0x28FB4, "ldrb", "r0, [r4, #0xc]", "207b")
    exact(parser, 0x28FC0, "and", "r0, r0, #0xef", "00f0ef00")
    exact(parser, 0x28FC4, "str", "r0, [r4, #0xc]", "e060")
    exact(parser, 0x2904C, "ldr", "r0, [r4, #0xc]", "e068")
    exact(parser, 0x2904E, "cmp", "r0, #2", "0228")
    exact(parser, 0x2905A, "movs", "r0, #0", "0020")
    exact(parser, 0x2905E, "strb", "r0, [r1]", "0870")
    exact(parser, 0x290C8, "ldr", "r0, [pc, #0x158]", "5648")
    exact(parser, 0x290CA, "ldrb", "r0, [r0]", "0078")
    exact(parser, 0x290CC, "cbz", "r0, #0x290d6", "18b1")
    exact(parser, 0x290E0, "ldr", "r1, [pc, #0x130]", "4c49")
    exact(parser, 0x290E2, "ldr", "r0, [r4, #8]", "a068")
    exact(parser, 0x290E6, "cmp", "r0, r1", "8842")
    exact(parser, 0x290F4, "str", "r0, [r1]", "0860")
    exact(parser, 0x2912A, "ldr", "r0, [r4, #0xc]", "e068")
    exact(parser, 0x2912C, "cmp", "r0, #2", "0228")
    exact(parser, 0x2913C, "ldr", "r0, [pc, #0xe8]", "3a48")
    exact(parser, 0x2913E, "ldrh", "r0, [r0]", "0088")
    exact(parser, 0x29140, "uxth", "r3, r0", "83b2")
    exact(parser, 0x29142, "mov", "r1, r7", "3946")
    exact(parser, 0x29146, "ldr", "r2, [r4, #4]", "6268")
    exact(parser, 0x29148, "bl", "#0x7fce", "def741ff")
    exact(parser, 0x2914C, "b", "#0x291ec", "4ee0")
    need(u32(profile, I0 + 0x29214) == 0x20000548 and
         u32(profile, I0 + 0x29224) == 0x20000570 and
         u32(profile, I0 + 0x29228) == 0x2000054C,
         "cap, remap and current-chunk literals")

    # VA 0x7fce stores the caller's address and length in the OUT endpoint
    # context without translating the address, then calls the lower scheduler.
    receive = decode(profile, I0, 0x7FCE, 0x3C)
    exact(receive, 0x7FD6, "mov", "r6, r2", "1646")
    exact(receive, 0x7FD8, "mov", "r8, r3", "9846")
    exact(receive, 0x7FEA, "str", "r6, [r4, #0x10]", "2661")
    exact(receive, 0x7FEC, "str.w", "r8, [r4, #0x18]", "c4f81880")
    exact(receive, 0x7FF4, "strb", "r0, [r4, #1]", "6070")
    exact(receive, 0x7FFC, "str", "r6, [r4, #0x14]", "6661")
    exact(receive, 0x8002, "bl", "#0x2ac10", "22f005fe")

    # The OUT scheduler rounds nonzero requested receive capacity up to a
    # multiple of endpoint max-packet size, but keeps the pointer unchanged.
    scheduler = decode(profile, I0, 0x2AC10, 0xC4)
    exact(scheduler, 0x2AC20, "ldrb", "r0, [r4, #1]", "6078")
    exact(scheduler, 0x2AC24, "bne", "#0x2ac76", "27d1")
    exact(scheduler, 0x2AC86, "ldr", "r0, [r4, #0x18]", "a069")
    exact(scheduler, 0x2AC90, "ldr", "r0, [r4, #8]", "a068")
    exact(scheduler, 0x2AC92, "subs", "r0, r0, #1", "401e")
    exact(scheduler, 0x2AC94, "ldr", "r1, [r4, #0x18]", "a169")
    exact(scheduler, 0x2AC96, "add", "r0, r1", "0844")
    exact(scheduler, 0x2AC9A, "udiv", "r0, r0, r1", "b0fbf1f0")
    exact(scheduler, 0x2AC9E, "mul", "r8, r0, r1", "00fb01f8")
    exact(scheduler, 0x2ACA2, "mov", "r2, r8", "4246")
    exact(scheduler, 0x2ACA6, "ldr", "r1, [r4, #0x10]", "2169")
    exact(scheduler, 0x2ACA8, "bl", "#0x280c", "d7f7b0fd")

    # The descriptor writer ultimately stores r6 + descriptor offset into the
    # DMA address register.  For a 2-byte request on the 512-byte endpoint,
    # one descriptor has offset zero, hence the bus address is 0x47012406.
    descriptor = decode(profile, I0, 0x280C, 0x17C)
    exact(descriptor, 0x2810, "mov", "r6, r1", "0e46")
    exact(descriptor, 0x2818, "cmp", "r2, #0", "002a")
    exact(descriptor, 0x2896, "movs", "r4, #0", "0024")
    exact(descriptor, 0x28AA, "subs", "r0, r2, r4", "101b")
    exact(descriptor, 0x28AC, "cmp", "r0, r5", "a842")
    exact(descriptor, 0x28DA, "subs", "r0, r2, r4", "101b")
    exact(descriptor, 0x28DC, "cmp", "r0, r5", "a842")
    exact(descriptor, 0x296E, "adds", "r0, r6, r4", "3019")
    exact(descriptor, 0x2970, "str", "r0, [r1, #4]", "4860")

    # The OUT completion callback distinguishes header phase (remaining zero)
    # from payload phase (remaining nonzero).  It subtracts the actual DMA
    # completion count, advances the address, and only rearms a 12-byte header
    # after the remainder reaches zero.
    completion = decode(profile, I0, 0x28CF0, 0x1D6)
    exact(completion, 0x28D26, "ldr", "r0, [r4, #8]", "a068")
    exact(completion, 0x28D28, "cbnz", "r0, #0x28d66", "e8b9")
    exact(completion, 0x28D30, "bl", "#0x28f24", "00f0f8f8")
    exact(completion, 0x28D66, "ldr", "r0, [r4, #8]", "a068")
    exact(completion, 0x28D6E, "bl", "#0x260c", "d9f74dfc")
    exact(completion, 0x28D74, "ldr", "r0, [r4, #8]", "a068")
    exact(completion, 0x28D76, "sub.w", "r0, r0, sb", "a0eb0900")
    exact(completion, 0x28D7A, "str", "r0, [r4, #8]", "a060")
    exact(completion, 0x28D7C, "ldr", "r0, [r4, #4]", "6068")
    exact(completion, 0x28D7E, "add", "r0, sb", "4844")
    exact(completion, 0x28D80, "str", "r0, [r4, #4]", "6060")
    exact(completion, 0x28D82, "ldr", "r0, [r4, #8]", "a068")
    exact(completion, 0x28D84, "cmp", "r0, #0", "0028")
    exact(completion, 0x28D98, "movs", "r0, #6", "0620")
    exact(completion, 0x28DA0, "bl", "#0x29500", "00f0aefb")
    exact(completion, 0x28E14, "ldr", "r0, [pc, #0xd4]", "3548")
    exact(completion, 0x28E18, "cbnz", "r0, #0x28e74", "60bb")
    exact(completion, 0x28E2C, "uxth", "r3, r0", "83b2")
    exact(completion, 0x28E32, "ldr", "r2, [r4, #4]", "6268")
    exact(completion, 0x28E34, "bl", "#0x7fce", "dff7cbf8")

    count = decode(profile, I0, 0x260C, 0x48)
    exact(count, 0x2634, "uxth", "r4, r4", "a4b2")
    exact(count, 0x2636, "add", "r0, r4", "2044")
    exact(count, 0x264A, "ldr", "r4, [r1, #8]", "8c68")
    exact(count, 0x264C, "muls", "r4, r2, r4", "5443")
    exact(count, 0x264E, "subs", "r0, r4, r0", "201a")

    rearm = decode(profile, I0, 0x29500, 0x34)
    exact(rearm, 0x29518, "ldr", "r0, [r4, #0xc]", "e068")
    exact(rearm, 0x2951A, "cmp", "r0, #6", "0628")
    exact(rearm, 0x2951E, "ldr", "r0, [r4, #8]", "a068")
    exact(rearm, 0x29520, "cbnz", "r0, #0x29530", "30b9")
    exact(rearm, 0x29524, "movs", "r3, #0xc", "0c23")
    exact(rearm, 0x2952A, "bl", "#0x7fce", "def750fd")

    # The reset-scatter descriptor proves bulk OUT endpoint 0x02 has a
    # 512-byte max packet; this explains the 2 -> 512 receive-capacity round.
    need(sha(DECODER.read_bytes()) == DECODER_SHA, "decoder pin before import")
    spec = importlib.util.spec_from_file_location("pinned_scatter", DECODER)
    scatter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scatter)
    row0 = struct.unpack_from("<4I", profile, 0x3E340)
    need(row0 == (0x3E32C, 0x20000000, 0xF4C, 0x17C),
         "package image0 scatter row0")
    ram0, consumed0 = scatter.unpack(profile, row0[0] + I0, row0[2])
    need(consumed0 == 0x3E961 and
         sha(ram0) == "685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3",
         "package image0 scatter output")
    need(ram0.find(bytes.fromhex("07050202000200")) == 0x584,
         "bulk OUT endpoint descriptor and 512-byte max packet")

    # FILE = VA + 0x40200 for image 1.  Its root accessor loads the pointer at
    # CPU 0x200004e0; decoded row0 initializes that pointer to 0x20010000.
    root = decode(profile, I1, 0x38F4, 0x10)
    exact(root, 0x38FC, "ldr", "r0, [pc, #4]", "0148")
    exact(root, 0x38FE, "ldr", "r0, [r0]", "0068")
    exact(root, 0x3900, "bx", "lr", "7047")
    need(u32(profile, I1 + 0x3904) == 0x200004E0,
         "image1 root-pointer-slot literal")
    need(struct.unpack_from("<2I", profile, I1) == (0x20020000, 0x369),
         "image1 vector identity")
    anchor = 0x174
    table = anchor + u32(profile, I1 + anchor)
    end = anchor + u32(profile, I1 + anchor + 4)
    need((table, end) == (0x1D6A4, 0x1D734), "image1 scatter bounds")
    image1_rows = [struct.unpack_from("<4I", profile, I1 + table + 16 * i)
                   for i in range((end - table) // 16)]
    need(image1_rows[0] == (0x1D860, 0x20000000, 0x4F8, 0x17C),
         "image1 initialized row0")
    ram1, consumed1 = scatter.unpack(profile, I1 + image1_rows[0][0],
                                     image1_rows[0][2])
    need(consumed1 == 0x5DB5B and len(ram1) == 0x4F8 and
         sha(ram1) == "76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8",
         "image1 row0 decode")
    need(u32(ram1, 0x4E0) == 0x20010000,
         "image1 secondary-context root")
    need(0x20010000 + 0x2406 == 0x20012406 and
         0x20012406 + 0x27000000 == 0x47012406,
         "CPU object and non-A-core bus alias arithmetic")

    # Current acquired image mapper independently proves the 0x27... alias
    # addend for non-A core tags.  The protocol above does not call this
    # mapper for family 1; the host-supplied 0x47012406 is already the bus
    # address and is programmed unchanged.
    mapper = decode(current, I0, 0x9A48, 0x26)
    exact(mapper, 0x9A48, "mov", "r1, r0", "0146")
    exact(mapper, 0x9A4E, "cmp.w", "r1, #0x20000000", "b1f1005f")
    exact(mapper, 0x9A56, "cmp", "r1, r0", "8142")
    exact(mapper, 0x9A5A, "cmp", "r2, #0xa", "0a2a")
    exact(mapper, 0x9A5E, "add.w", "r0, r1, #0x25000000", "01f11450")
    exact(mapper, 0x9A64, "add.w", "r0, r1, #0x27000000", "01f11c50")
    need(u32(current, I0 + 0x9A70) == 0xE00FDFDC and
         u32(current, I0 + 0x9A74) == 0x20200000,
         "current mapper literals")

    # D3 retained a successful read of 0x47012400..0x470124ff.  The halfword
    # at offset 6 was zero at capture time.  This is not a claim that it is
    # still zero at a future write instant.
    d3 = D3_BLOCK.read_bytes()
    need(len(d3) == 256 and sha(d3) == D3_BLOCK_SHA,
         "D3 RT block identity")
    d3_record_raw = D3_RECORD.read_bytes()
    need(sha(d3_record_raw) == D3_RECORD_SHA,
         "D3 RT record identity")
    d3_record = json.loads(d3_record_raw)
    need(d3_record["request"] == {
        "target": "0x101", "address": "0x47012400", "length": 256},
        "D3 RT read request")
    need(d3_record["cleanup_stdout"].strip() == "STAGE_ABSENT",
         "D3 RT read cleanup")
    need(struct.unpack_from("<H", d3, 6)[0] == 0,
         "captured secondary logger halfword")

    # Exact direct-immediate census for +0x2406.  Image 0 has no MOVW of this
    # offset.  Image 1 has the logger gate plus two save/set/restore sequences.
    # This does not exclude computed offsets or aliases.
    need(movw_2406_hits(profile, I0, 0x40000) == [],
         "unexpected direct +0x2406 immediate in image0")
    expected_i1 = [0x183D8, 0x183E2, 0x183EE, 0x18548, 0x18552,
                   0x1B8D6, 0x1BA54, 0x1BA62, 0x1BA6E, 0x1BAAA, 0x1BAB4]
    need(movw_2406_hits(profile, I1, 0x20000) == expected_i1,
         "image1 direct +0x2406 immediate census")

    logger = decode(profile, I1, 0x1B8C8, 0x78)
    exact(logger, 0x1B8D6, "movw", "r0, #0x2406", "42f20640")
    exact(logger, 0x1B8DA, "ldrb", "r0, [r0, r5]", "405d")
    exact(logger, 0x1B8DC, "and", "r0, r0, #1", "00f00100")
    exact(logger, 0x1B8E0, "cbz", "r0, #0x1b938", "50b3")

    save1 = decode(profile, I1, 0x183B8, 0x1A4)
    exact(save1, 0x183D8, "movw", "r0, #0x2406", "42f20640")
    exact(save1, 0x183DC, "ldrb", "r0, [r0, r5]", "405d")
    exact(save1, 0x183DE, "and", "r8, r0, #1", "00f00108")
    exact(save1, 0x183E6, "ldrh", "r0, [r0, r5]", "405b")
    exact(save1, 0x183E8, "bic", "r0, r0, #1", "20f00100")
    exact(save1, 0x183EC, "adds", "r0, r0, #1", "401c")
    exact(save1, 0x183F2, "strh", "r0, [r1, r5]", "4853")
    exact(save1, 0x1854C, "ldrh", "r0, [r0, r5]", "405b")
    exact(save1, 0x1854E, "bfi", "r0, r8, #0, #1", "68f30000")
    exact(save1, 0x18556, "strh", "r0, [r1, r5]", "4853")

    save2 = decode(profile, I1, 0x1BA24, 0x98)
    exact(save2, 0x1BA54, "movw", "r0, #0x2406", "42f20640")
    exact(save2, 0x1BA58, "ldrb", "r0, [r0, r4]", "005d")
    exact(save2, 0x1BA5A, "and", "r0, r0, #1", "00f00100")
    exact(save2, 0x1BA60, "strb", "r0, [r1]", "0870")
    exact(save2, 0x1BA66, "ldrh", "r0, [r0, r4]", "005b")
    exact(save2, 0x1BA68, "bic", "r0, r0, #1", "20f00100")
    exact(save2, 0x1BA6C, "adds", "r0, r0, #1", "401c")
    exact(save2, 0x1BA72, "strh", "r0, [r1, r4]", "0853")
    exact(save2, 0x1BAAE, "ldrh", "r0, [r0, r4]", "005b")
    exact(save2, 0x1BAB0, "bfi", "r0, r1, #0, #1", "61f30000")
    exact(save2, 0x1BAB8, "strh", "r0, [r1, r4]", "0853")

    event = decode(profile, I1, 0xC1E0, 0x32)
    exact(event, 0xC1EC, "mov.w", "r0, #0x2400", "4ff41050")
    exact(event, 0xC1F0, "strh", "r1, [r0, r4]", "0153")
    exact(event, 0xC1F4, "movw", "r0, #0x240e", "42f20e40")
    exact(event, 0xC1F8, "strh", "r1, [r0, r4]", "0153")
    exact(event, 0xC1FA, "movw", "r1, #0x1001", "41f20101")
    exact(event, 0xC200, "strh", "r1, [r0, r4]", "0153")
    exact(event, 0xC206, "bl", "#0x1b8c8", "0ff05ffb")
    exact(event, 0xC20E, "bl", "#0x1b8c8", "0ff05bfb")

    slices = {
        (I0 + 0x28CF0, I0 + 0x28EC6):
            "7c165cbf88ebd117d929ee9c1dd8594c442b4c73b78b0fc12ad0273ba1c952b7",
        (I0 + 0x28F24, I0 + 0x291F0):
            "101fe3f099e3d9b75ed873206120a8753486edeefe3019b55648e3758a8c2bc4",
        (I0 + 0x29258, I0 + 0x293B4):
            "febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234",
        (I0 + 0x29500, I0 + 0x29534):
            "19b640cf59ed8e61dbefe6e4d59ce3188f4d20be75e9d8d432bd483ada39561f",
        (I0 + 0x7FCE, I0 + 0x800A):
            "fec5159ee7f5e38ae07f64d070d783af0a98bd2599905c6c8d1d8b0c243a9ebc",
        (I0 + 0x2AC10, I0 + 0x2ACD4):
            "ca6d2a5c81c82c37ae523712eee79e1549fb801e2e60ddf4574edfed1166ef48",
        (I0 + 0x280C, I0 + 0x2988):
            "42c9a28b25bc9dddca9436fdf64172897c4a381584a5f4a48d8b7753d65fe4f2",
        (I0 + 0x260C, I0 + 0x2654):
            "dadfb1866a5ce16b1b8ef60a85814d34e13d287ccf21277cc10479dbd29f5225",
        (I1 + 0x1B8C8, I1 + 0x1B940):
            "47abdf7963385a87473920daae5212943303054ceb9ba3df92c3c31928fb545e",
        (I1 + 0x183B8, I1 + 0x1855C):
            "42158128055eed35af26373855871473a0bfbcc94159d5046c83fde1010d4778",
        (I1 + 0x1BA24, I1 + 0x1BABC):
            "23daaceae0a229c5ac76796f50b8200ba0635b8da533ee09ca170a822f2128da",
        (I1 + 0xC1E0, I1 + 0xC212):
            "f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102",
    }
    for (start, stop), digest in slices.items():
        need(sha(profile[start:stop]) == digest,
             f"bounded package slice changed at FILE 0x{start:x}")

    # Pure state model.  Exact count 2 reaches the finish/rearm state.  A
    # one-byte completion leaves one byte pending at address+1; an overcount
    # underflows the unsigned remaining field.  This is why a timed-out or
    # partial transaction must never be followed by a fresh header retry.
    target, address, length = struct.unpack("<III", header)
    family = target >> 8
    operation = (target & 0xFF) & 0xEF
    mode = 0 if operation in (1, 2) else 1 if operation in (3, 4) else 2
    remap = 1 if family == 0 else 0
    chunk = min(length, 0x200)
    receive_capacity = ((chunk + 0x200 - 1) // 0x200) * 0x200
    need((family, operation, mode, remap, chunk, receive_capacity) ==
         (1, 2, 0, 0, 2, 512), "fixed request semantic model")
    need((length - 1, address + 1) == (1, 0x47012407),
         "one-byte partial state")
    need(((length - 12) & 0xFFFFFFFF) == 0xFFFFFFF6,
         "overcount underflow hazard model")
    need((length - 2, address + 2) == (0, 0x47012408),
         "exact payload finish state")

    print("PASS")
    print("target_0x102=family_1_operation_2_mode_0_direct_OUT_payload")
    print("fixed_header_hex=020100000624014702000000 payload_hex=0100")
    print("payload_IN_ack=false exact_payload_finish=rearm_12_byte_header")
    print("firmware_alignment_restriction=false armed_receive_capacity=512")
    print("live_or_writer_operations=0")


if __name__ == "__main__":
    main()
