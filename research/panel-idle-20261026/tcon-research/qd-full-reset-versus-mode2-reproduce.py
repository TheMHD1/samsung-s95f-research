#!/usr/bin/env python3
"""Hash-gated offline landmarks for the QDF Mode-2/PM callback comparison."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "qdf": (ROOT / "binaries/qdf_tcon.ko", "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"),
    "frc": (ROOT / "binaries/tztv_frc_tcon.ko", "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd"),
    "api": (ROOT / "binaries/tztv_frc_tcon_api.ko", "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6"),
    "ocl": (ROOT / "overnight/serdes-ack-copy-20261026/sdp_ocl_jp.ko", "e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_hashes() -> None:
    for name, (path, expected) in FILES.items():
        require(path.is_file(), f"missing {name}: {path}")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        require(got == expected, f"{name} SHA-256 mismatch: {got}")


def section(path: Path, start: int, stop: int, section_name: str) -> str:
    return subprocess.check_output(
        ["aarch64-linux-gnu-objdump", "-dr", "-j", section_name,
         f"--start-address=0x{start:x}", f"--stop-address=0x{stop:x}", str(path)],
        text=True,
    )


def need(text: str, *needles: str) -> None:
    for needle in needles:
        require(needle in text, f"missing disassembly landmark: {needle}")


def main() -> int:
    check_hashes()
    frc = FILES["frc"][0]
    qdf = FILES["qdf"][0]
    ocl = FILES["ocl"][0]
    raw = frc.read_bytes()
    # .rodata.str1.8 starts at file offset 0x296b0 in this exact ELF.
    need(raw[0x296b0 + 0x51b8:0x296b0 + 0x51d8].decode("ascii"), "sdp_ocl_reset_tcon_power")
    need(raw[0x296b0 + 0x51d8:0x296b0 + 0x51e8].decode("ascii"), "set_power_mode")
    resolver = section(frc, 0x57d8, 0x5804, ".text")
    need(resolver, "57e4:", "57f8:", "tztv_set_sdp_jp_tcon_power_reset", "57fc:", "5800:")
    pm_suspend = section(frc, 0x2bac, 0x2d0c, ".text.unlikely")
    need(pm_suspend, "2bac:", "2bb8:", "2bbc:", "2c68:", "2d00:", "2d08:")
    pm_resume = section(frc, 0x1698, 0x1958, ".text.unlikely")
    need(pm_resume, "1698:", "16a4:", "16a8:", "174c:", "176c:", "17c4:", "1954:")
    qdf_power = section(qdf, 0x119dc, 0x11b48, ".text")
    need(qdf_power, "119ec:", "tztv_set_sdp_jp_tcon_power_reset", "11b14:")
    reset = section(ocl, 0x2b38, 0x2b88, ".text")
    need(reset, "sdp_ocl_reset_tcon_power", "mov\tw1, #0x3f", "bl\t7d60 <SDP_OCL_I2C_MBox_Write>")
    mbox = section(ocl, 0x7d60, 0x7ee0, ".text")
    need(mbox, "SDP_OCL_I2C_MBox_Write", "7e60:", "i2c_transfer")
    print("PASS: hash-gated static Mode-2/PM callback landmarks verified")
    print("LIMIT: resolver returns, PM guards, mailbox receiver semantics, and live binding are not checked")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
