# Independent onset synchronization design review

2026-10-27 UTC. Offline retained-source review only: no TV, USB, root, UI, reset or network operation. Scope is an additive observer fork and **one Left down/up action from an already qualified Apps state**, with one USB owner and unchanged read addresses, pairs and failure rules. A second Left to For You is outside this revised bounded trial. Existing user authorization covers centrally coordinated tests; this review introduces no permission requirement.

## Recommendation

Use one bounded action worker, started only after the observer's first complete clean `R,M,C,H,L,R` cycle, while the original USB loop continues on its original thread. This provides a local causal ordering and avoids the avoidable blind interval from blocking the sampling thread on normal-key subprocesses. Preserve that first clean cycle separately from rolling `LastClean`; retain the one-shot trigger marker and key dispatch/return intervals in the same target monotonic clock domain.

The original suggestion to prohibit USB OUT while a normal-key child was pending was a design choice, **not an established transport invariant**. With that choice, an onset during a blocking key would necessarily be unobserved until the next read, irrespective of whether the key ran inside or outside the observer process. An external marker alone cannot eliminate that gap. The parent's clarified concurrent-worker design is supported by the retained ordinary-key source and preserves exclusive ownership of the vendor endpoint.

No reviewed evidence identifies normal `input_keyevent` as a second vendor-USB actor. Its retained1744-byte file, SHA-256 `7284ad5b0117a96a166a4fe327c6361bea998e5d2086a0e1a36d2a3477a87db9`, is a Bash script. The explicit down/up branches only call:

```text
/usr/bin/dbus-send --system --type=method_call --print-reply
  --dest=org.enlightenment.wm /org/enlightenment/wm
  org.enlightenment.wm.Test.EventKey uint32:1/0 string:Left
```

It has no usbfs open, vendor bulk request, controller reset, power command or arbitrary register write. It waits for the D-Bus reply, which explains why a key subprocess can block even though the observer could independently sample. A normal page transition can change display/controller behavior; that is the intended stimulus. The reviewed script does not prove that the entire compositor/application graph can never touch USB, but there is no positive source or execution evidence here requiring that hypothetical coupling to become a hard stop. A disconnect, changed identity, unexpected state or bad transfer is still handled by the existing terminal failure path.

## What the existing observer actually guarantees

`Program.cs` allocates all captures before preflight/open. Every header starts with phase `Unknown`; an exact12-byte OUT sets `ExpectingIn`; the one exact matching IN returns to `ReadyForHeader`. An accepted header's matching IN is attempted even if a later timestamp fails or the deadline expires. Short/long/error/throwing transfers never permit another header. Sleep occurs only between completed pairs/cycles. Release and close remain in `finally`.

The fixed windows remain R=`0x47012400/256`, M=`0x470004a0/68`, C=`0x47000bc0/16`, H=`0x4700d0e0/96`, L=`0x47010f00/64`; each cycle remains `R,M,C,H,L,R`. R is clean only for stop0/fault0/gate1 and faulted only for stop1/fault0x1001/gate0. The underlying reads are sequential and cannot become an atomic event tuple through synchronization.

The clean-cycle hook belongs after `LastClean.CopyFrom(Current)` and `Current.Clear()`, after `CleanCyclesCompleted` increments, and before nominal-period sleep. Require that this is the first full clean cycle, phase is `ReadyForHeader`, the one-shot action has never been armed, and the global deadline has sufficient predefined action margin. Triggering merely after the first clean R-start is too early: it does not qualify the full clean baseline. Mark the action attempted **before** scheduling it, so a scheduling/start exception cannot cause a later cycle to retry it.

The current observer only stores final output at the end. An external actor cannot robustly synchronize to its first clean cycle without an additive explicit signal. Therefore an injected action worker is the smaller design for this one action. An external worker would require a one-use nonce-bearing arm/ready/trigger handshake and its own timestamp/exit reconciliation; it should not rely on polling a stale file or guessing from the20-second process lifetime.

## Required action and concurrency contract

