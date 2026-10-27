#!/usr/bin/env python3
"""Bounded offline QD suspend/state disassembly; no TV access."""
from pathlib import Path
import hashlib
import subprocess

root = Path(__file__).resolve().parent.parent / "binaries"
module = root / "qdf_tcon.ko"
expected = "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"
ranges = (
    ("QDFTcon_SetSuspendFlag", 0x148, 0x1c8),
    ("QDFTcon_InitVariable", 0xf98, 0x10e8),
    ("QDFTcon_GetTconStatus", 0x4e0, 0x5c0),
    ("m_check_tcon_status", 0xb250, 0xb4f0),
    ("m_read_cmd_no_lock", 0xb8a0, 0xba60),
    ("m_send_cmd_gate", 0xbba0, 0xbc20),
    ("m_send_cmd_error", 0xbdd8, 0xbe40),
    ("m_set_power_control", 0x11a28, 0x11aa0),
    ("Resume_state_check", 0x11030, 0x11058),
)
digest = hashlib.sha256(module.read_bytes()).hexdigest()
if digest != expected:
    raise SystemExit(f"input hash mismatch: {digest}")
print(f"# qdf_tcon.ko sha256={digest}")
for name, start, stop in ranges:
    print(f"\n# {name}: .text+0x{start:x}..0x{stop:x}")
    subprocess.run(("aarch64-linux-gnu-objdump", "-dr", "-j", ".text",
                    f"--start-address=0x{start:x}",
                    f"--stop-address=0x{stop:x}", str(module)), check=True)
