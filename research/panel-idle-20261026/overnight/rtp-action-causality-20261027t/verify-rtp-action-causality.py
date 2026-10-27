#!/usr/bin/env python3
"""Offline byte verifier for rtp-action-causality.md."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PKG = HERE.parent / "selected-qd-profile-copy-20261027b" / "F_RSM1_BN9659934B_COMMON.bin"
G = HERE.parent / "finite-onset-logger-20261027g"
LATE = G / "fault-context-after-v6"
CURRENT = HERE.parent / "current-host-health-20261027v" / "rt-context-once"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def direct_bl_callers(image: bytes, target: int) -> list[int]:
    """Return halfword-aligned Thumb-2 BL sites targeting a linked VA."""
    callers: list[int] = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
            continue
        s = (first >> 10) & 1
        j1 = (second >> 13) & 1
        j2 = (second >> 11) & 1
        i1 = 1 ^ (j1 ^ s)
        i2 = 1 ^ (j2 ^ s)
        encoded = (s << 24) | (i1 << 23) | (i2 << 22) | ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1)
        resolved = address + 4 + sign_extend(encoded, 25)
        if resolved == target:
            callers.append(address)
    return callers


package = PKG.read_bytes()
require(len(package) == 5_242_880, "package length")
require(sha(package) == "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "package hash")


def image_slice(image: int, start: int, end: int) -> bytes:
    base = 0x200 if image == 0 else 0x40200
    return package[base + start : base + end]


slices = {
    (1, 0x1E68, 0x2040): "c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a",
    (1, 0x1C0C8, 0x1C12C): "643bde5a8297f1cf46505fed8775c3da58bd1ec56a2686cf456cdab8a4c69107",
    (1, 0xC1E0, 0xC212): "f8a6285dd94b3338eff37ded006a2ebff6ecfe7409bef9044f34fd25cdb27102",
    (1, 0xC250, 0xC2EC): "50c6338988042bdf09140937bd552d22e52240b729961970e9f286c6eeaaf32a",
    (1, 0xB644, 0xB796): "18caf88dab3b181c0a8681355986a2a66f1114ddb2cc4582344b215b099a69d6",
    (1, 0xB9F4, 0xBAF2): "e93aa53bdc7874bf76c29f7b641cbc5c5d06950063cde8de05bf155bba4ba311",
    (0, 0x214D4, 0x21512): "6636bd288c51f566df590a89e48aabb761377a5da4a64d01e868a8fdee371049",
    (0, 0xB660, 0xB6BE): "4570965905c97a1152425b2c91a3a821d4a2806e59472711962c8804f152677d",
    (0, 0x3DFC, 0x3E2C): "08f9b07245ee48024d0cc7421aefbe0baac9a8aa5ee93116c62401551de86ef8",
    (0, 0x14910, 0x149BC): "5fcc7bea9301c9aa6b815a92fff05ac97769daf64e9eccbe1bac23f5667e3d18",
    (0, 0x25B24, 0x25B60): "94f4a4f1407e57b0e80f80fa4b16b353b6c41dd7f98d566203b916f1f1387b48",
}
for key, expected in slices.items():
    require(sha(image_slice(*key)) == expected, f"slice {key}")

# Exact event tail: score comparison, action(mode,4), then setter(736).
tail = image_slice(1, 0x202A, 0x203E)
require(tail == bytes.fromhex("5f4507dde0b204211af049f84ff438700af0d1f8"), "event tail")

# Action helper's four mode destinations and OR operations.
helper = image_slice(1, 0x1C0C8, 0x1C12C)
for seq in (
    "42f28640005b284342f286410853",
    "42f28840005b284342f288410853",
    "42f28c40005b284342f28c410853",
):
    require(bytes.fromhex(seq) in helper, f"action helper sequence {seq}")
require(helper.count(bytes.fromhex("42f28c40005b2843")) == 2, "mode4/6 shared bucket")

# Setter stores 1, 0 and 0x1001, followed by two calls to the same logger.
setter = image_slice(1, 0xC1E0, 0xC212)
require(bytes.fromhex("01214ff410500153002142f20e40015341f20101001f0153") in setter, "setter stores")
require(setter.count(bytes.fromhex("0ff0")) == 2, "setter logger call prefix count")
require(package[0x40200 + 0xC214 : 0x40200 + 0xC220] == b"rtp_act_%d\n\0", "setter literal")

# Fault state drives d8 to zero and passes d8/d7 to b644.
c250 = image_slice(1, 0xC250, 0xC2EC)
require(bytes.fromhex("4ff41050005b38b942f20e40005b012802d1") in c250, "c250 fault condition")
require(bytes.fromhex("00201c490870") in c250, "c250 d8 zero")
require(bytes.fromhex("0648017802480078fff7adf9") in c250, "c250 calls b644")
require(package[0x40200 + 0xC2EC : 0x40200 + 0xC2F0] == struct.pack("<I", 0x200004D8), "d8 literal")
require(package[0x40200 + 0xC2F8 : 0x40200 + 0xC2FC] == struct.pack("<I", 0x200004D7), "d7 literal")

# b644's zero argument skips directly to finalization; pre-scan clear and
# predicate path lie in the skipped block.
b644 = image_slice(1, 0xB644, 0xB796)
require(bytes.fromhex("002c43d0") in b644, "b644 zero skip")
require(bytes.fromhex("00f091f9") in b644, "b644 calls b9f4")
require(bytes.fromhex("00f077f8") in b644, "b644 calls b7ec")

# Fixed-offset reference census within the bounded image-1 span. These exact
# MOVW encodings include all explicit materializations of 2486/2488/248c.
image1 = package[0x40200 : 0x60200]
require(direct_bl_callers(image1, 0x1C0C8) == [0x2032, 0xC640, 0xC78A, 0xC7D0, 0xC826], "action direct callers")
require(direct_bl_callers(image1, 0xC1E0) == [0x203A, 0xC792, 0xC7E0, 0xC836], "setter direct callers")
require(direct_bl_callers(image1, 0xC250) == [0x4446], "c250 direct callers")
require(direct_bl_callers(image1, 0xB644) == [0xC2E6], "b644 direct callers")
require(direct_bl_callers(image1, 0xB9F4) == [0xB6CE], "b9f4 direct callers")
require(image1[0x2030 : 0x2032] == bytes.fromhex("0421"), "bit4 caller 2032")
for caller in (0xC78A, 0xC7D0, 0xC826):
    require(image1[caller - 4 : caller - 2] == bytes.fromhex("0421"), f"bit4 caller {caller:x}")
require(image1[0xC63C : 0xC63E] == bytes.fromhex("0221"), "bit2 caller")
expected_refs = {
    "42f28640": [0xBAD8, 0xBCC0, 0xBCCA, 0xBD00, 0xBD0A, 0x1C0E6],
    "42f28641": [0x1C0EE],
    "42f28840": [0x1C0F6],
    "42f28841": [0x1C0FE],
    "42f28c40": [0xBC56, 0xBC60, 0xBC88, 0xBC92, 0x1C106, 0x1C116],
    "42f28c41": [0x1C10E, 0x1C11E],
}
for encoded, expected_offsets in expected_refs.items():
    needle = bytes.fromhex(encoded)
    got = []
    pos = 0
    while True:
        pos = image1.find(needle, pos)
        if pos < 0:
            break
        got.append(pos)
        pos += 1
    require(got == expected_offsets, f"fixed-offset census {encoded}")

# Image-0 poll and emergency action bytes.
image0 = package[0x200 : 0x40200]
common_callers = [
    0x391C, 0x3C2A, 0x5C52, 0x5E9E, 0x60D2, 0x6288, 0x6358,
    0x6EB8, 0x6EC4, 0x6ED0, 0x6F48, 0x7450, 0x93F0, 0x96B2,
    0x9834, 0x9862, 0xD6E2, 0xDBE2, 0x12FBC, 0x130EA, 0x13226,
    0x1C740, 0x1C970, 0x1CAA0, 0x1DDCA, 0x1DF38, 0x1DF86,
    0x1DFD4, 0x214F2, 0x2236E, 0x22420, 0x22486, 0x24CEE,
    0x2E60A, 0x39A54,
]
require(direct_bl_callers(image0, 0xB660) == common_callers, "image0 common-entry callers")
for caller in (0x9834, 0x9862, 0x214F2):
    require(image0[caller - 2 : caller] == bytes.fromhex("1020"), f"selector10 caller {caller:x}")

poll = image_slice(0, 0x214D4, 0x21512)
require(bytes.fromhex("42f20a40005d00f0010030b1") in poll, "image0 fault-bit poll")
require(bytes.fromhex("1020eaf7b5f8") in poll, "selector 0x10 common call")

common = image_slice(0, 0xB660, 0xB6BE)
for call in ("03f006f8", "24f031fc", "1af0f0fd", "fef72ef8", "09f036f9", "20f05df8"):
    require(bytes.fromhex(call) in common, f"common ordered call {call}")

action = image_slice(0, 0x14910, 0x149BC)
require(bytes.fromhex("102c33d10fe0") in action, "selector 0x10 dispatch")
require(bytes.fromhex("00203081012011f0d5f8") in action, "selector action pre-MMIO")
require(bytes.fromhex("10201049c860") in action, "0x4013400c write sequence")
require(bytes.fromhex("f4f7f2fff5f754fb") in action, "history and region calls")
require(package[0x200 + 0x149C0 : 0x200 + 0x149C4] == struct.pack("<I", 0x40134000), "MMIO base 40134000")

mmio = image_slice(0, 0x25B24, 0x25B60)
require(bytes.fromhex("802002490861042002490861") in mmio, "final MMIO writes")
require(package[0x200 + 0x25B58 : 0x200 + 0x25B5C] == struct.pack("<I", 0x40132000), "MMIO base 40132000")
require(package[0x200 + 0x25B5C : 0x200 + 0x25B60] == struct.pack("<I", 0x40131000), "MMIO base 40131000")
early_mmio = image_slice(0, 0x3DFC, 0x3E2C)
require(bytes.fromhex("082002490861") in early_mmio, "early MMIO 8 store")
require(bytes.fromhex("4ff4007002490861") in early_mmio, "conditional MMIO 0x200 store")
require(package[0x200 + 0x3E10 : 0x200 + 0x3E14] == struct.pack("<I", 0x40130000), "MMIO base 40130000")
require(package[0x200 + 0x3E28 : 0x200 + 0x3E2C] == struct.pack("<I", 0x40132000), "conditional MMIO base")

emergency_literal = b"\nSystem Emergence!! \n\0"
require(package[0x200 + 0xB704 : 0x200 + 0xB704 + len(emergency_literal)] == emergency_literal, "emergency literal")

# Retained late windows and their byte-identical later repetition.
late_rt = (LATE / "rt.bin").read_bytes()
late_context = (LATE / "context.bin").read_bytes()
require(len(late_rt) == 256 and sha(late_rt) == "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9", "late RT")
require(len(late_context) == 64 and sha(late_context) == "0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439", "late context")
require((CURRENT / "rt.bin").read_bytes() == late_rt, "later RT equality")
require((CURRENT / "context.bin").read_bytes() == late_context, "later context equality")

expected_halfwords = {
    0x00: 1,
    0x0A: 0x1001,
    0x0E: 0,
    0x86: 7,
    0x88: 0,
    0x8C: 0,
    0xC4: 40,
}
for offset, expected in expected_halfwords.items():
    require(u16(late_rt, offset) == expected, f"RT +{offset:02x}")
require(u16(late_context, 0x06) == 54, "context f06")
require(u16(late_context, 0x08) == 44, "context f08")

print(json.dumps({
    "ok": True,
    "package_sha256": sha(package),
    "slice_count": len(slices),
    "late_rt_sha256": sha(late_rt),
    "action_halfwords": {"2486": u16(late_rt, 0x86), "2488": u16(late_rt, 0x88), "248c": u16(late_rt, 0x8C)},
    "scores": {"f06": u16(late_context, 0x06), "f08": u16(late_context, 0x08)},
    "target_operations": 0,
}, sort_keys=True, separators=(",", ":")))
