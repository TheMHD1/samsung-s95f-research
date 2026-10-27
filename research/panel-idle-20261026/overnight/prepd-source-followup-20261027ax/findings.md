# AX: source freshness, host logs, and firmware experiment readiness

Recorded 2026-10-27 UTC. This follow-up is offline. It sent no TV command,
changed no setting, built or deployed no target collector, and performed no
flash, code write or protection bypass. The owner explicitly permits firmware
experiments and flashing if needed, while asking that the TV not be bricked.
The remaining obstacle is evidence about the change and recovery, not another
permission request.

## New results

The [host histogram reconstruction](host-histogram-reset-comparison.md)
recovers both rolling kernel snapshots directly from AV's original compressed
artifact. It finds 58 unique complete six-label groups after accounting for
43 groups repeated between the snapshots. Every retained group reports the
same values. The closest pre group begins at uptime136361.560322, the stock
MODE2 action runs136363.892943..136366.222190, and the closest post group begins
136371.577002. No retained group covers the action itself.

The copied driver source attributes these labels to host display-processor
register reads, but no live module/call binding was recorded and more than
one source route emits INP labels. Equality of the observed rows at the
sampled times cannot establish constant content, fresh measurements, panel
light, or a connection to the controller's Pre-PD source. The later clean RT
and smaller ordinary-input sums in AV/AW are delayed samples. Joining them
to this bracket would not demonstrate simultaneous cross-subsystem state or
which change caused another. The practical result is that the existing host
histogram rows cannot substitute for observing the controller input producer.

The [Pre-PD header trace](prepd-control-consumers.md) closes another specific
static lead. It found no direct selected-image-0 constant into the prefix
before the companion table, and both known companion consumers read forward
only. The positive bounded selected-image write path remains a generic
package copy into the named Pre-PD range, conditional on loader execution.
No runtime refresh, sample-latch, counter or
readiness control was identified. This is bounded evidence; computed
pointers, hardware updates and other code remain possibilities.

Both checks have local reproducers. The header checker includes four mutation
or self checks. Normal and optimized Python runs produced identical results
in the [independent review](independent-review.md). Its two wording findings
are corrected here: driver interpretation is conditional on live binding,
and the package copy is a source path rather than an observed initialization.
These checks do not require contacting the TV.

## Consequence for the fault model

The strongest measured intervention remains AV's one stock controller
lifecycle followed by a delayed clean RT tuple. Physical recovery and
blackout prevention are still unverified. The numeric chain and fault latch
are reconstructed, but this follow-up identifies neither a proven bad
parameter nor a justified instruction to patch. It specifically prevents
two shortcuts: treating host histogram stability as proof of unchanged
controller input, and treating an unnamed Pre-PD prefix as a known control.

The existing [write-readiness assessment](../code-write-readiness-20261027r/code-write-readiness.md)
distinguishes matching readable code from writable or executing code. The
additional [backup and recovery assessment](flash-recovery-gap.md) records
what the retained backups actually cover and what restoration evidence is
still missing. A successful storage read alone does not demonstrate that a
failed modified image can be recovered.

The subsequent [AY restore audit](../restore-integrity-20261027ay/restore-integrity.md)
tests that fallback assumption against the actual copied host restore code.
It finds capped rather than exact source-size validation, acceptance of short
source reads with requested-length writes, sign-only host write-count checks,
no mandatory host readback/checksum, and discarded ioctl callee status.
These source defects do not prove that a bad write happened or describe
remote storage internals. They leave recovery unqualified and are not a
diagnosis of the panel fault.
AY's normal/optimized reproductions and six focused checks pass, with an
[independent source/control review](../restore-integrity-20261027ay/independent-review.md).

## Next discriminating test

Before another power or navigation action, obtain the owner's physical
picture state and take a fresh unchanged RT observation while that state is
confirmed. The pending physical-state question remains unanswered. AV's old
clean window must not be combined with a later black-screen answer as though
they were simultaneous.

If a lit Apps control is available, one owner-annotated failing transition
with the existing finite observer can test whether the recovered RT fault
actually appears with loss of light. Dispatch is not a clean-state
acknowledgement: the retained timestamps and first sample must qualify the
record retrospectively. Do not infer recovery from screenshots or software
display-on flags. Do not repeatedly reset the controller without a new
physical observation or a distinct question that the action can answer.

Earlier rejected collector work remains stopped. No equivalent collector
was implemented here. Firmware modification remains a possible later step,
with no present claim of a permanent repair or untethered permanent root.
