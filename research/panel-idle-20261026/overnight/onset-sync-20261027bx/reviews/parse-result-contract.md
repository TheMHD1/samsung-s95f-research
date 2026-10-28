# Synchronized result parser contract and host verification

The parser and tests are additive offline artifacts. They do not edit `Program.cs`, `OnsetKey.cs`, the original observer, a root adapter or any TV state. No root, network or TV call occurred. This is an author verification record, not an independent review.

## Reused transport contract

`parse-result.py` reads and SHA-256 checks the exact original passive-observer `run-once.py` bytes against:

`a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82`

It compiles those exact already-hashed bytes with a non-main module name and the original file path. It does not execute the original CLI, load its root adapter or write a bytecode cache there. The original `parse_capture` validates the additional baseline; the original `parse_native` validates a projected result with the old schema and `accepted=observationAccepted`. The two new fields and additional baseline are removed only from that copy. All original global counters remain unchanged. The original native value and the extra baseline/raw files remain available to the caller.

The entry points are:

- `parse_native(text)` → `(native, captures, raw_files, gc_rows, qualification)`, where raw files retain the old `(filename, bytes, sha256)` tuple format.
- `parse_result(text)` → JSON-safe report with qualification, ordering, original global counters, capture summaries and raw-file metadata.
- CLI accepts one retained stdout file, or stdin, and prints the JSON-safe report. It reads at most 24577 bytes and rejects beyond 24576. A rejection exits 2 and leaves `transportAccepted=null`, not an invented transport failure/success claim.

A future central wrapper must save native output before rejecting its overall exit status. A valid unarmed outcome can have overall native `accepted=false`/exit 1 while still containing accepted transport evidence.

## Extension validation

Triggered successes require exactly one leading `trigger-baseline`, a complete `R,M,C,H,L,R` cycle with index 1, both R states decoded clean from exact raw bytes, exact transfer counts/hashes and ordered timestamps inside StartUs..EndUs. When the rolling last-clean is still cycle 1, every baseline byte/field/time must equal that cycle apart from role. Once rolling retention advances, the baseline must precede the later retained cycle. The armed timestamp must follow the baseline's final R-pair completion and precede any retained later-cycle USB request.

The key state must be the fixed Left/first-full-clean-cycle workflow, attempted/completed once, with exactly one successful down and one successful up child. Started/reaped must be true; exits must be integer zero; timeout/error fields are rejected. Output counts must fit 0..4096. Armed, down-before/after, up-before/after and intervention-end timestamps must be nondecreasing and no later than overall EndUs. Unknown fields, duplicate JSON keys, booleans masquerading as integer timestamps, malformed raw/state/hash data and extra attempts reject.

Valid unarmed `AlreadyFaulted`, first-cycle fault and zero-clean/partial timeout records remain `transportAccepted=true`, `trialQualified=false`. They must have no baseline or actual child activity and cannot claim overall native acceptance. Attempted failed/malformed key workflows are rejected by this constrained successful-trial parser; retain the original output for analysis instead of cleaning an ambiguous run.

## Temporal qualification

Overall EndUs is recorded after worker join. It is **not** used as the end of USB coverage. A structurally valid successful workflow is marked `trialQualified=false` with reason `keyOutsideObservedWindow` if Down begins after the last retained completed read, or no completed R pair overlaps/follows Down's start. Up can finish after USB observation stops without invalidating a correctly covered Down. This preserves transport evidence while rejecting a repeat of the original missed-key interval.

`trialQualified=true` means the instrumentation contract and this coverage condition passed. It does not mean that a key caused an RT transition, that the UI consumed it, that the expected tab was selected or that the physical panel was lit/black. `uiReceiptObserved`, `physicalPictureObserved` and `keyCausalityEstablished` are always false in successful parser output.

Every R observation uses the **full pair** from header OUT-before to data IN-after. The parser does not assume controller RAM sampling begins at IN-before. The conservative software transition bracket is `[latest clean R.headerBeforeUs, first fault R.dataAfterUs]`; it remains conditional on response freshness and is neither an exact event timestamp nor a physical-light interval.

The ordering report separates:

- a fault reply completed strictly before Down begins;
- a first fault read overlapping/touching the Down call;
- a first fault read after Down returns while the preceding clean/fault bracket still spans Down;
- retained clean and fault reads both after Down returns;
- no software transition, or no armed key comparison.

Key timestamps bracket the stock utility child call/return, including dispatch/reply overhead. They do not measure compositor consumption. Equality at an interval boundary is conservatively classified as overlapping/touching, not strict order.

## Verification

Both normal Python and optimized Python pass **113 checks**, including **67 rejected mutations**, with zero root/network/target calls. Tests load four frozen fixture files after checking their hashes, clone them in memory and add only synthetic intervention/baseline data. They verify exact baseline/raw/time matching, global counter preservation without double-counting, valid unarmed cases, timing order classifications, late worker dispatch with a larger EndUs, missing R coverage despite a later non-R read, permitted Up cleanup after USB completion, schema/type/state/child failures, invalid encodings/hashes/times/counters, duplicate JSON fields, inherited-parser pin failure and CLI acceptance/rejection.

The test script does not generate or execute an observer/helper, contact the TV or overwrite a fixture. The original parser's global transfer-count rules continue to validate the real read count; a duplicated retained baseline does not add six headers/twelve bulks to that count.

Reviewed current hashes:

| Artifact | SHA-256 |
| --- | --- |
| `parse-result.py` | `c2a653fa8ce07f18c3e817103228d7d0840a92a6e83ed44a4c8f968e856f3b06` |
| `test-parse-result.py` | `2b10f8af96452e59d0eea43b427a6b53a02cbbd8959fe12276b1f78af53fb308` |
| Original pinned passive parser | `a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82` |

The SWU adapter's separate ARM O_NOFOLLOW erratum and superseding target-trial report remain outside this parser work. This record neither changes nor revalidates that superseded adapter review.
