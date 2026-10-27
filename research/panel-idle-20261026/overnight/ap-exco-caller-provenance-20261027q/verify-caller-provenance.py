#!/usr/bin/env python3
"""Finite offline direct-caller provenance for three derived-object setters."""

from pathlib import Path
import hashlib
import json
import struct

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def bl_target(image, address):
    first, second = struct.unpack_from("<HH", image, address)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"BL encoding {address:#x}")
    s = (first >> 10) & 1
    j1, j2 = (second >> 13) & 1, (second >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ s), 1 ^ (j2 ^ s)
    value = ((s << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def direct_callers(image, target):
    result = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000:
            if bl_target(image, address) == target:
                result.append(address)
    return result


def adr_target(image, address):
    instruction = struct.unpack_from("<H", image, address)[0]
    need(instruction & 0xF800 == 0xA000, f"ADR encoding {address:#x}")
    return ((address + 4) & ~3) + (instruction & 0xFF) * 4


def branch16_target(image, address):
    instruction = struct.unpack_from("<H", image, address)[0]
    if instruction & 0xF000 == 0xD000 and instruction & 0x0F00 != 0x0F00:
        value = (instruction & 0xFF) << 1
        if value & 0x100:
            value -= 0x200
        return address + 4 + value
    need(instruction & 0xF800 == 0xE000, f"B encoding {address:#x}")
    value = (instruction & 0x7FF) << 1
    if value & 0x800:
        value -= 0x1000
    return address + 4 + value


def cbz_target(image, address):
    instruction = struct.unpack_from("<H", image, address)[0]
    need(instruction & 0xFD00 == 0xB100, f"CBZ encoding {address:#x}")
    offset = (((instruction >> 9) & 1) << 6) | (((instruction >> 3) & 0x1F) << 1)
    return address + 4 + offset


def cstring(package, va):
    start = va + 0x200
    end = package.index(b"\0", start, start + 80)
    return package[start:end].decode("ascii")


def printable_at(package, va):
    if not 0 <= va < 0x40000:
        return None
    start = va + 0x200
    try:
        end = package.index(b"\0", start, min(start + 80, len(package)))
    except ValueError:
        return None
    raw = package[start:end]
    if len(raw) < 3 or any(byte < 0x20 or byte > 0x7E for byte in raw):
        return None
    return raw.decode("ascii")


def direct_printable_refs(package, image, start, end):
    result = []
    for address in range(start, end, 2):
        instruction = struct.unpack_from("<H", image, address)[0]
        if instruction & 0xF800 == 0xA000:
            target = ((address + 4) & ~3) + (instruction & 0xFF) * 4
            text = printable_at(package, target)
            if text is not None:
                result.append((address, "adr", target, text))
        elif instruction & 0xF800 == 0x4800:
            literal = ((address + 4) & ~3) + (instruction & 0xFF) * 4
            if literal + 4 <= len(image):
                target = struct.unpack_from("<I", image, literal)[0]
                text = printable_at(package, target)
                if text is not None:
                    result.append((address, "ldr-literal", target, text))
    return result


def main():
    package = PACKAGE.read_bytes()
    need(len(package) == 0x500000 and sha(package) ==
         "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0",
         "selected package")
    image = package[0x200:0x40200]

    # +0 setter 0x3286c has exactly four direct callers in one unnamed
    # decision routine. Each call is immediately loaded with a fixed r0 value.
    plus0_callers = direct_callers(image, 0x3286C)
    need(plus0_callers == [0x329F8, 0x32A0C, 0x32A2E, 0x32AB6], "+0 callers")
    plus0_values = {0x329F8: 4, 0x32A0C: 1, 0x32A2E: 2, 0x32AB6: 3}
    for call, value in plus0_values.items():
        need(struct.unpack_from("<H", image, call - 2)[0] == 0x2000 | value,
             f"+0 immediate {call:#x}")
        need(bl_target(image, call) == 0x3286C, f"+0 call {call:#x}")
    plus0_parent = image[0x329CE:0x32AC8]
    need(sha(plus0_parent) == "85b842155f9881c6d0bf8e25a71ca51bd442ce5e28b3b6f3bb0681e80e716cd3",
         "+0 caller routine")
    need(direct_printable_refs(package, image, 0x329CE, 0x32AC8) == [],
         "+0 parent has no direct printable reference")

    # +1 setter callers all belong to one larger switch/command routine. Pin
    # every direct caller and every immediate argument; one path uses 8/10
    # selected directly from derived +0x3d8.
    plus1_callers = direct_callers(image, 0x35B56)
    need(plus1_callers == [0x35C8C, 0x35CDA, 0x35CE4, 0x35D14, 0x35D1E,
                           0x35D2A, 0x35D44, 0x35D66, 0x35E4E], "+1 callers")
    plus1_immediates = {0x35C8C: 11, 0x35CDA: 3, 0x35CE4: 2, 0x35D14: 6,
                        0x35D1E: 4, 0x35D2A: 5, 0x35D44: 7, 0x35E4E: 9}
    for call, value in plus1_immediates.items():
        need(struct.unpack_from("<H", image, call - 2)[0] == 0x2000 | value,
             f"+1 immediate {call:#x}")
    need(image[0x35D58:0x35D6A].hex() == "96f8d81309b10a21 00e00821 0846fff7f6fe".replace(" ", ""),
         "+3d8 chooses +1 code 10/8")
    need(bl_target(image, 0x35D66) == 0x35B56, "+1 selected call")
    plus1_parent = image[0x35BBA:0x35E8A]
    need(sha(plus1_parent) == "d5b296850cb370ddcafff35386db425a0355411b5835281fd364db79dfbb83ac",
         "+1 parent routine")

    # Only direct string references are accepted as names. These strings occur
    # in the same parent switch, but none is bound to a setter value. In
    # particular, the Write-panelID branch is control-flow-separated from the
    # value-11 callsite: BNE reaches the branch instruction, which jumps to the
    # common tail rather than falling through to the setter.
    direct_strings = {
        0x35C7C: (0x35E90, "Write-panelID"),
        0x35C94: (0x35EA4, "vcal_sw_ctrl_one"),
        0x35CAA: (0x35EBC, "cooling"),
        0x35CF8: (0x35EBC, "cooling"),
        0x35D82: (0x35EC8, "ELVDD_EN"),
    }
    for site, (target, text) in direct_strings.items():
        need(adr_target(image, site) == target and cstring(package, target) == text,
             f"direct string {site:#x}")
    need(image[0x35C7C:0x35C90].hex() == "84a300221146874801f0ecf9efe00b20fff763ff",
         "Write-panelID and adjacent value-11 blocks")
    need(branch16_target(image, 0x35C7A) == 0x35C88 and
         branch16_target(image, 0x35C88) == 0x35E6A,
         "Write-panelID path bypasses value-11 setter")
    need(direct_printable_refs(package, image, 0x35BBA, 0x35E8A) ==
         [(0x35C7C, "adr", 0x35E90, "Write-panelID"),
          (0x35C94, "adr", 0x35EA4, "vcal_sw_ctrl_one"),
          (0x35CAA, "adr", 0x35EBC, "cooling"),
          (0x35CF8, "adr", 0x35EBC, "cooling"),
          (0x35D82, "adr", 0x35EC8, "ELVDD_EN")],
         "+1 bounded direct printable references")

    # The derivation has one direct entry from a large unnamed startup/task
    # function. No direct printable string reference exists in the bounded
    # prefix ending at the call, so no function name is invented.
    need(direct_callers(image, 0x2FB44) == [0x13710], "derivation callers")
    derivation_parent = image[0x13464:0x13714]
    need(sha(derivation_parent) == "fb02019acc42be182aa0b7b0f2843e709f2b0d5bb8df232496bbb10f426d7a8b",
         "derivation parent")
    need(direct_printable_refs(package, image, 0x13464, 0x13714) == [],
         "derivation parent has no direct printable reference")
    need(bl_target(image, 0x13710) == 0x2FB44, "derivation call")
    need(bl_target(image, 0x2FB52) == 0x2F5D8 and
         bl_target(image, 0x2FB5C) == 0x2F980,
         "derivation pre-reduction call order")

    # Helper 0x2f980 is private to the derivation. It reads ordinary +2cc and
    # +2ce, dispatches on +2ce bits 0/1, and has a direct path that clears
    # ordinary +2fc. The unconditional 0x2f5d8 call and the two nested branch
    # targets are the precise first unresolved edges.
    helper = image[0x2F980:0x2F9BA]
    need(sha(helper) == "84fb989b1945c419f9291ec374ba59c57fb71807227f7892d5be2cc9ad2dfc12",
         "conditional helper")
    need(direct_printable_refs(package, image, 0x2F980, 0x2F9BA) == [],
         "helper has no direct printable reference")
    need(direct_callers(image, 0x2F980) == [0x2FB5C], "helper callers")
    need(bl_target(image, 0x2F982) == 0xE678, "helper ordinary getter")
    need(image[0x2F988:0x2F9B8].hex() ==
         "b4f8cc0288b1b4f8ce0270b194f8ce0200f0010008b100f00cf894f8ce0200f0020028b100f044f802e00020a4f8fc02",
         "helper exact conditions")
    need(bl_target(image, 0x2F99E) == 0x2F9BA and
         bl_target(image, 0x2F9AC) == 0x2FA38, "nested helper branches")
    need(cbz_target(image, 0x2F98C) == 0x2F9B2 and
         cbz_target(image, 0x2F992) == 0x2F9B2 and
         cbz_target(image, 0x2F99C) == 0x2F9A2 and
         cbz_target(image, 0x2F9AA) == 0x2F9B8,
         "helper CBZ control flow")
    need(image[0x2F9B2:0x2F9B8].hex() == "0020a4f8fc02",
         "helper direct +2fc clear")

    print(json.dumps({
        "schema": "ap-exco-caller-provenance-v1",
        "target_operations": 0,
        "plus0": {"fixed_values": [1, 2, 3, 4], "positive_field_name": None},
        "plus1": {"fixed_values": [2, 3, 4, 5, 6, 7, 9, 11],
                  "derived_plus3d8_selects": [8, 10],
                  "positive_field_or_value_name": None,
                  "unbound_parent_switch_strings":
                      ["Write-panelID", "vcal_sw_ctrl_one", "cooling", "ELVDD_EN"]},
        "plus3d8_entry": {
            "caller": "0x13710",
            "ordered_pre_reduction_calls": ["0x2f5d8", "0x2f980-if-+ca-nonzero"],
            "final_reads_follow_helpers": ["+0xe6", "+0x2fc"],
            "positive_name": None,
        },
        "helper_2f980": {"ordinary_offsets": ["0x2cc", "0x2ce", "0x2fc"],
                         "direct_plus2fc_clear_present": True,
                         "first_unresolved_targets":
                             ["0x2f5d8", "0x2f9ba", "0x2fa38"]},
        "field_units_proved": False,
        "whole_system_completeness_claimed": False,
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
