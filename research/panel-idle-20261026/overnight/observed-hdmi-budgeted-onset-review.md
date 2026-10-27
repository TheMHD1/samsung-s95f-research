# Budgeted 180-second HDMI collector: offline implementation review

Recorded 2026-10-27 UTC from retained local artifacts. No TV, root, network,
capture, or control operation was performed for this revision. The accepted
5-second smoke is instrumentation/rate evidence only; it does not qualify a
180-second observed run.

## Exact implementation boundary

The new derivative pins `observed-hdmi-long-onset-capture.py` SHA-256
`65aeae50409ad05532163072e118140d09c7eaf3437aabc5b3843a138ab5c2eb`
before import. It preserves that collector's only two modes:

- 180-second observed mode, requiring ordered in-window human annotations;
- 5-second `smoke-unobserved`, which is never physically or diagnostically
  eligible.

It uses a new output/stage/trace-instance namespace. Its only functional
changes are the linked resource budgets below. The existing map exception,
quiescence, trace-clock, PM/RPM accounting, sample/dd validation, identity,
staging, expiry, cleanup and no-global-trace-write contracts remain inherited.

Candidate source SHA-256 is
`18f2e3db892529218ca13fe5c7a3806348b155379d561db1cc07df7106d4be68`.
Candidate tests SHA-256 is
`b5cdda519d61d7a4322a4669558cf7d4e683805b831cca86e58e16a950c6e694`.
These hashes require independent review before any execution.

## Actual smoke inputs and rates

The accepted `sleep-smoke-20261027a.onset` record is pinned here by:

| retained item | bytes | SHA-256 |
| --- | ---: | --- |
| `record.json` | 8,423,270 | `b3e2b0746b211deb939bf834be0f4ee70c511c37bace89b9f0e8cf0a62a4c320` |
| `vlog-after.txt` | 4,632,040 | `c0b5d0c665f240651e846bc3a42db9dd5c5267c5ca917230069c69923732429e` |
| `meta.txt` | 494,807 | `45a51a101357416e2bee36d7781d21ea569a3cb0eca4586aea470450d6b008d4` |
| `artifacts.txt` | 143,983 | `8a38a176ac03e326769d977741575fa93401e4f274cece482169aace9fd8c907` |
| acquired `remote.sh` | 35,712 | `e9c088570f1fb97cce24d86fa4e2fa2ddeef7558265f2a7875feea2ed3d2cb22` |

The record is accepted/technical-complete with cleanup verified. Its vlog has
29,355 ordered records from uptime 93,124.000 through 93,133.992, a 9.992 s
covered span. The raw rate is 463,574.86 bytes/s. Straight scaling to a 185 s
long-window-plus-margin budget gives 85,761,349 bytes (81.79 MiB), already
above the old 64 MiB cap. This is why leaving the old cap is not a fail-closed
180-second design.

At 128 MiB, that same linear projection leaves 48,456,379 bytes (46.21 MiB,
36.1%) headroom. This is a planning projection, not a high-percentile burst
bound or 180-second qualification.

The smoke's private per-CPU raw ring byte inventories were loss-free:

| CPU | bytes | retained stats span | 185 s linear projection |
| ---: | ---: | ---: | ---: |
| 0 | 71,040 | 6.424 s | 2,045,961 B |
| 1 | 132,580 | 6.434 s | 3,812,023 B |
| 2 | 87,744 | 6.436 s | 2,522,185 B |
| 3 | 153,928 | 6.428 s | 4,430,262 B |

The largest projection is about 4.23 MiB, above one 4 MiB raw ring but below
8 MiB. Five quiet seconds cannot characterize event bursts, CPU imbalance, or
a long session; the increased ring remains guarded by exact per-CPU loss and
strictly-below-cap accounting.

## Linked budget changes

### Vlog

All three relevant boundaries move together:

1. the target vlog writer uses the target-proven 1,024-byte `ulimit -f` unit
   with value 131,072;
2. the remote final manifest requires `vlog-after < 134,217,728` bytes; and
3. every live host-side inherited sidecar-limit table and final parser uses
   the same 134,217,728-byte strict cap.

Reaching the cap is rejection, not truncation presented as complete.

### Private trace rings

The private instance requests 8,192 KiB per CPU and allows a read-back total
no larger than 32,768 KiB. Metadata acceptance independently requires the raw
readback to be exactly 8,192 KiB per online CPU, each CPU's retained byte count
strictly below 8 MiB, and zero overrun, commit-overrun and dropped-event
counts. The original raw metadata remains retained; only an in-memory
compatibility projection is passed to the pinned ancestor's old 4 MiB
configuration parser after the new values are independently checked.

### Memory and tmpfs headroom

Before creating/enabling the private instance, the target shell reads
`df -Pk` for the private `/tmp` output directory and `MemAvailable`. It now
requires each to be at least 393,216 KiB (384 MiB). The finalized sidecar caps
sum to 267 MiB:

| sidecar | strict cap |
| --- | ---: |
| trace | 128 MiB |
| vlog-after | 128 MiB |
| meta | 4 MiB |
| samples | 2 MiB |
| sample-errors | 1 MiB |
| artifacts | 2 MiB |
| fds | 2 MiB |

Thus the starting tmpfs guard is 117 MiB above the sum of final caps. It is a
start guard, not a reservation: subsequent system activity and tmpfs-backed
file growth can still reduce memory. Writer limits, remote manifest limits,
loss checks and cleanup therefore remain necessary.

The accepted smoke itself recorded 970,200 KiB `/tmp` availability but only
351,804 KiB `MemAvailable` at its starting artifact snapshot. The new 384 MiB
memory guard would deliberately reject that state. This revision does not
weaken the threshold to make the prior environment pass.

## Interpretation and remaining readiness

The new budgets prevent a known 64 MiB vlog failure mode and increase raw ring
headroom. They do not prove that 128 MiB vlog, 8 MiB per CPU, the 128 MiB trace
export, the 900-second expiry/fetch lifetime, or 384 MiB starting headroom are
sufficient for a particular 180-second content session.

An independently reviewed, accepted passive smoke of these exact bytes must
first demonstrate that the larger allocation is supported under adequate
memory. A subsequent 180-second run needs its own zero-loss/cap/cleanup result
and ordered owner annotations. No physical state, HDMI cause, RT-protection
cause, recovery, or generic log absence follows from this budget review.
