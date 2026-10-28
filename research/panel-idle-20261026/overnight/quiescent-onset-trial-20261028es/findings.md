# Custom instrumentation: accepted onset and separate recovery

Checkpoint: 2026-10-28 05:51 UTC. The original observation is frozen in
[live-analysis/README.md](live-analysis/README.md). Recovery is a later,
separate operation; it does not change the original trial's zero-recovery
ledger. [parent-final-checkpoint.json](parent-final-checkpoint.json) binds
the capture summary and completed recovery validation.

## What was installed and exercised

The ER custom native reader was deployed temporarily and actually ran.
It makes eight fixed read pairs per complete cycle, retaining bounded
58-byte checkpoints and selected full raw windows. Two additional fields
come from the already-read end-R window: selector mirror24ca and trainer
arm2468. It requests25ms start spacing, caps56 cycles and has a cooperative
2s observation budget. It sends one Left down/up only after an initial full
Clean cycle. It performs no controller-memory writes or executable hooks.
The sampled cadence was not guaranteed25ms: H-start intervals range
17,701–95,238us, median25,804us.

The prior EM observer stopped on a complete0/0/0 tuple at limit40. Source
audit identifies a stock gate-off writer that can produce this tuple
without setting the fault. ER calls this exact state Quiescent, separately
from Clean and Faulted, and continues observing it. USB transfer/identity
and pending-IN rules were preserved. The rejected EO record and its
separately qualified cleanup remain unchanged.

Private Linux tracing also ran: selected GPIO, IRQ and suspend events,
with a private trace instance, bounded buffers and watchdog. It collected
14 IRQ30 entry/exit pairs, no recorded loss, and removed its instance.
No selected GPIO/IRQ84/suspend event was retained. This limited scope does
not exclude controller-local activity. Kernel/native clocks were not
mapped, so their timestamps are not subtracted or treated as causal proof.

## What the new logger saw

ER accepted28 complete cycles, including two Quiescent cycles, then the
first Faulted R in cycle29. C7 and its end-R selector mirror changed0→1;
the sampled reference counter advanced1→2→0. The publication mirror
changed200→40, followed by H values8,8,14,20,26,34,34,40. The separately
retained post-fault H was48. R changed to stop1/fault0x1001/gate0.

The last Clean-to-first Faulted whole-request bracket is25,967us in the
native clock. This is a software observation bracket, not the physical
panel blanking edge. The H value and publication mirror are not measured
arguments at the historical comparator call. The sampled reference-counter
sequence fits the recovered seed/two-boundary-event mechanism; it does not
prove distinct top/bottom copies, exact reference age or the actual caller.

A separate EB post-read confirmed the latched fault at unchanged limit40.
All sampled primary/secondary lane gates were zero. Current N source
counts were zero; retained coordinate records are not thereby proved to
be a current valid prefix or a particular reference epoch.

The key workflow intended Apps→Live. A later cached UI snapshot was For
You plus saver. Dispatch success does not identify the destination during
the capture, and no physical-light feedback was available. This case
therefore establishes neither an actual Apps→Live transition nor optical
recovery. These limitations do not discard the accepted controller data.

## Completed return to clean controller state

The first DK recovery preparation refused cached For You before sending
any key or reset. A subsequent ordinary wake/navigation workflow selected
Apps. The separately guarded recovery then issued exactly one stock MODE2,
with zero threshold writes and no retry. Its final cached selection was
Apps. Same-boot USB62 disconnect followed by new enumeration63, with
unchanged descriptors, was positively checked.

A fresh EB validation on instance63 passed the original strict parser,
all16 saved raw-file byte/hash checks,16 headers/32 bulks, ReadyForHeader,
release/close and exact stage removal. Both R snapshots are0/0/1 at40,
with latch0. N source counts are zero but ordinal5 is36, and X/Y/RGB/B
are populated at validation: universal clearing by MODE2 is unproved,
because stock activity could repopulate them before the read.
No physical picture observation is claimed.

## Remaining instrumentation targets

The source-directed execution-hook plan focuses on image1 offsets2024
(actual score/selected FP), bd58 (selected A/B and caller LR), c5d0
(selected A path/caller) and c1e0 (common fault setter/event736/caller).
These are planned hooks, not installed debuggers. Five fixed live
code/literal windows totaling324bytes matched the selected source image
before this observation; that does not establish whole-image identity,
instruction-fetch behavior or safe writable executable storage.

The frozen ET stock-logging design covers a combined single-owner
gate-arm/ER/restore/ring capture. Historical stock logs already include
event736 and0x1001, so repeating that event alone would add little. Useful
new instrumentation must expose missing decision-time operands or caller
context. The combined helper still needs deadline/storage qualification;
it is not implemented. Instruction hooks still require proven scratch
ownership, cache handling and an independent rollback path.

No kernel, boot, flash, persistent logger, threshold or lane-mask change
was installed in this batch. The goal remains active: this is a much more
complete fault-path observation and validated logical recovery, not a
permanent prevention fix or proof that firmware rather than physical
damage is the underlying cause.
