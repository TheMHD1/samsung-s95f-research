# Independent synchronized-onset wrapper review

Scope: final wrapper manifest `8cb73c48ff6ef21e13e563efc96b59aa7f6353054d3f433cd3962d24523515ff`, not the earlier candidates. Offline read-only source/fixture review and local fake-root/parser tests only. This reviewer performed no root, TV, USB, UI, power, reset or network operation and changed only this review document.

## Finding and execution boundary

No material new source defect was found in the final bounded wrapper. It is suitable for one centrally coordinated invocation **conditional on a valid parent-authored readiness decision for the exact device instance and first-header premise**. A successful census of the existing device address does not supply fresh-enumeration history, continuously absent holders, endpoint queue state or receive-path liveness. An unknown prior vendor-OUT phase remains a stop condition for the parent decision. This review does not convert the metadata qualification into permission to assume a clean parser phase.

The wrapper requires exact manifest/readiness digests before loading root transport. Readiness has exact schema/fields, accepted/unbound/no-holders booleans, matching boot/sysfs/node/descriptor/configuration identity, and an explicit closed-world lineage statement while `endpointQueueProof` must be false. Evidence paths/hashes inside that decision are provenance references; the runner does not independently read or verify those referenced evidence files. Their adequacy is therefore an explicit central review responsibility, accurately disclosed by the README. The shape and digest checks are not a proof of the premise.

Native payload bytes are validated and retained in memory before dispatch; they are not later reread for upload. Native C#/parser/checkpoint and inherited passive wrapper/root adapter are hash pinned. The native remains the single vendor-USB owner. The Python wrapper adds no UI action, reset, recovery, telemetry enablement, ftrace, VLOG, forced collector or automatic retry. The native alone owns its one first-full-clean-cycle Left down/up intervention.

## FD census: corrected stock output and actual pipeline

The initial apostrophe-only ENOENT classifier was incompatible with the retained actual target line, whose opening character is ASCII backtick and closing character is apostrophe. The final classifier accepts either apostrophe or backtick opening, requires apostrophe closing, exact numeric `/proc/PID/fd/N` and exact ENOENT suffix. The real retained target fixture includes `character special file|1:3`, `fifo|0:0`, and the backtick/apostrophe diagnostic. Host tests now exercise those actual bytes rather than only a generated approximation.

The failed parent qualification 05 remains a failed ordinary metadata request, with no completed census or vendor I/O. Its awk/transport escaping root cause is not established merely by the escaped stderr rendering. The final classifier uses string operations and `sprintf` for quote characters; both its awk source and generated census pipeline have zero backslashes. Tests execute the exact command-substitution and shell-quoted pipeline with local fake stat data, including the trailing-newline case. Thus the earlier `sh -n`-only blind spot is addressed by actually running local awk and shell code.

The census has at most 4,096 process directories and 32,768 FD operands, one batched `stat -L -c '%F|%t:%T'` call under `LC_ALL=C`, and exact character-device major/minor holder comparison. Alternate device-node names are covered by rdev rather than filename matching. Numeric ENOENT churn is counted; permission/other diagnostics, holders, inconsistent extents and unexpected stat failure classes refuse. The default unmatched glob is not credited as a numeric disappearing FD. Identity and binding checks repeat after the census. These checks remain non-atomic snapshots; intervening holder races are not excluded.

I read the retained corrected target qualification 06: 11,283 operands, one exact ENOENT, zero holders and zero other errors, target uptime 167361.35 to 167361.95, host elapsed 0.71153 seconds. This qualifies the final census's actual target syntax/output and observed timing. It is not a positive USB endpoint or enumeration test. Full census commands have separate deadlines from native execution; the immediate execute command repeats identity/unbound checks without a full census. The measured census margin is therefore not silently charged against the 20-second native observation plus transfer completion/7-second worker join.

## One-shot orchestration and evidence retention

The fixed native startup/self-test commands, three payload inventory and exact modes/hashes are checked before execution. There is one `--execute` dispatch, with inflight/unknown recorded before it. Root45/host75-second transport limits, 8,192-byte command cap, 65,536-byte response cap, 24,576-byte native stdout and 2,048-byte stderr caps are retained. These remote limits do not create a new native kernel hard deadline.

The pinned root adapter saves raw transport responses before validation. The wrapper saves its execute envelope before framing and native bytes before JSON interpretation. Successfully parsed retained raw windows are saved before postcheck or cleanup. If framing/key/schema interpretation fails, original envelope/native bytes still remain, even where separate raw windows could not be safely derived.

