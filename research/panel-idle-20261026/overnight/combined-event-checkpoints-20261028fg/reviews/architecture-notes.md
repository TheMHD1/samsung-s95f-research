# FG early architecture review — not final approval

Review scope is read-only host source inspection. The implementation is still being revised by its author. No source inventory or payload is approved by this note; final checks must bind the author's subsequent frozen files. No target, root-adapter, network, OEM execution, or new helper execution was performed in this early phase.

The new engine has a single claimed FD and fixed logger halfword address 0x47012406. Its two permitted OUT payloads are 0100 and 0000; upper-bit drift is refused rather than overwritten. The twelve maximum control pairs are baseline ring, prearm R/M/C, arm, armed R, prerestore R/M/C, restore, restored R, post ring. Fresh M/C is checked before each write decision. Already-zero prerestore is a distinct no-write result with a confirming read; it does not attribute the stock change to this process.

The inherited ReadPair attempts its matching IN once after a full header even if timestamp collection fails. The new logger write pair likewise attempts the one matching 2-byte OUT payload after a full logger header despite later clock failure. Short or exceptional header/data/payload transfers set Unknown, stop new headers, and retain unresolved ownership/restoration state. Local release/close is still attempted. The wrapper must stop further root requests on an Unknown terminal receipt.

The native budget is cooperative: 40 seconds measured before USB preflight, 4 seconds reserved per complete pair, 26 seconds reserved for six cleanup pairs plus margin, and 7 seconds for the key join. Every optional observation pair requires 37 seconds remaining. Prearm admission requires 38 seconds remaining before arm. This can refuse before writing or stop a partial first cycle without a Left. It is not a hard process deadline; blocking native calls, preemption, clock loss, process death, or root timeout can leave the gate unresolved. A restored result needs actual readback or observed already-zero state, not a planned finally block.

Receipts and both ring sidecars are acquired exclusively in the owned stage before USB open. The JSON cap is 24576 bytes, diagnostics are separate, and the sidecars are each bounded to 15372 bytes. The root envelope is capped at65536 bytes and commands at8192 bytes. Sidecar retrieval must bind both length and hash; accepted removal must bind the exact eleven files, final census, and integrity result. No final pin or size proof has been checked yet.

Two concrete early findings were sent to the author and parent:

1. Production main selected the ER parser path while pinning FG parser bytes. The author confirmed the path will become HERE/parse-result.py before freeze.
2. The accepted parser initially checked only a subset of retained 58-byte checkpoint fields. The author confirmed it will reconstruct all58 bytes from each retained complete raw capture, including H header-before/data-after deltas.

A separately known source/context correction is in progress: scan can be0 after a stock transition and is asynchronously sampled. Prearm and the first full clean baseline still require scan1. Later observation and cleanup should admit only the finite source-qualified boolean domain0/1 while retaining known RT, logger, root, AA/AC, geometry, and profile restrictions. A sampled R tuple must not be treated as synchronously determining the M scan byte. The author's promised final source/tests must verify both scan0 and lagged scan cases.

Final review remains pending freeze, exact source/payload/manifest validation, focused normal/optimized tests, all-row source binding, worst receipt and command caps, and end-to-end fake wrapper failure cases. Event736 remains a stock event argument, not an executing PC or proof of the selected-A/FP decision.
