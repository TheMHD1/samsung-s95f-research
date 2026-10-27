# AVOC `SetPanelMute`: bounded output-gate analysis (offline)

## What the public interface exposes

The captured `org.tizen.tv.avoc.AvOutputControl` interface exposes:

* `SetPanelMute(int on_off) -> int ret`
* `GetPanelMute() -> (int on_off, int ret)`
* `GetPanelMuteCaseStatus() -> (int value, int ret)`

This is a real, ordinary AVOC service interface, rather than a factory QD
option or a raw TCON ioctl.  The current black-state observation was
`GetPanelMute=0`, `GetPanelMuteCaseStatus=0`, with `ret=0`.

## Exact implementation boundary

`libavoc.so` exports the generated D-Bus proxy methods.  The daemon imports
`ppi_ve_set_panel_mute`; the normal public video-enhancement wrapper has the
following two-argument dispatch:

```
ppi_ve_set_panel_mute(r0, r1)
  -> registered AVE implementation vtable slot +0x144(r0, r1)
```

The registered implementation is the AVE path:

```
VideoEnhancerImpl::set_panel_mute(bool, bool)
  -> ave_api_set_panel_mute(int, int)
  -> AVE implementation callback
```

At its lower TCON boundary, `ave_tcon_api_set_panel_mute(int)` uses the
existing AVE driver client with ioctl request `0xc004748c`.  `ave_frc_api_set_panel_mute(int)` is a distinct FRC ioctl path using
`0xc0046606`.  Consequently this is a real output-mute operation; it is not a
software redraw, and it is not evidence of a panel reset or a TCON
reinitialization.

## Guards and side effects proved from the exact daemon binary

The daemon contains the following panel-mute controller diagnostics and
call-site labels:

* `[PANEL MUTE FORCE] onoff(%d)`
* `[PANEL MUTE] panel %s mute`
* `[SKIP PANEL MUTE] ForceMute ON`
* `[SKIP PANEL MUTE] ... power state (%d)`
* `[PANEL MUTE RESET - FREEZE]` and `[PANEL MUTE RESET - BLACK]`
* resolution, VRR, PC-mode, HFR, and picture-setting callers.

That establishes that the public setter controls a *force-mute controller*.
It is also used internally to mask mode changes (not solely to restore a
panel that is already black).  The AVE binary's panel-mute-control routine is
6,040 bytes long and evaluates resolution/video mode conditions before
choosing mute behavior.  It is therefore not justified to treat a `1 -> 0`
sequence as a harmless generic "refresh".

## Consequence for the present failure

The captured black state already has panel mute disabled (`0`) while surface
frames, LVDS-on, logical screen-on, TCON power, PMIC and HSM all remain
normal.  Thus there is no observation that an AVOC panel mute is latched.
Calling `SetPanelMute(0)` alone may at most reassert the existing normal
unmuted state.  A `1 -> 0` pulse deliberately forces a real blanking operation
then releases it; it does **not** call QDF's ordinary power-on/status/recovery
route and cannot be presented as a proven recovery.

If the parent elects to run a tightly bounded diagnostic anyway, its only
sound restoration invariant is an unconditional final `SetPanelMute(0)`, then
read back `GetPanelMute` and `GetPanelMuteCaseStatus`.  This document does not
authorize or perform that operation.  It must not be combined with factory
Low Power Mode writes, fault-monitor suppression, or guessed kernel calls.

## Related AVOC names that are not recovery controls

The same public interface contains `SetFrameUnlock()`, `SetFrcPath(source,
path_422_enable)`, and `VideoScalerUnmuted()`.  Static daemon strings resolve
`SetFrameUnlock` to its video-wall frame-sync helper (with four internal
parameters), while `SetFrcPath` is a source-specific 4:2:2 FRC-path selector.
Neither is a documented FRC clock/panel recovery action.  They are therefore
not candidates for this damaged-panel investigation.  There is no no-argument
read-only FRC/frame-clock health getter in the captured AVOC interface.
