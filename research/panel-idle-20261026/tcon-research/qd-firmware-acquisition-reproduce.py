#!/usr/bin/env python3
"""Offline bounded QD firmware-path evidence; never contacts the TV."""
from hashlib import sha256
from pathlib import Path
from subprocess import run

ROOT = Path(__file__).resolve().parent.parent / "binaries"
ARTIFACT_ROOT = ROOT.parent
OFFICIAL_PREFIX = (
    ARTIFACT_ROOT / "overnight" /
    "samsung-official-T-RSMFAKUC-0090-msd-prefix.bin"
)
OFFICIAL_PREFIX_SHA256 = "01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d"
MODULES = {
    "qdf_tcon.ko": "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63",
    "tztv_frc_tcon.ko": "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd",
    "tztv_frc_tcon_api.ko": "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6",
    "sdp_tcon.ko": "9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee",
}

for name, expected in MODULES.items():
    data = (ROOT / name).read_bytes()
    digest = sha256(data).hexdigest()
    if digest != expected:
        raise SystemExit(f"hash mismatch: {name}")
    print(f"# {name} sha256={digest}", flush=True)
    for token in (b"F77ABU2D20", b"RHEA_M_TCON_FW_20250103_1715"):
        print(f"{token.decode()} offset={data.find(token)}", flush=True)

module = ROOT / "qdf_tcon.ko"
for start, stop in ((0x8c00, 0x8c78), (0x93c0, 0x9630),
                    (0x12e68, 0x12fc8), (0x12218, 0x12280)):
    run(["aarch64-linux-gnu-objdump", "-dr", "-j", ".text",
         f"--start-address={start}", f"--stop-address={stop}", str(module)], check=True)

prefix = OFFICIAL_PREFIX.read_bytes()
prefix_digest = sha256(prefix).hexdigest()
if prefix_digest != OFFICIAL_PREFIX_SHA256:
    raise SystemExit("hash mismatch: official MSD prefix")
print(f"# official MSD prefix sha256={prefix_digest} size={len(prefix)}", flush=True)
for token in (b"MSDU11", b"T-RSMFAKUC-0090", b"Salted__",
              b"F77ABU2D20", b"TconFwQd", b"qdf", b"tcon"):
    print(f"{token.decode()} offset={prefix.find(token)}", flush=True)
