#!/usr/bin/env python3
"""Reproduce the bounded W aggregate arithmetic without target I/O."""

from pathlib import Path
import hashlib
import json
import struct

HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
CAPTURE = HERE / "capture-once"
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
S_REPORT = OVERNIGHT / "ap-exco-helper-inputs-20261027s/ap-exco-helper-inputs.md"
S_VERIFY = OVERNIGHT / "ap-exco-helper-inputs-20261027s/verify-helper-inputs.py"
HOST_HEALTH = OVERNIGHT / "current-host-health-20261027v/host-health.stdout.json"


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, digest):
    raw = path.read_bytes()
    need(sha(raw) == digest, "SHA-256 " + str(path))
    return raw


def u16(raw, offset):
    return struct.unpack_from("<H", raw, offset)[0]


def pair32(raw, offset):
    return u16(raw, offset) | (u16(raw, offset + 2) << 16)


def branch16_target(image, address):
    insn = u16(image, address)
    need(insn & 0xF000 == 0xD000 and insn & 0x0F00 != 0x0F00,
         f"conditional branch {address:#x}")
    displacement = (insn & 0xFF) << 1
    if displacement & 0x100:
        displacement -= 0x200
    return address + 4 + displacement


def cbz_target(image, address):
    insn = u16(image, address)
    need(insn & 0xF500 == 0xB100, f"CBZ/CBNZ encoding {address:#x}")
    return address + 4 + (((insn >> 9) & 1) << 6) + (((insn >> 3) & 0x1F) << 1)


