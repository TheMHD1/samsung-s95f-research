# Physical-black topology and host-visible link analysis

Scope: offline analysis of the matched S95F kernel modules and already
captured logs. Nothing here sends a command to the TV or changes a setting.

## Evidence boundary

The owner reports a local irregular black spot and a one-pixel vertical black
line above it. That is physical-panel-local damage, not a UI layout issue. It
makes a panel-side or panel-link marginal condition a credible contributor to
the full-screen blackouts.

Two symptom classes must remain separate:

| Observation | Bounded conclusion |
|---|---|
| Internal Home/Live can be physically black while a rich Apps composition continues; audio can continue; host LVDS/TCON indicators are on; AVOC mute is zero; QDF power query returns `1`. | Not solely an HDMI source, HDMI cable, or source-selection fault. The failure is downstream of normal composition, or is emission/link behavior that these host indicators cannot see. |
| Ugoos playback is mostly stable but has rare brief blackouts with audio pause. The wiring is **Ugoos → JBL Bar 1300X HDMI input → TV via JBL HDMI output**. | The pause may originate in the Ugoos/JBL HDMI chain as well as the TV; do not attribute that audio symptom to a TV TCON. It does not explain the internal-Live/UI latch. |
| Live is worse; a full Settings/Apps screen can remain visible. | Compatible with content/cadence/output-mode sensitivity, but not proof of static dimming. SS brightness 7→0 did not recover an already-black state, and static QDF code has no direct UI-content caller. |

Samsung documents the S95F as a One Connect model, and its black-screen guide
says the One Connect cable is the hub link for external devices and should be
checked for damage/seating. That is a legitimate separate external-path check,
not an explanation for the demonstrated internal compositor-to-panel case.

Sources: [S95F specification sheet](https://images.samsung.com/is/content/samsung/p6pim/us/qn55s95fafxza/specsheet/us-specsheet-qn55s95fafxza-547829267.pdf), [Samsung One Connect guidance](https://www.samsung.com/us/support/troubleshoot/TSG10002233/).

## Matched software/hardware path

```
Ugoos → JBL Bar HDMI path ─┐
Tuner / internal apps ─────┼→ SoC composition → SDP FRC → SDP TCON/Vx1
                           │                              │
                           └────────────────── One Connect panel link → QD TCON → OLED drivers
```

The FRC snapshot identifies `RheaM_QD_V165T`, chip/board id `1`, and FRC
output frequency `165`; the cached TCON firmware separately reports `OutPut
Type : Vx1` and `OutPut Hz : 120 Hz`. Those are different pipeline stages and
snapshots, so they are not contradictory. Neither is a panel-light sensor.

No model-specific One Connect or panel cable pin assignment is in the captured
firmware or Samsung model documentation. A pinout must not be guessed from
the generic Vx1 label.

## Exact static link/power findings

* `sdp_tcon.ko:frcext_get_vx1_lock_status` (`0x91a8`) runtime-PM-acquires the
  Vx1 block, reads a status word at FRC-object offset `0x3040`, masks `0x5`,
  and returns true only when the result is `0x4`; then it releases runtime PM.
  This is a real link-lock diagnostic, not OLED emission and not recovery.
* `sdp_tcon.ko:sdp_get_vx1_status` (`0x9270`) combines several status words
  including that same lock test. `TCON_GetVx1CmdStatus` only forwards to a
  registered driver callback and does not itself make a user-facing ABI.
* Active paths exist but must not be used as probes: TCON power/reset/DPMS,
  Vx1 IP reset, FRC timing reset, QDF power control, and TCON mute. They are
  distinct from the passive `QDFTcon_GetPowerLevel` query already captured.
* During a physical-black capture the exact AVEMonDIM query returned QDF raw
  power level `1`; it does not validate emitted light. See
  `overnight-passive-black-i2c-decode.md`.
* `QDFTcon_TconMonitorTask` (`qdf_tcon.ko:0xa340`) is also not a hidden
  recovery/power-cycle loop. When its guard flags permit, it performs a
  single `F380...0001` status read and compares the response with the expected
  `0xABABABAB` pattern (with two alternate configured formats); it writes an
  error result back to its caller. This function contains no call to QDF power
  control, mute, reset, LPM, or screen-saver setters. Thus stopping that
  monitor would remove a diagnostic, not cure the physical-black condition.
* `QDFTcon_SetRecoveryMode` (`0xe00`) is only a parameter/output validation
  wrapper in this exact build; it assigns output value `0x11` and logs. It is
  not evidence of a recover-the-panel operation and is not a candidate call.

## Timing and next passive discriminator

No exact three-second timeout was found in the matched host QDF/FRC/TCON code
or available logs. The only precise periodic output operation in the FRC log
is black pixel shift roughly every 61.44 seconds, which does not match the
owner’s approximate multi-second latch boundary. Treat that boundary as an
experiment criterion, not an identified timer.

For a future owner-observed black event, compare an existing stock read-only
Vx1 lock/status surface between visible and black states, alongside the
existing compositor/QDF query:

* status differs with QDF level still `1`: evidence shifts to Vx1/One
  Connect/TCON transport;
* status matches: evidence shifts below the host-visible Vx1 boundary toward
  the TCON-to-panel drivers/damaged panel;
* an Ugoos+JBL audio pause concurrent with the first case remains an external
  HDMI-chain event until independently traced.

The read must use a reviewed existing read-only status interface. Do not call
kernel exports/private ioctls, write debugfs, reset Vx1/TCON, mute, or power
cycle hardware to obtain this measurement.

## Current causal boundary

Current evidence supports a content/output-sensitive panel-side blackout or
latch which is not equivalent to a commanded screen-off and which was not
recovered by the static-brightness test after latch. It also leaves a separate,
rare Ugoos/JBL/HDMI-chain interruption plausible for audio-pausing movie
glitches. No safe host command has been identified that can force physical
OLED emission after latch while retaining the panel’s fault, thermal,
compensation, and recovery protections.
