#!/usr/bin/env python3
"""Offline proof of the selected QD image's SSB target-0x203 read path.

This reads only retained local files.  It neither opens USB nor constructs a
live transport command.  Capstone must be supplied through the already-used
offline PYTHONPATH (for example /tmp/tcon-capstone).
"""
from __future__ import annotations

import hashlib
import importlib.util
import struct
from pathlib import Path

from capstone import CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_MCLASS
from capstone import CS_MODE_THUMB, Cs


ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
DECODER = ROOT / "tcon-research/qd-rt-window-reset-output-reproduce.py"
PREFLIGHT = ROOT / "overnight/rt-telemetry-followup-20261027b/usb-one-chunk-preflight-metadata.txt"
PROFILE_SHA256 = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
DECODER_SHA256 = "fa6e59c24b5a2d91c917c908b4c60b078add9a8ca6815c24ec3e6d55cfe18d02"
IMAGE0_BIAS = 0x200


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def insns(data: bytes, va: int, size: int):
    md = Cs(CS_ARCH_ARM,
            CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN | CS_MODE_MCLASS)
    decoded = list(md.disasm(data[va + IMAGE0_BIAS:va + IMAGE0_BIAS + size], va))
    need(decoded and decoded[0].address == va, "instruction slice did not decode")
    return {i.address: (i.mnemonic, i.op_str, i.bytes.hex()) for i in decoded}


def exact(table, address: int, mnemonic: str, operands: str, raw: str) -> None:
    need(table.get(address) == (mnemonic, operands, raw),
         "instruction changed at 0x%x: %r" % (address, table.get(address)))


