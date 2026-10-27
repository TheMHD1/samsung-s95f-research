#!/usr/bin/env python3
"""Offline verifier for the v3 RTP normal-log/counter provenance trace."""

from pathlib import Path
import hashlib
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_MCLASS, CS_MODE_THUMB


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
DELTA = HERE / "control-smoke-v3-log-delta.bin"
PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
DELTA_SHA256 = "1995fceeb887265d21610bda20b0f8c792ee1e12b4a587f6c8361fd9f3c4b9ac"
IMAGE1_FILE_BIAS = 0x40200


def need(value, why):
    if not value:
        raise ValueError(why)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


package = PACKAGE.read_bytes()
delta = DELTA.read_bytes()
need(len(package) == 0x500000 and sha256(package) == PACKAGE_SHA256,
     "selected package identity")
need(len(delta) == 56 and sha256(delta) == DELTA_SHA256,
     "v3 log delta identity")
need(delta == (b"t[10]\nt[11]\n[RTP]Frame end\nt[12]\n"
               b"[RTP:NORMAL][365]\nt[1]\n"), "exact v3 log delta")


def image1(va, size):
    return package[IMAGE1_FILE_BIAS + va:IMAGE1_FILE_BIAS + va + size]


def u32(va):
    return struct.unpack("<I", image1(va, 4))[0]


md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)


def instruction(va, size, mnemonic, operands):
    decoded = list(md.disasm(image1(va, size), va, count=1))
    need(len(decoded) == 1, "decode at " + hex(va))
    item = decoded[0]
    need(item.size == size and item.mnemonic == mnemonic and item.op_str == operands,
         "instruction at " + hex(va))


def literal_address(va, immediate):
    return ((va + 4) & ~3) + immediate


def adr_address(va, immediate):
    return ((va + 4) & ~3) + immediate


def direct_thumb_calls(target):
    result = []
    # This is an exact halfword-aligned encoding census over selected image 1.
    for va in range(0, 0x40000, 2):
        decoded = list(md.disasm(image1(va, 4), va, count=1))
        if (decoded and decoded[0].mnemonic in ("bl", "blx") and
                decoded[0].op_str == "#" + hex(target)):
            result.append(va)
    return result


# Exact strings and corrected selected-image mapping: FILE = VA + 0x40200.
need(package.find(b"[RTP]Frame end\n\0") == 0x4BB7C,
     "frame-end string FILE coordinate")
need(package.find(b"[RTP:%s][%d]\n\0") == 0x4BD48,
     "RTP status format FILE coordinate")
need(package.find(b"NORMAL\0\0ONSEN\0\0\0IO\0\0") == 0x5B94C,
     "mode strings FILE coordinate")
need(image1(0xB97C, 16) == b"[RTP]Frame end\n\0", "frame-end string VA")
need(image1(0xBB48, 16) == b"[RTP:%s][%d]\n\0\0\0", "status format VA")
need(image1(0x1B74C, 20) == b"NORMAL\0\0ONSEN\0\0\0IO\0\0", "mode strings VA")

for label, start, end, expected in (
    ("shared orchestrator", 0xB644, 0xB798,
     "77eaad94857db91496e71c80e7dd23f9509519fa5b0da7b2eac7a0119fba4ffa"),
    ("frame function", 0xB8A8, 0xB976,
     "a40c6da321991212c63a8de7b9aca3e7c65edbdf0ac9c75ba1ed62ac5d290395"),
    ("status function", 0xB9F4, 0xBAF2,
     "e93aa53bdc7874bf76c29f7b641cbc5c5d06950063cde8de05bf155bba4ba311"),
    ("mode mapper", 0x1B72C, 0x1B760,
     "48bd50484704a49f0017da91cc1965d235670fed9d7d591e3943b55bbdf6ea7d"),
    ("t reset", 0x19730, 0x1976C,
     "df9db491b11307030ba93e788a9b38a28548f102fb5e265e39ef4977f1623731"),
    ("transition", 0x1976C, 0x198FC,
     "b0dd92041c3ffce8908ec5e8740948e51df7e12e383c4ae02701d1ee20b50327"),
    ("t producer", 0x198FC, 0x19ABC,
     "58d1cf885c6cf3324e505a514d034994049282343a6e3b0936d90225e1f281c1"),
):
    need(sha256(image1(start, end - start)) == expected, label + " slice")

