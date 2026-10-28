# EE unchanged-40 onset control: independent offline replay

**This warm control did not reproduce the software fault.** The accepted DP observation completed 80 clean sampled cycles, with maximum sampled A0 24 and alternate limit 40 at both R brackets of every checkpoint. The later accepted EB capture again found all 68 primary halfwords and all 68 secondary bytes zero, with SB false. No threshold or table intervention was made. These results establish no prevention effect, physical picture state, root cause or fix.

This additive analysis preserves every original input. `analyze.py` checks frozen source/payload inventories, regenerates both manifests, strictly decodes the native receipts and envelopes, verifies all raw files and readiness evidence references, and replays all generated commands through a mock transport. It imports no real root adapter and makes no TV or network calls. `input-pins.json` lists 225 immutable input files; `decoded.json` retains the complete derived checkpoint trace, source endpoint contexts, table/reference comparisons, software timing brackets and explicit claim limits.

## Accepted sequence

| Boundary | Saved result |
| --- | --- |
| ED baseline | 16 read pairs; clean 0/0/1, original alternate limit 40, zero sampled lane tables; exact predecessor references verified |
| EE header preparation | Accepted normal keys, cached Apps tab and no saver; zero vendor operations/threshold writes; no optical proof |
| EE onset-01, frozen DP | One native invocation, one Left down/up attempt, 640 read pairs / 1280 bulk transfers, 80 clean checkpoints, `TimeLimit` |
| EE post-tables-01, frozen EB | One native invocation, 16 read pairs / 32 bulk transfers, clean stable R and original limit 40, both sampled tables zero |
| EE final Apps preparation | Accepted normal wake/Right/Up/Up sequence, cached Apps tab and no saver, zero vendor operations/threshold writes/retries |

Both native readers ended `ReadyForHeader`, released their own claim and closed the device; each exact stage was removed (`STAGE_ABSENT`). The saved boot/USB identity is the same USB instance 60 as ED. Identity snapshots alone do not prove continuous device ownership or absence of reinitialization; the explicit coordinator lineage statements remain premises. There was no new mask write, threshold write or stock reset in this control.

The final Apps result is complete and pinned. Its key calls, and the DP Left calls, are dispatch/return evidence; `execution_confirmed`/`uiReceiptObserved` and physical observation remain false. The EB reader itself performs no UI operation. Normal preparation is separate from the native DP one-Left action.

## Independently decoded score trace

The compact record is 34 bytes per completed cycle. All 80 records were independently unpacked and compared field by field with the strict DP parser: clean start/end RT codes, C7, both alternate limits, full A0 and low16 A0, q0, four history halfwords, N ordinal0, full H read-pair bracket and the M publication-bound mirror.

| Cycle | A0 | Four history halfwords | N ordinal0 | C7 | Publication-bound mirror |
| --- | ---: | --- | ---: | ---: | ---: |
| 1–2 | 0 | 0,0,0,0 | 0 | 0 | 200 |
| 3 | 0 | See full trace | 0 | 1 | 200 |
| 4 | 20 | 0,0,0,4 | 24 | 1 | 40 |
| 5 | 24 | 0,0,4,0 | 41 | 1 | 40 |
| 6 | 16 | 0,0,0,4 | 41 | 1 | 40 |
| 7–80 | 0 | See full trace | 41 | 1 | 40 |

Every q0 is zero; every start/end alternate limit is 40. No sampled clean A0 low16 exceeds 40. The C7/mirror change is sequential: cycle 3 already samples C7=1 while the earlier-read M mirror is still 200. It is not evidence of a simultaneous inconsistent state, an actual FP register observation or a selected-A branch. The source-selected normal mode-1 limit remains 200; the alternate limit remains 40. AA/AC endpoint context is 0/2 while R operating mode is 4; these are different categories.

The retained first clean cycle has all H scores, q and histories zero and N all zero, with historical R latch 69. The retained last-clean cycle has A0=0, q0=0, history0 [0,0,4,0], N ordinal0 41, source count0 zero and R latch 41. Their full raw H/N/R and read-pair timestamps are preserved and independently decoded. Baseline duplication is not counted as an extra cycle or transfer.

One Left was armed at 183111807161 us. Down dispatch/return spans [183111809593, 183111958824] us and up spans [183112110033, 183112139701] us; both returned zero, were reaped and did not time out. Strict qualification confirms down began within the observed USB window. The call times do not establish UI consumption or physical screen timing.

The nominal observation budget is 20 seconds: native start 183111792089 us, deadline 183131792089 us, outcome end 183131796169 us. Checkpoints sample sequential eight-pair cycles at nominal 250 ms cadence; they do not instrument every comparator call. No above-40 checkpoint does not exclude an unsampled crossing, reset, transient or a different earlier initial state. A0 is a source-defined aggregate count, not voltage, difference magnitude or a physical light measurement.

## Later EB observation and explicit gap

