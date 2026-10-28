# CE actual target authentication: independent retained-evidence review

Reviewed 2026-10-28 UTC. **PASS for the actual bounded CE authentication result and private acquisition.** Independent host verification authenticates the selected4027-byte stream's3765-byte signed remainder with the exact pinned installed RSA public key. The retained target diagnostic agrees: one fixed0/1/2 sequence,4032/0 output, canonical PKCS7 padding5,12 present top-level roots, normal native cleanup and subsequent stage removal. No blocking discrepancy was found.

This is a read-only audit of an already completed central attempt. The reviewer performed no TV, root, network, TEE, updater, controller or display operation and reran no target helper. No private plaintext, salt, signature, decoded descriptor body, key material, raw base64 or private plaintext-file hash is reproduced in this report or its verification summary. Only this report and its own offline verification artifacts were written. The raw private acquisition and the frozen source/deployment files were preserved.

## Exact execution identity and recorded lifecycle

| Reviewed/run identity | SHA-256 |
| --- | --- |
| CE adapter DLL | `4394d2e25a547ef6c096f67e552331880d3319819ff5087159d483a994aa4d3e` |
|18-file deployment manifest | `041242c9551ba397385379ca4d21d293b3d3de9d9a6355d5528a8f46ce4223d0` |
| Runner saved at execution and current frozen runner | `ebecd87cab031f72f8a55314f7ba93b05a9782e887e744f058afebaa74746622` |
| Reused frozen CC authentication source | `a9797c9dda6f66ed6cc2e764117915ac115b4f36db7796f8bb921be00ddce5cf` |

All18 deployment entries still match exact byte counts/hashes and the run's retained manifest. Reconstructing every recorded bounded base64 upload produces the exact four reviewed payload files, including the4056-byte encrypted header envelope; no payload was inferred from a diagnostic alone. The at-run runner equals the reviewed runner byte for byte.

The complete `cleanup.json` receipt contains **34** authenticated shell calls: one native invocation at index31, private fetch at32 and stage cleanup at33. Every call has a matching single-command echo, authenticated root identity, transport exit0, empty decoded transport stderr, no host timeout, target exit0, empty target stderr and no target timeout. Commands remain within8192bytes. No separately recorded UI key, controller USB, power/reset, firmware-write or collector command occurs in this sequence.

The saved `record.json` is the33-call pre-cleanup checkpoint, not the final cleanup receipt. `invoke-once.json` has32 calls, the fetch checkpoint and `record.json` have33, and all three call lists match the corresponding exact prefixes of `cleanup.json`. This accounting distinction does not imply another invocation or missing cleanup: the final34th call returns the exact `STAGE_REMOVED` receipt after removing the fixed reviewed inventory and directory.

The saved native frame equals the original invocation response exactly. Its strict frame has `RUN_EXIT=0`, empty stderr, five selector result0/value0 observations, one diagnostic row, one authentication row and only the allowed runtime GC diagnostic lines. The diagnostic reports result0, origin4, local0, command counts1/1/1, output and observed counts4032/0, session closed, three shared buffers released and context finalized. The authentication row reports accepted, private raw saved, selected4027/padding5, roots12/present12/checked leaves0, signature/framing subset true, full schema/publication false. No plaintext appears in that native diagnostic frame.

## Private copy and independent authentication

The retained acquisition directory is mode0700. Its raw file is a regular single-link4032-byte file, mode0600 and owned by the same user as the private directory. The saved private fetch frame is byte-identical to the authenticated fetch response. Strict frame parsing and base64 decoding reproduce the retained raw file exactly; its computed SHA-256 equals the framed target hash. The successful fetch command enforces target root ownership/mode0600/size4032 and checks target SHA before and after encoding. The cleanup command binds that same raw hash before removal. The verifier compares these private hashes in memory without printing or copying them into its public-safe output.

The independent verifier uses Python zlib and cryptography directly. It imports no CE target runner or root adapter, reuses no target authentication result as a substitute for signature verification and returns no parsed private field/body values.

| Independently established property | Result |
| --- | --- |
| Exact installed master public PEM |426 bytes; SHA-256 `ebf12ab9d4ef069e1a6030b8c3b117894746637715270f7e3d37d3cd737f71a3` |
| Exact PEM CRC / key size / signature extent | `860be2ed` / RSA2048 /256 bytes |
| Raw-versus-trimmed representation | Raw CRC does not match; removing exactly one canonical5-byte tail uniquely matches |
| Whole selected-stream CRC | `cbcf1d91` over4027 bytes, including prefix and signature |
| Prefix key identifier / declared signature size |Match exact installed-key CRC /256 |
| Signature verification |RSA PKCS#1 v1.5, SHA512, signature bytes6..262, signed bytes262..4027 |
| Signed remainder length |3765 bytes |
| Bounded top-level framing |Exact51-byte magic,12 roots,12 present,0 fully checked CRC/RSA leaves, exact remainder consumption |

