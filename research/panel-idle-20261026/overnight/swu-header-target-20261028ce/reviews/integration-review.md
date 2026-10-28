# CE integration review

Verdict: PASS for the exact final CE source, DLL, runner, tests and18-file deployment manifest identified below. No blocking integration defect remains. The initial runner findings were resolved and independently retested: root bounds now account for one-byte absent flags, host verification independently enforces the unique CRC representation, and native diagnostic counts must total4032 and match observed counts. This review makes no target execution/provider-success or full-schema claim.

This reviewer independently reviewed CE integration but authored the reused CC validator. This report is therefore not an independent review of CC's cryptographic/framing implementation. The CC copy was checked against its frozen source pin. Only this review file was written; no frozen CE/BZ/CC source, manifest or log was modified. No TV, root, network, real TEEC invocation or retained target ELF execution occurred. Existing host-built mock libraries were loaded by the inspected host tests.

## C# dataflow and unchanged operation scope

Comparison with BZ shows that Core adds a `PlaintextConsumer` callback, accounts for final output bytes in total, and calls the callback only after all fixed commands0/1/2 return successfully, count bounds pass and the final selector recheck succeeds. The callback receives exactly the aggregated bytes; when supplied, total must equal4032 rather than buffer capacity merely being4032. The exact command frames, Operation60 including+56 tail, shared capacities, command order and one-call budgets are unchanged. No new TA operation or retry was introduced.

The observed BZ count form4032update/0final is supported by the code and independently executed in the final32-check integration suite. The zero-length final copy at offset4032 is legal, and total remains4032. A4031update/0final case is also executed and refuses inspection despite sufficient allocated capacity while still completing native cleanup. The4016update/16final aggregate remains covered.

Program adds one exact public-key file pin and includes its identity in every existing selector/file/boot recheck. It calls the exact frozen CC API with `PublicPemPin.Master`. The callback copies the span to a4032-byte managed buffer, invokes authentication, calls the private file sink only if Accepted, and wipes that managed copy in finally. CC's own snapshot is separately wiped. No callback receives a raw pointer or unchecked advertised count. The library returns no plaintext reference or text.

A rejected authentication result creates no output file and leaves native acceptance false through exit70. If the file sink throws, Core marks inspection/local failure, still performs normal reverse cleanup, and Program cannot return success. If a private file was written but a later native cleanup fails, exit70 and the runner's strict terminal gates must prevent fetch/cleanup acceptance. Authentication success alone is not enough for native exit0: quarantined/code0/closed/released3/finalized, authentication Accepted and rawSaved are all required.

The callback runs before native session close/release/finalize, inside the inherited25-second native deadline. Private target output can therefore exist before normal cleanup completes, but central fetch is gated on reported complete native cleanup. This is the intended private quarantine ordering, not an assertion that the file sink itself closes the TA. Abrupt SIGALRM/outer termination remains distinct from normal cleanup and makes no TA rollback guarantee.

## Private target file sink

The live sink has one fixed path under the parent's fresh private stage. It uses WRONLY|CREAT|EXCL plus architecture-correct inherited NOFOLLOW/CLOEXEC/LARGEFILE flags; ARM flags are0xa80c1, x64 flags0xa00c1. It creates mode0600 and requires regular0600, link count1, effective UID ownership and exact initial zero length. One bounded write must return4032, fsync must succeed, final stat must still report4032 and close must succeed before rawSaved becomes true. A short/error write leaves an unaccepted private partial file; there is no write or TEEC retry. The temporary unmanaged snapshot is wiped via Block.Dispose. No plaintext is written to stdout or exception messages.

The target stage is protected by root ownership/mode0700 and the central runner's fixed inventory checks. Native O_NOFOLLOW protects the final component; stage/ancestor identity is not held by a directory fd inside SaveAt. The design relies on the existing centrally serialized, trusted-root private-stage assumption rather than claiming atomic protection against another privileged process replacing ancestors. Existing-file and symlink refusal were independently executed on host fixtures.

No display, controller power, reset, firmware-writing or installation call was added. This integration changes private metadata handling and does not constitute a damaged-panel remedy or a full firmware applicability decision.

## Runner review boundary

The final runner uses the existing authenticated adapter/boot/dotnet pins, fresh mode0700 stage, four pinned payload files, chunked offset uploads and exactly one native invocation. Native diagnostics are saved before interpretation. It requires exit0, empty stderr, five selector0 observations, the native quarantine/cleanup contract and one authentication Accepted/private_raw_saved status before fetching the fixed private output. Fetch checks exact stage inventory, mode0600/root ownership/4032 length and before/after SHA256, then preserves the framed receipt privately before decoding. The host's exact selected public PEM is independently pinned; Python zlib and cryptography independently repeat unique raw/canonical-PKCS7 selection, whole selected CRC, key CRC, declared signature size and RSA2048 PKCS1 SHA512. The exact pinned Python framing model then independently checks the bounded root framing and matching root/present/checked-leaf counts before creation of the host binary. Authentication is relative to the selected installed public-key pin, not a separately established OEM certificate chain. Full schema/applicability remain false. Known stage cleanup follows validated host acquisition; failing/ambiguous paths must retain evidence without a retry.

