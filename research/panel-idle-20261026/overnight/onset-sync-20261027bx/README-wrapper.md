# Bounded synchronized-onset runner

`run-once.py` is dry by default. Default mode prints a plan without reading build inputs, loading root transport, creating files, or target I/O. `--print-manifest` performs local read-only hash checks and prints a deterministic JSON manifest; its SHA256 includes these wrapper sources, tests and documentation plus all pinned native checkpoint files. No target action has been performed by this implementation task.

The only owned wrapper artifacts are this file, `run-once.py`, and `test-runner.py`. Native C# and `parse-result.py` remain frozen. The wrapper compiles exact hash-checked original passive-wrapper bytes to reuse its guard, integrity, self-test, and authenticated envelope parsers. New strict result parsing keeps transport acceptance, trial qualification, UI receipt and physical light distinct. Even a qualified trial establishes no key causation.

## Local review and invocation contract

```
python3 -B run-once.py
python3 -B run-once.py --print-manifest > /parent/chosen/local/manifest.json
sha256sum /parent/chosen/local/manifest.json
python3 -B test-runner.py
python3 -B -O test-runner.py
```

A later centrally coordinated invocation requires all of:

```
python3 -B run-once.py --execute \
  --manifest-sha256 REVIEWED_MANIFEST_SHA256 \
  --readiness /absolute/parent-authored-decision.json \
  --readiness-sha256 EXACT_DECISION_BYTES_SHA256 \
  --output /absolute/fresh/local/result-directory
```

Neither command here authorizes an automatic TV run. User authorization already exists; technical readiness and all TV actions are centrally coordinated by the parent. Parent prepares stable Apps/header focus outside this wrapper. The wrapper sends no UI, power, reset, recovery, telemetry enablement, ftrace, VLOG, or forced collection calls. The native helper alone attempts one Left down/up after the first full clean cycle. Unarmed accepted transport is retained with trial qualification false.

## Parent-authored readiness decision

Exact schema is `synchronized-onset-readiness-decision-v1`. All fields below are mandatory; extra fields are rejected. This is a shape example, **not a readiness decision**. Replace every placeholder using parent-reviewed evidence; no fake values are usable.

```json
{
  "schema": "synchronized-onset-readiness-decision-v1",
  "accepted": true,
  "identity": {
    "boot": "00000000-0000-4000-8000-000000000000",
    "sysfsRealpath": "/sys/devices/ACTUAL_PARENT_PATH/7-1",
    "sysfsStat": "ACTUAL_STAT_d_i",
    "busnum": "7",
    "devnum": "ACTUAL_DECIMAL_ADDRESS",
    "deviceNode": "/dev/bus/usb/007/ACTUAL_THREE_DIGIT_ADDRESS",
    "nodeStat": "bd:ACTUAL_HEX_MINOR:ACTUAL_DECIMAL_INODE",
    "descriptorsSha256": "SHA256_OF_EXACT_116_CACHED_BYTES",
    "configuration": "1", "authorized": "1", "runtimeStatus": "active",
    "interfaceNumber": "02", "alternate": "0", "interfaceClass": "ff",
    "interfaceSubClass": "00", "interfaceProtocol": "00"
  },
  "interfaceUnbound": true,
  "noHolders": true,
  "closedWorldVendorOutLineage": {
    "accepted": true,
    "statement": "PARENT_DOCUMENTED_CONDITIONAL_SOURCE_AND_LINEAGE_PREMISE_AT_LEAST_40_CHARACTERS",
    "evidenceSha256": "SHA256_OF_PARENT_PREMISE_DOCUMENT"
  },
  "evidence": [{"path": "PARENT_EVIDENCE_PATH", "sha256": "EXACT_EVIDENCE_SHA256"}],
  "endpointQueueProof": false
}
```

All identity values are strings. `sysfsStat` is `stat -L -c '%d:%i' /sys/bus/usb/devices/7-1`; `nodeStat` is `stat -L -c '%t:%T:%i' NODE`. Bus7 minor is `(7-1)*128 + devnum-1`. Descriptor hash must match the native's exact pinned 116 bytes. Decision is hash checked and copied unchanged before any root call. Evidence paths and hashes are provenance references within the parent decision, not independently reinterpreted by this runner. The explicit lineage statement remains the parent's conditional source/closed-world premise. Metadata, driver absence, no observed USBFS holders, and lack of new dmesg rows do not prove endpoint queue state or fresh enumeration. Unknown prior vendor-OUT phase must remain a hard stop in the parent's decision.

## Target sequence and limits

