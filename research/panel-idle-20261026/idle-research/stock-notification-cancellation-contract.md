# Stock notification cancellation contract for the forced off-sensing warning

## Result

The exact forced-warning notification is identifiable inside the stock
notification system by the `tv-viewer` tag
`noti_qd_force_off_sensing_req_tag`.  The copied `tv-viewer` uses the public
`libnotification` symbols `notification_load_by_tag`,
`notification_post_with_event_cb`, and `notification_delete` for that family.

The exact legacy-provider trace establishes the relevant server-side condition:
after `del_noti_single` successfully deletes one or more matching records, it
constructs the legacy GVariant tuple **`(1, priv_id, uid)`** and emits the
`delete_single_notify` signal to every event monitor registered for that UID.
The leading integer is therefore a proven server-side legacy event value of
**1**, rather than an inference from a string or enum name.

The matching client route is also proved: `libnotification.so.0` parses that
signal and dispatches its literal `1` to a registered detailed event callback.
The viewer destroys its timer when its callback receives `1`, `100`, or `101`.
Consequently the *stock notification* route can destroy the local viewer
progress timer when the listener and callback registration are live.  It still
does not cancel off-sensing policy, and static analysis cannot prove runtime
registration state or ordering against a callback already due.

Accordingly, this is a proven route for the **local notification countdown**
only. It does not cancel an already issued off-sensing request or alter the
underlying off-sensing, maintenance, or rearm policy.

No notification lookup, deletion, IPC request, app-control message, or TV
action was issued for this analysis.

## Viewer-local contract

The forced/reinforced warning is notification ID `0x0f`. Its construction has
the tag literal at `tv-viewer` file offset `0x532744`, along with the exact
diagnostics `notification_load_by_tag return NULL`, `notification_post failed`,
and `notification_delete`. The relevant manager symbols are:

| Viewer routine | ARM/Thumb entry | Relevant static behavior |
|---|---:|---|
| `CNotificationManager::ShowNotification` | `0x26e4c0` / symbol `0x26e4c1` | receives the forced warning ID and reaches its stock notification construction path. |
| `CNotificationManager::m_ShowNotification` | `0x270130` / symbol `0x270131` | special ongoing-notification path for ID `0x0f`; uses the forced-warning tag and creates the local 60-update progress timer. |
| `CNotificationManager::m_NotificationEventCallBack` | `0x26e988` / symbol `0x26e989` | receives framework notification events and contains the close/hide/deleted handling. |
| `m_DestroyNotificationProgressUpdateTimer` | `0x26c834` / symbol `0x26c835` | destroys the viewer-local progress alarm. |

The callback explicitly handles event values `1`, `100`, and `101` as
close/hide/cancel cases, including `NOTIFICATION_EVENT_TYPE_DELETED`. Those
branches destroy the local progress timer and do not directly call the
off-sensing request wrapper. In contrast, the button-one and sixty-tick expiry
branches call `RequestQdDisplayOffSensing`. This distinction is important:

```text
viewer receives 1 / 100 / 101
    -> destroy local progress timer
    -> no direct off-sensing request in that event branch

button one or progress expiry
    -> RequestQdDisplayOffSensing()
```

For the reinforced variant, close/hide accounting reads and increments
`memory/tv-viewer/cancel_reinforce_off_sensing_popup`. That is separate from
the notification database operation and should not be mistaken for deletion of
the notification record.

Together with the provider and client trace below, this proves the static
conditional route from a successful legacy delete to this callback's event-1
branch. Its runtime prerequisites (matching authorization, live monitor and
kind-2 callback registration, successful delivery) and ordering against a
callback already due remain unobserved.

## `libnotification` public IPC boundary

The copied `libnotification.so.0` exports the following relevant public
symbols:

| Public symbol | Symbol address | Role supported by this copy |
|---|---:|---|
| `notification_load_by_tag` | `0x46c60f09` | convenience lookup path; corresponding `notification_load_by_tag_for_uid` is the substantive UID-aware implementation. |
| `notification_post_with_event_cb` | `0x46c5cb19` | posts while registering an event callback; this is how a later viewer-local callback can exist. |
| `notification_delete` | `0x46c60f1d` | public delete wrapper. |
| `notification_ipc_request_delete_single` | internal | client-side IPC delete request boundary. |
| `notification_ipc_request_load_noti_by_tag` | internal | client-side tag lookup request boundary. |
| `notification_ipc_event_monitor_init` | internal | event-monitor subscription boundary. |

The library names the data-provider notification interfaces
`org.tizen.data_provider_noti_service` and
`org.tizen.data_provider_noti_event_service`, and object path
`/org/tizen/data_provider_service`. These are **interfaces**, not destination
bus names. The actual destination is addressed below. The client contains the
delete operation string `delete_noti` and the event signal/callback strings
`send_event`, `call event[%d]`, and `call event callback`.

