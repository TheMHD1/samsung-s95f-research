# `QD_TCON_OFF` is a monitor latch, not a current power reading

Evidence source: the exact captured `libave.so.0.1`, function
`ave_tcon_monitor_ddr_pmic_check_qd_oled()` at Thumb `0x002695fd`.

`[QD_TCON_OFF]` is the local static variable
`qd_tcon_off` at BSS `0x005bfc78`.  It is not returned directly from the
kernel power state, PMIC status, or display state.

## Set path

The function checks adjacent monitor recovery counters before collecting the
current PMIC result:

* recovery counter at state `+0x48` greater than 1, or
* recovery counter at state `+0x4c` greater than 3.

When either threshold is exceeded, it logs/raises KPI fault 9 and stores `1`
to state `+0x58` (`qd_tcon_off`) at `0x00269786`.  Only *afterward* does the
path ask for PMIC status and call `ave_tcon_api_status_check(0)`.

Therefore a later report with kernel TCON power on and healthy PMIC/HSM is not
in conflict with `QD_TCON_OFF=1`: the latter records prior monitor recovery
history.

## Repeated-log path

At the next monitor tick, a nonzero state `+0x58` branches directly to the log
path (`0x00269b98`).  That path reports `QD_TCON_OFF` and returns through the
normal monitor flow.  It does not call QD power control, off sensing, a TCON
write/ioctl, or other panel actuation.  This is why a once-set latch can appear
every second while high-level `lcdon` and kernel power state still report on.

The variable is cleared only by a broader monitor-state reset block that clears
the adjacent counters and latch together; it is not a normal per-tick status
sample.

Consequently it is not evidence that Apps/blank UI causes an ongoing software
power-off command, nor a safe setting to force-clear.  Clearing or bypassing it
would suppress recovery history/policy without addressing the physical black
panel, and is outside the permitted troubleshooting scope.
