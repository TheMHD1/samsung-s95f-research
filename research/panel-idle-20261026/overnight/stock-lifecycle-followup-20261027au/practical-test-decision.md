# Practical decision for one stock-lifecycle RT test

Recorded 2026-10-27 UTC. This is a read-only risk decision based on retained
source, helper, trace and runtime evidence. It made no TV, root, network, USB,
I2C, GPIO, power, reset, UI, firmware or controller request and did not build
or alter a collector or helper.

## Decision

**One stock MODE2 followed by at most one unchanged X observation is a
reasonable, bounded technical experiment if the minimum gates below pass
immediately before and after the action.** It need not be blocked on an
impossible proof that no firmware task anywhere could start. This is a
risk-managed one-shot decision, not proof of atomic exclusion and not a
recovery procedure.

The fresh public sample in `current-host-preflight.json` is favorable:
authenticated root, unchanged boot, software-upgrade status `0`, power state
`lcdon`, screen state `1`, and burn-in-in-progress `0` at uptime
`135607.81..135607.91`. It is not sufficient by itself because it will be
stale at dispatch and none of those getters exposes QDF's private update word.
Repeated in the immediate dispatch bracket, however, those values are useful
negative evidence. Adding an accepted changed-sentinel stock status read
would prove that the private `tcon_flash_update == 1` bypass was not taken at
that call's branch. Together, those facts are a reasonable instantaneous
idle-risk sentinel for one stock action; they are not a lock.

## Hard hazards versus residual risk

### Residual firmware scheduling risk

The copied stock code positively shows a race: operation 41 holds
`tcon_ioctl_mutex`, while the proved QD update worker uses the distinct
`frc_ioctl_mutex`; the lower power-control body neither reads
`tcon_flash_update` nor holds a lifecycle-wide update lock. An updater could
therefore begin after the sentinel and overlap MODE2.

That prevents a claim of concurrency safety, but it is not evidence that an
update is currently active. With fresh public no-busy results, a
changed-sentinel transaction, no observed competing owner, root-serialized
dispatch, a deliberately short sentinel-to-MODE2 interval, exactly one stock
request and no retry, the remaining race is an ordinary scheduling risk. For
this owner's authorized diagnostic and the narrow software-state question,
it is reasonable to accept that residual risk explicitly. A positive busy
signal, unchanged sentinel, timeout, malformed reply, unexpected service
state or identity drift is instead a meaningful reject.

### USB transaction-phase hazard

An unknown pending vendor-OUT payload is a harder stop because a new 12-byte
header could otherwise be consumed in the wrong phase. Before MODE2, a fresh
accepted fixed RT read must end `ReadyForHeader`; old same-boot success is not
fresh enough.

After MODE2, the source-backed normal configuration path initializes
operation `6`, remaining length `0`, installs the header pointer and attempts
an exact 12-byte OUT receive. A complete observed disconnect followed by the
same USB identity/configuration re-enumerating, combined with a serialized
closed-world session containing no intervening vendor OUT or new interface
owner, is sufficient for a practical one-shot phase assumption. It is not a
formal observation that the endpoint accepted the receive descriptor.
Endpoint liveness may still fail; X's short/error/timeout handling must then
preserve the ambiguity and stop without another header. Missing or incomplete
re-enumeration, identity/configuration drift, a bound interface, any unknown
vendor transaction, or ambiguous prior transfer remains a hard reject before
X.

## Minimum predeclared acceptance gates

The action is eligible only under this finite sequence:

1. Pin the current boot, USB identity, exact unchanged MODE2 and X manifests,
   absent old stages and fresh exclusive output paths. Preserve authenticated
   raw envelopes and uptime anchors.
2. Obtain one fresh accepted pre-action RT sample with exact transfer counts,
   release/close and terminal `ReadyForHeader`. Retain the tuple as the
   pre-action software baseline; do not infer picture state.
3. Arm the unchanged private kernel collector and prove it is running,
   quiescent before start, loss-bounded, inside its deadline and has enough
   remaining capture time. Serialize all planned calls through the existing
   root channel.
4. In that armed interval, repeat the exact public preflight. Require upgrade
   status `0`, `lcdon`, screen state `1`, burn-in value `0`, matching boot and
   successful typed replies. Require no positively observed USB holder,
   interface binding, maintenance action or competing TCON operation.
5. Run the already-reviewed sentinel status getter once. Require its sentinel
   to change with an accepted, clean transaction. Use that only as evidence
   that the private update bypass was not taken at that instant; its returned
   status is not a health or light measurement.
6. Dispatch the fixed operation-41/mode-2 helper exactly once with the old
   trace/deadline gate. Any preflight failure, helper timeout, nonzero return,
   boot change or ambiguous completion stops the sequence. There is no retry,
   compensating reset or alternative power command.
7. Let the collector terminate and clean up before any X request. Accept the
   lower lifecycle only through the predeclared channel-scoped rules in
   `readiness-review.md`: complete raw acquisition and PID binding, ordered
   ACDET/reset/USB disappearance and same-identity re-enumeration, ERR_DET
   sample, complete I2C replay, zero ring/decoder integrity errors, and
   verified trace/stage cleanup. An AVOC duplicate leaves the whole collector
   rejected and supports no AVOC claim; a shared-integrity or lifecycle
   failure also rejects the narrow sequence.
8. Recheck the post-reset USB identity/configuration and reject any new owner,
   binding or intervening vendor OUT. Only then invoke unchanged X at most
   once. X must stop on its first uncertainty and may clean only after its
   parsed terminal `ReadyForHeader`, release and close.

This list is an acceptance contract, not approval to bypass a failing gate.
It also does not authorize a modified collector, relaxed AVOC parser,
protection change, firmware write, flash operation or repeated MODE2 loop.

## Result scope

Because X begins only after the old collector has finished and cleaned up,
its first R is a **delayed post-lifecycle sample**. The useful outcomes are
therefore narrow:

- pre-action faulted and delayed first R clean establishes different sampled
  software states across the lifecycle bracket, but not exclusive causation;
- first R clean followed by accepted X `TransitionCaptured` establishes a
  clean-to-fault transition inside X's own finite window;
- `AlreadyFaulted` cannot distinguish persistence from a clear-and-refault
  interval while the collector was finishing; and
- `TimeLimit`/`CycleLimit` proves only the tuples sampled during X.

No owner physical response is required for that technical classification.
The test cannot establish panel light, hardware repair, physical recovery or
the exact fault time.

## Bottom line

The public zeros plus an immediate changed-sentinel result are sufficient as
a documented **risk judgment** for one stock lifecycle when combined with
the exact serialization, trace, phase and stop gates above. They are not
mathematical absence proof. The private updater's scheduling race is accepted
as a disclosed residual risk; an unknown USB parser phase is not. The current
retained preflight shows that such a test is plausible, but it must be
repeated in the dispatch window and all gates must pass before any MODE2 is
sent.
