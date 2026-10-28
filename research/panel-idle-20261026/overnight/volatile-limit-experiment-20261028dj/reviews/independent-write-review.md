# Independent host-only DJ write review

**PASS for the frozen bounded policy-comparison implementation, with the interpretation limits below.** No remaining blocking code defect was found in the final native/helper, strict parser, wrapper or source guards. This is an independent review of DJ; the reviewer did not author DJ. The reviewer did author the separate DE formatter appendix, so that appendix is supporting source analysis rather than independent validation of itself.

The reviewed directory is `volatile-limit-experiment-20261028dj`. Final SHA256 pins, independently read from disk:

| Artifact | SHA256 |
|---|---|
| Program.cs |64096ac36d1d558b01703e4e43c58a218b7c730f88aab1ee5505ea1e2580e744|
| FixedLimit.dll |1fc52b243afa83f872c84745cef91babb0f42d4d121d12f6cb252bcba355150a|
| parse-result.py |0e0dd547ceed9802b3bc5be7de71fc92ffd18fc395b4ab131e1132c314c52e5e|
| run-once.py |25468222f447b0d217181ef65efb716e26ee2beb3dd80b9b8229f6c34c2940cf|
| test-runner.py |2f826421d3a12242440af0eaf0bfb185afcd03ed1ef147433dcf147419893b94|
| host-build-checkpoint.json |f570912ad6d3545036ad44cc150f191986fc52ae2b1e62db0d61de79edcbe2e0|
| deployment-manifest.json |242440a8ab09deb1d25beddda2b50239120a7a308621e4406e75d1025c2bbe12|
| source-inventory.json |7ead651c366288b2172262671af010d6799cc8cfbf599bb44e962a85c7d2345d|

The review file is outside the author's frozen inventory; it changes none of those artifacts.

The only write is target0x102, address0x470124c4, length2: fixed little-endian40→200 or200→40. No caller supplies an address, length or arbitrary payload. Real bulk OUT accepts only the fixed write header, four fixed read headers, or a two-byte40/200 payload. The controller sequence supplies exactly one payload in the required phase. ARM32/little-endian/16-byte ioctl structure and root UID/EUID are checked before real I/O; the ARM `O_NOFOLLOW=0x8000` and `O_CLOEXEC=0x80000` constants match this inherited target ABI.

The sequence is seven pairs: callback64, baseline R256, M68, C16, fresh R256, write2, readback R256. Pre-write guards check the callback tuple, clean stop/fault/ordinary gate/logger, full retained R profile, starting limit, alternative-event gates/latches, aggregate gate, numeric mode/root/geometry and source selector domains. R's only mutable exclusions are exactly86..89,8c..8d,90..93,a2..a3; selector byteca must be0/1 and equal baseline/fresh/readback. The readback independently requires the requested limit and unchanged remaining profile bytes. High bytec5 remains exact. No physical observation or root-cause claim is inferred from those bytes.

Two review findings were corrected before this freeze:

- Native preflight now requires the readiness decision's canonical `--device N`, checks current devnum against it, validates the opened FD's USB rdev/descriptors, and revalidates before and after claim. Its receipt contains that device number, and the wrapper binds it back to the decision. This closes accepting a different devnum between the wrapper's immediate snapshot and native preflight. Same-number reuse, ongoing exclusion and snapshot atomicity are not proved.
- A clock failure while ReadyForHeader now stops before issuing a new header. After an exact accepted header, clock failure still permits the matching IN/payload, then rejects the result. Focused tests distinguish pre-header failure from post-header completion. Short/failed/throwing bulk transfers enter Unknown and stop all later headers; there is no retry, drain, implicit restore or UI/reset operation.

Each bulk has2s timeout; the controller reserves4s before beginning each pair within its40s transaction budget. Root45s/host75s are transport limits, not a claim that all ordinary file reads are individually hard-timed. Release and close each run once for resources actually acquired, with cleanup errors retained. A rejected/ambiguous run does not automatically replay or restore the value.

The strict parser independently validates exact JSON fields/types, one native row, terminal state,14 exact counts/directions/phases/monotonic timestamps, total transfer-span bound, six ordered raw windows and their canonical base64/SHA, callbacks/profile/context/readback, and false physical/fix claims. Wrapper execution requires the pinned payload manifest and parent readiness decision before loading the root transport. Separate cached census/immediate metadata checks bind the instance; they explicitly do not establish endpoint-queue proof or continuous FD absence. The wrapper saves the complete returned envelope before parsing, retains evidence on ambiguity, invokes once, and only attempts stage cleanup after accepted native/parser/exit/status plus fresh metadata. Cleanup failure remains recorded; no retry follows it.

The record-capacity argument is narrow and correct: selected image1's publication bound allows indices0..200 at limit200, below the separate512-slot store guard, across all five u16 arrays. This does not establish electrical safety, running-code attestation, a root-cause fix, or permanent operation at200. It couples the alternate aggregate threshold and record publication bound, so the trial cannot claim to isolate those two effects. The clean precondition also means this helper cannot clear an already latched stop/fault. Explicit restore is a separate200→40 transaction with its own fresh readiness and clean guards; it may refuse after a later fault, and no automatic restoration is promised.

Independently rerun on the host against the final functional sources: native fake self-test **644 checks**, wrapper/parser **1032 checks** both ordinary and `python3 -O`, **238 generated shell syntax checks**, maximum command **6964 bytes**. Tests cover fixed set/restore, short/throwing transfer positions, context/profile refusals, cleanup failures, clock phase distinction, instance races, schema/count/hash/time/phase mutations, exact target ENOENT classifier fixtures, partial envelopes, action binding and no retry. No TV/root/network operation and no OEM execution was performed during this review.
