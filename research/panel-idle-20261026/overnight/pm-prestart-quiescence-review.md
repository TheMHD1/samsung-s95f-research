# PM observer pre-start quiescence review

Status: design-only, offline review. This document does not modify or clear the
hash-pinned PM observer, does not reclassify either failed smoke, and does not
authorize another capture. No target, root, network, or TV action was used to
prepare it.

## Retained failure and exact scope

The second five-second PM smoke is retained at
`pm-idle-smoke-20261026.onset`. Its `record.json` is 3,440 bytes, SHA-256
`247298a3adb37a33ace809438fc6301424c0a3ae5519bca4e59d69b45babfe29`.
It remains `accepted=false`, `technical_capture_complete=false`, and
`diagnostic_eligible=false`. Quiesce and cleanup were independently verified;
there is no capture trace sidecar and no physical or absence conclusion.

The relevant raw evidence is:

- `partial-fds.txt`, 2,245 bytes, SHA-256
  `75ba03cce48df409ac270420416d40da724a99ad6ff86a6dfd44ec33eeb46bbc`;
- `remote.sh`, 35,323 bytes, SHA-256
  `082aaf8c9bb8a76a314fc4528119bfef0079847372288b01cf19ea4a8546e08b`;
- `partial-meta.txt`, 253,691 bytes, SHA-256
  `e76a4caa8546423c6ce5d1526765e1c429f4a735389d75d1b96889de29cbdabc`.

The exact START, PRE, and ARM TID lists agree and contain 23 TIDs. Tracing was
enabled at uptime `68292.29`, the `CAPTURE_TRACE_ARMED` marker was emitted, and
the read-only sweep then retained numeric non-54 states for TIDs 706 through
1010. Its first read of TID 1011 at uptime `68292.35` was:

```text
54 0x21 0xc010643a 0xf4efe4ac 0x10ac5 0x0 0xf4efe4ac 0xf4efe44c 0x42edcf2c
```

The collector deliberately exited 86 immediately. That is a correct rejection
under the frozen contract. Because the private trace instance was removed by
the authenticated cleanup before export, the retained artifacts do not show
this call's return, duration, or endpoint. None may be inferred.

## The invariant that must not change

Before `CAPTURE_PREROLL_START`, every exact ARM TID needs a positive state
anchor proving that it was observed outside ARM32 syscall 54 at least once
after raw-syscall tracing became continuously active. This is necessary to
exclude a call that entered before tracing and could otherwise remain wholly
invisible across the physical window.

A timeout, a fixed number of observations, literal `running`, or repeated
numeric 54 observations is not such an anchor. Exhaustion must reject. The
physical window remains exactly `CAPTURE_START..CAPTURE_END`; pre-roll, drain,
thread-lifecycle, loss, FD, marker, and pairing rules are not relaxed.

## Smallest coherent correction

Treat a numeric 54 sample as a retained **transient-active** attempt, not as an
immediate success and not as an immediate fatal error. Retry that same TID
under the already declared limits used for `running`:

- at most eight total attempts for the TID;
- 2 ms requested sleep between attempts;
- the existing absolute `ENABLE_AFTER..PREROLL_START <= 0.500 s` prelude bound;
- the existing `TARGET-PREROLL_START` range of 0.750 through 1.250 seconds.

Only a later parseable numeric syscall number other than 54 qualifies the TID.
Read failure, malformed text, TID disappearance/change, attempt exhaustion, or
prelude deadline exhaustion rejects before `CAPTURE_PREROLL_START`. This is a
fixed a-priori false-negative budget, not a claim that every wait-vblank call
finishes in it. Earlier retained trace timing makes a short retry plausible,
but cannot prove that a future call will fit.

The host validator must accept preceding attempts only when each is either
literal `running` (`indeterminate`) or numeric 54 (`transient_active_54`) and
the final attempt is numeric non-54. It must retain every raw line and classify
the terminal row separately. `active_nr54` becomes a raw list of intermediate
attempts, not an empty-list assertion. No final non-54 row means
`syscall_quiescence.complete=false` and rejection.

## Why sequential polling remains bounded evidence

The sweep need not be a simultaneous snapshot. Raw syscall enter/exit events
for the exact PRE TIDs are enabled before `CAPTURE_TRACE_ARMED` and remain
enabled through drain. Once a TID has a terminal non-54 point sample, any later
54 entry should be retained. If such a later call begins in the trace prelude
and overlaps START, the existing unbounded-start rule rejects it. A pre-roll
entry that crosses START is accepted only under the existing fully recorded
boundary-pair contract. An unresolved pre-roll/window entry at drain rejects.

