#!/usr/bin/env python3
"""Offline checks for ssb-transport-driver-binding.md; never loads a module."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "overnight/sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko"
METADATA = ROOT / "overnight/ssb-device-metadata-20261026a/client.stdout"
REGISTRATION = ROOT / "overnight/ssb-registration-metadata-20261026a/client.stdout"
MODULE_SHA = "1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4"
METADATA_SHA = "a306d32dfa3dfd1e214fbcb22625bff5ade0d26957cbdf6e2516a26b2f759952"
REGISTRATION_SHA = "2807922e63b27c2aef8d9b3ad9c9b5eb3b20a49f5d6e2808928784b6bff48351"


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tool(*args: str) -> str:
    return subprocess.check_output(args, text=True)


def disasm(start: int, stop: int) -> str:
    return tool("aarch64-linux-gnu-objdump", "-dr", "--section=.text",
                f"--start-address={start:#x}", f"--stop-address={stop:#x}", str(MODULE))


def main() -> None:
    require(MODULE.stat().st_size == 1_015_070 and sha(MODULE) == MODULE_SHA, "module identity")
    require(sha(METADATA) == METADATA_SHA, "metadata identity")
    require(REGISTRATION.stat().st_size == 5_209 and sha(REGISTRATION) == REGISTRATION_SHA,
            "registration metadata identity")
    meta = METADATA.read_text()
    for item in ("SSB_METADATA_START", "ABSENT /dev/ssb1", "ABSENT /dev/ssbs1",
                 "ABSENT_CLASS=/sys/class/usbmisc/ssb1",
                 "ABSENT_CLASS=/sys/class/usbmisc/ssbs1", "SSB_METADATA_END"):
        require(item in meta, f"metadata marker {item!r}")
    registration_doc = json.loads(REGISTRATION.read_text())
    registration = registration_doc["commands"][0]["stdout"]
    for item in ("SSB_REGISTRATION_START", "sdp_pqe_frc 598016 0 - Live",
                 "platform:sdp_ld", "platform:sdp_pqe_frc", "USB_DEVICE=/sys/bus/usb/devices/7-1",
                 "idVendor\n04e8\nidProduct\n20d2", "idVendor\n04e8\nidProduct\n2001",
                 "STL1 CDC and Bulk", "SSB_REGISTRATION_END"):
        require(item in registration, f"registration marker {item!r}")
    require("\nPRESENT\n" not in registration, "unexpected named SSB registration")

    sym = tool("aarch64-linux-gnu-readelf", "-sW", str(MODULE))
    for item in ("usb-ssb.c", "_ssb_init_func", "ssb_open", "ssb_probe", "ssb_write",
                 "ssb_ioctl", "ssb_usb_device_ready", "ssb_fops", "ssb_driver", "ssb_table"):
        require(item in sym, f"missing symbol {item}")
    reloc_rodata = tool("aarch64-linux-gnu-readelf", "-rW", str(MODULE))
    for item in (".text + 597b0", ".text + 5aba8", ".text + 5a0d0",
                 ".text + 5aa78", ".text + 5a3d0", ".text.unlikely + 5060"):
        require(item in reloc_rodata, f"fops/driver relocation {item}")

    init = disasm(0x573E8, 0x57530)
    for item in ("bl\t5b098 <resolve_usb_symbols>", "bl\t5b9f8 <ssb_usb_register_driver>",
                 "R_AARCH64_ABS64\t.bss+0x44a0"):
        require(item in init, f"init landmark {item}")
    register = disasm(0x5B9F8, 0x5BACC)
    for item in ("bl\t0 <__symbol_get>", "bl\t0 <__request_module>",
                 "R_AARCH64_ABS64\t.data+0x450"):
        require(item in register, f"registration landmark {item}")
    opened = disasm(0x5A0D0, 0x5A2E8)
    for item in ("ldr\tw22, [x19, #76]", "ldr\tx2, [x23, #16]",
                 "ldr\tx1, [x23, #112]", "blr\tx1", "str\tx22, [x21, #200]"):
        require(item in opened, f"open landmark {item}")
    released = disasm(0x5AA78, 0x5AB30)
    require("ldr\tx1, [x1, #48]" in released and "blr\tx1" in released,
            "release runtime-PM callback landmark")
    resolver = disasm(0x5B0E0, 0x5B290)
    for item in ("5b118:", "5b12c:\tf9001a60", "5b258:", "5b26c:\tf9003a60"):
        require(item in resolver, f"runtime-PM resolver landmark {item}")
    ready = disasm(0x5BB70, 0x5BC08)
    for item in ("bl\t0 <find_module>", "ldr\tw0, [x0, #144]"):
        require(item in ready, f"ready landmark {item}")
    blob = MODULE.read_bytes()
    require(blob[0xAD6C0 + 0x1F20:0xAD6C0 + 0x1F26] == bytes.fromhex("0300e8040120"),
            "USB ID table leading vendor/product record")
    require(b"ssb\x00" in blob and b"usb_register_driver\x00" in blob,
            "SSB driver-name/register literals")
    require(b"usb_autopm_get_interface\x00" in blob and b"usb_autopm_put_interface\x00" in blob,
            "runtime-PM symbol literals")
    for item in (b"/dev/ssb1\x00", b"/dev/ssbs1\x00", b"usb:v04E8p2001d*dc*dsc*dp*ic*isc*ip*in*"):
        require(item in blob, f"literal {item!r}")
    require(re.search(r"000000000005a3d0\s+1460\s+FUNC\s+LOCAL", sym) is not None, "probe extent")
    print("PASS ssb transport driver binding: retained module and static paths match")


if __name__ == "__main__":
    main()
