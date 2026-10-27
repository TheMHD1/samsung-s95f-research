#!/usr/bin/env python3
"""Finite offline provenance checks for the corrected derived AP_EXCO object."""

from pathlib import Path
import hashlib
import json
import struct

HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
OLD_CAPTURE = OVERNIGHT / "ap-exco-source-read-20261027m/capture-once"
NEW_CAPTURE = OVERNIGHT / "ap-exco-callback-source-20261027o/capture-once"


def need(ok, why):
    if not ok:
        raise ValueError(why)


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


def main():
    package = load(PACKAGE, "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    need(len(package) == 0x500000, "package extent")
    image0 = package[0x200:0x40200]

    # The separate 0x1000c-root record names a MULTI/AP_EXCO object. Its
    # destination and extent are positive; the other record fields stay unnamed.
    record = package[0x3C5B8:0x3C5D4]
    need(sha(record) == "41dfa8809a435830065f05cbcf22bc20ee9b0f4b4f773e3d49f02f3b04403f66",
         "alternate registry record")
    words = struct.unpack("<7I", record)
    need(words == (0x3DD84, 0x3D44B, 2, 0x3DD8C, 0x200158A8, 0x3EC, 0x18),
         "alternate registry words")
    need(package[0x3DF84:0x3DF8A] == b"MULTI\0" and
         package[0x3DF8C:0x3DF94] == b"AP_EXCO\0", "registry names")

    # Image-0's ordinary accessor returns the CPU object directly.
    getter = image0[0xE76C:0xE774]
    need(getter.hex() == "00487047a8580120" and
         sha(getter) == "a971931ca704d394dc4e3ea628440af003c9773be24beb079d5a66a08fefcfc0",
         "derived object getter")
    need(u32(image0, 0xE770) == 0x200158A8, "getter literal")

    # Reset scatter row 11 zero-fills the whole corrected object. Pin both the
    # complete table and the zero routine's relevant loop rather than inferring
    # allocation from address arithmetic alone.
    table = package[0x3E340:0x3E400]
    need(sha(table) == "3f09781583f48d9b429fe8438b06bbd26196b3f673c79e6a2cf7adde356b612d",
         "image0 scatter table")
    rows = [struct.unpack_from("<4I", table, i * 16) for i in range(12)]
    need(rows[11] == (0x3E764, 0x20000F4C, 0x16438, 0x1D8), "zero-fill row")
    zero_start, zero_end = rows[11][1], rows[11][1] + rows[11][2]
    need(zero_start <= 0x200158A8 and 0x20015C94 <= zero_end == 0x20017384,
         "object inside zero-fill extent")
    zero = image0[0x1D8:0x1F4]
    need(zero.hex() == "0023002400250026103a28bf78c1fbd8520728bf30c148bf0b607047",
         "zero-fill loop and bounded tail")

    # The large ordinary startup initializer at 0x398c4 calls 0x333a8 once.
    # That sub-initializer obtains this getter into r4 and explicitly clears
    # object byte +0. This is runtime initialization in addition to reset zero.
    init = image0[0x333A8:0x33468]
    need(sha(init) == "d0e5c3d63a9691982e8a1d475d05260392a4b6298095baef2c5d97369f4646f7",
         "derived object ordinary initializer")
    need(bl_target(image0, 0x333C4) == 0xE76C, "initializer getter")
    need(image0[0x333C8:0x333EC].hex().endswith("00bf00202070"),
         "initializer explicit byte-zero store")
    need(direct_callers(image0, 0x333A8) == [0x39B22], "startup initializer caller")
    need(bl_target(image0, 0x39B22) == 0x333A8, "startup call")

    # A bounded direct setter takes its caller's r0 byte, obtains the derived
    # root, and stores that value to +0. Its field meaning is not named.
    plus0 = image0[0x3286C:0x328A4]
    need(sha(plus0) == "ccaae391eab8d2cda5b01f181a99308fb799ba9e93923251f3fb29a841616a9d",
         "+0 setter")
    need(image0[0x3286C:0x3287E].hex() == "70b50546dbf77cff04460b480b4908602570",
         "+0 input/getter/store dataflow")
    need(bl_target(image0, 0x32870) == 0xE76C, "+0 getter")
    need(direct_callers(image0, 0x3286C) == [0x329F8, 0x32A0C, 0x32A2E, 0x32AB6],
         "+0 direct caller census")

    # The finite +1 setter is even narrower: caller r0 -> r4, getter -> r5,
    # STRB r4,[r5,#1]. Caller-specific meanings are outside this pass.
    plus1 = image0[0x35B56:0x35B6A]
    need(sha(plus1) == "50d464ed7f82d179e974c298739548ca77b0fc698dcc6a57e79c48397d8174ce",
         "+1 setter")
    need(bl_target(image0, 0x35B5A) == 0xE76C and
         image0[0x35B5E:0x35B64].hex() == "05466c702846", "+1 direct dataflow")
    need(direct_callers(image0, 0x35B56) ==
         [0x35C8C, 0x35CDA, 0x35CE4, 0x35D14, 0x35D1E, 0x35D2A, 0x35D44, 0x35D66, 0x35E4E],
         "+1 direct caller census")

    # The strongest positive derivation is byte +0x3d8. Function 0x2fb44 gets
    # the derived root in r5 and the ordinary AP_EXCO root in r4, then calls
    # 0x2f5d8 unconditionally. Ordinary +0xca subsequently gates helper
    # 0x2f980. Only after those calls does it form the stored boolean from the
    # then-current (+0xe6 & 1) OR +0x2fc values and write derived +0x3d8.
    plus3d8 = image0[0x2FB44:0x2FB7C]
    need(sha(plus3d8) == "f9b94ce545ffc142ac8cbff9d0c4f2c6bcf7146316a59dd32d49814ffb8443a7",
         "+3d8 derivation")
    need(bl_target(image0, 0x2FB46) == 0xE76C and
         bl_target(image0, 0x2FB4C) == 0xE678, "derived/ordinary getters")
    need(bl_target(image0, 0x2FB52) == 0x2F5D8 and
         bl_target(image0, 0x2FB5C) == 0x2F980,
         "pre-reduction call order")
    need(image0[0x2FB56:0x2FB7A].hex() ==
         "b4f8ca0008b1fff710ff94f8e60000f00100b4f8fc12084308b1012000e0002085f8d803",
         "+3d8 boolean reduction and store")
    need(direct_callers(image0, 0x2FB44) == [0x13710], "+3d8 direct caller")

    # Pin the directly visible helper effect that matters to the final
    # reduction: its fall-through path writes zero to ordinary halfword +2fc.
    # The nested call targets remain outside this bounded pass.
    need(image0[0x2F9B2:0x2F9B8].hex() == "0020a4f8fc02",
         "helper direct +2fc clear")

    # The older ordinary captures do not overlap the three positive transform
    # inputs. Keep them as raw evidence without imposing 20/0 defaults on this
    # distinct derived object.
    old_base = load(OLD_CAPTURE / "source-base-window.bin",
                    "374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb")
    old_tail = load(OLD_CAPTURE / "source-tail-window.bin",
                    "f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b")
    need(len(old_base) == 16 and len(old_tail) == 32, "old raw extents")
    old_ranges = [(0, 0x10), (0x3CC, 0x3EC)]
    transform_offsets = (0xCA, 0xE6, 0x2FC)
    need(all(not any(start <= offset < end for start, end in old_ranges)
             for offset in transform_offsets), "transform inputs absent from old captures")

    # The corrected late sample is positive raw corroboration of the three
    # fields only. It is neither an invocation trace nor an event-time tuple.
    pointer = load(NEW_CAPTURE / "pointer-window.bin",
                   "7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3")
    base = load(NEW_CAPTURE / "callback-base-window.bin",
                "21f2234ff842c398b65210295a7a5e15220503bc73240a0eb68e4b897929db47")
    tail = load(NEW_CAPTURE / "callback-tail-window.bin",
                "eb1b55a1e4f19a403134f7ddc3a4f7f3853f50ef06cb9b9e74a5659f6183323f")
    need(u32(pointer, 0x0C) == 0x450158A8, "live pointer binding")
    need((base[0], base[1], tail[0x10]) == (3, 10, 1), "late field tuple")

    print(json.dumps({
        "schema": "ap-exco-derived-object-provenance-v1",
        "target_operations": 0,
        "object": {"cpu_base": "0x200158a8", "extent": "0x3ec",
                   "positive_names": ["MULTI", "AP_EXCO"]},
        "reset_initial_values": {"+0": 0, "+1": 0, "+0x3d8": 0},
        "ordinary_paths": {
            "+0": "unnamed input-byte setter plus startup clear",
            "+1": "unnamed input-byte setter",
            "+0x3d8": ("call 0x2f5d8; ordinary +0xca gates 0x2f980; "
                       "then boolean is post-helper (+0xe6 bit0) OR +0x2fc"),
        },
        "late_sample": {"+0": 3, "+1": 10, "+0x3d8": 1,
                        "event_time_or_invocation_proved": False},
        "old_raw_windows_cover_transform_inputs": False,
        "field_names_or_units_proved": False,
        "complete_computed_or_indirect_writer_census": False,
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
