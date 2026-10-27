#!/usr/bin/env python3
"""Verify the bounded offline trace for the newly captured ``t[10]\n`` record."""

from pathlib import Path
import hashlib
import struct

from capstone import Cs, CS_ARCH_ARM, CS_MODE_MCLASS, CS_MODE_THUMB


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PACKAGE = BASE / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CAPTURE = HERE / "logger-smoke-once"
IMAGE1_FILE_BIAS = 0x40200
PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
COUNTER_ADDRESS = 0x2000045C


def need(value, why):
    if not value:
        raise ValueError(why)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


package = PACKAGE.read_bytes()
need(len(package) == 0x500000, "selected package size")
need(sha256(package) == PACKAGE_SHA256, "selected package identity")


def image1(va, size):
    start = IMAGE1_FILE_BIAS + va
    return package[start:start + size]


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
    # Thumb-1 PC-relative literal loads use Align(PC + 4, 4) + immediate.
    return ((va + 4) & ~3) + immediate


def adr_address(va, immediate):
    # This 16-bit ADR uses Align(PC + 4, 4) + immediate.
    return ((va + 4) & ~3) + immediate


# Bind this trace to the accepted before/after ring snapshots without changing them.
baseline = (CAPTURE / "baseline-ring.bin").read_bytes()
post = (CAPTURE / "post-ring.bin").read_bytes()
need(len(baseline) == len(post) == 12 + 0x3C00, "ring snapshot extents")
need(sha256(baseline) == "25ab379c50fe087d209870c3e69e31ea7a5eabd7ad1fb11cf40b7ff382f165b7",
     "baseline snapshot identity")
need(sha256(post) == "f0dff6e11caa1da039ae86bc451efc68e3fea5fc1623691d4cbe894bf9afe479",
     "post snapshot identity")
need(struct.unpack_from("<III", baseline) == (5, 5, 0), "baseline cursor/header")
need(struct.unpack_from("<III", post) == (11, 11, 0), "post cursor/header")
changed = [index for index, pair in enumerate(zip(baseline, post)) if pair[0] != pair[1]]
need(changed == [0, 4, 17, 18, 19, 20, 21, 22], "exact changed bytes")
need(post[12 + 5:12 + 11] == b"t[10]\n", "new non-wrapping cursor span")

# Pin the only matching retained C string in the image-1 coordinate space.
needle = b"t[%d]\n\0"
occurrences = []
offset = 0
while True:
    offset = package.find(needle, offset)
    if offset < 0:
        break
    occurrences.append(offset)
    offset += 1
need(occurrences == [0x374D1, 0x3E2F1, 0x59CD8], "all retained format occurrences")
image1_occurrences = [value for value in occurrences if value >= IMAGE1_FILE_BIAS]
need(image1_occurrences == [0x59CD8], "image-1 format occurrence")
need(0x59CD8 - IMAGE1_FILE_BIAS == 0x19AD8, "format FILE/VA coordinate")

# Exact direct-caller function, relevant tail, literal pool, and format.
for label, start, end, expected in (
    ("direct caller", 0x198FC, 0x19ABC,
     "58d1cf885c6cf3324e505a514d034994049282343a6e3b0936d90225e1f281c1"),
    ("counter/log tail", 0x19A96, 0x19ABC,
     "a106ed527de2dd75f2d778a37542d89f5d1826fe653e3274fdeae839bc0059b5"),
    ("literal pool", 0x19ABC, 0x19AD8,
     "9e11555e83349d7fbf6d2f83a1862b50afea3097a93106fd64de26acf856bfc6"),
    ("format literal", 0x19AD8, 0x19AE0,
     "94c3ff564a86a2b99f3e154c5eb602894e12c0ed256d7da4223a930ba7189c7b"),
):
    need(sha256(image1(start, end - start)) == expected, label + " slice")

# Pin the locally described setup: r4 comes from 0x38f4, a configuration pointer
# comes from 0x391c, and r4+0x6c7 selects its halfword at +0xc2 or +0x122.
for row in (
    (0x1990A, 4, "bl", "#0x38f4"),
    (0x1990E, 2, "mov", "r4, r0"),
    (0x19910, 4, "bl", "#0x391c"),
    (0x19914, 4, "str.w", "r0, [sp, #0xf20]"),
    (0x1992C, 4, "ldrb.w", "r0, [r4, #0x6c7]"),
    (0x19930, 2, "cbz", "r0, #0x1993e"),
    (0x19932, 4, "ldr.w", "r0, [sp, #0xf20]"),
    (0x19936, 4, "ldrh.w", "r0, [r0, #0xc2]"),
    (0x1993A, 2, "str", "r0, [sp, #4]"),
    (0x1993C, 2, "b", "#0x19948"),
    (0x1993E, 4, "ldr.w", "r0, [sp, #0xf20]"),
    (0x19942, 4, "ldrh.w", "r0, [r0, #0x122]"),
    (0x19946, 2, "str", "r0, [sp, #4]"),
):
    instruction(*row)

# The direct caller increments a halfword, performs a modulo test, and skips the
# remainder of this path when the remainder is nonzero.
for row in (
    (0x19A06, 4, "ldrh.w", "r0, [r4, #0x6e2]"),
    (0x19A0A, 2, "adds", "r0, r0, #1"),
    (0x19A0C, 4, "strh.w", "r0, [r4, #0x6e2]"),
    (0x19A10, 4, "ldrh.w", "r1, [r4, #0x6e2]"),
    (0x19A14, 2, "ldr", "r0, [sp, #4]"),
    (0x19A16, 4, "udiv", "r2, r1, r0"),
    (0x19A1A, 4, "mls", "r0, r0, r2, r1"),
    (0x19A1E, 2, "cmp", "r0, #0"),
    (0x19A20, 2, "bne", "#0x19aac"),
):
    instruction(*row)

# Both tail literal loads resolve to the same byte at 0x2000045c.  The byte is
# incremented, truncated by STRB, reloaded unsigned by LDRB, and passed in r1.
for row in (
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
need(literal_address(0x19A96, 0x3C) == literal_address(0x19A9C, 0x34) == 0x19AD4,
     "shared counter literal coordinate")
need(u32(0x19AD4) == COUNTER_ADDRESS, "shared counter RAM address")
need(adr_address(0x19AA4, 0x30) == 0x19AD8, "format ADR coordinate")
need(image1(0x19AD8, 8) == b"t[%d]\n\0\0", "exact format bytes")

print("PASS: captured t[10]\\n matches image-1 format VA 0x19ad8; "
      "argument is the post-increment unsigned byte at 0x2000045c; semantics unassigned")
