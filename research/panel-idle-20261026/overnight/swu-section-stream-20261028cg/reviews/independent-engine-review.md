# Independent review of frozen CG section streaming engine

Reviewed 2026-10-28, host only. No TV, root transport, real TEEC, firmware write, or network operation was performed. The reviewed source remains unchanged.

**Result: no material defect found in the pure engine's stated raw streaming contract.** This review supports using it through a separately reviewed fixed-plan adapter with bounded native and I/O calls. It does not qualify a live adapter, transport, complete payload authentication, or installation.

## Exact inputs and reproduction

`SectionStream.cs` SHA-256 `d1f44521d28bd822af1dab47e9e983b9fbf973afbfde82b96a2c5b7600a3a874`; library DLL `95132d516c57c2fbe7b810194bb5fabdf752f4108616446f0388c810231eb81d`; inventory `c58c9fa4f9f9607693450e684c2fb8c4aedffbc7ec6da997f75d7d2f00a435b9`. All thirteen inventory size/hash entries were independently checked before and after testing.

The retained runtime ran the frozen `bin/Release/net6.0/HostTests.dll synthetic-anchors.json`: 84 cases, 1,808 checks pass. The independent review project links the exact frozen engine and mock definitions; building `reviews/independent-engine-artifacts/Independent.csproj` with cleared package sources succeeded with zero warnings/errors. Its executable adds seven cases and 35 explicit assertions. Summaries, harness, and project are retained in `independent-engine-artifacts/`; the build touches only that review directory.

## ABI and state machine

Context/session storage is four bytes each, shared descriptors 36 bytes, operation storage 60 bytes. Each frame clears all 60 bytes, including the implementation word at offset 56. Full-byte parameter type words are retained: command 0 `0x01010d0d`, command 1 `0x00020e0d`, command 2 `0x0000020e`. Command 0 uses the observed master/salt and p2 `(0,1)`, p3 `(1,0x201)` tuple. Command 1 advertises actual aligned input length at most 65,536 and a fixed 65,536 output capacity; its returned count comes from offset 32. Command 2 count comes from offset 20. This follows the retained target decoder contract rather than a generic nibble interpretation.

Exactly one derive, bounded update calls, and one final are possible on a successful run. Failure stops the forward sequence without native retry or another command. Positive short source reads fill the current input chunk; exact EOF and rolling ciphertext SHA-256 are checked before final, after provisional updates. Master identity is checked before initialization. Master/salt copies and whole mapped input/output regions are cleared along the normal and failure paths.

Successful allocations are tracked before descriptor/map validation; all owned descriptors are released in reverse order even when later mapping fails. Mapped spans must have the exact 65,536 capacity and be disjoint, while parent addresses must be aligned, nonzero and distinct. Session close, reverse wipe/release, and context finalize continue despite cleanup failures. First error and native origin survive later cleanup failures. Sink completion happens only after clean native cleanup; failure attempts sink abort and keeps acceptance false. Backend exceptions during ownership acquisition are explicitly reported as uncertain ownership, rather than silently claimed clean.

## Additional independent fault checks

The review harness rejected partially overlapping mapped spans and an incorrect mapped size before derive. It exercised backend mutation of operation capacity words and the offset-56 token without making those words trusted buffer bounds. Valid returned output remains bounded by the original allocated capacity and aggregate cipher-byte ceiling. Negative and over-reported sink counts fail without finalization or completion, preserve zero confirmed bytes, and still release all three allocations. Existing tests additionally cover native/code/exception failures, tail clearing between frames, cleanup failures, source truncation/extra input/digest mismatch, output overflows, short writes, guard failures, and invalid plans.

## Integration constraints and precise limits

* `Accepted` means completed raw transport and cleanup. It can be true when the backend returns no output or less output than ciphertext. The independent zero-output case confirms this behavior. This is consistent with the explicit raw-only contract; it must not be used alone to accept an extracted firmware section. A concrete caller must check expected original size, strict padding representation and authenticated/original integrity fields before promoting a provisional artifact. Actual CI/CK results are separate target evidence and are outside this frozen-source review.
* `MetadataPlanSha256` is validated as lowercase SHA-256 syntax only. The caller must bind that identity to an immutable authenticated plan, selected section, master, salt, offsets and source identity. The engine cannot derive a metadata-plan hash from fields it does not receive. An independently changed valid metadata hash is intentionally accepted by the engine.
* Ciphertext identity is established at exact EOF, after updates may have emitted plaintext. All sink writes must stay private and provisional until this check, successful final and cleanup, and caller payload validation. The source itself must pin its fixed file/range and must not silently reconnect or substitute bytes.
* Calls are synchronous. Guards between calls do not interrupt a blocked native invocation, source read, sink write or completion. A live adapter needs native and per-I/O deadlines plus an outer job deadline. It must also prevent concurrent vendor access, implement exact 32-bit parent addressing, and validate actual native mappings. No transport is supplied or qualified here.
* Raw CRC and SHA-512 describe emitted raw bytes, including any padding. On a failed sink write the attempted-byte counters may exceed confirmed sink bytes; failure flags prevent acceptance. Caller-owned original master/salt arrays remain caller responsibility after the engine wipes its private copies.

These are bounded interface obligations, not reasons to stall host-side implementation or re-run an already authenticated header. The smallest useful next adapter is one fixed section, fixed provenance and provisional private sink, with explicit size/padding/integrity checks and finite I/O/native/job lifetimes.
