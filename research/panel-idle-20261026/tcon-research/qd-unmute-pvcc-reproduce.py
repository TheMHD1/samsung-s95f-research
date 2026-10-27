#!/usr/bin/env python3
"""Print exact offline PVCC guard/lifecycle evidence; no TV access."""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent / "binaries"
INPUTS = {
    "qdf_tcon.ko": ("97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63", [
        (".text", 0xf98, 0x10e0), (".text", 0xbba0, 0xbc10),
        (".text", 0xbe80, 0xbf08), (".text", 0x11b88, 0x11c48),
        (".init.text", 0xe4, 0x148)]),
    "tztv_frc_tcon_api.ko": ("3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6", [
        (".text", 0xc020, 0xc098)]),
    "tztv_frc_tcon.ko": ("aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd", [
        (".text", 0x5408, 0x5440), (".text", 0x60d0, 0x6328),
        (".text", 0x63d8, 0x6440), (".text.unlikely", 0x1114, 0x14b8)]),
}

for name, (expected, ranges) in INPUTS.items():
    path = ROOT / name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise SystemExit(f"Input hash mismatch: {name}")
    print(f"# {name} sha256={digest}", flush=True)
    for section, start, stop in ranges:
        subprocess.run(["aarch64-linux-gnu-objdump", "-dr", "-j", section,
                        f"--start-address={start}", f"--stop-address={stop}", str(path)], check=True)
