#!/usr/bin/env python3
"""Reproduce the bounded image-0 Pre-PD header/control-source findings."""

from pathlib import Path
import argparse
import hashlib
import json
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"

PRE_PD_BASE = 0x58410000
COMPANION = 0x58410178
TABLE = 0x584109A4


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_pinned(path, digest):
    data = path.read_bytes()
    need(sha(data) == digest, f"SHA-256 mismatch: {path}")
    return data


def u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def words_in_range(data, start, end):
    """Return every byte-positioned little-endian word in [start,end)."""
    return [(offset, u32(data, offset)) for offset in range(len(data) - 3)
            if start <= u32(data, offset) < end]


def thumb_immediate(first, second):
    value = ((first & 0xF) << 12) | (((first >> 10) & 1) << 11)
    value |= ((second >> 12) & 7) << 8 | (second & 0xFF)
    return value


def movt_hits(image, immediate):
    found = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xFBF0 == 0xF2C0 and thumb_immediate(first, second) == immediate:
            found.append((address, (second >> 8) & 15))
    return found


def literal_refs(image, literal):
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


def analyze(package):
    need(len(package) == 0x500000, "selected package extent")
    image = package[0x200:0x40200]

    # This is intentionally the header/control-prefix question, not another
    # census of the already reviewed fixed table address and its consumers.
    image_header_words = words_in_range(image, PRE_PD_BASE, COMPANION)
    package_header_words = words_in_range(package, PRE_PD_BASE, COMPANION)
    need(image_header_words == [], "unexpected image-0 Pre-PD header word")
    need(package_header_words == [(0x80624, PRE_PD_BASE)],
         "whole-package Pre-PD header-word inventory")
    need(movt_hits(image, 0x5841) == [],
         "unexpected image-0 MOVT construction of Pre-PD high half")

    record = package[0x80600:0x80800]
    need(sha(record) ==
         "11696518d668a8c2ac409a0cf2d7a7e462f2e410bba6e5a0747007618e2ec87f",
         "Pre-PD metadata record")
    need(record[:32] == b"Pre-PD" + bytes(26), "Pre-PD record name")
    fields = tuple(u32(record, offset) for offset in
                   (0x20, 0x24, 0x28, 0x2C, 0x6C, 0xAC))
    need(fields == (7, PRE_PD_BASE, 1, 0x8000, 0, 0xAB0),
         "Pre-PD first-group metadata")

    payload = package[0x88000:0x88AB0]
    need(sha(payload) ==
         "af62caa7f38a9a6a3702901ca84aa09a9ae895f1b498cabc846e51469872ddd8",
         "Pre-PD stored payload")
    need(PRE_PD_BASE <= COMPANION and COMPANION + 0x40 <= PRE_PD_BASE + 0xAB0,
         "companion containment")
    need(PRE_PD_BASE <= TABLE and TABLE + 0x100 <= PRE_PD_BASE + 0xAB0,
         "table containment")

    # Bind the previously reviewed generic type-7 dispatch and first-group
    # loader. This is the only positive producer edge claimed here.
    need(sha(image[0x7586:0x75A2]) ==
         "23cca4d662c9ba8d089caf0f856ca64ed3ec25aff315c676e5e128497f0f8302",
         "type-7 dispatch slice")
    need(sha(image[0x5C74:0x5E24]) ==
         "b77188019bd4de2e61579bd81174842a1ac97a468c8a8901839fc3e2f0e23d05",
         "type-7 first-group loader slice")

    companion_literals = [offset for offset in range(0, len(image) - 3, 4)
                          if u32(image, offset) == COMPANION]
    need(companion_literals == [0x10428, 0x19334],
         "companion literal inventory")
    need({literal: literal_refs(image, literal) for literal in companion_literals} == {
        0x10428: [(0x10342, "ldr16", 6)],
        0x19334: [(0x190B2, "ldr16", 0)],
    }, "companion literal references")

    # Both complete known companion consumers use only indices 0..15. These
    # byte pins cover the load/index loops; they do not establish a global
    # absence of computed or caller-supplied pointers.
    need(sha(image[0x10334:0x10424]) ==
         "12d4d300b3402aab6bb23d31744b4bc9a1babb12698075c45fdd399c872c0dc2",
         "first companion consumer")
    need(sha(image[0x19064:0x19330]) ==
         "d6e9d5f5d129583ba1b248b790c947558e6759bd49371ec3ebe7f9832bff842a",
         "second companion consumer")
    need(image[0x103C8:0x103CE].hex() == "411e56f82110" and
         image[0x103F2:0x103FA].hex() == "0f2804d156f82010",
         "first consumer forward companion loads")
    need(image[0x19100:0x19106].hex() == "049951f82520",
         "second consumer forward companion load")

    broader = [offset for offset in range(0, len(image) - 3, 4)
               if u32(image, offset) == 0x58400000]
    need(broader == [0x713C, 0x1F3D4], "broader base literal inventory")
    need({literal: literal_refs(image, literal) for literal in broader} == {
        0x713C: [(0x70A2, "ldr16", 1)],
        0x1F3D4: [(0x1F3CA, "ldr16", 1)],
    }, "broader base references")
    need(image[0x70A2:0x70A6].hex() == "26490860" and
         image[0x1F3CA:0x1F3CE].hex() == "02490860",
         "broader base sites store at offset zero")

    return {
        "schema": "prepd-control-consumers-offline-v1",
        "selected_package_sha256": sha(package),
        "image0_header_prefix_embedded_words": image_header_words,
        "whole_package_header_prefix_embedded_words": [
            {"file_offset": offset, "value": value}
            for offset, value in package_header_words
        ],
        "image0_movt_5841_hits": movt_hits(image, 0x5841),
        "positive_producer_edge": {
            "kind": "generic_type7_package_copy",
            "source_file_range": [0x88000, 0x88AB0],
            "destination_cpu_range": [PRE_PD_BASE, PRE_PD_BASE + 0xAB0],
            "runtime_refresh_producer_identified": False,
        },
        "known_companion_consumers_access": "forward indices 0..15 only",
        "header_control_semantics_identified": False,
        "table_runtime_producer_identified": False,
        "scope": "selected image-0 embedded words, MOVT high-half, reviewed loader, and two fixed companion consumers",
    }


