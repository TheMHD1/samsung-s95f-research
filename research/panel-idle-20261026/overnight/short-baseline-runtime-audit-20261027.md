# Independent runtime audit of the short captures — 2026-10-27

## Scope

This is an offline audit of `apps-live-20261027b.onset` and the immediately following `apps-foryou-20261027c.onset`. I made no TV, root, network, trace, getter, setter, or cleanup call. The original records and sidecars were not modified.

Both captures used corrected short-source SHA-256 `5c0e4ff02d1b54f4493dede7c7cda5eb78d2163d936b207c26f572a5ab00f7c4` and inherited the accepted quiescent-PM collector. Both original records remain correctly rejected.

## Findings

### P0 — the reported pending PM operations are parser false-negatives, not long callbacks

The PM validator includes the mutable formatted ftrace context token in its pairing key and later requires exact token equality. In both traces, raw entry and return evidence is adjacent and otherwise identity-consistent, but the token changes between entry and return.

In baseline `b`:

| Entry → return lines | Identity | Operation | Context | Duration |
|---|---|---|---|---:|
| 21663 → 21664 | idle PID 0, CPU 2 | `rpm_suspend mmc0:0001`, return 0 | `d.h2` → `dNh2` | 8 µs |
| 40887 → 40888 | idle PID 0, CPU 2 | `rpm_suspend mmc0:0001`, return 0 | `d.h2` → `dNh2` | 5 µs |
| 47392 → 47393 | `sfpmd` PID 2805, saved TGID 2764 | `rpm_suspend mmc0:0001`, return 0 | `d.h1` → `dNh1` | 6 µs |

In transition run `c`:

| Entry → return lines | Identity | Operation | Context | Duration |
|---|---|---|---|---:|
| 9639 → 9640 | idle PID 0, CPU 2 | `rpm_suspend mmc0:0001`, return 0 | `d.h2` → `dNh2` | 7 µs |
| 19686 → 19687 | idle PID 0, CPU 2 | `rpm_suspend mmc0:0001`, return 0 | `d.h2` → `dNh2` | 5 µs |
| 42156 → 42157 | idle PID 0, CPU 2 | `rpm_suspend mmc0:0001`, return 0 | `d.h2` → `dNh2` | 7 µs |

The corresponding returns were classified as unassigned because they landed in different context-key buckets; the entries were then reported pending at drain. The raw rows do not describe operations lasting until drain. The validator's fail-closed rejection is nevertheless faithful to its current contract and must not be retroactively changed in either record.

Any future parser correction should treat the formatted context token as recorded mutable state, not authoritative task identity. It may retain entry/return context separately while pairing positive tasks by PID, saved TGID, task name and lifecycle, and pairing PID 0 only by exact idle identity plus CPU. That change needs adversarial tests for cross-CPU idle rows, PID reuse/lifecycle events, nested same-name operations, and mismatched names; it is not authorized by this audit.

### P0 — capture `b` is a complete raw baseline but not the requested physical experiment

`apps-live-20261027b.onset/record.json` has SHA-256 `6dca2c6d9645acde6b307d5139a1dcbaa1cfb36b4f382af927059bcb3582600f`. It remains `accepted=false`, `technical_capture_complete=false`, and `diagnostic_eligible=false`.

Raw completeness evidence:

- collector stdout contains all seven sidecar rows followed by `CAPTURE_COMPLETE`; every advertised byte count and SHA-256 matches the fetched main sidecar;
- collector stderr and both launch stderr files are empty;
- trace retained/written/decoded counts are all 52,760, with `dropped=0` and `ring_complete=true`;
- all four per-CPU stats report zero overrun, commit overrun and dropped events;
- marker rows are exact and ordered: armed 36, pre-roll 826, start 1583, end 52706, drain-end 52799;
- marker uptimes are 84280.484384, 84280.852691, 84281.731201, 84311.801072 and 84311.906408; the physical marker span is about 30.070 seconds and the drain is about 0.105 seconds;
- base syscall accounting completes 11,647 syscall-54 pairs. Its one pending row is drain-only (`/dev/dri/card0`, line 52791), explicitly reported outside the physical window rather than used for an absence claim;
- all 23 guarded AVOC TIDs and FD targets remain stable;
- 135 monitor rows cover 29.74 seconds at 4.506 Hz; 30 Q rows cover 28.97 seconds at 1.001 Hz; endpoint and row-span checks pass;
- all 954 expected `dd` operations have complete success summaries; and
- vlog coverage is complete, source exit is 0, and maximum gap is 0.034 seconds.

Quiesce is authenticated root/status 0 with `QUIESCED`. Cleanup is authenticated root/status 0, returns global tracing `0` and `CLEAN`, and the record has `cleanup_verified=true`.

The only owner annotation says the owner was instructed to make an Apps-to-Live transition and that physical state had not yet been reported. Subsequent owner text explicitly indicated that the intended page transition did not occur. Therefore `b` is useful only as an uncalibrated stable-state baseline. It contains no confirmed physical transition or onset.

### P0 — capture `c` contains the manual transition interval but is not diagnostic-certified

`apps-foryou-20261027c.onset/record.json` has SHA-256 `9f06519a295acfbb0f7dda124e327c56251f19a826eea75aaf151f4ee605e322`. It also remains `accepted=false`, `technical_capture_complete=false`, and `diagnostic_eligible=false`.

Raw completeness evidence mirrors `b`:

- all seven advertised sidecars match exact bytes and hashes; collector stderr is empty and `CAPTURE_COMPLETE` is present;
- trace retained/written/decoded counts are all 51,383, ring complete, with no dropped records or I2C parse errors;
- all per-CPU overrun, commit-overrun and dropped-event counts are zero;
- marker rows are 26, 703, 1744, 51314 and 51423, at uptimes 84415.771444, 84416.024507, 84417.022988, 84447.184305 and 84447.289390;
- base accounting completes 11,722 syscall-54 pairs. The one pending row is again drain-only (`/dev/dri/card0`, line 51421), outside the physical window;
- 23 TIDs/FD targets are stable;
- 135 monitor rows cover 29.86 seconds at 4.488 Hz; 30 Q rows cover 28.97 seconds at 1.001 Hz; all endpoint/span checks pass;
- all 954 `dd` operations have complete success summaries; and
- vlog coverage is complete, source exit is 0, and maximum gap is 0.034 seconds.

Authenticated quiesce and cleanup both succeed; cleanup returns `0` and `CLEAN`, and `cleanup_verified=true`.

The GO note and owner's `done` acknowledgment are wholly inside the trace window. The later `picture black` annotation is outside it, has neither reaction nor host-clock uncertainty, and there is no structured visible annotation. Thus the data establishes only that the manually acknowledged navigation occurred during the capture and the owner later reported black. It does not establish an onset timestamp or a certified visible-to-black interval.

### P1 — sampled branch and monitor payloads did not distinguish the two runs

Every one of the 30 Q sample bodies is identical within each run and byte-identical across `b` and `c`. Every one of the 135 monitor payloads is likewise constant within each run and byte-identical across the two runs. This means the sampled userspace branch/cache and monitor block did not change across the captured baseline and transition intervals.

That is bounded evidence about these sequential, non-atomic sampled fields only. It does not prove that the panel output, controller-internal state, kernel state, or values between samples were unchanged.

## Outcome

Both runs provide loss-free raw traces, complete sidecars, valid sample coverage and verified cleanup. Both original records must remain rejected because the current PM pairing contract fails closed on mutable context changes. Run `b` is baseline-only with no confirmed transition. Run `c` captured the acknowledged navigation interval, but the black report arrived outside the trace window without calibrated uncertainty, so it is not diagnostic onset evidence.