1. **One USB thread and owner.** The action worker receives no `IOps`, USB fd, capture buffer, reset helper or USB library reference. It cannot issue a header, claim/release, or alter phase. It reports only bounded immutable action events/result. The sampling thread remains the only caller of `ReadPair` and the only writer of captures/protocol state.
2. **One fixed key pair.** Preflight the boot, exact stock utility hash and calibrated current Apps/focus context before observation. The worker performs only `Left down`, the existing150ms hold, and `Left up`. No wake, extra Up, second Left, navigation loop, cached-state retry or recovery is hidden inside it. If focus is not the calibrated state, report the trial unqualified instead of adding keys. Cached Apps alone is not proof of focus. A later cached tab can confirm Live navigation separately from physical light.
3. **Timestamp boundaries honestly.** Record arm time, successful scheduling/start, immediately before/after each down/up subprocess call, each exit status, and worker completion/join. Those bound dispatch/reply, not the compositor's exact event-consumption time or physical light onset. Use the same `IClock`/verified monotonic basis as the USB transfer records. Host UTC and coarse `/proc/uptime` cannot replace target monotonic ordering. If clock acquisition fails, record missing stamps and reject temporal qualification; still attempt the key-up cleanup and finish any already accepted USB pair.
4. **Bound children and output.** Launch fixed executable/arguments without shell interpolation where possible. Each action subprocess needs a finite deadline, bounded/drained stdout/stderr and an explicit descendant policy. A child waiting on D-Bus must not block the USB thread. The150ms hold is a requested minimum interval, not a real-time guarantee. No unbounded `WaitForExit`, task wait, pipe read or thread join belongs on the USB path.
5. **Always attempt Up once.** Attempt the one matching key-up in worker `finally` after any down attempt, including a nonzero down exit, timeout or exception. Do not retry down. A killed/lost child or failed up leaves input completion unknown; record that rather than claiming cleanup. The worker may finish that required up even if the observer has already seen the fault or reached its USB deadline. No automatic reset follows.
6. **Finish pending IN before considering other failures.** A worker failure/cancellation flag must not interrupt `ReadPair` between its accepted OUT and matching IN. Observe stop flags only at safe pair boundaries. If action failure is terminal for the trial, stop issuing new headers after the pending pair; keep the partial capture and exact phase/error diagnostics.
7. **USB deadline and action cleanup are distinct.** Stop new headers at the original20-second/80-cycle bounds. Do not skip the pending matching IN. Perform bounded worker reconciliation without masking release/close. State the possible total overshoot as the current USB pair allowance plus the defined action cleanup allowance; an unjoined worker cannot be reported as a clean successful run. Never allow a worker launched near the end to escape into a later trial.
8. **Keep first baseline and bounded output.** Add a fixed preallocated trigger-baseline capture; ordinary rolling LastClean continues unchanged for onset bracketing. Action event storage is fixed-size. No growing per-cycle list, UI snapshot subprocess or JSON serialization belongs inside the transfer loop. Recheck the24,576-byte output bound with the additional retained baseline and worst-case errors.
9. **Preserve scientific status distinctions.** A transport-clean run can still have action failure or no qualified navigation. A fault before action dispatch is pre-action recurrence, not an action-triggered onset. Fault intervals overlapping the down/hold/up interval are sampled brackets, not exact execution times. Keep physical annotation separate. If the panel is visibly on but RT is already faulted, retain that counterexample; do not reset to make the initial condition fit.

The scheduling choice can retain the original250ms nominal period; moving action launch before that sleep already lets it overlap the next scheduled sample. Removing that sleep for only the trigger cycle might improve latency, but changes cadence and should be an explicit reviewed/tested fork choice. It is unnecessary for fixing the blocking-child blind interval.

## Evidence from BH, BI and BS

BH proves the synchronization problem directly: an intended Home observation finished clean, but the owner's actual keypress was not established within that recorder interval. The later sample was already faulted. Local first-clean triggering and monotonic action brackets address this missing temporal linkage; they do not promise the physical transition is captured at exactly one instant.

BI proves that positive owner recovery and successful UI calls cannot rehabilitate a rejected acquisition. Its forced vlog/export termination and incomplete action-PID I2C replay remain independent record-quality defects. Do not launch another collector inside the key worker or use it to revise the old record's acceptance.

BS distinguishes the one recovered I2C post-check failure from USB parser phase. It found no positive edge from that I2C retry to the vendor parser. It also preserves the concrete first-header limitation: configuration intent discards the receive-submission return, so a fresh configured instance alone does not prove endpoint liveness. This additive synchronization design neither resets the controller nor repairs a previously unknown phase. Central coordination must supply the same qualified first-header/no-intervening-OUT lineage used for the actual observer instance. Once the observer has completed a full clean cycle, the normal exact-pair model carries subsequent `ReadyForHeader` transitions. An action worker must not weaken that model.

## Minimum host test matrix for the additive fork

These are requirements for fake-transport/fake-action tests before centrally coordinated execution; this review has not seen or tested a new fork implementation.

| Case | Required assertion |
|---|---|
| Two clean cycles, worker fast | Exactly one arm and one Left down/up; no trigger at first R-start; trigger only after all12 first-cycle transfers; first baseline retained. |
| Worker remains pending for several cycles | USB cycles continue; no blocking wait on observer thread; only the observer issues all USB calls; no repeated arm. |
| Fault while down child blocks, during hold, or while up blocks | Transition and bounded post-fault capture retained with actual transfer intervals; one up still attempted; no second key. |
| First R already faulted/unexpected; first-cycle end faulted; first cycle incomplete | No action; preserve original AlreadyFaulted/Unexpected/transport behavior. |
| Arm/schedule/start exception | One attempted arm, zero retries; stage/exception retained; no dangling worker or second key. |
| Down nonzero/throws/times out | Up attempted exactly once, down never retried; failure cannot cancel a matching pending IN. |
| Up nonzero/throws/times out | Input completion unproved, accepted scientific status false, no reset/recovery or next key; bounded exit/reconciliation. |
| Deadline during OUT/IN while worker pending | Exactly matching IN attempted; no later OUT; cleanup and worker join bounded and independently reported. |
| Clock failure at each action boundary | Missing timestamp explicit, no invented ordering; still one up cleanup and matching pending IN. |
| Worker finishes/fails immediately between OUT and IN | Single-thread USB ordering unchanged; failure handled only after IN. |
| Transport failure while worker pending | No further header or USB retry; release/close attempted; matching up cleanup remains bounded. |
| Stale/duplicate external marker (if external design used) | Cannot launch action or arm twice; run nonce and first-clean handshake enforced. |
| Baseline overwritten by many later clean cycles | Trigger baseline stays byte-identical while rolling LastClean/discard counters continue. |
| Maximum retention, partial transfer, longest action errors | Output remains below cap; actual counts/prefixes preserved; action output cannot deadlock pipes. |

Inject action scheduling and completion for deterministic tests rather than assuming real host thread interleavings. A separate real host worker blocking test can prove that an actual wait does not stall the sampling thread; it does not need any TV or USB library. Existing fake-transport regression tests for count/exception/clock/deadline/release/close must still pass unchanged.