# The shared packaged orchestrator contains the only direct calls to these two
# local functions. Their order within one invocation is status then frame; the
# captured reverse order therefore cannot be assigned to one invocation.
need(direct_thumb_calls(0xB9F4) == [0xB6CE], "status caller census")
need(direct_thumb_calls(0xB8A8) == [0xB72E], "frame caller census")
instruction(0xB6CE, 4, "bl", "#0xb9f4")
instruction(0xB72E, 4, "bl", "#0xb8a8")

# Frame end: nonzero byte at 0x2000049c is cleared, then the literal is sent to
# the existing image-1 formatter/ring sink.
for row in (
    (0xB8B0, 2, "ldr", "r0, [pc, #0xc4]"),
    (0xB8B2, 2, "ldrb", "r0, [r0]"),
    (0xB8B4, 2, "cbz", "r0, #0xb8e8"),
    (0xB8B6, 2, "movs", "r0, #0"),
    (0xB8B8, 2, "ldr", "r1, [pc, #0xbc]"),
    (0xB8BA, 2, "strb", "r0, [r1]"),
    (0xB8BC, 2, "adr", "r0, #0xbc"),
    (0xB8BE, 4, "bl", "#0x1b8c8"),
):
    instruction(*row)
need(literal_address(0xB8B0, 0xC4) == literal_address(0xB8B8, 0xBC) == 0xB978,
     "frame flag literal coordinate")
need(u32(0xB978) == 0x2000049C, "frame flag RAM address")
need(adr_address(0xB8BC, 0xBC) == 0xB97C, "frame format ADR")

# Status mode: halfword 0x200004ac==1 selects code 6 (IO), otherwise
# 0x200004aa==1 selects code 4 (ONSEN), otherwise code 1 (NORMAL). The mapper
# returns the corresponding static string.
for row in (
    (0xBA8A, 2, "movs", "r5, #0"),
    (0xBA8C, 2, "ldr", "r0, [pc, #0x9c]"),
    (0xBA8E, 2, "ldrh", "r0, [r0]"),
    (0xBA90, 2, "cmp", "r0, #1"),
    (0xBA94, 2, "movs", "r5, #6"),
    (0xBA98, 2, "ldr", "r0, [pc, #0x74]"),
    (0xBA9A, 2, "ldrh", "r0, [r0]"),
    (0xBA9C, 2, "cmp", "r0, #1"),
    (0xBAA0, 2, "movs", "r5, #4"),
    (0xBAA4, 2, "movs", "r5, #1"),
    (0xBAA6, 2, "mov", "r0, r5"),
    (0xBAA8, 4, "bl", "#0x1b72c"),
    (0xBAAC, 2, "mov", "r6, r0"),
):
    instruction(*row)
need(literal_address(0xBA8C, 0x9C) == 0xBB2C and u32(0xBB2C) == 0x200004AC,
     "IO-selector address")
need(literal_address(0xBA98, 0x74) == 0xBB10 and u32(0xBB10) == 0x200004AA,
     "ONSEN-selector address")
for row in (
    (0x1B72C, 2, "mov", "r1, r0"),
    (0x1B72E, 2, "cmp", "r1, #1"),
    (0x1B732, 2, "adr", "r0, #0x18"),
    (0x1B736, 2, "cmp", "r1, #4"),
    (0x1B73A, 2, "adr", "r0, #0x18"),
    (0x1B73E, 2, "cmp", "r1, #6"),
    (0x1B742, 2, "adr", "r0, #0x18"),
):
    instruction(*row)
need(adr_address(0x1B732, 0x18) == 0x1B74C, "NORMAL string mapping")
need(adr_address(0x1B73A, 0x18) == 0x1B754, "ONSEN string mapping")
need(adr_address(0x1B742, 0x18) == 0x1B75C, "IO string mapping")