def self_test(package):
    checks = 0
    analyze(package)
    checks += 1

    changed = bytearray(package)
    struct.pack_into("<I", changed, 0x80624, PRE_PD_BASE + 4)
    try:
        analyze(bytes(changed))
        raise ValueError("metadata mutation accepted")
    except ValueError as error:
        need("whole-package Pre-PD header-word inventory" in str(error) or
             "Pre-PD metadata record" in str(error), "metadata mutation result")
    checks += 1

    changed = bytearray(package)
    struct.pack_into("<I", changed, 0x202 + 0x200, PRE_PD_BASE + 0x40)
    try:
        analyze(bytes(changed))
        raise ValueError("inserted header pointer accepted")
    except ValueError as error:
        need("unexpected image-0 Pre-PD header word" in str(error),
             "inserted pointer mutation result")
    checks += 1

    changed = bytearray(package)
    changed[0x200 + 0x103CA] ^= 1
    try:
        analyze(bytes(changed))
        raise ValueError("companion-load mutation accepted")
    except ValueError as error:
        need("first companion consumer" in str(error) or
             "first consumer forward companion loads" in str(error),
             "companion mutation result")
    checks += 1
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    package = load_pinned(
        PACKAGE,
        "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    load_pinned(OVERNIGHT / "ap-table-source-20261027y/table-source-trace.md",
                "52774f5a67d1f927a05c71dd7788da2b4601091472ac9e3230b53692c89aacdb")
    load_pinned(OVERNIGHT / "pre-pd-stored-values-20261027ab/stored-values.md",
                "31312fd987633bba78f4d9edc87c149d766181a50a5c99c01ba6be1632c7ac3f")
    load_pinned(OVERNIGHT / "pre-pd-cross-image-20261027ad/cross-image-census.md",
                "99683145f700ca639ae432ba7d1bfa7ffb8996373dfc76ef06182f14a0f5926b")
    load_pinned(OVERNIGHT / "ordinary-invocation-20261027aa/invocation-findings.md",
                "417d84630ea8a67c8078945174226c0775b5def9340d283bd51d2eb5da7de8f9")

    result = analyze(package)
    if args.self_test:
        result["self_test_checks"] = self_test(package)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
