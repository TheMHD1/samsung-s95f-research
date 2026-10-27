# Quiescent PM observer capacity assessment

## Scope and conclusion

This is an offline capacity assessment, not a capture authorization or a
physical/fault diagnosis.  It uses the retained five-second quiescent-PM smoke
and the earlier ninety-second passive trace.  No TV, root, network, getter,
setter, ioctl, key, or control action was performed for this assessment.

The measured buffers and file ceilings have enough **baseline** headroom for a
90-second passive run at the two observed workloads.  A duration-scaled
projection of the five-second per-CPU raw-ring occupancies reaches at most
46.62% of one 4 MiB CPU ring.  Adding one entire observed smoke footprint to
each projected CPU as an intentionally coarse illustration reaches at most
49.86%.  The earlier real 90-second trace retained all 107,587 written events.

That is not a justified upper bound on a future resume burst.  The PM smoke
contained a short framework-PM burst but no standard `sdp-hdmi` callback, and
the selected seven generic tracepoints cannot observe or exclude the
proprietary Samsung runtime-PM dispatch.  Consequently this report does **not**
clear 85/90-second execution by itself.  It supports asking for a separately
reviewed, zero-annotation passive capacity run of the corrected exact source;
all existing per-CPU loss, sidecar-size, timing, lifecycle, cleanup, and parser
checks must remain fail-closed.

## Pinned evidence and review state

The five-second evidence is
`qpm-smoke-20261026t204819.onset/record.json`, SHA-256
`82771270a4aed3b08f8afa9c9bc6bac6fd175d77ea4abdf38bc8d4a9e846553e`.
Its trace is 1,198,275 bytes, SHA-256
`64bd189afff5c01a08556cac05f3407489ba74a9bcf2c6d0140a88051bc9f9a5`;
its metadata is 494,864 bytes, SHA-256
`7d6a74c59eddc39cbc7ece8480ea1d9ad1d59a13fbe56ac6b5bcd7b9ff0241c3`;
and its vlog is 4,898,382 bytes, SHA-256
`0b9e673c776e53bf3e0907bfbb8c176ca968039eb62173c8200ab44c5b6db267`.
The record says accepted/technical/cleanup true and physical unobserved, but a
later review found that its redundant host cleanup named the ancestor PM trace
namespace rather than the collector's quiescent-PM namespace.  Therefore those
record flags are not used here as proof of the old host-cleanup contract.
Successful collector self-cleanup likely removed the actual instance, and the
later read-only residue response (SHA-256
`4480e7e25a9db002acee96df495f2f3a88d0ec10d5a14c410b285fb27e8a7355`)
reported both namespaces and both output/stage trees absent with global tracing
off and tracer `nop`.  The namespace defect has since been corrected and
independently cleared offline in source SHA-256
`8390e85eff9a40fe774c5e2bd7488ebaaa703c734af20a19fd0a780b58cdc43f`;
that review cleared a future five-second passive smoke only, not an 85/90 run.

The historical capacity record is
`capacity-20261026t1648.onset/record.json`, SHA-256
`c2a1476e09149108d4cf25c0ccac6db18f86010f541ee671e680b2a03b6b4434`.
Its trace SHA-256 is
`403d6951854ae14e312d894534a02b1fe42bb59e576ef58fe9ef8a44994058e7`.
The accompanying result report SHA-256 is
`688d98008a6b0fdb3ae29f4ff5ab5fd7bde2b6f1df467b10e20214b64aa298b0`.
That run was correctly rejected under its then-current parser for an ioctl
enter 4.038 ms before END whose exit was not retained.  It remains valid
capacity evidence: the trace ring reported 107,587 retained of 107,587 written
events, with no overwrite.  Later observers added the bounded drain without
retroactively accepting the historical run.

## Raw ring measurements

The current observer configures 4096 KiB **per CPU**, 16,384 KiB total on four
online CPUs.  The smoke metadata reports:

| CPU | Raw events | Raw bytes | Oldest-to-now seconds | Overrun / commit overrun / dropped |
| ---: | ---: | ---: | ---: | --- |
| 0 | 2,895 | 124,032 | 6.470833 | 0 / 0 / 0 |
| 1 | 2,028 | 91,516 | 6.468699 | 0 / 0 / 0 |
| 2 | 2,948 | 135,680 | 6.473442 | 0 / 0 / 0 |
| 3 | 2,906 | 135,228 | 6.475100 | 0 / 0 / 0 |

These `bytes` values are raw per-CPU trace-ring occupancy from tracefs stats.
They are not the 1,198,275-byte formatted `trace` sidecar.  The formatted file
expands binary ring records into text and must be budgeted independently.

For a conservative duration-only comparison, 93.30 seconds is used: the
validator permits up to 91.00 seconds for a requested 90-second physical
window, plus the configured maxima of 0.05 second enable bracket, 0.50 second
armed prelude, 1.25 seconds pre-roll, and 0.50 second drain.  Each CPU is
projected independently as `observed bytes * 93.30 / observed CPU
duration`; no cross-CPU pooling is assumed.

| CPU | Linear events | Linear raw bytes | 4 MiB CPU ring | Plus one whole observed smoke footprint |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 41,742 | 1,788,361 | 42.64% | 45.60% |
| 1 | 29,250 | 1,319,963 | 31.47% | 33.65% |
| 2 | 42,489 | 1,955,520 | 46.62% | 49.86% |
| 3 | 41,873 | 1,948,506 | 46.46% | 49.68% |

