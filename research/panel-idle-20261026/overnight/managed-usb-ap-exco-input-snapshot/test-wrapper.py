#!/usr/bin/env python3
"""Zero-I/O host-contract tests for the fixed AP_EXCO input snapshot."""

import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def check(value, why):
    if not value:
        raise AssertionError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("ap_exco_input_snapshot_wrapper", HERE / "run-once.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


W = load()


def rejected(call):
    try:
        call()
    except (ValueError, UnicodeError, json.JSONDecodeError):
        return True
    return False


def native(ordinary_pointer=0x4500FF14, derived_pointer=0x450158A8):
    pointer = bytearray(range(32))
    ordinary = bytearray(824)
    derived = bytearray(1004)
    pointer[4:8] = ordinary_pointer.to_bytes(4, "little")
    pointer[12:16] = derived_pointer.to_bytes(4, "little")
    decoded = {
        "ordinary_gate_ca": 1, "ordinary_gate_116": 1,
        "ordinary_x_10a": 9, "ordinary_x_10c": 10,
        "ordinary_output_e6": 1, "ordinary_output_2fc": 2,
        "ordinary_counter_300": 7, "ordinary_counter_302": 8,
        "derived_byte_zero": 3, "derived_byte_one": 10,
        "derived_byte_3d8": 1,
    }
    for offset, key in ((0xCA, "ordinary_gate_ca"), (0x116, "ordinary_gate_116"),
                        (0x10A, "ordinary_x_10a"), (0x10C, "ordinary_x_10c"),
                        (0xE6, "ordinary_output_e6"), (0x2FC, "ordinary_output_2fc"),
                        (0x300, "ordinary_counter_300"), (0x302, "ordinary_counter_302")):
        ordinary[offset:offset + 2] = decoded[key].to_bytes(2, "little")
    derived[0] = decoded["derived_byte_zero"]
    derived[1] = decoded["derived_byte_one"]
    derived[0x3D8] = decoded["derived_byte_3d8"]
    matched = ordinary_pointer == 0x4500FF14 and derived_pointer == 0x450158A8
    specs = [("open", "LOCAL", 0, 9), ("claim", "LOCAL", 0, 0),
             ("pointer-header", "OUT", 12, 12), ("pointer-data", "IN", 32, 32),
             ("ordinary-header", "OUT", 12, 12), ("ordinary-data", "IN", 824, 824),
             ("derived-header", "OUT", 12, 12), ("derived-data", "IN", 1004, 1004),
             ("release", "LOCAL", 0, 0), ("close", "LOCAL", 0, 0)]
    value = {
        "Schema": "managed-usb-ap-exco-input-snapshot-v1", "Stage": "complete",
        "ProtocolPhase": "ReadyForHeader", "Opened": True, "Claimed": True,
        "Released": True, "Closed": True, "Accepted": True,
        "PointerBase64": base64.b64encode(pointer).decode(), "PointerSha256": sha(pointer),
        "OrdinaryBase64": base64.b64encode(ordinary).decode(), "OrdinarySha256": sha(ordinary),
        "DerivedBase64": base64.b64encode(derived).decode(), "DerivedSha256": sha(derived),
        "OrdinaryPointer": ordinary_pointer, "DerivedPointer": derived_pointer,
        "PointerMatches": matched,
        "OrdinaryGateCa": decoded["ordinary_gate_ca"], "OrdinaryGate116": decoded["ordinary_gate_116"],
        "OrdinaryX10A": decoded["ordinary_x_10a"], "OrdinaryX10C": decoded["ordinary_x_10c"],
        "OrdinaryOutputE6": decoded["ordinary_output_e6"], "OrdinaryOutput2Fc": decoded["ordinary_output_2fc"],
        "OrdinaryCounter300": decoded["ordinary_counter_300"], "OrdinaryCounter302": decoded["ordinary_counter_302"],
        "DerivedByteZero": decoded["derived_byte_zero"], "DerivedByteOne": decoded["derived_byte_one"],
        "DerivedByte3D8": decoded["derived_byte_3d8"],
        "InterpretationAccepted": matched,
        "Interpretation": "pointer-gated-sequential-object-snapshot" if matched else "not-decoded",
        "PhysicalPictureObserved": False, "BusContentsAltered": False,
        "Steps": [{"Name": n, "Direction": d, "Expected": e, "Count": c,
                   "Errno": 0, "Error": None} for n, d, e, c in specs],
    }
    return value, bytes(pointer), bytes(ordinary), bytes(derived), decoded


def envelope(stdout, stderr=b"", rc=0):
    return ("META_BEGIN\n" + W.BOOT + "\n1.00 2.00\n" + str(rc) + "\n" +
            str(len(stdout)) + "\n" + sha(stdout) + "\n" + str(len(stderr)) + "\n" +
            sha(stderr) + "\nINVENTORY_OK\nMETA_END\nSTDOUT_B64_BEGIN\n" +
            base64.b64encode(stdout).decode() + "\nSTDOUT_B64_END\nSTDERR_B64_BEGIN\n" +
            base64.b64encode(stderr).decode() + "\nSTDERR_B64_END\nEXECUTE_COMPLETE\n")


def main():
    tests = 0
    value, pointer, ordinary, derived, decoded = native()
    got, gp, go, gd, gdecoded, gc = W.parse_native(json.dumps(value) + "\n")
    check(gp == pointer and go == ordinary and gd == derived and gdecoded == decoded and
          got["InterpretationAccepted"] is True and gc == [], "native success")
    tests += 1
    mutations = [
        lambda x: x.update(Stage="ordinary-data"),
        lambda x: x.update(ProtocolPhase="Unknown"),
        lambda x: x.update(OrdinarySha256="0" * 64),
        lambda x: x.update(OrdinaryGate116=2),
        lambda x: x.update(InterpretationAccepted=False),
        lambda x: x.update(OrdinaryPointer=0x12345678),
        lambda x: x["Steps"].__setitem__(7, dict(x["Steps"][7], Count=1003)),
        lambda x: x["Steps"].append(dict(x["Steps"][-1])),
    ]
    for mutate in mutations:
        bad = copy.deepcopy(value)
        mutate(bad)
        check(rejected(lambda bad=bad: W.parse_native(json.dumps(bad) + "\n")), "native reject")
        tests += 1
    for op, dp in ((0x12345678, 0x450158A8), (0x4500FF14, 0x12345678)):
        bad, _, _, _, _ = native(op, dp)
        check(rejected(lambda bad=bad: W.parse_native(json.dumps(bad) + "\n")), "pointer reject")
        tests += 1
    raw = (json.dumps(value) + "\n").encode()
    terminal, got_raw, err = W.parse_envelope(envelope(raw))
    check(terminal["exit_code"] == 0 and got_raw == raw and err == b"", "envelope")
    tests += 1
    for bad in ("noise\n" + envelope(raw), envelope(raw) + "noise\n",
                envelope(raw).replace("META_END\n", "META_END\nnoise\n", 1),
                envelope(raw).replace(sha(raw), "0" * 64, 1)):
        check(rejected(lambda bad=bad: W.parse_envelope(bad)), "envelope reject")
        tests += 1
    W.parse_selftest('{"selfTestsPassed":48,"targetOperations":0}\n')
    W.parse_selftest('[GC_INFO] bounded\n{"selfTestsPassed":48,"targetOperations":0}\n')
    check(rejected(lambda: W.parse_selftest('{"selfTestsPassed":47,"targetOperations":0}\n')), "selftest count")
    tests += 3
    dry = json.loads(subprocess.run([sys.executable, str(HERE / "run-once.py")],
                                    check=True, capture_output=True, text=True).stdout)
    check(dry["target_operations"] == 0 and dry["writes"] == 0 and dry["retries"] == 0,
          "dry zero I/O")
    check(dry["requests"] == [{"target": "0x101", "address": "0x470002c0", "length": 32},
                               {"target": "0x101", "address": "0x4500ff14", "length": 824},
                               {"target": "0x101", "address": "0x450158a8", "length": 1004}],
          "dry geometry")
    tests += 2
    source = (HERE / "Program.cs").read_text()
    check("01010000C002004720000000" in source and "0101000014FF004538030000" in source and
          "01010000A8580145EC030000" in source and "ordinary[0x302]" not in source and
          "PointerLength = 32, OrdinaryLength = 824, DerivedLength = 1004" in source,
          "source geometry")
    check(source.index('Need(result.PointerMatches, "pointer anchors mismatch")') <
          source.index('Read("ordinary"'), "pointer gate ordering")
    check("Reset" not in source and "writes = 0" in source, "source no reset/write")
    wrapper = (HERE / "run-once.py").read_text()
    check(wrapper.index('record["target_operations"] = None') < wrapper.index("envelope = call(command)") <
          wrapper.index('record["target_operations"] = 3'), "inflight accounting")
    tests += 4
    check(sha((HERE / "root-with-margin.py").read_bytes()) == W.ROOT_ADAPTER_SHA, "adapter pin")
    tests += 1
    print(json.dumps({"wrapperTestsPassed": tests, "targetOperations": 0}, separators=(",", ":")))


if __name__ == "__main__":
    main()
