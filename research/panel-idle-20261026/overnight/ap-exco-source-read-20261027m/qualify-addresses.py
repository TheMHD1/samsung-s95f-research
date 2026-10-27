#!/usr/bin/env python3
"""Reproduce the fixed AP_EXCO source-reader address qualification offline.

This script reads retained local evidence only.  It does not access the TV,
network, USB, device nodes, processes, or firmware configuration.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct


BASE = Path("${S95F_EVIDENCE_ROOT}/panel-idle-20261026")
PACKAGE = BASE / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CURRENT = BASE / "overnight/firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
LIVE_MODE = BASE / "overnight/finite-onset-logger-20261027g/selector-context-after-v6/result.json"
HELPER = BASE / "overnight/managed-usb-ap-exco-source-read"

PACKAGE_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
CURRENT_SHA = "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562"
IMAGE1_SHA = "56bfea112d161a22f5bee8630c81306bf04fa9d8d3d901c6d8e7cdd89c09dfbf"
LIVE_MODE_SHA = "d2c3a49f2bd721eb6a33eed70776689386cf32bacab036459fcff2f16795c703"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact(blob: bytes, start: int, end: int, digest: str, label: str) -> bytes:
    value = blob[start:end]
    need(len(value) == end - start, f"{label}: truncated")
    need(sha256(value) == digest, f"{label}: SHA-256 mismatch")
    return value


def unpack_scatter(data: bytes, source_file: int, size: int) -> tuple[bytes, int]:
    """Exact bounded behavior of the packaged scatter handler VA 0x17c."""
    source = source_file
    out = bytearray()
    while len(out) < size:
        tag = data[source]
        source += 1
        literal_count = tag & 7
        if literal_count == 0:
            literal_count = data[source]
            source += 1
        run_count = tag >> 4
        if run_count == 0:
            run_count = data[source]
            source += 1
        need(literal_count >= 1, "invalid literal count")
        for _ in range(literal_count - 1):
            need(len(out) < size, "literal exceeds output")
            out.append(data[source])
            source += 1
        if tag & 8:
            distance = data[source]
            source += 1
            need(distance != 0 and distance <= len(out), "bad back reference")
            for _ in range(run_count + 2):
                need(len(out) < size, "back reference exceeds output")
                out.append(out[-distance])
        else:
            need(len(out) + run_count <= size, "zero run exceeds output")
            out.extend(b"\0" * run_count)
    return bytes(out), source


def in_extent(start: int, length: int, extent_start: int, extent_length: int) -> bool:
    return start >= extent_start and start + length <= extent_start + extent_length


def main() -> None:
    package = PACKAGE.read_bytes()
    current = CURRENT.read_bytes()
    need(len(package) == 0x500000 and sha256(package) == PACKAGE_SHA, "selected package pin")
    need(len(current) == 0x500000 and sha256(current) == CURRENT_SHA, "current backup pin")
    need(sha256(package[0x40000:0x80000]) == IMAGE1_SHA, "selected image-1 slot")
    need(package[0x40000:0x80000] == current[0x40000:0x80000], "stored image-1 slots differ")

    # Image-1 reset scatter row 0 positively allocates the CPU pointer slot.
    table = exact(package, 0x5D8A4, 0x5D934,
                  "73eaacb3784da627c734f46dceeca569c403209c3e3e969d813f2bf13d09caef",
                  "image-1 scatter table")
    rows = [struct.unpack_from("<4I", table, off) for off in range(0, len(table), 16)]
    need(rows[0] == (0x1D860, 0x20000000, 0x4F8, 0x17C), "scatter row zero")
    pointer_cpu = 0x200002CC
    need(in_extent(pointer_cpu, 4, rows[0][1], rows[0][2]), "pointer slot allocation")
    reset, consumed = unpack_scatter(package, 0x40200 + rows[0][0], rows[0][2])
    need(consumed == 0x5DB5B, "scatter decoder consumed extent")
    need(sha256(reset) == "76bebfc83f8e286d8ae152749a1aa376d0bc8d3f415f2433d9ca6944506e7ef8",
         "scatter reset output")
    need(reset[0x2CC:0x2D0] == b"\0" * 4, "pointer reset value")

    # Pin the dynamic image-1 mapper. It yields 0x470002cc only on the
    # non-0x0a core-tag branch, so this is deliberately not an unconditional
    # alias assertion.
    mapper = exact(package, 0x43284, 0x432A8,
                   "64ef2153ee7053a16b6741c455535147ddb1d247aaf216482b5e46fba7c0f471",
                   "image-1 dynamic mapper")
    need(mapper == bytes.fromhex(
        "014609480268b1f1005f0ad30748814207d20a2a02d101f11450704701f11c50fbe70846"
    ), "mapper bytes")
    pointer_bus_window = 0x470002C0
    need(pointer_bus_window + 0x0C == pointer_cpu + 0x27000000,
         "conditional pointer bus arithmetic")

    # Same-boot local corroboration remains evidence for this narrow candidate
    # mapping only. It cannot promote the entire 0x4700 bank to a CPU alias.
    need(sha256(LIVE_MODE.read_bytes()) == LIVE_MODE_SHA, "same-boot live result pin")
    live = json.loads(LIVE_MODE.read_text())
    need(live["transport_accepted"] is True and live["root_word_raw"] == 0x20010000,
         "same-boot root anchor")
    need(live["raw_sha256"] ==
         "c58a20a4147d7b09bfe560456cb65bfce1462fdc5aefcfc50b80e3f5927765c9",
         "same-boot mode-window hash")
    need(live["alternate_raw_sha256"] ==
         "2efca8a0f734277a3df0351751a2ec11d33d20423983381f5068299289fc308a",
         "same-boot candidate-window hash")

    # Selected AP_EXCO table row and two contiguous CPU allocations.
    row_file = 0x3CCBC + 10 * 0x1C
    row = struct.unpack_from("<7I", package, row_file)
    expected_row = (0x3DD8C, 0x2000FF14, 0x33A, 0x2001024E, 0x1200,
                    0x1B0000, 0x1B0400)
    need(row == expected_row, "AP_EXCO mapping row")
    need(sha256(package[row_file:row_file + 0x1C]) ==
         "e3d967a7b74ce674f6c10d2b5c1f945913b1381baa5ac50ad5aec6e4c370713d",
         "AP_EXCO row hash")
    need(row[1] + row[2] == row[3], "AP_EXCO allocations contiguous")

    # Pin metadata and packaged comparison payloads. These are not live-state
    # or active-bank claims.
    exact(package, 0x85E00, 0x86000,
          "dad4caf149769f0b363a11231267d73752802a3bd7484bd720562bbaa7be1cd8",
          "AP_EXCO metadata")
    first_payload = exact(package, 0x182200, 0x182200 + row[2],
                          "c50e438b4882c04e62542fa718cda662b56c3ea0930e20d54944a949e2e3afbf",
                          "AP_EXCO first payload")
    second_payload = exact(package, 0x182600, 0x182600 + row[4],
                           "5000ce2a135b4b463505a32cf5b525916605b32c21a20de4bd91607d4b839761",
                           "AP_EXCO second payload")

    # Image-1 startup explicitly passes selector zero through the lookup body,
    # selecting +0x25000000 for the AP_EXCO CPU destination. Pin its complete
    # lookup/mapping body and the ordinary slot writer/getter chain.
    lookup = exact(package, 0x40200 + 0x1BB74, 0x40200 + 0x1BD4A,
                   "9297113c033fee2008a35f991c436e798cb1315114f09272fc37e097b7cebb54",
                   "AP_EXCO lookup/mapping body")
    need(len(lookup) == 0x1D6, "lookup body extent")
    need(package[0x40200 + 0x1BD4C:0x40200 + 0x1BD54] == b"AP_EXCO\0",
         "startup context key")
    need(struct.unpack_from("<I", package, 0x40200 + 0x1BD5C)[0] == pointer_cpu,
         "pointer-slot literal")
    need(package[0x40200 + 0x1BCE6:0x40200 + 0x1BCEA].hex() == "1d490860",
         "pointer-slot store")
    need(package[0x40200 + 0x38E8:0x40200 + 0x38F4].hex() ==
         "0148006870470000cc020020", "pointer-slot getter")

    source_base_bus = row[1] + 0x25000000
    source_tail_bus = source_base_bus + 0x3CC
    need(source_base_bus == 0x4500FF14, "mapped AP_EXCO base")
    need(source_tail_bus == 0x450102E0, "mapped AP_EXCO tail window")
    need(in_extent(source_base_bus, 16, 0x4500FF14, row[2]), "base window allocation")
    need(in_extent(source_tail_bus, 32, 0x4501024E, row[4]), "tail window allocation")
    need(source_tail_bus + 0x0C == source_base_bus + 0x3D8, "tail field offset")

    first_compare = first_payload[:16]
    tail_compare = second_payload[0x92:0xB2]
    need(sha256(first_compare) ==
         "9d34149fbd1fe777eb238799054c8cbfbce372255f219f8740838def9bfd02db",
         "base comparison window")
    need(sha256(tail_compare) ==
         "f4eec86c76db591f12c003fc318c76418e9455c10f10ad2c40acf0b21010814b",
         "tail comparison window")
    need(tail_compare[0x0C] == 0x14, "packaged +3d8 comparison byte")

    geometries = [
        (0x101, pointer_bus_window, 32, "01010000c002004720000000"),
        (0x101, source_base_bus, 16, "0101000014ff004510000000"),
        (0x101, source_tail_bus, 32, "01010000e002014520000000"),
    ]
    for target, address, length, expected in geometries:
        need(struct.pack("<III", target, address, length).hex() == expected,
             "fixed request header")

    program = (HELPER / "Program.cs").read_text()
    for _, _, _, header in geometries:
        need(header.upper() in program, "helper header does not match qualification")

    print(json.dumps({
        "schema": "ap-exco-source-address-qualification-v1",
        "offline_only": True,
        "target_operations": 0,
        "selected_sha256": PACKAGE_SHA,
        "current_backup_sha256": CURRENT_SHA,
        "stored_image1_equal": True,
        "pointer": {
            "cpu_slot": "0x200002cc",
            "allocated": True,
            "bus_window": "0x470002c0",
            "word_offset": 12,
            "expected_word": "0x4500ff14",
            "binding": "conditional-on-returned-pointer-and-local-same-boot-anchors",
            "whole_bank_alias_proved": False,
        },
        "source_windows": [
            {"bus": "0x4500ff14", "length": 16, "allocation_qualified": True},
            {"bus": "0x450102e0", "length": 32, "allocation_qualified": True,
             "object_3d8_offset": 12},
        ],
        "headers": [item[3] for item in geometries],
        "active_bank_proved": False,
        "live_tuple_proved": False,
        "physical_semantics_proved": False,
    }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
