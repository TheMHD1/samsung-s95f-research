# Independent audit: namespace-corrected quiescent-PM home smoke

## Outcome and boundary

The five-second passive capture at
`overnight/qpm-home-smoke-20261026.onset/` is technically accepted by an
independent offline review.  The capture ran from
`2026-10-26T21:32:34.444630Z` through `21:33:12.143292Z`; its physical window
was only about five seconds.  It contains no observer annotations, so it is
correctly `diagnostic_eligible=false`, `physical_state=unobserved-or-incomplete`,
and `absence_claim_supported=false`.  It does not show that the panel was
visible, black, healthy, or faulty and does not identify an onset cause.

No target call was made for this audit.  It rechecked retained local bytes and
did not modify the capture or its source.

The final record is 9,430,934 bytes, SHA-256
`92de00c6109785e389f4c9aad88630496fcd9923b7ff0a27c6ffe37199bccf5a`.
It says `accepted=true`, `technical_capture_complete=true`,
`pre_cleanup_technical_complete=true`, and `cleanup_verified=true`; the raw
evidence below supports those technical flags.

## Exact source and transport provenance

The active host source was
`observed-quiescent-pm-onset-capture.py`, SHA-256
`8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f`.
Its offline tests were SHA-256
`ae330c948f7f66cb229ee88e7eb44fbf45d4cd92b914a9da439a3b5213ecb2e8`.
The pinned quiescence addendum was SHA-256
`595e0faa6fb6eefb2193a28b1c812b2482a4a016e1589c0dc0817e5b994cc92e`.

The exact rendered collector was 35,474 bytes, SHA-256
`84708b923b758fc010217454011f66c5244d81a0c8914aa392feaadd9cbf4870`.
That size and hash agree among local `remote.sh`, `staging.json`, both metadata
endpoints, the authenticated launch command, and the staged-file launch
checks.  The launch response is authenticated root on model `QN77S95FAFXZC`,
uses persistent-only access, records collector PID/process-group/session
`23548` with start ticks `17991797`, and has empty client and remote stderr.

All seven returned sidecars match both the collector manifest and the local
files:

| sidecar | bytes | SHA-256 |
| --- | ---: | --- |
| trace | 1,167,897 | `ba599c04a67b7eff3e3caead83ca6c51971886c833a75839fc97664bee711526` |
| meta | 494,848 | `af034c2fb84443cc40aeea58e111cfac0048dce07eac489d7cc75037c945e075` |
| samples | 6,962 | `e377bfc886c3096387484f47620cfb5157f55cb705e0397d474b069e6ba13875` |
| sample-errors | 14,753 | `03e75d398b863c8600512759500dee3c5dc2a3b4ef3c07bea19b3ede11b35361` |
| vlog-after | 5,848,561 | `edb361bab68e677818f0b57e7cce00b5ce3f6d56cde8c908628a9dba7c9eb110` |
| artifacts | 4,433 | `4438266599db230754e5eac9384ef7fb272c18028a8b350e4116880f41b88cfc` |
| fds | 5,710 | `f491c2b78f8a02f64a37347251dc1269e2423f4b62d190e9a8dab8da8105c681` |

`collector.stdout` lists exactly that manifest followed by
`CAPTURE_COMPLETE`; `collector.stderr` is empty.

## Identity, quiescence, and sampling

The boot ID is the same at both metadata endpoints.  AVOC remains PID `706`,
start ticks `603`, executable `/usr/bin/avocd`; deviced remains PID `675`,
start ticks `560`, executable `/usr/bin/deviced`.  Their executable hashes,
the `libave` hash, maps, computed pointers, and typed header identities pass
the retained start/end checks.

The exact 23 AVOC TIDs agree across START, PRE, ARM, post-sweep quiescent, and
END inventories.  All three FD inventories are identical, including the
attributed `/dev/tztv_frc`, `/dev/tztv_tcon`, `/dev/sdp_pqe_dp`, DRM, I2C, and
kdbus descriptors.  No AVOC fork or exit is retained in the bounded trace.

Every TID reached a terminal numeric non-54 `/proc/.../syscall` point on its
first attempt.  The sweep ran from uptime `71977.84` through `71977.98`, within
the bounded prelude.  No intermediate syscall 54 occurred, so this run
validates the ordinary terminal path but still does not live-exercise the new
retry-after-54 branch.

The sample stream has 22 monitor rows and five Q rows.  Monitor and Q endpoint
gaps and rates pass.  Q reads span 0.43--0.47 seconds, below the 2.0-second
limit.  `sample-errors.txt` contains exactly 191 complete successful `dd`
summaries with the expected record-count inventory and no other diagnostic.

## Trace and PM accounting

