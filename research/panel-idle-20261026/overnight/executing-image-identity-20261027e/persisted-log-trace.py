#!/usr/bin/env python3
"""Offline verifier/parser for the packaged controller persisted-log path.

This script reads only retained local files.  It has no transport, device,
network, root, or write operation.  Run with PYTHONPATH=/tmp/tcon-capstone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_MCLASS, CS_MODE_THUMB, Cs
from capstone.arm import ARM_OP_IMM


ROOT = Path("${S95F_EVIDENCE_ROOT}/panel-idle-20261026/overnight")
PACKAGE = ROOT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
STORED = ROOT / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
CAPTURE = ROOT / "executing-image-identity-20261027e/main-event-log-read-once/returned-block.bin"

EXPECTED = {
    PACKAGE: (0x500000, "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"),
    STORED: (0x500000, "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"),
    CAPTURE: (0xC00, "6d82903d4abeb366af859c8966345514a50315a14a891ee1370f69fe173b912a"),
}

RANGES = {
    "dual_header_reader": (0x056F0, 0x0574C, "63bc2ff8a1cf3c9d97603bd095ef3431321ff13cad3ea005b75a60086e32e62f"),
    "record_builder": (0x0762C, 0x07C80, "e574f25b0eddf06d4914513501e3c24a9ca2a9d536d054769af6a894870975fd"),
    "header_builder": (0x07C80, 0x07CF0, "bbda99a683ed41a57d1dd29f4b7f5f9e2071d597c206a70332f0418545be623d"),
    "header_selector": (0x20454, 0x204E0, "7968a5380bba1f28991cf66d179cfd4b9cf85225235bccdee2ee88adb4d71308"),
    "persist_service": (0x20510, 0x20624, "a5fb6873b5364319728b7e46150d2974ce617d9c3518ed2b663b839f20c593dd"),
    "emmc_read_wrapper": (0x09BD4, 0x09CB8, "7eb2e0e5029fb8ac2c64fe88c207c7922dafbfcc651928dcae21b1a2cef2343b"),
    "emmc_write_wrapper": (0x09EE4, 0x09FC6, "67ede89b8a2d30fb6043b353d85fb8a493fd9d384e3a138bd37f125a6e659023"),
    "storage_command_programmer": (0x16924, 0x16960, "282ab21323a50a4492d17f76f603baa3ca045e658c05e06687ce57ac9818b597"),
    "storage_controller_leaf": (0x16B70, 0x16CD4, "c8d764cfde98205a0c82fcc5d89cb5afde088a301063ee14fed33273f2bd5826"),
    "checksummed_read": (0x1D9CC, 0x1DA50, "0ffb9f0ee71d483136215caa01ae621f021caeb0b061c1ad8a2e7b15ff950020"),
    "usb_target_validator": (0x29258, 0x293B4, "febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234"),
    "emergency_loop": (0x0B6DC, 0x0B6FA, "9bfe11209ff36e04e88964a663f7bf3b6f3b7c31140827730562687e2f5b6f36"),
    "ordinary_loop": (0x39BDA, 0x39C4E, "e2d3cc629921b0cdccdd3151a4b545dbb594c5b214ff87faf9e7c81c03bd8936"),
}

FORMATS = {
    0x20630: b"LOG Buffer Copy: %d(%d)\n\x00",
    0x20658: b"LOG eMMMC Data Write: %d ~ %d(%d)\n\x00",
    0x20680: b"LOG eMMMC Hedaer Write: %d(%d)\n\x00",
    0x32CF0: b"mod_match: %s[%s],r%d,f%d,b%d\n\x00",
    0x3559C: b"framework_ch:%d, p_sen_ch:%d\n\x00",
    0x36848: b"fe_p_sen_ch:%d\n\x00",
    0x3AB58: b"deadPool:%d\n\x00",
}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def verify_inputs() -> dict[Path, bytes]:
    out: dict[Path, bytes] = {}
    for path, (size, digest) in EXPECTED.items():
        need(path.is_file(), f"missing input: {path}")
        data = path.read_bytes()
        need(len(data) == size, f"size mismatch for {path}: {len(data):#x}")
        need(sha256(data) == digest, f"SHA-256 mismatch for {path}")
        out[path] = data
    return out


def insn_at(md: Cs, image: bytes, va: int):
    # Image 0 mapping is FILE = VA + 0x200.
    decoded = list(md.disasm(image[va + 0x200 : va + 0x208], va, count=1))
    need(len(decoded) == 1, f"cannot decode instruction at VA {va:#x}")
    return decoded[0]


def verify_static(package: bytes, stored: bytes) -> dict:
    need(len(package) == 0x500000, "package is not the pinned 5 MiB image")
    for name, (start, end, digest) in RANGES.items():
        got = package[start + 0x200 : end + 0x200]
        need(len(got) == end - start, f"short mapped range for {name}")
        need(sha256(got) == digest, f"range hash mismatch for {name}")

    for va, value in FORMATS.items():
        got = package[va + 0x200 : va + 0x200 + len(value)]
        need(got == value, f"format mismatch at VA {va:#x}")

    # Exact direct calls that prove the same service occurs in both schedules.
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    md.detail = True
    expected_calls = {
        0x0B6F0: 0x20510,
        0x39C08: 0x20510,
        0x09CA2: 0x16B70,
        0x09FB2: 0x16B70,
        0x16BF6: 0x16924,
        0x205C0: 0x09EE4,
        0x20602: 0x09EE4,
    }
    calls = {}
    for site, target in expected_calls.items():
        insn = insn_at(md, package, site)
        need(insn.mnemonic == "bl", f"expected BL at {site:#x}, got {insn.mnemonic}")
        need(len(insn.operands) == 1 and insn.operands[0].type == ARM_OP_IMM,
             f"expected immediate BL at {site:#x}")
        need(insn.operands[0].imm == target,
             f"call target mismatch at {site:#x}: {insn.operands[0].imm:#x}")
        calls[f"{site:#x}"] = f"{target:#x}"

    exact_insns = {
        # Target-203's 0xabcd fifth-argument sentinel bypasses buffer mapping;
        # it is not a storage address or partition selector.
        0x09BF6: ("movw", "r0, #0xabcd"),
        0x09BFE: ("movs", "r6, #0"),
        0x09C90: ("lsr.w", "sl, r5, #9"),
        0x09C96: ("movs", "r2, #1"),
        0x09FA0: ("lsr.w", "sl, r5, #9"),
        0x09FA6: ("movs", "r2, #2"),
        0x1692E: ("str", "r7, [r4, #0x28]"),
        0x16BF0: ("mov", "r2, sl"),
        # Both persistence calls overwrite r0 immediately after the BL;
        # neither tests the write wrapper's returned status.
        0x205C4: ("ldr", "r0, [pc, #0x64]"),
        0x20606: ("ldr", "r0, [pc, #0x74]"),
        # Family-2 transport gate: address must be below 16 MiB.
        0x2938A: ("cmp.w", "r0, #0x1000000"),
        0x293A0: ("cmp.w", "r0, #0x1000000"),
    }
    for site, (mnemonic, operands) in exact_insns.items():
        insn = insn_at(md, package, site)
        need((insn.mnemonic, insn.op_str) == (mnemonic, operands),
             f"instruction mismatch at {site:#x}: {insn.mnemonic} {insn.op_str}")

    # Wrapper fixed DMA buffer and the storage leaf's small/large READ command
    # words. These constants are data, not Thumb instructions.
    need(u32(package, 0x09CB8 + 0x200) == 0x20270000,
         "read-wrapper fixed DMA literal mismatch")
    need(u32(package, 0x16CBC + 0x200) == 0x02000010,
         "single-sector READ command literal mismatch")
    need(u32(package, 0x16CC0 + 0x200) == 0xA0002351,
         "multi-sector READ command literal mismatch")

    # Positive identity discriminator: all three typo-preserving persistence
    # formats are in the package and absent byte-for-byte from stored image 0.
    persistence_values = [FORMATS[x] for x in (0x20630, 0x20658, 0x20680)]
    for value in persistence_values:
        need(stored.find(value[:-1]) == -1,
             "stored image unexpectedly contains a package persistence format")

    return {
        "range_sha256": {k: v[2] for k, v in RANGES.items()},
        "decisive_calls": calls,
        "write_status_checked_by_persist_service": False,
        "target203_high_bank_valid": False,
    }


def parse_capture(data: bytes) -> dict:
    text = data.decode("ascii", "replace")
    copy_re = re.compile(r"LOG Buffer Copy: (\d+)\((\d+)\)")
    data_re = re.compile(r"LOG eMMMC Data Write: (\d+) ~ (\d+)\((\d+)\)")
    head_re = re.compile(r"LOG eMMMC Hedaer Write: (\d+)\((\d+)\)")
    copies = [(int(a), int(b)) for a, b in copy_re.findall(text)]
    writes = [(int(a), int(b), int(c)) for a, b, c in data_re.findall(text)]
    headers = [(int(a), int(b)) for a, b in head_re.findall(text)]
    need(len(copies) >= 30, f"unexpectedly few complete Copy rows: {len(copies)}")
    need(set(range(197151, 197183)).issubset({x for x, _ in copies}),
         "capture does not contain the complete 197151..197182 sequence")
    need(set(writes) == {(197146, 197155, 10), (197156, 197165, 10), (197166, 197175, 10)},
         f"unexpected data-write tuples: {writes}")
    need(set(headers) == {(1, 41), (0, 42), (1, 43)},
         f"unexpected header tuples: {headers}")
    for selector, counter in headers:
        need(selector == (counter & 1), f"header selector/counter parity mismatch: {(selector, counter)}")
    return {
        "complete_copy_range": [197151, 197182],
        "data_writes": sorted(writes),
        "header_writes": sorted(headers, key=lambda x: x[1]),
        "latest_text_evidenced_attempted_batch_end": 197175,
        "copy_rows_after_that_attempt": 7,
        "durability_proved_by_text": False,
    }


def parse_header_sector(data: bytes, label: str) -> dict:
    need(len(data) == 0x200, f"{label}: header sector must be exactly 0x200 bytes")
    words = struct.unpack("<128I", data)
    terminator = data.find(b"\x00", 4, 8)
    version = data[4 : terminator if terminator >= 0 else 8]
    return {
        "label": label,
        "checksum_word": words[0],
        "sum_u32_mod_2_32": sum(words) & 0xFFFFFFFF,
        "checksum_valid": (sum(words) & 0xFFFFFFFF) == 0xFFFFFFFF,
        "version_bytes_hex": version.hex(),
        "version_terminated_before_record_count": terminator >= 0,
        "record_count": u32(data, 0x08),
        "layout_magic": u32(data, 0x0C),
        "session_count": u32(data, 0x10),
        "reserved_14": u32(data, 0x14),
        "header_attempt_tick_low": u32(data, 0x18),
        "header_attempt_tick_high": u32(data, 0x1C),
    }


def parse_header_file(path: Path) -> list[dict]:
    need(path.is_file(), f"header input does not exist: {path}")
    data = path.read_bytes()
    need(len(data) in (0x200, 0x400),
         f"header input must be one sector (0x200) or both sectors (0x400), got {len(data):#x}")
    return [parse_header_sector(data[i:i + 0x200], f"sector_{i // 0x200}")
            for i in range(0, len(data), 0x200)]


def parse_metadata(data: bytes, label: str) -> dict:
    need(len(data) == 0x2C, f"{label}: metadata must be exactly 0x2c bytes")
    return {
        "label": label,
        "sha256": sha256(data),
        "last_record_service_tick": u32(data, 0x00),
        "first_record_session_latch": data[0x04],
        "total_record_number": u32(data, 0x08),
        "record_number_after_last_header_attempt": u32(data, 0x0C),
        "session_count": u32(data, 0x10),
        "startup_header_tick_low": u32(data, 0x14),
        "header_attempt_counter": u32(data, 0x18),
        "header_selector": u32(data, 0x18) & 1,
        "runtime_identifier_pointer": u32(data, 0x1C),
        "telemetry_subindex": struct.unpack_from("<H", data, 0x20)[0],
        "staged_record_count": u32(data, 0x24),
        "flush_threshold": u32(data, 0x28),
        "raw_hex": data.hex(),
    }


def parse_ram_snapshot(before_path: Path, staging_path: Path,
                       after_path: Path) -> dict:
    for path in (before_path, staging_path, after_path):
        need(path.is_file(), f"RAM snapshot input does not exist: {path}")
    before_raw = before_path.read_bytes()
    staging = staging_path.read_bytes()
    after_raw = after_path.read_bytes()
    before = parse_metadata(before_raw, "metadata_before")
    after = parse_metadata(after_raw, "metadata_after")
    need(len(staging) == 0x1400,
         f"staging buffer must be exactly 0x1400 bytes, got {len(staging):#x}")

    critical = (
        "total_record_number",
        "record_number_after_last_header_attempt",
        "header_attempt_counter",
        "staged_record_count",
    )
    for key in critical:
        need(before[key] == after[key],
             f"incoherent RAM snapshot: {key} changed across staging read")

    total = before["total_record_number"]
    staged = before["staged_record_count"]
    need(total <= 0x300000, f"total record number is out of range: {total:#x}")
    need(staged <= 10, f"staged record count is out of range: {staged}")
    need(total >= staged, f"total record number {total} is below staged count {staged}")

    slots = []
    for index in range(10):
        slot = staging[index * 0x200:(index + 1) * 0x200]
        slots.append({
            "index": index,
            "current": index < staged,
            "sha256": sha256(slot),
            "record_number": u32(slot, 0x00),
            "session_count": u32(slot, 0x04),
            "tick_low": u32(slot, 0x08),
            "tick_high": u32(slot, 0x0C),
        })

    if staged:
        first = total - staged + 1
        for index in range(staged):
            need(slots[index]["record_number"] == first + index,
                 f"slot {index} record number mismatch: "
                 f"{slots[index]['record_number']} != {first + index}")
        for index in range(1, staged):
            delta = (slots[index]["tick_low"] - slots[index - 1]["tick_low"]) & 0xFFFFFFFF
            need(0 < delta < 0x80000000,
                 f"slot {index} tick does not advance modulo 32 bits")

    return {
        "coherent_critical_counters": True,
        "staging_sha256": sha256(staging),
        "metadata_before": before,
        "metadata_after": after,
        "current_batch_state": ("none" if staged == 0 else
                                "possibly_in_flight" if staged == 10 else
                                "staged"),
        "slots": slots,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--header", type=Path,
                        help="optional retained 0x200/0x400-byte header read to validate offline")
    parser.add_argument("--metadata-before", type=Path,
                        help="first retained 0x2c-byte producer-metadata read")
    parser.add_argument("--staging", type=Path,
                        help="retained 0x1400-byte staging-buffer read")
    parser.add_argument("--metadata-after", type=Path,
                        help="second retained 0x2c-byte producer-metadata read")
    args = parser.parse_args()
    snapshot_args = (args.metadata_before, args.staging, args.metadata_after)
    need(all(x is None for x in snapshot_args) or all(x is not None for x in snapshot_args),
         "--metadata-before, --staging, and --metadata-after must be supplied together")
    blobs = verify_inputs()
    result = {
        "inputs": {str(p): {"size": len(d), "sha256": sha256(d)} for p, d in blobs.items()},
        "static": verify_static(blobs[PACKAGE], blobs[STORED]),
        "capture": parse_capture(blobs[CAPTURE]),
        "storage": {
            "contract": "internal firmware storage-byte-address contract; not a target-203-cleared host address",
            "header_addresses": ["0x80000000", "0x80000200"],
            "data_base": "0x80004000",
            "record_size": "0x200",
            "record_address_formula": "0x80004000 + record_index * 0x200",
            "maximum_record_count": "0x300000",
            "target203_family2_limit": "address and address+length must remain below 0x01000000",
            "target203_high_bank_supported": False,
            "qualified_ram_candidates": {
                "staging": {
                    "cpu": "0x2000be40",
                    "dma_alias": "0x4500be40",
                    "length": "0x1400",
                    "target101_header_hex": "0101000040be004500140000"
                },
                "metadata": {
                    "cpu": "0x20000850",
                    "dma_alias": "0x45000850",
                    "length": "0x2c",
                    "target101_header_hex": "01010000500800452c000000"
                }
            },
        },
    }
    if args.header is not None:
        result["parsed_headers"] = parse_header_file(args.header)
    if args.metadata_before is not None:
        result["parsed_ram_snapshot"] = parse_ram_snapshot(
            args.metadata_before, args.staging, args.metadata_after)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
