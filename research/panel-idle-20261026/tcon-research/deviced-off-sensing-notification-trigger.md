# Off-sensing popup signal boundary

## Result

The exact popup signal literals are in the copied **`tv-viewer`** executable,
not in copied `deviced` or `libdeviced`. Static inspection therefore does not
support attributing `force_off_sensing_required`,
`normal_off_sensing_required`, or `reinforce_off_sensing` to a `deviced`
threshold/counter policy. The copied device-service binaries implement the
off-sensing lifecycle described in `deviced-off-sensing-policy.md`, but do not
contain any of these three message names.

The earlier statement in this document that the producer was not present in
the copied set is superseded by a later acquisition of
`app-control-service`. Its recovered producer-side enum mapping and reinforce
timer boundary are in
[`app-control-off-sensing-producer.md`](app-control-off-sensing-producer.md).
The bounded absence finding here applies to `deviced` and `libdeviced` only;
it was never a global-absence claim.

The presentation receiver is
`CAppControlShowHandleProcessor::m_ProcessShowQdDisplayNoti(app_control_s*)`
in `tv-viewer`, ELF Thumb function address `0x18f089` (code starts at
`0x18f088`; 2134-byte symbol). It compares a decoded incoming string against
the literals and calls `CNotificationManager::ShowNotification` at
`0x26e4c1`. This is the verified path from an already-emitted app-control
message into popup/notification presentation. The producer is now identified
as `app-control-service`; see the follow-up report linked above.

## Exact receiver dispatch

The function handles a decoded string object held on its local stack; the
surrounding app-control extraction helpers are not named in the stripped
executable. The following comparisons and notification calls are direct
Thumb-code facts:

| Incoming literal | Compare site | Presentation result |
|---|---:|---|
| `normal_off_sensing_required` | `0x18f1e4..0x18f1f2` | constructs display text at `0x18f1f4..0x18f20c`, then calls `ShowNotification` with numeric ID `0x0e` at `0x18f212..0x18f216`. |
| `force_off_sensing_required` | `0x18f24c..0x18f25a` | shares the force/reinforce branch below. |
| `reinforce_off_sensing` | `0x18f25c..0x18f26a` | shares the force/reinforce branch below. |
| force or reinforce | `0x18f26c..0x18f2c8` | obtains shared storage at `0x18f26c`, derives `is_reinforce_off_sensing` by comparing against the reinforce literal (`0x18f280..0x18f29a`), stores that boolean with `CSharedStorage::SetValue<bool>` at `0x18f29a`, then calls `ShowNotification` with numeric ID `0x0f` at `0x18f2c6..0x18f2ca`. |

For force, the stored boolean is false; for reinforce it is true. This is a
**presentation-mode distinction**, not proof that the upstream producer uses
different electrical or sensing behavior. A nearby completion/cancellation
dispatch exists (`off_sensing_completed` to numeric ID `0x10` at `0x18f422`,
`off_sensing_canceled` to numeric ID `0x11` at `0x18f314`), reinforcing that
this function consumes named event messages rather than deciding when a power
maintenance operation is required.

The notification manager's own strings include
`noti_qd_force_off_sensing_req_tag`, “show
NOTIFICATION_QD_FORCE_OFF_SENSING_REQUIRED Noti”, and UI button handling.
Those prove the force/reinforce path is capable of a user-visible notification;
they do not reveal the sender's policy condition.

## What the copied `deviced` policy does and does not establish

The existing static analysis establishes a legacy/Y23 selection in
`off_sensing_init`: `config_get_off_sensing_support()` must be nonzero, and
product year `0x17` selects Y23. The selected implementation has structured
power-suspend and explicit user-request routes. That selection governs the
device-service off-sensing implementation, but no static edge from either
variant to any of the three `tv-viewer` signal literals was recovered.

In particular, a search of all printable strings in exact copied `deviced`
and `libdeviced` finds lifecycle messages such as “off sensing required before
power off”, but not `force_off_sensing_required`,
`normal_off_sensing_required`, or `reinforce_off_sensing`. That is only an
absence of **presentation literals**. It does not exclude upstream enum
production: the copied `qd_get_state` classifier produces numeric result `1`
or `2`, which app-control-service later maps to those two names. The
classifier thresholds and its non-passive query contract are documented in
`qd-display-state-query-contract.md`; the app-control consumer mapping is in
`app-control-off-sensing-producer.md`.

It remains unsound to disable a device flag merely because a presentation
literal is absent: the recovered evidence distinguishes device-service
classification from app-control UI transport, and neither report establishes
that a particular flag safely suppresses the panel-maintenance operation.

## Output boundary and remaining unknowns

```
app-control-service (recovered separately)
  -> app-control payload with named QD display notification
  -> tv-viewer CAppControlShowHandleProcessor
  -> CNotificationManager::ShowNotification(ID 0x0e or 0x0f)
  -> popup/notification UI
```

The receiver has no recovered call from these branches to the copied QD PPI,
AVE, GPIO, TCON, or off-sensing command APIs. That absence is not a global
claim about other processes. It is only the
bounded fact that the examined receiver branch is presentation handling.

## Integrity and offline reproduction

| File | SHA-256 |
|---|---|
| `binaries/tv-viewer` | `d32fbb420d26a27845cbb23ab216de23706c6aeb6376e4107849f74ec5a1883f` |
| `binaries/deviced` | `2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2` |
| `binaries/libdeviced.so.1.0.3` | `ea3ddbe08dbad2eb3d969d0df434be23afe69eb00921a7969191646e2d1bcb1a` |

The direct receiver disassembly can be reproduced offline with Capstone in
Thumb mode over `tv-viewer .text` range `0x18f088..0x18f8de`. It must not be
used as authorization to send an app-control message or modify an off-sensing
setting.
