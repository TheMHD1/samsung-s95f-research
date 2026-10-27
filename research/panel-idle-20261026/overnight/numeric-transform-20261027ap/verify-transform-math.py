#!/usr/bin/env python3
"""Offline verifier for the selected-image transform at image-0 VA 0x2dbd0.

This opens retained local files only.  It has no device, USB, network, MMIO,
write, or execution path into the television.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
AM_REPORT = OVERNIGHT / "npc-ap-writer-math-20261027am/writer-math.md"

PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
AM_REPORT_SHA256 = "6fde3f57183820a60646b48ce59da70c1e3ef7f73dc371f4f5d5231a082d5baa"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path, digest: str) -> bytes:
    raw = path.read_bytes()
    need(sha256(raw) == digest, f"SHA-256 mismatch: {path}")
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
    displacement = ((sign << 24) | (i1 << 23) | (i2 << 22) |
                    ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if displacement & (1 << 24):
        displacement -= 1 << 25
    return address + 4 + displacement


def direct_callers(image: bytes, target: int) -> list[int]:
    result: list[int] = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000:
            if bl_target(image, address) == target:
                result.append(address)
    return result


def pc_relative_table_roots(image: bytes) -> dict[str, int]:
    """Reproduce the four literal-offset + PC-add table addresses."""
    need(image[0x2DCFE:0x2DD0A].hex() == "be4871eec01a31ee812a7844",
         "log-table address construction")
    need(image[0x2DE1C:0x2DE2C].hex() ==
         "7b4900f00f0040ee011a21ee800a7944",
         "exp-low table address construction")
    need(image[0x2DE34:0x2DE3C].hex() == "7649794401eb8001",
         "exp-exact table address construction")
    need(image[0x2DE40:0x2DE4C].hex() == "744901ee801a794401eb8000",
         "exp-high table address construction")
    roots = {
        "log2_split": 0x2DD0C + u32(image, 0x2DFF8),
        "exp2_low": 0x2DE2E + u32(image, 0x2E00C),
        "exp2_exact": 0x2DE3A + u32(image, 0x2E010),
        "exp2_high": 0x2DE4A + u32(image, 0x2E014),
    }
    need(roots == {
        "log2_split": 0x3DB78,
        "exp2_low": 0x3DC38,
        "exp2_exact": 0x3DC78,
        "exp2_high": 0x3DBF8,
    }, "PC-relative table roots")
    return roots


def verify_image(image: bytes) -> dict[str, object]:
    need(len(image) == 0x40000, "selected image-0 extent")

    regions = {
        "complete_body_and_pools": (0x2DBD0, 0x2E228,
            "70d0dd8ce4728859af7c86a1d71fb2d5191e45c9d78b10f5c984c04d215a6937"),
        "entry_and_classification": (0x2DBD0, 0x2DC20,
            "aac0ce1c3dbacddbefd4ea1f827e089fe5550cafdb8833bd87ec7ff3070a035b"),
        "log2_reduction": (0x2DC20, 0x2DD54,
            "02d7d12129e9be98302f2ad8dd779cc0dab35fd62cd176d3a5ba1c530da509a9"),
        "log_times_y_and_reduction": (0x2DD54, 0x2DDCE,
            "63a4f12252e4848aec220693e4a815e755537cb9c6f3df6002240bcfd92cee21"),
        "exp2_reconstruction": (0x2DDCE, 0x2DF4A,
            "8ec1092f776370a73f5f66330934d893ca14dd42c975f7683fa873ec771fced5"),
        "negative_base_integer_test": (0x2DF4C, 0x2DFD0,
            "069386061879775eed2a58600d70a7a5fbe630df2ac90e0cd92610fc1cc7ee10"),
        "main_literal_pool": (0x2DFD0, 0x2E030,
            "762dfdd9f6e3111949a4ec9960387c77a19f47949126aaf30f9beb0165fac164"),
        "special_cases_and_small_log_path": (0x2E030, 0x2E206,
            "755765c8649d45ab606d5add9bce24741608365a012b660f265fd726aab50922"),
        "trailing_literal_pool": (0x2E206, 0x2E228,
            "4ba26efc42d09215c013ed1fb1205bda7e34ff82d4a7b3df9d56c178bf7ece2e"),
    }
    for label, (start, end, digest) in regions.items():
        need(sha256(image[start:end]) == digest, "region " + label)

    # The next bytes are code, not part of the trailing literal pool.  This,
    # combined with the branch/return census pinned by the regions, fixes the
    # bounded function footprint; it is not a symbol-table claim.
    need(image[0x2E228:0x2E238].hex() ==
         "491e00ebc102b0ee401b92ed000b31f0", "next-body boundary bytes")

    need(image[0x2DBD0:0x2DC20].hex() ==
         "10b52ded088b9fedfe1a10ee100a10ee901ab0ee418a0022a0f5000c4ff00073"
         "dfedf89abcf1fe4f4ff07f4403eb410c80f0a481bcf1804fc0f01882f2490144"
         "9fedf23a9fedf2aab1f5005f40f2ca82", "entry bytes")
    need(image[0x2DD70:0x2DD74].hex() == "28ee890a",
         "split-log times split-exponent multiply")

    caller = image[0x1AE9C:0x1AF52]
    need(sha256(caller) ==
         "8761bfa3a6e42095a66d789dfa95d0541708ae85203136409b96d65f6f0223b4",
         "ordinary caller body")
    need(sha256(image[0x1AEAC:0x1AF42]) ==
         "5d87a3074882dcb3192645f49c6527d32f8a6a871e20b80b81e3646502dfadd6",
         "fixed-argument call subrange")
    need([bl_target(image, x) for x in (0x1AEB8, 0x1AECC, 0x1AEE0)] ==
         [0x2DBD0, 0x2DBD0, 0x2DBD0], "ordinary three-channel calls")
    callers = direct_callers(image, 0x2DBD0)
    need(callers == [0x33AE, 0xD488, 0xDAC6, 0x17A98, 0x197D2, 0x19EA0,
                     0x1AEB8, 0x1AECC, 0x1AEE0, 0x22FE4, 0x23292],
         "bounded image-0 direct-caller census")

    exponent_bits = u32(image, 0x1AF54)
    exponent = f32_at(image, 0x1AF54)
    need(exponent_bits == 0x3EE8BA2E and exponent == 0.45454543828964233,
         "fixed exponent")
    need((exponent_bits >> 31) == 0 and
         ((exponent_bits >> 23) & 0xFF) == 125 and
         (exponent_bits & 0x7FFFFF) != 0 and 0.0 < exponent < 1.0,
         "fixed exponent is positive, normal, nonzero, and non-integer")
    need(exponent != 5.0 / 11.0, "do not replace stored exponent with 5/11")

    roots = pc_relative_table_roots(image)
    table_hashes = {
        "log2_split": sha256(image[0x3DB78:0x3DBF8]),
        "exp2_high": sha256(image[0x3DBF8:0x3DC38]),
        "exp2_low": sha256(image[0x3DC38:0x3DC78]),
        "exp2_exact": sha256(image[0x3DC78:0x3DCB8]),
    }
    need(table_hashes == {
        "log2_split": "f09c6d6c83a6f1d2bb607527e42b69bd7e3bb94416e979ad7856e3ddbae966cb",
        "exp2_high": "0b9acac1c771ff6b79f9a659dffee2771ff6431dda6ef2022280248eb65c9813",
        "exp2_low": "d40eeb9d3e47ac1b5907842859de142687de58d0a3d0e2a54c4da62f7b05c099",
        "exp2_exact": "897133476516e88d5d9dc2d47dc5e236b66cab035bbabbf8212cdeff4c54e620",
    }, "table hashes")

    log_errors = []
    exp_exact_bits = []
    exp_reconstruction_bits = []
    for index in range(16):
        log_hi = f32_at(image, 0x3DB78 + index * 8)
        log_lo = f32_at(image, 0x3DB7C + index * 8)
        log_errors.append(abs((log_hi + log_lo) -
                              16.0 * math.log2(1.0 + index / 16.0)))
        high = f32_at(image, 0x3DBF8 + index * 4)
        low = f32_at(image, 0x3DC38 + index * 4)
        exact = f32_at(image, 0x3DC78 + index * 4)
        exp_exact_bits.append(f32_bits(exact))
        exp_reconstruction_bits.append(f32_bits(f32(high + low)))
        need(f32_bits(exact) == f32_bits(2.0 ** (index / 16.0)),
             f"exp2 exact table entry {index}")
    need(max(log_errors) < 6.0e-11, "split log2 table relation")
    need(exp_reconstruction_bits == exp_exact_bits,
         "split exp2 tables reconstruct exact table in binary32")

    # Constants support the 32*log2 and exp2/32 reductions.  Pin bits rather
    # than decimal spellings where a split constant is intentionally inexact.
    pool_words = [u32(image, x) for x in range(0x2DFD0, 0x2E030, 4)]
    need(pool_words == [
        0x3F800000, 0x00000000, 0xC0801000, 0x3EAAAAAB,
        0x3F000000, 0x3D800000, 0x3E4CE27E, 0x4238B000,
        0xBBB89AD4, 0x4238AA3B, 0x0000FE6C, 0xBF000000,
        0x376359FC, 0x3A75FFC9, 0x3D317218, 0x0000FE0A,
        0x0000FE3E, 0x0000FDAE, 0x42FC0000, 0x42FE0000,
        0x4B000000, 0x43400000, 0xBF800000, 0x4D000000,
    ], "main literal words")
    need(u32(image, 0x2E208) == 0x003FFFFF and
         [u32(image, x) for x in range(0x2E20C, 0x2E228, 4)] == [
             0xFF800000, 0x7F800000, 0x80000000, 0x3E800000,
             0x41B8B000, 0xBB389AD4, 0x41B8AA3B,
         ], "special-case and 16/ln(2) trailing literals")

    # External leaf helpers reached by the special-case continuation.
    helpers = {
        "nan_propagation_add": (0x2E320, 0x2E328,
            "7f7a31996619e0a0a906288955d6996befde2a6f59dd9181b4bd33cf467ecc60"),
        "zero_div_zero_nan": (0x2E328, 0x2E338,
            "5ac0f9ceb04925a5d0f941a89b53e63573683f1f41912ac9f1d60141345f04c5"),
        "square_special_a": (0x2E338, 0x2E348,
            "9e007b2d73827ae0f9134aab736695bf1891a0c4aff67c4354d7197baaabca8d"),
        "square_special_b": (0x2E348, 0x2E358,
            "4ba3d97fae60a9d31cb026f87661b2547d86218a5a61d20e355796fa5be256b8"),
    }
    for label, (start, end, digest) in helpers.items():
        need(sha256(image[start:end]) == digest, "special helper " + label)
    need(image[0x2E320:0x2E326].hex() == "30ee200a7047",
         "NaN propagation helper is VADD.F32 then return")
    need(image[0x2E328:0x2E332].hex() == "dfed020a80eea00a7047",
         "NaN constructor is zero divided by zero then return")

    # For this fixed y, the negative finite nonzero path fails the integer-y
    # test and tail-calls the zero/zero helper.  The body also has explicit
    # endpoint/special branches for +0, 1, +infinity and NaN.  This records
    # the instruction-backed operation class, not a target-FPSCR oracle.
    need(bl_target(image, 0x2DF8E) == 0xDB4 and
         image[0x2DF9A:0x2DF9E].hex() == "00f0c5b9",
         "negative non-integer diagnostic and NaN-helper tail branch")
    need(image[0x2DFB6:0x2DFC2].hex() == "6ff01a02dfed1c1a20ee210a",
         "positive subnormal scale by 2^27 path")

    return {
        "schema": "numeric-transform-math-v1",
        "package_sha256": PACKAGE_SHA256,
        "image": 0,
        "function_va": "0x2dbd0",
        "footprint": {"start": "0x2dbd0", "end_exclusive": "0x2e228",
                      "bytes": 1624,
                      "sha256": regions["complete_body_and_pools"][2]},
        "operation": "binary32-power-x-to-y",
        "operation_identified_structurally": True,
        "exact_library_or_ulp_contract_identified": False,
        "fixed_exponent": {"bits": "0x3ee8ba2e", "value": exponent,
                           "hex": exponent.hex(), "equal_to_5_over_11": False},
        "ordinary_fixed_call_sites": [f"0x{x:x}" for x in
                                      (0x1AEB8, 0x1AECC, 0x1AEE0)],
        "all_image0_direct_callers": [f"0x{x:x}" for x in callers],
        "table_roots": {k: f"0x{v:x}" for k, v in roots.items()},
        "max_log2_split_error_against_host_reference": max(log_errors),
        "finite_positive_unit_interval_real_target": "x**0.45454543828964233",
        "mathematical_endpoint_targets": {"x=0": 0.0, "x=1": 1.0},
        "target_operations": 0,
    }


def expect_rejected(image: bytes, offset: int) -> None:
    changed = bytearray(image)
    changed[offset] ^= 1
    try:
        verify_image(bytes(changed))
    except ValueError:
        return
    raise AssertionError(f"mutation unexpectedly accepted at {offset:#x}")


def main() -> None:
    package = load(PACKAGE, PACKAGE_SHA256)
    load(AM_REPORT, AM_REPORT_SHA256)
    need(len(package) == 0x500000, "selected package size")
    image = package[0x200:0x40200]
    result = verify_image(image)
    # Meaningful fail-closed fixtures: body, caller literal, and table.
    for offset in (0x2DBD0, 0x1AF54, 0x3DC78):
        expect_rejected(image, offset)
    result["negative_mutation_fixtures"] = 3
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
