# Passive observer host-wrapper review before one run

Final wrapper manifest:
915d19e20d7e5e7fc81a1962cec150ef17f2d00229277666918d199e755d2fe1.

Final run-once.py:
a4146bc302a764f476e068f456398b8dc34a6e3cc480b876f6e44ed65098cc82.
Final test-wrapper.py:
9b8a5260ac1a9a75bf27926e40b8578806309bbce087096c1f5614e17773c403.
Native pins remain those in native-review.md; no native source was changed.

Independent read-only review cleared the exact17-file wrapper manifest for
one bounded run, with no remaining P0/P1/P2 findings and subject to the
external same-boot/known-ready lineage. The author ran55wrapper tests normally
and optimized with identical results and zero target operations. Native75fake
tests, host ABI refusal/dry behavior and generated shell syntax also passed.

Root caught a target-compatibility defect before any execution: the first
wrapper omitted Samsung's GC diagnostic rows, despite W's actual self-test
showing them. The exact rejected20aab wrapper is retained as
wrapper-before-gc-review.py for inspection only. Do not execute that archive.
The final wrapper accepts one JSON record plus at most32 bounded known
GC_INFO rows, rejects unknown/oversize/excess rows, and tests real W-format
self-test/native output. No failed live run or retry occurred for this defect.

Independent review also corrected pre-execution defects in maximum cycle80
counts (485requests/970bulk calls including post-fault reads), list extents
before zip, and an unjustified strict4-second overshoot cap. Actual root
45-second/host75-second supervision remains. These were offline corrections.

Final review verifies authenticated one-execute staging, unknown accounting
before launch, raw retention before parsing, exact accepted outcomes and
read-only counters, raw window reconstruction/hashes, role/window/transfer
extents and order, monotonic timestamps, distinct safe filenames and cleanup
only after accepted ReadyForHeader/release/close. No retry, write, reset or
new request after transport ambiguity is introduced.

A nonblocking P3 strictness gap remains: wrapper timestamps are checked for
monotonic ordering, but not explicitly bounded inside outcome startUs/endUs.
The separately pinned native code guarantees that relationship. This is
recorded as malformed-evidence strictness, not a known live failure.

The external lineage immediately before the proposed run is W125699.16:
same boot, six exact transfers, ReadyForHeader, release/close and stage absent.
No intervening controller operation was issued by root. The new wrapper and
native preflight independently recheck boot/device identity before traffic.
This clears one passive current-state run, not a reboot, physical recovery,
firmware modification or claim of event-time CPU registers.
