# Fixed live-port contract (not implemented)

The only runnable EF implementation is a pure state machine. A live port must
be a separate reviewed additive implementation. It may bind the fixed actions
below; no arbitrary command/address/value or retry option is part of this API.
Do not invoke the hardcoded `DH/initialize-baseline.py` main or old recovery
quickpath main: they have fixed output directories and differing historical
scope. Reuse their reviewed constituent functions with fresh output paths.

`port.owner_lease()` must identify a parent-owned exclusive lifecycle, held
across initialize→observe, every staging/readiness/native/cleanup call and
any qualified recovery. `journal(snapshot)` persists intent before an action;
use exclusive private files, atomic durable snapshots and retained original
receipts. Check freshness/exclusive output before any normal key or MODE2.
Precompute host payloads/contracts and allocate the entire run's output tree
before initialization, to avoid a late local path collision after a successful
key or request. No generic root function is exposed by EF.

Every `Receipt` has the exact Action, original-evidence index SHA256 and exact
identity SHA256, plus bounded normalized metadata. The evidence index must list
original result/record/native/private receipt, readiness/evidence references,
all raw-window bytes/sizes/hashes and source/manifest pins. Store that index
and original bytes; digest-only normalization must not replace them. Common
facts are `accepted=true`, integer `retries=0`, `physicalObserved=false`.

| Action | Original checks and normalized facts |
|---|---|
| Apps/pre-header/return | Pin NAV + root adapter. Apps gates require accepted workflow, cached `d/apps.tab`, all key subprocesses reaped and no vendor header. Header binds frozen v2's optional wake/Right + two Up and all bounded settle records, final no screensaver and CSFS presence. `boundedHeaderWorkflow=true` is the workflow receipt, not proof of focus pixels. Initial Apps carries a digest of the actual boot identifier. |
| Public gates | Use frozen `public_gate` reply parsing for integer upgrade0/screen1/burnin0 and string `lcdon`. Preserve the actual replies; do not reinterpret missing/failed getters as good. |
| INIT / RECOVER | Pin `run-deadline-mode2.py`, its build manifest, original stock parser/contract and original source. Use `contract()` then one `execute(fresh_output,payloads)`. Require accepted `deadline-stock-mode2-result-v1`, helper_exit0, request_count1, cleanup_confirmedtrue, native_deadline12, parsed open/ioctl/close zero and classification `kernel_return_zero_only`. Normalize requests/helperExit/cleanupConfirmed, retain receipt hash. Kernel zero is not hardware action acknowledgement. |
| FRESH / RECOVER_FRESH | Retain bounded same-boot kernel/sysfs lifecycle proving old instance disconnect then new enumeration + expected configuration, ordered after the associated request's begin. Bind exact old identity and MODE2 evidence digest. Re-read full wrapper META_KEYS, descriptors hash, bus7/interface2, active/authorized/config1, node major/minor/inode, sysfs device/inode and a fresh bounded FD census; require positive unbound/no holders. Instance digest must differ even if devnum wraps/reuses. Normalize `oldDisconnected`, `freshEnumerated`, `previousIdentity`, initializationEvidence, bus/devnum, boot digest and target monotonic disconnectUs/enumerationUs. Do not use only tail dmesg lines without proving they belong to this request/boot. |
| READY_BASE / READY_POST | Use EB readiness schema `eb-rtp-lane-gate-readiness-decision-v1`, not DP schema. Bind fresh instance evidence and exact last vendor result/receipt/phase/release/close/cleanup/raw hashes. Fresh metadata/census now; hash evidence before and after constructing decision and before execute. `ED/prepare-readiness.py` is the concrete EB constructor pattern. Normalize schema to `eb-readiness`, current unbound/noHolders and lineageAccepted; endpointQueueProof remainsfalse. |
| READY_DP | Same strict contract with `dp-score-checkpoint-readiness-decision-v1` and EB baseline as last completed vendor result. `DK/prepare-current-readiness.py` already names the DP schema. Normalize to `dp-readiness`. The previousVendorEvidence field must equal the immediate predecessor's evidence index, never a stale historical accepted capture. |
| BASE / POST | Frozen EB `execute` with exact reviewed manifest, freshly loaded readiness/raw SHA, source-validated strict parser. Parse result, original native and raw files; require16/32, three native bindings, exact expecteddevice, Ready/errors empty/release/close/cleanup, packing/gate context. Match original hashes and every R c4=40. Classify both R samples by exact stop/fault/gate tuple. Normalize firstHeaderUs from first OUT and lastDataUs from final completed IN. No table-zero or N-zero admission test; retain contents for offline comparison. |
| DP | Frozen DP `execute` with exact manifest/readiness and pinned strict parser chain. Require wrapper accepted+trialQualified, original native accepted+observationAccepted, all counters/timestamps/hash provenance, clean cycle1 trigger-baseline, exactly one normal Left down/up, attempted workflow1, both children reaped/completed and no key error. Require Ready/release/close, exact same device and STAGE_ABSENT. Normalize terminal, full actual header/bulk counts, maxCycles80/duration20e6, bindingQualified and `rtEnd` from actual terminal retained R. Validate every R raw c4 and every compact checkpoint's start/end c4=40. `TransitionCaptured` requires native onsetObserved and strict fault terminal; TimeLimit/CycleLimit requires strict clean terminal. Extract first/last read times from actual transfers, not EndUs. Preserve all partial captures; do not invent full checkpoints. |

The normalized schema is deliberately an internal design contract, not a new
on-target receipt schema. For example `allSampledRLimits40` requires explicit raw
and checkpoint checks; frozen DP wrapper acceptance alone does not establish it.
The port must reject mismatched fields, pending key work, missing raw artifacts,
partial/short/ambiguous transfers and ambiguous cleanup. A wrapper exception
never becomes an accepted normalized receipt merely because a later cached
metadata read looks normal.

Before using this design live, implement and independently test these exact
bindings, strict original-artifact normalization, immutable source-set check,
request-relative lifecycle parsing, durable journal/owner lease and both native
read-time gap extractions. Replay saved **actual** accepted/refused artifacts
and malformed variants without target calls. In particular qualify the native
DP partial-TimeLimit terminal and readiness immediately after each helper.
This missing adapter is a concrete implementation boundary; no technical
permission question or additional user approval is introduced.
