# AVEMon all-syscall V2: rejected before trace export

## Inputs and outcome

This offline audit covers only
`avemon-all-syscalls-20261027b/record.json`.  The source record and the V2
shell are hash-pinned in the adjacent JSON summary.  No target command was
sent for this audit.

The V2 probe is **rejected**.  It has no `raw.txt`, its record leaves
`accepted` and `technical_capture_complete` false, and the first transport
command exited 1.  That is the intended result of the trace-size guard:

```
TRACE_BYTES 475651
test "$nb" -lt 40000
```

The script exits before `TRACE_BEGIN`; therefore no trace content, marker
coverage, syscall-ID inventory, enter/exit pairing, or unmatched-event count
is retained.  In particular, V2 does not answer whether removing the former
ID-54 filter would reveal exits under a different ID.

## Narrowly valid runtime facts

The first transport response did not time out and had empty stderr.  It ran
from uptime 96106.96 to 96111.97 with `mono`, a 128-KiB per-CPU buffer, and
only the two `raw_syscalls` events filtered by `common_pid == 1011`.

Before the size rejection, all four retained per-CPU stats records passed the
strict V2 grammar and reported zero `overrun`, `commit overrun`, `dropped
events`, and `read events`.  Their entries total 4,802.  This supports only
that the V2 loss counters did not reject; it does not override the independent
475,651-byte export cap.

The endpoint identity checks succeeded: boot UUID, AVOC process/thread start
ticks, executable, AVEMonMain name, FD21 `/dev/tztv_frc`, and FD33
`/dev/dri/card0` were stable.  The separate verification-only root command
then found the V2 private trace instance absent and global tracing off.

## Limits and next design boundary

The record establishes a high event volume for this all-syscall filter during
five seconds, not an AVOC controller action or a display event.  No UI,
controller, GPIO, QDF, or panel operation is in the executed shell.

Any future recorder redesign would need a separately reviewed capacity policy
that retains and validates the full trace (or changes the question and states
that it is sampling).  Raising or removing the cap would not make this
rejected V2 record interpretable.  V1 remains independently rejected for the
predecessor whitespace grammar defect.
