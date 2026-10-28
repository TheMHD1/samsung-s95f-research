# ER source freeze for independent review

ER closes the newly observed logging blind spot: after a full Clean first cycle and one Left, exact stop0/fault0/gate0 at alternate threshold40 is retained as **Quiescent** and observation continues. It is never counted Clean or Faulted. This work is host-only; no target/root/network request, OEM execution, RAM write, reset or policy change occurred. EM, EQ and other frozen workstreams remain unchanged in content.

The selected EQ source supplies an ordinary-gate-only off path; it does not identify the actual EO caller. Quiescent is therefore an observation label, not proof that the controller is idle, physically safe or prevented from faulting. Every other unexpected RT triplet remains rejected. Native initial Quiescent refuses before key, including a Clean start/Quiescent end in the first full cycle.

The read map R,M,C,P,N,H,L,R and its fixed seven address/length definitions are unchanged. NativeBinding.cs and OnsetKey.cs are byte-identical EM. Source verification checks exact ReadPair, ReadSet, preflight/open/fd/revalidate/claim/start-clock, pacing, catch/release/close and cached descriptor-reading sections. No header follows ambiguous transport; a fully accepted OUT retains its pending-IN obligation even on clock failure. No new target files or sidecar are introduced beyond the same inherited three-payload/two-receipt/diagnostic staging contract.

The controlled Run changes classify the new state, require the initial full Clean baseline, permit later nonfault Clean/Quiescent R brackets, split completed-cycle counters, and replace the one rolling slot truthfully as last-clean/last-quiescent. Fault transitions remain separate. `cleanCyclesDiscarded` refers to the rolling slot; the baseline is a retained duplicate. No extra raw capture slot was allocated. The strict transport decoder was explicitly extended for these roles/counters/state bytes; no Quiescent-to-Clean projection or adjusted global transfer count is used.

The compact record is **58 bytes ×56 maximum**, adding end-R+0xca at offset54 and end-R+0x68 at offset56 to EM's54-byte record. EJ qualifies the root24ca selector-byte mirror source; EQ qualifies the root2468 zero-to-one trainer-arm input. Both fields were already in R; no transaction was added. The first54 byte coordinates are unchanged, while classification nibble3 now records Quiescent. Native classifies Quiescent only with exact R triplet0/0/0 and c4==40. Existing Clean/Faulted classification remains unchanged; this candidate's intended parent admission is unchanged40.

The requested period remains25ms, cooperative ceiling2s;56 zero-overrun cycles end near1.4s, with a1.375s first-to-last H span. Actual service/key scheduling can reduce coverage or change spacing. M/P/end-R taps remain sequential, and only H full-pair times are retained compactly. Dense read load may affect the system; no historical branch/epoch, every-comparator-call or optical claim follows from the record. Header cap is455 and bulk cap910, including a full last-cycle fault and seven post-fault reads.

Adversarial output covers clean and Quiescent prefixes at each14 late post-fault throw sites,19-digit clocks, maximum diagnostic counters and duplicated JSON-expanding bounded key errors. Maximum semantic receipt is24,301 bytes plus newline=**24,302**, leaving**274 bytes** under24,576. The same preheader-only full binding audit, late compact binding flag,128 serialized-byte error bound and exclusive private semantic file are retained. Opaque stdout16KiB/stderr2KiB/root64KiB/command8KiB/root45s/host75s budgets remain. There is no native process alarm or guaranteed2-second wall-clock termination.

Completed offline checks:

| Suite | Result |
|---|---|
| Offline .NET6.0.428 build | 0 warnings / 0 errors |
| Native lifecycle/protocol |93 |
| One-Left worker |22 |
| Checkpoint/Quiescent/capacity/failure |79; maximum24,302 including newline |
| Source/parent identity and unchanged critical sections |70 normal and `-O` |
| Inherited malformed decoder cases, adapted58×56 |439 normal and `-O` |
| Quiescent counters, resume/fault, new taps, refusals |399 normal and `-O` |
| Wrapper mocks/exclusive host receipt |1,506 normal and `-O`;479 shell checks, max7,850 bytes |
| Cadence and overrun arithmetic |196 normal and `-O` |
| Cached-readiness builder |17 normal and `-O`; one mocked cached request |

The wrapper tests now include full Quiescent and Quiescent-to-Faulted successful native fixtures, preserving distinct result outcomes and one-invocation cleanup. Initial Quiescent fixtures retain original refusal booleans and are rejected by the success parser without repair. Corruption tests cover every retained new tap, state nibbles, separate counters, wrong threshold, role relabeling and initial key admission. Older discarded compact tap bytes do not have separately retained full raw windows; their provenance is the source builder and original receipt/input hashes, not invented redundant raw evidence.

Host interpretation distinguishes workflowQualified/trialQualified from rtObservationOutcome (CleanOnly, QuiescentObserved, Faulted), and keeps physical/UI/causal proof false. Quiescent in an accepted partial R capture is also reported, even without a complete new checkpoint. A clean-only observation is not prevention proof. Software fault ordering now brackets the last retained **nonfault** R, which can be Quiescent, and the first Faulted R; it does not mislabel the prior R Clean.

The EM cached-readiness builder is copied with ER-only wrapper map/schema/marker substitutions. It has not been run against a target. A current parent-provided identity, explicit protocol premise and pinned evidence remain required; no endpoint queue proof is created. Native/semantic refusal or ambiguity still retains the stage with no retry/recovery; any refusal classifier/cleanup is separate. `build-host.sh` reproduces the offline build and tests using task-owned environment paths and cleared NuGet sources. The deployment manifest and source inventory pin reviewable artifacts, with independent reviews/build environment/cache excluded. Independent review and actual target qualification remain pending.
