# Limit200 interpretation and packed-baseline hypothesis

This is a prospective host-only interpretation aid, not an account of a completed limit trial. The parent reports that DJ set-01 stopped during fake self-test framing, before production invocation: no threshold write occurred. The numerical examples below use frozen **CB and DH menu-onset-01** evidence. They do not relabel the later DH02 result, which the parent reports has score42. No TV/root/network call or OEM execution occurred here. Earlier DE/DJ/DH artifacts remain unchanged.

The selected source predicts a narrow effect: **the same aggregate score44 is clean at limit200 and faulted at limit40**. Raising the limit neither clears that score nor caps its inputs. A successful bounded trial would establish prevention of this software stop condition under its captured context. It would not by itself identify the packed producer, establish physical light output, repair bottom-edge damage or justify a permanent threshold.

## Exact aggregate model

Selected image1 VA0x1e68..0x203e (FILE0x42068,470 bytes, SHA256 `24edc9aadb2296ce9b773acb461075a0fc5e237e4a2506bdb87273c9432879df`) is modeled in the adjacent original Python file. The model is conditional on aggregate gate1, wait helper0, the chosen mode slot and an explicitly supplied T helper result. It does not implement or assume the physical meaning of those producers.

For mode1, C+7 nonzero selects root+0x24c4; zero selects root+0x2430. With the observed profile these are40 and200. Each qualifying dispatch:

1. Shifts q to `(2*q)&31`, then adds1 if the current source count s is strictly greater than BP160.
2. Shifts the four u16 history slots left and appends s.
3. Unless the new q is in `{8,9,10,12,24,25}`, adds the new oldest history slot to the u32 aggregate A, then subtracts T **once** if A>=T.
4. Publishes low16(A) as the score, and takes the common stop path only when that score is **strictly greater** than the chosen limit.

Equality40/200 remains clean. A is u32 and the comparison uses its low16, not the full accumulated word. High-count q patterns and T can change the result; there is no universal conversion from record count or elapsed time to score. A larger source count is not guaranteed to produce a larger aggregate at every dispatch.

CB's last sampled A=38/history[4,0,2,0] can reach A=44/history[4,0,4,0] through s=[4,0,4,0], q0,T0. The scores are38,40,40,44. The crossing dispatch has **current s=0** because it adds a delayed4 from history. The same arithmetic under limit200 yields the same scores and no stop. This is a compatible trace, not reconstruction of the unique unrecorded dispatches.

The source has no built-in “stop accumulating at40” rule. As an explicitly synthetic counterexample, from A/q/history zero, repeated s4, T0 and no reset crosses40 at score44 on invocation14; it crosses200 at204 on invocation54. A finite20-second clean observation cannot establish permanent prevention. Conversely, software frame-end resets can prevent contributions from accumulating across epochs; extrapolating four counts forever across resets is also invalid.

## Reset and publication coupling

Per-dispatch0xb7f8..b80a resets only the six working s counts. The broader reset0xca84 clears A, q, four-history state, record ordinals and s. The frame-end handler0xb8a8 calls it at0xb964; initialization0xcb2c also calls it. Therefore A0 is a per-software-epoch aggregate, rather than a lifetime damage/error counter. Mode score latches and root record-ID latches are not all cleared by this reset, and sequential reads may straddle it. A late s0/A0 sample does not exclude earlier qualifying input; an old score latch does not prove a current crossing.

The c4 field is coupled to the formatter publication bound via CPU0x4ca. Bound40 permits indices0..40 and stops at ordinal41; bound200 permits indices0..200 and stops at201. Both are inside the separate512-entry store guard. **s continues incrementing after publication stops.** At the same input sequence, aggregate gate1 and disabled alternative events, changing this publication bound does not change the modeled s/A recurrence. It changes diagnostic stores, ordinals, record latches and possible execution timing. The live experiment still cannot claim an isolated comparison-only intervention: source paths are concurrent, the same field has two roles, and timing/upstream changes are not experimentally excluded.

The independent formatter appendix maps five columns x/y/RGB/B/diff, not direct A/B pairs. Value/diff tail entries can survive partial clears, mode slots share the arrays, and absolute difference loses sign. Records help localize eligible inputs only with their source mode, ordinals and read brackets. Publication beyond41 alone does not prove A exceeded40, because q/T/history/reset rules are separate.

## What a future accepted result would mean

