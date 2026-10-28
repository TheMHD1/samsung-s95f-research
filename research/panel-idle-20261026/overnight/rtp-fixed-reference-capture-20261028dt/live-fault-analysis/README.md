# Actual RTP fault: record values match the later bottom reference

Independent frozen-parser replay accepts both `DK/reference-onset-01` (DP48 headers/96 bulk calls) and the later `DK/reference-fault-01` (DT14/28). **All41 source-compatible prefix tuples uniquely reconstruct a12-bit A value that equals the later bottom-reference value at the same lane; none equals the top reference.** This strengthens the fixed-bottom data hypothesis. It does not prove the historical pointer branch or the epoch/type of every retained array entry.

This analysis is host-only. It changes no original capture, readiness, frozen parser, manifest or native helper, and performs no TV/root/network operation. The saved DT readiness explicitly places this read-only capture after the accepted DP fault and before any recovery, with no intervening coordinated UI/reset/vendor request. That is a retained coordinator lineage premise, not proof of global absence of other actors.

| Lane pair | Later top candidate | Later bottom candidate | Prior DM conditional A | Change from prior conditional A | New source-compatible records |
|---|---:|---:|---:|---:|---:|
| 570/571 | 2168 | 1857 | 1861 | −4 | 6+6 |
| 622/623 | 2160 | 454 | 550 | −96 | 0+0 |
| 624/625 | 2149 | 3053 | 3052 | +1 | 8+7 |
| 632/633 | 2157 | 1717 | 1718 | −1 | 7+7 |

“Prior DM” refers to `DK/record-fault-01`, separately parsed from its original receipt and12 raw windows. These are different runs, not simultaneous values. “Conditional A” assumes the selected source labels and a valid mode1 tuple; the source stores B and unsigned absolute difference, not A directly. In all41 new prefix entries B is0..486 and difference is at least1371, so B−difference is negative and **B+difference is the only possible A in0..4095**. For each entry that value equals the later bottom candidate and differs from the later top candidate. All41 have y2159/channel0 and x in570/571/624/625/632/633. They are compatible with a last image row for the captured height2160, without proving physical damage caused them.

The baseline DT capture returned104 zero bytes at both fixed candidate addresses. This later postfault capture returns nonzero top and bottom data, independently decoded as68 complete12-bit lanes568..635 from102 bytes, with2 tail bytes excluded. All decoded lane values and all41 comparisons are in `decoded.json`. This does not claim whole-buffer contents, physical units or a controller acquisition timestamp for each packed value.

The top pair bracket is **179350121068–179350121136 µs**; bottom is **179350121150–179350121219 µs**. The DT R/N brackets match at both ends and remain faulted: stop1/fault0x1001/gate0, alternate40, ordinal/latch41 and six current source counts zero. C7=1, aa0/ac2, publication mirror40 and xbase0. Current/saved metadata rows are69, while the retained tuple rows are2159. This reinforces the need to keep current M metadata separate from the historical record header. The whole DT paired-read span is **179350115505–179350121383 µs**. Matching brackets do not prove atomicity, no intervening reset or a single array epoch.

## What the source supports about the missing 622/623 pair

The selected source at comparator `0xbbbc..0xbd2e` computes unsigned absolute A−B and selects directional thresholds. Captured M has **both directional mode1 difference thresholds500**. The formatter at `0xc5e6..0xc5f4` accepts B outside the sampled band: B<500 or B>3183. Mode1 difference gating is **strictly greater than500**, so equality does not pass. Caller masks, per-lane flags, execution scheduling and later publication gates still apply.

For a hypothetical contemporaneous A454 and any **low-outside-band B0..499**, absolute difference is at most454, so none can pass strict difference>500. The script exhaustively checks that constrained domain. Previous source-compatible622/623 entries had B0 and conditional A550: difference550 passes. Holding B0 fixed and substituting454 gives difference454, which fails. This explains a concrete way the observed cluster could disappear.

