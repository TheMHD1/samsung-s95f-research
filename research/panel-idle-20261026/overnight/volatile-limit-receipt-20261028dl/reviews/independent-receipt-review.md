# Independent DL structured-receipt review

**PASS for the frozen bounded implementation.** No blocking defect was found in DL's receipt separation, native entrypoints, strict parser or orchestration. This is a host-only independent review; the reviewer did not author DL. It carries forward DJ's bounded policy-comparison limitations, rather than establishing electrical safety, a root-cause fix or permission for an unknown USB phase.

Final on-disk SHA256 pins:

| Artifact | SHA256 |
|---|---|
| Program.cs |d66128ae3faa00f907a3c017799a26f8ad06d783945deee3532f55312d09a307|
| FixedLimit.dll |f8f7049c5254ec07a248da0262a2047c74fa4c587759a39f0cd1bb2b4374b620|
| parse-result.py |fdfdd792ede3beaadc390b43f372ad4dcec369b5998051bd373fc53e29b05777|
| run-once.py |eaaacabc19bbf948db3a83391d15a1cf41c0405b1d30d0eea68e27f660316c40|
| test-runner.py |1d7f30d624fe70bef8a122337821825a89c8a73a7baf00f7296a654fda9815b8|
| host-build-checkpoint.json |46ee3a4611634bb7662026321b70cff17e674e970b184f584fe95a31cb76f7c9|
| deployment-manifest.json |95c5f4c911efa3ae1b401f4a11c02294d41f686dfba0809c829dec60a70ad1e5|
| source-inventory.json |9bd7ba2805b5b2b27d54390696763a23b2800d6719c9fd682e175c6c6dba1bbb|

A direct comparison of the complete pre-entrypoint native source against frozen DJ shows only the schema-name change. Thus IOps/RealOps, fixed c4 write and values, phase transitions, clock-error completion rule, expected-device checks, preconditions, dynamic whitelist, readback, cleanup and all644 fake native checks are unchanged. The additive native code opens/publishes receipts and replaces the real entrypoint's stdout serialization. No extra USB header, write, retry, reset or recovery path was introduced.

`Receipt()` allows only `selftest.receipt.json` or `native.receipt.json`, under the current directory shaped exactly `/tmp/researcher-limit-dl-` plus32 lowercase hex characters. `statx` with no-follow requires type/mode/UID fields, directory0700 and UID=EUID ownership. `open` uses O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC, mode0600, with ARM's correct O_NOFOLLOW0x8000 and the host/ARM64 value0x20000 on the alternate branch. A pre-existing regular file or symlink is refused. The wrapper separately guards the fresh root-owned stage and sets umask077.

Both receipt files are opened **before** the associated operation. Self-test captures only managed Console.Out into a StringWriter, then writes its one JSON result to the exclusive file; its operations are FakeOps. Production opens its file before `Run`, and serializes the outcome directly after USB cleanup. Publishing bounds UTF-8 bytes to24576 and flushes the file to disk. A creation/publish/dispose failure is not treated as native success or retried. Opening a receipt before Run means creation refusal cannot accidentally follow an otherwise unrecorded production operation.

The wrapper captures three distinct blobs: structured receipt<=24576, diagnostic stdout<=16384, stderr<=2048. The worst combined base64 payload plus fixed framing fits its65536-byte root-response cap. Each blob has its own declared size, SHA and canonical base64 verification; exact boot, uptime shape, native exit and full terminal framing are required. Full envelopes are saved before parsing. Diagnostic stdout is opaque data and never a semantic self-test/native receipt, even if it contains JSON or the previous byte-interleaved GC output. The structured self-test must be exactly the644/zero-target-operation result. Native parsing independently refuses GC rows and checks the full prior schema/profile/action/device/phase/count/raw-hash contract. Exit0 and empty stderr remain necessary; a parse failure cannot fall through to production invocation or cleanup.

Readiness, cached census/instance checks, fixed device binding, one native invocation, no retry and separate restoration remain in place. Final integrity and exact inventory precede cleanup; ambiguous/failed paths retain their recorded cleanup requirement. The root45s/host75s and native40s transaction budget remain unchanged. The stage contains the three payloads plus six explicit receipt/diagnostic files on a successful run. No arbitrary path or command is supplied over a protocol.

Independently rerun **1486 host checks normally and under `python3 -O`**, each with **377 generated shell syntax checks**, maximum command **7992 bytes**. These include actual host exclusive receipt creation/0600 mode, existing-file and symlink refusal, nonprivate/wrong stage refusal, the retained real GC-interleaving fixture, corrupted/duplicated/partial/oversized envelopes, diagnostic JSON separation, native/parser refusal and cleanup/no-retry cases. The native644 checks are rerun by the actual host receipt tests. No TV/root/network operation or OEM execution occurred during this review. ARM receipt-file behavior remains to be qualified by the centrally coordinated zero-I/O self-test before any production invocation; the wrapper fails closed if that qualification does not pass.
