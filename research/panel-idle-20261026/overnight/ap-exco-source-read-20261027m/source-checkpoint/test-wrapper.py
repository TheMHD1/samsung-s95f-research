#!/usr/bin/env python3
"""Zero-I/O host-contract tests for the fixed AP_EXCO source reader."""

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
    spec = importlib.util.spec_from_file_location("ap_exco_source_wrapper", HERE / "run-once.py")
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


def native(pointer_word=0x4500FF14):
    pointer = bytearray(range(32))
    source_base = bytearray(range(16))
    source_tail = bytearray(range(32))
    pointer[0x0C:0x10] = pointer_word.to_bytes(4, "little")
    source_base[0] = 3
    source_tail[0x0C] = 1
    matched = pointer_word == 0x4500FF14
    specs = [("open", "LOCAL", 0, 9), ("claim", "LOCAL", 0, 0),
             ("pointer-header", "OUT", 12, 12), ("pointer-data", "IN", 32, 32),
             ("source-base-header", "OUT", 12, 12), ("source-base-data", "IN", 16, 16),
             ("source-tail-header", "OUT", 12, 12), ("source-tail-data", "IN", 32, 32),
             ("release", "LOCAL", 0, 0), ("close", "LOCAL", 0, 0)]
    value = {"Schema": "managed-usb-ap-exco-source-read-v1", "Stage": "complete",
             "ProtocolPhase": "ReadyForHeader", "Opened": True, "Claimed": True,
             "Released": True, "Closed": True, "Accepted": True,
             "PointerBase64": base64.b64encode(pointer).decode(), "PointerSha256": sha(pointer),
             "BaseBase64": base64.b64encode(source_base).decode(), "BaseSha256": sha(source_base),
             "TailBase64": base64.b64encode(source_tail).decode(), "TailSha256": sha(source_tail),
             "PointerWord": pointer_word, "PointerMatches": matched,
             "SourceByteZero": 3, "SourceByte3D8": 1,
             "InterpretationAccepted": matched,
             "Interpretation": "conditional-local-pointer-binding-sequential-source-samples" if matched else "pointer-anchor-mismatch",
             "PhysicalPictureObserved": False, "BusContentsAltered": False,
             "Steps": [{"Name": n, "Direction": d, "Expected": e, "Count": c,
                        "Errno": 0, "Error": None} for n, d, e, c in specs]}
    return value, bytes(pointer), bytes(source_base), bytes(source_tail)


def envelope(stdout, stderr=b"", rc=0):
    return ("META_BEGIN\n" + W.BOOT + "\n1.00 2.00\n" + str(rc) + "\n" +
            str(len(stdout)) + "\n" + sha(stdout) + "\n" + str(len(stderr)) + "\n" +
            sha(stderr) + "\nINVENTORY_OK\nMETA_END\nSTDOUT_B64_BEGIN\n" +
            base64.b64encode(stdout).decode() + "\nSTDOUT_B64_END\nSTDERR_B64_BEGIN\n" +
            base64.b64encode(stderr).decode() + "\nSTDERR_B64_END\nEXECUTE_COMPLETE\n")


def main():
    tests = 0
    for pointer_word, accepted in ((0x4500FF14, True), (0x12345678, False)):
        value, pointer, source_base, source_tail = native(pointer_word)
        got, got_pointer, got_base, got_tail, gc = W.parse_native(json.dumps(value) + "\n")
        check(got_pointer == pointer and got_base == source_base and got_tail == source_tail and
              got["InterpretationAccepted"] is accepted and gc == [], "native path")
        tests += 1
    base, _, _, _ = native()
    mutations = [
        lambda x: x.update(Stage="source-tail-data"),
        lambda x: x.update(ProtocolPhase="Unknown"),
        lambda x: x.update(TailSha256="0" * 64),
        lambda x: x.update(InterpretationAccepted=False),
        lambda x: x["Steps"].__setitem__(7, dict(x["Steps"][7], Count=31)),
        lambda x: x["Steps"].append(dict(x["Steps"][-1])),
    ]
    for mutate in mutations:
        bad = copy.deepcopy(base)
        mutate(bad)
        check(rejected(lambda bad=bad: W.parse_native(json.dumps(bad) + "\n")), "native reject")
        tests += 1
    raw = (json.dumps(base) + "\n").encode()
    terminal, got, err = W.parse_envelope(envelope(raw))
    check(terminal["exit_code"] == 0 and got == raw and err == b"", "envelope")
    tests += 1
    for bad in ("noise\n" + envelope(raw), envelope(raw) + "noise\n",
                envelope(raw).replace("META_END\n", "META_END\nnoise\n", 1),
                envelope(raw).replace(sha(raw), "0" * 64, 1)):
        check(rejected(lambda bad=bad: W.parse_envelope(bad)), "envelope reject")
        tests += 1
    W.parse_selftest('{"selfTestsPassed":47,"targetOperations":0}\n')
    W.parse_selftest('[GC_INFO] bounded\n{"selfTestsPassed":47,"targetOperations":0}\n')
    check(rejected(lambda: W.parse_selftest('{"selfTestsPassed":46,"targetOperations":0}\n')), "selftest count")
    tests += 3
    dry = json.loads(subprocess.run([sys.executable, str(HERE / "run-once.py")],
                                    check=True, capture_output=True, text=True).stdout)
    check(dry["target_operations"] == 0 and dry["writes"] == 0 and dry["retries"] == 0,
          "dry zero I/O")
    check(dry["requests"] == [{"target": "0x101", "address": "0x470002c0", "length": 32},
                               {"target": "0x101", "address": "0x4500ff14", "length": 16},
                               {"target": "0x101", "address": "0x450102e0", "length": 32}],
          "dry geometry")
    tests += 2
    source = (HERE / "Program.cs").read_text()
    check("01010000C002004720000000" in source and "0101000014FF004510000000" in source and
          "01010000E002014520000000" in source and
          "PointerLength = 32, BaseLength = 16, TailLength = 32" in source,
          "source geometry")
    check("Reset" not in source and "writes = 0" in source, "source no reset/write")
    wrapper = (HERE / "run-once.py").read_text()
    check(wrapper.index('record["target_operations"] = None') < wrapper.index("envelope = call(command)") <
          wrapper.index('record["target_operations"] = 3'), "inflight accounting")
    tests += 3
    check(sha((HERE / "root-with-margin.py").read_bytes()) == W.ROOT_ADAPTER_SHA, "adapter pin")
    tests += 1
    print(json.dumps({"wrapperTestsPassed": tests, "targetOperations": 0}, separators=(",", ":")))


if __name__ == "__main__":
    main()
