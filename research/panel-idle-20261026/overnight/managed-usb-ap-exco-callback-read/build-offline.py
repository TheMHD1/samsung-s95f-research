#!/usr/bin/env python3
"""Rebuild and verify the fixed AP_EXCO callback-source reader offline."""

import hashlib
import json
from pathlib import Path
import subprocess
import struct
import sys

HERE = Path(__file__).resolve().parent
DOTNET = Path("${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet")
DOTNET_SHA = "6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36"
ASSEMBLY = "ManagedUsbRtBlockReadOnce"
OUTPUTS = [ASSEMBLY + x for x in (".dll", ".deps.json", ".runtimeconfig.json")]
OVERNIGHT = HERE.parent
EVIDENCE = {
    "ap-exco-source-read-20261027m/ordinary-provenance-evidence-manifest.json": "26b5cc4faa8a3c03917b92ac48254ba359362bd201830cdf29fb229154b3dd0b",
    "ap-exco-source-read-20261027m/source-lineage-erratum.md": "d2e4492bbdb7042479ebfed6a5e2300feb5f97387d68700f14924651f9c1030f",
    "ap-exco-source-read-20261027m/verify-pointer-layout-followup.py": "ccbc619eb4ddba2078f162bc1de520f9cb90aec0a9422d13015cbf13d393b1cd",
    "code-map-qualified-followup-20261027n/capture-once/result.json": "3119fb85c08b970794adcdf975313d825c80a301b995e293f2fc5cb458df57c1",
    "code-map-qualified-followup-20261027n/capture-once/window-a.bin": "8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49",
    "code-map-qualified-followup-20261027n/capture-once/window-b.bin": "0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb",
    "code-map-qualified-followup-20261027n/capture-once/window-c.bin": "035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8",
}


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
    object_base, object_extent, tail_start = 0x450158A8, 0x3EC, 0x45015C70
    need(tail_start - object_base == 0x3C8, "tail object offset")
    need(tail_start + 0x10 == object_base + 0x3D8, "+3d8 response offset")
    need(tail_start + 32 <= object_base + object_extent, "tail inside object extent")
    for address, length, header in (
        (0x470002C0, 32, "01010000c002004720000000"),
        (object_base, 16, "01010000a858014510000000"),
        (tail_start, 32, "01010000705c014520000000"),
    ):
        need(struct.pack("<III", 0x101, address, length).hex() == header,
             "derived fixed header")
    for relative, expected in EVIDENCE.items():
        need(sha((OVERNIGHT / relative).read_bytes()) == expected, "evidence pin " + relative)
    derivation = run([sys.executable, "build-derivative.py"])
    run([str(DOTNET), "restore", "--configfile", "NuGet.Config"])
    run([str(DOTNET), "build", "-c", "Release", "--no-restore"])
    dll = HERE / "bin/Release/net6.0" / (ASSEMBLY + ".dll")
    native = json.loads(run([str(DOTNET), str(dll), "--self-test"]).stdout)
    need(native == {"selfTestsPassed": 47, "targetOperations": 0}, "native tests")
    dry = json.loads(run([str(DOTNET), str(dll)]).stdout)
    need(dry == {"schema": "managed-usb-ap-exco-callback-read-dry-v1", "dryRun": True,
                 "targetOperations": 0,
                 "requests": [
                     {"address": "0x470002c0", "headerHex": "01010000C002004720000000", "length": 32},
                     {"address": "0x450158a8", "headerHex": "01010000A858014510000000", "length": 16},
                     {"address": "0x45015c70", "headerHex": "01010000705C014520000000", "length": 32},
                 ],
                 "timeoutMs": 2000, "interfaceNumber": 2, "writes": 0, "retries": 0},
         "native dry")
    refusal = run([str(DOTNET), str(dll), "--execute"], 64)
    need(refusal.stdout == b"REFUSED_ARM32_ABI\n" and refusal.stderr == b"", "ABI refusal")
    unknown = run([str(DOTNET), str(dll), "--bad"], 63)
    need(unknown.stdout == b"" and unknown.stderr == b"", "CLI refusal")
    expected_tests = {"wrapperTestsPassed": 24, "targetOperations": 0}
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
    manifest = {"schema": "managed-usb-ap-exco-callback-read-build-v1", "offline_only": True,
                "target_executions": 0,
                "build": {"framework": "net6.0", "configuration": "Release",
                          "dotnet_path": str(DOTNET), "dotnet_sha256": DOTNET_SHA,
                          "nuget_sources": [], "derivation_stdout_sha256": sha(derivation.stdout)},
                "parent": {"directory": "managed-usb-ap-exco-source-read",
                           "manifest_sha256": "3222c56b1b80749123a2b360ebae9ffbf44779cf748061737774c93fc153fa51",
                           "program_sha256": "99fe549a5b4c408e6c83a44675cdd7c5f975231f2495e07b1bc9481939d6dc60",
                           "wrapper_sha256": "79341a52a0c69031a2d489d35c80997997b80b75661814637f6de27836221106"},
                "boot_id": "00000000-0000-4000-8000-000000000000",
                "root_adapter": {"sha256": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
                                 "remote_timeout_seconds": 45, "host_timeout_seconds": 75},
                "protocol": {"target": "0x101", "bulk_steps": 6,
                             "requests": [{"address": "0x470002c0", "length": 32,
                                           "header_hex": "01010000c002004720000000"},
                                          {"address": "0x450158a8", "length": 16,
                                           "header_hex": "01010000a858014510000000"},
                                          {"address": "0x45015c70", "length": 32,
                                           "header_hex": "01010000705c014520000000"}],
                             "timeout_ms_per_bulk": 2000, "writes": 0, "retries": 0},
                "object_geometry": {"base": "0x450158a8", "extent": 1004,
                                    "inclusive_end": "0x45015c93",
                                    "tail_window_start_offset": 968,
                                    "tail_window_end_offset": 999},
                "interpretation": {"pointer_offset": 12, "expected_pointer": "0x450158a8",
                                   "source_byte_zero_offset": 0,
                                   "source_byte_one_offset": 1,
                                   "source_byte_3d8_tail_offset": 16,
                                   "scope": "conditional-local-pointer-binding-sequential-only",
                                   "samples_atomic": False, "live_tuple_inferred": False,
                                   "ordinary_object_default_comparison": False,
                                   "current_executing_body_proved": False,
                                   "whole_core_identity_proved": False,
                                   "pointer_mismatch_preserves_raw": True,
                                   "late_or_partial_failure_preserves_prior_exact_windows": True},
                "evidence_pins": EVIDENCE,
                "tests": {"native_fake_ops": 47, "wrapper_normal": 24,
                          "wrapper_optimized": 24, "host_abi_refusal": True,
                          "unknown_cli_refusal": True}, "files": files}
    (HERE / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schema": manifest["schema"], "targetOperations": 0,
                      "nativeTests": 47, "wrapperTests": 24,
                      "manifestSha256": sha((HERE / "build-manifest.json").read_bytes())},
                     separators=(",", ":")))


if __name__ == "__main__": main()
