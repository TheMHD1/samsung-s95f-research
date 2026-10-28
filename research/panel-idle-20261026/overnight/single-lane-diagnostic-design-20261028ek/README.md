# EK: fixed single-lane volatile diagnostic design

This is a **host-only design and pure model, not a write helper or deployable experiment**. It specifies one fixed bit0 set for logical lane570 and a separate guarded restore. It performs no TV/root/network operation, builds no native helper and installs no code. Existing EA/EC/EG source evidence and two immutable zero-table captures support the design; they do not establish continuous writer exclusion, unconditional rollback or electrical safety.

The only proposed data write is the two-byte primary halfword at CPU`0x20010474`, bus`0x47010474`, derived from current root`0x20010000 + 2*570`. Original full word must be exactly0. Set payload is little-endian1; separate restore payload is the retained original0. No other15bits, other lane, secondary byte, executable address, boot state, storage or persistent field is changed. There is no all-lane bypass, code patch, high-bank/POFLG/persisted route, reset loop or fallback bank.

## What this could test

The selected unpacker loads primary byte`[root+2*lane] & 1`; nonzero skips that lane's comparator irrespective of SB. Lane570 is the third unrolled lane of the568..571 group, at image1 VA`bf22..bf2a`. The chosen lane has appeared in prior fault tuples, but it is a **logical source index**, not an established physical pixel or damaged-edge coordinate.

A verified0→1 write plus a live-matching source fingerprint would establish a conditional local skip intervention: if this exact code executes with the captured root and reaches lane570, the gate skips its comparator. A matched new record epoch and comparable B/A/input exposure could then test tuple exclusion or score contribution. Absence alone is not proof: an earlier comparator can terminate the loop before570, the current lane may not qualify, and existing record arrays can retain old tuples. Masking a lane that would have returned0 can let later lanes execute; the aggregate effect is not necessarily minus1. Histories, publication bounds and reset timing also affect sampled scores.

No whole-fault prevention is predicted. Other lanes remain eligible. Earlier unchanged40 warm controls also stayed clean, so a later clean masked run would not isolate this bit's effect. A useful comparison requires the same instrumentation and independently characterized reference/initial/record state. Current physical content identity, pointer header/epoch, actual gate execution and optical state remain separate evidence gaps.

## Positive live source fingerprints required before any future write

Image1 file offset is VA+`0x40200` of selected package SHA-256 `bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`. DW's nonzero-tag image1 code alias supplies bus`0x46000000+VA`. There is no alternate-bank attempt on mismatch. Existing DX samples do not attest this later gate body, and a new USB instance requires its own current qualification.

| Region | Fixed bus / length | Expected SHA-256 |
| --- | --- | --- |
| Root getter38fc | `460038fc/12` | `d495280b4557a25b3c9154ca8d64678afb7b949c089d353ef884a74e68790268` |
| Root savebd6c | `4600bd6c/8` | `bc6728d90e8693c9f3ef034a61687cdcc130797d4015863c5f49e809c7eafc3e` |
| Operating mode/SBbe0c | `4600be0c/44` | `3864a39cd1178e7c986cbcdaaccae42843430e6a38d13de7723d115417232fcd` |
| Four local gatesbeb4 | `4600beb4/228` | `044752267f71da1f8c28f8bca423972ac77ca099b1deb089e23ac42cde138d19` |
| Required literal adjunctc030 | `4600c030/32` | `c629789db4bcbc06d85c7b04c6c880cb8ec1a4585b836dc28a72f83f5fd1808c` |

The four requested code intervals total292bytes. Getter38fc is6bytes of actual instructions,2bytes of alignment padding and the4byte literal3904=`CPU200004e0`; that word points to the mutable root pointer, whose current value must be checked separately. Root-save is whole instructions endingbd74. SB endsbe38 before the next branch. Gates endbf98 before the loop advance. The containing-function decode confirms instruction boundaries; none of these code spans cuts an IT block. These are read fingerprints, not patch sites or displaced-instruction qualifications.

The extra32byte **data-only** interval is necessary to bind the live semantics of otherwise unmeasured PC-relative words: c030=`CPU4aa`, c040=`CPU4ac`, c044=`CPU4cc`, c048=`CPUc95c`. Four code hashes alone would leave those literal values unobserved. Five fixed read pairs/10bulks/324bytes are proposed. They require a separately reviewed fixed read-only qualification implementation; `source-qualification.json` contains exact headers, source offsets, hashes and the limited instruction anchors. No live matches are claimed here, nor whole-function/image identity or active instruction fetch.

