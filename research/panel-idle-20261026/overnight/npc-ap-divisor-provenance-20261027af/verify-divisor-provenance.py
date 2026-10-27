#!/usr/bin/env python3
"""Offline checks for the three NPC_AP halfwords consumed by VA 0x2f5d8."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
BACKUP = OVERNIGHT / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
W_ORDINARY = OVERNIGHT / "ap-exco-input-snapshot-20261027w/capture-once/ordinary-ap-exco-prefix.bin"

PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
BACKUP_SHA256 = "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"
W_ORDINARY_SHA256 = "0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271"


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


def cstring(package: bytes, linked_va: int) -> str:
    start = linked_va + 0x200
    end = package.index(0, start)
    return package[start:end].decode("ascii")


def bl_target(image: bytes, address: int) -> int:
    first, second = struct.unpack_from("<HH", image, address)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"BL encoding at {address:#x}")
    sign = (first >> 10) & 1
    j1, j2 = (second >> 13) & 1, (second >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ sign), 1 ^ (j2 ^ sign)
    value = ((sign << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def direct_callers(image: bytes, target: int) -> list[int]:
    result = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000:
            if bl_target(image, address) == target:
                result.append(address)
    return result


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def derived_index(numerator_a: int, numerator_b: int, divisor: int,
                  cap: int) -> int:
    need(0 <= numerator_a <= 0xFFFF and 0 <= numerator_b <= 0xFFFF,
         "u16 numerator")
    need(1 <= divisor <= 0xFFFF and 0 <= cap <= 0xFFFF, "positive divisor/cap")
    product = f32(f32(float(numerator_a)) * f32(float(numerator_b)))
    quotient = f32(product / f32(float(divisor)))
    converted = int(f32(quotient + f32(0.5)))
    need(0 <= converted <= 0xFFFFFFFF, "finite in-range unsigned conversion")
    # STRH precedes LDRH and the cap comparison, so wrapping comes first.
    return min(converted & 0xFFFF, cap)


def main() -> None:
    package = load(PACKAGE, PACKAGE_SHA256)
    backup = load(BACKUP, BACKUP_SHA256)
    w = load(W_ORDINARY, W_ORDINARY_SHA256)
    need(len(package) == len(backup) == 0x500000, "firmware extents")
    need(len(w) == 0x338, "W ordinary prefix extent")
    image = package[0x200:0x40200]

    # Positive object-level identity. Field names/units do not follow from the
    # NPC_AP row label.
    registry = package[0x3CCBC:0x3CF08]
    need(sha256(registry) ==
         "669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287",
         "ordinary registry")
    rows = [struct.unpack_from("<7I", registry, index * 28) for index in range(21)]
    need(rows[2][:3] == (0x3DE84, 0x2000D71C, 0x540), "NPC_AP registry row 2")
    need(cstring(package, 0x3DE84) == "NPC_AP", "NPC_AP row name")
    need(image[0xEF9C:0xEFA4].hex() == "004870471cd70020" and
         sha256(image[0xEF9C:0xEFA4]) ==
         "84f93c6639be7fc7a21229eead9d80b31746059a46741f4973167e2b14ff0b47",
         "NPC_AP getter")
    base_word = struct.pack("<I", 0x2000D71C)
    need([offset for offset in range(len(image) - 3)
          if image[offset:offset + 4] == base_word] == [0xEFA0, 0x3CAF8],
         "exact NPC_AP base words are getter and registry only")

    # Selected and recovered images agree on the named directory block and
    # its first associated payload. The header's relative payload field is
    # 0x0f2600; the retained container coordinate adds the 0x80000 parameter
    # region base, producing FILE 0x172600.
    directory = package[0x84E00:0x85000]
    allocation_slice = package[0x172600:0x172B40]
    payload = package[0x172600:0x172B3E]
    need(directory == backup[0x84E00:0x85000] and sha256(directory) ==
         "04a151171ff9a3774578ff4ad328f2a0016f2ab4c60c9afa7dd30501c307b414",
         "NPC_AP directory selected/backup")
    need(directory[:32] == b"NPC_AP" + bytes(26), "NPC_AP directory label")
    need(u32(directory, 0x20) == 4 and u32(directory, 0x28) == 1 and
         u32(directory, 0x2C) == 0xF2600 and 0x80000 + u32(directory, 0x2C) == 0x172600,
         "NPC_AP first payload coordinate")
    need(u32(directory, 0x24) == 0x140000 and
         u32(directory, 0x6C) == 0 and u32(directory, 0xAC) == 0x53E,
         "NPC_AP logical base, destination offset and copy length")
    need(allocation_slice == backup[0x172600:0x172B40] and sha256(allocation_slice) ==
         "37bb4edfb3d24fc8fe0887f59815cbfb10e3ecf87bfbdf40e481b0852de56518",
         "NPC_AP allocation-sized stored slice selected/backup")
    need(payload == backup[0x172600:0x172B3E] and sha256(payload) ==
         "3e9f4747fa26eeca6818944a6dae2fbba54f6ccc79d1ed6a4dc05434b5ad21b7",
         "NPC_AP metadata-declared payload selected/backup")
    stored = [u16(payload, offset) for offset in (0x16, 0x18, 0x1A)]
    need(stored == [1024, 1024, 1024], "stored divisor defaults")

    # Complete pinned bodies: consumer, two direct writers, their common
    # dispatcher, and the dispatcher's sole direct caller.
    bodies = {
        "consumer_2f5d8": (0x2F5D8, 0x2F970,
            "428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45"),
        "array_writer_1a748": (0x1A748, 0x1AA04,
            "c6389c2f4d136215608d5242b09a17b4a8b75214f25e82eb5fc087d1862261b6"),
        "direct_writer_1aa20": (0x1AA20, 0x1AB7C,
            "9d34ab9fb84cf51a05f6bbd9a34396f716ab43d213c706d7f3f22d1cd94cdfe6"),
        "dispatcher_180e4": (0x180E4, 0x18408,
            "9f31abe91ea5bb0d0c3da95817152ccc15cf1364b7d9fd8616feb3afd235db14"),
        "caller_13464": (0x13464, 0x13780,
            "b3b7d880f11c68c6eddb95628baaf9e2b19864747dceff366c9d835199df327a"),
    }
    for label, (start, end, digest) in bodies.items():
        need(sha256(image[start:end]) == digest, "body " + label)

    need(direct_callers(image, 0x1A748) == [0x1829E, 0x183CA],
         "array writer direct callers")
    need(direct_callers(image, 0x1AA20) == [0x1836A, 0x183F8],
         "direct writer direct callers")
    need(direct_callers(image, 0x180E4) == [0x136D0],
         "dispatcher sole direct caller")
    need(bl_target(image, 0x2F5EE) == 0xEF9C and
         bl_target(image, 0x1A750) == 0xEF9C and
         bl_target(image, 0x1AA2C) == 0xEF9C,
         "consumer/writers use NPC_AP getter")

    # The consumer loads precisely +16/+18/+1a into s19/s20/s21. Its second
    # pass repeats the same O+ea and O+f0 numerator for all three divisions.
    need(image[0x2F5E8:0x2F612].hex() ==
         "dff746f80446dff7d5fc0990dff73cf808900998c08a09ee900a0998008b0aee100a0998408b0aee900a",
         "consumer getter/divisor load prolog")
    need(image[0x2F6BA:0x2F71A].hex() ==
         "208800ee100af8ee400ae08800ee100ab8ee400a20ee800af8ee690a80ee208a"
         "208800ee100af8ee400ae08800ee100ab8ee400a20ee800af8ee4a0ac0ee208a"
         "208800ee100af8ee400ae08800ee100ab8ee400a20ee800af8ee6a0a80ee209a",
         "same numerator three divisor operations")
    need(image[0x2F722:0x2F75A].hex() ==
         "b6ee000a38ee000abceec00a10ee100af2346082b6ee000a38ee800abceec00a"
         "10ee100aa082b6ee000a39ee000abceec00a10ee100ae082",
         "round and candidate stores")
    need(image[0x2F75A:0x2F794].hex() ==
         "608a34f8f219884203ddb4f8f200a4f80401b4f80601b4f8f410884203ddb4f8"
         "f400a4f80601b4f80801b4f8f610884203ddb4f8f600a4f80801",
         "three cap clamps")

    # Both direct writer forms convert bounded floating inputs with 1024.0.
    # The array form uses the final row; the direct form zeros all three if
    # helper 0x2178 returns nonzero. These are exact writes to NPC_AP.
    need(u32(image, 0x1AA0C) == 0x44800000 and
         image[0x1A890:0x1A8E6].hex() ==
         "90ed000adfed5d0a20ee200abceec00a10ee100ae882781e00eb400006eb8000"
         "90ed010adfed550a20ee200abceec00a10ee100a2883781e00eb400006eb8000"
         "90ed020adfed4d0a20ee200abceec00a10ee100a6883",
         "array writer final-row stores")
    need(u32(image, 0x1AB7C) == 0x44800000 and
         image[0x1AA80:0x1AAF6].hex() ==
         "e7f77afb38b10020adf80400adf80200adf8000026e09ded020adfed380a"
         "20ee200abceec00a10ee100a80b2adf800009ded030adfed310a20ee200a"
         "bceec00a10ee100a80b2adf802009ded040adfed2b0a20ee200abceec00a"
         "10ee100a80b2adf80400bdf80000e082bdf802002083bdf804006083",
         "direct writer gated stores")

    # The array writer reads the values back and mirrors each to two distinct
    # fixed 0x5843... destinations. The values are not copied from 0x584109a4.
    need(image[0x1A966:0x1A99C].hex() ==
         "e88a2949496c284948642849496c27494864288b2549896c244988642449896c"
         "23498864688b2049c96c1f49c8641f49c96c1e49c864",
         "array writer outward mirrors")
    need([u32(image, offset) for offset in (0x1AA10, 0x1AA14)] ==
         [0x58431000, 0x58430000], "outward mirror roots")
    for start, end, digest in (
        (0x1A886, 0x1A890, "4917517ac677decbba21f2b699fa1dfde09652bb3d1fd2815dbc682de0108281"),
        (0x1A8E6, 0x1A966, "4e162dc7d969b5fdc9ac01e8323f66a21c127cf92625ec44b62728294134263d"),
        (0x1AAF6, 0x1AB3C, "1a227204940e21c7cae21b7b9fe02bda6c7555774c4ec9f4926d683daef812d7"),
        (0x1810C, 0x18132, "45df605f0021c9af2cac6d821ca2dd7cd4faf91aedc7595b17909bcf0183acea"),
    ):
        need(sha256(image[start:end]) == digest,
             "count-minus-one / conditional outward zero / count controls")

    # The one bounded caller layer chooses only these writer routines. Its
    # direct NPC reads are +2,+be,+c0,+8e; it does not read bin-result offsets
    # +56/+58/+5a. The exact source-bin base also does not appear here.
    dispatcher = image[0x180E4:0x18408]
    need(struct.pack("<I", 0x584109A4) not in dispatcher and
         struct.pack("<I", 0x584109A4) not in image[0x1A748:0x1AB7C],
         "no direct fixed-bin source word in writer layer")
    need(image[0x180F6:0x1812E].hex() ==
         "07468846f6f74fff054620f0c4fdf0ee408a688801287ed1b5f8be0001287bd1"
         "b5f8c060b5f88e000c2802dd4ff00c0901e0b5f88e900024",
         "dispatcher NPC controls")
    need(image[0x18276:0x182A2].hex().endswith("4946684602f053fa") and
         image[0x1833C:0x18370].hex().endswith("02f059fb45e0") and
         image[0x183C6:0x18400].hex().count("02f0") >= 2,
         "dispatcher writer calls")
    need(image[0x136BC:0x136D4].hex() ==
         "28463146f0ee481a9ded041added030a9ded020a04f008fd",
         "sole caller passes r5/r6 and s0..s3")

    # W did not include NPC_AP, but it did include every O field used here.
    w_fields = {offset: u16(w, offset) for offset in
                (0xE8, 0xEA, 0xEC, 0xEE, 0xF0, 0xF2, 0xF4, 0xF6,
                 0x104, 0x106, 0x108, 0x116)}
    need(w_fields == {
        0xE8: 0, 0xEA: 3, 0xEC: 3, 0xEE: 3, 0xF0: 900,
        0xF2: 6, 0xF4: 6, 0xF6: 6,
        0x104: 6, 0x106: 6, 0x108: 6, 0x116: 1,
    }, "W relevant fields")
    stored_predictions = [derived_index(w_fields[0xEA], w_fields[0xF0], value, cap)
                          for value, cap in zip(stored, (w_fields[0xF2],
                                                        w_fields[0xF4],
                                                        w_fields[0xF6]))]
    need(stored_predictions == [3, 3, 3], "stored-default W-state predictions")
    need(derived_index(3, 900, 490, 6) == 6 and
         derived_index(3, 900, 491, 6) == 5 and
         derived_index(3, 900, 1024, 6) == 3,
         "W-state divisor boundary fixtures")
    need(derived_index(65535, 65535, 1, 6) == 0,
         "STRH truncation before clamping regression")

    output = {
        "schema": "npc-ap-divisor-provenance-v1",
        "target_operations": 0,
        "npc_ap": {"cpu_base": "0x2000d71c", "extent": "0x540",
                   "fields": ["+0x16", "+0x18", "+0x1a"]},
        "stored_initializer": {"selected_equals_backup": True,
                               "metadata_payload_bytes": 0x53E,
                               "allocation_bytes": 0x540,
                               "runtime_loading_proven": False,
                               "values": stored},
        "consumer": {
            "va": "0x2f5d8",
            "same_recompute_numerator_for_all_lanes": ["O+0xea", "O+0xf0"],
            "initial_tail_fields": ["O+0xea", "O+0xec", "O+0xee"],
            "candidate_outputs": ["O+0x104", "O+0x106", "O+0x108"],
            "caps": ["O+0xf2", "O+0xf4", "O+0xf6"],
            "low16_before_cap": True,
        },
        "direct_writers": [
            {"va": "0x1a748", "source": "rows[count-1]; final row only if count>0",
             "scale": 1024.0},
            {"va": "0x1aa20", "source": "three caller float arguments",
             "scale": 1024.0, "zero_gate_helper": "0x2178"},
        ],
        "outward_values_zero_if": "NPC_AP+19a==1 && NPC_AP+19c==0; otherwise mirror",
        "writer_dispatcher": "0x180e4",
        "dispatcher_direct_caller": "0x136d0",
        "source_bin_result_directly_feeds_fields_in_traced_direct_layer": False,
        "indirect_upstream_relation_excluded": False,
        "field_names_or_units_identified": False,
        "w": {
            "captured_numerator": [3, 900],
            "captured_caps": [6, 6, 6],
            "captured_outputs": [6, 6, 6],
            "stored_default_prediction": stored_predictions,
            "npc_fields_captured": False,
            "logical_minimum_additional_measurement_bytes": 6,
        },
        "global_writer_census_complete": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
