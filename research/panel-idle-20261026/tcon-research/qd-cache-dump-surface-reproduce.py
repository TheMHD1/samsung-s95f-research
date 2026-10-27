#!/usr/bin/env python3
"""Offline verifier for the hash-bound QDF debug fixed-exit finding.

Reads copied module bytes and tool output only.  It does not open a TV
connection, load code, write any device file, or issue an ioctl.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED_SHA256 = "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"
ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "binaries" / "qdf_tcon.ko"


def output(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def require(text: str, needle: str) -> None:
    if needle not in text:
        raise SystemExit(f"FAIL: missing expected evidence: {needle}")


def main() -> None:
    if not MODULE.is_file():
        raise SystemExit(f"FAIL: missing copied module: {MODULE}")
    actual = hashlib.sha256(MODULE.read_bytes()).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"FAIL: SHA-256 mismatch: {actual}")

    symbols = output("readelf", "-sW", str(MODULE))
    for needle in (
        "0000000000000000     4 OBJECT  LOCAL  DEFAULT   21 m_suspend_status",
        "0000000000000010     4 OBJECT  LOCAL  DEFAULT   21 m_tcon_state",
        "0000000000000040     4 OBJECT  LOCAL  DEFAULT   21 m_pvcc_status",
        "000000000000010c     4 OBJECT  LOCAL  DEFAULT   21 m_command_skip",
        "0000000000000194     4 OBJECT  LOCAL  DEFAULT   21 m_panel_dpms_pvcc_status",
        "0000000000013c30  8008 FUNC    GLOBAL DEFAULT    3 QDFTcon_Tcon_Debug",
        "0000000000016650     8 FUNC    GLOBAL DEFAULT    3 t2ddebug_get_hex",
    ):
        require(symbols, needle)

    objdump = "aarch64-linux-gnu-objdump"
    helpers = output(objdump, "-dr", "--start-address=0x16648", "--stop-address=0x16658", str(MODULE))
    require(helpers, "<t2ddebug_get_decimal>")
    require(helpers, "<t2ddebug_get_hex>")
    if helpers.count("mov\tx0, #0x99") != 2 or helpers.count("ret") != 2:
        raise SystemExit("FAIL: t2ddebug helper bodies are not both fixed 0x99 returns")

    gate = output(objdump, "-dr", "--start-address=0x14428", "--stop-address=0x1449c", str(MODULE))
    for needle in ("bl\t16650 <t2ddebug_get_hex>", "cmp\tw0, #0x90", "br\tx0", "cmp\tw26, #0x99", "ret"):
        require(gate, needle)

    cache_block = output(objdump, "-dr", "--start-address=0x1454c", "--stop-address=0x14ae0", str(MODULE))
    for needle in ("ldr\tw4, [x20]", "ldr\tw4, [x20, #16]", "ldr\tw4, [x20, #64]", "ldr\tw4, [x20, #268]"):
        require(cache_block, needle)

    init = output(objdump, "-dr", "--start-address=0x3bc", "--stop-address=0x434", str(MODULE))
    for needle in ("QDFTcon_Tcon_Debug", "str\tx9, [x19, #24]"):
        require(init, needle)

    reloc = output("readelf", "-rW", str(MODULE))
    for needle in ("QDFTcon_UpgradeFlashDataCAD", "QDFTcon_SetOffSensing"):
        require(reloc, needle)
    command_branch = output(objdump, "-dr", "--start-address=0x15a18", "--stop-address=0x15a30", str(MODULE))
    require(command_branch, "m_send_cmd_with_lock.constprop.0")

    print("PASS: exact QDF module has constant 0x99 debug helpers and a verified menu/exit path;")
    print("      cache and mutating selector branches exist but are not reached; public transport is unproved.")


if __name__ == "__main__":
    main()
