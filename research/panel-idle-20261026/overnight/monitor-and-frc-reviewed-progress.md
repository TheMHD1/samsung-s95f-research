# Monitor provenance and FRC lifecycle: reviewed progress

Recorded 2026-10-26T18:50:20.797921+00:00. Offline analysis of exact copied firmware binaries; no TV commands, writes, reboot, factory change, suspend/resume or physical observation were performed for this phase. No fault cause, permanent fix or physically verified recovery/prevention is established.

## What the additional reverse engineering establishes

The [monitor input audit](../tcon-research/monitor-input-status-provenance.md) traces ERR_DET, VDD_DET and cached health through userspace checks, ioctl dispatch, registered kernel callbacks and the GPIO provider. The checks normalize signed-negative getter returns to zero, so a no-fault result is not sufficient evidence of a healthy physical panel. ERR and VDD interpret raw levels differently; the health result is cached state rather than a new electrical measurement. A conditional raw-read error interpretation was identified, but no such error was observed during the owner's failure.

The [FRC write/lifecycle audit](../tcon-research/frc-duty-write-recovery.md) traces the separate dimming write through its ioctl and static callback pairing to a lower extension envelope. Selector 0x42b48 is positively present at index 3 of the nine-entry static QD save table. Suspend attempts to refresh values without checking individual read results. Resume input 20 can replay that table without a per-entry valid flag or useful aggregate write-error result. These are conditional code paths; their execution, saved values and downstream acceptance during this fault remain unknown.

Earlier work established that the ordinary immediate dimming candidate is clamped above zero, while a separate userspace request cache is updated before output is confirmed and can suppress an identical repeat. Those facts provide testable hypotheses, not proof that cache ordering caused this panel failure. The kernel generic-command replay, userspace resume records and FRC selector table are separate mechanisms.

## Review and verification

Both packages received a read-only independent review with no remaining material finding on the exact final bytes below. The FRC initial draft had callback-identity, cache-gating and replay omissions that were corrected before this review; these corrections are described in its report. The parent reran both offline reproducibility helpers successfully. Helpers hash-check copied source ELFs and compare selected instruction/data landmarks and retained disassembly; they are not full emulators or proof of runtime behavior.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| monitor-input-status-provenance.md | 9895 | `382a4783d5b2313b76816eea4ebb7a5847fe8abe47adb1194a5e4a4cf2d04aca` |
| monitor-input-status-provenance.py | 10690 | `e4f195711e774ae432f43343c04e99e506dec89c0d2cf52cd228bc82a447d1c9` |
| monitor-input-status-provenance.disasm | 62200 | `9290dfec4c339d301f571bc477c54beb3bffbfe415456326e1f6c2358abd37a8` |
| frc-duty-write-recovery.md | 8147 | `46dac70602dfdb7ee3044a8e787926bde225b381f281dcf1f0d0a07106d9c769` |
| frc-duty-write-recovery-reproduce.py | 5571 | `e3611cfda1f0d251ba1895f1e2ecb6d4ef7d6f42a01c57091df5760c66349543` |
| frc-duty-write-recovery.disasm | 38489 | `8b96c928304424cb996e98716abd7db62e793d0102e9471778820ae9dc6def88` |

These new files are not yet covered by a published evidence snapshot. Prior frozen snapshot files were not edited.

## Distance from a diagnosis

We now have a substantially narrower software map and specific failure mechanisms to distinguish. We have not yet linked a fault/status transition, failed output request or replay event to the exact physical blackout. The owner's damaged panel and content dependence remain relevant observations; neither proves which controller/rail/component fails or whether a software workaround can prevent it.

The next decisive experiment is one physically observed transition from populated Apps to the page that triggers black, with aligned policy state, fault/monitor state and controller traffic, then comparison to the visible control. The expanded combined observer remains under implementation and independent review; prior accepted passive captures did not include an owner-confirmed onset. No recovery/prevention control experiment is running. Firmware inside the panel MCU and complete machine-code coverage have not been obtained.