This reasoning is conditional on all existing evidence remaining true:

1. START, PRE, ARM, post-sweep, and END TID sets are identical.
2. Both raw-syscall filters read back the exact PRE TID set and ID 54.
3. Sched fork/exit/exec tracing is active before the sweep; any relevant
   lifecycle ambiguity rejects, including a transient new AVOC thread omitted
   from the fixed syscall filter.
4. Tracing is continuous from the bounded enable bracket through drain.
5. Per-CPU retained/written/loss accounting and marker retention are exact.

Thus a qualified early TID may enter syscall 54 while later TIDs are still
being sampled, but that new enter is traced rather than invisible. A TID that
never supplies a terminal non-54 sample never qualifies.

## Role and limit of traced exits

An orphan syscall-54 exit in the trace prelude is compatible with a call that
was already active when tracing began. It must remain raw outside-window
evidence and cannot prove return success, identify a physical effect, or become
a window pair.

The first correction should **not** use an online trace-file search for an exit
as an alternative qualification path. Doing so would require an exact
per-attempt ordering anchor, non-consuming concurrent trace reads, a retained
same-TID/saved-TGID exit, and final proof that the row survived without loss.
An unanchored exit might belong to a different completed call. Adding dynamic
markers or an online trace state machine expands both the shell and validation
surface without being necessary if a terminal `/proc/.../syscall` sample is
obtained.

If bounded polling repeatedly cannot observe TID 1011 outside syscall 54, the
safe outcome is another pre-window rejection. A future hybrid trace-exit design
would need separate review; it must never qualify merely because the deadline
expired or because some exit for the TID exists.

## Prelude and controller budget

The proposed change does not increase the 0.500-second prelude, target lead,
collector timeout, controller timeout, or 85/90-second capture budget. The
post-sweep TID equality check, `FDS_PREROLL` acquisition, and PREROLL marker
must still finish inside that same 0.500-second envelope. Therefore retrying 54
can consume only slack already present; it cannot delay START.

The implementation should preserve timestamps before every attempt and the
existing `SWEEP_START`, `SWEEP_END`, and PREROLL body clocks. It should use the
absolute prelude deadline on every attempt, including after sleep, rather than
relying only on attempt count. If the eight-attempt retry leaves insufficient
time for the post-sweep TID/FD checks and PREROLL marker, the run rejects. Any
proposal to enlarge the prelude or schedule tracing earlier requires a new
controller/ring/resource analysis, especially for the 90-second mode.

## Required offline tests before implementation review

1. `running, 54, 54, non54` qualifies one TID; all attempts and raw arguments
   remain in the report.
2. Eight numeric-54 rows, mixed `running/54` exhaustion, read failure, malformed
   number, TID-set change, and deadline overrun each reject.
3. A TID qualified non-54 and then having a traced enter in the prelude is
   handled only by existing trace pairing: prelude-to-window and unresolved
   overlap reject; prelude-only completion is outside physical evidence.
4. A pre-trace 54 followed by a prelude orphan exit and terminal non-54 sample
   qualifies quiescence but keeps that exit unmatched/outside; it never becomes
   an ordinary or boundary pair.
5. A missing terminal sample cannot be rescued by an arbitrary prelude exit.
6. Attempt indices, TID grouping/order, raw timestamps, maximum attempts, and
   all prelude/marker bounds are exact and adversarially tested.
7. The retained second-smoke sidecars remain byte-pinned and rejected under the
   historical implementation. An in-memory validator fixture may append only
   explicitly synthetic retry rows; it must not rewrite the raw artifact or
   claim what TID 1011 actually did after the retained first observation.
8. Public dry/run dispatch, cleanup, generated-shell syntax/size, no-global-
   tracing, no-control, no-retry, and original physical/absence tests remain
   unchanged.

## Recommendation

Implement only numeric-54-as-bounded-retry plus the matching host evidence
schema. Do not accept a numeric-54 terminal row, do not infer a return, and do
not use an unanchored trace exit as a substitute. This addresses the observed
transient-start failure while keeping invisible pre-trace calls fail-closed.
Independent exact-byte review is required before any new passive smoke; this
review supplies no 85/90-second or physical/causal clearance.
