#!/usr/bin/env python3
"""Offline verifier for the ordinary RTP score-input provenance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CONTEXT = HERE / "fault-context-after-v6/context.bin"
RT = HERE / "fault-context-after-v6/rt.bin"
IMAGE1_BIAS = 0x40200


def need(value: bool, why: str) -> None:
    if not value:
        raise ValueError(why)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pinned(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    need(sha256(raw) == expected, "identity: " + str(path))
    return raw


def u16(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def signed(value: int, bits: int) -> int:
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def thumb_bl_target(raw: bytes, address: int) -> int:
    need(len(raw) == 4, "BL width")
    first, second = struct.unpack("<HH", raw)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         "BL encoding at " + hex(address))
    s = (first >> 10) & 1
    j1, j2 = (second >> 13) & 1, (second >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ s), 1 ^ (j2 ^ s)
    displacement = ((s << 24) | (i1 << 23) | (i2 << 22) |
                    ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    return address + 4 + signed(displacement, 25)


def direct_bl_callers(image: bytes, target: int) -> list[int]:
    callers = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000:
            if thumb_bl_target(image[address:address + 4], address) == target:
                callers.append(address)
    return callers


def ldr16_literal_refs(image: bytes, literal_va: int) -> list[int]:
    refs = []
    for address in range(0, len(image) - 1, 2):
        instruction = u16(image, address)
        if instruction & 0xF800 != 0x4800:
            continue
        target = ((address + 4) & ~3) + (instruction & 0xFF) * 4
        if target == literal_va:
            refs.append(address)
    return refs


def occurrences(raw: bytes, word: int) -> list[int]:
    encoded = struct.pack("<I", word)
    return [offset for offset in range(len(raw) - 3)
            if raw[offset:offset + 4] == encoded]


def main() -> None:
    package = pinned(PACKAGE, "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    need(len(package) == 0x500000, "package extent")
    image = package[IMAGE1_BIAS:IMAGE1_BIAS + 0x40000]
    need(len(image) == 0x40000, "image-1 extent")

    def code(va: int, size: int) -> bytes:
        return image[va:va + size]

    def exact(va: int, encoded: str, why: str) -> None:
        expected = bytes.fromhex(encoded)
        need(code(va, len(expected)) == expected, why + " at " + hex(va))

    # Corrected coordinate: selected image 1 uses FILE = VA + 0x40200.
    need(package[0x40200 + 0xB7EC:0x40200 + 0xB8A8] == code(0xB7EC, 0xBC),
         "corrected VA/FILE mapping")
    slices = {
        (0x1E68, 0x2040): "c3afd8863cf7f6d098fe7459ef91da9fd8827662041e77cd29497dccb2aae57a",
        (0xB7EC, 0xB8A8): "78bbf2da87adaa7cc1c9c30cbed5381d079810c8d9e3809a1c0e6744cd6d8c07",
        (0xBBBC, 0xBD2E): "9161e90f083f9e3f230c6e8d6f2b2f2503c7cbcd6c2ca1525e025f116a30dd71",
        (0xBD58, 0xC02C): "5d9924044096fbef1f5c14db5c289d60d465750ad5ea5be6ce479375542ffcb6",
        (0xC5D0, 0xC842): "51c6c80996f433f94b2774ae6b86ba61f1e95a306433b98aad6681256deb5827",
        (0xCA84, 0xCAFC): "35f9ace204a351b9446e82f0fbab8cb6a6eb688f103a882ec2bf0d8f8e353795",
    }
    for (start, end), expected in slices.items():
        need(sha256(code(start, end - start)) == expected, "slice " + hex(start))

    # The selected-package references to the six-halfword s[] base are finite.
    need(occurrences(image, 0x2000BA40) == [0x204C, 0xB890, 0xC88C, 0xCB00],
         "0x2000ba40 literal census")
    need(ldr16_literal_refs(image, 0x204C) == [0x1F64, 0x1F72], "predicate s refs")
    need(ldr16_literal_refs(image, 0xB890) == [0xB7FE], "selector reset s ref")
    need(ldr16_literal_refs(image, 0xC88C) == [0xC70A, 0xC716, 0xC760],
         "formatter s refs")
    need(ldr16_literal_refs(image, 0xCB00) == [0xCA90], "broad reset s ref")

    # The selector zeros all six s[i] before selecting/calling the unpacker.
    exact(0xB7F8, "002005e00021244a22f81010411cc8b20628f7db", "selector six-halfword reset loop")
    need(u32(image, 0xB890) == 0x2000BA40, "selector reset literal")
    need(direct_bl_callers(image, 0xB7EC) == [0xB6FA], "selector ordinary caller")
    need(direct_bl_callers(image, 0xBD58) == [0xB84C, 0xB874, 0xB88A],
         "unpacker source paths")

    # Correct the earlier pointer-overlap reading. b884 resolves to literal
    # b894 (0x20000494), whereas b890 (0x2000ba40) is used only by b7fe.
    need(u32(image, 0xB894) == 0x20000494 and u32(image, 0xB898) == 0x20000498,
         "dynamic source pointer slots")
    need(occurrences(image, 0x20000494) == [0xB894, 0x1C064],
         "0x20000494 raw occurrence census")
    need(occurrences(image, 0x20000498) == [0xB7AC, 0xB898, 0xC5AC, 0x1C1A4],
         "0x20000498 raw occurrence census")
    need(ldr16_literal_refs(image, 0xB894) == [0xB812, 0xB884], "0x20000494 refs")
    need(ldr16_literal_refs(image, 0xB898) == [0xB81C, 0xB832, 0xB844, 0xB852, 0xB86C, 0xB87E],
         "0x20000498 refs")
    exact(0xB87A, "33462a4606480168083103480068083000f065fa", "fallback A/B pointer call")
    need(thumb_bl_target(code(0xB88A, 4), 0xB88A) == 0xBD58, "fallback unpacker call")

    # bbbc computes uint16 abs(A-B); its four calls to c5d0 carry category
    # 4, 6, 1, 1. c5d0 then increments s[category-1] by one, not by diff.
    exact(0xBC20, "b84509daa7eb080086b2", "A greater-than-B absolute difference")
    exact(0xBC38, "a8eb070086b2", "B greater-or-equal absolute difference")
    need(direct_bl_callers(image, 0xC5D0) == [0xBC74, 0xBCA8, 0xBCDE, 0xBD1E],
         "formatter callers")
    need(u32(image, 0xBD50) == 0x200004AA and u32(image, 0xBD54) == 0x200004AC,
         "mode flag literals")
    exact(0xC708, "601e604931f81000401c81b2601e5d4a22f81010", "s indexed increment")

    # A record-ID bound-exceeded path bypasses the ID update/publication but
    # still reaches the s increment: c604 BHI c6de; c6de B c708.
    exact(0xC5F6, "601e944951f820009449098888426bd8", "record-ID bound and short path")
    exact(0xC6DE, "13e0", "record-ID bypass to s increment")

    # After incrementing the separate u32 record ID, mode 1 publishes its low
    # half at R+0x2490; modes 4 and 6 share R+0x2492.  These are record-ID
    # latches, not s[] and not the d0e4 accumulator latch.
    exact(0xC6AA, "601e674951f82000401c611e654a42f82100", "record-ID increment")
    exact(0xC6BC, "012c04d0042c0dd0062c1dd113e0", "record-ID mode selection")
    exact(0xC6CA, "601e5f4931f8200081b242f29040415314e0", "mode-1 R+0x2490 store")
    exact(0xC6E0, "601e5a4931f8200081b242f29240415309e0", "mode-4 R+0x2492 store")
    exact(0xC6F2, "601e554931f8200081b242f29240415300e0", "mode-6 R+0x2492 store")

    # Separate record IDs use six u32 values at ba28; they end immediately
    # before s[] and are not the score input themselves.
    need(u32(image, 0xC84C) == 0x2000BA28, "record-ID base")
    need(ldr16_literal_refs(image, 0xC84C) ==
         [0xC5F8, 0xC62C, 0xC646, 0xC65C, 0xC66C, 0xC67C, 0xC68C,
          0xC69C, 0xC6AC, 0xC6B6, 0xC6CC, 0xC6E2, 0xC6F4, 0xC744,
          0xC75A, 0xC76C, 0xC77E], "record-ID refs")

    # Broader initializer ca84 also clears record IDs, s, accumulators, q and
    # history. The ordinary selector reset above is independently sufficient
    # to establish per-selector s=0 before bd58.
    exact(0xCA84, "00201ae000211c4a42f820101b4a22f810101b4a42f820101a4a22f81010",
          "broad six-slot reset prefix")
    need(u32(image, 0xCAFC) == 0x2000BA28 and u32(image, 0xCB00) == 0x2000BA40 and
         u32(image, 0xCB04) == 0x2000D0E4 and u32(image, 0xCB08) == 0x2000D0FC,
         "broad reset bases")
    need(direct_bl_callers(image, 0xCA84) == [0xB964, 0xCB50], "broad reset callers")

    # Predicate shifts the per-mode s count into H, conditionally increments q,
    # and accumulates delayed H.h0 into the u32 A slot. No diff/amplitude value
    # is loaded in this body.
    need(u32(image, 0x2044) == 0x2000D0FC and u32(image, 0x2048) == 0x2000D108 and
         u32(image, 0x204C) == 0x2000BA40 and u32(image, 0x206C) == 0x2000D0E4,
         "predicate state literals")
    exact(0x1F5E, "c0008180601e394931f8101002ebc000c180601e364931f8101042f2a040405b814217dd",
          "history append s and s-threshold compare")
    exact(0x1FB4, "234a32f81100fff744ff", "q membership input")
    exact(0x1FC0, "601e2a4951f820101f4a32f830000144601e264a42f82010",
          "A plus delayed history count")
    need(direct_bl_callers(image, 0x1E68) == [0xBFBC, 0xBFD0, 0xBFDC],
         "predicate callers")
    exact(0xBFAE, "20480088012805d1324651460420f5f754ff0ee01f480088012805d1324651460620f5f74aff04e0324651460120f5f744ff",
          "mode-4/mode-6/mode-1 predicate calls")

    # bd58 advances four logical lane indices per six packed bytes. These are
    # representation indices; this chain contains no physical-coordinate map.
    exact(0xBE3E, "00eb0b07ddf8200f00eb0b08d8f80000c0f30b0001a921f81400",
          "packed group pointers and first 12-bit lane")
    exact(0xBF98, "241d0bf106001ffa80fb", "four-lane/six-byte loop advance")

    context = pinned(CONTEXT, "0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439")
    rt = pinned(RT, "91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9")
    need(len(context) == 64 and len(rt) == 256, "retained read extents")
    need((u16(context, 6), u16(context, 8)) == (54, 44), "retained r7 latches")
    need([u16(rt, x) for x in (0x30, 0x32, 0x40, 0xC0, 0xC4)] == [200, 0, 0, 200, 40],
         "retained candidate thresholds")
    need((u16(rt, 0x90), u16(rt, 0x92)) == (41, 54), "retained record-ID latches")

    result = {
        "schema": "rtp-score-input-provenance-v1",
        "package_sha256": sha256(package),
        "image1_file_bias": "0x40200",
        "s_cpu_range": "0x2000ba40..0x2000ba4b",
        "s_reset": "six uint16 zeroes before each selector/unpacker call",
        "s_update": "uint16 s[category-1] += 1 per accepted formatter path",
        "s_is_diff_or_amplitude": False,
        "aggregate": "per-category delayed qualifying-count accumulator",
        "fallback_a_pointer_slot": "0x20000494",
        "fallback_b_pointer_slot": "0x20000498",
        "pointer_overlaps_s": False,
        "logical_lane_index_is_physical_coordinate": False,
        "retained_r7_latches": {"mode6": 54, "other": 44},
        "retained_record_id_latches": {"mode1": 41, "mode4_or_mode6_shared": 54},
        "record_id_54_equals_r7_54_is_dataflow_proved": False,
        "record_ids_are_one_to_one_with_s": False,
        "record_id_bound_bypass_still_increments_s": True,
        "cpu_2001_bus_4701_alias_proved": False,
        "offline_only": True,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
