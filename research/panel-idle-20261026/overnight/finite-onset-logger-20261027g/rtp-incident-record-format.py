#!/usr/bin/env python3
"""Verify v6 RTP incident records and selected-package argument provenance."""

from pathlib import Path
from collections import Counter
import base64
import hashlib
import json
import re
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_MCLASS, CS_MODE_THUMB


HERE = Path(__file__).resolve().parent
RUN = HERE / "onset-v6"
OUTCOME = RUN / "native-outcome.json"
PACKAGE = HERE.parent / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
IMAGE1_FILE_BIAS = 0x40200
PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
OUTCOME_SHA256 = "1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9"
DELTA_SHA256 = "deccf31188b565c7c4c9aadcb838e042c55f81f94ffae7c88093902dc21678ba"


def need(value, why):
    if not value:
        raise ValueError(why)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


outcome_raw = OUTCOME.read_bytes()
need(sha256(outcome_raw) == OUTCOME_SHA256, "v6 outcome identity")
outcome = json.loads(outcome_raw)
need(outcome["Accepted"] is True and outcome["ProtocolPhase"] == "ReadyForHeader" and
     outcome["PreArmGate"] == 0 and outcome["PreArmFault"] == 0 and
     outcome["ArmedGate"] == 1 and outcome["RestoredGate"] == 0 and
     len(outcome["Steps"]) == 16 and not outcome["Errors"], "accepted finite run")

pre = (RUN / "prearm-rt.bin").read_bytes()
armed = (RUN / "armed-rt.bin").read_bytes()
restored = (RUN / "restored-rt.bin").read_bytes()
need(len(pre) == len(armed) == len(restored) == 64, "RT extents")
need(sha256(pre) == "eed5edc3c31936e3d9612360ac9b994ba086e90378f6b8cfa0ce4e89524a0568",
     "prearm RT identity")
need(sha256(armed) == "5ccebe4abe8c8e7b81291392b96ad2f0c34b3691ba9cc02839c1fdb12b292245",
     "armed RT identity")
need(sha256(restored) == "2175e6ce7455123b8071e9edb3b3ada855107d182650c47a307f31bdd39a6ab8",
     "restored RT identity")
need(struct.unpack_from("<H", pre, 6)[0] == 0 and
     struct.unpack_from("<H", armed, 6)[0] == 1 and
     struct.unpack_from("<H", restored, 6)[0] == 0 and
     struct.unpack_from("<H", pre, 10)[0] == 0 and
     struct.unpack_from("<H", restored, 10)[0] == 0x1001,
     "gate and observed event field transition")

baseline = (RUN / "baseline-ring.bin").read_bytes()
post = (RUN / "post-ring.bin").read_bytes()
need(len(baseline) == len(post) == 12 + 0x3C00, "ring extents")
need(sha256(baseline) == "b889e9001401d03257a0673e483da061b6788a5832e891dccd6cb9fbb1ff588e",
     "baseline ring identity")
need(sha256(post) == "c81eaa908cf0b0f3bacc456f846e837b41d390a85c6de666ca7ae0f8091529d1",
     "post ring identity")
need(struct.unpack_from("<III", baseline) == (143, 143, 0), "baseline header")
need(struct.unpack_from("<III", post) == (1899, 1899, 0), "post header")
delta = post[12 + 143:12 + 1899]
need(len(delta) == 1756 and sha256(delta) == DELTA_SHA256, "exact v6 delta")
text = delta.decode("ascii")
lines = text.splitlines()
need(lines[:2] == ["[RTP]END", "[RTP:NORMAL][395]"] and
     lines[-2:] == ["rtp_act_736", "rtp_act_736"], "boundary records")

record_re = re.compile(
    r"^\[RTP\s+(\d+)\]RGB:(\d+) x:\s*(\d+) y:\s*(\d+)/"
    r"c:\s*(\d+)/diff:(\d+)/m:(\w+)$")
