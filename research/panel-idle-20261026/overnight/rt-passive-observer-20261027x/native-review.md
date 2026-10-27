# Passive observer: native candidate review

Recorded2026-10-27. This is an offline source/build review, not deployment or
live validation. A supervised host wrapper is being built separately.

Accepted native pins:

| Artifact | SHA256 |
| --- | --- |
| native-build-manifest.json | 44f74a8a695f41ed21d68a7a36e13934eebc74050bf991c634e6015ec88043a2 |
| Program.cs | 0edd0363c0969e3abc1d69c9116e2b06c9414632a069a78a767379f1cd19887e |
| native DLL | ffcba3f95040114a4ee3c6476a2d686d9e874d198898d678707ccc31b1cf6e2d |

The independent read-only reviewer found no P0/P1/P2 issues. Root also inspected
the fixed geometries, allocation/retention model, output limit, and production
monotonic clock. The candidate uses the previously proven read-only target101
transport and fixed R/M/C/H/L windows qualified in U; H is inside reproduced
image1 data RAM, while its CPU-field interpretation remains conditional.

The reviewer verified unknown-before-bulk and Ready-only-after-exact-IN,
completion of a pending matching IN even after deadline/clock trouble, no
header after ambiguity, exact initial RT-state classification, initially
faulted onset-missed capture, and at most one post-fault set. It changes no
memory setting and arms no diagnostic gate.

Observation is bounded to20seconds and80cycles at nominal250ms. The current
header/IN pair can add up to two2-second transfer timeouts; managed scheduling
is not a hard real-time guarantee. Each retained transfer has monotonic
before/after timestamps. Older fully clean cycles are explicitly discarded;
only the last clean, transition/initial, post-fault and current partial records
can remain. Consequently it must not be described as a complete80-cycle raw
archive or an exact CPU-register/event-time trace.

The75-case fake suite passes. Its maximum success shape is17windows and
34transfers, serialized to10541bytes under the24576-byte native cap. A remaining
P3 coverage gap is explicit: overlong-IN handling retains the true count and
safely clamps raw bytes, but no dedicated FailDelta=+1 regression was included
in those75cases. Source behavior was reviewed as correct; this is not a live
failure or a blocker, and no source repin was made for it.

Four deterministic accepted fixtures were generated from the built fake
transport via a temporary host reflection harness: AlreadyFaulted, transition
at R-start, transition at R-end and TimeLimit. No CLI, source, native manifest,
target or network operation changed during fixture generation.

Native review clears host-wrapper integration only. The wrapper requires its
own pinned contract, failure-path review and tests before one target run.
