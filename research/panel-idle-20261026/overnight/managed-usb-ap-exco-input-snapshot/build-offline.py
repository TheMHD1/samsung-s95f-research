#!/usr/bin/env python3
"""Rebuild and verify the fixed AP_EXCO input snapshot offline."""

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
OUTPUTS = [ASSEMBLY + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json")]
OVERNIGHT = HERE.parent
EVIDENCE = {
    "ap-exco-helper-inputs-20261027s/ap-exco-helper-inputs.md":
        "17068bd31de065a2720ca027498da41517e5d214e0dd633272ed144c29cabdb6",
    "ap-exco-helper-inputs-20261027s/verify-helper-inputs.py":
        "ae0d25c648e8b777f3829cd2e13fc563ec5f26cb0514c7a89b542b9bac1283bd",
    "ap-exco-input-snapshot-20261027w/read-plan.md":
        "5034fba44f9c91182b65ece200149f8c2b4320b9c4c9d73c20058dd28336db11",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def run(argv, expected=0):
    result = subprocess.run(argv, cwd=HERE, capture_output=True)
    need(result.returncode == expected,
         f"command {argv!r} rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}")
    return result


def main():
    need(sha(DOTNET.read_bytes()) == DOTNET_SHA, "dotnet pin")
    geometry = (
        (0x470002C0, 32, "01010000c002004720000000"),
        (0x4500FF14, 824, "0101000014ff004538030000"),
        (0x450158A8, 1004, "01010000a8580145ec030000"),
    )
    for address, length, header in geometry:
        need(struct.pack("<III", 0x101, address, length).hex() == header, "derived fixed header")
    need(824 <= 0x33A and 0x306 + 2 <= 824, "ordinary allocation and field coverage")
    need(1004 == 0x3EC and 0x3D8 < 1004, "derived allocation and field coverage")
    for relative, expected in EVIDENCE.items():
        need(sha((OVERNIGHT / relative).read_bytes()) == expected, "evidence pin " + relative)

    derivation = run([sys.executable, "build-derivative.py"])
    run([str(DOTNET), "restore", "--configfile", "NuGet.Config"])
    run([str(DOTNET), "build", "-c", "Release", "--no-restore"])
    dll = HERE / "bin/Release/net6.0" / (ASSEMBLY + ".dll")
    native = json.loads(run([str(DOTNET), str(dll), "--self-test"]).stdout)
    need(native == {"selfTestsPassed": 48, "targetOperations": 0}, "native tests")
    dry = json.loads(run([str(DOTNET), str(dll)]).stdout)
    need(dry == {"schema": "managed-usb-ap-exco-input-snapshot-dry-v1", "dryRun": True,
                 "targetOperations": 0,
                 "requests": [
                     {"address": "0x470002c0", "headerHex": "01010000C002004720000000", "length": 32},
                     {"address": "0x4500ff14", "headerHex": "0101000014FF004538030000", "length": 824},
                     {"address": "0x450158a8", "headerHex": "01010000A8580145EC030000", "length": 1004},
                 ],
                 "timeoutMs": 2000, "interfaceNumber": 2, "writes": 0, "retries": 0},
         "native dry")
    refusal = run([str(DOTNET), str(dll), "--execute"], 64)
    need(refusal.stdout == b"REFUSED_ARM32_ABI\n" and refusal.stderr == b"", "ABI refusal")
    unknown = run([str(DOTNET), str(dll), "--bad"], 63)
    need(unknown.stdout == b"" and unknown.stderr == b"", "CLI refusal")
    expected_tests = {"wrapperTestsPassed": 26, "targetOperations": 0}
    need(json.loads(run([sys.executable, "test-wrapper.py"]).stdout) == expected_tests, "wrapper normal")
    need(json.loads(run([sys.executable, "-O", "test-wrapper.py"]).stdout) == expected_tests,
         "wrapper optimized")

    names = {"Program.cs", "ManagedUsbRtBlockReadOnce.csproj", "NuGet.Config",
             "build-derivative.py", "build-offline.py", "run-once.py", "test-wrapper.py",
             "root-with-margin.py", "README.md"}
    names.update("bin/Release/net6.0/" + name for name in OUTPUTS)
    files = {}
    for name in sorted(names):
        raw = (HERE / name).read_bytes()
        files[name] = {"size": len(raw), "sha256": sha(raw)}
    manifest = {
        "schema": "managed-usb-ap-exco-input-snapshot-build-v1",
        "offline_only": True, "target_executions": 0,
        "build": {"framework": "net6.0", "configuration": "Release",
                  "dotnet_path": str(DOTNET), "dotnet_sha256": DOTNET_SHA,
                  "nuget_sources": [], "derivation_stdout_sha256": sha(derivation.stdout)},
        "parent": {"directory": "managed-usb-ap-exco-callback-read",
                   "manifest_sha256": "48b202a87cd714dab866a32cb36cb716a65cdec6745519463a346bab9d35f00a",
                   "program_sha256": "cc90506197ba2784d0918b5cc9567d7fd78c5bcb10973c6b7bb90870080842be",
                   "wrapper_sha256": "a7d50ab656c727c2aab080410a1360db27f64051c0b488398eb9836651d0feae"},
        "boot_id": "00000000-0000-4000-8000-000000000000",
        "root_adapter": {"sha256": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
                         "remote_timeout_seconds": 45, "host_timeout_seconds": 75},
        "protocol": {"target": "0x101", "bulk_steps": 6,
                     "requests": [{"address": hex(a), "length": n, "header_hex": h}
                                  for a, n, h in geometry],
                     "timeout_ms_per_bulk": 2000, "writes": 0, "retries": 0,
                     "pointer_gate_before_dependent_headers": True},
        "object_geometry": {"ordinary_base": "0x4500ff14", "ordinary_extent": 826,
                            "ordinary_captured_prefix": 824, "ordinary_last_offset": "0x337",
                            "derived_base": "0x450158a8", "derived_extent": 1004},
        "interpretation": {"ordinary_pointer_response_offset": 4,
                           "ordinary_pointer_expected": "0x4500ff14",
                           "derived_pointer_response_offset": 12,
                           "derived_pointer_expected": "0x450158a8",
                           "ordinary_u16_offsets": ["0xca", "0x116", "0x10a", "0x10c",
                                                    "0xe6", "0x2fc", "0x300", "0x302"],
                           "derived_byte_offsets": ["0x0", "0x1", "0x3d8"],
                           "samples_atomic": False, "event_time_inferred": False,
                           "physical_cause_inferred": False,
                           "pointer_mismatch_preserves_raw_and_stops": True,
                           "late_failure_preserves_prior_exact_windows": True},
        "evidence_pins": EVIDENCE,
        "tests": {"native_fake_ops": 48, "wrapper_normal": 26, "wrapper_optimized": 26,
                  "host_abi_refusal": True, "unknown_cli_refusal": True},
        "files": files,
    }
    (HERE / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schema": manifest["schema"], "targetOperations": 0,
                      "nativeTests": 48, "wrapperTests": 26,
                      "manifestSha256": sha((HERE / "build-manifest.json").read_bytes())},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