rows = []
for line in lines:
    match = record_re.fullmatch(line)
    if match:
        rows.append(tuple(map(int, match.groups()[:6])) + (match.group(7),))
need(len(lines) == 35 and len(rows) == 31, "record counts")
need([row[0] for row in rows] ==
     [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
      18, 19, 20, 21, 24, 25, 26, 27, 32, 33, 34, 35, 38, 39, 40],
     "record sequence IDs")
need(Counter(row[1] for row in rows) == {0: 31}, "RGB values")
need(Counter(row[3] for row in rows) == {2159: 31}, "y values")
need(Counter(row[6] for row in rows) == {"NORMAL": 31}, "mode values")
need(Counter((row[2], row[4], row[5]) for row in rows) == {
    (620, 0, 1252): 8, (621, 0, 1252): 7,
    (630, 4095, 1065): 3, (631, 4095, 1065): 3,
    (570, 492, 1836): 2, (571, 492, 1836): 2,
    (570, 464, 1864): 1, (571, 464, 1864): 1,
    (570, 482, 1846): 1, (571, 482, 1846): 1,
    (570, 470, 1858): 1, (571, 470, 1858): 1,
}, "captured x/c/diff tuples")

package = PACKAGE.read_bytes()
need(len(package) == 0x500000 and sha256(package) == PACKAGE_SHA256,
     "selected package identity")


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
    for va in range(0, 0x40000, 2):
        decoded = list(md.disasm(image1(va, 4), va, count=1))
        if (decoded and decoded[0].mnemonic in ("bl", "blx") and
                decoded[0].op_str == "#" + hex(target)):
            result.append(va)
    return result


need(package.find(b"[RTP]END\n\0") == 0x4B9D8, "RTP END coordinate")
record_format = b"[RTP %3d]RGB:%d x:%4d y:%4d/c:%4d/diff:%d/m:%s\n\0"
need(package.find(record_format) == 0x4CA58, "record format coordinate")
need(package.find(b"rtp_act_%d\n\0") == 0x4C414, "event format coordinate")
need(image1(0xB7D8, 12) == b"[RTP]END\n\0\0\0", "RTP END VA")
need(image1(0xC858, 48) == record_format, "record format VA")
need(image1(0xC214, 12) == b"rtp_act_%d\n\0", "event format VA")

for label, start, end, expected in (
    ("orchestrator", 0xB644, 0xB798,
     "77eaad94857db91496e71c80e7dd23f9509519fa5b0da7b2eac7a0119fba4ffa"),
    ("packed source selector", 0xB7EC, 0xB8A8,
     "78bbf2da87adaa7cc1c9c30cbed5381d079810c8d9e3809a1c0e6744cd6d8c07"),
    ("compare helper", 0xBBBC, 0xBD2E,
     "9161e90f083f9e3f230c6e8d6f2b2f2503c7cbcd6c2ca1525e025f116a30dd71"),
    ("packed unpacker", 0xBD58, 0xC02C,
     "5d9924044096fbef1f5c14db5c289d60d465750ad5ea5be6ce479375542ffcb6"),
    ("record formatter", 0xC5D0, 0xC842,
     "51c6c80996f433f94b2774ae6b86ba61f1e95a306433b98aad6681256deb5827"),
    ("event setter", 0xC1E0, 0xC212,
     "f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102"),
):
    need(sha256(image1(start, end - start)) == expected, label + " slice")

# Shared orchestrator loads y and RGB from fixed halfwords, invokes the packed
# source selector, and has the bounded END literal/flag path.
for row in (
    (0xB6F2, 2, "ldr", "r0, [pc, #0xc0]"),
    (0xB6F4, 2, "ldrh", "r1, [r0]"),
    (0xB6F6, 2, "ldr", "r0, [pc, #0xb8]"),
    (0xB6F8, 2, "ldrh", "r0, [r0]"),
    (0xB6FA, 4, "bl", "#0xb7ec"),
    (0xB752, 2, "adr", "r0, #0x84"),
    (0xB754, 4, "bl", "#0x1b8c8"),
):
    instruction(*row)
