#!/usr/bin/env python3
"""Offline, hash-checked QD command-skip disassembly; no TV access."""
import hashlib
from pathlib import Path
import subprocess

MODULE = Path(__file__).resolve().parent.parent / "binaries" / "qdf_tcon.ko"
EXPECTED = "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"
RANGES = (
    (".text", 0xf98, 0x10e8), (".text", 0x9b88, 0x9e14),
    (".text", 0x69b0, 0x6d80), (".text", 0xbba0, 0xc180),
    (".text", 0xa938, 0xa9f8), (".text", 0xab00, 0xabd0),
    (".text", 0x10c70, 0x10d68), (".text", 0x10fe0, 0x11058),
    (".text", 0x11d78, 0x12058), (".text", 0x13690, 0x13988),
    (".init.text", 0x90, 0x140),
)

if hashlib.sha256(MODULE.read_bytes()).hexdigest() != EXPECTED:
    raise SystemExit("qdf_tcon.ko hash mismatch")
print(f"# qdf_tcon.ko sha256={EXPECTED}")
for section, start, stop in RANGES:
    subprocess.run(["aarch64-linux-gnu-objdump", "-dr", "-j", section,
                    f"--start-address={start}", f"--stop-address={stop}",
                    str(MODULE)], check=True)
