# GE Live+saver stock MODE2 adapter

GE is a dry-default, host-qualified implementation of GB's prerequisite experiment. It has **zero UI keys, navigation, vendor reads, threshold/mask writes, automatic retries or recovery**. It consumes the unchanged DH DeadlineMode2 three payloads, fixed ioctl operation41/mode2 and native12/root45/host75 deadlines. No native assembly was rebuilt. This family has not been deployed or run against a TV.

The operational premise remains separate: a complete accepted EB fault40/logger0 source and known Ready/released/closed phase must refer to the exact current instance, while the cached UI must be Live+saver+CSFS. The latest Apps recovery or a historical fault capture cannot establish this premise. The cached predicate does not prove compositor focus, continuous saver state, key consumption, emitted light or electrical readiness.

## Fixed admission and execution

`admit-fault.py` locally parses the frozen EB16/32 family, full stable start/end fault R1/4097/0 at40 with logger0, every native/raw/hash inventory, all readiness evidence, authenticated saved root records and exact three-blob envelopes. It replays **every source command and saved artifact** through the unchanged EB wrapper with a no-I/O root. An incomplete/refused capture, changed result pin, source drift, logger ownership, unclosed phase or cleanup claim unsupported by the actual ledger refuses before loading a live root transport. Same-instance current identity and explicit closed-world phase lineage remain mandatory; no endpoint-queue proof is claimed.

The new coordinator performs an initial current identity/census, strict one-shot Live+saver+CSFS query and unchanged BV public rejects. Upgrade busy, display not lcdon, screenstate not1 or burn-in-progress not0 refuses. These getters are reject signals only. Initial UI/public failure sends no staging or native request.

`helper.py` preserves DH's exact staging commands, native invocation command, original stock receipt parser and successful six-file cleanup command. After staging it rechecks ordinary identity/census, repeats the unchanged public rejects, and takes one final strict cached snapshot. No root call occurs between that snapshot and the fixed native invocation. Host monotonic query-return→submission age must be0..1second inclusive. Missing saver/CSFS, wrong/duplicate tab, malformed bytes or clock failure stops without retry; staged files remain as evidence.

The fixed native result remains `kernel_return_zero_only`, with no power-action acknowledgement or recovery inference. GE additionally checks complete canonical framing and bounded receipt/stderr blobs before the unchanged parser. The original terminal/receipt and helper result are saved separately. A failed or ambiguous invocation produces no cleanup, postquery, retry or vendor call. A successful helper retains its exact existing file cleanup, followed by one strict post-init cached Live+saver+CSFS query. A post-context failure preserves the accepted helper terminal/result while GE overall admission fails; no navigation, wake, repeated MODE2 or EB is attempted.

`accepted:true` means only the helper and cached postcondition succeeded. `initializationPrerequisiteQualified`, `newInstanceQualified` and `freshEbBaselineQualified` remain false in GE. **The parent must separately prove positive old-instance disconnect/new enumeration on the same boot/path/descriptors and obtain fresh accepted EB clean40/logger0/full FN-compatible context.** GE does not collect or manufacture these later facts. MODE2 does not prove universal RAM clearing, instruction reload, panel light or root cause.

## Host qualification and CLI

`sh build-host.sh` writes the finite source and mocked test reports in this new directory. Normal and optimized Python outputs must match. Tests import only pinned source/pure parsers and no real root adapter. They exercise local source refusal, identity/public/cache/timing failures, canonical framing, one-shot invocation ambiguity, unchanged command bytes, helper cleanup and separate post-context failure. Reports and source inventory carry exact counts and pins. Scratch is private under `host-environment/tmp` in this directory; no target/network operation occurs.

Dry and manifest modes:

```sh
python3 -B run-once.py
python3 -B run-once.py --print-manifest
```

The readiness builder is also dry by default. The same explicit identity, phase-note and evidence arguments used by the frozen cached readiness family are required:

```sh
python3 -B prepare-readiness.py --wrapper ge --wrapper-sha256 <GE-wrapper-sha> \
  --manifest-sha256 <GE-manifest-sha> --identity <absolute-current-identity.json> \
  --phase-note <absolute-current-known-phase.md> --evidence <absolute-evidence> \
  --output <fresh-absolute-readiness-dir>
```

Only explicit `--execute` on that builder permits its single ordinary cached identity/census query. It sends no MODE2 or UI operation. A future centrally coordinated single initialization attempt, after independent review and current prerequisite admission, has this shape:

```sh
python3 -B run-once.py --execute --manifest-sha256 <GE-manifest-sha> \
  --capture <absolute-current-completed-EB-fault-capture> \
  --capture-result-sha256 <exact-result.json-sha> \
  --readiness <absolute-current-GE-readiness.json> --readiness-sha256 <decision-sha> \
  --output <fresh-absolute-output-dir>
```

All failures require central interpretation of saved stage/lifecycle evidence. File cleanup is not operational recovery. The adapter never deletes another refused recorder's stage, and does not send an automatic compensating action after a failure.
