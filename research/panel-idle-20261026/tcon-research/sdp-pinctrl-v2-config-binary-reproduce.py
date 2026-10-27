#!/usr/bin/env python3
"""Hash-gated checks for the built-in sdp-pinctrl-v2 gpio_chip callbacks.

This is an offline raw-Image checker.  It does not execute the Image or access
the TV.  Internal function boundaries and the no-later-store conclusion are a
manual CFG result; this script pins the complete bounded bytes and the exact
data/instruction landmarks on which that result rests.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "overnight/kernel-Image.bin"
INDEX = ROOT / "overnight/kernel-export-index.json"
META = ROOT / "overnight/gpio-controller-metadata-20261026a/client.stdout"

IMAGE_SHA = "77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d"
INDEX_SHA = "6d3ffe0edfd2ab92fc4439ffe35371db4c3f2ad8a99cf5b2b20ae2ef4eb937ac"
META_SHA = "d478bfdad3fd80de82771569cfce4763263d057f0ad320a4b06c555c15934ba8"

# Raw data pointers use the linked Image base.  Artificial-export-view symbols
# intentionally use file offsets/base zero; keep the two address spaces apart.
LINK_BASE = 0xFFFFFFC010080000

PLATFORM_DRIVER = 0xADF4F8
OF_MATCH = 0x8587E0
PROBE = (0x3BF6F8, 0x3BFD50)
CHIP_INIT = (0x3BF918, 0x3BFB34)

SLICE_HASHES = {
    (0xA18FCC, 0xA18FEC): "ad23971ce5220fd443c0c353a812cc48afc508b6d9e4acbb06cfef7ee68320e1",
    (0x3BF688, 0x3BF6F8): "e492076454809036ae971dd556f8b94e54d6ab0e22db81f8e70f07adc5530bb4",
    PROBE: "273ddc884339fb9c173eba2a53aca72a7b9b779f667d0b7d41d59658d2ba9f05",
    CHIP_INIT: "7d437f458fe8ad4e18756c6b445ff5a744befb12a69ac7105c2ebcb488647949",
    (0x3BFEF0, 0x3C0020): "27baa829433302575e573d3dc3562cc1d05d03af68efeef21ccf37a36e132679",
    (0x3C0020, 0x3C00E0): "a4808602dc5c77189989848bbb55622fd8cc71919e5ae4e0dfbfcd6c7b811a96",
    (0x3C00E0, 0x3C0124): "277a72b91525fe275733a2f4eae6824733a7209ff1641ac7e54bcf7198b801ea",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: object) -> None:
    if not condition:
        raise RuntimeError(str(message))


def u32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def u64(data: bytes, off: int) -> int:
    return struct.unpack_from("<Q", data, off)[0]


def cstr(data: bytes, off: int) -> str:
    end = data.index(0, off)
    return data[off:end].decode("ascii")


def sext(value: int, bits: int) -> int:
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def bl_target(data: bytes, off: int) -> int:
    word = u32(data, off)
    require(word & 0xFC000000 == 0x94000000, (hex(off), hex(word)))
    return off + (sext(word & 0x03FFFFFF, 26) << 2)


def exports(index: dict) -> dict[str, int]:
    out = {}
    for item in index["exports"]:
        out[item["name"]] = int(item["target_image_offset"], 16)
    return out


def check_words(data: bytes) -> None:
    # platform-driver init and exact exported registration call
    words = {
        0xA18FD0: 0xD2800001,  # mov x1,#0
        0xA18FD4: 0xF0000620,  # adrp x0,0xadf000
        0xA18FDC: 0x9113E000,  # add x0,x0,#0x4f8
        # x25 is the gpio_chip address (x26+8).
        0x3BF9B4: 0x91002359,
        # This zero pair is [gpio_chip+0x60,+0x68].  +0x68 is set_config.
        0x3BF9D4: 0xA9067F3F,
        # Callback stores use x26-relative addresses, hence chip offset -8.
        0x3BF9F4: 0xF9002340,  # chip+0x38 = direction_input
        0x3BF9FC: 0xF9002740,  # chip+0x40 = direction_output
        0x3BFA04: 0xF9002B40,  # chip+0x48 = get
        0x3BFA10: 0xF9003340,  # chip+0x58 = set
        # Registration gets x25 unchanged; other arguments are zero.
        0x3BFB20: 0xAA1903E0,
        0x3BFB24: 0xD2800003,
        0x3BFB28: 0xD2800002,
        0x3BFB2C: 0xD2800001,
        # direction_input performs MMIO read/modify/write and returns zero.
        0x3BFFC8: 0xF8217883,
        0x3C0000: 0xB90002B3,
        0x3C000C: 0x52800000,
        0x3C001C: 0xD65F03C0,
    }
    for off, expected in words.items():
        require(u32(data, off) == expected, (hex(off), hex(u32(data, off)), hex(expected)))


def main() -> None:
    image = IMAGE.read_bytes()
    raw_index = INDEX.read_bytes()
    raw_meta = META.read_bytes()
    require(sha(image) == IMAGE_SHA, "Image hash")
    require(sha(raw_index) == INDEX_SHA, "export index hash")
    require(sha(raw_meta) == META_SHA, "metadata hash")
    require(len(image) == 11_786_752, "Image size")

    index = json.loads(raw_index)
    require(index["source_sha256"] == IMAGE_SHA, "index source binding")
    ex = exports(index)
    require(ex["__platform_driver_register"] == 0x494B98, "platform register export")
    require(ex["gpiochip_add_data_with_key"] == 0x3C6138, "gpiochip register export")
    require(ex["gpiod_set_transitory"] == 0x3C22B0, "transitory export")
    require(ex["gpiochip_generic_config"] == 0x3C0E88, "generic config export")

    # Exact platform_driver object and built-in binding material.
    require(u64(image, PLATFORM_DRIVER + 0x00) == LINK_BASE + 0x3BF6F8, "probe pointer")
    require(u64(image, PLATFORM_DRIVER + 0x08) == LINK_BASE + 0x3BF688, "remove pointer")
    require(u64(image, PLATFORM_DRIVER + 0x28) == LINK_BASE + 0x8F1FC8, "driver name pointer")
    require(u64(image, PLATFORM_DRIVER + 0x50) == LINK_BASE + OF_MATCH, "of_match pointer")
    require(cstr(image, 0x8F1FC8) == "sdp-pinctrl-v2", "driver name")
    require(cstr(image, OF_MATCH + 0x40) == "samsung,sdp-pinctrl-v2", "compatible")
    require(image[OF_MATCH:OF_MATCH + 0x40] == bytes(0x40), "of_match name/type prefix")

    # The init function passes the exact driver object to the exported core.
    require(bl_target(image, 0xA18FE0) == ex["__platform_driver_register"], "driver registration call")
    require(bl_target(image, 0x3BFB30) == ex["gpiochip_add_data_with_key"], "gpiochip registration call")

    for (lo, hi), expected in SLICE_HASHES.items():
        require(sha(image[lo:hi]) == expected, (hex(lo), hex(hi)))
    check_words(image)

    # Live metadata binds the relevant platform device to this exact driver
    # name/compatible; it is not a live hash of kernel text.
    meta = json.loads(raw_meta)
    require(meta["authenticated"] is True and meta["uid"] == 0 and meta["euid"] == 0,
            "metadata authentication")
    require(len(meta["commands"]) == 1, "metadata command count")
    cmd = meta["commands"][0]
    require(cmd["exit_code"] == 0 and cmd["timed_out"] is False and cmd["stderr"] == "",
            "metadata command result")
    out = cmd["stdout"]
    for required in (
        "/sys/bus/platform/drivers/sdp-pinctrl-v2",
        "/sys/devices/platform/soc/4630000.pinctrl",
        "DRIVER=sdp-pinctrl-v2",
        "OF_COMPATIBLE_0=samsung,sdp-pinctrl-v2",
    ):
        require(required in out, ("missing metadata", required))

    print("PASS sdp-pinctrl-v2 paired-Image callback proof")
    print("platform_driver=0xadf4f8 probe=0x3bf6f8 gpiochip_register=0x3bfb30")
    print("gpio_chip.set_config(+0x68)=NULL at registration")
    print("direction_input=0x3bff70 (MMIO RMW); get=0x3c00e0")
    print("scope=offline paired Image; not live-text proof")


if __name__ == "__main__":
    main()
