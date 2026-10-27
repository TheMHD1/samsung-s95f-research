# Read-only `deviced` EL/off-sensing observer map

Offline map for copied `binaries/deviced` SHA-256
`2f58aacf9bf073f27ab4f49a54f07abd2bf4536ada3f00dec90110a8e56f9cc2` only.
It specifies later root-operated, read-only `/proc/<deviced-pid>/maps` and
four-byte `/proc/<pid>/mem` reads. It does not authorize a TV/network command,
write, ptrace, injection, or service action.

## PIE rule

Find the exact offset-zero `deviced` executable map. With its ELF first
`PT_LOAD` at VMA zero, `L=map_start`. Every address below is runtime `L+VMA`.
Validate each word target is readable and read a compact snapshot twice; reject
any differing pointer/selector/state value. Static support/configuration does
not prove a live object was constructed.

## EL instance selector and chain

The mapped ARM code for `el_sensing_request_start` (`0x73944..0x73994`, then
`$d`) loads literal `0x73994`, adds it using the **following** ARM PC value
`0x73954`, producing global block `0x12af7c`. It then does:

```
selector = *(uint8_t *)(L+0x12af84)
legacy   = *(uint32_t *)(L+0x12af7c)
y23      = *(uint32_t *)(L+0x12af80)
active   = selector == 0 ? legacy : y23
```

Y23 selection requires PPI EL type zero and product year `0x17`; a nonzero EL type forces legacy. Only a nonzero selected pointer permits the direct start call: legacy start
`0x74a94`, Y23 start `0x7d394`. This is an object-selection observation, not a
claim that either method ran. The caller must retain selector, both pointers,
and selected pointer together; never infer activity from an unselected support
object.

For selected EL objects, capture only established local fields:

| offset | width | evidence |
| --- | --- | --- |
| `+0x30` | int32 | start rejects already-`2`; on successful qualifying start it changes to `2`. |
| `+0x38` | pointer | constructor-stored `OledDeviceTimer`; not evidence a timer is active. |
| `+0x3c` | pointer | constructor-stored `PowerAdapter`. |

Validate the adapter before dereference: its vptr must be `L+0x128ab0`
(`_ZTV12PowerAdapter` VMA `0x128aa8`, Itanium address point `+8`). Its
`getPowerState` virtual target is the named `PowerAdapter::getPowerState` at
`0x7c478`, which tail-branches to `pm_get_power_state`.

## Off-sensing selector and chain

`off_sensing_init` writes the single authoritative family selector and pointers:

```
selector = *(uint8_t *)(L+0x12af90)    # Y23 requires PPI type 0 AND product-year 0x17
legacy   = *(uint32_t *)(L+0x12af88)
y23      = *(uint32_t *)(L+0x12af8c)
active   = selector == 0 ? legacy : y23
```

The user wrapper `off_sensing_request_start_by_user` (`0x76700`) dispatches
legacy `startByUser` `0x79368` or Y23 `0x80374` through that selection. A
nonzero active pointer proves only a pointer value, not a live object or running
without its named state-machine evidence; both suspend handlers require event
state `1` and reject type `6` before their start policies.

## Power-state table: independent local state

`PowerAdapter::getPowerState` uses the global index `L+0x12aeb8`. The bounded
`pm_get_power_state` code multiplies that index by 24 and reads word zero of
the seven-record table at `L+0x1288e4`. Accepted index/code values are:

| index | code/name |
| ---: | --- |
| 0 | start |
| 1 | lcdon |
| 2 | lcdoff |
| 3 | standby |
| 4 | suspend |
| 5 | lowpower |
| 6 | poweroff |

Reject values outside `0..6`; do not use a different public screen-state value
as a substitute. EL start's comparison to `3` is specifically `standby`.

## Request bookkeeping versus running

`RequestELSensing(1)` writes VCONF key `db/sysman/el_sensing_poweroff`; it is
not a live-object field and does not call start directly. The later
`onPowerOffRequested` route has its own request/type/run-cycle gates. Therefore
an observer may report separately: *EL object selected*, *local state word*,
*power-state index*, and *request bookkeeping unknown/not sampled*. It must
not collapse any of those into “maintenance running,” nor infer panel/TCON or
physical light state from them.

Race guard: read global tuple G1 `{EL selector, EL legacy/Y23 pointers, off selector,
off legacy/Y23 pointers, power-state index}`, then selected object header/local
fields and adapter vptr, then global tuple G2. Accept only G1==G2 and matching object reads,
valid selector branch, non-null aligned selected object, valid adapter vptr,
and power index 0–6. Otherwise preserve raw status as unstable/unmapped.
