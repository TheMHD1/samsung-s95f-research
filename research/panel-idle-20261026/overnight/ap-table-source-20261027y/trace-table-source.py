#!/usr/bin/env python3
"""Finite offline provenance checks for fixed source 0x584109a4."""

from pathlib import Path
import hashlib
import json
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
W = OVERNIGHT / "ap-exco-input-snapshot-20261027w"
I = OVERNIGHT / "rtp-scan-input-origin-20261027i"


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


def literal_refs(image, literal):
    """Find aligned Thumb-1 and Thumb-2 literal-load encodings to literal."""
    found = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 == 0x4800:
            target = ((address + 4) & ~3) + (first & 0xFF) * 4
            if target == literal:
                found.append((address, "ldr16", (first >> 8) & 7))
        elif first == 0xF8DF:
            target = ((address + 4) & ~3) + (second & 0xFFF)
            if target == literal:
                found.append((address, "ldr32-positive", (second >> 12) & 15))
        elif first == 0xF85F:
            target = ((address + 4) & ~3) - (second & 0xFFF)
            if target == literal:
                found.append((address, "ldr32-negative", (second >> 12) & 15))
    return found


def mov_immediate_hits(image, wanted):
    """Find Thumb-2 MOVW/MOVT halves containing one exact 16-bit immediate."""
    found = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xFBF0 == 0xF240:
            kind = "movw"
        elif first & 0xFBF0 == 0xF2C0:
            kind = "movt"
        else:
            continue
        immediate = ((first & 0xF) << 12) | (((first >> 10) & 1) << 11)
        immediate |= ((second >> 12) & 7) << 8 | (second & 0xFF)
        if immediate == wanted:
            found.append((address, kind, (second >> 8) & 15))
    return found


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
        end = package.index(b"\0", start, start + 80)
    except ValueError:
        return None
    raw = package[start:end]
    if len(raw) < 3 or any(byte < 0x20 or byte > 0x7E for byte in raw):
        return None
    return raw.decode("ascii")


def direct_printable_refs(package, image, start, end):
    """Check ADR16 and positive/negative LDR-literal 16/32 references."""
    found = []
    for address in range(start, end, 2):
        instruction = u16(image, address)
        if instruction & 0xF800 == 0xA000:
            target = ((address + 4) & ~3) + (instruction & 0xFF) * 4
        elif instruction & 0xF800 == 0x4800:
            literal = ((address + 4) & ~3) + (instruction & 0xFF) * 4
            if literal + 4 > len(image):
                continue
            target = u32(image, literal)
        elif instruction in (0xF8DF, 0xF85F) and address + 4 <= len(image):
            second = u16(image, address + 2)
            displacement = second & 0xFFF
            literal = ((address + 4) & ~3)
            literal += displacement if instruction == 0xF8DF else -displacement
            if not 0 <= literal <= len(image) - 4:
                continue
            target = u32(image, literal)
        else:
            continue
        text = maybe_printable(package, target)
        if text is not None:
            found.append((address, target, text))
    return found


