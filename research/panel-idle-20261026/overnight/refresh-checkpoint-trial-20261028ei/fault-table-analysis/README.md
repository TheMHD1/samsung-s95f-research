# EI fault tables and separate recovery validation

This host-only replay accepts the original `fault-tables-01` and `recovery-validation-01` EB captures on their existing transport contracts. Each has one native invocation, 16 completed read headers/32 bulks, `ReadyForHeader`, release/close and exact `STAGE_ABSENT` cleanup. The earlier EH `onset-01` remains rejected with `AlreadyFaulted`, eight headers/16 bulks and no Left attempt. Its observation and separate zero-vendor cleanup supply predecessor evidence; they do not become an accepted onset trial.

`decoded.json` contains the independently decoded 48 tuples, all 68 lanes in each fixed sample, source context, raw-file digests, every native step, comparison arrays and recovery summary. `input-provenance.json` pins the 251 named original inputs without copying them. They include private retained captures and the selected package, so the original inputs must remain private. This directory contains authored derived metadata and no copied OEM raw window, root envelope, authentication material or physical observation.

The fault snapshot has identical start/end R bytes: stop 1, fault `0x1001`, gate 0, alternate limit 40 and latch 41. R's operating mode is 4; the separate M AA/AC inputs are 0/2, producing the source interpretation category 1. C7 is **currently zero** in the Apps context, x-base is zero, packed width is 2880, lane count is 1920, and publication mirror is 40. These sampled values do not retrospectively identify the context that produced the retained records. All 68 primary u16 entries and 68 secondary bytes are zero; the source-derived override is false. Each sampled lane therefore has local table permission. The loop may have exited earlier, so this is neither proof of a comparator call nor proof that these table values applied historically.

N is byte-identical at the two boundaries: ordinal slot 0 is 41, the other five ordinals are zero, and all six source counts are zero. X/Y have 41 nonzero coordinate entries; all RGB entries are zero. The first 41 Y values are 2159. Their coherent coordinates are useful retained evidence, but ordinal 41 and zero source counts do not establish a valid current prefix, an epoch or 41 current calls. Modes share arrays, and the checked frame-end/init paths clear X/Y/RGB while retaining B/Diff.

Under the explicit premises that a coordinate-bearing entry is a same-epoch type-1 formatter tuple with 12-bit operands and the captured x-base interpretation, its possible A operands are `B ± Diff` within 0..4095. For all first 41 entries, subtraction is negative and addition is the unique possible value. All 41 such conditional values equal the later captured bottom sample at that lane and differ from the later top sample:

| Lanes | Tuple count | Retained B values | Conditional A | Later top | Later bottom |
| --- | ---: | --- | ---: | ---: | ---: |
| 570, 571 | 7 each | 407, 420, 431, 435, 447, 462 | 1827 | 2141 | 1827 |
| 624, 625 | 7 each | 0 | 3045 | 2152 | 3045 |
| 632, 633 | 7, 6 | 0 | 1712 | 2160 | 1712 |

This is positive compatibility with a retained bottom reference, not proof of the historical fixed-A branch, current comparator input, physical row identity or producer timing. No A is reconstructed for the seven cleared-coordinate tail entries. Their Diff values are 1311, 1311, 2161, 2161, 1329, 1329, 1681 and are byte-identical to the same tail in the earlier EE post-read. That persistence, while coordinates were cleared, directly reinforces the stale-field caution.

The comparison re-parses original EE and DK receipts and verifies their raw indices. Compared with EE's cleared-coordinate post-read, current X/Y change at exactly indices 0..40, Diff changes at exactly 0..40, B changes at 18 positions, and RGB remains zero. EE's bottom values at lanes 570/571, 624/625 and 632/633 were respectively 505, 322 and 898; current bottom values are 1827, 3045 and 1712. The older DK fixed-reference fault had corresponding bottoms 1857, 3053 and 1717. Its C7 was 1, as was the old DK record-only fault; current C7 is 0. Array contents and reference samples demonstrably vary between retained captures. None of these comparisons establishes why they changed or supplies a missing epoch tag.

D is decoded as 24 offset-tagged halfwords in the JSON. Source-conditional previous tail at D+0x04..0x0b and current tail at D+0x16..0x1d both equal `[0,67,0,0]`; D+0x18 is 67, saved D+0x1e is 66 and pending byte D+0x2b is zero. These are software descriptor mirrors. They are not the B ring header at the historical predicate and cannot settle its final A branch.

The accepted EB fault read spans native monotonic 184709346939..184709353533 microseconds, or 6.594 ms. Its first header is 404.280869 seconds after the last completed EH IN. EH already saw the fault in its first R, and never attempted Left. The fault onset is therefore **unknown before that initial EH observation**; neither this gap nor the EB read interval is an onset bracket. EH's earlier retained H value 42 has its own bracket in the JSON. EB does not capture H, so 42 must not be described as EB's current score. No physical darkness/light timestamp or observation was supplied.

The separate recovery result records one accepted stock MODE2 and no threshold write or retry. Pinned source inputs corroborate same-boot USB60 disconnect followed by USB61 enumeration and unchanged descriptors. The Samsung SDU log inserts vendor details inside its disconnect line; the source check uses that actual specific format. The initial literal-format host check and the pre-target readiness refusal for missing instance proof are preserved in `validation-preparation-note.md`. The subsequent accepted validation is not a rerun of an ambiguous native capture. Lifecycle log time is not mapped to the native capture clock here.

Recovery validation independently shows identical clean R boundaries `[stop=0,fault=0,gate=1]`, limit 40, latch 0, all N ordinals/counts zero, both gate tables zero, and both complete 104-byte fixed sample windows zero. X/Y/RGB/Diff are zero; B remains nonzero. This supports a sampled reference/state reinitialization and explicitly does not prove clearing all RAM, reloading original instructions, a cold boot of every domain, permanent repair or physical picture recovery.

The source lineage is the selected 5 MiB package SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Image1 addresses map to file offsets by adding `0x40200`. Rehashed source ranges cover formatter `0xc5d0`, comparator `0xbbbc`, unpacker `0xbd58`, dispatch `0xb7ec`, frame-end `0xb8a8`, ordinal reset `0xca84`, record clear `0xcb2c`, and descriptor refresh/copy `0x3934..0x3a64`. The source proof retains the corrected columns: X is lane plus u16 CPU4c0, Y is dispatch argument 0, RGB argument 1, B comes from pointer498+8, and Diff is absolute selected-A minus B (type6 uses zero). Gate qualification and all 30 frozen EB source/payload inventory entries are verified. This is source provenance, not whole-running-image attestation.

Both captures replay through the frozen EB wrapper with an injected mock root. Every generated command matches its recorded command bytes, and every saved output artifact matches byte-for-byte; 28 commands per capture, maximum 7712 bytes. All readiness references, three binding stages, canonical receipt envelopes, diagnostic separation, 32 total raw hashes, census snapshots and parent recovery proof inputs are checked. No real root adapter is imported. Temporary replay copies stay in a private directory beneath this analysis and are removed automatically.

Reproduce without target access:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 analyze.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -O analyze.py --check
```

Each run recomputes the exact decoded artifact. The tests reject 222 malformed cloned receipts, steps, hashes, source guards, envelopes, readiness and transport cases. Truthfully rehashed nonzero gate samples are decoded as different local permission rather than forcibly rejected as impossible. Successful replay validates the retained transport and decoding contracts; endpoint queues, atomic firmware state, continuous absence of other clients, historical table execution and the root cause remain unproved.