The raw header says 10,521 retained of 10,521 written events.  Per-CPU stats
sum to the same 10,521 entries; every CPU reports zero overrun, commit overrun,
and dropped events.  The five exact owned markers occur once, from collector
PID/TGID `23548` and the same marker source `0xffffffc01017095c`:

| marker | trace time |
| --- | ---: |
| TRACE_ARMED | 71977.836660 |
| PREROLL_START | 71978.070644 |
| CAPTURE_START | 71979.086264 |
| CAPTURE_END | 71984.114133 |
| DRAIN_END | 71984.219963 |

The trace-enable bracket is 0.01 seconds, prelude 0.234 seconds, pre-roll
1.016 seconds, physical window 5.028 seconds, and drain about 0.106 seconds.
There are 24 enable-slop, 703 prelude, 961 pre-roll, 8,723 physical-window,
105 drain, and zero post-drain rows.

Syscall-54 accounting contains one complete start-boundary pair, 426 complete
pre-roll pairs, 2,128 window-originated pairs, no window-tail pair, and 43
drain-only pairs.  There is no orphan, unresolved drain-end, or post-drain
syscall row.  All relevant FD targets remain stable.  The 19 filtered I2C rows
are only raw event inventory and do not establish a complete transaction or a
physical result.

All seven exact PM formats and enable readbacks are present.  The trace has 22
selected PM rows forming 11 runtime-PM pairs: three resume, five suspend, three
idle, and eleven return rows, all on CPU 2.  There is no malformed/unmatched
PM row, callback pair, system-phase pair, or positive `sdp-hdmi` correlation.
That last absence says nothing about the proprietary private dispatch, which
the selected framework events may not cover.

The vlog has 38,571 ordered records from uptime `71977.002` through
`71986.996`, covers both required endpoints, has a maximum reported gap of
0.01 seconds, exits zero, and terminates naturally.  It does not support a
generic log-absence claim.

## Namespace and cleanup

This run used the corrected private roots:

- `/tmp/researcher-observed-quiescent-pm-onset-20261026/qpm-home-smoke-20261026`
- `/tmp/researcher-observed-quiescent-pm-onset-stage-20261026/qpm-home-smoke-20261026`
- `/sys/kernel/debug/tracing/instances/researcher-quiescent-pm-onset-qpm-home-smoke-20261026`

The authenticated cleanup command names those exact roots, stops the guarded Q
sampler, collector group, vlog process, watchdog group, and expiry group,
disables and removes the private trace instance, removes the exact output and
stage paths, and verifies their absence.  It exits zero with empty stderr and
stdout `0` then `CLEAN`.  Global trace state is `0`, tracer `nop`, at both
metadata endpoints and is again `0` in cleanup.  This resolves the older
ancestor-namespace defect for this actual run.

## Narrow next-run decision

This evidence, together with the prior capacity assessment
`quiescent-pm-capacity-assessment.md` SHA-256
`9cf70211177556f6b7766a62c09659d61c55ef9dc3a9578727481ea24f956955`,
supports **one separately coordinated 85-second run of this exact source**.
It does not clear 90 seconds, repeated runs, or an automatic retry.

For an 85-second request the validator's maximum configured trace interval is
88.30 seconds.  Scaling this smoke's raw per-CPU occupancy independently gives
about 34.49%, 30.20%, 53.79%, and 36.38% of the four 4 MiB rings.  The same
simple scaling gives about 16.0 MiB formatted trace.  Current vlog rate over a
90-second required coverage interval projects about 52.7 MiB of its 64 MiB
ceiling.  An illustrative exact-row-rate sample-error projection is about
205 KiB of its 256 KiB ceiling.  These are workload projections, not burst
bounds; the unchanged ring-loss and file-size checks must reject any excess.

For a physically useful run, omit `--smoke-unobserved`, keep the owner on the
visible Apps page before launch, and do not reboot or restart either daemon.
The owner must provide an honest, ordered `picture visible` annotation and,
after personally triggering the known Live-page blackout, a `picture black`
annotation, both well inside the 85-second START..END window and both with
`reaction_ms` and `clock_ms`.  The terminal must remain attached so those
lines can be delivered to stdin.  The two uncertainty intervals must not
overlap.  A failure, loss, incomplete annotation, or cleanup problem remains
useful rejected evidence and must not trigger an automatic rerun.

The exact command shape is:

```sh
python3 overnight/observed-quiescent-pm-onset-capture.py UNIQUE-LABEL \
  --seconds 85 --run --reviewed
```

`UNIQUE-LABEL` must be lowercase, start with a letter, contain only lowercase
letters/digits/hyphens, be at most 31 characters, and have no existing
`overnight/UNIQUE-LABEL.onset` directory.