It is not a proof of the disappearance's cause. **The current B values for absent lanes622/623 were not retained.** A high-outside-band value such as B3184 would still produce difference2730 with A454 and could pass. A skipped comparator call or another source gate could also remove a record. Do not replace these missing inputs with the old B0 merely because it makes the counterfactual fit. The later bottom reference is not proven to be the value used at those absent decisions.

## New score trace and timing

The DP five full clean checkpoint scores are **0,0,0,0,28**. C7 is0,0,1,1,1; publication mirror is200,200,200,40,40; alternate R+c4 remains40; all q0 values arezero. Last-clean N ordinal0 is32 and working source count0 is2. Last-clean H history0 is`[0,2,0,2]`. Postfault H score is **42**, history`[2,0,2,0]`, q0zero; postfault N ordinal0 is41 and all six current source counts arezero. These current counts reset per dispatch. The increase28→42 can contain multiple intervening updates; these two samples cannot identify an exact dispatch sequence or frame cadence.

The last clean R pair is **179323001087–179323001157 µs**. First fault R is **179323250300–179323254213 µs**. The conservative possible software-transition bracket is **179323001087–179323254213 µs**, width253126µs, strictly after Left-down returned according to the frozen parser. It spans OUT-header start through IN-data completion and is conditional on reply freshness; it is not an exact RAM or physical-light transition timestamp. The partial transition cycle contains only its initial R window, so no sixth full compact checkpoint is invented. Postfault H is **179323254846–179323254928 µs**.

The native counter difference from postfault H completion to DT first-header start is26860577µs. Treat the26.860577-second gap as conditional on the shared native monotonic timebase in the same saved boot, not as continuous observation. The later reference match cannot bridge that unobserved interval by itself. No compact clean checkpoint sampled score>40; nominal250ms polling cannot exclude an intervening crossing. Actual decision-time FP and key causation remain unobserved.

## Limits and the next missing execution-time fact

Publication admits ordinal<=40, producing indices0..40 and then ordinal41. Capacity checking and per-dispatch source counting are separate; publication saturation does not mean all later qualifying samples were retained. Types1/4/6 share column arrays and checked resets do not uniformly clear B/difference. Prefix41 is **source-compatible**, not a guaranteed valid epoch. Tail entries remain excluded from the conditional-A match claim.

The dispatcher at `0xb832..0xb88a` chooses fixed-top/fixed-bottom/dynamic A using the contemporaneous B header+6, cycling count and C7. This capture has no direct historical B ring header. Even a perfect numerical bottom match can also be compatible with another buffer containing identical data. It therefore does not promote `actualFixedABranchProven`, `fixedReferenceIdentityAtFaultProven` or `recordEpochProven` to true. The separate DS plan identifies in-process selected-pointer and formatter actual-A checkpoints that would close those blindspots, but executable-RAM hooking remains technically unqualified. The physical packed-data producer and electrical meaning of12-bit values are still unresolved.

## Verification and artifacts

`analyze.py` pins inputs before importing the exact frozen DP/DT/DM parsers. It verifies all exported raw files, original wrapper raw declarations, saved interpretations, original transport counts, captured/current manifest equality, every native/wrapper source and payload pin in all three frozen manifests, seven selected-package source ranges, the same saved boot/USB59 context and readiness digests. It independently decodes complete reference lanes, checks all41 unique conditional-A values, compares the older DM values and exhaustively tests the constrained622/623 counterfactual. Source evidence comes from the selected package and pinned disassemblies, not new target probing.

Run `PYTHONDONTWRITEBYTECODE=1 python3 analyze.py --check` and `PYTHONDONTWRITEBYTECODE=1 python3 -O analyze.py --check`. Both pass1041 explicit checks including exact artifact replay; frozen parser checks run additionally. `validation.json` records the results; `source-inventory.json` freezes the additive analysis. These are transport/source/data findings, not a root-cause fix, a physical-light measurement or evidence that changing a protection threshold is electrically safe.
