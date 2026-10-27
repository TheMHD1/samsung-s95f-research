#!/usr/bin/env python3
"""Offline, hash-gated checks for the copied ARM64 kernel image only."""
from pathlib import Path
import hashlib
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "overnight/kernel-Image.bin"
VIEW = ROOT / "overnight/kernel-export-view.elf"
EXPECTED = "77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d"


def disasm(start, size):
    output = subprocess.run([
        "aarch64-linux-gnu-objdump", "-D", "-b", "binary", "-m", "aarch64",
        "--adjust-vma=0", f"--start-address={start:#x}",
        f"--stop-address={start + size:#x}", str(IMAGE),
    ], check=True, capture_output=True, text=True).stdout
    return output


def symbol_table():
    output = subprocess.run(["readelf", "-sW", str(VIEW)], check=True,
                            capture_output=True, text=True).stdout
    values = {}
    for line in output.splitlines():
        match = re.match(r"\s*\d+: ([0-9a-f]+)\s+\d+\s+\S+\s+\S+\s+\S+\s+\d+\s+(\S+)$", line)
        if match:
            values[match.group(2)] = int(match.group(1), 16)
    return values


def main():
    assert hashlib.sha256(IMAGE.read_bytes()).hexdigest() == EXPECTED
    table = symbol_table()
    required = {
        "__bpf_call_base": 0x107B08,
        "bpf_event_output": 0x107B18,
        "bpf_prog_free": 0x107B20,
        "bpf_prog_alloc": 0x10AA98,
        "bpf_prog_select_runtime": 0x10B9D8,
        "bpf_prog_destroy": 0x651090,
        "bpf_prog_create": 0x6568F8,
        "bpf_prog_create_from_user": 0x6572F0,
        "get_compat_bpf_fprog": 0x667898,
        "probe_kernel_read": 0x11A4E8,
    }
    for name, address in required.items():
        assert table.get(name) == address, (name, table.get(name), address)
    # Upstream Linux v5.4 defines __bpf_call_base as a fixed-offset anchor
    # returning zero, even where eBPF is enabled. Only bpf_event_output's
    # -ENOTSUPP return is an event-output-route limitation in this image.
    assert re.search(r"107b08:.*mov\s+x0, #0x0.*\n\s*107b0c:.*ret", disasm(0x107B08, 8))
    assert re.search(r"107b18:.*mov\s+x0, #0xfffffffffffffdf4.*\n\s*107b1c:.*ret",
                     disasm(0x107B18, 8))
    # Classical socket-filter creation remains compiled: it allocates a program
    # and copies/validates a user fprog. This is not proof of bpf(2) syscall,
    # BPF events, BTF, tracing attachment, or helper permission.
    create = disasm(0x6572F0, 0x80)
    assert re.search(r"65733c:.*bl\s+0x10aa98", create)
    assert re.search(r"657350:.*mrs\s+x1, sp_el0", create)
    compat = disasm(0x667898, 0x58)
    assert re.search(r"6678ac:.*bl\s+0xc2208", compat)
    assert re.search(r"6678b4:.*mrs\s+x1, sp_el0", compat)
    # A real probe_kernel_read implementation exists; its presence alone does
    # not make it available to a BPF program or an externally callable reader.
    read = disasm(0x11A4E8, 0x80)
    assert re.search(r"11a4f0:.*mrs\s+x3, sp_el0", read)
    assert re.search(r"11a528:.*ldxr\s+x1, \[x3\]", read)
    print("PASS: classic-BPF paths and event-output -ENOTSUPP verified; bpf/perf syscall exposure remains unproved")


if __name__ == "__main__":
    main()
