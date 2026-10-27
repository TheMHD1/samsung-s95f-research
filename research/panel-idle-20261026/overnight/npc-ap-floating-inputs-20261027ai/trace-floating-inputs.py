#!/usr/bin/env python3
"""Verify the bounded ordinary input chain into NPC_AP divisor writers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
ROOT = OVERNIGHT.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
PRIOR_DUTY = ROOT / "tcon-research/qd-final-duty-application-callers.md"
PRIOR_F300 = ROOT / "tcon-research/qd-f300-write-payload-dispatch.md"
PRIOR_DIVISOR = OVERNIGHT / "npc-ap-divisor-provenance-20261027af/divisor-provenance.md"

PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
PRIOR_DUTY_SHA256 = "fbdb030ef7fabecc1301132c7a53682f90c904d3ba7822a595a0399865dad05f"
PRIOR_F300_SHA256 = "2fd6029d587022c839a2655108c977ed0108e2835a7069d590b2ac7ac4da7664"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path, digest: str | None = None) -> bytes:
    raw = path.read_bytes()
    if digest is not None:
        need(sha256(raw) == digest, f"SHA-256 mismatch: {path}")
    return raw


def u32(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<I", raw, offset)[0]


def u16(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def f32_at(raw: bytes, offset: int) -> float:
    return struct.unpack_from("<f", raw, offset)[0]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


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


def exact_word_offsets(image: bytes, value: int) -> list[int]:
    word = struct.pack("<I", value)
    return [offset for offset in range(len(image) - 3)
            if image[offset:offset + 4] == word]


def verify_image(image: bytes) -> dict[str, object]:
    need(len(image) == 0x40000, "nominal image-0 extent")

    bodies = {
        "outer_13464": (0x13464, 0x13780,
            "b3b7d880f11c68c6eddb95628baaf9e2b19864747dceff366c9d835199df327a"),
        "dispatcher_180e4": (0x180E4, 0x18408,
            "9f31abe91ea5bb0d0c3da95817152ccc15cf1364b7d9fd8616feb3afd235db14"),
        "clamp_18410": (0x18410, 0x184C0,
            "52445d9f6635ae2ea81449a11fbed934fcbca633428d96a42d367d2a5dc7b77b"),
        "scale_184c8": (0x184C8, 0x18666,
            "768d98f9eff1c1314959fac968306b514800d139967ae47732edfc931d903360"),
        "feedback_18674": (0x18674, 0x186BE,
            "bc275f59841e21151b08bb80dd206cb9c16817b6e045fb723de0090c39f6a822"),
        "prefactor_18834": (0x18834, 0x1889C,
            "2e4d5d1b38c4ee2100da546c71f48a132e4f212b16761b061b2784c3e2e0897b"),
        "duty_188d8": (0x188D8, 0x18952,
            "a8c1b3047cef32811210a282456ac36e67ef7fd03ae3d6763cb1cc50c1fff64a"),
        "selector_scale_1895c": (0x1895C, 0x1897E,
            "07e2920a9fcb8def72ae96a61af0935e4609706a5e94f76c3ed6a588378f0554"),
        "triple_18984": (0x18984, 0x18A44,
            "37116a011bb42cac4f822f00986eba0808b2241182da7b92adfb0e077df2ab58"),
        "side_effect_18b20": (0x18B20, 0x18B98,
            "2c52e1f3d6f3288a637e3b1d5ba89ce50c51ca2b0a646ec6cc7536f0d5381e8b"),
        "input_halfword_243ac": (0x243AC, 0x2478A,
            "d47688051880d5b80f1cc2cf4ca8713f20c8d97ea755569b9bac1b94bca9bbc8"),
        "input_word_24838": (0x24838, 0x24904,
            "e3ae6b1e4503a6437ed837b812fb84c4bdd5a4f78554e106f15651e44015dbe9"),
        "scalar_d254": (0xD254, 0xD58C,
            "8708252625f4dfd565b288573bd56064f6659a34eb1e45f5e2b21de695584111"),
        "counter_get_38b14": (0x38B14, 0x38B20,
            "07e33315f983756bb3eb2adc49e9468e6304f10291ebeba1c4ba25709e8ff3b2"),
        "counter_inc_390a4": (0x390A4, 0x390B8,
            "b128dc989c220213f40f8f17f0b0fc7580cb7125c3dd039caa7ea8937d45459c"),
        "array_writer_1a748": (0x1A748, 0x1AA04,
            "c6389c2f4d136215608d5242b09a17b4a8b75214f25e82eb5fc087d1862261b6"),
        "direct_writer_1aa20": (0x1AA20, 0x1AB7C,
            "9d34ab9fb84cf51a05f6bbd9a34396f716ab43d213c706d7f3f22d1cd94cdfe6"),
    }
    for label, (start, end, digest) in bodies.items():
        need(sha256(image[start:end]) == digest, "body " + label)

    callers = {
        0x180E4: [0x136D0],
        0x18984: [0x13624],
        0x18674: [0x1366E],
        0xD254: [0x13682],
        0x18834: [0x189C2],
        0x188D8: [0x189CE],
        0x1895C: [0x189B6],
        0x18410: [0x189DA],
        0x184C8: [0x18A10],
        0x390A4: [0x1373C],
        0x1A748: [0x1829E, 0x183CA],
        0x1AA20: [0x1836A, 0x183F8],
        0x19064: [0x18B44],
        0x243AC: [0x13612],
        0x24838: [0x13564],
    }
    for target, expected in callers.items():
        need(direct_callers(image, target) == expected,
             f"direct callers of {target:#x}")

    # Counter getter and updater use the same fixed pair. The getter is
    # invoked before the dispatcher; the increment is after it.
    need(image[0x38B14:0x38B20].hex() ==
         "014903c970470000380e0020", "fixed pair getter bytes")
    need(image[0x390A4:0x390B8].hex() ==
         "0448d0e900305a1c40f100000149c1e900207047", "pair increment bytes")
    need(exact_word_offsets(image, 0x20000E38) == [0x38B1C, 0x390B8],
         "fixed pair exact-word references")

    # The caller stores the triple returned by 0x18984, later reloads it,
    # and passes it unchanged at the 0x136d0 ABI boundary. 0x18b20 executes
    # between those points but does not replace the three stack slots.
    need(bl_target(image, 0x13624) == 0x18984 and
         bl_target(image, 0x13640) == 0x18B20 and
         bl_target(image, 0x136D0) == 0x180E4,
         "outer triple call order")
    need(bl_target(image, 0x18B44) == 0x19064,
         "intervening source/companion call")
    need(image[0x13628:0x13640].hex() ==
         "8ded020acded030a8ded041a9ded041added030a9ded020a",
         "save/reload returned triple")
    need(image[0x136BC:0x136D4].hex() ==
         "28463146f0ee481a9ded041added030a9ded020a04f008fd",
         "dispatcher ABI input setup")
    need(image[0x13606:0x13628].hex() ==
         "8089009009a9b0ee680a009810f0cbfef1f785feb0ee680abdf82400089905f0aef9",
         "0x18984 immediate input setup")
    need(u32(image, 0x24908) == 0x200006C4 and
         image[0x248E8:0x248F0].hex() == "074800683060b4f8",
         "0x18984 r1 source word")

    # The positive source edge begins at the selector-0x128 leaf. Its entry
    # gates/table are pinned as a complete slice, and table displacement
    # 0x4e2 from PC 0x2c7b4 resolves to leaf 0x2cc96. The leaf masks the
    # received scalar in r4 to ten bits and stores through the NPC_AP base r5.
    need(sha256(image[0x2C71C:0x2C7B2]) ==
         "150862c6cbfb1e403bccf967f6ab8267356552e9ecd47e46eb30ce60386aca3c",
         "F300 selector entry")
    need(u16(image, 0x2C8B8) == 0x4E2 and 0x2C7B4 + 0x4E2 == 0x2CC96,
         "selector 0x128 table target")
    need(image[0x2CC96:0x2CCA0].hex() == "c4f30900a5f8a60056e1" and
         sha256(image[0x2CC96:0x2CCA0]) ==
         "288b05c9e05c206ce67df2860890dfde42fab4049e07d7e8b4c121b3d3c12bf7",
         "selector 0x128 low-ten NPC_AP+a6 store")

    # 0x188d8 uses low10(NPC_AP+a6)/1023 and NPC_AP+2e/65535,
    # minNum with its argument, multiplication, and a 65535 conversion/cache.
    need(image[0x188F0:0x1894C].hex() ==
         "b4f8a600c0f3090000ee100ab8eec00adfed140a80ee201ab0ee419ae08d"
         "00ee100ab8ee400adfed0f0a80ee201af0ee419a00bf89fee80ab0ee408a"
         "28ee090ab0ee408a9fed080a28ee000abceec00a10ee100aa4f86800b0ee480a",
         "duty arithmetic and cache")
    constants = {
        0x184C0: 1023.0,
        0x184C4: 65535.0,
        0x18668: 65535.0,
        0x1866C: 1023.0,
        0x18670: 1024.0,
        0x186C0: 1024.0,
        0x1889C: 1023.0,
        0x188A0: 65535.0,
        0x18954: 1023.0,
        0x18958: 65535.0,
        0x18980: 1024.0,
        0xD5C0: 1024.0,
    }
    for address, expected in constants.items():
        need(f32_at(image, address) == expected, f"float literal {address:#x}")
    # In particular, the VLDR at 0x18934 resolves to 0x18958. This prevents
    # confusing its 65535.0 cache scale with the unrelated 1024.0 at 0x18980.
    need(image[0x18934:0x18938].hex() == "9fed080a" and
         f32_at(image, 0x18958) == 65535.0 and
         f32_at(image, 0x18980) == 1024.0,
         "0x188d8 cache scale is 65535, not 1024")

    # 0x184c8 has no +ac zero guard. Its VCMPE/BHS sequence is an ordered
    # finite minimum only; it is deliberately not modeled as VMINNM.
    need(image[0x1853C:0x18556].hex() ==
         "b4f85c0000ee100ab8ee400adfed490a80ee201ab0ee41aaf0ee",
         "optional divisor load without intervening zero guard")
    need(image[0x18596:0x185D8].hex() ==
         "9ded000ab4eec80af1ee10fa03d29ded000ab0ee408a9ded010ab4eee80a"
         "f1ee10fa03d29ded010af0ee408a9ded020ab4eec90af1ee10fa0ad2"
         "9ded020ab0ee409a",
         "three VCMPE/BHS conditional replacements")

    # The returned duty-dependent value is supplied to 0x18410, whose
    # result triple is supplied to 0x184c8. The latter returns the exact
    # three stack values later handed back by 0x18984.
    need(bl_target(image, 0x189CE) == 0x188D8 and
         bl_target(image, 0x189DA) == 0x18410 and
         bl_target(image, 0x18A10) == 0x184C8,
         "duty-to-triple calls")
    need(image[0x189CA:0x18A3C].hex() ==
         "b0ee490afff783fff0ee40aab0ee6a0afff719fd8ded000acded010a8ded021a"
         "9ded021added010a9ded000afcf719fff0ee409af0ee691a28469ded021added010a"
         "9ded000afff75afd8ded030acded040a8ded051a9ded051added040a9ded030a"
         "00f00af89ded030added040a9ded051a",
         "triple dataflow tail")

    # Feedback scalar: 0x20000890 is loaded before 0x18674, its halfword
    # result goes to 0xd254, and the new float is saved back before dispatch.
    need(u32(image, 0x13778) == 0x20000890,
         "feedback float literal")
    need(image[0x1365A:0x13690].hex() ==
         "06a84649d1ed001a9ded041added030a9ded020a05f001f818f0b9fcf9f7a9fc"
         "bdf80410bdf81800f9f7e7fdb0ee408a3b4880ed008a",
         "feedback load/derive/save order")
    need(image[0x1867A:0x186B8].hex() ==
         "b0ee618a0446f6f78cfc0546b5f85c0000ee100ab8ee400adfed0b0a80ee201a"
         "f0ee418af0ee480ab0ee680a01f097fc00f067fc01f0c7f901f094fd2080",
         "feedback halfword derivation")
    need(image[0xD516:0xD530].hex() ==
         "00ee105ab8ee400adfed280a80ee201a2d4880ed001a90ed000a",
         "d254 final u16/1024 return cache")
    need(image[0xD442:0xD464].hex() ==
         "b7f8960110b9b7f89a0140b1b7f89c0110b95948058004e05848058801e056480580",
         "d254 bounded NPC control reads")

    # Demonstrate only numeric relations; do not attach physical units.
    for duty in (0, 1, 512, 1023):
        normalized = f32(f32(float(duty)) / f32(1023.0))
        need(0.0 <= normalized <= 1.0, "low-ten normalization range")
    need(f32(f32(1023.0) / f32(1023.0)) == 1.0,
         "full low-ten normalization")
    need(f32(f32(65535.0) / f32(65535.0)) == 1.0,
         "full u16 normalization")

    return {
        "package_sha256": PACKAGE_SHA256,
        "dispatch_call": "0x136d0->0x180e4",
        "integer_inputs": {
            "r0": "u32[0x20000e38] before same-pass increment",
            "r1": "u32[0x20000e3c] before same-pass increment",
        },
        "float_inputs": {
            "s0_s2": "saved return triple from 0x18984",
            "s3": "0xd254 final_u16 / 1024.0",
        },
        "f3_0x128_join": "conditional positive dataflow via NPC_AP+a6 and 0x188d8/0x18410/0x184c8",
        "direct_same_invocation_source_bin_outputs_feed_saved_triple": False,
        "field_units_identified": False,
        "physical_application_proved": False,
        "verified_bodies": sorted(bodies),
    }


def expect_failure(image: bytes, offset: int, label: str) -> None:
    changed = bytearray(image)
    changed[offset] ^= 1
    try:
        verify_image(bytes(changed))
    except ValueError:
        return
    raise ValueError("mutation was not rejected: " + label)


def main() -> None:
    package = load(PACKAGE, PACKAGE_SHA256)
    need(len(package) == 0x500000, "selected package extent")
    load(PRIOR_DUTY, PRIOR_DUTY_SHA256)
    load(PRIOR_F300, PRIOR_F300_SHA256)
    # AF is intentionally content-mutable while its independent audit is
    # being reconciled; require existence only and do not consume its prose.
    need(PRIOR_DIVISOR.is_file(), "prior divisor report exists")
    image = package[0x200:0x40200]
    result = verify_image(image)
    expect_failure(image, 0x188F0, "duty arithmetic")
    expect_failure(image, 0x18958, "duty cache scale literal")
    expect_failure(image, 0x18596, "conditional comparison")
    expect_failure(image, 0x38B1C, "counter literal")
    result["negative_mutations_rejected"] = 4
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
