# Passive post-END-drain smoke: technically accepted, physically unobserved

## Frozen source and review

This run used observer SHA-256 `17a30cbee3d0d6ce5d4b23ffd1333b359b124bb4c1caaac253e1a6bc0f9999d5` (94,422 bytes), tests `ab6c4307d611d00e886d042ec855a7dbae21e76db65673d039811cc8f5872970` (43,043 bytes), preserved in `onset-review-archives/17a30cbee3d0d6ce-ab6c4307d611/`. Independent review passed all 35 offline tests, Python compilation, and shell syntax for generated 5/10/85/90-second scripts, and cleared exactly one new five-second passive smoke. An in-memory replay of the earlier rejected trace tested a hypothetical post-END return; that replay did not alter the original trace and was not real runtime evidence.

## Actual run

The unique label is `smoke-20261026t-drain1`; actual host execution was 2026-10-26T16:59:31.337575+00:00 through 2026-10-26T17:00:08.618524+00:00. The exact staged 18,413-byte script hash was `c06d561e790ea52b42d92ff064ec119d6732b07cedd1c1997eb7159bbe70e3fc`. It used `--seconds 5 --smoke-unobserved --run --reviewed` and closed input. No observer annotation, remote key, display/power setter, factory operation, service restart or kernel/firmware change occurred.

The result is `accepted=true`, `technical_capture_complete=true`, `diagnostic_eligible=false`, `cleanup_verified=true`. Physical picture remains unobserved and no absence claim is supported. The raw record and sidecars are under `smoke-20261026t-drain1.onset/`.

The exact collector-owned trace markers are START 55594.878489, END 55600.056919, DRAIN_END 55600.163817. The observation interval is 5.178430 seconds and the drain is 0.106898 seconds. All 7,230 retained events equal the written and decoded counts; 6,196 are inside the observation interval and 107 in the drain. No AVOC lifecycle change, unrelated scoped syscall, duplicate ambiguity or unresolved capture-window call was reported. All seven file hashes/sizes validate against the collector manifest.

Crucially, this actual run exercised the previously missing case: AVOC TID 1011 entered fd 33 (`0x21`), request `0xc010643a` / DRM wait-vblank at 55600.053573, returned 0 at 55600.058059, and crossed END at 55600.056919. It is preserved as one in-window pair with `return_after_capture_end=true`. The return was recorded 1.140 ms after END, with total call duration 4.486 ms. This proves the bounded tail captured one real crossing return; it does not prove physical light output or guarantee that future calls always return within 100 ms.

There were 43 wholly drain-only pairs, excluded from the physical interval and separately reported. There are 2,637 total retained completed pairs, including excluded prelude/drain pairs; do not confuse that count with the capture-window inventory.

The sampler recorded 23 monitor and five QD rows, approximately 4.435 Hz and 0.895 Hz over their respective sampled spans. All 116 dd operations have complete-success summaries. The vlog contains 29,306 ordered records covering 55592.000..55601.996 with maximum detected gap 0.010 seconds and natural exit 0. These validate instrumentation continuity, not panel emission or absence of a fault.

Authenticated cleanup must be assessed from `cleanup.json`, not the launcher exit alone. The recorded cleanup completed with empty stderr, exit 0 and `0\nCLEAN\n`; private tracing and temporary collectors were removed. The global trace state was off at that check. No further run or repair follows automatically from this smoke result.

Independent review of the actual run confirmed the raw three-marker ownership, real crossing return, seven sidecar hashes, exact label-specific script regeneration, stable 23-TID and 44-FD endpoints, source/mapping/pointer checks, sample/log gates, global trace baseline, and authenticated cleanup. No blocking discrepancy was found. This review does not authorize a physical-state inference.

## Remaining limits

A physically observed Apps-to-black transition is still required to classify the fault. A fully black-state recovery test also requires a physical observer. The 90-second buffer-capacity result and this five-second boundary validation are complementary checks; neither is a validated permanent fix. Calls genuinely unresolved at the bounded drain cutoff still cause rejection rather than being silently treated as successful.
