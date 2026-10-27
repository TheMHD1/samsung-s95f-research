#!/usr/bin/env python3
"""Offline fake-transport tests for the RTP passive-observer wrapper."""

import base64
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def check(value, why):
    if not value:
        raise AssertionError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load():
    spec = importlib.util.spec_from_file_location("rt_passive_observer_wrapper", HERE / "run-once.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


W = load()
GC_ROWS = ("[GC_INFO] GC_Start #1: Gen(0), Time(125698544 ms), Reason(0)\n"
           "[GC_INFO] GC_End #1: Gen(0), Time(125698545 ms)\n")


def rejected(call):
    try:
        call()
    except (ValueError, UnicodeError, json.JSONDecodeError):
        return True
    return False


def outcome(name):
    return json.loads((HERE / "fixtures" / name).read_text())


def encoded(value):
    return (json.dumps(value, separators=(",", ":")) + "\n").encode()


def envelope(stdout, stderr=b"", rc=0, declared_stdout=None):
    stdout_size = len(stdout) if declared_stdout is None else declared_stdout
    return ("META_BEGIN\n" + W.BOOT + "\n1.00 2.00\n" + str(rc) + "\n" +
            str(stdout_size) + "\n" + sha(stdout) + "\n" + str(len(stderr)) + "\n" +
            sha(stderr) + "\nINVENTORY_OK\nMETA_END\nSTDOUT_B64_BEGIN\n" +
            base64.b64encode(stdout).decode() + "\nSTDOUT_B64_END\nSTDERR_B64_BEGIN\n" +
            base64.b64encode(stderr).decode() + "\nSTDERR_B64_END\nEXECUTE_COMPLETE\n")


class FakeRoot:
    def __init__(self, native):
        self.native = native
        self.commands = []
        self.execute_calls = 0
        self.cleanup_calls = 0

    @staticmethod
    def save(path, value):
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

    def root(self, command, record, output):
        syntax = subprocess.run(["/bin/sh", "-n"], input=command, text=True, capture_output=True)
        check(syntax.returncode == 0 and syntax.stderr == "" and len(command.encode()) <= 8192,
              "generated root command syntax/bound")
        self.commands.append(command)
        record.setdefault("calls", []).append({"command": command, "fake": True})
        self.save(output, record)
        if "--self-test" in command:
            return '{"selfTestsPassed":75,"targetOperations":0,"maxTestOutputBytes":10541}\n'
        if "--execute" in command:
            self.execute_calls += 1
            return envelope(self.native)
        if "rm --" in command:
            self.cleanup_calls += 1
            return "STAGE_ABSENT\n"
        return "FAKE_OK\n"


def integration(native, expect_success):
    fake = FakeRoot(native)
    old_root, old_contract, old_argv = W.load_root, W.load_contract, sys.argv
    staged = {name: (name + "-bytes").encode() for name in W.REMOTE_NAMES}
    try:
        W.load_root = lambda: fake
        W.load_contract = lambda manifest: (b"offline-wrapper-manifest", staged)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "record"
            sys.argv = [str(HERE / "run-once.py"), "--execute", "--manifest-sha256", "0" * 64,
                        "--output", str(output)]
            stream = io.StringIO()
            if expect_success:
                with contextlib.redirect_stdout(stream): W.main()
                result = json.loads(stream.getvalue())
                check(result["transport_accepted"] is True and result["cleanup"] == "STAGE_ABSENT" and
                      result["native_gc_lines"] == 2,
                      "integration accepted result")
                check(fake.cleanup_calls == 1 and (output / "result.json").is_file(), "accepted cleanup")
                raw_files = result["retained_raw_files"]
                check(raw_files and all((output / row["name"]).read_bytes() for row in raw_files),
                      "raw windows persisted")
            else:
                check(rejected(lambda: W.main()), "invalid integration rejected")
                check(fake.cleanup_calls == 0 and not (output / "result.json").exists(), "rejected stage retained")
                check((output / "native.stdout.bin").read_bytes() == native and
                      (output / "native.stderr.bin").read_bytes() == b"", "failed native bytes retained")
                record = json.loads((output / "record.json").read_text())
                check(record["target_operations"] is None and
                      record["target_operations_status"] == "inflight_or_unknown" and
                      record["cleanup_required"] is True, "failed accounting remains unknown")
            check(fake.execute_calls == 1 and sum("--execute" in row for row in fake.commands) == 1,
                  "exactly one native execution")
    finally:
        W.load_root, W.load_contract, sys.argv = old_root, old_contract, old_argv


def main():
    tests = 0
    fixture_names = ["accepted-already-faulted.json", "accepted-transition-rstart.json",
                     "accepted-transition-rend.json", "accepted-time-limit.json"]
    parsed = {}
    for name in fixture_names:
        value, captures, raws, gc = W.parse_native((HERE / "fixtures" / name).read_text())
        check(value["accepted"] and captures and raws and
              sum(row["window_count"] for row in captures) == len(raws) and gc == [], "fixture " + name)
        parsed[name] = value; tests += 1

    cycle_limit = outcome("accepted-time-limit.json")
    cycle_limit["terminalReason"] = "CycleLimit"
    W.parse_native(json.dumps(cycle_limit) + "\n"); tests += 1
    zero_cycle = outcome("accepted-time-limit.json")
    zero_cycle.update(cyclesStarted=0, cleanCyclesCompleted=0, cleanCyclesDiscarded=0,
                      bulkTransfers=0, headersSent=0, inputsCompleted=0, retained=[])
    W.parse_native(json.dumps(zero_cycle) + "\n"); tests += 1
    partial = outcome("accepted-time-limit.json")
    last = partial["retained"][0]
    current = copy.deepcopy(last)
    last["cycleIndex"] = 79
    current["role"] = "current-partial"; current["cycleIndex"] = 80
    current["windows"] = current["windows"][:3]; current["transfers"] = current["transfers"][:6]
    for row in current["transfers"]:
        row["beforeUs"] += 250000; row["afterUs"] += 250000
    partial["retained"].append(current)
    partial.update(cyclesStarted=80, cleanCyclesCompleted=79, cleanCyclesDiscarded=78,
                   headersSent=477, inputsCompleted=477, bulkTransfers=954,
                   endUs=current["transfers"][-1]["afterUs"],
                   overshootUs=current["transfers"][-1]["afterUs"] - partial["deadlineUs"])
    W.parse_native(json.dumps(partial) + "\n"); tests += 1

    impossible_start = outcome("accepted-transition-rstart.json")
    impossible_start["retained"] = impossible_start["retained"][1:]
    for capture in impossible_start["retained"]: capture["cycleIndex"] = 1
    impossible_start.update(cyclesStarted=1, cleanCyclesCompleted=0, cleanCyclesDiscarded=0,
                            headersSent=6, inputsCompleted=6, bulkTransfers=12)
    check(rejected(lambda: W.parse_native(json.dumps(impossible_start) + "\n")),
          "initial R-start cannot be transition"); tests += 1
    full_partial = outcome("accepted-time-limit.json")
    current = copy.deepcopy(full_partial["retained"][0]); current["role"] = "current-partial"
    full_partial["retained"] = [current]
    full_partial.update(cyclesStarted=1, cleanCyclesCompleted=0, cleanCyclesDiscarded=0,
                        headersSent=6, inputsCompleted=6, bulkTransfers=12)
    check(rejected(lambda: W.parse_native(json.dumps(full_partial) + "\n")),
          "full cycle cannot be deadline partial"); tests += 1
    wrong_state = outcome("accepted-transition-rstart.json")
    clean_r = copy.deepcopy(wrong_state["retained"][0]["windows"][0])
    wrong_state["retained"][1]["windows"][0] = clean_r
    check(rejected(lambda: W.parse_native(json.dumps(wrong_state) + "\n")),
          "transition state provenance"); tests += 1
    late_transition = outcome("accepted-transition-rend.json")
    late_clean = copy.deepcopy(outcome("accepted-time-limit.json")["retained"][0])
    late_clean["cycleIndex"] = 79
    for row in late_clean["transfers"]:
        row["beforeUs"] -= 250000; row["afterUs"] -= 250000
    for capture in late_transition["retained"]:
        capture["cycleIndex"] = 80
        for row in capture["transfers"]:
            row["beforeUs"] += 19750000; row["afterUs"] += 19750000
    late_transition["retained"].insert(0, late_clean)
    late_transition.update(cyclesStarted=80, cleanCyclesCompleted=79, cleanCyclesDiscarded=78,
                           headersSent=485, inputsCompleted=485, bulkTransfers=970,
                           endUs=19752200, overshootUs=0)
    W.parse_native(json.dumps(late_transition) + "\n"); tests += 1
    delayed_cleanup = outcome("accepted-time-limit.json")
    delayed_cleanup.update(endUs=25000000, overshootUs=5000000)
    W.parse_native(json.dumps(delayed_cleanup) + "\n"); tests += 1
    before_deadline = outcome("accepted-time-limit.json")
    before_deadline.update(endUs=19999999, overshootUs=0)
    check(rejected(lambda: W.parse_native(json.dumps(before_deadline) + "\n")),
          "time limit must reach deadline"); tests += 1
    extra_retained = outcome("accepted-transition-rstart.json")
    extra_retained["retained"].append(7)
    check(rejected(lambda: W.parse_native(json.dumps(extra_retained) + "\n")),
          "scalar retained extra rejected"); tests += 1
    extra_window = outcome("accepted-transition-rstart.json")
    extra_window["retained"][0]["windows"].append(7)
    extra_window["retained"][0]["transfers"].extend(
        copy.deepcopy(extra_window["retained"][0]["transfers"][:2]))
    check(rejected(lambda: W.parse_native(json.dumps(extra_window) + "\n")),
          "scalar window extra rejected"); tests += 1

    base = outcome("accepted-transition-rstart.json")
    mutations = [
        ("schema", lambda x: x.update(schema="wrong")),
        ("extra field", lambda x: x.update(extra=True)),
        ("stage", lambda x: x.update(stage="R-data")),
        ("phase", lambda x: x.update(protocolPhase="Unknown")),
        ("release", lambda x: x.update(released=False)),
        ("accepted", lambda x: x.update(accepted=False)),
        ("write", lambda x: x.update(writes=1)),
        ("terminal", lambda x: x.update(terminalReason="TransitionDetected")),
        ("discarded", lambda x: x.update(cleanCyclesDiscarded=1)),
        ("bulk counter", lambda x: x.update(bulkTransfers=x["bulkTransfers"] - 1)),
        ("header counter", lambda x: x.update(headersSent=x["headersSent"] - 1)),
        ("onset flag", lambda x: x.update(onsetObserved=False)),
        ("role order", lambda x: x["retained"].reverse()),
        ("address", lambda x: x["retained"][0]["windows"][0].update(address="0x47012402")),
        ("count", lambda x: x["retained"][0]["windows"][0].update(count=255)),
        ("hash", lambda x: x["retained"][0]["windows"][0].update(sha256="0" * 64)),
        ("window order", lambda x: x["retained"][0]["windows"].__setitem__(0, x["retained"][0]["windows"][1])),
        ("timestamp", lambda x: x["retained"][0]["transfers"][0].update(afterUs=-1)),
        ("transfer length", lambda x: x["retained"][0]["transfers"][1].update(count=255)),
    ]
    for name, mutate in mutations:
        bad = copy.deepcopy(base); mutate(bad)
        check(rejected(lambda bad=bad: W.parse_native(json.dumps(bad) + "\n")), "reject " + name)
        tests += 1

    short = copy.deepcopy(base)
    window = short["retained"][0]["windows"][0]
    raw = base64.b64decode(window["rawBase64"][:-4] + "AAAA")
    window["rawBase64"] = base64.b64encode(raw[:-1]).decode(); window["sha256"] = sha(raw[:-1])
    check(rejected(lambda: W.parse_native(json.dumps(short) + "\n")), "raw extent reject"); tests += 1

    raw_native = encoded(base)
    terminal, got, err = W.parse_envelope(envelope(raw_native))
    check(terminal["exit_code"] == 0 and got == raw_native and err == b"", "envelope accepted"); tests += 1
    bad_envelopes = [
        "noise\n" + envelope(raw_native),
        envelope(raw_native) + "noise\n",
        envelope(raw_native).replace("META_END\n", "META_END\nnoise\n", 1),
        envelope(raw_native).replace(sha(raw_native), "0" * 64, 1),
        envelope(raw_native, declared_stdout=W.MAX_NATIVE_STDOUT + 1),
        envelope(raw_native).replace("INVENTORY_OK", "INVENTORY_BAD"),
    ]
    for bad in bad_envelopes:
        check(rejected(lambda bad=bad: W.parse_envelope(bad)), "envelope reject"); tests += 1

    selftest_json = '{"selfTestsPassed":75,"targetOperations":0,"maxTestOutputBytes":10541}\n'
    W.parse_selftest(selftest_json)
    check(rejected(lambda: W.parse_selftest('{"selfTestsPassed":74,"targetOperations":0,"maxTestOutputBytes":10541}\n')),
          "selftest reject"); tests += 2
    W.parse_selftest(selftest_json + GC_ROWS); tests += 1
    native_with_gc = encoded(base).decode() + GC_ROWS
    _, _, _, gc = W.parse_native(native_with_gc)
    check(gc == GC_ROWS.splitlines(), "native GC diagnostics classified"); tests += 1
    check(rejected(lambda: W.parse_native(encoded(base).decode() + "unknown diagnostic\n")),
          "unknown native line reject"); tests += 1
    check(rejected(lambda: W.parse_native(encoded(base).decode() + "[GC_INFO] x\n" * 33)),
          "too many GC lines reject"); tests += 1
    check(rejected(lambda: W.parse_native(encoded(base).decode() + "[GC_INFO] " + "x" * 600 + "\n")),
          "oversize GC line reject"); tests += 1

    integration(encoded(outcome("accepted-already-faulted.json")) + GC_ROWS.encode(), True); tests += 1
    invalid = outcome("accepted-transition-rend.json"); invalid["released"] = False
    integration(encoded(invalid), False); tests += 1

    dry = json.loads(subprocess.run([sys.executable, str(HERE / "run-once.py")],
                                    check=True, capture_output=True, text=True).stdout)
    check(dry["target_operations"] == 0 and dry["writes"] == 0 and dry["retries"] == 0 and
          dry["cycle"] == ["R", "M", "C", "H", "L", "R"], "dry zero I/O")
    tests += 1
    source = (HERE / "run-once.py").read_text()
    check(source.index('record["target_operations"] = None') < source.index("envelope = call(command)") <
          source.index('record["target_operations"] = native["headersSent"]'), "inflight accounting order")
    check(source.index('(args.output / "native.stdout.bin").write_bytes(native_stdout)') <
          source.index("need(terminal[\"exit_code\"] == 0"), "raw before interpretation")
    check("--execute" in source and "no_retry" in source and source.count("/usr/bin/dotnet {dll} --execute") == 1,
          "one execute source")
    tests += 3
    print(json.dumps({"wrapperTestsPassed": tests, "targetOperations": 0}, separators=(",", ":")))


if __name__ == "__main__":
    main()
