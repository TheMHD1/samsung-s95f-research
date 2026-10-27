# Native ABI availability probe — execution denied

This experiment was attempted once. **The helper did not execute.** It gives
no BPF/perf syscall result, configuration conclusion, private-driver state,
physical-panel observation or recovery result. No retry or policy change was
performed.

## Purpose and exact scope

The remaining kernel-observer question was whether native `bpf` and
`perf_event_open` handlers are reachable. Existing tracepoints do not expose
the private QDF suspend/skip/state/PVCC words. The live config, BTF, symbols
and module-section address surfaces remain unavailable in
[`kernel-observer-features-20261026T123326Z.json`](../kernel-observer-features-20261026T123326Z.json).

The probe is a592-byte static AArch64 userspace ELF with one RX load segment
and a non-executable stack. It has no interpreter or libc dependency. Its
[assembly](probe.S) makes five calls: positive-control `getpid`, invalid
`bpf(-1,NULL,0)`, null-attribute `perf_event_open(NULL,0,-1,-1,0)`, one32-byte
stdout write, and exit. No valid create/load/attach command is supplied.

Arm64 uses the generic syscall numbers172/280/241/64/93 for these operations.
[Linux5.4 arm64 ABI](https://github.com/torvalds/linux/blob/v5.4/arch/arm64/include/uapi/asm/unistd.h),
[number definitions](https://github.com/torvalds/linux/blob/v5.4/include/uapi/asm-generic/unistd.h).
In the upstream source, the invalid BPF command reaches an error/policy path;
the null perf attribute faults before event/FD allocation. These source facts
justify the narrow non-creating request design, not assumptions about the
TV's vendor implementation or response.
[BPF syscall](https://github.com/torvalds/linux/blob/v5.4/kernel/bpf/syscall.c),
[perf syscall and attribute copy](https://github.com/torvalds/linux/blob/v5.4/kernel/events/core.c).

An independent primary-source/assembly review checked the ABI, stack
alignment, arguments, RX/stack permissions and32-byte format before the
attempt. The parser requires exit0, exact magic/length/SHA, positive PID,
negative observer returns and confirmed temporary-directory cleanup. Five
offline parser fixtures initially covered a valid record plus truncated, failed,
cleanup-missing and unexpected nonnegative-observer results. The saved
[integrity tests](test-probe.py) also reject the actual denied-launch record
as syscall evidence. Target assembly was not executed on the host.

## Build and staging

[`build-manifest.json`](build-manifest.json) preserves source/binary hashes
and the exact cross-build argument list. Binary SHA-256:
`7621e61295a1137bc542080bc43aab070b26a958f36560ad4531b0a61719fe2b`.

[`run-probe.py`](run-probe.py) defaults to emitting the
[reviewed shell](review-command.sh). The attempted run used persistent-only
root and created one private `/tmp/researcher-kernel-abi-XXXXXX` directory. It
decoded and hash-checked the helper there, made it executable, attempted it
once, preserved the result and removed both files/directory. This temporary
file staging is an intentional TV filesystem change, unlike the earlier
file-read-only feature discovery. It does not change the access wrapper,
permissions, tracefs, kernel configuration, driver flags or factory settings,
restart/patch existing TV processes, or submit panel controls.

## Authoritative outcome

[`result-20261026T124321Z.json`](result-20261026T124321Z.json) records remote
time12:43:22 UTC, same boot ID, uptime40211.07..40211.09, root UID/EUID0,
CapEff`0000003fffffffff`, NoNewPrivs0 and Seccomp0 in the launching shell.
The shell reported:

```text
/tmp/researcher-kernel-abi-rQ7885/probe: Operation not permitted
PROBE_EXIT=1
```

The result file was0bytes, with the empty-file SHA-256. The reader correctly
returned nonzero and retained `accepted=false`. The shell's own exit0 is
the completed staging/readback/cleanup script status, **not** a successful
probe. The record ends with `PRIVATE_TEMP_DIRECTORY_REMOVED`, after an
explicit absence test. This confirms cleanup at that check.

The cause of the execution denial is not established. A later350-line dmesg
tail contained no matching denial/path/signature diagnosis
([preserved response](../kernel-abi-probe-denial-log-20261026T124635Z.json));
that bounded later log does not exclude an earlier or differently logged
denial. No security policy, signature, file-label or execution restriction was
changed, and the helper was not retried through another route.

The failed launch cannot distinguish an absent BPF syscall from a present,
restricted or usable implementation. Kernel-private gates therefore remain
unobserved. Continue from the bounded I2C/static-event trace and actual
userspace counter/cache observer; do not classify the unknown words from
this failure.