The projected raw total is 7,012,350 bytes, but total free space cannot repair
one overflowing CPU; the per-CPU percentages are the relevant checks.  The
“plus one smoke” column is only a sensitivity illustration, not a statistical
or causal burst allowance.  A future run is accepted only if every CPU again
reports retained equals written and zero overrun, commit overrun, and dropped
events.

The older 90.16-second trace, without the seven PM events, recorded per-CPU
event counts 28,113 / 25,188 / 27,606 / 26,680 and retained every event.  Its
11,543,194-byte formatted trace is direct long-duration evidence and is more
informative than a five-second formatted-file projection.  It does not prove
the PM-extended event rate or a fault-time burst bound.

## PM event volume and its limit

The smoke retained 238 selected PM rows totaling 28,831 formatted bytes
(maximum row 131 bytes): 57 `rpm_resume`, 59 `rpm_suspend`, 3 `rpm_idle`, and
119 `rpm_return_int`.  By CPU the counts/bytes were 4/484, 144/17,431,
86/10,432, and 4/484 for CPUs 0 through 3.  Of these, 224 rows occurred in
pre-roll, concentrated from uptime 69323.378908 through 69323.406783
(27.875 ms), and 14 occurred in the physical window.  All 119 runtime pairs
were accounted; callback and system-phase pair counts were zero, unmatched was
empty, and `sdp_hdmi_positive_correlations` was empty.

Scaling all 238 rows continuously across 93.30 seconds would yield about 3,429
rows and 415,427 formatted bytes.  This is a workload extrapolation, not a
resume-burst bound.  The observed 27.875 ms clustering shows why a mean rate
alone is insufficient.  More importantly, zero standard `sdp-hdmi` callbacks
does not imply the private callback did not run: static analysis shows the
proprietary dispatch may bypass all seven selected tracepoints.  PM silence or
low volume never supports absence, panel-state, or causal conclusions.

## Formatted sidecars and ceilings

The enforced ceilings are trace 128 MiB, meta 4 MiB, samples 2 MiB,
sample-errors 256 KiB, vlog 64 MiB, artifacts 2 MiB, and FDs 2 MiB.  The smoke
started with `/tmp` available 969,896 KiB and `MemAvailable` 503,508 KiB; it
ended at 964,652 KiB and 497,384 KiB.  The preflight floor for each is
262,144 KiB.  These are endpoint measurements, not a guarantee against later
system pressure.

| Sidecar | Five-second PM smoke | Long-run evidence or projection | Ceiling | Assessment |
| --- | ---: | ---: | ---: | --- |
| formatted trace | 1,198,275 B | 11,543,194 B actual historical 90 s; 17,265,997 B duration projection | 134,217,728 B | ample file headroom; ring loss remains the primary trace check |
| vlog | 4,898,382 B over 9.996 s | 44,427,406 B actual historical; 46,553,250 B at the smoke rate for 95 s | 67,108,864 B | about 66–69% used; must retain natural exit and timestamp/order checks |
| samples | 6,962 B (22 M, 5 Q) | 99,760 B historical; about 125,316 B for 396 M and 90 same-size Q rows | 2,097,152 B | ample |
| sample-errors | 14,754 B, 191 complete dd operations | 109,153 B historical; about 214 KiB for an illustrative 2,775-operation branch run | 262,144 B | narrowest projected non-vlog margin; exact inventory and size cap must reject excess |
| meta | 494,864 B | 481,703 B historical | 4,194,304 B | largely fixed maps/formats; ample in these runs |
| artifacts | 4,433 B | 4,433 B historical | 2,097,152 B | ample |
| FDs | 5,710 B | 2,296 B historical | 2,097,152 B | ample |

The sample and sample-error estimates use the smoke's exact 216-byte M rows,
442-byte Q rows, and complete dd-summary inventory.  They are planning numbers,
not acceptance substitutes.  In particular, Q row count and dd diagnostics
can vary; any unexpected diagnostic, missing operation, or size-limit hit must
continue to reject and preserve the partial artifacts.

## Readiness decision and smallest next evidence

The evidence supports a **conditional capacity expectation**, not an
85/90-second clearance:

- raw per-CPU linear projections remain below half of each ring, and a real
  older 90-second run had no ring loss;
- formatted trace and all sidecars project below their enforced ceilings, with
  vlog and sample-errors providing the smallest margins;
- the PM burst observed in the smoke fits easily, but one burst cannot bound a
  different resume episode and provides no private-path coverage;
- the corrected namespace source has exact-byte offline clearance only for a
  five-second passive smoke; and
- all 23 quiescence attempts in the retained smoke terminated on their first
  numeric non-54 sample, so the bounded retry-after-54 branch still lacks live
  exercise.  That is a validation limitation, not a reason to infer failure or
  to weaken the guard.

The smallest defensible next evidence, if separately authorized, is one
zero-annotation passive 85/90-second capacity run of the exact namespace-fixed
source after an independent reviewer explicitly extends clearance to that
duration.  It needs no owner physical claim and must retain the unchanged
per-CPU trace stats, PM format/enables, source identities, sidecar limits,
natural vlog termination, quiescence attempts, lifecycle/pairing checks, and
authenticated cleanup of the actual derivative namespace.  A failure or
overflow is useful bounded evidence and must not trigger an automatic retry.
Even a fully accepted run would validate transport/capacity only; it would not
show a private HDMI callback, establish absence of a module cycle, diagnose a
panel gate, or replace an annotated visible-to-black onset capture.
