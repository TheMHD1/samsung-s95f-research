#!/usr/bin/env python3
"""Offline source-hash and disassembly-landmark checks; CFG reviewed manually."""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QDF = ROOT / "binaries/qdf_tcon.ko"
FRC = ROOT / "binaries/tztv_frc_tcon.ko"
HASHES = {
    QDF: "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63",
    FRC: "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd",
}


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def need(text, item):
    if item not in text:
        raise SystemExit("FAIL: missing " + item)


def main():
    for path, expected in HASHES.items():
        if not path.is_file():
            raise SystemExit("FAIL: missing " + str(path))
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != expected:
            raise SystemExit(f"FAIL: SHA-256 for {path.name}: {got}")

    od = "aarch64-linux-gnu-objdump"
    power = run(od, "-dr", "--start-address=0x11848", "--stop-address=0x11d78", str(QDF))
    for item in (
        "<m_set_power_control>",
        "str\twzr, [x20, #4]", "str\twzr, [x20, #16]", "str\twzr, [x20, #64]",
        "mov\tw0, #0x2bc", "mov\tw0, #0x3e8", "mov\tw0, #0x64", "mov\tw0, #0xa",
        "m_check_tcon_status", "m_tcon_recovery_frame_mode", "m_register_recovery_noFramerate",
        "tztv_frc_tcon_set_acdet", "tztv_frc_tcon_set_dvdd", "tztv_frc_tcon_set_elvdd",
        "tztv_frc_tcon_read_err_det_status", "tztv_set_sdp_jp_tcon_power_reset",
        "<QDFTcon_SetQdTconPowerControl>",
    ):
        need(power, item)

    err = run(od, "-dr", "--start-address=0x1af0", "--stop-address=0x1c30", str(FRC))
    for item in ("of_get_named_gpio_flags", "gpio_request", "gpiod_direction_input",
                 "gpiod_get_raw_value_cansleep", "gpio_free", "str\tw1, [x21]"):
        need(err, item)

    rails = run(od, "-dr", "--start-address=0x7ec8", "--stop-address=0x82a8", str(FRC))
    for item in ("<_tztv_frc_tcon_set_elvdd>", "<_tztv_frc_tcon_set_acdet>",
                 "gpiod_direction_output_raw", "gpiod_set_raw_value_cansleep",
                 "_tztv_frc_tcon_nvt_set_stbc_gpio"):
        need(rails, item)

    print("PASS: exact hashes and power/GPIO/timing/recovery disassembly landmarks verified")
    print("      Branch flow, delay placement and error propagation are manually reviewed, not fully asserted here.")


if __name__ == "__main__":
    main()
