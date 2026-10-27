# S95F reverse-engineering evidence index — October26 overnight

Start with [diagnosis-20261026.md](diagnosis-20261026.md). This is an unfinished diagnosis; no permanent blackout fix has been validated. Owner-observed physical states and later unobserved software baselines are explicitly separate.

The newly resolved automatic ten-minute warning is summarized in
[automatic-optimization-end-to-end.md](automatic-optimization-end-to-end.md),
with source links, countdown/producer flow and the remaining repair boundary.

The subsequent [ARM32 CLR syscall probe](managed-kernel-abi-probe/README.md)
completed with ENOSYS for both BPF and perf; that result is specific to the
tested compatibility ABI. Factory-transmit and notification-server follow-up
are recorded in [the follow-up log](notification-factory-and-compat-abi-followup.md).
The initial selector5/storage-only factory claim was rejected by independent
review: the actual serialized-node driver selector is16.

A later [live backend capture](factory-backend-runtime.md) closes the diagnosis
table/method pairing with44read-only bytes. The new
[route-coverage audit](../tcon-research/off-sensing-disable-route-coverage.md)
limits value6 to eligible new classifier notifications. The combined onset
observer is being corrected against the [review findings](onset-capture-review.md)
before any live smoke or physical-trigger test.

The [current phase record](backend-storage-and-onset-preparation.md) links the
corrected type2 NVRAM getter path, actual log/resource observations and the
observer's unexecuted review boundary.

The [new evidence snapshot](backend-storage-onset-evidence-manifest.json)
preserves this storage/backend phase without rewriting the prior snapshot.
Actively changing observer source/tests are explicitly excluded.

