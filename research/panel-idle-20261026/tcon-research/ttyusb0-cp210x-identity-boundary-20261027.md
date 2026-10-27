# `ttyUSB0` CP210x identity boundary

This is a documentation review of already retained metadata plus the upstream
Linux `cp210x` source. It did not open a TTY, transmit serial bytes, access
USB control endpoints, or make a TV call.

## Result

`ttyUSB0` is positively identified as the separately enumerated USB device
`04e8:20e4`, product **SmartThings Dongle**, manufacturer **Silicon Labs**,
bound to the `cp210x` USB-serial driver. This is distinct from the separate
Samsung `04e8:2001` / `STL1 CDC and Bulk` device used by the retained
reset-coupled/SSB evidence.

Accordingly, `ttyUSB0` is **not evidence of the TCON/SSB USB transport** and
is excluded as a TCON serial/debug path on the present evidence. This is an
identity separation, not a claim about every function the SmartThings dongle
could provide.

## Retained positive provenance

`overnight/rt-telemetry-followup-20261027b/usb-uart-parent-metadata.txt`
(SHA-256 `21f5cbbd20ad20d77b55d476353b7febbe20dd8a9bd13c074e04fd7f6d0683d`)
and its structured counterpart
`usb-uart-parent-metadata.json` (SHA-256
`7bdf1e45f653059efd65722b677d615e826341e8ab7740f035453422a969d73d`)
record, on boot UUID `00000000-0000-4000-8000-000000000000`:

| property | retained value |
| --- | --- |
| tty parent | `/sys/devices/platform/soc/2818000.ohci/usb12/12-1/12-1:1.0/ttyUSB0` |
| USB device | `12-1` |
| VID:PID | `04e8:20e4` |
| manufacturer / product strings | `Silicon Labs` / `SmartThings Dongle` |
| driver link | `/sys/bus/usb-serial/drivers/cp210x` |
| interface class/subclass/protocol | `ff/00/00` |

The retained `/proc/tty/driver/usbserial` observation independently reports
one cp210x port at the same `04e8:20e4` identity and OHCI path. It is a
binding observation, not a record of a serial session.

## Upstream-driver check

The primary Linux source reviewed was the current upstream
[`drivers/usb/serial/cp210x.c`](https://github.com/torvalds/linux/blob/master/drivers/usb/serial/cp210x.c).
Its USB-ID table has no textual `0x20e4` or `0x04e8` match in that source
revision. Upstream therefore does not provide a product-name or TCON/MCU
interpretation for `04e8:20e4`.

That is compatible with the TV's retained observation that its vendor kernel
binds the device through `cp210x`; it does **not** identify why this vendor
kernel accepted the ID. No matching cp210x source, modalias entry, device
tree node, or retained module string was found tying `04e8:20e4` to Samsung
TCON, OCB, SSB, or an MCU. A VID alone is not such a tie.

## Contrast with the independently relevant USB identity

The retained SSB transport work is pinned to a different device:
`04e8:2001`, manufacturer `Samsung`, product `STL1 CDC and Bulk`, including a
module USB alias that matches exactly `usb:v04E8p2001...`. Its device path,
function, and reset-coupled observations must not be transferred to the
SmartThings dongle simply because both IDs have Samsung's vendor value.

## Boundary

This report establishes only current cached identity and separation. It does
not prove the dongle's physical wiring, protocol, trust role, whether it is
internal or external, serial activity, or any causal relation to the display
fault. No serial probing is proposed from this evidence.
