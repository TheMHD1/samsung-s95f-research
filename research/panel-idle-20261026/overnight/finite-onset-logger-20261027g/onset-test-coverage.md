# Qualified onset wrapper: actual offline test coverage

This document describes the frozen 19-case suite in
`managed-usb-secondary-logger-onset-qualified/test-wrapper.py` at SHA-256
`adc62341f046850402df8c929742bdc936176b002fd8f7e42e8c920684daf9c1`.
It is a factual coverage map, not a full-coverage claim. No candidate file was
changed or rerun while writing it.

The frozen candidate aggregate manifest is
`aa4fc99a5cd22f86736e49487322b1c6aa6996eae482c8fda3a1971049b386d6`.
Its independently reviewed source has no additional fail-closed implementation
blocker, but several negatives in `qualified-supervisor-plan.md` are not yet
represented in the 19 logical cases.

## What the 19 logical cases cover

| Test result name | Actual coverage |
|---|---|
| `qualified-launcher-source-contract` | Statically requires the `nohup` + `setsid -f` + `/bin/sh -c "$(cat ...)"` data-launch form, numeric descriptor closure through `/proc/self/fd`, absence of the old direct `setsid /bin/sh PATH` form, a generated `set -eu` supervisor, publication of `supervisor.start` before the dotnet command, and explicit nonzero-child `wait` handling. |
| `local-qualified-launcher-lifecycle` | Runs a harmless local marker through the qualified launch shape. It establishes that dispatch PID and actual `setsid -f` child PID differ, the actual child has `PID == PGRP == SID`, one deliberately inherited descriptor above 2 is closed, marker completion is observed, launcher stdout/stderr are empty, and the child disappears. It also pre-creates `supervisor.pid` in a modeled supervisor and verifies that this one pre-native collision prevents a native-start sentinel. |
| `accepted-detached-ready-grace` | Exercises one successful fake orchestration with distinct dispatch (699), supervisor (700), and native (701) identities; one launch; supervisor/native group and session binding; READY and FINISHED publication; accepted terminal parsing and cleanup; and no root call between the READY liveness probe and the end of the 22-second local grace. |
| `selftest-size-variation-accepted` | Accepts the target self-test's platform-dependent `successOutputBytes=45848` while all fixed counts and zero-operation fields match, then completes the accepted path through one launch. |
| `selftest-oversize-and-fixed-fields-refused` | Internally exercises five prelaunch rejects: `successOutputBytes=50001`, and one mismatch each in total tests, baseline tests, state-machine tests, and target operations. Each stops before detached launch, READY, or local grace. |
| `ambiguous-launch-safe-stop` | Injects a timeout after the single launch submission and requires no retry, signal, or cleanup. The stage remains marked deferred. |
| `invalid-actual-supervisor-handshake-refused` | Internally exercises two launch-receipt rejects: wrong process group/session in the saved supervisor stat and a stale handshake uptime. Each permits exactly one dispatch and no later status poll or cleanup. |
| `early-prearm-reject-retained` | Exercises a native rejected outcome before READY, retains the stage, and performs no UI grace. |
| `invalid-ready-refused` | Rejects a READY object whose protocol phase is `Unknown`, before READY broadcast or grace. |
| `oversized-output-refused` | Rejects terminal metadata claiming native stdout above 50,000 bytes before fetching native stdout or cleaning the stage. |
| `nonempty-launch-diagnostic-retained` | Makes the accepted fake path return nonempty launcher diagnostic bytes and verifies that accepted cleanup is refused and the stage is retained. |
| `launcher-mismatch-refused` | After a valid launch handshake for supervisor 700, returns a saved status stat for PID 702 and requires refusal before READY/grace. This covers later status identity disagreement with the launch-bound supervisor. |
| `stale-ready-refused` | Rejects READY when the status poll's end uptime makes the published READY older than the two-second allowance. |
| `stale-probe-refused` | Rejects READY when the second liveness probe ends outside the two-second freshness allowance. |
| `child-mismatch-refused` | Rejects a live native child whose process group/session do not bind to the actual supervisor. |
| `cmdline-mismatch-refused` | Rejects a live native child whose exact dotnet assembly/`--execute` command line differs. |
| `completion-absent-retained` | After READY and grace, injects a missing terminal completion and verifies retention with no signal or cleanup. |
| `ready-binding-mismatch-retained` | Returns a final native outcome whose embedded READY JSON/hash binding differs from the published READY and refuses cleanup. |
| `cleanup-residue-retained` | Injects failure of the terminal cleanup/inventory operation after an otherwise accepted native outcome and retains the cleanup-deferred state. |

