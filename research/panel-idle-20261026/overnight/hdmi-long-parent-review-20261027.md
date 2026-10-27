# Independent parent review of the longer HDMI recorder

Reviewed 2026-10-27 UTC before target execution. Author: combined_onset_capture;
reviewer: root. Source SHA-256
`65aeae50409ad05532163072e118140d09c7eaf3437aabc5b3843a138ab5c2eb`;
tests SHA-256
`3eb3f0df946da03e5073000d2c12faf2605b99aa40a955bcdbc1ece2667251f4`.

The parent inspected the source and generated-contract approach and ran all20
tests normally and with `-O`; both passed. The earlier draft's metadata
validator would have rejected the exposed five-second smoke mode. That defect
was reported to the author, corrected before execution, and is now covered by
a nested smoke-runtime dispatch test. No earlier draft ran on the target.

The source pins its frozen HDMI ancestor and design before import. It keeps
the original acquisition machinery, explicit private mono clock, process and
binary identity guards, per-read map checks, pointer-chain checks, expiry and
cleanup. The one permitted map delta is monotonic growth of a single AVOC
heap high endpoint; the full original maps remain retained. The adapter
normalizes that one end section only after the full raw-map policy and all
sampled/provenance spans pass. Every other mapping and deviced map change
still fails. This is not a claim that heap contents are constant.

The sample-error writer and concatenation limits, remote final check and host
manifest validator all use1MiB. All sidecars must remain strictly below their
caps, and per-CPU bytes below4MiB with zero reported loss. The actual program_b
60-second maximum CPU bytes were1,347,316; simple threefold scaling is4,041,948,
close to4,194,304. A five-second smoke therefore cannot qualify180-second
capacity. A real longer run still must independently pass the capacity/loss
checks; this narrow headroom remains an explicit limitation.

Verdict: ready for one five-second passive, physically unobserved smoke under
the owner's current authorization. This is not a tested fault fix or a
physical-onset capture. A180-second mode implementation exists, but neither
its target duration nor its capacity is yet qualified by this review.
