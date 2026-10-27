#!/usr/bin/env python3
"""Verify the retained E common-status-window zero entirely offline."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
import struct


HERE = Path(__file__).resolve().parent
OVERNIGHT = HERE.parent
E_RUN = OVERNIGHT / "executing-image-identity-20261027e/common-error-guard-read-once"
BUILD = OVERNIGHT / "managed-usb-common-error-guard-read-once"
AJ = OVERNIGHT / "npc-ap-read-qualification-20261027aj"
PACKAGE = OVERNIGHT / "selected-qd-profile-copy-20261027b/F_RSM1_BN9659934B_COMMON.bin"
CURRENT = OVERNIGHT / "firmware-fingerprint-20261027d/full-backup-recovered/fixeddata.bin"
V6 = OVERNIGHT / "finite-onset-logger-20261027g/onset-v6"
HOST10 = OVERNIGHT / "finite-onset-logger-20261027g/after-v6-host-status.json"

PINS = {
    "record": "cf9f5fab4186562e1c953e9cdf888b06ff324d4d0ca6545cdb5b8fb3d0def26d",
    "raw": "309cd7686044d75384b26fd389eef73add04f6a4651339151a0535fce3c4d3aa",
    "stdout": "33f19e6df97bdab9ae29712786bc0d14f67bd8484092e90f7a48e4868ad329d0",
    "manifest": "db25f3b8dccd5d95705a097a987784a7fc902d7d18a78a348794de91a0840aa4",
    "program": "868a94de9e721f5de7607a98ccdc2ca67887260ad8b81a1fd4ff87182a44d101",
    "wrapper": "f5e1b1789f73e49babd0d571d9ba5e02b204c3ecdb5201445cd38582c9e256f8",
    "aj_report": "f9c341e50eaee8fdcddf2a6e13ccd7d21f79a12d311e988c44c26098dab756cc",
    "aj_verifier": "48b381845284d754cf46b01d01b964be41d1ad9f8b7175cc21c06520e057ad34",
    "package": "bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0",
    "current": "f4108538a75b182e41af251e0373e4b32dddb0958d4d2fca815cf3cdfd06e562",
    "v6_result": "3c653c425050c327f984a044c610abea8b0fdef44ff970dfb16dfbe06f3923c9",
    "v6_native": "1dad737eac2e3f9d9ca08b13e6e57484f84e3af9aafa81c856f9a39b1d6752d9",
    "host10": "5f8662e4cfed25563b59a303bd94190d2463e5c584dd117de15b219fd2e0e6e0",
}
BOOT = "00000000-0000-4000-8000-000000000000"


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(path: Path, pin: str) -> bytes:
    raw = path.read_bytes()
    need(sha256(raw) == pin, f"SHA-256 mismatch: {path}")
    return raw


def strict_json(raw: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            need(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs)


def u16(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<H", raw, offset)[0]


def audit_record(record: dict[str, object], raw: bytes, stdout: bytes,
                 manifest: dict[str, object]) -> dict[str, object]:
    need(record["manifest_sha256"] == PINS["manifest"], "record manifest pin")
    need(record["deployment_script_sha256"] == PINS["wrapper"], "wrapper pin")
    need(record["root_runner_sha256"] ==
         "7ca9bf01f3df4524f4f04e561dc4839d0805f4062f665b5c1b9a397adf788c8a",
         "root runner pin")
    need(record["helper_stdout_sha256"] == PINS["stdout"], "stdout pin")
    need(record["request"] == {"target": "0x101", "address": "0x4500f0c0",
                                "length": 64}, "fixed request")
    need(record["remote_stage"] ==
         "/tmp/researcher-usb-rtblock-d68384de927e40c89023eb298ff775fe",
         "fixed retained stage name")

    calls = record["calls"]
    need(isinstance(calls, list) and len(calls) == 16, "exactly 16 root calls")
    for index, call in enumerate(calls):
        need(isinstance(call, dict), f"call {index} object")
        need(call["transport_exit"] == 0 and call["host_timeout"] is False,
             f"call {index} transport result")
        need(call["transport_stderr"] == {"encoding": "base64", "data": ""},
             f"call {index} transport stderr")
        encoded = call["transport_stdout"]
        need(encoded["encoding"] == "base64", f"call {index} stdout encoding")
        decoded = base64.b64decode(encoded["data"], validate=True)
        need(strict_json(decoded) == call["response"],
             f"call {index} authenticated envelope bytes")
        response = call["response"]
        need(response["authenticated"] is True and response["uid"] == 0 and
             response["euid"] == 0 and response["host"] == "198.51.100.20" and
             response["model"] == "QN77S95FAFXZC", f"call {index} identity")
        commands = response["commands"]
        need(isinstance(commands, list) and len(commands) == 1,
             f"call {index} one command")
        command = commands[0]
        need(command["command"] == call["command"] and
             command["exit_code"] == 0 and command["timed_out"] is False and
             command["stderr"] == "", f"call {index} command completion")

    need(calls[14]["started_utc"] == "2026-10-27T07:15:11.671040+00:00" and
         calls[14]["finished_utc"] == "2026-10-27T07:15:12.342009+00:00",
         "active-call host UTC bracket")
    active = [call for call in calls if "ACTIVE_READ_BEGIN" in call["command"]]
    need(len(active) == 1 and active[0]["command"].count(" --execute") == 1,
         "one native execute")
    native_stdout = active[0]["response"]["commands"][0]["stdout"].encode()
    need(native_stdout == stdout, "saved stdout exact")
    need(record["cleanup_stdout"] == "STAGE_ABSENT\n" and
         calls[-1]["response"]["commands"][0]["stdout"] == "STAGE_ABSENT\n",
         "exact terminal cleanup")

    # Recover the exact three staged runtime files from the authenticated
    # commands.  No command text or encoded payload is emitted in the result.
    chunks: dict[str, str] = {}
    pattern = re.compile(r"^printf %s ([A-Za-z0-9+/=]+) (>>|>) (\S+\.b64)$", re.M)
    for call in calls:
        for payload, operation, remote in pattern.findall(call["command"]):
            name = Path(remote).name
            chunks[name] = (chunks.get(name, "") + payload if operation == ">>"
                            else payload)
    expected_names = {"ManagedUsbRtBlockReadOnce." + suffix + ".b64"
                      for suffix in ("dll", "deps.json", "runtimeconfig.json")}
    need(set(chunks) == expected_names, "staged runtime inventory")
    files = manifest["files"]
    for encoded_name, text in chunks.items():
        name = encoded_name[:-4]
        built_path = "bin/Release/net6.0/" + name
        payload = base64.b64decode(text, validate=True)
        entry = files[built_path]
        need(len(payload) == entry["size"] and sha256(payload) == entry["sha256"] and
             payload == (BUILD / built_path).read_bytes(), "staged bytes " + name)

    lines = stdout.decode("utf-8").splitlines()
    need(lines[0] == BOOT and lines[1] == "106924.06 399389.23" and
         lines[2] == '{"selfTestsPassed":26,"targetOperations":0}' and
         lines[3] == "ACTIVE_READ_BEGIN", "native preamble")
    outcome = strict_json(lines[4].encode())
    need(outcome["Stage"] == "complete" and outcome["Accepted"] is True and
         outcome["Opened"] is True and outcome["Claimed"] is True and
         outcome["Released"] is True and outcome["Closed"] is True,
         "native accepted and cleaned")
    need([(step["Phase"], step["Value"], step["Errno"], step["Error"])
          for step in outcome["Steps"]] == [
              ("open", 25, 0, None), ("claim", 0, 0, None),
              ("out", 12, 0, None), ("in", 64, 0, None),
              ("release", 0, 0, None), ("close", 0, 0, None),
          ], "native exact six steps")
    need(outcome["OutCount"] == 12 and outcome["InCount"] == 64 and
         outcome["DataSha256"] == PINS["raw"] and
         base64.b64decode(outcome["DataBase64"], validate=True) == raw,
         "native raw payload binding")
    need(lines[5].startswith("[GC_INFO] GC_Start #1:") and
         lines[6].startswith("[GC_INFO] GC_End #1:") and
         lines[7:] == ["HELPER_EXIT=0", "106924.58 399390.76"],
         "known GC diagnostics, exit, and uptime end")
    return {"root_calls": 16, "native_transfers": 2,
            "uptime_start": 106924.06, "uptime_end": 106924.58}


def verify_mapper_and_field(package: bytes, current: bytes) -> None:
    # Direct selected-image accessor and selector-8 getter bind the CPU root
    # and +0x10 halfword without depending on the mutable AS prose report.
    image0 = package[0x200:0x40200]
    need(image0[0xE670:0xE678].hex() == "00487047e0f00020" and
         sha256(image0[0xE670:0xE678]) ==
         "2f24cbd0d31aea9c8e387aac1ce94e6aa00ea1a72dff69c96f6a5c6e752ccf54",
         "fixed common-object accessor")
    need(image0[0x21E66:0x21E6E].hex() == "ecf703fc008ae5e7",
         "ordinary selector-8 accessor and +0x10 LDRH")

    mapper = package[0x40200 + 0x1BB74:0x40200 + 0x1BBC4]
    need(sha256(mapper) ==
         "94da5bec3c7fd05448a66d3828ec420e5cb08e03cb4474a54d07570732d1fe5c" and
         mapper.hex() ==
         "024609b90020704772b9b1f5802f02d201f18840f7e7b1f1005f14d30b488142"
         "11d201f11450eee7b1f5003f02d201f18c40e8e7b1f1005f05d30448814202d2"
         "01f11c50dfe70020dde7000000000220", "selected image-1 mapper")

    def selected_map(selector: int, address: int) -> int:
        if address == 0:
            return 0
        if 0x20000000 <= address < 0x20020000:
            return address + (0x25000000 if selector == 0 else 0x27000000)
        return 0

    need(selected_map(0, 0x2000F0C0) == 0x4500F0C0 and
         selected_map(0, 0x2000F0F0) == 0x4500F0F0,
         "conditional selected-mapper association")
    need(0x2000F0F0 == 0x2000F0E0 + 0x10 and
         0x4500F0F0 == 0x4500F0C0 + 0x30, "field/window arithmetic")

    current_mapper = current[0x9A48 + 0x200:0x9A78 + 0x200]
    need(sha256(current_mapper) ==
         "f2180e3657acd60cdbfc3b30c28d01a782d60bfe8ff89803cc0bf0cefeba7d85" and
         current_mapper.hex() ==
         "014609480268b1f1005f0ad30748814207d20a2a02d101f11450704701f11c50"
         "fbe70846f9e70000dcdf0fe000002020", "E current-image mapper")
    # The current-image body selects +0x25000000 only when its core tag is
    # 0xa.  The retained run did not read that tag; keep the alias conditional.


def main() -> None:
    record_raw = load(E_RUN / "record.json", PINS["record"])
    raw = load(E_RUN / "returned-block.bin", PINS["raw"])
    stdout = load(E_RUN / "stdout.txt", PINS["stdout"])
    manifest_raw = load(BUILD / "build-manifest.json", PINS["manifest"])
    load(BUILD / "Program.cs", PINS["program"])
    load(BUILD / "run-once.py", PINS["wrapper"])
    load(AJ / "read-qualification.md", PINS["aj_report"])
    load(AJ / "verify-read-qualification.py", PINS["aj_verifier"])
    package = load(PACKAGE, PINS["package"])
    current = load(CURRENT, PINS["current"])
    v6_result = strict_json(load(V6 / "result.json", PINS["v6_result"]))
    v6_native = strict_json(load(V6 / "native-outcome.json", PINS["v6_native"]))
    host10 = strict_json(load(HOST10, PINS["host10"]))
    record = strict_json(record_raw)
    manifest = strict_json(manifest_raw)

    need(len(raw) == 64 and u16(raw, 0x30) == 0, "raw +0x30 halfword zero")
    need(manifest["fixed_target"] == "0x101" and
         manifest["fixed_address"] == "0x4500f0c0" and
         manifest["fixed_length"] == 64 and
         manifest["header_hex"] == "01010000c0f0004540000000",
         "build fixed request")
    audit = audit_record(record, raw, stdout, manifest)
    verify_mapper_and_field(package, current)

    need(v6_result["accepted"] is True and v6_result["restore_verified"] is True and
         v6_result["physical_picture_observed"] is False,
         "V6 bounded result")
    need(v6_native["ReadyJson"].find(BOOT) >= 0 and
         v6_native["ObserveStartUptime"] == "115887.39 432569.20" and
         v6_native["ObserveEndUptime"] == "115907.45 432646.40" and
         v6_native["PreArmFault"] == 0 and v6_native["RestoredRtBase64"] is not None,
         "V6 later same-Linux-boot bracket")
    restored = base64.b64decode(v6_native["RestoredRtBase64"], validate=True)
    need(u16(restored, 0x0A) == 0x1001, "V6 restored RT fault")

    need(host10["accepted"] is True and host10["cleanup_confirmed"] is True and
         host10["execution"]["boot_id"] == BOOT and
         host10["execution"]["execute_uptime"] == 116071.7 and
         host10["execution"]["result"]["status_hex"] == "0x00000010" and
         host10["execution"]["result"]["classification"] ==
         "kernel_output_written" and
         host10["execution"]["result"]["controller_transaction_proved"] is False,
         "later host status and its retained limit")

    result = {
        "schema": "historical-common-status-zero-v1",
        "boot_id": BOOT,
        "e_record_sha256": PINS["record"],
        "raw_sha256": PINS["raw"],
        "raw_length": len(raw),
        "raw_bus_address": "0x4500f0c0",
        "raw_halfword_offset_0x30": u16(raw, 0x30),
        "conditional_cpu_field": "0x2000f0f0",
        "mapper_association_conditional": True,
        "live_mapper_selector_or_core_tag_observed": False,
        "e_uptime": [audit["uptime_start"], audit["uptime_end"]],
        "v6_uptime": [115887.39, 115907.45],
        "minimum_seconds_from_e_end_to_v6_start": round(115887.39 - 106924.58, 2),
        "later_host_status_uptime": 116071.7,
        "later_host_status": "0x00000010",
        "later_host_status_raw_controller_transaction": False,
        "partial_temporal_premise": True,
        "requires_same_controller_instance_and_mapping": True,
        "intervening_controller_restart_excluded": False,
        "event_aligned_common_status_sample": False,
        "physical_picture_observed": False,
        "unique_v6_cause_proved": False,
        "target_operations": 0,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
