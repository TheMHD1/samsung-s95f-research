#!/usr/bin/env python3
"""Stage a hash-bound, fixed eMMC-sector reader; no target work by default."""
import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import uuid

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parent / "managed-tcon-status-read/run-status-read.py"
RUNNER_SHA = "7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a"
BOOT = "00000000-0000-4000-8000-000000000000"
DOTNET_SHA = "e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310"
NAMES = ["ManagedUsbEmmcSectorReadOnce." + s for s in
         ("dll", "deps.json", "runtimeconfig.json")]


def need(ok, why):
    if not ok:
        raise ValueError(why)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"target_operations": 0, "planned_header":
                          "03020000008a020000020000", "input_length": 512}))
        return
    need(args.output is not None and args.manifest_sha256 is not None,
         "Explicit retained output and manifest hash required")
    manifest_raw = (HERE / "build-manifest.json").read_bytes()
    need(digest(manifest_raw) == args.manifest_sha256, "Build manifest hash")
    manifest = json.loads(manifest_raw)
    need(manifest["schema"] == "usb-fixed-emmc-sector-read-build-v1", "Manifest schema")
    expected = {"Program.cs", "ManagedUsbEmmcSectorReadOnce.csproj",
                *("bin/Release/net6.0/" + n for n in NAMES)}
    need(set(manifest["files"]) == expected, "Manifest inventory")
    for name, row in manifest["files"].items():
        raw = (HERE / name).read_bytes()
        need(len(raw) == row["size"] and digest(raw) == row["sha256"], name)
    need(digest(RUNNER.read_bytes()) == RUNNER_SHA, "Root runner identity")
    spec = importlib.util.spec_from_file_location("pinned_root_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args.output.mkdir(parents=True, exist_ok=False)
    record_path = args.output / "record.json"
    remote = "/tmp/researcher-usb-emmcsector-" + uuid.uuid4().hex
    record = {"manifest_sha256": digest(manifest_raw), "remote_stage": remote,
              "deployment_script_sha256": digest(Path(__file__).read_bytes()),
              "root_runner_sha256": RUNNER_SHA,
              "request": {"target": "0x203", "address": "0x28a00", "length": 512},
              "calls": []}
    module.save(record_path, record)

    def call(command):
        return module.root(command, record, record_path)

    attempted_stage = False
    try:
        attempted_stage = True
        call("set -eu\numask 077\n"
             f'test "$(cat /proc/sys/kernel/random/boot_id)" = {BOOT}\n'
             f'test "$(sha256sum /usr/bin/dotnet | cut -d " " -f1)" = {DOTNET_SHA}\n'
             f"mkdir {shlex.quote(remote)}\necho STAGE_CREATED\n")
        for name in NAMES:
            data = (HERE / "bin/Release/net6.0" / name).read_bytes()
            encoded = base64.b64encode(data).decode("ascii")
            target = remote + "/" + name
            temp = target + ".b64"
            for start in range(0, len(encoded), 5000):
                chunk = encoded[start:start + 5000]
                call(f"set -eu\nprintf %s {shlex.quote(chunk)} >> {shlex.quote(temp)}\n")
            call("set -eu\n"
                 f"base64 -d {shlex.quote(temp)} > {shlex.quote(target)}\n"
                 f'test "$(wc -c < {shlex.quote(target)})" = {len(data)}\n'
                 f'test "$(sha256sum {shlex.quote(target)} | cut -d " " -f1)" = {digest(data)}\n'
                 f"rm {shlex.quote(temp)}\necho FILE_VERIFIED\n")
        dll = shlex.quote(remote + "/" + NAMES[0])
        # Self-tests use injected I/O only. Execute exactly once, never retry.
        command = ("set -eu\ncat /proc/sys/kernel/random/boot_id\ncat /proc/uptime\n"
                   f"/usr/bin/dotnet {dll} --self-test\n"
                   "echo ACTIVE_READ_BEGIN\nrc=0\n"
                   f"/usr/bin/dotnet {dll} --execute || rc=$?\n"
                   'echo HELPER_EXIT=$rc\ncat /proc/uptime\n')
        stdout = call(command)
        (args.output / "stdout.txt").write_text(stdout)
        record["helper_stdout_sha256"] = digest(stdout.encode())
        module.save(record_path, record)
    finally:
        if attempted_stage:
            files = [remote + "/" + n + suffix for n in NAMES for suffix in ("", ".b64")]
            clean = ("set -eu\n" + f"test ! -L {shlex.quote(remote)}\n" +
                     f"if test -d {shlex.quote(remote)}; then\n" +
                     "rm -f " + " ".join(map(shlex.quote, files)) + "\n" +
                     f"rmdir {shlex.quote(remote)}\nfi\n" +
                     f"test ! -e {shlex.quote(remote)}\necho STAGE_ABSENT\n")
            record["cleanup_stdout"] = call(clean)
            module.save(record_path, record)
    print(json.dumps({"record": str(record_path), "cleanup": record["cleanup_stdout"].strip()}))


if __name__ == "__main__":
    main()
