#!/usr/bin/env python3
"""Zero-I/O host-contract tests for the fixed mode reader."""

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
    spec = importlib.util.spec_from_file_location("mode_wrapper", HERE / "run-once.py")
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


def native(root=0x20010000):
    data = bytearray(range(68))
    data[0x0A:0x0C] = (1).to_bytes(2, "little")
    data[0x0C:0x0E] = (0).to_bytes(2, "little")
    data[0x40:0x44] = root.to_bytes(4, "little")
    matched = root == 0x20010000
    specs = [("open", "LOCAL", 0, 9), ("claim", "LOCAL", 0, 0),
             ("mode-header", "OUT", 12, 12), ("mode-data", "IN", 68, 68),
             ("alternate-header", "OUT", 12, 12), ("alternate-data", "IN", 16, 16),
             ("release", "LOCAL", 0, 0), ("close", "LOCAL", 0, 0)]
    value = {"Schema": "managed-usb-rt-mode-read-v1", "Stage": "complete",
             "ProtocolPhase": "ReadyForHeader", "Opened": True, "Claimed": True,
             "Released": True, "Closed": True, "Accepted": True,
             "DataBase64": base64.b64encode(data).decode(), "DataSha256": sha(data),
             "AlternateBase64": base64.b64encode(bytes(range(16))).decode(),
             "AlternateSha256": sha(bytes(range(16))),
             "ModeAa": 1, "ModeAc": 0, "RootWord": root, "RootMatches": matched,
             "MirrorCandidate": int.from_bytes(data[0x22:0x24], "little"),
             "EnableCandidate": int.from_bytes(data[0x24:0x26], "little"),
             "InterpretationAccepted": matched,
             "Interpretation": "conditional-image1-mode-sample" if matched else "root-anchor-mismatch",
             "PhysicalPictureObserved": False, "BusContentsAltered": False,
             "Steps": [{"Name": n, "Direction": d, "Expected": e, "Count": c,
                        "Errno": 0, "Error": None} for n, d, e, c in specs]}
    return value, bytes(data)


def envelope(stdout, stderr=b"", rc=0):
    return ("META_BEGIN\n" + W.BOOT + "\n1.00 2.00\n" + str(rc) + "\n" +
            str(len(stdout)) + "\n" + sha(stdout) + "\n" + str(len(stderr)) + "\n" +
            sha(stderr) + "\nINVENTORY_OK\nMETA_END\nSTDOUT_B64_BEGIN\n" +
            base64.b64encode(stdout).decode() + "\nSTDOUT_B64_END\nSTDERR_B64_BEGIN\n" +
            base64.b64encode(stderr).decode() + "\nSTDERR_B64_END\nEXECUTE_COMPLETE\n")


def main():
    tests = 0
    for root, accepted in ((0x20010000, True), (0x12345678, False)):
        value, data = native(root)
        got, raw, alternate, gc = W.parse_native(json.dumps(value) + "\n")
        check(raw == data and alternate == bytes(range(16)) and
              got["InterpretationAccepted"] is accepted and gc == [], "native path")
        tests += 1
    base, _ = native()
    mutations = [
        lambda x: x.update(Stage="mode-data"),
        lambda x: x.update(ProtocolPhase="Unknown"),
        lambda x: x.update(DataSha256="0" * 64),
        lambda x: x.update(InterpretationAccepted=False),
        lambda x: x["Steps"].__setitem__(5, dict(x["Steps"][5], Count=15)),
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
    W.parse_selftest('{"selfTestsPassed":35,"targetOperations":0}\n')
    W.parse_selftest('[GC_INFO] bounded\n{"selfTestsPassed":35,"targetOperations":0}\n')
    check(rejected(lambda: W.parse_selftest('{"selfTestsPassed":34,"targetOperations":0}\n')), "selftest count")
    tests += 3
    dry = json.loads(subprocess.run([sys.executable, str(HERE / "run-once.py")],
                                    check=True, capture_output=True, text=True).stdout)
    check(dry["target_operations"] == 0 and dry["writes"] == 0 and dry["retries"] == 0,
          "dry zero I/O")
    check(dry["requests"] == [{"target": "0x101", "address": "0x470004a0", "length": 68},
                               {"target": "0x101", "address": "0x47000bc0", "length": 16}],
          "dry geometry")
    tests += 2
    source = (HERE / "Program.cs").read_text()
    check("01010000A004004744000000" in source and "01010000C00B004710000000" in source and
          "ModeLength = 68, AltLength = 16" in source,
          "source geometry")
    check("Reset" not in source and "writes = 0" in source, "source no reset/write")
    wrapper = (HERE / "run-once.py").read_text()
    check(wrapper.index('record["target_operations"] = None') < wrapper.index("envelope = call(command)") <
          wrapper.index('record["target_operations"] = 2'), "inflight accounting")
    tests += 3
    check(sha((HERE / "root-with-margin.py").read_bytes()) == W.ROOT_ADAPTER_SHA, "adapter pin")
    tests += 1
    print(json.dumps({"wrapperTestsPassed": tests, "targetOperations": 0}, separators=(",", ":")))


if __name__ == "__main__":
    main()