need(literal_address(0xB6F2, 0xC0) == 0xB7B4 and u32(0xB7B4) == 0x200004D4,
     "RGB source halfword")
need(literal_address(0xB6F6, 0xB8) == 0xB7B0 and u32(0xB7B0) == 0x200004D0,
     "y source halfword")
need(adr_address(0xB752, 0x84) == 0xB7D8, "RTP END ADR")
need(direct_thumb_calls(0xB7EC) == [0xB6FA], "packed-source caller census")

# The source selector always passes B=*(u32*)0x20000498+8. Depending on its
# ordinary state tests, A is 0x20015000, 0x20015f10, or
# *(u32*)0x2000ba40+8. All three calls preserve y in r2 and RGB in r3.
need(u32(0xB898) == 0x20000498 and u32(0xB8A0) == 0x20015000 and
     u32(0xB8A4) == 0x20015F10 and u32(0xB890) == 0x2000BA40,
     "packed source pointer literals")
need(direct_thumb_calls(0xBD58) == [0xB84C, 0xB874, 0xB88A],
     "packed-unpacker caller census")
for row in (
    (0xB840, 2, "mov", "r3, r6"),
    (0xB842, 2, "mov", "r2, r5"),
    (0xB844, 2, "ldr", "r0, [pc, #0x50]"),
    (0xB846, 2, "ldr", "r1, [r0]"),
    (0xB848, 2, "adds", "r1, #8"),
    (0xB84A, 2, "ldr", "r0, [pc, #0x54]"),
    (0xB84C, 4, "bl", "#0xbd58"),
):
    instruction(*row)

# Four 12-bit unsigned lanes are unpacked from each six-byte group in B; the
# corresponding lane in A is extracted immediately before each helper call.
for row in (
    (0xBE4A, 4, "ldr.w", "r0, [r8]"),
    (0xBE4E, 4, "ubfx", "r0, r0, #0, #0xc"),
    (0xBE58, 4, "ldr.w", "r0, [r8]"),
    (0xBE5C, 4, "ubfx", "r1, r0, #0xc, #0xc"),
    (0xBE68, 4, "ldr.w", "r0, [r8]"),
    (0xBE6C, 2, "lsrs", "r0, r0, #0x18"),
    (0xBE6E, 4, "ldrh.w", "r1, [r8, #4]"),
    (0xBE72, 4, "and", "r1, r1, #0xf"),
    (0xBE76, 4, "add.w", "r1, r0, r1, lsl #8"),
    (0xBE80, 4, "ldrh.w", "r0, [r8, #4]"),
    (0xBE84, 2, "lsrs", "r1, r0, #4"),
    (0xBED0, 4, "ldrh.w", "r1, [r3, r4, lsl #1]"),
    (0xBED4, 2, "ldr", "r3, [r7]"),
    (0xBED6, 4, "ubfx", "r0, r3, #0, #0xc"),
    (0xBEDC, 4, "bl", "#0xbbbc"),
):
    instruction(*row)
need(direct_thumb_calls(0xBBBC) == [0xBEDC, 0xBF18, 0xBF5A, 0xBF90],
     "four-lane compare-helper calls")

# Compare helper computes unsigned absolute A-B. Its NORMAL branches pass
# c=B, x=element index, y=caller scalar, RGB=caller scalar, diff=abs(A-B), and
# mode code 1 to the record formatter.
for row in (
    (0xBC20, 2, "cmp", "r8, r7"),
    (0xBC24, 4, "sub.w", "r0, r7, r8"),
    (0xBC28, 2, "uxth", "r6, r0"),
    (0xBC38, 4, "sub.w", "r0, r8, r7"),
    (0xBC3C, 2, "uxth", "r6, r0"),
    (0xBCD0, 2, "movs", "r0, #1"),
    (0xBCD2, 4, "strd", "r6, r0, [sp]"),
    (0xBCD6, 2, "mov", "r2, sb"),
    (0xBCD8, 2, "mov", "r1, r4"),
    (0xBCDA, 2, "mov", "r0, r7"),
    (0xBCDC, 2, "ldr", "r3, [sp, #0x30]"),
    (0xBCDE, 4, "bl", "#0xc5d0"),
):
    instruction(*row)
