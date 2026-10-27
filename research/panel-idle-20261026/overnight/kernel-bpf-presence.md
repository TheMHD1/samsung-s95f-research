# Kernel BPF/perf observer feasibility — exact-image boundary

Follow-up: a deliberately invalid userspace ABI probe was staged once, but
the TV denied execution before it produced output. Its result is
**unclassified**, with temporary-directory cleanup confirmed. See the
[attempt and raw outcome](kernel-abi-probe/README.md). No syscall-presence or
driver-gate conclusion follows from that launch failure.

This is an offline analysis of the copied ARM64 kernel Image and the local
export-view reconstruction. It does not attach a BPF program, open a perf
event, call either syscall, load a module, change tracefs, or contact the TV.
It cannot establish that a capability is enabled in the running kernel merely
because it appears in the copied image.

## Inputs and scope

`kernel-Image.bin` has SHA-256
`77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d`.
The paired uImage header/CRC and version establish Linux5.4.261 in
`kernel-image-manifest.json`; the captured partition is a matching candidate,
not a hash of executing kernel text. `kernel-export-view.elf` is a host-made
ELF view of image bytes plus recovered exports. It is useful for symbol
addresses, but it is not an original Samsung `vmlinux`, a live map, or a
kernel replacement.

The fresh passive feature read at12:33:27 UTC is saved in
`kernel-observer-features-20261026T123326Z.json`. It found:

| Runtime surface | Result | Limit |
| --- | --- | --- |
| `/proc/config.gz`, BTF, `/proc/kallsyms` | absent/unreadable | Does not prove their underlying config options are off |
| `/proc/sys/kernel/unprivileged_bpf_disabled`, `perf_event_paranoid`, `ftrace_enabled` | absent/unreadable | No policy setting is inferred |
| qdf module `.text`/`.bss` section paths | absent/unreadable | No module base or BSS reader is exposed there |
| `kptr_restrict` | 1 | An address-disclosure policy value, not BPF feature proof |
| `raw_syscalls`, scheduler and I2C static trace events | listed | Existing event names do not prove BPF attachment or access to QDF BSS |

The remote command used read-only file checks. Its attempted `/proc/kallsyms`
read failed because the path was absent; the stderr is retained and no empty
result is treated as a symbol-negative conclusion.

## What the exact image proves

The image contains working classic socket-filter creation/validation paths:
`bpf_prog_create` at0x6568f8, `bpf_prog_create_from_user` at0x6572f0,
`get_compat_bpf_fprog` at0x667898, allocation at0x10aa98 and runtime
selection at0x10b9d8. The observed code allocates a program and copies an
`fprog` from a task's user context. This supports **classic BPF used by socket
filtering**. It does not prove the separate `bpf(2)` syscall exists, that an
eBPF program type is enabled, or that tracing attachments are permitted.

Two nearby exported symbols have materially different meanings:

```text
__bpf_call_base  0x107b08: return 0
bpf_event_output 0x107b18: return -524 (ENOTSUPP)
```

`__bpf_call_base` is a normal fixed-offset anchor in upstream Linux5.4's
[`kernel/bpf/core.c`](https://raw.githubusercontent.com/torvalds/linux/v5.4/kernel/bpf/core.c).
Its return-zero body is intentional, so it is not evidence that eBPF is
disabled. The separate `bpf_event_output` return is evidence that this specific
event-output hook is not implemented in the recovered image. It does not rule
out map-based extraction, other helpers, the `bpf(2)` syscall, or a different
eBPF output mechanism. The image also has a real `probe_kernel_read` body at
0x11a4e8, but an internal kernel function is not evidence that a BPF program
can call it or that userspace can read arbitrary kernel memory.

The image contains only `PERF_EVENTS`/tick dependency text in this bounded
search. That is insufficient to prove `perf_event_open` syscall exposure,
supported event types, policy, or a safe way to read a proprietary module's
BSS. Neither a BPF syscall entry nor a perf syscall entry was recovered from
the current export set; those entries need not be exported, so this is not an
absence conclusion.

The hash-gated [offline reproducer](kernel-bpf-presence-reproduce.py) checks
the listed symbol addresses and instruction facts. It makes the positive/stub
findings reproducible without executing the image:

```sh
python3 overnight/kernel-bpf-presence-reproduce.py
```

## Consequence for this diagnosis

The current evidence does **not** yet justify an eBPF observer to read
`qdf_tcon.ko` globals such as suspend, command-skip, TCON-state or PVCC flags.
Even if the `bpf(2)` syscall later proves present, a kernel-memory reading
program would require a program type, verifier helper policy, module-address
provenance and attachment mechanism that have not been established. The
known event-output limitation rules out one ordinary trace/perf event output
route; it does not rule out all map-based extraction or other output mechanisms.

A future feature probe must be deliberately separated from the panel
diagnostic: even a valid BPF map/program load or perf-event open allocates
kernel state, and an attachment changes observability state. A deliberately
invalid `bpf(2)` or `perf_event_open` argument could distinguish `ENOSYS` from
other failure classes without attaching or loading a program, but it still
executes a kernel interface and cannot identify QDF BSS. The later native
probe attempt above failed at execution and reached no classified syscall
result. The existing bounded trace plus paired userspace
and monitor observations remains the current supported evidence path.

No kernel patch, config change, module action, BPF load, perf event, BPF map,
QDF flag write, panel control or recovery workaround follows from this report.
