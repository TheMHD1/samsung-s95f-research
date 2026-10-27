# Maintenance IPC client versus executed EL sensing

## Scope and method

This is an offline audit of the copied firmware pair only. No D-Bus call,
service restart, panel command, network connection, or television-file change
was made. [`maintenance-ipc-client-reproduce.py`](../maintenance-ipc-client-reproduce.py)
hash-guards the exact files before checking these symbols:

| Copy | SHA-256 |
| --- | --- |
| `binaries/libdeviced.so.1.0.3` | `ea3ddbe08dbad2eb3d969d0df434be23afe69eb00921a7969191646e2d1bcb1a` |
| `binaries/deviced` | `2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2` |

`deviced` has `.symtab` ARM `$a`/`$d` mapping symbols. Instruction claims stop
at the next `$d` literal pool; apparent ARM `andeq` after those boundaries is
data. Named functions/direct branches, not a broad linear Capstone sweep, are
used for control-flow claims. Where an Itanium ABI vtable is relevant, its
virtual address point is vtable `+8`, after its two-word RTTI prefix.

## Client ABI and its actual transport

`libdeviced` exports:

| Entry point | Address / size | Static behavior |
| --- | --- | --- |
| `qd_display_request_off_sensing_with_mode(int mode)` | `0x444a450c` / 436 | Builds `GVariant` `"(i)"`, makes a synchronous D-Bus call, parses an integer reply. |
| `qd_display_request_off_sensing(void)` | `0x444a46c0` / 24 | Wrapper; it does not itself start sensing. |
| `qd_display_request_el_sensing(int mode)` | `0x444a46d8` / 596 | Only accepts `0` or `1`; they have different paths. |
| `oled_is_burn_in_protection_in_progress(void)` | `0x444a492c` / 436 | Synchronously queries status; true only for parsed integer reply `1`. |

The common helper at `0x444a5548` invokes `g_dbus_connection_call_sync` through
the PLT with `G_DBUS_CALL_FLAGS_NONE`, timeout `-1`, `reply_type=NULL`, and a
`GError **`. A client request is therefore control-plane IPC, not a direct
call to the panel/PPi sensing implementation.

Embedded identifiers are:

```
org.tizen.system.deviced.display
/Org/Tizen/System/DeviceD/Display
org.tizen.system.deviced
RequestOffSensing
RequestELSensing
BurnInProtectionInProgress
```

Off-sensing has the conventional recovered call shape: `"(i)"` input and
integer reply, using the display service/path/interface literals. EL is exact
as well: the following ARM `add ..., pc` instructions resolve its call tuple
to owner `org.tizen.system.deviced`, path
`/Org/Tizen/System/DeviceD/Display`, interface
`org.tizen.system.deviced.display`, method `RequestELSensing`, with `"(i)"`
input. This calculation uses the PC value of each **add** instruction, not
the preceding literal-load PC.

## Crucial EL mode split

At `0x444a47bc`, `qd_display_request_el_sensing(1)` constructs
`GVariant("(i)", 1)` and calls `RequestELSensing` synchronously. Unsupported
hardware returns `2`; invalid modes return `3`; daemon success is an
integer result.

At `0x444a481c`, `qd_display_request_el_sensing(0)` does **not** call D-Bus.
It calls `device_power_request_poweroff(0x4000002a)` and maps nonzero local
failure to `1`. The audited copies provide no authoritative enum name for base
reason `42`, so it must not be labelled as a particular UI action.

## Daemon: persisted request is not maintenance running

`gdbus_request_el_sensing` is at `0x5bf34`, size 392, with its next `$d` pool
at `0x5c084`. It checks EL support, parses one incoming integer, accepts only
`1`, then calls `vconf_set_int` with:

```
db/sysman/el_sensing_poweroff = 1
```

It returns an integer result variant. It has no direct call to
`el_sensing_request_start` (`0x73944`, size 84). Thus a successful
`RequestELSensing(1)` records user intent only; it does not demonstrate that
physical maintenance began.

The separate consumer is fully visible in named daemon functions:

1. `ELSensing::pixelRefreshRequestByUser()` (`0x73d50`, 236) reads that VCONF key
   using `vconf_get_int` and converts nonzero to true.
2. `ELSensing::onPowerOffRequested(int *reason)` (`0x754bc`) calls that
   predicate at `0x754cc`. A nonzero request reaches the common path only when
   `getPowerOffType() != 6` (`0x755c4..0x755d0`). Type `6` returns without
   consuming the request. If the request is zero, `passedRunCycle()` at
   `0x755f8` can independently join that same common path.
3. The common qualifying path calls `clearPixelRefreshRequest()` at `0x755d8`,
   saves result `1`, and stores `0x4000002a` through `reason` at `0x755e8`.

The proven order is therefore:

```
RequestELSensing(1) -> VCONF user-request flag
power-off-request callback -> request nonzero AND type != 6 -> clears flag -> reason 0x4000002a
power-off-request callback -> request zero AND passedRunCycle AND type != 6 -> same reason
```

`el_sensing_request_start` selects the relevant OLED-family object then calls
either `ELSensing::start()` (`0x74a94`) or the Y23 start function. Its named
direct external caller is `set_initial_power_state` (`0x6913c`), not the D-Bus
handler. The later start logic and its power/standby handling are a separate
contract; see the power-state audit rather than treating this IPC as proof of a
panel transition.

## Answer to the user-refresh workflow question

The binary establishes two independently callable operations:

```
unknown dialog client -- RequestELSensing(1) --> persisted request
unknown dialog client -- EL mode 0? ---------> power-off request 0x4000002a
any qualifying power-off event --------------> consumes persisted request
```

It is plausible that a UI flow uses both, but this cannot be promoted to fact:
the copied evidence has not identified the prompt client, its accept/cancel or
timeout handler, or their ordering. The D-Bus request alone does **not** power
off; a later power-off-request callback is the proven consumer. Conversely,
the mode-0 client call directly requests power off, but no static caller ties
it to the observed dialog. Likewise, reason `0x4000002a` is not unique proof
of a user request because the passed-run-cycle route writes it too.

## Boundaries / safe next evidence

This does not supply a way to force a damaged panel/TCON on, bypass protection,
or recover a physical blackout. It proves only control-plane request handling.
When an observer is available, the useful next acquisition is timestamped,
read-only correlation of D-Bus result/status, allowed VCONF state, power event
and reason, daemon/kernel display logs, and physical panel state. Remaining
unknowns are the dialog client and its timeout policy, the exact reason-name
mapping for `0x4000002a`, and all indirect
callback paths not named/directly traced here.