Cleanup requires strict transport acceptance, consistent native exit, ReadyForHeader, released/closed, empty stderr, a successful ordinary postcheck and exact five-file integrity/inventory. Any partial/failed interpretation retains `cleanup_required=true`, performs no retry and makes no accepted result. Cleanup failure can be partially destructive, which the README correctly distinguishes from guaranteed complete retention. Post-census failure does not erase already saved native/raw evidence.

## Transport, trial and physical conclusions

The parser reuses the exact inherited transport contract while separately validating key state and cycle-one baseline. It keeps the trigger baseline as a retained duplicate without adjusting global I/O counters, checks timing/order and down/up success, and rejects attempted-key failures. Trial qualification additionally requires completed R coverage overlapping or after Down begins; an observer's later worker-join end time cannot manufacture USB observation coverage.

Valid unarmed transport may be cleaned up and retained with `trialQualified=false`, `intervention_not_armed`, and native exit1. Successful key call/return is not compositor event receipt. Transition brackets use full OUT-before/IN-after intervals, remain conditional on reply freshness, and do not establish physical light onset or key causation. The wrapper/parser consistently retain false UI-receipt, physical-picture and causality claims. No hidden second key, wake, navigation loop or reset repairs a failed native trial.

## Offline checks independently run

* `python3 -B test-runner.py` and `python3 -B -O test-runner.py`: both PASS, 1,305 checks, 386 generated shell syntax checks, maximum command 7,196 bytes, fake native invocations only, zero target operations. These also execute standalone awk and the exact local fake-stat pipeline.
* `python3 -B test-parse-result.py` and optimized equivalent: both PASS, 113 checks, 67 rejected mutations, four hash-pinned original fixtures, zero root/network/target calls.
* Local `build_manifest` reproduced the exact reviewed digest, checked frozen dependencies/checkpoint and captured all three native payloads, 67,735 bytes total. No root adapter was loaded by that operation.

## Proposed Apps-selected initialization: separate source assessment

No source requirement in the unchanged fixed MODE2 helper restricts it to an already black panel. It sends one fixed operation41/mode2 ioctl, has no mode argument/retry loop, closes its descriptor, and classifies return zero only as `kernel_return_zero_only`, not action acknowledgement, recovery, physical light or cleared protection. The black-panel scope belongs to the existing recovery quickpath's experimental intent and must not be silently rewritten or invoked for a different purpose.

A new explicitly labeled experiment may reuse the reviewed helper and safe constituent navigation/public-getter functions for one Apps-selected initialization, while preserving the original recovery quickpath. Record the initially lit ScreenSaver and cached Apps separately, establish the normal calibrated Apps/header-focus context, and retain fresh public reject checks. Those getters are rejection signals, not a complete maintenance or physical-state proof.

A passive sysfs-only monitor can overlap the one MODE2 invocation without becoming a vendor-USB owner. Require the actual old instance's disappearance and a new configured instance/identity, rather than inferring enumeration from device-number/inode age or a missing dmesg line. Then obtain fresh unbound/census metadata and make the conditional closed-world no-intervening-vendor-OUT decision before any vendor header. An absent reset/re-enumeration edge or unknown phase stops this path; it does not justify a second initialization or header retry. No reviewed source establishes an I2C-all2 prerequisite for this USB phase decision. Reset return zero alone cannot supply freshness or liveness.

## Exact input pins

| Artifact | SHA-256 |
| --- | --- |
| Wrapper manifest | `8cb73c48ff6ef21e13e563efc96b59aa7f6353054d3f433cd3962d24523515ff` |
| run-once.py | `2e7916110354d6ab3449c940c404be572e43aa425436556a6532d4498994e53f` |
| test-runner.py | `a4b99ba0b9829cf51938c17fbeda5a8040f2a0f6ef38a220a1bc540b8670ee3c` |
| README-wrapper.md | `af9609cf1463ef5024dbc4d2bc812aceecc2a246917c785f0eb31cc4f49329b7` |
| parse-result.py | `c2a653fa8ce07f18c3e817103228d7d0840a92a6e83ed44a4c8f968e856f3b06` |
| test-parse-result.py | `2b10f8af96452e59d0eea43b427a6b53a02cbbd8959fe12276b1f78af53fb308` |
| Native host checkpoint | `2eb6f75ac69b299eb55abb134df5fd6258bc032b8aa0d3fc7c56b195748b6a5a` |
| Actual stat diagnostic fixture | `df9ca13c2d7fa58897e0292519cbf2034d9f8b8b0a8e49b51e26dd8d14e702fe` |
| Corrected actual census 06 text | `0b4cd5020370ab5b962d16b73b0b279c9e2170f7f7d97d18bb6e7f17b1830f95` |
| Corrected actual census 06 summary | `32cc9935a47e40dda602a511128b0f6e1ea0abe42f316fa7a2a4d7644e47992e` |

