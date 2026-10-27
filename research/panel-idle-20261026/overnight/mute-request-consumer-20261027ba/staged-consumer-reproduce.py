#!/usr/bin/env python3
"""Offline checks for the selected-image derived Failmode consumer."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
PACKAGE_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def cstring(data: bytes, offset: int) -> str:
    return data[offset:data.index(0, offset)].decode("ascii")


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value ^ sign) - sign


def thumb_bl_target(image: bytes, address: int) -> int | None:
    if address < 0 or address + 4 > len(image) or address & 1:
        return None
    first, second = struct.unpack_from("<HH", image, address)
    if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
        return None
    s = (first >> 10) & 1
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    i1 = 1 ^ (j1 ^ s)
    i2 = 1 ^ (j2 ^ s)
    encoded = ((s << 24) | (i1 << 23) | (i2 << 22) |
               ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    return address + 4 + sign_extend(encoded, 25)


def callers(image: bytes, target: int) -> list[int]:
    return [address for address in range(0, len(image) - 3, 2)
            if thumb_bl_target(image, address) == target]


package = PACKAGE.read_bytes()
need(len(package) == 5_242_880 and sha(package) == PACKAGE_SHA, "package identity")
image = package[0x200:0x40200]
need(len(image) == 0x40000, "image-0 extent")

az = OVERNIGHT / "mmio-block-attribution-20261027az/ordinary-mute-receiver.md"
need(sha(az.read_bytes()) == "78ee9e039f6b7f317cf17323e7e01b3bdc2b78f81664a93eb312908537069541",
     "AZ input identity")

slices = {
    "derived_accessor": (0xE76C, 0xE774, "a971931ca704d394dc4e3ea628440af003c9773be24beb079d5a66a08fefcfc0"),
    "request_setter": (0x3A078, 0x3A0CA, "334790e63e567c1af59ed9766d2fea3bdf8836e73046ead3b090c00411969cfb"),
    "status_apply": (0x314C4, 0x3155C, "88056c17683e9e4d529463155630cdea966464dab7fdb24c4009edb5e03ca8ee"),
    "set_side_effect": (0x20744, 0x2076A, "92da54bbc75c2d0df03110b6dc126731a8b14a1dfe7a1327496bba0c9132d000"),
    "clear_side_effect": (0x20770, 0x20788, "64ca8ce0af8081bc1c4c78bbf10ec818d5ccf2fbd79c8887a5d14387911fa95e"),
    "startup_pair": (0x39B50, 0x39B5C, "a4d978d090d3080cc32641b94d3fa01af968268448cc30ef9455cf9c9fd19020"),
    "callback_body": (0x132C0, 0x13346, "2e472ef163d2a285a67628abaef6195cdc824f781654e471f4e9659eb51e7a25"),
    "descriptor_claim": (0x13AA8, 0x13AD6, "4f160a140ffebfdcc7a428da7829be6c682cf040a35167439cf25bf50c0a11fa"),
    "mute_callback_registration": (0x1E702, 0x1E79E, "f8149b02537502650770f0d17f644081262029d70266db922a6cbac7d265fb8e"),
    "fault_teardown": (0x96D8, 0x9746, "9bdc29f2519b7a6ac90e2e3bc5fea5054249f4218d6b99d8591f454e6f4a212d"),
    "descriptor_lookup": (0x38C24, 0x38C38, "287a309773f5f64fae4fac7d201097180674aa4480a6dd708fe5d84afc204df6"),
    "irq_disable_helper": (0x1B0E8, 0x1B100, "6d4da6c2ee0a19e412c80eba27610a4c0040d66bae19a1a1222c5910c7ad294a"),
}
for name, (start, end, expected) in slices.items():
    need(sha(image[start:end]) == expected, "slice mismatch: " + name)

# Object roots and fixed-address literals.
need(u32(image, 0xE770) == 0x200158A8, "derived root")
need(u32(image, 0xE674) == 0x2000F0E0, "common root")
need(u32(image, 0x3155C) == 0x58200000, "status-block root")
need(u32(image, 0x31568) == 0x20000ED8, "clear debounce counter")
need(cstring(image, 0x31560) == "F-Set\n", "set log")
need(cstring(image, 0x3156C) == "F-Clr\n", "clear log")
need(u32(image, 0x2076C) == 0x58300000, "set-side fixed block")
need((u32(image, 0x20788), u32(image, 0x2078C), u32(image, 0x20790)) ==
     (0x20000D40, 0x58300000, 0x20000D4C), "clear-side fixed copies")

# Positive call edges and the finite direct-call context.
need(thumb_bl_target(image, 0x314CC) == 0xE76C, "consumer derived getter")
need(thumb_bl_target(image, 0x314F6) == 0x20744, "set-side call")
need(thumb_bl_target(image, 0x3A0A8) == 0x20770, "clear-side call")
need(image[0x39B52:0x39B54] == bytes.fromhex("0120"), "startup scalar one")
need(thumb_bl_target(image, 0x39B54) == 0x3A078, "startup request setter")
need(thumb_bl_target(image, 0x39B58) == 0x314C4, "startup apply")
need(thumb_bl_target(image, 0x13306) == 0x314C4, "callback apply")
need(callers(image, 0x314C4) == [0x13306, 0x39B58], "direct apply callers")
need(callers(image, 0x20744) == [0x314F6], "set-side callers")
need(callers(image, 0x20770) == [0x3A0A8], "clear-side callers")

# Successful claim returns its input index; failure returns 0xff. This ties
# the registration to descriptor 8 conditionally, not to a measured live IRQ.
need(image[0x1E702:0x1E704] == bytes.fromhex("0820"), "claim descriptor index eight")
need(thumb_bl_target(image, 0x1E704) == 0x13AA8, "descriptor claim call")
need(thumb_bl_target(image, 0x1E70C) == 0x38C24, "claimed descriptor lookup")
need(u32(image, 0x1E8A0) == 0x20000884 and
     u32(image, 0x1E8A4) == 0x132C1, "registration literals")
need(image[0x1E712:0x1E714] == bytes.fromhex("0860") and
     image[0x1E79C:0x1E79E] == bytes.fromhex("8860"), "saved descriptor and callback stores")
need(u32(image, 0x38C34) == 0x20000948, "descriptor table base")
need(image[0x9724:0x9726] == bytes.fromhex("0820"), "teardown descriptor index eight")
need(thumb_bl_target(image, 0x9726) == 0x38C24 and
     thumb_bl_target(image, 0x9730) == 0x1B0E8, "same-descriptor teardown edge")
need(u32(image, 0x1B0FC) == 0xE000E180, "interrupt clear-enable base")

print(json.dumps({
    "accepted": True,
    "source_sha256": PACKAGE_SHA,
    "coordinate_model": "image0 FILE = linked VA + 0x200",
    "staged_word": "derived MULTI/AP_EXCO CPU 0x200158a8 + 0x80",
    "pending_bit": 2,
    "requested_state_bit": 3,
    "consumer_va": "0x314c4",
    "direct_consumer_callers": ["0x13306", "0x39b58"],
    "startup_sequence": "0x3a078(1), then 0x314c4",
    "callback_registration": {
        "descriptor_index_if_claim_succeeds": 8,
        "callback_thumb_pointer": "0x132c1",
        "saved_descriptor_pointer": "0x20000884",
        "claim_failure_return": "0xff",
        "fault_teardown_visits_same_descriptor": True,
        "runtime_irq_identity_or_disable_observed": False,
        "later_reenable_excluded": False,
    },
    "set_apply": {
        "status_field": "0x58200060 bits[23:22] = 2",
        "side_effect_va": "0x20744",
        "side_effect_block": "0x58300000",
        "log": "F-Set\\n",
    },
    "clear_apply": {
        "counter": "0x20000ed8; attempt/pre-read match and pending clear on the third qualifying bit2=1, bit3=0 invocation after 0x3a078(0) resets the counter; no frame/time proof",
        "status_field": "0x58200060 bits[23:22] = 1",
        "common_field": "CPU 0x2000f0e0 + 0x158 = 0xabababab when a write is needed",
        "side_effect_va": "0x20770",
        "side_effect_block": "0x58300000",
        "log": "F-Clr\\n",
    },
    "completion": "consumer clears staged bit2 after a pre-read match or an unacknowledged write attempt",
    "slice_sha256": {name: expected for name, (_, _, expected) in slices.items()},
    "target_operations": 0,
}, indent=2, sort_keys=True))
