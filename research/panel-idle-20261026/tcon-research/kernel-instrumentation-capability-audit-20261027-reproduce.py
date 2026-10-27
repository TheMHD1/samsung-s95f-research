#!/usr/bin/env python3
"""Reproduce retained kernel-instrumentation capability facts offline only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
IMAGE = ROOT / "overnight/kernel-Image.bin"
INDEX = ROOT / "overnight/kernel-export-index.json"
ACCESS = ROOT / "overnight/sleep-investigation-20261027a/kernel-access.stdout"
CAPS = ROOT / "overnight/qd-uart-probe-capabilities-20261027a.json"
MODULES = {
    ROOT / "overnight/sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko":
        "1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4",
    ROOT / "overnight/serdes-ack-copy-20261026/sdp_ocl_jp.ko":
        "e5a064da2cfbd37194f5e97463c3519126a09aedaf4b3c95107b08ab0680aa2c",
}
IMAGE_SHA = "77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d"
INDEX_SHA = "6d3ffe0edfd2ab92fc4439ffe35371db4c3f2ad8a99cf5b2b20ae2ef4eb937ac"


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def slice_sha(data: bytes, start: int, end: int) -> str:
    return hashlib.sha256(data[start:end]).hexdigest()


def main() -> None:
    image = IMAGE.read_bytes()
    index_bytes = INDEX.read_bytes()
    need(len(image) == 11786752 and sha(image) == IMAGE_SHA, "kernel Image changed")
    need(sha(index_bytes) == INDEX_SHA, "kernel export index changed")
    index = json.loads(index_bytes)
    need(index["source_sha256"] == IMAGE_SHA and index["record_size"] == 12,
         "export-index source/schema changed")
    exports = {item["name"]: item for item in index["exports"]}
    need(len(index["exports"]) == 9379, "export count changed")

    expected = {
        "tracepoint_probe_register": 0xE63D8,
        "tracepoint_probe_unregister": 0xE6470,
        "tracepoint_probe_register_prio": 0xE6358,
        "for_each_kernel_tracepoint": 0xE63F0,
        "register_tracepoint_module_notifier": 0xE5C20,
        "unregister_tracepoint_module_notifier": 0xE5CB0,
        "__symbol_get": 0xBE450,
        "__symbol_put": 0xBE760,
        "is_module_sig_enforced": 0xBC988,
        "register_ftrace_export": 0xEDE98,
        "unregister_ftrace_export": 0xEF7B8,
        "__tracepoint_rpm_idle": 0xB29F50,
        "__tracepoint_rpm_resume": 0xB29F80,
        "__tracepoint_rpm_suspend": 0xB29FB0,
        "__tracepoint_rpm_return_int": 0xB29EF0,
        "__tracepoint_suspend_resume": 0xB29D70,
    }
    for name, target in expected.items():
        need(name in exports, "missing export " + name)
        need(int(exports[name]["target_image_offset"], 16) == target,
             "export target changed for " + name)

    absent = {
        "register_kprobe", "unregister_kprobe", "register_kretprobe",
        "unregister_kretprobe", "kallsyms_lookup_name",
        "register_ftrace_function", "unregister_ftrace_function",
        "ftrace_set_filter", "ftrace_set_filter_ip",
    }
    need(not (absent & exports.keys()), "previously absent instrumentation export appeared")

    banner = (b"Linux version 5.4.261 (abuild@A2001DPG) "
              b"(gcc version 9.2.0 (GCC)) #1 SMP PREEMPT "
              b"Wed Jul 1 16:51:36 UTC 2026")
    need(image.count(banner) == 1, "kernel banner changed")
    need(image[0xBC988:0xBC990].hex() == "00008052c0035fd6",
         "is_module_sig_enforced no longer returns zero")
    slices = {
        "tracepoint_register": slice_sha(image, 0xE63D8, 0xE63F0),
        "tracepoint_enumerator": slice_sha(image, 0xE63F0, 0xE646C),
        "tracepoint_unregister_prefix": slice_sha(image, 0xE6470, 0xE6500),
        "symbol_get": slice_sha(image, 0xBE450, 0xBE510),
        "module_sig_enforced": slice_sha(image, 0xBC988, 0xBC990),
    }
    need(slices == {
        "tracepoint_register": "cd4e36410618ae522d5bd9731c0c7dfe25577344c3f7a14f587a8df30aa89565",
        "tracepoint_enumerator": "73bbb634a5f5d63a20686f7bbba00944b6901a50895b3e9ac5307684e32601e1",
        "tracepoint_unregister_prefix": "c1ea6b13000fd45981a7f5d067b9665d8ef94f959584432982118637d3e47161",
        "symbol_get": "743661c922eb2b7069bbafba89068a248892078a4da81bde3c2a4e7595235b85",
        "module_sig_enforced": "2f6110664dbd16b514a0c2c7c8326932a36e85d2f15b91e57ca76efd2c7a625a",
    }, "kernel code slices changed")

    vermagic = b"vermagic=13781815, release SMP preempt mod_unload aarch64\0"
    for path, expected_hash in MODULES.items():
        body = path.read_bytes()
        need(sha(body) == expected_hash, "module changed: " + path.name)
        need(body.count(vermagic) == 1, "module vermagic changed: " + path.name)
        need(body.endswith(b":UEP"), "module UEP trailer missing: " + path.name)
        need(b"~Module signature appended~" not in body,
             "unexpected standard signature marker: " + path.name)

    access = ACCESS.read_bytes()
    need(sha(access) == "5e92bbfcc7ee2844e7dd43a4d73fe4b42ff8178240aac89888a2313a6628c15b",
         "kernel-access metadata changed")
    access_stdout = json.loads(access)["commands"][0]["stdout"]
    need("VALUE /proc/sys/kernel/modules_disabled\n0\n" in access_stdout,
         "modules_disabled evidence changed")
    capabilities = CAPS.read_bytes()
    need(sha(capabilities) == "6dbca53fdc4885fe7cc359cd25b8364fb53619f5693642b73a3ec54cdf69b22e",
         "probe-capability metadata changed")
    for path in (b"/proc/kallsyms", b"/proc/config.gz",
                 b"/sys/kernel/debug/tracing/kprobe_events",
                 b"/sys/kernel/debug/kprobes/blacklist",
                 b"/sys/kernel/debug/tracing/available_filter_functions"):
        need(b"ABSENT " + path in capabilities, "surface result changed: " + path.decode())

    print("PASS")
    print("exports=%d tracepoint_register=0x%x tracepoint_unregister=0x%x" %
          (len(index["exports"]), expected["tracepoint_probe_register"],
           expected["tracepoint_probe_unregister"]))
    print("kprobe_exports=0 kallsyms_lookup_name_export=0")
    print("standard_module_sig_enforced_static=0 modules_disabled_sample=0")
    print("module_vermagic=13781815,_release_SMP_preempt_mod_unload_aarch64 uep_trailer=present")
    for name, value in slices.items():
        print(name, value)


if __name__ == "__main__":
    main()
