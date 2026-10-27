#!/usr/bin/env python3
"""Build and verify the fixed NPC_AP candidate reader offline."""

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
DOTNET = Path("${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet")
DOTNET_SHA = "6206ebc1d4b6fb5d73311bc7571c654451550e446daf39fe7cfd3cd84bd6da36"
ASSEMBLY = "ManagedUsbRtBlockReadOnce"
OUTPUTS = [ASSEMBLY + suffix for suffix in (".dll", ".deps.json", ".runtimeconfig.json")]
OVERNIGHT = HERE.parent
EVIDENCE = {
    "npc-ap-read-qualification-20261027aj/read-qualification.md":
        "f9c341e50eaee8fdcddf2a6e13ccd7d21f79a12d311e988c44c26098dab756cc",
    "npc-ap-read-qualification-20261027aj/verify-read-qualification.py":
        "48b381845284d754cf46b01d01b964be41d1ad9f8b7175cc21c06520e057ad34",
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
    address, length = 0x4500D730, 8
    header = "0101000030d7004508000000"
    need(struct.pack("<III", 0x101, address, length).hex() == header,
         "derived fixed header")
    need(address == 0x4500D71C + 0x14 and
         address + length == 0x4500D71C + 0x1C,
         "candidate allocation-relative envelope")
    for relative, expected in EVIDENCE.items():
        need(sha((OVERNIGHT / relative).read_bytes()) == expected,
             "evidence pin " + relative)

    run([str(DOTNET), "restore", "--configfile", "NuGet.Config"])
    run([str(DOTNET), "build", "-c", "Release", "--no-restore"])
    dll = HERE / "bin/Release/net6.0" / (ASSEMBLY + ".dll")
    native = json.loads(run([str(DOTNET), str(dll), "--self-test"]).stdout)
    need(native == {"selfTestsPassed": 26, "targetOperations": 0}, "native tests")
    dry = json.loads(run([str(DOTNET), str(dll)]).stdout)
    need(dry == {
        "schema": "managed-usb-npc-ap-divisor-read-dry-v1", "dryRun": True,
        "targetOperations": 0,
        "requests": [{"address": "0x4500d730",
                      "headerHex": "0101000030D7004508000000", "length": 8}],
        "timeoutMs": 2000, "interfaceNumber": 2, "writes": 0, "retries": 0,
        "interpretation": "conditional-selector0-npc-ap-object-offsets-14-through-1b",
        "pointerIdentityGate": False, "storedDefaultsIdentityGate": False,
    }, "native dry")
    refusal = run([str(DOTNET), str(dll), "--execute"], 64)
    need(refusal.stdout == b"REFUSED_ARM32_ABI\n" and refusal.stderr == b"", "ABI refusal")
    unknown = run([str(DOTNET), str(dll), "--bad"], 63)
    need(unknown.stdout == b"" and unknown.stderr == b"", "CLI refusal")
    expected_tests = {"wrapperTestsPassed": 34, "targetOperations": 0}
    need(json.loads(run([sys.executable, "test-wrapper.py"]).stdout) == expected_tests,
         "wrapper normal")
    need(json.loads(run([sys.executable, "-O", "test-wrapper.py"]).stdout) == expected_tests,
         "wrapper optimized")

    names = {"Program.cs", "ManagedUsbRtBlockReadOnce.csproj", "NuGet.Config",
             "build-offline.py", "run-once.py", "test-wrapper.py",
             "root-with-margin.py", "README.md"}
    names.update("bin/Release/net6.0/" + name for name in OUTPUTS)
    files = {}
    for name in sorted(names):
        raw = (HERE / name).read_bytes()
        files[name] = {"size": len(raw), "sha256": sha(raw)}
    manifest = {
        "schema": "managed-usb-npc-ap-divisor-read-build-v1",
        "offline_only": True, "target_executions": 0,
        "build": {"framework": "net6.0", "configuration": "Release",
                  "dotnet_path": str(DOTNET), "dotnet_sha256": DOTNET_SHA,
                  "nuget_sources": [], "deterministic": True},
        "parent": {"directory": "managed-usb-ap-exco-input-snapshot",
                   "manifest_sha256": "5d760fbdabf7b23b6e57f13fc40914a8ede43bf1b488738dc7c42f203321ca69",
                   "program_sha256": "ef5dd6f33a9daece5fbcaca8decf1328128a0b648268d21a1dc97d28da9136b9",
                   "wrapper_sha256": "92b6b36e9001fed8817d3b34420fd5b85cb5cf25c20f5a957c6d8deeb3f9b37e"},
        "boot_id": "00000000-0000-4000-8000-000000000000",
        "root_adapter": {"sha256": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
                         "remote_timeout_seconds": 45, "host_timeout_seconds": 75},
        "protocol": {"target": "0x101", "bulk_steps": 2,
                     "requests": [{"address": hex(address), "length": length,
                                   "header_hex": header}],
                     "timeout_ms_per_bulk": 2000, "writes": 0, "retries": 0,
                     "dynamic_addresses": False},
        "interpretation": {"candidate_cpu_base": "0x2000d71c",
                           "candidate_bus_base": "0x4500d71c",
                           "captured_object_offsets": ["0x14", "0x1b"],
                           "decoded_u16_offsets": ["0x14", "0x16", "0x18", "0x1a"],
                           "pointer_identity_gate_used": False,
                           "stored_defaults_used_as_identity": False,
                           "conditional_selector0_alias": True,
                           "event_time_inferred": False,
                           "physical_cause_inferred": False,
                           "partial_exact_prefix_retained": True},
        "evidence_pins": EVIDENCE,
        "tests": {"native_fake_ops": 26, "wrapper_normal": 34,
                  "wrapper_optimized": 34, "host_abi_refusal": True,
                  "unknown_cli_refusal": True},
        "files": files,
    }
    (HERE / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"schema": manifest["schema"], "targetOperations": 0,
                      "nativeTests": 26, "wrapperTests": 34,
                      "manifestSha256": sha((HERE / "build-manifest.json").read_bytes())},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
