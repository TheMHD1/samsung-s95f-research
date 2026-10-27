# Independent review: AVEMon all-syscall checkpoint

## Reviewed candidate

Read-only review of `avemon-syscall-checkpoint.sh` SHA-256
`a6f90f07a28d28bab92535667b8d81d92ad6db8f67db4b2d750be92d5adc665f`.
This review also covers its host wrapper,
`run-avemon-syscall-checkpoint.py` SHA-256
`997dec9de07053ae0cc4ad60b509c39e1dd9f0510aeb0a08218d4089b85d2862`.
No target command was sent in this review.

## What is correct

The candidate is narrowly scoped to the existing AVEMonMain task:

* it requires the recorded boot UUID, global `tracing_on=0`, AVOC PID706,
  AVEMonMain TID1011, executable path, and process/thread start ticks before
  creating a unique private trace instance;
* it enables only `raw_syscalls/sys_enter` and `raw_syscalls/sys_exit` inside
  that private instance, each filtered to `common_pid == 1011`; it does not
  write an AVOC/QDF/controller/GPIO/UI interface;
* it records all syscall IDs for that one TID, so it can determine whether the
  previous missing/simple-pair issue was confined to the earlier ID-54 filter;
* it uses `mono`, a five-second bounded sleep, two trace markers, and a
  post-stop `<40000` trace-byte cap; and
* it disables its private tracing/events and removes the private instance on
  normal completion and via an EXIT/HUP/INT/TERM cleanup trap.  It does not
  clear the global ring or globally enable tracing.

It also has an end-of-run boot check—the concern that this was missing is not
supported by the current bytes.  It reads the boot ID and then tests it against
the original UUID before exporting the trace.

## Required fixes before one target execution

### 1. Fail closed on per-CPU trace loss

The script prints each `per_cpu/cpu*/stats` file but never validates it.  A
complete all-syscall answer requires every emitted CPU stats record to show no
overrun/loss.  Printing a nonzero overrun and then emitting `CLEANUP_VERIFIED`
would make the command look successful while its core evidence is incomplete.

After tracing is stopped and before `TRACE_BEGIN`, parse each stats file and
require the exact no-loss condition supported by that kernel's stats format
(at minimum `overrun: 0`; retain the full files for offline interpretation).
If the expected field is absent or nonnumeric, fail and let cleanup run.

### 2. Bind the observed FD mapping at both endpoints

The candidate prints `/proc/706/fd/21` and `/proc/706/fd/33` at both ends but
does not compare them.  The current runtime audit correctly interprets printed
`0x21` as decimal33 (`/dev/dri/card0`), rather than decimal21.  For this
checkpoint's answer to be attributed to one stable AVEMon environment, save
both initial readlinks and require exact equality at end, in addition to the
existing PID/TID start-tick checks.  A changed/missing FD should reject the
record rather than be silently carried to offline inference.

### 3. Recheck AVOC executable identity at end

Start ticks make PID reuse unlikely, and the current end task-start/comm
checks are good.  Add the same end `readlink /proc/706/exe` equality check as
the start guard.  This is a small consistency guard for a diagnostic intended
to reason about a specific process's syscall stream.

## Non-blocking notes

* The outer pinned root-client timeout must exceed the five-second capture,
  setup, trace export, and cleanup.  The script's own trap is finite but is
  not an independent wall-clock watchdog; parent should retain the existing
  bounded root timeout and save all transport envelopes.
* A trace-size cap is a rejection guard, not a capacity proof.  If it is
  exceeded the script should clean up and preserve the failed command output;
  it must not truncate/interpret a partial trace as a result.
* `raw_syscalls` provides kernel syscall entry/exit records, not a proof of
  display state, panel activity, or causal relation to the prior duplicate
  enter.  Even a clean five-second sample can only narrow the checkpoint's
  tracing/filter representation question.

## Verdict

**Hold pending the three small validity guards above.**  Once they are added
and the shell syntax/local fixture checks pass, one five-second private,
all-syscall checkpoint is a proportionate passive diagnostic.  It should be
reported as a finite trace-integrity observation, never as a panel test.

## Addendum: corrected shell and wrapper re-review

The revised shell is SHA-256
`79c7c1cdc63afa7798732c707f419d5085e9015a08aa033e829a7c432b59fbdb`;
the wrapper now pins that exact digest and is SHA-256
`519ec948439f459bc0e57e409ce45642f2b1aeb84ae15fd5f8df7201f577ed1f`.

All three required guards are now present before `TRACE_BEGIN`:

* each discovered `per_cpu/cpu*/stats` file must satisfy the retained exact
  eight-line grammar, with integer counters, decimal timestamps, and zero
  `overrun`, `commit overrun`, `dropped events`, and `read events` values;
  missing, duplicate, unknown, malformed, or nonzero records fail closed;
* initial FD 21 and FD 33 targets are constrained to `/dev/tztv_frc` and
  `/dev/dri/card0`, respectively, and are required to be unchanged at the
  end; and
* the AVOC executable link is required again at the end, alongside the
  pre-existing boot, process/thread start-tick, and task-name checks.

I ran `sh -n`, `py_compile`, and the wrapper's dry path locally.  I also ran
the exact embedded AWK grammar against all four retained checkpoint CPU stats
records, plus negative `overrun: 1` and unknown-key fixtures; the retained
records passed and both negative fixtures were rejected.  This is a local
syntax/fixture result only, not a target execution.

The original hold is therefore cleared for **one** bounded five-second private
checkpoint through the pinned wrapper.  The same limits remain: a root-client
timeout must cover setup, five seconds, export, and cleanup; any failed guard
or cap is a rejected record; and a clean syscall sample says nothing by itself
about panel light, panel reset, or fault causality.
