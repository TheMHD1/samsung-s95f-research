# Fresh host and retained-controller state

Recorded 2026-10-27 UTC. These are new observations, not a physical recovery
test. The owner is unavailable to annotate emitted light. The TV's Linux boot
remains `00000000-0000-4000-8000-000000000000`.

## Measurements

Two authenticated, persistent-only root commands read host state without
opening the controller USB interface. Their complete envelopes are retained
in `host-health.stdout.json` and `process-attribution.stdout.json`; the first
also has its command/timing receipt in `record.json`. Both returned exit zero.
The kernel is Linux 5.4.261, aarch64. Host uptimes were 124547.46 and 124573.81.
Graphics synchronization messages continued. Those messages are not a light
sensor or confirmation that the physical display works.

The second command attributes recurring signal-11 messages to thread 28637,
process 16097, UID 5001, running
`/opt/usr/apps/com.samsung.tv.csfs/bin/csfs.dll`. The captured process is alive,
sleeping, with a signal handler and no core dump in progress. These messages
do not establish repeated process deaths, a kernel restart, or a panel reset.
No process was killed or attached to a debugger in this capture.

The already reviewed fixed two-window reader was then executed once. Its
11-file contract still matches manifest
`c64d77d8356fde3867490155095e1ef240151634f1c72a529a43970055f5aa7e`.
The immediately preceding controller acquisition was O at uptime123267.81,
which ended with exact transfers, ReadyForHeader and clean release/close.
No intervening controller command was issued by this work block.

The new result in `rt-context-once/` was accepted at terminal uptime124639.19:

| Sample | Returned value |
| --- | --- |
| RT fault at bus4701240a | 0x1001 |
| Logger gate at bus47012406 | 0 |
| Context halfwords bus47010f04/06/08 | 0 / 54 / 44 |
| All64 context bytes vs earlier117834.25 capture | identical |
| All256 RT bytes vs earlier117834.25 capture | identical |

Context SHA256:
`0683bb72c1bb998774ba4747987ec82ac938ce892ede62d877b9a1da641f2439`.
RT SHA256:
`91055b0ce0f0b798a78313bd90520506f63261fa1c35d78a0de85b2d332379f9`.

All four synchronous USB transfers were exact. The native result ended
ReadyForHeader, released and closed the interface, and the wrapper verified
removal of its exact private stage (`STAGE_ABSENT`). No setting, logging gate,
threshold, firmware, UI or power state was deliberately changed.

## Interpretation and limits

The matching snapshots are 6804.94 seconds apart, approximately113.4 minutes.
They corroborate a retained controller fault while Linux continues operating.
They do not prove that the values were continuously unchanged between reads,
that every possible writer is stopped, or which mode/limit caused the event.
The snapshots remain sequential rather than atomic event-time measurements.

A stock kernel row at124541.431857 says `QD tcon status [OK], tcon power(1)`;
an adjacent HSM query returns0. Neither is the captured F380 selector8
RTProtect response. The subsequent direct RT read still returns1001, so that
generic OK row must not be presented as clearing the recorded RT fault or
proving emitted light. It is preserved as a separate observation.

No reset, recovery, preventive patch, bypass, flash or physical repair is
established. Next useful offline work tests whether the ordinary action helper
retains the selected mode, potentially reducing the need for an inline
event logger. This is a hypothesis being checked, not a successful capture.
