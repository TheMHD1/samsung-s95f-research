# Independent DF eight-window integration review

Verdict: no blocking integration defect found in the frozen host-only delta. This review made no TV, root-client, USB, key or network call.

Reviewed the exact source diff against frozen `onset-sync-20261027bx`, the new transport parser, synchronized-key projection, wrapper mapping and source-window qualification. P is fixed at0x47000490/16 and N at0x4700ba28/36. The full cycle R/M/C/P/N/H/L/R and post set M/C/P/N/H/L/R agree across native source and both parsers. Native capture capacities are8 windows/16 transfers; final R indexes are7 for a cycle and6 for a post set. The36-byte input length joins the fixed allowlist. Header bytes agree with target0x101 and little-endian addresses/lengths. Matching IN is still attempted only after accepted OUT; short/failing new reads stop without a new header or retry.

Global accepted count equations use8 reads per complete cycle and7 post reads, with maxima647 headers/1294 bulk transfers. Baseline retention remains a duplicate and does not inflate I/O counts. Wrapper pins the derived parser, native checkpoint and three payloads, accepts the new schema and P/N retained filenames, and preserves one native invocation, one Left workflow, bounded stdout/envelope, fresh dynamic USB device number, strict accepted receipt and exact stage cleanup. The ARM32 transport implementation is unchanged; the added OnsetKey changes are host-test count/index adjustments only.

Independent host rerun: parser132 checks,84 malformed rejections; wrapper1344 checks,399 shell syntax checks, maximum7098-byte command. All passed, with fake target bindings only. The manifest and runner digests match the parent's frozen selection. No new build or target execution was needed for this delta review.

Limits: source qualification establishes intended SRAM range/layout and request construction, not whole live-image identity or a previously observed36-byte device reply. The first fixed P/N pair must satisfy the ordinary exact-length protocol checks; failure is a rejected trial. Cached UI, accepted key subprocess and fault tuple do not establish physical-light state or compositor consumption. Readiness remains a separate central coordinator decision under its explicitly recorded closed-world lineage premise. The inherited transport-parser comment referring to480 ordinary reads/five post reads is stale prose; executable bounds and equations use640/seven and are correct.

Reviewed pins:

- `Program.cs`: `bdfb71a425a66ce2cea5f56d14dad79812e8114f5eb65f005e1b430d773d94fd`
- `OnsetKey.cs`: `1e874627fa43aac9a47e888b36fe8d488bc1ebd5da7787b041ee95f531ebcd6b`
- `transport-parser.py`: `acc9f37f3586dc1066a31ec853d739da127fc2afb704fe7202f14a1cc170f0af`
- `parse-result.py`: `38264b8463db7f8add0e1f39c84726baed19ea17f46e3b3037307592ede30ddc`
- `run-once.py`: `946c0b8f66156b70d69bbf0acb121a165d7db26fac09811b247c8cdc8b008ff9`
- `deployment-manifest.json`: `ace348b57b15d27feca2bb67b88c4663535c2c72754b2cbb9ac51c88a3cc85c2`
