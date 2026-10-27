# ERR_DET GPIO character-device ABI and side-effect boundary

This is an offline ABI and call-path review. It did not open a GPIO device,
request a line, change direction, read a value, or access the TV. The narrow
question is whether Linux's GPIO character-device ABI can obtain one current
ERR_DET sample independently of AVE/QDF policy.

## Decision

The ABI is exact and a direct sample would bypass QDF's cached-power gate,
debug override, and AVE's historical monitor latch. **A value-reading helper
is nevertheless HOLD, not yet cleared for implementation or execution.**

Linux 5.4.261's v1 `GPIO_GET_LINEHANDLE_IOCTL` path always calls
`gpiod_set_transitory(desc, false)` after claiming the line and before setting
input direction. That call clears the descriptor's `FLAG_TRANSITORY`; if the
gpio15 controller supplies `set_config`, it also requests
`PIN_CONFIG_PERSIST_STATE=1`. Close/free does not restore that flag or the
prior persistence setting. The stock vendor getter reviewed earlier does not
call `gpiod_set_transitory`.

Therefore the proposed character-device route is **not side-effect-equivalent
to the stock getter**. Before any implementation can be cleared, the exact
gpio15 controller's `set_config`/persistence behavior must be recovered and
bounded. Merely naming the line-handle request “input” or “read-only” is
insufficient.

