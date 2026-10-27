# PQE policy and Home-exit investigation

This phase follows the independently verified [176-file observer-validation snapshot](onset-observer-validation-evidence-manifest.json). Earlier evidence and its source files remain unchanged. The panel fault is still unidentified; no permanent repair, prevention or physical recovery has been verified. Root remains host-assisted, and current physical picture state is unobserved.

## Content-dependent routes now reconstructed

The [kernel record audit](../tcon-research/pqe-kernel-event-records.md) establishes six tags produced into one PQE event queue. The [userspace consumer analysis](../tcon-research/pqe-event-userspace-consumer.md) reconstructs the matching ARM32 decoder and dispatch. Only return zero dispatches a record; nonzero returns including -11 resume polling. Thus the potential uninitialized bytes on a kernel error return do not become a fresh event in this recovered consumer. The actual dequeued event buffers were not captured.

The recovered tags drive DLSR classification, genre, HDR classification, object count, AI color level and GSR. The type-3 object count reaches QDDimming's per-vsync Weber-gain policy, which selects and ramps a raw gain clamped to 1..1023. In one conditional final-duty path this gain can feed a backend request. The nearest mapped base-QDDimming output boundary sends QD selector0x128 and an FRC write; its cache records the request before transport succeeds. The gain's numeric range is not a calibrated brightness scale, and no emitted-light measurement or fault correlation follows from these static edges.

The [independent GSR review](../tcon-research/gsr-npu-pq-edge-review.md) follows a different policy path. When its enable word is1 and a changed class is1..5, GSR selects a configured PQ index and reaches TDDataLoader's data-setting route through static vtable bindings. Its cache and queueing behavior can hide lower errors; the selected words are PQ indices, not established duty, voltage or power values. The active VideoEnhancer object must be dynamically bound before interpreting its live state; the existing QDDimming pointer is a different object graph.

## Deferred Home-exit behavior

The [Home-exit report](../tcon-research/newhome-exit-restore-path.md) resolves a previously open deferred flag consumer. A changed Home-off request can leave an exit flag for later resolution processing. That routine clears the flag before applying video/output configuration and can advance comparison caches before the final rate helper succeeds. The exact hash-gated disassembly and control flow received independent review. These are attempted reapplication and cache/error boundaries, not proof of a successful physical restore or a missed restore during the owner's blackout. Different tabs within Home are not automatically entry/exit transitions.

## Frequent FRC ioctl clarified

The [FRC6626 report](../tcon-research/frc-ioctl-6626-analysis.md) identifies the frequent eight-byte ioctl as a selector/result read ABI. It is not a series of setters. Its zero return can occur without a registered callback, a hardware transfer or a changed result. The raw retained trace and the strict observation interval have different counts, explicitly recorded. Parent review corrected two preliminary CFG mistakes before accepting the report: the actual output-copy arm is2cd4/2cfc, and the no-transfer Rosem branch returns without writing output (no selector echo). The current report and checker reflect these corrections; success is not panel-state evidence.

## Passive policy baseline: executed and reviewed

A new default-dry reader completed one accepted finite read of typed VideoEnhancer and QDDimming state after an earlier attempt timed out and was retained as incomplete. The [actual results report](pqe-policy-baseline-runtime-results.md) links both raw records and documents source revisions, independent review, guards and limitations. The accepted run took 0.77 seconds, retained all 240 requested memory bytes, and passed paired identity, mapping and pointer checks. It did not invoke event queries, getters, setters, driver controls or target code. Reading the transient ioctl stack buffer later cannot reconstruct past events and was excluded.

The live objects bind to RoseMVideoEnhancer, QDDimming and DimmingBackendRoseMQD. The observed GSR enable word was 0, Weber gain/target were 1023/1023 with count 0, and working/backend requested values were 236/236/236. Physical picture state was unobserved, reads were non-atomic, and final-duty branch gates were not all sampled. These values therefore do not establish physical brightness, output application or a causal exclusion of a policy across the owner's blackout.

