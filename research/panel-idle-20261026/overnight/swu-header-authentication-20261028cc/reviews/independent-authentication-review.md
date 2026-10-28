# Independent CC authentication review

Reviewed 2026-10-28 UTC. **No material defect found in the frozen bounded authentication subset.** The source is suitable for the centrally coordinated, separately reviewed CE integration to consume after its exact4032-byte aggregate and selector gates. This conclusion covers the pure CC validator and its fixed Master anchor; it does not approve an unreviewed integration, qualify target crypto-provider availability, establish a complete OUIT schema or infer firmware applicability.

The reviewer did not author CC, modify its frozen source/manifests/fixtures, regenerate signed assets, contact the television, invoke a root client/TEE/updater or use actual decrypted plaintext. Writes and the additional offline build are confined to this review and `independent-authentication-artifacts/`.

## Inputs and independent verification

The frozen `HeaderAuthentication.cs` SHA-256 is `a9797c9dda6f66ed6cc2e764117915ac115b4f36db7796f8bb921be00ddce5cf`. All76 entries of the author's frozen source inventory still match their byte counts and hashes, including the existing test/library DLLs. The exact Core ELF is `b8de9e31bf6e74cf9a1f3cfd2598658d978a4edd88b36d1c2f10129ccc8a2697`; all29 retained instruction/data anchors were independently mapped through its ELF load segments and compared to original bytes. The review also produced its own small disassembly excerpts; EXIDX range labels are not treated as individual function guarantees.

The independently read installed master public PEM is426 bytes, SHA-256 `ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3`, zlib CRC32 `860be2ed`, and an RSA2048 public key with256-byte signatures. The master selector/file relationship remains the retained `itemsPublicRSAKey.txt` source/acquisition trace, not an arbitrary PEM chosen from decrypted data. This verifies the exact selected installed-key pin; it is not an independently certified Samsung root-of-trust chain.

The first65,494 bytes of the separately acquired main MSD match retained prefix SHA-256 `01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d`. Direct reads confirm wrapper words at offsets234/238 are `cbcf1d91`/`efed4e54`, `Salted__` at242, and ciphertext CRC32 over258..4290 is `efed4e54`. These checks read encrypted package bytes only and independently bind the Master's whole-plaintext CRC anchor to the main wrapper. They are not a new full-archive hash or decryption check.

The retained validation-readiness report predates actual PEM acquisition and the BZ count result. Its statements that the key is missing and no bounded output count is known are historical gaps, now superseded by those independent acquisitions/results. Its prefix/CRC/signature/framing traces remain the source specification. The report's old padded-only Python model is not mistaken for CC's broader, explicitly conservative two-candidate policy.

| Offline check | Result |
| --- | --- |
| Existing frozen `HostTests.dll`, executed directly without rebuilding the author's tree |1,018 checks;53 synthetic fixtures;35 accepted,18 rejected |
| Independent Python cryptography + zlib + bounded root-framing implementation, normal and `-O` |472 explicit checks in each run; all53 fixture classifications agree; all29 byte anchors and76 inventory entries match |
| Every synthetic fixture against the actual Master public-key/wrapper anchor |53 refusals; no actual-key authentication success inferred |
| Additional independent C# harness compiling the exact frozen source into this review's own assembly |56 checks over14 cases; synthetic only, actual public-key parsing/binding only |

The extra compiled harness checks a valid synthetic baseline, actual Master versus synthetic PEM, actual PEM versus synthetic data, independently CRC-reanchored wrong prefix and wrong actual-key signatures, wrong declared signature length, modified signed middle and final byte, wrong signature/digest/PSS/remainder, deliberate CRC ambiguity and changed actual PEM bytes. New synthetic mutation CRCs come from Python zlib, not the C# CRC under review. Caller buffers remain unchanged; every refusal exposes no selected representation/counts or authenticity claim. The harness source is included and invokes no target library or platform interface.

## Representation and authentication binding

`Authenticate4032` first requires the actual input array length4032. It then requires a bounded, internally consistent independently supplied pin and exact public PEM byte count/hash/CRC, a single public-key PEM block with only surrounding whitespace, and the expected RSA key/signature size. The Master values are fixed constants. The general public pin constructor intentionally supports synthetic or other independently reviewed anchors; **CE must pass `PublicPemPin.Master`, never derive a pin or expected CRC from decrypted fields**.

The whole-stream CRC and signature spans are correctly different. The selected-stream CRC covers key-file CRCu32, declared signature-lengthu16, expected256 signature bytes and the entire OUIT remainder. RSA SHA512 PKCS#1 v1.5 verifies exactly the remainder beginning at offset262. The declared length does not select a potentially unsafe slicing extent. Actual Core bytes corroborate prefix reads, construction of the RSA sink after signature consumption, the digest selector2/SHA512 path, PKCS1 numeric padding1 and exact verification-success1 comparison. `VerifyData` hashes that remainder once before verification; it is consistent with the stock SHA512 sink feeding digest-level OpenSSL verification.