| Area | Reconstructible evidence | Important boundary |
| --- | --- | --- |
| Owner history | ../owner-observations-20261026.json; ../paired-capture/ | B0/B1 are physically confirmed black with changing rich software frames; later uploads do not time a current recovery |
| Actual hardware | owner-photo-manifest.json; ../tcon-research/owner-photo-board-map.md; hardware-hdmi-evidence.md | Ten source images fingerprinted; no physical connector pinout or identified failing component |
| Kernel acquisition | pull-kernel-image.py; kernel-image-manifest.json; kernel-slot-metadata.json; kernel-running-baseline.json | Read-only p6 Image, header/data CRC valid, full running banner matches, no live-text hash |
| Export reconstruction | recover-kernel-exports.py; kernel-export-index.json; build-kernel-export-view.py; kernel-export-view-manifest.json | 9,379 export names; artificial host-only ELF is not original vmlinux or a replacement image |
| Samsung kernel PM | kernel-runtime-pm-findings.md; kernel-runtime-pm.disasm | Proprietary busy count with bounded suspend wait, not a demonstrated blackout cause; one suspect observer read postdates failures |
| Native AVOC | trace-avocd-panel-mute.py; avocd-panel-mute-*.txt/json; ../idle-research/overnight-avocd-controller.md | Getter flags are intent/case, not physical mute; lower unmute errors can be discarded |
| Managed Home | matching-plugin-manifest.json; ../idle-research/common-mute-il-audit.md; ../idle-research/overnight-mute-output-chain.md | Actual Common/Page IL and loaded native-image variants preserved; no unknown tab semantics invented |
| Verified Home callback | ../idle-research/newhome-ui-native-arguments.md; matching-avoc-managed-manifest.json | Registration uses name/callback pairs; SetNewHome is0xc1524, not the temporarily misaligned0x3d5ac attribution |
| Home output policy | ../tcon-research/newhome-qd-dimming-policy.md; ../tcon-research/newhome-frc-output-policy.md; ../tcon-research/newhome-tcon-vfreq-backend.md; trace-newhome-frc.py; newhome-frc-*.json/disasm | QD dimming virtual call is a stub; separate FRC selector3 changes rate policy, not a proven sparse-page trigger |
| Independent correction audit | home-output-independent-review.md | Records rejected callback/rate interpretations, real frame-mode mute bracket, hidden errors and complete fault thresholds |
| Actual output gate | ../tcon-research/overnight-panel-mute-gates.md | Stock unmute-zero reads live QDF mute status and can re-send zero; no recovery yet tested |
| QD transport and mute writers | ../tcon-research/qd-command-transport-failure.md; ../tcon-research/qd-mute-writer-map.md; ../tcon-research/qd-mute-concurrency.md | Final zero may skip before I2C/mutex; temporary bracket is not atomic; finite immediate-writer inventory only |
| Transport independent review | qd-transport-independent-review.md | Corrected broader skip gates, handshake byte selection, Resume ordering and decoder integrity before live control |
| Command-gate reference | ../tcon-research/qd-command-gate-reference.md | Decision order and locking/no-lock read differences, with explicit output/return semantics |
| Sensing setter ABI | ../tcon-research/qd-sensing-entry-callers.md; ../tcon-research/qd-sensing-entry-callers-reproduce.py | Exact ioctl operation9/15 and QDF callbacks; service-plugin path separately audited, no onset attribution |
| Daemon maintenance policy | ../tcon-research/deviced-off-sensing-policy.md; ../tcon-research/deviced-el-sensing-policy.md; matching reproducers/raw | Power-policy and IPC paths; real PPI enable/disable distinct from bookkeeping; no Home client or blackout attribution |
| Maintenance IPC and power contract | ../tcon-research/maintenance-ipc-client.md; ../maintenance-ipc-client-reproduce.py; ../tcon-research/deviced-power-state-contract.md; ../tcon-research/pm-lock-expiry-notifier.md; matching reproducers | Request flag versus power-off/start; enum3=standby; nominal15-minute lock with conditional EL-stop; popup timing/caller still unknown |
| Content/duty policy | ../tcon-research/qd-content-duty-policy.md; ../tcon-research/qd-content-duty-reproduce.py; paired-content-duty-log-extract.json | Arithmetic ramp,0x128 request and failure-insensitive caches; no measured panel luminance or timed sparse-page rule |
| AutoDim upstream and actual runtime object | ../tcon-research/qd-autodim-upstream.md; ../tcon-research/qd-runtime-observer-map.md; runtime-dimming-baseline.md; runtime-dimming-state-20261026T112858Z.json | Client/provider+0x98 match; one40-byte read finds QDDimming and rawAutoDim0; physical state unobserved, not an onset capture |
| Actual base QD output and duty cache | ../tcon-research/qd-active-base-duty-path.md; matching reproducer; runtime-control-state.md; runtime-qd-duty-cache-20261026T115305Z.json | Live RoseMQD vptr/slot/cache resolved; cached207 equals working207; pre-I/O cache can hide retry after error, but no failed transaction/blackout observed |
| Daemon object-state memory | ../tcon-research/deviced-runtime-observer-map.md; runtime-deviced-state-20261026T114500Z.json; runtime-control-state.md | Legacy selected objects and three child vptrs validated; local state0/power1; not panel state or active-timer proof |
| Manual Pixel Refresh UI | ../idle-research/menu-screen-optimization.md; ../idle-research/menu-optimization-probe/; matching-optimization-ui-manifest.json | Exact buttons through managed/native modes0/1; five bounded hash-checked methods; automatic60s/10min prompt remains unidentified |
| Self Diagnosis resource follow-up | ../idle-research/selfdiagnosis-optimization-candidate.md; ../idle-research/scan-selfdiagnosis-resources.py; ../idle-research/selfdiagnosis-resource-scan.json | Four additional files hash-checked; Screen optimization/Pixel Refresh labels found; no verified automatic-countdown implementation or blackout attribution |
| Runtime/control independent review | runtime-control-independent-review.md | Parent-preserved read-only reviewer messages; corrected selectors/gated calls; steady-state suppression distinguished from failed retry |
| Actual monitor latch/counters and repeatable reader | runtime-monitor-baseline.md; qd-monitor-baseline-20261026t122239z.json; snapshot-qd-runtime.py; test-snapshot-qd-runtime.py; ../tcon-research/qd-monitor-runtime-map.md; matching reproducer |356bytes/20matching pairs; ERR recovery2/latch1, no current physical observation; exact conditional restart clear resolved; persistent-only access prevents fallback staging |
| RoseMQD cache lifecycle | ../tcon-research/qd-rosem-cache-lifecycle.md; matching reproducer | PIC anchor is not a shared backend object; file initializer-1; bounded ctor/dtor/init/resume checks provide no known standby/resume cache rearm, not a global writer census |
| Monitor lifecycle callers | ../tcon-research/qd-monitor-lifecycle-callers.md; matching reproducer | Normal monitor-start directly requests enable/restart; later QD invocation may clear bookkeeping; current owner-event reachability and physical recovery unproved |
| Kernel observer feature boundary | kernel-observer-features-20261026T123326Z.json; kernel-bpf-presence.md; matching reproducer | Static trace events available; config/BTF/kallsyms/module-section paths unavailable; call-base zero is normal ABI anchor, event-output -ENOTSUPP limits only that route |
| Vendor cache-print debug boundary | ../tcon-research/qd-cache-dump-surface.md | Exact numeric-input helpers return exit0x99; cache-print selector0x30 and mutating selectors are dormant; normal callback is not a gate observer; no invocation or helper modification |
| Lifecycle/observer final review | lifecycle-observer-independent-review.md; lifecycle-observer-evidence-manifest.json | Corrected truncated early scan, dormant debug-cache reachability and PVCC load address; denied native launch gives no syscall result; final bounded review has no blockers |
| Exact automatic warning and countdown | ../idle-research/tv-viewer-optimization-resource-match.md; ../idle-research/extract-tv-viewer-optimization-text.py; ../idle-research/tv-viewer-optimization-text.json; ../idle-research/tv-viewer-automatic-sensing-notification.md; ../idle-research/tv-viewer-off-sensing-timeout-flow.md; matching reproducer | Exact owner text; ongoing ID0f, intended one-minute/60-tick local expiry auto-requests mode0 off-sensing; not an observed owner callback/cycle or sparse-menu cause |
| Automatic optimization phase record | automatic-optimization-end-to-end.md; automatic-optimization-evidence-manifest.json | Reconstructed producer/UI/service flow and passive13:29..13:53 values; no configuration change, native patch or verified repair |
| Notification producer and stored-key contract | ../tcon-research/app-control-off-sensing-producer.md; ../tcon-research/deviced-off-sensing-notification-trigger.md; ../tcon-research/qd-display-state-query-contract.md; matching reproducer | App-control enum presentation and reinforce route; GetQDDisplayState can acknowledge results and was not called; direct key reads preserve unobserved stored values |
| Factory off-sensing period candidate | ../tcon-research/factory-off-sensing-test-period.md; matching reproducer; optimization-factory-period-baseline-20261026T134120Z.json | UID506e/item200802 value6 predicate; current service0 with absent named key; no proved all-route disable or setter apply semantics; no change |
| Real power sequence and physical latch chronology | ../tcon-research/qd-power-control-hardware-sequence.md; matching landmark checker; monitor-latch-physical-timeline.md; power-notification-independent-review.md | GPIO/reset plus transitive recovery commands; incomplete lower error propagation; visible Apps already had history latch1; unsampled gap prevents terminal-action exclusion |
| Native syscall availability attempt | kernel-abi-probe/README.md; assembly/binary/build manifest/runner/tests; result-20261026T124321Z.json | Temporary helper launch denied,0result bytes, accepted=false and cleanup confirmed; BPF/perf syscall and private QDF gate availability remain unknown |
| Upstream/contract independent review | upstream-contract-independent-review.md | Corrected two PC/dataflow errors before integration; raw curated versus generated evidence distinguished; non-atomic runtime limits preserved |
| Policy independent review | policy-independent-review.md | Rejected timer, slot, caller-absence and terminal-action interpretations; corrections and transcript lineage |
| Controller firmware boundary | ../tcon-research/qd-firmware-acquisition-map.md; samsung-official-firmware-archive-metadata.json; samsung-official-*-info.txt; samsung-official-T-RSMFAKUC-0090-msd-prefix.bin | F77 controller payload not recovered; official archive metadata/prefix only, no flashing or exact installed-image match |
| Broader gate lifecycles | ../tcon-research/qd-command-skip-lifecycle.md; ../tcon-research/qd-suspend-state-lifecycle.md | Sensing/suspend/status/power paths can suppress commands; no live cache forcing or onset attribution |
| Runtime gate constraints | qd-gate-evidence-constraints.md; existing-gate-sensing-log-extract.json; gate-log-baseline-20261026T055728Z.json | Actual query constrains gates only at matched checks; historical skips near lifecycle events; no direct RAM observer available |
| Unmute PVCC guard lifecycle | ../tcon-research/qd-unmute-pvcc-guard.md; ../tcon-research/qd-unmute-pvcc-reproduce.py; ../tcon-research/qd-unmute-pvcc.raw.disasm | Static lifecycle routing, not a live flag value; flag setter can cause real power-on and was not invoked |
| Offline I2C evidence decoder | decode-qd-trace.py; test-decode-qd-trace.py; qd-trace-decoder.md; passive-black-*.qd.json | Sixteen integrity tests; separate mute/frame, maintenance and dimming focus lists; no physical-state inference |
| Historical fault | historical-errdet-decode.md; ../tcon-research/historical-fault-recovery-timing.md; ../tcon-research/monitor-task-cadence.md; errdet-*.disasm.txt | QD bit4 RT Protect; three raw samples/two100ms waits; fault GPIO drives reset; no current-onset alignment |
| FRC/output | ../tcon-research/overnight-frc-output-policy.md; frc-cached-status.json; frc-irq-cached-baseline.json | Cached baseline, not fresh physical-black proof; actual counter path frc/frctest/irq_status |
| DT/GPIO | display-devicetree.tar; gpio-devicetree.tar; gpio-control-map.json; ../tcon-research/overnight-gpio-dt-driver-chain.md | Logical GPIO wiring only; private getters can request/direction/read/free, so were not invoked |
| Finite passive trace | diagnostic-trace.py; summarize-trace.py; passive-*.trace/summary.json; helper-validation.* | Static events available, function/kprobe/uprobe absent; validation lineage qualified in report |
| Next observed recovery/entry tests | next-observed-session.md; unmute-zero-capture.py; next-unmute-zero.review.sh | Combined one-zero probe is dry-run prepared only, no power or mute-one, no automatic retry |
| Binary provenance | analysis-input-manifest.json; matching-driver*.json; matching-plugin-manifest.json; matching-avoc-managed-manifest.json; matching-display-panel-manifest.json; matching-display-panel-backends-manifest.json | Original43 copied matching files plus the two framework System assemblies and display-panel PPI bridge/backends fingerprinted; kernel and photos separately fingerprinted |

The external QDF microcontroller firmware and its internal emission/protection algorithm have not been acquired. The photos and family repair guide are not a complete schematic. No kernel/factory/protection patch, panel power change or autonomous recovery loop was deployed. Root remains host-assisted.
