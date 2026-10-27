# `tv-viewer` automatic QD sensing notification path

This is an offline, static trace of copied `binaries/tv-viewer`, SHA-256
`d32fbb420d26a27845cbb23ab216de23706c6aeb6376e4107849f74ec5a1883f`
(32-bit ARM, stripped executable). It describes code that can construct and
act on notifications; it does **not** establish that the owner’s television
received a particular app-control event or that any request ran.

The locale extraction independently resolves the resource key
`TV_SID_QD_CBSEP_INFO_MSG_SCREEN_TURN_OFF_RUN_SCREEN_RESTORATION` to the
owner-reported warning:

> For a clearer screen, Screen Optimization will run automatically in a moment.
> The power will be turned off and on for about 10 minutes.

That exact key is materially stronger evidence than a visual/timing guess: it
occurs in the forced QD off-sensing route below. The text’s “about 10 minutes”
describes the subsequent screen-optimization operation, not the popup’s own
countdown duration.

## Producer inputs and notification IDs

`CAppControlShowHandleProcessor::m_ProcessShowQdDisplayNoti(app_control_s*)`
starts at Thumb `0x18f088` (size 2134). It recognizes these keys/paths in its
own read-only data:

| Input/resource at code address | Notification ID passed to `CNotificationManager::ShowNotification` | Static meaning |
| --- | ---: | --- |
| `normal_off_sensing_required` at `0x18f1e4`; resource `TV_SID_QD_CBSEP_INFO_MSG_SCREEN_RESTORATION_CLEARER` at `0x18f1f4` | `0x0e` at `0x18f212` | normal off-sensing message path |
| `force_off_sensing_required` at `0x18f24c`, with `is_reinforce_off_sensing` / `reinforce_off_sensing` state handling at `0x18f272–0x18f29a`; exact owner-text resource at `0x18f2a8` | `0x0f` at `0x18f2c6` | forced/reinforced off-sensing warning path |
| `off_sensing_completed` / `off_sensing_canceled` | `0x10` / `0x11` at `0x18f422` / `0x18f314` | completion/cancel message paths |
| `el_sensing_completed`, `el_sensing_failed`, `force_el_sensing_required` | separate IDs including `0x12` / `0x13` at `0x18f5c8` / `0x18f642` | EL-sensing/pixel-refresh family, not the forced-off warning |

The initial processor uses app-control access/parsing calls around these tests;
the shown values should be read as incoming event-key branches, not as a claim
that a Home or Live screen intrinsically creates them. In particular,
`normal_off_sensing_required` and `force_off_sensing_required` are distinct
inputs and produce different IDs.

## The `0x0f` forced-warning popup and its countdown

`CNotificationManager::m_ShowNotification` begins at `0x270130`. It has an
explicit `ID == 0x0f` split at `0x270278` and again at `0x270672`:

```text
ID != 0x0f  -> ordinary notification construction
ID == 0x0f  -> forced-warning construction (from 0x2706e2)
             -> CNotificationManager::m_CreateNotifiationProgressUpdateTimer()
                at 0x270812
```

The special route creates notification type `1` (*ongoing*) rather than the
normal type `0` form (`0x2706e2–0x2706e4`; diagnostic
`NOTIFICATION_TYPE_ONGOING` at `0x54279c`). Its timer helper is at `0x26cc44`;
its diagnostic is “Create 1 min count down callback to update progress bar.”
The recovered setup calls `Lotus::TCAlarm::Create` with storage `this+0x9c`,
event context `this+0x4`, and numeric arguments `1000, 60`
(`0x26cd54–0x26cd60`); the recovered reset path uses the same `1000, 60`
pair. It installs `m_OnUpdateNotiProgressBarCb` (`0x27217d`) with the
notification context at `0x26cd64–0x26cd70`.

The thunk directly calls `m_OnUpdateNotiProgressBar` at `0x272180`. That
handler increments `this+0xd4` per callback, formats `60 - counter` in
`CNotificationUtil::SetNotificationLeftTimeInfo` (including quotient and
remainder by 60), and tests equality with 60. This proves an intended
60-tick countdown, conventionally one minute for a 1000-unit alarm—not a
one-minute *progress-update interval*. Static evidence does not establish the
timer unit or exact wall-clock deadline under suspension, coalescing, or
scheduler delay, nor that the owner’s prompt was this notification.

## User action, cancellation, and service boundary

`CNotificationManager::m_NotificationEventCallBack` (`0x26e988`) has explicit
handling for `NOTIFICATION_QD_FORCE_OFF_SENSING_REQUIRED` and both of these
outcomes:

* Its button-one/start-now path logs “click on button 1: start now” (string
  built at `0x26f664`) and directly calls the local
  `CNotificationUtil::RequestQdDisplayOffSensing()` wrapper at `0x26f724`.
  It immediately calls `m_DestroyNotificationProgressUpdateTimer()` at
  `0x26f72a`.
* Framework events `1`, `100`, and `101` are the recovered close/hide/cancel
  handling. They destroy the progress timer and contain no direct request
  call. If delivered before the sixtieth callback tick they prevent the local
  expiry route; ordering with an already due callback is not recoverable from
  static code alone. The close/hide diagnostic is at `0x26ecc4`. In reinforced
  state handling it reads/increments
  `memory/tv-viewer/cancel_reinforce_off_sensing_popup` at `0x26ee28–0x26ee4e`.
  This is cancellation/accounting policy, not proof that every close requests
  sensing or that a non-reinforced warning writes that key.

The executable exports the local wrapper at `0x273bd8` (size 2476) and imports
the distinct external service symbols `qd_display_request_off_sensing` and
`qd_display_request_el_sensing`. The imports establish two separate service
interfaces in this binary. The recovered forced-warning button route targets
the **off-sensing wrapper**, not the EL-sensing import. Within that wrapper,
the imported off-sensing API is called at `0x273cc6` with no deliberate
duration argument; `r0` is tested at `0x273cca`, where zero follows success
and nonzero branches to error logging at `0x27412e`. The local wrapper returns
`void`, so neither caller receives that status. In copied `libdeviced`
(SHA-256 `ea3ddbe08dbad2eb3d969d0df434be23afe69eb00921a7969191646e2d1bcb1a`),
the resolved function at ARM `0x444a46c0` sets service mode `0` at
`0x444a46c4` before tail-branching to its `with_mode` path at `0x444a46d4`.
Static analysis here does not substitute a manual call to either API, and it
does not prove that the wrapper reached the external service on a particular
TV event.

## What is and is not matched to the owner report

The message text matches exactly, and its resource key is reached by the
`force_off_sensing_required` / notification-ID `0x0f` branch. That identifies
a concrete software family for the reported “Screen Optimization” warning.
It does not, by itself, prove that the owner saw this particular instance:
the capture lacks a contemporaneous app-control key, notification ID, callback
event, or timer trace. The 10-minute text must not be conflated with the
intended one-minute/60-tick warning countdown or with separate EL-sensing
paths.

No notification, timer, off-sensing request, EL request, or panel control was
sent while performing this audit.
