# Runtime-PM idle tracepoint addendum

Status: implementation-review addendum. This does not alter the frozen
six-event design `pm-rpm-onset-extension-design.md`, SHA-256
`1a52bf7c35bd519ccf63ba252ac71de724bfa7365018b5f0e240dc24cd614dc2`,
or authorize a TV capture. It records why the six-event implementation
candidate was rejected and the narrower seven-event replacement contract.

## Why six events are insufficient

The generic `rpm_return_int` event carries a device name and return value but
does not itself encode whether the returning operation is resume, suspend, or
idle. Linux 5.4 `rpm_resume()` can call `rpm_idle(dev, RPM_ASYNC)` before
emitting its own generic return. Consequently this valid nesting:

```text
rpm_resume dev.0
  rpm_idle dev.0
  rpm_return_int ...:dev.0 ret=-11
rpm_return_int ...:dev.0 ret=0
```

cannot be typed from `rpm_resume`, `rpm_suspend`, and `rpm_return_int` alone.
The first return can falsely close the pending resume even though it belongs
to the nested idle operation. Raw symbol text is retained but is not treated
as a trustworthy operation discriminator.

The rejected six-event implementation source/test candidate hashes were
`b453c8f543008105a6c104dcc4e01aab1920e5dd254bb05d9bc84e8adf7ac7d5`
and `7c27f1ee76e7cbef95426ca502e2f665cef4cc422e1db7c43bd0d99893ad61ad`.
They were never cleared for a passive smoke. Independent review also found
that their PM-only state machines could leave an enable-slop or trace-prelude
operation pending through the physical window. The replacement must reject
that unbounded overlap rather than classifying it as outside context.

## Exact seventh format provenance

The bounded read-only acquisition is
`pm-idle-tracepoint-format-20261026/remote-stdout.txt`, 1,193 bytes, SHA-256
`4b3d1d29cebcca4d119b44075c3839dfc97fb60965d19e70cbcc3985c4159bfa`.
It records boot `00000000-0000-4000-8000-000000000000`, kernel `5.4.261`,
uptime `67237.64..67237.65`, and global trace state `0/nop` at both endpoints.
No event was enabled. Supporting raw hashes are:

- client JSON: `e90e86bd693b1a91582368d4240ef5c3567e1f1615781bb28b8d7251fd6051e9`;
- intent: `d6048636ec7e0a8b48873ce297948ffff9eea9196cff59ada2e75869c6d12072`;
- host result: `115a57ef33ba47c8f921b0f4920434426fb1320cfe4115e181dcd429080dabb1`;
- empty client stderr: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

The exact `rpm/rpm_idle` format is ID 129 on this acquired build and has the
same `rpm_internal` payload layout as the captured resume and suspend entries:
dynamic device name, signed flags/count/depth/auto/pending/IRQ/child fields,
and the exact padded print format. The ID is provenance, not portable ABI.
The future collector must compare and retain all seven exact live format files
and read back all seven private-instance enables.

## Seven-event runtime state machine

`rpm_resume`, `rpm_suspend`, and `rpm_idle` entries share one ordered stack per
exact task. A generic return may close only the top entry when its exact device
name suffix matches. The resulting pair inherits that entry's operation kind;
the return row never supplies or overrides it. The nested sequence above must
therefore produce two distinct pairs, idle `-11` and resume `0`, with their own
start/end clocks, durations, raw bodies, task identity, and regions.

An unmatched generic return remains
`unassigned_return_unknown_operation`. It is retained without inventing a
resume, suspend, or idle type and cannot support an absence claim. A name
mismatch does not pop the pending entry. Any selected entry that begins in
enable-slop, trace-prelude, pre-roll, or the capture window and remains pending
at drain cutoff rejects semantic completeness. A start in enable-slop or
trace-prelude that returns in the capture window, drain, or post-drain also
rejects as an unbounded physical-window overlap. Callback/system orphan ends
in capture, drain, or post-drain reject; a generic unmatched runtime return
keeps its special unknown-operation treatment.

Numeric PID and saved TGID are not sufficient across reuse. Every completed PM
pair must retain and compare start/end task comm and reject any retained
`sched_process_exit`, child-PID birth, or `sched_process_exec` for that PID
between its endpoints. The existing trace already retains those lifecycle
events. This is fail-closed pairing identity, not proof against an unrecorded
reuse if trace loss occurred; any trace loss already rejects the capture.

The exact positive standard callback driver spelling is `sdp-hdmi` (hyphen),
from the pinned platform-driver name. `sdp_hdmi` and near matches do not qualify.
The module-file hash remains separate source evidence and does not prove live
driver-object binding.

## Per-CPU idle runtime identity

The first reviewed seven-event implementation, source SHA-256
`eabe5bde6037f5f5b83b6bcec67af8b7c83f3c69f9630c97d993d36259b74d64`,
was used for one five-second passive smoke.  That historical run remains
rejected: its immutable `record.json`, SHA-256
`f18a665e85da085339245be9fad058120be3891d73690cdc36dd9eb6951553be`,
records `accepted=false` and the original PID/TGID identity error.  Its retained
trace, SHA-256
`44603d1091cea91a0753dd9a0331dcd84c81cb69a8b0c2247c7135dc6a0032b3`,
contains two complete runtime-suspend pairs emitted as exact ftrace identity
`<idle>-0 (-------)` on CPU 2 with opaque context token `dNh2`.

PID 0 is not a missing positive process identity that can be accepted
generically: Linux represents a distinct idle thread on every CPU.  The narrow
replacement admits PID 0 only for the runtime entry/return family and only when
the printed task is exactly `<idle>` and the raw saved-TGID text is exactly
`-------`.  Its stack identity includes the exact CPU number and opaque printed
ftrace state token in addition to PID/task/raw-TGID.  A return on another CPU or
under another printed state token cannot pop the entry.  Callback and system-PM rows
still require positive PID and numeric positive saved TGID.

For positive process identities, the exact opaque printed state token is also
part of the pairing key.  The token is mutable formatted flag/state output; it
is not a stable or authoritative execution-context identity, and its letters
are not decoded here.  Equality is only a conservative disambiguator.  It can
reject a legitimate begin/end pair if the printed state changes, producing a
fail-closed false negative rather than evidence that the operation did not
occur.  An in-window mismatch is not silently discarded: the return remains
unassigned and the entry remains pending, so the existing overlap rule rejects
the capture.  Completed pairs and counts retain both endpoint CPUs, raw
saved-TGID text, and printed state tokens.  Numeric PID/TGID/task, scheduler
lifecycle, trace-loss, marker, physical-window, and absence-claim rules are
unchanged.

## Unchanged limits

The physical and annotation window remains `CAPTURE_START..CAPTURE_END`.
All seven events are passive stock tracepoints enabled only in the owned
private instance. They do not cover or exclude Samsung's proprietary
`sdp_runtime_pm_get/put` dispatcher, and zero decoded rows never proves that a
private callback, SerDes poll, power transition, or physical panel change did
not occur. Positive timing remains correlation, not causation. A separately
reviewed passive smoke and capacity analysis are still required before any
full observed run.
