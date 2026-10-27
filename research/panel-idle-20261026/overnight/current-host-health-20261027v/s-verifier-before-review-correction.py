#!/usr/bin/env python3
"""Finite offline checks for three selected-image AP_EXCO helper bodies."""

from pathlib import Path
import hashlib
import json
import struct

HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
BACKUP = OVERNIGHT / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
M_CAPTURE = OVERNIGHT / "ap-exco-source-read-20261027m/capture-once"
O_CAPTURE = OVERNIGHT / "ap-exco-callback-source-20261027o/capture-once"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, digest):
    raw = path.read_bytes()
    need(sha(raw) == digest, "SHA-256 " + str(path))
    return raw


def u16(raw, offset):
    return struct.unpack_from("<H", raw, offset)[0]


def u32(raw, offset):
    return struct.unpack_from("<I", raw, offset)[0]


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


def branch16_target(image, address):
    instruction = u16(image, address)
    need(instruction & 0xF000 == 0xD000 and instruction & 0x0F00 != 0x0F00,
         f"conditional branch encoding {address:#x}")
    value = (instruction & 0xFF) << 1
    if value & 0x100:
        value -= 0x200
    return address + 4 + value


def cstring(package, va):
    start = va + 0x200
    end = package.index(b"\0", start, start + 80)
    raw = package[start:end]
    need(raw and all(0x20 <= byte <= 0x7E for byte in raw), f"cstring {va:#x}")
    return raw.decode("ascii")


def maybe_printable(package, va):
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
        instruction = u16(image, address)
        if instruction & 0xF800 == 0xA000:
            target = ((address + 4) & ~3) + (instruction & 0xFF) * 4
            text = maybe_printable(package, target)
            if text is not None:
                result.append((address, "adr", target, text))
        elif instruction & 0xF800 == 0x4800:
            literal = ((address + 4) & ~3) + (instruction & 0xFF) * 4
            if literal + 4 <= len(image):
                target = u32(image, literal)
                text = maybe_printable(package, target)
                if text is not None:
                    result.append((address, "ldr-literal", target, text))
    return result


