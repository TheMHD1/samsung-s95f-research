# SSB transport driver binding for `/dev/ssb1` and `/dev/ssbs1`

## Result

The required character-driver implementation is **not a separate missing
module in the retained corpus**.  It is compiled into the exact copied
`sdp_pqe_frc.ko` module, in the source unit named `usb-ssb.c`.  The module
contains:

- a USB driver object (`ssb_driver`), an ID table (`ssb_table`), and its
  `ssb_probe` / disconnect / suspend / resume callbacks;
- a `usbmisc`-style character interface (`ssb_fops`) whose relocations bind
  `.open` to `ssb_open`, `.read` to `ssb_read`, `.write` to `ssb_write`,
  `.unlocked_ioctl` to `ssb_ioctl`, and `.release` to `ssb_release`; and
- strings saying the probe registers main and sub devices as `ssb%d` and
  `ssbs%d`, respectively.

Thus a usable `/dev/ssb1` or `/dev/ssbs1` needs a successful runtime USB
probe by this driver's registered USB ID table, followed by its call to the
USB-core device-registration callback.  It is not enough that the module's
ordinary PQE provider code is present.

The first retained current-state metadata probe sampled at boot ID
`00000000-0000-4000-8000-000000000000`, uptime `80515.19` seconds, found:

```
ABSENT /dev/ssb1
ABSENT /dev/ssbs1
ABSENT_CLASS=/sys/class/usbmisc/ssb1
ABSENT_CLASS=/sys/class/usbmisc/ssbs1
```

It performed no open, ioctl, read, write, USB request, or controller command.
This proves absence at those four named paths during that short sample.  That
first sample alone does **not** establish why they were absent, whether the
module was loaded, whether another device name existed, or the state of any
downstream panel or controller.  The later registration-state sample below
does establish that `sdp_pqe_frc` was live at its separate timestamp; it does
not retroactively establish this first sample's module state.

In particular, the names and module logs are insufficient to identify either
endpoint as the TCON or to tie this transport to the owner's black-picture
incident.

## Provenance

All addresses below are relocatable ELF offsets, not runtime addresses.

| input | size | SHA-256 |
| --- | ---: | --- |
| `overnight/sdp-pqe-frc-provider-copy-20261026a/sdp_pqe_frc.ko` | 1,015,070 | `1a312cf33a0ca67c170b9dc73a56a58fa03a0f05bbfb6277a72740dd8e7328a4` |
| `overnight/ssb-device-metadata-20261026a/client.stdout` | 1,201 | `a306d32dfa3dfd1e214fbcb22625bff5ade0d26957cbdf6e2516a26b2f759952` |
| `overnight/ssb-registration-metadata-20261026a/client.stdout` | 5,209 | `2807922e63b27c2aef8d9b3ad9c9b5eb3b20a49f5d6e2808928784b6bff48351` |

The retained local module inventory contains this module and no separately
copied module whose filename or symbols identify it as an SSB character-driver
provider.  That is a bounded inventory observation, not an installed-module
census or a claim that no other implementation could exist.

## Fresh registration-state sample and the exact USB table

A second authenticated, metadata-only sample on the same boot ran from
uptime `80586.50` through `80586.66` seconds.  It found `sdp_pqe_frc` live
with refcount zero.  Its module sysfs directory listed only two platform
driver links (`platform:sdp_ld` and `platform:sdp_pqe_frc`), not a USB-driver
link.  The sample again emitted no present result for its globs over
`/dev/ssb*`, `/sys/class/usbmisc/ssb*`, and `/sys/bus/usb/drivers/*ssb*`.

The driver-name pointer at `.data+0x450` relocates to the literal `"ssb"` at
`.rodata.str1.8+0x5ec0`; its adjacent probe pointer at `.data+0x458` relocates
to `ssb_probe`.  Therefore the metadata glob over `/sys/bus/usb/drivers/*ssb*`
does cover this driver's actual name.  Its absence bounds the named `ssb`
USB-driver directory at that time, but does not exclude an unrelated driver or
a differently named implementation.

The module's 64-byte `ssb_table` begins at `.rodata+0x1f20` with:

```
03 00 e8 04 01 20 00 00 ...
```

Interpreted as the ordinary `struct usb_device_id` leading fields, that is
match-flags `0x0003` (vendor and product), vendor `0x04e8`, product `0x2001`;
the remaining first record is zero.  There is no static interface-class,
subclass, protocol, or revision match value in this record.  The same sample's
cached USB-device metadata contained a device at `/sys/bus/usb/devices/7-1`
with those VID/PID values, product `STL1 CDC and Bulk`, manufacturer `Samsung`,
and device-level driver link `/sys/bus/usb/drivers/usb`.

That is a descriptor-level match candidate, **not** proof that `ssb_probe`
ran or that its USB interface was bound.  The retained sample did not inspect
interface-child bindings, so the device-level generic USB link cannot classify
an interface binding.  The absence of the named nodes/class/driver paths only
bounds the sampled names.  It must not be generalized to absence of all
possible USB transport drivers or all device interfaces.

## Driver registration and endpoint creation

`_ssb_init_func` (`.text+0x573e8`, 272 bytes) is called from the PQE path at
`0x58080` and from two backup-data paths (`0x58a78`, `0x58dd8`).  It first
calls `frc_pqe_sys_get_dimming_info` twice and refuses initialization if bit 1
or bit 2 is set.  It then calls `resolve_usb_symbols` at `0x57454` and
`ssb_usb_register_driver` at `0x574d4`; its local initialized byte and result
are stored in the structure reached through the relocated `.bss+0x44a0`
pointer.  This is a registration/setup path, not an endpoint open.

