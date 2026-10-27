# QD display-state query: result acknowledgement is a side effect

The client API `qd_display_get_state()` is not a passive snapshot of stored
maintenance results. Its daemon implementation can acknowledge/reset those
results while classifying its reply. It was **not manually invoked by the
investigation** in this pass; natural service code can call it independently.
The parent instead used direct `vconftool get` reads of named stored keys;
the raw records preserve those values without this query's acknowledgement.

## Exact source identity and client boundary

* `binaries/libdeviced.so.1.0.3`: SHA-256
  `ea3ddbe08dbad2eb3d969d0df434be23afe69eb00921a7969191646e2d1bcb1a`.
* `binaries/deviced`: SHA-256
  `2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2`.

The client function at ARM VA `0x444a4384` issues `GetQDDisplayState` on
destination `org.tizen.system.deviced`, object
`/Org/Tizen/System/DeviceD/Display`, interface
`org.tizen.system.deviced.display`. Its PC-relative literals resolve these
strings in the copied image. This differs from
`qd_display_get_display_state(context)` at `0x444a4364`, which returns the
first word of a non-null context or-1 for null; the similarly named functions
are not interchangeable.

The daemon handler `gdbus_get_qd_display_state` calls `qd_get_state` at
`0x5c0c8`, logs the result and builds an integer reply. It is the called
classifier that has the relevant acknowledgement paths.

## Conditional writes reached by `qd_get_state`

The classifier starts at `0x71520`. After its model/support checks, it reads
off-sensing time, EL time/recommended cycle and saved results. Its result
handling includes these exact calls:

| Site | Action | Boundary |
| --- | --- | --- |
| `0x715c8` | `el_sensing_notify_saved_result_read()` | Reached for the relevant saved EL-result classification, not on every query. |
| `0x71654..0x71658` | pass4 to `off_sensing_save_result()` | Reached for the corresponding saved off-result classification before returning its event code. |

The EL wrapper selects legacy/Y23 at `0x73b68`; the two object callbacks
(`0x75a68`, `0x7e280`) each pass result4 to their `saveResult` implementation
(`0x74de8`, `0x7d87c`). The off wrapper selects its family at `0x767c0`,
tail-branching to legacy `OffSensing::saveResult` (`0x77340`) or Y23
(`0x7ecd0`). Both off implementations call `vconf_set_int` through PLT
`0x3d438`, which resolves via jump slot `0x12a060`; the installed key is
`db/sysman/off_sensing_result`. A write failure is possible, but the existence
of the attempted write path is enough to reject a pure-read interpretation.

The classifier also checks the off-sensing factory-disable/ready conditions
and compares its returned off-time against `0xef` and `0x2d0`. Those numeric
comparisons are not a license to infer a live popup, applied sensing state,
or time units from a separately read stored integer. Full event policy is
traced separately in the app-control producer report.

## Passive stored values actually obtained

The direct reads at13:35:07 UTC, uptime43316.46..43316.75, same recorded boot,
returned these Int32 values with each CLI status0:

| Stored key under `db/sysman/` | Raw value |
| --- | ---: |
| `off_sensing_result` | 0 |
| `el_sensing_result` | 4 |
| `off_sensing_time` | 1789 |
| `el_sensing_time` | 5752 |
| `off_sensing_count` | 6 |

Source: `overnight/optimization-maintenance-stored-state-20261026T133506Z.json`.
These are database values, not fresh hardware samples, physical picture
observations, current object-state measurements or proof of when a cycle ran.
No key was set, no result was acknowledged through the QD query, and no
notification, sensing, GPIO or power control was invoked for these reads.

Earlier direct reminder-key reads at13:29:10 are separately retained in
`overnight/optimization-notification-state-20261026T132909Z.json`:
`need_show_off_sensing=False`, reinforce time0, cancel count0, force-EL count0.
These fields have distinct policy roles. Zero/false is not a global
notification-disable or proof of no pending/active maintenance.

Natural startup is one such caller: the app-control service's delayed startup
callback reaches `CheckQdDisplayState`, which calls the exact side-effecting
query. A manual-read exclusion does not prove that no service invocation ever
ran. See the [producer trace](app-control-off-sensing-producer.md).

Reproduce source hashes,14 exact ARM instruction sites, setter relocation/key
and client binding strings offline:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-display-state-query-contract-reproduce.py
```

The conditional reachability and surrounding classifier CFG were reviewed
manually; the script does not mechanically prove every policy branch.
