# Current-boot QD monitor-latch / physical-picture timeline

This is an offline reconstruction from three already saved paired captures. It
does not send a TV command, change a setting, or treat the compositor PNG as a
physical-light sensor. It supplements, rather than replaces,
[the latch disassembly](../tcon-research/qd-tcon-off-latch.md) and [the
separate content/power-path audit](../tcon-research/content-static-power-path.md).

## Evidence rules

* A **physical** label below is only an owner statement copied from the paired
  capture summary. `enlightenment_info -dump_screen` can show a composited Apps
  frame even when the owner reports that the actual panel is black.
* `QD_TCON_OFF=1` is the monitor-history latch described by the linked static
  audit, not a contemporaneous panel-power measurement.
* “No terminal marker found” means that the named text did not occur in the
  saved command stdout. It does not prove that a call did not occur during an
  uncaptured interval, was not logged, or used a different log spelling.
* Source offsets are **decoded UTF-8 stdout** line and zero-based byte offsets
  in `commands[0].stdout`, not JSON-file byte positions. This avoids treating
  JSON escaping as display-log data.

## Common boot and monitor identity

Every paired capture starts with the same `/proc/sys/kernel/random/boot_id`:
`00000000-0000-4000-8000-000000000000`. Every shown latch line identifies
`tcon-monitor` as process **P 706**, thread **T 1019**. The kernel uptime is
strictly increasing. Thus the three captures are from one kernel boot and show
the same PID/TID pair at their sampled times.

That is strong continuity evidence against a **system reboot** between the Apps
control and the black captures. It is not an attestation of an uninterrupted
userspace process lifetime: these captures did not record `/proc/706/stat`, an
exec/start event, or a continuous log cursor, and a PID could in principle be
reused. In particular, the `QD_TCON_OFF` latch could have been cleared by a
reachable monitor restart/reset path and set again during an unsampled gap.

## Chronology

| Capture / physical qualification | UTC header; uptime at command start → end | QD latch evidence | Raw stdout source offsets |
| --- | --- | --- | --- |
| `apps-visible-control` — owner confirmed the full Apps page **visible immediately before** the requested control capture | `03:33:17`; `7206.74 → 7210.11` | `QD_TCON_OFF = 1` every roughly one second from uptime `7194.280` through `7207.289`, P706/T1019 | [`apps-visible-control.json`](../paired-capture/apps-visible-control.json) `commands[0].stdout`, lines 6614–6645; bytes 561814–567020 |
| `black-after-live-b0` — owner explicitly confirmed the physical panel **remained completely black** through both captures and a volume press; audio/menu clicks continued | `03:36:24`; `7393.61 → 7397.52` | latch still `1`, from `7375.378` through `7394.390`, same P706/T1019 | [`black-after-live-b0.json`](../paired-capture/black-after-live-b0.json) `commands[0].stdout`, lines 6486–6523; bytes 538483–544525 |
| `black-volume-b1` — same explicit physical-black confirmation, including volume press and continuing audio/menu clicks | `03:36:55`; `7424.12 → 7429.27` | latch still `1`, from `7405.391` through `7424.403`, same P706/T1019 | [`black-volume-b1.json`](../paired-capture/black-volume-b1.json) `commands[0].stdout`, lines 6482–6513; bytes 538415–543167 |

The saved paired-capture summaries provide the physical qualifications and the
corresponding images. The `black-after-live-b0` summary adds an important
boundary: the owner reports the blackout after navigating to Live and then
blindly attempted Apps navigation, but its PNG depicts Apps and **does not
establish which Live frame triggered the failure**.

The Apps evidence is the relevant ordering result: a latch `1` was observed in
the same control acquisition only about 0.55 seconds after its initial uptime
sample, while the owner had just confirmed the full Apps page visible. This is
strong evidence that the latch pre-dated the deliberate Live blackout and can
remain asserted when Apps is physically visible. Strictly, the owner statement
is “immediately before capture,” not an optical measurement at the exact
`7207.289` log timestamp; the record does not prove sub-second simultaneity.

## What the paired samples exclude—and do not

The black samples do **not** show a newly distinguishable latch transition:
the observed value remains `1` before and after the reported Live-triggered
black state. The raw stdout in all three captures contains no match for these
known terminal-power signature strings:

```text
QDFTcon_SetQdTconPowerControl
panel dpms: off
TCON_MUTE_CTRL
off sensing required
```

Together with the static latch behavior, that means the repeated `QD_TCON_OFF`
lines alone cannot be read as a new monitor-originated terminal power-off
action at the later Live transition. They are fully consistent with a stale
history latch already observed around the visible Apps control.

However, this evidence is **not sufficient to exclude** a new terminal monitor
power-control action as the later trigger. There is an unsampled interval of
about `168.089 s` between the final Apps latch line (`7207.289`) and the first
black-capture latch line (`7375.378`), and the capture’s vlog query is a
bounded tail. A new action during that gap could leave the same final value
`1`; a reset/restart could also clear and then permit a later re-set. The
same-PID observation makes a whole-kernel reboot implausible, but cannot rule
out process restart/PID reuse or a state transition between samples.

The shorter black-to-black interval is also not continuous: it spans
`7394.390 → 7405.391` (about `11.001 s`). It adds persistence evidence, not a
terminal-action trace.

## Narrow conclusion and next passive discriminator

The current boot contains both (1) owner-confirmed visible Apps immediately
before the control capture and (2) an already asserted QD monitor latch in
that capture, followed by owner-confirmed physical black with the same latch
and monitor PID/TID. This refutes the simple claim that each repeated latch log
is itself the new off command that caused the later blackout. It does not
identify the blackout’s cause and does not authorize clearing, bypassing, or
forcing the latch.

To decide whether a future physical transition coincides with a new monitor
terminal action, retain a continuous existing-log cursor across the user’s
navigation and pair it with timestamped owner physical observations. The
useful discriminator is a *new ordered* QD/Deviced power signature plus a
latch reset/set transition—not another isolated `QD_TCON_OFF=1` sample.
