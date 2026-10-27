#!/usr/bin/env python3
"""Verify the bounded selected-image math feeding NPC_AP+16/+18/+1a.

This is deliberately an offline byte/model checker.  It opens only retained
local evidence and contains no transport, device, network, or write path.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
AF = OVERNIGHT / "npc-ap-divisor-provenance-20261027af/divisor-provenance.md"
AI = OVERNIGHT / "npc-ap-floating-inputs-20261027ai/floating-inputs.md"
AK_RAW = OVERNIGHT / "npc-ap-divisor-snapshot-20261027ak/capture-once/npc-ap-offset-14-through-1b.bin"

PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
AF_SHA256 = "a1adb0c07a03a65f7801a1fd2893cad5ddf4ee2d4e3ff60481d26b3b4fc274b9"
AI_SHA256 = "e9fa855b3e672a9115d63bcfab704cf056473aaa4bc4f0d51d123020b66c02ed"
AK_RAW_SHA256 = "703e6dd703874a61cf296a379be701c53e5db31d7b51e5e1c868504fb380a86d"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    need(sha256(raw) == expected, f"SHA-256 mismatch: {path}")
    return raw


def u16(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def f32_at(raw: bytes, offset: int) -> float:
    return struct.unpack_from("<f", raw, offset)[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", f32(value)))[0]


def bl_target(image: bytes, address: int) -> int:
    first, second = struct.unpack_from("<HH", image, address)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"BL encoding at {address:#x}")
    sign = (first >> 10) & 1
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    i1 = 1 ^ (j1 ^ sign)
    i2 = 1 ^ (j2 ^ sign)
    value = ((sign << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def direct_callers(image: bytes, target: int) -> list[int]:
    callers: list[int] = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000:
            if bl_target(image, address) == target:
                callers.append(address)
    return callers


def quantize_writer_input(value: float) -> int:
    """Finite nonnegative in-range model of VCVT then the halfword store."""
    value = f32(value)
    need(0.0 <= value <= 1.0, "model input outside finite [0,1]")
    product = f32(value * f32(1024.0))
    return int(product) & 0xFFFF


def row_prefactor(value: float, c0: int, count: int, row: int) -> float:
    """Binary32 model of the dispatcher row prefactor for nonzero divisor."""
    need(0 < count <= 12 and 0 <= row < count, "row/count domain")
    need(0 <= c0 <= 0xFFFF, "c0 domain")
    denominator = (c0 + count - 1 - row) & 0xFFFF
    need(denominator != 0, "zero row denominator")
    return f32(f32(f32(value) * f32(float(c0))) /
               f32(float(denominator)))


def verify_image(image: bytes, package: bytes) -> dict[str, object]:
    need(len(image) == 0x40000, "nominal selected image-0 extent")

    bodies = {
        "dispatcher_180e4": (0x180E4, 0x18408,
            "9f31abe91ea5bb0d0c3da95817152ccc15cf1364b7d9fd8616feb3afd235db14"),
        "interpolator_1a530": (0x1A530, 0x1A6C6,
            "67ef1d4a4418980222e40645147c4ed7eb732eb29365b011333d771d32242eca"),
        "array_writer_1a748": (0x1A748, 0x1AA04,
            "c6389c2f4d136215608d5242b09a17b4a8b75214f25e82eb5fc087d1862261b6"),
        "direct_writer_1aa20": (0x1AA20, 0x1AB7C,
            "9d34ab9fb84cf51a05f6bbd9a34396f716ab43d213c706d7f3f22d1cd94cdfe6"),
        "nonlinear_1ae9c": (0x1AE9C, 0x1AF52,
            "8761bfa3a6e42095a66d789dfa95d0541708ae85203136409b96d65f6f0223b4"),
        "lookup_27b78": (0x27B78, 0x27C68,
            "981639b2c841b1da1a573fc300b6dbc07e16153b2dd9cb2e411474cbf02d09b6"),
    }
    for label, (start, end, digest) in bodies.items():
        need(sha256(image[start:end]) == digest, "body " + label)

    subpaths = {
        "array_preprocess": (0x18130, 0x182A2,
            "5663d34720f76ec9a1e55a06fe163112c9976acd5dfb7c32cb16a1487d2050c3"),
        "direct_preprocess": (0x182A4, 0x18370,
            "f6ce44bdafd9f4df6f214e1cf15dfc4b3543d6fcaa648a039a7e6b6334532a2c"),
        "unity_fallbacks": (0x18370, 0x18400,
            "617803911cd3fd7d2c8830d57e12cf2798057c87f0dae9be5391fae02e600f91"),
        "interpolator_modes": (0x1A546, 0x1A688,
            "3dd3226adfb42659e4b17ab9ede88908c02995fe8f95e090de839fe1622776fd"),
        "interpolator_override": (0x1A688, 0x1A6BC,
            "d4d9d7be62b22902d96b4e28613df9c503b2e15ba84e10a5465337ea5aa5f40b"),
        "lookup_mask_and_forces": (0x27BA4, 0x27C60,
            "59f3d07489d30c439cc9a3baeb5f4704083019ddb96186fa564bdf8a65acfee2"),
        "fixed_exponent_calls": (0x1AEAC, 0x1AF42,
            "5d87a3074882dcb3192645f49c6527d32f8a6a871e20b80b81e3646502dfadd6"),
        "final_row_stores": (0x1A886, 0x1A8E6,
            "dca3aac11aa536fe23b753576db0517adbd41f0cfe3609bf2af41e98a6fd106f"),
    }
    for label, (start, end, digest) in subpaths.items():
        need(sha256(image[start:end]) == digest, "subpath " + label)

    expected_callers = {
        0x180E4: [0x136D0],
        0x1A530: [0x181B6, 0x181D8, 0x181FA, 0x182B6, 0x182D0, 0x182EA],
        0x1AE9C: [0x18282, 0x1834A, 0x19150],
        0x1A748: [0x1829E, 0x183CA],
        0x1AA20: [0x1836A, 0x183F8],
        0x27B78: [0x1A5F0],
        0x38C8C: [0x18100],
    }
    for target, callers in expected_callers.items():
        need(direct_callers(image, target) == callers,
             f"direct callers of {target:#x}")
    need(bl_target(image, 0x1A5F0) == 0x27B78,
         "interpolator lookup-helper call")
    need([bl_target(image, address) for address in
          (0x1AEB8, 0x1AECC, 0x1AEE0)] == [0x2DBD0] * 3,
         "three fixed-second-argument calls")

    # The two state-table literal roots are adjacent but distinct.  Each
    # processed branch loads its reference values and stores the pre-factor
    # interpolator result back to the same fixed RAM table.
    need(u32(image, 0x18408) == 0x20007C8C, "array state table root")
    need(u32(image, 0x1840C) == 0x20007C80, "direct state table root")
    need(image[0x181A8:0x1823A].hex().count("01eb8000") >= 6,
         "array table indexed load/store sequence")
    need(image[0x182AC:0x1830C].hex().count("90ed") >= 3 and
         image[0x182F6:0x1830C].hex().count("80ed") == 3,
         "direct table load/store sequence")

    # 0x38c8c returns the float at the fixed CPU literal 0x20000714.
    need(image[0x38C8C:0x38C98].hex() == "014890ed000a704714070020",
         "common multiplier getter")

    literals = {
        0x1A6C8: 1023.0,
        0x1A6CC: 511.0,
        0x1A6D0: 1.0 / 32768.0,
        0x1A6D4: 65535.0,
        0x1AF58: 65535.0,
        0x1AA0C: 1024.0,
        0x1AB7C: 1024.0,
        0x27C68: 1024.0,
    }
    for address, expected in literals.items():
        need(f32_bits(f32_at(image, address)) == f32_bits(expected),
             f"float literal {address:#x}")
    need(u32(image, 0x1AF54) == 0x3EE8BA2E and
         f32_at(image, 0x1AF54) == 0.45454543828964233,
         "fixed nonlinear exponent literal")

    # Key control and masking encodings.  These bind: +2/+be/+c0/+8e,
    # mode +24/+4de, rates +26/+28, selector +51e, final override +3e and
    # +7e/+7c, difference low16 and >1024 reset, and +214 cache selector.
    need(image[0x180F6:0x1812E].hex() ==
         "07468846f6f74fff054620f0c4fdf0ee408a688801287ed1b5f8be0001287bd1"
         "b5f8c060b5f88e000c2802dd4ff00c0901e0b5f88e900024",
         "dispatcher control loads")
    need(image[0x1A546:0x1A552].hex() == "a08c012877d1b4f8de04d0bb",
         "interpolator top mode gates")
    need(image[0x1A55C:0x1A5C8].hex().startswith("208d00ee100ab8ee400a") and
         image[0x1A592:0x1A5C8].hex().startswith("e08c00ee100ab8ee400a"),
         "interpolator +28/+26 rates")
    need(image[0x1A5E2:0x1A5F4].hex() ==
         "b4f81e653046f0ee680ab0ee480a0df0c2fa",
         "lookup selector and call")
    need(image[0x1A688:0x1A6BC].hex().startswith("e88f012816d1") and
         "b4f87e00" in image[0x1A688:0x1A6BC].hex() and
         "b4f87c00" in image[0x1A688:0x1A6BC].hex(),
         "final object/NPC override")
    need(image[0x27BAE:0x27BF0].hex().count("bceec00a") == 2 and
         image[0x27BE6:0x27BF0].hex() == "b6f5806f00dd00264db9",
         "difference conversion low16 and >1024 reset")
    need(image[0x1AEE8:0x1AEFC].hex() ==
         "b4f814020c2801db0b2501e0b4f81452ae4222d1",
         "nonlinear cache row selector")

    # Both writers use 1024 scaling and an unsigned conversion.  The array
    # writer's final stores are STRH, so they too retain the low 16 bits even
    # though no separate UXTH precedes those three final stores.
    final_row_hex = image[0x1A890:0x1A8E6].hex()
    need(final_row_hex.count("bceec00a") == 3 and
         all(store in final_row_hex for store in ("e882", "2883", "6883")),
         "array final conversions and halfword stores")
    need(image[0x1AA96:0x1AAF6].hex().count("bceec00a") == 3 and
         image[0x1AA96:0x1AAF6].hex().count("80b2") == 3,
         "direct conversions and explicit low16")

    # Static NPC_AP initializer values are retained only as non-live context.
    package_payload = package[0x172600:0x172B3E]
    need(sha256(package_payload) ==
         "3e9f4747fa26eeca6818944a6dae2fbba54f6ccc79d1ed6a4dc05434b5ad21b7",
         "stored NPC_AP payload")
    stored_controls = {offset: u16(package_payload, offset) for offset in
                       (0x02, 0x16, 0x18, 0x1A, 0x24, 0x26, 0x28,
                        0x7C, 0x7E, 0x8E, 0xBE, 0xC0, 0x214,
                        0x4DE, 0x51E)}
    need(stored_controls == {
        0x02: 1, 0x16: 1024, 0x18: 1024, 0x1A: 1024,
        0x24: 1, 0x26: 512, 0x28: 1023, 0x7C: 8199,
        0x7E: 1, 0x8E: 1, 0xBE: 1, 0xC0: 2250,
        0x214: 0, 0x4DE: 1, 0x51E: 0,
    }, "stored controls (not runtime state)")

    return {
        "body_hashes": {key: digest for key, (_, _, digest) in bodies.items()},
        "state_tables": {"array": "0x20007c8c", "direct": "0x20007c80"},
        "common_multiplier_float_address": "0x20000714",
        "stored_controls_are_runtime_evidence": False,
    }


def verify_math_boundaries() -> dict[str, object]:
    lo = f32(118.0 / 1024.0)
    hi = f32(119.0 / 1024.0)
    hi_previous = struct.unpack("<f", struct.pack("<I", f32_bits(hi) - 1))[0]
    need(quantize_writer_input(lo) == 118, "118 interval lower endpoint")
    need(quantize_writer_input(hi_previous) == 118,
         "118 interval upper predecessor")
    need(quantize_writer_input(hi) == 119, "119 interval lower endpoint")

    # Algebra cancels c0 on the final row, but the two binary32 roundings do
    # not guarantee bit identity.  Keep a fixed counterexample as a regression.
    x = struct.unpack("<f", struct.pack("<I", 0x3D6A936E))[0]
    q = row_prefactor(x, 2250, 7, 6)
    need(f32_bits(x) == 0x3D6A936E and f32_bits(q) == 0x3D6A936D,
         "final-row cancellation is not bit-exact")

    # Earlier denominators are u16.  This exact case wraps to zero and is
    # intentionally rejected by the finite helper rather than guessed.
    wrapped = (0xFFFF + 2 - 1 - 0) & 0xFFFF
    need(wrapped == 0, "u16 denominator wrap fixture")
    try:
        row_prefactor(0.25, 0xFFFF, 2, 0)
    except ValueError as exc:
        need(str(exc) == "zero row denominator", "wrap rejection reason")
    else:
        raise ValueError("wrapped zero denominator was accepted")

    return {
        "finite_writer_118_interval": [lo, hi],
        "interval_upper_exclusive": True,
        "final_row_algebraic_c0_cancellation_bit_exact": False,
        "count_zero_safe_model": False,
        "exceptional_vfp_modeled": False,
    }


def main() -> None:
    package = load(PACKAGE, PACKAGE_SHA256)
    load(AF, AF_SHA256)
    load(AI, AI_SHA256)
    ak = load(AK_RAW, AK_RAW_SHA256)
    need(struct.unpack("<4H", ak) == (100, 118, 118, 118),
         "retained AK context/divisor tuple")
    image = package[0x200:0x40200]
    static = verify_image(image, package)
    math = verify_math_boundaries()

    # Mutation checks use explicit exceptions and remain active under -O.
    for address in (0x18130, 0x1A546, 0x1AEAC, 0x1A890):
        mutated = bytearray(image)
        mutated[address] ^= 1
        matching = [label for label, (start, end, digest) in {
            "array_preprocess": (0x18130, 0x182A2,
                "5663d34720f76ec9a1e55a06fe163112c9976acd5dfb7c32cb16a1487d2050c3"),
            "interpolator_modes": (0x1A546, 0x1A688,
                "3dd3226adfb42659e4b17ab9ede88908c02995fe8f95e090de839fe1622776fd"),
            "fixed_exponent_calls": (0x1AEAC, 0x1AF42,
                "5d87a3074882dcb3192645f49c6527d32f8a6a871e20b80b81e3646502dfadd6"),
            "final_row_stores": (0x1A886, 0x1A8E6,
                "dca3aac11aa536fe23b753576db0517adbd41f0cfe3609bf2af41e98a6fd106f"),
        }.items() if start <= address < end and
            sha256(mutated[start:end]) == digest]
        need(not matching, f"mutation escaped slice hash at {address:#x}")

    output = {
        "schema": "npc-ap-writer-math-v1",
        "target_operations": 0,
        "selected_package_sha256": PACKAGE_SHA256,
        "retained_divisors": [118, 118, 118],
        "static": static,
        "math": math,
        "actual_producing_branch_identified": False,
        "current_runtime_controls_known": False,
        "field_units_or_physical_meaning_identified": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
