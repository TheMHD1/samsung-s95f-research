# HA independent implementation review

**PASS_HOST_ONLY: no blocking implementation defect found in the frozen five-pair read-only candidate.** This qualifies the reviewed source/build/parser/wrapper contract. It is not evidence that the three new image0 SRAM intervals are reachable through the live USB/DMA endpoint, or that sampled values prove PC, historical emergency entry, loop exit or physical recovery. Parent remains the sole target operator.

I independently authored GY/HB source research; this review is independent of HA implementation, which I did not author or modify. All review outputs and disposable test files stayed under HA/reviews. No target, USB, root adapter or network call was performed; the frozen managed DLL was run only with synthetic selftests and its x64 production-ABI refusal path. No rebuild or checkpoint regeneration occurred.

## Frozen candidate

|Artifact|SHA256|
|---|---|
|deployment-manifest.json|`727a80b6091c8a58b297cec50cab103ee4e13873528c7475544ef2b9a3626437`|
|source-inventory.json|`f723782a84e856021ae60ca34df9e2274ea08b1777c7fda12da66691d7046ff3`|
|run-once.py|`5d1af2292602df25f0bd84e4ea27e1894356e677daf2d2b81aaecb55bb305492`|
|parse-result.py|`72fdfc382529e15688b762d2077ab3b009364d47b37ced99c7b3b679f9c74d24`|
|APFaultWitness.dll|`9a89568a1ea6788c46b38e73b49ac021e88b4ad7ad1453dfdb3693befdc50c3b`|
|host-build-checkpoint.json|`6ff6ac0bb114fd6fcce0fb26f8736e6271fefcb55ed19e8c13ff0bd1d7266104`|
|prepare-readiness.py|`b2f506847206b5ef1a5a31c45e98791283ae40011ba1d96b2ff7f50796352eb6`|

All27 author inventory entries have exact ordinary-file sizes/hashes. The deployment manifest was regenerated in memory from the frozen source/checkpoint/payloads and matched byte-for-byte. Final checks confirmed all pins unchanged.

## Reviewed behavior

The native sequence is exactly start-R `47012400/256`, AP `4500f0e0/20`, AP_EXCO-data `4500ff14/12`, AP_EXCO-context `45015924/4`, end-R `47012400/256`:5headers/10bulks,60 header OUT bytes and548 IN bytes. Every header is command0x101; the backend accepts only these fixed headers and the fixed input lengths. It has no memory-write command, logger change, key, reset, alternate address or retry.

The three complete image0 CPU intervals are inside the source mapper's `20000000..20020000` SRAM domain and translate through tag0 by adding25000000. The getter and pointer literals, identical image0/image1 mapper bodies, strict interval upper bounds, alignment and selected package identity are checked directly against retained bytes. These are specific source-derived SRAM windows rather than a generic address-bank permission. The source proof does not establish the exact windows' current USB/DMA accessibility. Any short/exception result must retain Unknown and prevent another header; no fallback probe is available.

`NativeBinding.cs` is byte-identical to frozen EB. It preserves ARM32 little-endian/16-byte transfer ABI checks, root UID/EUID, current boot/device/descriptors/configuration/interface checks, one descriptor read on the opened FD, same-FD statx identity, preclaim positive no-driver/ENODATA proof and postclaim native inode/GETDRIVER own-usbfs proof. The known managed sysfs alias-resolution defect is not reintroduced. The fixed readonly observer appropriately omits EB's lane/geometry admission: no runtime data redirects its addresses, no writer depends on that context, and arbitrary complete R bytes remain observations rather than being coerced into Clean.

The Controller is byte-identical to EB. A complete OUT header creates an IN obligation; clock failure after header completion does not skip that IN. Clock failure before a Ready-state header prevents it. An ambiguous/short/throwing transfer ends vendor operations, with one owned release/close attempt. Success requires all five windows, no errors, ReadyForHeader and successful release/close. The whole40second budget and4second pair admission are cooperative; per-bulk timeout is2000ms. Arbitrary OS stalls have no hard native alarm here. Root45/host75second transport bounds are unchanged.

The native receipt uses the fixed root-owned0700 nonce stage and exclusive0600 nofollow receipt file, with ARM-specific nofollow value retained. GC diagnostic stdout is opaque and separately framed. The parser checks exact schema/field sets, binding proofs, five ordered windows, ten ordered full transfer steps, lengths/counts/errno/phases, monotonic timestamps, canonical Base64/hashes and receipt span. It rejects boolean impostors for numeric fields. Both raw R windows, AP halfwords and context word/bit12 are decoded at their exact offsets. Magic-match is a sampled boolean only; stronger historical/PC/reset/recovery/atomic/optical flags remain false even when magic words match. Arbitrary valid AP contents remain transport-accepted.

The wrapper is dry by default. Local source/checkpoint/manifest/readiness validation precedes root module loading. The decision carries all16 exact identity fields and an explicit parent first-header lineage premise; it does not prove endpoint queue emptiness or continuous no-holder state. Fresh cached metadata is checked before staging, before native, immediately before native without another vendor transaction, and afterward. Selftest is one zero-I/O managed invocation; production is one invocation only. No automatic cleanup or recovery follows a refusal/ambiguity.

The successful tail requires post-census acceptance, exact inventory/size/hash validation of all9 owned files, then exact inventory plus explicit9-file removal/rmdir and STAGE_ABSENT. This retains the reviewed EB two-command integrity/delete structure rather than adding a hidden retry. Final payload/receipt failures leave the stage for separate reconciliation. Native output24576, diagnostics16384/2048, root envelope65536 and command8192 caps remain. The retained current-identity synthetic wrapper test maximum is7734bytes, leaving458bytes under the command cap. This is a measured mock with actual retained identity strings, not new live readiness.

## Independent verification

- 65 source/equivalence checks reproduced under normal Python and `-O`, byte-identical output.
- 978 parser/wrapper checks reproduced under both modes,269 generated shell commands each checked by `sh -n`, maximum7734bytes. Exact author test source was run with only its disposable-directory allocator redirected into reviews/private.
- 516 frozen managed native selftests reproduced. These cover all ten bulk positions with short/throw ambiguity, binding/claim/release/close failures, fixed-header mutations, clock failures and pending-IN deadline completion. Production mode on the x64 host refused ARM32 ABI with exit64 before device/receipt access.
- 86 additional focused checks reproduced under normal Python and `-O`: all frozen pins/inventory and exact manifest, five specs/548bytes, numeric-type impostors, every step's reverse timestamp, binding ownership/inode changes, expanded/incorrect window extents, independent AP/magic/word decoding, conservative interpretation flags and full interval bounds.

No further testing campaign is needed absent a source change or new finding. The next parent action, if separately admitted under fresh readiness, is a single bounded target qualification of these precise read pairs; this report does not itself assert that qualification happened.
