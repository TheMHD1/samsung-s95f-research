#!/usr/bin/env python3
"""Offline verifier for the bounded SSB restore-integrity audit."""

from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
ROOT = OVERNIGHT.parent
MODULE = OVERNIGHT / "sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko"
OBJDUMP = "aarch64-linux-gnu-objdump"
MAXIMUM = 0x500000
CHUNK = 0x2000


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_pinned(path, digest):
    data = path.read_bytes()
    need(sha(data) == digest, f"SHA-256 mismatch: {path}")
    return data


def disasm(section, start, stop):
    return subprocess.check_output([
        OBJDUMP, "-dr", "--no-show-raw-insn", f"--section={section}",
        f"--start-address={start:#x}", f"--stop-address={stop:#x}",
        str(MODULE),
    ], text=True)


def effective_size(llseek_result):
    """Model the unsigned LS CSEL at VA 0x58f00..0x58f20."""
    unsigned = llseek_result & 0xFFFFFFFFFFFFFFFF
    return unsigned if unsigned <= MAXIMUM else MAXIMUM


def requested_chunks(total):
    """Model the parent loop, including its unconditional final call."""
    need(0 <= total <= MAXIMUM, "modeled total out of bounds")
    rows = []
    offset = 0
    while offset + CHUNK < total:
        rows.append((offset, CHUNK))
        offset += CHUNK
    rows.append((offset, total - offset))
    return rows


def short_read_effect(previous, incoming, requested):
    """Model reuse of the parent's zero-initialized 8 KiB buffer."""
    need(len(previous) == requested and 0 <= len(incoming) <= requested,
         "short-read fixture geometry")
    out = bytearray(previous)
    out[:len(incoming)] = incoming
    return bytes(out)


FUNCTIONS = {
    # section, linked offset, file base, size, SHA-256
    "file_write.part.0": (".text.unlikely", 0x2388, 0x9E870, 96,
                          "bf195cdecf870fc3fd092141120e42892dcb98065b1a4bb495334a4806a34728"),
    "_write_data": (".text.unlikely", 0x2B90, 0x9E870, 704,
                    "a767ce1ad034ffd0f8b4a334c32755a89b7a74233bf0de8b13de60f903c5cecf"),
    "_restore_data": (".text.unlikely", 0x2ED0, 0x9E870, 296,
                      "d55301fc72ff69e06ae9d532cd4d7b7f8cf78fe37670979fbab90c64780d0d5f"),
    "file_close.part.0": (".text", 0x573A0, 0x80, 64,
                          "1ed93345ef4b97223e8d16668ea3dd104f7bf5d4efd1daaff65c1e0b351d687b"),
    "_ssb_init_func": (".text", 0x573E8, 0x80, 272,
                       "1fb8e07d0e19581ac4288c5d02f67bc33ed4191d5ab6a953b4360a7ed60da8e0"),
    "file_open": (".text", 0x57530, 0x80, 300,
                  "d0462c1ed585d380f0f9417ae41b204ad731aed25a8a9f1d4f80daa8dad5b529"),
    "tcon_restore_backup_data": (".text", 0x58DC8, 0x80, 844,
                                 "ee25c0d85f4b2bfd30a6f7144e52cd53c6bb9a7adf6c5b9e2dbf6c5e0359b05d"),
    "ssb_ioctl": (".text", 0x591A8, 0x80, 196,
                  "82ed53a7b15f665257fd40a0855808b2bb9851d6aa1f25581983fa58b129dc84"),
    "ssb_write": (".text", 0x5ABA8, 0x80, 1156,
                  "c56f4214239e61ba01fb90ba2ad2d0b5caf156e72bc3b9c0966720b9007328a6"),
}


def verify_function_bytes(blob):
    for name, (_, address, base, size, digest) in FUNCTIONS.items():
        body = blob[base + address:base + address + size]
        need(len(body) == size and sha(body) == digest, f"function bytes: {name}")


