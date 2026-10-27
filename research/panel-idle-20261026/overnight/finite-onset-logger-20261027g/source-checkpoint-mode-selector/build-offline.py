#!/usr/bin/env python3
"""Rebuild and verify the fixed mode reader entirely offline."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DOTNET = Path("${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet")
DOTNET_SHA = "6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36"
ASSEMBLY = "ManagedUsbRtBlockReadOnce"
OUTPUTS = [ASSEMBLY + x for x in (".dll", ".deps.json", ".runtimeconfig.json")]


def sha(raw): return hashlib.sha256(raw).hexdigest()


def need(ok, why):
    if not ok: raise RuntimeError(why)


def run(argv, expected=0):
    result = subprocess.run(argv, cwd=HERE, capture_output=True)
    need(result.returncode == expected,
         f"command {argv!r} rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}")
    return result


def main():
    need(sha(DOTNET.read_bytes()) == DOTNET_SHA, "dotnet pin")
    derivation = run([sys.executable, "build-derivative.py"])
    run([str(DOTNET), "restore", "--configfile", "NuGet.Config"])
    run([str(DOTNET), "build", "-c", "Release", "--no-restore"])
    dll = HERE / "bin/Release/net6.0" / (ASSEMBLY + ".dll")
    native = json.loads(run([str(DOTNET), str(dll), "--self-test"]).stdout)
    need(native == {"selfTestsPassed": 35, "targetOperations": 0}, "native tests")
    dry = json.loads(run([str(DOTNET), str(dll)]).stdout)
    need(dry == {"schema": "managed-usb-rt-mode-read-dry-v1", "dryRun": True,
                 "targetOperations": 0, "modeAddress": "0x470004a0",
                 "modeHeaderHex": "01010000A004004744000000", "modeLength": 68,
                 "alternateAddress": "0x47000bc0",
                 "alternateHeaderHex": "01010000C00B004710000000", "alternateLength": 16,
                 "timeoutMs": 2000, "interfaceNumber": 2, "writes": 0, "retries": 0},
         "native dry")
    refusal = run([str(DOTNET), str(dll), "--execute"], 64)
    need(refusal.stdout == b"REFUSED_ARM32_ABI\n" and refusal.stderr == b"", "ABI refusal")
    unknown = run([str(DOTNET), str(dll), "--bad"], 63)
    need(unknown.stdout == b"" and unknown.stderr == b"", "CLI refusal")
    expected_tests = {"wrapperTestsPassed": 22, "targetOperations": 0}
    need(json.loads(run([sys.executable, "test-wrapper.py"]).stdout) == expected_tests, "wrapper normal")
    need(json.loads(run([sys.executable, "-O", "test-wrapper.py"]).stdout) == expected_tests, "wrapper optimized")

    names = {"Program.cs", "ManagedUsbRtBlockReadOnce.csproj", "NuGet.Config",
             "build-derivative.py", "build-offline.py", "run-once.py", "test-wrapper.py",
             "root-with-margin.py", "README.md"}
    names.update("bin/Release/net6.0/" + name for name in OUTPUTS)
    files = {}
    for name in sorted(names):
        raw = (HERE / name).read_bytes()
        files[name] = {"size": len(raw), "sha256": sha(raw)}
    manifest = {"schema": "managed-usb-rt-mode-read-build-v1", "offline_only": True,
                "target_executions": 0,
                "build": {"framework": "net6.0", "configuration": "Release",
                          "dotnet_path": str(DOTNET), "dotnet_sha256": DOTNET_SHA,
                          "nuget_sources": [], "derivation_stdout_sha256": sha(derivation.stdout)},
                "parent": {"directory": "managed-usb-rt-fault-context-read",
                           "program_sha256": "f7418df841af9b616c198958b5b725dd7fc2434c92f5b360b65989c9da66b6a0",
                           "wrapper_sha256": "93af800b0e4103a03d268680cb13b6ea6ed3c2d4ceeead79625f75b10b584c1a"},
                "boot_id": "00000000-0000-4000-8000-000000000000",
                "root_adapter": {"sha256": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
                                 "remote_timeout_seconds": 45, "host_timeout_seconds": 75},
                "protocol": {"target": "0x101", "bulk_steps": 4,
                             "requests": [{"address": "0x470004a0", "length": 68,
                                           "header_hex": "01010000a004004744000000"},
                                          {"address": "0x47000bc0", "length": 16,
                                           "header_hex": "01010000c00b004710000000"}],
                             "timeout_ms_per_bulk": 2000, "writes": 0, "retries": 0},
                "interpretation": {"mode_aa_offset": 10, "mode_ac_offset": 12,
                                   "root_offset": 64, "expected_root": "0x20010000",
                                   "root_mismatch_preserves_raw": True,
                                   "alternate_window": "raw-candidate-only"},
                "tests": {"native_fake_ops": 35, "wrapper_normal": 22,
                          "wrapper_optimized": 22, "host_abi_refusal": True,
                          "unknown_cli_refusal": True}, "files": files}
    (HERE / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schema": manifest["schema"], "targetOperations": 0,
                      "nativeTests": 35, "wrapperTests": 22,
                      "manifestSha256": sha((HERE / "build-manifest.json").read_bytes())},
                     separators=(",", ":")))


if __name__ == "__main__": main()
