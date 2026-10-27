# `deviced` off-sensing policy path

This is an offline analysis of the copied `deviced` daemon, SHA-256
`2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2`.
It establishes static policy paths. It does not show that one was invoked on the
TV, that it completed, or that it caused a physical blackout.

## Execution mode and back-end boundary

`deviced` is ELF32 ARM. Its selected mapping symbols are `$a` and the functions
below have even addresses; the reproducer decodes them as ARM, not Thumb. Its
undefined imports include `ppi_displaypanel_set_offsensing`,
`ppi_displaypanel_set_offsensingShortTerm`,
`ppi_displaypanel_set_tcon_power`, and availability/info getters. The matching
PPI/AVE/QD route from the first setter to the QD off-sensing control request is
documented separately in [qd-sensing-entry-callers.md](qd-sensing-entry-callers.md).

The daemon has two substantially parallel implementations. The factory selector
is now resolved: `off_sensing_init` (`0x76558`) first requires
`config_get_off_sensing_support()` (`0xca5ec`) to return nonzero. It then calls
`config_get_product_year()` (`0xcb69c`); the value `0x17` constructs and stores
the Y23 implementation, otherwise it constructs and stores the legacy one.
It writes its selector byte `is_y23_model` at `0x12af90`, and stores legacy and
Y23 instances at `0x12af88` and `0x12af8c` respectively.

| variant | start | power-suspend handler | user start | power-normal handler |
| --- | --- | --- | --- | --- |
| legacy `OffSensing` | `0x774e0` | `0x78ab8` | `0x79368` | `0x791ac` |
| `OffSensingY23` | `0x7eee0` | `0x7fba4` | `0x80374` | `0x80208` |

The C-visible wrapper `off_sensing_request_start_by_user` at `0x76700` tests a
global selector byte. It branches to legacy `startByUser` at `0x79368` when the
byte is zero, or Y23 `startByUser` at `0x80374` otherwise. It returns `-1` when
the selected object pointer is null. A bounded, named GDBus-facing handler,
`gdbus_request_off_sensing` at `0x5dee0`, calls it directly at `0x5dfe0`
when its decoded request value is zero; a nonzero request value calls the tester
path `off_sensing_request_start_by_tester` at `0x5df48`. This proves an IPC
request entry point, but does not identify Home, For You, Live, Apps, or a
particular IPC client as its caller.

## What normal power policy can do

The two `onPowerSuspend(poweroff_info*)` functions are the strong static
entry-points. In both variants, they reject a null event and then require a
specific event-state value (`[event] == 1`), reject event type `6`, and require
the sensing state field at object `+0x24` to be zero before they take their
start/scheduling path. They then distinguish an event reason `0x2a` from other
reasons. On the non-`0x2a` path they call a `needSensing()` helper before
calling their respective `start(reason)` function. The legacy handler does so
at `0x78de0..0x78f2c`; Y23 does so at `0x7fde0..0x7fe58`.

The `start` functions are not a blind display-off action. They query virtual
methods from the attached `OledDevice`, then either arrange a timer/state
transition or report a failed start. The relocated vtables resolve the
previously unnamed legacy calls: from address point `0x128a28`, offset `+0x5c`
is `getTCONState`, `+0x38` is `turnOnTCON`, `+0x18` is
`startOffSensing`, and `+0x28` is `startJBUpdate`. The Y23 address point is
`0x128ae8`; its comparable start calls `turnOn` at `+0x2c`,
`startOffSensing` at `+0x18`, `startJBUpdate` at `+0x24` for reason 4, and
`turnOff` at `+0x30` on its failure route. The full tables are emitted by the
reproducer. These mappings identify requested software actions only.

The special `0x2a` power-suspend path in both variants can schedule a timer
while changing sensing state. This is still a reaction to the supplied
`poweroff_info`, not evidence of an awake UI request.

On return to normal power, the two `onPowerStateNormal` handlers inspect the
stored state (`+0x24`) and perform cancellation/ready cleanup: legacy uses
`cancel` at `0x784c0` or `cancel_ready` at `0x7911c`; Y23 uses `cancel` at
`0x7f654` or `cancel_ready` at `0x80174`. This supports a power-lifecycle
state machine rather than an unconditional background loop.

## User-request path is separate

Both `startByUser` routines require the state not already equal to `2`, and
require local `pm_get_power_state` at `0x624d0` to return 1 before setting
pending reason/state values and invoking `start`. The legacy version calls
`start(2)` at `0x794b8`; Y23 calls `start(2)` at `0x804b4`. The explicit
exported wrapper above selects these functions. This proves a user-requested
route exists, but does not identify a Home, For You, Live, Screensaver, or
app-menu caller.

## TCON power capability and limits

`OledDevice::turnOnTCON` (`0x7b234`) calls the ARM PLT target `0x3d558` with
argument 1 and then calls `setTCONState(1)` at `0x7b2a8`. `turnOffTCON`
(`0x7b2d4`) makes the same call with argument 0 and then calls
`setTCONState(0)` at `0x7b348`. The three-instruction PLT sequence at
`0x3d558` resolves to relocation/GOT `0x12a0c0`, whose symbol is
`ppi_displaypanel_set_tcon_power`.

The cached TCON state is failure-insensitive: turn-on calls PPI at `0x7b244`,
saves its return, but still calls `setTCONState(1)` at `0x7b2a8` before
returning. Turn-off likewise calls PPI at `0x7b2e4` and records state0 at
`0x7b348` regardless of that return. Legacy `OffSensing::start` trusts
`getTCONState()` at `0x77504` and branches past its turn-on request when
the result is nonzero (`0x7750c` to `0x77520`). A failed request can thus
advance the desired-state cache and suppress a later identical attempt.
This is a static mechanism, not proof of a failed power request or its causal
role in the owner's blackout. No cache value was forced.

`OledDevice::startOffSensing` / `stopOffSensing` (`0x7a834` / `0x7a89c`) and
their Y23 equivalents (`0x81078` / `0x810e0`) are tiny wrappers that pass 1 or
0 through PLT `0x3d5b8`. Its ARM PLT instructions resolve to relocation/GOT
`0x12a0e0`, symbol `ppi_displaypanel_set_offsensing`, which is the beginning
of the separately proven PPI/AVE/QD request chain. The QD command gate can
still suppress the downstream command, and an accepted request is not proof
that sensing was active or the panel was powered down.

## Conclusion for the menu hypothesis

The copied daemon clearly has two possible off-sensing routes: a structured
power-suspend policy route and an explicit GDBus user-request entry. It does
not provide static evidence that ordinary awake UI navigation is an IPC client
of that entry. Home, For You, and Live code are outside this daemon, and no
caller-to-IPC-client chain has been reconstructed. The current static evidence
therefore supports capturing these requests during a future observed event, not
disabling or forcing the state machine based on a menu correlation.

## Reproduction

From the investigation root, run:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/deviced-off-sensing-policy-reproduce.py
```

The script hash-checks the copied input, parses its ELF `.text`, and produces
bounded ARM disassembly for the addresses above. It needs the already-used
Capstone and pyelftools packages in `/tmp/tcon-capstone`; it performs no
network, TV, firmware, GPIO, power, or display operation.

To save a deterministic local transcript, add `--write-raw` and a file path.
The checked transcript is
`deviced-off-sensing-policy.raw.disasm`, SHA-256
`c5605fe97e37deada844352b4f9419fd6f4567335909ca3d1588860a60d99341`.
