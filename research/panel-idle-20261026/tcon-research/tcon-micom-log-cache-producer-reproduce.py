#!/usr/bin/env python3
"""Hash-gated offline checks for the sdp_tcon TCON MICOM log surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "binaries/sdp_tcon.ko"
PREFIX = ROOT / "overnight/tcon-firmware-log-prefix.txt"
CAPTURE = ROOT / "overnight/tcon-firmware-log-prefix.json"

EXPECTED = {
    MODULE: "9b7c1cb8e2bb8d11e5465a41fa402e71bd8d15a5dabd6b3d76de98a7a42549ee",
    PREFIX: "39b72938ffc5aec8238417fce72cdd131864040dea137a1cbbc5e3191116e846",
    CAPTURE: "70810157116234fb027d320434f8a4f5ae411d3fc271138706d3d8f2d21fce4a",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    if result.stderr:
        raise RuntimeError(f"unexpected stderr from {args[0]}: {result.stderr}")
    return result.stdout


def require(value: bool, message: object) -> None:
    if not value:
        raise RuntimeError(str(message))


for path, expected in EXPECTED.items():
    require(sha(path) == expected, f"hash mismatch: {path}")

symbols = run("aarch64-linux-gnu-readelf", "-WsW", str(MODULE))
for pattern in (
    r"\b00000000000061b0\s+412\s+FUNC\s+LOCAL\s+DEFAULT\s+3\s+tcon_dbg_tcon_micom_log$",
    r"\b0000000000001660\s+264\s+OBJECT\s+LOCAL\s+DEFAULT\s+15\s+tcon_dbg_tcon_micom_log_fops$",
    r"\b0000000000000df8\s+312\s+FUNC\s+GLOBAL\s+DEFAULT\s+3\s+sdp_tcon_frc_micom_log_out_print$",
    r"\b0000000000000fa0\s+116\s+FUNC\s+LOCAL\s+DEFAULT\s+3\s+sdp_tcon_frc_micom_log_out_func$",
):
    require(re.search(pattern, symbols, re.M) is not None, pattern)

relocs = run("aarch64-linux-gnu-readelf", "-rW", str(MODULE))
require(re.search(r"^0000000000001668\s+.*R_AARCH64_ABS64\s+.*generic_file_llseek \+ 0$", relocs, re.M) is not None, "missing llseek relocation")
require(re.search(r"^0000000000001670\s+.*R_AARCH64_ABS64\s+.*\.text \+ 61b0$", relocs, re.M) is not None, "missing read relocation")
require(re.search(r"^00000000000016d0\s+.*R_AARCH64_ABS64\s+.*simple_open \+ 0$", relocs, re.M) is not None, "missing simple_open relocation")

dis = run("aarch64-linux-gnu-objdump", "-dr", str(MODULE))
for required_line in (
    "c84:\tb942f301 \tldr\tw1, [x24, #752]",
    "c90:\td2a00042 \tmov\tx2, #0x20000",
    "cc8:\t91428281 \tadd\tx1, x20, #0xa0, lsl #12",
    "cd0:\td2a00042 \tmov\tx2, #0x20000",
    "cd8:\tf901be60 \tstr\tx0, [x19, #888]",
    "61c8:\tf941bc17 \tldr\tx23, [x0, #888]",
    "61cc:\t794002f4 \tldrh\tw20, [x23]",
    "61f4:\t94000000 \tbl\t270 <tcon_rpm_dev_tryuse>",
    "6214:\t713ffe9f \tcmp\tw20, #0xfff",
    "621c:\taa1403f8 \tmov\tx24, x20",
    "6280:\tcb130294 \tsub\tx20, x20, x19",
    "6284:\tf13ffe9f \tcmp\tx20, #0xfff",
    "6294:\taa1903f4 \tmov\tx20, x25",
    "6298:\teb00033f \tcmp\tx25, x0",
    "62f0:\taa1803e2 \tmov\tx2, x24",
    "62f8:\t94000000 \tbl\t0 <__arch_copy_to_user>",
    "6260:\t94000000 \tbl\t280 <tcon_rpm_dev_disuse>",
    "6304:\t94000000 \tbl\t280 <tcon_rpm_dev_disuse>",
    "270:\t90000000 \tadrp\tx0, 0 <sdp_tcon_ext_set_frc_remap_status>",
    "278:\tb944cc00 \tldr\tw0, [x0, #1228]",
    "280:\t52800000 \tmov\tw0, #0x0",
    "fbc:\tf941bc01 \tldr\tx1, [x0, #888]",
    "fdc:\t79000422 \tstrh\tw2, [x1, #2]",
):
    require(required_line in dis, required_line)

# Finite direct field-reference census.  Some functions receive adjusted
# structure bases, so this proves only the exact syntactic inventory, not
# whole-program alias absence.
direct_888 = {
    int(m.group(1), 16)
    for m in re.finditer(
        r"^\s*([0-9a-f]+):\s+[0-9a-f]{8}\s+\s*(?:ldr|str)\s+[wx][0-9]+, \[x[0-9]+, #888\]$",
        dis,
        re.M,
    )
}
require(direct_888 == {0x1C4, 0xCD8, 0xDB8, 0xE14, 0xF58, 0xFBC, 0x61C8}, direct_888)

module = MODULE.read_bytes()
text_file_offset = 0x80  # pinned by the whole-file hash and ELF section table
windows = {
    "rpm_gate": (0x270, 0x288, "e3f3994b4ee804507e2a95dbbfa684eb3d7b1a1c631b9e80832c0992bda86b72"),
    "mapping": (0xC84, 0xCFC, "7330b4be09e4dd77023497be3d65b547422ddf05d95e43a16ee5100f3e751403"),
    "log_printer": (0xDF8, 0xF30, "88909b3f6cba694d377bbb8c4af964ea0e6681a7751dcccbd82536c028fc8967"),
    "log_work": (0xFA0, 0x1014, "1193896467422869128dba33adb880b53216ff82226f6dbc2b821e3e4244f60c"),
    "debugfs_read": (0x61B0, 0x634C, "72bbddbffbab8893febe5cfbd3171ef7ff4fd2aad651f36afa3ee36aa6180554"),
}
for name, (start, end, expected) in windows.items():
    got = hashlib.sha256(module[text_file_offset + start:text_file_offset + end]).hexdigest()
    require(got == expected, f"{name} window mismatch")

prefix = PREFIX.read_bytes()
require(len(prefix) == 1405, "prefix size")
require(prefix.startswith(b"RHEA_M_TCON_FW_20250103_1715\n"), "prefix start")
require(prefix.endswith(b"Msgbox ISR out\nS"), "prefix end")
require(prefix.count(b"\n") == 68, "prefix newline count")

capture = json.loads(CAPTURE.read_text())
require(capture["authenticated"] is True and capture["uid"] == capture["euid"] == 0, "capture auth")
require(capture["root_persistence"] == "host-assisted", "capture root persistence")
require(capture["global_system_files_unchanged_at_acquisition"] is True, "capture invariant")
require(len(capture["commands"]) == 1, "capture command count")
command = capture["commands"][0]
require(command["exit_code"] == 0 and command["timed_out"] is False, "capture status")
require("head -c 4096 /sys/kernel/debug/tcon/tcon_micom_log | base64" in command["command"], "capture command")


def modeled_read_sizes(total: int, request: int) -> list[int]:
    """Model only the length-selection CFG proven by the instructions above."""
    pos = 0
    sizes: list[int] = []
    while pos < total and len(sizes) < 32:
        if total <= 0xFFF:
            selected = total
        else:
            remaining = total - pos
            selected = remaining if remaining <= 0xFFF else request
        sizes.append(selected)
        pos += selected
    require(pos >= total, (total, request, sizes))
    return sizes


# A larger single request can exceed the valid length; fixed 4096-byte
# requests cover every representable nonzero length without doing so.
require(modeled_read_sizes(5000, 65536) == [65536], "large-request overcopy model")
for total in range(1, 65537):
    sizes = modeled_read_sizes(total, 4096)
    require(sum(sizes) == total and len(sizes) <= 16, (total, sizes))

print(json.dumps({
    "status": "PASS",
    "module_sha256": EXPECTED[MODULE],
    "debugfs_read": "mapped shared region; no consume/clear in read body",
    "mapped_region": "runtime tcon_info base + 0xa0000, 0x20000 bytes",
    "prefix_bytes": len(prefix),
    "prefix_sha256": EXPECTED[PREFIX],
    "direct_instance_plus_888_references": [hex(x) for x in sorted(direct_888)],
    "safe_read_unit": "4096-byte requests, at most 16 requests",
    "limits": "direct-reference and selected-window proof, not alias-complete firmware producer proof",
}, indent=2, sort_keys=True))