need(direct_thumb_calls(0xC5D0) == [0xBC74, 0xBCA8, 0xBCDE, 0xBD1E],
     "record-formatter caller census")

# Record formatter saves its six machine arguments and then arranges the eight
# printf-style fields. The fifth and sixth incoming arguments are loaded from
# the original caller stack at new-sp+0x38.
for row in (
    (0xC5D4, 2, "mov", "r7, r0"),
    (0xC5D6, 2, "mov", "r6, r1"),
    (0xC5D8, 2, "mov", "r8, r2"),
    (0xC5DA, 2, "mov", "sb, r3"),
    (0xC5DC, 4, "ldrd", "sl, r4, [sp, #0x38]"),
    (0xC61A, 4, "bl", "#0x1b72c"),
    (0xC620, 4, "strd", "r7, sl, [sp, #4]"),
    (0xC624, 4, "str.w", "r8, [sp]"),
    (0xC628, 2, "str", "r0, [sp, #0xc]"),
    (0xC62C, 2, "ldr", "r2, [pc, #0x21c]"),
    (0xC62E, 4, "ldr.w", "r1, [r2, r0, lsl #2]"),
    (0xC632, 2, "mov", "r3, r6"),
    (0xC634, 2, "mov", "r2, sb"),
    (0xC636, 2, "adr", "r0, #0x220"),
    (0xC638, 4, "bl", "#0x1b8c8"),
):
    instruction(*row)
need(literal_address(0xC62C, 0x21C) == 0xC84C and u32(0xC84C) == 0x2000BA28,
     "mode-specific record sequence table")
need(adr_address(0xC636, 0x220) == 0xC858, "record format ADR")

# Captured arithmetic agrees with 12-bit A/B provenance. Every observed B=c
# and diff pair has exactly one 12-bit A candidate in this data set.
def a_candidates(c_value, difference):
    return sorted({value for value in (c_value - difference, c_value + difference)
                   if 0 <= value <= 0xFFF})

need(a_candidates(0, 1252) == [1252] and
     a_candidates(4095, 1065) == [3030] and
     a_candidates(492, 1836) == [2328] and
     a_candidates(464, 1864) == [2328] and
     a_candidates(482, 1846) == [2328] and
     a_candidates(470, 1858) == [2328], "captured packed-source arithmetic")

# One event=0x2e0 call enters the common setter; the setter writes 0x1001 to
# root+0x240a and invokes the same format twice, explaining a paired record if
# this packaged body produced the capture.
for row in (
    (0x2036, 4, "mov.w", "r0, #0x2e0"),
    (0x203A, 4, "bl", "#0xc1e0"),
    (0xC1FA, 4, "movw", "r1, #0x1001"),
    (0xC1FE, 2, "subs", "r0, r0, #4"),
    (0xC200, 2, "strh", "r1, [r0, r4]"),
    (0xC202, 2, "mov", "r1, r5"),
    (0xC204, 2, "adr", "r0, #0xc"),
    (0xC206, 4, "bl", "#0x1b8c8"),
    (0xC20A, 2, "mov", "r1, r5"),
    (0xC20C, 2, "adr", "r0, #4"),
    (0xC20E, 4, "bl", "#0x1b8c8"),
):
    instruction(*row)
need(adr_address(0xC204, 0x0C) == adr_address(0xC20C, 0x04) == 0xC214,
     "duplicated event format ADR")
need(direct_thumb_calls(0xC1E0) == [0x203A, 0xC792, 0xC7E0, 0xC836],
     "event-setter caller census")

print("PASS: v6 RTP incident records, 12-bit packed A/B provenance, scalar y/RGB, "
      "and duplicated event-736 producer pinned; physical units remain unassigned")
