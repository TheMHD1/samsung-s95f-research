# `deviced` EL / Screen Optimization policy — offline map

This is an offline analysis of the copied matching `deviced` binary. It does
not change a TV, start maintenance, or establish that an EL-sensing request
occurred during an observed physical blackout.

## Provenance and instruction mode

`binaries/deviced` is the 32-bit ARM PIE executable with SHA-256
`2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2`.
Its ELF mapping symbols mark the relevant code as ARM (`$a`), and the named
functions have even addresses. The reproducer uses Capstone ARM mode, not
Thumb mode. It needs the already-installed offline `pyelftools` and Capstone
environment: `PYTHONPATH=/tmp/tcon-capstone`.

## User-request bookkeeping versus actual EL control

The daemon has two parallel generations of the EL-sensing state machine:
`ELSensing` and `ELSensingY23`. `pixelRefreshRequestByUser()` exists in both
(0x73d50 and 0x7c650). It only reads a persisted request value and returns a
boolean-like result; it does not itself call the display-panel EL setter.

The concrete start policy is in `ELSensing::start()` at 0x74a94 and
`ELSensingY23::start()` at 0x7d394. Resolving their `OledDevice` vtables
shows that the first virtual call is an action, `turnOn()`, followed by
`startELSensing()`. In both variants, it proceeds only when:

1. the local state at object+0x30 is not already `2`;
2. an indirect power-state query returns `3` (`standby`, now resolved by the
   [power-state contract](deviced-power-state-contract.md));
3. `startELSensing()` returns zero after the preceding turn-on action.

It then logs/changes the local state to `2`. Its
final indirect call is through the separate `PowerAdapter` at object+0x3c,
with arguments `5` and `0x000dbba0`. Construction stores the `OledDeviceTimer`
at +0x38 and the `PowerAdapter` at +0x3c, so this is **not** a timer-start
call. Resolving the PowerAdapter vtable identifies the target as
`PowerAdapter::lockBGStandby(int, int)` at 0x7c254. The subsequent
[power-state contract](deviced-power-state-contract.md) resolves the argument
unchanged through the type-10 handler and `pm_lock_state` into GLib's
millisecond timeout: a nominal 900,000 ms / 15-minute background-lock expiry
interval. ID-5 expiry also follows a conditional
[EL-timeout/stop route](pm-lock-expiry-notifier.md). This is not a proved
15-minute maintenance duration or the owner's ten-minute popup timer, and a
zero wrapper return does not prove a lock was allocated or panel work began.

`onSensingPrepared()` is a separate gate on the Y23 implementation at
0x7d628: it requires a zero first virtual result, power state `3`, and local
state `1`, then calls 0x7d394. The older 0x756f0 function is instead named
`ELSensing::onOffSensingByELSensingDone()`; it has analogous model-specific
conditions before it can call 0x74a94, but it is not an `onSensingPrepared`
method. Thus a timer/counter or the user request alone is insufficient to show
actual maintenance began.

The resolved older vtable is at 0x128a20, with address point 0x128a28:
`+0x30` selects `turnOn()` at 0x7a9d4 and `+0x08` selects
`startELSensing()` at 0x7a690. The Y23 vtable is 0x128ae0, with address point
0x128ae8: `+0x2c` selects `turnOn()` at 0x81218 and `+0x08` selects
`startELSensing()` at 0x80ed4. The start wrapper tail-branches to the PPI EL
setter with scalar one. Therefore this path issues a PPI EL-sensing request
before the `lockBGStandby` call when its guards permit it.

The terminal callbacks delegate to `stop()` with different reason codes.
Depending on state/reason, stop can issue an EL-disable request: in state2,
timeout reason1 loads virtual `+0x0c` at `0x7512c` and calls it at
`0x75130` (Y23 load/call `0x7dbc0`/`0x7dbc4`),
and normal-power reason2 does so at `0x75194` (Y23 `0x7dc28`). That slot
resolves to `stopELSensing` (`0x7a6f8` / `0x80f3c`), which tail-branches
to the PPI setter with scalar0. Therefore a callback log proves neither a
successful prior enable nor completed maintenance. These are potential
control actions, not only bookkeeping.

## The actual request boundary

The executable imports `ppi_displaypanel_set_elsensing` (JUMP_SLOT GOT
0x12a0d0). The exact lower static chain from that PPI boundary through the
display-panel libraries, AVE, the TCON API ioctl, and QDF command callback is
already reconstructed in [qd-sensing-entry-callers.md](qd-sensing-entry-callers.md).

Within this binary, `OledDevice::startELSensing()` at 0x7a690 logs then
tail-branches to `ppi_displaypanel_set_elsensing@plt` at 0x3d588 with scalar
`1`; `stopELSensing()` at 0x7a6f8 does so with scalar `0`. The corresponding
Y23 wrappers are 0x80ed4 and 0x80f3c. GNU objdump resolves the PLT symbol
name directly, and the dynamic relocation names the JUMP_SLOT at 0x12a0d0.
The four wrappers therefore distinguish a request to enable/disable EL
sensing from UI request bookkeeping. A linked route alone cannot prove the
runtime PPI binding, its return value, a bus transfer, controller acceptance,
or a completed sensing cycle.

## Relation to the owner’s prompt and blackout

The reported 60-second "Screen Optimization" confirmation and the claimed
roughly ten-minute off/on period are consistent with a *separate user-facing
workflow which can lead into this EL state machine*, but this copied daemon
does not contain the UI text or a 60,000-ms literal at the mapped start gate.
It therefore cannot identify the popup implementation or prove it emitted the
EL request. The `0x000dbba0` argument reaches `lockBGStandby`; its units are
not yet established and it cannot be compared to the reported ten minutes.

The saved log at `tcon-deep-probe.json` does contain normal off-sensing
power-off/power-on lifecycle activity around uptime 1826–1836. That is not an
EL request, is not aligned to the later menu blackouts, and must not be used
to attribute them to Screen Optimization. The saved retained EL timer lines
(`ELSensing ... update time`) likewise establish only elapsed bookkeeping.

No wakeful UI-navigation edge into the Y23 `onSensingPrepared`, no
physical-blackout edge into any EL setter, and no live PPI binding were
captured. This build does not expose kprobes, uprobes, or function tracing, so
a direct PPI-call trace is not currently implemented. The next evidence that
could make this causal is an onset-aligned capture of daemon lifecycle logs
together with lower I2C `0x1a0` control-request markers while a separate
observer confirms the physical panel state.

## Reproduction

Run:

```sh
PYTHONPATH=/tmp/tcon-capstone python3 tcon-research/deviced-el-sensing-policy-reproduce.py
```

It checks the binary hash and emits bounded ARM disassembly of the start,
user-request, transition, PPI-wrapper, and terminal state paths. It has no
network or TV code.
