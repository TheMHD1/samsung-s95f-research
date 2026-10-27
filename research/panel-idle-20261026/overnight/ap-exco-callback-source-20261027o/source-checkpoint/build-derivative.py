#!/usr/bin/env python3
"""Verify the callback reader is a bounded derivative of the reviewed M reader."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "managed-usb-ap-exco-source-read"


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
        "Program.cs": "99fe549a5b4c408e6c83a44675cdd7c5f975231f2495e07b1bc9481939d6dc60",
        "ManagedUsbRtBlockReadOnce.csproj": "05893d224110307cdce9838c9620aba3ed1326901288ad105279cfc9eed3f187",
        "NuGet.Config": "5256a7e3e07d2c5c94f7a1e6c45f39aab011c659c5e2d53e452dea525ce04575",
        "root-with-margin.py": "bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a",
        "run-once.py": "79341a52a0c69031a2d489d35c80997997b80b75661814637f6de27836221106",
        "build-manifest.json": "3222c56b1b80749123a2b360ebae9ffbf44779cf748061737774c93fc153fa51",
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
        'Convert.FromHexString("01010000A858014510000000")',
        'Convert.FromHexString("01010000705C014520000000")',
        'Read("pointer", PointerHeader, pointer, ProtocolPhase.ExpectingPointerIn)',
        'Read("source-base", BaseHeader, sourceBase, ProtocolPhase.ExpectingBaseIn)',
        'Read("source-tail", TailHeader, sourceTail, ProtocolPhase.ExpectingTailIn)',
        'result.PointerWord == 0x450158A8u',
        'result.SourceByteOne = sourceBase[1]',
        'result.SourceByte3D8 = sourceTail[0x10]',
    ):
        need(token in current, "fixed source token " + token)
    need("args[0] == \"--execute\"" in current and "args[0] == \"--self-test\"" in current,
         "fixed CLI")

    wrapper = (HERE / "run-once.py").read_text()
    for token in (
        '"address": "0x470002c0", "length": 32',
        '"address": "0x450158a8", "length": 16',
        '"address": "0x45015c70", "length": 32',
        'record["target_operations_status"] = "inflight_or_unknown"',
        'record["target_operations"] = 3',
        'need(terminal["exit_code"] == 0 and native_stderr == b"", "native terminal status")',
    ):
        need(token in wrapper, "wrapper boundary " + token)
    need("packaged_defaults" not in wrapper and "ordinary_object_default_comparison_performed" in wrapper,
         "no ordinary-object default inference")
    need("return pointer_matches is True and byte_zero == 3 and byte_3d8 == 1" in wrapper,
         "saved-context correlation pointer gate")
    need(wrapper.count("envelope = call(command)") == 1, "one native execute call")
    print(json.dumps({
        "schema": "managed-usb-ap-exco-callback-derivative-check-v1",
        "parent_manifest_sha256": pins["build-manifest.json"],
        "fixed_requests": 3,
        "bulk_steps": 6,
        "writes": 0,
        "retries": 0,
        "targetOperations": 0,
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