The available client-side data shape is a notification handle plus event
integer (`(vi)` appears in the IPC data). The matching provider and client-side
signal parser are decoded below, so the service-side event rule is no longer
an unresolved static boundary. No live request or registration check was
needed or performed for this offline analysis.

## Tag and identity scope

The tag is not a global capability. The copied library's data-provider SQL
includes these predicates:

```text
caller_app_id = %Q AND tag = %Q
caller_app_id = %Q AND priv_id = %d AND uid = %d
```

It also carries original caller identity fields named
`__AUL_ORG_CALLER_UID__`, `__AUL_ORG_CALLER_APPID__`, and
`__AUL_ORG_CALLER_PKGID__`. Thus the safe static conclusion is that lookup and
deletion are scoped by notification identity (including caller application and
private ID/UID where applicable), not by the bare tag alone. A different app
or UID cannot be assumed to be able to find or remove tv-viewer's notification
solely by reusing its tag string.

## Runtime conditions not observable offline

The provider-to-client callback contract is statically resolved. The following
runtime facts would still require observation at the relevant time; none was
tested here:

1. Whether a matching record is actually deleted: the signal path requires the
   delete primitive to return zero and its deleted-count out-value to be
   positive.
2. Which event-monitor recipient(s) are registered for the retained
   app/UID/private-ID identity at that instant.
3. Whether this particular `tv-viewer` process's event subscription and its
   kind-2 detailed callback registration remain live at the instant of a
   future operation.
4. The ordering of record deletion, message acceptance, asynchronous client
   dispatch, and a progress callback that may already be due.

Therefore this local-countdown effect must not be represented as cancellation
of the underlying screen-optimization, off-sensing, or panel-maintenance
policy.

## Historical acquisition grounding (superseded)

This was the bounded acquisition assessment before the exact provider was
copied.  It is retained as provenance only; the provider is now hash-qualified
below.

| Priority | Candidate | Evidence and limitation |
|---|---|---|
| 1 | The system service registered as **`data-provider-master`** | Confirmed later: the unit names `/usr/bin/data-provider-master` and bus name `org.tizen.data_provider_service`. |
| 2 | `org.tizen.data_provider_noti_service` and `org.tizen.data_provider_noti_event_service` | Earlier wording that treated the interface names as service owners is rejected. They are interfaces; the confirmed destination/owner is `org.tizen.data_provider_service` / `data-provider-master`. |
| 3, presentation only | `/usr/apps/com.samsung.tv.notification-serviceapp/bin/NotificationServiceApp` and `/usr/apps/com.samsung.tv.notification-app/bin/NotificationApp` | Both paths appear in `overnight/optimization-service-catalog-20261026T131321Z.json`; their copied managed assemblies are UI/application candidates, not evidence that either owns the native data-provider D-Bus names. They are not substitutes for the provider server. |
| 4, presentation only | `/usr/apps/global-notif-service/bin/global-notif-service` | Listed by the same service catalog, but no captured string or dependency ties it to `delete_noti` or the two provider D-Bus names. |

The later acquisition confirmed this selection: the target is
`/usr/bin/data-provider-master`, not either notification UI application.

## Inputs and integrity

| File | SHA-256 | Size |
|---|---|---:|
| `binaries/libnotification.so.0` | `16d1aaa56fde2506e80291d7aa39f73db2e4d3b446339fbd439a3d1f23ce7f91` | 199044 bytes |
| `binaries/data-provider-master` | `ce0b2c76f625d66b6967a05e9c743c294661c0f7964227629289e1495fcb7337` | 149396 bytes |
| `binaries/libnotification-ex.so.1` | `948df9c8be3045111a40851d4c8e44824a78522bcbeb40d3b963b8fc13a6d8c7` | 398588 bytes |
| `binaries/tv-viewer` | `d32fbb420d26a27845cbb23ab216de23706c6aeb6376e4107849f74ec5a1883f` | existing copied input |

`libnotification.so.0` is an ELF32 ARM shared object. The tag/event control
flow in `tv-viewer` is cross-checked against the prior offline analyses
`tv-viewer-automatic-sensing-notification.md` and
`tv-viewer-off-sensing-timeout-flow.md`; this note does not modify them.

## Acquired provider: exact D-Bus contract

The previously missing provider is now an exact copied input:
`binaries/data-provider-master`, ELF32 ARM PIE, 149396 bytes, SHA-256
`ce0b2c76f625d66b6967a05e9c743c294661c0f7964227629289e1495fcb7337`.
The recorded systemd unit in
`overnight/runtime-and-provider-targets-20261026T141158Z.json` has:

