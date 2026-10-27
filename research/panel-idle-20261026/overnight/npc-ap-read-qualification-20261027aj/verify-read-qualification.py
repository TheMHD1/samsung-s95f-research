#!/usr/bin/env python3
"""Offline qualification checks for a bounded NPC_AP low-field read."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
BACKUP = OVERNIGHT / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
W = OVERNIGHT / "ap-exco-input-snapshot-20261027w"

PACKAGE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
BACKUP_SHA256 = "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"
W_PROGRAM_SHA256 = "ef5dd6f33a9daece5fbcaca8decf1328128a0b648268d21a1dc97d28da9136b9"
W_MANIFEST_SHA256 = "5d760fbdabf7b23b6e57f13fc40914a8ede43bf1b488738dc7c42f203321ca69"
W_RESULT_SHA256 = "83cd349d84ef397074f36c5b80e2cc72ad8b00bbeebae5dae978a21f11935171"


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


def cstring(package: bytes, file_offset: int) -> str:
    end = package.index(0, file_offset, file_offset + 64)
    return package[file_offset:end].decode("ascii")


def image1(package: bytes, va: int, size: int) -> bytes:
    return package[0x40200 + va:0x40200 + va + size]


def thumb_bl_target(package: bytes, va: int) -> int:
    first, second = struct.unpack_from("<HH", package, 0x40200 + va)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"BL encoding at {va:#x}")
    sign = (first >> 10) & 1
    j1, j2 = (second >> 13) & 1, (second >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ sign), 1 ^ (j2 ^ sign)
    value = ((sign << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return va + 4 + value


def thumb_adr_target(package: bytes, va: int) -> int:
    instruction = u16(package, 0x40200 + va)
    need(instruction & 0xF800 == 0xA000, f"ADR encoding at {va:#x}")
    return ((va + 4) & ~3) + (instruction & 0xFF) * 4


def thumb_ldr_literal(package: bytes, va: int) -> int:
    instruction = u16(package, 0x40200 + va)
    need(instruction & 0xF800 == 0x4800, f"LDR literal encoding at {va:#x}")
    literal_va = ((va + 4) & ~3) + (instruction & 0xFF) * 4
    return u32(package, 0x40200 + literal_va)


def mapped(selector: int, address: int) -> int:
    """Exact relevant branches of image-1 mapper VA 0x1bb74."""
    if address == 0:
        return 0
    if selector == 0:
        if address < 0x40000:
            return address + 0x44000000
        if 0x20000000 <= address < 0x20020000:
            return address + 0x25000000
        return 0
    if address < 0x20000:
        return address + 0x46000000
    if 0x20000000 <= address < 0x20020000:
        return address + 0x27000000
    return 0


def read_header(address: int, length: int) -> bytes:
    need(address & 3 == 0, "four-byte-aligned start")
    need(length > 0 and length & 3 == 0, "positive four-byte length")
    return struct.pack("<III", 0x101, address, length)


def main() -> None:
    package = load(PACKAGE, PACKAGE_SHA256)
    backup = load(BACKUP, BACKUP_SHA256)
    need(len(package) == len(backup) == 0x500000, "firmware extent")

    # Positive named allocation and fixed-root identity in selected image 0.
    registry = package[0x3CCBC:0x3CF08]
    need(sha256(registry) ==
         "669adda911a2e5bf5b053ab486f11c2611e115b284eeaec79c58e5876fbad287",
         "ordinary registry pin")
    rows = [struct.unpack_from("<7I", registry, index * 28) for index in range(21)]
    npc = rows[2]
    need(npc[:3] == (0x3DE84, 0x2000D71C, 0x540), "NPC_AP registry row")
    need(cstring(package, 0x200 + npc[0]) == "NPC_AP", "NPC_AP registry name")
    image0 = package[0x200:0x40200]
    getter = image0[0xEF9C:0xEFA4]
    need(getter.hex() == "004870471cd70020" and sha256(getter) ==
         "84f93c6639be7fc7a21229eead9d80b31746059a46741f4973167e2b14ff0b47",
         "fixed NPC_AP getter")
    word = struct.pack("<I", npc[1])
    need([offset for offset in range(len(image0) - 3)
          if image0[offset:offset + 4] == word] == [0xEFA0, 0x3CAF8],
         "bounded exact base-word census")

    # Stored source provenance is an initializer, never a live-value gate.
    directory = package[0x84E00:0x85000]
    allocation_slice = package[0x172600:0x172B40]
    payload = package[0x172600:0x172B3E]
    need(directory == backup[0x84E00:0x85000] and sha256(directory) ==
         "04a151171ff9a3774578ff4ad328f2a0016f2ab4c60c9afa7dd30501c307b414",
         "NPC_AP directory selected/backup")
    need(directory[:32] == b"NPC_AP" + bytes(26) and
         u32(directory, 0x2C) == 0xF2600, "NPC_AP directory coordinate")
    need(u32(directory, 0x20) == 4 and u32(directory, 0x24) == 0x140000 and
         u32(directory, 0x6C) == 0 and u32(directory, 0xAC) == 0x53E,
         "type4 metadata logical base, destination and copy length")
    need(allocation_slice == backup[0x172600:0x172B40] and sha256(allocation_slice) ==
         "37bb4edfb3d24fc8fe0887f59815cbfb10e3ecf87bfbdf40e481b0852de56518",
         "NPC_AP allocation-sized stored slice")
    need(payload == backup[0x172600:0x172B3E] and sha256(payload) ==
         "3e9f4747fa26eeca6818944a6dae2fbba54f6ccc79d1ed6a4dc05434b5ad21b7",
         "NPC_AP metadata-declared stored payload")
    need([u16(payload, offset) for offset in (0x16, 0x18, 0x1A)] ==
         [1024, 1024, 1024], "stored low-field defaults")

    # Positive mapper instruction body and complete RAM-domain boundaries.
    mapper = image1(package, 0x1BB74, 0x50)
    need(sha256(mapper) ==
         "94da5bec3c7fd05448a66d3828ec420e5cb08e03cb4474a54d07570732d1fe5c",
         "image-1 mapper body")
    need(mapper.hex() ==
         "024609b90020704772b9b1f5802f02d201f18840f7e7b1f1005f14d30b48814211d201f11450eee7b1f5003f02d201f18c40e8e7b1f1005f05d30448814202d201f11c50dfe70020dde7000000000220",
         "exact mapper instructions")
    need(mapped(0, 0x20000000) == 0x45000000 and
         mapped(0, 0x2001FFFF) == 0x4501FFFF and
         mapped(0, 0x20020000) == 0, "selector-zero RAM boundary fixtures")

    cpu_base, extent = npc[1], npc[2]
    cpu_end = cpu_base + extent
    need(cpu_base >= 0x20000000 and cpu_end <= 0x20020000,
         "complete NPC_AP allocation inside mapper domain")
    bus_base = mapped(0, cpu_base)
    need(bus_base == 0x4500D71C and
         mapped(0, cpu_end - 1) == 0x4500DC5B,
         "complete NPC_AP selector-zero mapped extent")

    # The complete known startup pointer initializer has no NPC_AP entry.
    # This is a finite seven-slot result, not a global absence statement.
    calls = [0x1BCCA, 0x1BCD6, 0x1BCE2, 0x1BCEE, 0x1BCFA, 0x1BD06, 0x1BD12]
    expected = [
        ("AP_EXCO", 0x1BBFC, 0x200002C4),
        ("AP_EXCO", 0x1BBD4, 0x200002C8),
        ("AP_EXCO", 0x1BC24, 0x200002CC),
        ("AP_TED",  0x1BBFC, 0x200002D0),
        ("AP_TED",  0x1BBD4, 0x200002D4),
        ("AP",      0x1BBFC, 0x200002D8),
        ("MULTI",   0x1BC24, 0x200002BC),
    ]
    decoded = []
    for call, wanted in zip(calls, expected):
        name_va = thumb_adr_target(package, call - 4)
        got = (cstring(package, 0x40200 + name_va),
               thumb_bl_target(package, call),
               thumb_ldr_literal(package, call + 4))
        need(u16(package, 0x40200 + call + 6) == 0x6008, "startup pointer store")
        need(got == wanted, f"startup triplet at {call:#x}")
        decoded.append(got)
    need(sha256(image1(package, 0x1BCC4, 0x84)) ==
         "344accecffd7cff7fb1e7e56ec85778bfa99a9b12646223f34a84e43fb49288b",
         "startup initializer body")
    need(all(name != "NPC_AP" for name, _, _ in decoded),
         "NPC_AP unexpectedly has known startup slot")

    # Prior accepted W capture proves the fixed target-0x101 transport and
    # gives same-domain selector-zero examples; it did not sample NPC_AP.
    program = load(W / "source-checkpoint/Program.cs", W_PROGRAM_SHA256)
    load(W / "source-checkpoint/build-manifest.json", W_MANIFEST_SHA256)
    for header_hex in ("0101000014FF004538030000", "01010000A8580145EC030000"):
        need(header_hex.encode("ascii") in program, f"W fixed header {header_hex}")
    w_result_raw = load(W / "capture-once/result.json", W_RESULT_SHA256)
    w_result = json.loads(w_result_raw)
    need(w_result["transport_accepted"] is True and
         w_result["interpretation_accepted"] is True and
         w_result["cleanup"] == "STAGE_ABSENT" and
         w_result["bus_contents_altered"] is False,
         "W accepted read-only capture")
    pointer = (W / "capture-once/pointer-window.bin").read_bytes()
    need(len(pointer) == 32 and sha256(pointer) ==
         "7634f63e1eace3b6da5f287655f1b1ef3ebdb81b22909605a467c2472af43cd3",
         "W pointer window")
    pointer_words = struct.unpack("<8I", pointer)
    need(pointer_words == (0x1, 0x4500FF14, 0x4501024E, 0x450158A8,
                           0x450130B6, 0x450130F0, 0x4500F0E0, 0x1B691),
         "W mapped pointers")
    need(bus_base not in pointer_words, "unexpected NPC_AP known-slot pointer")

    # Minimal aligned envelope covers object +0x14..+0x1b. The requested
    # halfwords are response offsets +2,+4,+6. The larger base envelope is a
    # diagnostic alternative, not a live-identity fingerprint.
    minimal_address, minimal_length = bus_base + 0x14, 8
    minimal_header = read_header(minimal_address, minimal_length)
    need(minimal_address == 0x4500D730 and
         minimal_header.hex() == "0101000030d7004508000000",
         "minimal fixed read geometry")
    need(cpu_base + 0x16 >= cpu_base and cpu_base + 0x1B < cpu_end,
         "requested fields inside allocation")
    need(minimal_address <= bus_base + 0x16 and
         bus_base + 0x1B < minimal_address + minimal_length,
         "minimal envelope coverage")
    diagnostic_header = read_header(bus_base, 32)
    need(diagnostic_header.hex() == "010100001cd7004520000000",
         "optional prefix geometry")
    need(payload[0x14:0x1C].hex() == "6400000400040004" and
         sha256(payload[0x14:0x1C]) ==
         "20cae6279c2a3816896854fb7e76f6d8366bd14520d6c0fd81764369fc2ff2c0",
         "stored minimal-envelope bytes")

    # Pure boundary/negative fixtures protect the proposed arithmetic.
    for bad_address, bad_length in ((minimal_address + 2, 8),
                                    (minimal_address, 6),
                                    (minimal_address, 0)):
        try:
            read_header(bad_address, bad_length)
        except ValueError:
            pass
        else:
            raise ValueError("unaligned/empty header fixture accepted")
    need(mapped(0, cpu_base - 1) == bus_base - 1 and
         mapped(1, cpu_base) == 0x4700D71C,
         "selector distinction fixtures")

    output = {
        "schema": "npc-ap-read-qualification-v1",
        "offline_only": True,
        "target_operations": 0,
        "status": "fixed-read-transport-qualified-live-object-binding-conditional",
        "npc_ap": {
            "cpu_base": "0x2000d71c",
            "extent": "0x540",
            "cpu_inclusive_end": "0x2000dc5b",
            "selector_zero_bus_base": "0x4500d71c",
            "selector_zero_bus_inclusive_end": "0x4500dc5b",
            "requested_offsets": ["0x16", "0x18", "0x1a"],
        },
        "minimal_fixed_read": {
            "address": "0x4500d730",
            "length": 8,
            "header_hex": minimal_header.hex(),
            "requested_response_offsets": [2, 4, 6],
            "extra_object_offset": "0x14",
        },
        "optional_diagnostic_prefix": {
            "address": "0x4500d71c", "length": 32,
            "header_hex": diagnostic_header.hex(),
            "static_bytes_are_not_live_identity_gate": True,
        },
        "known_startup_pointer_slots": [hex(slot) for _, _, slot in decoded],
        "npc_ap_known_startup_slot": None,
        "prior_same_domain_transport_accepted": True,
        "new_register_or_mmio_primitive_required": False,
        "live_npc_ap_pointer_anchor_proved": False,
        "unconditional_live_object_identity_proved": False,
        "stored_defaults_are_live_values": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