def verify_disassembly(parts):
    parent = parts["parent"]
    for item in (
        "bl\t573e8 <_ssb_init_func>",
        "mov\tw1, #0x0",
        "bl\t57530 <file_open>",
        "bl\t0 <vfs_llseek>",
        "cmp\tx19, #0x500, lsl #12",
        "csel\tx19, x19, x1, ls",
        "mov\tw5, #0x300",
        "str\tw5, [sp, #120]",
        "mov\tx1, #0x500000",
        "R_AARCH64_CALL26\t.text.unlikely+0x2ed0",
    ):
        need(item in parent, f"parent landmark: {item}")
    need(parent.count("bl\t0 <vfs_llseek>") == 2, "two parent seeks")
    need(parent.count("R_AARCH64_CALL26\t.text.unlikely+0x2ed0") == 2,
         "two parent restore-call sites")
    need(parent.count("tbz\tw0, #31") >= 2,
         "parent accepts restore result by sign only")
    need("tcon_read_fw_data" not in parent and "crc" not in parent.lower(),
         "unexpected parent readback/checksum path")

    restore = parts["restore"]
    for item in (
        "bl\t0 <kernel_read>",
        "tbz\tw21, #31",
        "ldr\tw3, [x20, #8]",
        "ldr\tx2, [x20]",
        "mov\tw0, #0x0",
        "bl\t2b90 <_write_data>",
        "tbz\tw0, #31",
    ):
        need(item in restore, f"restore-chunk landmark: {item}")
    need("cmp\t" not in restore[restore.index("bl\t0 <kernel_read>"):restore.index("bl\t2b90 <_write_data>")],
         "unexpected exact source-read comparison")

    writer = parts["writer"]
    for item in (
        "cmp\tw3, #0x300",
        "csel\tx3, x4, x3, ne",
        "and\tw0, w0, #0xfffffe00",
        "mov\tw2, #0xc",
        "bl\t2388 <file_write.part.0>",
        "tbz\tw19, #31",
    ):
        need(item in writer, f"writer landmark: {item}")
    need(writer.count("bl\t2388 <file_write.part.0>") == 4,
         "header/payload write call inventory")
    for site, register in ((0x2D58, "w19"), (0x2D84, "w0"),
                           (0x2DCC, "w0"), (0x2DFC, "w0")):
        need(f"{site:x}:\ttbz\t{register}, #31" in writer,
             f"header/payload sign-only check at {site:#x}")
    need("kernel_read" not in writer and "_read_data" not in writer,
         "unexpected writer readback")

    file_write = parts["file_write"]
    need("bl\t0 <kernel_write>" in file_write and "mov\tw0, w19" in file_write,
         "file writer raw return propagation")

    init = parts["init"]
    for item in ("bl\t5b098 <resolve_usb_symbols>",
                 "bl\t5b9f8 <ssb_usb_register_driver>"):
        need(item in init, f"initialization dependency: {item}")

    ioctl = parts["ioctl"]
    need("bl\t58dc8 <tcon_restore_backup_data>" in ioctl and
         "mov\tx19, #0x0" in ioctl,
         "ioctl restore result-discard path")

    usb_write = parts["usb_write"]
    for item in ("csel\tx20, x20, x2, ls", "mov\tx26, x20",
                 "ldr\tw28, [x21, #140]"):
        need(item in usb_write, f"USB write completion landmark: {item}")


def get_parts():
    return {
        "parent": disasm(".text", 0x58DC8, 0x59114),
        "restore": disasm(".text.unlikely", 0x2ED0, 0x2FF8),
        "writer": disasm(".text.unlikely", 0x2B90, 0x2E50),
        "file_write": disasm(".text.unlikely", 0x2388, 0x23E8),
        "init": disasm(".text", 0x573E8, 0x574F8),
        "ioctl": disasm(".text", 0x591A8, 0x5926C),
        "usb_write": disasm(".text", 0x5ABA8, 0x5B02C),
    }


def verify_label_binding(blob):
    # _write_data's literal slots bind x3 to EMMC_write and x4 to
    # EMMC_writeCRC. CMP/CSEL therefore select EMMC_write for target 0x300.
    relocs = subprocess.check_output([
        "aarch64-linux-gnu-readelf", "-rW", str(MODULE)], text=True)
    need(re.search(r"^0000000000002e50\s+.*R_AARCH64_ABS64.*"
                   r"\.rodata\.str1\.8 \+ 3138$", relocs, re.M) is not None,
         "EMMC_write literal relocation")
    need(re.search(r"^0000000000002e58\s+.*R_AARCH64_ABS64.*"
                   r"\.rodata\.str1\.8 \+ 3148$", relocs, re.M) is not None,
         "EMMC_writeCRC literal relocation")
    string_base = 0xAFD38
    need(blob[string_base + 0x3138:string_base + 0x3138 + 11] == b"EMMC_write\0",
         "EMMC_write label")
    need(blob[string_base + 0x3148:string_base + 0x3148 + 14] == b"EMMC_writeCRC\0",
         "EMMC_writeCRC label")