The v5.4.261 stable tree keeps this character-device implementation in
[`drivers/gpio/gpiolib.c`](https://github.com/gregkh/linux/blob/v5.4.261/drivers/gpio/gpiolib.c),
not `drivers/gpio/gpiolib-cdev.c`; that latter path does not exist at this tag.
The ABI definitions are in
[`include/uapi/linux/gpio.h`](https://github.com/gregkh/linux/blob/v5.4.261/include/uapi/linux/gpio.h).

## Retained route identity

The authenticated read-only metadata acquisition is
`overnight/gpio-route-metadata-20261026a`:

| Artifact | SHA-256 |
| --- | --- |
| `client.stdout` | `d3250426a66c40014eaf5fd4b148635c3d9ea25ce7f726fbbc356dbdfbee2bf6` |
| `client.stderr` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `intent.json` | `af7063eb520ea32a4890d86f99fe20d2a4d5c84c016abc6cd7e969fb320dd630` |

It is authenticated root output on boot
`00000000-0000-4000-8000-000000000000`, uptime `76487.67..76487.77`, with
status0, no timeout and empty stderr. It establishes:

* `/dev/gpiochip15` is a root-owned mode0600 character device with device
  number `fe:f` (major254, minor15);
* the matching sysfs chip has label `gpio15`, base120 and 8 lines;
* debugfs lists `gpiochip15: GPIOs 120-127 ... gpio15`;
* legacy sysfs GPIO125 is not exported and debugfs did not list a current
  line125 consumer at that instant.

The retained `overnight/gpio-control-map.json`, SHA-256
`c254af8fc86c00efbb84a0f97e56bf0b7e2df0f6ab2f6a3131c64af3bde5e5e1`,
maps vendor property `samsung,err_det` to phandle`0x36`, controller
`soc/pinctrl/gpio15`, local offset5, DT flags0, and legacy Linux GPIO125.

Absence from sysfs/debugfs is only a point-in-time observation. A future
request must query line information immediately before requesting and must
still accept `-EBUSY` as a race-safe refusal without retry.

## Fixed ARM32 ABI

The v1 UAPI uses fixed-width arrays and integers; it contains no userspace
pointer or C `long`. The ARM32 compat handler only converts the ioctl argument
pointer and calls the same implementation. The layouts are consequently the
same for the deployed ARM32 process and AArch64 kernel.

| Structure | Size | Required offsets |
| --- | ---: | --- |
| `gpiochip_info` | 68 | name0[32], label32[32], lines64:u32 |
| `gpioline_info` | 72 | line_offset0:u32, flags4:u32, name8[32], consumer40[32] |
| `gpiohandle_request` | 364 | offsets0[64*u32], flags256:u32, defaults260[64], label324[32], lines356:u32, fd360:i32 |
| `gpiohandle_data` | 64 | values0[64*u8] |

Using the standard `_IOC` encoding in the exact header gives:

| Operation | Constant | Direction/size |
| --- | --- | --- |
| `GPIO_GET_CHIPINFO_IOCTL` | `0x8044b401` | read, 68 |
| `GPIO_GET_LINEINFO_IOCTL` | `0xc048b402` | read/write, 72 |
| `GPIO_GET_LINEHANDLE_IOCTL` | `0xc16cb403` | read/write, 364 |
| `GPIOHANDLE_GET_LINE_VALUES_IOCTL` | `0xc040b408` | read/write, 64 |
| forbidden `GPIOHANDLE_SET_LINE_VALUES_IOCTL` | `0xc040b409` | read/write, 64 |

The only request flag permitted for a future candidate is
`GPIOHANDLE_REQUEST_INPUT=1`. It must not set OUTPUT`2`, ACTIVE_LOW`4`,
OPEN_DRAIN`8`, OPEN_SOURCE`16`, or any unknown flag.

Any managed implementation must use explicit byte/fixed-array layouts rather
than platform-dependent string marshalling, and must fail before opening the
chip unless it is ARM32, little endian, and all four sizes and field offsets
above match exactly. Each ioctl request value must be passed as a 32-bit
unsigned value. Return and errno for every open/ioctl/close must be retained.

## Required identity and refusal gates

A future helper, if the persistence issue is resolved, must first:

1. Require the exact boot and `/dev/gpiochip15` character-device identity
   expected by the execution plan, including nonsymlink status, major/minor,
   owner and mode.
2. Open the chip `O_RDONLY|O_CLOEXEC` once.
3. Call CHIPINFO once and require exact C strings `gpiochip15`, `gpio15`, and
   lines8.
4. Initialize a zeroed LINEINFO with `line_offset=5`, call it once, and require
   offset5 plus flags exactly zero. This refuses KERNEL/busy, output,
   active-low, open-drain and open-source states. A nonempty consumer with
   otherwise zero flags is inconsistent and must also refuse.
5. Build one fully zeroed 364-byte request with only offset[0]=5, flags=INPUT,
   a short fixed ASCII consumer label, lines=1 and fd=-1.

`flags==0` at LINEINFO is not a lock. If another user claims the line before
the handle request, `gpiod_request` returns `-EBUSY`; that is a terminal
incomplete result, not grounds for retry.

## Exact line-handle behavior

The stable source's `linehandle_create` performs these steps:

1. copies all364 request bytes; validates line count and flags;
2. allocates handle state and consumer label;
3. calls `gpiod_request` for offset5, which owns the descriptor and may call
   the gpio15 driver's request/get-direction hooks;
4. applies any requested active-low/open mode flags (none are permitted here);
5. calls `gpiod_set_transitory(desc,false)`;
6. calls `gpiod_direction_input` and treats an error as fatal;
7. creates an `O_RDONLY|O_CLOEXEC` anonymous line-handle fd and copies that fd
   into the request.

The persistence step at item5 is the current blocker. It first clears the
software transitory flag and may call the controller's `set_config` with a
persistence-state request. That occurs even though the requested line mode is
input and before any value read. If a non-`ENOTSUPP` lower error occurs, the
request unwinds, but the source does not restore the transitory flag first.

The input-direction step is also a mutation, although it matches the intended
direction change in the stock vendor getter. Unlike that vendor getter, the
cdev path propagates a direction error and will not produce a handle.

On a handle GET ioctl, the kernel reads the line via
`gpiod_get_array_value_complex(raw=false,can_sleep=true)`, propagates a lower
read error, zeroes all64 output bytes, and writes the first value as 0 or1.
Because a permitted request never sets ACTIVE_LOW and the pre-request
LINEINFO gate requires that flag clear, this logical value equals the raw
chip value in this bounded path. A candidate should initialize all64 input
bytes to a sentinel and require output byte0 in `{0,1}` with bytes1..63 zero.

It must never call the SET-values ioctl.

Closing the line handle calls `gpiod_free`, releases the consumer label and
module/device references, and clears requested, active-low, open-drain and
open-source descriptor flags. It can call the controller's free hook. It does
not restore the prior GPIO direction, `FLAG_TRANSITORY`, or a lower driver's
persistence configuration. The chip fd must then also be closed. Both closes
belong in `finally` paths, and process exit is only a fallback, not the normal
cleanup proof.

## What a successful sample would and would not mean

This route directly addresses gpiochip15 offset5. It does not enter
`/dev/tztv_tcon`, QDF's cached `m_tcon_power_state` gate, QDF's debug override,
or AVE's userspace monitor/latch. If all binding and request guards pass, one
successful GET would therefore be a stronger current raw-level sample than
the prior QDF-mediated output.

The exact vendor monitor treats a successful nonzero raw ERR_DET value as a
fault predicate. Thus raw1 would be consistent with that vendor predicate at
the sample instant. It would still not identify electrical polarity at the
panel connector, show OLED emission, explain `RT Protect`, establish the
cause of the blackout, or authorize a recovery action.

Direct and transitive side effects include descriptor ownership, consumer
label/module/device allocations and references, optional controller request
and free hooks, persistence configuration, input-direction configuration, a
controller value read, and any enabled GPIO tracepoint. This is not a passive
memory read.

## Minimum next prerequisite

Before building or running a value reader, recover the exact gpio15 chip
registration and determine whether its `set_config` is absent, rejects
`PIN_CONFIG_PERSIST_STATE` with `-ENOTSUPP`, or changes hardware/software
state. If it changes state, the v1 line-handle route should not be used merely
to obtain an independent sample. No retry or fallback to sysfs/event/output
interfaces should be added implicitly.

## Sysfs export is not a persistence-free alternative

The tempting legacy sequence—export GPIO125 only if absent, read
`direction`, `active_low`, and `value`, then unexport it—does not avoid the
blocker. Exact Linux 5.4.261
[`gpiolib-sysfs.c`](https://github.com/gregkh/linux/blob/v5.4.261/drivers/gpio/gpiolib-sysfs.c)
shows that `export_store` performs:

1. `gpiod_request(desc,"sysfs")`;
2. **`gpiod_set_transitory(desc,false)`**;
3. `gpiod_export(desc,true)` and `FLAG_SYSFS` publication.

It therefore has the same potential descriptor/hardware persistence mutation
as the cdev handle, plus global sysfs publication, device/attribute allocation,
and cleanup-residue concerns.

Export itself does not call `gpiod_direction_input`. Reading `direction`
calls `gpiod_get_direction` and reports the result; writing `direction` would
change it. A bounded shell that refuses unless the returned text is exactly
`in` could avoid an explicit direction write, but it relies on the line
already being input. Reading `active_low` is a software-flag observation.
`value_show` calls `gpiod_get_value_cansleep`, so exact `active_low=0` is
required before treating its `0`/`1` as raw.

`unexport_store` only frees a descriptor after atomically clearing
`FLAG_SYSFS`; `gpiod_free` then removes the export and releases the line. It
still does not restore persistence configuration or prior direction.

There is also an ownership gap in a shell-only transaction. A trap can set an
`owned=1` flag immediately after a successful synchronous export and unexport
only when that flag is set. It must refuse if GPIO125 existed initially and
must never unexport a preexisting node. But process death in the narrow window
after the kernel accepts export and before the shell records `owned=1` can
leave a global export behind; a later process cannot authenticate that export
as its own because the sysfs consumer label is only `sysfs`. A lost controller
response creates the same cleanup-proof problem even if the target trap
usually runs.

Consequently sysfs is also **HOLD**. It is not an authorized automatic
fallback and does not remove the need to resolve gpio15's persistence-config
behavior first.

