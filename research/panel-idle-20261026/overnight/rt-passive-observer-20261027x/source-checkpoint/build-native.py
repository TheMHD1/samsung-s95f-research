#!/usr/bin/env python3
"""Build and verify the passive observer without target or network access."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DOTNET = Path("${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet")
DOTNET_SHA = "6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36"
PARENT = HERE.parent / "managed-usb-rt-fault-context-read"
PARENT_PROGRAM_SHA = "f7418df841af9b616c198958b5b725dd7fc2434c92f5b360b65989c9da66b6a0"
PARENT_DLL_SHA = "cd80eafa03fdcf9f3cc514434aef78ccd25228bb3b5cbe058d93dcb788e32127"
ASSEMBLY = "ManagedUsbRtPassiveObserver"
DLL = HERE / "bin/Release/net6.0" / (ASSEMBLY + ".dll")
OUTPUTS = [ASSEMBLY + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json")]


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


def main():
    need(sha(DOTNET.read_bytes()) == DOTNET_SHA, "local dotnet pin")
    need(sha((PARENT / "Program.cs").read_bytes()) == PARENT_PROGRAM_SHA,
         "parent Program.cs pin")
    need(sha((PARENT / "bin/Release/net6.0/ManagedUsbRtBlockReadOnce.dll").read_bytes()) == PARENT_DLL_SHA,
         "parent DLL pin")

    first = run([str(DOTNET), "build", "-c", "Release", "--no-restore"])
    need(b"0 Warning(s)" in first.stdout and b"0 Error(s)" in first.stdout,
         "warning-free build")
    first_outputs = {name: sha((HERE / "bin/Release/net6.0" / name).read_bytes()) for name in OUTPUTS}
    second = run([str(DOTNET), "build", "-c", "Release", "--no-restore"])
    need(b"0 Warning(s)" in second.stdout and b"0 Error(s)" in second.stdout,
         "second warning-free build")
    second_outputs = {name: sha((HERE / "bin/Release/net6.0" / name).read_bytes()) for name in OUTPUTS}
    need(first_outputs == second_outputs, "managed outputs not reproducible")

    selftest = json.loads(run([str(DOTNET), str(DLL), "--self-test"]).stdout)
    need(selftest == {"selfTestsPassed": 75, "targetOperations": 0,
                      "maxTestOutputBytes": 10541}, "native self-tests")
    dry = json.loads(run([str(DOTNET), str(DLL)]).stdout)
    need(dry == {
        "schema": "managed-usb-rt-passive-observer-dry-v1",
        "dryRun": True, "targetOperations": 0, "target": "0x101",
        "cycle": ["R", "M", "C", "H", "L", "R"],
        "addresses": ["0x47012400/256", "0x470004a0/68", "0x47000bc0/16",
                      "0x4700d0e0/96", "0x47010f00/64"],
        "durationMs": 20000, "maxCycles": 80, "nominalPeriodMs": 250,
        "timeoutMs": 2000, "interfaceNumber": 2, "writes": 0, "retries": 0,
        "outputLimitBytes": 24576,
    }, "dry contract")
    refusal = run([str(DOTNET), str(DLL), "--execute"], expected=64)
    need(refusal.stdout == b"REFUSED_ARM32_ABI\n" and refusal.stderr == b"",
         "host ABI refusal")
    unknown = run([str(DOTNET), str(DLL), "--unknown"], expected=63)
    need(unknown.stdout == b"" and unknown.stderr == b"", "unknown CLI refusal")

    names = {"Program.cs", "ManagedUsbRtPassiveObserver.csproj", "build-native.py",
             "README-native.md"}
    names.update("bin/Release/net6.0/" + name for name in OUTPUTS)
    files = {}
    for name in sorted(names):
        raw = (HERE / name).read_bytes()
        files[name] = {"size": len(raw), "sha256": sha(raw)}
    manifest = {
        "schema": "managed-usb-rt-passive-observer-native-build-v1",
        "offline_only": True,
        "target_executions": 0,
        "build": {"configuration": "Release", "framework": "net6.0",
                  "dotnet_path": str(DOTNET), "dotnet_sha256": DOTNET_SHA,
                  "outputs_reproducible": True},
        "parent": {"directory": str(PARENT), "program_sha256": PARENT_PROGRAM_SHA,
                   "dll_sha256": PARENT_DLL_SHA},
        "protocol": {
            "target": "0x101", "interface": 2, "timeout_ms_per_bulk": 2000,
            "cycle": ["R", "M", "C", "H", "L", "R"],
            "duration_ms": 20000, "max_cycles": 80, "nominal_period_ms": 250,
            "writes": 0, "retries": 0,
            "requests": [
                {"id": "R", "address": "0x47012400", "length": 256,
                 "header_hex": "010100000024014700010000"},
                {"id": "M", "address": "0x470004a0", "length": 68,
                 "header_hex": "01010000a004004744000000"},
                {"id": "C", "address": "0x47000bc0", "length": 16,
                 "header_hex": "01010000c00b004710000000"},
                {"id": "H", "address": "0x4700d0e0", "length": 96,
                 "header_hex": "01010000e0d0004760000000"},
                {"id": "L", "address": "0x47010f00", "length": 64,
                 "header_hex": "01010000000f014740000000"},
            ],
        },
        "retention": {"last_fully_clean": 1, "transition": 1,
                      "post_fault_sets": 1, "current_partial": 1,
                      "output_limit_bytes": 24576},
        "tests": {"native_fake_cases": 75, "max_test_output_bytes": 10541,
                  "host_abi_refusal": True, "unknown_cli_refusal": True,
                  "default_zero_io": True},
        "files": files,
    }
    target = HERE / "native-build-manifest.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schema": manifest["schema"], "targetOperations": 0,
                      "nativeTests": 75, "maxTestOutputBytes": 10541,
                      "manifestSha256": sha(target.read_bytes())}, separators=(",", ":")))


if __name__ == "__main__":
    main()
