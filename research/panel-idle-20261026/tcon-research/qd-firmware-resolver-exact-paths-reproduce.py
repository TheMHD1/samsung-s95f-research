#!/usr/bin/env python3
"""Offline byte/relocation checks for qd-firmware-resolver-exact-paths.md."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
QDF = BASE / "binaries/qdf_tcon.ko"
QDF_SHA256 = "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"
API = BASE / "binaries/tztv_frc_tcon_api.ko"
API_SHA256 = "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6"
API_PATH_WRAPPER_SHA256 = "b0663854680ea2b0e7c4491ec0c7bf9a1e2bf357e0263308aa22d146d908dc28"
ROUTE_METADATA = BASE / "overnight/firmware-route-metadata-20261026a/client.stdout"
ROUTE_METADATA_SHA256 = "a076292b45588add9e671728f973185f97788d7ab668b426db521f548ea82201"
ROOT_METADATA = BASE / "overnight/firmware-resolver-roots-metadata-20261026a/client.stdout"
ROOT_METADATA_SHA256 = "17628f7c724548d20b9886d75d50ab3b2dbdcdca2ff7bf31dd678341ab727cf2"
FACTORY_METADATA = BASE / "overnight/factory-qd-data-metadata-20261026a/client.stdout"
FACTORY_METADATA_SHA256 = "730b84fb929779223e989b7d01e56619bf5531c00605b3ded83b54e8b8e2e5da"
FACTORY_HASHES = BASE / "overnight/factory-qd-data-hashes-20261026a/client.stdout"
FACTORY_HASHES_SHA256 = "4d6a58d152c6cd4dfb31059ba09d336e33bf624299bf26054cea31ccee542897"

TEXT_FILE_OFFSET = 0x80
RODATA_FILE_OFFSET = 0x44220
STRINGS_FILE_OFFSET = 0x47760

FUNCTIONS = {
    "m_get_upgrade_path.factory": (0x4DB0, 108, "537069e091c1cead34cd7ce2bedc711125659a78df2445a55ba3988891bfdebf"),
    "m_get_upgrade_path.table": (0x8C00, 116, "d2c8d27f386844542244b1ab3b8f0486af712cd15f23a5c827e3930ec338a3bf"),
    "m_get_cad_upgrade_file_name": (0x82A8, 540, "d1d91a64e0973f337b179237554d0fe74436632bc73ae37c1524e1ae35edfa59"),
    "m_tcon_flash_upgrade_se": (0x8C78, 968, "c1c426cfbb86e26fa81a2d5eef7e7f51894143df187098d236563d294cd2dac2"),
    "QDFTcon_UpgradeFlashFirmware_se": (0x9200, 444, "0165c6d41f98d2905ab42a1a164ea4dddfe3652933c6ad29764530f2791811f1"),
    "m_get_tcon_fw_file_path": (0x93C0, 620, "3b5349db232ded45b11bd1b2195c7407abbf1ca12922c8a05f0b1362b8a09f07"),
    "QDFTcon_UpgradeFlashData": (0x12C98, 464, "041ae8f52fadd8bb7e2b02c31a44b6a86ab40c6bcf0e170f8ab9291e318a90f0"),
    "QDFTcon_UpgradeFlashDataOtp": (0x12E68, 348, "6a359cbd69bdbffbcf12effe58431581d40e0d7cb6c92e7afcfc89caf5b86cb1"),
    "m_tcon_upgrade_data_cad": (0x13298, 720, "4618554a949d9cb72471e1eaf1e7ff16b2e906842ceb25a986e8343d4d1e1d47"),
    "QDFTcon_UpgradeFlashDataCAD": (0x13568, 152, "ec61b2d0b08192814460a0a16801ef9db00716aa65e8b0c79a17a8264dd8fa51"),
}

ROOTS = tuple(
    f"/opt/media/USBDrive{letter}{suffix}/"
    for letter in "ABCD"
    for suffix in ("", "1", "2", "3", "4")
)

FACTORY_FILES = (
    "F_RSM1_BN9658111C_COMMON.bin",
    "F_RSM1_BN9658112C_COMMON.bin",
    "F_RSM1_BN9659920A_COMMON.bin",
    "F_RSM1_BN9659920B_COMMON.bin",
    "F_RSM1_BN9659932A_COMMON.bin",
    "F_RSM1_BN9659932B_COMMON.bin",
    "F_RSM1_BN9659934A_COMMON.bin",
    "F_RSM1_BN9659934B_COMMON.bin",
    "F_RSM1_BN9660751A_COMMON.bin",
)

FACTORY_FILE_HASHES = {
    "F_RSM1_BN9658111C_COMMON.bin": "b5fd9a19ce23b59ed5e8c8951c36b5ab3f10f24f513377ead9885d0f6a2f043a",
    "F_RSM1_BN9658112C_COMMON.bin": "89af82818de1430b7bd86ea36c219dd4021745e180d30c53abb41c72ffd2c8bf",
    "F_RSM1_BN9659920A_COMMON.bin": "02cc716b603b0b084b97a9d9749ac1f82de868f65d4bb507e82ce63577e08a56",
    "F_RSM1_BN9659920B_COMMON.bin": "5af9dfa525a97f511ebf5c153b75c5657e1ce241992fa3f7850bf2473c762829",
    "F_RSM1_BN9659932A_COMMON.bin": "053e7c0b55100863e55e24b803d9d0466f949512d967856234a13637aae71f9d",
    "F_RSM1_BN9659932B_COMMON.bin": "735d93d2fb050b38dea7b3e47edc562b7043e714933f0d45540b5dbf5a7cad53",
    "F_RSM1_BN9659934A_COMMON.bin": "2e2ec0a105d1575a71a171ad9e5eb5a8563e8b4340c0b5d98d6702038127da89",
    "F_RSM1_BN9659934B_COMMON.bin": "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0",
    "F_RSM1_BN9660751A_COMMON.bin": "aee6240fce4172ffb9e72bcd669800fcbe05c50b8099241da460e4058611143f",
}

STRINGS = {
    ("rodata", 0x2120): b"/opt/media/USBDriveA/",
    ("str", 0x2520): b"/factory_peq/tcon_data/QD/",
    ("str", 0x2668): b"TCON/",
    ("str", 0x3D78): b".bin",
    ("str", 0x0BC8): b"%s%s",
    ("str", 0x0C48): b"SE",
    ("str", 0x0C50): b"%s%s%s",
    ("str", 0x0C58): b"TconFwQd",
    ("str", 0x3C30): b"_PML1_",
    ("str", 0x3C38): b"_COMMON",
    ("str", 0x3C40): b"_OCS1_",
    ("str", 0x3C48): b"_MAIN",
    ("str", 0x3C50): b"_RSP1_",
    ("str", 0x3C58): b"_PTM1_",
    ("str", 0x3C60): b"_RSM1_",
    ("str", 0x3C68): b"%c%s%s%s",
    ("str", 0x41D0): b"TconFwRoseM2",
    ("str", 0x41E0): b"TconFwPontusM3",
    ("str", 0x41F0): b"TconFwPontusML3",
    ("str", 0x4200): b"TconFwOscarS4",
    ("str", 0x4210): b"TconFwOscarS5",
    ("str", 0x4220): b"TconFwPontusML4",
    ("str", 0x4230): b"TconFwRoseM1",
    ("str", 0x8F50): b"OTP",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cstring(data: bytes, offset: int) -> bytes:
    end = data.find(b"\0", offset)
    require(end >= offset, f"unterminated string at {offset:#x}")
    return data[offset:end]


def main() -> None:
    raw = QDF.read_bytes()
    api_raw = API.read_bytes()
    require(sha(raw) == QDF_SHA256, "qdf_tcon hash")
    require(sha(api_raw) == API_SHA256, "tztv_frc_tcon_api hash")
    require(sha(api_raw[0x271D8:0x271D8 + 700]) == API_PATH_WRAPPER_SHA256,
            "API m_tcon_flash_upgrade bytes")
    for magic in (bytes.fromhex("5a5aa5a5"), bytes.fromhex("a5a55a5a")):
        require(magic not in raw and magic not in api_raw,
                f"sampled header magic absent as literal: {magic.hex()}")
    require(sha(ROUTE_METADATA.read_bytes()) == ROUTE_METADATA_SHA256, "route metadata hash")
    require(sha(ROOT_METADATA.read_bytes()) == ROOT_METADATA_SHA256, "root metadata hash")
    require(sha(FACTORY_METADATA.read_bytes()) == FACTORY_METADATA_SHA256,
            "factory metadata hash")
    require(sha(FACTORY_HASHES.read_bytes()) == FACTORY_HASHES_SHA256,
            "factory hashes response hash")

    function_hashes = {}
    for name, (address, size, expected) in FUNCTIONS.items():
        blob = raw[TEXT_FILE_OFFSET + address:TEXT_FILE_OFFSET + address + size]
        require(len(blob) == size and sha(blob) == expected, f"{name} bytes")
        function_hashes[name] = expected

    rodata = raw[RODATA_FILE_OFFSET:RODATA_FILE_OFFSET + 0x3539]
    strings = raw[STRINGS_FILE_OFFSET:STRINGS_FILE_OFFSET + 0xCAEF]
    decoded_roots = []
    for index in range(20):
        record = rodata[0x2120 + index * 255:0x2120 + (index + 1) * 255]
        require(len(record) == 255, f"root record {index} length")
        value = cstring(record, 0).decode("ascii")
        require(record[len(value) + 1:] == b"\0" * (254 - len(value)), f"root record {index} padding")
        decoded_roots.append(value)
    require(tuple(decoded_roots) == ROOTS, "20-root table")

    for (section, offset), expected in STRINGS.items():
        data = rodata if section == "rodata" else strings
        require(cstring(data, offset) == expected, f"string {section}+{offset:#x}")

    symbols = subprocess.run(
        ["readelf", "-Ws", str(QDF)], check=True, capture_output=True, text=True
    ).stdout
    for needle in (
        "00000000000093c0   620 FUNC    LOCAL  DEFAULT    3 m_get_tcon_fw_file_path.isra.0",
        "00000000000001b8    20 OBJECT  LOCAL  DEFAULT   21 m_strModel",
        "00000000000001d0    20 OBJECT  LOCAL  DEFAULT   21 m_strPanelType",
        "000000000000000c     4 OBJECT  LOCAL  DEFAULT   21 m_tcon_type",
        "0000000000000048     4 OBJECT  LOCAL  DEFAULT   21 m_chip_type",
        "000000000000019c     1 OBJECT  LOCAL  DEFAULT   21 m_year_tag",
        "00000000000001a8     4 OBJECT  LOCAL  DEFAULT   21 m_is_monitor",
    ):
        require(needle in symbols, f"symbol: {needle.split()[-1]}")

    disasm = subprocess.run(
        ["aarch64-linux-gnu-objdump", "-dr", str(QDF)],
        check=True, capture_output=True, text=True
    ).stdout
    for needle in (
        "00000000000093c0 <m_get_tcon_fw_file_path.isra.0>",
        "R_AARCH64_ADR_PREL_PG_HI21\t.rodata+0x2120",
        "cmp\tw20, #0x14",
        "bl\t16770 <ft_file_open>",
        "0000000000008c00 <m_get_upgrade_path.isra.0.constprop.0>",
        "R_AARCH64_ADR_PREL_PG_HI21\t.rodata.str1.8+0x2668",
        "0000000000004db0 <m_get_upgrade_path.isra.0.part.0>",
        "R_AARCH64_ADR_PREL_PG_HI21\t.rodata.str1.8+0x2520",
        "bl\t93c0 <m_get_tcon_fw_file_path.isra.0>",
        "00000000000082a8 <m_get_cad_upgrade_file_name.constprop.0>",
        "bl\t2220 <m_i2c_burst_read>",
        "R_AARCH64_ADR_PREL_PG_HI21\t.rodata.str1.8+0x3c60",
        "R_AARCH64_ADR_PREL_PG_HI21\t.rodata.str1.8+0x3c68",
    ):
        require(needle in disasm, f"disassembly landmark: {needle}")

    api_disasm = subprocess.run(
        ["aarch64-linux-gnu-objdump", "-dr", str(API)],
        check=True, capture_output=True, text=True
    ).stdout
    for needle in (
        "0000000000000000 <m_tcon_flash_upgrade.isra.0>",
        "R_AARCH64_ADR_PREL_PG_HI21\ttztv_frc_tcon_ext_cmd",
        "R_AARCH64_LDST64_ABS_LO12_NC\ttztv_frc_tcon_ext_cmd",
        "mov\tw0, #0x9",
    ):
        require(needle in api_disasm, f"API wrapper landmark: {needle}")

    metadata = json.loads(ROUTE_METADATA.read_text())
    require(metadata["authenticated"] is True and metadata["uid"] == metadata["euid"] == 0,
            "route metadata provenance")
    command = metadata["commands"]
    require(len(command) == 1 and command[0]["exit_code"] == 0 and not command[0]["timed_out"],
            "route metadata result")
    stdout = command[0]["stdout"]
    require("TREE_ROWS 6\nLONG_PATHS 0\n" in stdout, "firmware tree inventory")
    require(stdout.count("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855") == 2,
            "empty placeholder hashes")

    roots_metadata = json.loads(ROOT_METADATA.read_text())
    require(roots_metadata["authenticated"] is True and roots_metadata["uid"] == roots_metadata["euid"] == 0,
            "root metadata provenance")
    roots_command = roots_metadata["commands"]
    require(len(roots_command) == 1 and roots_command[0]["exit_code"] == 0
            and not roots_command[0]["timed_out"] and roots_command[0]["stderr"] == "",
            "root metadata result")
    roots_stdout = roots_command[0]["stdout"]
    require("PRESENT /factory_peq/tcon_data/QD\n" in roots_stdout, "factory root present")
    for name in FACTORY_FILES:
        require(roots_stdout.count(f"/factory_peq/tcon_data/QD/{name}\n") == 1,
                f"factory file {name}")
        stem = name.removesuffix(".bin")
        fields = stem.split("_")
        require(fields == ["F", "RSM1", fields[2], "COMMON"] and len(fields[2]) == 10,
                f"CAD filename grammar {name}")
    require(roots_stdout.count("ABSENT_OR_NOT_DIRECTORY /opt/media/USBDrive") == 20,
            "20 removable directories absent")
    require("ROWS 33\nLONG_PATHS 0\n" in roots_stdout, "bounded root inventory")

    factory_metadata = json.loads(FACTORY_METADATA.read_text())
    require(factory_metadata["authenticated"] is True
            and factory_metadata["uid"] == factory_metadata["euid"] == 0,
            "factory metadata provenance")
    factory_commands = factory_metadata["commands"]
    require(len(factory_commands) == 1 and factory_commands[0]["exit_code"] == 0
            and not factory_commands[0]["timed_out"]
            and factory_commands[0]["stderr"] == "", "factory metadata result")
    factory_stdout = factory_commands[0]["stdout"]
    require("FILE_COUNT=9\n" in factory_stdout, "factory metadata file count")
    require(factory_stdout.count("HASH_SKIPPED_SIZE\n") == 9,
            "deliberate first-pass hash skips")
    require(factory_stdout.count(" 5a 5a a5 a5 00 00 00 00") == 9,
            "nine sampled headers")
    for name in FACTORY_FILES:
        row = f"/factory_peq/tcon_data/QD/{name} 5242880 0:0:644\n"
        require(factory_stdout.count(row) == 1, f"factory stat {name}")

    hash_metadata = json.loads(FACTORY_HASHES.read_text())
    require(hash_metadata["authenticated"] is True
            and hash_metadata["uid"] == hash_metadata["euid"] == 0,
            "factory hash provenance")
    hash_commands = hash_metadata["commands"]
    require(len(hash_commands) == 1 and hash_commands[0]["exit_code"] == 0
            and not hash_commands[0]["timed_out"]
            and hash_commands[0]["stderr"] == "", "factory hash result")
    hash_stdout = hash_commands[0]["stdout"]
    for name, digest in FACTORY_FILE_HASHES.items():
        path = f"/factory_peq/tcon_data/QD/{name}"
        require(hash_stdout.count(f"{path} 5242880 10241\n") == 1,
                f"hash stat {name}")
        require(hash_stdout.count(f"{digest}  {path}\n") == 1,
                f"file hash {name}")
    require(len(set(FACTORY_FILE_HASHES.values())) == 9, "nine distinct assets")

    print(json.dumps({
        "status": "PASS",
        "qdf_sha256": QDF_SHA256,
        "api_sha256": API_SHA256,
        "api_path_wrapper_sha256": API_PATH_WRAPPER_SHA256,
        "function_hashes": function_hashes,
        "removable_roots": decoded_roots,
        "factory_root": "/factory_peq/tcon_data/QD/",
        "suffix": ".bin",
        "route_metadata_sha256": ROUTE_METADATA_SHA256,
        "root_metadata_sha256": ROOT_METADATA_SHA256,
        "factory_metadata_sha256": FACTORY_METADATA_SHA256,
        "factory_hashes_response_sha256": FACTORY_HASHES_SHA256,
        "factory_files": list(FACTORY_FILES),
        "factory_file_hashes": FACTORY_FILE_HASHES,
        "factory_file_size": 5242880,
        "sampled_header_magic_le_u32": "0xa5a55a5a",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