After local manifest and decision acceptance, load the reviewed root adapter SHA `bbf73130091b1a7ac5ec80490193821f0c8a0f150cfcb8f71d79ccc41633d66a` (remote45sec/host75sec, command8192B, response65536B). Root precheck uses cached sysfs/proc/stat only. Create a fresh root0:0 mode0700 UUID stage, upload exactly three pinned native files in offset-checked base64 chunks, mode0600, and verify exact size/hash/inventory. Payload bytes are the same local snapshot that was validated, with no later reread.

Run native `--self-test` (75 checks, zero target operations) and `--key-self-test` (22 checks, zero target operations). Check target `/usr/bin/dotnet` SHA `e5840c05c567183295f0bb37e3b28613618cec5e0c8c08a44a400672a1c73310`. A separate fresh preflight request immediately before execute checks exact instance/descriptor/configuration/activity/unbound interface and observed device holders. The execute shell then repeats identity and binding checks without a full census before its one foreground `--execute`. Native duration20sec plus bounded transfer completion and worker join7sec fits within the45sec remote budget only if identity checks and startup complete within the remaining margin. Full censuses each have a separate root deadline. No automatic retry exists. The remote deadline covers each command; it is not a claim of a new native kernel hard deadline.

No-holders census uses one batched `stat -L -c '%F|%t:%T'` across `/proc/[0-9]*/fd/*`, at most32768 entries and4096 processes, and exact character-device major/minor comparison. It covers alternate node path names. ENOENT diagnostics for numeric `/proc/PID/fd/N` are counted as snapshot churn under LC_ALL=C; other diagnostics, permission failures, holder matches or extent inconsistencies refuse the run. Counts are saved with each snapshot. Target fixed multi-operand stat format support has been reported qualified by the parent; full census timing remains an ordinary metadata qualification requirement. A per-FD subprocess loop observed taking25sec is intentionally not copied. Identity and unbound checks repeat after the census. These are non-atomic snapshots; they cannot exclude an intervening race or provide positive endpoint queue evidence. The native also rechecks its frozen preflight.

Native stdout24576B, stderr2048B, root response65536B. The entire authenticated envelope is saved before framing. Native bytes are saved before exit/JSON interpretation; validated retained raw windows are saved before postcheck and cleanup. Global counters are preserved without counting the baseline twice. Only strict transport acceptance, ReadyForHeader, released=true, closed=true, consistent native exit0/1, empty stderr, and a successful ordinary postcheck allow cleanup. Unarmed accepted transport may clean up while trialQualified stays false. Cleanup verifies exact five-file inventory, permissions, sizes and hashes before removing the known files and directory. Every ambiguous, failed or partially parsed run keeps cleanup_required=true and performs no recovery or retry; a cleanup failure may have removed some files, so retention is an intention, not proof of complete remote preservation. Parent must inspect recorded evidence and coordinate subsequent work.

## Host verification scope

Fake-root tests exercise success, unarmed transport, identity refusal before staging and immediately before invoke, timeout, partial envelope/native JSON, bad key/exit/stderr, postcheck race, cleanup guard/receipt failure, exact invocation counts, saved raw evidence, and all generated shell syntax/command bounds. They execute no generated target shell (only sh -n syntax checks), import no root adapter, and contact no TV/network. They do not qualify actual ARM execution, USB readiness, UI receipt, physical light, endpoint queue state, or target census timing.

The exact target diagnostic in parent-owned `stat-format-qualified-03.txt` is pinned by the host regression test (SHA256 `df9ca13c2d7fa58897e0292519cbf2034d9f8b8b0a8e49b51e26dd8d14e702fe`). Its opening quote is ASCII backtick and its closing quote is ASCII apostrophe. The classifier accepts either ASCII apostrophe or backtick as the opening quote, requires an apostrophe closing quote, exact numeric `/proc/PID/fd/N`, and the exact ENOENT suffix. Permission errors, nonnumeric paths, malformed quoting and trailing text remain rejected. This corrects the initial apostrophe-only classifier; it adds no target action or queue-state claim.

The parent's cached-only `census-qualification-05.json` failed before vendor I/O with a target awk syntax error; no holder census completed. Its retained command matches the original classifier bytes, while target diagnostics display escaped backslashes. The updated classifier therefore avoids escape-sensitive awk grammar entirely: it parses exact prefixes/suffixes and slash-separated numeric paths with string operations, constructs quote characters via `sprintf("%c",...)`, and uses `print` for its receipt. Both the awk program and generated census pipeline contain zero backslashes. Host regression tests now execute the exact `metadata_body` command-substitution and shell-quoted awk pipeline using a fake stat and the pinned actual target diagnostic, including a trailing-newline case. These execute local fixture commands only. A successful local regression does not supersede the failed target qualification; the corrected full census still needs centrally coordinated ordinary target qualification.
