# Managed QD TCON power-cycle-once helper

This package is prepared offline and has not been deployed or executed on the
TV. It contains one argument-free ARM32 portable-IL helper for the exact stock
power-control envelope `operation=41, mode=2, reserved words=0` through
`/dev/tztv_tcon` ioctl `0xc010749f`.

Mode 2 selects the exact-build QDF normal off sequence followed by its normal
on sequence if the intended live callback binding exists. The lower source has
up to roughly 2.7 seconds of explicit waits in the longest recovered route,
plus callback/scheduler overhead. The reused managed lifecycle retains its
eight-second helper deadline and 25-second root-command timeout.

Return zero is not an acknowledgement. Missing interface/callback paths can
also return zero, and lower cache updates/errors are incomplete evidence. The
helper therefore reports only `kernel_return_zero_only`; it never reports
recovery, emitted light, successful rails, or a cleared protection condition.

There are no arguments, retries, loops, protection changes, EEPROM/flash
operations, arbitrary controller commands, or alternate device paths. The
package must remain dry until exact-byte independent review and coordination
with the passive before/during/after evidence plan in
`recovery-experiment-plan.md`.
