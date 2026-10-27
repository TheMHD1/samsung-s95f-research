#!/usr/bin/env python3
"""Rebuild and verify the fixed helper without target or network access."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DOTNET = Path("${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet")
DOTNET_SHA = "6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36"
ASSEMBLY = "ManagedUsbRtBlockReadOnce"
OUTPUTS = [ASSEMBLY + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json")]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(value, why):
    if not value:
        raise RuntimeError(why)


def run(argv, expected=0):
    result = subprocess.run(argv, cwd=HERE, capture_output=True)
    need(result.returncode == expected,
         "command failed: " + repr(argv) + " rc=" + str(result.returncode) +
         " stdout=" + result.stdout.decode(errors="replace") +
         " stderr=" + result.stderr.decode(errors="replace"))
    return result


def main():
    need(sha(DOTNET.read_bytes()) == DOTNET_SHA, "local dotnet pin")
    derivation = run([sys.executable, "build-derivative.py"])
    run([str(DOTNET), "build", "-c", "Release", "--no-restore"])
    dll = HERE / "bin/Release/net6.0" / (ASSEMBLY + ".dll")

    native_test = run([str(DOTNET), str(dll), "--self-test"])
    native_value = json.loads(native_test.stdout)
    need(native_value == {"selfTestsPassed": 34, "targetOperations": 0}, "native tests")
    dry = json.loads(run([str(DOTNET), str(dll)]).stdout)
    need(dry == {"schema": "managed-usb-rt-fault-context-read-dry-v1", "dryRun": True,
                 "targetOperations": 0, "contextAddress": "0x47010f00",
                 "contextHeaderHex": "01010000000F014740000000", "contextLength": 64,
                 "rtAddress": "0x47012400", "rtHeaderHex": "010100000024014700010000",
                 "rtLength": 256, "timeoutMs": 2000, "interfaceNumber": 2,
                 "writes": 0, "retries": 0}, "native dry contract")
    refusal = run([str(DOTNET), str(dll), "--execute"], expected=64)
    need(refusal.stdout == b"REFUSED_ARM32_ABI\n" and refusal.stderr == b"", "host refusal")
    unknown = run([str(DOTNET), str(dll), "--unknown"], expected=63)
    need(unknown.stdout == b"" and unknown.stderr == b"", "unknown CLI refusal")

    wrapper_normal = json.loads(run([sys.executable, "test-wrapper.py"]).stdout)
    wrapper_optimized = json.loads(run([sys.executable, "-O", "test-wrapper.py"]).stdout)
    expected_wrapper = {"wrapperTestsPassed": 30, "targetOperations": 0}
    need(wrapper_normal == expected_wrapper and wrapper_optimized == expected_wrapper,
         "wrapper tests")
    wrapper_dry = json.loads(run([sys.executable, "run-once.py"]).stdout)
    need(wrapper_dry["target_operations"] == 0 and wrapper_dry["writes"] == 0,
         "wrapper dry contract")

    names = {"Program.cs", "ManagedUsbRtBlockReadOnce.csproj", "build-derivative.py",
             "build-offline.py", "run-once.py", "test-wrapper.py", "root-with-margin.py",
             "README.md"}
    names.update("bin/Release/net6.0/" + name for name in OUTPUTS)
    files = {}
    for name in sorted(names):
        raw = (HERE / name).read_bytes()
        files[name] = {"size": len(raw), "sha256": sha(raw)}
    manifest = {
        "schema": "managed-usb-rt-fault-context-read-build-v1",
        "offline_only": True,
        "target_executions": 0,
        "build": {"configuration": "Release", "framework": "net6.0",
                  "dotnet_path": str(DOTNET), "dotnet_sha256": DOTNET_SHA,
                  "derivation_stdout_sha256": sha(derivation.stdout)},
        "parent": {"directory": "managed-usb-secondary-root-read-once",
                   "program_sha256": "4a725f342237a848bd835ef090a9341ae30a80c70e9798a05236d108bbffe5e4",
                   "project_sha256": "05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187"},
        "root_adapter": {"sha256": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
                         "remote_timeout_seconds": 45, "host_timeout_seconds": 75},
        "boot_id": "00000000-0000-4000-8000-000000000000",
        "protocol": {"interface": 2, "timeout_ms_per_bulk": 2000,
                     "bulk_steps": 4, "writes": 0, "retries": 0,
                     "requests": [
                         {"target": "0x101", "address": "0x47010f00", "length": 64,
                          "header_hex": "01010000000f014740000000"},
                         {"target": "0x101", "address": "0x47012400", "length": 256,
                          "header_hex": "010100000024014700010000"}]},
        "tests": {"native_fake_ops": 34, "wrapper_normal": 30,
                  "wrapper_optimized": 30, "host_abi_refusal": True,
                  "unknown_cli_refusal": True},
        "files": files,
    }
    (HERE / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schema": manifest["schema"], "targetOperations": 0,
                      "nativeTests": 34, "wrapperTestsNormal": 30,
                      "wrapperTestsOptimized": 30,
                      "manifestSha256": sha((HERE / "build-manifest.json").read_bytes())},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