```text
User=app_fw; Group=app_fw; SmackProcessLabel=System
BusName=org.tizen.data_provider_service
Type=dbus
ExecStart=/usr/bin/data-provider-master
```

Its embedded introspection XML makes the notification management ABI exact:

| Destination | Object | Interface | Method | Inputs | Output |
|---|---|---|---|---|---|
| `org.tizen.data_provider_service` | `/org/tizen/data_provider_service` | `org.tizen.data_provider_noti_service` | `load_noti_by_tag` | `app_id:s`, `tag:s`, `uid:i` | `noti:v` |
| same | same | same | `del_noti_single` | `app_id:s`, `priv_id:i`, `uid:i` | `priv_id:i` |
| same | same | same | `send_noti_event` | `noti:v`, `event_type:i` | none declared |
| same | same | same | `send_noti_event_by_priv_id` | `priv_id:i`, `event_type:i` | none declared |

This confirms that a stock delete is private-ID based after lookup; the bare
tag is only a lookup selector in the `(app_id, tag, uid)` namespace. The
provider also contains sender/record UID validation diagnostics, including
“Invalid sender uid … noti_uid”, and retains the AUL original-caller identity
fields. It is therefore not valid to represent the tag as a cross-app delete
capability.

## Delete and event result after provider acquisition

The provider has separate exported request handlers
`notification_del_noti_single` (`0x15d2c` code),
`notification_send_noti_event` (`0x17318`), and
`notification_send_noti_event_by_priv_id` (`0x174fc` code), plus the internal
delete-processing types `DPMManager::OnDelete`, `DPMReporter::OnDelete`, and
`DPMReporter::DoDelete`.  The matching shared library additionally embeds the
distinct C++ interface `org.tizen.notification_ex` with methods `Post`,
`Update`, `Delete`, `Get`, `Error`, `Count`, `DeleteAll`, `Register`, and
`Unregister`. This establishes a second, C++ notification-ex control plane
alongside the legacy data-provider interfaces; the protocols must not be
conflated.

The relevant legacy handler is now bounded precisely.  The public
`notification_del_noti_single` body (`0x15d2c`, 268 bytes) parses and
validates its request, then enters local helper `0x143c0`.  That helper calls
`notification_noti_delete_by_priv_id_get_changes`; only when the return is
zero and the deleted-count out-value is positive does it take `0x143fe`.
There it constructs GVariant `(iii)` with `r1=#1`, the private ID, and the UID
at `0x143fe..0x14408`, then calls local `send_notify` at `0x14424` with
`delete_single_notify` and interface `org.tizen.data_provider_noti_service`.
`send_notify` looks up monitors registered for the UID, iterates their bus
names, and calls `g_dbus_connection_emit_signal` at `0x1a6f6` for each.  This
is the direct legacy delete-to-signal route.

### Exact legacy client signal-to-callback mapping

The matching `libnotification.so.0` has an independently decoded receive
path.  Its event-monitor initialization at `0x46c5a5d0` subscribes using
`g_dbus_connection_signal_subscribe` (PLT `0x46c47a38`) with:

| Subscription field | Static value |
|---|---|
| sender | `org.tizen.data_provider_service` |
| interface | `org.tizen.data_provider_noti_service` |
| object | `/org/tizen/data_provider_service` |
| member | NULL (all members) |
| callback | Thumb `0x46c5cdf1` |

The subscription identifier is stored at its global state offset `+0x10`.
The callback compares the incoming member to `delete_single_notify` at
`0x46c5cf7a`.  On a match, it parses `(iii)` at `0x46c5cf8e..0x46c5cf9c` into
the server tuple fields, builds the notification object, and calls local
dispatcher `0x46c5ec8c` at `0x46c5cfb2..0x46c5cfb6` with event literal `r1=#1`
and the parsed UID in `r2`.

That dispatcher performs a local hash lookup by UID, walks the associated
registration list, and for a kind-2 registration with non-null callback calls
the detailed callback at `0x46c5ecfe..0x46c5ed06`.  Its fourth argument is the
stored event value, `1`; the user-data, notification type, and constructed
object occupy the preceding callback arguments.  Kind-1 registrations instead
take a separate two-argument callback.  This proves the legacy event payload
is delivered as the detailed callback event integer `1` when all of these
conditions hold: subscription active, signal received, `(iii)` parsing and
object construction succeed, the UID has a local registration, and the
matching registration is kind 2 with a callback.

The C++ `DPMManager::OnDelete` path is a separate notification-ex mechanism;
it must not be substituted for the legacy client route.  It is described below
only to record the distinction, not as evidence for the `tv-viewer` signal.

For contrast, the bounded C++ notification-ex callback chain is:

```text
DPMManager::OnDelete (0x12128)
  -> DPMReporter::OnDelete (calls at 0x11b8c / 0x11bf4)
     -> EventInfo::EventInfo(2, ...) (0x116de..0x116ea)
     -> DPMReporter::DoDelete (calls at 0x11774 / 0x11802)
        -> notification::Manager::SendEvent(EventInfo(type=2), item-list)
           (0xfaf2..0xfaf8)
```

The ARM AAPCS argument setup immediately before that separate constructor is
explicit:
`r0=r4` (the new object), `r1=#2`, `r2=fp`, and `r3=sl`; `r1` is the first
integer constructor parameter.  `DoDelete` receives that same object as its
`r1` argument (`r8` after prologue) and supplies it unchanged to
`Manager::SendEvent`.  The send block is reached only after its preliminary
list-processing result is zero (`0xfaba..0xfacc`); it is not a proof that the
later asynchronous recipient dispatch completed.

The matching sender implementation in `libnotification-ex.so.1` is
`Manager::SendEvent` at `0x35764`.  At `0x35844..0x3584c` it passes the same
`EventInfo` pointer as `r1` to its sender virtual method, after constructing
the event item list.  Thus this decode establishes the provider-side producer
value and the fact that the sender receives that object; it does not invent a
separate deleted-event integer from names or strings.

The provider's public `send_noti_event*` methods separately accept arbitrary
`event_type:i`; they are not the legacy deletion-signal path above.  The
provider can also fail or affect zero records (`Failed to delete noti`, `err`,
`num_changes`, and failure to obtain the private ID).  No IPC action was taken
here.

The safe end-to-end conclusion is therefore:

```text
legacy del_noti_single with return == 0 and deleted_count > 0
  -> emit delete_single_notify(1, priv_id, uid) to UID-registered monitors
  -> libnotification detailed callback event 1 if its subscription and
     kind-2 UID registration are live
  -> tv-viewer callback's event-1 branch destroys its local progress timer
  != cancellation of off-sensing / panel-maintenance policy
```

### Limits of that result

This is an authorization- and state-dependent notification operation, not a
global UI capability.  The request remains scoped by app ID, private ID, and
UID; the provider includes sender/record UID checks, and no signal follows a
failed delete or a delete with count zero.  Even when the local progress timer
is destroyed, this path does not clear the off-sensing result, maintenance
schedule, or `tv-viewer`/app-control policy state.  In particular, it cannot
prove that a reinforced warning will not be rearmed later.

There is also an unavoidable asynchronous race: a progress callback that is
already dispatched or due can still request off-sensing before the delete
signal is received and its detailed callback destroys the timer.  No live
delete, monitor registration check, notification request, or cancellation test
was performed.

### Offline integrity and landmark validation

The exact input hashes were verified locally before decoding:

```text
PASS data-provider-master       ce0b2c76f625d66b6967a05e9c743c294661c0f7964227629289e1495fcb7337
PASS libnotification.so.0       16d1aaa56fde2506e80291d7aa39f73db2e4d3b446339fbd439a3d1f23ce7f91
PASS libnotification-ex.so.1    948df9c8be3045111a40851d4c8e44824a78522bcbeb40d3b963b8fc13a6d8c7
PASS provider landmark: 0x143f8..0x14424 contains r1=#1 and send_notify call
PASS client landmark: 0x46c5cf7a..0x46c5cfb6 supplies r1=#1 to 0x46c5ec8c
```

Those are hash/landmark checks, not a complete control-flow proof or a live
delivery test.  The remaining call- and registration-conditions are recorded
explicitly above.

The parent additionally preserved and ran
[`stock-notification-cancellation-reproduce.py`](stock-notification-cancellation-reproduce.py).
It hash-gates the four relevant copied inputs and checks the provider count
branch/event1/send site, client event1 dispatcher call, and detailed-callback
argument/call landmarks. Its PASS message explicitly excludes full CFG,
identity/registration and live-delivery proof. The complete route remains a
manual analysis of those hash-qualified sources.

### Resolved shared transport input

The matching `binaries/libnotification-ex.so.1` has since been acquired:
398588 bytes, SHA-256
`948df9c8be3045111a40851d4c8e44824a78522bcbeb40d3b963b8fc13a6d8c7`.
It supplies the imported `notification::Manager::SendEvent` and
`notification::Reporter::SendEvent` implementations (code `0x35764` and
`0x2e000`, respectively), `EventInfo::GetEventType`, and D-Bus event
transport.  The sender serializes the event type under the literal key
`__NOTIFICATION_EX_EVENT_TYPE_KEY__`.  Combined with the constructor decode
above, this establishes the *notification-ex* producer's type as `2`.  It is
not the legacy `delete_single_notify(1, priv_id, uid)` transport used by the
`libnotification.so.0` client. It therefore does not alter the separately
proven legacy event-1 callback and local-timer conclusion above.
