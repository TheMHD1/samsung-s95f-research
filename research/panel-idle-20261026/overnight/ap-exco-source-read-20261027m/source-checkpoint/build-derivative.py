#!/usr/bin/env python3
"""Verify this fixed three-window reader is a bounded derivative of mode-read."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "managed-usb-rt-mode-read"


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def between(text, start, end):
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b]


def main():
    pins = {
        "Program.cs": "6770c29a29cd0751448f2c9ba6da8dbfdd00d01765914df13df2d87bab7d9e63",
        "ManagedUsbRtBlockReadOnce.csproj": "05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187",
        "NuGet.Config": "5256a7e3e07d2c5c94f7a1e6c45f39aab011c659c5e2d53e452dea525ce04575",
        "root-with-margin.py": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
        "run-once.py": "67a485873f318323f89d337cdecd8a83c0c3238f5bfb8ac9b861b253e1f954ad",
        "build-manifest.json": "4d3e0ac655aff8eac8d1d2f3835d96597f74d5c45c751e67323ea36805663446",
    }
    for name, digest in pins.items():
        need(sha((PARENT / name).read_bytes()) == digest, "parent pin " + name)
    for name in ("ManagedUsbRtBlockReadOnce.csproj", "NuGet.Config", "root-with-margin.py"):
        need((HERE / name).read_bytes() == (PARENT / name).read_bytes(), "unchanged " + name)

    parent = (PARENT / "Program.cs").read_text()
    current = (HERE / "Program.cs").read_text()
    # P/Invoke declarations, ARM32 identity checks, descriptor/FD validation,
    # claim/release/open/close implementation and usbfs timeout remain byte-for-byte.
    native_start = "        const uint ClaimRequest"
    native_end = "        public NativeResult Bulk"
    need(between(current, native_start, native_end) == between(parent, native_start, native_end),
         "native preflight/FD/claim engine drift")
    bulk_tail = "            GCHandle pinned = GCHandle.Alloc(data, GCHandleType.Pinned);"
    fake_start = "    sealed class FakeOps"
    need(between(current, bulk_tail, fake_start) == between(parent, bulk_tail, fake_start),
         "native usbfs bulk/release/close tail drift")
    for token in (
        'Convert.FromHexString("01010000C002004720000000")',
        'Convert.FromHexString("0101000014FF004510000000")',
        'Convert.FromHexString("01010000E002014520000000")',
        'Read("pointer", PointerHeader, pointer, ProtocolPhase.ExpectingPointerIn)',
        'Read("source-base", BaseHeader, sourceBase, ProtocolPhase.ExpectingBaseIn)',
        'Read("source-tail", TailHeader, sourceTail, ProtocolPhase.ExpectingTailIn)',
        'result.PointerWord == 0x4500FF14u',
    ):
        need(token in current, "fixed source token " + token)
    need("args[0] == \"--execute\"" in current and "args[0] == \"--self-test\"" in current,
         "fixed CLI")

    wrapper = (HERE / "run-once.py").read_text()
    for token in (
        '"address": "0x470002c0", "length": 32',
        '"address": "0x4500ff14", "length": 16',
        '"address": "0x450102e0", "length": 32',
        'record["target_operations_status"] = "inflight_or_unknown"',
        'record["target_operations"] = 3',
        'need(terminal["exit_code"] == 0 and native_stderr == b"", "native terminal status")',
    ):
        need(token in wrapper, "wrapper boundary " + token)
    need(wrapper.count("envelope = call(command)") == 1, "one native execute call")
    print(json.dumps({
        "schema": "managed-usb-ap-exco-source-derivative-check-v1",
        "parent_manifest_sha256": pins["build-manifest.json"],
        "fixed_requests": 3,
        "bulk_steps": 6,
        "writes": 0,
        "retries": 0,
        "targetOperations": 0,
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