The host binary is created exclusively under a fresh mode0700 output directory and then chmod0600. Other receipt/record files can contain base64 plaintext and must remain inside that protected private directory. Python immutable byte buffers and JSON/base64 transport copies are not wipe-qualified; confidentiality depends on the private host directory and parent handling. This differs from the explicit normal-path target buffer wiping and must not be described as complete host-memory erasure.

The final root-status bound is `0<=leaves<=present<=roots<=selected-317`, preserving absent-root cases. Native update/final counts must each fit4032, sum to4032 and equal the reported observed counts. The independent host gate refuses zero or multiple CRC candidates and compares the computed form/selected extent/padding with the native status; it does not fall back after RSA or framing failure. The final runner differs from the already-reviewed functional revision only in the complete SOURCE_NAMES list. Replacing that line with the prior list reproduces its exact prior SHA256, independently confirming no intervening functional change.

## Independently executed host checks

The existing CE DLL was hash checked and run using `${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet` with `--self-test` and `--integration-self-test`. Both exited0. Inherited output confirms three golden frames, eight TEEC failure stages, allocation/count/selector guards, statx/open flags/NOFOLLOW, four retained target ELF content/Build-ID checks, canonical preload ownership, eight aborting exports resolved without invocation, and seven ownership rejection cases. Those tests load only explicit host mock libraries, not target ELF objects.

All32 final integration checks passed:4016+16 aggregate callback contents/order, successful and throwing callbacks followed by cleanup, no callback after eight native failure stages or three count-overflow modes, correct exclusive output flags, exact private fixture bytes, existing-file refusal, symlink refusal and bad output count refusal before creation, plus exact4032+0 acceptance and4031+0 inspection refusal with normal cleanup. `run-once.py` default dry printed target_operations0 and retries0. No25-second deadline test was repeated because deadline code is inherited unchanged.

## Reviewed C# identity

| Artifact | SHA256 |
|---|---|
| Core.cs | `8d9dc63298a007b49f8de85bb321eb816faba8e57af0222f3e49b60edaaad604` |
| Native.cs | `a65e424353311361892a3d940a16a4617ed59e0416ed5b3817e0dd5bf32dd623` |
| Program.cs | `fa89c790e499235a4a2bd50120c4f610a23af29b4f06cf0d576446527e84cfd0` |
| HeaderAuthentication.cs (unchanged CC copy) | `a9797c9dda6f66ed6cc2e764117915ac115b4f36db7796f8bb921be00ddce5cf` |
| PrivateHeaderFile.cs | `8fb5f0d0ded74740e42f69cfce99c276e53b66c2367d3a8830f0791151e53e8e` |
| IntegrationTests.cs | `e52fef9b7e7f77c97d509380614adedb8e81d1ceccc5d0ed4bf41e19bc64f0bb` |
| SwuMetadataAdapter.dll | `4394d2e25a547ef6c096f67e552331880d3319819ff5087159d483a994aa4d3e` |

## Final runner/artifact verification

All18 final deployment-manifest entries were independently checked for exact size/SHA256. The reviewed runner, tests, deployment manifest and final DLL hashes were checked both before and after the host suite and stayed unchanged. The exact copied framing model is SHA256 `e4ff82b67f2b6514f7c97a6bf309fa3dbdcef4a5acb6256724f8b24835c624af`.

The final fake-root suite passed in normal and optimized Python:53 independently CRC-anchored synthetic fixtures (including genuine signatures, signed malformed data and a deliberate unsigned CRC-ambiguity collision),12 orchestration cases, maximum generated command4721bytes, targetOperations0, rootAdapterImported=false. The suite executes independent RSA/CRC/framing verification rather than faking signature acceptance for its signed fixtures. Cases include upload/native/framing/authentication/schema-overclaim/representation/count-sum/observed-count/fetch-hash/host-auth/cleanup failures. The absent-root fixture exceeds the incorrect old4032//5 bound and now passes. Failed host verification prevents promotion of the private binary; failed/ambiguous outcomes make no cleanup-success result or automatic native retry.

For read-only execution, the test's single deterministic manifest rewrite was replaced in memory with equality against the frozen manifest. All substantive tests and shell syntax checks were unchanged; this adds one equality assertion, so this review observes840checks versus the parent's unmodified839. No manifest or source file was rewritten by the reviewer. Native32-check integration and inherited mock suites were run against the final DLL. No actual decrypted plaintext or real firmware signature fixture was available to this reviewer.

| Final artifact | SHA256 |
|---|---|
| run-once.py | `ebecd87cab031f72f8a55314f7ba93b05a9782e887e744f058afebaa74746622` |
| test-runner.py | `be846fdf790a1fe1778c9ef2144f4545366517151a1419e842d9a22311d365bb` |
| deployment-manifest.json (18 files) | `041242c9551ba397385379ca4d21d293b3d3de9d9a6355d5528a8f46ce4223d0` |

Any later source/artifact change requires reconciliation with this exact review identity. A centrally coordinated target attempt may still refuse because target CLR crypto-provider behavior and actual plaintext representation have not been observed here; refusal retains evidence and does not authorize a retry or alternate operation.
