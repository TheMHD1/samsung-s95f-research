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
    lines = text.splitlines()
    need(len(lines) == 1, "one self-test row")
    value = strict_json(lines[0])
    need(value == {"selfTestsPassed": 75, "targetOperations": 0,
                   "maxTestOutputBytes": 10541}, "self-test contract")


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
    cycle = integer(capture.get("cycleIndex"), "capture cycle", 1, 80)
    windows = capture.get("windows"); transfers = capture.get("transfers")
    need(isinstance(windows, list) and isinstance(transfers, list), "capture arrays")
    need([row.get("name") for row in windows if isinstance(row, dict)] == expected_names,
         "window order " + expected_role)
    need(len(transfers) == len(windows) * 2, "transfer count " + expected_role)
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
    lines = text.splitlines()
    need(len(lines) == 1, "one native outcome")
    value = strict_json(lines[0])
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
    overshoot = integer(value.get("overshootUs"), "overshoot", 0, 4_000_000)
    need(deadline - start == 20_000_000 and overshoot == max(0, end - deadline),
         "native time bounds")
    # A suspend or large monotonic jump immediately after StartUs can produce
    # an accepted TimeLimit before the first cycle; keep that native-valid
    # zero-cycle shape distinct from any observed sample.
    cycles = integer(value.get("cyclesStarted"), "cycles started", 0, 80)
    clean = integer(value.get("cleanCyclesCompleted"), "clean cycles", 0, cycles)
    discarded = integer(value.get("cleanCyclesDiscarded"), "discarded clean", 0, 79)
    need(discarded == max(0, clean - 1), "discarded clean consistency")
    headers = integer(value.get("headersSent"), "headers sent", 0, 480)
    bulk = integer(value.get("bulkTransfers"), "bulk transfers", 0, 960)
    inputs = integer(value.get("inputsCompleted"), "inputs completed", 0, 480)
    need(bulk == headers * 2 and inputs == headers, "global exact transfer counters")
    need(value.get("retentionPolicy") ==
         "last-fully-clean+transition+one-postfault-set+current-partial; older-clean-discarded",
         "retention policy")
    retained = value.get("retained"); need(isinstance(retained, list), "retained captures")
    roles = [row.get("role") for row in retained if isinstance(row, dict)]
    terminal = value.get("terminalReason")
    expected = []
    if terminal == "AlreadyFaulted":
        need(value.get("onsetObserved") is False and value.get("onsetMissed") is True and
             cycles == 1 and clean == 0 and headers == 6, "already-faulted counters")
        expected = [("initial-faulted", ["R"]), ("post-fault", ["M", "C", "H", "L", "R"])]
    elif terminal == "TransitionCaptured":
        need(value.get("onsetObserved") is True and value.get("onsetMissed") is False and
             clean == cycles - 1, "transition counters")
        transition = next((row for row in retained if isinstance(row, dict) and row.get("role") == "transition"), None)
        need(transition is not None and isinstance(transition.get("windows"), list), "transition retained")
        width = len(transition["windows"]); need(width in (1, 6), "transition width")
        if width == 1: need(cycles >= 2, "R-start transition requires prior clean cycle")
        if clean: expected.append(("last-clean", ["R", "M", "C", "H", "L", "R"]))
        expected += [("transition", ["R"] if width == 1 else ["R", "M", "C", "H", "L", "R"]),
                     ("post-fault", ["M", "C", "H", "L", "R"])]
        need(headers == clean * 6 + width + 5, "transition header count")
    elif terminal in ("TimeLimit", "CycleLimit"):
        need(value.get("onsetObserved") is False and value.get("onsetMissed") is False,
             "clean terminal flags")
        if clean: expected.append(("last-clean", ["R", "M", "C", "H", "L", "R"]))
        current = next((row for row in retained if isinstance(row, dict) and row.get("role") == "current-partial"), None)
        partial_names = []
        if current is not None:
            windows = current.get("windows"); need(isinstance(windows, list), "partial windows")
            need(len(windows) <= 5, "deadline partial stops before R-end")
            partial_names = ["R", "M", "C", "H", "L", "R"][:len(windows)]
            expected.append(("current-partial", partial_names))
        need(cycles in (clean, clean + 1) and (current is not None) == (cycles == clean + 1),
             "clean/current cycle relation")
        need(headers == clean * 6 + len(partial_names), "clean terminal header count")
        if terminal == "CycleLimit": need(cycles == clean == 80 and current is None, "cycle limit exact")
    else:
        need(False, "accepted terminal reason")
    need(roles == [role for role, _ in expected], "retained role order")
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
    return value, captures, raw_files


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"schema": "managed-usb-rt-passive-observer-wrapper-dry-v1",
                          "target_operations": 0, "duration_ms": 20000,
                          "max_cycles": 80, "nominal_period_ms": 250,
                          "cycle": ["R", "M", "C", "H", "L", "R"],
                          "requests": REQUESTS, "writes": 0, "retries": 0},
                         separators=(",", ":")))
        return
    need(args.output is not None and args.output.is_absolute(), "absolute output required")
    need(not args.output.exists(), "fresh output required")
    manifest_raw, staged = load_contract(args.manifest_sha256)
    args.output.mkdir(parents=True, exist_ok=False)
    root = load_root()
    stage = "/tmp/researcher-rt-passive-" + uuid.uuid4().hex
    record_path = args.output / "record.json"
    record = {"schema": "managed-usb-rt-passive-observer-wrapper-record-v1",
              "manifest_sha256": sha(manifest_raw), "native_manifest_sha256": NATIVE_MANIFEST_SHA,
              "wrapper_sha256": sha(Path(__file__).read_bytes()),
              "root_adapter_sha256": ROOT_ADAPTER_SHA, "expected_boot_id": BOOT,
              "remote_stage": stage, "calls": [], "target_operations": 0,
              "target_operations_status": "not_started", "native_invocations": 0,
              "no_retry": True, "cleanup_required": True, "requests": REQUESTS}
    root.save(record_path, record)

    def call(command):
        return root.root(command, record, record_path)

    call("set -eu\numask 077\n" +
         f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
         f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n' +
         f"test ! -e {shlex.quote(stage)}\ntest ! -L {shlex.quote(stage)}\n" +
         f"mkdir -m 700 {shlex.quote(stage)}\n" + dir_guard(stage) +
         "cat /proc/uptime\necho PRIVATE_STAGE_CREATED\n")

    for name in REMOTE_NAMES:
        raw = staged[name]; target = stage + "/" + name
        encoded = base64.b64encode(raw).decode("ascii"); raw_offset = 0
        for offset in range(0, len(encoded), 5000):
            chunk = encoded[offset:offset + 5000]
            decoded = base64.b64decode(chunk, validate=True)
            initialize = (f"test ! -e {shlex.quote(target)}\n" +
                          f"test ! -L {shlex.quote(target)}\n" +
                          f": > {shlex.quote(target)}\nchmod 600 {shlex.quote(target)}\n") if offset == 0 else ""
            call("set -eu\numask 077\n" +
                 f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
                 dir_guard(stage) + initialize + file_guard(target, raw_offset) +
                 f"printf %s {shlex.quote(chunk)} | base64 -d >> {shlex.quote(target)}\n" +
                 file_guard(target, raw_offset + len(decoded)) + "echo STAGED_CHUNK\n")
            raw_offset += len(decoded)
        need(raw_offset == len(raw), "upload extent " + name)
        call("set -eu\numask 077\n" +
             f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
             dir_guard(stage) + file_guard(target, len(raw)) +
             f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {sha(raw)}\n' +
             "echo STAGED_FILE\n")

    dll = shlex.quote(stage + "/" + REMOTE_NAMES[0])
    selftest = call("set -eu\numask 077\n" +
                    f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
                    integrity(stage, staged) + f"/usr/bin/dotnet {dll} --self-test\n")
    (args.output / "selftest.stdout.txt").write_text(selftest)
    parse_selftest(selftest); record["selftest_sha256"] = sha(selftest.encode()); root.save(record_path, record)

    stdout_name, stderr_name = "native.stdout", "native.stderr"
    stdout_remote, stderr_remote = stage + "/" + stdout_name, stage + "/" + stderr_name
    command = ("set -eu\numask 077\n" +
               f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' + integrity(stage, staged) +
               f"test ! -e {shlex.quote(stdout_remote)}\ntest ! -L {shlex.quote(stdout_remote)}\n" +
               f"test ! -e {shlex.quote(stderr_remote)}\ntest ! -L {shlex.quote(stderr_remote)}\n" +
               f": > {shlex.quote(stdout_remote)}\n: > {shlex.quote(stderr_remote)}\n" +
               f"chmod 600 {shlex.quote(stdout_remote)} {shlex.quote(stderr_remote)}\n" +
               "set +e\n" + f"/usr/bin/dotnet {dll} --execute > {shlex.quote(stdout_remote)} 2> {shlex.quote(stderr_remote)}\n" +
               "native_rc=$?\nset -e\n" + file_guard(stdout_remote) + file_guard(stderr_remote) +
               f'test "$(wc -c < {shlex.quote(stdout_remote)})" -le {MAX_NATIVE_STDOUT}\n' +
               f'test "$(wc -c < {shlex.quote(stderr_remote)})" -le {MAX_NATIVE_STDERR}\n' +
               exact_inventory(stage, REMOTE_NAMES + [stdout_name, stderr_name]) +
               "echo META_BEGIN\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n" +
               'echo "$native_rc"\n' +
               f"wc -c < {shlex.quote(stdout_remote)}\nsha256sum {shlex.quote(stdout_remote)} | cut -d ' ' -f1\n" +
               f"wc -c < {shlex.quote(stderr_remote)}\nsha256sum {shlex.quote(stderr_remote)} | cut -d ' ' -f1\n" +
               "echo INVENTORY_OK\necho META_END\necho STDOUT_B64_BEGIN\n" +
               f"base64 {shlex.quote(stdout_remote)}\n" +
               "echo STDOUT_B64_END\necho STDERR_B64_BEGIN\n" +
               f"base64 {shlex.quote(stderr_remote)}\n" +
               "echo STDERR_B64_END\necho EXECUTE_COMPLETE\n")
    record["native_invocations"] = 1
    record["target_operations"] = None
    record["target_operations_status"] = "inflight_or_unknown"
    root.save(record_path, record)
    envelope = call(command)
    (args.output / "execute-envelope.txt").write_text(envelope)
    terminal, native_stdout, native_stderr = parse_envelope(envelope)
    # Preserve authenticated native bytes before interpreting exit or JSON.
    (args.output / "native.stdout.bin").write_bytes(native_stdout)
    (args.output / "native.stderr.bin").write_bytes(native_stderr)
    record["terminal"] = terminal; record["terminal_validated"] = True; root.save(record_path, record)
    need(terminal["exit_code"] == 0 and native_stderr == b"", "native terminal status")
    native, captures, raw_files = parse_native(native_stdout.decode("utf-8", errors="strict"))
    for name, raw, expected_sha in raw_files:
        need(re.fullmatch(r"retained-[0-9]{2}-[a-z_]+-cycle[0-9]{3}-[0-9]{2}-[RMCHL]\.bin", name) is not None,
             "raw filename allowlist")
        need(sha(raw) == expected_sha, "raw file hash")
        (args.output / name).write_bytes(raw)
    record["target_operations"] = native["headersSent"]
    record["target_operations_status"] = "accepted_exact_read_requests"
    record["native_outcome_sha256"] = sha(native_stdout)
    record["native_terminal_validated"] = True
    record["retained_raw_files"] = [{"name": name, "length": len(raw), "sha256": digest}
                                    for name, raw, digest in raw_files]
    root.save(record_path, record)

    all_remote = dict(staged); all_remote[stdout_name] = native_stdout; all_remote[stderr_name] = native_stderr
    cleanup_names = REMOTE_NAMES + [stdout_name, stderr_name]
    cleanup = call("set -eu\numask 077\n" +
                   f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
                   integrity(stage, all_remote, cleanup_names) +
                   "rm -- " + " ".join(shlex.quote(stage + "/" + name) for name in cleanup_names) + "\n" +
                   f"rmdir -- {shlex.quote(stage)}\n" +
                   f"test ! -e {shlex.quote(stage)}\ntest ! -L {shlex.quote(stage)}\n" +
                   "echo STAGE_ABSENT\n")
    need(cleanup == "STAGE_ABSENT\n", "cleanup receipt")
    record["cleanup_required"] = False; record["cleanup_stdout"] = cleanup; root.save(record_path, record)
    result = {"schema": "managed-usb-rt-passive-observer-wrapper-result-v1",
              "transport_accepted": True, "native_accepted": True,
              "terminal_reason": native["terminalReason"],
              "onset_observed": native["onsetObserved"], "onset_missed": native["onsetMissed"],
              "manifest_sha256": sha(manifest_raw), "native_manifest_sha256": NATIVE_MANIFEST_SHA,
              "record": str(record_path), "target_read_requests": native["headersSent"],
              "bulk_transfers": native["bulkTransfers"], "cycles_started": native["cyclesStarted"],
              "clean_cycles_completed": native["cleanCyclesCompleted"],
              "clean_cycles_discarded": native["cleanCyclesDiscarded"],
              "retained_captures": captures,
              "retained_raw_files": record["retained_raw_files"],
              "samples_sequential_not_atomic": True, "exact_event_tuple_inferred": False,
              "physical_cause_inferred": False, "physical_picture_observed": False,
              "bus_contents_altered": False, "cleanup": "STAGE_ABSENT"}
    save(args.output / "result.json", result)
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
