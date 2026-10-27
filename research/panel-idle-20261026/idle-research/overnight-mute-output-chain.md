# Full-Home AV mute versus panel-emission path

## Proven CSFS sequence

CSFS `FullView::ShowModeStateChange` invokes `RetryMuteAV(3)` only on the
global show-mode `2 -> 1` entry path. `RetryMuteAV` immediately invokes
`TVServiceController.MuteAV(1)`, writes NUI hint
`wm.video.animation.mode.id = "0 0 0 0 0"`, then repeats only while the view
remains shown, mode 1, and focused. The three retries are separated by 100 ms;
there is no unmute call in this CSFS method.

This is an AV/session operation plus a compositor hint. It is not, in CSFS
itself, a DPMS/TCON/emission command.

## AVOC panel-mute implementation boundary

The copied `libavoc.so` exposes distinct D-Bus client methods:

* `avoc_set_panel_mute` at `0x472b6c65`;
* `avoc_get_panel_mute` at `0x472b6ecd`;
* `avoc_get_panel_mute_case_status` at `0x472b69ed`;
* `avoc_video_scaler_unmuted` at `0x472e513d`;
* audio mute is separately `avoc_audio_mute` at `0x472e35b5`.

The matching `avocd` strings identify a separate `CAvocdPanelMuteCtrl` path
and AVE PPI `ppi_ve_set_panel_mute`. Its logged guards include initialized
state, power state, force-mute, source/resolution/VRR/PC-mode transitions, and
NewHome state. It also has explicit reset cases labelled `FREEZE` and `BLACK`.
Thus AVOC panel mute is a controlled AVE/video-plane transition mechanism,
not automatically proof of OLED-emission-off: its state must be observed
independently from Deviced DPMS/TCON mute/power markers.

## What is and is not linked

No copied CSFS IL call from `RetryMuteAV` directly calls libavoc
`SetPanelMute`, `ppi_ve_set_panel_mute`, Deviced DPMS, or TCON power. The
matching `TVServiceController.MuteAV` implementation has now been copied and
is recorded below: it routes through `IAVControl` video/audio mute rather than
directly through AVOC. There is still no proof that a Settings overlay performs
the required global `2 -> 1` FullView transition.

Accordingly, Settings/full-Home entry can plausibly produce a short AV
mute/hint burst, but persistent physical black after several seconds is not
explained by this finite 3x100-ms CSFS loop alone. The decisive existing-log
signature is time-aligned CSFS `RetryMuteAV`, AVOC `[PANEL MUTE]`,
`GetPanelMute`/case-status, and kernel `TCON_MUTE_CTRL`/DPMS records.

The Ugoos audio-pause/brief-black observation must **not** be attributed to
this route unless a CSFS global `2 -> 1` entry is present immediately before
it. The owner did not report Home/Settings before those playback events, so
they remain a separate AV/session, FRC, or output-path symptom.

## Resolved bridge: exact Common.dll implementation

The acquired matching `Tizen.TV.Service.ViewPlugin.Common.dll` resolves the
bridge. `TVServiceController::MuteAV` (method token `06000118`) queues a
worker at `<>c__DisplayClass21_0::<MuteAV>b__0` (token `06000177`), not an
AVOC call. When
the TV-service session exists, that worker creates `TVServiceAPI` AV control
and calls both `IAVControl::MuteVideo(onoff)` and
`IAVControl::MuteAudio(onoff)`. Failure of video mute does not prevent it from
attempting audio mute. Thus CSFS `RetryMuteAV(3)` can explain the owner's
brief Ugoos **audio pause plus blackout** as a TV-service AV-plane mute burst;
it is not a direct OLED/TCON emission control.

`TrySetPanelMuteOnResume` (method token `06000121`) is a separate path. It first skips when the previous
fullscreen app equals the stored UG-detail return app. Otherwise it reads
`AvocGetPanelMuteCaseStatus`; only when that result is zero and the method's
internal resume condition is one does it call `AvocSetPanelMute(1)`. The
captured IL is sufficient to prove the condition and call, but does not name
the compiler local's originating state field. This provides
a concrete FullView-entry route to AVOC panel mute, distinct from `MuteAV`.
Its matching unmute/reset behavior remains in AVOC's panel-mute controller;
no CSFS unmute is present in `RetryMuteAV` itself.

## Native AVE panel-mute implementation

AVOC's `ppi_ve_set_panel_mute` import is distinct from the screen-saver PPI.
The matching AVE exports resolve the downstream implementation chain:

```
impl_set_panel_mute                 0x002a3ca1
 -> VideoEnhancerImpl::set_panel_mute(bool,bool) 0x0029eb75
 -> ave_api_set_panel_mute           0x00277791
    -> ave_frc_api_set_panel_mute    0x0023f8c5
    -> ave_tcon_api_set_panel_mute   0x002527cd
```

This is the critical distinction: unlike CSFS `MuteAV`, AVOC panel mute can
reach both FRC and the TCON mute API. The copied AVE code also exposes separate
resolution/photo checks before panel-mute use (`ave_api_check_panel_mute_for_resolution`
at `0x00277acd`, and photo check at `0x0027d8c1`). The exact AVOC controller
arguments, public-getter limitations, and reset branches are now recovered in
[`overnight-avocd-controller.md`](overnight-avocd-controller.md): native
`ResetBlack` attempts `ppi_ve_set_panel_mute(0, 0)` but clears controller state
without checking whether the downstream PPI succeeded. No claim is made that a
FullView entry leaves this native mute latched.