def main() -> None:
    data = PROFILE.read_bytes()
    need(len(data) == 0x500000 and sha(data) == PROFILE_SHA256,
         "selected profile identity")

    need(sha(DECODER.read_bytes()) == DECODER_SHA256,
         "scatter decoder identity")
    spec = importlib.util.spec_from_file_location("pinned_scatter_decoder", DECODER)
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)

    # Reset row 0 populates the RAM-resident USB callback table.
    row0 = struct.unpack_from("<4I", data, 0x3E340)
    need(row0 == (0x3E32C, 0x20000000, 0xF4C, 0x17C),
         "scatter row0")
    context, consumed = decoder.unpack(data, row0[0] + IMAGE0_BIAS, row0[2])
    need(consumed == 0x3E961, "scatter row0 consumed endpoint")
    need(sha(context) ==
         "685d8eda90bb3ce7e6210ad0dfe962f65ac3b8e1b2eb1a40962e0e5720d81eb3",
         "scatter row0 output")
    callback_table = struct.unpack_from("<8I", context, 0x58C)
    need(callback_table == (0x2945D, 0x293D1, 0x294FB, 0, 0,
                            0x28B85, 0x28CF1, 0x294F5),
         "vendor callback table")
    core_table = struct.unpack_from("<8I", context, 0x4B8)
    need(core_table == (0x28449, 0x2824D, 0x285C9, 0x282D9,
                        0x282A5, 0x28195, 0x281F1, 0x28561),
         "USB-core callback table")

    preflight = PREFLIGHT.read_bytes()
    need(sha(preflight) ==
         "ac45ca58422861555639eac65dd2fd1b26aba71ffb389753da96292d0cab948c",
         "fresh USB preflight identity")
    need(b"98176.31 367052.09" in preflight and
         b"98176.36 367052.18" in preflight and
         b"FIELD=bConfigurationValue\n1\n" in preflight and
         b"FIELD=power/runtime_status\nactive\n" in preflight and
         preflight.count(b"UNBOUND\n") == 3 and
         b"/dev/bus/usb/007/045" in preflight,
         "fresh USB preflight semantics")

    init = insns(data, 0x2490C, 0x60)
    exact(init, 0x24920, "movs", "r0, #0x82", "8220")
    exact(init, 0x24924, "str", "r0, [r1, #0x14]", "4861")
    exact(init, 0x24926, "movs", "r0, #2", "0220")
    exact(init, 0x24928, "str", "r0, [r1, #0x18]", "8861")
    exact(init, 0x24934, "bl", "#0x284b4", "03f0befd")
    exact(init, 0x2493A, "bl", "#0x284a0", "03f0b1fd")
    exact(init, 0x2495A, "bl", "#0x28b36", "04f0ecf8")

    startup = insns(data, 0x399B0, 0xC0)
    exact(startup, 0x39A16, "bl", "#0x2490c", "eaf779ff")

    accessor = insns(data, 0x284A0, 0x14)
    exact(accessor, 0x284A2, "ldr", "r0, [pc, #8]", "0248")
    exact(accessor, 0x284A4, "str", "r1, [r0]", "0160")
    exact(accessor, 0x284A6, "ldr", "r0, [pc, #8]", "0248")
    exact(accessor, 0x284A8, "bx", "lr", "7047")
    need(u32(data, 0x284AC + IMAGE0_BIAS) == 0x200004B4 and
         u32(data, 0x284B0 + IMAGE0_BIAS) == 0x200004B8,
         "USB-core callback accessor literals")

    broadcaster = insns(data, 0x28448, 0x4A)
    exact(broadcaster, 0x2845C, "ldr", "r0, [r4, #8]", "a068")
    exact(broadcaster, 0x2845E, "ldr", "r0, [r0]", "0068")
    exact(broadcaster, 0x28468, "ldr", "r3, [r0]", "0368")
    exact(broadcaster, 0x2846C, "blx", "r3", "9847")

    class_config = insns(data, 0x2945C, 0x88)
    exact(class_config, 0x29492, "ldr", "r0, [pc, #0x54]", "1548")
    exact(class_config, 0x29496, "str", "r0, [r4, #0x10]", "2061")
    exact(class_config, 0x294C6, "mov.w", "r0, #0x200", "4ff40070")
    exact(class_config, 0x294D0, "mov.w", "r0, #0x6000", "4ff4c040")
    exact(class_config, 0x294DC, "bl", "#0x29500", "00f010f8")
    need(u32(data, 0x294E8 + IMAGE0_BIAS) == 0x20000544 and
         u32(data, 0x294EC + IMAGE0_BIAS) == 0x2026141F and
         u32(data, 0x294F0 + IMAGE0_BIAS) == 0x20000548,
         "class-config pool/cap literals")

    arm = insns(data, 0x29500, 0x34)
    exact(arm, 0x29524, "movs", "r3, #0xc", "0c23")
    exact(arm, 0x2952A, "bl", "#0x7fce", "def750fd")

    completion = insns(data, 0x28CF0, 0x4A0)
    exact(completion, 0x28F50, "ldr", "r0, [r4, #0x10]", "2069")
    exact(completion, 0x28F52, "ldr", "r0, [r0, #8]", "8068")
    exact(completion, 0x28F54, "str", "r0, [r4, #8]", "a060")
    exact(completion, 0x28F56, "ldr", "r0, [r4, #0x10]", "2069")
    exact(completion, 0x28F58, "ldr", "r0, [r0]", "0068")
    exact(completion, 0x28F5A, "str", "r0, [r4, #0xc]", "e060")
    exact(completion, 0x28F5C, "ldr", "r0, [r4, #0x10]", "2069")
    exact(completion, 0x28F5E, "ldr", "r0, [r0, #4]", "4068")
    exact(completion, 0x28F60, "str", "r0, [r4, #4]", "6060")
    exact(completion, 0x28F68, "bl", "#0x29258", "00f076f9")
    # Ordinary header processing forces mode 2, then bypasses all operation
    # dispatch while that exact byte remains 2.  No live packet is modeled.
    exact(completion, 0x28F44, "movs", "r0, #2", "0220")
    exact(completion, 0x28F46, "ldr", "r1, [pc, #0x2a8]", "aa49")
    exact(completion, 0x28F48, "strb", "r0, [r1]", "0870")
    exact(completion, 0x290D6, "ldr", "r0, [pc, #0x118]", "4648")
    exact(completion, 0x290D8, "ldrb", "r0, [r0]", "0078")
    exact(completion, 0x290DA, "cmp", "r0, #2", "0228")
    exact(completion, 0x290DC, "bne", "#0x290e0", "00d1")
    exact(completion, 0x290DE, "b", "#0x28f70", "47e7")
    need(u32(data, 0x291F0 + IMAGE0_BIAS) == 0x20000571,
         "header/dispatch mode-byte literal")
    needle = struct.pack("<I", 0x20000571)
    image0_hits = [i for i in range(0, 0x40000 - 3)
                   if data[i:i + 4] == needle]
    need(image0_hits == [0xF348, 0x28EDC, 0x290EC, 0x293F0],
         "exact image0 mode-byte literal census")
    exact(completion, 0x28FB4, "ldrb", "r0, [r4, #0xc]", "207b")
    exact(completion, 0x28FC0, "and", "r0, r0, #0xef", "00f0ef00")
    exact(completion, 0x28FC4, "str", "r0, [r4, #0xc]", "e060")
    exact(completion, 0x2914E, "ldr", "r0, [r4, #0xc]", "e068")
    exact(completion, 0x29150, "cmp", "r0, #3", "0328")
    exact(completion, 0x29166, "movw", "r0, #0xabcd", "4af6cd30")
    exact(completion, 0x2916A, "str", "r0, [sp]", "0090")
    exact(completion, 0x2916E, "ldr", "r2, [r4, #4]", "6268")
    exact(completion, 0x29172, "ldr", "r3, [r0]", "0368")
    exact(completion, 0x29174, "movs", "r0, #0", "0020")
    exact(completion, 0x29176, "bl", "#0x9bd4", "e0f72dfd")
    # The immediately following instruction consumes no return-status branch.
    exact(completion, 0x2917A, "ldr", "r0, [pc, #0xac]", "2b48")
    need(u32(data, 0x29218 + IMAGE0_BIAS) == 0x20001BC0,
         "response-buffer literal")
    need(u32(data, 0x29228 + IMAGE0_BIAS) == 0x2000054C,
         "bounded-chunk-length literal")

    exact(completion, 0x290E0, "ldr", "r1, [pc, #0x130]", "4c49")
    exact(completion, 0x290E2, "ldr", "r0, [r4, #8]", "a068")
    exact(completion, 0x290E6, "cmp", "r0, r1", "8842")
    exact(completion, 0x290F0, "ldr", "r0, [r4, #8]", "a068")
    exact(completion, 0x290F4, "str", "r0, [r1]", "0860")
    need(u32(data, 0x29214 + IMAGE0_BIAS) == 0x20000548,
         "configured chunk-cap literal")
    row11 = struct.unpack_from("<4I", data, 0x3E340 + 11 * 16)
    need(row11 == (0x3E764, 0x20000F4C, 0x16438, 0x1D8),
         "response-buffer BSS scatter row")
    response = 0x20001BC0
    need(row11[1] <= response and response + 0x6000 <= row11[1] + row11[2],
         "response buffer and maximum chunk are not covered by reset RAM span")

    validator = insns(data, 0x29258, 0x15C)
    exact(validator, 0x29322, "movw", "r1, #0x201", "40f20121")
    exact(validator, 0x2932C, "adds", "r1, r1, #1", "491c")
    exact(validator, 0x29334, "adds", "r1, r1, #1", "491c")
    exact(validator, 0x2933E, "cmp.w", "r0, #0x204", "b0f5017f")

    emmc = insns(data, 0x9BD4, 0xE4)
    exact(emmc, 0x9C44, "ubfx", "r0, r4, #0, #9", "c4f30800")
    exact(emmc, 0x9C54, "ubfx", "r0, r5, #0, #9", "c5f30800")
    exact(emmc, 0x9C90, "lsr.w", "sl, r5, #9", "4fea552a")
    exact(emmc, 0x9C9A, "mov.w", "r0, #0x58000000", "4ff0b040")
    exact(emmc, 0x9CA2, "bl", "#0x16b70", "0cf065ff")

    slices = {
        "vendor_init": (0x24B0C, 0x24B64,
                        "fe0614e38e5ba9a93ea7b9e7f6713407c9f2abdc4fcce28d11448c8baee41ae2"),
        "out_completion": (0x28EF0, 0x29124,
                           "08ac2b1b519d532452e92428777d04d935f4bbe883d42e06a5456b4a6d5ddb17"),
        "target_validator": (0x29458, 0x295B4,
                            "febec20e4653208a48681cf6f82f1f9e13a7b03149e53f6baf5ddf149827c234"),
        "arm_next_header": (0x29700, 0x29734,
                            "19b640cf59ed8e61dbefe6e4d59ce3188f4d20be75e9d8d432bd483ada39561f"),
        "emmc_read": (0x9DD4, 0x9EB8,
                      "7eb2e0e5029fb8ac2c64fe88c207c7922dafbfcc651928dcae21b1a2cef2343b"),
        "emmc_write": (0xA1E8, 0xA22E,
                       "3303ecbaa6a74cc7a25c6420aa9a33aa44ff077807e70c27443bfeb132bf7466"),
        "core_broadcast": (0x28648, 0x28692,
                           "c4f064a989b3b50c08d280832b60792021494ac45e7b1ec65691a7981c46ff3b"),
        "core_table_accessor": (0x286A0, 0x286B4,
                                "0b2ed95da6399a86d48c019a1b21ddfc546dc5c49933f91866f417ce12d619f5"),
        "class_config": (0x2965C, 0x296E4,
                         "7d0acce7e777be885ce0e87c205580f21a204dc38800d1d58a633405dda25748"),
        "startup_call": (0x39C00, 0x39C1A,
                         "1be8eb4f97bb2028d3ffe93a61dc0566e5021eeaae5044dd55af294752dbe722"),
    }
    for name, (start, stop, expected) in slices.items():
        need(sha(data[start:stop]) == expected, "slice changed: " + name)

    # Offline grammar model only.  It does not produce or transmit bytes.
    header = struct.pack("<III", 0x203, 0, 0x200)
    target, address, length = struct.unpack("<III", header)
    need(target >> 8 == 2 and (target & 0xEF) == 3,
         "target family/operation model")
    need(address < 0x1000000 and address + length < 0x1000000,
         "family-2 bounded range model")
    need((address & 0x1FF) == 0 and (length & 0x1FF) == 0,
         "eMMC alignment model")
    need(length <= 0x200, "one-sector proposal exceeds normal firmware cap")

    print("PASS")
    print("target_0x203_local_leaf=eMMC sector-addressed MMIO_0x58000000")
    print("ordinary_header_dispatch_ready=false mode_0x20000571_forced_2")
    print("vendor_endpoints=OUT_0x02 IN_0x82 header_bytes=12")
    print("offline_operations=0 current_executable_equality_proved=false")


if __name__ == "__main__":
    main()
