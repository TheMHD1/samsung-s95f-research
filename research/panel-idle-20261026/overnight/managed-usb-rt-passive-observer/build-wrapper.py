#!/usr/bin/env python3
"""Build and verify the passive-observer host wrapper without target access."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NATIVE_MANIFEST = HERE / "native-build-manifest.json"
NATIVE_MANIFEST_SHA = "44f74a8a695f41ed21d68a7a36e13934eebc74050bf991c634e6015ec88043a2"
SCHEMA = "managed-usb-rt-passive-observer-wrapper-build-v1"
REMOTE_NAMES = ["ManagedUsbRtPassiveObserver" + suffix
                for suffix in (".dll", ".deps.json", ".runtimeconfig.json")]
NATIVE_FILES = {
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


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(value, why):
    if not value:
        raise RuntimeError(why)


def run(argv, expected=0):
    result = subprocess.run(argv, cwd=HERE, capture_output=True)
    need(result.returncode == expected,
         "command failed " + repr(argv) + " rc=" + str(result.returncode) +
         " stdout=" + result.stdout.decode(errors="replace") +
         " stderr=" + result.stderr.decode(errors="replace"))
    return result


def file_rows(names):
    rows = {}
    for name in sorted(names):
        raw = (HERE / name).read_bytes()
        rows[name] = {"size": len(raw), "sha256": sha(raw)}
    return rows


def manifest_bytes(files):
    value = {
        "schema": SCHEMA,
        "offline_only": True,
        "target_executions": 0,
        "native_build_manifest_sha256": NATIVE_MANIFEST_SHA,
        "transport": {"remote_timeout_seconds": 45, "host_timeout_seconds": 75,
                      "max_command_bytes": 8192, "max_response_bytes": 65536,
                      "native_stdout_max_bytes": 24576, "native_stderr_max_bytes": 2048,
                      "native_invocations": 1, "retries": 0},
        "observer": {"duration_ms": 20000, "max_cycles": 80,
                     "nominal_period_ms": 250, "target": "0x101", "writes": 0,
                     "cycle": ["R", "M", "C", "H", "L", "R"]},
        "tests": {"wrapper_cases_normal": 55, "wrapper_cases_optimized": 55,
                  "target_operations": 0, "generated_shell_syntax": True,
                  "strict_native_fixtures": 4},
        "files": files,
    }
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main():
    native_before = file_rows(NATIVE_FILES)
    native_raw = NATIVE_MANIFEST.read_bytes()
    need(sha(native_raw) == NATIVE_MANIFEST_SHA, "native manifest pin")
    native = json.loads(native_raw)
    need(native.get("schema") == "managed-usb-rt-passive-observer-native-build-v1",
         "native manifest schema")
    for name in NATIVE_FILES - {"native-build-manifest.json"}:
        need(native.get("files", {}).get(name) == native_before[name],
             "native inherited file " + name)

    all_files = NATIVE_FILES | FIXTURES | HOST_FILES
    files = file_rows(all_files)
    raw = manifest_bytes(files)
    target = HERE / "wrapper-build-manifest.json"
    target.write_bytes(raw)
    need(target.read_bytes() == manifest_bytes(file_rows(all_files)),
         "wrapper manifest reproducibility")

    run([sys.executable, "-m", "py_compile", "run-once.py", "test-wrapper.py",
         "root-with-margin.py", "build-wrapper.py"])
    normal = json.loads(run([sys.executable, "test-wrapper.py"]).stdout)
    optimized = json.loads(run([sys.executable, "-O", "test-wrapper.py"]).stdout)
    expected = {"wrapperTestsPassed": 55, "targetOperations": 0}
    need(normal == expected and optimized == expected, "wrapper tests")
    dry = json.loads(run([sys.executable, "run-once.py"]).stdout)
    need(dry.get("target_operations") == 0 and dry.get("writes") == 0 and
         dry.get("retries") == 0, "dry contract")

    spec = importlib.util.spec_from_file_location("verified_rt_passive_wrapper", HERE / "run-once.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    loaded_raw, staged = module.load_contract(sha(raw))
    need(loaded_raw == raw and set(staged) == set(REMOTE_NAMES), "manifest load contract")
    need(file_rows(NATIVE_FILES) == native_before and sha(NATIVE_MANIFEST.read_bytes()) == NATIVE_MANIFEST_SHA,
         "native files remained unchanged")

    final_raw = manifest_bytes(file_rows(all_files))
    need(final_raw == raw, "post-test manifest stability")
    print(json.dumps({"schema": SCHEMA, "targetOperations": 0,
                      "wrapperTestsNormal": 55, "wrapperTestsOptimized": 55,
                      "manifestSha256": sha(raw)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
