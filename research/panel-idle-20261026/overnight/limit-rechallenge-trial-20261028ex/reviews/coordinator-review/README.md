# Independent EX raised-limit coordinator review

PASS for final frozen `run-raised.py` SHA256 `23116a99f988947216ab77d95979dadf148aeed97a06d043fdd91b36fdb9dba4` and25-input `raised-input-pins.json` SHA256 `951cc194cc30fa1c29dfcd2d67a84e1d0f66a634e34b9e4acaa96d4c677e6400`. No blocking finding remains after the two bounded handoff corrections described below. This is host-only control-flow qualification, not an actual set200, observation, recovery, restored state or prevention result.

The reviewer verified all25 original pins against regular non-symlink inputs, including the coordinator self-pin, fixed operational helpers/manifests/parsers/builders, current identity/predecessor and completed independent FA/EY reviews. The frozen FA/EY/EB helpers enforce their own transitive source/payload and native contracts. The coordinator is dry by default; explicit execute is one fixed flow and a fixed fresh `raised-01` output. Missing/changed required inputs stop before creating a target-stage ledger or invoking any helper. The pins file and coordinator remain externally sealed local provenance; this is not an OEM signature or a continuous filesystem/queue-ownership proof.

## Findings resolved before this freeze

The first source checked only `accepted:true` in the saved EY admission before post-read. Missing, stale or malformed proof fields could therefore allow a post-read before a later field dereference failed. Final source now recomputes the pinned offline EY verifier on the exact onset directory and requires complete dictionary equality **before post-readiness or EB**. The independent mocks reject changed schema, Unknown phase, wrong limit, stale inputs, missing terminal, explicit refusal and verifier failure with zero post-readiness/EB calls.

FA/EB wrapper handoffs now check source/result schema, action where applicable, manifest/readiness digests, exact invocation/transfer counts and full raw inventory against strict native-parser results and saved bytes. All four wrapper counts require actual integers; Boolean aliases are refused. These corrections do not add controller operations or modify the native/helper contracts. Historical pre-correction hashes are superseded; no target action was performed by the reviewer.

## Fixed order and failure behavior

The successful mock sequence is exactly:

1. Ordinary pinned DK Apps/header preparation, with accepted result.
2. FA fresh metadata/readiness and one fixed set40→200 invocation.
3. Strict FA native parse, complete6-file raw binding, accepted source/readiness/result and7/14 terminal contract.
4. EY fresh metadata/readiness and one fixed200 one-Left reader.
5. Its saved offline admission and a fresh identical offline recomputation.
6. EB fresh metadata/readiness, one read-only capture and strict16/32 result/raw binding with both sampled alternate limits200.

There is no MODE2/recovery helper, automatic reverse write, fallback, retry or caller-selected operation in this script. Parent recovery/restoration remains separate. The coordinator can complete a valid post-fault capture; `complete_ready` describes the protocol boundary rather than a clean RT state, optical output or successful prevention.

Before attempting the FA wrapper, state conservatively sets restoration_required=true. Any wrapper refusal, host launch exception, parse failure, wrong manifest/count or corrupted raw data thereafter preserves that obligation and stops; it does not infer that no write occurred or launch a reverse write. The last_qualified_c4 field is explicitly a previous qualified observation, not an assertion of the current value after failure. Failures after EY may leave unknown protocol/native status requiring central reconciliation; no subsequent EB or automatic recovery follows them. Even a completely accepted clean observation leaves restoration_required=true because this coordinator intentionally does not restore.

The sequential child helpers retain their independently reviewed finite actions and transport/native budgets. EX does not add an overall subprocess wall-clock timeout or establish hard termination of uninterruptible kernel I/O. A missing completion ledger after a launch/transport exception is retained alongside the conservative result rather than fabricated as successful completion. Actual current phase, exclusive coordination and input freshness remain parent responsibilities; cached identity and lineage are snapshots, not endpoint queue proof.

## Independently exercised tests

`test-coordinator.py` executes the actual final coordinator's main function with task-private synthetic input trees and injected subprocess/parser/verifier modules. No real operational helper module is imported or executed. It verifies25 actual frozen input hashes before constructing synthetic data and rechecks source/pins afterward. No source file, predecessor capture or original helper was modified.

Normal and optimized Python each pass **306 checks across33 cases**, with byte-identical results. Cases include:

- Complete fixed successful order, with exactly one set, one EY and one EB post-read.
- Missing/changed pins, ordinary preparation failure and set-readiness failure before any set.
- Set wrapper nonzero/launch exception/strict-parser refusal, rejected result, manifest/count/Boolean-count/inventory/raw corruption: zero EY/post-read.
- EY-readiness/native/admission failure, seven malformed/stale/rejected proof variants and fresh-verifier refusal: zero post-readiness/EB.
- Post-readiness or EB wrapper failure and EB manifest/count/Boolean-count/inventory/raw/limit corruption: no accepted final workflow.
- Every retained result has zero automatic recovery/restore/retry, and restoration_required is true exactly once a set invocation was attempted, including an uncertain launch failure.

This campaign intentionally does not repeat the much larger FA/EY/native tests already qualified in their separate pinned reviews. Those parsers are represented by explicit host stubs here to test EX sequencing and failure handling; these synthetic objects are not claimed to be actual native receipts. No target, root, network, USB, key or native production operation occurred.

Run `PYTHONDONTWRITEBYTECODE=1 python3 -B reviews/coordinator-review/test-coordinator.py` and again with `-O` in the original retained layout. Temporary fake trees are under excluded `private/` and removed. The saved normal/optimized JSON and this review are sealed in `source-inventory.json`. Parent alone decides any target invocation using these exact hashes and the separate reviewed FA/EY readiness and phase contracts.
