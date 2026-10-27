# AVEMon all-syscall V3 runtime audit

## Result

This offline audit promotes the retained V3 transport record only for its
defined two-second AVEMonMain syscall-pairing question.  The source
`record.json` itself remains `accepted: false`; the separate eligibility JSON
records the audit decision and its pinned content hashes.

The unique base64 body decoded, and `gzip -dc` completed successfully.  The
decoded trace is 190,711 bytes, exactly matching `TRACE_RAW_BYTES 190711`.
It has one begin and one end marker, a normal ftrace header, and
`entries-in-buffer/entries-written: 1922/1922` on four CPUs.

The boot UUID, AVOC process and AVEMonMain thread start ticks, executable,
task name, FD21 `/dev/tztv_frc`, and FD33 `/dev/dri/card0` are stable across
the endpoints.  Per-CPU loss counters are zero.  The verification-only call
then confirmed the private instance was removed and global tracing was off.

## Decoded stream and pairing

Trace-event IDs are 22 (`sys_enter`) and 21 (`sys_exit`).  The `NR` values
below are the ARM syscall-number field, not trace-event IDs.

| `NR` | event lines | complete interior pairs |
| ---: | ---: | ---: |
| 54 | 240 | 119 |
| 240 | 1,200 | 600 |
| 263 | 480 | 240 |

There are 1,920 syscall lines: 960 entries and 960 exits.  The first event
after the begin marker is `sys_exit: NR 54`; the final event before the end
marker is `sys_enter: NR 54`.  After excluding precisely those two unavoidable
trace-boundary half-pairs, the remaining 1,918 lines form 959 stack-ordered
enter/exit pairs with no interior duplicate or syscall-ID mismatch.

This establishes that AVEMonMain emits ordinary exits under the all-syscall
filter, and that this retained stream contains `NR` 54, 240, and 263.  It does
not identify the semantics of those syscall numbers or prove why any earlier,
rejected capture lacked an exit.

## Boundaries

The record says nothing about panel light, controller state, fault causality,
or syscalls outside this one thread and two-second marker window.  It must not
be presented as whole-window pairing merely because total entry and exit counts
match; the retained leading exit and terminal entry are explicitly boundary
events.
