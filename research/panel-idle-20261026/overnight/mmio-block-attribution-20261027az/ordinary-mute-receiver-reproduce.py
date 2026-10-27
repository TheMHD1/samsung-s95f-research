#!/usr/bin/env python3
"""Offline checks for selected-image F3:00 selector 0x164; no target I/O."""

import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PROFILE = ROOT / "overnight/selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
QDF = ROOT / "binaries/qdf_tcon.ko"
PROFILE_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
QDF_SHA = "97fff5ba5cf3cff758807abbc2bdfb835b4696cbf88626dec5f7eb0e33b7ea63"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def u32(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def s32(data, offset):
    return struct.unpack_from("<i", data, offset)[0]


def cstring(data, offset):
    return data[offset:data.index(0, offset)].decode("ascii")


profile = PROFILE.read_bytes()
qdf = QDF.read_bytes()
need(len(profile) == 5_242_880 and sha(profile) == PROFILE_SHA, "profile identity")
need(sha(qdf) == QDF_SHA, "QDF identity")

slices = {
    "receive_state_machine": (0x12AC4, 0x12DBE, "5b2cbcbac9d03ba3a1dd175568a5cbc8cb7e74a75264a17fd354833d1f4e9c85"),
    "open_register_dispatch": (0x21824, 0x21876, "5f9a3da21a8aff22610a23c58b4e79bc20836d4111a456ccb393044616abacbe"),
    "f300_getter": (0x2194C, 0x21FF0, "fc3bbd7a16650a34ce0105c0174f6e5099e8f0fc5722844649149016c1cdea07"),
    "selector_164_read_leaf": (0x21F2C, 0x21F40, "3f27d4b423cc5467ddd9eda57250fe77fc942daafdd22d7fe29a657808aee9d0"),
    "write_ingress": (0x2C7F4, 0x2C842, "d16e6fc80b238ce85265229a7d328548e0ef614a9544e233f6973ee4272a4b49"),
    "f300_writer_entry": (0x2C91C, 0x2C9B4, "d0802314c7b4c0761973b3a0157f8442bb10dacdfc9902a0a16978836418e630"),
    "selector_164_write_leaf": (0x2D00A, 0x2D020, "ce80bc3bad56c0e7409f7e698e6ff7d7a0291bf58cfe3cefe2307c372817bbf4"),
    "failmode_function": (0x3A278, 0x3A2CA, "334790e63e567c1af59ed9766d2fea3bdf8836e73046ead3b090c00411969cfb"),
    "unmute_fixed_copy": (0x20970, 0x20988, "64ca8ce0af8081bc1c4c78bbf10ec818d5ccf2fbd79c8887a5d14387911fa95e"),
    "derived_accessor": (0xE96C, 0xE974, "a971931ca704d394dc4e3ea628440af003c9773be24beb079d5a66a08fefcfc0"),
    "derived_registry": (0x3C5B8, 0x3C5D4, "41dfa8809a435830065f05cbcf22bc20ee9b0f4b4f773e3d49f02f3b04403f66"),
}
for name, (start, end, expected) in slices.items():
    need(sha(profile[start:end]) == expected, "slice mismatch: " + name)

selector = 0x164
index = selector // 4 - 9
need(index == 0x50, "selector index")
read_entry = 0x219B0 + 4 * index
write_entry = 0x2C9B4 + 4 * index
read_target = (0x217B0 + s32(profile, read_entry)) & 0xFFFFFFFF
write_target = (0x2C7B4 + s32(profile, write_entry)) & 0xFFFFFFFF
need((read_entry, s32(profile, read_entry), read_target) == (0x21AF0, 0x57C, 0x21D2C), "read mapping")
need((write_entry, s32(profile, write_entry), write_target) == (0x2CAF4, 0x656, 0x2CE0A), "write mapping")

# FILE = VA + 0x200. Pin full leaf encodings and their literal inputs.
need(profile[0x21F2C:0x21F40] == bytes.fromhex("3048006ec0f38150022801d1012028e5002026e5"), "read leaf")
need(u32(profile, 0x21FF0) == 0x58200000, "read block literal")
need(profile[0x2D00A:0x2D020] == bytes.fromhex("012c03d101200df032f903e014b900200df02df996e0"), "write leaf")
need(cstring(profile, 0x3A2CC) == "Failmode:%d\n", "Failmode literal")
need(u32(profile, 0xE970) == 0x200158A8, "derived-object literal")
need(u32(profile, 0x3A2DC) == 0x20000ED8, "zero-branch literal")
need((u32(profile, 0x20988), u32(profile, 0x2098C), u32(profile, 0x20990)) ==
     (0x20000D40, 0x58300000, 0x20000D4C), "zero-branch fixed-copy literals")

registry = struct.unpack_from("<7I", profile, 0x3C5B8)
need(registry == (0x3DD84, 0x3D44B, 2, 0x3DD8C, 0x200158A8, 0x3EC, 0x18), "registry tuple")
need(cstring(profile, 0x3DF84) == "MULTI" and cstring(profile, 0x3DF8C) == "AP_EXCO", "registry names")
need(0x84 <= registry[5], "object extent")

# Reuse three already accepted, late, non-event-aligned snapshots only to test
# whether this word was retained.  They do not prove execution or light.
capture_specs = {
    "W": (ROOT / "overnight/ap-exco-input-snapshot-20261027w/capture-once",
          "de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0",
          "83cd349d84ef397074f36c5b80e2cc72ad8b00bbeebae5dae978a21f11935171"),
    "AK": (ROOT / "overnight/npc-ap-divisor-snapshot-20261027ak/capture-ordinary-after",
           "de263b1ebda47b3d1c306f87017b4961e1f25473d43b7ee7964345002b3a90f0",
           "e1480df76124fa3ea07a62bfc88c68d3f1eaa718bee60d3dc86df424ca1c2541"),
    "AW": (ROOT / "overnight/stock-rt-state-delta-20261027aw/post-lifecycle-inputs",
           "eb15688aac78bcaf6ca12d34249898b355df5d4f7332b97e9d9b325852be4694",
           "778cb7e9ab4f3950c6a466f799e41b13115e0b9e4cef8f8ac412466041d90e57"),
}
retained_words = {}
for label, (directory, raw_sha, result_sha) in capture_specs.items():
    raw = (directory / "derived-ap-exco.bin").read_bytes()
    result_bytes = (directory / "result.json").read_bytes()
    result = json.loads(result_bytes)
    need(len(raw) == 1004 and sha(raw) == raw_sha, label + " raw identity")
    need(sha(result_bytes) == result_sha, label + " result identity")
    need(result["transport_accepted"] is True and result["pointer_matches_expected"] is True,
         label + " capture gates")
    need(result["physical_picture_observed"] is False and result["event_time_inferred"] is False,
         label + " interpretation limits")
    need(result["samples_sequential_not_atomic"] is True, label + " timing limit")
    retained_words[label] = u32(raw, 0x80)
need(retained_words == {"W": 0, "AK": 0, "AW": 0}, "retained +0x80 words")

print(json.dumps({
    "accepted": True,
    "coordinate_model": "image0 FILE = linked VA + 0x200",
    "wire_header": "f3 00 00 00 01 64",
    "read": {
        "table_entry_file": hex(read_entry),
        "target_va": hex(read_target),
        "word_address": "0x58200060",
        "predicate": "1 iff bits[23:22] equal 2; otherwise 0",
    },
    "write": {
        "table_entry_file": hex(write_entry),
        "target_va": hex(write_target),
        "callee_va": "0x3a078",
        "literal": "Failmode:%d\\n",
        "derived_object": "MULTI/AP_EXCO at CPU 0x200158a8, extent 0x3ec",
        "zero_branch_fixed_words": ["0x58300000", "0x58300018"],
    },
    "retained_late_word_at_derived_plus_0x80": retained_words,
    "retained_word_limit": "late sequential samples; no event timing, execution, persistence, or physical-picture inference",
    "source_sha256": PROFILE_SHA,
    "qdf_sha256": QDF_SHA,
    "slice_sha256": {name: expected for name, (_, _, expected) in slices.items()},
    "target_operations": 0,
}, indent=2, sort_keys=True))
