# Stock MODE2 followed by the unchanged X observer: readiness review

Recorded 2026-10-27 UTC. This is a read-only assessment of retained local
evidence. It made no TV, root, network, USB, GPIO, I2C, UI, power, reset,
firmware, or controller request and did not build or alter a helper.

## Decision

**The question is diagnostically useful, but the sequence as currently
specified is not execution-ready.** One new stock MODE2 run followed by one
unchanged X run could answer the narrow post-lifecycle question only after the
missing lifecycle, maintenance, baseline, and vendor-protocol prerequisites
below are closed. It is not cleared as a blind invocation now.

This is a new technical question rather than a retry intended to recover the
picture: does the RT tuple appear clean after one positively observed stock
lifecycle, and does it remain clean or fault during X's fixed finite window?
That distinction is sufficient to make one future experiment scientifically
nonredundant, but it does not waive the existing one-shot, positive-bracket,
and no-retry requirements.

## What the retained MODE2 run proves

The fixed helper is still byte-identical to its reviewed build:

- build manifest SHA-256
  `67aa102cdd3cdc85ed7fabb68b37d570b721664298317f24f9bd24b8250f9faa`;
- `Program.cs` SHA-256
  `2f4333d381a0a5dbba4b6fcdb87790438f595f981dfadd3e6e6e76b341ae5e9b`;
- runner SHA-256
  `5c7ec5d3581e349d7f91669977123497147777e573fbdefd8a9b6f96dcf3cb75`.

It accepts no argument selecting another operation or mode. Its one ioctl is
the fixed 16-byte operation-41/mode-2 envelope, it has no retry or compensating
command, and it classifies return zero only as `kernel_return_zero_only`.

The earlier actual helper record, SHA-256
`5571bc79ca021113f76428969f8f6d2e3ebf18224438e5cd168cfb5a9ec315d2`,
is accepted and cleaned. More importantly, the separately retained transport
evidence positively shows that this invocation reached the lower stock path:
ACDET low, OCL reset-mailbox value 1, USB `04e8:2001` disconnect, OCL reset
value 0, the same detailed USB identity re-enumerating, ACDET high, ERR_DET
sample zero, and 346 complete I2C transfers through the normal check/replay
tail. The transport audit is SHA-256
`70b0d0f2f7a8301d2b598d45a3510a4304bd493c2e7507e0bb1c8f270baf8847`.

Those facts prove one historical stock lifecycle and fresh host USB
enumeration. They do not make a future helper return zero into action
acknowledgement, prove rail voltage or emitted light, or prove that the USB
vendor parser initializes to `ReadyForHeader`.

## What the unchanged X observer can establish

The unchanged X wrapper remains pinned by manifest
`915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1`
and runner
`a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82`.
It performs only fixed target-`0x101` reads in
`R-start,M,C,H,L,R-end` order, has no writes or retries, and accepts cleanup
only after a parsed terminal `ReadyForHeader` result.

Its prior real run ended at uptime `126642.16` as accepted
`AlreadyFaulted / OnsetMissed`, with tuple
`stop=1 / fault=0x1001 / ordinary_gate=0`. A later fixed reader ended at
uptime `131332.14` on the same Linux boot with exact transfers,
`ReadyForHeader`, release/close, and cleanup. This is useful preexisting
lineage, but neither observation is an immediate pre-MODE2 RT baseline.

If a future stock lifecycle and post-lifecycle X run were both positively
accepted:

- first `R = 0/0/1` would prove a clean RT sample after the lifecycle. A later
  accepted `TransitionCaptured` would establish a software clean-to-fault
  transition during X's finite window;
- accepted `TimeLimit` or `CycleLimit` would show clean sampled tuples through
  that finite window only;
- `AlreadyFaulted` would show that fault state was present by X's first read,
  but could not distinguish persistence from clear-and-refault before that
  read; and
- an unexpected tuple or any transport/identity ambiguity would be retained
  and stop the experiment without retry.

