# `sdp-pinctrl-v2` GPIO persistence callback in the paired kernel Image

## Result

The exact built-in `sdp-pinctrl-v2` probe registers each of its GPIO banks
with **`gpio_chip.set_config == NULL`**.  The slot at `gpio_chip+0x68` is
explicitly zeroed and is not populated before the chip is passed to
`gpiochip_add_data_with_key()`.

For gpio15, this closes the narrow `PIN_CONFIG_PERSIST_STATE` question:
`gpiod_set_transitory(desc, false)` clears Linux descriptor flag `0x1000`,
sees a null `set_config` callback, and returns zero without delivering packed
config `0x116` to this vendor driver and without making a vendor persistence
MMIO call.  The driver therefore neither handles nor rejects
`PIN_CONFIG_PERSIST_STATE`; it has no callback to receive it.

This does **not** make a GPIO character-device value request mutation-free.
The same request subsequently calls the driver's `direction_input` callback,
whose exact body performs register read/modify/write operations even for an
input request.  Descriptor ownership/flags and allocation state also change.
Thus the persistence-callback blocker is resolved, but this report does not
authorize or execute a pin read.

No TV, root, GPIO, pinctrl, ioctl, sysfs, debugfs, network, or live-memory
operation was performed.  This is an offline analysis of the already copied
paired Image.

## Provenance and address spaces

| Input | SHA-256 |
| --- | --- |
| `overnight/kernel-Image.bin` (11,786,752 bytes) | `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d` |
| `overnight/kernel-export-view.elf` | `83a91462c65fd80a4a0ddcd7d5c295b35ea38fc8823298f9018c7353f3cafbc7` |
| `overnight/kernel-export-index.json` | `6d3ffe0edfd2ab92fc4439ffe35371db4c3f2ad8a99cf5b2b20ae2ef4eb937ac` |
| authenticated driver metadata | `d478bfdad3fd80de82771569cfce4763263d057f0ad320a4b06c555c15934ba8` |

The Image banner matches the running kernel's Linux 5.4.261 build, but this is
paired-slot evidence, not a live kernel-text hash and not proof against a
runtime patch.  The failed kallsyms/vmlinux reconstruction was not retried.

All offsets below are raw Image file offsets.  The artificial export view uses
base zero and names only the recovered PREL32 exports; it is not the original
vmlinux.  Initialized data pointers in the Image use linked base
`0xffffffc010080000`, which the checker keeps separate from file offsets.

## Exact platform-driver binding

The platform-driver object begins at Image `0xadf4f8`:

| Object field | Initialized pointer | Converted Image offset |
| --- | ---: | ---: |
| probe | `0xffffffc01043f6f8` | `0x3bf6f8` |
| remove | `0xffffffc01043f688` | `0x3bf688` |
| driver name | `0xffffffc010971fc8` | `0x8f1fc8`, `sdp-pinctrl-v2` |
| OF match table | `0xffffffc0108d87e0` | `0x8587e0` |

The first OF match entry has zero name/type prefixes and the compatible field
at entry `+0x40`, Image `0x858820`, is exactly
`samsung,sdp-pinctrl-v2`.  Init function `0xa18fcc` forms `0xadf4f8` and calls
the recovered export `__platform_driver_register` at `0x494b98`.

Authenticated metadata on boot
`00000000-0000-4000-8000-000000000000` records:

```text
/sys/bus/platform/devices/4630000.pinctrl/driver
  -> /sys/bus/platform/drivers/sdp-pinctrl-v2
DRIVER=sdp-pinctrl-v2
OF_COMPATIBLE_0=samsung,sdp-pinctrl-v2
/sys/class/gpio/gpiochip120/device
  -> /sys/devices/platform/soc/4630000.pinctrl
```

Separate retained metadata identifies gpio15 as base120 with eight lines and
maps the TCON ERR_DET property to gpio15 local line5/global GPIO125.  Those
observations bind the relevant bank to this driver.  They do not hash live
kernel code or prove the pin's electrical state.

## Probe and `gpio_chip` construction

Probe `0x3bf6f8..0x3bfd4f` parses the controller resources and constructs a
`gpio_chip` for each bank.  The bounded per-bank initialization is
`0x3bf918..0x3bfb33`.

At `0x3bf9b4`, `x25 = x26 + 8`; `x25` is the exact `gpio_chip *` later passed
unchanged in `x0` at `0x3bfb20` to exported
`gpiochip_add_data_with_key` (`0x3c6138`).  The probe first zeroes the callback
area.  In particular:

