# QD OLED monitor task cadence and `qd_tcon_off` rearm boundary

Scope: offline trace of the exact captured `libave.so.0.1`. No TV interaction or state change occurred.

## Configured scheduling path

The QD OLED monitor is called by the normal TCON DDR/PMIC monitor thread, not by the Home renderer or a per-frame dimming callback:

```text
ave_tcon_monitor_start()
  -> pthd_ave_tcon_ddr_pmic_monitor(void *)     Thumb 0x0026bc21
       -> selected by OLED-model result
       -> ave_tcon_monitor_ddr_pmic_check_qd_oled()
                                                    Thumb 0x002695fd
```

The model-selection branch is explicit in the thread routine: `0x0026bd82` calls the WOLED variant and `0x0026bd88` calls the QD OLED variant. The latter is a PLT call to `ave_tcon_monitor_ddr_pmic_check_qd_oled`.

Each normal-thread loop iteration locks `g_tcon_monitor_mutex`, calls `gettimeofday`, builds an absolute timeout with `tv_sec + 1` and `tv_usec * 1000`, and waits through `pthread_cond_timedwait`:

```text
0x0026bd02  pthread_mutex_lock
0x0026bd0c  gettimeofday
0x0026bd1c  tv_sec + 1
0x0026bd20  tv_usec * 1000      # nanoseconds for the absolute timespec
0x0026bd28  pthread_cond_timedwait
0x0026bd2c  check monitor-on state
0x0026bd88  QD OLED monitor call (when selected model is QD)
```

This proves a **configured one-second timed-wait cadence** for the normal QD monitor task. It is not a guarantee that calls occur exactly once per wall-clock second: condition-variable signals can wake it early, lock contention and monitor work can delay it, and it does not run its hardware check if the monitor-on state is not `1`.

The separate `pthd_ave_tcon_ddr_pmic_monitor_short_interval` routine exists, but the QD call is not in that routine. Its timing must not be assigned to the QD ERR_DET branch.

## Relation to the historical recovery interval

Within one QD monitor invocation, an asserted ERR_DET GPIO gets the previously established three-sample retry with two `usleep(100000)` waits. Combining the two proven layers gives a useful but bounded picture:

* normal scheduled check: nominal one-second timed wait;
* fault confirmation inside a check: roughly 200 ms of explicit delay plus I/O;
* terminal monitor actions occur only after the relevant counter/branch conditions.

This does **not** prove an owner-observed three-second blackout timer. It does show that, if the outer task was actually running near its nominal cadence, multi-tick counter thresholds can span seconds; the exact elapsed time remains runtime-dependent and was not measured in an aligned historical trace.

## `qd_tcon_off` writes and rearm limits

The named local static is `qd_tcon_off` at BSS `0x005bfc78` (symbol table). In the QD monitor routine:

* the terminal recovery path stores the latch after its operation-0 power-control branch (the established store site is `0x00269786`);
* a subsequent monitor invocation tests the latch before normal checking and takes the report-and-return route at `0x00269b98` when it remains set;
* the routine also contains its broader monitor-state clear block, which clears the latch together with the adjacent recovery counters. It is not a public rearm interface and is not reached by the latch-report path itself.

The ordinary monitor on/off helper (`ave_tcon_monitor_onoff`, `0x0026b17d`) writes the monitor-on flag and, when it differs from the saved previous flag, sets `g_tcon_monitor_restart = 1`; it does not signal the condition variable or contain a direct `qd_tcon_off` clear. The [subsequent exact runtime map](qd-monitor-runtime-map.md) resolves the QD routine's guarded clear condition as that restart global equal to1, through GOT relocation0x5a7370. The QD routine then clears the bookkeeping/latch and the restart flag. The normal monitor thread itself only waits, checks the enabled flag, and dispatches the model-specific routine; it has no direct latch clear.

Consequently, the captured code proves neither that an ordinary standby/wake re-arms this latch nor that it preserves it forever. A process restart naturally reinitializes BSS, while an in-process broader monitor-state reset can clear the associated group; neither is evidence that a normal standby transition performs that reset. There is no safe reason to force the clear: it would suppress recovery history/state without repairing a fault.

## Measurement boundary

The one-second value is a static configured timeout, not a live timing measurement. To measure actual cadence, an aligned passive kernel/vlog capture must contain consecutive monitor-entry or ERR_DET log timestamps while the relevant monitor is enabled. The retained `paired-capture/apps-visible-control.json` independently shows roughly one-second QD_TCON_OFF reporting timestamps (for example7194.280,7195.280,7196.288). This measures that later visible-state reporting interval, not the historical October12 fault-entry cadence; it cannot time the onset of the current menu failure.
