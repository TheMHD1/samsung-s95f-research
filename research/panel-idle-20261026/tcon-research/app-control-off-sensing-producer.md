# App-control off-sensing notification producer

## Result

Offline inspection of the copied `binaries/app-control-service` establishes
the producer boundary for named QD off-sensing notifications. Its
`ShowQdDisplayNotiByTV(qd_display_state_e)` (Thumb code `0x16c64`; symbol
`0x16c65`) builds a state-to-name table and calls
`util::launch_app::LaunchOtherApp` (Thumb `0xd1f8`; symbol `0xd1f9`). The
same executable contains `org.tizen.tv-viewer`, `NoRaiseWindow`,
`show_qd_display_notification`, and `show`. This is notification transport,
not a recovered TCON/GPIO/panel-control route.

## Recovered mapping

The static initializer materializes keys `1` through `7` and the consecutive
read-only strings at `0x22e00..0x22e94`:

| QD enum | Event |
|---:|---|
| 1 | `normal_off_sensing_required` |
| 2 | `force_off_sensing_required` |
| 3 | `off_sensing_completed` |
| 4 | `off_sensing_canceled` |
| 5 | `el_sensing_completed` |
| 6 | `el_sensing_failed` |
| 7 | `force_el_sensing_required` |

This is code/data evidence rather than label inference.
`QdDisplayStateChangedCb` (code `0x1714c`) gets a QD display state, compares
it with `4`, then calls the translator only on equality; that callback emits
the canceled lifecycle event, not a normal/force policy decision.

The executable imports `qd_display_subscribe_state_changed` and
`qd_display_get_display_state`; its callback uses the latter. Its separate
`CheckQdDisplayState` (code `0x1764c`) also routes state to this translator.
Thus normal/force originate upstream as QD enum 1/2; this service maps them
to presentation events. The independently traced receiver maps normal to
notification ID `0x0e` and force/reinforce to `0x0f`; see
`deviced-off-sensing-notification-trigger.md`.

`qd_display_get_state` is a different imported API. It is specifically not a
safe manual observer: provider analysis shows that its `GetQDDisplayState`
path can acknowledge/save results while classifying them. This work made no
live query. The normal startup callback above can nevertheless invoke that
API as part of the TV's existing lifecycle.

## Concrete classifier and consumer control flow

The upstream classifier is now traced in the exact copied device-service
images, in
[`qd-display-state-query-contract.md`](qd-display-state-query-contract.md).
`qd_display_get_state()` is a DBus client for `GetQDDisplayState`, whose
daemon handler calls `qd_get_state` at `0x71520`. Subject to its support,
factory-disable, and ready checks, that classifier compares its returned
off-sensing time with `0xef` and `0x2d0`:

| Classifier result | Off-time range on the eligible path | Consumer event |
|---:|---|---|
| 0 | at or below `0xef` | no required-off event |
| 1 | greater than `0xef`, below `0x2d0` | `normal_off_sensing_required` |
| 2 | at least `0x2d0` | `force_off_sensing_required` |

The numeric boundaries are exact; their time units are not established by this
evidence. In particular, the directly read stored `db/sysman/off_sensing_time`
value must not be substituted for the classifier's live object-derived value
to assert a current popup state. The same linked report documents why this
query is not safe as an observer: some result classifications acknowledge/save
state.

`CheckQdDisplayState` is the delayed startup consumer of that classifier. Main
setup registers a one-second GLib timeout; its local callback begins at
`0x14950`, counts invocations, and calls `CheckQdDisplayState` at `0x149c4`
on the `count == 25` branch (the sixth callback after initial count 30). That
direct caller is not exported `Init(APP_DATA_S*)` at `0x1492c`.

`CheckQdDisplayState` validates `(state - 1) <= 6`, then uses the seven-entry
Thumb branch table at `0x176ae`. Values `1`, `2`, `3`, `5`, and `6` flow
directly to `ShowQdDisplayNotiByTV(state)`. Value `4` is the cancellation
path: power-state `0` shows state `4`, while value `2` records a deferred
presentation. Value `7` calls separate force-EL policy
`CheckToShowForceElSensingPopup`, not force-off sensing. Out-of-range values
log the invalid-state case and do not use the normal/force map.

## Reinforce

Reinforce is a separate timer route, not enum 1 or 2.
`CReinforceOffSensingTimer::t_ProcessTimeout()` (code `0xd378`) calls the
same launch helper; nearby is `reinforce_off_sensing` (`0x1f9c8`). The binary
also contains `Is48HoursOffSensingPopupSupport`, feature key
`com.samsung/featureconf/product.adaptive_off_sensing_support`, named setup
paths `Set48HoursReinforceOffSensingPopup` and
`Set4HoursReinforceOffSensingPopupCb`, and persistent/cancel keys
`db/tv-viewer/reinforce_off_sensing_time` and
`memory/tv-viewer/cancel_reinforce_off_sensing_popup`.

The timeout path calls `device_power_get_state` and bypasses launch unless its
return is zero. It then reads
`memory/enterprise/swupgrade/working_status`: value `1` suppresses launch and
sets `db/app-control/need_show_off_sensing` true; otherwise it sets the
working status to `2` and launches reinforce. The non-normal-power log is the
other explicit suppression branch. This describes notification policy only;
it does not authorize changing either key.

The feature key above gates both startup Set48 and the cancellation watcher.
`Set48HoursReinforceOffSensingPopup` constructs its `CTimerNode` at `0x12820`
with default period `0x2a300` = `172800` seconds (48 hours). A valid positive
`db/tv-viewer/reinforce_off_sensing_time` value is multiplied by `60` before
the timer-period virtual call at `0x128c2..0x128d0`; its log consequently
labels the input “min(s)”. A missing or non-positive key does not become a
zero-length period: it retains the constructor's 48-hour default.

The timer's time base is seconds: the framework combines a steady-clock value
with a nanoseconds-to-seconds divisor and runs its processing through
`g_timeout_add_seconds(1, ...)`. The cancellation watcher is triggered by
`memory/tv-viewer/cancel_reinforce_off_sensing_popup`, but its callback ignores
the supplied keynode value and re-reads
`db/tv-viewer/reinforce_off_sensing_time`. It recreates timer ID 13; a valid
positive value from that **persistent reinforce-time key** is scaled by five
seconds, otherwise it materializes `14400` seconds at Thumb `0x11ea8`, the
four-hour fallback. These are exact timer-policy facts, but do not prove that
a stored value reflects current panel operation or make either setting safe to
alter.

## Integrity

| Item | Value |
|---|---|
| Input | `binaries/app-control-service` |
| SHA-256 | `f2adcb0ab496e555f6c2b40c854240956860d84909daf83be9fc6017bb7001c6` |
| Capture | `overnight/optimization-app-control-inventory-20261026.json` (`/usr/bin/app-control-service`, 161812 bytes) |
| Form | ELF32 ARM PIE; odd symbol addresses are Thumb entries, code begins at preceding even address |

The passive process/key snapshot at
`overnight/optimization-notification-process-state-20261026T134819Z.json`
records app-control-service PID 1519 (start ticks 2667), tv-viewer PID 427
(start ticks 253), `CLK_TCK=250`, and working status `0` at the capture time.
It involved no manual restart or write. It is not proof that the delayed
startup callback has already run, cannot be re-armed, or that a notification
will not occur later.

Verification is offline-only: hash the copy and inspect the named function and
seven strings. Do not turn this into an app-control request or QD API probe.
