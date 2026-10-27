#!/usr/bin/env python3
"""Offline checks for qd-ssb-readback-acquisition-boundary.md.

This checker reads only retained local artifacts and disassembles the copied
module.  It does not open a device node, issue an ioctl, load a module, or
construct a controller transaction.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "overnight/sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko"
COPY_MANIFEST = ROOT / "overnight/sdp-pqe-frc-provider-copy-20261026a/manifest.json"
DEVICE_METADATA = ROOT / "overnight/ssb-device-metadata-20261026a/client.stdout"
REGISTRATION_METADATA = ROOT / "overnight/ssb-registration-metadata-20261026a/client.stdout"

MODULE_SHA = "1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4"
COPY_MANIFEST_SHA = "54cc98708203cee3778ba329ab8e2219c91fcb4fc82eb9f3076f283fdaad2f4d"
DEVICE_METADATA_SHA = "a306d32dfa3dfd1e214fbcb22625bff5ade0d26957cbdf6e2516a26b2f759952"
REGISTRATION_METADATA_SHA = "2807922e63b27c2aef8d9b3ad9c9b5eb3b20a49f5d6e2808928784b6bff48351"

# Section, offset, size, exact function-byte SHA-256.
FUNCTIONS = {
    "_ssb_init_func": (".text", 0x573E8, 272, "1fb8e07d0e19581ac4288c5d02f67bc33ed4191d5ab6a953b4360a7ed60da8e0"),
    "tcon_read_fw_data": (".text", 0x588B8, 392, "f1c7532c75eaf0c1bdd0f9c864d12d3f03b68219e51442a71af21d447e75231b"),
    "tcon_read_backup_data": (".text", 0x58A68, 776, "44588f4b9831a2b9f87f390bb294bdc9194bfaff4ab106c1a118d40f7c056d04"),
    "tcon_restore_backup_data": (".text", 0x58DC8, 844, "ee25c0d85f4b2bfd30a6f7144e52cd53c6bb9a7adf6c5b9e2dbf6c5e0359b05d"),
    "ssb_ioctl": (".text", 0x591A8, 196, "82ed53a7b15f665257fd40a0855808b2bb9851d6aa1f25581983fa58b129dc84"),
    "ssb_do_read_io": (".text", 0x59290, 388, "cde4a51e9da347b97f05061de4dcdde0d880daaa7964c9feafaacbc2072e1adc"),
    "ssb_read": (".text", 0x597B0, 1016, "1cb6459ded7b794e8376c50b9ac9e030cd460ba274974a71600022e26124ba91"),
    "ssb_open": (".text", 0x5A0D0, 536, "f9c0d13b752037828a497bcf8c524c16dbe0af06f0d9cb4c6e97b308f85ebfb4"),
    "ssb_probe": (".text", 0x5A3D0, 1460, "4c6c75095f20441d2f0498a3c6424547c4ea8078d413c75833d5f89ba5b02175"),
    "ssb_release": (".text", 0x5AA78, 260, "f091a46f1d6be4b4eb1171a7fe7d4d12adfd545216c73a60bf208aa60be67c24"),
    "ssb_write": (".text", 0x5ABA8, 1156, "c56f4214239e61ba01fb90ba2ad2d0b5caf156e72bc3b9c0966720b9007328a6"),
    "resolve_usb_symbols": (".text", 0x5B098, 1944, "b848c7dd7e94c95aa93c46c5ee842dc059b4407f68ebe9f3077583d27ffb3bca"),
    "file_write.part.0": (".text.unlikely", 0x2388, 104, "feb9ab932ea4ccd40e82f3a58a88a4f41f1bb4a43f3407045daff8cfa25f07b2"),
    "_read_data": (".text.unlikely", 0x2440, 740, "2fc860d845ca3662587f932a5f68d3c85ee26aeb75061cfb6af0f27da005a21b"),
    "_backup_data": (".text.unlikely", 0x27C0, 176, "6f91f42089233e46bc2c30d58482f11354c9437809808359c4f65f648107651d"),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True)


def disasm(section: str, start: int, stop: int) -> str:
    return run(
        "aarch64-linux-gnu-objdump", "-dr", f"--section={section}",
        f"--start-address={start:#x}", f"--stop-address={stop:#x}", str(MODULE),
    )


def main() -> None:
    blob = MODULE.read_bytes()
    require(len(blob) == 1_015_070 and digest(blob) == MODULE_SHA, "module identity changed")
    require(digest(COPY_MANIFEST.read_bytes()) == COPY_MANIFEST_SHA, "copy manifest changed")
    require(digest(DEVICE_METADATA.read_bytes()) == DEVICE_METADATA_SHA, "device metadata changed")
    require(digest(REGISTRATION_METADATA.read_bytes()) == REGISTRATION_METADATA_SHA,
            "registration metadata changed")

    manifest = json.loads(COPY_MANIFEST.read_text())
    require(manifest.get("accepted") is True, "module copy was not accepted")
    require(manifest.get("size") == len(blob) and manifest.get("sha256") == MODULE_SHA,
            "module copy identity mismatch")

    bases = {".text": 0x80, ".text.unlikely": 0x9E870}
    for name, (section, address, size, expected) in FUNCTIONS.items():
        body = blob[bases[section] + address:bases[section] + address + size]
        require(len(body) == size and digest(body) == expected, f"function changed: {name}")

    syms = run("aarch64-linux-gnu-readelf", "-sW", str(MODULE))
    for name in ("tcon_read_fw_data", "tcon_read_backup_data", "tcon_restore_backup_data"):
        require(re.search(rf"\bFUNC\s+GLOBAL\s+DEFAULT\s+3\s+{name}$", syms, re.M) is not None,
                f"global symbol missing: {name}")
        require(f"__ksymtab_{name}" not in syms and f"__kstrtab_{name}" not in syms,
                f"readback helper unexpectedly exported: {name}")

    reader = disasm(".text.unlikely", 0x2440, 0x2724)
    for needle in (
        "mov\tw1, #0x2", "mov\tw2, #0xc", "bl\t2388 <file_write.part.0>",
        "bl\t0 <kernel_read>", "tbz\tw22, #31", "mov\tw21, #0x0",
        "and\tw3, w3, #0xfffffe00",
    ):
        require(needle in reader, f"_read_data landmark missing: {needle}")
    require(b"/dev/ssb1\0" in blob and b"/dev/ssbs1\0" in blob, "SSB node literals changed")

    firmware = disasm(".text", 0x588B8, 0x58A40)
    require(firmware.count("R_AARCH64_CALL26\t.text.unlikely+0x2440") == 2,
            "firmware read chunk calls changed")
    for needle in ("mov\tx0, #0x2000", "mov\tw1, #0x203", "bl\t0 <memcpy>"):
        require(needle in firmware, f"firmware read landmark missing: {needle}")

    backup = disasm(".text", 0x58A68, 0x58D70)
    for needle in (
        "bl\t573e8 <_ssb_init_func>", "mov\tw1, #0x241", "mov\tw2, #0x1b6",
        "R_AARCH64_CALL26\t.text.unlikely+0x27c0", "cmp\tx27, #0x4fe, lsl #12",
        "mov\tx3, #0xe000", "movk\tx3, #0x4f, lsl #16",
        "movk\tx3, #0x2000, lsl #32",
    ):
        require(needle in backup, f"backup landmark missing: {needle}")

    backup_chunk = disasm(".text.unlikely", 0x27C0, 0x2870)
    require("bl\t2440 <_read_data>" in backup_chunk and "bl\t2388 <file_write.part.0>" in backup_chunk,
            "backup read/write chain changed")

    ioctl = disasm(".text", 0x591A8, 0x5926C)
    for needle in (
        "cmp\tw19, #0xa", "cmp\tw19, #0xb", "bl\t58a68 <tcon_read_backup_data>",
        "bl\t58dc8 <tcon_restore_backup_data>", "mov\tx19, #0x0",
    ):
        require(needle in ioctl, f"ioctl dispatch landmark missing: {needle}")

    # The SSB fops open/release path is also an active USB runtime-PM path.
    # resolve_usb_symbols binds the named kernel helpers to slots +112/+48;
    # open and release invoke those exact slots respectively.
    opener = disasm(".text", 0x5A0D0, 0x5A2E8)
    for needle in ("ldr\tx1, [x23, #112]", "blr\tx1", "cbz\tw0, 5a190"):
        require(needle in opener, f"SSB open runtime-PM landmark missing: {needle}")
    releaser = disasm(".text", 0x5AA78, 0x5AB7C)
    for needle in ("ldr\tx1, [x1, #48]", "blr\tx1"):
        require(needle in releaser, f"SSB release runtime-PM landmark missing: {needle}")

    resolver = disasm(".text", 0x5B098, 0x5B838)
    for needle in (
        "R_AARCH64_ADR_PREL_PG_HI21\t.text+0x5b890",
        "str\tx0, [x19, #48]",
        "R_AARCH64_ADR_PREL_PG_HI21\t.text+0x5b980",
        "str\tx0, [x19, #112]",
    ):
        require(needle in resolver, f"USB symbol resolver landmark missing: {needle}")

    relocs = run("aarch64-linux-gnu-readelf", "-rW", str(MODULE))
    for offset, target in (("1e28", "597b0"), ("1e30", "5aba8")):
        require(re.search(rf"000000000000{offset}\s+.*R_AARCH64_ABS64.*\.text \+ {target}", relocs),
                f"SSB fops relocation changed: {offset}->{target}")
    require(re.search(r"0000000000001e68\s+.*R_AARCH64_ABS64.*\bssb_ioctl \+ 0", relocs),
            "SSB ioctl fops relocation changed")
    for offset, target in (("1e88", "5a0d0"), ("1e98", "5aa78")):
        require(re.search(rf"000000000000{offset}\s+.*R_AARCH64_ABS64.*\.text \+ {target}", relocs),
                f"SSB open/release fops relocation changed: {offset}->{target}")

    # Literal-pointer relocations bind the resolver input at .text+5b890 to
    # usb_autopm_put_interface and .text+5b980 to
    # usb_autopm_get_interface.  The section-relative string offsets resolve
    # to the exact bytes checked below.
    require(re.search(r"000000000005b890\s+.*R_AARCH64_ABS64.*\.rodata\.str1\.8 \+ 5880", relocs),
            "usb_autopm_put_interface resolver relocation changed")
    require(re.search(r"000000000005b980\s+.*R_AARCH64_ABS64.*\.rodata\.str1\.8 \+ 5c60", relocs),
            "usb_autopm_get_interface resolver relocation changed")
    put_name = b"usb_autopm_put_interface\0"
    get_name = b"usb_autopm_get_interface\0"
    require(blob[0xAFD38 + 0x5880:0xAFD38 + 0x5880 + len(put_name)] == put_name,
            "runtime-PM put symbol name changed")
    require(blob[0xAFD38 + 0x5C60:0xAFD38 + 0x5C60 + len(get_name)] == get_name,
            "runtime-PM get symbol name changed")

    # ssb_table begins at .rodata+0x1f20.  The exact first ID is match flags 3,
    # Samsung USB vendor 0x04e8 and product 0x2001 in little-endian storage.
    table = blob[0xAD6C0 + 0x1F20:0xAD6C0 + 0x1F20 + 64]
    require(table[:6] == bytes.fromhex("0300e8040120"), "USB match-table identity changed")

    meta = json.loads(DEVICE_METADATA.read_text())
    require(meta.get("authenticated") is True and meta.get("uid") == meta.get("euid") == 0,
            "device metadata authentication changed")
    require(len(meta.get("commands", [])) == 1, "unexpected metadata command count")
    command = meta["commands"][0]
    require(command.get("exit_code") == 0 and command.get("timed_out") is False,
            "device metadata command failed")
    require(command.get("stderr") == "", "device metadata stderr was nonempty")
    stdout = command.get("stdout", "")
    for line in (
        "ABSENT /dev/ssb1", "ABSENT /dev/ssbs1",
        "ABSENT_CLASS=/sys/class/usbmisc/ssb1",
        "ABSENT_CLASS=/sys/class/usbmisc/ssbs1",
    ):
        require(line in stdout, f"device absence evidence missing: {line}")

    registration = json.loads(REGISTRATION_METADATA.read_text())
    require(registration.get("authenticated") is True
            and registration.get("uid") == registration.get("euid") == 0,
            "registration metadata authentication changed")
    require(len(registration.get("commands", [])) == 1, "unexpected registration command count")
    reg_command = registration["commands"][0]
    require(reg_command.get("exit_code") == 0 and reg_command.get("timed_out") is False,
            "registration metadata command failed")
    require(reg_command.get("stderr") == "", "registration metadata stderr was nonempty")
    reg_stdout = reg_command.get("stdout", "")
    for text in (
        "sdp_pqe_frc 598016 0 - Live", "MODULE_SYSFS_PRESENT", "initstate\nlive\n",
        "refcnt\n0\n", "USB_DEVICE=/sys/bus/usb/devices/7-1",
        "idVendor\n04e8\nidProduct\n2001\nproduct\nSTL1 CDC and Bulk\n",
        "manufacturer\nSamsung\nbcdDevice\n0250\nDRIVER\n/sys/bus/usb/drivers/usb\n",
    ):
        require(text in reg_stdout, f"registration/device evidence missing: {text!r}")
    require("\nPRESENT\n" not in reg_stdout, "SSB registration path became present")

    print("PASS qd-ssb-readback-acquisition-boundary: exact offline landmarks match")


if __name__ == "__main__":
    main()
