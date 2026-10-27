# PM lock expiry → notifier 20 — bounded static trace

Offline `deviced` audit only; SHA-256: `2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2`. No live-TV action or configuration change was made. `deviced` is ARM-state code at the addresses below; `$a`/`$d` mapping symbols delimit code and literal data.

## Expiry path

`pm_lock_timer_cb` (`0x65f08`) reads a lock-record kind at `r4+0x110`. Its `==5` branch is exact:

```
0x66008  mov r1, #0
0x6600c  mov r0, #0x14
0x66010  bl  0x415ac       ; device_notify(20, NULL)
```

The common tail then schedules the same record through the GLib idle callback:

```
0x65fcc  mov r2, r4
0x65fd0  mov r0, #0
0x65fd4  add r1, pc, ...  ; pm_unlock_timeout, 0x677f4
0x65fd8  bl  0x3e2a8      ; g_idle_add_full-style scheduler
```

`pm_unlock_timeout` (`0x677f4`) reads PM state at `+0x104` and lock ID at `+0x110`, then calls local `pm_unlock_state` (`0x670fc`) with record identity, derived state, and ID. It does not call `device_notify`. This is a deferred PM-unlock continuation, not evidence that a UI/EL-maintenance duration has completed. Its wall-clock dispatch is runtime-dependent.

## Exact type-20 registration and handler

`device_notify` (`0x415ac`) walks enabled notifier nodes, compares node `+4` with the type, then calls function pointer node `+8` with the payload. `el_sensing_init(void*)` (`0x737bc..0x73944`) contains the exact type-20 registration:

```
0x73834  ldr r1, [pc, #0xe0]  ; literal 0x7391c = -0x1d8
0x73838  mov r0, #0x14
0x7383c  add r1, pc, r1       ; _OnSensingTimeOut, 0x7366c
0x73840  bl  0x412a4          ; register_notifier(20, ...)
```

`_OnSensingTimeOut(void*)` (`0x7366c`, `$a`, 84 bytes) ignores its NULL payload. A holder mode byte at `+8` selects exactly one direct wrapper:

| Mode byte | Target | Direct result |
| --- | --- | --- |
| zero | `ELSensing::onSensingTimeOut()` `0x752a0` | invokes its core `0x74fa0` with `r1=1` |
| nonzero | `ELSensingY23::onSensingTimeOut()` `0x7dd34` | invokes its core `0x7da34` with `r1=1` |

The wrappers log/forward; neither itself makes a direct display-panel PPI or display-power call. Crucially, the recovered timeout argument is `r1==1`. If the selected sensing core is in state `2`, its direct branch is `0x7512c..0x75130` (legacy) or `0x7dbc0..0x7dbc4` (Y23): it calls the virtual function in object `+0x34`, vtable `+0x0c`.

That virtual edge is statically resolved for the two known object types:

| Object | vtable symbol / address point | `+0x0c` value | target and consequence |
| --- | --- | --- | --- |
| Legacy `OledDevice` | `0x128a20` / `0x128a28` | `0x128a34 = 0x7a6f8` | `OledDevice::stopELSensing()` → PPI EL-sensing request `0` |
| `OledDeviceY23` | `0x128ae0` / `0x128ae8` | `0x128af4 = 0x80f3c` | `OledDeviceY23::stopELSensing()` → PPI EL-sensing request `0` |

This proves a conditional EL-stop route: kind-5 expiry → notifier 20 → timeout handler → selected sensing core **when state 2** → known OledDevice virtual slot → EL-sensing `0`. A lower-layer PPI return does not prove that a physical state was applied, and this route still does not identify a panel power/output setter.

## Bounded conclusion

Lock ID 5 expiry is statically connected to the EL-sensing timeout notifier and a deferred PM unlock. It does **not** equate a background-standby PM lock expiry with the user-visible screen-optimization/EL duration. It conditionally establishes an EL-stop request, not a panel-off or hardware-output setter. Runtime evidence still required: actual record state/ID, notifier list, selected legacy/Y23 object/state, and downstream PPI/result history. Other dynamically registered handlers remain possible.
