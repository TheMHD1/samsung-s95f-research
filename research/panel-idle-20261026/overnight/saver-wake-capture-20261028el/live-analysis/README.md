# EL saver-context one-key observation

The retained EL experiment is an accepted **clean observation from a cached Apps-plus-saver context**, not a demonstrated Apps→Live exposure. Baseline EB, the 60-checkpoint EH run and post EB all meet their frozen transport/parser contracts and exact cleanup. EH attempted one Left down/up after its first complete clean cycle. Both key children exited zero and were reaped, but there is no UI-consumption receipt or physical observation.

This analysis used host files only. It verified 227 named original inputs, all 37 frozen EH and 30 frozen EB source/payload inventory entries, regenerated deployment manifests, every readiness evidence reference, the admission and six serialized coordinator slots. Injected mock roots reproduce all **95 generated wrapper commands** and every saved artifact byte-for-byte. Temporary replay outputs are private and removed. No real root transport was imported, and no target or network call was made.

| Capture | Accepted contract | Sampled state | Cleanup |
| --- | --- | --- | --- |
| baseline-01 | EB 16 headers / 32 bulks | clean 0/0/1, limit 40, latch/N 0 | STAGE_ABSENT |
| onset-01 | EH 480 headers / 960 bulks, 60 checkpoints, TimeLimit | all completed R brackets clean; no observed software transition | STAGE_ABSENT |
| post-tables-01 | EB 16 headers / 32 bulks | clean 0/0/1, limit 40, latch/N 0 | STAGE_ABSENT |

All are single native invocations with released/closed ownership and `ReadyForHeader`. Across the three captures this is 512 headers/1024 bulks, with no controller memory write, reset, automatic restore or retry. Forty-nine retained raw files, including the 3240-byte checkpoint record, match their native receipts and saved inventories. EH's compact success records `bindingQualified`; EB also retains the three detailed native filesystem/GETDRIVER binding stages. These are scoped ownership/transport checks, not endpoint-queue or atomic-state proofs.

Every independent 54-byte checkpoint decode agrees with the frozen parser. Across all 60 samples:

- Start/end alternate limits are 40. The earlier sequential M publication-bound mirror is 200; the mirror is not evidence that the alternate limit became 200.
- C7, selector mirror CPU4c2 and reference counter CPU4c4 are zero.
- A0, Q0, all four history words and N ordinal 0 are zero.
- Trainer control CPU4a2, aggregate CPU4a4, end-R root2460 and root246e taps are zero.
- Dynamic A/B pointer words rotate among `0x20253002`, `0x20253b6a` and `0x202546d2`, spaced by `0xb68`. Both pointer taps change at cycles 2, 5, 15, 26, 35, 45 and 55. These words do not establish an actual header, active buffer, epoch or selected comparator branch.

The 60 checkpoints count cycles 1 through 60 exactly once; the retained trigger baseline duplicates cycle 1's data without adding a checkpoint. All eight appended taps come from the existing M/P/end-R reads. Their sequential positions differ from C/H/N, and no common sampling instant exists. At a nominal 250 ms cadence, a complete short selector/counter sequence could occur between samples. All-zero observed counters do not exclude the stock refresh path, transient state, unobserved comparator calls or a counter crossing between reads. The run is separately bounded to 15 seconds, unlike the 20-second DP80 tests.

The key was armed at native monotonic 185567715269 µs after the full first clean cycle. Down ran at 185567718339..185568000395 µs; Up at 185568151531..185568175757 µs. Both returned zero with empty stdout/stderr and no timeout. These are process call/return brackets, not key-consumption or display timestamps. The intended action in the phase premise is saver wake; no Apps header preparation occurred before EH, and no valid Apps→Live exposure is established.

Baseline/post R, C and N bytes are unchanged, as are X/Y/RGB/B/Diff, the two 104-byte fixed-reference samples and both lane-gate tables. Both fixed samples and all 68 primary u16/68 secondary bytes are zero. X/Y/RGB/Diff and all N ordinals/source counts remain zero; B is nonzero and byte-identical across the pair, consistent with retained fields on partial-clear paths. Local table permission does not prove that a loop reached any particular lane. D and M do change: the JSON retains all D halfwords and changed byte offsets, rather than assigning physical units or an epoch to these software metadata. For example, M halfwords at offsets 0x12/0x14 change from 2159/1980 to 325/1755. This shows that the observation was not a byte-static capture of every context field, while leaving scheduling and producer identity unresolved.

The actual native-clock gaps are:

| Boundary | Native monotonic µs | Derived interval |
| --- | --- | --- |
| EB baseline last IN → EH first OUT | 185553028239 → 185567703703 | 14.675464 s |
| First H OUT → last H IN | 185567710161 → 185582499470 | 14.789309 s |
| EH last IN → EB post first OUT | 185582499634 → 185592115221 | 9.615587 s |

EH process time is 185567700452..185582704085 µs, or 15.003633 s. H brackets bound USB transactions, not exact firmware sample times. The gaps and all read sequences are conditional on the saved same-boot USB61 identity and reply freshness; none is an onset bracket. The phase/admission/ledger statements bound the coordinated experiment and do not continuously attest every possible client.

The original cached UI-before getter output reports Apps, saver windows and CSFS. Parent subsequently authorized inclusion of the later cached UI-after output, which also reports Apps, saver windows and CSFS. Both retained getter commands, authenticated transport envelopes, saved stdout and derived summaries are checked. The delay allows the saver to reappear: these two snapshots do not prove continuous saver presence, failure to wake, unchanged intermediate UI or emitted light. No physical claim is made.

Source qualification is the selected package SHA256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`; image1 file offsets are VA+`0x40200`. The checker rehashes EG's five source ranges, 56 instruction anchors and literals. Selected source at `0xc250` compares C7 with CPU4c2 and seeds CPU4c4 to 1 for a changed nonzero selector or clears it for zero. `0x1c12c` can copy the boundary reference while both selector/counter are nonzero, counting qualifying boundary events rather than proving one distinct top and one distinct bottom. Sampled zeros here leave that intervening event order unknown. EJ's separate timer/provider report is pinned as context; this analysis does not assert a measured callback period or pursue persisted/high-bank operations.

Reproduce with no target access:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 analyze.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -O analyze.py --check
```

Each run verifies the exact derived JSON and rejects 494 malformed cloned window/step/receipt/checkpoint/key/envelope/transport cases. Original captures, frozen helpers, CURRENT and public repositories were not modified. `input-provenance.json` references private originals without copying raw OEM windows or root envelopes. The result narrows this run to a clean saver-context observation; it establishes neither a failing Apps→Live mechanism nor a prevention fix.
