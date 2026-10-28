# Four sampled code fingerprints at proposed checkpoint sites

The fixed read-only DX probe completed once, and all four16-byte payload hashes matched the selected image1 firmware package. This adds live sampled-code correspondence at the proposed execution-log sites. It does not establish active instruction fetch, whole-running-image identity, executable write safety or hook qualification. No execution logger was installed.

| Proposed log role | Linked image1 interval | Accepted bus read | Result |
|---|---|---|---|
| Aggregate score/threshold | `0x2020..0x202f` | `0x46002020`,16 bytes | Exact selected-package hash match |
| A/B pointer selection | `0xbd58..0xbd67` | `0x4600bd58`,16 bytes | Exact selected-package hash match |
| Qualifying tuple formatter | `0xc5d0..0xc5df` | `0x4600c5d0`,16 bytes | Exact selected-package hash match |
| Common fault setter | `0xc1e0..0xc1ef` | `0x4600c1e0`,16 bytes | Exact selected-package hash match |

[DW source qualification](../research/panel-idle-20261026/overnight/code-alias-qualification-20261028dw/README.md) established the address conversion from the selected firmware. [DX source and wrapper](../research/panel-idle-20261026/overnight/live-code-fingerprint-20261028dx/README-wrapper.md) fixed the four reads and expected hashes; its [independent implementation review](../research/panel-idle-20261026/overnight/live-code-fingerprint-20261028dx/reviews/independent-fingerprint-review.md) passed before production. The selected package SHA256 remains `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. Source correspondence is limited to these four sampled intervals.

## Recorded operation and scope

The [DY coordinator findings](../research/panel-idle-20261026/overnight/live-code-fingerprint-trial-20261028dy/findings.md) record one production invocation, four complete read headers, eight exact bulk transfers and64 input bytes. Native ended `ReadyForHeader`, released its claim and closed its descriptor; wrapper cleanup returned `STAGE_ABSENT`. There were zero writes, UI operations, resets and retries. The separate fake selftest passed724 checks with zero target operations.

The first OUT-before to final IN-after interval was181530599387–181530604026 µs, a4639 µs sequential transport span. This was not an atomic instruction snapshot. The probe followed a separately accepted final DM read at limit40; it did not itself resample controller fault state or optical output. The last cached UI selection was Apps. These facts do not establish continued clean RT state or physical panel light during the code read.

Private cached identity, own-claim binding, fresh readiness evidence and the prior completed transfer boundary were reviewed separately. Matching identity snapshots and a supplied closed-world lineage premise are not continuous endpoint-queue observation. The public checkpoint retains original source and derived capture summaries; it omits raw native/transport receipts, device/binding/network metadata and the four raw OEM code payload files. No code bytes were added to the existing scientific fixtures, which remain unchanged. Historical source fake tests retain only their previously reviewed bounded instruction excerpts as data, not executable OEM programs.

## What remains before execution logging

The [DS design](../research/panel-idle-20261026/overnight/rtp-checkpoint-hook-design-20261028ds/README.md) identifies the values an execution logger would need: actual aggregate and threshold, actual selected A/B pointers, qualifying operands and the common fault setter's event/caller. The successful read closes the narrower sampled source-alias/payload correspondence gap. It does not show that this alias was fetched for execution, that all surrounding control flow matches, or that writable storage is safe scratch space.

Positive memory ownership, stack/interrupt/ABI overhead, installation/removal atomicity, cache and barrier behavior, and rollback independent of a failed USB session still require evidence. Zero-filled memory is not assumed spare. A stock MODE2 recovery and USB re-enumeration do not by themselves prove that arbitrary overwritten instructions would be reloaded. No patch, background logger or permanent bypass follows from these four matches, and the blackout cause and prevention remain unresolved.

The [independent actual-capture replay](../research/panel-idle-20261026/overnight/live-code-fingerprint-trial-20261028dy/live-analysis/README.md) is frozen separately:770 checks passed in normal and optimized Python against94 pinned inputs, including97 negative cases. It replays the exact command/receipt contract using saved artifacts without importing the real root adapter. Private identity-bearing decoded output is withheld; original analysis source, validation, input pins and inventory remain available with the explicit private-input reproduction limit.

## Frozen memory and rollback constraints

The [DZ startup/ownership audit](../research/panel-idle-20261026/overnight/controller-scratch-rollback-20261028dz/README.md) passed1046 checks in normal and optimized Python. It replays all21 startup scatter rows and narrows several misleading apparent opportunities. Image0 has an owned stock heap initially spanning4KiB at CPU `0x20018000..0x20019000`; it can grow toward a ceiling derived from the current stack pointer. This is an image0 allocation domain, not an available image1 reservation. The proposed DS data pool alone needs5952 bytes, before stub/context/alignment/stack overhead.

Image1's startup initializes data and BSS, including existing RTP context and fixed references, without copying its low instruction bank. An unclassified numerical gap is not a reservation, and the unpacker's3920-byte stack use before callees, callers or interrupts rules out treating high SRAM as idle scratch. MODE2's recovered callback/mailbox/GPIO/I2C/USB lifecycle does not establish the mailbox receiver's code reload semantics. A matching fingerprint before and after a reset would show stability, not restoration of a modified bank. DZ qualifies neither a logger allocation nor guaranteed instruction rollback.

## Existing lane eligibility before comparison

The [EA source qualification](../research/panel-idle-20261026/overnight/rtp-lane-gate-qualification-20261028ea/README.md) identifies two existing per-lane gates before the ordinary comparator. The primary gate tests bit0 in the low byte of a two-byte-stride entry at `root+2*lane`; a set bit skips that lane. With that bit clear, a nonzero secondary byte at CPU `0x2000c95c+lane` skips comparison unless the separately derived SB condition is true. This describes local permission **if the loop reaches that lane**: a preceding comparator can terminate the loop, so a passing gate does not prove the call occurs. These are eligibility tests before comparison, distinct from the difference filter, publication bound and aggregate fault threshold. They do not recover an official field name or physical pixel mapping.

EA proposes two bounded read-only windows for lanes568..635:136 bytes at bus `0x47010470` and68 bytes at `0x4700cb94`, totaling204 bytes. The proposal requires freshly verified root `0x20010000`, xBase0 and retained runtime context. It is source-qualified only: there is no helper, live table result, table write or prevention outcome in EA. The operating-mode field4 differs from the record/predicate category1; the first host check's incorrect mode1 premise was corrected before any target operation. DX sampled the unpacker prologue, not these later gate instructions.

The [independent EA review](../research/panel-idle-20261026/overnight/rtp-lane-gate-qualification-20261028ea/reviews/independent-source-review.md) passed the91 source checks and6220 additional checks in both normal and optimized Python, including6192 decoded branch cases. That validates the source/range claims, not live gate values or historical execution. Initialization/writers, other bit meanings, lifetime, safe original-bit preservation, readback and restoration remain separate qualifications before any table intervention. Low-bit comparator suppression is not proof of electrical safety or repair. Moving EB/ED and the remainder of EC are excluded from this checkpoint; the existing public fixtures remain unchanged.

## Correction to the earlier trainer lead

The frozen EA review ends with a parent-reported, explicitly unverified lead that associated the trainer with AA. The later sealed [EC training-gate correction](../research/panel-idle-20261026/overnight/rtp-lane-table-writers-20261028ec/training-gate-correction.json) supersedes that lead: the `0xc01e→0xc058` call is gated by `u16[CPU0x200004a2] == 1`, loaded through the literal at `0xc050`. The separate field at `0x200004aa` selects category4 dispatch; it is not this trainer gate. The local secondary-override SB formula using4aa/4ac/4cc is unaffected.

At the retained final DM sample,4a2 was0, so that trainer was disabled at that sequential sample. AA0 was not the reason. Field4a8 was1920 and supplies the loop divisor on this path. These facts do not establish the trainer's state at other calls, live table values, historical gate execution or a prevention mechanism. Only this immutable correction artifact is included from EC; its larger writer investigation remains outside this release. The original EA review remains unchanged as historical evidence.
