#!/usr/bin/env python3
"""Zero-I/O host-contract tests for the fixed code fingerprint reader."""

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
    spec = importlib.util.spec_from_file_location("code_fingerprint_wrapper", HERE / "run-once.py")
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


def native(corrupt=None):
    windows = [bytearray(item) for item in W.EXPECTED]
    if corrupt is not None:
        windows[corrupt][len(windows[corrupt]) // 2] ^= 0x80
    match = [bytes(got) == expected for got, expected in zip(windows, W.EXPECTED)]
    specs = [("open", "LOCAL", 0, 9), ("claim", "LOCAL", 0, 0),
             ("window-a-header", "OUT", 12, 12), ("window-a-data", "IN", 512, 512),
             ("window-b-header", "OUT", 12, 12), ("window-b-data", "IN", 64, 64),
             ("window-c-header", "OUT", 12, 12), ("window-c-data", "IN", 576, 576),
             ("release", "LOCAL", 0, 0), ("close", "LOCAL", 0, 0)]
    value = {"Schema": "managed-usb-code-fingerprint-read-v1", "Stage": "complete",
             "ProtocolPhase": "ReadyForHeader", "Opened": True, "Claimed": True,
             "Released": True, "Closed": True, "Accepted": True,
             "AllWindowsMatchSelected": all(match),
             "ContentComparison": "all-windows-match-selected-package" if all(match) else "one-or-more-window-mismatch",
             "PhysicalPictureObserved": False, "BusContentsAltered": False,
             "ExecutingCodeIdentityProved": False, "WholeImageIdentityInferred": False,
             "Steps": [{"Name": n, "Direction": d, "Expected": e, "Count": c,
                        "Errno": 0, "Error": None} for n, d, e, c in specs]}
    for letter, raw, matched in zip("ABC", windows, match):
        value["Window" + letter + "Base64"] = base64.b64encode(raw).decode()
        value["Window" + letter + "Sha256"] = sha(raw)
        value["Window" + letter + "MatchesSelected"] = matched
    return value, tuple(bytes(item) for item in windows)


def envelope(stdout, stderr=b"", rc=0):
    return ("META_BEGIN\n" + W.BOOT + "\n1.00 2.00\n" + str(rc) + "\n" +
            str(len(stdout)) + "\n" + sha(stdout) + "\n" + str(len(stderr)) + "\n" +
            sha(stderr) + "\nINVENTORY_OK\nMETA_END\nSTDOUT_B64_BEGIN\n" +
            base64.b64encode(stdout).decode() + "\nSTDOUT_B64_END\nSTDERR_B64_BEGIN\n" +
            base64.b64encode(stderr).decode() + "\nSTDERR_B64_END\nEXECUTE_COMPLETE\n")


def main():
    tests = 0
    for corrupt in (None, 0, 1, 2):
        value, windows = native(corrupt)
        got, a, b, c, gc = W.parse_native(json.dumps(value) + "\n")
        check((a, b, c) == windows and got["AllWindowsMatchSelected"] is (corrupt is None) and gc == [],
              "native match/mismatch path")
        tests += 1
    base, _ = native()
    mutations = [
        lambda x: x.update(Stage="window-c-data"),
        lambda x: x.update(ProtocolPhase="Unknown"),
        lambda x: x.update(WindowCSha256="0" * 64),
        lambda x: x.update(WindowBMatchesSelected=False),
        lambda x: x.update(AllWindowsMatchSelected=False),
        lambda x: x.update(ContentComparison="one-or-more-window-mismatch"),
        lambda x: x["Steps"].__setitem__(7, dict(x["Steps"][7], Count=575)),
        lambda x: x["Steps"].append(dict(x["Steps"][-1])),
        lambda x: x.update(ExecutingCodeIdentityProved=True),
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
    W.parse_selftest('{"selfTestsPassed":50,"targetOperations":0}\n')
    W.parse_selftest('[GC_INFO] bounded\n{"selfTestsPassed":50,"targetOperations":0}\n')
    check(rejected(lambda: W.parse_selftest('{"selfTestsPassed":49,"targetOperations":0}\n')), "selftest count")
    tests += 3
    dry = json.loads(subprocess.run([sys.executable, str(HERE / "run-once.py")],
                                    check=True, capture_output=True, text=True).stdout)
    check(dry["target_operations"] == 0 and dry["writes"] == 0 and dry["retries"] == 0,
          "dry zero I/O")
    check(dry["requests"] == [{"target": "0x101", "address": "0x46001e60", "length": 512},
                               {"target": "0x101", "address": "0x460038c0", "length": 64},
                               {"target": "0x101", "address": "0x4601bb60", "length": 576}],
          "dry geometry")
    tests += 2
    source = (HERE / "Program.cs").read_text()
    check("01010000601E004600020000" in source and "01010000C038004640000000" in source and
          "0101000060BB014640020000" in source and
          "WindowALength = 512, WindowBLength = 64, WindowCLength = 576" in source,
          "source geometry")
    check("Reset" not in source and "writes = 0" in source and "retries = 0" in source,
          "source no reset/write/retry")
    wrapper = (HERE / "run-once.py").read_text()
    check(wrapper.index('record["target_operations"] = None') < wrapper.index("envelope = call(command)") <
          wrapper.index('record["target_operations"] = 3'), "inflight accounting")
    check("content_mismatch_is_not_transport_failure" in wrapper and
          "executing_code_identity_proved" in wrapper, "bounded interpretation")
    tests += 4
    check(sha((HERE / "root-with-margin.py").read_bytes()) == W.ROOT_ADAPTER_SHA, "adapter pin")
    tests += 1
    print(json.dumps({"wrapperTestsPassed": tests, "targetOperations": 0}, separators=(",", ":")))


if __name__ == "__main__":
    main()
