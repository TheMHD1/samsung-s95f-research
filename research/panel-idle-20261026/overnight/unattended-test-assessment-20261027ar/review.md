# Unattended reuse assessment for the X passive observer

Recorded 2026-10-27 UTC. This is an offline review of retained files only. It
made no TV, network, root, USB, UI, power, controller, reset, protection, or
target operation. It does not build, alter, or replace a collector; the
rejected AL combined-recorder work remains stopped.

## Decision

An unchanged X run in the current retained fault state, without an intervening
and independently evidenced lifecycle, is redundant. Its first `R` read would
be expected to classify the same `stop=1 / fault=0x1001 / ordinary_gate=0`
tuple as `AlreadyFaulted`, then retain another late sequential `M,C,H,L,R`
set. That can detect an unexpected byte change, but it cannot recover the
missed onset or add a clean side of the comparison.

There is one narrower test shape that could add evidence: after an
**independently observed** ordinary standby/off then on lifecycle, and after
same-boot host reachability returns, run the unchanged reviewed X observer
once with a fresh output directory. That prerequisite is not presently met.
The currently available `KEY_POWER` route is a state-dependent toggle, not a
verified off command followed by a separately verified wake path. With no
physical observer and no positive two-phase software acknowledgement, two
blind toggles cannot establish that standby and wake both occurred and could
leave the set unreachable. Therefore this review does **not** clear an
unattended power action or a new X run now. The causal test should wait unless
a separately reviewed path first supplies that lifecycle evidence.

If that prerequisite is later met, the resulting run would be a
controller-lifecycle test, not a physical-blackout or repair test. No status
getter, GPIO getter, extra UI request, reset, threshold change, or protection
write should be interleaved with its finite run, and there should be no
automatic retry.

The ordinary power action does **not** establish clean state. Only X's first
exact `R` response can do that:

- `Clean` (`0 / 0 / 1`) positively establishes a controller-clean RT sample
  at that instant without physical feedback. A later `TransitionCaptured`
  would give a technical clean-to-fault bracket; `TimeLimit` or `CycleLimit`
  would show that the sampled tuple stayed clean through the finite run.
- `AlreadyFaulted` establishes only that the observer began after a fault was
  present. It cannot distinguish “standby never cleared it” from “it cleared
  and re-faulted before the first read.” If the ordinary power lifecycle was
  separately evidenced, an identical retained tuple would still be useful
  negative lifecycle evidence, but not a clean control.
- An unexpected first tuple, a boot/identity refusal, or an ambiguous
  transport result must be retained as such and not retried.

The current wrapper is specifically pinned to boot
`00000000-0000-4000-8000-000000000000`. An ordinary standby is historically
capable of preserving Linux and daemon identities, but that is not guaranteed.
If the off/on changes the boot, the unchanged wrapper must refuse; that result
does not authorize a rebuild or a looser invocation in this assessment.

## Why this does not replace the owner-assisted causal test

Launching X **after** an Apps, For You, Live, Back, or Power action cannot
bracket a transition caused by that action. If the first `R` is faulted, onset
was already missed; if it is clean, the action did not produce a fault that
survived to the sample. The 20-second observation can capture only a later
transition.

The unattended UI evidence also lacks a reliable consumption and physical
acknowledgement. The retained V4/V5/V6 AppControl calls returned normally, but
the sampled UI state remained Apps and the audits correctly classify the For
You request as attempted rather than rendered. The current read at uptime
`133210.63` likewise reports cached Apps, logical compositor `Display State:
On`, and full-screen screen-saver windows; none measures OLED light. By
contrast, the earlier owner-driven Apps-to-For-You capture confirmed the
software tab change, but its black-picture report did not provide a calibrated
onset inside the capture.

Historical owner-power evidence contains a host `lcdon -> standby -> lcdon`
transition on the same Linux boot, but that rescued capture was incomplete and
contains no RT clean/fault sample. It proves neither physical recovery nor
that ordinary standby clears `0x1001`.

Therefore a **verified** standby/on followed by one X run could answer the
limited question “did the RT tuple present clean after this lifecycle, and did
it remain clean or transition during the next finite window?” The presently
available blind toggle sequence cannot supply that prerequisite and should not
be used unattended. Even a qualified future test cannot answer
“was the panel visibly restored?” or “did a known UI/content transition cause
the blackout?” The latter causal test still requires a visibly lit Apps
control, X already active from a clean first `R`, an in-window known failing
transition, and the owner's physical picture annotation. A clean unattended X
sample is an epoch-specific technical control, not proof that the state will
remain clean until a later owner session.