This review supersedes no earlier scientific outcome. It reviews only the corrected wrapper and the separately stated initialization proposal; prior failed candidates and rejected trials remain failed/rejected.

## CA evidence-specific assessment after experimental initialization

The parent subsequently supplied completed CA initialization evidence. I read `onset-preparation-20261028ca/initialization-01/central-runner.py`, its intent/summary/native MODE2 outcome and cached lifecycle text, qualification07 identity, qualification08 census and the parent phase decision. All seven entries in `phase-evidence.json` matched their retained file hashes at this check.

The observed lifecycle is concrete: device53 disconnect at 167477.977815..167478.004197; new device54 high-speed enumeration at 167479.546928; matching 04e8:2001/revision2.50 and configuration1 at 167479.695389. It is not an inference from an old device-node creation timestamp. Qualification07 binds device54, bus7, node major/minor `bd:335`, the exact expected descriptor digest, configured/authorized/active state and interface2 alternate0/class ff/subclass00/protocol00. Qualification08 successfully repeats the cached identity/unbound checks and samples 10,988 FDs with zero ENOENT/holders/errors at target uptime 167499.36..167499.87 (about0.51 seconds). These observations satisfy the fresh-instance and sampled ownership parts of the previously reviewed conditional route.

The recorded central initialization contains exactly the two normal Up pairs, cached Apps/CSFS checks, public reject checks, one unchanged stock MODE2 helper, then cached USB lifecycle reads. The MODE2 result is accepted and cleanup-confirmed but explicitly does not infer action acknowledgement or physical recovery. The initialization record reports zero vendor bulk transfers. The parent reports that no other vendor OUT occurred in its serialized lineage after device54 configured. This is the relevant bounded ledger premise, not proof about every privileged actor or endpoint queue. The parent also reports the owner's post-initialization confirmation that populated Apps is visible; that report belongs in the pre-dispatch baseline record, separate from RT state and UI event-consumption evidence.

One precision was sent to the parent: completion of the same stock MODE2 action may include its I2C tail **after** USB enumeration. The phase narrative should include that reviewed tail plus later cached metadata, rather than literally asserting that all completed activity since enumeration was cached reads. The reviewed BS source gives no known edge from that I2C continuation/retry into host vendor bulk or vendor parser phase. This wording correction introduces neither an all-I2C-return2 gate nor a new queue-state proof.

On these concrete records, no additional source-based obstacle was found to the parent's explicit conditional first-header decision for device54, with the unchanged wrapper's fresh prechecks and no-retry rules. The remaining callback-executed/state-store/submission assumptions stay exactly the BS limitations; configuration1 is not positive proof of an active12-byte receive. A first native AlreadyFaulted/unarmed result remains a valid transport counterexample with no key workflow; it must not trigger another reset to force the intended initial state. This assessment adds no target operation.

CA evidence pins at the check:

| Artifact | SHA-256 |
| --- | --- |
| phase-decision.md, before any subsequent parent wording revision | `43db0d12a9a255c8ff224215ac837ad29acb5eabcb4e66922058ae03cbfc6b86` |
| initialization-01/lifecycle-after.txt | `f8756ee9342efaff8bf1820fd76ec7d13d0e412a8209629720b8d9a3117a7dc5` |
| initialization-01/summary.json | `b7b676ed5e898bf90763c6ddc0631ad0d4538033b74d30885e73e1b080d33789` |
| initialization-01/mode2.json | `f21c99a23463f15a19596e2790ccda2646187b2c384d376c58ebeb6adbfc6140` |
| identity-qualification-07.json | `720ad08670adb26728bf3b82922d07084e84bc9b4afa8044d99d95d08085a740` |
| census-qualification-08-summary.json | `0e57459453471bd7bd76d5043dbeb2621be70f25a271259ce1bcb8b0c218197c` |
| Retained BS phase review | `9a399ef961f1e126d2c25df39cd0f1d7c2307c7d06cda4e307b5d96ac2626ce5` |
