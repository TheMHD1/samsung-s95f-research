# Accepted short instrumentation smoke

One separately reviewed five-second **physically unobserved** smoke completed
with CLI exit0. This establishes a working short passive capture on this TV;
it does not identify the blackout fault, demonstrate recovery, or establish
full-duration capacity.

Frozen observer SHA:
`3a83318a23665919610a232a6fdc48d6d78a20c350f17fb5eb5a40bc0079768c`.
Tests SHA:
`413ba238820e7b1064db2fe7a889eeb5182a98460fee2577acf533154999b63b`.
The exact source/tests/four generated shell variants are preserved in
`onset-review-archives/3a83318a23665919-413ba238820e/`.
Independent review and all31 offline fixtures passed before this attempt.
The rejected intermediate candidates are preserved separately; none ran.

## Actual result

Capture directory: [smoke-20261026t1642c.onset](smoke-20261026t1642c.onset/).
Host start/finish: 16:40:24.784–16:41:01.031 UTC, including staging, scheduled
lead, capture, transfer and cleanup. Exact trace marker times are
54448.159270–54453.170859, approximately5.011589 seconds.

| Check | Actual evidence |
| --- | --- |
| Script data |18,266 bytes; source regeneration and stored hash match |
| Trace |7,001 retained/written/decoded rows, no ring loss;6,072 in-window |
| Selected syscalls |2,124 complete in-window AVOC ioctl pairs;0 unrelated, boundary-ambiguous, fork or exit entries |
| Process scope |Same23 START/PRE/ARM/END TIDs and exact enter/exit filter readback |
| Markers |Same hex event source and recorded collector PID/TGID |
| Monitor |22 rows,4.384Hz; leading/trailing gaps0.01/0.21 seconds |
| QD/Deviced |5 rows,0.887Hz; leading/trailing gaps0.01/0.49 seconds |
| Memory reads |All115 dd operations complete; raw lengths/identity/pointers validated |
| Vlog |27,713 records,54446.001–54455.999, maxgap0.010 seconds, natural exit0 |
| Artifacts |All seven sidecar lengths/SHA match; collector stderr empty |
| Cleanup |Authenticated exit0, empty stderr, exact `0\nCLEAN\n`, explicit checked-path absence |

The independent reviewer decoded and verified these retained artifacts,
including source/script hashes, PID/startticks, maps, pointers, FD state,
trace accounting, sample endpoints and global-trace baselines. This is a
bounded non-atomic userspace/trace observation. I2C reporting in this observer
is explicitly raw-line inventory; it does not prove complete transactions,
MCU acknowledgement or emitted light.

The record correctly reports `accepted=true`,
`technical_capture_complete=true`, `diagnostic_eligible=false`, no observer
rows, physical state unobserved-or-incomplete, and
`absence_claim_supported=false`. Technical acceptance must not be relabelled
as a physical panel recovery or evidence that the current picture is visible.

## Capacity is a separate question

Observed in-window CPU event counts are1387/1436/1801/1448. A steady90second
projection with the observed setup prelude gives approximately
25.0k/26.0k/32.7k/26.3k rows, about11.9MB formatted text in total.
CPU2 is the tightest ring and requires an average raw record below roughly
128 bytes for the4MiB-per-CPU budget. Formatted text size is not raw ring
occupancy. Only an actual long-run retained==written result proves retention
for that interval; future load changes can still overflow.

Vlog projects about39.2MB per95seconds against its64MiB limit; sampler
diagnostics project about161KB against256KiB. These are conditional
projections. Root metadata showed approximately970MB temporary-space and
503MB available-memory headroom at the short run.

The reviewer separately cleared one passive90second zero-annotation capacity
run with the same exact source. Its intent file explicitly says capacity-only
and stdin is DEVNULL. The internal record mode name `full-observed` describes
the code path, while the empty observer timeline must keep physical state
unobserved and diagnostic eligibility false. It cannot replace a subsequent
owner-annotated visible-to-black transition. The long result must be examined
before claiming capacity has passed.
