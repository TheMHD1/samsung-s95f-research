# Content/static-dimming vs. actual panel-power path

## New observation that changes the weighting

After the normal user power cycle, populated Apps stays visibly on even with
the TV screensaver enabled.  `QD_TCON_OFF=1` continues to be logged while the
panel is visibly on.  Therefore that value is a stale monitor-history latch,
not the command causing the present black screen.

## Exact, separately observable paths

### A. Content/static-dimming path

The copied `libave.so.0.1` contains this QD dimming flow:

```
AVOC/AVE vsync
  -> QDDimming::t_vSyncCallBack()                 0x17b35d
       -> QDDimming::m_SetAPLFilter()             0x17b191
       -> QDDimming::m_SetScreenSaver()           0x17b205
            -> initialized backend screen-saver request
                 -> ave_tcon_api_set_qd_ss_brightness(value)
                      -> QDFTcon_SetQdSsBrightness(value)
```

`SetTconScreenSaver(int)` stores an AVE state value at the QD dimming state
offset used by `m_SetScreenSaver`; the latter builds a backend request each
vsync when its feature gates are enabled.  This is a dimming/render pipeline,
not Deviced's panel DPMS state machine.

The captured kernel sequence demonstrates the two values in normal operation:

```
AVEMonDIM: screen saver brightness : 0
QDF: m_ss_brightness[0] Fac_ss:7 value:0
...
AVEMonDIM: screen saver brightness : 7
QDF: m_ss_brightness[7] Fac_ss:7 value:1
```

The observed `0` is an AVEMonDIM/QDF **command value**, not a raw
panel-power-off command.  The captured code and logs do not, by themselves,
prove that it means zero emitted light.  In particular, a later visibly stable
wake also logged the `0`/`7` transitions.  The factory scalar `Screen Saver
Brightness=7` is one input selected by `value=1`, but it is not sufficient to
explain physical blackouts.  The completed `7 -> 0 -> 7` trial changed a
baseline after the panel was already dark; it is a negative recovery result,
not a prevention test or proof of command-value semantics.

### B. Real Deviced/off-sensing panel cycle

In contrast, the known real power cycle at uptime 3864 contains this ordered
signature:

```
Deviced: off sensing required before power off
frc-tcon: panel dpms: off [pid:675,deviced]
QDF: TCON_MUTE_CTRL / QD Mute ==> 1
QDF: QDFTcon_SetQdTconPowerControl: Off(0)
... later ...
QDF: QDFTcon_SetQdTconPowerControl: On(1)
QDF: m_check_tcon_status ... Access Success
```

That sequence resets/mutes/powers the TCON.  A lone AVEMonDIM
`m_set_ss_brightness(...0)` lacks all of these markers.  It should be treated
as an alternate *correlated control-path observation*, not an explanation for
physical black without a matching experiment.

### C. Post-wake TCON health and recovery checks

The full normal wake sequence is observable in the kernel without adding a
probe.  After power-on, Deviced requests the QDF driver to run:

```
QDFTcon_SetQdTconPowerControl(On)
  -> m_check_tcon_status(SetFlag:2)
       -> QD init/read-access check
       -> QD display check (up to three retries)
       -> PMIC / LPDDR status check
  -> QDFTcon_Resume and internal TCON diagnosis
  -> TCON_MUTE_CTRL release
```

Offline `qdf_tcon.ko` confirms `m_check_tcon_status` at `0xb250` performs
bounded reads of the display-status command (initially
`0xf38000000000`, then `...03` in the check path), recognizes the expected
`0xabababab` response, and retries with 50-ms sleeps.  It is reached by the
stock power-on path; it is not a public on-demand health API.  Do not call the
kernel function directly merely to obtain a sample.

The remaining available kernel-exported observations include
`QDFTcon_GetTconStatus`, `QDFTcon_GetPMICStatus`, `QDFTcon_GetHsmStatus`,
`QDFTcon_GetErrDetStatus`, and the SDP frame-lock helper
`tcon_get_wf_framelock_val`.  They are kernel interfaces rather than a
documented userspace diagnostic ABI.  The safe way to observe them is the
vendor's existing monitor/KPI log output, not a new external caller.

### D. Actual monitor-originated reset branches

The ARM/Thumb disassembly establishes the concrete source of *fault-triggered*
TCON power controls.  In `libave.so.0.1`, the `tcon-monitor` routine
`ave_tcon_monitor_ddr_pmic_check_qd_oled()` (`0x2695fd`) owns retry counters
and calls `ave_tcon_qd_set_power_control()` only on its monitor-fault branches:

```
monitor reads/checks fault/status inputs
  -> bounded counter / retry branches
       -> ave_tcon_qd_set_power_control(2)       # reset branch
       -> ... or, after terminal retry threshold ...
       -> ave_tcon_qd_set_power_control(0)
       -> qd_tcon_off = 1
       -> PMIC/status checks and log/return
```

The terminal branch is at `0x269746`: it selects operation `0`, stores the
stale `qd_tcon_off` marker, then makes the PMIC/status calls.  Separate retry
branches at `0x269ae0` and `0x269b26` select operation `2`.  This directly
explains why the marker can remain logged after a later successful picture:
once set, normal monitor ticks take the log-and-return path and do not issue a
new power-control call.

This monitor routine has no direct call edge to `QDDimming::m_SetScreenSaver`
or its screen-saver-brightness request.  The two paths can occur near the same
physical symptom but are distinct in this firmware.  Counter labels/reasons
remain proprietary; in particular, no claim is made that a particular QD
brightness command increments a monitor fault counter.

## Current hypothesis, with limits

The full Apps/screen-saver observation establishes that scene composition
matters, but it does not yet assign causality to QD command value `0`: that
same value occurs during a visibly stable wake.  It does **not** prove that
every historic black event is a static-content effect: prior captures contain
a genuine Deviced off-sensing cycle, and hardware I2C faults have also been
observed.

The former factory test is a negative *recovery* result only.  It does not
test whether suppressing the static entry before it occurs would prevent
blackout.  No supported external AVOC/DBus method to alter `SetTconScreenSaver`
was found; direct PPI/backend/driver calls remain out of scope.

## Conclusive, read-only isolation experiment

With the panel presently visible, retain a timestamped kernel/vlog cursor and
compare two user-driven conditions for the same bounded duration:

1. populated Apps or moving video (control);
2. the sparse/blank Home state that normally goes black (challenge).

For each, capture only:

* kernel lines matching `AVEMonDIM|screen saver brightness|panel dpms|TCON_MUTE|SetQdTconPowerControl|off sensing|required|turn (on|off) TCON|ERR DET`;
* existing read-only Deviced `GetScreenState` and `BurnInProtectionInProgress`;
* physical observation time, not inferred from logical LCD state.

Interpretation:

| Observation at blackout | Conclusion |
|---|---|
| `AVEMonDIM ... brightness : 0`, without the four DPMS/mute/power markers | Evidence of a content/dimming command transition while the TCON is not commanded off. It is not proof that this command caused the black image. Compare with a known visibly stable occurrence first. |
| Full ordered DPMS/mute/power-off signature | A real Deviced/offsensing transition; correlate the preceding logged power requester before changing any policy. |
| Neither signature | Not explained by these software paths; prioritize panel/TCON electrical diagnosis rather than a software override. |

This experiment is safe because it changes no setting and does not suppress
thermal protection, compensation, monitoring, or recovery.