## Existing windows and exact proposed packet

Reuse EB's live-captured windows, avoiding a new two-byte read length:

- Primary: bus`47010470`,136bytes,68halfwords for lanes568..635; lane570 is **byte offset4**.
- Secondary: bus`4700cb94`,68bytes; lane570 is **byte offset2**.
- R: `47012400/256`; M:`470004a0/68`; C:`47000bc0/16`.

Both immutable ED and later EE table captures have all68primary words and all68secondary bytes zero and sampled known writer controls zero. These historical examples are not admission for the current target. No ongoing recovery input is incorporated in this freeze.

The one fixed write header is `020100007404014702000000`: u32 command0x102, address0x47010474, length2. Set payload is `0100`; separate restore payload is `0000`. Read headers use command0x101. `design.json` records every fixed read header and the proposed transfer schedule. DV established the two-byte OUT protocol class at a different address; its native allowlist does **not** authorize this address. A new fixed contract and independent implementation review are required. There is no arbitrary address/value/length argument.

For each separately admitted set or restore, use this fixed schedule:

1. Rpre, Mpre, Cpre, Secondarypre, Primarypre.
2. Rfresh, Mfresh, Cfresh, Secondaryfresh, Primaryfresh; validate both sampled contexts and exact original/owned windows before the write.
3. One write header and its exact two-byte OUT payload.
4. Primaryreadback, Rpost, Mpost, Cpost, Secondarypost, Primarypost; verify the expected full primary window twice and unchanged secondary/source guards.

This is16read pairs plus one write header/payload pair:17headers,34bulks,1768input bytes and2write payload bytes per action. Fresh R/M are part of the immediate pre-action sequence; they are still earlier than the last primary read and write. No key, reset, external callback or unrelated request may be inserted within an action. It is not atomic read-modify-write or a controller compare-and-swap.

## Set admission and ownership

Before opening the device, require the exact reviewed source/payload/readiness manifest, completed positive fingerprints and an explicit same-boot/device/interface/descriptor/FD/coordinator-lineage decision. Use the proven native owned-usbfs claim/FD checks and fixed vendor endpoint ABI, not managed symlink resolution or an inherited wrong allowlist. Ordinary metadata/censuses remain snapshots, not continuous client/queue proof.

Both pre/fresh contexts must satisfy:

- Current rootCPU20010000,2160rows/1920lanes/2880packed bytes,x base0; AA0/AC2 and R operating mode4.
- Known writer gates M+2 (`CPU4a2`) =0, R+0x60 (`root2460`) =0 and R+0x6e (`root246e`) =0. These source-disable the known trainer/publisher families only at their sampled times.
- Conservative additional guards: M+36 refresh counter0, C7 in0/1, M+34 mirror equal to sampled C7, and settled same selector across the action's pre/fresh reads.
- Coherent clean RT0/0/1, stable between the pre/fresh R reads.
- Entire136byte primary and68byte secondary windows zero, not just lane570's bit. Baseline originals and hashes are retained exactly.

Post-write full primary expectation is the same zero136byte window except lane570word1 at offset4; all68secondary bytes remain0. Any high-bit, other-lane, secondary, writer/control/root/geometry/dispatch drift is a failed set result with `writeMayHaveChanged=true`, not permission to clear those bytes. A set admission is **not ownership**: the pure model keeps it pending until exact write completion, full-window readback and post-context checks confirm the installed state. The receipt must preserve the original false/ambiguous outcome if any check fails.

This is a new mask-specific semantic admission contract. DU's thermal endpoint arithmetic/profile whitelist protects a different threshold experiment and must not be edited or selectively weakened to admit this write. Temperature/endpoints may be recorded for comparison, but they do not establish ownership of this table bit.

## Separate guarded restore and exposure

A successful set receipt creates conditional ownership only of lane570bit0. Its immutable parent ledger must bind the original0, installed1, full before/after windows, source/manifest hashes, device identity, protocol phase, exact transfers, readback and normal release/close result. A separately invoked restore must consume that receipt and fresh readiness; no automatic set/restore/retry loop is designed.

A finite observational exposure may legitimately change C7/mirror, publication bound, rows, ordinals, latches, temperature and clean/fault state. Those changes are recorded rather than forcing byte identity to an Apps baseline. Within each restore action, selector and coherent RT must be stable. Restore may admit coherent **clean0/0/1 or fault1/4097/0**; a fault alone must not make an otherwise qualified exact restore impossible.