def self_test(blob, parts):
    checks = 0
    need([effective_size(value) for value in
          (0, 1, CHUNK, MAXIMUM - 1, MAXIMUM, MAXIMUM + 1, -1)] ==
         [0, 1, CHUNK, MAXIMUM - 1, MAXIMUM, MAXIMUM, MAXIMUM],
         "size-boundary model")
    need(requested_chunks(0) == [(0, 0)] and
         requested_chunks(CHUNK) == [(0, CHUNK)] and
         len(requested_chunks(MAXIMUM)) == 640 and
         requested_chunks(MAXIMUM)[-1] == (MAXIMUM - CHUNK, CHUNK),
         "chunk-boundary model")
    checks += 1

    first = short_read_effect(bytes(CHUNK), b"A" * 3, CHUNK)
    later = short_read_effect(b"B" * CHUNK, b"C" * 3, CHUNK)
    need(first[:4] == b"AAA\0" and first[3:] == bytes(CHUNK - 3) and
         later[:4] == b"CCCB" and later[3:] == b"B" * (CHUNK - 3),
         "short-read retained-tail model")
    checks += 1

    changed = bytearray(blob)
    _, address, base, _, _ = FUNCTIONS["tcon_restore_backup_data"]
    changed[base + address + 0x138] ^= 1
    try:
        verify_function_bytes(bytes(changed))
        raise ValueError("function mutation accepted")
    except ValueError as error:
        need("tcon_restore_backup_data" in str(error), "function mutation result")
    checks += 1

    changed_parts = dict(parts)
    changed_parts["parent"] = parts["parent"].replace(
        "csel\tx19, x19, x1, ls", "csel\tx19, x19, x1, hi")
    try:
        verify_disassembly(changed_parts)
        raise ValueError("size-cap mutation accepted")
    except ValueError as error:
        need("csel" in str(error), "size-cap mutation result")
    checks += 1

    changed_parts = dict(parts)
    changed_parts["restore"] = parts["restore"].replace(
        "tbz\tw21, #31", "cmp\tw21, w25", 1)
    try:
        verify_disassembly(changed_parts)
        raise ValueError("short-read-check mutation accepted")
    except ValueError as error:
        need("tbz" in str(error), "short-read mutation result")
    checks += 1

    changed_parts = dict(parts)
    changed_parts["writer"] = parts["writer"].replace(
        "bl\t2388 <file_write.part.0>", "nop", 1)
    try:
        verify_disassembly(changed_parts)
        raise ValueError("write-call mutation accepted")
    except ValueError as error:
        need("inventory" in str(error), "write-call mutation result")
    checks += 1
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    blob = load_pinned(MODULE,
        "1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4")
    need(len(blob) == 1_015_070, "module size")
    load_pinned(ROOT / "tcon-research/qd-ssb-readback-acquisition-boundary.md",
                "911c230c3509752f318af6e8ca7aa846547510c41c28a4fcdcbb02f6c72c7607")
    load_pinned(ROOT / "tcon-research/ssb-backup-entry-audit-20261027.md",
                "31a5f8bef9fdf4fbd8082f12676f7f6051684b997eb94e8e122b72e94023f730")
    load_pinned(OVERNIGHT / "prepd-source-followup-20261027ax/flash-recovery-gap.md",
                "154d0a8aa2895de22f57374a2030d84f3e9d82174b79c1209ef63254378a508f")

    verify_function_bytes(blob)
    verify_label_binding(blob)
    parts = get_parts()
    verify_disassembly(parts)
    result = {
        "schema": "restore-integrity-offline-v1",
        "module_sha256": sha(blob),
        "maximum_input_bytes": MAXIMUM,
        "exact_input_size_required": False,
        "negative_size_rejected": False,
        "zero_size_final_call_modeled": True,
        "restore_header_target": "0x300",
        "module_label_for_target": "EMMC_write",
        "source_short_read_rejected": False,
        "header_or_payload_short_write_explicitly_rejected_by_writer": False,
        "host_side_readback_or_checksum": False,
        "usb_transport_completion_observed_by_lower_driver": True,
        "remote_storage_commit_or_verify_observed": False,
        "independent_recovery_endpoint_proved": False,
        "target_operations": 0,
    }
    if args.self_test:
        result["self_test_checks"] = self_test(blob, parts)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
