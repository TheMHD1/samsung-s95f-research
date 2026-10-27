#!/usr/bin/env python3
"""Offline-only verifier for the two AP_EXCO bytes copied by image 1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
BACKUP = OVERNIGHT / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
OBSERVED = OVERNIGHT / "finite-onset-logger-20261027g/selector-context-after-v6/alternate-window.bin"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path, digest: str) -> bytes:
    data = path.read_bytes()
    need(sha256(data) == digest, f"SHA-256: {path}")
    return data


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def thumb_bl_target(data: bytes, address: int) -> int:
    need(len(data) == 4, "BL width")
    first, second = struct.unpack("<HH", data)
    need(first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000,
         f"BL encoding at {address:#x}")
    s = (first >> 10) & 1
    j1 = (second >> 13) & 1
    j2 = (second >> 11) & 1
    i1 = 1 ^ (j1 ^ s)
    i2 = 1 ^ (j2 ^ s)
    value = ((s << 24) | (i1 << 23) | (i2 << 22) |
             ((first & 0x3FF) << 12) | ((second & 0x7FF) << 1))
    if value & (1 << 24):
        value -= 1 << 25
    return address + 4 + value


def direct_callers(image: bytes, target: int) -> list[int]:
    result: list[int] = []
    for address in range(0, len(image) - 3, 2):
        first, second = struct.unpack_from("<HH", image, address)
        if first & 0xF800 != 0xF000 or second & 0xD000 != 0xD000:
            continue
        if thumb_bl_target(image[address : address + 4], address) == target:
            result.append(address)
    return result


def main() -> None:
    package = load(PACKAGE, "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    backup = load(BACKUP, "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562")
    observed = load(OBSERVED, "2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a")
    need(len(package) == len(backup) == 0x500000, "firmware extents")
    need(len(observed) == 16, "saved alternate-window extent")
    image0 = package[0x200:0x40200]

    # The selected AP_EXCO mapping row and the two retained baseline payloads.
    row_file = 0x3CCBC + 10 * 0x1C
    row = struct.unpack_from("<7I", package, row_file)
    expected_row = (0x3DD8C, 0x2000FF14, 0x33A, 0x2001024E,
                    0x1200, 0x1B0000, 0x1B0400)
    need(row == expected_row, "AP_EXCO mapping row")
    need(package[row[0] + 0x200 : row[0] + 0x208] == b"AP_EXCO\0", "AP_EXCO name")
    need(sha256(package[row_file : row_file + 0x1C]) ==
         "e3d967a7b74ce674f6c10d2b5c1f945913b1381baa5ac50ad5aec6e4c370713d",
         "AP_EXCO row slice")
    need(package[0x85E00:0x86000] == backup[0x85E00:0x86000], "retained directory equality")
    for start, size, digest in (
        (0x182200, 0x33A, "c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf"),
        (0x182600, 0x1200, "5000ce2a135b4b463505a32cf5b525916605b32c21a20de4bd91607d4b839761"),
    ):
        need(package[start:start + size] == backup[start:start + size], f"retained payload equality {start:#x}")
        need(sha256(package[start:start + size]) == digest, f"payload SHA-256 {start:#x}")
    need((package[0x18269E], package[0x182200]) == (20, 0), "baseline source pair")
    need((observed[7], observed[8]) == (1, 3), "saved candidate pair")

    # Controller-local text table binds the labels bin and param to their set handlers.
    need(package[0x3D36C:0x3D388] == b"bin\0" + bytes(20) + struct.pack("<I", 0x11719),
         "bin command-table row")
    need(package[0x3D3A4:0x3D3C0] == b"param\0" + bytes(18) + struct.pack("<I", 0x11A75),
         "param command-table row")
    names = b"HandlerQueryBin\0HandlerSetBin\0HandlerQueryParam\0HandlerSetParam\0"
    need(package[0x3D564:0x3D564 + len(names)] == names, "adjacent handler-name strings")

    # Both set handlers are the complete direct-caller set of generic writer VA 0x733c.
    need(direct_callers(image0, 0x733C) == [0x11906, 0x11D52], "generic-writer direct callers")
    need(image0[0x11900:0x1190A].hex() == "710808aa4046f5f719fd", "bin writer call setup")
    need(thumb_bl_target(image0[0x11906:0x1190A], 0x11906) == 0x733C, "bin writer call")
    need(image0[0x11D46:0x11D56].hex() == "079880b2069006aa01212046f5f7f3fa",
         "param one-halfword call setup")
    need(thumb_bl_target(image0[0x11D52:0x11D56], 0x11D52) == 0x733C, "param writer call")
    need(sha256(image0[0x11718:0x1197E]) ==
         "8daeb8b04c6bce8fa2e0890412d28698b35b43b729f31520d3755b304365cf5c",
         "bin set-handler slice")
    need(sha256(image0[0x11A74:0x11DAE]) ==
         "c9108478bf841a5ef0d01fd695fa1bf2c11668c10cc56d8fa2c8754fff1ec568",
         "param set-handler slice")

    # Generic writer row arithmetic. Its fixed table is the same 21-row mapping.
    need(sha256(image0[0x733C:0x73E6]) ==
         "8f8d3ab719d3869d997d6712da77d2a79895b1057d60fa08770831853d4fe9c5",
         "generic configuration writer")
    need(u32(image0, 0x73E8) == 0x3CABC, "writer mapping-table literal")
    need(image0[0x73DC:0x73E2] == bytes.fromhex("641c152cbbd3"), "21-row writer bound")
    need(image0[0x73C2:0x73D8].hex() == "7200c4ebc401074b03eb81014968c8194146f9f74dfb",
         "first-region destination and two-byte-count copy")
    need(image0[0x7386:0x73A2].hex() == "c4ebc401174b03eb8101c9683944abeb0903c81a72004146f9f768fb",
         "second-region destination and two-byte-count copy")

    # A one-word AP_EXCO first-region write has a dedicated selector-zero hook.
    need(sha256(image0[0x73EC:0x7428]) ==
         "b5c77a049af33775dcb207e056527f72fd12fb977af21cb9ce6b42276f5afd12",
         "one-word row hook")
    need(image0[0x742C:0x7433] == b"AP\0\0AP_", "hook string prefix")
    need(image0[0x7430:0x7438] == b"AP_EXCO\0", "AP_EXCO hook key")
    need(direct_callers(image0, 0xC4BC) == [0x741E], "AP_EXCO special-hook direct callers")
    need(sha256(image0[0xC4BC:0xC4F6]) ==
         "322df5e83f263d7afc631f9b8d8efa5d8d6a25fabf7a80ed2e4b2a79dfd569d8",
         "AP_EXCO selector-zero hook slice")
    need(thumb_bl_target(image0[0xC4C4:0xC4C8], 0xC4C4) == 0xE678, "AP_EXCO root getter")
    need(image0[0xE678:0xE680].hex() == "0048704714ff0020", "AP_EXCO getter and root literal")
    need(image0[0xC4E8:0xC4F4].hex() == "012c01d12af050ffa8f80040",
         "selector-zero conditional helper and AP_EXCO+0 halfword store")

    # The second-region logical address is not object offset +3d8: it includes
    # the table's 0x400 logical gap and resolves to physical second +0x9e.
    logical_plus_zero = row[5]
    logical_plus_3d8 = row[6] + (0x3D8 - row[2])
    resolved_plus_3d8 = row[3] + ((logical_plus_3d8 & 0xFFFF) - (row[6] - row[5]))
    need(logical_plus_zero == 0x1B0000, "logical +0")
    need(logical_plus_3d8 == 0x1B049E, "logical +3d8")
    need(resolved_plus_3d8 == row[1] + 0x3D8 == 0x200102EC, "resolved +3d8 destination")

    # The ordinary F300/I2C scalar dispatcher is separate. It has no direct
    # call to either generic configuration writer or AP_EXCO special hook.
    need(sha256(image0[0x2C71C:0x2CF54]) ==
         "9c84175a8a05a888f1b820b155b0cc52e1aaf2cecbc8f2fcd2831b982d9b548d",
         "F300 setter body")
    f300_call_targets = []
    for address in range(0x2C71C, 0x2CF54 - 3, 2):
        first, second = struct.unpack_from("<HH", image0, address)
        if first & 0xF800 == 0xF000 and second & 0xD000 == 0xD000:
            f300_call_targets.append(thumb_bl_target(image0[address:address + 4], address))
    need(0x733C not in f300_call_targets and 0xC4BC not in f300_call_targets,
         "F300 is not the generic AP_EXCO writer route")
    need(f300_call_targets.count(0xE678) == 1, "single AP_EXCO root acquisition in F300 body")
    need(image0[0x2CE2A:0x2CE54].count(bytes.fromhex("a9f80600")) == 2,
         "F300 AP_EXCO direct stores are the separate +6 halfword case")

    result = {
        "schema": "ap-exco-runtime-writer-provenance-v1",
        "target_operations": 0,
        "baseline_pair": [20, 0],
        "saved_candidate_pair": [1, 3],
        "proven_ordinary_writer": {
            "ingress": "controller-local UART command table",
            "handlers": ["bin", "param"],
            "generic_writer_va": "0x733c",
            "ap_exco_plus_0_logical": "0x1b0000",
            "ap_exco_plus_3d8_logical": "0x1b049e",
            "plus_0_special_hook_va": "0xc4bc",
        },
        "named_field_or_setting": None,
        "host_i2c_or_linux_api_binding": False,
        "observed_invocation": False,
        "limitations": [
            "The two retained firmware baselines and saved candidate bytes are offline artifacts.",
            "This proves an ordinary controller-local update route, not that it ran before V6.",
            "No field-level name or value semantics for AP_EXCO+0 or +0x3d8 were recovered.",
            "No USB-CDC-to-UART bridge or Linux/QDF/I2C binding to this generic writer is proved.",
            "Computed or indirect writers outside the pinned paths are not excluded.",
            "No active bank, persistence, protection, return-guard, high-bank or POFLG path was examined.",
        ],
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
