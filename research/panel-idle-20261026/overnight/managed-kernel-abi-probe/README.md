# ARM32 kernel-observation interface probe through the stock CLR

## Observed result

One run at **2026-10-26 14:22:30 UTC**, same boot
`00000000-0000-4000-8000-000000000000`, completed with:

| Check | Actual result |
| --- | --- |
| Process architecture / pointer size | Arm / 4 bytes |
| libc PID / raw ARM getpid | 19071 / 19071 |
| Real/effective UID | 0 / 0 |
| CapEff / NoNewPrivs / Seccomp | `0000003fffffffff` / 0 / 0 |
| `bpf(-1, NULL, 0)` | libc return -1, errno **38 / ENOSYS** |
| `perf_event_open(NULL, 0, -1, -1, 0)` | libc return -1, errno **38 / ENOSYS** |
| Helper exit / stderr | 0 / empty |
| Private directory cleanup | Confirmed removed |

The complete eight transport calls, command strings, verified identities,
managed output and cleanup result are in
[result-20261026T142228Z.json](result-20261026T142228Z.json).
The recorded execution interval is uptime46159.49–46159.80. Physical picture
state was **unobserved** and this operation was not a panel-recovery test.

These two raw syscall interfaces returned ENOSYS to this ARM32 process. That
closes the proposed ARM32 CLR route to BPF/perf observation on this boot. It
does **not** establish native ARM64 syscall availability, a complete kernel
configuration, the absence of classic BPF, or availability of every internal
kernel instrumentation facility. Seccomp was zero in the actual probe, but
the exact vendor dispatch/stub returning ENOSYS has not been recovered.

The earlier standalone ARM64 ELF failed execution with EPERM and produced no
syscall result. This run neither retried that ELF nor changed execution policy.

## Scope and implementation

The installed `/usr/bin/dotnet` is a custom ARM32 launcher. Its help supports
`--clr-path`; `--list-runtimes` is unsupported. The installed framework path is
`/usr/share/dotnet/shared/Microsoft.NETCore.App/6.0.9`. Launcher, CoreCLR and
CoreLib SHA256 values were captured and pinned before staging. Discovery is
recorded in the parent overnight directory's `installed-*runtime*` and
`installed-clr-identity-20261026T141257Z.json` files.

The helper is portable net6 IL, built with existing host SDK6.0.428 and no
external package. It refuses non-ARM32 processes, non-root identities, missing
or nonzero Seccomp state, and mismatched libc/raw getpid before the two probes.
P/Invoke uses Cdecl, native-width words and immediate saved errno retrieval.

The numbers20/364/386 and argument ordering come from the upstream
[Linux5.4 ARM syscall table](https://github.com/torvalds/linux/blob/v5.4/arch/arm/tools/syscall.tbl).
The deliberately invalid inputs cannot create/load/attach a BPF object or
allocate a perf event on the corresponding upstream implementations:
[BPF dispatcher](https://github.com/torvalds/linux/blob/v5.4/kernel/bpf/syscall.c),
[perf entry and attribute copy](https://github.com/torvalds/linux/blob/v5.4/kernel/events/core.c).
These source references establish the intended ABI/input contract, not a
claim that every Samsung implementation byte matches upstream.

The runner is dry by default. It stages only the DLL, deps JSON and runtime
config as data in a unique mode700 `/tmp` directory, verifies their SHA256,
and executes the installed launcher with diagnostics and telemetry disabled.
A watchdog sends TERM at10seconds and KILL at12seconds if needed. Each root
command is at most8192bytes. It removes exact private filenames and the exact
directory, with no recursive delete or installed-file change. The actual run
finished well before watchdog expiry. There are no display/device calls,
kernel patches, valid BPF/perf requests or attached hooks.

## Independent review and validation

Agent `runtime_reader_review` independently reviewed the source, ARM ABI,
errno handling, architecture/PID gates, temporary staging, watchdog and
cleanup before the one live run; no blocking issue remained. It noted that a
transport outage can leave the recorded private path and that a host process
timeout cannot guarantee retaining partial wrapper stdout. Neither occurred
in the accepted result. A host X64 run exited64 at the architecture guard
before P/Invoke. The project built with zero warnings/errors; the Python
runner compiled and its dry run passed. Source, runner and artifacts are
hash-listed in [build-manifest.json](build-manifest.json).

The same reviewer inspected the completed result independently: all eight
calls returned cleanly, all identity/hash preflights and file transfers passed,
the raw ARM PID matched, both errno values were38, and cleanup was confirmed.
Its final scope explicitly distinguishes ARM32 compatibility from native ARM64.

No retry or broader tracing deployment is justified by this result alone.