| Retained result, with otherwise matching source/profile | Supported interpretation | Remaining limit |
|---|---|---|
| c4=200; C+7=1; clean R; retained current-epoch A/score41..200 | The old40 comparison would reject that same arithmetic state; supports this narrow prevention mechanism | Does not prove equal live inputs, physical light, electrical safety or why the score arose |
| c4=200; clean R; all sampled scores<=40 | Compatible with prevention, but also with different/reset/unsampled input | Finite250ms sampling can miss brief score excursions and frame resets |
| C+7=0; clean R | Mode1 already selects normal200; this sample does not exercise the changed alternate comparison | Selector's other input-selection effects remain |
| c4 reverts40, layout/mode/gates differ, or transfer rejected | Intervention/context is not established for comparison | Preserve raw result and refusal; no success claim |
| c4=200; matching mode1; score>200 and stop/bucket event path | Threshold may delay rather than prevent this software event | Event code/common-setter alternatives and timing still need evidence |
| Software stays clean but an independent physical observation reports dark | This stop path is not a sufficient explanation of that physical failure | A screenshot/cached UI is not a light measurement |
| Software and physical image remain working only for the bounded exposure | Bounded prevention evidence | Does not establish a permanent fix or a matched-content causal A/B by itself |

After raising c4, normal and alternate mode1 limits both equal200, but **C+7 still changes source selection**. Keeping the selector intact preserves that distinction for investigation. Changing C+7 would alter threshold selection and fixed-reference behavior together, making a broader intervention. The older W AP_EXCO mask2 disables its AP+0x37a frame-mode predicate bit0; a refresh-rate-only fix has no positive bridge from that snapshot. Its histogram/e6→SLG→C+7 route remains distinct and positively sourced by DF.

## Narrow upstream explanation worth testing against records

The positive software route compares different stored inputs. Producer0x18ae8 copies two descriptor-selected payloads from the0x60000000 aperture into a three-slot ring. Dynamic A is the remaining older slot; B is the first newly copied slot. C+7 plus the cycling CPU0x4c4 and the **actual B header row** can instead choose a fixed A snapshot atCPU0x20015000 or0x20015f10 on the first/terminal-row branch. Snapshot refresh0x1c12c itself depends on the selected B header flag and advances/reset that counter. Thus descriptor age, snapshot age and row/channel alignment are real software comparison boundaries. Whether any of them are wrong is unproved.

There is a further exact arithmetic regularity: the producer's channel stride0x1950000 divided by row stride0xc00 is8640, exactly4×2160; its copied payload is0xb60 bytes,32 bytes beyond the ordinary2880-byte unpack span, which yields1920 12-bit lanes. These are code arithmetic and profile-extent facts. They do **not** establish four physical frames, image-pixel units, electrical feedback, ownership of the aperture, or its hardware writer.

A sparse-content baseline mismatch is a plausible unifying hypothesis only if it explains both menu and HDMI controls. The qualification counts numeric B extremes outside inclusive500..3183 with a large A/B difference; an identical pair of low values does not qualify merely because the picture is sparse/dark. A stale/different fixed A, descriptor mismatch, content-dependent physical response or another upstream change is needed. Since the packed units are not established, “low B” cannot automatically be called a dark pixel. Populated Apps or an HDMI Home overlay can change the histogram→SLG selection **and** compared signals/content; their stability is compatible with this route but does not isolate it. Working titles and working23.976 controls reject frame rate or darkness alone as sufficient explanations.

The bottom-edge damage and DH01's sampled row-like2159 metadata make the terminal-row/reference branch a concrete candidate. They do not prove it was taken: CPU0x4b4 is current metadata, CPU0x4d0 is diagnostic/dispatch metadata, and neither substitutes for the selected B ring header. No bus alias forCPU0x20253002 is inferred from the SRAM alias. Existing descriptor previous/current fields plus source-qualified record x/y/channel clusters are useful discriminators without inventing a direct ring read. If future tuples localize repeated qualified differences to terminal-row coordinates with stable descriptor context, that would support a localized input/reference issue; it still would not decide software baseline error versus damage-related physical behavior without closing the aperture's producer/units.

The accompanying model passes233 checks normally and under `python3 -O`: exact selected-source landmarks; CB-compatible delayed history; strict thresholds; q gating; T subtraction; u32/u16 narrowing; separate publication capacity/count behavior; producer address arithmetic; and invalid/bounded input refusals. No result is a claim of full binary equivalence. All source and evidence hashes are in the additive inventory.
