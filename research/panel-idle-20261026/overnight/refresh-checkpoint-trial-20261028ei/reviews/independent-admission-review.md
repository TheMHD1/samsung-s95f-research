# EI independent admission review — final PASS

The corrected EI guard has no blocking finding in the reviewed scope. Host-only tests pass147 checks in normal and optimized Python with byte-identical output. The three EH FakeOps fixture shapes—clean terminal, full-cycle transition, and first-R partial transition—are admitted after normalizing every retained R+0xc4 and each compact row's start/end limit to40. No real TV, root-client, network or production observation was executed by this review.

Reviewed source pins:

| Artifact | SHA256 |
|---|---|
|verify-observation.py|9b7420b5092e35e59f65eeac6dd6e1c6747949f668868d7d599c51e3c2cd9498|
|prepare-readiness.py|c846e3a8f95ed2e7d8ebf14eb0e08195c3fa14b7406940efd404bccceebded53|
|check-predecessor.py|20d302b2b9132b0d116902ca15a8daf199704de5934d043afdb27437ab30dd1a|
|test-verify-observation.py|1b0f3a08a9821d20aeff416a5633b0376877f115075af00430cbb4a14b665c80|
|reviews/admission-validation.json|696826fa343bc1c93a80948808cbe40723856d5cbbff39319f1eafe1d5d5ceca|

Initial review found a counter type gap: Python equality admitted booleans/floats for integer wrapper counters and inventory byte sizes. The original failing result is retained as admission-validation-initial.json:89 checks and24 unexpected acceptances, before the parent correction. Parent changed only its owned guard to use the pinned strict JSON parser and exact integer tests. All24 cases now reject; duplicate keys and NaN/positive/negative Infinity reject too. The reviewer did not modify any EI root source or frozen EH file.

The final tests reject false/nonboolean acceptance and trial flags, wrong manifest, mismatched header/bulk/checkpoint counts, missing stage cleanup, extra invocation/retry, missing or altered raw files/inventory, non-Ready phase, incomplete close/release, native refusal and failed key children. Both compact start/end limits are mutated to200 in a discarded intermediate row, with canonical Base64/hash and saved compact inventory recomputed. The strict EH parser otherwise admits that native-valid data; EI independently refuses it because every compact row must retain40. A transport-valid, key-successful fixture whose Down begins after every retained IN has q.trialQualified=false; EI refuses it. This specifically tests the workflow qualification gate, separately from malformed key metadata.

The strict pinned EH parser proves exact native transfer/window/role counts, completed pair timestamps, retention ordering, terminal shape, key workflow, ReadyForHeader and released/closed state. EI then binds the wrapper's exact manifest and counts, all saved raw bytes/digests, all compact and retained R limit samples, and the sampled final tuple. Its lastCompletedDataAfterUs is the maximum actual retained IN afterUs, rather than native EndUs, which can include the key-worker join. The final R is selected from completed R pairs by afterUs; inherited chronological role checks require the final postfault R to remain faulted for a transition, and final clean/partial R samples clean for clean terminals. Duplicate trigger-baseline retention does not add protocol counts. Tests check the tuple/count/time result for all three shapes.

prepare-readiness.py is an exact source derivative of frozen EE's helper: only DP→EH wrapper/schema selection and EE→EI naming change. The EB option, pinned root adapter, fresh cached identity/census, ordinary bounded evidence, explicit historical parent protocol premise and endpointQueueProof=false are preserved. The review imports only definitions and performs no main/root call. check-predecessor.py likewise differs from EE only in the selected exact predecessor path/name: EE/post-tables-01. The already-written predecessor proof and every listed source/native/result/raw input hash were rechecked read-only. Its source requires exact16 headers/32 bulks, Ready/released/closed/STAGE_ABSENT, clean0/0/1 at40, identical start/end R and captured zero tables. It neither proves future queues nor excludes later firmware activity.

This PASS qualifies the offline admission logic, not a target operation or continuous phase monitor. Fresh readiness, the closed-world coordinator ledger and the actual EH/EB invocation remain parent responsibilities. No owner optical confirmation is an admission requirement. Cached UI/preparation and software RT tuples remain separate from emitted-light evidence. Parent's preparation-note.md correctly distinguishes prior reviewed Apps/header UI preparation from execution of the new EH native candidate.

Reproduction: run `python3 -B test-verify-observation.py` and `python3 -O -B test-verify-observation.py`. These invoke only EH's explicit FakeOps fixture CLI. Task-owned reviews/host-environment/tmp holds temporary captures and is outside any source publication inventory; temporary fixture directories are removed on exit. Tests never import or execute the root adapter, readiness main or predecessor top-level writer.
