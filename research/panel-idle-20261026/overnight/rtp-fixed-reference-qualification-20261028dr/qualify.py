#!/usr/bin/env python3
"""Read retained host files, verify source anchors, emit qualification metadata only."""
import hashlib
import json
import re
import struct
from pathlib import Path
from reference_model import window, amplitude_candidates, lane_from_x

D = Path(__file__).resolve().parent
B = D.parent
P = B / "firmware-rtp-producer-20261028df/private/official-selected-package.bin"
PACKAGE_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
checks = 0


def need(ok, message):
    global checks
    checks += 1
    if not ok:
        raise ValueError(message)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run():
    blob = P.read_bytes()
    need(len(blob) == 5242880 and sha(blob) == PACKAGE_SHA, "exact selected official asset")
    image = blob[0x40200:0x60200]
    retained = [
        B / "onset-trial-20261028cb/operand-analysis/unpacker-with-literals.disasm.txt",
        B / "onset-trial-20261028cb/operand-analysis/difference-with-literals.disasm.txt",
        B / "onset-trial-20261028cb/operand-analysis/all-formatter-with-literals.disasm.txt",
        B / "firmware-rtp-producer-20261028df/producer-pointer-disassembly.txt",
        B / "firmware-rtp-producer-20261028df/cross-core-slg-disassembly.txt",
    ]
    anchors = {}
    for path in retained:
        for line in path.read_text().splitlines():
            match = re.match(r"^([0-9a-f]{8}) ([0-9a-f]{4,8})\s+(.*)$", line)
            if not match:
                continue
            address = int(match[1], 16)
            # This retained file also contains IMAGE0 sections with its own VA space.
            if path.name == "cross-core-slg-disassembly.txt" and not 0x1BB74 <= address < 0x1BBC4:
                continue
            raw = bytes.fromhex(match[2])
            need(image[address:address + len(raw)] == raw, "retained disassembly byte match")
            anchors[address] = {"va": hex(address), "bytes_hex": raw.hex(),
                                "instruction": match[3], "retained_path": str(path.relative_to(B))}
    selected = [0xbd58, 0xbe3a, 0xbe3e, 0xbe42, 0xbe46, 0xbe4a, 0xbe4e,
                0xbe5c, 0xbe6c, 0xbe6e, 0xbe72, 0xbe76, 0xbe80, 0xbe84,
                0xbed4, 0xbed6, 0xbedc, 0xbf0c, 0xbf0e, 0xbf18,
                0xbf3c, 0xbf3e, 0xbf40, 0xbf44, 0xbf48, 0xbf5a,
                0xbf8a, 0xbf8c, 0xbf90, 0xbf98, 0xbf9a, 0xbf9e, 0xbfa2, 0xbfa6, 0xbfa8,
                0xbbc0, 0xbbc2, 0xbbc4, 0xbc20, 0xbc24, 0xbc38,
                0xbcda, 0xbcde, 0xc652, 0xc654, 0xc656, 0xc658, 0xc666,
                0xb82c, 0xb830, 0xb836, 0xb83a, 0xb848, 0xb84a, 0xb84c,
                0xb856, 0xb858, 0xb85c, 0xb85e, 0xb862, 0xb870, 0xb872, 0xb874,
                0xb888, 0xb88a, 0x1c134, 0x1c13a, 0x1c144, 0x1c14c, 0x1c150,
                0x1c152, 0x1c15a, 0x1c15c, 0x1c15e, 0x1c17e, 0x1c186, 0x1c188, 0x1c18a,
                0x1bba8, 0x1bbb2, 0x1bbb4]
    need(all(a in anchors for a in selected), "all decisive source anchors available")
    literals = {0xb8a0: 0x20015000, 0xb8a4: 0x20015F10, 0xb89c: 0x200004C4,
                0xb898: 0x20000498, 0xc888: 0x200004C0, 0xc04c: 0x200004A6,
                0x1c1a8: 0x20015000, 0x1c1ac: 0x20015F10, 0x1bbc0: 0x20020000}
    for address, expected in literals.items():
        need(struct.unpack_from("<I", image, address)[0] == expected, "literal " + hex(address))
    # Fresh disassembly of memcpy entry and both load/store paths checked separately.
    memcpy_anchors = {0x70c: "032a", 0x752: "51f8043b", 0x758: "51f804cb",
                      0x75c: "a0e80810", 0x79e: "b1e81850", 0x7a4: "a0e81850"}
    for address, raw in memcpy_anchors.items():
        need(image[address:address + len(raw) // 2].hex() == raw, "raw copy anchor")
    capture = B / "volatile-limit-trial-20261028dk/record-fault-01"
    names = ("M", "C", "X", "Y", "RGB", "B", "Diff")
    captured = {name: (capture / (name + ".bin")).read_bytes() for name in names}
    m, c = captured["M"], captured["C"]
    need(len(m) == 68 and len(c) == 16, "retained metadata sizes")
    u16 = lambda raw, offset: struct.unpack_from("<H", raw, offset)[0]
    xbase = u16(m, 0x20)
    need(xbase == 0 and u16(m, 6) == 2880 and u16(m, 8) == 1920, "actual packing geometry/xbase")
    need(struct.unpack_from("<3H", c) == (2160, 1920, 2880), "actual context geometry")
    need(all(len(captured[n]) == 96 for n in names[2:]), "all five arrays exact size")
    rows = list(zip(*(struct.unpack("<48H", captured[n]) for n in names[2:])))
    recovered = {}
    for x, y, rgb, b, diff in rows[:41]:
        need(y == 2159 and rgb == 0 and b < 500 and diff > 500, "candidate prefix")
        a = amplitude_candidates(b, diff)
        need(len(a) == 1, "unique conditional 12bit A")
        lane = lane_from_x(x, xbase)
        recovered.setdefault(x, set()).add(a[0])
        need(lane == x and all(v <= 4095 for v in a), "lane mapping")
    expected = {570: 1861, 571: 1861, 622: 550, 623: 550,
                624: 3052, 625: 3052, 632: 1718, 633: 1718}
    need(recovered == {x: {a} for x, a in expected.items()}, "conditional stable A by coordinate")
    windows = [window(k, n) for n in (104, 120) for k in ("top", "bottom")]
    ranges = [("packing", 0xbd58, 0x2d8), ("formatter", 0xc5d0, 0x2d4),
              ("comparator", 0xbbbc, 0x172), ("dispatch", 0xb7ec, 0xbc),
              ("snapshot_writer", 0x1c12c, 0x84), ("raw_copy", 0x70c, 0xee),
              ("mode1_alias", 0x1bb9c, 0x28)]
    return {"schema": "dr-fixed-reference-qualification-v1", "accepted_host_static_checks": True,
            "checks": checks, "target_operations": 0, "network_operations": 0,
            "status": "source-qualified windows; no fixed reference target capture yet",
            "whole_live_image_attested": False, "historical_fixed_branch_proven": False,
            "source": {"package_sha256": PACKAGE_SHA, "package_bytes": len(blob),
                       "image": 1, "file_offset_formula": "VA+0x40200",
                       "retained_disassembly_inputs": [{"path": str(p.relative_to(B)),
                                                        "sha256": sha(p.read_bytes())} for p in retained],
                       "ranges": [{"label": n, "va": hex(a), "file_offset": hex(a + 0x40200),
                                   "bytes": z, "sha256": sha(image[a:a + z])} for n, a, z in ranges],
                       "anchors": [anchors[a] for a in selected],
                       "literals": [{"va": hex(a), "value": hex(v)} for a, v in literals.items()],
                       "raw_copy_anchors": {hex(a): v for a, v in memcpy_anchors.items()}},
            "windows": windows, "candidate_rows": 41, "captured_xbase": xbase,
            "conditional_reconstructed_A": expected,
            "inputs": [{"path": str((capture / (n + ".bin")).relative_to(B)),
                        "bytes": len(raw), "sha256": sha(raw)} for n, raw in captured.items()]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