None of those outcomes establishes visible picture, emitted light, repaired
hardware, or a causal relation to a particular UI/content state.

## Concrete blockers to running the pair now

### 1. A new MODE2 lifecycle would not be positively observed

The unchanged power helper's accepted result proves only an ioctl return of
zero. The historical lifecycle became positive evidence because independent
kernel/ftrace/USB/I2C records captured the lower sequence. The unchanged
runner does not arm that trace, record an action marker, or enforce the old
orchestrator's trace/deadline gates. X starts only after the helper returns and
does not observe ACDET, mailbox, disconnect/re-enumeration, or replay.

Therefore the two unchanged helpers alone cannot satisfy the premise “after a
positively observed stock lifecycle.” The older run proves capability, not
that a new request took the same branch. The earlier 60-second containing
observer also remains rejected for its duplicate syscall-enter invariant and
cannot be relabeled as an accepted reusable bracket.

The existing reviewed MODE2 plan is stricter for this reason. Its technical
variant requires pre/post status with matching raw kernel evidence when
available, ERR_DET GPIO, selector `0x128`, the reviewed AVOC/QD source/cache
fields, and an already armed passive trace with an action marker. Those are
not optional physical-picture demands; they are the retained technical checks
that distinguish a requested lifecycle from one positively observed to have
run. No such current bracket is armed or prepared by the unchanged runner.

### 2. There is no fresh pre-action RT sample

The accepted X tuple at uptime `126642.16` is thousands of seconds before the
current decision point. Same Linux boot and absence of a known reset do not
exclude an unmodelled writer, initialization path, or independent state
change. Consequently, even a clean first R after MODE2 would prove a clean
post-lifecycle sample, but not by itself that MODE2 changed faulted to clean.
Attribution of a clear requires a fresh accepted pre-action R plus the
positive lifecycle bracket. This review does not propose or authorize an
extra collector or equivalent replacement for the rejected combined recorder.

### 3. MODE2 does not prove the post-enumeration vendor parser boundary

The last known vendor transaction before this review ended at
`ReadyForHeader`; thus there is no retained pre-MODE2 pending payload. MODE2,
however, deliberately disconnects and re-enumerates the device. Existing
analysis proves only a new host USB enumeration boundary, not initialization
of the application parser that consumes X's 12-byte headers. X's descriptor,
unbound-interface, open and claim checks cannot prove that application state.

X fails closed after a short/failed/throwing transfer and will not send a
second header from an unknown phase, but its first OUT header has already been
sent at that point. That stop rule limits consequences; it does not remove the
post-reset parser assumption. A past later successful vendor read after the
historical MODE2 run is corroborative, not proof of the immediate first-header
state for a new lifecycle.

### 4. Current maintenance exclusion is absent

The MODE2 helper is an invasive controller power lifecycle and has no proven
rollback if either half fails. Its preflight checks boot, binaries, device and
identity, but does not positively establish that controller firmware update,
Samsung panel maintenance/screen optimization, or another TCON lifecycle is
idle. The reviewed build explicitly records the live firmware-update state as
an unresolved concurrency boundary. Cached Apps/screensaver/compositor state
is not a maintenance-idle signal.

A fresh, independently supported idle determination is therefore a required
precondition. Mere absence of a known update in old records is insufficient,
especially under the owner's no-brick constraint.

## Bounded future eligibility

One future run could be reviewed as eligible only if all of these are true
before dispatch:

1. current boot/identity and a fresh pre-action RT tuple are accepted and
   retained;
2. firmware/panel-maintenance and competing TCON activity are positively
   excluded by an already-supported read-only source;
3. the single MODE2 action has the existing reviewed pre/post status, GPIO,
   selector-`0x128`, AVOC/QD and action-marked passive bracket, and that
   bracket positively captures the lower lifecycle rather than relying on
   ioctl return zero;