def main():
    package = load(PACKAGE, "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    need(len(package) == 0x500000, "package extent")
    image = package[0x200:0x40200]

    # Positive object-level names and destinations from the exact ordinary
    # registry table. No field name is inferred from these row labels.
    table = package[0x3CCBC:0x3CF08]
    need(sha(table) == "669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287",
         "ordinary registry table")
    rows = [struct.unpack_from("<7I", table, index * 28) for index in range(21)]
    expected = {
        "AP": (1, 0x3DE88, 0x2000F0E0, 0x40C),
        "NPC_AP": (2, 0x3DE84, 0x2000D71C, 0x540),
        "AP_EXCO": (10, 0x3DD8C, 0x2000FF14, 0x33A),
        "AP_AG": (13, 0x3DE64, 0x2000DC5C, 0x282),
    }
    for name, (index, name_va, base, extent) in expected.items():
        row = rows[index]
        need(row[:3] == (name_va, base, extent), f"{name} row")
        need(cstring(package, name_va) == name, f"{name} label")

    multi = struct.unpack_from("<7I", package, 0x3C5B8)
    need(multi == (0x3DD84, 0x3D44B, 2, 0x3DD8C, 0x200158A8, 0x3EC, 0x18),
         "derived MULTI/AP_EXCO record")
    need(cstring(package, multi[0]) == "MULTI" and
         cstring(package, multi[3]) == "AP_EXCO", "derived registry labels")

    getters = {
        0xE660: (0x2000DC5C, "cc248c859236659913895d13a528929e84c8e614e29f3348fc4de6ee4a293947"),
        0xE670: (0x2000F0E0, "2f24cbd0d31aea9c8e387aac1ce94e6aa00ea1a72dff69c96f6a5c6e752ccf54"),
        0xE678: (0x2000FF14, "87fd2495df98c5847a6492c2cfb3599a0554f072d430266d55f55e307f595705"),
        0xE76C: (0x200158A8, "a971931ca704d394dc4e3ea628440af003c9773be24beb079d5a66a08fefcfc0"),
        0xEF9C: (0x2000D71C, "84f93c6639be7fc7a21229eead9d80b31746059a46741f4973167e2b14ff0b47"),
    }
    for address, (literal, digest) in getters.items():
        raw = image[address:address + 8]
        need(sha(raw) == digest and raw[:4] == bytes.fromhex("00487047") and
             u32(raw, 4) == literal, f"getter {address:#x}")

    # Evaluate the equations against the already copied selected and backup
    # AP_EXCO initializer payloads. This is a stored-image statement, not a
    # claim that either payload was the live event-time source.
    backup = load(BACKUP, "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562")
    directory = package[0x85E00:0x86000]
    need(directory == backup[0x85E00:0x86000] and sha(directory) ==
         "dad4caf149769f0b363a11231267d73752802a3bd7484bd720562bbaa7be1cd8",
         "selected/backup AP_EXCO directory")
    need(directory[:32] == b"AP_EXCO" + bytes(25), "stored AP_EXCO label")
    first_offset, first_length = 0x182200, 0x33A
    initializer = package[first_offset:first_offset + first_length]
    need(initializer == backup[first_offset:first_offset + first_length] and
         sha(initializer) == "c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf",
         "selected/backup first AP_EXCO payload")
    initial_u16 = {offset: u16(initializer, offset) for offset in
                   (0xCA, 0xCC, 0xCE, 0xE0, 0xE2, 0xE4, 0xE6,
                    0x10A, 0x10C, 0x2CC, 0x2CE, 0x2E4, 0x2E6,
                    0x2F4, 0x2F6, 0x2FC, 0x300, 0x302)}
    need(initial_u16 == {
        0xCA: 1, 0xCC: 1, 0xCE: 0, 0xE0: 30, 0xE2: 0, 0xE4: 0,
        0xE6: 0, 0x10A: 0, 0x10C: 0, 0x2CC: 1, 0x2CE: 2,
        0x2E4: 0x32, 0x2E6: 0xA000, 0x2F4: 0x32, 0x2F6: 0xA000,
        0x2FC: 0, 0x300: 0, 0x302: 0,
    }, "stored initializer fields")
    initial_x = (initial_u16[0x10C] << 16) | initial_u16[0x10A]
    initial_r5 = (initial_u16[0x2F4] << 16) | initial_u16[0x2F6]
    need(initial_x == 0 and initial_r5 == 0x0032A000 and
         not (initial_x > initial_r5), "stored bit-1 invariant is false")
    need((initializer[0xE6] & 1) == 0 and u16(initializer, 0x2FC) == 0,
         "stored final predicate is zero")

    # The first helper is complete through its restoring return at 0x2f96c.
    # Pin its body, literal pool, four object getters, control region, and the
    # only relevant +ca/+e6/+2fc accesses.
    first = image[0x2F5D8:0x2F970]
    pool = image[0x2F970:0x2F980]
    need(len(first) == 920 and sha(first) ==
         "428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45",
         "0x2f5d8 body")
    need(pool.hex() == "a4094158810e0020941a6058941a6258" and sha(pool) ==
         "9a9c9a4bfefe85282065081ad355f3168e7551664dea99ad0eaf769039ea31c3",
         "0x2f5d8 literal pool")
    need(sha(image[0x2F804:0x2F964]) ==
         "1edc35ef9c97b5836cbf6be9c671d948f247b31375c70d1fe9cff1f57941566a",
         "0x2f5d8 decision/output region")
    need([bl_target(image, address) for address in (0x2F5E2, 0x2F5E8, 0x2F5EE, 0x2F5F4)] ==
         [0xE76C, 0xE678, 0xEF9C, 0xE670], "0x2f5d8 getter order")
    need(branch16_target(image, 0x2F80A) == 0x2F908, "+ca zero branch")
    need(first.count(bytes.fromhex("b4f8ca00")) == 1, "+ca read count")
    need(first.count(bytes.fromhex("a4f8ca00")) == 0, "+ca is not written")
    need(first.count(bytes.fromhex("a4f8e600")) == 2, "+e6 write paths")
    need(bytes.fromhex("b4f8fc02") not in first and
         bytes.fromhex("a4f8fc02") not in first, "+2fc untouched by first helper")
    need(u32(image, 0x2F970) == 0x584109A4 and
         u32(image, 0x2F974) == 0x20000E81 and
         u32(image, 0x2F978) == 0x58601A94 and
         u32(image, 0x2F97C) == 0x58621A94, "first helper literals")

    # The bit-0 helper's whole body is small enough to pin. Its exact branches
    # prove the disjunction and its set/increment versus reset/clear behavior.
    bit0 = image[0x2F9BA:0x2FA38]
    need(len(bit0) == 126 and sha(bit0) ==
         "e0b885549f1a95d40867a7289c6b7d05eba931523a9a10ae7a7c7ed4fa35bae5",
         "0x2f9ba body")
    need([bl_target(image, address) for address in (0x2F9BC, 0x2F9C2, 0x2F9C8)] ==
         [0xE670, 0xE660, 0xE678], "bit-0 getter order")
    need(branch16_target(image, 0x2F9D8) == 0x2F9E6 and
         branch16_target(image, 0x2F9E4) == 0x2F9FE and
         branch16_target(image, 0x2F9F0) == 0x2FA24 and
         branch16_target(image, 0x2F9FC) == 0x2FA24 and
         branch16_target(image, 0x2FA08) == 0x2FA18,
         "bit-0 condition branches")
    need(bit0.count(bytes.fromhex("b4f8fc02")) == 2 and
         bit0.count(bytes.fromhex("a4f8fc02")) == 2 and
         bytes.fromhex("40f00100") in bit0 and
         bytes.fromhex("20f00100") in bit0, "bit-0 set/clear paths")

    # The bit-1 helper samples three fixed 32-bit words, persists each pair of
    # halves, applies six strict comparisons, then debounces bit 1.
    bit1 = image[0x2FA38:0x2FB40]
    need(len(bit1) == 264 and sha(bit1) ==
         "0275a3f5b85be051f4b4a48a2759b9cf8005ffdc96e6b7f26e1c5735274cfb56",
         "0x2fa38 body")
    need(bl_target(image, 0x2FA3C) == 0xE678, "bit-1 ordinary getter")
    need(u32(image, 0x2FB40) == 0x584109A4 and
         sha(image[0x2FB40:0x2FB44]) ==
         "92e54f111a9ae505abda8c7dfa6dee7e56c954ecd2947c2bd19b1e5022580bbf",
         "bit-1 fixed source literal")
    need(all(branch16_target(image, address) == 0x2FB2A
             for address in (0x2FAD6, 0x2FADC, 0x2FAE2, 0x2FAE6, 0x2FAEC, 0x2FAF2)),
         "bit-1 six-comparison failure target")
    need(branch16_target(image, 0x2FAFE) == 0x2FB1E, "bit-1 debounce increment")
    need(bit1.count(bytes.fromhex("b4f8fc02")) == 2 and
         bit1.count(bytes.fromhex("a4f8fc02")) == 2 and
         bytes.fromhex("40f00200") in bit1 and
         bytes.fromhex("20f00200") in bit1, "bit-1 set/clear paths")

    need(direct_callers(image, 0x2F5D8) == [0x2FB52] and
         direct_callers(image, 0x2F9BA) == [0x2F99E] and
         direct_callers(image, 0x2FA38) == [0x2F9AC], "private direct callers")
    need(direct_printable_refs(package, image, 0x2F5D8, 0x2F970) == [] and
         direct_printable_refs(package, image, 0x2F9BA, 0x2FA38) == [] and
         direct_printable_refs(package, image, 0x2FA38, 0x2FB40) == [],
         "no direct printable field/control names")

    # Retained ordinary captures cover only +0..+f and +3cc..+3eb. The later
    # corrected captures cover those offsets in the distinct derived object.
    source_base = load(M_CAPTURE / "source-base-window.bin",
                       "374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb")
    source_tail = load(M_CAPTURE / "source-tail-window.bin",
                       "f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b")
    callback_base = load(O_CAPTURE / "callback-base-window.bin",
                         "21f2234ff842c398b65210295a7a5e15220503bc73240a0eb68e4b897929db47")
    callback_tail = load(O_CAPTURE / "callback-tail-window.bin",
                         "eb1b55a1e4f19a403134f7ddc3a4f7f3853f50ef06cb9b9e74a5659f6183323f")
    need((len(source_base), len(source_tail), len(callback_base), len(callback_tail)) ==
         (16, 32, 16, 32), "retained capture extents")
    ordinary_ranges = ((0, 0x10), (0x3CC, 0x3EC))
    required = (0xCA, 0xCC, 0xCE, 0xE0, 0xE2, 0xE4, 0xE6,
                0x2CC, 0x2CE, 0x2D0, 0x2FC, 0x300, 0x302, 0x306)
    need(all(not any(start <= offset < end for start, end in ordinary_ranges)
             for offset in required), "helper inputs absent from ordinary captures")
    need(callback_tail[0x3D8 - 0x3C8] == 1, "late derived +3d8 value")

    print(json.dumps({
        "schema": "ap-exco-helper-inputs-v1",
        "target_operations": 0,
        "helpers": {
            "0x2f5d8": {
                "effect": "+e6 = F0 | (F1 << 1) when +ca != 0, else 0",
                "writes_plus_ca": False,
                "writes_plus_2fc": False,
            },
            "0x2f9ba": {"effect": "debounced set/reset of +2fc bit0"},
            "0x2fa38": {"effect": "debounced set/reset of +2fc bit1"},
        },
        "positive_object_names": ["AP_EXCO", "AP", "AP_AG", "NPC_AP", "MULTI/AP_EXCO"],
        "positive_field_names_or_units": [],
        "stored_initializer": {
            "selected_equals_backup": True,
            "+ca": 1, "+cc": 1, "+ce": 0, "+e0": 30,
            "+e6": 0, "+2cc": 1, "+2ce": 2, "+2fc": 0,
            "final_predicate": 0,
            "first_pass_cannot_mature_F0": True,
            "bit1_condition_forced_false_by_X_le_R5": True,
        },
        "retained_captures_cover_helper_inputs": False,
        "late_derived_plus3d8": 1,
        "late_one_is_stored_initializer_default": False,
        "fault_source_discriminated": False,
        "complete_writer_or_physical_source_census": False,
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