## Additional content/statistics input resolved

The [Weber-input producer audit](../tcon-research/qd-weber-input-producer.md) combines the captured backend identity with the exact ELF slot relocation. It recovers 35 register samples, a count of samples unsigned greater than 14, FRC read selector `0x45238`, and a signed scaled object-count input to the existing Weber predicates. The local register wrapper has no-write success routes and discards the lower read status; the backend's overall return is instead the FRC read status. A nonzero backend return selects the calculator's direct 1023 fallback without updating the separate DimmingShare statics.

The live slot `+0x1c4` itself was not sampled: this is a static class-method binding against a captured class identity, not an observed call or slot word. Independent review corrected an earlier draft's stronger runtime-target wording. Per-call statistics, the shared skip flags and actual selector output remain unobserved.

## Final-duty zero hypothesis narrowed

The [final-duty branch audit](../tcon-research/qd-final-duty-branch-analysis.md) reconstructs ordered calculation gates at inner `+0x38`, `+0x450` and `+0x188`. It preserves exact wrapped integer arithmetic and the intervening virtual mutation hook. Crucially, the final signed clamps come after AutoPowerOff: the immediate backend candidate is clamped to `[51,1023]`, or `[12,1023]` for exact `+0x188 == 1`, on the normal sequential path. AutoPowerOff alone can produce zero, but that later clamp raises it before this backend call. These are raw scalars, not calibrated light units.

This weakens the specific explanation that this routine directly sends a zero candidate because a menu becomes sparse. It does not exclude other output/mute/maintenance routes, skipped or failed transport, controller state, concurrent changes or a damaged panel becoming dark despite a nonzero request. The captured baseline omitted the gates and most arithmetic inputs, so it does not identify the active formula branch at that read.

The immediate backend prewrites its requested-value cache before both transports, has no rollback, and skips identical later requests. A failed attempt can therefore suppress an identical later attempt. The first transport receives a pointer to a local scalar; the second reloads it, so equality of the two transmitted values is not proved by this bounded body. No such failure has been captured at the owner's blackout. This is a concrete recovery/retry question rather than an established cause or deployable fix.

## Type-0 DLSR route classified

The [base DLSR-class audit](../tcon-research/dlsr-class-pq-route.md) resolves its conditional picture-register read and shared-table selection into the existing PQ-index/data-loader route. It found no direct named duty, mute, TCON/FRC or panel-power primitive in that bounded function. Downstream PQ consumers remain outside that negative claim. Parent review corrected the combined MOV/MOVT read-register literal to `0x007c037c`; the helper now pins that construction. The public entry prewrites the class cache before downstream work, so an equal later class does not establish successful prior application.

## Review, preservation and next discriminator

The [actual baseline review](pqe-policy-baseline-independent-review.md), [follow-up review](pqe-policy-followup-independent-review.md) and [final-duty review](pqe-final-duty-independent-review.md) preserve the accepted scope and corrections. Hash-gated helpers reproduce symbol/instruction/relocation landmarks locally; full branch/formula interpretation remains manual CFG reasoning. Review of a helper or a hash does not prove a physical repair.

The phase evidence index is [pqe-policy-followup-evidence-manifest.json](pqe-policy-followup-evidence-manifest.json), created by the separate no-overwrite local snapshot helper. It anchors both previous snapshots, the reviewed reader archives, both actual baseline attempts, reports, reproducibility helpers and prerequisites. Mutable navigation and generated bytecode caches are excluded. Earlier evidence is not rewritten to adopt the new interpretations.

The most useful future observation is a physically timed tuple from object count through Weber gain, branch gates, working duty and requested backend value, synchronized with controller commands and fault-state samples. It must distinguish the persistent menu blackout with continuing audio from the separate brief Ugoos/playback loss with audio pause. No single cache proves the panel lit, and this specific route is only one candidate among dimming, timing/mute, maintenance, transport and panel-internal mechanisms. No recovery/control experiment was run during this follow-up analysis.
