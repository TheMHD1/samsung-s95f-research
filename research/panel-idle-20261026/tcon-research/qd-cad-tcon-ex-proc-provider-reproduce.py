#!/usr/bin/env python3
"""Offline byte/landmark checks for qd-cad-tcon-ex-proc-provider.md.

This program reads only retained local files.  It neither loads the module nor
executes target code.  Control-flow interpretation still requires the report's
manual review.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "overnight/sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko"
MANIFEST = ROOT / "overnight/sdp-pqe-frc-provider-copy-20261026a/manifest.json"
SCAN = ROOT / "overnight/tcon-ex-proc-provider-scan-20261026a/client.stdout"
VLOG = ROOT / "overnight/owner-power-on-20261026a-rescue/retained/vlog-after.txt"
FIELDS_DIR = ROOT / "overnight/factory-qd-data-fields-20261026a"
FIELDS = FIELDS_DIR / "fields.json"
FIELDS_STDOUT = FIELDS_DIR / "client.stdout"

MODULE_SHA = "1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4"
MANIFEST_SHA = "54cc98708203cee3778ba329ab8e2219c91fcb4fc82eb9f3076f283fdaad2f4d"
SCAN_SHA = "43d62d1f13fa7b4ece51ae0ddf83c530dd255b0d30ed6a2364a5e257dd11a240"
VLOG_SHA = "eac02d7bf3a4fb216295edba8be99466d7b80c7a43f7535841f882b052c1c3d3"
FIELDS_SHA = "b1f0df94dfc81d7774293314e03e668b3056709169985fc31defa0c4ea8dc327"
FIELDS_STDOUT_SHA = "ad0090732901edfadd0c202e855a7bacd660af5acd1e94967710b360a849cdd0"

EXPECTED_TEXT = {
    "F_RSM1_BN9658111C_COMMON.bin": ("12210", "F55ABU1D2", "FA224C240"),
    "F_RSM1_BN9658112C_COMMON.bin": ("12220", "F65ABU1D2", "FA224C240"),
    "F_RSM1_BN9659920A_COMMON.bin": ("12200", "F55ABU0D2", "FA124C190"),
    "F_RSM1_BN9659920B_COMMON.bin": ("12200", "F55ABUAE2", "FA024C190"),
    "F_RSM1_BN9659932A_COMMON.bin": ("12210", "F65ABU0D2", "FA124C190"),
    "F_RSM1_BN9659932B_COMMON.bin": ("12210", "F65ABUAE2", "FA024C190"),
    "F_RSM1_BN9659934A_COMMON.bin": ("12230", "F77ABU0D2", "FA124C190"),
    "F_RSM1_BN9659934B_COMMON.bin": ("12300", "F77ABUAE2", "FA024C300"),
    "F_RSM1_BN9660751A_COMMON.bin": ("\0\0\0\0\0", "\0" * 9, "FB925620A"),
}

# (section, address, size, SHA-256).  Addresses are relocatable section offsets.
FUNCTIONS = {
    "_get_file_path.isra.0": (".text", 0x57678, 180, "0b1b5e374a958b24ce232f3167c37a9c75a1c55eb01ad8e8634dcc1538913239"),
    "_read_data_file": (".text", 0x57748, 424, "fd08e47a18ea7dfa71c1145d606b06abe642e66c0b0a131f3dcad6d30189ddb9"),
    "getDataVersionAddr": (".text", 0x57C90, 116, "4a07043d19b5b4c453c48a84476b7df4da218a14023c718dbb900a9221e65191"),
    "getFWType": (".text", 0x57E58, 76, "0aa8855a05edf5ffbfc0f34ea1bc5004571093bc5782ac1ea037e46610184642"),
    "getDataregionAddr": (".text", 0x57F48, 96, "e5fe21284b023486f6f573759137d37a644dc2283d2f89f30d480c6a4c0fb1e5"),
    "getVDAddr": (".text", 0x57FA8, 156, "9655989c6fce2e1a67eec8a61bfcb95858a889a28b7cd72c0c7ba886697e42a1"),
    "tcon_ex_proc": (".text", 0x58048, 1436, "a205411955a4cb87bf9352f15feef212a6ace2d4189a9613dd0dc1e0c6165da4"),
    "calculate_CRC": (".text", 0x586E0, 184, "03443d926679211ea793ea88e5507a9f4c87b1a79264bbd86c1df70f0e15aaba"),
    "tcon_read_fw_data": (".text", 0x588B8, 392, "f1c7532c75eaf0c1bdd0f9c864d12d3f03b68219e51442a71af21d447e75231b"),
    "_write_data": (".text.unlikely", 0x2B90, 704, "a767ce1ad034ffd0f8b4a334c32755a89b7a74233bf0de8b13de60f903c5cecf"),
    "_check_version_compatibility_crc": (".text.unlikely", 0x3A48, 1052, "eeb5c256cea273fe9c8e9fabf91e9ffaaeac76ba38ac6fdaf52aee1796066a56"),
    "_upgrade": (".text.unlikely", 0x3ED8, 4044, "b3651bd27a4b7e246d3102f096d965917d4fd1049073cc109123ddd3f589bb1e"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True)


def disasm(section: str, start: int, stop: int) -> str:
    return run(
        "aarch64-linux-gnu-objdump", "-dr", f"--section={section}",
        f"--start-address={start:#x}", f"--stop-address={stop:#x}", str(MODULE),
    )


def main() -> None:
    blob = MODULE.read_bytes()
    require(len(blob) == 1_015_070, "module size changed")
    require(sha(blob) == MODULE_SHA, "module hash changed")
    require(sha(MANIFEST.read_bytes()) == MANIFEST_SHA, "copy manifest changed")
    require(sha(SCAN.read_bytes()) == SCAN_SHA, "provider scan changed")
    require(sha(FIELDS.read_bytes()) == FIELDS_SHA, "field manifest changed")
    require(sha(FIELDS_STDOUT.read_bytes()) == FIELDS_STDOUT_SHA, "field response changed")

    manifest = json.loads(MANIFEST.read_text())
    require(manifest.get("accepted") is True, "copy manifest is not accepted")
    require(manifest.get("size") == 1_015_070, "manifest size mismatch")
    require(manifest.get("sha256") == MODULE_SHA, "manifest hash mismatch")

    sections = run("aarch64-linux-gnu-readelf", "-SW", str(MODULE))
    require(re.search(r"\]\s+\.text\s+PROGBITS\s+0+\s+000080\s", sections) is not None,
            "unexpected .text layout")
    require(re.search(r"\]\s+\.text\.unlikely\s+PROGBITS\s+0+\s+09e870\s", sections) is not None,
            "unexpected .text.unlikely layout")
    file_offsets = {".text": 0x80, ".text.unlikely": 0x9E870}
    for name, (section, address, size, expected) in FUNCTIONS.items():
        body = blob[file_offsets[section] + address:file_offsets[section] + address + size]
        require(len(body) == size, f"short slice: {name}")
        require(sha(body) == expected, f"function hash mismatch: {name}")

    syms = run("aarch64-linux-gnu-readelf", "-sW", str(MODULE))
    require(re.search(r"\b0*58048\s+1436\s+FUNC\s+GLOBAL\s+DEFAULT\s+3\s+tcon_ex_proc$", syms, re.M) is not None,
            "exported tcon_ex_proc symbol changed")
    require("__ksymtab_tcon_ex_proc" in syms and "__kstrtab_tcon_ex_proc" in syms,
            "kernel export records missing")

    entry = disasm(".text", 0x58048, 0x585E4)
    require("cmp\tw19, #0x20" in entry, "operation 0x20 dispatch missing")
    require("bl\t5bb70 <ssb_usb_device_ready>" in entry, "USB-ready gate missing")
    require("kthread_create_on_node" in entry and "wake_up_process" in entry,
            "upgrade worker launch landmarks missing")
    require("add\tx1, sp, #0x90" in entry, "48-byte-envelope worker context changed")
    require("mov\tw0, #0x64" in entry and "mov\tw21, #0xa" in entry,
            "bounded outer poll landmarks changed")

    upgrade = disasm(".text.unlikely", 0x3ED8, 0x4EA4)
    for needle in (
        "cmp\tw19, #0x30", "R_AARCH64_CALL26\t.text+0x57748",
        "bl\t57fa8 <getVDAddr>", "bl\t57c90 <getDataVersionAddr>",
        "bl\t3a48 <_check_version_compatibility_crc>",
        "bl\t2b90 <_write_data>", "mov\tw24, #0x500000",
    ):
        require(needle in upgrade, f"upgrade landmark missing: {needle}")
    require("sub\tx22, x22, #0x500, lsl #12" in upgrade,
            "5 MiB lower-bound normalization missing")
    require("cmp\tx22, #0x100, lsl #12" in upgrade,
            "6 MiB upper-bound comparison missing")
    require("sub\tw0, w0, #0x30" in upgrade and "cmp\tw0, #0x3" in upgrade,
            "0x30..0x33 branch gate missing")
    require(upgrade.count("ldr\tx3, [x20, #32]") >= 3,
            "comparison-metadata pointer loads changed")
    require("add\tx3, x3, #0x9" in upgrade and "add\tx3, x3, #0x14" in upgrade,
            "comparison-metadata pointee offsets changed")
    require("mov\tx2, #0x300" in upgrade, "command-0x30 target/address header changed")

    reader = disasm(".text", 0x57748, 0x578F0)
    for needle in ("vfs_llseek", "vmalloc", "kernel_read"):
        require(needle in reader, f"host file reader call missing: {needle}")
    require("mov\tw2, w21" in reader and "cbnz\tw23, 5786c" in reader,
            "whole-file request/nonzero-return acceptance landmarks changed")
    writer = disasm(".text.unlikely", 0x2B90, 0x2E50)
    require("file_write.part.0" in writer, "SSB file-write helper changed")
    require("mov\tw2, #0xc" in writer, "12-byte SSB header write changed")
    require(b"/dev/ssb1\x00" in blob and b"/dev/ssbs1\x00" in blob,
            "SSB target literals missing")

    # Exact command-0x30 container offsets produced by the selected helpers.
    # The +0x60000 bias is applied by the caller, not inside either helper.
    require(0x60000 + 0x2000A == 0x8000A, "version offset arithmetic")
    require(0x60000 + 0x20100 == 0x80100, "VD offset arithmetic")
    require(0x4FF000 + 0xE00 == 0x4FFE00, "tail identifier offset arithmetic")
    require(0x500000 == 5_242_880, "factory file size arithmetic")

    # This exact provider does not contain the sampled header value literally.
    # This is only a bounded literal census; it does not exclude computation.
    require(bytes.fromhex("5a5aa5a5") not in blob, "sampled magic newly literal")
    require(bytes.fromhex("a5a55a5a") not in blob, "reverse magic newly literal")

    vlog = VLOG.read_bytes()
    require(sha(vlog) == VLOG_SHA, "rescued vlog changed")
    for token in (b"F_RSM1_", b"BN9658111C", b"BN9658112C", b"BN9659920A",
                  b"BN9659920B", b"BN9659932A", b"BN9659932B", b"BN9659934A",
                  b"BN9659934B", b"BN9660751A"):
        require(token not in vlog, f"retained vlog now contains {token!r}")

    fields = json.loads(FIELDS.read_text())
    require(fields.get("accepted") is True and fields.get("physical_state") == "unobserved",
            "field acquisition classification changed")
    require(len(fields.get("files", [])) == 9, "field file count changed")
    seen: set[str] = set()
    for item in fields["files"]:
        name = Path(item["path"]).name
        require(name in EXPECTED_TEXT and name not in seen, f"unexpected/duplicate field file: {name}")
        seen.add(name)
        by_offset = {row["offset"]: row for row in item["fields"]}
        require(set(by_offset) == {0x8000A, 0x80100, 0xB000A, 0xB0100, 0x4FFE00},
                f"field offsets changed: {name}")
        for row in item["fields"]:
            raw = (FIELDS_DIR / row["local_path"]).read_bytes()
            require(len(raw) == row["bytes"] == 64, f"field length changed: {name}")
            require(sha(raw) == row["sha256"], f"field hash mismatch: {name}")
        version, vd, tail = EXPECTED_TEXT[name]
        require(bytes.fromhex(by_offset[0x8000A]["hex"]).startswith(version.encode("latin1")),
                f"version bytes changed: {name}")
        require(bytes.fromhex(by_offset[0x80100]["hex"]).startswith(vd.encode("latin1")),
                f"VD bytes changed: {name}")
        require(bytes.fromhex(by_offset[0x4FFE00]["hex"]).startswith(tail.encode("ascii")),
                f"tail bytes changed: {name}")
        if name == "F_RSM1_BN9660751A_COMMON.bin":
            require(bytes.fromhex(by_offset[0xB0100]["hex"]).startswith(b"F32AHUME2"),
                    "60751A command-0x32 VD bytes changed")
    require(seen == set(EXPECTED_TEXT), "field inventory incomplete")

    print("PASS qd-cad-tcon-ex-proc-provider: hashes and selected landmarks match")


if __name__ == "__main__":
    main()
