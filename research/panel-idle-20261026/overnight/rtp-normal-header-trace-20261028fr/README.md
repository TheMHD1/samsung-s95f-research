# FR: NORMAL header provenance and publication versus aggregate state

**The41 formatted detail rows are not an aggregate score of41, and FO's aggregate was not zero throughout.** The independently sealed FO analysis decodes all56 rows: the sampled mode1 aggregate rises during cycles24..55, peaks at36, and is zero in the retained first/last endpoints. With sampled alternate limit40, these observations are compatible with a clean comparison path. They do not establish the actual FP register, every intervening comparison, a shared record epoch or physical correctness.

FR is host-only source analysis. It changed no other workstream and made no TV, root, network, USB, kernel, firmware or public modification. There is no patch, deployment, new reader or limit write here. The selected asset stays at its retained private location; no OEM binary or full disassembly is copied into FR.

## The159 header is already positively resolved

SWU's sealed FO `live-analysis/decoded.json`, SHA256 `2ae4c84ab06ff2db7492329e39d88c6730141038d73f1f70ffb338c22f2f1c4c`, owns the independent header/transport analysis. FR pins that report, its checker, README, inputs and inventory, and revalidates its selected-source span hashes. It does not repeat the full FO replay.

The exact header format is image1 literal VA0xbb48, `[RTP:%s][%d]\n`. In function0xb9f4, the call at0xbab6 passes mode text from0x1b72c and a u16 loaded into R2 from CPU0x200004a0 at0xbab0, using literal0xbaf4. Only afterward do0xbabe/0xbac2 increment that counter;0xbacc..0xbad4 wrap values above9999 to1. Thus **159 is the pre-increment stock invocation counter**, not temperature, a threshold or an aggregate count. The actual M endpoints159→160 are compatible with this output, without proving unique epoch alignment. `NORMAL` is the source's software mode string; it does not assert physical panel health.

All source VAs below are selected image1 linked coordinates, FILE=VA+0x40200, in asset SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. They are not executing-PC or live-register observations.

## The detail records precede a separate aggregate calculation

The exact detail literal at VA0xc858 is `[RTP %3d]RGB:%d x:%4d y:%4d/c:%4d/diff:%d/m:%s\n`. At formatter0xc5d0, the call at0xc638 passes:

| Formatted field | Positive source argument |
| --- | --- |
| ordinal | u32 publication slot `CPU0x2000ba28 + 4*(mode−1)`, loaded0xc62e |
| RGB | saved channel-like incoming R3, moved into sink R2 at0xc634 |
| x | saved lane index incoming R1, moved into sink R3 at0xc632 |
| y | saved row-like incoming R2, placed at stack+0 at0xc624 |
| c | B sample incoming R0, placed at stack+4 by0xc620 |
| diff | incoming unsigned difference, placed at stack+8 by0xc620 |
| m | mode string from0x1b72c, placed at stack+12 by0xc628 |

The printed x is the lane index. The separate record-array X store at0xc666 adds CPU0x200004c0 xBase; these are equal only when the applicable xBase is zero. B and difference do not directly retain A or prove which fixed/dynamic A branch ran. C7=1 alone still does not supply the selected B-header/selector/counter branch at that invocation.

Publication, printing and qualifying counts have distinct limits and lifetimes:

- **Publication:**0xc5f6..0xc604 compares the current u32 ordinal to u16 bound CPU0x200004ca and bypasses publication only when ordinal>bound. With a stable bound40 and an ordinal starting0, IDs0..40 are permitted, then0xc6b8 leaves the ordinal at41. The512-slot array capacity guard is separate.
- **Qualifying count:** the bypass0xc604→0xc6de→0xc708 still reaches the u16 count increment/store at0xc710/0xc718, slot `CPU0x2000ba40 + 2*(mode−1)`. Publication saturation at41 does not cap later qualifying-count production. The checker gives a finite illustration of100 qualifying formatter entries yielding publication IDs0..40, final ordinal41, but count100.
- **Print throttle:**0xc606..0xc616 emits at most four detail calls while byte CPU0x200004be is below4. This is a refresher budget, not the publication bound and not an aggregate threshold. Runtime callback0x3934 explicitly places zero at outgoing stack byte+14 at0x3a04/0x3a06, calls0xbb58 at0x3a0e, and that helper copies the byte to CPU0x200004be at0xbb98. Thus additional refresher calls can admit more detail lines while a publication ordinal continues across dispatches. The41 rows do not identify the number/timing of actual refresher executions or exclude other computed writers.

The print call occurs before the current count increment, and both precede the unpacker's later aggregate call. The recovered normal difference path calls this formatter only after its numeric difference condition and B rejection-band checks. A formatted record therefore identifies a qualifying source formatter entry, conditional on source identity and provenance; it is not itself the aggregate predicate or a setter event.

## Per-dispatch count, delayed aggregate and predicate gates

Dispatcher0xb7ec resets **all six current source counts** at0xb7fc..0xb80a before fetching A/B and invoking the selected unpacker. It does not clear publication ordinals or the aggregate arrays in that reset loop. Counts seen in a later N read can therefore be zero while ordinal41 and earlier log text remain.

After the unpacker's lane processing,0xbfbc/0xbfd0/0xbfdc call aggregate predicate0x1e68 with mode4/6/1 respectively. With the sampled AA0/AC2 profile, the selected ordinary source branch is mode1. This is a selected-source conditional, not proof of the actual executed branch for every row.

Predicate admission has two independent gates:

1. Root+0x249e must equal1 at0x1ef6..0x1efe. Otherwise it returns before q/history/aggregate updates and comparison.
2. Helper0x35a4 examines root+0x240e. The loop at0x1f00..0x1f06 waits while the helper returns nonzero, which occurs when the ordinary gate is zero. The source provides no bounded waiting-time guarantee here. Logger root+0x2406 is a different gate controlling text output.

For an admitted mode slot, exact source operations are:

1. Shift q left and retain its low five bits,0x1f08..0x1f2c.
2. Shift four u16 history entries toward index0 and place the **current per-dispatch count** in history[3],0x1f30..0x1f6e.
3. If current count exceeds root+0x24a0, add1 to q and update its separate mirror,0x1f70..0x1fa0. This count bound is distinct from FP and the publication bound.
4. Helper0x1e46 returns zero for q values8,9,10,12,24,25. Those states skip the aggregate add and T subtraction, although q/history were already shifted.
5. Otherwise add the **post-shift oldest history[0]** to the mode's u32 aggregate,0x1fc0..0x1fd4. It is not a sum of all printed rows and does not add the newly inserted history[3] immediately.
6. Select helper0xca10 or0xc8a0 using root+0x24d2. Both return a u16 T, derived from separate per-lane history/counters. If aggregate>=T,0x2002/0x200a subtract T. If aggregate<T, the subtraction is skipped; it is not a clamp-to-zero rule. A positive T can reduce an aggregate or return it to zero without a whole-epoch reset. The checker models this condition without assigning FO's actual T or invocation sequence.
7. Load the aggregate's low16 bits into R7 at0x2012/0x2016. For mode1, C7 nonzero selects root+0x24c4 as FP; C7 zero selects root+0x2430. The comparison0x202a/0x202c takes the no-setter edge when R7<=FP. Only R7>FP reaches0x203a with event736. The sampled H word is a RAM aggregate, not the exact decision's FP register.

H mode1 aggregate is CPU0x2000d0e4, **H-window offset+4**, not the first word at+0. Q is H+28 and the first mode's four-count history starts H+40. FR binds these fields in all56 compact rows directly back to the actual native receipt, while leaving complete orchestration replay to SWU.

## Positive epoch-reset edges and their limits

Whole reset0xca84 explicitly clears all six publication ordinals, current counts, u32 aggregates, q values and four-entry histories at0xca8c/0xca92/0xca98/0xca9e/0xcaae. Its two positive aligned direct callers are frame-end0xb964 and initialization0xcb50. Initialization0xcb2c is called by orchestration at0xb6a0 and by software reinitialization0xc228. These are source epoch boundaries, not evidence that FO took them at a particular time or proof of a hardware reset.

The frame-end handler0xb8a8 conditionally clears the X/Y/RGB arrays, then calls the whole reset. Initialization also clears those arrays and xBase. B/Diff storage can survive those source reset paths, as DM already qualified. A separate nonaggregate wait branch can decrement a publication ordinal at0xc780. Thus ordinal equality, ordinal41, cursor advancement or retained coordinate tuples do not establish a common epoch or lack of reset/republication.

The checker performs a finite halfword-aligned direct-BL candidate census over the selected128KiB image1 slice for these four targets and validates the positive sites. It is not an alias-complete writer/caller census and does not exclude indirect calls, computed stores, cross-core/DMA activity or a different running image.

## What FO supports and the smallest useful discriminator

The corrected observation is55 Clean rows plus one final Quiescent row, sampled H aggregate max36, endpoints0, final publication ordinal41, and a retained2257-byte cursor-selected candidate containing the159 header and41 detail rows. SWU's decoder owns the complete raw/ring/transport interpretation. An increasing endpoint cursor does not prove no wrap, freshness, unique epoch, complete output or event absence. No physical picture state follows from these records.

A next matched content transition can discriminate **content/timing reproducibility** while retaining FN's limit40, key join budget and observation caps: preregister the actual start surface (for example current Live→ForYou), use a separately reviewed wake/readiness derivative for that surface, and compare all56 timed H/q/history/ordinal rows and the successful key-down overlap. Changing the accepted start tab is a wrapper/readiness change; the frozen Apps wake predicate cannot simply be relabeled. Capture enough post-down optional rows to observe the delayed history, and report a trial without a crossing as such. Publication41 or header159 is not a reason to change a limit.

That read-only capture still cannot distinguish the **actual FP register** from an inter-sample C7/threshold change. The minimal direct observation of actual operands remains DS's site0x2024, retaining R7 and FP immediately before the original0x202a comparison (plus mode/row/channel), with the original comparison preserved. Installing such a hook is not qualified by existing data reads and still requires the independently owned execution, instruction visibility and rollback prerequisites identified by DS. FR does not propose bypassing them. Without that facility, keep `actualFpProven=false`; use R/C brackets only as conditional source-context evidence. FO's sampled max36<40 does not test a prevented >40 crossing or establish a benefit from changing thresholds.

## Reproduction and frozen artifacts

Run `python3 -B audit.py` and `python3 -O -B audit.py` from FR. They read only retained files, use cached Capstone with bytecode disabled, and emit derived JSON. All682 checks use explicit exceptions and remain active under optimization. They verify selected identity, pinned dependencies, decisive instructions/literals/ranges, SWU's sealed header spans, the56 source-relevant row fields, q/history/subtraction/publication boundary models and the finite direct-call candidates. The outputs are byte-identical.

`input-pins.json` lists retained source/review/raw fixture hashes and cached disassembler files. `source-audit.json` and its optimized counterpart retain exact image/VA/file offsets and range SHA256 values plus the derived source facts, without OEM bodies. `validation.json` records parity. `source-inventory.json` freezes this directory only. No source gap is converted into target permission or a claim of actual execution.