The aggregate offline builder separately checks dry-default behavior, refusal of
a wrong aggregate-manifest pin before output/staging, generated supervisor shell
syntax, generated launcher shell syntax and its 8 KiB command ceiling, the same
19-result list under normal Python and `python -O`, and the independently
cleared native manifest. `build-native.py` separately reproduces 85 native
self-tests (26 baseline and 59 state-machine) with zero target operations and
the cleared native DLL hash. These builder checks support the suite but are not
additional logical cases in its reported count of 19.

## Planned negatives not covered by the frozen suite

### Pre-native filesystem handshake failures

Only one modeled filesystem failure is tied to the no-native-start sentinel:
an already-present final `supervisor.pid`. The suite does not individually
inject and prove fail-closed behavior for:

- creation or write failure of `supervisor.pid.tmp`, `supervisor.stat.tmp`, or
  `supervisor.start.tmp`;
- chmod failure for any of those three temporary files;
- failure to read `/proc/$$/stat`, boot ID, or uptime;
- rename failure for any of the three handshake files;
- an already-present final `supervisor.stat` or `supervisor.start`;
- native stdout/stderr/PID/exit-name collision after the handshake but before
  or immediately after native child creation.

Consequently, the suite does not yet demonstrate a no-native-start sentinel for
every pre-native filesystem operation named in the plan.

### Launch-handshake framing and process identity

Wrong group/session and stale uptime are covered, but the suite lacks distinct
negative cases for:

- a missing PID, stat, or start file and the shell's bounded one-second
  handshake-missing exit;
- empty, nonnumeric, zero, or oversized PID content;
- missing, truncated, malformed, or oversized saved stat and start records;
- saved-stat PID disagreement with `supervisor.pid`;
- wrong group without wrong session, wrong session without wrong group, and
  PID/group/session values of 1 or 0;
- zombie or dead saved/live states;
- nonnumeric or changed start ticks;
- boot-ID mismatch;
- actual supervisor death, PID reuse, or identity change during the 200 ms
  survival interval;
- malformed, reordered, duplicated, extra, or missing launch receipt frames;
- a root command that returns a bounded nonzero handshake-missing diagnostic,
  as distinct from the existing injected host-side timeout.

The successful local lifecycle proves one real dispatch/actual-child split. It
does not exercise every target shell scheduling or failure boundary.

### Descriptor and script execution details

The local test proves closure of one inherited descriptor above 2 and observes
empty redirected output files. It does not independently inspect the target of
each of descriptors 0, 1, and 2 inside the child, inject multiple or very high
descriptor numbers, or inject a failure while enumerating/closing
`/proc/self/fd`. The source contract checks the script-as-data spelling, but
there is no separate negative for a failed `cat`, failed `nohup`, failed
`setsid -f`, shell parse error, or an unavailable absolute executable.

### Launcher diagnostics

One nonempty diagnostic scenario is covered, but the fake returns the same
nonempty payload for either diagnostic fetch. The suite does not separately
distinguish launcher stdout from launcher stderr, test the 2,048-byte exact
boundary, reject 2,049 bytes, test malformed Base64 framing, or verify
target-side size/hash retention for each diagnostic under a failed launch.

### Terminal inventory and cleanup

`cleanup-residue-retained` proves a generic cleanup failure is retained, but
the fake transport does not model the complete remote filesystem inventory.
There are no individual negatives for:

- an unexpected terminal filename;
- a missing required input/output file;
- leftover `.tmp` or staging `.b64` files;
- symlink, non-regular file, wrong owner/group, or wrong mode;
- incorrect size or SHA-256 for a known terminal artifact;
- accepted versus rejected terminal inventories with conditional
  `logger.ready` presence;
- partial deletion during cleanup or failure of the final `rmdir`/absence
  verification;
- proof that every host artifact and its hash were durably present before the
  first deletion command.

### Remaining orchestration boundaries

The suite does not exhaust malformed completion schemas and field types,
supervisor/child completion PID mismatches, launcher-diagnostic fetch absence,
all possible READY schema/type errors, or every deadline/clock exception. The
builder checks the generated launcher command's size, but there is no test that
enumerates every generated root command and modeled response against both the
8 KiB and 64 KiB ceilings.

## Deployment status

These coverage gaps are candidates for the next offline test expansion; they do
not authorize edits to or deployment of the frozen candidate.

Deployment also remains independently blocked by controller-parser lineage.
The absence of old processes, marker files, or stage files is necessary but
does not reveal the firmware parser phase and is not sufficient evidence of a
clean state. A future live run requires either closed-world no-transfer lineage
from the unresolved v2 attempt (for example D6 or an already-running complete
USB trace) or an independently established controller-parser reinitialization.
This coverage document performs and authorizes neither.