def main():
    package = load(PACKAGE, "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0")
    need(len(package) == 0x500000, "package extent")
    image = package[0x200:0x40200]
    ordinary = load(CAPTURE / "ordinary-ap-exco-prefix.bin",
                    "0f7884892da5714a9adcb97cdc033c4d5b24201b1ac570dabcc6771c01a7e271")
    derived = load(CAPTURE / "derived-ap-exco.bin",
                   "de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0")
    result_raw = load(CAPTURE / "result.json",
                      "83cd349d84ef397074f36c5b80e2cc72ad8b00bbeebae5dae978a21f11935171")
    load(S_REPORT, "17068bd31de065a2720ca027498da41517e5d214e0dd633272ed144c29cabdb6")
    load(S_VERIFY, "ae0d25c648e8b777f3829cd2e13fc563ec5f26cb0514c7a89b542b9bac1283bd")
    host_raw = load(HOST_HEALTH,
                    "cb49debf72ef1270682fbf2850579a1404057d5f82385d189b0bc9349ea0b5c4")
    need((len(ordinary), len(derived)) == (824, 1004), "capture extents")
    result = json.loads(result_raw)
    need(result["ordinary_raw_sha256"] == sha(ordinary) and
         result["derived_raw_sha256"] == sha(derived) and
         result["cleanup"] == "STAGE_ABSENT" and
         result["transport_accepted"] is True and
         result["samples_sequential_not_atomic"] is True, "capture result contract")

    # Pin the complete first helper plus its two summation regions and decision
    # region. These are selected-image VA coordinates; FILE = VA + 0x200.
    slices = {
        (0x2F5D8, 0x2F970): "428c93783eeb93bec0a363d29043bca4c8aecdbf5e7339542ccd5c70ba537b45",
        (0x2F612, 0x2F6BA): "9f65e02cf9ad7f11804aab9b7d05cda5270a5e4002556c13ee5058553c3dd635",
        (0x2F71A, 0x2F804): "fb677d9b85a658b50e0282c55f7c689efd750a4b32672cbceab071f6cefbec85",
        (0x2F794, 0x2F804): "3a6cfd6b4d598f5f274759cdfe369e4bd988d21cbe525566ab6965aa5f84645e",
        (0x2F840, 0x2F882): "15e3f56552e5a635788c1a6a5e26a6f202ef4ca9dfb742b559d0ec324ce84835",
    }
    for (start, end), digest in slices.items():
        need(sha(image[start:end]) == digest, f"helper slice {start:#x}")
    need(struct.unpack_from("<I", image, 0x2F970)[0] == 0x584109A4,
         "three-lane table literal")
    need(image[0x2F658:0x2F66E].hex() ==
         "b4f8ea00c0f10f0503e059f8250006446d1c5545f9dd", "initial lane-0 loop")
    need(image[0x2F79C:0x2F7B2].hex() ==
         "b4f80401c0f10f0503e059f8250006446d1c5545f9dd", "recomputed lane-0 loop")
    need(image[0x2F7E6:0x2F804].hex() ==
         "04f585742680300c6080a780380ce080a4f808804fea18406081a4f58574",
         "three recomputed sum stores")
    need(branch16_target(image, 0x2F720) == 0x2F804 and
         cbz_target(image, 0x2F816) == 0x2F840 and
         branch16_target(image, 0x2F868) == 0x2F870,
         "gate and mature-counter branches")

    fields = {offset: u16(ordinary, offset) for offset in
              (0xCA, 0xCC, 0xCE, 0xD0, 0xD2, 0xD4, 0xD6, 0xD8, 0xDA,
               0xDC, 0xDE, 0xE0, 0xE2, 0xE4, 0xE6, 0xE8, 0xEA, 0xEC,
               0xEE, 0xF0, 0xF2, 0xF4, 0xF6, 0xF8, 0xFA, 0xFC, 0xFE,
               0x100, 0x102, 0x104, 0x106, 0x108, 0x10A, 0x10C,
               0x10E, 0x110, 0x112, 0x114, 0x116, 0x2FC)}
    expected = {
        0xCA: 1, 0xCC: 1, 0xCE: 0, 0xD0: 0xE800, 0xD2: 0x71,
        0xD4: 0xE800, 0xD6: 0x71, 0xD8: 0xE800, 0xDA: 0x71,
        0xDC: 0x0800, 0xDE: 0x7C, 0xE0: 30, 0xE2: 30, 0xE4: 0,
        0xE6: 1, 0xE8: 0, 0xEA: 3, 0xEC: 3, 0xEE: 3, 0xF0: 900,
        0xF2: 6, 0xF4: 6, 0xF6: 6, 0xF8: 0xEDA1, 0xFA: 0x7D,
        0xFC: 0xDB5F, 0xFE: 0x7D, 0x100: 0xDB9A, 0x102: 0x7D,
        0x104: 6, 0x106: 6, 0x108: 6, 0x10A: 62590, 0x10C: 125,
        0x10E: 59261, 0x110: 125, 0x112: 58967, 0x114: 125,
        0x116: 1, 0x2FC: 0,
    }
    need(fields == expected, "captured helper fields")
    p = [pair32(ordinary, offset) for offset in (0xD0, 0xD4, 0xD8, 0xDC)]
    initial = [pair32(ordinary, offset) for offset in (0xF8, 0xFC, 0x100)]
    x = [pair32(ordinary, offset) for offset in (0x10A, 0x10E, 0x112)]
    need(p == [7464960, 7464960, 7464960, 8128512], "P values")
    need(initial == [8252833, 8248159, 8248218], "initial table sums")
    need(x == [8254590, 8251261, 8250967], "recomputed table sums")

    upper = 15 if fields[0xE8] else 14
    initial_lower = [15 - fields[offset] for offset in (0xEA, 0xEC, 0xEE)]
    recomputed_lower = [15 - fields[offset] for offset in (0x104, 0x106, 0x108)]
    need(upper == 14 and initial_lower == [12, 12, 12] and
         recomputed_lower == [9, 9, 9], "live inclusive loop bounds")
    need(fields[0x116] == 1 and [fields[o] for o in (0x104, 0x106, 0x108)] ==
         [fields[o] for o in (0xF2, 0xF4, 0xF6)], "recompute enabled and capped values")

    area = 3840 * 2160
    need(p[0] * 10 == area * 9 and p[1] == p[0] and p[2] == p[0],
         "P0..2 exact 90 percent arithmetic")
    need(p[3] * 50 == area * 49, "P3 exact 98 percent arithmetic")
    condition_terms = [p[index] < x[index] for index in range(3)]
    c0 = fields[0xCC] != 0 and any(condition_terms)  # +ce==0 selects this simpler form.
    f0 = int(c0 and fields[0xE2] >= fields[0xE0])
    f1 = 0 if fields[0xCE] == 0 else None
    predicted_e6 = 0 if fields[0xCA] == 0 else f0 | ((f1 or 0) << 1)
    need(condition_terms == [True, True, True] and c0 and f0 == 1 and f1 == 0 and
         predicted_e6 == fields[0xE6] == 1, "captured first-helper decision")
    need(fields[0x2FC] == 0 and derived[0x3D8] == 1 and
         int(bool((fields[0xE6] & 1) or fields[0x2FC])) == derived[0x3D8],
         "captured derived composite")

    host = json.loads(host_raw)
    stdout = host["commands"][0]["stdout"]
    resolution_line = next(line for line in stdout.splitlines()
                           if "[S_F]BLACK PIXELSHIFT" in line and "de 3840 2160" in line)
    need("[124538.882938]" in resolution_line, "resolution observation timestamp")
    need("[DRM-DP] [HISTOGRAM INP(Y)" in stdout, "separate host histogram diagnostic")

    output = {
        "schema": "ap-exco-captured-aggregate-interpretation-v1",
        "target_operations": 0,
        "capture": {"ordinary_sha256": sha(ordinary), "derived_sha256": sha(derived),
                    "samples_atomic": False},
        "thresholds": {"P0": p[0], "P1": p[1], "P2": p[2], "P3": p[3],
                       "area_3840x2160": area, "P0_P1_P2_area_percent": 90,
                       "P3_area_percent": 98},
        "table_shape": {"base_literal": "0x584109a4", "lanes": 3,
                        "dwords_per_lane": 16, "lane_stride": 64,
                        "initial_inclusive_bounds": [12, 14],
                        "recomputed_inclusive_bounds": [9, 14]},
        "initial_sums": initial,
        "recomputed_X": x,
        "condition_terms_P_lt_X": condition_terms,
        "gate_ca": fields[0xCA], "gate_cc": fields[0xCC], "gate_ce": fields[0xCE],
        "counter_e2": fields[0xE2], "threshold_e0": fields[0xE0],
        "predicted_F0": f0, "captured_e6": fields[0xE6],
        "captured_2fc": fields[0x2FC], "derived_3d8": derived[0x3D8],
        "source_table_contents_captured": False,
        "source_table_producer_or_units_identified": False,
        "histogram_or_content_dependence_proved": False,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
