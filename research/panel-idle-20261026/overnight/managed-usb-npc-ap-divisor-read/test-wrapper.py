#!/usr/bin/env python3
"""Zero-I/O host-contract tests for the fixed NPC_AP candidate read."""

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
    spec = importlib.util.spec_from_file_location("npc_ap_divisor_read_wrapper", HERE / "run-once.py")
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


def native(raw=bytes.fromhex("6400ea01eb010004")):
    decoded = {
        "context_14": int.from_bytes(raw[0:2], "little"),
        "divisor_16": int.from_bytes(raw[2:4], "little"),
        "divisor_18": int.from_bytes(raw[4:6], "little"),
        "divisor_1a": int.from_bytes(raw[6:8], "little"),
    }
    specs = [("open", "LOCAL", 0, 9), ("claim", "LOCAL", 0, 0),
             ("npc-header", "OUT", 12, 12), ("npc-data", "IN", 8, 8),
             ("release", "LOCAL", 0, 0), ("close", "LOCAL", 0, 0)]
    value = {
        "Schema": "managed-usb-npc-ap-divisor-read-v1", "Stage": "complete",
        "ProtocolPhase": "ReadyForHeader", "Opened": True, "Claimed": True,
        "Released": True, "Closed": True, "Accepted": True,
        "DataBase64": base64.b64encode(raw).decode(), "DataSha256": sha(raw),
        "PartialDataBase64": base64.b64encode(raw).decode(), "PartialDataLength": 8,
        "Context14": decoded["context_14"], "Divisor16": decoded["divisor_16"],
        "Divisor18": decoded["divisor_18"], "Divisor1A": decoded["divisor_1a"],
        "Interpretation": "conditional-selector0-npc-ap-object-offsets-14-through-1b",
        "PointerIdentityGateUsed": False, "StoredDefaultsUsedAsIdentity": False,
        "TimestampFrequency": 10_000_000, "ReadStartTicks": 100, "ReadEndTicks": 200,
        "PhysicalPictureObserved": False, "BusContentsAltered": False,
        "Steps": [{"Name": n, "Direction": d, "Expected": e, "Count": c,
                   "Errno": 0, "Error": None} for n, d, e, c in specs],
    }
    return value, raw, decoded


def envelope(stdout, stderr=b"", rc=0):
    return ("META_BEGIN\n" + W.BOOT + "\n1.00 2.00\n" + str(rc) + "\n" +
            str(len(stdout)) + "\n" + sha(stdout) + "\n" + str(len(stderr)) + "\n" +
            sha(stderr) + "\nINVENTORY_OK\nMETA_END\nSTDOUT_B64_BEGIN\n" +
            base64.b64encode(stdout).decode() + "\nSTDOUT_B64_END\nSTDERR_B64_BEGIN\n" +
            base64.b64encode(stderr).decode() + "\nSTDERR_B64_END\nEXECUTE_COMPLETE\n")


def main():
    tests = 0
    value, raw, decoded = native()
    got, got_raw, got_decoded, gc = W.parse_native(json.dumps(value) + "\n")
    check(got_raw == raw and got_decoded == decoded and gc == [] and
          got["PointerIdentityGateUsed"] is False, "native success")
    tests += 1

    mutations = [
        lambda x: x.update(Stage="npc-data"),
        lambda x: x.update(ProtocolPhase="Unknown"),
        lambda x: x.update(DataSha256="0" * 64),
        lambda x: x.update(PartialDataLength=7),
        lambda x: x.update(Divisor18=0),
        lambda x: x.update(PointerIdentityGateUsed=True),
        lambda x: x.update(StoredDefaultsUsedAsIdentity=True),
        lambda x: x.update(Interpretation="live-npc-ap"),
        lambda x: x.update(ReadStartTicks=201),
        lambda x: x.update(TimestampFrequency=0),
        lambda x: x["Steps"].__setitem__(3, dict(x["Steps"][3], Count=7)),
        lambda x: x["Steps"].append(dict(x["Steps"][-1])),
    ]
    for mutate in mutations:
        bad = copy.deepcopy(value)
        mutate(bad)
        check(rejected(lambda bad=bad: W.parse_native(json.dumps(bad) + "\n")), "native reject")
        tests += 1

    # The parser accepts arbitrary exact eight-byte values; packaged defaults
    # have no special identity status.
    defaults, _, _ = native(bytes.fromhex("6400000400040004"))
    W.parse_native(json.dumps(defaults) + "\n")
    zeros, _, _ = native(bytes(8))
    W.parse_native(json.dumps(zeros) + "\n")
    tests += 2

    raw_json = (json.dumps(value) + "\n").encode()
    terminal, got_stdout, err = W.parse_envelope(envelope(raw_json))
    check(terminal["exit_code"] == 0 and got_stdout == raw_json and err == b"", "envelope")
    tests += 1
    for bad in ("noise\n" + envelope(raw_json), envelope(raw_json) + "noise\n",
                envelope(raw_json).replace("META_END\n", "META_END\nnoise\n", 1),
                envelope(raw_json).replace(sha(raw_json), "0" * 64, 1)):
        check(rejected(lambda bad=bad: W.parse_envelope(bad)), "envelope reject")
        tests += 1
    check(rejected(lambda: W.parse_envelope(envelope(b"x" * (W.MAX_NATIVE_STDOUT + 1)))),
          "stdout bound")
    check(rejected(lambda: W.parse_envelope(envelope(raw_json,
          b"x" * (W.MAX_NATIVE_STDERR + 1)))), "stderr bound")
    tests += 2

    W.parse_selftest('{"selfTestsPassed":26,"targetOperations":0}\n')
    W.parse_selftest('[GC_INFO] bounded\n{"selfTestsPassed":26,"targetOperations":0}\n')
    check(rejected(lambda: W.parse_selftest('{"selfTestsPassed":25,"targetOperations":0}\n')),
          "selftest count")
    check(rejected(lambda: W.parse_selftest("unknown\n" +
          '{"selfTestsPassed":26,"targetOperations":0}\n')), "unknown native line")
    tests += 4

    dry = json.loads(subprocess.run([sys.executable, str(HERE / "run-once.py")],
                                    check=True, capture_output=True, text=True).stdout)
    check(dry["target_operations"] == 0 and dry["writes"] == 0 and dry["retries"] == 0,
          "dry zero I/O")
    check(dry["requests"] == [{"target": "0x101", "address": "0x4500d730", "length": 8}],
          "dry geometry")
    tests += 2

    source = (HERE / "Program.cs").read_text()
    check("0101000030D7004508000000" in source and "DataLength = 8" in source and
          'Read("npc", Header, data, ProtocolPhase.ExpectingDataIn)' in source,
          "source geometry")
    check("PartialDataBase64" in source and "input.Value > 0 && input.Value <= output.Length" in source,
          "partial retention")
    check("Reset" not in source and "writes = 0" in source and "retries = 0" in source,
          "source no reset/write/retry")
    wrapper = (HERE / "run-once.py").read_text()
    check(wrapper.index('record["target_operations"] = None') < wrapper.index("envelope = call(command)") <
          wrapper.index('record["target_operations"] = 1'), "inflight accounting")
    check("npc-ap-offset-14-through-1b.bin" in wrapper and
          "stored_defaults_used_as_identity" in wrapper, "wrapper raw/claim scope")
    tests += 5

    check(sha((HERE / "root-with-margin.py").read_bytes()) == W.ROOT_ADAPTER_SHA, "adapter pin")
    tests += 1
    print(json.dumps({"wrapperTestsPassed": tests, "targetOperations": 0}, separators=(",", ":")))


if __name__ == "__main__":
    main()
