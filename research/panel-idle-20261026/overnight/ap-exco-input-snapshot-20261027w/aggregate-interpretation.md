# W captured aggregate interpretation

Date: 2026-10-27 UTC. This is a finite offline interpretation of the already retained W snapshot. It performed no TV, network, USB, root, device-node, UI, write, reset, or configuration operation.

## Result

The captured ordinary AP_EXCO bytes reproduce the selected first helper's positive branch exactly:

```text
P0 = P1 = P2 = 7,464,960
P3 = 8,128,512
X0 = 8,254,590
X1 = 8,251,261
X2 = 8,250,967

P0 < X0, P1 < X1, P2 < X2       => A = true
+cc = 1, +ce = 0                 => C0 = A
+e2 = 30, +e0 = 30               => mature, F0 = 1
+ca = 1, F1 bypassed by +ce = 0  => predicted +e6 = 1
captured +e6 = 1, +2fc = 0       => derived predicate = 1
captured derived +3d8 = 1
```

Thus the late W state no longer leaves the two operands of derived `+0x3d8` ambiguous: ordinary `+0xe6` bit 0 is the true operand and ordinary `+0x2fc` is zero. The selected first-helper condition, counter, and output are internally consistent with one another. Because the RAM was acquired after the V6 onset and the native read is not a guaranteed atomic controller snapshot, this does not prove that the same tuple existed at the fault instant or that this helper physically turned the panel off.

## Captured threshold arithmetic

The helper assembles four unsigned 32-bit values from ordinary AP_EXCO low/high halfword pairs:

| Analysis label | Ordinary offsets | Captured value | Exact relation to 3840×2160 |
| --- | --- | ---: | ---: |
| `P0` | `+d0/+d2` | 7,464,960 | 90% |
| `P1` | `+d4/+d6` | 7,464,960 | 90% |
| `P2` | `+d8/+da` | 7,464,960 | 90% |
| `P3` | `+dc/+de` | 8,128,512 | 98% |

`3840 × 2160 = 8,294,400`; the percentage equalities above are exact integer equalities, not rounded display values. An earlier same-boot host-health record at uptime `124538.882938` contains `de 3840 2160`; the W read completed at uptime `125699.16`. This supports the narrow observation that these configured values are dimension-scaled for the reported DE size. It does **not** establish that the values' units are pixels, that each table element is a pixel count, or that the earlier host line is simultaneous with W.

The `P` and `X` names here are analysis labels. The firmware provides no direct field name or unit for these offsets.

## Exact table/summation shape

At selected image-0 VA `0x2f612`, the helper loads literal `0x584109a4`. It treats that location as three lanes separated by `0x40` bytes. Each lane is addressable as 16 32-bit words. The additions are ordinary 32-bit additions with no explicit overflow check; the captured mirrors are the resulting 32-bit values.

The upper inclusive index is selected from ordinary `+e8`: 15 when nonzero and 14 when zero. W has `+e8=0`, so the upper bound is 14.

The initial pass uses lower bounds `15-(+ea)`, `15-(+ec)`, and `15-(+ee)`. All three fields are 3 in W, so each lane sums indices 12 through 14 inclusive—three words per lane. The results mirrored at ordinary `+f8..+102` are:

| Lane | Source range | Captured 32-bit mirror |
| ---: | --- | ---: |
| 0 | base `+ 4×[12..14]` | 8,252,833 |
| 1 | base `+0x40 + 4×[12..14]` | 8,248,159 |
| 2 | base `+0x80 + 4×[12..14]` | 8,248,218 |

Ordinary `+116=1` enables the recomputation block. It derives three candidate indexes through floating-point multiply/divide/round operations involving ordinary `+ea`, ordinary `+f0`, and three halfwords in the distinct `NPC_AP` object, then clamps them against ordinary `+f2/+f4/+f6`. W captured both the final indexes `+104/+106/+108` and the caps as 6. The W capture does not include the `NPC_AP` divisor fields, so it cannot distinguish a pre-clamp result equal to 6 from one above 6.

With each final index equal to 6, the recomputed lower bounds are `15-6=9`. The helper sums indices 9 through 14 inclusive—six words per lane—and stores the 32-bit results into ordinary `+10a..+114`:

| Analysis label | Ordinary mirror | Captured value | Fraction of 3840×2160, for scale only |
| --- | --- | ---: | ---: |
| `X0` | `+10a/+10c` | 8,254,590 | 99.5200% |
| `X1` | `+10e/+110` | 8,251,261 | 99.4799% |
| `X2` | `+112/+114` | 8,250,967 | 99.4764% |

All three `P<X` comparisons are true by margins of 789,630, 786,301, and 786,007 respectively. Since `+ce=0`, `P3` is not consulted by this invocation's `F0` condition and the second `F1` path is bypassed.

The counter logic is also decisive for this sampled state. A true condition with `+e2 < +e0` increments the counter but does not set `F0` on that call. W instead has `+e2=+e0=30`, so the selected code takes the mature branch and returns `F0=1`. This exactly explains the sampled first-helper output; it does not establish how long the condition was continuously true before W.

## What “histogram-like” means here

The code shape—three parallel 16-word arrays, selection of a high-index inclusive tail, summation, dynamically recomputed tail starts, and comparison against values exactly scaled to the current 3840×2160 DE area—is compatible with a histogram-like or distribution-aggregate mechanism. The same host-health record separately contains DRM-DP histogram diagnostics, but no selected-controller instruction, pointer, record name, or timestamp binds those host histograms to table `0x584109a4`. That coincidence is not used as identification evidence.

A content-dependent aggregate is therefore a concrete, testable hypothesis, not a conclusion:

- Hypothesis: table `0x584109a4` is refreshed from picture-dependent distribution data; the selected tail sums rise or fall with displayed content, and a sustained `P<X` condition matures `+e2` and `+e6`.
- Supporting facts: the exact table shape and summation are proven; the live sums exceed dimension-scaled thresholds; the mature output is set; and the user's failures vary strongly with menus/titles.
- Missing proof: the table producer, update cadence, register or DMA source, units, relationship to displayed pixels, and a synchronized safe-versus-failing content series are all unresolved. The W capture contains the sum mirrors, not the 48 source words.
- Discriminating negative tests: with resolution, gates, and thresholds unchanged, a controlled content series whose `X0..X2` stay unchanged would weaken the proposed dependence for those tested patterns. A failure while all three `P<X` terms remain false and the first-helper output stays clear would rule out this first-helper path as the sole explanation of that incident; it would not exclude the separate `+2fc` operand, another trigger, or prove that this condition is insufficient when it is present.
- Stronger positive test: a read-only time-aligned series across a known safe title and a known failing title should show stable `P` values, content-correlated `X` movement, and the predicted `+e2` reset/ramp/mature sequence before `+e6` changes. Even that would establish correlation and code-path consistency before it established physical causality.

## Evidence boundary

`verify-aggregates.py` pins the selected package, corrected S analysis, retained W binaries/result, the same-boot host-health record, the complete first helper, its initial/recomputed summation slices, loop bounds, mirrors, threshold arithmetic, branch selection, debounce decision, and derived composite. Normal and optimized Python runs emit identical JSON with `target_operations:0`.

This pass does not identify the table's producer or physical unit, recover V6 event-time values, inspect protection or persistence paths, propose a write, or claim a repair. Its useful closure is narrower: the late sampled `+e6=1` is fully explained by the selected first helper's captured inputs and mature counter, while the content-dependent histogram interpretation remains an experimentally discriminable hypothesis.