## Reviewed implementation and evidence

The unchanged wrapper is SHA-256
`a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82`
under wrapper manifest
`915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1`.
It performs only fixed target-`0x101` reads in cycles
`R-start,M,C,H,L,R-end`, stops immediately on an initially faulted or
unexpected tuple, uses no retries or writes, and accepts cleanup only after a
known `ReadyForHeader` result.

The prior real X run is independently audited at terminal uptime `126642.16`:
`AlreadyFaulted / OnsetMissed`, six fixed requests, twelve exact bulk
transfers, identical initial/final R bytes, successful release/close, and
verified stage removal. Its late candidate is not an event-time or physical
picture record. The current UI metadata file is SHA-256
`63fc0e6000e91d6427746ddf1a267bb92c7afd49d92b535ed2fa4850b291eb3a`;
it is host/UI metadata only and does not alter this decision.

## Addendum: X has no live clean/readiness signal

The unchanged X wrapper cannot honestly announce that its first R is clean
while it is running.

Its local `record.json` progresses as follows:

1. During staging and the zero-I/O self-test it says
   `target_operations_status=not_started` and `native_invocations=0`.
2. Immediately before the one foreground root call, it changes to
   `native_invocations=1`, `target_operations=null`, and
   `target_operations_status=inflight_or_unknown`.
3. It does not record terminal metadata, exact request counts, retained R
   bytes, or the native classification until that foreground root call has
   returned and the complete envelope has been parsed.

The second state proves only that dispatch is beginning. It precedes remote
shell preflight, native process start, USB open/claim, the monotonic start
stamp, and first R completion. It is not `LOGGER_READY`, “observer active,” or
“first R clean.” Native `Program.cs` emits its sole execute JSON with
`Console.WriteLine` only after `Run` has ended. The remote shell redirects that
line to a private file and returns its framed contents only after the native
process exits.

The persistent-root server also holds one `asyncio.Lock` across the entire
awaited foreground `connection.execute`. A second command through that server
cannot send an in-window UI action or poll target state. This differs from the
old detached V6 logger, which published a live READY artifact before its quiet
hold. The owner using a physical remote is independent of that root lock, but
the wrapper still supplies no live clean acknowledgement.

### Honest owner instruction

If an owner-assisted run is later authorized from a separately established
visible Apps control, the strongest honest GO message after observing the
local inflight record is:

> The observer command has been dispatched, but its first RT sample is not
> yet known clean. Perform the agreed action once now and immediately report
> what you physically see. We will accept timing only after the final samples
> show a clean-before/fault-after bracket; an initially faulted result means
> onset was missed.

No countdown or delay can upgrade that dispatch marker into source-backed
readiness. If the owner acts before the first clean R completes, the run may
legitimately end `AlreadyFaulted`; it must be retained rather than described
as a captured transition or automatically repeated.

### Retrospective bracket requirements

After completion, an action-correlated technical bracket is acceptable only
if all of the following are present:

- the native result is accepted `TransitionCaptured`, not `AlreadyFaulted`,
  `TimeLimit`, `CycleLimit`, or an unexpected/error result;
- exact per-transfer `beforeUs`/`afterUs` timestamps show a completed clean R
  and a later faulted R in the retained transition shape;
- the owner's one action has a conservatively bounded time interval mapped to
  the same target monotonic domain (or by a separately validated clock-offset
  bracket), rather than only chat receipt or host wall-clock time;
- the entire action interval is after the clean R data completion and before
  the faulted R header begins. For an R-start transition, those are the
  preceding last-clean R-end and next transition R-start. For an R-end
  transition, they are that cycle's clean R-start and faulted R-end; and
- any physical visible-to-black claim has its own owner observation interval
  with stated reaction/relay uncertainty. Software tabs, compositor `On`, or
  screensaver windows cannot replace that annotation.

If the action interval overlaps either R transfer, is not mapped into the
native clock domain, or the first R is already faulted, the raw run can remain
useful technical evidence but is not an accepted action-to-fault timing
bracket. These requirements do not prove causation; they only make temporal
ordering defensible.

