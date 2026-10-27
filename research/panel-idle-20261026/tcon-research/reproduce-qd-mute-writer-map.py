#!/usr/bin/env python3
"""Read-only, bounded evidence extractor for qdf_tcon panel-mute analysis.

It deliberately makes no network or device connection.  It verifies the exact
copied module, then prints only the disassembly windows used by
qd-mute-writer-map.md.  A toolchain with aarch64-linux-gnu-objdump is required.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import subprocess
import sys


EXPECTED_SHA256 = "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"
WINDOWS = (
    ("public SetMute", 0xCE00, 0xD080),
    ("initialization direct unmute", 0xF910, 0xFF10),
    ("frame-mode temporary mute", 0x10508, 0x107E8),
    ("recovery frame mode", 0x107E8, 0x10A00),
    ("resume direct unmute and recovery", 0x10EE8, 0x11058),
    ("power-control recovery caller", 0x118D0, 0x11950),
    ("EL-sensing recovery caller", 0x12180, 0x121E0),
    ("off-sensing recovery caller", 0x13B90, 0x13BF0),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "module",
        nargs="?",
        type=pathlib.Path,
        default=pathlib.Path(__file__).parents[1] / "binaries" / "qdf_tcon.ko",
    )
    args = parser.parse_args()
    digest = hashlib.sha256(args.module.read_bytes()).hexdigest()
    print(f"module={args.module}")
    print(f"sha256={digest}")
    if digest != EXPECTED_SHA256:
        print("REFUSING: module hash does not match the audited copy", file=sys.stderr)
        return 2

    for label, start, stop in WINDOWS:
        print(f"\n===== {label}: 0x{start:x}..0x{stop:x} =====")
        subprocess.run(
            [
                "aarch64-linux-gnu-objdump", "-dr", "--start-address", hex(start),
                "--stop-address", hex(stop), str(args.module),
            ],
            check=True,
        )
    print("\n===== static immediate command construction hits =====")
    output = subprocess.check_output(
        ["aarch64-linux-gnu-objdump", "-dr", "-j", ".text", str(args.module)],
        text=True,
    )
    for line in output.splitlines():
        if "#0x164" in line:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
