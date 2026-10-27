# Screen Saver Brightness: attended scalar test

This tests one exact factory setting on QN77S95FAFXZC build
`T-RSMFAKUC-0090-REL-202607141953`. It is not a force-on service.

The stock factory service maps menu item `60802`, **Screen Saver Brightness**,
to UID `20505` (`0x5019`), persistent EER_B storage. Captured factory data and
QDF code establish valid values 0–7 and baseline 7. The dedicated stock
`SetDecimalValue(60802, value)` transmits the item and saves factory storage.
Zero therefore persists until restored; it is not a RAM-only lease.

`trial.py trial` exclusively creates `state.json`, snapshots the 36 QD items,
requires the exact item/baseline, no burn-in operation, no lcdon lock, lcdon
power, and an unchanged boot before writing zero. The existing root-access
wrapper independently enforces model/build/developer-host identity. The stock
setter must return 1, followed by exact item readback 0.

The parent restores after 180 seconds. An independently detached TV shell
tries at 195 seconds, validates the target, changes only 0 to 7, and checks
readback, retrying on temporary failure. A separate host watchdog tries at
210 seconds and retries indefinitely until the root connection returns and
7 is verified. These are best-effort recovery paths: simultaneous host/TV
power loss can interrupt both. No true hard-expiry guarantee exists for this
persistent setting. `state.json` remains as the recorded baseline;
`restored.json` records successful restoration. Running `trial.py restore`
is an idempotent recovery command even after a TV reboot; it will not overwrite
an unexpected value other than 0 or 7.

Full QD before/after snapshots and deltas record collateral changes without
blocking the target restoration. Off-sensing/EL-sensing counters are dynamic.
No other factory value is written. No voltage, thermal, calibration, error
detection/recovery, firmware, compensation counter, or Screen Optimization
controls are changed.

The kernel must independently confirm UID20505/value0 and live brightness0.
A later factory restore request should resolve to Fac_ss0 rather than7.
Native screen-state=1 cannot establish a visible image: owner observation is
required. No automatic permanent setting is justified by readback alone.

## Completed 2026-10-26 test

The setter returned 1 and exact item readback was 0. Kernel uptime
5520.926508 independently confirmed `QDFTcon_SetFactoryData UID20505 Value0`
and brightness0. The last observation at uptime5684.33 (163.4 seconds later)
still retained that event, with no subsequent brightness7, ERR DET, fault,
or panel power-cycle entry in the captured kernel output. No new AVEMonDIM
`value:1` request occurred, so this did not separately exercise that callback.
The owner subsequently confirmed the picture stayed off throughout: this test failed to recover the panel.

At uptime5699.674443 the scheduled parent restore changed UID20505 back to7;
the kernel confirmed brightness7 and exact factory readback verified7.
All36 QD items matched their original snapshots. The TV expiry then read7
and exited without another write. The boot ID stayed unchanged. The trial
entry point is disabled again; the independent restore action remains usable.
This establishes successful reversible control of this scalar, not a proven
physical blackout repair.
