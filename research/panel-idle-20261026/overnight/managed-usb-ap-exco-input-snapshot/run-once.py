#!/usr/bin/env python3
"""Stage and execute the fixed AP_EXCO input snapshot; dry by default."""

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
ROOT_ADAPTER_SHA = "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a"
BOOT = "00000000-0000-4000-8000-000000000000"
DOTNET_SHA = "e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310"
SCHEMA = "managed-usb-ap-exco-input-snapshot-build-v1"
ASSEMBLY = "ManagedUsbRtBlockReadOnce"
REMOTE_NAMES = [ASSEMBLY + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json")]
MAX_NATIVE_STDOUT = 16384
MAX_NATIVE_STDERR = 2048


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def bad(value):
        raise ValueError("non-JSON constant " + value)
    return json.loads(raw, parse_constant=bad)


def load_root():
    need(sha(ROOT_ADAPTER.read_bytes()) == ROOT_ADAPTER_SHA, "root adapter pin")
    spec = importlib.util.spec_from_file_location("ap_exco_input_snapshot_root_transport", ROOT_ADAPTER)
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
    manifest_raw = (HERE / "build-manifest.json").read_bytes()
    need(sha(manifest_raw) == expected_manifest_sha, "reviewed manifest pin")
    manifest = strict_json(manifest_raw)
    need(manifest.get("schema") == SCHEMA, "manifest schema")
    expected = {"Program.cs", "ManagedUsbRtBlockReadOnce.csproj", "NuGet.Config", "build-derivative.py", "build-offline.py",
                "run-once.py", "test-wrapper.py", "root-with-margin.py", "README.md"}
    expected.update("bin/Release/net6.0/" + name for name in REMOTE_NAMES)
    files = manifest.get("files")
    need(isinstance(files, dict) and set(files) == expected, "manifest inventory")
    for name, row in files.items():
        raw = (HERE / name).read_bytes()
        need(row == {"size": len(raw), "sha256": sha(raw)}, "local pin " + name)
    staged = {name: (HERE / "bin/Release/net6.0" / name).read_bytes()
              for name in REMOTE_NAMES}
    return manifest_raw, staged


def parse_lines_with_gc(text):
    rows = []
    gc = []
    for line in text.splitlines():
        if line.startswith("{"):
            rows.append(strict_json(line))
        elif line.startswith("[GC_INFO] "):
            gc.append(line)
        else:
            need(False, "unclassified native output")
    need(len(gc) <= 32, "GC line bound")
    return rows, gc


def parse_selftest(text):
    rows, _ = parse_lines_with_gc(text)
    need(len(rows) == 1 and rows[0] == {"selfTestsPassed": 48, "targetOperations": 0},
         "self-test contract")


def parse_native(text):
    rows, gc = parse_lines_with_gc(text)
    need(len(rows) == 1 and isinstance(rows[0], dict), "one native outcome")
    value = rows[0]
    need(value.get("Schema") == "managed-usb-ap-exco-input-snapshot-v1", "native schema")
    need(value.get("Stage") == "complete" and value.get("ProtocolPhase") == "ReadyForHeader", "terminal phase")
    for key in ("Opened", "Claimed", "Released", "Closed", "Accepted", "PointerMatches", "InterpretationAccepted"):
        need(value.get(key) is True, "native " + key)
    need(value.get("PhysicalPictureObserved") is False and value.get("BusContentsAltered") is False, "bounded claims")
    pointer = base64.b64decode(value.get("PointerBase64", ""), validate=True)
    ordinary = base64.b64decode(value.get("OrdinaryBase64", ""), validate=True)
    derived = base64.b64decode(value.get("DerivedBase64", ""), validate=True)
    need(len(pointer) == 32 and sha(pointer) == value.get("PointerSha256"), "pointer raw")
    need(len(ordinary) == 824 and sha(ordinary) == value.get("OrdinarySha256"), "ordinary raw")
    need(len(derived) == 1004 and sha(derived) == value.get("DerivedSha256"), "derived raw")
    op, dp = int.from_bytes(pointer[4:8], "little"), int.from_bytes(pointer[12:16], "little")
    need((op, dp) == (0x4500FF14, 0x450158A8), "pointer anchors")
    u16 = lambda raw, offset: int.from_bytes(raw[offset:offset + 2], "little")
    decoded = {"ordinary_gate_ca": u16(ordinary, 0xCA), "ordinary_gate_116": u16(ordinary, 0x116),
               "ordinary_x_10a": u16(ordinary, 0x10A), "ordinary_x_10c": u16(ordinary, 0x10C),
               "ordinary_output_e6": u16(ordinary, 0xE6), "ordinary_output_2fc": u16(ordinary, 0x2FC),
               "ordinary_counter_300": u16(ordinary, 0x300), "ordinary_counter_302": u16(ordinary, 0x302),
               "derived_byte_zero": derived[0], "derived_byte_one": derived[1], "derived_byte_3d8": derived[0x3D8]}
    fields = (("ordinary_gate_ca", "OrdinaryGateCa"), ("ordinary_gate_116", "OrdinaryGate116"),
              ("ordinary_x_10a", "OrdinaryX10A"), ("ordinary_x_10c", "OrdinaryX10C"),
              ("ordinary_output_e6", "OrdinaryOutputE6"), ("ordinary_output_2fc", "OrdinaryOutput2Fc"),
              ("ordinary_counter_300", "OrdinaryCounter300"), ("ordinary_counter_302", "OrdinaryCounter302"),
              ("derived_byte_zero", "DerivedByteZero"), ("derived_byte_one", "DerivedByteOne"),
              ("derived_byte_3d8", "DerivedByte3D8"))
    for key, native_key in fields: need(value.get(native_key) == decoded[key], "decoded " + key)
    need(value.get("OrdinaryPointer") == op and value.get("DerivedPointer") == dp and
         value.get("Interpretation") == "pointer-gated-sequential-object-snapshot", "interpretation")
    expected = [("open", "LOCAL", 0), ("claim", "LOCAL", 0), ("pointer-header", "OUT", 12),
                ("pointer-data", "IN", 32), ("ordinary-header", "OUT", 12), ("ordinary-data", "IN", 824),
                ("derived-header", "OUT", 12), ("derived-data", "IN", 1004),
                ("release", "LOCAL", 0), ("close", "LOCAL", 0)]
    steps = value.get("Steps"); need(isinstance(steps, list) and len(steps) == 10, "steps")
    for row, (name, direction, count) in zip(steps, expected):
        need(row.get("Name") == name and row.get("Direction") == direction and row.get("Expected") == count and
             row.get("Error") is None, "step " + name)
        if direction in ("OUT", "IN") or name in ("claim", "release", "close"):
            need(row.get("Count") == count and row.get("Errno") == 0, "exact " + name)
        else: need(isinstance(row.get("Count"), int) and row.get("Count") >= 0 and row.get("Errno") == 0, "open")
    return value, pointer, ordinary, derived, decoded, gc


def parse_envelope(text):
    lines = text.splitlines()
    markers = ["META_BEGIN", "META_END", "STDOUT_B64_BEGIN", "STDOUT_B64_END",
               "STDERR_B64_BEGIN", "STDERR_B64_END", "EXECUTE_COMPLETE"]
    for marker in markers:
        need(lines.count(marker) == 1, "envelope marker " + marker)
    mi, me = lines.index("META_BEGIN"), lines.index("META_END")
    so, se = lines.index("STDOUT_B64_BEGIN"), lines.index("STDOUT_B64_END")
    eo, ee = lines.index("STDERR_B64_BEGIN"), lines.index("STDERR_B64_END")
    complete = lines.index("EXECUTE_COMPLETE")
    need(mi == 0 and me == 9 and so == 10 and se + 1 == eo and ee + 1 == complete and
         complete == len(lines) - 1, "exact contiguous envelope")
    meta = lines[mi + 1:me]
    need(len(meta) == 8, "metadata extent")
    boot, uptime, exit_text, stdout_size, stdout_sha, stderr_size, stderr_sha, inventory = meta
    need(boot == BOOT and re.fullmatch(r"[0-9.]+ [0-9.]+", uptime) is not None,
         "execution identity")
    need(exit_text in ("0", "1", "63", "64"), "native exit")
    need(stdout_size.isdigit() and stderr_size.isdigit(), "native size fields")
    need(int(stdout_size) <= MAX_NATIVE_STDOUT and int(stderr_size) <= MAX_NATIVE_STDERR,
         "native output bound")
    need(re.fullmatch(r"[0-9a-f]{64}", stdout_sha) is not None and
         re.fullmatch(r"[0-9a-f]{64}", stderr_sha) is not None, "native hashes")
    need(inventory == "INVENTORY_OK", "terminal inventory")
    stdout = base64.b64decode("".join(lines[so + 1:se]), validate=True)
    stderr = base64.b64decode("".join(lines[eo + 1:ee]), validate=True)
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
        print(json.dumps({"schema": "managed-usb-ap-exco-input-snapshot-wrapper-dry-v1",
                          "target_operations": 0,
                          "requests": [{"target": "0x101", "address": "0x470002c0", "length": 32},
                                       {"target": "0x101", "address": "0x4500ff14", "length": 824},
                                       {"target": "0x101", "address": "0x450158a8", "length": 1004}],
                          "writes": 0, "retries": 0}, separators=(",", ":")))
        return
    need(args.output is not None and args.output.is_absolute(), "absolute output required")
    need(not args.output.exists(), "fresh output required")
    manifest_raw, staged = load_contract(args.manifest_sha256)
    args.output.mkdir(parents=True, exist_ok=False)
    root = load_root()
    stage = "/tmp/researcher-ap-exco-input-" + uuid.uuid4().hex
    record_path = args.output / "record.json"
    record = {"schema": "managed-usb-ap-exco-input-snapshot-wrapper-record-v1",
              "manifest_sha256": sha(manifest_raw),
              "wrapper_sha256": sha(Path(__file__).read_bytes()),
              "root_adapter_sha256": ROOT_ADAPTER_SHA, "expected_boot_id": BOOT,
              "remote_stage": stage, "calls": [], "target_operations": 0,
              "native_invocations": 0, "no_retry": True, "cleanup_required": True,
              "requests": [{"target": "0x101", "address": "0x470002c0", "length": 32},
                           {"target": "0x101", "address": "0x4500ff14", "length": 824},
                           {"target": "0x101", "address": "0x450158a8", "length": 1004}]}
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
        raw = staged[name]
        target = stage + "/" + name
        encoded = base64.b64encode(raw).decode("ascii")
        raw_offset = 0
        for offset in range(0, len(encoded), 5000):
            chunk = encoded[offset:offset + 5000]
            decoded = base64.b64decode(chunk, validate=True)
            initialize = (f"test ! -e {shlex.quote(target)}\n"
                          f"test ! -L {shlex.quote(target)}\n"
                          f": > {shlex.quote(target)}\n"
                          f"chmod 600 {shlex.quote(target)}\n") if offset == 0 else ""
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
                    integrity(stage, staged) +
                    f"/usr/bin/dotnet {dll} --self-test\n")
    (args.output / "selftest.stdout.txt").write_text(selftest)
    parse_selftest(selftest)
    record["selftest_sha256"] = sha(selftest.encode())
    root.save(record_path, record)

    stdout_name, stderr_name = "native.stdout", "native.stderr"
    stdout_remote, stderr_remote = stage + "/" + stdout_name, stage + "/" + stderr_name
    command = ("set -eu\numask 077\n" +
               f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
               integrity(stage, staged) +
               f"test ! -e {shlex.quote(stdout_remote)}\ntest ! -L {shlex.quote(stdout_remote)}\n" +
               f"test ! -e {shlex.quote(stderr_remote)}\ntest ! -L {shlex.quote(stderr_remote)}\n" +
               f": > {shlex.quote(stdout_remote)}\n: > {shlex.quote(stderr_remote)}\n" +
               f"chmod 600 {shlex.quote(stdout_remote)} {shlex.quote(stderr_remote)}\n" +
               "set +e\n" + f"/usr/bin/dotnet {dll} --execute > {shlex.quote(stdout_remote)} 2> {shlex.quote(stderr_remote)}\n" +
               "native_rc=$?\nset -e\n" +
               file_guard(stdout_remote) + file_guard(stderr_remote) +
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
    (args.output / "native.stdout.txt").write_bytes(native_stdout)
    (args.output / "native.stderr.txt").write_bytes(native_stderr)
    record["terminal"] = terminal
    record["terminal_validated"] = True
    root.save(record_path, record)

    # Cleanup is permitted only after the retained native bytes prove a known,
    # complete, ReadyForHeader result.  Any rejected/partial result keeps the
    # private stage and the complete authenticated call record for review.
    need(terminal["exit_code"] == 0 and native_stderr == b"", "native terminal status")
    native, pointer, ordinary, derived, decoded, gc = parse_native(native_stdout.decode("utf-8"))
    (args.output / "pointer-window.bin").write_bytes(pointer)
    (args.output / "ordinary-ap-exco-prefix.bin").write_bytes(ordinary)
    (args.output / "derived-ap-exco.bin").write_bytes(derived)
    record["target_operations"] = 3
    record["target_operations_status"] = "accepted_exact"
    record["native_outcome_sha256"] = sha(native_stdout)
    record["native_terminal_validated"] = True
    root.save(record_path, record)

    all_remote = dict(staged)
    all_remote[stdout_name] = native_stdout
    all_remote[stderr_name] = native_stderr
    cleanup_names = REMOTE_NAMES + [stdout_name, stderr_name]
    cleanup = call("set -eu\numask 077\n" +
                   f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n' +
                   integrity(stage, all_remote, cleanup_names) +
                   "rm -- " + " ".join(shlex.quote(stage + "/" + n) for n in cleanup_names) + "\n" +
                   f"rmdir -- {shlex.quote(stage)}\n" +
                   f"test ! -e {shlex.quote(stage)}\ntest ! -L {shlex.quote(stage)}\n" +
                   "echo STAGE_ABSENT\n")
    need(cleanup == "STAGE_ABSENT\n", "cleanup receipt")
    record["cleanup_required"] = False
    record["cleanup_stdout"] = cleanup
    root.save(record_path, record)
    result = {"schema": "managed-usb-ap-exco-input-snapshot-wrapper-result-v1",
              "transport_accepted": True, "interpretation_accepted": True,
              "interpretation": native["Interpretation"], "manifest_sha256": sha(manifest_raw),
              "record": str(record_path), "pointer_raw_sha256": sha(pointer), "pointer_raw_length": len(pointer),
              "ordinary_raw_sha256": sha(ordinary), "ordinary_raw_length": len(ordinary),
              "derived_raw_sha256": sha(derived), "derived_raw_length": len(derived),
              "ordinary_pointer_raw": native["OrdinaryPointer"], "derived_pointer_raw": native["DerivedPointer"],
              "pointer_matches_expected": True, "decoded": decoded,
              "derived_composite_recomputed": bool((decoded["ordinary_output_e6"] & 1) or decoded["ordinary_output_2fc"]),
              "derived_composite_matches": decoded["derived_byte_3d8"] == int(bool((decoded["ordinary_output_e6"] & 1) or decoded["ordinary_output_2fc"])),
              "samples_sequential_not_atomic": True, "event_time_inferred": False,
              "physical_cause_inferred": False, "native_gc_lines": len(gc),
              "cleanup": "STAGE_ABSENT", "bus_contents_altered": False, "physical_picture_observed": False}
    save(args.output / "result.json", result)
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