`ssb_usb_register_driver` (`.text+0x5b9f8`, 148 bytes) dynamically obtains a
USB-registration symbol, requesting its provider module if necessary, then
calls it with this module object and the module's `ssb_driver` object at
`.data+0x450`.  The static `ssb_driver` relocation table binds:

| driver field | target |
| --- | --- |
| probe | `.text+0x5a3d0` `ssb_probe` |
| disconnect | `.text.unlikely+0x5060` `ssb_disconnect` |
| suspend | `.text+0x59df0` `ssb_suspend` |
| resume | `.text+0x591a0` `ssb_resume` |
| pre/post reset | `.text+0x59f40` / `.text+0x59e98` |
| ID table | `.rodata+0x1f20` `ssb_table` |

`ssb_probe` (`.text+0x5a3d0`, 1,460 bytes) allocates and initializes its
per-interface object, discovers matching USB endpoints, allocates transport
buffers, and calls dynamically-resolved USB-core callbacks.  Its probe logic
and its strings show that it registers a main or sub SSB `usbmisc` device.
The strings are descriptive evidence only; the positive executable binding is
the static driver/fops/USB-registration graph above.  The exact live USB
interface, interface number, minor, and successful probe are not retained.

The module's USB alias is `usb:v04E8p2001d*dc*dsc*dp*ic*isc*ip*in*`.  This
is a static match criterion for the driver's USB ID table, not evidence that
a device with those IDs was attached at the sample time.

## Character file operations and what `open` does

The 264-byte `ssb_fops` object at `.rodata+0x1e18` has relocation-backed
entries for the following code:

| operation | function | section offset |
| --- | --- | ---: |
| open | `ssb_open` | `.text+0x5a0d0` |
| read | `ssb_read` | `.text+0x597b0` |
| write | `ssb_write` | `.text+0x5aba8` |
| ioctl | `ssb_ioctl` | `.text+0x591a8` |
| release | `ssb_release` | `.text+0x5aa78` |
| flush | `ssb_flush` | `.text+0x59ce0` |

`ssb_open` obtains the interface from the USB core using the inode minor,
rejects a missing interface or missing per-interface object with `-ENODEV`,
then calls the dynamically resolved `usb_autopm_get_interface` callback on
that interface (`0x5a138..0x5a140`).  Only a zero return continues to increment
the object reference count and store it at `file->private_data` (`file+0xc8`).
`resolve_usb_symbols` obtains this callback through `__symbol_get` and stores
it at its dynamic callback table `+0x70` (`0x5b258..0x5b26c`); the resolved
name is the exact literal `usb_autopm_get_interface` at
`.rodata.str1.8+0x5c60`.

The matching `ssb_release` route loads callback-table `+0x30` and invokes it
at `0x5aaa0..0x5aab0`.  The resolver binds that slot at
`0x5b118..0x5b12c` to `usb_autopm_put_interface` (literal at
`.rodata.str1.8+0x5880`).  Consequently, a successful file open/release pair
acquires and releases USB runtime-PM usage.  USB runtime-PM acquisition can
resume an interface; this static evidence does not establish whether it would
resume this specific device at runtime.

Neither complete file operation directly calls a vendor controller reset,
explicit vendor power-control helper, or a data-transfer/URB-submit callback.
That is narrower than saying they are inert: the runtime-PM get/put side effect
is real, and opening a real character device was not attempted.

`ssb_write` is different: after copying user bytes it obtains a URB, builds a
bulk transfer, submits it via a resolved callback, and waits for its completion.
`ssb_read` similarly drives the read I/O helper.  `ssb_ioctl` only dispatches
commands `0x0a` and `0x0b` to `tcon_read_backup_data` and
`tcon_restore_backup_data` when a per-file context is present.  These
write/read/ioctl paths are not safe inspection interfaces and were not used.

## `ssb_usb_device_ready` is not a device-node test

`ssb_usb_device_ready` at `.text+0x5bb70` calls `find_module` using an
embedded module-name string.  It returns zero if that module cannot be found,
or if its first 32-bit state field is nonzero; otherwise it returns the
32-bit word at offset `+0x90` of an object reached through a relocated
pointer.  It does not stat `/dev/ssb1`, inspect `/sys/class/usbmisc`, open a
node, or check the `ssb_device_ready` global directly in its own body.

Consequently, a positive result is only the module's chosen readiness value,
not proof that either named character node currently exists.  Conversely, the
sampled node absence does not prove the return value of this helper because it
was not called.

## What this closes, and what it does not

Closed static edge:

```
_ssb_init_func
  -> dynamic USB registration callback(ssb_driver)
  -> ssb_probe
  -> USB-core device registration(ssb_class, ssb_fops)
  -> /dev/ssbN or /dev/ssbsN, if runtime probe/registration succeeds
```

The ordinary PQE CAD writer's `filp_open("/dev/ssb1")` therefore targets a
character interface supplied by the same `sdp_pqe_frc.ko` implementation,
not an unknown named external transport module.  Nothing in this conclusion
proves the device was present, opened, or used in the incident.

Remaining edges include the live dynamic USB callback bindings, the actual
USB device/interface that would satisfy the ID table, USB-core minor naming,
and the endpoint behind any successful transfer.  Those require additional
runtime evidence; none is inferred from endpoint names.

## Reproduction

Run only against the retained local copy:

```sh
python3 tcon-research/ssb-transport-driver-binding-reproduce.py
python3 -O tcon-research/ssb-transport-driver-binding-reproduce.py
```

The helper hashes the exact module and metadata response, checks fops/driver
relocations and the selected function landmarks, and does not load or invoke
the module.
