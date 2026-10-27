#!/usr/bin/env python3
"""Rebuild and verify the fixed AP_EXCO source reader entirely offline."""

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
    need(native == {"selfTestsPassed": 47, "targetOperations": 0}, "native tests")
    dry = json.loads(run([str(DOTNET), str(dll)]).stdout)
    need(dry == {"schema": "managed-usb-ap-exco-source-read-dry-v1", "dryRun": True,
                 "targetOperations": 0,
                 "requests": [
                     {"address": "0x470002c0", "headerHex": "01010000C002004720000000", "length": 32},
                     {"address": "0x4500ff14", "headerHex": "0101000014FF004510000000", "length": 16},
                     {"address": "0x450102e0", "headerHex": "01010000E002014520000000", "length": 32},
                 ],
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
    manifest = {"schema": "managed-usb-ap-exco-source-read-build-v1", "offline_only": True,
                "target_executions": 0,
                "build": {"framework": "net6.0", "configuration": "Release",
                          "dotnet_path": str(DOTNET), "dotnet_sha256": DOTNET_SHA,
                          "nuget_sources": [], "derivation_stdout_sha256": sha(derivation.stdout)},
                "parent": {"directory": "managed-usb-rt-mode-read",
                           "manifest_sha256": "4d3e0ac655aff8eac8d1d2f3835d96597f74d5c45c751e67323ea36805663446",
                           "program_sha256": "6770c29a29cd0751448f2c9ba6da8dbfdd00d01765914df13df2d87bab7d9e63",
                           "wrapper_sha256": "67a485873f318323f89d337cdecd8a83c0c3238f5bfb8ac9b861b253e1f954ad"},
                "boot_id": "00000000-0000-4000-8000-000000000000",
                "root_adapter": {"sha256": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
                                 "remote_timeout_seconds": 45, "host_timeout_seconds": 75},
                "protocol": {"target": "0x101", "bulk_steps": 6,
                             "requests": [{"address": "0x470002c0", "length": 32,
                                           "header_hex": "01010000c002004720000000"},
                                          {"address": "0x4500ff14", "length": 16,
                                           "header_hex": "0101000014ff004510000000"},
                                          {"address": "0x450102e0", "length": 32,
                                           "header_hex": "01010000e002014520000000"}],
                             "timeout_ms_per_bulk": 2000, "writes": 0, "retries": 0},
                "interpretation": {"pointer_offset": 12, "expected_pointer": "0x4500ff14",
                                   "source_byte_zero_offset": 0,
                                   "source_byte_3d8_tail_offset": 12,
                                   "scope": "conditional-local-pointer-binding-sequential-only",
                                   "samples_atomic": False, "live_tuple_inferred": False,
                                   "pointer_mismatch_preserves_raw": True,
                                   "late_or_partial_failure_preserves_prior_exact_windows": True},
                "tests": {"native_fake_ops": 47, "wrapper_normal": 22,
                          "wrapper_optimized": 22, "host_abi_refusal": True,
                          "unknown_cli_refusal": True}, "files": files}
    (HERE / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schema": manifest["schema"], "targetOperations": 0,
                      "nativeTests": 47, "wrapperTests": 22,
                      "manifestSha256": sha((HERE / "build-manifest.json").read_bytes())},
                     separators=(",", ":")))


if __name__ == "__main__": main()
