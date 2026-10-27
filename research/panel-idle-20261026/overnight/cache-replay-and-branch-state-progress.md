# Request replay and branch-state follow-up

This phase extends the frozen [81-file policy snapshot](pqe-policy-followup-evidence-manifest.json), SHA256 `775f470de4109b6fc66996fc0408f431fcac94ea424068a3dddd71ae8ff534af`. Those files and earlier snapshots remain unchanged. The goal remains active: no permanent blackout fix, physical recovery/prevention, or untethered root has been verified.

## What changed in the diagnosis

The prior phase established userspace pre-I/O caching and identical-request suppression, but that alone cannot explain whether output is restored after a controller lifecycle event. The [kernel replay audit](../tcon-research/qd-kernel-output-replay.md) now establishes a positive restore path: F3:0x128 is entry218 in a 226-key generic command table. A generic request caches its scalar and valid flag before the lower send. Eligible recovery paths later replay every exact-valid-one record after frame-mode recovery, including this command if recorded. They also restore separate screen-saver/global/low-power policy settings.

The replay calls discard lower errors; a zero aggregate return is not success evidence. Initialization clears validity, but the examined off/on sequence retains the records and attempts their replay. This narrows the missed-restore hypothesis: an unchanged userspace cache does not itself imply the kernel failed to resend the TCON command. No actual kernel valid entry, controller reset, replay invocation or incident-aligned failure has been observed. The separate userspace FRC selector `0x42b48` write is not established as part of that kernel replay.

The [RoseMQD resume-record audit](../tcon-research/qd-resume-record-replay.md) resolves another, separate 16-slot command/payload/enable table and its concrete writer. Its replay routine is conditional and discards send errors. Its contents were not read, and its body contains no fixed F3:0x128 command. This table must not be equated with either the userspace final-duty static cache or the kernel's 226-entry table. Parent review corrected a draft address derivation: command records begin at backend-inner `+0x8a8` (`0x115*8`), not `+0x1430`. The QDDimming resume gate is cleared only on the exact-one route; other values return without clearing.

The [send-buffer audit](../tcon-research/qd-onecommand-buffer-dataflow.md) closes an earlier conservative uncertainty. The stock send wrapper copies the scalar into its own 16-byte envelope and has no caller copyback. The adjacent read wrapper does copy back, but it is a distinct function. Thus, under defined stock execution, the final-duty backend's second output write receives the original requested scalar. Runtime replacement, corruption and actual transmission remain outside that static conclusion. Historical reports retain their earlier bounded scope rather than being rewritten.

## Actual expanded baseline

The new [branch reader](pqe-branch-baseline.py) is separate from the frozen policy reader and observer. It retains their source/identity/maps/pointer/range and raw byte accounting, and adds source-backed base-QDDimming branch inputs. The added fields and base AutoPowerOff static are read only when the exact base vptr is validated; MNT fixtures require their absence. It does not invoke an event query, getter, setter, target function or ioctl, and does not infer an active branch.

Frozen reader SHA256: `84ff5138a7c4551b932b10360eb6b98d806dc2ef385497b4ec2f7123d6c27acb`.
Tests SHA256: `750195a7a6f691cb209046406cb47301378cde2e5d6bc1942c2f3fae92bf8df6`.
Generated command: 4661 bytes, SHA256 `8e8e3ef9e8e4bd928122040bbfdaa884c8e4496a46303bab86fdcfc8a9f50364`.
Exact reviewed bytes and command are preserved in `pqe-branch-reader-reviews/84ff5138a7c4551b-750195a7a6f6/`. Its archive status records preparation, before later independent clearance and actual execution. Seventeen offline tests passed, including the actual CLI dangling-output-symlink refusal. Review cleared one finite read with the existing 25-second timeout and no retry.

That one actual run is [pqe-branch-baseline-20261026T181903Z.json](pqe-branch-baseline-20261026T181903Z.json), with adjacent intent and driver outputs. CLI returned zero, accepted=true. Captured uptime `60354.20..60355.08` spans 0.88 seconds; 292 process-memory bytes were requested. The result remains sequential/non-atomic and physically unobserved. The [independent raw-result review](pqe-branch-baseline-independent-review.md) records endpoint and byte-accounting verification separately.

| Raw field | Value |
| --- | --- |
| QDDimming inner `+0` | 89 |
| Aligned word `+0x38` / low byte used by code | 256 / 0 |
| Weights `+0x88`, `+0x98` | 102, 102 |
| Floor `+0xa4` | 0 |
| Sources `+0xf8`, `+0xfc` | 100, 17 |
| Model gate `+0x188` / control `+0x18c` | 0 / 0xffffffff |
| Gain `+0x2a4` / raw AutoDim `+0x2a8` | 1024 / 0 |
| Product gate `+0x450` | 0 |
| Base AutoPowerOff static count | 0 |
| Weber current / target / ramp count | 1023 / 1023 / 0 |
| Object count | 42 |
| Working values / backend requested cache | 256, 256 / 256 |

The aligned word at `+0x38` is deliberately not treated as a boolean: the relevant instruction reads its low byte, which was zero even though the word was 256. No physical units are assigned to these scalars.

## Conditional offline consistency check

Using the previously reviewed arithmetic model, `weber_formula(fc=17, f8=100, weight=102, weber=1023, scale=1024)` gives 256. Assuming that ordinary route, no additional virtual-hook mutation and the sampled AutoDim/count/model values, AutoPowerOff and the final clamp also leave 256. This matches the raw working words and backend requested cache.

This is a conditional consistency check, not a replay of an observed callback. The fields were sampled at different times; endpoint pointer equality cannot exclude changes away and back. The intervening virtual mutation hook was not sampled. A matching calculation does not establish which branch ran, whether the driver sent anything, panel acceptance, physical light or fault causality. The current result must not be labeled a physically black baseline.

## Remaining useful work

The expanded reader is a single finite baseline tool, not yet integrated into the sustained onset observer. The next instrumentation step is to align the new gate/input tuple with the existing monitor and controller trace during an owner-observed Apps-to-sparse-menu transition. That experiment must separately mark physical light and audio; the brief Ugoos loss with an audio pause remains a different incident pattern.

Offline follow-up should also establish whether the separate FRC `0x42b48` leg has its own reset/replay lifecycle. Existing request caches and replay mechanisms cannot substitute for observing emitted commands and their replies. No cache forcing, protection bypass, factory setting, service restart, firmware/kernel patch or display/power control was deployed in this phase. No experiment is left running from the completed finite baseline.

The [phase evidence index](cache-replay-followup-evidence-manifest.json) preserves the new source analyses, corrected interpretations, reviewed reader revision, raw capture and conditional model. Its local no-overwrite helper validates the preceding 81-file snapshot and the earlier 176/43-file anchors, revalidates the actual raw response, and checks the conditional calculation without running target code. Hash preservation is not proof of physical fault cause or repair.
