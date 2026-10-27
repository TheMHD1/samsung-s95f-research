# Decision for one corrected finite control run

Root decision, 2026-10-27. The owner authorizes unattended TV tests, reversible controller diagnostics and more intrusive changes if necessary, while requiring avoidance of bricking. This decision permits one already-reviewed volatile finite logger control only; no flash, protection suppression, reset, automatic UI change or retry.

## Conditional protocol lineage

The independent `control-v2-lineage-review.md` establishes that the detached v2 managed execute child did not execute under the ordinary private-root-stage/no-unrecorded-remover-or-replacement assumption. The decisive fact is absence of both native output files, which must be created by the shell before exec. Failure to create either prevents exec; success leaves those files unless an actor removes them. No recorded command, supervisor or execute-path source removes them. Earlier supervisor marker failures alone are not decisive because the old script was set-u.

The complete known session census since D6 is staging/self-tests, the rejected launch and read-only polls, read-only metadata/library copies, a marker-only qualification, and ordinary Apps prepare/send/cleanup. Subagents report no independent controller calls. No other controller USB transfer or privileged remover is evidenced. This supports conditional carry-forward of D6's accepted ReadyForHeader boundary, under normal exclusive-session assumptions. It does not prove immunity to unknown privileged actors or an unrecorded USB client.

Fresh `prequalified-smoke-metadata.json` on the same boot confirms the old stage remains root:root0700 with exactly its four inputs, whose hashes match the guarded launch. The USB device is active at address45, vendor interface unbound; fuser emitted no holder or diagnostic, but its combined no-holder-or-error classification is not treated as a historical proof. Old stage is preserved unchanged.

## Selected action and limits

Use `../managed-usb-secondary-logger-onset-qualified/run-once.py` with aggregate SHA256 `aa4fc99a5cd22f86736e49487322b1c6aa6996eae482c8fda3a1971049b386d6` for one fresh private stage. Independent source review found no additional unsafe branch, native bytes unchanged,19orchestration tests and85native tests pass. Coverage gaps are explicitly documented. One detached dispatch only; retain actual process handshake and diagnostics. No UI command during this control. Native performs only its fixed logging-gate operation, with a20second observation interval and priority restoration. If pre-arm status is unsuitable, preserve its bounded rejection. If launch/protocol state becomes ambiguous, do not retry, reset, signal or send further headers. No physical picture result can be inferred while the owner is asleep.
