#!/usr/bin/env python3
"""Pin packaged EEPROM-history branches against a retained RT snapshot."""
import hashlib
import json
from pathlib import Path
import struct
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS, CS_MODE_LITTLE_ENDIAN

HERE = Path(__file__).resolve().parent


def need(ok, why):
    if not ok:
        raise ValueError(why)


def main():
    profile = HERE.parent / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
    data = profile.read_bytes()
    need(hashlib.sha256(data).hexdigest() == "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0", "Profile identity")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS | CS_MODE_LITTLE_ENDIAN)
    code = {i.address: (i.mnemonic, i.op_str) for start, end in
            [(0x97e8, 0x986a), (0x9968, 0x99a4), (0xef94, 0xef98)]
            for i in md.disasm(data[start + 0x200:end + 0x200], start)}
    expected = {
        0xef94: ("ldr", "r0, [pc, #0]"), 0xef96: ("bx", "lr"),
        0x97ea: ("bl", "#0xef94"), 0x97f4: ("movs", "r0, #0xe0"),
        0x97f6: ("bl", "#0x9748"), 0x9818: ("movw", "r0, #0x2466"),
        0x981c: ("strh", "r1, [r0, r4]"), 0x981e: ("movw", "r0, #0x24aa"),
        0x9822: ("ldrb", "r5, [r0, r4]"), 0x9824: ("movw", "r0, #0x2484"),
        0x982a: ("cbz", "r0, #0x9838"), 0x9848: ("movw", "r0, #0x24ac"),
        0x984c: ("strh", "r1, [r0, r4]"), 0x9852: ("cmp", "r0, r5"),
        0x9854: ("blt", "#0x9866"), 0x9856: ("movw", "r0, #0x2484"),
        0x985c: ("cbz", "r0, #0x9866"), 0x9860: ("movs", "r0, #0x10"),
        0x9862: ("bl", "#0xb660"), 0x9978: ("movw", "r0, #0x24ac"),
        0x997c: ("ldrb", "r0, [r0, r6]"), 0x997e: ("adds", "r0, r0, #1"),
        0x9980: ("uxtb", "r5, r0"), 0x9982: ("cmp", "r5, #0xfe"),
        0x9984: ("ble", "#0x9988"), 0x9986: ("movs", "r5, #0"),
        0x999c: ("movs", "r0, #0xe0"), 0x999e: ("bl", "#0x9790"),
    }
    for address, instruction in expected.items():
        need(code.get(address) == instruction, "Instruction at VA%x: %r" % (address, code.get(address)))
    need(struct.unpack_from("<I", data, 0xef98 + 0x200)[0] == 0x47010000, "RT object root")
    live = (HERE / "rt-block-read-once/returned-block.bin").read_bytes()
    need(hashlib.sha256(live).hexdigest() == "7044ed744404edf22eff6d90a7cc9cdcd5704cbbad5e0e2f85de03acfa23217d", "Retained RT bytes")
    values = {name: struct.unpack_from("<H", live, offset)[0] for name, offset in
              [("history_check_flag", 0x66), ("history_gate", 0x84),
               ("unassigned_shared_field_9e", 0x9e), ("comparison_value", 0xaa), ("history_value", 0xac)]}
    need(values == {"history_check_flag": 1, "history_gate": 0, "unassigned_shared_field_9e": 1, "comparison_value": 100, "history_value": 243}, "Typed live values")
    need(struct.unpack_from("<H", data, 0x183800 + 0x9e)[0] == 1, "9e already one in packaged initializer")
    report = {"schema": "rt-packaged-history-interpretation-v1", "fields": values,
              "file_equals_image0_va_plus": "0x200",
              "packaged_check_va": "0x97e8", "packaged_check_file": "0x99e8",
              "packaged_feedback_va": "0x9968", "packaged_feedback_file": "0x9b68",
              "packaged_history_routes_would_be_gated_off_for_sample": values["history_gate"] == 0,
              "field_9e_semantics_shared_with_image1_proved": False,
              "executing_code_identity_proved": False, "protection_or_eeprom_write_performed": False}
    (HERE / "history-interpretation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
