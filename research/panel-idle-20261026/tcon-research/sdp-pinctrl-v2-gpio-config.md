# `sdp-pinctrl-v2` GPIO persistence-config source gap

This is a bounded, offline/source-research note. No TV, GPIO, sysfs export,
device node, controller register, or network service on the TV was accessed.

## Subsequent paired-Image closure

The exact released-source gap below remains real, but it no longer leaves the
narrow persistence callback unresolved. A later, independently reviewed
offline analysis of the acquired paired Image is recorded in
`sdp-pinctrl-v2-config-binary.md`, SHA-256
`4985f8a6e3508479436c51f1980ec6d7ed49278cc29ccca8afe73637163dcd77`;
its checker has SHA-256
`cc9cd7362b008aa0a56c7cc1376bfccad68dd378e1120bca6a520974146a4944`.

That analysis binds the exact driver probe and shows that each constructed
`gpio_chip` has `set_config` at `+0x68` explicitly zero at registration. The
full bounded construction interval contains no later store to that slot, and
generic v5.4.261 chip registration does not populate it. Therefore, for the
acquired paired Image, `gpiod_set_transitory(desc, false)` clears the Linux
descriptor flag but does not deliver `PIN_CONFIG_PERSIST_STATE` to vendor
code.

This closure is paired-Image evidence, not an exact-source recovery or a live
running-text hash. It removes the vendor persistence-MMIO concern only. A
cdev input request remains side-effecting because this driver's
`direction_input` callback unconditionally updates a software bitmap and
performs a locked register read/modify/write before a value can be read.
Metadata-only CHIPINFO/LINEINFO calls are a separate, narrower path and do not
request the line or invoke direction input.

## Practical result

**No exact released source for Samsung's `sdp-pinctrl-v2` driver was
recovered.** At the time of this source-only review, the gpio15 controller's
`gpio_chip.set_config` assignment and its handling of
`PIN_CONFIG_PERSIST_STATE` remained unknown; the subsequent paired-Image
analysis above closes that narrow binary question.

That is a material blocker for both proposed direct GPIO alternatives:

* Linux 5.4.261's v1 GPIO character-device line request calls
  `gpiod_set_transitory(desc, false)` before setting input direction.
* Linux 5.4.261's legacy sysfs `export_store` calls the same function before
  publishing the GPIO.

Neither route was cleared merely because it would only read the eventual GPIO
value. The subsequent null-callback proof removes one blocker but does not
make either line-request route passive: descriptor ownership and input
direction configuration remain. The already reviewed stock QDF GPIO getter
remains the only executed route, with its known request/direction/read/free
and cache/debug ambiguity.

## Exact runtime identity

The authenticated read-only metadata is retained under
`overnight/gpio-controller-metadata-20261026a`:

| Artifact | SHA-256 |
| --- | --- |
| `intent.json` | `ffa8491c5052f81616092205c81084b51521ceb34b095821c1e5c5eb244e67aa` |
| `client.stdout` | `d478bfdad3fd80de82771569cfce4763263d057f0ad320a4b06c555c15934ba8` |
| `client.stderr` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The response is authenticated root output on boot
`00000000-0000-4000-8000-000000000000`, uptime `76783.19..76783.20`, with
status zero and empty stderr. It establishes that platform device
`4630000.pinctrl` is bound to
`/sys/bus/platform/drivers/sdp-pinctrl-v2`, and both `modalias` and `uevent`
identify compatible `samsung,sdp-pinctrl-v2`.

The capture does **not** establish a loadable module. The printed
`.../driver/module` path came from `readlink -f`; that command can
canonicalize a nonexistent final path. No matching pinctrl module appeared in
the bounded `/proc/modules` output, and the captured debugfs
`pinctrl-devices` content was only its header. Calling the driver built-in
from those observations alone would therefore be an inference.

There is stronger but still separately qualified file evidence. The acquired
paired boot Image is:

* `overnight/kernel-Image.bin`, 11,786,752 bytes;
* SHA-256
  `77b6070c12a53f2b7ede3b7c503e242759e22dbaef2d12cc91b556416fed455d`;
* an uncompressed little-endian ARM64 boot Image with 4 KiB pages.

