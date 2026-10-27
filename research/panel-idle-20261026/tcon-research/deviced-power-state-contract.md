# Daemon power-state and EL background-lock contract

Offline reconstruction on 2026-10-26, using the exact copied `binaries/deviced`
SHA-256 `2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2`.
This closes two deliberately unresolved details in the earlier
[EL policy audit](deviced-el-sensing-policy.md): the numeric power-state names
and the units/consumer of its background-lock argument. It does not establish
an incident cause, current physical light output, or a successful repair.

## Power-state values come from the executable's table

`pm_get_power_state()` at `0x624d0` reads the current index at ELF-relative
`0x12aeb8`, multiplies it by 24, and returns word zero of the `states` table
at `0x1288e4`. `pm_get_power_state_name()` at `0x62568` uses the same index
and table but returns word one. The table is seven 24-byte records. Its
nonzero name/callback pointers are PIE addends with `R_ARM_RELATIVE` entries,
not runtime absolute addresses.

| Index / returned code | Name | Table record |
| ---: | --- | ---: |
| 0 | `start` | `0x1288e4` |
| 1 | `lcdon` | `0x1288fc` |
| 2 | `lcdoff` | `0x128914` |
| 3 | `standby` | `0x12892c` |
| 4 | `suspend` | `0x128944` |
| 5 | `lowpower` | `0x12895c` |
| 6 | `poweroff` | `0x128974` |

`PowerAdapter::getPowerState()` at `0x7c478` tail-branches directly to
`pm_get_power_state`. Thus the earlier EL-start comparison against `3` means
**standby**, while the off-sensing user-start comparison against `1` means
**lcdon**. These are distinct policies, not interchangeable meanings of
"screen on". The public `GetScreenState` integer is a separate accessor;
do not use its integer `1` to infer this enum.

The Display method table's exact `GetPowerState` record at `0x128674`
points to `gdbus_get_power_state` at `0x5dba4`. That callback calls
`pm_get_power_state_name` at `0x5dbd0`; it does not call the separate
`pm_get_power_state_name_excluding_lowpower` helper. This connects a public
`GetPowerState` string to the exact table used by the maintenance guard.
It still exposes daemon state, not measured panel power or emission.

## The EL lock argument reaches GLib unchanged

After its guarded PPI EL-enable attempt returns zero, the previously audited
EL start calls `PowerAdapter::lockBGStandby(5, 0xdbba0)` at `0x7c254`.
That wrapper stores two adjacent words, ID and interval, on the stack and
calls `device_notify(10, payload)` at `0x7c28c`.

The startup initializer `state_tv_lock_init` at `0x3f5e8` is referenced by
the `.init_array` slot `0x128220`. At `0x3f604/0x3f60c` it registers event
type 10 with `lock_background_standby` at `0x66c4c`. The handler resolves
the name `standby`, takes the payload words unchanged, obtains the daemon's
PID, and calls:

```text
pm_lock_state(getpid(), "standby", payload.ID, payload.interval)
```

`pm_lock_state` at `0x66850` validates/resolves the state name and checks
for an existing lock with the same PID/ID before allocating a record.
For a new lock and a positive interval, it stores that interval at record
`+0x108`, moves it unchanged to `r0`, and calls `g_timeout_add` at `0x66974`.
The callback resolves to `pm_lock_timer_cb` at `0x65f08`; it is **not**
directly `pm_unlock_timeout`. The source ID is saved at record `+0x10c`.

The PLT/GOT evidence is `0x3e5fc -> 0x12a64c -> g_timeout_add`.
GLib specifies milliseconds for this argument and permits delayed callbacks.
Consequently `0xdbba0 = 900000` is a nominal **900,000 ms / 15-minute
background-lock expiry interval** on the successfully allocated-lock path.
It is not evidence that EL maintenance itself lasts 15 minutes, that any
timer was actually registered during the owner's event, or that the UI's
60-second response prompt / claimed ten-minute cycle uses this timer.
[GLib API contract](https://docs.gtk.org/glib/func.timeout_add.html).

## Expiry dispatches a notification, then defers unlocking

`pm_lock_timer_cb` reads the lock ID at record `+0x110`. For ID 5 it calls
`device_notify(20, NULL)` at `0x66010`. It then follows the common deferred
unlock path. The [expiry-notifier audit](pm-lock-expiry-notifier.md) resolves
the registered EL timeout handler: for the known legacy/Y23 objects in sensing
state 2 it can request EL-disable through the resolved OledDevice virtual
slot. Thus this is also a conditional EL timeout/stop path, not bookkeeping
alone. Neither that request nor this timer establishes the observed popup's
duration or a physical panel power transition.

At `0x65fd8` the common path calls `g_idle_add_full` with priority zero,
the callback `pm_unlock_timeout` at `0x677f4`, the lock record as data,
and no destroy callback. The timeout callback returns zero. The separately
scheduled unlock callback obtains state/PID/ID from the record, calls
`pm_unlock_state` at `0x67820`, then returns zero. This proves the deferred
call contract, not every subsequent state-policy consequence of unlocking.
The GLib idle API schedules work through its main context; it is not a kernel
panel-reset timer. [GLib idle API](https://docs.gtk.org/glib/func.idle_add_full.html).

`device_notify` at `0x415ac` synchronously visits registered callback entries,
skipping marked/deleted entries and selecting matching types. It does not
propagate each handler's result. `PowerAdapter::lockBGStandby` explicitly
returns zero at `0x7c2b0` after that dispatch. Therefore the adapter's return
does not prove a standby lock or timer was successfully created. The earlier
PPI enable's zero result also does not independently prove panel acceptance;
lower transport suppression is documented separately.

## Live read-only baseline and its limits

[`power-contract-baseline-20261026T110956Z.json`](../overnight/power-contract-baseline-20261026T110956Z.json)
contains a parent-only, read-only capture at 11:09:57 UTC:

* boot ID `00000000-0000-4000-8000-000000000000`, uptime `34606.16`;
* `GetPowerState` returns `lcdon`; `GetScreenState` returns `1`;
* global tracing is off and the private tracing-instance directory is empty;
* transport and command exit zero, no timeout or stderr.

This makes the EL-start `standby` guard false **at that sample**, if evaluated
against the captured daemon state. It does not reconstruct a past transition,
exclude prior maintenance, prove physical visibility or identify the owner's
present location. The owner's photographs document local damage, not a timed
current picture-state observation. No setter, remote key or reboot was sent
for this capture.

## Reproduction and remaining work

Run `PYTHONPATH=/tmp/tcon-capstone python3 deviced-power-state-contract-reproduce.py`
from this directory. It fingerprints the binary, verifies all seven records
and pointer relocations, resolves the PC-relative literals and timer imports,
then disassembles named function bounds respecting `$a`, `$t` and `$d`
mapping symbols. It makes no network calls. The saved raw output SHA-256 is
`a8da12a19b316c66be35b93fb722bab092e3e435611d2b7e9337ffbab8e6bc19`.

Still unresolved: the actual UI caller and timing of the optimization prompt,
the onset-aligned maintenance/power values, and the initiating reason for
physical output loss. No factory/kernel/protection patch or recovery loop
follows from this static contract, and none was deployed.