# The status formatter loads an unsigned halfword from 0x200004a0 into r2 and
# passes it unchanged. Only after logging does it increment/reload that same
# halfword and replace values above 9999 with 1.
for row in (
    (0xBAAE, 2, "ldr", "r0, [pc, #0x44]"),
    (0xBAB0, 2, "ldrh", "r2, [r0]"),
    (0xBAB2, 2, "mov", "r1, r6"),
    (0xBAB4, 2, "adr", "r0, #0x90"),
    (0xBAB6, 4, "bl", "#0x1b8c8"),
    (0xBABA, 2, "ldr", "r0, [pc, #0x38]"),
    (0xBABC, 2, "ldrh", "r0, [r0]"),
    (0xBABE, 2, "adds", "r0, r0, #1"),
    (0xBAC0, 2, "ldr", "r1, [pc, #0x30]"),
    (0xBAC2, 2, "strh", "r0, [r1]"),
    (0xBAC4, 2, "mov", "r0, r1"),
    (0xBAC6, 2, "ldrh", "r0, [r0]"),
    (0xBAC8, 4, "movw", "r1, #0x270f"),
    (0xBACC, 2, "cmp", "r0, r1"),
    (0xBACE, 2, "ble", "#0xbad6"),
    (0xBAD0, 2, "movs", "r0, #1"),
    (0xBAD2, 2, "ldr", "r1, [pc, #0x20]"),
    (0xBAD4, 2, "strh", "r0, [r1]"),
):
    instruction(*row)
need(literal_address(0xBAAE, 0x44) == literal_address(0xBABA, 0x38) ==
     literal_address(0xBAC0, 0x30) == literal_address(0xBAD2, 0x20) == 0xBAF4,
     "shared status counter literal coordinate")
need(u32(0xBAF4) == 0x200004A0, "status counter RAM address")
need(adr_address(0xBAB4, 0x90) == 0xBB48, "status format ADR")

# Distinct t counter/reset path. A reset routine writes zero to byte
# 0x2000045c. One packaged transition caller conditionally invokes it, returns,
# then the top-level caller immediately calls the t producer. The producer tail
# increments/reloads that byte and formats it as t[%d]. This is a control-flow
# candidate for t[1], not proof that this exact packaged path ran.
need(direct_thumb_calls(0x19730) == [0x4460, 0x197DA], "t-reset caller census")
need(direct_thumb_calls(0x198FC) == [0x4454, 0x17B8E], "t-producer caller census")
for row in (
    (0x19754, 2, "movs", "r0, #0"),
    (0x19758, 2, "ldr", "r1, [pc, #0xc]"),
    (0x1975A, 2, "strb", "r0, [r1]"),
    (0x197D4, 4, "cmp.w", "sb, #0"),
    (0x197D8, 2, "beq", "#0x197de"),
    (0x197DA, 4, "bl", "#0x19730"),
    (0x444A, 4, "bl", "#0x1976c"),
    (0x444E, 2, "movs", "r2, #0"),
    (0x4450, 2, "mov", "r1, r2"),
    (0x4452, 2, "mov", "r0, r2"),
    (0x4454, 4, "bl", "#0x198fc"),
    (0x19A96, 2, "ldr", "r0, [pc, #0x3c]"),
    (0x19A98, 2, "ldrb", "r0, [r0]"),
    (0x19A9A, 2, "adds", "r0, r0, #1"),
    (0x19A9C, 2, "ldr", "r1, [pc, #0x34]"),
    (0x19A9E, 2, "strb", "r0, [r1]"),
    (0x19AA0, 2, "mov", "r0, r1"),
    (0x19AA2, 2, "ldrb", "r1, [r0]"),
    (0x19AA4, 2, "adr", "r0, #0x30"),
    (0x19AA6, 4, "bl", "#0x1b8c8"),
):
    instruction(*row)
need(literal_address(0x19758, 0x0C) == 0x19768 and u32(0x19768) == 0x2000045C,
     "t reset counter address")
need(literal_address(0x19A96, 0x3C) == literal_address(0x19A9C, 0x34) == 0x19AD4,
     "t producer counter literal")
need(u32(0x19AD4) == 0x2000045C, "t producer counter RAM address")
need(adr_address(0x19AA4, 0x30) == 0x19AD8 and
     image1(0x19AD8, 8) == b"t[%d]\n\0\0", "t format")

print("PASS: v3 delta and selected-package RTP/NORMAL/365/t-reset provenance pinned; "
      "365 is the pre-increment 0x200004a0 halfword; runtime body attribution unproven")
