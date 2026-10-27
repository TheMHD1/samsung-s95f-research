# Combined onset observer: review findings and deployment boundary

Status: the first draft has **not been run on the TV**. It passed15 offline
fixtures, shell syntax and command-size tests, but independent review found
material gaps. It is being corrected before a short explicitly unobserved
smoke test. A passing draft test suite is not evidence of correct physical
classification, finite process cleanup or real90second coverage.

## Required corrections to the first draft

- Physical eligibility: full mode must not become observed-onset evidence
  without an ordered physical timeline inside the actual trace interval.
  Preflight/export annotations are not in-window observations; host UTC,
  reaction/clock uncertainty and TV UTC↔uptime anchors must be related.
- Readiness: a prompt before remote preflight is not an armed-trace signal.
  Use a deterministic scheduled interval or a verified ready handshake; the
  current blocking controller does not expose incremental stdout.
- Sampler: count/internal gaps alone can accept a missing26second tail.
  Require finite ordered stamps, leading/trailing coverage and near-full
  span; label actual measured rate rather than assuming sleep.2 gives5Hz.
- Syscalls: exact AVOC is ARM32; ioctl is54. Native ARM64 ioctl29 is not an
  ioctl in those same threads. Filter enter and exit consistently and parse/
  pair the exact envelope/return by captured TID. Generic ioctl buffers remain
  opaque; new/unmonitored threads constrain absence claims.
- Trace markers/decoding: require exact ordered start/end events, accounting
  and actual event grammar; marker substrings are insufficient.
- Process lifetime: a blocked vlog wait or host interruption must not leave an
  orphan streaming process/open unlinked file. Own-process PID/start-time
  guarded expiry/cleanup and a cleanup-aware entire Popen lifetime are needed.
- Resource accounting: enforce headroom, actual file limits and trace totals.
 4096KiB is per CPU, not4MiB total. Setting131072 file-limit units on this TV
  permits128MiB, not64MiB; the child-only measured unit is1024bytes.
- Source/type integrity: preflight hashes before tracing/reading; preserve
  exact QD/deviced pointer/vptr guards and reject lifecycle changes.
- Raw data: validate sampler stderr and short reads. Vlog bracketing rows do
  not prove a loss-free interior; require order, gaps, termination and explicit
  incompleteness. Full raw source is retained with lengths/hashes/limits.

Read-only reviewer `runtime_reader_review` and parent identified these issues;
the implementer owns corrections in the new observer/tests. No setter, key,
active QD getter, ioctl invocation, power/service action or global trace write
is permitted in the observer. Physical recovery/causality remains unverified.

## Grounded TV resource facts

`onset-capture-environment-20261026T151541Z.json` records /bin/sh→/usr/bin/bash,
installed gzip, /tmp tmpfs available970196KiB, MemAvailable530668KiB and
CPUs0–3 at15:15:42. These are point-in-time resources, not future guarantees.

`onset-shell-file-limit-unit-20261026T151619Z.json` measures a one-unit file
limit in a child shell, then reads the inherited limit through its grep child:
Max file size1024/1024bytes. No regular file was written, no parent limit or TV
setting was changed, and no display operation was invoked. This is stronger
than guessing the shell's block unit from generic usage text.

The real vlog format/rate is preserved in [vlog-capture-contract.md](vlog-capture-contract.md).
Its two-second sample contains6327 records and936079 stdout bytes; a long
capture must budget streaming/retention and verify coverage rather than rely
on an assumed finite history size.

## Revised draft: additional blockers found before execution

A second draft passed21 offline fixtures, but independent source review found
that its full-run timeout argument175–180 exceeded the root controller's
accepted1–120second range. It would fail before launching a full capture.
The existing tests did not exercise that actual argument contract.

The controller also holds its serial gate until remote execution completes.
Killing the local s95f-access process does not cancel the running command;
only the root agent's command timeout kills its original process group.
Therefore a queued cleanup request could not immediately stop an in-flight
blocking collector. The implementer is replacing the blocking acquisition
request with one owned detached collector group, short status requests and
explicit group cancellation, while keeping all sampling and trace work in
that single collector shell. This is a required architecture correction,
not a live test result.

Parent/reviewer additionally found unbounded wait after vlog TERM and cleanup
existence tests whose failures were masked by a later successful echo.
Corrections must bound TERM/KILL/death verification and require every cleanup
assertion to succeed before reporting verified cleanup. The4MiB total trace
budget may also be too small for90seconds of actual traffic; the authorized
budget is now4096KiB per CPU with measured total<=16384KiB and enforced memory
headroom. Overflow/loss still makes evidence incomplete.

The second draft's hashes and21-test PASS do not constitute live clearance.
No capture, smoke, remote key, factory setting or display control was run.

The reviewed second-draft source SHA was
`6db0c368c3ce02739c3a3cbb96e4ed15e57e924d56bc1b47d09cf87810c866af`,
tests SHA
`9ce0657920c6cc78eb4416b397506ae6bbb3498555d95b15fc52c8feddfa8302`.
Those versions are superseded by ongoing edits and are not presented as the
current source or as fully archived, reproducible versions in this phase.

Additional review requirements: detect unresolved transient AVOC thread
lineage rather than infer coverage from equal endpoint TID lists; enforce an
actual full interval of at least85seconds; preserve failures from each end
artifact command rather than the group's last command only; and force
diagnostic eligibility false if cleanup verification fails. These require
negative fixtures plus source review. The pending draft source/tests are
excluded from the immutable storage/backend phase snapshot while they change.