4. post-enumeration vendor-parser readiness is independently justified, not
   inferred from USB descriptors alone;
5. the unchanged X manifest and pinned boot still match and its output path is
   fresh; and
6. the plan contains exactly one MODE2 invocation and at most one X
   invocation, with no automatic retry, invented rollback, or physical
   recovery claim.

If MODE2 changes the Linux boot, the unchanged X wrapper must refuse its
pinned-boot preflight. If either action is ambiguous, evidence is preserved
and the sequence stops. A later owner observation may separately report the
picture, but physical feedback is not required for the narrow software-state
classification above.

## Conclusion

The existing evidence makes the proposed RT-lifecycle question meaningful,
not redundant. It does **not** make a blind helper-then-X pair trustworthy.
At present the new action would lack positive lifecycle observation, an
immediate faulted baseline, a proved post-reset vendor-parser boundary, and a
current maintenance-idle fact. Those are concrete evidence and safety gaps,
so no MODE2 or X execution is cleared by this review.

## Addendum: channel-scoped lifecycle acceptance

For the narrower software question, acceptance of the observer's entire AVOC
model is **not indispensable** to proving that the lower stock lifecycle ran.
A predeclared, independent kernel/I2C-channel result can establish only that
component while the containing collector remains rejected. This is the same
separation already demonstrated by the frozen historical decode: its raw trace
had `104917/104917` retained/written/recognized event rows, zero known-I2C
parse errors, and 379 structurally complete transfers, even though the AVOC
syscall-pair parser correctly rejected a duplicate enter.

Such a future channel result would be usable only if all of the following
pass independently of the AVOC parser:

- the unchanged collector's raw trace and relevant kernel sidecars are
  retrieved completely, size/hash bound, monotonic, and free of ring loss;
- the one helper record binds its exact PID, boot and execution interval to
  the trace, and the trace contains one complete ordered lower sequence:
  ACDET low, reset-mailbox assertion, USB disappearance, reset release, the
  same detailed USB identity re-enumerating, ACDET high, ERR_DET sampling and
  the normal I2C replay tail;
- the frozen I2C decoder reports complete ring accounting, no parse errors,
  no orphan or partial transfers, and complete PID-bound replay transfers;
- the collector has terminated and its trace/stage cleanup is verified before
  X is started; and
- the separately pinned status/GPIO/selector and AVOC/QD source/cache samples
  meet their own raw identity, timing and parser contracts. Raw AVOC/QD bytes
  may be retained as context, but a rejected AVOC pair stream cannot support
  AVOC absence, onset, return-value or consumption claims.

An AVOC duplicate alone is therefore a channel-specific rejection, not a
reason to discard an otherwise complete kernel/I2C lifecycle substream. A
shared-integrity failure—ring overwrite, truncated/hash-mismatched trace,
missing helper/PID binding, incomplete lifecycle order, malformed I2C rows,
or failed collector cleanup—invalidates the narrow result too. The full
collector must still remain `accepted=false`; no parser rule is weakened and
the offline I2C result does not rehabilitate it.

This resolves only the positive-lifecycle-observation part of blocker 1. It
does not close blockers 2 through 4: a fresh pre-action RT sample, a current
maintenance/competing-lifecycle exclusion, and an independently justified
post-enumeration vendor-parser boundary remain required. In particular, X can
run only after the old collector has completed and cleaned up, so its first R
is a **delayed post-lifecycle sample**, not an immediate transition bracket.
A clean first R would prove clean state at that later sample; `AlreadyFaulted`
would not distinguish persistence from a clear-and-refault interval. Only a
clean first R followed by X's own accepted transition can prove a
clean-to-fault transition inside X's finite window.

Accordingly, channel-scoped acceptance is a sound bounded substitute for the
whole-observer invariant only for the proposition “the stock lower lifecycle
ran.” It is not execution clearance, controller-parser readiness, causal
attribution, physical recovery evidence, or permission to repeat MODE2.
