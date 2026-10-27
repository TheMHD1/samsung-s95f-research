# Settings overlay / Full Home path (static CSFS audit)

The copied CSFS binary contains the whole-Home `FullView` controller. Its
`ShowModeStateChange` is the only observed Home-side path that calls
`TVServiceController.TrySetPanelMuteOnResume`, registers AVOC handling and
invokes `RetryMuteAV(3)`. It is driven by global show-mode entry/exit, not by
an Apps/For You/Live tab ID or by a Settings tile selection.

`FullView` also has explicit page/sidebar/modal mechanics (`ShowSystemPage`,
`SetSystemCurrentTile`, `OnShow`, `OnHide`, `HideRootLayout`, and animation
completion callbacks). These can change overlay visibility and focus, but the
complete CSFS IL audit found no direct call from those Settings-overlay methods
to `AvocSetNewHome`, `SetHomeUI`, `SetScreenProtectAppLaunched`, AVE dimming,
DPMS, TCON power, or a graphics-mode setter.

Therefore the owner’s observed Settings-overlay/flicker correlation is real
evidence that an opaque/richer compositor scene changes the symptom, but it
does not establish a software panel-mute command. The plausible indirect
boundary is global FullView show mode/window visibility: it may cause the
existing AVOC NewHome/panel-mute coordination to run while Settings appears.

For a future passive transition capture, timestamp CSFS messages containing
`ShowModeStateChange`, `TrySetPanelMuteOnResume`, `RetryMuteAV`, `OnShow`,
`OnHide`, `ShowSystemPage`, `SetWindowVisible`, and AVOC `New Home`/
`PanelMute` logs alongside compositor and DRM state. A different FullView
show-mode or AVOC state would be a concrete lead; identical state would shift
weight toward composition/output/panel interaction rather than Settings policy.

No Settings application binary is currently copied, so this conclusion is
limited to the CSFS side and does not claim Settings itself has no display API.

## Exact FullView mute ordering and retry semantics

`ShowModeStateChange` only enters this sequence when the **new** show-mode is
`1` and the prior show-mode is `2`. It first requests `TvsExclusiveAVSession(1)`.
If the window is focused (except a Ballie-support special case), it calls
`TrySetPanelMuteOnResume`; it then records show state `full`, registers AVOC
events with `(false,false)`, calls `RetryMuteAV(3)`, disables auto-hide and
turns off PIP. Leaving prior full mode calls `ExitFullHome(0)`, stops the
spread-animation timer, and restores auto-hide.

`RetryMuteAV(3)` is not a three-second timeout. It immediately calls
`TVServiceController.MuteAV(1)`, writes NUI auxiliary hint
`wm.video.animation.mode.id = "0 0 0 0 0"`, then starts a worker. The worker
sleeps **100 ms** before every loop iteration; while `CurrentState.Shown`,
`CurrentMode==1`, and `IsFocused(false)` all hold, it calls `MuteAV(1)` again,
rewrites that hint, and decrements the count. Thus the nominal three attempts
are compressed into roughly hundreds of milliseconds, and stop early when
focus/show/mode changes. It does not perform an unmute call in this method.

This proves a short FullView-entry mute/hint burst exists. It does **not** show
that merely opening Settings creates the `2 -> 1` global show-mode transition;
the Settings overlay may be inside an already-full state and therefore skip
this branch entirely. The decisive passive evidence is the CSFS retry log plus
AVOC panel-mute state at overlay-open time.