The selected stream excludes five padding bytes. The privately saved4032-byte aggregate includes them; it must not be described as4032 bytes of unpadded authenticated OUIT content. Whole selected-stream CRC and the RSA signed span are different scopes. Independently, CRC over the signed remainder alone does not equal the anchored whole-stream CRC.

Seven negative bindings fail cryptographic verification: retaining raw padding in the signed span, including the prefix in the signed span, truncating the signed remainder, SHA256 substitution, PSS substitution, changing a signature byte and changing the final signed byte. These checks use transient host memory only; no altered plaintext copy is saved. They demonstrate that the acceptance depends on the exact span, digest, padding scheme, signature and signed bytes.

The bounded framing check enforces canonical root/mandatory flags, source-mapped outer tags, bounded descriptor lengths and exact selected-remainder consumption. It returns only aggregate counts. Other known descriptor bodies remain opaque; the0 checked-leaf count is preserved. No item name, key, salt, payload offset, nested graph or payload authentication field is extracted into this review.

## Input provenance to the complete official archive

The reviewer independently streamed and rehashed the complete acquired main MSD and official ZIP:

| Encrypted package input | Bytes | SHA-256 |
| --- | ---: | --- |
| Official ZIP |2,439,527,748 | `5891b5ac67157403a2cfa4541845cb68f4ddb263860f41bc874e41fb748d1f42` |
| Main MSD |1,493,538,434 | `790584c7a91391bc6e9964c8f1c4649c225d2f9e6aeffabfc5e58e8a64fb7fc3` |

The main MSD's first65,494 bytes match retained prefix SHA-256 `01821f40cf70841649c856090e23b35be6173659fb54be11f3b661a3e37bf92d`. Its interval234..4290 equals the reviewed/uploaded4056-byte header envelope exactly. Wrapper plaintext/encrypted CRC anchors are `cbcf1d91`/`efed4e54`, the marker is at the established offset, and CRC32 of ciphertext258..4290 is `efed4e54`. The official ZIP has one exact main member `T-RSMFAKUC-0090/image/upgrade.msd`; its size and read prefix match the acquired MSD. This binds the actual deployed header to the complete known package, rather than only a similarly named or separately captured prefix.

Full-file hashes and the encrypted CRC remain acquisition/storage consistency evidence. This audit did not independently repeat all ZIP-member CRC scans, authenticate every payload, or establish that the acquired complete image matches all executing firmware. The new RSA success authenticates the selected header remainder relative to the pinned installed public key; it does not turn the ZIP hash into an independently published OEM signature.

## Meaning and remaining boundaries

The previously unobserved target crypto-provider path is now exercised successfully for this exact CE DLL/runtime/key/SHA512/PKCS1 operation. The previous BZ result only established service acceptance/count4032 before wiping; CE now adds exact private acquisition, unique padding/whole-CRC validation, actual installed-key signature verification on target and independent host verification. These are substantive completed results, not synthetic-test extrapolation.

Signature authenticity is relative to the exact selected installed public key, not an independently certified vendor trust chain. `FullSchemaValidated`, `MetadataPublished` and firmware applicability remain false. All signed bytes are cryptographically covered even though most descriptor bodies remain semantically unparsed. Twelve top-level roots do not yet reconcile to the nine clear package intervals, establish payload names or validate nested item/group/data-processing graphs, payload CRCs or payload signatures. No filesystem plaintext, controller image identity, complete payload-decryption capability, flash safety or permanent blackout remedy follows from this result.

The retained authenticated private input is sufficient for the next bounded offline schema/graph review without another TEE call for this header. That work should consume the selected4027-byte representation while preserving the original4032-byte acquisition and its private provenance. Public sharing can use status/counts, public-key/package/source hashes and authored analysis; private raw output and the transport envelopes carrying it stay outside public exports.

## Reproduction and derived evidence

`target-authentication-artifacts/verify_target.py` requires an explicit `--private-trial` path, cryptography and the retained source/package inputs. It writes only `verification-summary.json`. Both normal and optimized Python runs passed **399 explicit checks**, including the seven negative signature bindings. The summary is byte-identical across the two runs. Neither execution contacts a target or exposes the private file's bytes/hash.

| Review artifact | SHA-256 |
| --- | --- |
| `verify_target.py` | `41f776db535c66ae6737b01f5e1a9bae382a7e1813dad4823dd6d1c67d50ac4c` |
| `verification-summary.json` | `fb154768b8fd30f39488ca4ad6ba4b171b34d64457854b554274eac5f6502997` |
