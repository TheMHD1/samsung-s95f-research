#!/usr/bin/env python3
"""One fixed stock MODE2 runner; dry by default and never retries."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MANIFEST = HERE / "build-manifest.json"
REMOTE_NAMES = (
    "ManagedTconPowerCycleOnce.deps.json",
    "ManagedTconPowerCycleOnce.dll",
    "ManagedTconPowerCycleOnce.runtimeconfig.json",
)
STATUS_RUNNER = HERE.parent / "managed-tcon-status-read" / "run-status-read.py"
STATUS_RUNNER_SHA256 = "7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a"
ACCESS_SHA256 = "3a92e02003ce51d2faeace231191f6f0c73731f2bfca9caa196e05b195b439a5"
MANIFEST_SHA256 = "67aa102cdd3cdc85ed7fabb68b37d570b721664298317f24f9bd24b8250f9faa"
ABI_SHA256 = "ff63e0c5c5c1679d870e4b816a47fcff51d6ccaf62aac0491f737962cb8e3983"
ABI_REVIEW_SHA256 = "6fe142a5d0c2d5e4105ec540a327ad13898afbd20b6486237df649537beaf510"


class ContractError(ValueError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise ContractError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lifecycle_module():
    # The implementation source is checked before Python executes its bytes.
    require(digest(STATUS_RUNNER) == STATUS_RUNNER_SHA256,
            "status lifecycle source changed before import")
    spec = importlib.util.spec_from_file_location("fixed_power_status_lifecycle",
                                                  STATUS_RUNNER)
    require(spec is not None and spec.loader is not None,
            "status lifecycle import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(digest(module.ACCESS) == ACCESS_SHA256, "root access client changed")
    module.REMOTE_NAMES = REMOTE_NAMES
    return module


def contract() -> tuple[dict, dict[str, bytes]]:
    require(digest(MANIFEST) == MANIFEST_SHA256, "build manifest changed")
    manifest = json.loads(MANIFEST.read_text())
    require(manifest.get("schema") == "managed-tcon-power-cycle-once-build-v1",
            "unexpected build schema")
    expected = {
        "Program.cs", "ManagedTconPowerCycleOnce.csproj", "NuGet.Config",
        "README.md", "recovery-experiment-plan.md", "local-x64-guard.json",
        *("bin/Release/net6.0/" + name for name in REMOTE_NAMES),
    }
    files = manifest.get("files")
    require(isinstance(files, dict) and set(files) == expected,
            "unexpected build inventory")
    staged = {}
    for name, expected_digest in files.items():
        require(re.fullmatch(r"[0-9a-f]{64}", str(expected_digest)) is not None,
                "malformed build digest")
        path = HERE / name
        require(digest(path) == expected_digest, "build file changed: " + name)
        if name.startswith("bin/"):
            staged[Path(name).name] = path.read_bytes()
    require(set(staged) == set(REMOTE_NAMES), "unexpected staged payloads")
    provenance = manifest.get("provenance")
    require(isinstance(provenance, dict), "missing provenance")
    for item in provenance.values():
        require(digest(ROOT / item["path"]) == item["sha256"],
                "provenance changed: " + item["path"])
    require(provenance["power_control_abi"]["sha256"] == ABI_SHA256 and
            provenance["power_control_abi_independent_review"]["sha256"] ==
            ABI_REVIEW_SHA256, "power ABI provenance mismatch")
    return manifest, staged


def parse_managed(text: str, helper_pid: int) -> dict:
    lines = text.splitlines()
    require(lines[:1] == ["QD_TCON_POWER_CYCLE_ONCE_V1"] and
            lines[-1:] == ["POWER_CYCLE_REQUEST_COMPLETE"],
            "managed output bounds")
    values = [line for line in lines if "=" in line]
    require(all(line.count("=") == 1 for line in values), "malformed managed line")
    fields = dict(line.split("=", 1) for line in values)
    bare = [line for line in lines if "=" not in line]
    require(bare == ["QD_TCON_POWER_CYCLE_ONCE_V1",
                     "POWER_CYCLE_REQUEST_COMPLETE"],
            "unexpected managed status")
    expected = {
        "ARCH", "PTR_BYTES", "STRUCT_BYTES", "ENDIAN_LITTLE",
        "OPERATION_OFFSET", "MODE_OFFSET", "RESERVED0_OFFSET",
        "RESERVED1_OFFSET", "ARGUMENT_COUNT", "UID", "EUID", "PID_LIBC",
        "PID_SYSCALL", "DEVICE", "OPEN_FLAGS", "IOCTL_REQUEST",
        "OPERATION_DECIMAL", "MODE_DECIMAL", "PAYLOAD_BEFORE", "OPEN_RETURN",
        "OPEN_ERRNO", "IOCTL_RETURN", "IOCTL_ERRNO", "PAYLOAD_AFTER",
        "CLOSE_RETURN", "CLOSE_ERRNO", "CLASSIFICATION",
        "POWER_ACTION_ACKNOWLEDGED", "RECOVERY_INFERRED",
        "PHYSICAL_STATE_INFERRED",
    }
    require(set(fields) == expected and len(values) == len(expected),
            "unknown or duplicate managed field")
    fixed = {
        "ARCH": "Arm", "PTR_BYTES": "4", "STRUCT_BYTES": "16",
        "ENDIAN_LITTLE": "1", "OPERATION_OFFSET": "0", "MODE_OFFSET": "4",
        "RESERVED0_OFFSET": "8", "RESERVED1_OFFSET": "12",
        "ARGUMENT_COUNT": "0", "UID": "0", "EUID": "0",
        "PID_LIBC": str(helper_pid), "PID_SYSCALL": str(helper_pid),
        "DEVICE": "/dev/tztv_tcon", "OPEN_FLAGS": "0x80002",
        "IOCTL_REQUEST": "0xc010749f", "OPERATION_DECIMAL": "41",
        "MODE_DECIMAL": "2",
        "PAYLOAD_BEFORE": "00000029,00000002,00000000,00000000",
        "OPEN_ERRNO": "0", "IOCTL_RETURN": "0", "IOCTL_ERRNO": "0",
        "PAYLOAD_AFTER": "00000029,00000002,00000000,00000000",
        "CLOSE_RETURN": "0", "CLOSE_ERRNO": "0",
        "CLASSIFICATION": "kernel_return_zero_only",
        "POWER_ACTION_ACKNOWLEDGED": "0", "RECOVERY_INFERRED": "0",
        "PHYSICAL_STATE_INFERRED": "0",
    }
    require(all(fields.get(name) == value for name, value in fixed.items()),
            "fixed MODE2 schema mismatch")
    require(re.fullmatch(r"[0-9]+", fields["OPEN_RETURN"]) is not None,
            "device open failed")
    return {
        "classification": "kernel_return_zero_only",
        "mode": 2,
        "power_action_acknowledged": False,
        "recovery_inferred": False,
        "physical_state_inferred": False,
        "raw_fields": fields,
    }


def render_lifecycle(private: str, boot: str, files: dict[str, bytes]) -> list[str]:
    module = lifecycle_module()
    original = module.execute(private, boot, files)
    execute = original.replace("TconStatusRead.dll",
                               "ManagedTconPowerCycleOnce.dll")
    require(original.count("TconStatusRead.dll") == 1 and
            "TconStatusRead.dll" not in execute,
            "managed DLL replacement failed")
    return [module.create(private, boot), *module.stage(private, boot, files),
            execute, module.postflight(private, boot, files),
            module.cleanup(private, boot)]


def dry_plan(manifest: dict, files: dict[str, bytes]) -> dict:
    module = lifecycle_module()
    private = "/tmp/researcher-tcon-" + "0" * 32
    boot = "00000000-0000-0000-0000-000000000000"
    commands = [module.preflight(), *render_lifecycle(private, boot, files)]
    return {
        "dry_run": True,
        "no_tv_root_device_or_network_calls": True,
        "one_shot": True,
        "retry_permitted": False,
        "fixed_payload": ["0x00000029", "0x00000002", "0x00000000",
                          "0x00000000"],
        "classification": "kernel_return_zero_only (not action acknowledgement)",
        "lifecycle_source_sha256": STATUS_RUNNER_SHA256,
        "build_manifest_sha256": MANIFEST_SHA256,
        "root_command_count": len(commands),
        "root_command_max_bytes": max(len(command.encode()) for command in commands),
        "all_root_commands_within_8192": all(
            0 < len(command.encode()) <= module.MAX_COMMAND for command in commands),
        "helper_deadline_seconds": 8,
        "lower_explicit_wait_budget_seconds": 2.7,
        "staged_payloads": {name: {"bytes": len(data),
                                   "sha256": hashlib.sha256(data).hexdigest()}
                            for name, data in files.items()},
        "limitations": [
            "Return zero can mean a missing interface/callback and is not recovery.",
            "Lower cache/error propagation is incomplete hardware evidence.",
            "Physical recovery requires separately bracketed owner observation.",
            "No automatic retry or compensating rollback is implemented.",
        ],
        "build": manifest,
    }


def run_once(destination: Path, manifest: dict, files: dict[str, bytes]) -> dict:
    module = lifecycle_module()
    module.MANIFEST = MANIFEST
    module.ABI_REPORT_SHA256 = ABI_SHA256
    original_execute = module.execute
    def execute(private: str, boot: str, data: dict[str, bytes]) -> str:
        command = original_execute(private, boot, data)
        require(command.count("TconStatusRead.dll") == 1,
                "managed DLL execution anchor changed")
        return command.replace("TconStatusRead.dll",
                               "ManagedTconPowerCycleOnce.dll")
    module.execute = execute
    module.parse_managed = parse_managed
    original_save = module.save
    def save(path: Path, record: dict) -> None:
        record["schema"] = "managed-tcon-power-cycle-once-result-v1"
        record["measurement"] = "fixed stock operation41 mode2 request"
        record["physical_state"] = "unobserved-by-helper"
        record["recovery_inferred"] = False
        record["limitations"] = [
            "Return zero is kernel_return_zero_only, not power acknowledgement.",
            "Missing live interface/callback can return zero without an action.",
            "Lower cache/error propagation is incomplete hardware evidence.",
            "No physical recovery or cleared protection state is inferred.",
            "The helper has no retry, protection change, EEPROM or flash action.",
        ]
        original_save(path, record)
    module.save = save
    return module.run_once(destination, manifest, files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--reviewed", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    manifest, files = contract()
    if not args.run:
        require(not args.reviewed and args.output is None,
                "--reviewed/--output are meaningful only with --run")
        print(json.dumps(dry_plan(manifest, files), indent=2, sort_keys=True))
        return
    require(args.reviewed and args.output and os.path.isabs(args.output),
            "live mode requires --run --reviewed --output /absolute/unique.json")
    result = run_once(Path(os.path.abspath(args.output)), manifest, files)
    print(json.dumps({
        "result": args.output,
        "accepted": result["accepted"],
        "cleanup_confirmed": result.get("cleanup_confirmed"),
        "classification": result.get("execution", {}).get("result"),
        "recovery_inferred": False,
    }, sort_keys=True))
    if not result["accepted"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
