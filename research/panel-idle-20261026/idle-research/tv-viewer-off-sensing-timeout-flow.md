# `tv-viewer` forced off-sensing expiry flow

This is a second, offline-only trace of copied `binaries/tv-viewer`, SHA-256
`d32fbb420d26a27845cbb23ab216de23706c6aeb6376e4107849f74ec5a1883f`.
It follows the forced-warning progress callback independently of the earlier
notification-path note. No notification, timer, sensing request, or display
control was invoked.

## The progress callback has an automatic request branch

`CNotificationManager::m_OnUpdateNotiProgressBarCb(void*)` is a small adapter
at `0x27217d` (12 bytes): when its context argument is non-null it calls
`m_OnUpdateNotiProgressBar()` at `0x26d218`, then returns `1`. The alarm's
interpretation of that return value is not recovered here. The configured
alarm and the counter/expiry CFG below independently establish the intended
repeated60-tick design and its automatic request edge.

The update handler uses a counter at notification-manager offset `+0xd4`:

```text
0x26d2f8  load  [this + 0xd4]
0x26d306  add   1
0x26d308  store [this + 0xd4]
...
0x26d342  load  [this + 0xd4]
0x26d348  pass that value and literal 60 to SetNotificationLeftTimeInfo
0x26d3b4  load  [this + 0xd4]
0x26d3b8  compare with 60
0x26d3ba  branch to expiry block when equal
```

At expiry (`0x26d540`), the handler clears the counter at `0x26d56a` and
reaches the local `CNotificationUtil::RequestQdDisplayOffSensing()` call at
`0x26d5b2`. This is separate from, and in addition to, the explicit button
route. Thus the copied code proves an **automatic off-sensing request after
the progress counter reaches 60 callback updates**.

The handler does not call `RequestQdDisplayElSensing` on that expiry edge.
Its direct target is the off-sensing wrapper (`0x273bd8`), so the previously
identified forced off-sensing notification should not be reclassified as the
long EL/pixel-refresh path merely because the localized message says the later
operation will take about ten minutes.

## What “60” means here, and the remaining clock caveat

`CNotificationUtil::SetNotificationLeftTimeInfo` starts at `0x2727f9`.
The call from the update handler supplies:

```text
r0 = incremented counter
r1 = 60
r2 = time-information output object
```

At `0x27286c–0x2728ae`, that helper computes `60 - counter`, divides it by
60, and also computes the remainder modulo 60 before filling the time display.
This is concrete countdown formatting, not merely a progress-bar percentage.
Combined with the equality test above, the internal deadline is exactly 60
countdown units/updates.

The timer helper has the diagnostic literal “Create 1 min count down callback
to update progress bar.” It calls `Lotus::TCAlarm::Create` with alarm storage
`this+0x9c`, event context `this+0x4`, and the pair `1000, 60` at
`0x26cd54–0x26cd60`, installs the adapter callback at `0x26cd64–0x26cd70`,
and the recovered reset path uses the same `1000, 60` pair. This is an
intended one-minute countdown composed of 60 ticks—not a one-minute update
interval. The forced popup is notification type `1` (*ongoing*), whereas the
ordinary construction uses type `0`.

Static evidence establishes **60 callback ticks**, countdown formatting, and
the automatic branch at tick 60. It cannot independently measure wall-clock
elapsed time if the timer is suspended, coalesced, or delayed; `1000` is an
intended timer parameter, not a captured timing measurement. The diagnostic
and owner’s reported response window are consistent with, but do not upgrade,
that conclusion to a measured 60-second deadline.

## Expiry versus notification events

There are two recovered direct callers of the local off-sensing wrapper in
the relevant code:

| Route | Exact call | Consequence |
| --- | --- | --- |
| Progress expiry | `m_OnUpdateNotiProgressBar`, `0x26d5b2` | automatic request after counter equals 60 |
| Explicit Start Now | `m_NotificationEventCallBack`, `0x26f724` | user-event request, followed by progress-timer destruction at `0x26f72a` |

Framework events `1`, `100`, and `101` are the recovered close/hide/cancel
cases. Their branches destroy the progress timer and do not directly call
`RequestQdDisplayOffSensing`; therefore delivery before tick 60 suppresses the
local automatic route. The event handler’s close/hide diagnostic is at
`0x26ecc4`; its reinforcement-specific handling reads/increments
`memory/tv-viewer/cancel_reinforce_off_sensing_popup` at `0x26ee28–0x26ee4e`.
Static code cannot resolve ordering against a callback that is already due or
in flight, so it does not prove a live framework ordering guarantee.

## Wrapper boundary and failure evidence

`CNotificationUtil::RequestQdDisplayOffSensing()` is a no-argument local
wrapper (symbol start `0x273bd9`, body `0x273bd8`, size 2476). Both recovered
automatic and button routes therefore select the same request policy. It calls
the imported `qd_display_request_off_sensing` API at `0x273cc6`, tests its
return at `0x273cca`, takes zero through success, and branches nonzero to
error logging at `0x27412e`; the local wrapper itself returns `void`.

The copied `libdeviced` boundary independently resolves the imported function:
`qd_display_request_off_sensing` at ARM `0x444a46c0` (24 bytes) sets the mode
argument to `0` at `0x444a46c4` and tail-branches to its `with_mode` service
path at `0x444a46d4`. That is the normal/user-start mode, not an
uninitialized caller argument. The lower wrapper returns a reply integer and
uses `1` for its recovered transport-error path (`0x444a4674`). This remains
static evidence; it does not show any request or reply on the owner’s TV.

The executable imports both `qd_display_request_off_sensing` and the separate
`qd_display_request_el_sensing` service symbol. The local wrapper and its
return log name the off-sensing interface. This static analysis is not
authorization to call either imported service manually, and the lack of a
paired live callback/request record means it cannot establish that the owner’s
popup reached expiry or that the service accepted a request.

## Narrow conclusion

The strongest supported result is: the exact forced-warning family has a
60-unit countdown whose update handler automatically invokes the off-sensing
request wrapper at the terminal count, even without a Start Now button event.
The code also supports an immediate explicit-button route and a separate
close/hide/timeout accounting route. A future read-only correlation needs the
incoming notification ID/key, callback count or request log, and owner physical
observation to determine which route actually occurred.
