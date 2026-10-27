#!/usr/bin/env python3
"""Rebuild, test, and manifest the offline fixed code fingerprint helper."""

from pathlib import Path
import hashlib
import json
import os
import subprocess

HERE = Path(__file__).resolve().parent
DOTNET = Path("${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet")
DOTNET_SHA = "6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36"
SELECTED = HERE.parent / "selected-qd-profile-copy-20261027b" / "F_RSM1_BN9659934B_COMMON.bin"
SELECTED_SHA = "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0"
PARENT_MANIFEST_SHA = "3222c56b1b80749123a2b360ebae9ffbf44779cf748061737774c93fc153fa51"
ADDRESS_REPORT_SHA = "d14282ce16dac0b6a594bfdcce078170d28264c54c515f3b02ad670477901c2a"
ADDRESS_VERIFIER_SHA = "6f645c0bc6fc90f92c4f3180a053a1be6d47734fcaf7eb234a9906f5322ca11c"
ASSEMBLY = "ManagedUsbRtBlockReadOnce"
REMOTE = [ASSEMBLY + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json")]
WINDOWS = [
    (0x1E60, 512, "0x46001e60", "01010000601e004600020000", "8be303fddfa4aefd0f2d307f05c7522213f8017ae15b374a4fd7178aeca2bb49"),
    (0x38C0, 64, "0x460038c0", "01010000c038004640000000", "0483a632a5e65f8eba8bd623411d6f955705d012c831eac9347e7f9564d944cb"),
    (0x1BB60, 576, "0x4601bb60", "0101000060bb014640020000", "035d13a7c17ac9b303ee5739a421a84d0ceec46167d6efce13f4723fc701d9b8"),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(argv, expected=0):
    env = dict(os.environ)
    env["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1"
    env["DOTNET_NOLOGO"] = "1"
    result = subprocess.run(argv, cwd=HERE, env=env, capture_output=True, text=True)
    if result.returncode != expected:
        raise RuntimeError(f"command failed {argv!r}: {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result


if sha(DOTNET.read_bytes()) != DOTNET_SHA:
    raise RuntimeError("dotnet pin")
if sha(SELECTED.read_bytes()) != SELECTED_SHA:
    raise RuntimeError("selected package pin")

derivation = run(["python3", "build-derivative.py"])
run([str(DOTNET), "restore", "--configfile", "NuGet.Config", "--ignore-failed-sources"])
build = run([str(DOTNET), "build", "-c", "Release", "--no-restore"])
dll = HERE / "bin" / "Release" / "net6.0" / (ASSEMBLY + ".dll")
selftest = run([str(DOTNET), str(dll), "--self-test"])
selftest_row = json.loads(selftest.stdout)
if selftest_row != {"selfTestsPassed": 50, "targetOperations": 0}:
    raise RuntimeError("native self-test contract")
dry = json.loads(run([str(DOTNET), str(dll)]).stdout)
expected_requests = [
    {"address": "0x46001e60", "headerHex": "01010000601E004600020000", "length": 512},
    {"address": "0x460038c0", "headerHex": "01010000C038004640000000", "length": 64},
    {"address": "0x4601bb60", "headerHex": "0101000060BB014640020000", "length": 576},
]
if dry.get("requests") != expected_requests or dry.get("targetOperations") != 0 or dry.get("writes") != 0 or dry.get("retries") != 0:
    raise RuntimeError("native dry geometry")
refused = run([str(DOTNET), str(dll), "--execute"], expected=64)
if refused.stdout != "REFUSED_ARM32_ABI\n" or refused.stderr:
    raise RuntimeError("host ABI refusal")
unknown = run([str(DOTNET), str(dll), "--unknown"], expected=63)
if unknown.stdout or unknown.stderr:
    raise RuntimeError("unknown CLI refusal")
wrapper = run(["python3", "test-wrapper.py"])
wrapper_o = run(["python3", "-O", "test-wrapper.py"])
wrapper_row = json.loads(wrapper.stdout)
if wrapper_row != {"wrapperTestsPassed": 28, "targetOperations": 0} or wrapper_o.stdout != wrapper.stdout:
    raise RuntimeError("wrapper tests")

selected = SELECTED.read_bytes()
for va, length, _, _, expected_sha in WINDOWS:
    raw = selected[0x40200 + va:0x40200 + va + length]
    if len(raw) != length or sha(raw) != expected_sha:
        raise RuntimeError("selected window pin")

names = ["Program.cs", "ManagedUsbRtBlockReadOnce.csproj", "NuGet.Config",
         "build-derivative.py", "build-offline.py", "run-once.py", "test-wrapper.py",
         "root-with-margin.py", "README.md", "source-note.md"]
names += ["bin/Release/net6.0/" + name for name in REMOTE]
files = {}
for name in names:
    raw = (HERE / name).read_bytes()
    files[name] = {"size": len(raw), "sha256": sha(raw)}

manifest = {
    "schema": "managed-usb-code-fingerprint-read-build-v1",
    "offline_only": True,
    "target_executions": 0,
    "boot_id": "00000000-0000-4000-8000-000000000000",
    "parent": {"directory": "managed-usb-ap-exco-source-read", "manifest_sha256": PARENT_MANIFEST_SHA},
    "address_source_qualification": {
        "report_sha256": ADDRESS_REPORT_SHA, "verifier_sha256": ADDRESS_VERIFIER_SHA,
        "selector_nonzero_low_va_mapping": "0x46000000 + linked VA for 0 < VA < 0x20000",
        "selector1_is_proven_current_executing_core": False,
    },
    "selected_package": {"sha256": SELECTED_SHA, "image1_file_bias": "0x40200"},
    "protocol": {
        "target": "0x101", "bulk_steps": 6, "writes": 0, "retries": 0,
        "timeout_ms_per_bulk": 2000,
        "requests": [{"address": address, "length": length, "header_hex": header,
                      "selected_sha256": expected_sha}
                     for _, length, address, header, expected_sha in WINDOWS],
    },
    "comparison": {
        "transport_acceptance_independent_of_content_match": True,
        "mismatch_retained": True, "windows_sequential_not_atomic": True,
        "executing_code_identity_proved": False, "whole_image_identity_inferred": False,
    },
    "root_adapter": {"sha256": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
                     "remote_timeout_seconds": 45, "host_timeout_seconds": 75},
    "build": {"dotnet_path": str(DOTNET), "dotnet_sha256": DOTNET_SHA,
              "framework": "net6.0", "configuration": "Release", "nuget_sources": [],
              "derivation_stdout_sha256": sha(derivation.stdout.encode())},
    "tests": {"native_fake_ops": 50, "wrapper_normal": 28, "wrapper_optimized": 28,
              "host_abi_refusal": True, "unknown_cli_refusal": True},
    "files": files,
}
(HERE / "build-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
print(json.dumps({"status": "offline-build-pass", "nativeTests": 50, "wrapperTests": 28,
                  "targetOperations": 0, "manifestSha256": sha((HERE / "build-manifest.json").read_bytes())},
                 separators=(",", ":")))
