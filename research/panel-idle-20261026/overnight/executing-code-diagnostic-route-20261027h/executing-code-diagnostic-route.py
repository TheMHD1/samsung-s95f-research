#!/usr/bin/env python3
"""Finite offline census for an existing running-code identity diagnostic.

The checker reads only retained local files.  It does not open a target,
device node, network connection, USB interface, controller, or process.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


ROOT = Path("${S95F_EVIDENCE_ROOT}/panel-idle-20261026")
PROFILE = ROOT / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
PROFILE_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"

PINNED_FILES = {
    ROOT / "binaries/libave.so.0.1": "a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777",
    ROOT / "binaries/tztv_frc_tcon.ko": "aefabb5735b8b091c70006833141b9b0602983a9c1dbc182830dca7cf8b45dbd",
    ROOT / "binaries/tztv_frc_tcon_api.ko": "3a34e9507c44f3ca9b7955e92844187a5396e30e3ab7c745bf0296145be3f7c6",
    ROOT / "binaries/qdf_tcon.ko": "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63",
    ROOT / "tcon-research/qd-i2c-read-command-family-census-20261027-checker.py":
        "5c9b06a7cdbd923eab9c3be470bced20d6edd8a532c2f11b59c11e3265240431",
    ROOT / "tcon-research/qd-usb-cdc-rx-consumer-20261027-checker.py":
        "556ece01a08f5571b81ff3c3ee5120785eef62cd56a67f018f0063a1a0e298e5",
    ROOT / "tcon-research/ssb-mode-gate-followup-20261027.py":
        "3231939cf13432cfeb2fa3aac493cc3a3b18e4747d464843b95968b5d23b7ea0",
    ROOT / "tcon-research/qd-usb-ap-rtp-logical-read-route-reproduce.py":
        "e174f6344cdedfe96159381d9778a275917dbdd5ddf595ae8b0a7626dc31284c",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def check_slice(data: bytes, start: int, end: int, expected: str, label: str) -> bytes:
    value = data[start:end]
    need(len(value) == end - start, label + ": truncated")
    need(sha(value) == expected, label + ": SHA-256")
    return value


def sign_extend(value: int, bits: int) -> int:
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def thumb_bl_target(data: bytes, file_offset: int) -> int | None:
    """Decode an image-0 halfword-aligned Thumb-2 BL to linked VA."""
    first, second = struct.unpack_from("<HH", data, file_offset)
    if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000 or not second & 0x1000:
        return None
    s = (first >> 10) & 1
    j1, j2 = (second >> 13) & 1, (second >> 11) & 1
    i1, i2 = 1 ^ (j1 ^ s), 1 ^ (j2 ^ s)
    immediate = sign_extend(
        (s << 24) | (i1 << 23) | (i2 << 22)
        | ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1),
        25,
    )
    linked_call = file_offset - 0x200
    return (linked_call + 4 + immediate) & 0xFFFFFFFF


def callers(data: bytes, target: int, low_va: int = 0, high_va: int = 0x3FE00) -> list[int]:
    return [
        va for va in range(low_va, high_va - 3, 2)
        if thumb_bl_target(data, va + 0x200) == target
    ]


def main() -> None:
    profile = PROFILE.read_bytes()
    need(len(profile) == 0x500000, "profile size")
    need(sha(profile) == PROFILE_SHA, "profile SHA-256")
    for path, digest in PINNED_FILES.items():
        need(sha(path.read_bytes()) == digest, "pinned input changed: " + str(path))

    slices = {
        "i2c_parser": (0x12AC4, 0x12DBE,
            "5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85"),
        "i2c_f3_open": (0x21824, 0x21876,
            "5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe"),
        "i2c_f3_getter": (0x2194C, 0x21FF0,
            "fc3bbd7a16650a34ce0105c0174f6e5099e8f0fc5722844649149016c1cdea07"),
        "i2c_f380_getter": (0x21FF8, 0x220EA,
            "7b7038d870a46b9f897a44d3368618a13a61025ed86a9c5c61b6dccddba23aa0"),
        "i2c_d0": (0x21878, 0x218F2,
            "09a4c7e01bb146e2f7d33d78c59f99da83595b9d73fac3c6bc0388f786923349"),
        "i2c_fe": (0x2212E, 0x221C6,
            "fc1635b96eeda65f2976cf9ba4fea0ed7b40391cc18827040685b5a5ff712f53"),
        "i2c_f7_tx": (0x1F608, 0x1F65C,
            "2ae7a0bb909b54b67268f938d7456961ceb7a60a908794ffe15bc767241f1d51"),
        "usb_vendor_out": (0x28EF0, 0x29124,
            "08ac2b1b519d532452e92428777d04d935f4bbe883d42e06a5456b4a6d5ddb17"),
        "usb_target_validator": (0x29458, 0x295B4,
            "febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234"),
        "usb_cdc_rx_worker": (0x29CFC, 0x29DA2,
            "95f2b8b66c1a603d4d7b0d7868e5c387f0788086efc88be823b516408c725959"),
        "uart_parser_dispatch": (0x171C0, 0x172E0,
            "421faef06466558f0101d6d61002d6b00ffde43603f88088526326f9ba65782c"),
        "console_table": (0x3D334, 0x3D564,
            "1229edb65dbeea426346e033265d01b571df28819c8758d1d835c8e6a160f988"),
        "console_log_handler": (0x1106C, 0x110D0,
            "5e940f18ccb2a289d6e73e3f60444aedec2a0747692f04afd6ba33445f088125"),
        "console_version_leaf": (0x20630, 0x20652,
            "4431fdc7589c78b4ff26ac8d6ffc76432c160fc5169ba7823af3a75a5bcdf8bb"),
        "image0_fault_handler": (0x12270, 0x1234E,
            "68a9505a12f574d00a492ed5271eba8772e29a704e0ad9a37abf855b5dbb99ae"),
        "image1_fault_handler": (0x44244, 0x44322,
            "e5bc68c4d28bed7e33f6bb40c5ee662748d6b4c2e44745ba02c8bcadd7e519d4"),
        "mks_crc_validator": (0xCD74, 0xCDBC,
            "f645ed9572821abdc39aa9a18f11e5141c1d5cc73dd9ef2e3ecc608cee73d32c"),
    }
    for label, (start, end, digest) in slices.items():
        check_slice(profile, start, end, digest, label)

    # The local-UART command table has 19 handlers followed by END_TABLE.
    expected_console = [
        ("model?", 0x11179), ("bin?", 0x10F0D), ("bin", 0x11719),
        ("param?", 0x1121D), ("param", 0x11A75), ("ELV?", 0x11125),
        ("CURRENT?", 0x110FD), ("TEMP?", 0x2769D), ("TIME?", 0x11155),
        ("RTDBG", 0x11E39), ("RTDBG?", 0x11585), ("TCDBG", 0x11F7D),
        ("LOG", 0x10E6D), ("fab", 0x11A05), ("fab?", 0x10E05),
        ("test", 0x11FE5), ("RT_EN", 0x1163D), ("RTCFG", 0x11E35),
        ("RTCFG?", 0x10E69), ("END_TABLE", 0),
    ]
    console = []
    for index in range(20):
        row = profile[0x3D334 + index * 28:0x3D334 + (index + 1) * 28]
        name = row[:12].split(b"\0", 1)[0].decode("ascii")
        handler = struct.unpack_from("<I", row, 24)[0]
        console.append((name, handler))
    need(console == expected_console, "console table rows")

    # LOG's VERSION leaf constructs bytes 03 03 04 on its stack and returns
    # numeric 0x040303.  It neither reads memory nor calls a checksum routine.
    need(profile[0x110D4:0x1110C] == (
        b"CLEAN\0\0\0INDEX\0\0\0LOG %s %d\n\0\0VERSION\0"
        b"LOG %s %d.%d.%d\n\0\0\0\0"
    ), "LOG subcommand/format strings")
    version_leaf = profile[0x20630:0x20652]
    need(version_leaf == bytes.fromhex(
        "08b503208df800008df8010004208df80200bdf8001008469df8021040ea0140"
        "08bd"
    ), "hard-coded console version leaf")
    need(callers(profile, 0x20430) == [0x10EB0], "console version leaf callers")

    # Vector index 3 is HardFault.  These handlers load stacked +0x18 as PC,
    # format it, then loop forever; they are not normal read handlers.
    image0_vector = [struct.unpack_from("<I", profile, 0x200 + 4 * i)[0] for i in range(16)]
    image1_vector = [struct.unpack_from("<I", profile, 0x40200 + 4 * i)[0] for i in range(16)]
    need(image0_vector[3] == 0x12071, "image-0 HardFault vector")
    need(image1_vector[3] == 0x4045, "image-1 HardFault vector")
    pc_text = b"PC [R15] = %x  program counter\n\0"
    need([offset for offset in range(len(profile)) if profile.startswith(pc_text, offset)]
         == [0x12404, 0x443D8], "PC-format string census")
    need(profile[0x1234C:0x1234E] == b"\xfe\xe7", "image-0 fault terminal loop")
    need(profile[0x44320:0x44322] == b"\xfe\xe7", "image-1 fault terminal loop")

    # The only direct users of generic CRC helper VA 0x2e6c4 are the two
    # header/payload calls within the Mks buffer validator.  That validator
    # has one caller, in the stored/container acquisition path.
    need(callers(profile, 0x2E6C4) == [0xCB80, 0xCBA2], "generic CRC callers")
    need(callers(profile, 0xCB74) == [0xCC54], "Mks CRC validator callers")
    need(callers(profile, 0xCC04) == [0x56E4], "Mks acquisition validator callers")
    need(profile.find(b"Mks : HEADER CRC %x %x MISMATCH\n\0") == 0xCDC0,
         "Mks header CRC text")
    need(profile.find(b"Mks : DATA CRC %x %x MISMATCH\n\0") == 0xCDE4,
         "Mks data CRC text")

    # A second displayed checksum belongs to a configuration dataset loaded
    # by VA 0x176b4; it is not a whole-image or executing-text digest.
    need(profile.find(b"Checksum : %04x\n\0") == 0x175A4, "config checksum text")
    need(callers(profile, 0x1732C) == [0x176DC], "config checksum formatter callers")

    # The CDC implementation still has no direct edge to local-UART parser,
    # dispatcher, or ring producer.  The sole generic-reader edge is the
    # separately classified TCDATA sampler.
    for target in (0x16FC0, 0x17084, 0x21084):
        need(callers(profile, target, 0x27E00, 0x2BE00) == [],
             "CDC-to-UART edge: " + hex(target))
    need(callers(profile, 0x637C, 0x27E00, 0x2BE00) == [0x2A2F8],
         "CDC-area generic reader census")

    result = {
        "status": "diagnostic_route_gap",
        "offline_only": True,
        "target_operations": 0,
        "profile_sha256": PROFILE_SHA,
        "finite_surfaces": {
            "i2c": {
                "families": ["F3", "D0", "FE", "F7"],
                "running_code_crc_pc_or_fingerprint": False,
                "identity_output": "FE profile/storage-derived fields only",
            },
            "local_uart_console": {
                "handler_rows": 19,
                "commands": [name for name, _ in console[:-1]],
                "version_result": "3.3.4 (hard-coded 0x040303)",
                "running_code_crc_pc_or_fingerprint": False,
            },
            "usb_cdc": {
                "direct_rx_to_uart_dispatch_edge": False,
                "running_code_crc_pc_or_fingerprint": False,
            },
            "usb_vendor": {
                "target_0x101": "caller-addressed direct memory; requires qualified address",
                "target_0x203": "eMMC storage bytes; not executing-text identity",
                "address_free_running_code_identity_operation": False,
            },
            "fault_pc_formatter": {
                "image0_vector": "0x12071",
                "image1_vector": "0x4045",
                "only_on_exception": True,
                "terminal_infinite_loop": True,
                "normal_read_diagnostic": False,
            },
            "crc_routines": {
                "mks": "supplied header/payload buffer validation",
                "config": "configuration dataset display",
                "executing_text_input": False,
                "read_dispatch_binding": False,
            },
            "host_qdf_debug": {
                "input_helper": "fixed 0x99 exit",
                "public_read_transport": False,
                "running_code_crc_pc_or_fingerprint": False,
            },
        },
        "existing_host_abi": {
            "qdf_operation_19": "finite I2C command read; no identity selector recovered",
            "usb_12_byte_header": "target/address/length; target0x101 still needs code bus address",
        },
        "existing_address_free_route": None,
        "candidate_future_request": None,
        "reason": (
            "finite recovered read/diagnostic handlers expose profile fields, fixed status, "
            "stored bytes, caller-addressed memory, or exception-only PC output; none "
            "computes or reports an address-free fingerprint of currently executing image-1 code"
        ),
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
