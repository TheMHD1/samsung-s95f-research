# FRC output policy: freeze, dormant, patterns, clocks, and UI-content boundary

Scope: offline matched-module analysis (`sdp_frc.ko`, `rosem_frc.ko`,
`sdp_drm.ko`) plus the existing FRC status snapshot. No FRC, DRM, or TCON
control was invoked.

## Cached FRC state has no active obvious hold indicator

The FRC snapshot records all of the following together:

```
drv_ready=1, drv_status=1, dormant=0, seamless_freeze=0,
ONECMD EXCEPTION=NONE, FRC mode=2D, FRC_OUT_UHD_QD_STD
```

It also records active QD165 Video60 operation, normal raster programming,
and periodic black-pixel-shift position updates. This snapshot was collected
after the owner was asleep, so panel emission was not verified at its exact
timestamp. It is a pipeline baseline, not a matched physical-black capture:
the limited cached output has no currently recorded FRC dormant state,
registered seamless freeze, FRC power-down, or pattern command. It neither
proves OLED emission nor rules out a transient command/state that occurred
before the snapshot and was no longer recorded.

## Dormant state is an explicit power-state transition, not a low-APL detector

`sdp_frc_set_dormant` at `sdp_frc.ko:0x3a20` receives an explicit encoded
state word, serializes it under the dormant mutex, saves/disables IRQs on the
dormant transition, and—only for selected requested flags—calls
`sdp_frc_power_ctrl` at `0x6198`. It invokes the dormant notifier chain after
the state work. `sdp_frc_get_dormant_status` (`0x3778`) reads the stored
dormant state under that mutex; it does not examine pixels, APL, UI pages, or
panel brightness.

The DRM side contains registered FRC dormant notifier hooks and explicit
`*_set_frc_dormant_status` functions; this is the DP/CRTC-to-FRC policy path.
It is a control path, not a continuous content classifier. No callsite in the
matched code was found that feeds the raw rendered pixel values of Home, Apps,
or Live into `sdp_frc_set_dormant`.

## Freeze state has two different meanings

* The generic `cmd_proc_Seamless_Freeze` and `proc_Seamless_Freeze` stubs in
  this exact FRC image (`0x19920` and `0x282d8`) simply return zero: they do
  not freeze output here.
* MC seamless freeze is real: `cmd_proc_MC_Seamless_Freeze` (`0x17ec0`)
  dispatches callback slot `+0x98` with value `1`; its unfreeze counterpart
  sends `0`. `proc_MC_Seamless_Freeze` is the lower handler.
* Rosem's independent `RosemFrc_SetFreezeMode` (`0x6298`) maintains
  `m_freeze_mode` and sends FRC command `F104:0x15` for ON and `F104:0x16`
  for OFF when the requested state changes. Its own log strings label those
  actions “Freeze Mode: ON/OFF.” This is explicit command-driven state, not a
  timeout inferred from a sparse UI.

The snapshot says `seamless_freeze=0`, and contains no corresponding F104
freeze log in its limited output. That baseline has no active recorded
freeze-latch indicator; it cannot exclude an earlier transient freeze command
or another downstream cause of a separately observed black event.

## Patterns and low-power art controls are explicit test/display policies

Rosem contains pattern setters before/after DDR, aging/TSI/LD patterns, and
`m_rosem_set_low_power_art_mode` (`0x6050`). The low-power routine maps only
an explicit boolean to FRC `F116` command values `0` or `1`; it has no frame
analysis, APL threshold, or page-id inspection. Pattern functions are likewise
explicit setters with bounded pattern-number ranges. They are unsuitable
recovery experiments and were not present in the status snapshot.

This distinguishes them from AVE/QD dimming telemetry: AVEMonDIM’s APL and
power-consumption calculations are a different userspace/QD policy layer.
The FRC code analysed here handles output timing/raster/commands, not the
observed UI’s average pixel brightness.

## Clock/raster transitions are real downstream output changes—but are mode driven

For `RheaM_QD_V165T`, FRC logs show the chain:

```
OneCmd_Set_Video60 → mode/raster configuration → FRC remap notifiers
→ DP/FRC output configuration → Vx1/TCON output
```

`frc_dev_clk_src` (`0x283d0`) and `frc_dev_clk_divide` (`0x28598`) program
clock/reset muxes based on a supplied mode selector. The snapshot explicitly
logs “Nothing to be done for clk src change” and unchanged divider `1 → 1`.
It also logs Video60, QD165 branch, 2160 active lines, and active FRC stages.
Thus the available baseline contains no recorded clock switch or raster
restart at the time represented by that status snapshot. It cannot establish
what occurred before collection.

The periodic `BLACK PIXELSHIFT` lines are output-position updates at about
61.44-second intervals. They are not a three-second retry timer and cannot
explain the owner’s approximate “empty page longer than three seconds” latch
boundary.

## CRTC/vblank versus FRC/TCON

`sdp_drm.ko` has plane/CRTC mechanisms (`dp_drv_set_plane_mute`, layer freeze,
vblank controls, output blank colour), upstream of FRC. It also exposes FRC
dormant/mute notifier registration. By contrast, `sdp_frc.ko` owns FRC
mode/raster/clock transitions and hands output toward Vx1/TCON; QDF then owns
the panel-side command transport. A compositor frame/capture progressing only
proves upstream CRTC activity. It does not prove Vx1 transport integrity or
OLED emission.

## What this changes

The owner’s richer Apps screen versus sparse Home/Live sensitivity remains a
useful physical hypothesis, but this static pass found no host FRC rule of the
form “low-load/black UI for N seconds → freeze/dormant/power-down.” The
available cached-state baseline reports active normal FRC output; it is not a
matched physical-black sample. The next discrimination should therefore
correlate an already-supported read-only Vx1/FRC status comparison across
confirmed visible and black states, not disable FRC dormant/freeze logic or
force patterns/clocks.
