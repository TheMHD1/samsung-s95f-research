# QD monitor lifecycle caller boundary

This is a bounded offline caller audit of copied `libave.so.0.1`, SHA-256
`a205924fcd05dffb50ee39d88523d298be9362f727dd37035eeb212779bc1777`.
It does not observe a panel blackout, invoke monitor controls, alter a flag,
or establish that any lifecycle call occurred on the TV.

## What can reset the QD monitor's bookkeeping

The [runtime-map audit](qd-monitor-runtime-map.md) already proves that the QD
monitor itself clears `qd_tcon_off`, its counters and
`g_tcon_monitor_restart` after seeing `g_tcon_monitor_restart == 1`. Two
directly recovered *write-one* routes can request that later clear. The first
is the state-change helper:

```text
ave_tcon_monitor_onoff(argument)
  store argument -> g_tcon_monitor_on
  if argument differs from saved pre_monitor_on:
      store argument -> pre_monitor_on
      store 1 -> g_tcon_monitor_restart

QD monitor, on a later invocation with restart == 1
  clear QD counters and qd_tcon_off
  clear g_tcon_monitor_restart
```

`ave_tcon_monitor_start()` is the second route: it writes 1 directly to both
`g_tcon_monitor_on` and `g_tcon_monitor_restart`; it does not call the helper.
Both routes are bookkeeping reset logic, not a command to restore panel power
or light.
The normal helper does not directly clear `qd_tcon_off`, signal the monitor
condition variable, call QD TCON power control, or issue mute/frame/duty I/O.
The actual QD monitor performs its guarded clear later, if it runs.

The previous runtime baseline had monitor enabled 1, saved previous 1 and restart 0.
That shows no restart request at that read, but does not reconstruct earlier
calls or prove the thread schedule, state at a blackout, output power or light.

## Direct caller search in the matching library

`ave_tcon_monitor_onoff(int)` is globally exported. Its PLT relocation is
index945, jump-slot `0x5a4ed0`, and its ARM PLT entry is `0x8d0c8`. The
hash-gated [reproducer](qd-monitor-lifecycle-callers-reproduce.py) confirms
the helper's stores and performs a complete mapping-symbol scan: all `$t`
intervals decode as Thumb, the one `$a` interval as ARM, and all `$d` literal
pools are excluded. It covers 2,045,156 Thumb bytes, 28 ARM bytes and 298,268
data bytes with no partially decoded code interval. It finds two real direct call
calls to the helper, both in `ave_tcon_api_set_instant_on`.

The direct known-PIC materialization scan for restart offset `0x3370` finds
five literal-pool sites: ULED monitor status, QD OLED monitor, WOLED monitor,
monitor start and `monitor_onoff`. The active QD route's relevant direct stores
are therefore bounded as follows:

| Routine | Exact write | Active-QD interpretation |
| --- | --- | --- |
| `ave_tcon_monitor_start` | stores 1 to monitor-on and restart through GOT | A normal AVE monitor-start request can schedule the later bookkeeping clear |
| `ave_tcon_monitor_onoff` | conditionally stores 1 to restart after changing saved on-state | A changed monitor-on request can schedule the later bookkeeping clear |
| QD OLED monitor | after its restart gate, clears restart and QD counter/latch block | It consumes the request; no panel recovery is implied |

The two other sites are model-specific ULED/WOLED monitor code. They are not
substituted for the active QD OLED behavior. This five-site result covers the
same immediate literal/PIC form only; it is not a proof that no other addressing
form, alias, external writer, firmware or live corruption affects the global.

## Recovered normal lifecycle entry paths

The segmented call inventory exposes two concrete AVE API chains. Neither tells
us which product UI/service called the public entry point, or that it ran during
the owner's event.

```text
ave_api_start_monitor
  -> ave_tcon_api_start_monitor
  -> ave_tcon_monitor_start
  -> store monitor_on=1, restart=1

ave_api_set_instant_on(mode)
  -> ave_tcon_api_set_instant_on(mode)
  -> ave_tcon_monitor_onoff(0 if mode==0, otherwise 1)
  -> conditional restart=1 if remembered state differs
```

The first chain has one recovered call from `ave_api_start_monitor` to the TCON
API, and two call sites from that TCON API to monitor start. The TCON API reads
object words at offsets `+0x28` and `+0x7c`. Its normal `+0x28 == 0` /
`+0x7c == 0` path calls monitor-start at `0x24f102`; its `+0x28 != 0` report
path reloads `+0x7c` and, when that word is zero, converges on that same call.
The `+0x7c != 0` report path calls monitor-start at `0x24f15a`. Thus each of
these recovered normal/report branches reaches one of the two monitor-start
calls. The object fields' semantic names remain unknown.

For Instant On, the public wrapper saves its input at `0x27a04c`, performs a
lookup through PLT `0x8fef4`, and branches to its null-error path if the result
is null; only a non-null result reaches the TCON API call at `0x27a0dc`.
The TCON API saves that input at `0x25122a`, reads object words `+0x28` and
`+0x7c`, and its report branches converge at the input test `0x251240`.
That test is exact: zero is passed through as 0; any nonzero input becomes 1.
This identifies a guarded Instant On lifecycle route, not a panel recovery
button or a known cause of a Home-page blackout.

It also checks complete bodies of the two plausible local lifecycle functions:

| Function | Static result |
| --- | --- |
| `ave_tcon_monitor_start` | **Directly stores 1** to `g_tcon_monitor_on` and `g_tcon_monitor_restart` using the exact GOT slots `0x5a6e18` and `0x5a7370`. It does this without calling `onoff`; if the QD monitor subsequently runs, its established restart branch can clear the latch/bookkeeping. This is a concrete normal-start rearm path, not an observed execution or panel recovery. |
| `ave_tcon_monitor_set_system_power` | No direct call instruction to the `onoff` PLT entry in its 244-byte body. Its name is not evidence that it re-arms the monitor bookkeeping. |

This is meaningful negative evidence inside the recovered direct-call scope:
no named system-power path in this copied AVE library is currently proved to
call the helper directly. Startup and Instant On are different: the first
directly writes the bookkeeping globals and the latter directly calls the
helper through the recovered API chain. This does **not** exclude an indirect
function pointer, an external caller through this
exported interface, a different shared library, a firmware event, or a live
memory write. It is not an installation-wide dependency map. The complete
mapping-symbol scan covers direct ARM as well as Thumb call instructions, so
ARM-mode omission is not a remaining limitation of this direct-call inventory.

## Consequence for the blackout work

There is now a software route that can clear the monitor history latch after a
normal monitor-start or a monitor on-state change, but no proven link from Home tab/content density,
Samsung Live TV, Ugoos, playback, ordinary standby/wake, or the damage location
to that route. In particular, do not use it as a recovery workaround, and do
not infer that a previous reboot cleared the latch by this route.

For an observed future event, preserve the passive monitor fields before and
after the event. If restart changes0→1 and later returns0 with the latch/counters
cleared, that supports this host bookkeeping sequence. It still would not prove
panel recovery, transport emission or a hardware root cause. No flag, cache,
power control or process restart was sent for this audit.

Run the offline check with:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/qd-monitor-lifecycle-callers-reproduce.py
```