All fixed root/geometry/x-base/AA/AC/operating-mode, device and known-writer invariants remain required. Full primary must still equal the exact installed window (only lane570word1); full secondary must still equal the original all-zero window. A changed word, other15bits, other lane, secondary flag, writer gate, refresh state or fixed source context makes restore **refuse without a write**. It must never clear a newly produced secondary flag or overwrite a legitimate different publication. Restore payload0 is checked against the saved original, not guessed from an old capture. The post-restore full primary/secondary/context checks must confirm the exact original window; otherwise ownership remains unresolved.

No MODE2/reset is allowed as an assumed mask restore while the bit is owned. Stock startup/clear paths are distinct and do not prove that MODE2 restores this primary word. Observation receipt/stage cleanup also does not restore the bit. Parent coordination must retain this outstanding ownership state until exact restore/readback is recorded.

## Phase, deadline and failure rules

A read accepts one12byte OUT header then owes one exact matching IN. A write accepts one12byte OUT header then owes its exact two-byte OUT payload; there is no invented IN acknowledgment. Once a header is fully accepted, a clock/deadline error cannot cancel that one pending partner. Short, overlong or throwing transfers move toUnknown and prohibit every later header, payload retry, bank fallback or reset. Mark `writeMayHaveChanged` before attempting the write header, including an ambiguous header result. Full payload completion gives protocol ReadyForHeader, not proof of RAM value or ownership; readback is still required.

A proposed cooperative40second transaction budget and2second per-bulk timeout must reserve32seconds before starting the write:4seconds for its two OUTs,24seconds for six post-read pairs and4seconds cleanup margin. Thus a slow preflight/action can refuse **before** writing. Root45s/host75s limits are inherited margins, not hard target termination guarantees. No native alarm is implemented in this design. Kernel timeout adherence, release/close latency and clock failures remain implementation qualifications, not unconditional wall-clock guarantees.

The future receipt must be exclusive0600 in a fresh owned0700stage and opened before any target operation. JSON goes to that file; diagnostic GC stdout remains opaque and separately bounded. Retain exact before/fresh/post raw buffers, full16read-pair/onewrite-pair metadata and phases, requested versus observed values, independent readback status, first failure, `writeMayHaveChanged`, ownership disposition and cleanup. Prove actual serialized success/late-failure/escaped-error bounds before any deployment; do not infer them from this pure model or truncate receipts. Normal cleanup releases/closes its own device and removes only exact known stage files after receipt validation; it is never a mask restore.

A failure before any write header leaves no intervention. A completed payload with failed readback/receipt or clock error leaves unresolved ownership even if phaseReady. Only a separate reviewed read-only reconciliation is permissible when Ready is positively established. **Unknown phase has no qualified automatic recovery route here.** It may prevent safe restore; blind replay or reset would violate the ownership rules. This is a material open boundary, not a fully guaranteed reversible implementation.

There is also an indistinguishable stock-writer race: a publisher could replace the word with the same1 between sampled guards. Full-window equality and zero sampled controls cannot exclude such ABA activity, computed/DMA/cross-core writers or a write immediately after the final read. USB read-then-write provides no CAS. Exact guards reduce observable interference but do not prove continuous writer quiescence or prevent overwriting an indistinguishable legitimate1 on restore. Resolving or explicitly bounding this ownership/race question is required in the future implementation review.

## Verification and implementation boundary

`state_model.py` is an integer/state contract only. It contains no target I/O, native binding, executable payload, runner or write deployment. Tests cover all65536halfwords for preservation of the other15bits; exact0/1 production admission; full-window and source-context drift; separate coherent clean/fault restoration; pending versus confirmed ownership; short/ambiguous header/payload stop; readback failure; boolean/width rejection; and the explicitly unobservable stock ABA case.

`verify_sources.py` checks45pinned inputs, source inventories, actual accepted result/raw relationships, instruction boundaries, literal targets, exact fingerprint hashes, lane/address arithmetic and generated packet schedule. Normal and optimized runs are recorded in `validation.json`. `source-inventory.json` freezes this design only. Future work requires a separately reviewed fixed read-only fingerprint qualification, a new native fixed data-write contract with exhaustive failure/receipt tests, resolved ownership/Unknown-phase boundaries, and a preregistered matched observational comparison. No helper is ready for implementation/deployment on the strength of this artifact alone.
