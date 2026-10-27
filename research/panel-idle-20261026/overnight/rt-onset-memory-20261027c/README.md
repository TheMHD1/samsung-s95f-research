# Bounded RT-memory onset recording work, 2026-10-27

Previous goal turn classification: progress. The preserved controller-access
checkpoint contains a successful known18-byte descriptor read and32-byte
RT-prefix read, with exact transport/cleanup and corroborated later zero
status. No physical recovery or permanent fix is established.

This work uses a new directory and separate helper derivatives. The preceding
90-file snapshot is immutable. Owner authorization permits unattended commands
and testing; the requirement to avoid bricking the TV remains.

Current aim: qualify a fixed256-byte RT block read and a finite recorder for
physical-onset comparisons. No flash, protection-value change or continuous
background polling is part of these preparations. No target call has occurred
at this initial checkpoint.

## Completed work block

See [progress](progress.md), [runtime audit](runtime-audit.json),
[reproduction](audit-runtime.py), [instruction-bound history interpretation](verify-history-interpretation.py)
and [parent-retained independent reviews](independent-review-record.md).
Three actual target invocations completed: one256-byte RT read, one20-sample
RT series and one512-byte read-only sector request. All52 root-call envelopes
and uploaded payloads reconcile. The series had20/20 exact reads, stable RT
bytes and4755ms duration; this was physically unobserved. The sector reply's
241205A header differs from the selected241230A header, making a larger
verified backup/fingerprint the next image-identity task before patching.
All stages were removed. No permanent fix, flash, protection-value change,
EEPROM write, UI navigation or panel reset occurred in this block.

## Preserved checkpoint

The [41-file snapshot](rt-recorder-evidence-manifest.json) covers6,166,952 bytes,
SHA256c012fdadd49d8f5dec30e6fff53d5e43a14fed1bb0c04a2bfb00f1883f3dc98f.
Normal/optimized runtime and history checks passed. Optimized snapshot
verification and an independent full byte/hash scan passed; a second publication
was refused without modifying the snapshot. The preceding90-file and260-file
snapshots reverified unchanged. Mutable README/navigation and future new files
are excluded. Source, builds, failed/accepted classifications and raw evidence
remain preserved. No target process from this block remains running.
