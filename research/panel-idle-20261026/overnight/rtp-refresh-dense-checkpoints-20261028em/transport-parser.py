#!/usr/bin/env python3
"""Stage and execute the fixed RTP passive observer; dry by default."""

import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex
import uuid

HERE = Path(__file__).resolve().parent
ROOT_ADAPTER = HERE / "root-with-margin.py"
ROOT_ADAPTER_SHA = "e69b79a103931c4eecca6f6f505975acdd8f9de2e1e8189b8321dd77d8bc6938"
NATIVE_MANIFEST_SHA = "44f74a8a695f41ed21d68a7a36e13934eebc74050bf991c634e6015ec88043a2"
BOOT = "00000000-0000-4000-8000-000000000000"
DOTNET_SHA = "e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310"
SCHEMA = "managed-usb-rt-passive-observer-wrapper-build-v1"
ASSEMBLY = "ManagedUsbRtPassiveObserver"
REMOTE_NAMES = [ASSEMBLY + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json")]
MAX_NATIVE_STDOUT = 24576
MAX_NATIVE_STDERR = 2048
REQUESTS = [
    {"id": "R", "address": "0x47012400", "length": 256},
    {"id": "M", "address": "0x470004a0", "length": 68},
    {"id": "C", "address": "0x47000bc0", "length": 16},
    {"id": "P", "address": "0x47000490", "length": 16},
    {"id": "N", "address": "0x4700ba28", "length": 36},
    {"id": "H", "address": "0x4700d0e0", "length": 96},
    {"id": "L", "address": "0x47010f00", "length": 64},
]
WINDOWS = {row["id"]: (row["address"], row["length"]) for row in REQUESTS}
NATIVE_LOCAL_FILES = {
    "Program.cs", "ManagedUsbRtPassiveObserver.csproj", "build-native.py",
    "README-native.md", "native-build-manifest.json",
    *("bin/Release/net6.0/" + name for name in REMOTE_NAMES),
}
FIXTURES = {
    "fixtures/accepted-already-faulted.json",
    "fixtures/accepted-transition-rstart.json",
    "fixtures/accepted-transition-rend.json",
    "fixtures/accepted-time-limit.json",
}
HOST_FILES = {"run-once.py", "test-wrapper.py", "root-with-margin.py",
              "README-wrapper.md", "build-wrapper.py"}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def bad(value):
        raise ValueError("non-JSON constant " + value)
    return json.loads(raw, parse_constant=bad)


def integer(value, why, low=None, high=None):
    need(type(value) is int, why)
    if low is not None: need(value >= low, why)
    if high is not None: need(value <= high, why)
    return value


def load_root():
    need(sha(ROOT_ADAPTER.read_bytes()) == ROOT_ADAPTER_SHA, "root adapter pin")
    spec = importlib.util.spec_from_file_location("rt_passive_observer_root_transport", ROOT_ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dir_guard(path):
    q = shlex.quote(path)
    return (f"test ! -L {q}\n" + f"test -d {q}\n" +
            f'test "$(stat -c "%u:%g:%a" {q})" = "0:0:700"\n')


def file_guard(path, size=None):
    q = shlex.quote(path)
    text = (f"test ! -L {q}\n" + f"test -f {q}\n" +
            f'test "$(stat -c "%u:%g:%a" {q})" = "0:0:600"\n')
    if size is not None:
        text += f'test "$(wc -c < {q})" = {size}\n'
    return text


def exact_inventory(path, names):
    q = shlex.quote(path)
    cases = "|".join(shlex.quote(name) for name in sorted(names))
    return (f"count=0\nfor item in {q}/* {q}/.[!.]* {q}/..?*; do\n" +
            '  test -e "$item" || test -L "$item" || continue\n' +
            '  name=${item##*/}\n' +
            f'  case "$name" in {cases}) ;; *) exit 91 ;; esac\n' +
            "  count=$((count+1))\ndone\n" + f'test "$count" = {len(names)}\n')


def integrity(stage, staged, names=None):
    names = REMOTE_NAMES if names is None else names
    text = dir_guard(stage) + exact_inventory(stage, names)
    for name in names:
        raw = staged[name]
        target = stage + "/" + name
        text += file_guard(target, len(raw))
        text += (f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" '
                 f"= {sha(raw)}\n")
    return text


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def load_contract(expected_manifest_sha):
    need(re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha or "") is not None,
         "manifest SHA required")
    wrapper_raw = (HERE / "wrapper-build-manifest.json").read_bytes()
    need(sha(wrapper_raw) == expected_manifest_sha, "reviewed wrapper manifest pin")
    manifest = strict_json(wrapper_raw)
    need(manifest.get("schema") == SCHEMA, "wrapper manifest schema")
    expected = NATIVE_LOCAL_FILES | FIXTURES | HOST_FILES
    files = manifest.get("files")
    need(isinstance(files, dict) and set(files) == expected, "wrapper manifest inventory")
    for name, row in files.items():
        raw = (HERE / name).read_bytes()
        need(row == {"size": len(raw), "sha256": sha(raw)}, "local pin " + name)
    native_raw = (HERE / "native-build-manifest.json").read_bytes()
    need(sha(native_raw) == NATIVE_MANIFEST_SHA and
         manifest.get("native_build_manifest_sha256") == NATIVE_MANIFEST_SHA,
         "native manifest pin")
    native = strict_json(native_raw)
    for name in NATIVE_LOCAL_FILES - {"native-build-manifest.json"}:
        row = native.get("files", {}).get(name)
        need(row == files[name], "native file inherited pin " + name)
    staged = {name: (HERE / "bin/Release/net6.0" / name).read_bytes()
              for name in REMOTE_NAMES}
    return wrapper_raw, staged


def parse_selftest(text):
    rows, _ = parse_lines_with_gc(text)
    need(len(rows) == 1, "one self-test row")
    value = rows[0]
    need(value == {"selfTestsPassed": 75, "targetOperations": 0,
                   "maxTestOutputBytes": 10541}, "self-test contract")


def parse_lines_with_gc(text):
    rows, gc = [], []
    lines = text.splitlines()
    need(len(lines) <= 33, "native output line bound")
    for line in lines:
        need(len(line.encode("utf-8")) <= MAX_NATIVE_STDOUT, "native line bound")
        if line.startswith("{"):
            rows.append(strict_json(line))
        elif line.startswith("[GC_INFO] "):
            need(len(line) > len("[GC_INFO] ") and len(line.encode("utf-8")) <= 512,
                 "GC diagnostic bound")
            gc.append(line)
        else:
            need(False, "unclassified native output")
    need(len(gc) <= 32, "GC diagnostic count")
    return rows, gc


def decode_raw(value, expected, expected_sha, why):
    need(type(value) is str and type(expected_sha) is str and
         re.fullmatch(r"[0-9a-f]{64}", expected_sha) is not None, why + " encoding")
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError(why + " base64") from exc
    need(len(raw) == expected and sha(raw) == expected_sha, why + " raw/hash")
    return raw


def parse_capture(capture, expected_role, expected_names, retained_index):
    need(isinstance(capture, dict) and capture.get("role") == expected_role,
         "capture role " + expected_role)
    need(set(capture) == {"role", "cycleIndex", "windows", "transfers"},
         "capture fields " + expected_role)
    cycle = integer(capture.get("cycleIndex"), "capture cycle", 1, 60)
    windows = capture.get("windows"); transfers = capture.get("transfers")
    need(isinstance(windows, list) and isinstance(transfers, list), "capture arrays")
    need(len(windows) == len(expected_names) and all(isinstance(row, dict) for row in windows),
         "window extent " + expected_role)
    need([row.get("name") for row in windows] == expected_names,
         "window order " + expected_role)
    need(len(transfers) == len(windows) * 2 and all(isinstance(row, dict) for row in transfers),
         "transfer count " + expected_role)
    decoded = []
    rt_states = []
    prior_after = None
    for index, (window, name) in enumerate(zip(windows, expected_names)):
        need(isinstance(window, dict), "window object")
        address, length = WINDOWS[name]
        expected_fields = {"name", "address", "expected", "count", "complete", "rawBase64", "sha256"}
        if name == "R": expected_fields.add("observedRtState")
        need(set(window) == expected_fields, "window fields " + name)
        need(window.get("name") == name and window.get("address") == address and
             integer(window.get("expected"), "window expected") == length and
             integer(window.get("count"), "window count") == length and
             window.get("complete") is True, "window fixed contract")
        raw = decode_raw(window.get("rawBase64"), length, window.get("sha256"),
                         expected_role + "/" + name)
        rt = window.get("observedRtState")
        if name == "R":
            need(isinstance(rt, dict), "R state")
            observed = (integer(rt.get("stop"), "R stop", 0, 0xffff),
                        integer(rt.get("fault"), "R fault", 0, 0xffff),
                        integer(rt.get("ordinaryGate"), "R gate", 0, 0xffff))
            actual = (int.from_bytes(raw[0:2], "little"),
                      int.from_bytes(raw[0x0a:0x0c], "little"),
                      int.from_bytes(raw[0x0e:0x10], "little"))
            classify = "Clean" if actual == (0, 0, 1) else "Faulted" if actual == (1, 0x1001, 0) else "Unexpected"
            need(observed == actual and rt.get("classification") == classify and
                 set(rt) == {"stop", "fault", "ordinaryGate", "classification"}, "R decode")
            rt_states.append(classify)
        else:
            need(rt is None, "non-R not decoded")
        for transfer_index, (direction, suffix, expected_count) in enumerate(
                (("OUT", "header", 12), ("IN", "data", length))):
            row = transfers[index * 2 + transfer_index]
            need(isinstance(row, dict) and set(row) ==
                 {"name", "direction", "expected", "count", "errno", "beforeUs", "afterUs"},
                 "transfer fields " + name + "/" + direction)
            need(isinstance(row, dict) and row.get("name") == name + "-" + suffix and
                 row.get("direction") == direction and
                 integer(row.get("expected"), "transfer expected") == expected_count and
                 integer(row.get("count"), "transfer count") == expected_count and
                 integer(row.get("errno"), "transfer errno") == 0 and
                 "error" not in row, "transfer exact " + name + "/" + direction)
            before = integer(row.get("beforeUs"), "transfer before", 0)
            after = integer(row.get("afterUs"), "transfer after", before)
            if prior_after is not None: need(before >= prior_after, "capture timestamp order")
            prior_after = after
        safe_role = expected_role.replace("-", "_")
        filename = f"retained-{retained_index:02d}-{safe_role}-cycle{cycle:03d}-{index:02d}-{name}.bin"
        decoded.append((filename, raw, window.get("sha256")))
    return {"role": expected_role, "cycle": cycle, "window_count": len(windows),
            "first_us": None if not transfers else transfers[0]["beforeUs"],
            "last_us": None if not transfers else transfers[-1]["afterUs"],
            "rt_states": rt_states}, decoded


def parse_native(text):
    rows, gc = parse_lines_with_gc(text)
    need(len(rows) == 1 and isinstance(rows[0], dict), "one native outcome")
    value = rows[0]
    need(isinstance(value, dict) and value.get("schema") == "managed-usb-rt-passive-observer-v1",
         "native schema")
    need(set(value) == {"schema", "stage", "terminalReason", "protocolPhase", "opened", "claimed",
                       "released", "closed", "accepted", "onsetObserved", "onsetMissed",
                       "physicalPictureObserved", "busContentsAltered", "writes", "retries",
                       "cyclesStarted", "cleanCyclesCompleted", "cleanCyclesDiscarded", "bulkTransfers",
                       "headersSent", "inputsCompleted", "startUs", "deadlineUs", "endUs", "overshootUs",
                       "retentionPolicy", "retained"}, "native outcome fields")
    need(value.get("stage") == "terminal" and value.get("protocolPhase") == "ReadyForHeader",
         "known terminal phase")
    for key in ("opened", "claimed", "released", "closed", "accepted"):
        need(value.get(key) is True, "native " + key)
    need(value.get("physicalPictureObserved") is False and
         value.get("busContentsAltered") is False and
         integer(value.get("writes"), "writes") == 0 and
         integer(value.get("retries"), "retries") == 0 and
         "error" not in value, "read-only outcome")
    start = integer(value.get("startUs"), "start time", 0)
    deadline = integer(value.get("deadlineUs"), "deadline time", start)
    end = integer(value.get("endUs"), "end time", start)
    overshoot = integer(value.get("overshootUs"), "overshoot", 0)
    need(deadline - start == 2_000_000 and overshoot == max(0, end - deadline),
         "native time bounds")
    # A suspend or large monotonic jump immediately after StartUs can produce
    # an accepted TimeLimit before the first cycle; keep that native-valid
    # zero-cycle shape distinct from any observed sample.
    cycles = integer(value.get("cyclesStarted"), "cycles started", 0, 60)
    clean = integer(value.get("cleanCyclesCompleted"), "clean cycles", 0, cycles)
    discarded = integer(value.get("cleanCyclesDiscarded"), "discarded clean", 0, 59)
    need(discarded == max(0, clean - 1), "discarded clean consistency")
    # The 60-cycle cap bounds ordinary reads at 480.  A transition at the
    # R-end of cycle 60 legitimately adds the one post-fault seven-read set.
    headers = integer(value.get("headersSent"), "headers sent", 0, 487)
    bulk = integer(value.get("bulkTransfers"), "bulk transfers", 0, 974)
    inputs = integer(value.get("inputsCompleted"), "inputs completed", 0, 487)
    need(bulk == headers * 2 and inputs == headers, "global exact transfer counters")
    need(value.get("retentionPolicy") ==
         "last-fully-clean+transition+one-postfault-set+current-partial; older-clean-discarded",
         "retention policy")
    retained = value.get("retained"); need(isinstance(retained, list), "retained captures")
    need(all(isinstance(row, dict) for row in retained), "retained object extent")
    roles = [row.get("role") for row in retained]
    terminal = value.get("terminalReason")
    expected = []
    if terminal == "AlreadyFaulted":
        need(value.get("onsetObserved") is False and value.get("onsetMissed") is True and
             cycles == 1 and clean == 0 and headers == 8, "already-faulted counters")
        expected = [("initial-faulted", ["R"]), ("post-fault", ["M", "C", "P", "N", "H", "L", "R"])]
    elif terminal == "TransitionCaptured":
        need(value.get("onsetObserved") is True and value.get("onsetMissed") is False and
             clean == cycles - 1, "transition counters")
        transition = next((row for row in retained if isinstance(row, dict) and row.get("role") == "transition"), None)
        need(transition is not None and isinstance(transition.get("windows"), list), "transition retained")
        width = len(transition["windows"]); need(width in (1, 8), "transition width")
        if width == 1: need(cycles >= 2, "R-start transition requires prior clean cycle")
        if clean: expected.append(("last-clean", ["R", "M", "C", "P", "N", "H", "L", "R"]))
        expected += [("transition", ["R"] if width == 1 else ["R", "M", "C", "P", "N", "H", "L", "R"]),
                     ("post-fault", ["M", "C", "P", "N", "H", "L", "R"])]
        need(headers == clean * 8 + width + 7, "transition header count")
    elif terminal in ("TimeLimit", "CycleLimit"):
        need(value.get("onsetObserved") is False and value.get("onsetMissed") is False,
             "clean terminal flags")
        if clean: expected.append(("last-clean", ["R", "M", "C", "P", "N", "H", "L", "R"]))
        current = next((row for row in retained if isinstance(row, dict) and row.get("role") == "current-partial"), None)
        partial_names = []
        if current is not None:
            windows = current.get("windows"); need(isinstance(windows, list), "partial windows")
            need(len(windows) <= 7, "deadline partial stops before R-end")
            partial_names = ["R", "M", "C", "P", "N", "H", "L", "R"][:len(windows)]
            expected.append(("current-partial", partial_names))
        need(cycles in (clean, clean + 1) and (current is not None) == (cycles == clean + 1),
             "clean/current cycle relation")
        need(headers == clean * 8 + len(partial_names), "clean terminal header count")
        if terminal == "CycleLimit": need(cycles == clean == 60 and current is None, "cycle limit exact")
    else:
        need(False, "accepted terminal reason")
    need(len(retained) == len(expected) and roles == [role for role, _ in expected],
         "retained role order/extent")
    if terminal == "TimeLimit": need(end >= deadline, "time limit reached")
    captures, raw_files = [], []
    previous_time = None
    for index, ((role, names), capture) in enumerate(zip(expected, retained)):
        summary, decoded = parse_capture(capture, role, names, index)
        if previous_time is not None and summary["first_us"] is not None:
            need(summary["first_us"] >= previous_time, "retained chronological order")
        if summary["last_us"] is not None: previous_time = summary["last_us"]
        captures.append(summary); raw_files.extend(decoded)
    by_role = {row["role"]: row for row in captures}
    if "last-clean" in by_role:
        need(by_role["last-clean"]["cycle"] == clean and
             by_role["last-clean"]["rt_states"] == ["Clean", "Clean"], "last-clean provenance")
    if "initial-faulted" in by_role:
        need(by_role["initial-faulted"]["cycle"] == 1 and
             by_role["initial-faulted"]["rt_states"] == ["Faulted"], "initial-faulted provenance")
    if "transition" in by_role:
        transition_states = ["Faulted"] if by_role["transition"]["window_count"] == 1 else ["Clean", "Faulted"]
        need(by_role["transition"]["cycle"] == cycles and
             by_role["transition"]["rt_states"] == transition_states, "transition provenance")
    if "post-fault" in by_role:
        need(by_role["post-fault"]["cycle"] == cycles and
             by_role["post-fault"]["rt_states"] == ["Faulted"], "post-fault provenance")
    if "current-partial" in by_role:
        need(by_role["current-partial"]["cycle"] == cycles and
             by_role["current-partial"]["rt_states"] in ([], ["Clean"]), "partial provenance")
    need(len({name for name, _, _ in raw_files}) == len(raw_files), "unique raw filenames")
    return value, captures, raw_files, gc


def parse_envelope(text):
    lines = text.splitlines()
    markers = ["META_BEGIN", "META_END", "STDOUT_B64_BEGIN", "STDOUT_B64_END",
               "STDERR_B64_BEGIN", "STDERR_B64_END", "EXECUTE_COMPLETE"]
    for marker in markers: need(lines.count(marker) == 1, "envelope marker " + marker)
    mi, me = lines.index("META_BEGIN"), lines.index("META_END")
    so, se = lines.index("STDOUT_B64_BEGIN"), lines.index("STDOUT_B64_END")
    eo, ee = lines.index("STDERR_B64_BEGIN"), lines.index("STDERR_B64_END")
    complete = lines.index("EXECUTE_COMPLETE")
    need(mi == 0 and me == 9 and so == 10 and se + 1 == eo and ee + 1 == complete and
         complete == len(lines) - 1, "exact contiguous envelope")
    meta = lines[mi + 1:me]; need(len(meta) == 8, "metadata extent")
    boot, uptime, exit_text, stdout_size, stdout_sha, stderr_size, stderr_sha, inventory = meta
    need(boot == BOOT and re.fullmatch(r"[0-9.]+ [0-9.]+", uptime) is not None, "execution identity")
    need(exit_text in ("0", "1", "63", "64", "65"), "native exit")
    need(stdout_size.isdigit() and stderr_size.isdigit(), "native size fields")
    need(int(stdout_size) <= MAX_NATIVE_STDOUT and int(stderr_size) <= MAX_NATIVE_STDERR, "native output bound")
    need(re.fullmatch(r"[0-9a-f]{64}", stdout_sha) is not None and
         re.fullmatch(r"[0-9a-f]{64}", stderr_sha) is not None and inventory == "INVENTORY_OK",
         "native metadata")
    try:
        stdout = base64.b64decode("".join(lines[so + 1:se]), validate=True)
        stderr = base64.b64decode("".join(lines[eo + 1:ee]), validate=True)
    except Exception as exc:
        raise ValueError("envelope base64") from exc
    need(len(stdout) == int(stdout_size) and sha(stdout) == stdout_sha, "stdout framing")
    need(len(stderr) == int(stderr_size) and sha(stderr) == stderr_sha, "stderr framing")
    return {"boot_id": boot, "uptime": uptime, "exit_code": int(exit_text),
            "stdout_sha256": stdout_sha, "stderr_sha256": stderr_sha}, stdout, stderr