Only the raw4032-byte stream and removal of one canonical1..16-byte PKCS#7 suffix are considered. The validator computes each candidate's independently anchored whole-stream CRC and requires exactly one match. Padding-looking authentic raw data retains every byte when only its raw CRC matches. Zero matches refuse; two matches refuse before RSA. A later public-key-prefix, RSA or framing failure returns immediately and cannot trigger a different interpretation or additional trimming. All16 canonical pad lengths,16 authentic raw padding-looking tails and the deliberately ambiguous CRC fixture exercise those distinctions.

CRC is a representation/corruption discriminator, not authenticity. Acceptance additionally requires the pinned key, declared signature size and actual SHA512/PKCS1 signature verification. Wrong key, changed signed tail, digest substitution and PSS do not pass. Signature authenticity is relative to the selected pinned public key and exact authenticated span.

## Bounded framing and result scope

After signature verification, the validator requires the exact51-byte format magic including NUL, a bounded little-endian root count, canonical0/1 presence flags, descriptor extents of at least tagu32 + mandatoryu8, the21 source-mapped tags and canonical mandatory flags. Root count cannot exceed remaining bytes; descriptor lengths are bounded before integer casts/slices, so no attacker-controlled allocation or unbounded recursion follows a field value. The selected signed remainder must be consumed exactly.

Known CRC leaf18 consumes exactly9 body bytes. Known RSA leaf16 requires its11-byte prefix and exact declared leaf-signature remainder. These are framing checks, not validation of item payload CRCs or payload signatures. Other recognized descriptor bodies stay opaque. A known outer tag and bounded body do not establish nested item/group validity, names, payload identity, offsets, graph consistency or applicability. Unknown tags and noncanonical booleans conservatively refuse even where stock has more permissive branches. The resulting conservative refusal risk is documented and is not a false-authentication path.

`FullSchemaValidated`, `MetadataPublished` and `FirmwareApplicabilityValidated` remain false on every result. Refusals return zeroed selected/count fields and representation None. The public result has no buffer/signature/descriptor reference or content-derived diagnostic. The actual plaintext snapshots are fixed-size and explicitly zeroed in `finally` on normal success/refusal/crypto exception paths; spans do not create descriptor-buffer copies. The caller still owns and must wipe its original aggregate. No claim is made that this library erases all internal CLR/provider transient state or can undo an external plaintext sink.

## Integration limits and disposition

The library source has no file, console, network, process, P/Invoke or TEE calls, and exports only enums/status/bounded counts. It does not itself write the parent's planned private raw file. CE's selector/output-count gates, use of the exact Master, exclusive0600 creation, publication order, sink-failure handling, error mapping, cleanup and wipe remain the separate integration reviewer's responsibility. A full4032-byte private raw aggregate may include padding even when the selected authenticated span is shorter; downstream parsing must honor the accepted representation and selected extent.

Host RSA/PEM success and portable IL do not qualify the target runtime's crypto provider or prove a future live authentication success. A provider/platform failure must remain a failed bounded operation with no automatic retry or plaintext publication. The earlier BZ result establishes only that the installed service completed0/1/2 and returned4032/0 before wiping. Actual plaintext CRC/signature/representation acceptance is still unobserved by this review. This technical gap can be resolved by the centrally coordinated bounded CE attempt after its integration review; it does not justify blocking all source work or inventing another user-authorization requirement.

## Reproduction and artifact hashes

Run the existing host DLL with the original fixture directory and pinned public PEM as documented in `HostTests.cs`. Do not run `verify-host.py` merely to repeat this review: that script rewrites the author's build/log/verification files. The independent Python verifier needs `cryptography`, Capstone and pyelftools; this environment uses `PYTHONPATH=/tmp/tcon-capstone`. Its outputs contain hashes, fixed classifications and synthetic results only. The separate review-local C# project clears NuGet package sources and compiles the frozen source read-only.

| Review artifact | SHA-256 |
| --- | --- |
| `verify_independent.py` | `1450226e330a6bb6ce61507129dd0f050d8bf571756ca38d75b08d9749a63f4e` |
| `independent-verification.json` | `6646c6c5a0b26b4873ee93b89f233a043c65a5554865d186a396bf3a61b8ee0c` |
| `independent-core-excerpts.txt` | `5d3dcbbd4718ed63f380f407bd1db5e8c9fdb7c4db8d803605f244724ada3fec` |
| `existing-host-tests.json` | `f40c4802346cd4d88b58b356b844c592d5794e9ab94f289af537305852352fb8` |
| `IndependentBindings.cs` | `569232a5d38f5a47a572cf6b671897deacefe5b82777eab69732f691c53c5628` |
| `independent-bindings.json` | `3a704dda6f0ba65af8620f8ae51d0e7a81b79c42aea407e703ac27f4dc772c12` |
