# Independent actual logger restoration replay

The saved FM restoration is **accepted and independently reproduced**. Its native receipt reports5 headers,10 bulk calls,4 complete INs and one fixed2-byte logger-off payload, ending ReadyForHeader with release/close. The wrapper's exact32-command sequence and all16 generated local artifacts reproduce byte-for-byte from saved authenticated responses. The new FM stage's exact nine-file inventory/hash check and `STAGE_ABSENT` cleanup succeed. The original FH/FG refusal and generic inflight audit remain unchanged; FM neither owns nor removes the retained FG stage.

`verify.py` is host-only. It loads frozen pure wrapper/parser code, substitutes an in-memory saved-response adapter and fixed stage nonce, and imports no real root adapter. It verifies71 pinned inputs before and after replay, including all16 restoration files, frozen FM manifest/source inventory and review, original five-input FH phase proof, FL source pins and the actual readiness evidence. It checks root transport exit/authentication/UID/child status, decoded transport JSON equality, command byte lengths, three-blob framing and exclusive receipt/stdout/stderr inventories. Root/native/host timestamps remain their respective clock domains; no inter-domain synchronization is claimed. Temporary replay files and four extracted raw windows are private below this analysis directory.

The frozen FM manifest is `c2315adb3f6643dd45fcceab70b4013fd0670bd96f7226a08dad3dec0094327d`; readiness is `9802410a028de39c206a56b565fecdb659daafafd56279f4dfe06703ed4900c9`. The underlying original FH phase proof remains `b6b5573a9c1ecf3b3b075e62a3906a598f15c505e2ee846864be3e3d9c82c140`: it establishes the original logger0→1, terminal known Ready/released/closed and no restore, while preserving native and wrapper refusal. Actual FM readiness equals the complete original USB65 identity, including boot, descriptor hash, sysfs/node instance and interface metadata. This binds the same instance, without claiming continuous holder absence or endpoint queue emptiness.

The native elapsed interval is66,374us: start201205370523, end201205436897. The sampled M root is20010000, AA0/AC2, scan1; C geometry2160/1920/2880, category92, C7=0 and C8=3. Both full R snapshots are **Clean0/0/1 at actual threshold40**. The first has logger halfword1, the second0. Comparing every one of their256 bytes finds exactly one changed byte, offset6, so the captured logger upper byte and remaining R contents agree. These are sequential samples, not atomic or continuous-state proofs.

| Pair | Full host-side transaction bracket, native monotonic microseconds |
|---|---|
| Pre-write R | 201205426329–201205426395 |
| Restore header plus fixed payload | 201205428473–201205429176 |
| Checked post-write R | 201205429181–201205429248 |

The write source is the frozen fixed command0x102/address0x47012406/length2 and payload`0000`; there is no wire-payload dump pretending to prove independently measured controller storage. Full header and payload return counts and the subsequent R0 are retained. There was exactly one native invocation, zero arm/UI/threshold/reset operations and zero retry. No ring read occurs in FM. Diagnostic stdout remains separate from JSON: selftest327B and native109B, with empty stderr. The selftest's exclusive receipt records406 checks/72 cases and zero target operations. Maximum actual root command is7954B, within8192. Pre- and immediate-before censuses each see11276 FDs, post11280; all have0 ENOENT,0 observed holders and0 other errors, each only a bounded snapshot.

FM's pre-write R is already Clean. Consequently **the logger-off write cannot be credited with producing the sampled Clean state**. Original FH's last complete set was Quiescent with C7=1/C8=0 and logger1; FM later samples Clean with C7=0/C8=3 and logger1 before restoring it. The monotonic gap from original FH end to FM start is1,296,895,160us. There is no continuous trace across that interval establishing when or why those fields changed. No MODE2 or threshold change was performed by FM; software Clean is not a physical light measurement. The data proves neither spontaneous physical recovery nor a causal effect of the logging gate on the earlier condition.

Normal and optimized Python runs produce byte-identical decoded output: **1470 checks,71 input files,13 malformed refusals**. Negatives cover original accepted/phase/release/payload/ownership claims, a rehashed nonzero final gate, corrupt envelope, deleted/reordered tail calls, substituted cleanup/integrity/post-census stdout with coherent outer JSON, and command substitution. Exact wrapper replay rejects these while the authentic saved sequence succeeds. The four extracted M/C/R/R windows are independently bound by extent/SHA256 and are kept private.

The known terminal phase supports the parent's separately coordinated next action. This analysis itself performs no target, root, network, UI, cleanup or recovery operation, and does not authorize an automatic follow-up. It does not infer physical display state, actual comparator instruction/FP, event736 content, whole-image reload, universal RAM clearing or a cause/fix. Later ordinary UI and EB validation are outside this frozen restoration scope.

Reproduce from this directory's parent:

```sh
python3 -B restore-analysis/verify.py
python3 -O -B restore-analysis/verify.py
```

`input-pins.json` binds original inputs; `decoded.json` contains derived data and timing; `source-inventory.json` seals this analysis and the four private extracted windows. Original receipts, wrapper record, source/manifests, proof and prior refusal analysis are immutable.
