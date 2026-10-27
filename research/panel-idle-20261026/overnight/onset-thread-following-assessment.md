# Onset capture: thread lineage and actual kernel metadata

This is preparation for incident capture, not a new physical observation or
repair. The preceding phase completed the reviewed storage trace and froze
43 verified evidence files. This continuation checks
instrumentation gaps before attempting a live smoke.

## Actual TV metadata, read only

`onset-thread-coverage-metadata-20261026T155621Z.json` records a successful
persistent-only root read at 15:56:22 UTC, uptime 51791.88, boot
`00000000-0000-4000-8000-000000000000`. No trace option, filter, display control
or factory setting was written by that command.

- Global `trace_options` contains `record-tgid`, `noevent-fork` and `overwrite`.
- `options/event-fork` exists and currently reads `0`.
- `set_event_pid` exists and is empty.
- `sched_process_fork` has parent/child command and PID fields with the
  standard printed `comm=... pid=... child_comm=... child_pid=...` form.
- `raw_syscalls/sys_enter` exposes `common_pid`, syscall ID and six arguments.
  Its recorded format has no common TGID field for a simple TGID filter.

These are global-instance metadata reads. They do not establish how every
option behaves in a new private instance, nor whether a current screen is lit.

## Primary-source contract and limitation

The [Linux 5.4 ftrace documentation](https://www.kernel.org/doc/html/v5.4/trace/ftrace.html)
describes `set_event_pid` as a task filter for events; enabling `event-fork`
adds descendants and removes exited tasks. It separately describes
`record-tgid` as a PID-to-TGID cache. That cache is not itself a declared
`common_tgid` event-filter field. These documented features must still be
checked against the installed private-instance interface before use.

Applying an AVOC-only `set_event_pid` to the combined instance would also
restrict its other event families. That would undermine the intended capture
of Deviced and other threads' I2C/power traffic. It is not a drop-in fix for
the selected raw-syscall filter. A separate instance could isolate that scope,
but would require its own resource, clock, accounting and cleanup validation.

## Required interpretation of the current design

Equal AVOC TID lists at the endpoints cannot exclude a thread born and exited
between them. The second draft also had a setup gap: it selected TIDs while
fork tracing was still off, then waited for the scheduled start. A thread born
there could execute inside the physical test window without appearing in
either endpoint list or the recorded fork window.

The implementer/reviewer are correcting that interval. Capturing fork events
before initial enumeration and rejecting unresolved AVOC lineage can preserve
a conservative complete-case scope. Unresolved lineage or an overflowing
trace remains partial evidence; neither a missing syscall nor a quiet partial
trace establishes absence of a host command. The observer's global
`absence_claim_supported` remains false. This does not invalidate independently
retained I2C traffic from other issuing threads or physically timed observations.

No observer source version has yet been cleared for a live smoke in this
continuation. Draft code is actively changing and is excluded from the prior
immutable storage/backend snapshot.