This was **not an immediate post-transition snapshot**. Saved DP root orchestration ends at 04:25:18.175004 UTC. Post-readiness cached metadata spans 04:26:27.906803–04:26:28.540721 UTC. Actual EB root orchestration spans **04:28:47.312366–04:28:54.520630 UTC**. These saved times supersede the approximate later handoff time.

The final completed DP R pair ends at 183131608380 us. The first EB header begins at 183348014860 us: a **216406480 us (216.406480 s)** numerical gap. From the DP outcome-end timestamp it is 216218691 us. The EB read span itself is 7351 us. All comparisons therefore span separate observations with a host preparation/analysis gap. The explicit post-phase premise says no intervening coordinator key, reset or vendor request; it does not establish continuous controller state.

EB start/end R are byte-identical, clean 0/0/1, alternate limit 40, normal mode-1 limit 200, historical mode-1 latch 49, temperature 24, both B upper endpoints 3161 and echo 0. Start/end N are byte-identical and entirely zero. M root is CPU 0x20010000, x base 0, geometry 2160/1920/2880, AA=0/AC=2/byte4cc=0, C7=0 and publication-bound mirror 200.

All X/Y/RGB columns are zero. B and Diff remain nonzero, but differ from ED by 2 and 51 bytes respectively. A valid current record prefix is not established, and A must not be reconstructed from those remnants. In particular, latch 49 is not a current N count. The post capture has no H window and is not an aggregate score observation.

## Table and reference comparison with ED

Both entire table windows are byte-identical zero between ED and the later EB capture: primary 136 bytes / 68 full halfwords and secondary 68 bytes. With SB false, each sampled lane passes `(primary & 1)==0 && (secondary==0 || SB)`. This is **local eligibility only**. Earlier comparator return-zero paths can terminate the unpacker before a later locally admitted lane is called. Neither capture proves historical gate execution, trainer inactivity, writer/reset semantics, a physical lane mapping or safe modification. The complete gate body was not live fingerprinted.

The fixed top candidate changed 81 bytes and bottom 84 bytes. Both 104-byte windows were independently decoded as 68 little-endian packed12 values from their first 102 bytes; all values and changed byte offsets are retained in `decoded.json`.

| Logical lanes | ED top | Later top | ED bottom | Later bottom |
| --- | ---: | ---: | ---: | ---: |
| 570 / 571 | 2168 | 2160 | 460 | 505 |
| 622 / 623 | 2155 | 2154 | 1363 | 1358 |
| 624 / 625 | 2170 | 2163 | 377 | 322 |
| 632 / 633 | 2164 | 2162 | 980 | 898 |

These are later fixed candidate bytes, not proof of the actual A source used by an earlier comparator call or of a matching record epoch. Changing candidates alongside a non-reproducing trial is a hypothesis lead, not a cause. The capture does not establish physical input/content identity, normal app policy, temperature causality, an electrical fault mechanism or a repair.

## Replay, source guards and verification

The frozen DP and EB manifests are respectively `ba02517d7f8bb5cae6aa4257c426b7cc50780bfdfd5e0a73a7838e2386dff9ee` and `e7df47861e25aca4df6fc18e82b646a53eada192451b9b16383c5b31a9f44a11`. Both source/payload inventories and regenerated manifests match. This pins the reviewed fixed-window/geometry guards, exact paired phase handling, cached owned-claim binding checks, no-header-after-ambiguity behavior and cleanup implementation; it does not claim every target-side branch executed.

Both selftest and native three-blob envelopes are checked. DP selftest reports 93 observer, 22 key and 44 checkpoint checks; EB reports 2071, each with zero target operations. Semantic JSON is read from the exclusive private receipt; native GC stdout remains separate opaque diagnostics. All raw encodings/hashes, retained file declarations, readiness references, cached censuses, terminal records and accepted results agree.

The mock regenerates **38 DP and 28 EB root commands**, matching every command and every saved artifact byte for byte. Maximum command sizes are 7778 and 7712 bytes, within the 8192-byte contract. Saved response identity/status and 45/75-second root/host budgets are checked. Readiness and pre/before-invoke/post censuses are bounded holder snapshots, not continuous absence or endpoint-queue proof.

Cloned malformed tests reject wrong checkpoint extents and dimensions, self-consistently hashed retained-checkpoint inconsistencies, invalid key results/timing, wrong fixed addresses, ambiguous transfer phases, corrupt envelopes and invalid transport status/length. No original input is mutated. Normal and optimized `analyze.py --check` results are recorded in `validation.json`; `source-inventory.json` freezes this analysis. No additional target operation was performed for this replay.

The bounded conclusion is that this instrumented warm control at unchanged 40 remained sampled-clean and did not reproduce the earlier software fault. It does not isolate a causal threshold effect or invalidate the earlier fault captures. Future explanations must preserve the separate initial states, reference/record epochs, menu/HDMI positive and negative cases, and the continuing lack of optical proof.
