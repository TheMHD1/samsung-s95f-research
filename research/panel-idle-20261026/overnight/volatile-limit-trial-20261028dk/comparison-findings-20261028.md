# First completed volatile-limit comparison and debugging checkpoint

Recorded 2026-10-28 UTC. This report supersedes earlier pending-write statements
for this experiment. Historical refusals and earlier reports remain unchanged.

## Result

The finite intervention completed: the source-qualified alternate limit was
changed **40→200**, observed, and separately restored **200→40** with exact
readbacks. Both subsequent 20-second, 80-cycle observations were clean. The
200 run's largest sampled score was26; the restored40 run's was24. Neither
crossed40. **Prevention is inconclusive.** This is not a demonstrated fix, and
the comparison does not justify leaving the larger limit enabled.

All operations used the same controller USB instance, without an intervening
stock reset. After a final normal return to Apps, DM verified actual limit40
and clean stop/fault/gate0/0/1. The final transaction completed, its claim was
released, its descriptor closed, and its exact temporary stage was removed.
No executable instruction, boot image, kernel, persistent hook or update
storage was modified. There is no unattended optical confirmation.

## Actual sequence

| Local immutable capture | Operation and retained result |
|---|---|
| `dv-set-01` | DV accepted40→200;7 headers/14 bulks; baseline, fresh and readback guards passed. |
| `dv-observation-01` | DP200:80 clean cycles,640 headers/1280 bulks; maximum sampled score26; no sampled score above40. |
| `dv-restore-01` | Separate DV accepted200→40;7 headers/14 bulks; exact restored-field readback. |
| `dv-rechallenge-01` | DP40:80 clean cycles,640 headers/1280 bulks; maximum sampled score24. |
| `dv-clean-reference-01` | DT:14 headers/28 bulks; stable clean R and actual40; new top/bottom reference windows. |
| `dv-final-clean-01` | DM after normal Apps navigation:12 headers/24 bulks; stable clean R and actual40. |

The two writers' baseline/fresh/readback inputs matched the restrictive
source-derived admission model at input24, ordinary/alternate upper3161 and
echo0. Later read-only windows show input25, ordinary3183 and alternate3161:
the firmware refreshes the selected endpoint while sharing other diagnostics.
That between-observation change is a real covariate, not a failed earlier
writer guard and not a reason to relax the model for another write.

Twenty seconds is the DP observation budget, not the full wall-clock exposure
to200. Separate preparation, staging and restoration add time. The independent
replay derives a130.388670-second outer numerical envelope from set-payload
start to restored40 readback completion, under its common-clock, reply-freshness
and no-intervening-writer premises. It is not an exact RAM-commit interval or
unconditional proof of continuously200. No causal conclusion should be based
on an inaccurately reported twenty-second total intervention.

## What the custom loggers have narrowed

Earlier unchanged40 DP runs did capture faults: sampled score38→42 in one,
and28→42 in the reference run. Both entered stop1/fault0x1001/gate0. A fixed
reference capture following the second fault reconstructs all41 retained
source-compatible A candidates exactly from the later **bottom** reference
window, with no exact matches to the later top window. This identifies a
specific input-data path to investigate; it does not prove the pointer or
reference epoch actually used at each earlier comparison.

The later clean40 DT window has different bottom references:460,1363,377,980
at the four relevant column pairs, compared with1857,454,3053,1717 in the
fault capture. Reset/initialization, reference contents and age, live content,
history and selective input refresh are therefore important discriminators.
The comparison is sequential and not frame-atomic. DT's count4→0 with an
unchanged ordinal41 also shows why a changing working count cannot be treated
as a persistent complete-event log.

All41 later clean DT prefix tuples also uniquely reconstruct conditional
A=B+Diff matching the later bottom candidate and not the top. Their columns
are622/623,632/633 and572/573, unlike the previous fault prefix. For the absent
570/571 and624/625 columns, bottom values460 and377 cannot satisfy strict
diff>500 if their hypothetical B values were0..499. Their actual B, masks and
scheduling were not captured. This is a testable input-path consistency result,
not proof that reference changes caused the clean outcome.

The source bridges the retained candidate publication, aggregate score test
and common stop setter. The physical producer of the packed inputs and the
final electrical loss-of-light edge remain unresolved. The user-observed
fullscreen HDMI failures, successful overlay controls and damaged panel
remain constraints on any explanation; this software comparison does not
erase or explain them by itself.

## Execution-level debugging next

Our new readers are real custom target-side acquisition code, but they are
not instruction breakpoints. DS now specifies exact sites for an execution
logger: actual aggregate score/threshold at linked VA2024; actual selected
A/B pointers atbd58; actual qualifying A/B/lane/context atc5d0; and common
fault-setter event/caller atc1e0. Each addresses a known blind spot of later
RAM snapshots. No detour or execution logger has been installed.

DW independently source-qualifies the image1 code/resource bus alias and four
fixed16-byte fingerprints at those sites. DX is being implemented offline as
the smallest read-only live-identity probe. It must be independently reviewed
before a target request. A matching64-byte result would qualify those sampled
bytes only. Scratch ownership, instruction-fetch mapping, atomic installation,
cache/barrier behavior, ABI/interrupt/stack overhead and rollback independent
of a failed USB session still need evidence before executable patching.

The immediate objective is to close those specific gaps while retaining the
working boot/network route. No repeated limit exposure, automatic fault reset,
permanent protection bypass or speculative firmware flash follows from this
inconclusive result.

## Evidence and reproduction

The six local capture directories above retain original receipts, windows,
readiness decisions and hashes. The independent analysis is
`../volatile-limit-dynamic-profile-20261028dv/live-comparison-analysis/`.
The earlier source/capture bridges remain in
`reference-findings-20261028.md`, DM/DP/DT analyses, DU's dynamic-profile model,
DS's checkpoint-hook design, and DW's code-alias qualification. Sanitized
scientific fixtures and original research source are staged separately for
the public repository; raw authentication metadata and OEM binaries are not
public artifacts. No source-compatible reconstruction is presented as an
execution trace or a hardware-light measurement.
