# Volatile limit experiment: a discriminating software witness

Checkpoint: 2026-10-28 06:38 UTC. This is a completed finite experiment,
followed by restoration and recovery. It establishes a useful workaround
lead; permanent prevention, physical light and the original hardware cause
remain unproved. The [parent checkpoint](parent-final-checkpoint.json)
binds the completed actual outputs.

## Raised-limit observation

The earlier DV200/40 experiment never sampled clean H above40. The new
FA writer and fixed200 EY recorder were built and independently reviewed
before use. FA accepted one fixed two-byte40→200 write and full guarded
readback. EY then completed56 checkpoints: **55 Clean and one Quiescent**
(cycle19), with no sampled latched fault. The terminal reason was CycleLimit.

There are **23 complete Clean/Clean cycles with Hlow16>40, C7=1 and
end-R selector mirror1**. The maximum sampled H is76 at cycle35. The final
retained cycle56 is Clean/Clean, H52, AA0/AC2, scan1, C7=1, root20010000,
and both R limits200 with selector mirrors1. These are sequential fields
from one retained cycle, not an atomic execution snapshot. Actual FP at
the comparison instruction is not measured.

A separate EB post-read remained clean at200 with latch201 and publication
mirror200. It began6.779946s after EY's final IN. The numeric span from set
readback to EB final read is17.961762s; matching endpoint reads do not
prove continuous clean residence over that gap. EY's native observation
duration is1.453952s and median H-start spacing25,845us. The requested25ms
schedule is not a guaranteed rate.

[Raised analysis](raised-analysis/README.md) independently replays every
saved FA/EY/EB command and generated artifact and verifies all raw windows.
Normal and optimized runs each pass2811 checks over309 pinned inputs and
reject23 malformed cases. The56-row decode and contextual witness remain
separate from optical output, UI destination and decision-time operands.

## Source-backed endpoint admission

The old DV guard correctly refused the fresh Apps baseline: ordinary3161
and shared temperature24 matched, but alternate3138 did not match that
same temperature. Selected image0 source389d0 writes only the selected
ordinary or alternate endpoint before updating shared diagnostics.
Alternate3138 has a unique compatible modeled input23; this does not
prove its historical age or actual writer execution.

FA retains the ordinary-current prediction and admits the alternate only
from the exact72-value image of the pinned32-bit ARM arithmetic over
current inputs0..4095. It rejects729 other integers inside3000..3800.
The source's >4000→25 fallback applies to the reference input, not current
temperature; reference24 remains pinned. All other static profile,
context, callbacks, tuple stability, binding, transport and fixed2-byte
action constraints remain unchanged. No endpoint value is written.

## Restoration and two distinct40 controls

The separate FA200→40 restoration passed7headers/14bulks, all six raw
windows and full clean40 readback. The first original ER40 control then
recorded56 Clean cycles, H0 and C7=0; its EB post-read was clean40 with
latch201. This did not expose the alternate branch and is inconclusive.
A later cached Apps+saver snapshot does not prove an earlier wake failure
or identify where the original Left was consumed.

The next control used an explicit, observed Up,Up,Left,Left normal-key
path: cached Apps→Live→ForYou. A separate accepted EB then bracketed a
stable fault1/0x1001/0 at40, AA0/AC2, C7=1, publication mirror40 and latch41.
N ordinal0 was41 with all current source counts0. There is no dense onset
bracket for this explicit control and no physical-light observation.

[Restoration/control analysis](restoration-control-analysis/README.md)
replays the restore, ER, EB and NAV artifacts exactly. Its3261 checks and
326 input pins reproduce in both Python modes, with12 malformed refusals.
Conditional type1/same-epoch/12-bit reconstruction matches all41 source-
compatible prefix A values to the later bottom reference, including high-B
4095 and low-B groups. Current counts0 do not establish a valid historical
prefix, selected A branch, comparator execution or physical pixel mapping.

The200 witness and later40 fault strengthen the case for a finite software
workaround. They are not a perfectly matched causal experiment: navigation,
input history, reference state and timing differ. Fieldc4 also changes both
the score threshold and publication capacity. The result cannot isolate
those two effects or repair the known physical damage.

## Completed recovery and final state

After returning to cached Apps with ordinary keys and passing the existing
public reject gates, the unchanged EI40 guard issued exactly one stock
MODE2, with zero threshold writes. Positive USB63 disconnect followed by
new enumeration64, unchanged descriptors and the same Linux boot were
verified. No USB re-enumeration was observed in the captures before that
intentional recovery; this does not exclude an internal core-only reset.

Fresh EB64 validation passed16headers/32bulks, all16 raw-file checks,
ReadyForHeader, release/close and exact stage removal. Both R snapshots
are clean0/0/1 at40 with latch0; N ordinals and source counts are all0.
X/Y/RGB/Diff columns are zero, while20 B entries are nonzero. This records
the validation sample, not universal RAM clearing. FA had already restored
40 before MODE2, so this case does not prove MODE2 resets200→40.

Apps is the final cached selection. Physical picture remains unobserved.
There is no outstanding helper/trace stage from the completed workflows,
no persistent logger, instruction patch, kernel/boot/flash change or
permanent raised-limit policy. Total field actions in this experiment are
one set and one separate restore; total recovery requests are one.

## Next discriminating work

FB defines an additive wrapper wake/check stage immediately before native
submission, after staging and selftests. It would log one ordinary wake,
bounded Apps/no-saver/CSFS checks and the submission gap while retaining
the same native recorder. It is design-only at this checkpoint. It narrows
an entry-state blind spot without claiming continuous no-saver state or
key consumption. The existing command has only326bytes spare, so inline
UI probes must not silently displace identity/phase guards.

Next trials need that better entry-state record, repeated40/200 exposure
under closer-matched context, and the HDMI title cases. Physical benefit
still needs optical evidence. Execution-time logging at selected-A,
score/FP and common-setter sites remains a separate source-directed plan
requiring owned executable storage, cache handling and independent removal.
The overall diagnosis/prevention goal remains active.
