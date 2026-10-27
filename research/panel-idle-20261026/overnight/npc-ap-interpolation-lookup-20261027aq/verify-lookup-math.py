#!/usr/bin/env python3
"""Offline verifier for the selected 0x19830 integer lookup math."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
AF = OVERNIGHT / "npc-ap-divisor-provenance-20261027af/divisor-provenance.md"
AM = OVERNIGHT / "npc-ap-writer-math-20261027am/writer-math.md"
AM_REVIEW = OVERNIGHT / "npc-ap-writer-math-20261027am/review-closure.md"

PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
AF_SHA256 = "a1adb0c07a03a65f7801a1fd2893cad5ddf4ee2d4e3ff60481d26b3b4fc274b9"
AM_SHA256 = "6fde3f57183820a60646b48ce59da70c1e3ef7f73dc371f4f5d5231a082d5baa"
AM_REVIEW_SHA256 = "3dd7cfc1a4907bac0311544b06225ca6511bcadb673cc6f3a367cd7788ab970a"


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


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


def sdiv_trunc_zero(numerator: int, denominator: int) -> int:
    need(denominator != 0, "signed division by zero")
    magnitude = abs(numerator) // abs(denominator)
    return -magnitude if (numerator < 0) != (denominator < 0) else magnitude


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
    result: list[int] = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000:
            if bl_target(image, address) == target:
                result.append(address)
    return result


def lookup_trace(x: int, xs: list[int], ys: list[int], count: int) -> dict[str, int | str]:
    """Bit-accurate selected routine model through its 32-bit return."""
    need(0 <= x <= 0xFFFF, "x u16 domain")
    need(count > 0, "count zero is an unchecked target memory access")
    need(count <= len(xs) and count <= len(ys), "table extent")
    need(all(0 <= value <= 0xFFFF for value in xs[:count] + ys[:count]),
         "table u16 domain")

    if xs[0] <= x:
        return {"branch": "first", "value32": ys[0], "value16": ys[0]}
    if xs[count - 1] >= x:
        return {"branch": "last", "value32": ys[count - 1],
                "value16": ys[count - 1]}

    for index in range(1, count):
        if xs[index] >= x:
            continue
        # Every skipped predecessor satisfies xs[index-1] >= x, while this
        # row satisfies x > xs[index]. The selected denominator is therefore
        # positive even if the overall table is duplicated or unsorted.
        delta_x = x - xs[index]
        delta_y = ys[index - 1] - ys[index]
        denominator = xs[index - 1] - xs[index]
        need(delta_x > 0 and denominator > 0,
             "crossing pair must have positive width")
        mathematical_product = delta_x * delta_y
        wrapped_product = s32(mathematical_product)
        quotient = sdiv_trunc_zero(wrapped_product, denominator)
        value32 = u32(ys[index] + quotient)
        return {
            "branch": "interior",
            "index": index,
            "delta_x": delta_x,
            "delta_y": delta_y,
            "denominator": denominator,
            "mathematical_product": mathematical_product,
            "wrapped_product": wrapped_product,
            "quotient": quotient,
            "value32": value32,
            "value16": value32 & 0xFFFF,
        }
    raise ValueError("no crossing despite strict endpoint inequalities")


def selected_maps(xs: list[int], tables: list[list[int]]) -> tuple[list[dict[str, object]], int]:
    expected_hashes = [
        "4cdf124c57ff845ea7fdc807246ee7c2cd337a38f50171761d2bf3b4e08ed485",
        "8661ec76ca105acf1a20f51a2b02a372eee315d263338eacbad8e69cd7e6ec7c",
        "53d1d9d128ea89d00848b78f0dee7ca1cde1c3db3e818b2cdf5d173bfea2f2db",
        "5799cd775096ae3127486999a80e4ddd657736cb2d76f5623848372eb40859e2",
    ]
    summaries: list[dict[str, object]] = []
    maximum_product = 0
    for selector, (ys, expected_hash) in enumerate(zip(tables, expected_hashes)):
        outputs: list[int] = []
        for x in range(1025):
            trace = lookup_trace(x, xs, ys, 5)
            outputs.append(int(trace["value16"]))
            if trace["branch"] == "interior":
                maximum_product = max(maximum_product,
                                      abs(int(trace["mathematical_product"])))
                need(trace["mathematical_product"] == trace["wrapped_product"],
                     "selected stored table signed-product overflow")
                lo = min(ys[int(trace["index"]) - 1], ys[int(trace["index"])])
                hi = max(ys[int(trace["index"]) - 1], ys[int(trace["index"])])
                need(lo <= int(trace["value32"]) <= hi,
                     "selected local non-overshoot")
        packed = struct.pack("<1025H", *outputs)
        need(sha256(packed) == expected_hash, f"selector {selector} output map")
        summaries.append({
            "selector": selector,
            "minimum": min(outputs),
            "maximum": max(outputs),
            "unique_outputs": len(set(outputs)),
            "map_sha256": expected_hash,
        })
    need(maximum_product == 65408, "selected maximum interpolation product")
    return summaries, maximum_product


def verify(package: bytes) -> dict[str, object]:
    image = package[0x200:0x40200]
    need(len(image) == 0x40000, "nominal image-0 extent")
    need(sha256(image[0x19830:0x19898]) ==
         "2b9338f990c409e8848d43d1fd64c05b5eb9640ed12d762764c8f82c821572e3",
         "complete 0x19830 body")
    need(sha256(image[0x19830:0x19840]) ==
         "03278a209e6112b604485ff0303aef5cc56d98ecd84b2bd0b69fc8e081d22c86",
         "first endpoint path")
    need(sha256(image[0x19840:0x19852]) ==
         "8fc6fce77a62b951c30f0421eb1af69bec53d41c6eb2f24a14fe138a1b86808c",
         "last endpoint path")
    need(sha256(image[0x19852:0x19894]) ==
         "30f37fb6f22f4e06da0418820faa526064b146783fdb1ac9c654ef9c3dcc8956",
         "interior search/math path")
    need(direct_callers(image, 0x19830) == [0x27BFC, 0x27C1A],
         "0x19830 direct callers")

    # Both calls use count=5; selector zero supplies +4ea and selectors 1..3
    # supply +520 + 10*(selector-1), all with the shared +4e0 coordinate table.
    need(image[0x27BF0:0x27C20].hex() ==
         "052304f2ea4204f59c613046f1f718fe87b20de0681e00eb800104f5a460"
         "00eb4102052304f59c613046f1f709fe87b2",
         "selector table pointers and count-five calls")

    payload = package[0x172600:0x172B3E]
    need(len(payload) == 0x53E and sha256(payload) ==
         "3e9f4747fa26eeca6818944a6dae2fbba54f6ccc79d1ed6a4dc05434b5ad21b7",
         "stored NPC_AP payload")
    offsets = [0x4E0, 0x4EA, 0x520, 0x52A, 0x534]
    expected_slices = [
        ("a80ca04ad60baee8e8dd81a6a0caa6e0f9c5ac642b81badc24b5b78c8b5f9bfa",
         [1024, 256, 128, 64, 32]),
        ("21b7a7d200ec34f197c221a9c4ef1f68c4ed107eb3be1dd5cb8f759bab9b3c2f",
         [1023, 1023, 512, 256, 64]),
        ("248669ddb7ba6a6bb56ed04f414017c7d8106a7d5106d3c0f2555a1af30dd60c",
         [32, 32, 32, 32, 32]),
        ("c290dbd422ebcfcf63fcdcd878af90e20d10e1c3198a90a7513860cbdd91714f",
         [16, 16, 16, 16, 16]),
        ("ec50204def149b71e6481b2cb725db8f571d93f163dcfffe6b9c2466091f3223",
         [64, 64, 64, 64, 64]),
    ]
    decoded: list[list[int]] = []
    for offset, (digest, values) in zip(offsets, expected_slices):
        raw = payload[offset:offset + 10]
        need(sha256(raw) == digest, f"stored table slice {offset:#x}")
        actual = list(struct.unpack("<5H", raw))
        need(actual == values, f"stored table values {offset:#x}")
        decoded.append(actual)
    xs, tables = decoded[0], decoded[1:]
    need(all(xs[index - 1] > xs[index] for index in range(1, 5)),
         "stored X table strictly descending")
    need(tables[0][0] == tables[0][1] and
         all(tables[0][index - 1] >= tables[0][index] for index in range(1, 5)),
         "selector-zero duplicate/nonincreasing outputs")
    need(all(len(set(values)) == 1 for values in tables[1:]),
         "selectors one through three constant outputs")

    maps, maximum_product = selected_maps(xs, tables)

    # Exact selected endpoint/tie fixtures.
    y0 = tables[0]
    fixtures = {
        0: 64, 32: 64, 33: 70, 64: 256, 65: 260,
        128: 512, 129: 515, 256: 1023, 257: 1023, 1024: 1023,
    }
    for x, expected in fixtures.items():
        need(lookup_trace(x, xs, y0, 5)["value16"] == expected,
             f"selector-zero fixture x={x}")

    # Duplicate X values never create a zero-width division. An interior tie
    # skips all equal rows and resolves to the last duplicate's Y at the next
    # strictly lower crossing. Endpoint precedence remains first/last.
    duplicate_x = [100, 50, 50, 0]
    duplicate_y = [1000, 800, 700, 0]
    tie = lookup_trace(50, duplicate_x, duplicate_y, 4)
    need(tie["branch"] == "interior" and tie["index"] == 3 and
         tie["denominator"] == 50 and tie["value16"] == 700,
         "interior duplicate tie order")
    need(lookup_trace(100, duplicate_x, duplicate_y, 4)["value16"] == 1000,
         "first endpoint precedence")
    need(lookup_trace(0, duplicate_x, duplicate_y, 4)["value16"] == 0,
         "last endpoint precedence")

    # A wide u16 table can overflow the signed 32-bit MUL. The raw returned
    # word then no longer follows the ordinary convex expression; the caller's
    # later low16 reduction is a separate operation. This fixed fixture is why
    # the restricted proof carries an explicit no-overflow premise.
    overflow = lookup_trace(65534, [65535, 0], [65535, 0], 2)
    need(overflow["mathematical_product"] == 4294770690 and
         overflow["wrapped_product"] == -196606 and
         overflow["value16"] == 65533,
         "signed-product overflow boundary fixture")

    try:
        lookup_trace(0, [], [], 0)
    except ValueError as exc:
        need(str(exc) == "count zero is an unchecked target memory access",
             "count-zero refusal reason")
    else:
        raise ValueError("count zero was modeled as safe")

    return {
        "body_sha256": "2b9338f990c409e8848d43d1fd64c05b5eb9640ed12d762764c8f82c821572e3",
        "count": 5,
        "coordinate_offset": "NPC_AP+0x4e0",
        "value_offsets": ["NPC_AP+0x4ea", "NPC_AP+0x520",
                          "NPC_AP+0x52a", "NPC_AP+0x534"],
        "stored_coordinates": xs,
        "stored_values": tables,
        "stored_maps": maps,
        "stored_max_abs_mathematical_product": maximum_product,
        "stored_signed_product_overflow": False,
        "stored_global_nonovershoot": True,
        "stored_tables_are_runtime_evidence": False,
        "general_unforced_k_bound_0_to_1023": False,
        "restricted_stored_table_k_bound": [16, 1023],
        "zero_width_interior_division_reachable_for_positive_count": False,
        "count_zero_guard_present": False,
    }


def main() -> None:
    package = load(PACKAGE, PACKAGE_SHA256)
    load(AF, AF_SHA256)
    load(AM, AM_SHA256)
    load(AM_REVIEW, AM_REVIEW_SHA256)
    result = verify(package)

    # Explicit mutation failures stay active under optimized Python.
    image = package[0x200:0x40200]
    for address, start, end, expected in (
        (0x19830, 0x19830, 0x19898,
         "2b9338f990c409e8848d43d1fd64c05b5eb9640ed12d762764c8f82c821572e3"),
        (0x19840, 0x19840, 0x19852,
         "8fc6fce77a62b951c30f0421eb1af69bec53d41c6eb2f24a14fe138a1b86808c"),
        (0x19852, 0x19852, 0x19894,
         "30f37fb6f22f4e06da0418820faa526064b146783fdb1ac9c654ef9c3dcc8956"),
    ):
        changed = bytearray(image[start:end])
        changed[address - start] ^= 1
        need(sha256(changed) != expected, f"mutation escaped {address:#x}")

    output = {
        "schema": "npc-ap-interpolation-lookup-v1",
        "target_operations": 0,
        "selected_package_sha256": PACKAGE_SHA256,
        "lookup": result,
        "units_or_cadence_identified": False,
        "current_runtime_tables_known": False,
        "rejected_recorder_continued": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