```text
0x3bf9d4  stp xzr,xzr,[x25,#0x60]
```

This clears both `gpio_chip+0x60` and **`gpio_chip+0x68`**.  The latter is the
exact `set_config` slot independently established from the paired Image's
`gpiod_set_transitory` body.

The probe then installs these callbacks:

| `gpio_chip` offset | Stored function | Recovered behavior |
| ---: | ---: | --- |
| `+0x38` | `0x3bff70` | direction input; clears direction/mode state through locked register RMW |
| `+0x40` | `0x3c0020` | direction output; calls the value setter and selects output mode |
| `+0x48` | `0x3c00e0` | get; reads the bank data register and returns one bit |
| `+0x58` | `0x3bfef0` | set; locked read/modify/write of the bank data bit |
| `+0x68` | **zero** | no `set_config` callback |

The complete bounded CFG and every store to the constructed callback region
were manually inspected.  There is no store to `x25+0x68` (equivalently
`x26+0x70`) after the zero and before registration at `0x3bfb30`.  No call in
that interval receives the chip pointer before registration.  The reproducer
pins the whole 1,624-byte probe, the 540-byte construction interval, the
individual callback bodies, exact instruction words, driver pointers,
strings, and both export call targets.  Automated checks intentionally do not
claim to reconstruct a general alias-aware CFG.

The exported `gpiochip_generic_config` exists at `0x3c0e88`, but this vendor
chip does not assign it to `set_config`.  Core registration does not make a
null vendor callback into a persistence implementation merely because that
generic export exists.

## Consequence for `gpiod_set_transitory(false)`

The exact paired-Image generic helper is documented separately in
`kernel-gpio-transitory-exact.md` (SHA-256
`d2e4be7913b49427d2aedea6b67abdacde4a5e857fc8f1f994e12dd99fe2f9b3`).
For boolean false it:

1. clears descriptor flag mask `0x1000`;
2. loads `gpio_chip+0x68`;
3. returns zero immediately when that pointer is null; or, only when non-null,
   packs parameter `0x16`/argument1 as config `0x116` and calls it.

The sdp chip takes the null path.  Consequently this step has a Linux software
descriptor side effect, but it does not send a persistence request to the
vendor pinctrl implementation and does not alter a vendor persistence
register.  There is no `-ENOTSUPP` return to normalize because no callback is
called.

## What remains side-effecting

The v1 line-handle path still requests the descriptor and then invokes
`gpiod_direction_input`.  For this chip, `0x3bff70` modifies a software bitmap
and performs locked MMIO read/modify/write of the per-pin mode field before
returning zero.  Even if the pin was already input, the callback still executes
its writes.  The later getter at `0x3c00e0` is a register read, but it cannot be
reached through that cdev setup without the preceding ownership, descriptor,
and direction operations.

The probe leaves the request/free callback locations zero as part of the same
initialized callback block, so no additional vendor request/free routine was
identified.  Generic descriptor ownership and cleanup still occur.  Close
does not restore the prior direction or the cleared transitory software flag.

Legacy sysfs export shares `gpiod_set_transitory(false)` and therefore also
takes this null vendor-callback path, but it introduces global publication,
ownership and cleanup-residue concerns.  This report does not select sysfs as
an alternative architecture or authorize an export.

## Supported conclusion and limits

Supported:

* the actual bound driver name/compatible matches the paired built-in driver;
* every bank produced by this exact probe, including gpio15, registers a null
  `set_config` slot;
* `PIN_CONFIG_PERSIST_STATE=1` is therefore not delivered to vendor code by
  `gpiod_set_transitory(false)` on this driver; and
* the same cdev request still has a concrete direction-input MMIO write path.

Not supported:

* that copied Image bytes equal live text at the sampling instant;
* that GPIO125 is currently unclaimed, input, low/high, or electrically active;
* that a cdev/sysfs request is passive or should be run;
* that a GPIO sample diagnoses `RT Protect`, panel emission, or fault cause; or
* any pinctrl, protection, recovery, power, or hardware change.

Reproduce offline with:

```sh
python3 tcon-research/sdp-pinctrl-v2-config-binary-reproduce.py
python3 -O tcon-research/sdp-pinctrl-v2-config-binary-reproduce.py
```
