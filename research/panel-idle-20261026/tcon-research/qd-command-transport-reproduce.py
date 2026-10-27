#!/usr/bin/env python3
"""Offline bounded disassembly of captured QDF command transport only."""
from __future__ import annotations
import argparse
import hashlib
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
MODULE = HERE.parent / "binaries" / "qdf_tcon.ko"
SHA256 = "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"
RANGES = (("m_read_cmd_no_lock", 0xB8A0, 0xBBA0),
          ("m_send_cmd_with_lock", 0xBBA0, 0xC200),
          ("QDFTcon_t_Tcon_SetMute", 0xCE00, 0xD088))

def render() -> str:
    digest = hashlib.sha256(MODULE.read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"wrong qdf_tcon.ko: expected {SHA256}, got {digest}")
    result = [f"# sha256={digest}\n"]
    for name, start, stop in RANGES:
        command = ["aarch64-linux-gnu-objdump", "-dr", "-j", ".text",
                   f"--start-address=0x{start:x}", f"--stop-address=0x{stop:x}",
                   str(MODULE)]
        text = subprocess.run(command, check=True, text=True,
                              stdout=subprocess.PIPE).stdout
        result.extend((f"\n# {name}: .text+0x{start:x}..0x{stop:x}\n", text))
    return "".join(result)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", type=pathlib.Path,
                        help="optional local output artifact path")
    args = parser.parse_args()
    content = render()
    if args.write:
        args.write.write_text(content)
    else:
        sys.stdout.write(content)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