It contains the strings `samsung,sdp-pinctrl-v2` at file offset `0x858820`,
`sdp-pinctrl-v2` at `0x8f1fc8`, and built-in-style metadata strings
`pinctrl_sdp_v2.description=Samsung SDP SoCs pinctrl-v2 driver` and
`pinctrl_sdp_v2.license=GPL v2` near `0x98bf05`. The Image was extracted from
the CRC-valid `/dev/mmcblk0p6` uImage payload; its `Linux-5.4.261` header and
the paired active-root slot agree with the running release. However, no live
running-text hash was obtained. This establishes linkage into the acquired
paired boot Image, not that every byte was proven identical to currently
executing text.

None of these strings or metadata reveals the `gpio_chip` callback table.

## Exact generic Linux behavior

The primary stable source reviewed was Linux v5.4.261
[`drivers/gpio/gpiolib.c`](https://github.com/gregkh/linux/blob/v5.4.261/drivers/gpio/gpiolib.c).
Its `gpiod_set_transitory(desc, false)` behavior is unambiguous:

1. clear the descriptor's `FLAG_TRANSITORY` first;
2. if `chip->set_config` is null, return zero;
3. otherwise pack `PIN_CONFIG_PERSIST_STATE` with argument true and call
   `chip->set_config(chip, gpio, packed)`;
4. normalize only `-ENOTSUPP` to success; propagate every other return.

Thus the unresolved controller has three materially different lower paths:

| Exact controller state | Generic result | What is still changed |
| --- | --- | --- |
| `set_config == NULL` | success | descriptor transitory flag was cleared |
| callback returns `-ENOTSUPP` | normalized success | descriptor transitory flag was cleared; lower callback ran |
| callback handles PERSIST or returns another value | callback-dependent | descriptor flag was cleared and lower callback may touch controller/pin state |

The generic source does not restore the old descriptor flag when a lower
error is returned. Closing/freeing the cdev handle or unexporting sysfs also
does not establish restoration of a controller-specific persistence setting.

`gpiochip_generic_config` and `pinctrl_gpio_set_config` exist in this kernel,
but their presence does not show that `sdp-pinctrl-v2` assigns either route.
Likewise, the runtime driver name and DT compatible do not prove any
particular pinconf implementation. The upstream Samsung/Exynos pinctrl driver
is not a valid behavioral substitute for this private SDP compatible.

## Released-source search boundary

On 2026-10-26, exact-string searches were made for:

* `sdp-pinctrl-v2`;
* `samsung,sdp-pinctrl-v2`;
* `pinctrl_sdp_v2`;
* `Samsung SDP SoCs pinctrl-v2 driver`.

The bounded search covered Samsung's official Open Source Release Center
index, Samsung/GitHub-targeted web search, logged-out GitHub search, and
Sourcegraph's public index including archived/fork queries. No exact driver
source or vendor mirror was recovered. Samsung's live Release Center was
Cloudflare-challenged from this environment, while its indexed results did
not expose an S95F/RoseM/T-RSMF package. GitHub's logged-out code search
required sign-in, and broader public indexes returned no matching code. These
are search limitations, not proof that no corresponding-source archive
exists.

Relevant official entry points retained for a later exact package lookup or
source request are:

* [Samsung Open Source Release Center](https://opensource.samsung.com/)
* [Samsung source-code inquiry](https://opensource.samsung.com/requestInquiry)

No public mainline or generic Exynos file was treated as the missing SDP
implementation.

## Smallest useful next step

Keep the cdev and sysfs plans on HOLD. The next useful work is offline and has
two possible sources of truth:

1. obtain the exact S95F/RoseM corresponding-source archive from Samsung and
   identify the `gpio_chip` registration for this compatible; or
2. use bounded machine-code references from the already acquired Image to
   locate the `sdp-pinctrl-v2` probe/registration, then prove the gpio15
   `set_config` field is null or resolve its exact callback and
   `PIN_CONFIG_PERSIST_STATE` branch.

The existing artificial-base export view contains 9,379 PREL32 export labels,
but the previous full embedded-kallsyms recovery attempt failed; it must not
be represented as a complete internal symbol map. For the binary route, the
proof must identify the actual `gpio_chip` field assignment and callback
body. A nearby `gpiochip_generic_config` export, driver string, or pinconf
table is not sufficient.

If the callback is null, the direct paths still clear the software transitory
flag and change/request line direction as already documented, but the
hardware-persistence concern would be closed. If a callback is present, its
PERSIST case and all writes and returns must be bounded before either direct
value-reader design is reconsidered.