def main():
    package = load(PACKAGE,
                   "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    need(len(package) == 0x500000, "selected package extent")
    load(W / "aggregate-interpretation.md",
         "e68887c161565753bdf5ec1bcba16cfca00dc2ec437670b242c66d69b20b06f2")
    load(W / "verify-aggregates.py",
         "f7058a485fd7edde0ebda256d917013999ba37a65355342db782b7d936f4e6b7")
    load(I / "rtp-scan-input-origin.md",
         "0d704c421e51d795088a9787b284f80a4d422a8c80a4d5154c0280b0d9accd14")
    load(I / "rtp-scan-input-origin.py",
         "52b92f72a962c431228c27bb3ef4f9498514c6529abe280f476320bcb96ead8a")
    image = package[0x200:0x40200]

    base = 0x584109A4
    base_literals = [offset for offset in range(0, len(image) - 3, 4)
                     if u32(image, offset) == base]
    need(base_literals == [0xF3A8, 0x10424, 0x19330, 0x2F970, 0x2FB40],
         "base literal inventory")
    base_refs = {literal: literal_refs(image, literal) for literal in base_literals}
    need(base_refs == {
        0xF3A8: [(0xF20A, "ldr16", 6)],
        0x10424: [(0x10340, "ldr16", 7)],
        0x19330: [(0x190AE, "ldr32-positive", 9)],
        0x2F970: [(0x2F612, "ldr32-positive", 9)],
        0x2FB40: [(0x2FA42, "ldr16", 5)],
    }, "base literal references")

    lane4 = base + 0xC0
    lane4_literals = [offset for offset in range(0, len(image) - 3, 4)
                      if u32(image, offset) == lane4]
    need(lane4_literals == [0x5540, 0x2C230], "base+c0 literal inventory")
    lane4_refs = {literal: literal_refs(image, literal) for literal in lane4_literals}
    need(lane4_refs == {
        0x5540: [(0x536C, "ldr16", 1)],
        0x2C230: [(0x2C0EA, "ldr16", 1), (0x2C104, "ldr16", 0),
                  (0x2C10A, "ldr16", 0), (0x2C110, "ldr16", 0)],
    }, "base+c0 literal references")

    companion = 0x58410178
    companion_literals = [offset for offset in range(0, len(image) - 3, 4)
                          if u32(image, offset) == companion]
    need(companion_literals == [0x10428, 0x19334], "companion literal inventory")
    need({literal: literal_refs(image, literal) for literal in companion_literals} == {
        0x10428: [(0x10342, "ldr16", 6)],
        0x19334: [(0x190B2, "ldr16", 0)],
    }, "companion literal references")

    # The 0x200-byte package-record interpretation follows the exact same
    # offsets already used by the independently reviewed EXCO_PAR2_S0 case.
    exco = package[0x83C00:0x83E00]
    need(sha(exco) == "2dfc6d013c0907962adfed3750534b32f70bbcbfe278020f3aef5a6368789d6a" and
         exco[:32] == b"EXCO_PAR2_S0" + bytes(20), "EXCO_PAR2_S0 analogue")
    need(tuple(u32(exco, offset) for offset in (0x20, 0x24, 0x28, 0x2C, 0xAC)) ==
         (7, 0x58601400, 1, 0xC8C00, 0x2600), "EXCO_PAR2_S0 metadata fields")

    pre_pd = package[0x80600:0x80800]
    need(len(pre_pd) == 0x200 and sha(pre_pd) ==
         "11696518d668a8c2ac409a0cf2d7a7e462f2e410bba6e5a0747007618e2ec87f",
         "Pre-PD metadata record")
    need(pre_pd[:32] == b"Pre-PD" + bytes(26), "Pre-PD name")
    metadata_type, metadata_base, metadata_count, metadata_source_offset, metadata_destination_offset, metadata_size = (
        u32(pre_pd, offset) for offset in (0x20, 0x24, 0x28, 0x2C, 0x6C, 0xAC))
    need((metadata_type, metadata_base, metadata_count, metadata_source_offset, metadata_destination_offset, metadata_size) ==
         (7, 0x58410000, 1, 0x8000, 0, 0xAB0), "Pre-PD metadata fields")
    # Bind the independently decoded type-7 dispatch and first-group loader
    # instructions, including the descriptor-copy ABI and array offsets.
    need(sha(image[0x7586:0x75A2]) ==
         "23cca4d662c9ba8d089caf0f856ca64ed3ec25aff315c676e5e128497f0f8302" and
         bl_target(image, 0x759E) == 0x5C74 and
         sha(image[0x5C74:0x5E24]) ==
         "b77188019bd4de2e61579bd81174842a1ac97a468c8a8901839fc3e2f0e23d05",
         "reviewed type-7 dispatch and first-group loader slices")
    package_config_base = 0x80000
    payload_start = package_config_base + metadata_source_offset
    payload_end = payload_start + metadata_size
    need((payload_start, payload_end) == (0x88000, 0x88AB0) and
         sha(package[payload_start:payload_end]) ==
         "af62caa7f38a9a6a3702901ca84aa09a9ae895f1b498cabc846e51469872ddd8",
         "Pre-PD first-group packaged payload")
    destination_start = metadata_base + metadata_destination_offset
    record_end = destination_start + metadata_size
    need(destination_start <= companion and companion + 0x40 <= record_end and
         destination_start <= base and base + 0x100 <= record_end,
         "Pre-PD address containment")
    osd = package[0x80400:0x80600]
    need(sha(osd) == "2251a40cac556450f287b6146dafc548ed1f3a0dfd1d2033f6d21612fd1d1019" and
         osd[:32] == b"OSD" + bytes(29) and
         (u32(osd, 0x24), u32(osd, 0xAC)) == (0x58400000, 0x40) and
         not (u32(osd, 0x24) <= base < u32(osd, 0x24) + u32(osd, 0xAC)),
         "OSD record does not contain source")

    # No MOVW/MOVT half for either exact low half or the shared high half is
    # present. This is a scoped immediate census, not proof against a pointer
    # passed from outside the selected image.
    need(mov_immediate_hits(image, 0x09A4) == [] and
         mov_immediate_hits(image, 0x0A64) == [] and
         mov_immediate_hits(image, 0x5841) == [], "MOVW/MOVT source halves")

    block_base = 0x58400000
    block_literals = [offset for offset in range(0, len(image) - 3, 4)
                      if u32(image, offset) == block_base]
    need(block_literals == [0x713C, 0x1F3D4] and
         {literal: literal_refs(image, literal) for literal in block_literals} == {
             0x713C: [(0x70A2, "ldr16", 1)],
             0x1F3D4: [(0x1F3CA, "ldr16", 1)],
         }, "broader block-base references")
    need(image[0x70A2:0x70A6].hex() == "26490860" and
         image[0x1F3CA:0x1F3CE].hex() == "02490860",
         "broader base stores remain at offset zero")

    bodies = {
        "f1f4": (0xF1F4, 0xF3A8, "ede08927ce58e699ad253a0efd29be471d673259035344a7d83b64d60d4a91e0"),
        "10334": (0x10334, 0x10424, "12d4d300b3402aab6bb23d31744b4bc9a1babb12698075c45fdd399c872c0dc2"),
        "19064": (0x19064, 0x19330, "d6e9d5f5d129583ba1b248b790c947558e6759bd49371ec3ebe7f9832bff842a"),
        "2f5d8": (0x2F5D8, 0x2F970, "428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45"),
        "2fa38": (0x2FA38, 0x2FB40, "0275a3f5b85be051f4b4a48a2759b9cf8005ffdc96e6b7f26e1c5735274cfb56"),
        "5324": (0x5324, 0x5540, "9e327e2f9b173b27de252859cde1372d964228015a990eef0ca729f28ae3f45a"),
        "2c080": (0x2C080, 0x2C230, "406c855cd3da3fc5e5b6aff6b8e25b4b76e512406bf5d330919cb44548e6d56f"),
    }
    for name, (start, end, digest) in bodies.items():
        need(sha(image[start:end]) == digest, "body " + name)
        need(direct_printable_refs(package, image, start, end) == [],
             "no direct printable reference in " + name)

    # Exact source-register access instructions in the five base consumers.
    # Every classified instruction is an LDR. No STR through the register
    # loaded by the base literal occurs in these complete pinned bodies.
    read_sites = {
        0xF238: "56f82200", 0x1037C: "57f82110", 0x10392: "57f82220",
        0x190E2: "59f82100", 0x1912A: "59f82100",
        0x2F662: "59f82500", 0x2F7A6: "59f82500",
        0x2FA44: "e86b", 0x2FA48: "e86f", 0x2FA4E: "4059",
    }
    for address, expected in read_sites.items():
        need(image[address:address + len(expected) // 2].hex() == expected,
             f"source read {address:#x}")

    # Both explicit 64-byte copies place source in r1, destination in r0,
    # length in r2, and call the selected image's load/store copy routine.
    need(image[0x536A:0x5374].hex() == "402274497548fbf7c4fb" and
         bl_target(image, 0x5370) == 0xAFC and u32(image, 0x5544) == 0x2000B4E0,
         "lane-four copy to RAM")
    need(image[0x2C0E8:0x2C0F2].hex() == "4022514903a8d4f705fd" and
         bl_target(image, 0x2C0EE) == 0xAFC, "lane-four copy to stack")
    need(sha(image[0xAFC:0xB60]) ==
         "dcedcf9312a0399a79b51da6a240a74c79a4ccfd6f2a6c429f279769db6229ba",
         "copy routine")

    # Positive named provenance is limited to RAM records consumed alongside
    # the fixed source. These names do not name the source register block.
    registry = package[0x3CCBC:0x3CF08]
    need(sha(registry) == "669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287",
         "ordinary registry")
    rows = [struct.unpack_from("<7I", registry, index * 28) for index in range(21)]
    named = {
        "NPC_AP": (2, 0x3DE84, 0x2000D71C, 0x540),
        "AP_SPC": (5, 0x3DE3C, 0x2000F7C2, 0x124),
        "AP_EXCO": (10, 0x3DD8C, 0x2000FF14, 0x33A),
        "AP_AG": (13, 0x3DE64, 0x2000DC5C, 0x282),
    }
    for name, (index, name_va, base_address, extent) in named.items():
        need(rows[index][:3] == (name_va, base_address, extent), "registry " + name)
        need(cstring(package, name_va) == name, "registry name " + name)
    need(rows[14][:3] == (0x3DE8C, 0x47012400, 0x100) and
         cstring(package, 0x3DE8C) == "AP_RTP", "separate AP_RTP registry fact")

    getters = {
        0xE660: 0x2000DC5C, 0xE678: 0x2000FF14,
        0xEF94: 0x47010000, 0xEF9C: 0x2000D71C, 0xF4F0: 0x2000F7C2,
    }
    for address, value in getters.items():
        need(image[address:address + 4].hex() == "00487047" and
             u32(image, address + 4) == value, f"getter {address:#x}")

    output = {
        "schema": "ap-fixed-table-source-trace-v1", "target_operations": 0,
        "source_base": hex(base),
        "base_literal_vas": [hex(value) for value in base_literals],
        "base_literal_load_vas": [hex(items[0][0]) for items in base_refs.values()],
        "used_layout": {"dword_lanes": 4, "dwords_per_lane": 16,
                        "lane_stride": 0x40, "observed_span_bytes": 0x100,
                        "highest_observed_byte_offset": 0xFF},
        "explicit_outward_copies": [
            {"va": "0x536a", "source": "0x58410a64",
             "destination_selected_package_cpu_literal": "0x2000b4e0", "bytes": 64,
             "destination_live_alias_or_allocation_proved": False},
            {"va": "0x2c0e8", "source": "0x58410a64", "destination": "stack",
             "bytes": 64},
        ],
        "direct_base_consumers_all_read_only": True,
        "direct_writer_found": False,
        "named_enclosing_package_record": "Pre-PD",
        "named_enclosing_package_record_file_offset": "0x80600",
        "named_enclosing_package_record_type": metadata_type,
        "named_enclosing_package_record_count": metadata_count,
        "named_enclosing_package_record_address_range": [hex(metadata_base), hex(record_end)],
        "named_enclosing_package_record_source_file_range": [hex(payload_start), hex(payload_end)],
        "individual_source_or_table_name_identified": False,
        "runtime_producer_identified": False,
        "record_loaded_for_observed_boot_proved": False,
        "field_units_identified": False,
        "named_consumer_records": sorted(named),
        "unnamed_context_root_literal": "0x47010000",
        "paired_unnamed_source": hex(companion),
        "broader_0x58400000_refs_only_store_offset_zero": True,
        "pointer_passed_from_unscanned_external_code_excluded": False,
        "physical_units_inferred": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
