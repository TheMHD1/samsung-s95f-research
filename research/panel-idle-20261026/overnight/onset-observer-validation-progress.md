# Onset observer validation: current continuation

This continues the historical [backend/storage phase](backend-storage-and-onset-preparation.md) without rewriting that phase's 43-file snapshot. The observer is no longer wholly unexecuted: four passive short attempts and one 90-second capacity run have actual artifacts. A permanent repair, physically observed onset, recovery, prevention and untethered root remain unverified.

## Why this work matters

The existing owner-confirmed black captures show changing software frames and continued compositor activity while physical light is absent. The outstanding question is what changes across the content-dependent transition from populated Apps to a sparse page: a software control request, a display/panel-controller condition, or another downstream failure. A later unobserved software sample cannot answer that question. Repeated latched TCON-off messages cannot be counted as repeated fresh off actions. The impact damage is owner-reported as no larger than a thumb; a hardware fault can remain possible even when most software calls return success.

## Actual validation, including failures

- [First smoke: UEP launch rejection](onset-smoke-uep-launch-failure.md). The platform rejected execution of an unsigned staged script file before acquisition. The original failure and cleanup are preserved. The subsequent launcher uses the existing installed shell with exact hash-verified script data as its command argument; no policy change was made.
- [Second smoke: partial capture](onset-second-smoke-partial-result.md). Collection occurred but cleanup stderr, sampler latency and marker representation exposed implementation defects. Its record remains rejected; improvements were made in a later separately archived revision.
- [Third smoke: technical acceptance](onset-third-smoke-accepted.md). A five-second capture passed actual trace, sample, source/identity, log and cleanup checks. No physical observer was present, so it is not a panel-state or repair validation.
- [Ninety-second capacity run](onset-capacity-90s-result.md). All 107,587 trace events were retained and the measured files fit their limits. The host nevertheless rejected diagnostic completeness because one ioctl started 4.038 ms before END and its return lay outside the recorded interval. That missing return is not evidence of a hang or panel causality.

All actual attempts retained zero human picture annotations. None sent remote keys, changed display/power/factory settings, restarted services, patched firmware/kernel code or changed execution policy. Authenticated cleanup was checked for every attempt. Root remains host-assisted.

## Offline controller-traffic result

The [capacity I2C report](capacity-20261026t1648.onset/offline-qd-i2c-analysis.md) and its raw-derived JSON identify 44 structurally complete QD transactions. Nine exchanges match the already disassembled stock power-level getter, approximately ten seconds apart. All Linux transfers returned their requested message count, which proves neither controller acceptance nor physical emission. None of these captured QD transfers used the known mute, frame/VRR, sensing, dimming, low-power or screensaver-control selectors. This is an inventory of this unobserved interval, not proof that such commands cannot cause the owner's fault.

A tcon-monitor read of selector 0x0c returns raw `00170017` at about 21-second intervals. The subsequent [exact module analysis](../tcon-research/tcon-monitor-selector-0c-analysis.md) maps this to `QDFTcon_GetExtTempPcb`, splitting the reply into two u16 output fields (23 and 23). Its symbol names support an external PCB-temperature getter; units, calibration, sensor placement and any relation to emitted light are unproven. These are not named fault counters.

An independent completed-ioctl inventory also found a repeating 0/-11 return pattern on `/dev/sdp_pqe_dp`. [Exact kernel disassembly](../tcon-research/pqe-query-event-analysis.md) resolves that request as a kernel event dequeue: -11 is the empty-queue branch, not a panel-off error. The event payload was not captured, so its contents and userspace interpretation remain unknown.

## Capture correction and actual validation

The revised observer preserves START..END as the physical-observation interval and continues tracing for a bounded tail. In-window calls may pair with returns in that tail; unresolved in-window calls must still fail completeness. Calls wholly in the tail must be reported separately so stopping at the tail does not create the same boundary problem. Scope, process identity and lifecycle checks must continue through the tail. The new exact source/tests were immutably archived and independently reviewed before one additional live five-second run. The [drain smoke report](onset-drain-smoke-accepted.md) records technical acceptance and a real wait-vblank ioctl that began before END and returned 1.140 ms after it. Independent raw-artifact review confirmed the real crossing return, all seven sidecar hashes, event accounting, identity/configuration/sampler/log gates and cleanup. Physical state remains unobserved. This verifies a capture fix, not a panel fix. The historical rejected capture remains rejected.

## Remaining repair requirements

An observed visible-to-black capture, or a separately observed finite recovery test from a confirmed black state, is still needed. Software screenshots and status replies must never stand in for emitted-light observations. The next repair decision depends on correlating actual controller commands, internal fault/state changes and physical onset. Controller MCU firmware has not been acquired or reconstructed. No validated permanent blackout fix exists, and the physical impact line has not been repaired.

## Evidence preservation

`snapshot-onset-validation.py` verifies all 43 historical phase files unchanged, pins the seven immutable source/test review revisions, verifies their exact six payloads, and preserves the five actual attempt records and raw/derived artifacts. The new `onset-observer-validation-evidence-manifest.json` is exclusively published; it does not rewrite earlier snapshots. Inclusion of an archived revision is not live clearance or physical diagnostic eligibility. The snapshot helper and PQE route interpretation both received independent read-only review.
